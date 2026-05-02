#!/usr/bin/env bash
#SBATCH --job-name=asr_t2_4_dataset_version
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_4_dataset_version_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_4_dataset_version_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G

# T2.4: Define dataset version and record manifest SHA-256.
#
# Reads librispeech_sources.yaml and public_examples_excluded.yaml, counts
# manifest lines, computes SHA-256, and writes configs/training/dataset_version.yaml
# plus reports/training/dataset_version_v1.md into the repo.
#
# Submit from datamove1 via the repo wrapper (sbatch is not in PATH on login nodes):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t2_4_define_dataset_version.sh
#
# Apptainer constraints (Surrey): user bind control disabled, --pwd disabled.
# Use absolute paths; pass variables via --env. No --nv (CPU only).

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"

SOURCES_CONFIG="$REPO/configs/training/librispeech_sources.yaml"
EXCLUSION_CONFIG="$REPO/configs/training/public_examples_excluded.yaml"
# After T2.3b the active dataset manifest is the filtered manifest (2693 records).
# The original source manifest (librispeech_manifest_v1.jsonl, 2703 records) is unchanged
# and preserved at scratch but is no longer the active dataset for T3.1 onwards.
MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl"
OUT_CONFIG="$REPO/configs/training/dataset_version.yaml"
REPORT_OUT="$REPO/reports/training/dataset_version_v1.md"
SUMMARY_OUT="$TRAIN_ROOT/artifacts/t2_4_dataset_version_${SLURM_JOB_ID:-local}.json"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/artifacts"

echo "=== T2.4 define dataset version ==="
echo "Host:              $(hostname)"
echo "Date:              $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container:         $CONTAINER"
echo "Repo:              $REPO"
echo "Sources config:    $SOURCES_CONFIG"
echo "Exclusion config:  $EXCLUSION_CONFIG"
echo "Manifest:          $MANIFEST"
echo "Out config:        $OUT_CONFIG"
echo "Report:            $REPORT_OUT"
echo "Summary:           $SUMMARY_OUT"
echo "===================================="

cd "$REPO" || exit 1

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  --env SLURM_JOB_ID="${SLURM_JOB_ID:-}" \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/t2_4_define_dataset_version.py" \
    --sources-config   "$SOURCES_CONFIG" \
    --exclusion-config "$EXCLUSION_CONFIG" \
    --manifest         "$MANIFEST" \
    --out-config       "$OUT_CONFIG" \
    --report           "$REPORT_OUT" \
    --summary          "$SUMMARY_OUT"

echo ""
echo "=== Shell-side YAML validation (inside Apptainer) ==="
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="${REPO}:${PREFIX}" \
  "$CONTAINER" \
  python3 -s -c "
import yaml, sys
d = yaml.safe_load(open('${OUT_CONFIG}'))
assert d['dataset_version'], 'missing dataset_version'
assert len(d['manifest']['sha256']) == 64, 'sha256 must be 64 hex chars'
assert d['manifest']['records'] == 2693, f'records mismatch: {d[\"manifest\"][\"records\"]}'
assert d['exclusion_policy']['status'] == 'complete', f'expected complete, got {d[\"exclusion_policy\"][\"status\"]}'
assert d['exclusion_policy']['t3_blocked_while_pending'] == False, 't3 gate must be False after complete'
sha_prefix = d['manifest']['sha256'][:12]
assert sha_prefix in d['dataset_version'], 'sha256 prefix not in version string'
assert 'excl10' in d['dataset_version'], 'excl10 tag not in version string'
print('version:      ', d['dataset_version'])
print('sha256:       ', d['manifest']['sha256'])
print('records:      ', d['manifest']['records'])
print('excl_status:  ', d['exclusion_policy']['status'])
print('YAML validation: OK')
"

echo ""
echo "Summary artifact: $SUMMARY_OUT"

echo ""
echo "=== T2.4 dataset version step complete ==="
