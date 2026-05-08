#!/usr/bin/env bash
#SBATCH --job-name=robust_asr_p0_4_contract_smoke
#SBATCH --output=/mnt/fast/nobackup/users/gb0048/asr_enhancement/artifacts/robust_asr/runtime_contract/p0_4_contract_smoke_%j.out
#SBATCH --error=/mnt/fast/nobackup/users/gb0048/asr_enhancement/artifacts/robust_asr/runtime_contract/p0_4_contract_smoke_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif"

cd "$REPO"

echo "---VALIDATOR---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH= \
  --env PYTHONUSERBASE= \
  --env PIP_USER=0 \
  "$CONTAINER" \
  python3 "$REPO/scripts/robust_asr/validate_runtime_contract.py" \
    --strict-skeleton \
    --request "$REPO/artifacts/robust_asr/runtime_contract/rp5_request_fixture.json" \
    --response "$REPO/artifacts/robust_asr/runtime_contract/rp5_response_fixture.json"

echo "---PYTEST---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH= \
  --env PYTHONUSERBASE= \
  --env PIP_USER=0 \
  "$CONTAINER" \
  python3 -m pytest -q "$REPO/tests/robust_asr/test_runtime_contract_skeleton.py"

echo "---DONE---"
