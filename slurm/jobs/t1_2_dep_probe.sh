#!/usr/bin/env bash
#SBATCH --job-name=asr_t1_2_probe
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

# T1.2 Stage A discovery probe.
#
# Submit from datamove1 via the repo wrapper (sbatch is not in PATH on the
# login node):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t1_2_dep_probe.sh
#
# Apptainer constraints (Surrey): user bind control disabled, --pwd
# disabled. Use absolute paths, pass variables via --env. No --nv (CPU
# probe). No install in this stage.

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
JSON_OUT="$TRAIN_ROOT/artifacts/t1_2_probe_${SLURM_JOB_ID:-local}.json"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runtime" \
  "$TRAIN_ROOT/artifacts" \
  "$TRAIN_ROOT/cache" \
  "$TRAIN_ROOT/python_env"

echo "=== T1.2 Stage A — discovery probe ==="
echo "Hostname  : $(hostname)"
echo "Date      : $(date -Iseconds)"
echo "Container : $CONTAINER"
echo "Repo      : $REPO"
echo "Prefix    : $PREFIX (read-only check; not installing in Stage A)"
echo "JSON out  : $JSON_OUT"
echo

apptainer exec \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env T1_2_PREFIX="$PREFIX" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/t1_2_imports_probe.py" \
    --mode probe \
    --strict-no-user-site \
    --out "$JSON_OUT" \
    --repo-root "$REPO" \
    --prefix "$PREFIX"

echo
echo "=== T1.2 Stage A complete ==="
