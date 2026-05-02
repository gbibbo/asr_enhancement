#!/usr/bin/env bash
#SBATCH --job-name=asr_t2_2_build_manifest
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_2_build_manifest_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_2_build_manifest_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

# T2.2 LibriSpeech manifest generation.
#
# Reads configs/training/librispeech_sources.yaml, pre-scans config-present
# splits for usability (FLAC + transcript files), and writes a JSONL manifest
# with duration_seconds and sample_rate from soundfile.info() header reads.
#
# Strict failure policy: missing FLAC, soundfile error, duplicate utterance_id,
# sample_rate != 16000, or validation failure all cause exit 1 with no manifest
# written.
#
# Submit from datamove1 via the repo wrapper (sbatch is not in PATH on the
# login node):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t2_2_build_manifest.sh
#
# Apptainer constraints (Surrey): user bind control disabled, --pwd disabled.
# Use absolute paths; pass variables via --env. No --nv (CPU only).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"

CONFIG="$REPO/configs/training/librispeech_sources.yaml"
MANIFEST_OUT="$TRAIN_ROOT/datasets/librispeech_manifest_v1.jsonl"
SUMMARY_OUT="$TRAIN_ROOT/artifacts/t2_2_manifest_summary_${SLURM_JOB_ID:-local}.json"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/artifacts" \
  "$TRAIN_ROOT/datasets"

echo "=== T2.2 LibriSpeech manifest build ==="
echo "Hostname     : $(hostname)"
echo "Date         : $(date -Iseconds)"
echo "Container    : $CONTAINER"
echo "Repo         : $REPO"
echo "Prefix       : $PREFIX"
echo "Config       : $CONFIG"
echo "Manifest out : $MANIFEST_OUT"
echo "Summary out  : $SUMMARY_OUT"
echo

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/t2_2_build_manifest.py" \
    --config        "$CONFIG" \
    --out-manifest  "$MANIFEST_OUT" \
    --summary       "$SUMMARY_OUT"

echo
echo "=== Shell-side manifest validation ==="
echo "Line count:"
wc -l "$MANIFEST_OUT"
echo
echo "First 2 records:"
head -2 "$MANIFEST_OUT"
echo
echo "Last 2 records:"
tail -2 "$MANIFEST_OUT"
echo

echo "=== T2.2 manifest build complete ==="
