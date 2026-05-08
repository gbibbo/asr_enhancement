#!/usr/bin/env bash
#SBATCH --job-name=robust_asr_p0_3_build_runtime_image
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/build_logs/p0_3_build_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/build_logs/p0_3_build_%j.err
#SBATCH --time=01:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
RUNTIME_DIR="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime"

export ASR_REPO_ROOT="${REPO}"

mkdir -p "${RUNTIME_DIR}/build_logs" "${RUNTIME_DIR}/build_cache"

cd "${REPO}"

bash "${REPO}/scripts/robust_asr/build_runtime_image.sh"
