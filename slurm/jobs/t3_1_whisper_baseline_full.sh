#!/usr/bin/env bash
#SBATCH --job-name=asr_t3_1_baseline_full
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_1_whisper_baseline_full_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_1_whisper_baseline_full_%j.err
#SBATCH --time=06:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# T3.1 full run: all 2693 filtered records, base.en, CPU only.
# Submit only after the smoke run passes its gate.
#
# Submit from datamove1 via the repo wrapper:
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t3_1_whisper_baseline_full.sh
#
# Surrey Apptainer constraints: user bind control disabled, --pwd disabled.
# Use absolute paths; pass variables via --env. No --nv (CPU only).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
WHISPER_CACHE="$TRAIN_ROOT/cache/whisper"
RUN_DIR="$TRAIN_ROOT/runs/t3_1_baseline_full_${SLURM_JOB_ID:-local}"

mkdir -p "$RUN_DIR" "$TRAIN_ROOT/logs" "$TRAIN_ROOT/cache/whisper"

echo "=== T3.1 Whisper baseline (full) ==="
echo "Host:          $(hostname)"
echo "Date:          $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:     $CONTAINER"
echo "Repo:          $REPO"
echo "Prefix:        $PREFIX"
echo "Whisper cache: $WHISPER_CACHE"
echo "Run dir:       $RUN_DIR"
echo "Records:       2693 (full)"
echo "====================================="

cd "$REPO" || exit 1

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env WHISPER_CACHE="$WHISPER_CACHE" \
  --env XDG_CACHE_HOME="$TRAIN_ROOT/cache" \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/run_whisper_baseline.py" \
    --manifest      "$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl" \
    --exclusion-config         "$REPO/configs/training/public_examples_excluded.yaml" \
    --dataset-version-config   "$REPO/configs/training/dataset_version.yaml" \
    --model         base.en \
    --whisper-cache "$WHISPER_CACHE" \
    --out-dir       "$RUN_DIR" \
    --summary-md    "$REPO/reports/training/baseline_clean_wer.md"

echo ""
echo "=== T3.1 full baseline step complete ==="
echo "Run dir: $RUN_DIR"
