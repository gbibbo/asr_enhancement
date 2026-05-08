#!/usr/bin/env bash
#SBATCH --job-name=robust_asr_p1_4_build_degradation_v1
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=06:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --partition=2080ti

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/datasets/degradation_v1"

cd "$REPO"

echo "---ENV---"
echo "host=$(hostname)"
echo "container_sha256=$(sha256sum "$CONTAINER" | awk '{print $1}')"
echo "free_scratch_gb=$(df -BG --output=avail "$TRAIN_ROOT/datasets" | tail -1 | tr -d 'G ')"

echo "---BUILD_DEGRADATION_V1---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH= \
  --env PYTHONUSERBASE= \
  --env PIP_USER=0 \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/build_degradation_v1.py" \
    --config "$REPO/configs/robust_asr/degradation_v1.yaml" \
    --workers 16

echo "---DONE---"
