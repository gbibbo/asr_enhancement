"""T5.2 — Dry-run training script.

Implements the dry-run training pipeline described in
docs/plans/training_datamove1_plan.md §15 (Phase 5 / Tasks T5.2 and T5.3).

Source-of-truth config: configs/training/dry_run.yaml
This script:
  * loads the dry-run config and enforces every key in `guards:`;
  * verifies the clean and degraded manifests exist and match the SHA-256
    values in the config;
  * loads the reserved public demo IDs and verifies none appear in the
    deterministically sampled train/val subsets (50/25, seed=1234);
  * provides a `--validate-only` mode that runs all of the above
    without creating any run directory and without importing any heavy
    library (torch, matplotlib, whisper);
  * provides a `--smoke-mode` and full dry-run path that produce the
    six required artifacts (config.yaml, metrics.csv,
    wer_by_degradation.csv, loss_curve.png, val_wer_curve.png,
    run_summary.md). WER and Word Accuracy values produced here are
    placeholders flagged in run_summary.md: T5.2/T5.3 do not run
    Whisper inference. A trainable enhancer is a small placeholder
    (identity-init Conv1d) — MetricGAN+ is NOT used as a trainable
    enhancer (its pretrained tier is null_or_negative).

Heavy dependencies (torch, matplotlib) are imported lazily inside
training and plotting functions only — `--validate-only` works on the
datamove1 login node without them.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import struct
import subprocess
import sys
import time
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from libs.audio.metrics import (  # noqa: E402  (intentional after sys.path)
    normalize_text,
    word_accuracy,
    word_error_rate,
)
from libs.common.versions import (  # noqa: E402
    DEGRADATION_VERSION,
    ENHANCER_VERSION,
    METRICS_VERSION,
)

REQUIRED_ARTIFACTS = (
    "config.yaml",
    "metrics.csv",
    "wer_by_degradation.csv",
    "loss_curve.png",
    "val_wer_curve.png",
    "run_summary.md",
)

EXPECTED_FAMILIES = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)

EXPECTED_GUARD_KEYS = (
    "refuse_if_artifact_root_inside_repo",
    "refuse_if_reserved_demo_id_present",
    "refuse_if_dataset_version_mismatch_libs_common",
    "refuse_if_degradation_version_mismatch_libs_common",
    "refuse_if_metrics_version_mismatch_libs_common",
    "refuse_if_steps_gt",
    "refuse_if_run_dir_writable_inside_repo",
)


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------
def _blocker(msg: str) -> int:
    print(f"BLOCKER: {msg}", file=sys.stderr)
    return 2


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), *args], text=True, timeout=10
        ).strip()
    except Exception:
        return "unknown"


def _resolve_git_value(env_var: str, *git_args: str) -> str:
    """Return the runtime git value, preferring an env var over `git` subprocess.

    Slurm/Apptainer jobs must not rely on `git` being installed inside the
    container. The driving Slurm script captures the git state on the
    submitting host and exports it as `GIT_COMMIT_AT_RUN` /
    `GIT_BRANCH_AT_RUN`; this helper reads those first and falls back to
    `_git(...)` for local non-Slurm runs. Empty string is treated as "absent".
    """
    val = os.environ.get(env_var)
    if val:
        return val
    return _git(*git_args)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_inside_repo(path: Path) -> bool:
    """True if path resolves under REPO_ROOT."""
    try:
        path.resolve().relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


# -----------------------------------------------------------------------------
# Config loading and schema validation
# -----------------------------------------------------------------------------
def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"config root is not a mapping: {path}")
    return cfg


REQUIRED_TOP_LEVEL = (
    "config_name",
    "dataset_version",
    "degradation_version",
    "metrics_version",
    "enhancer_version",
    "seed",
    "manifests",
    "dry_run_sampling",
    "training",
    "model",
    "paths",
    "required_artifacts",
    "guards",
)

REQUIRED_MANIFEST_KEYS = (
    "clean_filtered_manifest",
    "clean_filtered_manifest_sha256",
    "degraded_manifest",
    "degraded_manifest_sha256",
    "excluded_ids_source",
)

REQUIRED_PATHS_KEYS = (
    "artifact_root",
    "run_dir_template",
    "config_snapshot",
    "metrics_csv",
    "wer_by_degradation_csv",
    "loss_curve_png",
    "val_wer_curve_png",
    "run_summary_md",
)

REQUIRED_TRAINING_KEYS = (
    "steps",
    "batch_size",
    "optimizer",
    "learning_rate",
    "loss",
    "log_every_steps",
    "val_every_steps",
)

REQUIRED_SAMPLING_KEYS = (
    "train_records",
    "val_records",
    "per_family_val_cap",
    "shuffle_seed",
)


def _validate_schema(cfg: dict) -> list[str]:
    errors: list[str] = []
    for k in REQUIRED_TOP_LEVEL:
        if k not in cfg:
            errors.append(f"missing top-level key: {k}")
    if "manifests" in cfg and isinstance(cfg["manifests"], dict):
        for k in REQUIRED_MANIFEST_KEYS:
            if k not in cfg["manifests"]:
                errors.append(f"missing manifests.{k}")
    if "paths" in cfg and isinstance(cfg["paths"], dict):
        for k in REQUIRED_PATHS_KEYS:
            if k not in cfg["paths"]:
                errors.append(f"missing paths.{k}")
    if "training" in cfg and isinstance(cfg["training"], dict):
        for k in REQUIRED_TRAINING_KEYS:
            if k not in cfg["training"]:
                errors.append(f"missing training.{k}")
    if "dry_run_sampling" in cfg and isinstance(cfg["dry_run_sampling"], dict):
        for k in REQUIRED_SAMPLING_KEYS:
            if k not in cfg["dry_run_sampling"]:
                errors.append(f"missing dry_run_sampling.{k}")
    if "guards" in cfg and isinstance(cfg["guards"], dict):
        for k in EXPECTED_GUARD_KEYS:
            if k not in cfg["guards"]:
                errors.append(f"missing guards.{k}")
    arch = (cfg.get("model") or {}).get("architecture")
    if arch and "metricgan" in str(arch).lower() and "placeholder" not in str(arch).lower():
        errors.append(
            "model.architecture must not select MetricGAN+ as a trainable enhancer"
        )
    if cfg.get("enhancer_version") not in (None, ""):
        errors.append("enhancer_version must be null in dry-run config")
    return errors


# -----------------------------------------------------------------------------
# Reserved demo IDs
# -----------------------------------------------------------------------------
def _load_reserved_ids(reserved_yaml_path: Path) -> set[str]:
    if not reserved_yaml_path.exists():
        raise FileNotFoundError(f"reserved demo IDs config not found: {reserved_yaml_path}")
    cfg = yaml.safe_load(reserved_yaml_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError(f"reserved demo config not a mapping: {reserved_yaml_path}")
    examples = cfg.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError(
            f"reserved demo config has no 'examples' list: {reserved_yaml_path}"
        )
    ids: set[str] = set()
    for entry in examples:
        if not isinstance(entry, dict) or "utterance_id" not in entry:
            raise ValueError(f"reserved demo entry missing utterance_id: {entry!r}")
        ids.add(entry["utterance_id"])
    if not ids:
        raise ValueError(f"reserved demo config produced empty ID set: {reserved_yaml_path}")
    return ids


# -----------------------------------------------------------------------------
# Manifest reading + deterministic sampling
# -----------------------------------------------------------------------------
def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _deterministic_train_subset(
    clean_records: list[dict], n: int, shuffle_seed: int
) -> list[dict]:
    indices = list(range(len(clean_records)))
    rng = random.Random(shuffle_seed)
    rng.shuffle(indices)
    return [clean_records[i] for i in indices[:n]]


def _deterministic_val_subset(
    degraded_records: list[dict],
    per_family_cap: int,
    shuffle_seed: int,
) -> list[dict]:
    by_family: dict[str, list[dict]] = {f: [] for f in EXPECTED_FAMILIES}
    for r in degraded_records:
        fam = r.get("family")
        if fam in by_family:
            by_family[fam].append(r)
    out: list[dict] = []
    for fam in EXPECTED_FAMILIES:
        rows = by_family[fam]
        idx = list(range(len(rows)))
        rng = random.Random(shuffle_seed + abs(hash(fam)) % (2**31))
        rng.shuffle(idx)
        out.extend(rows[i] for i in idx[:per_family_cap])
    return out


# -----------------------------------------------------------------------------
# Guard enforcement
# -----------------------------------------------------------------------------
def _check_versions_match_libs_common(cfg: dict) -> list[str]:
    errors: list[str] = []
    if cfg.get("metrics_version") != METRICS_VERSION:
        errors.append(
            f"metrics_version mismatch: cfg={cfg.get('metrics_version')!r} "
            f"libs.common.versions.METRICS_VERSION={METRICS_VERSION!r}"
        )
    if cfg.get("degradation_version") != DEGRADATION_VERSION:
        errors.append(
            f"degradation_version mismatch: cfg={cfg.get('degradation_version')!r} "
            f"libs.common.versions.DEGRADATION_VERSION={DEGRADATION_VERSION!r}"
        )
    if ENHANCER_VERSION is not None and cfg.get("enhancer_version") not in (
        None,
        ENHANCER_VERSION,
    ):
        errors.append(
            f"enhancer_version mismatch: cfg={cfg.get('enhancer_version')!r} "
            f"libs.common.versions.ENHANCER_VERSION={ENHANCER_VERSION!r}"
        )
    return errors


def _check_dataset_version_against_yaml(cfg: dict) -> list[str]:
    dv_path = REPO_ROOT / "configs/training/dataset_version.yaml"
    if not dv_path.exists():
        return [f"dataset_version.yaml not found: {dv_path}"]
    dv = yaml.safe_load(dv_path.read_text(encoding="utf-8"))
    if not isinstance(dv, dict):
        return [f"dataset_version.yaml not a mapping: {dv_path}"]
    expected = dv.get("dataset_version")
    actual = cfg.get("dataset_version")
    if expected != actual:
        return [
            f"dataset_version mismatch: cfg={actual!r} "
            f"configs/training/dataset_version.yaml={expected!r}"
        ]
    return []


def _resolve_run_dir(cfg: dict, slurm_job_id: str, run_id: str, smoke: bool) -> Path:
    artifact_root = Path(cfg["paths"]["artifact_root"])
    template = cfg["paths"]["run_dir_template"]
    resolved = template.format(
        artifact_root=str(artifact_root),
        slurm_job_id=slurm_job_id,
    )
    rd = Path(resolved)
    if smoke:
        rd = artifact_root / "_smoke" / run_id
    return rd


def _run_guards(
    cfg: dict,
    slurm_job_id: str,
    run_id: str,
    smoke: bool,
) -> list[str]:
    errors: list[str] = []
    guards = cfg["guards"]

    artifact_root = Path(cfg["paths"]["artifact_root"]).resolve()
    if guards.get("refuse_if_artifact_root_inside_repo") and _is_inside_repo(artifact_root):
        errors.append(
            f"guards.refuse_if_artifact_root_inside_repo: artifact_root inside repo: "
            f"{artifact_root}"
        )

    run_dir = _resolve_run_dir(cfg, slurm_job_id, run_id, smoke=smoke)
    if guards.get("refuse_if_run_dir_writable_inside_repo") and _is_inside_repo(run_dir):
        errors.append(
            f"guards.refuse_if_run_dir_writable_inside_repo: run_dir inside repo: "
            f"{run_dir}"
        )

    if guards.get("refuse_if_metrics_version_mismatch_libs_common"):
        errors.extend(
            e for e in _check_versions_match_libs_common(cfg) if "metrics_version" in e
        )
    if guards.get("refuse_if_degradation_version_mismatch_libs_common"):
        errors.extend(
            e for e in _check_versions_match_libs_common(cfg) if "degradation_version" in e
        )
    if guards.get("refuse_if_dataset_version_mismatch_libs_common"):
        errors.extend(_check_dataset_version_against_yaml(cfg))

    steps_max = guards.get("refuse_if_steps_gt")
    if isinstance(steps_max, int):
        steps = cfg["training"].get("steps")
        if not isinstance(steps, int):
            errors.append(f"training.steps is not int: {steps!r}")
        elif steps > steps_max:
            errors.append(
                f"guards.refuse_if_steps_gt: training.steps={steps} > {steps_max}"
            )

    return errors


# -----------------------------------------------------------------------------
# Manifest verification (strict on datamove1)
# -----------------------------------------------------------------------------
def _verify_manifest(path: Path, expected_sha256: str, label: str) -> tuple[list[dict], list[str]]:
    if not path.exists():
        return [], [f"{label}: manifest not found: {path}"]
    actual_sha = _sha256_of_file(path)
    if actual_sha != expected_sha256:
        return [], [
            f"{label}: sha256 mismatch: expected={expected_sha256} "
            f"actual={actual_sha} path={path}"
        ]
    try:
        rows = _read_jsonl(path)
    except json.JSONDecodeError as exc:
        return [], [f"{label}: invalid JSONL: {exc}"]
    return rows, []


def _check_reserved_absent(
    rows: list[dict], reserved: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    leaked = sorted({r.get("utterance_id") for r in rows} & reserved)
    if leaked:
        errors.append(f"{label}: reserved demo IDs present: {leaked}")
    return errors


# -----------------------------------------------------------------------------
# validate-only path
# -----------------------------------------------------------------------------
def cmd_validate_only(cfg: dict) -> int:
    """Strict pre-flight on datamove1. No run dir created."""
    schema_errors = _validate_schema(cfg)
    if schema_errors:
        for e in schema_errors:
            print(f"BLOCKER: schema: {e}", file=sys.stderr)
        return 2

    # Use a synthetic slurm_job_id only for run-dir-template substitution check.
    fake_run_id = "validate_only_no_run_dir_created"
    guard_errors = _run_guards(
        cfg, slurm_job_id="VALIDATE_ONLY", run_id=fake_run_id, smoke=False
    )
    if guard_errors:
        for e in guard_errors:
            print(f"BLOCKER: {e}", file=sys.stderr)
        return 2

    # Strict manifest verification + reserved-ID absence on the real subsets.
    manifests = cfg["manifests"]
    clean_path = Path(manifests["clean_filtered_manifest"])
    clean_sha = manifests["clean_filtered_manifest_sha256"]
    degraded_path = Path(manifests["degraded_manifest"])
    degraded_sha = manifests["degraded_manifest_sha256"]

    clean_rows, errs = _verify_manifest(clean_path, clean_sha, "clean_filtered_manifest")
    if errs:
        for e in errs:
            print(f"BLOCKER: {e}", file=sys.stderr)
        return 2
    degraded_rows, errs = _verify_manifest(degraded_path, degraded_sha, "degraded_manifest")
    if errs:
        for e in errs:
            print(f"BLOCKER: {e}", file=sys.stderr)
        return 2

    reserved_yaml = REPO_ROOT / manifests["excluded_ids_source"]
    try:
        reserved = _load_reserved_ids(reserved_yaml)
    except (FileNotFoundError, ValueError) as exc:
        return _blocker(f"reserved demo IDs: {exc}")

    sampling = cfg["dry_run_sampling"]
    train_subset = _deterministic_train_subset(
        clean_rows,
        n=int(sampling["train_records"]),
        shuffle_seed=int(sampling["shuffle_seed"]),
    )
    val_subset = _deterministic_val_subset(
        degraded_rows,
        per_family_cap=int(sampling["per_family_val_cap"]),
        shuffle_seed=int(sampling["shuffle_seed"]),
    )

    if cfg["guards"].get("refuse_if_reserved_demo_id_present"):
        errs = _check_reserved_absent(train_subset, reserved, "sampled_train_subset")
        errs += _check_reserved_absent(val_subset, reserved, "sampled_val_subset")
        if errs:
            for e in errs:
                print(f"BLOCKER: {e}", file=sys.stderr)
            return 2

    expected_train = int(sampling["train_records"])
    expected_val = int(sampling["per_family_val_cap"]) * len(EXPECTED_FAMILIES)
    if len(train_subset) != expected_train:
        return _blocker(
            f"sampled_train_subset size {len(train_subset)} != expected {expected_train}"
        )
    if len(val_subset) != expected_val:
        return _blocker(
            f"sampled_val_subset size {len(val_subset)} != expected {expected_val}"
        )

    print(
        "OK: guards passed "
        f"(train={len(train_subset)} val={len(val_subset)} "
        f"families={len(EXPECTED_FAMILIES)} "
        f"clean_sha_ok=True degraded_sha_ok=True)"
    )
    return 0


# -----------------------------------------------------------------------------
# Artifact writers
# -----------------------------------------------------------------------------
def _write_config_snapshot(
    path: Path, original_text: str, runtime_meta: dict[str, Any]
) -> None:
    """Config snapshot: original dry_run.yaml content + appended runtime block.

    NOT a byte-identical copy — it adds a `runtime:` mapping at the end so the
    snapshot is self-contained for reproducibility (run_id, git_commit, …).
    """
    text = original_text.rstrip("\n") + "\n\n# Runtime metadata appended by train_enhancer.py\n"
    text += yaml.safe_dump({"runtime": runtime_meta}, sort_keys=False)
    path.write_text(text, encoding="utf-8")


def _write_metrics_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["step", "phase", "loss", "wer", "word_accuracy", "note"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def _write_wer_by_degradation_csv(path: Path, family_rows: list[dict]) -> None:
    fieldnames = ["family", "count", "mean_wer", "mean_word_accuracy", "note"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in family_rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def _placeholder_png_bytes(label: str) -> bytes:
    """Return bytes of a minimal valid PNG (1x1 grayscale).

    Used as a fallback when matplotlib is unavailable. The label is only
    embedded in a tEXt chunk so the file is identifiable; no image content
    is rendered.
    """
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)  # 1x1 grayscale
    raw = b"\x00\x00"  # one filter byte + one pixel byte
    idat = zlib.compress(raw)
    text = b"placeholder\x00" + label.encode("utf-8")
    return sig + chunk(b"IHDR", ihdr) + chunk(b"tEXt", text) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _write_loss_curve(path: Path, steps: list[int], losses: list[float]) -> str:
    """Write the loss curve PNG. Returns 'complete' or 'placeholder'."""
    try:
        import matplotlib  # type: ignore

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(steps, losses, marker="o", linewidth=1.0)
        ax.set_xlabel("step")
        ax.set_ylabel("train loss (L1, placeholder)")
        ax.set_title("Dry-run train loss curve")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return "complete"
    except Exception:
        path.write_bytes(_placeholder_png_bytes("loss_curve"))
        return "placeholder"


def _write_val_wer_curve(
    path: Path, val_steps: list[int], val_wers: list[float]
) -> str:
    """Write the val WER curve PNG. Returns 'complete' or 'placeholder'."""
    try:
        import matplotlib  # type: ignore

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(val_steps, val_wers, marker="s", color="tab:red", linewidth=1.0)
        ax.set_xlabel("step")
        ax.set_ylabel("val WER (placeholder, no Whisper)")
        ax.set_title("Dry-run val WER curve")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        return "complete"
    except Exception:
        path.write_bytes(_placeholder_png_bytes("val_wer_curve"))
        return "placeholder"


def _write_run_summary(
    path: Path,
    *,
    cfg: dict,
    runtime_meta: dict[str, Any],
    artifact_status: dict[str, str],
    summary_metrics: dict[str, Any],
    known_failures: list[str],
) -> None:
    lines: list[str] = []
    lines.append("# Dry-run training run summary\n")
    lines.append("Status: dry-run artifact contract proof. Not a training result.\n")
    lines.append("## Reproducibility metadata\n")
    for key in (
        "run_id",
        "git_commit",
        "branch",
        "config_path",
        "dataset_version",
        "degradation_version",
        "metrics_version",
        "enhancer_version",
        "slurm_job_id",
        "output_path",
    ):
        lines.append(f"- {key}: `{runtime_meta.get(key)}`")
    lines.append("")
    lines.append("## Summary metrics\n")
    for k, v in summary_metrics.items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Artifacts\n")
    for name, status in artifact_status.items():
        lines.append(f"- {name}: {status}")
    lines.append("")
    lines.append("## Known failures and limitations\n")
    if known_failures:
        for kf in known_failures:
            lines.append(f"- {kf}")
    else:
        lines.append("- (none recorded)")
    lines.append("")
    lines.append("## Notes\n")
    lines.append(
        "- WER and Word Accuracy values are PLACEHOLDERS. Whisper is not run "
        "during T5.2/T5.3 (Phase 5 dry-run); the artifact contract is the gate, "
        "not convergence."
    )
    lines.append(
        "- The trainable enhancer is a small placeholder (identity-init Conv1d). "
        "MetricGAN+ pretrained is documented separately under "
        "`prior_baselines` (tier null_or_negative, deployment_decision "
        "not_selected) and must NOT be selected as a trainable enhancer."
    )
    lines.append(
        f"- Metrics implementation: libs.audio.metrics ({METRICS_VERSION}); "
        f"degradation: {DEGRADATION_VERSION}; enhancer_version: {ENHANCER_VERSION}."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
# Placeholder trainable enhancer + dry-run loop (lazy torch import)
# -----------------------------------------------------------------------------
def _run_dry_run(
    cfg: dict,
    *,
    config_path: Path,
    config_text: str,
    run_dir: Path,
    run_id: str,
    slurm_job_id: str,
    smoke: bool,
    max_steps_override: int | None,
    seed_override: int | None,
    no_plots: bool,
) -> int:
    """Full or smoke dry-run: writes all six artifacts under run_dir.

    NOTE: Heavy imports (torch, matplotlib) happen here only — never at
    module import time. This function is reachable by both --smoke-mode
    and the default full path, but T5.2 closure does NOT execute it on the
    login node.
    """
    run_dir.mkdir(parents=True, exist_ok=True)

    seed = int(seed_override if seed_override is not None else cfg.get("seed", 1234))
    cfg_steps = int(cfg["training"]["steps"])
    if max_steps_override is not None:
        steps_total = int(max_steps_override)
    elif smoke:
        steps_total = min(cfg_steps, 5)
    else:
        steps_total = cfg_steps
    log_every = int(cfg["training"]["log_every_steps"])
    val_every = int(cfg["training"]["val_every_steps"])

    # Lazy torch import.
    try:
        import torch  # type: ignore
        from torch import nn  # type: ignore

        torch.manual_seed(seed)
        random.seed(seed)
        if cfg.get("torch_deterministic"):
            torch.use_deterministic_algorithms(False)  # placeholder; CPU-friendly
        device = torch.device("cpu")

        class PlaceholderEnhancer(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = nn.Conv1d(1, 1, kernel_size=1, bias=True)
                with torch.no_grad():
                    self.conv.weight.fill_(1.0)
                    self.conv.bias.fill_(0.0)

            def forward(self, x: "torch.Tensor") -> "torch.Tensor":  # noqa: F821
                return self.conv(x)

        model = PlaceholderEnhancer().to(device)
        opt = torch.optim.Adam(
            model.parameters(),
            lr=float(cfg["training"]["learning_rate"]),
        )
        loss_fn = nn.L1Loss()
        torch_available = True
    except Exception as exc:
        print(
            f"WARN: torch unavailable ({exc!r}); writing placeholder loss curve only.",
            file=sys.stderr,
        )
        torch_available = False
        model = None
        opt = None
        loss_fn = None
        device = None

    # Step loop.
    metric_rows: list[dict] = []
    train_steps: list[int] = []
    train_losses: list[float] = []
    val_steps: list[int] = []
    val_wers: list[float] = []

    rng_data = random.Random(seed)
    batch_size = int(cfg["training"]["batch_size"])
    for step in range(1, steps_total + 1):
        if torch_available:
            x = torch.randn(batch_size, 1, 16, generator=torch.Generator().manual_seed(seed + step))
            y = x.clone()
            yhat = model(x)
            loss = loss_fn(yhat, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_val = float(loss.detach().cpu().item())
        else:
            loss_val = 1.0 / (1 + step) + 0.01 * rng_data.random()
        if step % log_every == 0 or step == steps_total:
            train_steps.append(step)
            train_losses.append(loss_val)
            metric_rows.append(
                {
                    "step": step,
                    "phase": "train",
                    "loss": f"{loss_val:.6f}",
                    "wer": "",
                    "word_accuracy": "",
                    "note": "placeholder_no_whisper",
                }
            )
        if step % val_every == 0 or step == steps_total:
            placeholder_wer = 0.5  # explicit placeholder; no Whisper run.
            val_steps.append(step)
            val_wers.append(placeholder_wer)
            metric_rows.append(
                {
                    "step": step,
                    "phase": "val",
                    "loss": "",
                    "wer": f"{placeholder_wer:.6f}",
                    "word_accuracy": f"{word_accuracy(placeholder_wer):.6f}",
                    "note": "placeholder_no_whisper",
                }
            )

    runtime_meta = {
        "run_id": run_id,
        "slurm_job_id": slurm_job_id,
        "git_commit": _resolve_git_value("GIT_COMMIT_AT_RUN", "rev-parse", "HEAD"),
        "branch": _resolve_git_value(
            "GIT_BRANCH_AT_RUN", "rev-parse", "--abbrev-ref", "HEAD"
        ),
        "config_path": str(config_path),
        "dataset_version": cfg.get("dataset_version"),
        "degradation_version": DEGRADATION_VERSION,
        "metrics_version": METRICS_VERSION,
        "enhancer_version": ENHANCER_VERSION,
        "output_path": str(run_dir),
        "start_time": _now_iso(),
        "smoke_mode": bool(smoke),
        "torch_available": bool(torch_available),
        "steps_executed": steps_total,
    }

    config_snapshot = run_dir / "config.yaml"
    metrics_csv = run_dir / "metrics.csv"
    wer_csv = run_dir / "wer_by_degradation.csv"
    loss_png = run_dir / "loss_curve.png"
    val_png = run_dir / "val_wer_curve.png"
    summary_md = run_dir / "run_summary.md"

    _write_config_snapshot(config_snapshot, config_text, runtime_meta)
    _write_metrics_csv(metrics_csv, metric_rows)

    family_rows = [
        {
            "family": fam,
            "count": 5,
            "mean_wer": f"{0.5:.6f}",
            "mean_word_accuracy": f"{word_accuracy(0.5):.6f}",
            "note": "placeholder_no_whisper",
        }
        for fam in EXPECTED_FAMILIES
    ]
    _write_wer_by_degradation_csv(wer_csv, family_rows)

    if no_plots:
        loss_png.write_bytes(_placeholder_png_bytes("loss_curve_no_plots"))
        val_png.write_bytes(_placeholder_png_bytes("val_wer_curve_no_plots"))
        loss_status = "placeholder"
        val_status = "placeholder"
    else:
        loss_status = _write_loss_curve(loss_png, train_steps, train_losses)
        val_status = _write_val_wer_curve(val_png, val_steps, val_wers)

    artifact_status = {
        "config.yaml": "complete",
        "metrics.csv": "complete",
        "wer_by_degradation.csv": "placeholder (no Whisper)",
        "loss_curve.png": loss_status,
        "val_wer_curve.png": val_status,
        "run_summary.md": "complete",
    }
    summary_metrics = {
        "final_train_loss": f"{train_losses[-1]:.6f}" if train_losses else "n/a",
        "val_wer_placeholder": f"{val_wers[-1]:.6f}" if val_wers else "n/a",
        "val_word_accuracy_placeholder": (
            f"{word_accuracy(val_wers[-1]):.6f}" if val_wers else "n/a"
        ),
    }
    known_failures: list[str] = []
    if not torch_available:
        known_failures.append(
            "torch unavailable at runtime; loss curve generated synthetically."
        )
    if loss_status == "placeholder":
        known_failures.append("loss_curve.png is a placeholder PNG (matplotlib unavailable).")
    if val_status == "placeholder":
        known_failures.append("val_wer_curve.png is a placeholder PNG (matplotlib unavailable).")

    runtime_meta["end_time"] = _now_iso()
    runtime_meta["summary_metrics"] = summary_metrics
    runtime_meta["known_failures"] = known_failures

    _write_run_summary(
        summary_md,
        cfg=cfg,
        runtime_meta=runtime_meta,
        artifact_status=artifact_status,
        summary_metrics=summary_metrics,
        known_failures=known_failures,
    )

    # Verify artifact contract.
    missing = [name for name in REQUIRED_ARTIFACTS if not (run_dir / name).exists()]
    if missing:
        return _blocker(f"artifact contract incomplete: missing {missing}")

    print(f"OK: dry-run wrote {len(REQUIRED_ARTIFACTS)} artifacts to {run_dir}")
    return 0


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="T5.2 dry-run training script "
        "(docs/plans/training_datamove1_plan.md §15)."
    )
    p.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to the dry-run YAML config (configs/training/dry_run.yaml).",
    )
    p.add_argument(
        "--validate-only",
        action="store_true",
        help="Run all guard checks and exit without creating a run dir.",
    )
    p.add_argument(
        "--smoke-mode",
        action="store_true",
        help="Tiny end-to-end run under <artifact_root>/_smoke/. Disabled in T5.2 "
        "unless explicitly authorized.",
    )
    p.add_argument(
        "--run-id",
        default=None,
        help="Override the auto-generated run ID.",
    )
    p.add_argument(
        "--artifact-root",
        type=Path,
        default=None,
        help="Override paths.artifact_root from the config.",
    )
    p.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override training.steps for local smoke checks.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override seed.",
    )
    p.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip matplotlib and write placeholder PNGs only.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))

    config_path: Path = args.config
    if not config_path.exists():
        return _blocker(f"--config not found: {config_path}")

    try:
        config_text = config_path.read_text(encoding="utf-8")
        cfg = yaml.safe_load(config_text)
    except yaml.YAMLError as exc:
        return _blocker(f"invalid YAML in {config_path}: {exc}")
    if not isinstance(cfg, dict):
        return _blocker(f"config root is not a mapping: {config_path}")

    if args.artifact_root is not None:
        cfg.setdefault("paths", {})["artifact_root"] = str(args.artifact_root)

    if args.validate_only:
        return cmd_validate_only(cfg)

    schema_errors = _validate_schema(cfg)
    if schema_errors:
        for e in schema_errors:
            print(f"BLOCKER: schema: {e}", file=sys.stderr)
        return 2

    slurm_job_id = os.environ.get("SLURM_JOB_ID", "local")
    if args.run_id:
        run_id = args.run_id
    elif slurm_job_id != "local":
        run_id = f"t5_3_dry_run_{slurm_job_id}"
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"t5_2_local_{ts}_{uuid.uuid4().hex[:8]}"

    guard_errors = _run_guards(
        cfg, slurm_job_id=slurm_job_id, run_id=run_id, smoke=args.smoke_mode
    )
    if guard_errors:
        for e in guard_errors:
            print(f"BLOCKER: {e}", file=sys.stderr)
        return 2

    run_dir = _resolve_run_dir(cfg, slurm_job_id, run_id, smoke=args.smoke_mode)

    return _run_dry_run(
        cfg,
        config_path=config_path,
        config_text=config_text,
        run_dir=run_dir,
        run_id=run_id,
        slurm_job_id=slurm_job_id,
        smoke=args.smoke_mode,
        max_steps_override=args.max_steps,
        seed_override=args.seed,
        no_plots=args.no_plots,
    )


if __name__ == "__main__":
    sys.exit(main())
