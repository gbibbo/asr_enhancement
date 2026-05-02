#!/usr/bin/env bash
#SBATCH --job-name=asr_t3_2_baseline_degraded_smoke
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2_baseline_degraded_smoke_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2_baseline_degraded_smoke_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# T3.2 smoke run: 5 utterance_ids x 5 families = 25 degraded records, base.en, CPU only.
#
# Submit from datamove1 via the repo wrapper:
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t3_2_whisper_baseline_degraded_smoke.sh
#
# Surrey Apptainer constraints: user bind control disabled, --pwd disabled.
# Use absolute paths; pass variables via --env. No --nv (CPU only).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
WHISPER_CACHE="$TRAIN_ROOT/cache/whisper"
RUN_DIR="$TRAIN_ROOT/runs/t3_2_baseline_degraded_smoke_${SLURM_JOB_ID:-local}"

mkdir -p "$RUN_DIR" "$TRAIN_ROOT/logs" "$TRAIN_ROOT/cache/whisper"

# Capture git state in the shell before entering Apptainer (git not in container).
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T3.2 Whisper degraded baseline (smoke) ==="
echo "Host:          $(hostname)"
echo "Date:          $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:     $CONTAINER"
echo "Repo:          $REPO"
echo "Prefix:        $PREFIX"
echo "Whisper cache: $WHISPER_CACHE"
echo "Run dir:       $RUN_DIR"
echo "Per-family:    5 utterance_ids (25 records total)"
echo "==============================================="

cd "$REPO" || exit 1

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env WHISPER_CACHE="$WHISPER_CACHE" \
  --env XDG_CACHE_HOME="$TRAIN_ROOT/cache" \
  --env ASR_REPO_ROOT="$REPO" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/run_whisper_baseline_degraded.py" \
    --manifest                "$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl" \
    --clean-source-manifest   "$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl" \
    --exclusion-config        "$REPO/configs/training/public_examples_excluded.yaml" \
    --dataset-version-config  "$REPO/configs/training/dataset_version.yaml" \
    --reserved-demo-config    "$REPO/configs/training/reserved_public_demo_examples.yaml" \
    --clean-baseline-report   "$REPO/reports/training/baseline_clean_wer.md" \
    --model                   base.en \
    --whisper-cache           "$WHISPER_CACHE" \
    --out-dir                 "$RUN_DIR" \
    --max-records-per-family  5

echo ""
echo "=== T3.2 smoke step complete ==="
echo "Run dir: $RUN_DIR"
