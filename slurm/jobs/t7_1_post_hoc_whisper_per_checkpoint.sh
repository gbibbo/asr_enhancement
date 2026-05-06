#!/usr/bin/env bash
# T7.1 — per-checkpoint post-hoc Whisper evaluation Slurm job.
# Loads one of the four un-evaluated T6.2 candidate checkpoints
# (steps 10000, 12500, 15000, 17500) and runs the existing
# `--eval-checkpoint` mode of scripts/training/train_enhancer.py against
# configs/training/full_training.yaml on a Surrey a100 node, evaluating
# 533 records per family (2665 transcriptions total) with Whisper on
# CUDA. Produces the per-family WER/WA artifacts that
# scripts/training/select_checkpoint.py consumes.
#
# Step 20000 is intentionally REJECTED: T6.3b already evaluated
# latest.pt (which is bit-equivalent to checkpoint_step_0020000.pt
# subject to a SHA-256 cross-check at selection time).
#
# STEP-passing mechanism (only this is supported):
#
#   ./slurm/tools/on_submit.sh sbatch \
#     --export=ALL,T7_1_STEP=10000 \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t7_1_post_hoc_whisper_per_checkpoint.sh
#
# Repeat for T7_1_STEP in {12500, 15000, 17500}.
#
# Hard scope guards (must remain TRUE):
#   * T7_1_STEP set and ∈ {10000, 12500, 15000, 17500}
#   * --partition=a100, --gpus=1, apptainer exec --nv (no --pwd, no --bind)
#   * Host nvidia-smi reports ≥1 GPU before Python starts
#   * In-Apptainer torch.cuda.is_available() is True before eval starts
#   * ASR_EXPECT_CUDA=1 inside Apptainer blocks silent CPU fallback
#   * Whisper cache base.en.pt already exists at $ASR_CACHE_ROOT/whisper
#   * eval_out_dir lives under $ASR_TRAINING_ROOT/runs/, NOT inside the
#     repo and NOT inside the T6.2 source run_dir; verify JSON also
#     lives outside eval_out_dir
#   * Does NOT modify the T6.2 source run_dir

#SBATCH --job-name=asr_t7_1_post_hoc_whisper_per_checkpoint
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t7_1_post_hoc_whisper_per_checkpoint_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t7_1_post_hoc_whisper_per_checkpoint_%j.err
#SBATCH --partition=a100
#SBATCH --gpus=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00

set -euo pipefail

# ----------------------------------------------------------------------------
# Hard guard: T7_1_STEP must be one of the four allowed values. Step 20000
# is rejected (its metrics come from T6.3b's evaluation of latest.pt).
# ----------------------------------------------------------------------------
case "${T7_1_STEP:-}" in
  10000|12500|15000|17500)
    ;;
  20000)
    echo "BLOCKER: T7_1_STEP=20000 is rejected; step 20000 metrics come from T6.3b's evaluation of latest.pt" >&2
    exit 2
    ;;
  *)
    echo "BLOCKER: T7_1_STEP must be one of 10000|12500|15000|17500; got '${T7_1_STEP:-<unset>}'" >&2
    exit 2
    ;;
esac

REPO=/mnt/fast/nobackup/users/gb0048/asr_enhancement
TRAIN_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
PREFIX=$TRAIN_ROOT/python_env/site-packages-py310
CONTAINER=/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
CACHE_ROOT=$TRAIN_ROOT/cache
ASR_CACHE_ROOT="$CACHE_ROOT"

T6_2_RUN_DIR=$TRAIN_ROOT/runs/t6_2_full_training_2128952
STEP_PADDED=$(printf "%07d" "$T7_1_STEP")
EVAL_CHECKPOINT=$T6_2_RUN_DIR/checkpoints/checkpoint_step_${STEP_PADDED}.pt

JOBID="${SLURM_JOB_ID:-local}"
EVAL_OUT_DIR="$TRAIN_ROOT/runs/t7_1_post_hoc_whisper_step_${T7_1_STEP}_${JOBID}"
ARTIFACT_DIR="$TRAIN_ROOT/artifacts"
VERIFY_JSON="$ARTIFACT_DIR/t7_1_post_hoc_whisper_step_${T7_1_STEP}_verify_${JOBID}.json"

EVAL_PER_FAMILY_CAP=533
EXPECTED_TRANSCRIPTIONS=2665

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runs" \
  "$TRAIN_ROOT/runtime" \
  "$ARTIFACT_DIR" \
  "$CACHE_ROOT"

# ----------------------------------------------------------------------------
# Whisper cache pre-condition.
# ----------------------------------------------------------------------------
if [ ! -s "$ASR_CACHE_ROOT/whisper/base.en.pt" ]; then
  echo "BLOCKER: $ASR_CACHE_ROOT/whisper/base.en.pt missing or empty; pre-stage from login node before submitting T7.1 jobs." >&2
  exit 2
fi

# ----------------------------------------------------------------------------
# Source checkpoint pre-condition.
# ----------------------------------------------------------------------------
if [ ! -s "$EVAL_CHECKPOINT" ]; then
  echo "BLOCKER: T6.2 candidate checkpoint missing or empty: $EVAL_CHECKPOINT" >&2
  exit 2
fi

# ----------------------------------------------------------------------------
# Refuse to run if eval_out_dir would land inside the T6.2 source run_dir.
# ----------------------------------------------------------------------------
case "$EVAL_OUT_DIR" in
  "$T6_2_RUN_DIR"/*|"$T6_2_RUN_DIR")
    echo "BLOCKER: EVAL_OUT_DIR must be outside the T6.2 source run_dir: $EVAL_OUT_DIR" >&2
    exit 2
    ;;
esac

# ----------------------------------------------------------------------------
# Host CUDA guard (fail-fast).
# ----------------------------------------------------------------------------
echo "--- Host CUDA guard: nvidia-smi ---"
if ! nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv; then
  echo "BLOCKER: nvidia-smi failed on host" >&2
  exit 2
fi
GPU_ROWS=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l | tr -d ' ')
if [ "${GPU_ROWS:-0}" -lt 1 ]; then
  echo "BLOCKER: nvidia-smi reported no GPU on host" >&2
  exit 2
fi
echo "Host GPU rows: $GPU_ROWS"

# ----------------------------------------------------------------------------
# In-Apptainer CUDA guard (fail-fast).
# ----------------------------------------------------------------------------
echo "--- In-Apptainer CUDA guard ---"
apptainer exec --nv \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  "$CONTAINER" \
  python3 -s -c "import torch, sys; assert torch.cuda.is_available(), 'CUDA not visible inside Apptainer'; print(f'OK: torch={torch.__version__} cuda={torch.version.cuda} device={torch.cuda.get_device_name(0)}')"

GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH_AT_RUN=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T7.1 per-checkpoint post-hoc Whisper eval start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "Host:                 $(hostname)"
echo "Container:            $CONTAINER"
echo "Repo:                 $REPO"
echo "Train root:           $TRAIN_ROOT"
echo "ASR cache root:       $ASR_CACHE_ROOT"
echo "Slurm job id:         $JOBID"
echo "Slurm node list:      ${SLURM_NODELIST:-unset}"
echo "T7_1_STEP:            $T7_1_STEP"
echo "Eval checkpoint:      $EVAL_CHECKPOINT"
echo "Eval out dir:         $EVAL_OUT_DIR"
echo "Verify JSON path:     $VERIFY_JSON"
echo "Eval per_family_cap:  $EVAL_PER_FAMILY_CAP"
echo "Expected transcrips:  $EXPECTED_TRANSCRIPTIONS"
echo "Git commit at run:    $GIT_COMMIT_AT_RUN"
echo "Git branch at run:    $GIT_BRANCH_AT_RUN"
echo "Git status (short):   ${GIT_STATUS_SHORT_AT_RUN:-clean}"
echo "============================="

cd "$REPO" || exit 1

# ----------------------------------------------------------------------------
# Step 1: post-hoc Whisper full evaluation for the requested step.
# ----------------------------------------------------------------------------
echo "--- Step 1: post-hoc Whisper evaluation for step $T7_1_STEP ---"
apptainer exec --nv \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$ARTIFACT_DIR" \
  --env ASR_CACHE_ROOT="$ASR_CACHE_ROOT" \
  --env ASR_EXPECT_CUDA=1 \
  --env PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_BRANCH_AT_RUN="$GIT_BRANCH_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/train_enhancer.py" \
    --config "$REPO/configs/training/full_training.yaml" \
    --eval-checkpoint "$EVAL_CHECKPOINT" \
    --eval-out-dir "$EVAL_OUT_DIR" \
    --eval-per-family-cap "$EVAL_PER_FAMILY_CAP" \
    --whisper-device cuda \
    --run-id "t7_1_post_hoc_whisper_step_${T7_1_STEP}_${JOBID}"

eval_rc=$?
echo ""
echo "--- Step 1 exit: $eval_rc ---"
if [ "$eval_rc" -ne 0 ]; then
  echo "BLOCKER: eval-only step failed with rc=$eval_rc; skipping verification." >&2
  exit "$eval_rc"
fi

# ----------------------------------------------------------------------------
# Step 2: read-only verification (mirrors T6.3b's verifier exactly).
# ----------------------------------------------------------------------------
echo "--- Step 2: verification (read-only) ---"
apptainer exec --nv \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env REPO="$REPO" \
  --env TRAIN_ROOT="$TRAIN_ROOT" \
  --env JOB_ID="$JOBID" \
  --env EVAL_OUT_DIR="$EVAL_OUT_DIR" \
  --env VERIFY_JSON="$VERIFY_JSON" \
  --env EVAL_CHECKPOINT="$EVAL_CHECKPOINT" \
  --env EXPECTED_TRANSCRIPTIONS="$EXPECTED_TRANSCRIPTIONS" \
  --env EVAL_PER_FAMILY_CAP="$EVAL_PER_FAMILY_CAP" \
  --env T6_2_RUN_DIR="$T6_2_RUN_DIR" \
  --env T7_1_STEP="$T7_1_STEP" \
  "$CONTAINER" \
  python3 -s -c '
import csv
import json
import math
import os
import sys
from pathlib import Path

EVAL_OUT_DIR = Path(os.environ["EVAL_OUT_DIR"])
VERIFY_JSON = Path(os.environ["VERIFY_JSON"])
EVAL_CHECKPOINT = Path(os.environ["EVAL_CHECKPOINT"])
EXPECTED = int(os.environ["EXPECTED_TRANSCRIPTIONS"])
CAP = int(os.environ["EVAL_PER_FAMILY_CAP"])
T6_2_RUN_DIR = Path(os.environ["T6_2_RUN_DIR"])
STEP = int(os.environ["T7_1_STEP"])

expected_families = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)

result = {
    "validation_passed": False,
    "errors": [],
    "phase": f"t7_1_post_hoc_whisper_step_{STEP}",
    "eval_out_dir": str(EVAL_OUT_DIR),
    "t7_1_step": STEP,
}

meta_path = EVAL_OUT_DIR / "eval_metadata.json"
if not meta_path.exists():
    result["errors"].append("missing eval_metadata.json")
else:
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["errors"].append("eval_metadata.json parse failed: " + repr(exc))
        meta = {}
    for key in (
        "checkpoint_path", "checkpoint_step", "checkpoint_model_architecture",
        "checkpoint_parameter_count", "eval_per_family_cap",
        "total_expected_transcriptions", "total_completed_transcriptions",
        "temp_wavs_written", "temp_dir_cleaned", "missing_transcript_count",
        "selected_families", "per_family_counts", "per_family_mean_wer",
        "per_family_mean_word_accuracy", "macro_wer", "macro_word_accuracy",
        "per_record_predictions_count", "whisper_model", "whisper_version",
        "whisper_device", "enhancer_device", "gpu_used", "apptainer_nv_used",
        "expected_cuda", "torch_cuda_is_available", "enhancement_run",
    ):
        result[key] = meta.get(key)
    if meta.get("checkpoint_step") not in (STEP, None):
        result["errors"].append(
            "eval_metadata.checkpoint_step=" + str(meta.get("checkpoint_step"))
            + " != T7_1_STEP=" + str(STEP)
        )

wer_csv = EVAL_OUT_DIR / "wer_by_degradation.csv"
fams_seen = []
all_finite = True
all_non_placeholder = True
per_family_counts_ok = True
if not wer_csv.exists():
    result["errors"].append("missing wer_by_degradation.csv")
else:
    with wer_csv.open() as f:
        for row in csv.DictReader(f):
            fam = row.get("family", "")
            if fam:
                fams_seen.append(fam)
            mw = row.get("mean_wer", "")
            mwa = row.get("mean_word_accuracy", "")
            note = row.get("note", "")
            count_str = row.get("count", "0")
            try:
                if int(count_str) != CAP:
                    per_family_counts_ok = False
                    result["errors"].append(
                        "wer_by_degradation.csv family=" + fam
                        + " count=" + count_str + " != " + str(CAP)
                    )
            except ValueError:
                per_family_counts_ok = False
                result["errors"].append("non-numeric count in wer_by_degradation.csv family=" + fam)
            if "placeholder" in note.lower():
                all_non_placeholder = False
                result["errors"].append("placeholder note in wer_by_degradation.csv family=" + fam)
            if not mw or not mwa:
                all_finite = False
                result["errors"].append("empty WER/WA in wer_by_degradation.csv family=" + fam)
            else:
                try:
                    if not (math.isfinite(float(mw)) and math.isfinite(float(mwa))):
                        all_finite = False
                        result["errors"].append("non-finite WER/WA in wer_by_degradation.csv family=" + fam)
                except ValueError:
                    all_finite = False
                    result["errors"].append("non-numeric WER/WA in wer_by_degradation.csv family=" + fam)
result["wer_by_degradation_family_count"] = len(fams_seen)
result["wer_by_degradation_families"] = fams_seen
result["wer_by_degradation_all_finite"] = all_finite
result["wer_by_degradation_no_placeholder_note"] = all_non_placeholder
result["wer_by_degradation_per_family_counts_ok"] = per_family_counts_ok

pred_path = EVAL_OUT_DIR / "per_record_predictions.jsonl"
pred_lines = 0
if pred_path.exists():
    with pred_path.open() as f:
        for ln in f:
            if ln.strip():
                pred_lines += 1
else:
    result["errors"].append("missing per_record_predictions.jsonl")
result["per_record_predictions_lines"] = pred_lines

if not (EVAL_OUT_DIR / "run_summary.md").exists():
    result["errors"].append("missing eval run_summary.md")

val_tmp = EVAL_OUT_DIR / "val_enhanced_tmp"
result["val_enhanced_tmp_absent"] = not val_tmp.exists()
if val_tmp.exists():
    result["errors"].append("val_enhanced_tmp/ unexpectedly present: " + str(val_tmp))

if not EVAL_CHECKPOINT.exists():
    result["errors"].append("source T6.2 checkpoint missing post-eval: " + str(EVAL_CHECKPOINT))

bank_hits = list(EVAL_OUT_DIR.glob("*enhancement_bank*"))
result["enhancement_bank_generation_artifacts_found"] = bool(bank_hits)
if bank_hits:
    result["errors"].append("enhancement_bank_* artifact present: " + str(bank_hits))

if result.get("total_expected_transcriptions") != EXPECTED:
    result["errors"].append(
        "total_expected_transcriptions=" + str(result.get("total_expected_transcriptions"))
        + " != " + str(EXPECTED)
    )
if result.get("total_completed_transcriptions") != EXPECTED:
    result["errors"].append(
        "total_completed_transcriptions=" + str(result.get("total_completed_transcriptions"))
        + " != " + str(EXPECTED)
    )
if result.get("temp_wavs_written") != EXPECTED:
    result["errors"].append(
        "temp_wavs_written=" + str(result.get("temp_wavs_written"))
        + " != " + str(EXPECTED)
    )
if result.get("temp_dir_cleaned") is not True:
    result["errors"].append("temp_dir_cleaned not True: " + str(result.get("temp_dir_cleaned")))
if result.get("missing_transcript_count") != 0:
    result["errors"].append(
        "missing_transcript_count != 0: " + str(result.get("missing_transcript_count"))
    )
if result.get("eval_per_family_cap") != CAP:
    result["errors"].append(
        "eval_per_family_cap=" + str(result.get("eval_per_family_cap"))
        + " != " + str(CAP)
    )
if pred_lines != EXPECTED:
    result["errors"].append(
        "per_record_predictions_lines=" + str(pred_lines) + " != " + str(EXPECTED)
    )

for k, expected in (
    ("whisper_device", "cuda"),
    ("enhancer_device", "cuda"),
    ("gpu_used", True),
    ("apptainer_nv_used", True),
    ("expected_cuda", True),
    ("torch_cuda_is_available", True),
    ("enhancement_run", False),
):
    actual = result.get(k)
    if k == "enhancer_device":
        if not (isinstance(actual, str) and actual.startswith("cuda")):
            result["errors"].append(k + "=" + repr(actual) + " expected str startswith cuda")
        continue
    if actual != expected:
        result["errors"].append(k + "=" + repr(actual) + " != " + repr(expected))

result["validation_passed"] = bool(
    not result["errors"]
    and len(fams_seen) == len(expected_families)
    and all_finite
    and all_non_placeholder
    and per_family_counts_ok
    and pred_lines == EXPECTED
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
echo "=== T7.1 per-checkpoint post-hoc Whisper eval end: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit "$verify_rc"
