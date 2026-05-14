#!/usr/bin/env bash
#SBATCH --job-name=asr_p8_1_system_eval
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs"

cd "$REPO"

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_USER=0 \
  --env PYTHONPATH="" \
  --env PYTHONUSERBASE="" \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/evaluate_system.py" \
    --selected-router "$REPO/artifacts/robust_asr/router/selected_router" \
    --selector-evidence "$REPO/artifacts/robust_asr/router/selector_evidence.parquet" \
    --backend-tables "$REPO/artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet" \
    --baselines whisper_base_ct2_int8 \
    --profile battery_aware \
    --bootstrap-iterations 10000 \
    --bootstrap-method bca \
    --rng-seed 20250514 \
    --ask-repeat-wer 1.0 \
    --ask-repeat-wer-sensitivity 0.5 \
    --out "$REPO/reports/robust_asr/system/system_eval.md"

echo "P8_1_SYSTEM_EVAL_DONE"
