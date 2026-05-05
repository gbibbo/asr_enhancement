#!/usr/bin/env bash
#SBATCH --job-name=asr_t5_3_dry_run
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t5_3_dry_run_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t5_3_dry_run_%j.err
#SBATCH --time=00:45:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G

# T5.3 — Phase 5 dry-run training job (docs/plans/training_datamove1_plan.md §15).
#
# Runs scripts/training/train_enhancer.py with configs/training/dry_run.yaml
# inside the Apptainer container. The script enforces all `guards:` from the
# config (steps<=200, version match against libs/common/versions.py and
# configs/training/dataset_version.yaml, reserved-demo-IDs absent, run dir
# outside repo) and writes the six required artifacts under
# $TRAIN_ROOT/runs/t5_3_dry_run_<job_id>/.
#
# CPU only. No --nv. No --bind. No --pwd. No GPU. No Whisper. No enhancement.
# This job must not submit other jobs and must not update trackers.
#
# Submit from datamove1 via the repo wrapper (sbatch is not in PATH on
# datamove1; the wrapper forwards to aisurrey-submit01.surrey.ac.uk):
#
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t5_3_dry_run.sh
#
# Surrey Apptainer constraints (CLAUDE.md §8):
#   * "user bind control is disabled by system administrator" — the current
#     working directory is NOT auto-mounted into the container.
#   * Use absolute paths inside the container; do not rely on $PWD.
#   * Pass variables through --env.

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
CACHE_ROOT="$TRAIN_ROOT/cache"
JOBID="${SLURM_JOB_ID:-local}"
RUN_DIR="$TRAIN_ROOT/runs/t5_3_dry_run_${JOBID}"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runs" \
  "$TRAIN_ROOT/runtime" \
  "$TRAIN_ROOT/artifacts" \
  "$CACHE_ROOT"

# Capture git state in the shell before entering Apptainer (git is not in the
# container). train_enhancer.py reads GIT_COMMIT_AT_RUN / GIT_BRANCH_AT_RUN
# from the environment first and falls back to its own `git` subprocess only
# for local non-Slurm runs.
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH_AT_RUN=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T5.3 dry-run on Slurm ==="
echo "Host:                 $(hostname)"
echo "Date:                 $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:            $CONTAINER"
echo "Repo:                 $REPO"
echo "Prefix:               $PREFIX"
echo "Train root:           $TRAIN_ROOT"
echo "Cache root:           $CACHE_ROOT"
echo "Slurm job id:         $JOBID"
echo "Expected run dir:     $RUN_DIR"
echo "Git commit at run:    $GIT_COMMIT_AT_RUN"
echo "Git branch at run:    $GIT_BRANCH_AT_RUN"
echo "Git status (short):   ${GIT_STATUS_SHORT_AT_RUN:-clean}"
echo "============================="

cd "$REPO" || exit 1

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$CACHE_ROOT" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_BRANCH_AT_RUN="$GIT_BRANCH_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/train_enhancer.py" \
    --config "$REPO/configs/training/dry_run.yaml"

rc=$?
echo ""
echo "=== T5.3 dry-run script exit: $rc ==="
echo "Run dir: $RUN_DIR"
exit "$rc"
