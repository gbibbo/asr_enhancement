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

# Make sibling helper modules (models.py, datasets.py, losses.py) importable
# under their flat names. They are imported lazily inside _run_training so that
# this module's import path stays torch-free (the --validate-only contract on
# the datamove1 login node depends on it).
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

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

# T6.2d: per-row note recorded in metrics.csv and wer_by_degradation.csv when
# the Whisper-enabled smoke validation path actually ran (as opposed to the
# T6.2b/T6.2c "no_whisper" placeholder note).
WHISPER_SMOKE_NOTE = "whisper_smoke_t6_2d"

EXPECTED_GUARD_KEYS = (
    "refuse_if_artifact_root_inside_repo",
    "refuse_if_reserved_demo_id_present",
    "refuse_if_dataset_version_mismatch_libs_common",
    "refuse_if_degradation_version_mismatch_libs_common",
    "refuse_if_metrics_version_mismatch_libs_common",
    "refuse_if_steps_gt",
    "refuse_if_run_dir_writable_inside_repo",
)

# T6.2b: training_split SHA verification (cfg.training_split block).
# Path/SHA pairs verified at --validate-only and at PairedDevCleanDataset
# construction. Keys mirror configs/training/full_training.yaml's
# training_split: block. The block is OPTIONAL — dry_run.yaml has no
# training_split: and the verification is skipped silently for that config.
TRAINING_SPLIT_PATH_SHA_PAIRS = (
    ("train_clean_manifest", "train_clean_manifest_sha256"),
    ("val_clean_manifest", "val_clean_manifest_sha256"),
    ("train_degraded_manifest", "train_degraded_manifest_sha256"),
    ("val_degraded_manifest", "val_degraded_manifest_sha256"),
)

# T6.2b: parameter budget for trainable architectures (asserted at training
# startup; the same bound is asserted by tests/training/test_architecture_registry.py).
TRAINABLE_PARAM_COUNT_MIN = 200_000
TRAINABLE_PARAM_COUNT_MAX = 1_000_000


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


def _select_whisper_smoke_subset(
    degraded_records: list[dict],
    per_family_cap: int,
) -> list[dict]:
    """T6.2d: deterministic, no-shuffle Whisper smoke subset.

    Iterates `degraded_records` in manifest order and takes the first
    `per_family_cap` rows of each `EXPECTED_FAMILIES` family, returning
    them in the canonical family order. Distinct from
    `_deterministic_val_subset` (which RNG-shuffles per family) — for the
    Whisper smoke we want stability across runs without depending on a
    seed.
    """
    by_family: dict[str, list[dict]] = {f: [] for f in EXPECTED_FAMILIES}
    for r in degraded_records:
        fam = r.get("family")
        if fam in by_family and len(by_family[fam]) < per_family_cap:
            by_family[fam].append(r)
    out: list[dict] = []
    for fam in EXPECTED_FAMILIES:
        out.extend(by_family[fam])
    return out


def _load_transcripts_by_utterance_id(jsonl_path: Path) -> dict[str, str]:
    """T6.2d: load utterance_id -> transcript mapping from a JSONL manifest.

    Used for the Whisper smoke to pull reference text from the val clean
    manifest by utterance_id. Records without a `transcript` field map to
    the empty string and are detected as missing by the smoke pre-flight.
    """
    out: dict[str, str] = {}
    for row in _read_jsonl(jsonl_path):
        uid = row.get("utterance_id")
        if not uid:
            continue
        tx = row.get("transcript")
        out[str(uid)] = str(tx) if tx else ""
    return out


def _resolve_training_device(
    cfg: dict,
    *,
    cuda_available: bool,
    expect_cuda: bool,
) -> tuple[str, list[str]]:
    """T6.2: resolve training device from cfg.hardware + ASR_EXPECT_CUDA env.

    Pure function: takes `cuda_available` and `expect_cuda` as inputs (no
    torch import here), so it can be unit-tested on the login node without
    importing torch. Returns ``(device_str, errors)`` where:
      * ``device_str`` is "cuda" or "cpu";
      * ``errors`` is a non-empty list when the resolution is a hard
        blocker (caller should `_blocker(...)` and exit non-zero).

    Hard guard: when ``expect_cuda`` is True (set by the GPU Slurm jobs via
    ``ASR_EXPECT_CUDA=1``), CUDA absence is a blocker even if the config
    block would otherwise permit a CPU fallback. This prevents a GPU job
    from silently degrading to CPU.

    Without ``expect_cuda``: ``hardware.target=gpu_required`` requires
    CUDA; ``hardware.target=gpu_preferred`` falls back to CPU when
    ``hardware.cpu_fallback`` is True; otherwise CPU.
    """
    hw = cfg.get("hardware") or {}
    target = str(hw.get("target", "cpu_only"))
    cpu_fallback = bool(hw.get("cpu_fallback", False))

    if expect_cuda and not cuda_available:
        return "cpu", [
            "ASR_EXPECT_CUDA=1 set but torch.cuda.is_available()=False inside Apptainer "
            f"(hardware.target={target!r})"
        ]

    if target == "gpu_required":
        if not cuda_available:
            return "cpu", [
                f"hardware.target=gpu_required but torch.cuda.is_available()=False"
            ]
        return "cuda", []

    if target == "gpu_preferred":
        if cuda_available:
            return "cuda", []
        if cpu_fallback:
            return "cpu", []
        return "cpu", [
            "hardware.target=gpu_preferred and torch.cuda.is_available()=False, "
            "but hardware.cpu_fallback=False"
        ]

    # cpu_only or unrecognised target: CPU.
    return "cpu", []


def _check_whisper_cli_consistency(
    cfg: dict, *, enable_whisper_val: bool
) -> list[str]:
    """T6.2d: cheap (no torch/whisper/torchaudio/matplotlib) check that the
    CLI flag and the config block agree on whether Whisper validation is
    enabled. Mismatches are blockers — silent disagreement is forbidden.
    """
    errors: list[str] = []
    vp = cfg.get("validation_policy") or {}
    config_flag = bool(vp.get("whisper_validation_enabled", False))
    if config_flag and not enable_whisper_val:
        errors.append(
            "config validation_policy.whisper_validation_enabled=true "
            "but --enable-whisper-val not passed on CLI"
        )
    if enable_whisper_val and not config_flag:
        errors.append(
            "--enable-whisper-val passed on CLI but config "
            "validation_policy.whisper_validation_enabled is false or absent"
        )
    return errors


def _check_whisper_smoke_pre_flight(cfg: dict) -> list[str]:
    """T6.2d: login-node-safe pre-flight (no torch/whisper/torchaudio
    /matplotlib) for the Whisper-enabled smoke. Verifies that:

      * `cfg.training_split.val_degraded_manifest` exists, parses as JSONL,
        and yields a 1-per-family subset covering all `EXPECTED_FAMILIES`;
      * `cfg.training_split.val_clean_manifest` exists, parses as JSONL,
        and contains a non-empty `transcript` for each selected smoke
        utterance_id (no silent skipping — even one missing transcript is
        a blocker).

    Returns an empty list on success, else a list of blocker strings.
    """
    errors: list[str] = []
    ts = cfg.get("training_split") or {}
    vp = cfg.get("validation_policy") or {}
    per_family_cap = int(vp.get("per_family_records_cap", 1))

    val_deg_path_s = ts.get("val_degraded_manifest")
    val_clean_path_s = ts.get("val_clean_manifest")
    if not val_deg_path_s:
        errors.append("training_split.val_degraded_manifest missing")
    if not val_clean_path_s:
        errors.append("training_split.val_clean_manifest missing")
    if errors:
        return errors

    val_deg_path = Path(val_deg_path_s)
    val_clean_path = Path(val_clean_path_s)
    if not val_deg_path.exists():
        return [f"val_degraded_manifest not found: {val_deg_path}"]
    if not val_clean_path.exists():
        return [f"val_clean_manifest not found: {val_clean_path}"]

    try:
        val_rows = _read_jsonl(val_deg_path)
    except json.JSONDecodeError as exc:
        return [f"val_degraded_manifest invalid JSONL: {exc}"]
    smoke_subset = _select_whisper_smoke_subset(val_rows, per_family_cap)
    families_found = {r.get("family") for r in smoke_subset}
    missing_families = [f for f in EXPECTED_FAMILIES if f not in families_found]
    if missing_families:
        return [
            f"whisper smoke subset missing families: {missing_families} "
            f"(per_family_records_cap={per_family_cap})"
        ]

    try:
        transcripts = _load_transcripts_by_utterance_id(val_clean_path)
    except json.JSONDecodeError as exc:
        return [f"val_clean_manifest invalid JSONL: {exc}"]

    missing_tx = [
        r.get("utterance_id")
        for r in smoke_subset
        if not (transcripts.get(str(r.get("utterance_id"))) or "").strip()
    ]
    if missing_tx:
        return [f"whisper smoke records missing transcript: {missing_tx}"]
    return []


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
# T6.2b: training_split SHA verification (login-node, no torch).
# -----------------------------------------------------------------------------
def _verify_training_split_shas(cfg: dict) -> list[str]:
    """If `cfg.training_split` is present, verify each of the four split
    manifests exists and that their SHA-256s match the values declared in
    the config. Returns a list of error strings (empty on success or when
    no `training_split:` block is present in `cfg`).
    """
    ts = cfg.get("training_split")
    if not isinstance(ts, dict):
        return []
    errors: list[str] = []
    for path_key, sha_key in TRAINING_SPLIT_PATH_SHA_PAIRS:
        path_val = ts.get(path_key)
        sha_val = ts.get(sha_key)
        if not path_val:
            errors.append(f"training_split.{path_key}: missing in config")
            continue
        if not sha_val:
            errors.append(f"training_split.{sha_key}: missing in config")
            continue
        p = Path(path_val)
        if not p.exists():
            errors.append(f"training_split.{path_key}: file not found: {p}")
            continue
        actual = _sha256_of_file(p)
        if actual != sha_val:
            errors.append(
                f"training_split.{path_key}: sha256 mismatch: "
                f"expected={sha_val} actual={actual} path={p}"
            )
    return errors


# -----------------------------------------------------------------------------
# validate-only path
# -----------------------------------------------------------------------------
def cmd_validate_only(cfg: dict, *, enable_whisper_val: bool = False) -> int:
    """Strict pre-flight on datamove1. No run dir created.

    `enable_whisper_val` (T6.2d) reflects the CLI flag. When set, this
    function additionally enforces config/CLI agreement and runs a
    login-node-safe Whisper-smoke pre-flight (manifest parse, family
    coverage, transcript presence) without importing torch, whisper,
    torchaudio, or matplotlib.
    """
    consistency_errors = _check_whisper_cli_consistency(
        cfg, enable_whisper_val=enable_whisper_val
    )
    if consistency_errors:
        for e in consistency_errors:
            print(f"BLOCKER: whisper-cli-consistency: {e}", file=sys.stderr)
        return 2

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

    # T6.2b: also verify the four training_split manifests when the cfg has
    # the block (full_training.yaml). dry_run.yaml has no training_split:
    # block, so this is silent on the dry-run path.
    ts_errors = _verify_training_split_shas(cfg)
    if ts_errors:
        for e in ts_errors:
            print(f"BLOCKER: {e}", file=sys.stderr)
        return 2
    ts = cfg.get("training_split")
    if isinstance(ts, dict):
        ts_version = cfg.get("training_split_version") or "unknown"
        print(
            "OK: training_split verified "
            f"(version={ts_version} "
            f"train_clean={ts.get('train_clean_records')} "
            f"val_clean={ts.get('val_clean_records')} "
            f"train_degraded={ts.get('train_degraded_records')} "
            f"val_degraded={ts.get('val_degraded_records')} "
            f"all_sha_ok=True)"
        )

    # T6.2d: Whisper smoke pre-flight runs only when the CLI flag is set
    # AND the config block agrees (the consistency check above already
    # ensures that). This block remains login-node-safe (no torch/whisper).
    if enable_whisper_val:
        smoke_errors = _check_whisper_smoke_pre_flight(cfg)
        if smoke_errors:
            for e in smoke_errors:
                print(f"BLOCKER: whisper-smoke-pre-flight: {e}", file=sys.stderr)
            return 2
        vp = cfg.get("validation_policy") or {}
        per_family_cap = int(vp.get("per_family_records_cap", 1))
        print(
            "OK: whisper-smoke pre-flight verified "
            f"(per_family_records_cap={per_family_cap} "
            f"families={len(EXPECTED_FAMILIES)} "
            f"transcripts_present=True)"
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
    path: Path,
    val_steps: list[int],
    val_wers: list[float],
    *,
    whisper_enabled: bool = False,
) -> str:
    """Write the val WER curve PNG. Returns 'complete' or 'placeholder'.

    `whisper_enabled=True` (T6.2d) switches the y-axis label and title to
    real Whisper-smoke wording; the values plotted are then expected to be
    actual WER values, not validation losses. With `whisper_enabled=False`
    the legacy placeholder/no-Whisper wording is preserved (used by T5.3
    and T6.2c so those paths reproduce identically).
    """
    try:
        import matplotlib  # type: ignore

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(val_steps, val_wers, marker="s", color="tab:red", linewidth=1.0)
        ax.set_xlabel("step")
        if whisper_enabled:
            ax.set_ylabel("val WER (Whisper smoke)")
            ax.set_title("Val WER curve (Whisper smoke)")
        else:
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
    whisper_enabled: bool = False,
) -> None:
    lines: list[str] = []
    if whisper_enabled:
        lines.append("# T6.2d Whisper-enabled CPU smoke validation run summary\n")
        lines.append(
            "Status: Whisper-enabled CPU smoke validation. Not full training. "
            "Not T6.2 closure.\n"
        )
    else:
        lines.append("# Dry-run training run summary\n")
        lines.append(
            "Status: dry-run artifact contract proof. Not a training result.\n"
        )
    lines.append("## Reproducibility metadata\n")
    summary_keys: tuple[str, ...] = (
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
    )
    if whisper_enabled:
        summary_keys = summary_keys + (
            "whisper_validation_enabled",
            "whisper_model",
            "whisper_version",
        )
    for key in summary_keys:
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
    if whisper_enabled:
        asr_block = cfg.get("asr") or {}
        decode_options = asr_block.get("decode_options") or {}
        vp = cfg.get("validation_policy") or {}
        per_family_cap = vp.get("per_family_records_cap")
        lines.append(
            "- This run is the **T6.2d Whisper-enabled CPU smoke validation**, "
            "not full training. WER and Word Accuracy values recorded here are "
            "real Whisper smoke values produced on a tiny subset, not "
            "convergence evidence. Production WER is the responsibility of "
            "T6.3+."
        )
        lines.append(
            f"- Whisper validation ran on cropped 4-second val windows "
            f"(reusing the existing val DataLoader output), "
            f"{per_family_cap} record per family across "
            f"{len(EXPECTED_FAMILIES)} families "
            f"({', '.join(EXPECTED_FAMILIES)})."
        )
        lines.append(
            f"- ASR: framework=`{asr_block.get('framework')}`, "
            f"model=`{asr_block.get('model')}`, "
            f"whisper_version=`{asr_block.get('whisper_version')}`."
        )
        if decode_options:
            opts = ", ".join(f"{k}={v}" for k, v in sorted(decode_options.items()))
            lines.append(f"- Decode options: {opts}.")
        lines.append(
            f"- Selected utterance_ids: "
            f"`{runtime_meta.get('selected_utterance_ids')}`; "
            f"selected families: `{runtime_meta.get('selected_families')}`; "
            f"missing_transcript_count: "
            f"`{runtime_meta.get('missing_transcript_count')}`."
        )
        lines.append(
            f"- Temporary enhanced WAVs written: "
            f"`{runtime_meta.get('temp_wavs_written')}`; "
            f"Whisper transcriptions completed: "
            f"`{runtime_meta.get('whisper_transcriptions_completed')}`; "
            f"temp_dir_cleaned: `{runtime_meta.get('temp_dir_cleaned')}`."
        )
    else:
        lines.append(
            "- WER and Word Accuracy values are PLACEHOLDERS. Whisper is not run "
            "during T5.2/T5.3 (Phase 5 dry-run); the artifact contract is the "
            "gate, not convergence."
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
# T6.2b: checkpoint save/load helpers (lazy torch import).
# -----------------------------------------------------------------------------
def save_checkpoint(
    *,
    path: Path,
    model: "object",
    optimizer: "object | None",
    scheduler: "object | None",
    step: int,
    cfg: dict,
    config_path: Path,
    config_sha256: str,
    run_id: str,
    slurm_job_id: str,
    parameter_count: int,
) -> Path:
    """Atomically write a checkpoint .pt file containing model state +
    metadata to `path`. Imports torch lazily."""
    import numpy as np  # type: ignore
    import torch  # type: ignore

    payload = {
        "step": int(step),
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict() if optimizer is not None else None,
        "scheduler_state_dict": (
            scheduler.state_dict()
            if scheduler is not None and hasattr(scheduler, "state_dict")
            else None
        ),
        "rng": {
            "torch": torch.get_rng_state(),
            "numpy": np.random.get_state(),
            "python": random.getstate(),
        },
        "config_path": str(config_path),
        "config_sha256": config_sha256,
        "dataset_version": cfg.get("dataset_version"),
        "degradation_version": cfg.get("degradation_version"),
        "metrics_version": cfg.get("metrics_version"),
        "training_split_version": cfg.get("training_split_version"),
        "model_architecture": (cfg.get("model") or {}).get("architecture"),
        "model_params": (cfg.get("model") or {}).get("params") or {},
        "parameter_count": int(parameter_count),
        "git_commit": _resolve_git_value("GIT_COMMIT_AT_RUN", "rev-parse", "HEAD"),
        "branch": _resolve_git_value("GIT_BRANCH_AT_RUN", "rev-parse", "--abbrev-ref", "HEAD"),
        "run_id": run_id,
        "slurm_job_id": slurm_job_id,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)
    return path


def load_checkpoint(
    path: Path,
    *,
    model: "object | None" = None,
    optimizer: "object | None" = None,
    scheduler: "object | None" = None,
    map_location: str = "cpu",
    restore_rng: bool = True,
) -> dict:
    """Load a checkpoint; optionally restore model/optimizer/scheduler/RNG.
    Returns the full payload dict. Imports torch lazily."""
    import numpy as np  # type: ignore
    import torch  # type: ignore

    payload = torch.load(str(path), map_location=map_location)
    if model is not None and payload.get("model_state_dict") is not None:
        model.load_state_dict(payload["model_state_dict"])
    if optimizer is not None and payload.get("optimizer_state_dict") is not None:
        optimizer.load_state_dict(payload["optimizer_state_dict"])
    if (
        scheduler is not None
        and payload.get("scheduler_state_dict") is not None
        and hasattr(scheduler, "load_state_dict")
    ):
        scheduler.load_state_dict(payload["scheduler_state_dict"])
    if restore_rng:
        rng = payload.get("rng") or {}
        if "torch" in rng:
            try:
                torch.set_rng_state(rng["torch"])
            except Exception:
                pass
        if "numpy" in rng:
            try:
                np.random.set_state(rng["numpy"])
            except Exception:
                pass
        if "python" in rng:
            try:
                random.setstate(rng["python"])
            except Exception:
                pass
    return payload


def _prune_old_checkpoints(checkpoints_dir: Path, keep_last_n: int) -> None:
    """Delete `checkpoint_step_*.pt` beyond the most recent `keep_last_n`."""
    if keep_last_n <= 0:
        return
    items = sorted(checkpoints_dir.glob("checkpoint_step_*.pt"))
    if len(items) <= keep_last_n:
        return
    for old in items[: len(items) - keep_last_n]:
        try:
            old.unlink()
        except OSError:
            pass


CHECKPOINT_METADATA_KEYS = (
    "step",
    "model_state_dict",
    "config_path",
    "config_sha256",
    "dataset_version",
    "degradation_version",
    "metrics_version",
    "training_split_version",
    "model_architecture",
    "model_params",
    "parameter_count",
    "git_commit",
    "branch",
    "run_id",
    "slurm_job_id",
)


# -----------------------------------------------------------------------------
# T6.2b: real training loop scaffold (wired, NOT exercised by --validate-only).
# -----------------------------------------------------------------------------
def _maybe_run_whisper_validation(
    *,
    enable_whisper_val: bool,
    cfg: dict | None = None,
    model: Any = None,
    sample_rate: int = 16000,
    run_dir: Path | None = None,
) -> dict[str, Any]:
    """T6.2d: real Whisper-enabled smoke validation on a 1-per-family subset.

    With `enable_whisper_val=False`, returns immediately with `ran=False`
    and no other side effects (T6.2b/T6.2c contract preserved).

    With `enable_whisper_val=True`, runs:
      1. select 1 record per `EXPECTED_FAMILIES` family from the val
         degraded manifest (deterministic, no shuffle);
      2. load reference transcripts from the val clean manifest by
         utterance_id; missing transcripts ⇒ raise (no silent skip);
      3. for each selected record, load the degraded WAV, take a centered
         4-second crop matching the val DataLoader, run the enhancer,
         write the enhanced cropped WAV to `run_dir/val_enhanced_tmp/`;
      4. transcribe each tmp WAV with openai-whisper (CPU, cache under
         `$ASR_CACHE_ROOT/whisper`) using the cfg.asr decode options;
      5. compute per-utterance WER via libs.audio.metrics, aggregate per
         family, populate the return dict;
      6. delete the tmp dir in a `finally` block — the six-artifact
         contract must not gain a seventh artifact, so survival metadata
         (counts, ids, families) is recorded in the returned dict and
         propagated to the runtime block of config.yaml plus the
         external verify JSON.

    Heavy imports (whisper, torch, torchaudio, scipy) are lazy.
    """
    result: dict[str, Any] = {
        "ran": False,
        "family_rows": [],
        "mean_wer": None,
        "mean_word_accuracy": None,
        "selected_utterance_ids": [],
        "selected_families": [],
        "missing_transcript_count": 0,
        "temp_wavs_written": 0,
        "whisper_transcriptions_completed": 0,
        "temp_dir_cleaned": False,
        "whisper_model": None,
        "whisper_version": None,
    }
    if not enable_whisper_val:
        return result
    if cfg is None or model is None or run_dir is None:
        raise RuntimeError(
            "_maybe_run_whisper_validation: cfg/model/run_dir required when "
            "enable_whisper_val is True"
        )

    import importlib
    import importlib.metadata
    import shutil

    import torch  # type: ignore

    try:
        import whisper  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"whisper import failed: {exc!r}") from exc

    whisper_version = getattr(whisper, "__version__", None)
    if whisper_version is None:
        try:
            whisper_version = importlib.metadata.version("openai-whisper")
        except Exception:
            whisper_version = "unknown"

    asr_block = cfg.get("asr") or {}
    whisper_model_name = str(asr_block.get("model") or "base.en")
    decode_opts_cfg = asr_block.get("decode_options") or {}
    decode_kwargs: dict[str, Any] = {
        "language": str(decode_opts_cfg.get("language", "en")),
        "task": str(decode_opts_cfg.get("task", "transcribe")),
        "beam_size": int(decode_opts_cfg.get("beam_size", 1)),
        "temperature": float(decode_opts_cfg.get("temperature", 0.0)),
        "fp16": False,
    }

    cache_root_s = os.environ.get("ASR_CACHE_ROOT")
    if not cache_root_s:
        raise RuntimeError(
            "ASR_CACHE_ROOT not set; required for whisper cache resolution"
        )
    download_root = str(Path(cache_root_s) / "whisper")

    ts = cfg.get("training_split") or {}
    vp = cfg.get("validation_policy") or {}
    per_family_cap = int(vp.get("per_family_records_cap", 1))

    val_deg_path = Path(ts["val_degraded_manifest"])
    val_clean_path = Path(ts["val_clean_manifest"])
    val_rows = _read_jsonl(val_deg_path)
    smoke_subset = _select_whisper_smoke_subset(val_rows, per_family_cap)
    families_found = {r.get("family") for r in smoke_subset}
    missing_families = [f for f in EXPECTED_FAMILIES if f not in families_found]
    if missing_families:
        raise RuntimeError(
            f"whisper smoke subset missing families: {missing_families}"
        )

    transcripts = _load_transcripts_by_utterance_id(val_clean_path)
    missing_tx = [
        r.get("utterance_id")
        for r in smoke_subset
        if not (transcripts.get(str(r.get("utterance_id"))) or "").strip()
    ]
    if missing_tx:
        raise RuntimeError(
            f"whisper smoke records missing transcript: {missing_tx}"
        )

    selected_uids = [str(r["utterance_id"]) for r in smoke_subset]
    selected_families = [str(r["family"]) for r in smoke_subset]
    result["selected_utterance_ids"] = selected_uids
    result["selected_families"] = selected_families
    result["missing_transcript_count"] = 0
    result["whisper_model"] = whisper_model_name
    result["whisper_version"] = whisper_version

    tmp_dir = run_dir / "val_enhanced_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    whisper_model = whisper.load_model(
        whisper_model_name,
        device="cpu",
        download_root=download_root,
    )

    def _load_mono(path: Path, target_sr: int) -> Any:
        try:
            import torchaudio  # type: ignore

            wav, sr = torchaudio.load(str(path))
            if wav.dim() == 2:
                wav = wav.mean(dim=0)
            if int(sr) != target_sr:
                raise RuntimeError(
                    f"sample_rate mismatch: {sr} vs {target_sr} for {path}"
                )
            return wav.contiguous().float()
        except Exception:
            import numpy as _np  # type: ignore
            import scipy.io.wavfile as _wavfile  # type: ignore

            sr, data = _wavfile.read(str(path))
            if int(sr) != target_sr:
                raise RuntimeError(
                    f"sample_rate mismatch: {sr} vs {target_sr} for {path}"
                )
            if data.dtype.kind == "i":
                max_v = float(2 ** (8 * data.dtype.itemsize - 1))
                arr = data.astype(_np.float32) / max_v
            elif data.dtype.kind == "u":
                max_v = float(2 ** (8 * data.dtype.itemsize))
                arr = (data.astype(_np.float32) - max_v / 2) / (max_v / 2)
            else:
                arr = data.astype(_np.float32)
            if arr.ndim == 2:
                arr = arr.mean(axis=1)
            return torch.from_numpy(arr).float()

    def _save_wav(path: Path, samples: Any, target_sr: int) -> None:
        import numpy as _np  # type: ignore
        import scipy.io.wavfile as _wavfile  # type: ignore

        if hasattr(samples, "detach"):
            samples = samples.detach().cpu().numpy()
        arr = _np.asarray(samples, dtype=_np.float32)
        _wavfile.write(str(path), int(target_sr), arr)

    family_wers: dict[str, list[float]] = {f: [] for f in EXPECTED_FAMILIES}
    n_written = 0
    n_transcribed = 0
    temp_dir_cleaned = False
    crop_len = 4 * int(sample_rate)  # PairedDevCleanDataset's val crop length
    try:
        for rec in smoke_subset:
            uid = str(rec["utterance_id"])
            family = str(rec["family"])
            degraded_path = Path(rec["degraded_audio_path"])

            wav = _load_mono(degraded_path, int(sample_rate))
            total = int(wav.shape[-1])
            if total < crop_len:
                pad = crop_len - total
                wav = torch.nn.functional.pad(wav, (0, pad))
            else:
                offset = (total - crop_len) // 2
                wav = wav[offset : offset + crop_len]

            # Enhancer runs on whatever device the model is on (T6.2 device
            # selection). Whisper is loaded with device="cpu" above, so the
            # enhanced waveform is moved back to CPU before the tmp WAV save.
            model_device = next(model.parameters()).device
            x = wav.view(1, 1, -1).float().to(model_device, non_blocking=True)
            with torch.no_grad():
                yhat = model(x)
            enhanced = yhat.view(-1).clamp(-1.0, 1.0).detach().cpu()

            tmp_wav = tmp_dir / f"{uid}__{family}.wav"
            _save_wav(tmp_wav, enhanced, int(sample_rate))
            n_written += 1

            transcribe_result = whisper_model.transcribe(
                str(tmp_wav), **decode_kwargs
            )
            n_transcribed += 1
            hypothesis = str(transcribe_result.get("text") or "")
            reference = transcripts.get(uid, "")
            wer = float(word_error_rate(reference, hypothesis))
            family_wers[family].append(wer)
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=False)
            temp_dir_cleaned = not tmp_dir.exists()
        except Exception:
            temp_dir_cleaned = False

    family_rows: list[dict] = []
    for fam in EXPECTED_FAMILIES:
        wers = family_wers[fam]
        if not wers:
            family_rows.append(
                {
                    "family": fam,
                    "count": 0,
                    "mean_wer": "",
                    "mean_word_accuracy": "",
                    "note": WHISPER_SMOKE_NOTE,
                }
            )
            continue
        mean_wer = sum(wers) / len(wers)
        mean_wa = float(word_accuracy(mean_wer))
        family_rows.append(
            {
                "family": fam,
                "count": len(wers),
                "mean_wer": f"{mean_wer:.6f}",
                "mean_word_accuracy": f"{mean_wa:.6f}",
                "note": WHISPER_SMOKE_NOTE,
            }
        )

    flat_wers = [w for fam in EXPECTED_FAMILIES for w in family_wers[fam]]
    overall_wer = sum(flat_wers) / len(flat_wers) if flat_wers else None
    overall_wa = float(word_accuracy(overall_wer)) if overall_wer is not None else None

    result.update(
        {
            "ran": True,
            "family_rows": family_rows,
            "mean_wer": overall_wer,
            "mean_word_accuracy": overall_wa,
            "temp_wavs_written": n_written,
            "whisper_transcriptions_completed": n_transcribed,
            "temp_dir_cleaned": temp_dir_cleaned,
        }
    )
    return result


def _run_training(
    cfg: dict,
    *,
    config_path: Path,
    config_text: str,
    run_dir: Path,
    run_id: str,
    slurm_job_id: str,
    resume_path: Path | None,
    force_fresh: bool,
    enable_whisper_val: bool,
    max_steps_override: int | None,
    seed_override: int | None,
    no_plots: bool,
) -> int:
    """Real `spectral_unet_small_v1` training loop.

    Wired by main() for `cfg.model.architecture` other than
    `placeholder_for_t5_2_or_later`. T6.2b does NOT execute this path —
    closure depends on `--validate-only` and pytest only. The function is
    written so T6.2c (CPU micro-validation Slurm) can call it without
    further code changes.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir = run_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    latest_path = checkpoints_dir / "latest.pt"
    if resume_path is None and not force_fresh:
        existing = list(checkpoints_dir.glob("checkpoint_step_*.pt"))
        if existing or latest_path.exists():
            return _blocker(
                f"checkpoints_dir already populated: {checkpoints_dir}. "
                f"Pass --resume <path> to resume or --force-fresh to start over."
            )

    # Lazy heavy imports.
    import numpy as np  # type: ignore  # noqa: F401  (used by RNG restore)
    import torch  # type: ignore
    from torch.utils.data import DataLoader  # type: ignore

    from datasets import PairedDevCleanDataset  # type: ignore  (sibling module)
    from losses import CompositeReconstructionLoss  # type: ignore
    from models import build_model, parameter_count as _param_count  # type: ignore

    seed = int(seed_override if seed_override is not None else cfg.get("seed", 1234))
    torch.manual_seed(seed)
    random.seed(seed)

    arch = (cfg.get("model") or {}).get("architecture") or ""
    params = (cfg.get("model") or {}).get("params") or {}
    model = build_model(arch, params)
    p_count = _param_count(model)
    if not (TRAINABLE_PARAM_COUNT_MIN <= p_count <= TRAINABLE_PARAM_COUNT_MAX):
        return _blocker(
            f"parameter_count {p_count} outside "
            f"[{TRAINABLE_PARAM_COUNT_MIN}, {TRAINABLE_PARAM_COUNT_MAX}] "
            f"for architecture {arch!r}"
        )

    # T6.2: device selection. The legacy CPU-only behaviour is preserved by
    # `hardware.target=cpu_only` (T6.2c/T6.2d smokes). The GPU Slurm jobs
    # (T6.2 preflight + full training) set `ASR_EXPECT_CUDA=1` to make CUDA
    # absence a hard blocker, regardless of `hardware.cpu_fallback`.
    expect_cuda = os.environ.get("ASR_EXPECT_CUDA") == "1"
    cuda_available = bool(torch.cuda.is_available())
    device_str, device_errors = _resolve_training_device(
        cfg, cuda_available=cuda_available, expect_cuda=expect_cuda
    )
    if device_errors:
        for e in device_errors:
            print(f"BLOCKER: device-selection: {e}", file=sys.stderr)
        return 2
    device = torch.device(device_str)
    model = model.to(device)
    hardware_target = str((cfg.get("hardware") or {}).get("target", "cpu_only"))

    ts = cfg.get("training_split")
    if not isinstance(ts, dict):
        return _blocker("cfg.training_split missing; T6.2a split required for training")

    sample_rate = int(params.get("sample_rate", 16000))
    train_ds = PairedDevCleanDataset(
        clean_manifest=Path(ts["train_clean_manifest"]),
        degraded_manifest=Path(ts["train_degraded_manifest"]),
        clean_sha256=ts["train_clean_manifest_sha256"],
        degraded_sha256=ts["train_degraded_manifest_sha256"],
        mode="train",
        sample_rate=sample_rate,
        seed=seed,
    )
    val_ds = PairedDevCleanDataset(
        clean_manifest=Path(ts["val_clean_manifest"]),
        degraded_manifest=Path(ts["val_degraded_manifest"]),
        clean_sha256=ts["val_clean_manifest_sha256"],
        degraded_sha256=ts["val_degraded_manifest_sha256"],
        mode="val",
        sample_rate=sample_rate,
        seed=seed,
    )

    hw = cfg.get("hardware") or {}
    bs = int(cfg["training"]["batch_size"])
    train_loader = DataLoader(
        train_ds,
        batch_size=bs,
        shuffle=True,
        num_workers=int(hw.get("num_workers", 0)),
        pin_memory=bool(hw.get("pin_memory", False)),
        drop_last=True,
        collate_fn=PairedDevCleanDataset.collate,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=bs,
        shuffle=False,
        num_workers=int(hw.get("num_workers", 0)),
        pin_memory=bool(hw.get("pin_memory", False)),
        drop_last=False,
        collate_fn=PairedDevCleanDataset.collate,
    )

    loss_fn = CompositeReconstructionLoss(
        l1_log_mag_w=1.0,
        mrstft_w=0.5,
        n_fft=int(params.get("n_fft", 512)),
        hop_length=int(params.get("hop_length", 128)),
        win_length=int(params.get("win_length", 512)),
    )
    opt = torch.optim.Adam(
        model.parameters(),
        lr=float(cfg["training"]["learning_rate"]),
    )

    config_sha = _sha256_of_text(config_text)
    start_step = 1
    if resume_path is not None:
        ck = load_checkpoint(resume_path, model=model, optimizer=opt)
        start_step = int(ck.get("step", 0)) + 1

    cfg_steps = int(cfg["training"]["steps"])
    steps_total = int(max_steps_override if max_steps_override is not None else cfg_steps)
    log_every = int(cfg["training"]["log_every_steps"])
    val_every = int(cfg["training"]["val_every_steps"])
    save_every = int(cfg["training"].get("save_every_steps", 1000))
    keep_last_n = int((cfg.get("checkpoint_policy") or {}).get("keep_last_n", 5))

    metric_rows: list[dict] = []
    train_steps_log: list[int] = []
    train_losses_log: list[float] = []
    val_steps_log: list[int] = []
    val_losses_log: list[float] = []
    val_wer_log: list[float] = []  # T6.2d: real WER values when whisper enabled
    whisper_result: dict[str, Any] = {"ran": False}

    runtime_meta: dict[str, Any] = {
        "run_id": run_id,
        "slurm_job_id": slurm_job_id,
        "git_commit": _resolve_git_value("GIT_COMMIT_AT_RUN", "rev-parse", "HEAD"),
        "branch": _resolve_git_value(
            "GIT_BRANCH_AT_RUN", "rev-parse", "--abbrev-ref", "HEAD"
        ),
        "config_path": str(config_path),
        "config_sha256": config_sha,
        "dataset_version": cfg.get("dataset_version"),
        "degradation_version": DEGRADATION_VERSION,
        "metrics_version": METRICS_VERSION,
        "enhancer_version": ENHANCER_VERSION,
        "output_path": str(run_dir),
        "start_time": _now_iso(),
        "torch_available": True,
        "architecture": arch,
        "parameter_count": p_count,
        "training_split_version": cfg.get("training_split_version"),
        "whisper_validation_enabled": bool(enable_whisper_val),
        "device": str(device),
        "torch_cuda_is_available": cuda_available,
        "hardware_target": hardware_target,
        "expected_cuda": expect_cuda,
        "gpu_used": str(device).startswith("cuda"),
    }

    train_iter = iter(train_loader)
    model.train()
    for step in range(start_step, steps_total + 1):
        try:
            batch = next(train_iter)
        except StopIteration:
            train_iter = iter(train_loader)
            batch = next(train_iter)
        clean = batch["clean"].to(device, non_blocking=True)
        degraded = batch["degraded"].to(device, non_blocking=True)
        opt.zero_grad()
        yhat = model(degraded)
        loss, _components = loss_fn(yhat, clean)
        loss.backward()
        opt.step()
        loss_val = float(loss.detach().cpu().item())
        if step % log_every == 0 or step == steps_total:
            train_steps_log.append(step)
            train_losses_log.append(loss_val)
            metric_rows.append(
                {
                    "step": step,
                    "phase": "train",
                    "loss": f"{loss_val:.6f}",
                    "wer": "",
                    "word_accuracy": "",
                    "note": "no_whisper_t6_2b",
                }
            )
        if step % val_every == 0 or step == steps_total:
            model.eval()
            total = 0.0
            n_batches = 0
            with torch.no_grad():
                for vb in val_loader:
                    v_clean = vb["clean"].to(device, non_blocking=True)
                    v_degraded = vb["degraded"].to(device, non_blocking=True)
                    vyhat = model(v_degraded)
                    vloss, _ = loss_fn(vyhat, v_clean)
                    total += float(vloss.item())
                    n_batches += 1
            val_loss = total / max(n_batches, 1)
            val_steps_log.append(step)
            val_losses_log.append(val_loss)
            val_row: dict[str, Any] = {
                "step": step,
                "phase": "val",
                "loss": f"{val_loss:.6f}",
                "wer": "",
                "word_accuracy": "",
                "note": "placeholder_no_whisper_t6_2b",
            }
            if enable_whisper_val:
                # T6.2d: real Whisper-enabled smoke validation. Errors are
                # not swallowed — a failure here is the point of the gate.
                whisper_result = _maybe_run_whisper_validation(
                    enable_whisper_val=True,
                    cfg=cfg,
                    model=model,
                    sample_rate=sample_rate,
                    run_dir=run_dir,
                )
                if whisper_result.get("ran"):
                    mw = whisper_result.get("mean_wer")
                    mwa = whisper_result.get("mean_word_accuracy")
                    if mw is not None:
                        val_row["wer"] = f"{float(mw):.6f}"
                        val_row["note"] = WHISPER_SMOKE_NOTE
                        val_wer_log.append(float(mw))
                    if mwa is not None:
                        val_row["word_accuracy"] = f"{float(mwa):.6f}"
            model.train()
            metric_rows.append(val_row)
        if step % save_every == 0 or step == steps_total:
            ckpt_path = checkpoints_dir / f"checkpoint_step_{step:07d}.pt"
            save_checkpoint(
                path=ckpt_path,
                model=model,
                optimizer=opt,
                scheduler=None,
                step=step,
                cfg=cfg,
                config_path=config_path,
                config_sha256=config_sha,
                run_id=run_id,
                slurm_job_id=slurm_job_id,
                parameter_count=p_count,
            )
            # latest.pt: copy bytes atomically (avoids torch.save reentrancy).
            tmp_latest = checkpoints_dir / "latest.pt.tmp"
            tmp_latest.write_bytes(ckpt_path.read_bytes())
            tmp_latest.replace(latest_path)
            _prune_old_checkpoints(checkpoints_dir, keep_last_n)

    runtime_meta["end_time"] = _now_iso()
    runtime_meta["steps_executed"] = steps_total

    whisper_ran = bool(whisper_result.get("ran"))
    if whisper_ran:
        # T6.2d: surface Whisper-smoke survival metadata into the runtime
        # block of config.yaml. No new artifact is added — the six-artifact
        # contract is preserved.
        runtime_meta["whisper_model"] = whisper_result.get("whisper_model")
        runtime_meta["whisper_version"] = whisper_result.get("whisper_version")
        runtime_meta["selected_utterance_ids"] = whisper_result.get(
            "selected_utterance_ids"
        )
        runtime_meta["selected_families"] = whisper_result.get("selected_families")
        runtime_meta["temp_wavs_written"] = whisper_result.get("temp_wavs_written")
        runtime_meta["whisper_transcriptions_completed"] = whisper_result.get(
            "whisper_transcriptions_completed"
        )
        runtime_meta["temp_dir_cleaned"] = whisper_result.get("temp_dir_cleaned")
        runtime_meta["missing_transcript_count"] = whisper_result.get(
            "missing_transcript_count"
        )
        runtime_meta["whisper_mean_wer"] = whisper_result.get("mean_wer")
        runtime_meta["whisper_mean_word_accuracy"] = whisper_result.get(
            "mean_word_accuracy"
        )

    # Emit the same artifact contract the dry-run path produces (T5.2/T6.1).
    config_snapshot = run_dir / "config.yaml"
    metrics_csv = run_dir / "metrics.csv"
    wer_csv = run_dir / "wer_by_degradation.csv"
    loss_png = run_dir / "loss_curve.png"
    val_png = run_dir / "val_wer_curve.png"
    summary_md = run_dir / "run_summary.md"

    _write_config_snapshot(config_snapshot, config_text, runtime_meta)
    _write_metrics_csv(metrics_csv, metric_rows)

    if whisper_ran and whisper_result.get("family_rows"):
        family_rows = whisper_result["family_rows"]
        wer_csv_status = "complete (whisper smoke)"
    else:
        family_rows = [
            {
                "family": fam,
                "count": 0,
                "mean_wer": "",
                "mean_word_accuracy": "",
                "note": "placeholder_no_whisper_t6_2b",
            }
            for fam in EXPECTED_FAMILIES
        ]
        wer_csv_status = "placeholder (no Whisper)"
    _write_wer_by_degradation_csv(wer_csv, family_rows)

    if no_plots:
        loss_png.write_bytes(_placeholder_png_bytes("loss_curve_no_plots"))
        val_png.write_bytes(_placeholder_png_bytes("val_wer_curve_no_plots"))
        loss_status = "placeholder"
        val_status = "placeholder"
    else:
        loss_status = _write_loss_curve(loss_png, train_steps_log, train_losses_log)
        if whisper_ran and val_wer_log:
            # Plot real WER values; align step labels with the steps that ran
            # whisper validation (the tail of val_steps_log).
            wer_steps = val_steps_log[-len(val_wer_log) :]
            val_status = _write_val_wer_curve(
                val_png, wer_steps, val_wer_log, whisper_enabled=True
            )
        else:
            val_status = _write_val_wer_curve(
                val_png,
                val_steps_log,
                val_losses_log,
                whisper_enabled=False,
            )

    artifact_status = {
        "config.yaml": "complete",
        "metrics.csv": "complete",
        "wer_by_degradation.csv": wer_csv_status,
        "loss_curve.png": loss_status,
        "val_wer_curve.png": val_status,
        "run_summary.md": "complete",
    }
    summary_metrics: dict[str, Any] = {
        "final_train_loss": (
            f"{train_losses_log[-1]:.6f}" if train_losses_log else "n/a"
        ),
        "final_val_loss": (
            f"{val_losses_log[-1]:.6f}" if val_losses_log else "n/a"
        ),
        "parameter_count": p_count,
        "architecture": arch,
        "training_split_version": cfg.get("training_split_version"),
    }
    if whisper_ran:
        mw = whisper_result.get("mean_wer")
        mwa = whisper_result.get("mean_word_accuracy")
        summary_metrics["whisper_mean_wer"] = (
            f"{float(mw):.6f}" if mw is not None else "n/a"
        )
        summary_metrics["whisper_mean_word_accuracy"] = (
            f"{float(mwa):.6f}" if mwa is not None else "n/a"
        )
        summary_metrics["whisper_model"] = whisper_result.get("whisper_model")
        summary_metrics["whisper_version"] = whisper_result.get("whisper_version")
    runtime_meta["summary_metrics"] = summary_metrics
    runtime_meta["known_failures"] = []

    _write_run_summary(
        summary_md,
        cfg=cfg,
        runtime_meta=runtime_meta,
        artifact_status=artifact_status,
        summary_metrics=summary_metrics,
        known_failures=[],
        whisper_enabled=whisper_ran,
    )

    missing = [name for name in REQUIRED_ARTIFACTS if not (run_dir / name).exists()]
    if missing:
        return _blocker(f"artifact contract incomplete: missing {missing}")
    print(f"OK: training run wrote {len(REQUIRED_ARTIFACTS)} artifacts to {run_dir}")
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
    # T6.2b: real-architecture path flags. None of these are exercised in
    # T6.2b closure; they exist so T6.2c can call the same script.
    p.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Path to a checkpoint .pt to resume training from.",
    )
    p.add_argument(
        "--force-fresh",
        action="store_true",
        help="Allow starting a fresh run when checkpoints already exist in run_dir.",
    )
    p.add_argument(
        "--enable-whisper-val",
        action="store_true",
        help="Enable openai-whisper validation passes (T6.2c gate; OFF in T6.2b).",
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
        return cmd_validate_only(
            cfg, enable_whisper_val=bool(args.enable_whisper_val)
        )

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

    # T6.2b: dispatch by cfg.model.architecture.
    # - "placeholder_for_t5_2_or_later" (dry_run.yaml) -> existing dry-run path
    # - any other registered architecture (e.g. "spectral_unet_small_v1" in
    #   full_training.yaml) -> _run_training. T6.2b does not exercise this
    #   branch; T6.2c (CPU micro-validation Slurm) does.
    arch = (cfg.get("model") or {}).get("architecture") or ""
    if str(arch).lower().startswith("placeholder"):
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
    return _run_training(
        cfg,
        config_path=config_path,
        config_text=config_text,
        run_dir=run_dir,
        run_id=run_id,
        slurm_job_id=slurm_job_id,
        resume_path=args.resume,
        force_fresh=bool(args.force_fresh),
        enable_whisper_val=bool(args.enable_whisper_val),
        max_steps_override=args.max_steps,
        seed_override=args.seed,
        no_plots=args.no_plots,
    )


if __name__ == "__main__":
    sys.exit(main())
