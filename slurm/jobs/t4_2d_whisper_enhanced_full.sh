#!/usr/bin/env bash
#SBATCH --job-name=asr_t4_2d_whisper_enhanced_full
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# T4.2d full run: 13 465 enhanced records (2693 x 5 families), base.en, CPU only.
# T4.2d smoke (job 2127690) ran at 4.480 s/record on aisurrey05, projecting
# ~16.76 h for the full 13 465 records. Wall-time set to 24 h to keep a safe
# margin without changing the runtime environment relative to T3.2 (CPU only,
# same container, same base.en model).
#
# Submit only AFTER the T4.2d smoke gate passes, and only via (NOT inside this script):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t4_2d_whisper_enhanced_full.sh
#
# Surrey Apptainer constraints: user bind control disabled, --pwd disabled.
# Use absolute paths; pass variables via --env. No --nv (CPU only).
# This committed form omits --summary-md; the committed report is produced at Gate D.

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
WHISPER_CACHE="$TRAIN_ROOT/cache/whisper"
RUN_DIR="$TRAIN_ROOT/runs/t4_2d_whisper_enhanced_full_${SLURM_JOB_ID:-local}"

ENHANCED_MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl"
DEGRADED_SOURCE_MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl"

mkdir -p "$RUN_DIR" "$TRAIN_ROOT/logs" "$TRAIN_ROOT/cache/whisper"

# Capture git state in the shell before entering Apptainer (git not in container).
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T4.2d Whisper enhanced eval (full) ==="
echo "Host:                     $(hostname)"
echo "Date:                     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:                $CONTAINER"
echo "Repo:                     $REPO"
echo "Prefix:                   $PREFIX"
echo "Whisper cache:            $WHISPER_CACHE"
echo "Run dir:                  $RUN_DIR"
echo "Enhanced manifest:        $ENHANCED_MANIFEST"
echo "Degraded source manifest: $DEGRADED_SOURCE_MANIFEST"
echo "Records:                  13 465 (2693 x 5 families)"
echo "=========================================="

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
  python3 -s "$REPO/scripts/training/run_whisper_enhanced.py" \
    --enhanced-manifest          "$ENHANCED_MANIFEST" \
    --degraded-source-manifest   "$DEGRADED_SOURCE_MANIFEST" \
    --exclusion-config           "$REPO/configs/training/public_examples_excluded.yaml" \
    --dataset-version-config     "$REPO/configs/training/dataset_version.yaml" \
    --reserved-demo-config       "$REPO/configs/training/reserved_public_demo_examples.yaml" \
    --clean-baseline-report      "$REPO/reports/training/baseline_clean_wer.md" \
    --degraded-baseline-report   "$REPO/reports/training/baseline_degraded_wer.md" \
    --model                      base.en \
    --whisper-cache              "$WHISPER_CACHE" \
    --out-dir                    "$RUN_DIR"

echo ""
echo "=== T4.2d full step complete ==="
echo "Run dir: $RUN_DIR"
