#!/usr/bin/env bash
# T6.2b — Apptainer pytest validation job for the spectral_unet_small_v1
# trainer code path.
#
# Scope:
#   * runs the torch import probe inside the project Apptainer image;
#   * runs --validate-only against configs/training/dry_run.yaml and
#     configs/training/full_training.yaml;
#   * runs the full tests/training/ pytest suite (login-node-only tests
#     plus the four torch-dependent test files added in T6.2b).
#
# Hard scope guards (must remain TRUE):
#   * CPU only. No GPU SBATCH flags. No --nv on apptainer exec.
#   * No --bind on apptainer exec. No --pwd on apptainer exec.
#   * No call to slurm/tools/on_submit.sh, sbatch, squeue, sacct, scancel,
#     sinfo, or scontrol from inside this job script (those wrappers run
#     OUTSIDE the job, on datamove1, when this script is submitted).
#   * Does not run training, Whisper, or enhancement.
#   * Does not modify trackers, configs, libs, or the model card.
#   * Submission is performed manually with:
#       ./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t6_2b_pytest_apptainer.sh
#     T6.2b CLOSURE does NOT submit this job; it is the gate that follows.

#SBATCH --job-name=asr_t6_2b_pytest
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2b_pytest_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2b_pytest_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G

set -euo pipefail

REPO=/mnt/fast/nobackup/users/gb0048/asr_enhancement
TRAIN_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
PREFIX=$TRAIN_ROOT/python_env/site-packages-py310
CONTAINER=/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
CACHE_ROOT=$TRAIN_ROOT/cache

mkdir -p "$TRAIN_ROOT/logs" "$CACHE_ROOT"

# --- Environment ---
# /mnt/fast/nobackup is auto-bound. CWD is not auto-mounted, so all paths
# passed into the container must be absolute.
cd "$REPO"

echo "=== T6.2b pytest job start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "REPO=$REPO"
echo "TRAIN_ROOT=$TRAIN_ROOT"
echo "PREFIX=$PREFIX"
echo "CONTAINER=$CONTAINER"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
echo "SLURM_NODELIST=${SLURM_NODELIST:-unset}"

apptainer_exec_python() {
  apptainer exec \
    --env PYTHONNOUSERSITE=1 \
    --env PYTHONPATH="$REPO:$PREFIX" \
    --env XDG_CACHE_HOME="$CACHE_ROOT" \
    --env ASR_REPO_ROOT="$REPO" \
    --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
    --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
    --env ASR_CACHE_ROOT="$CACHE_ROOT" \
    "$CONTAINER" \
    "$@"
}

# 1. Torch import probe.
echo "--- Step 1: torch import probe ---"
apptainer_exec_python python3 -s -c "import torch; print('TORCH_VERSION', torch.__version__)"

# 2. --validate-only on dry_run.yaml.
echo "--- Step 2: validate-only dry_run.yaml ---"
apptainer_exec_python python3 -s "$REPO/scripts/training/train_enhancer.py" \
  --config "$REPO/configs/training/dry_run.yaml" --validate-only

# 3. --validate-only on full_training.yaml.
echo "--- Step 3: validate-only full_training.yaml ---"
apptainer_exec_python python3 -s "$REPO/scripts/training/train_enhancer.py" \
  --config "$REPO/configs/training/full_training.yaml" --validate-only

# 4. Full tests/training/ pytest suite.
echo "--- Step 4: pytest tests/training/ ---"
apptainer_exec_python python3 -s -m pytest -q "$REPO/tests/training/"

echo "=== T6.2b pytest job end: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
