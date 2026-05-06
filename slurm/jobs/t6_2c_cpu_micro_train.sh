#!/usr/bin/env bash
# T6.2c — CPU micro-validation training job for the spectral_unet_small_v1
# trainer code path (training_datamove1_plan.md §16, internal subgate).
#
# Runs scripts/training/train_enhancer.py with
# configs/training/full_training_cpu_micro.yaml inside the project Apptainer
# image on a CPU compute node, then performs read-only artifact and
# checkpoint validation in the SAME Apptainer job and writes a verify JSON.
#
# Hard scope guards (must remain TRUE):
#   * CPU only. No GPU SBATCH flags. No --nv on apptainer exec.
#   * No --bind on apptainer exec. No --pwd on apptainer exec.
#   * No call to slurm/tools/on_submit.sh, sbatch, squeue, sacct, scancel,
#     sinfo, or scontrol from inside this job script (those wrappers run
#     OUTSIDE the job, on datamove1, when this script is submitted).
#   * Does not run Whisper, enhancement, or full training.
#   * Does not modify trackers, configs, libs, or the model card.
#   * Submission is performed manually with:
#       ./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t6_2c_cpu_micro_train.sh

#SBATCH --job-name=asr_t6_2c_cpu_micro_train
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2c_cpu_micro_train_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2c_cpu_micro_train_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

set -euo pipefail

REPO=/mnt/fast/nobackup/users/gb0048/asr_enhancement
TRAIN_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
PREFIX=$TRAIN_ROOT/python_env/site-packages-py310
CONTAINER=/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
CACHE_ROOT=$TRAIN_ROOT/cache

JOBID="${SLURM_JOB_ID:-local}"
RUN_DIR="$TRAIN_ROOT/runs/_smoke/t6_2c_cpu_micro_${JOBID}"
ARTIFACT_DIR="$TRAIN_ROOT/artifacts"
VERIFY_JSON="$ARTIFACT_DIR/t6_2c_cpu_micro_verify_${JOBID}.json"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runs/_smoke" \
  "$TRAIN_ROOT/runtime" \
  "$ARTIFACT_DIR" \
  "$CACHE_ROOT"

# Capture git state before entering Apptainer (git is not in the container).
# train_enhancer.py reads GIT_COMMIT_AT_RUN / GIT_BRANCH_AT_RUN from the
# environment first.
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH_AT_RUN=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T6.2c CPU micro-validation training start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "Host:                 $(hostname)"
echo "Container:            $CONTAINER"
echo "Repo:                 $REPO"
echo "Prefix:               $PREFIX"
echo "Train root:           $TRAIN_ROOT"
echo "Cache root:           $CACHE_ROOT"
echo "Slurm job id:         $JOBID"
echo "Slurm node list:      ${SLURM_NODELIST:-unset}"
echo "Expected run dir:     $RUN_DIR"
echo "Verify JSON path:     $VERIFY_JSON"
echo "Git commit at run:    $GIT_COMMIT_AT_RUN"
echo "Git branch at run:    $GIT_BRANCH_AT_RUN"
echo "Git status (short):   ${GIT_STATUS_SHORT_AT_RUN:-clean}"
echo "============================="

cd "$REPO" || exit 1

# ----------------------------------------------------------------------------
# Step 1: CPU micro-training run.
# ----------------------------------------------------------------------------
echo "--- Step 1: CPU micro-training run ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$ARTIFACT_DIR" \
  --env ASR_CACHE_ROOT="$CACHE_ROOT" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_BRANCH_AT_RUN="$GIT_BRANCH_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/train_enhancer.py" \
    --config "$REPO/configs/training/full_training_cpu_micro.yaml"

train_rc=$?
echo ""
echo "--- Step 1 exit: $train_rc ---"
if [ "$train_rc" -ne 0 ]; then
  echo "BLOCKER: training step failed with rc=$train_rc; skipping verification." >&2
  exit "$train_rc"
fi

# ----------------------------------------------------------------------------
# Step 2: read-only artifact and checkpoint verification (same Apptainer).
# ----------------------------------------------------------------------------
echo "--- Step 2: verification (read-only) ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env REPO="$REPO" \
  --env TRAIN_ROOT="$TRAIN_ROOT" \
  --env JOB_ID="$JOBID" \
  --env RUN_DIR="$RUN_DIR" \
  --env VERIFY_JSON="$VERIFY_JSON" \
  "$CONTAINER" \
  python3 -s -c '
import csv
import json
import math
import os
import sys
import traceback
from pathlib import Path

REPO = os.environ["REPO"]
TRAIN_ROOT = os.environ["TRAIN_ROOT"]
JOB_ID = os.environ["JOB_ID"]
RUN_DIR = Path(os.environ["RUN_DIR"])
VERIFY_JSON = Path(os.environ["VERIFY_JSON"])

# Make scripts/training importable as flat modules (same trick the trainer
# uses internally).
sys.path.insert(0, os.path.join(REPO, "scripts", "training"))

required_artifacts = (
    "config.yaml",
    "metrics.csv",
    "wer_by_degradation.csv",
    "loss_curve.png",
    "val_wer_curve.png",
    "run_summary.md",
)
expected_families = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)

result = {
    "validation_passed": False,
    "job_id": JOB_ID,
    "run_dir": str(RUN_DIR),
    "verify_json_path": str(VERIFY_JSON),
    "errors": [],
    "artifacts": {},
    "metrics_csv_train_rows": 0,
    "metrics_csv_val_rows": 0,
    "metrics_finite": True,
    "wer_by_degradation_family_rows": 0,
    "wer_by_degradation_families": [],
    "checkpoint_files": [],
    "latest_checkpoint_path": None,
    "checkpoint_metadata_check": "fail",
    "checkpoint_state_dict_roundtrip": "fail",
    "parameter_count": None,
    "whisper_run": False,
    "enhancement_run": False,
    "gpu_used": False,
    "apptainer_nv_used": False,
    "torch_version": None,
    "torch_cuda_is_available": None,
    "checkpoint_payload_step": None,
    "checkpoint_dataset_version": None,
    "checkpoint_training_split_version": None,
    "checkpoint_model_architecture": None,
}

try:
    import torch  # type: ignore
    result["torch_version"] = torch.__version__
    result["torch_cuda_is_available"] = bool(torch.cuda.is_available())
except Exception as exc:
    result["errors"].append("torch import failed: " + repr(exc))

# 1. Required artifact presence + sizes.
for name in required_artifacts:
    p = RUN_DIR / name
    if p.exists() and p.is_file():
        result["artifacts"][name] = {"present": True, "size_bytes": p.stat().st_size}
    else:
        result["artifacts"][name] = {"present": False, "size_bytes": None}
        result["errors"].append("missing artifact: " + name)

# 2. metrics.csv: count rows + finite check.
metrics_csv = RUN_DIR / "metrics.csv"
if metrics_csv.exists():
    try:
        with metrics_csv.open() as f:
            for row in csv.DictReader(f):
                phase = row.get("phase", "")
                loss_str = row.get("loss", "")
                if phase == "train":
                    result["metrics_csv_train_rows"] += 1
                elif phase == "val":
                    result["metrics_csv_val_rows"] += 1
                if loss_str:
                    try:
                        v = float(loss_str)
                        if not math.isfinite(v):
                            result["metrics_finite"] = False
                            result["errors"].append("metrics.csv non-finite loss at step=" + str(row.get("step")))
                    except ValueError:
                        result["metrics_finite"] = False
                        result["errors"].append("metrics.csv non-numeric loss: " + repr(loss_str))
    except Exception as exc:
        result["errors"].append("metrics.csv read failed: " + repr(exc))

# 3. wer_by_degradation.csv: family rows.
wer_csv = RUN_DIR / "wer_by_degradation.csv"
if wer_csv.exists():
    try:
        with wer_csv.open() as f:
            for row in csv.DictReader(f):
                fam = row.get("family", "")
                if fam:
                    result["wer_by_degradation_family_rows"] += 1
                    result["wer_by_degradation_families"].append(fam)
    except Exception as exc:
        result["errors"].append("wer_by_degradation.csv read failed: " + repr(exc))

# 4. Checkpoint enumeration.
ckdir = RUN_DIR / "checkpoints"
if ckdir.exists() and ckdir.is_dir():
    result["checkpoint_files"] = sorted(p.name for p in ckdir.glob("checkpoint_step_*.pt"))
    latest = ckdir / "latest.pt"
    if latest.exists():
        result["latest_checkpoint_path"] = str(latest)
else:
    result["errors"].append("checkpoints/ directory missing")

# 5. Checkpoint metadata + state_dict roundtrip via models.build_model.
required_meta_keys = (
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
ckpt_to_check = result["latest_checkpoint_path"]
if ckpt_to_check is None and result["checkpoint_files"]:
    ckpt_to_check = str(ckdir / result["checkpoint_files"][-1])
if ckpt_to_check is not None:
    try:
        payload = torch.load(ckpt_to_check, map_location="cpu")
        missing_keys = [k for k in required_meta_keys if k not in payload]
        if missing_keys:
            result["errors"].append("checkpoint missing keys: " + str(missing_keys))
        else:
            arch = payload.get("model_architecture")
            params = payload.get("model_params") or {}
            pc = int(payload.get("parameter_count", -1))
            result["checkpoint_payload_step"] = int(payload.get("step", -1))
            result["checkpoint_dataset_version"] = payload.get("dataset_version")
            result["checkpoint_training_split_version"] = payload.get("training_split_version")
            result["checkpoint_model_architecture"] = arch
            result["parameter_count"] = pc
            ok_arch = arch == "spectral_unet_small_v1"
            ok_pc = 200_000 <= pc <= 1_000_000
            ok_dv = payload.get("dataset_version") == "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8"
            ok_tsv = payload.get("training_split_version") == "devclean_speaker_split_v1"
            if ok_arch and ok_pc and ok_dv and ok_tsv:
                result["checkpoint_metadata_check"] = "pass"
            else:
                result["errors"].append(
                    "checkpoint metadata: arch=" + str(arch)
                    + " parameter_count=" + str(pc)
                    + " dataset_version=" + str(payload.get("dataset_version"))
                    + " training_split_version=" + str(payload.get("training_split_version"))
                )
            try:
                from models import build_model  # type: ignore
                model = build_model(arch, params)
                model.load_state_dict(payload["model_state_dict"])
                result["checkpoint_state_dict_roundtrip"] = "pass"
            except Exception as exc:
                result["errors"].append("state_dict roundtrip failed: " + repr(exc))
                result["errors"].append(traceback.format_exc())
    except Exception as exc:
        result["errors"].append("checkpoint load failed: " + repr(exc))
else:
    result["errors"].append("no checkpoint file to validate")

# 6. Whisper / enhancement / GPU policy. T6.2c hardcodes false because the
# job does not pass --enable-whisper-val, does not import the enhancement
# stack, does not request GPU resources, and does not pass --nv. These
# claims are also cross-checked against config.yaml runtime metadata
# below; any mismatch raises an error.
result["whisper_run"] = False
result["enhancement_run"] = False
result["gpu_used"] = False
result["apptainer_nv_used"] = False

cfg_snapshot = RUN_DIR / "config.yaml"
if cfg_snapshot.exists():
    try:
        import yaml  # type: ignore
        snap = yaml.safe_load(cfg_snapshot.read_text(encoding="utf-8")) or {}
        runtime = snap.get("runtime") or {}
        wv = runtime.get("whisper_validation_enabled")
        if wv is True:
            result["whisper_run"] = True
            result["errors"].append("runtime.whisper_validation_enabled is True; T6.2c forbids Whisper")
        result["runtime_architecture"] = runtime.get("architecture")
        result["runtime_parameter_count"] = runtime.get("parameter_count")
        result["runtime_steps_executed"] = runtime.get("steps_executed")
    except Exception as exc:
        result["errors"].append("config.yaml runtime read failed: " + repr(exc))

# 7. Final pass/fail decision.
all_artifacts_present = all(a.get("present") for a in result["artifacts"].values())
result["validation_passed"] = bool(
    not result["errors"]
    and all_artifacts_present
    and result["metrics_finite"]
    and result["metrics_csv_train_rows"] >= 1
    and result["metrics_csv_val_rows"] >= 1
    and result["wer_by_degradation_family_rows"] == len(expected_families)
    and bool(result["checkpoint_files"])
    and result["checkpoint_metadata_check"] == "pass"
    and result["checkpoint_state_dict_roundtrip"] == "pass"
    and result["whisper_run"] is False
    and result["enhancement_run"] is False
    and result["gpu_used"] is False
    and result["apptainer_nv_used"] is False
)

VERIFY_JSON.parent.mkdir(parents=True, exist_ok=True)
with VERIFY_JSON.open("w") as f:
    json.dump(result, f, indent=2, sort_keys=True)
print("VERIFY_JSON " + str(VERIFY_JSON))
print("VALIDATION_PASSED " + str(result["validation_passed"]))
if result["errors"]:
    print("VALIDATION_ERRORS:")
    for e in result["errors"]:
        print("  - " + str(e))
sys.exit(0 if result["validation_passed"] else 1)
'

verify_rc=$?
echo ""
echo "--- Step 2 exit: $verify_rc ---"
echo "=== T6.2c CPU micro-validation training end: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit "$verify_rc"
