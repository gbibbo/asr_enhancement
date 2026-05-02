#!/usr/bin/env bash
#SBATCH --job-name=asr_t2_3b_reserve_demo
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_3b_reserve_demo_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_3b_reserve_demo_%j.err
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G

# T2.3b: Reserve 10 public demo examples from the dev-clean manifest.
#
# Two phases:
#   Phase A: select examples, validate set, write reserved_public_demo_examples.yaml.
#   Phase B: update public_examples_excluded.yaml to status: complete.
#
# Submit from datamove1 via the repo wrapper (sbatch is not in PATH on login nodes):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/reserve_public_demo_examples.sh
#
# Apptainer constraints (Surrey): user bind control disabled, --pwd disabled.
# Use absolute paths; pass variables via --env. No --nv (CPU only).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
REPO_PARENT="/mnt/fast/nobackup/users/gb0048"
CONTAINER="$REPO_PARENT/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"

MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1.jsonl"
SOURCES_CONFIG="$REPO/configs/training/librispeech_sources.yaml"
EXCLUSION_CONFIG="$REPO/configs/training/public_examples_excluded.yaml"
OUT_RESERVED="$REPO/configs/training/reserved_public_demo_examples.yaml"
SUMMARY_OUT="$TRAIN_ROOT/artifacts/t2_3b_reserve_${SLURM_JOB_ID:-local}.json"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/artifacts"

echo "=== T2.3b reserve public demo examples ==="
echo "Host:              $(hostname)"
echo "Date:              $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:         $CONTAINER"
echo "Repo:              $REPO"
echo "Manifest:          $MANIFEST"
echo "Sources config:    $SOURCES_CONFIG"
echo "Exclusion config:  $EXCLUSION_CONFIG"
echo "Out reserved:      $OUT_RESERVED"
echo "Summary:           $SUMMARY_OUT"
echo "==========================================="

cd "$REPO" || exit 1

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/reserve_public_demo_examples.py" \
    --manifest         "$MANIFEST" \
    --sources-config   "$SOURCES_CONFIG" \
    --exclusion-config "$EXCLUSION_CONFIG" \
    --out-reserved     "$OUT_RESERVED" \
    --summary          "$SUMMARY_OUT"

echo ""
echo "Summary artifact: $SUMMARY_OUT"
python3 -m json.tool "$SUMMARY_OUT"

echo ""
echo "=== T2.3b reserve step complete ==="
