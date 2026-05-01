#!/usr/bin/env bash
#SBATCH --job-name=asr_t1_3_audio_probe
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t1_3_audio_probe_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t1_3_audio_probe_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

# T1.3 audio processing gate probe.
#
# Generates a synthetic WAV, processes it through
# libs.audio_pipeline.pipeline.apply_preset("denoise"), validates the
# output, checks import origins and user-site isolation, writes JSON
# evidence.
#
# Submit from datamove1 via the repo wrapper (sbatch is not in PATH on the
# login node):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t1_3_audio_probe.sh
#
# Apptainer constraints (Surrey): user bind control disabled, --pwd
# disabled. Use absolute paths, pass variables via --env. No --nv (CPU
# only — no GPU needed for DSP).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"

INPUT_WAV="$TRAIN_ROOT/artifacts/t1_3_input_${SLURM_JOB_ID:-local}.wav"
OUTPUT_DIR="$TRAIN_ROOT/artifacts/t1_3_audio_output_${SLURM_JOB_ID:-local}"
JSON_OUT="$TRAIN_ROOT/artifacts/t1_3_probe_${SLURM_JOB_ID:-local}.json"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runtime" \
  "$TRAIN_ROOT/artifacts" \
  "$TRAIN_ROOT/cache"

echo "=== T1.3 audio processing probe ==="
echo "Hostname   : $(hostname)"
echo "Date       : $(date -Iseconds)"
echo "Container  : $CONTAINER"
echo "Repo       : $REPO"
echo "Prefix     : $PREFIX"
echo "Input WAV  : $INPUT_WAV"
echo "Output dir : $OUTPUT_DIR"
echo "JSON out   : $JSON_OUT"
echo

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/t1_3_audio_probe.py" \
    --out        "$JSON_OUT" \
    --input-wav  "$INPUT_WAV" \
    --output-dir "$OUTPUT_DIR"

echo
echo "=== T1.3 audio processing probe complete ==="
