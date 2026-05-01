#!/usr/bin/env bash
#SBATCH --job-name=asr_t0_minimal
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

# T0.5 minimal Slurm gate job for the ASR training branch.
#
# Submit from datamove1 via the repo wrapper:
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t0_minimal_job.sh
#
# All paths in this script are absolute. Surrey Apptainer disables user bind
# control, so the current working directory is NOT auto-mounted into the
# container; do not rely on $PWD inside the apptainer call.

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/runtime" "$TRAIN_ROOT/artifacts" "$TRAIN_ROOT/cache"

echo "=== T0.5 minimal Slurm gate job ==="
echo "Hostname: $(hostname)"
echo "Date: $(date -Iseconds)"
echo "Working directory (host, informational only): $(pwd)"
echo "Container: $CONTAINER"
echo
echo "--- Disk usage (head of df -h) ---"
df -h | head -n 5
echo
echo "--- Python version (inside Apptainer) ---"
apptainer exec \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  "$CONTAINER" \
  python3 -c "import sys, platform; print('Python:', sys.version.replace(chr(10), ' ')); print('Platform:', platform.platform())"

echo
echo "=== T0.5 minimal job complete ==="
