#!/usr/bin/env bash
#SBATCH --job-name=asr_p3_1_lora_smoke
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=04:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --partition=2080ti
#SBATCH --gres=gpu:1

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs" \
         "$REPO/artifacts/robust_asr/lora_smoke" \
         "$REPO/reports/robust_asr/lora"

CONTAINER_SHA=$(sha256sum "$CONTAINER" | awk '{print $1}')
echo "container_sha256=$CONTAINER_SHA"
echo "expected_container_sha256=8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713"
echo "hostname=$(hostname)"
nvidia-smi -L || true

cd "$REPO"

WHISPER_BASE_SNAPSHOT="$TRAIN_ROOT/cache/huggingface/hub/models--openai--whisper-base.en/snapshots/911407f4214e0e1d82085af863093ec0b66f9cd6"

APPTAINER_ENV=(
  --env PYTHONNOUSERSITE=1
  --env PIP_USER=0
  --env PYTHONPATH=""
  --env PYTHONUSERBASE=""
  --env ASR_REPO_ROOT="$REPO"
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime"
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts"
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache"
  --env HF_HOME="$TRAIN_ROOT/cache/huggingface"
  --env HF_HUB_CACHE="$TRAIN_ROOT/cache/huggingface/hub"
  --env TRANSFORMERS_CACHE="$TRAIN_ROOT/cache/huggingface/hub"
  --env HF_HUB_OFFLINE=1
  --env TRANSFORMERS_OFFLINE=1
  --env HF_HUB_DISABLE_TELEMETRY=1
  --env WHISPER_BASE_MODEL="$WHISPER_BASE_SNAPSHOT"
)

###############################################################################
# Step 1: train LoRA smoke
###############################################################################
echo "=== STEP 1: train_lora_smoke ==="
set +e
apptainer exec --nv "${APPTAINER_ENV[@]}" "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/train_lora_smoke.py" \
    --config "$REPO/configs/robust_asr/lora_smoke.yaml"
TRAIN_RC=$?
set -e
echo "train_lora_smoke_exit=$TRAIN_RC"

if [ "$TRAIN_RC" -eq 2 ]; then
  echo "CUDA_OOM_AT_BATCH_SIZE_1 — recording HALTED + BLOCKED_RUNTIME"
  exit 2
fi
if [ "$TRAIN_RC" -eq 3 ]; then
  echo "NON_FINITE_LOSS_THRESHOLD_EXCEEDED — recording FAIL"
  exit 3
fi
if [ "$TRAIN_RC" -ne 0 ]; then
  echo "train_lora_smoke failed with exit $TRAIN_RC"
  exit "$TRAIN_RC"
fi

###############################################################################
# Step 2: evaluate LoRA smoke
###############################################################################
echo "=== STEP 2: evaluate_lora_smoke ==="
set +e
apptainer exec --nv "${APPTAINER_ENV[@]}" "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/evaluate_lora_smoke.py" \
    --config "$REPO/configs/robust_asr/lora_smoke.yaml" \
    --checkpoint-manifest "$REPO/artifacts/robust_asr/lora_smoke/checkpoint_manifest.json" \
    --out "$REPO/reports/robust_asr/lora/lora_smoke_result.json"
EVAL_RC=$?
set -e
echo "evaluate_lora_smoke_exit=$EVAL_RC"

if [ "$EVAL_RC" -eq 4 ]; then
  echo "DEGENERATE_SMOKE_RESULT — recording FAIL"
  exit 4
fi
if [ "$EVAL_RC" -ne 0 ]; then
  echo "evaluate_lora_smoke failed with exit $EVAL_RC"
  exit "$EVAL_RC"
fi

###############################################################################
# Step 3: export smoke (CT2 INT8)
###############################################################################
echo "=== STEP 3: smoke_export_lora_ct2 ==="
BEST_STEP=$(apptainer exec "${APPTAINER_ENV[@]}" "$CONTAINER" \
  python3 -c "import json,sys; m=json.load(open('$REPO/artifacts/robust_asr/lora_smoke/checkpoint_manifest.json')); print('step_{:05d}'.format(m['best_step']))")
echo "best_checkpoint=$BEST_STEP"

set +e
apptainer exec --nv "${APPTAINER_ENV[@]}" "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/smoke_export_lora_ct2.py" \
    --config "$REPO/configs/robust_asr/lora_smoke.yaml" \
    --checkpoint "$REPO/artifacts/robust_asr/lora_smoke/checkpoints/$BEST_STEP" \
    --out "$REPO/artifacts/robust_asr/lora_smoke/export_smoke_result.json"
EXPORT_RC=$?
set -e
echo "smoke_export_lora_ct2_exit=$EXPORT_RC"

if [ "$EXPORT_RC" -eq 5 ]; then
  echo "CT2_UNSUPPORTED_VERSION_OR_OP — recording EXPORT_BLOCKED (smoke NOT failed)"
  # Section 5/§3590: export failure does not fail the smoke; continue to PASS.
fi

echo "P3_1_LORA_SMOKE_DONE"
exit 0
