#!/usr/bin/env bash
# T6.3a — post-hoc Whisper smoke evaluation Slurm job.
# Loads the T6.2 latest.pt checkpoint and runs eval-only mode against
# configs/training/full_training.yaml on a Surrey a100 node, evaluating
# 1 record per family (5 transcriptions total) with Whisper on CUDA.
# Exists to validate the entire --eval-checkpoint code path on real GPU
# hardware before the 2 665-record T6.3b full evaluation.
#
# Hard scope guards (must remain TRUE):
#   * --partition=a100, --gpus=1, apptainer exec --nv (no --pwd, no --bind).
#   * Host nvidia-smi must report at least one GPU before Python starts.
#   * In-Apptainer torch.cuda.is_available() must be True before eval starts.
#   * ASR_EXPECT_CUDA=1 inside Apptainer makes train_enhancer.py block if
#     CUDA is somehow lost between guard and eval (no silent CPU fallback).
#   * Whisper cache base.en.pt must already exist at $ASR_CACHE_ROOT/whisper.
#   * eval_out_dir lives under $ASR_ARTIFACTS_ROOT, NOT inside the repo and
#     NOT inside the T6.2 run_dir; verify JSON also lives outside eval_out_dir.
#   * Does NOT modify the T6.2 source run_dir.
#
# Submission (manual, only after T6.3 prep is committed):
#   ./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t6_3_post_hoc_whisper_smoke.sh

#SBATCH --job-name=asr_t6_3_post_hoc_whisper_smoke
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_3_post_hoc_whisper_smoke_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_3_post_hoc_whisper_smoke_%j.err
#SBATCH --partition=a100
#SBATCH --gpus=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00

set -euo pipefail

REPO=/mnt/fast/nobackup/users/gb0048/asr_enhancement
TRAIN_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
PREFIX=$TRAIN_ROOT/python_env/site-packages-py310
CONTAINER=/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
CACHE_ROOT=$TRAIN_ROOT/cache
ASR_CACHE_ROOT="$CACHE_ROOT"

# Source checkpoint = T6.2 latest.pt (frozen artifact).
T6_2_RUN_DIR=$TRAIN_ROOT/runs/t6_2_full_training_2128952
EVAL_CHECKPOINT=$T6_2_RUN_DIR/checkpoints/latest.pt

JOBID="${SLURM_JOB_ID:-local}"
EVAL_OUT_DIR="$TRAIN_ROOT/runs/_smoke/t6_3_post_hoc_whisper_smoke_${JOBID}"
ARTIFACT_DIR="$TRAIN_ROOT/artifacts"
VERIFY_JSON="$ARTIFACT_DIR/t6_3_post_hoc_whisper_smoke_verify_${JOBID}.json"

EVAL_PER_FAMILY_CAP=1
EXPECTED_TRANSCRIPTIONS=5

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runs/_smoke" \
  "$TRAIN_ROOT/runtime" \
  "$ARTIFACT_DIR" \
  "$CACHE_ROOT"

# ----------------------------------------------------------------------------
# Whisper cache pre-condition. T6.3 evaluation MUST NOT download from a
# compute node. Pre-stage from the login node before submitting.
# ----------------------------------------------------------------------------
if [ ! -s "$ASR_CACHE_ROOT/whisper/base.en.pt" ]; then
  echo "BLOCKER: $ASR_CACHE_ROOT/whisper/base.en.pt missing or empty; pre-stage from login node before submitting T6.3 jobs." >&2
  exit 2
fi

# ----------------------------------------------------------------------------
# Source checkpoint pre-condition.
# ----------------------------------------------------------------------------
if [ ! -s "$EVAL_CHECKPOINT" ]; then
  echo "BLOCKER: T6.2 checkpoint missing or empty: $EVAL_CHECKPOINT" >&2
  exit 2
fi

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
# In-Apptainer CUDA guard (fail-fast). No CPU fallback in this Slurm job.
# ----------------------------------------------------------------------------
echo "--- In-Apptainer CUDA guard ---"
apptainer exec --nv \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  "$CONTAINER" \
  python3 -s -c "import torch, sys; assert torch.cuda.is_available(), 'CUDA not visible inside Apptainer'; print(f'OK: torch={torch.__version__} cuda={torch.version.cuda} device={torch.cuda.get_device_name(0)}')"

# Capture git state before entering Apptainer (git is not in the container).
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH_AT_RUN=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T6.3a post-hoc Whisper smoke start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "Host:                 $(hostname)"
echo "Container:            $CONTAINER"
echo "Repo:                 $REPO"
echo "Train root:           $TRAIN_ROOT"
echo "ASR cache root:       $ASR_CACHE_ROOT"
echo "Slurm job id:         $JOBID"
echo "Slurm node list:      ${SLURM_NODELIST:-unset}"
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
# Step 1: post-hoc Whisper evaluation (real). ASR_EXPECT_CUDA=1 hard guard.
# ----------------------------------------------------------------------------
echo "--- Step 1: post-hoc Whisper smoke evaluation ---"
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
    --run-id "t6_3_post_hoc_whisper_smoke_${JOBID}"

eval_rc=$?
echo ""
echo "--- Step 1 exit: $eval_rc ---"
if [ "$eval_rc" -ne 0 ]; then
  echo "BLOCKER: eval-only step failed with rc=$eval_rc; skipping verification." >&2
  exit "$eval_rc"
fi

# ----------------------------------------------------------------------------
# Step 2: read-only verification. Reads eval_metadata.json and the per-family
# CSV/JSONL written by Step 1; writes verify JSON OUTSIDE eval_out_dir.
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
    "phase": "t6_3_post_hoc_whisper_smoke",
    "eval_out_dir": str(EVAL_OUT_DIR),
}

# 1. eval_metadata.json must exist and be parseable.
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

# 2. wer_by_degradation.csv: 5 rows, finite, non-placeholder note.
wer_csv = EVAL_OUT_DIR / "wer_by_degradation.csv"
fams_seen = []
all_finite = True
all_non_placeholder = True
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

# 3. per_record_predictions.jsonl: line count.
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

# 4. run_summary.md present.
if not (EVAL_OUT_DIR / "run_summary.md").exists():
    result["errors"].append("missing eval run_summary.md")

# 5. tmp dir must be cleaned and absent.
val_tmp = EVAL_OUT_DIR / "val_enhanced_tmp"
result["val_enhanced_tmp_absent"] = not val_tmp.exists()
if val_tmp.exists():
    result["errors"].append("val_enhanced_tmp/ unexpectedly present: " + str(val_tmp))

# 6. T6.2 source run_dir must be unchanged: assert checkpoint still exists
# at the original path (best-effort sanity).
if not EVAL_CHECKPOINT.exists():
    result["errors"].append("source T6.2 checkpoint missing post-eval: " + str(EVAL_CHECKPOINT))

# 7. enhancement_bank artifact absence inside eval_out_dir.
bank_hits = list(EVAL_OUT_DIR.glob("*enhancement_bank*"))
result["enhancement_bank_generation_artifacts_found"] = bool(bank_hits)
if bank_hits:
    result["errors"].append("enhancement_bank_* artifact present: " + str(bank_hits))

# 8. Posture and totals checks.
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

# 9. CUDA posture (whisper + enhancer).
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

# 10. Final pass/fail.
result["validation_passed"] = bool(
    not result["errors"]
    and len(fams_seen) == len(expected_families)
    and all_finite
    and all_non_placeholder
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
echo "=== T6.3a post-hoc Whisper smoke end: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit "$verify_rc"
