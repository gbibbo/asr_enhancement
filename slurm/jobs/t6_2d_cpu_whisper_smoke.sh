#!/usr/bin/env bash
# T6.2d — Whisper-enabled CPU smoke validation job for the
# spectral_unet_small_v1 trainer code path
# (training_datamove1_plan.md §16, internal subgate).
#
# Runs scripts/training/train_enhancer.py with
# configs/training/full_training_cpu_whisper_smoke.yaml inside the project
# Apptainer image on a CPU compute node, exercising the openai-whisper
# validation path on a tiny subset (1 record per family). Then performs
# read-only artifact and checkpoint validation in the SAME Apptainer job
# and writes a verify JSON outside the run directory.
#
# Hard scope guards (must remain TRUE):
#   * CPU only. No GPU SBATCH flags. No --nv on apptainer exec.
#   * No --bind on apptainer exec. No --pwd on apptainer exec.
#   * No call to slurm/tools/on_submit.sh, sbatch, squeue, sacct, scancel,
#     sinfo, or scontrol from inside this job script.
#   * Does not run full training. Does not run enhancement bank generation.
#   * Does not modify trackers, configs, libs, or the model card.
#   * The whisper model cache MUST be pre-staged from the login node into
#     $CACHE_ROOT/whisper. The job fails before invoking Python if the
#     cache is missing — no compute-node downloads are allowed.
#   * Submission is performed manually with:
#       ./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t6_2d_cpu_whisper_smoke.sh

#SBATCH --job-name=asr_t6_2d_cpu_whisper_smoke
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2d_cpu_whisper_smoke_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2d_cpu_whisper_smoke_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

set -euo pipefail

REPO=/mnt/fast/nobackup/users/gb0048/asr_enhancement
TRAIN_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
PREFIX=$TRAIN_ROOT/python_env/site-packages-py310
CONTAINER=/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
CACHE_ROOT=$TRAIN_ROOT/cache
ASR_CACHE_ROOT="$CACHE_ROOT"

JOBID="${SLURM_JOB_ID:-local}"
RUN_DIR="$TRAIN_ROOT/runs/_smoke/t6_2d_cpu_whisper_smoke_${JOBID}"
ARTIFACT_DIR="$TRAIN_ROOT/artifacts"
VERIFY_JSON="$ARTIFACT_DIR/t6_2d_cpu_whisper_smoke_verify_${JOBID}.json"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runs/_smoke" \
  "$TRAIN_ROOT/runtime" \
  "$ARTIFACT_DIR" \
  "$CACHE_ROOT" \
  "$CACHE_ROOT/whisper"

# ----------------------------------------------------------------------------
# Whisper cache pre-condition. T6.2d MUST NOT download from a compute node.
# The login-node pre-stage step is the only place a download is allowed.
# ----------------------------------------------------------------------------
if [ ! -s "$ASR_CACHE_ROOT/whisper/base.en.pt" ]; then
  echo "BLOCKER: $ASR_CACHE_ROOT/whisper/base.en.pt missing or empty; pre-stage from login node before submitting T6.2d." >&2
  exit 2
fi

# Capture git state before entering Apptainer (git is not in the container).
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH_AT_RUN=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T6.2d CPU Whisper smoke validation start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "Host:                 $(hostname)"
echo "Container:            $CONTAINER"
echo "Repo:                 $REPO"
echo "Prefix:               $PREFIX"
echo "Train root:           $TRAIN_ROOT"
echo "Cache root:           $CACHE_ROOT"
echo "ASR cache root:       $ASR_CACHE_ROOT"
echo "Whisper cache file:   $ASR_CACHE_ROOT/whisper/base.en.pt"
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
# Step 1: CPU smoke training run with Whisper validation enabled.
# ----------------------------------------------------------------------------
echo "--- Step 1: CPU Whisper smoke run ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$ARTIFACT_DIR" \
  --env ASR_CACHE_ROOT="$ASR_CACHE_ROOT" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_BRANCH_AT_RUN="$GIT_BRANCH_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/train_enhancer.py" \
    --config "$REPO/configs/training/full_training_cpu_whisper_smoke.yaml" \
    --enable-whisper-val \
    --force-fresh

train_rc=$?
echo ""
echo "--- Step 1 exit: $train_rc ---"
if [ "$train_rc" -ne 0 ]; then
  echo "BLOCKER: training step failed with rc=$train_rc; skipping verification." >&2
  exit "$train_rc"
fi

# ----------------------------------------------------------------------------
# Step 2: read-only artifact, checkpoint, and Whisper-smoke verification
# (same Apptainer). Reads runtime metadata from the runtime: block appended
# inside run_dir/config.yaml — no separate runtime_meta.json artifact is
# created, the six-artifact contract is preserved.
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
    "metrics_val_wer_finite": False,
    "wer_by_degradation_family_rows": 0,
    "wer_by_degradation_families": [],
    "wer_by_degradation_all_finite": False,
    "wer_by_degradation_no_placeholder_note": False,
    "checkpoint_files": [],
    "latest_checkpoint_path": None,
    "checkpoint_metadata_check": "fail",
    "checkpoint_state_dict_roundtrip": "fail",
    "parameter_count": None,
    "whisper_validation_enabled": False,
    "whisper_model": None,
    "whisper_version": None,
    "selected_utterance_ids": None,
    "selected_families": None,
    "missing_transcript_count": None,
    "temp_wavs_written": None,
    "whisper_transcriptions_completed": None,
    "temp_dir_cleaned": None,
    "val_enhanced_tmp_absent": False,
    "mean_wer": None,
    "mean_word_accuracy": None,
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

# 2. metrics.csv: count rows, finite check, and confirm at least one val row
# has finite WER and Word Accuracy.
metrics_csv = RUN_DIR / "metrics.csv"
if metrics_csv.exists():
    try:
        with metrics_csv.open() as f:
            for row in csv.DictReader(f):
                phase = row.get("phase", "")
                loss_str = row.get("loss", "")
                wer_str = row.get("wer", "")
                wa_str = row.get("word_accuracy", "")
                if phase == "train":
                    result["metrics_csv_train_rows"] += 1
                elif phase == "val":
                    result["metrics_csv_val_rows"] += 1
                    if wer_str:
                        try:
                            wv = float(wer_str)
                            if math.isfinite(wv):
                                result["metrics_val_wer_finite"] = True
                            else:
                                result["errors"].append(
                                    "metrics.csv val row non-finite WER at step="
                                    + str(row.get("step"))
                                )
                        except ValueError:
                            result["errors"].append(
                                "metrics.csv val row non-numeric WER: "
                                + repr(wer_str)
                            )
                    if wa_str:
                        try:
                            wav = float(wa_str)
                            if not math.isfinite(wav):
                                result["errors"].append(
                                    "metrics.csv val row non-finite WA at step="
                                    + str(row.get("step"))
                                )
                        except ValueError:
                            result["errors"].append(
                                "metrics.csv val row non-numeric WA: "
                                + repr(wa_str)
                            )
                if loss_str:
                    try:
                        v = float(loss_str)
                        if not math.isfinite(v):
                            result["metrics_finite"] = False
                            result["errors"].append(
                                "metrics.csv non-finite loss at step="
                                + str(row.get("step"))
                            )
                    except ValueError:
                        result["metrics_finite"] = False
                        result["errors"].append(
                            "metrics.csv non-numeric loss: " + repr(loss_str)
                        )
    except Exception as exc:
        result["errors"].append("metrics.csv read failed: " + repr(exc))

# 3. wer_by_degradation.csv: family rows, finite values, no placeholder note.
wer_csv = RUN_DIR / "wer_by_degradation.csv"
if wer_csv.exists():
    try:
        all_finite = True
        all_non_placeholder = True
        with wer_csv.open() as f:
            for row in csv.DictReader(f):
                fam = row.get("family", "")
                if fam:
                    result["wer_by_degradation_family_rows"] += 1
                    result["wer_by_degradation_families"].append(fam)
                mw = row.get("mean_wer", "")
                mwa = row.get("mean_word_accuracy", "")
                note = row.get("note", "")
                if "placeholder" in note.lower() or "no_whisper" in note.lower():
                    all_non_placeholder = False
                    result["errors"].append(
                        "wer_by_degradation.csv placeholder note for family="
                        + fam + " note=" + repr(note)
                    )
                if not mw or not mwa:
                    all_finite = False
                    result["errors"].append(
                        "wer_by_degradation.csv empty WER/WA for family=" + fam
                    )
                else:
                    try:
                        if not math.isfinite(float(mw)) or not math.isfinite(float(mwa)):
                            all_finite = False
                            result["errors"].append(
                                "wer_by_degradation.csv non-finite values for family="
                                + fam
                            )
                    except ValueError:
                        all_finite = False
                        result["errors"].append(
                            "wer_by_degradation.csv non-numeric values for family="
                            + fam
                        )
        result["wer_by_degradation_all_finite"] = all_finite
        result["wer_by_degradation_no_placeholder_note"] = all_non_placeholder
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

# 6. Whisper smoke survival metadata: read from the runtime: block appended
# inside run_dir/config.yaml. No separate runtime_meta.json.
result["enhancement_run"] = False
result["gpu_used"] = False
result["apptainer_nv_used"] = False

cfg_snapshot = RUN_DIR / "config.yaml"
if cfg_snapshot.exists():
    try:
        import yaml  # type: ignore
        snap = yaml.safe_load(cfg_snapshot.read_text(encoding="utf-8")) or {}
        runtime = snap.get("runtime") or {}
        result["whisper_validation_enabled"] = bool(
            runtime.get("whisper_validation_enabled")
        )
        result["whisper_model"] = runtime.get("whisper_model")
        result["whisper_version"] = runtime.get("whisper_version")
        result["selected_utterance_ids"] = runtime.get("selected_utterance_ids")
        result["selected_families"] = runtime.get("selected_families")
        result["missing_transcript_count"] = runtime.get("missing_transcript_count")
        result["temp_wavs_written"] = runtime.get("temp_wavs_written")
        result["whisper_transcriptions_completed"] = runtime.get(
            "whisper_transcriptions_completed"
        )
        result["temp_dir_cleaned"] = runtime.get("temp_dir_cleaned")
        result["mean_wer"] = runtime.get("whisper_mean_wer")
        result["mean_word_accuracy"] = runtime.get("whisper_mean_word_accuracy")
        result["runtime_architecture"] = runtime.get("architecture")
        result["runtime_parameter_count"] = runtime.get("parameter_count")
        result["runtime_steps_executed"] = runtime.get("steps_executed")
    except Exception as exc:
        result["errors"].append("config.yaml runtime read failed: " + repr(exc))

# 7. val_enhanced_tmp/ must have been cleaned.
val_tmp = RUN_DIR / "val_enhanced_tmp"
result["val_enhanced_tmp_absent"] = not val_tmp.exists()
if val_tmp.exists():
    result["errors"].append("val_enhanced_tmp/ was not cleaned: " + str(val_tmp))

# 8. Final pass/fail decision.
all_artifacts_present = all(a.get("present") for a in result["artifacts"].values())
result["validation_passed"] = bool(
    not result["errors"]
    and all_artifacts_present
    and result["metrics_finite"]
    and result["metrics_csv_train_rows"] >= 1
    and result["metrics_csv_val_rows"] >= 1
    and result["metrics_val_wer_finite"]
    and result["wer_by_degradation_family_rows"] == len(expected_families)
    and result["wer_by_degradation_all_finite"]
    and result["wer_by_degradation_no_placeholder_note"]
    and bool(result["checkpoint_files"])
    and result["checkpoint_metadata_check"] == "pass"
    and result["checkpoint_state_dict_roundtrip"] == "pass"
    and result["whisper_validation_enabled"] is True
    and result["whisper_transcriptions_completed"] == len(expected_families)
    and result["temp_wavs_written"] == len(expected_families)
    and result["temp_dir_cleaned"] is True
    and result["missing_transcript_count"] == 0
    and result["val_enhanced_tmp_absent"] is True
    and result["enhancement_run"] is False
    and result["gpu_used"] is False
    and result["apptainer_nv_used"] is False
)

VERIFY_JSON.parent.mkdir(parents=True, exist_ok=True)
with VERIFY_JSON.open("w") as f:
    json.dump(result, f, indent=2, sort_keys=True, default=str)
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
echo "=== T6.2d CPU Whisper smoke validation end: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit "$verify_rc"
