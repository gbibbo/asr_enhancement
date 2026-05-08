#!/usr/bin/env bash
#SBATCH --job-name=asr_p2_1_baseline
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --partition=2080ti
#SBATCH --gres=gpu:1

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs" "$REPO/artifacts/robust_asr/eval_tables"

CONTAINER_SHA=$(sha256sum "$CONTAINER" | awk '{print $1}')
echo "container_sha256=$CONTAINER_SHA"
echo "expected_container_sha256=8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713"

cd "$REPO"

set +e
apptainer exec --nv \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_USER=0 \
  --env PYTHONPATH="" \
  --env PYTHONUSERBASE="" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env HF_HOME="$TRAIN_ROOT/cache/huggingface" \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/run_backend_eval.py" \
    --backend whisper_base_ct2_int8 \
    --manifests "$REPO/configs/robust_asr/eval_manifests_v1.yaml" \
    --out "$REPO/artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet" \
    --use-gpu
EVAL_RC=$?
set -e
echo "run_backend_eval_exit=$EVAL_RC"

if [ "$EVAL_RC" -eq 13 ]; then
  echo "MISSING_EVIDENCE: CT2 INT8 weights not found; halting cleanly."
  exit 13
fi

if [ "$EVAL_RC" -ne 0 ]; then
  echo "run_backend_eval failed with exit $EVAL_RC"
  exit "$EVAL_RC"
fi

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_USER=0 \
  --env PYTHONPATH="" \
  --env PYTHONUSERBASE="" \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/summarize_backend_eval.py" \
    --input "$REPO/artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet" \
    --out "$REPO/reports/robust_asr/baseline_whisper_base.md"

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_USER=0 \
  --env PYTHONPATH="" \
  --env PYTHONUSERBASE="" \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/validate_eval_table.py" \
    --input "$REPO/artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet"

echo "P2_1_BASELINE_DONE"
