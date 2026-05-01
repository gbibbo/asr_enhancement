#!/usr/bin/env python3
"""T1.2 dependency import probe / verifier.

Two modes:

* ``--mode probe``: discovery only. Reports interpreter, platform, pip
  availability, sanitized ``sys.path``, per-package import status (with
  version + ``__file__``) and torch CUDA fields. Exits non-zero on
  blockers (pip unavailable, torch missing/broken).

* ``--mode verify``: everything ``probe`` does, plus explicit project
  submodule imports and three origin assertions:

    1. every imported ``libs.*`` module's ``__file__`` lives under
       ``$ASR_REPO_ROOT``;
    2. no project-source directory (``libs/``, ``services/``,
       ``scripts/``, ``alembic/``, ``configs/``) exists under ``$PREFIX``;
    3. ``torch.__file__`` does not live under ``$PREFIX``.

In both modes, a structured JSON summary is written to the path passed
via ``--out``; the same data is mirrored to stdout for Slurm logs.

The probe never instantiates application Settings, never imports
``services.api.app.main``, and never reads or prints environment
variables outside an explicit allow-list.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as md
import json
import os
import platform
import shutil
import site
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ENV_ALLOWLIST_EXACT = {"PATH", "PYTHONPATH", "HOME", "LANG"}
ENV_ALLOWLIST_PREFIX = ("ASR_", "LC_")

# (import_name, distribution_name)
PACKAGES = [
    ("torch", "torch"),
    ("torchaudio", "torchaudio"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("soundfile", "soundfile"),
    ("whisper", "openai-whisper"),
    ("fastapi", "fastapi"),
    ("celery", "celery"),
    ("sqlalchemy", "SQLAlchemy"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),
]

# Module imports for verify mode (no Settings instantiation).
PROJECT_MODULES_REQUIRED = [
    "libs.asr_adapter",
    "libs.asr_adapter.factory",
    "libs.audio_pipeline",
    "libs.audio_pipeline.pipeline",
    "libs.common",
    "libs.common.settings",
    "libs.observability",
    "libs.observability.logging",
]

PROJECT_MODULES_OPTIONAL = [
    "libs.asr_adapter.assemblyai",
    "libs.common.db",
    "libs.common.models",
    "libs.common.storage",
    "libs.observability.metrics",
    "libs.observability.tracing",
]

# Top-level repo subdirectories that must NOT be copied into $PREFIX.
PROJECT_DIR_NAMES = {"libs", "services", "scripts", "alembic", "configs"}


# ---------------------------------------------------------------------------
# Blocker codes (must match the plan §"Stop / blocker conditions")
# ---------------------------------------------------------------------------

EXIT_OK = 0
EXIT_PIP_UNAVAILABLE = 2
EXIT_TORCH_MISSING = 3
EXIT_WHISPER_IMPORT_FAILED = 4
EXIT_LIBS_OUTSIDE_REPO = 5
EXIT_PROJECT_IN_PREFIX = 6
EXIT_TORCH_SHADOWED = 7
EXIT_USER_SITE_LEAK = 11
EXIT_TORCH_MISSING_CLEAN = 12

BLOCKER_CODE = {
    EXIT_PIP_UNAVAILABLE: "pip_unavailable",
    EXIT_TORCH_MISSING: "torch_missing_or_broken",
    EXIT_WHISPER_IMPORT_FAILED: "openai_whisper_import_failed",
    EXIT_LIBS_OUTSIDE_REPO: "libs_resolved_outside_repo",
    EXIT_PROJECT_IN_PREFIX: "project_source_copied_into_prefix",
    EXIT_TORCH_SHADOWED: "torch_shadowed_in_prefix",
    EXIT_USER_SITE_LEAK: "scientific_deps_satisfied_from_user_local",
    EXIT_TORCH_MISSING_CLEAN: "torch_missing_or_broken_clean_image",
}

# Substrings that mark a module path as living under the host's user-local
# site-packages. Used by the strict-no-user-site check.
USER_LOCAL_PATH_MARKERS = ("/.local/", "/home/gb0048/.local/")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def sanitize_env_keys() -> list[str]:
    keys = []
    for k in sorted(os.environ):
        if k in ENV_ALLOWLIST_EXACT or any(k.startswith(p) for p in ENV_ALLOWLIST_PREFIX):
            keys.append(k)
    return keys


def pip_version() -> tuple[bool, str]:
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if out.returncode != 0:
            return False, f"exit {out.returncode}: {out.stderr.strip() or out.stdout.strip()}"
        return True, out.stdout.strip()
    except FileNotFoundError as exc:
        return False, f"FileNotFoundError: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def probe_package(import_name: str, dist_name: str) -> dict:
    entry = {
        "distribution": dist_name,
        "import_ok": False,
        "version": None,
        "file": None,
        "error": None,
    }
    try:
        m = importlib.import_module(import_name)
    except Exception as exc:  # noqa: BLE001
        entry["error"] = f"{type(exc).__name__}: {exc}"
        return entry
    entry["import_ok"] = True
    entry["file"] = getattr(m, "__file__", None)
    ver = getattr(m, "__version__", None)
    if ver is None:
        try:
            ver = md.version(dist_name)
        except md.PackageNotFoundError:
            ver = "unknown"
        except Exception as exc:  # noqa: BLE001
            ver = f"metadata-error: {type(exc).__name__}"
    entry["version"] = ver
    return entry


def probe_torch_extras() -> dict:
    extras = {
        "version": None,
        "version_cuda": None,
        "cuda_available": None,
        "file": None,
        "error": None,
    }
    try:
        import torch  # type: ignore
    except Exception as exc:  # noqa: BLE001
        extras["error"] = f"{type(exc).__name__}: {exc}"
        return extras
    extras["version"] = getattr(torch, "__version__", None)
    extras["file"] = getattr(torch, "__file__", None)
    try:
        extras["version_cuda"] = getattr(getattr(torch, "version", None), "cuda", None)
    except Exception as exc:  # noqa: BLE001
        extras["version_cuda"] = f"error: {type(exc).__name__}"
    try:
        extras["cuda_available"] = bool(torch.cuda.is_available())
    except Exception as exc:  # noqa: BLE001
        extras["cuda_available"] = f"error: {type(exc).__name__}"
    return extras


def import_project_modules(modules: list[str], required: bool) -> dict:
    out = {}
    for name in modules:
        entry = {"required": required, "import_ok": False, "file": None, "error": None}
        try:
            m = importlib.import_module(name)
            entry["import_ok"] = True
            entry["file"] = getattr(m, "__file__", None)
        except ModuleNotFoundError as exc:
            if required:
                entry["error"] = f"ModuleNotFoundError: {exc}"
            else:
                entry["error"] = f"absent (optional): {exc}"
        except Exception as exc:  # noqa: BLE001
            entry["error"] = f"{type(exc).__name__}: {exc}"
        out[name] = entry
    return out


def assert_origins(
    project_imports: dict,
    repo_root: str | None,
    prefix: str | None,
    torch_file: str | None,
    torchaudio_file: str | None,
    numpy_file: str | None,
) -> dict:
    result = {
        "repo_root": repo_root,
        "prefix": prefix,
        "all_libs_under_repo": True,
        "libs_outside_repo": [],
        "no_project_dirs_in_prefix": True,
        "project_dirs_in_prefix": [],
        "torch_not_in_prefix": True,
        "torchaudio_not_in_prefix": True,
        "numpy_not_in_prefix": True,
    }
    repo_real = os.path.realpath(repo_root) if repo_root else None
    prefix_real = os.path.realpath(prefix) if prefix else None

    for name, entry in project_imports.items():
        if not name.startswith("libs."):
            continue
        if not entry.get("import_ok"):
            continue
        f = entry.get("file")
        if not f:
            continue
        f_real = os.path.realpath(f)
        if repo_real and not f_real.startswith(repo_real + os.sep):
            result["all_libs_under_repo"] = False
            result["libs_outside_repo"].append({"module": name, "file": f_real})

    if prefix_real and os.path.isdir(prefix_real) and repo_real:
        for entry in os.listdir(prefix_real):
            if entry not in PROJECT_DIR_NAMES:
                continue
            repo_pkg_init = os.path.join(repo_real, entry, "__init__.py")
            if not os.path.isfile(repo_pkg_init):
                continue
            p = os.path.join(prefix_real, entry)
            if os.path.isdir(p):
                result["no_project_dirs_in_prefix"] = False
                result["project_dirs_in_prefix"].append(p)

    if prefix_real:
        if torch_file and os.path.realpath(torch_file).startswith(prefix_real + os.sep):
            result["torch_not_in_prefix"] = False
        if torchaudio_file and os.path.realpath(torchaudio_file).startswith(prefix_real + os.sep):
            result["torchaudio_not_in_prefix"] = False
        if numpy_file and os.path.realpath(numpy_file).startswith(prefix_real + os.sep):
            result["numpy_not_in_prefix"] = False

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("probe", "verify"), required=True)
    parser.add_argument("--out", required=True, help="absolute path to JSON artifact")
    parser.add_argument(
        "--repo-root",
        default=os.environ.get("ASR_REPO_ROOT"),
        help="absolute path to the live repo (defaults to $ASR_REPO_ROOT)",
    )
    parser.add_argument(
        "--prefix",
        default=os.environ.get("T1_2_PREFIX"),
        help="absolute path to the dependency install prefix (defaults to $T1_2_PREFIX)",
    )
    parser.add_argument(
        "--slurm-job-id",
        default=os.environ.get("SLURM_JOB_ID"),
        help="Slurm job ID for the JSON artifact (defaults to $SLURM_JOB_ID)",
    )
    parser.add_argument(
        "--strict-no-user-site",
        action="store_true",
        help=(
            "Enforce that user-site is disabled and that no module file path "
            "lives under ~/.local. Required for clean Stage A and for Stage C."
        ),
    )
    parser.add_argument(
        "--expected-torch-version",
        default=None,
        help="If set, Stage C fails when torch.__version__ != this value.",
    )
    parser.add_argument(
        "--expected-torchaudio-version",
        default=None,
        help="If set, Stage C fails when torchaudio.__version__ != this value.",
    )
    parser.add_argument(
        "--expected-numpy-version",
        default=None,
        help="If set, Stage C fails when numpy.__version__ != this value.",
    )
    args = parser.parse_args(argv)

    user_site_path = None
    try:
        user_site_path = site.getusersitepackages()
    except Exception as exc:  # noqa: BLE001
        user_site_path = f"error: {type(exc).__name__}: {exc}"

    user_site_in_sys_path = bool(
        user_site_path
        and isinstance(user_site_path, str)
        and any(
            os.path.realpath(p) == os.path.realpath(user_site_path)
            for p in sys.path
        )
    )

    summary: dict = {
        "mode": args.mode,
        "slurm_job_id": args.slurm_job_id,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_version": sys.version,
        "sys_executable": sys.executable,
        "platform": platform.platform(),
        "which_python3": shutil.which("python3"),
        "pip_ok": False,
        "pip_version": None,
        "env_keys_visible": sanitize_env_keys(),
        "sys_path": list(sys.path),
        "repo_root": args.repo_root,
        "prefix": args.prefix,
        "strict_no_user_site": bool(args.strict_no_user_site),
        "user_site_enabled": bool(getattr(site, "ENABLE_USER_SITE", False)),
        "user_site_path": user_site_path,
        "user_site_in_sys_path": user_site_in_sys_path,
        "python_no_user_site_env": os.environ.get("PYTHONNOUSERSITE"),
        "pythonpath_env": os.environ.get("PYTHONPATH"),
        "any_user_local_module_paths_detected": False,
        "user_local_module_paths": [],
        "packages": {},
        "torch": {},
        "project_modules": {},
        "origin_assertions": None,
        "blocker": None,
    }

    # ---- Print header to stdout ------------------------------------------
    print(f"=== T1.2 imports probe (mode={args.mode}) ===", flush=True)
    print(f"python_version : {sys.version.replace(chr(10), ' ')}", flush=True)
    print(f"sys.executable : {sys.executable}", flush=True)
    print(f"platform       : {summary['platform']}", flush=True)
    print(f"which python3  : {summary['which_python3']}", flush=True)
    print(f"repo_root      : {args.repo_root}", flush=True)
    print(f"prefix         : {args.prefix}", flush=True)
    print(f"slurm_job_id   : {args.slurm_job_id}", flush=True)
    print(
        "strict_no_user_site         : "
        f"{summary['strict_no_user_site']}",
        flush=True,
    )
    print(f"site.ENABLE_USER_SITE       : {summary['user_site_enabled']}", flush=True)
    print(f"site.USER_SITE              : {summary['user_site_path']}", flush=True)
    print(f"user_site_in_sys_path       : {summary['user_site_in_sys_path']}", flush=True)
    print(f"PYTHONNOUSERSITE            : {summary['python_no_user_site_env']}", flush=True)
    print(f"PYTHONPATH                  : {summary['pythonpath_env']}", flush=True)

    # ---- pip availability -------------------------------------------------
    ok, info = pip_version()
    summary["pip_ok"] = ok
    summary["pip_version"] = info
    print(f"pip            : {'OK ' if ok else 'FAIL '}{info}", flush=True)

    # Sanitized env keys + sys.path (printed for the human log).
    print("env keys (allow-list only):", flush=True)
    for k in summary["env_keys_visible"]:
        print(f"  {k}", flush=True)
    print("sys.path:", flush=True)
    for p in summary["sys_path"]:
        print(f"  {p}", flush=True)

    # If pip is broken, fail early with the matching blocker code.
    if not ok:
        summary["blocker"] = BLOCKER_CODE[EXIT_PIP_UNAVAILABLE]
        write_json(args.out, summary)
        print(f"BLOCKER: {summary['blocker']}", flush=True)
        return EXIT_PIP_UNAVAILABLE

    # ---- Per-package probe ------------------------------------------------
    print("--- package status ---", flush=True)
    for import_name, dist_name in PACKAGES:
        entry = probe_package(import_name, dist_name)
        summary["packages"][import_name] = entry
        marker = "OK     " if entry["import_ok"] else "MISSING"
        ver = entry["version"] or "n/a"
        f = entry["file"] or "n/a"
        err = entry["error"] or ""
        print(f"  {marker} {import_name:20s} {ver:18s} file={f} {err}", flush=True)

    summary["torch"] = probe_torch_extras()
    print(
        f"torch.version       : {summary['torch']['version']}",
        flush=True,
    )
    print(
        f"torch.version.cuda  : {summary['torch']['version_cuda']}",
        flush=True,
    )
    print(
        f"torch.cuda.available: {summary['torch']['cuda_available']}",
        flush=True,
    )
    print(
        f"torch.__file__      : {summary['torch']['file']}",
        flush=True,
    )

    # Detect any module path under ~/.local across packages and torch.
    detected = []
    for name, entry in summary["packages"].items():
        f = entry.get("file")
        if f and any(marker in f for marker in USER_LOCAL_PATH_MARKERS):
            detected.append({"name": name, "file": f})
    tf = summary["torch"].get("file")
    if tf and any(marker in tf for marker in USER_LOCAL_PATH_MARKERS):
        detected.append({"name": "torch (extras)", "file": tf})
    summary["user_local_module_paths"] = detected
    summary["any_user_local_module_paths_detected"] = bool(detected)
    print(
        "user_local_module_paths_detected: "
        f"{summary['any_user_local_module_paths_detected']}",
        flush=True,
    )
    for item in detected:
        print(f"  USER-LOCAL {item['name']:20s} {item['file']}", flush=True)

    # Strict mode: enforce no user-site, no ~/.local module paths, no
    # USER_SITE in sys.path. Used by clean Stage A and by Stage C.
    if args.strict_no_user_site:
        leak = (
            summary["user_site_enabled"]
            or summary["user_site_in_sys_path"]
            or summary["any_user_local_module_paths_detected"]
        )
        if leak:
            summary["blocker"] = BLOCKER_CODE[EXIT_USER_SITE_LEAK]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_USER_SITE_LEAK

    # Hard-stop if torch is missing or broken.
    if not summary["packages"]["torch"]["import_ok"] or summary["torch"]["error"]:
        if args.strict_no_user_site:
            summary["blocker"] = BLOCKER_CODE[EXIT_TORCH_MISSING_CLEAN]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_TORCH_MISSING_CLEAN
        if args.mode == "probe":
            summary["blocker"] = BLOCKER_CODE[EXIT_TORCH_MISSING]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_TORCH_MISSING

    # ---- Verify mode: project module imports + origin assertions ---------
    if args.mode == "verify":
        print("--- project modules (required) ---", flush=True)
        req = import_project_modules(PROJECT_MODULES_REQUIRED, required=True)
        print("--- project modules (optional) ---", flush=True)
        opt = import_project_modules(PROJECT_MODULES_OPTIONAL, required=False)
        merged = {**req, **opt}
        summary["project_modules"] = merged
        for name, entry in merged.items():
            marker = "OK     " if entry["import_ok"] else (
                "absent " if not entry["required"] and entry["error"] and "absent" in entry["error"] else "FAIL   "
            )
            print(f"  {marker} {name:38s} file={entry['file']} {entry['error'] or ''}", flush=True)

        # Hard-fail if openai-whisper does not import.
        if not summary["packages"]["whisper"]["import_ok"]:
            summary["blocker"] = BLOCKER_CODE[EXIT_WHISPER_IMPORT_FAILED]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_WHISPER_IMPORT_FAILED

        # Hard-fail if any required project module did not import.
        missing_required = [
            n for n, e in req.items() if not e["import_ok"]
        ]
        if missing_required:
            summary["blocker"] = f"required_project_module_import_failed: {missing_required}"
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_LIBS_OUTSIDE_REPO  # treat as origin/import failure

        # Origin assertions.
        torch_file = summary["torch"]["file"]
        torchaudio_entry = summary["packages"].get("torchaudio", {})
        torchaudio_file = torchaudio_entry.get("file") if torchaudio_entry else None
        numpy_entry = summary["packages"].get("numpy", {})
        numpy_file = numpy_entry.get("file") if numpy_entry else None
        assertions = assert_origins(
            project_imports=merged,
            repo_root=args.repo_root,
            prefix=args.prefix,
            torch_file=torch_file,
            torchaudio_file=torchaudio_file,
            numpy_file=numpy_file,
        )
        summary["origin_assertions"] = assertions
        print("--- origin assertions ---", flush=True)
        print(f"  all_libs_under_repo      : {assertions['all_libs_under_repo']}", flush=True)
        print(f"  libs_outside_repo        : {assertions['libs_outside_repo']}", flush=True)
        print(f"  no_project_dirs_in_prefix: {assertions['no_project_dirs_in_prefix']}", flush=True)
        print(f"  project_dirs_in_prefix   : {assertions['project_dirs_in_prefix']}", flush=True)
        print(f"  torch_not_in_prefix      : {assertions['torch_not_in_prefix']}", flush=True)
        print(f"  torchaudio_not_in_prefix : {assertions['torchaudio_not_in_prefix']}", flush=True)
        print(f"  numpy_not_in_prefix      : {assertions['numpy_not_in_prefix']}", flush=True)

        if not assertions["all_libs_under_repo"]:
            summary["blocker"] = BLOCKER_CODE[EXIT_LIBS_OUTSIDE_REPO]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_LIBS_OUTSIDE_REPO

        if not assertions["no_project_dirs_in_prefix"]:
            summary["blocker"] = BLOCKER_CODE[EXIT_PROJECT_IN_PREFIX]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_PROJECT_IN_PREFIX

        if (
            not assertions["torch_not_in_prefix"]
            or not assertions["torchaudio_not_in_prefix"]
            or not assertions["numpy_not_in_prefix"]
        ):
            summary["blocker"] = BLOCKER_CODE[EXIT_TORCH_SHADOWED]
            write_json(args.out, summary)
            print(f"BLOCKER: {summary['blocker']}", flush=True)
            return EXIT_TORCH_SHADOWED

        # Pinned-version assertions for torch / torchaudio / numpy.
        if args.expected_torch_version is not None:
            actual = summary["packages"]["torch"].get("version")
            if actual != args.expected_torch_version:
                summary["blocker"] = (
                    f"torch_version_drift: expected {args.expected_torch_version} got {actual}"
                )
                write_json(args.out, summary)
                print(f"BLOCKER: {summary['blocker']}", flush=True)
                return EXIT_TORCH_SHADOWED
        if args.expected_torchaudio_version is not None:
            actual = summary["packages"]["torchaudio"].get("version")
            if actual != args.expected_torchaudio_version:
                summary["blocker"] = (
                    f"torchaudio_version_drift: expected {args.expected_torchaudio_version} got {actual}"
                )
                write_json(args.out, summary)
                print(f"BLOCKER: {summary['blocker']}", flush=True)
                return EXIT_TORCH_SHADOWED
        if args.expected_numpy_version is not None:
            actual = summary["packages"]["numpy"].get("version")
            if actual != args.expected_numpy_version:
                summary["blocker"] = (
                    f"numpy_version_drift: expected {args.expected_numpy_version} got {actual}"
                )
                write_json(args.out, summary)
                print(f"BLOCKER: {summary['blocker']}", flush=True)
                return EXIT_TORCH_SHADOWED

    write_json(args.out, summary)
    print(f"=== T1.2 imports probe complete (mode={args.mode}) ===", flush=True)
    return EXIT_OK


def write_json(path: str, summary: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(f"json_artifact: {p}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
