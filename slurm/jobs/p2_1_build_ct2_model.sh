#!/usr/bin/env bash
#SBATCH --job-name=asr_p2_1_build_ct2
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --partition=2080ti

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/runtime/whisper_models"

CONTAINER_SHA=$(sha256sum "$CONTAINER" | awk '{print $1}')
echo "container_sha256=$CONTAINER_SHA"

cd "$REPO"

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_USER=0 \
  --env PYTHONPATH="" \
  --env PYTHONUSERBASE="" \
  --env APPTAINER_CONTAINER_SHA256="$CONTAINER_SHA" \
  --env HF_HOME="$TRAIN_ROOT/cache/huggingface" \
  --env TRANSFORMERS_CACHE="$TRAIN_ROOT/cache/huggingface" \
  --env HF_HUB_DOWNLOAD_TIMEOUT=120 \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/build_whisper_base_ct2_int8.py" \
    --source "$TRAIN_ROOT/cache/whisper/base.en.pt" \
    --output "$TRAIN_ROOT/runtime/whisper_models/whisper_base_en_ct2_int8" \
    --quantization int8

echo "P2_1_BUILD_CT2_DONE"
