#!/usr/bin/env bash
#SBATCH --job-name=asr_t3_2a_bank_smoke
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2a_degradation_bank_smoke_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2a_degradation_bank_smoke_%j.err
#SBATCH --time=00:20:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

# T3.2a smoke run: 10 records x 5 families = 50 degraded WAV files.
# Submit only via:
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t3_2a_degradation_bank_smoke.sh
# Surrey constraints: --bind disabled, --pwd disabled. CPU-only (no --gres, no --nv).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
JID="${SLURM_JOB_ID:-local}"

RUN_DIR="$TRAIN_ROOT/runs/t3_2a_bank_smoke_${JID}"
STAGING_AUDIO_ROOT="$TRAIN_ROOT/datasets/degraded_build/degradation_v1_smoke_${JID}"
STAGING_MANIFEST_TMP="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_smoke_${JID}.jsonl.tmp"
FINAL_AUDIO_ROOT="$TRAIN_ROOT/datasets/degraded_smoke/degradation_v1"
FINAL_MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_smoke.jsonl"

mkdir -p "$RUN_DIR" "$TRAIN_ROOT/logs"
# Do NOT pre-create staging or final audio roots — the script must verify they are absent.
cd "$REPO" || exit 1

GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T3.2a degradation bank (smoke) ==="
echo "Host:          $(hostname)"
echo "Date:          $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:     $CONTAINER"
echo "Repo:          $REPO"
echo "Run dir:       $RUN_DIR"
echo "Staging audio: $STAGING_AUDIO_ROOT"
echo "Staging manif: $STAGING_MANIFEST_TMP"
echo "Final audio:   $FINAL_AUDIO_ROOT"
echo "Final manif:   $FINAL_MANIFEST"
echo "======================================"

df -h "$TRAIN_ROOT" || true

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env XDG_CACHE_HOME="$TRAIN_ROOT/cache" \
  --env ASR_REPO_ROOT="$REPO" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/build_degradation_bank.py" \
    --manifest                "$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl" \
    --exclusion-config        "$REPO/configs/training/public_examples_excluded.yaml" \
    --dataset-version-config  "$REPO/configs/training/dataset_version.yaml" \
    --mode                    smoke \
    --staging-audio-root      "$STAGING_AUDIO_ROOT" \
    --staging-manifest-tmp    "$STAGING_MANIFEST_TMP" \
    --final-audio-root        "$FINAL_AUDIO_ROOT" \
    --final-degraded-manifest "$FINAL_MANIFEST" \
    --out-dir                 "$RUN_DIR" \
    --max-records             10 \
    --validation-sample-size  50

echo ""
echo "=== T3.2a smoke step complete ==="
echo "Run dir: $RUN_DIR"
