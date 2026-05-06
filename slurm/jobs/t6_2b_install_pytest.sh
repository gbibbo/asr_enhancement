#!/usr/bin/env bash
# T6.2b — install pytest and its explicit non-forbidden dependencies into the
# T1.2 dependency prefix at $PREFIX, using a controlled apptainer-based pip
# install with `--target $PREFIX --no-deps`. Required because the project
# Apptainer image (`pytorch_2.1_cuda12.sif`) ships torch but does NOT ship
# pytest, and the T1.2 prefix was built `--no-deps` against an explicit
# resolved set that excluded pytest. This job adds pytest only.
#
# Hard scope guards (must remain TRUE):
#   * CPU only. No GPU SBATCH flags. No --nv on apptainer exec.
#   * No --bind on apptainer exec. No --pwd on apptainer exec.
#   * No call to slurm/tools/on_submit.sh, sbatch, squeue, sacct, scancel,
#     sinfo, or scontrol from inside this job script (those wrappers run
#     OUTSIDE the job, on datamove1, when this script is submitted).
#   * Does not run training, Whisper, or enhancement.
#   * Does not modify trackers, configs, libs, or the model card.
#   * Forbidden-stack guard runs BEFORE and AFTER the pip install. If any of
#     [torch, torchaudio, torchvision, torchtext, numpy, triton, nvidia-*]
#     appears in $PREFIX, the job aborts with a BLOCKER message.
#   * Submission is performed manually with:
#       ./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t6_2b_install_pytest.sh

#SBATCH --job-name=asr_t6_2b_install_pytest
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2b_install_pytest_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t6_2b_install_pytest_%j.err
#SBATCH --time=00:15:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

set -euo pipefail

REPO=/mnt/fast/nobackup/users/gb0048/asr_enhancement
TRAIN_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
PREFIX=$TRAIN_ROOT/python_env/site-packages-py310
CONTAINER=/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
CACHE_ROOT=$TRAIN_ROOT/cache
PIP_CACHE=$CACHE_ROOT/pip
ARTIFACT_DIR=$TRAIN_ROOT/artifacts

mkdir -p "$TRAIN_ROOT/logs" "$CACHE_ROOT" "$PIP_CACHE" "$ARTIFACT_DIR" "$PREFIX"

cd "$REPO"

# Forbidden packages — must NEVER be installed into the T1.2 prefix.
FORBIDDEN_PKGS=(torch torchaudio torchvision torchtext numpy triton)

# Explicit package list to install --no-deps into $PREFIX. Versions match
# the user-approved spec for T6.2b. None of these are in FORBIDDEN_PKGS.
PACKAGES=(
  "pytest==8.4.2"
  "pluggy==1.6.0"
  "iniconfig==2.1.0"
  "packaging==25.0"
  "tomli==2.2.1"
  "exceptiongroup==1.3.0"
)

apptainer_exec_python() {
  apptainer exec \
    --env PYTHONNOUSERSITE=1 \
    --env PYTHONPATH="$REPO:$PREFIX" \
    --env XDG_CACHE_HOME="$CACHE_ROOT" \
    --env PIP_CACHE_DIR="$PIP_CACHE" \
    --env ASR_REPO_ROOT="$REPO" \
    --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
    --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
    --env ASR_CACHE_ROOT="$CACHE_ROOT" \
    "$CONTAINER" \
    "$@"
}

# Forbidden-stack guard. Returns 0 if any forbidden package is present in
# $PREFIX, 1 if clean. Hits are printed on stdout for diagnostics.
forbidden_in_prefix() {
  local hits=()
  local pkg
  for pkg in "${FORBIDDEN_PKGS[@]}"; do
    # Match pure import directory: $PREFIX/<pkg>/
    if [ -d "$PREFIX/$pkg" ]; then
      hits+=("dir:$pkg")
    fi
    # Match dist-info: $PREFIX/<pkg>-<ver>.dist-info/
    local di
    for di in "$PREFIX/${pkg}"-*.dist-info; do
      [ -e "$di" ] && hits+=("dist-info:$(basename "$di")")
    done
  done
  # Match nvidia-* / nvidia_* (pip normalizes hyphens to underscores).
  local nv
  for nv in "$PREFIX"/nvidia*; do
    [ -e "$nv" ] && hits+=("nvidia:$(basename "$nv")")
  done
  if [ "${#hits[@]}" -gt 0 ]; then
    printf 'FORBIDDEN_HIT: %s\n' "${hits[@]}"
    return 0
  fi
  return 1
}

echo "=== T6.2b install pytest job start: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "REPO=$REPO"
echo "TRAIN_ROOT=$TRAIN_ROOT"
echo "PREFIX=$PREFIX"
echo "CONTAINER=$CONTAINER"
echo "PIP_CACHE=$PIP_CACHE"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
echo "SLURM_NODELIST=${SLURM_NODELIST:-unset}"

echo "--- Step 1: forbidden-stack pre-check on PREFIX ---"
if forbidden_in_prefix; then
  echo "BLOCKER: forbidden stack present in PREFIX BEFORE install. Abort." >&2
  exit 2
fi
echo "OK: no forbidden stack in PREFIX before install"

echo "--- Step 2: pre-install python + torch probe ---"
apptainer_exec_python python3 -s -c "import sys, torch; print('PY', sys.version.split()[0]); print('TORCH', torch.__version__, torch.__file__)"

echo "--- Step 3: pip install --target $PREFIX --no-deps for explicit list ---"
echo "Packages:"
printf '  - %s\n' "${PACKAGES[@]}"
# `--upgrade` is included because $PREFIX already contains exceptiongroup-1.3.1
# from the original T1.2 install; without `--upgrade`, pip refuses to replace
# the existing version in the target dir. `--no-deps` and `--target` remain
# as required by T6.2b. No package outside the explicit list is installed.
apptainer_exec_python python3 -s -m pip install \
  --no-warn-script-location \
  --target "$PREFIX" \
  --cache-dir "$PIP_CACHE" \
  --no-deps \
  --upgrade \
  "${PACKAGES[@]}"

echo "--- Step 4: forbidden-stack post-check on PREFIX ---"
if forbidden_in_prefix; then
  echo "BLOCKER: forbidden stack present in PREFIX AFTER install. Abort." >&2
  exit 3
fi
echo "OK: no forbidden stack in PREFIX after install"

echo "--- Step 5: import verification ---"
apptainer_exec_python python3 -s -c "import pytest, pluggy, iniconfig, packaging; print('PYTEST_VERSION', pytest.__version__)"
apptainer_exec_python python3 -s -c "import torch; print('TORCH_FROM', torch.__version__, torch.__file__)"
apptainer_exec_python python3 -s -c "import pytest; print('PYTEST_FROM', pytest.__file__)"

echo "--- Step 6: assert pytest comes from PREFIX, torch comes from /opt/conda ---"
apptainer_exec_python python3 -s -c "
import os, sys, pytest, torch
prefix = os.environ.get('PYTHONPATH','').split(':')[-1]
assert pytest.__file__.startswith(prefix), f'pytest not from PREFIX: {pytest.__file__} vs {prefix}'
assert torch.__file__.startswith('/opt/conda'), f'torch not from /opt/conda: {torch.__file__}'
print('OK: pytest from PREFIX, torch from /opt/conda')
"

echo "--- Step 7: write JSON verification artifact ---"
ARTIFACT_PATH="$ARTIFACT_DIR/t6_2b_pytest_install_verify_${SLURM_JOB_ID:-local}.json"
echo "ARTIFACT_PATH=$ARTIFACT_PATH"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env XDG_CACHE_HOME="$CACHE_ROOT" \
  --env PIP_CACHE_DIR="$PIP_CACHE" \
  --env VERIFY_OUT_PATH="$ARTIFACT_PATH" \
  --env VERIFY_PREFIX="$PREFIX" \
  --env VERIFY_JOB_ID="${SLURM_JOB_ID:-local}" \
  "$CONTAINER" \
  python3 -s -c "
import importlib, json, os, sys
out = {
    'job_id': os.environ['VERIFY_JOB_ID'],
    'python': sys.version.split()[0],
    'prefix': os.environ['VERIFY_PREFIX'],
    'modules': {},
}
mods = ['pytest', 'pluggy', 'iniconfig', 'packaging', 'tomli', 'exceptiongroup', 'torch']
for m in mods:
    try:
        mod = importlib.import_module(m)
        out['modules'][m] = {
            'version': getattr(mod, '__version__', None),
            'file': getattr(mod, '__file__', None),
        }
    except Exception as exc:
        out['modules'][m] = {'error': repr(exc)}
out['artifact_path'] = os.environ['VERIFY_OUT_PATH']
with open(os.environ['VERIFY_OUT_PATH'], 'w') as f:
    json.dump(out, f, indent=2, sort_keys=True)
print('VERIFY_JSON', os.environ['VERIFY_OUT_PATH'])
"

echo "=== T6.2b install pytest job end: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
