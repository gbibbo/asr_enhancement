#!/usr/bin/env bash
#SBATCH --job-name=asr_t2_3_exclude_examples
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_3_exclude_examples_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_3_exclude_examples_%j.err
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
REPO_PARENT="/mnt/fast/nobackup/users/gb0048"
CONTAINER="$REPO_PARENT/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"

CONFIG_EXCL="$REPO/configs/training/public_examples_excluded.yaml"
SOURCE_MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1.jsonl"
OUT_MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl"
SUMMARY_OUT="$TRAIN_ROOT/artifacts/t2_3_exclude_summary_${SLURM_JOB_ID:-local}.json"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/artifacts"

echo "=== T2.3 exclude public examples ==="
echo "Host:            $(hostname)"
echo "Date:            $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:       $CONTAINER"
echo "Config:          $CONFIG_EXCL"
echo "Source manifest: $SOURCE_MANIFEST"
echo "Out manifest:    $OUT_MANIFEST  (not written in placeholder mode)"
echo "Summary:         $SUMMARY_OUT"
echo "====================================="

cd "$REPO" || exit 1

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/t2_3_exclude_public_examples.py" \
    --config "$CONFIG_EXCL" \
    --source-manifest "$SOURCE_MANIFEST" \
    --out-manifest "$OUT_MANIFEST" \
    --summary "$SUMMARY_OUT"

echo ""
echo "Summary artifact: $SUMMARY_OUT"
python3 -m json.tool "$SUMMARY_OUT"

echo ""
echo "=== T2.3 exclusion step complete ==="
