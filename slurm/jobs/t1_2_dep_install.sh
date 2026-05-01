#!/usr/bin/env bash
#SBATCH --job-name=asr_t1_2_install
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:25:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

# T1.2 Stage B + Stage C: clean dry-run resolution + exact no-deps install
# into an external prefix, then full origin verification.
#
# Submission (sbatch is not in PATH on datamove1):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t1_2_dep_install.sh
#
# Strict runtime discipline (carried forward from clean Stage A):
#   --env PYTHONNOUSERSITE=1
#   python3 -s
# Blocks ~/.local from satisfying any T1.2 import.
#
# Forbidden stack: torch, torchaudio, torchvision, torchtext, numpy, triton,
# nvidia-*. They must remain image-resident under /opt/conda. The clean
# dry-run lets pip see them in the active interpreter so it does not mark
# them for install. We then install only the exact set of distributions pip
# resolved to install, with --no-deps, so no second resolution pass can
# pull them back in.

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
PIP_CACHE="$TRAIN_ROOT/cache/pip"
JOBID="${SLURM_JOB_ID:-local}"
DRYRUN_REPORT="$TRAIN_ROOT/artifacts/t1_2_pip_dryrun_${JOBID}.json"
RESOLVED_SET="$TRAIN_ROOT/artifacts/t1_2_resolved_install_set_${JOBID}.txt"
JSON_OUT="$TRAIN_ROOT/artifacts/t1_2_verify_${JOBID}.json"
PIP_INSTALL_CMD_LOG="$TRAIN_ROOT/artifacts/t1_2_pip_install_cmd_${JOBID}.txt"

# pyproject [project] dependencies (T1.2 install target = these + openai-whisper).
# Keep in sync with pyproject.toml. T1.2 does NOT install the project itself.
PYPROJECT_DEPS=(
  "fastapi>=0.111"
  "uvicorn[standard]>=0.29"
  "celery[redis]>=5.4"
  "redis>=5.0"
  "psycopg[binary]>=3.1"
  "sqlalchemy>=2.0"
  "alembic>=1.13"
  "minio>=7.2"
  "pydantic-settings>=2.0"
  "python-multipart>=0.0.9"
  "httpx>=0.27"
  "soundfile>=0.12"
  "scipy>=1.11"
  "numpy>=1.24"
  "prometheus-client>=0.20"
  "opentelemetry-api>=1.24"
  "opentelemetry-sdk>=1.24"
  "opentelemetry-exporter-otlp-proto-http>=1.24"
  "opentelemetry-instrumentation-fastapi>=0.45b0"
)
EXTRA_DEPS=(
  "openai-whisper"
)

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/runtime" \
  "$TRAIN_ROOT/artifacts" \
  "$TRAIN_ROOT/cache" \
  "$PREFIX" \
  "$PIP_CACHE"

echo "=== T1.2 Stage B (revised) — clean dry-run + no-deps install ==="
echo "Hostname           : $(hostname)"
echo "Date               : $(date -Iseconds)"
echo "Container          : $CONTAINER"
echo "Repo               : $REPO"
echo "Prefix             : $PREFIX"
echo "Pip cache          : $PIP_CACHE"
echo "Dry-run report     : $DRYRUN_REPORT"
echo "Resolved set       : $RESOLVED_SET"
echo "Verify JSON        : $JSON_OUT"
echo
echo "--- pyproject deps (input to dry-run) ---"
printf '  %s\n' "${PYPROJECT_DEPS[@]}"
echo "--- extra deps ---"
printf '  %s\n' "${EXTRA_DEPS[@]}"
echo

# ---- writability sanity ----------------------------------------------------
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "import os, sys; sys.exit(0 if os.access('$PREFIX', os.W_OK) else 9)"

# ---- Stage B1: clean dry-run resolution -----------------------------------
# No --target, no --ignore-installed, no --user. Pip sees the active
# interpreter's site-packages, so anything already in /opt/conda (torch,
# torchaudio, numpy, …) will NOT appear in the install plan.
echo "--- pip dry-run (no --target; sees /opt/conda) ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_CACHE_DIR="$PIP_CACHE" \
  "$CONTAINER" \
  python3 -s -m pip install \
    --dry-run \
    --report "$DRYRUN_REPORT" \
    --quiet \
    "${PYPROJECT_DEPS[@]}" \
    "${EXTRA_DEPS[@]}"

echo "Dry-run report written: $DRYRUN_REPORT"
ls -la "$DRYRUN_REPORT"
echo

# ---- Stage B2: parse report, build resolved-set file, forbidden-stack guard
echo "--- parse dry-run, build resolved set, enforce forbidden stack ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import json, re, sys
report_path = '$DRYRUN_REPORT'
out_path    = '$RESOLVED_SET'
forbidden_exact = {'torch', 'torchaudio', 'torchvision', 'torchtext', 'numpy', 'triton'}

def norm(name):
    return re.sub(r'[-_.]+', '-', name).lower()

with open(report_path) as f:
    report = json.load(f)

installs = report.get('install', []) or []
resolved = []
forbidden_hits = []
for entry in installs:
    meta = entry.get('metadata') or {}
    name = meta.get('name')
    version = meta.get('version')
    if not name or not version:
        continue
    n = norm(name)
    if n in forbidden_exact or n.startswith('nvidia-'):
        forbidden_hits.append({'name': name, 'normalized': n, 'version': version})
        continue
    resolved.append((name, version))

if forbidden_hits:
    print('FORBIDDEN STACK in dry-run plan:')
    for h in forbidden_hits:
        print(f'  {h[\"name\"]} (norm={h[\"normalized\"]}) {h[\"version\"]}')
    print('BLOCKER: dryrun_requires_forbidden_stack')
    sys.exit(20)

with open(out_path, 'w') as f:
    for name, version in sorted(resolved, key=lambda x: x[0].lower()):
        f.write(f'{name}=={version}\n')

print(f'Resolved install set ({len(resolved)} packages):')
for name, version in sorted(resolved, key=lambda x: x[0].lower()):
    print(f'  {name}=={version}')
"

echo
echo "--- resolved-set file ---"
ls -la "$RESOLVED_SET"
echo "--- file contents ---"
cat "$RESOLVED_SET"
echo

# ---- Stage B3: install exact pins with --no-deps --------------------------
PIP_INSTALL_CMD=(
  python3 -s -m pip install
  --no-warn-script-location
  --target "$PREFIX"
  --cache-dir "$PIP_CACHE"
  --no-deps
  -r "$RESOLVED_SET"
)
{
  echo "# T1.2 pip install command (recorded for tracker evidence)"
  printf '%q ' "${PIP_INSTALL_CMD[@]}"; echo
} > "$PIP_INSTALL_CMD_LOG"
echo "--- pip install (--no-deps, exact pins) ---"
cat "$PIP_INSTALL_CMD_LOG"

set -x
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_CACHE_DIR="$PIP_CACHE" \
  "$CONTAINER" \
  "${PIP_INSTALL_CMD[@]}"
set +x

echo
echo "=== T1.2 Stage B install complete ==="
echo

# ---- Post-install forbidden-path guard ------------------------------------
echo "--- post-install forbidden-path guard ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import os, re, sys
prefix = '$PREFIX'
forbidden_dir_names   = {'torch', 'torchaudio', 'torchvision', 'torchtext', 'numpy', 'numpy.libs', 'triton', 'nvidia'}
forbidden_dist_prefix = ('torch-', 'torchaudio-', 'torchvision-', 'torchtext-', 'numpy-', 'triton-', 'nvidia-')
def norm(s):
    return re.sub(r'[-_.]+', '-', s).lower()
violations = []
if not os.path.isdir(prefix):
    print(f'PREFIX missing: {prefix}')
    sys.exit(10)
for name in sorted(os.listdir(prefix)):
    full = os.path.join(prefix, name)
    if name in forbidden_dir_names and os.path.isdir(full):
        violations.append(('forbidden_dir', name, full))
    n_lower = name.lower()
    if any(n_lower.startswith(p) for p in forbidden_dist_prefix) and (
        name.endswith('.dist-info') or name.endswith('.data')
    ):
        violations.append(('forbidden_distinfo', name, full))
if violations:
    print('FORBIDDEN-PATH VIOLATIONS:')
    for kind, name, full in violations:
        print(f'  {kind:20s} {name:40s} {full}')
    print('BLOCKER: forbidden_stack_shadowed_in_prefix')
    sys.exit(7)
print('OK: no forbidden paths under PREFIX')
"

# ---- Stage C verify -------------------------------------------------------
echo
echo "=== T1.2 Stage C — verify ==="
echo "PYTHONPATH (runtime): $REPO:$PREFIX"
echo "JSON out             : $JSON_OUT"
echo

apptainer exec \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env T1_2_PREFIX="$PREFIX" \
  --env SLURM_JOB_ID="$JOBID" \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/t1_2_imports_probe.py" \
    --mode verify \
    --strict-no-user-site \
    --expected-torch-version 2.1.0 \
    --expected-torchaudio-version 2.1.0 \
    --expected-numpy-version 1.26.0 \
    --out "$JSON_OUT" \
    --repo-root "$REPO" \
    --prefix "$PREFIX"

echo
echo "=== T1.2 Stage C complete ==="
