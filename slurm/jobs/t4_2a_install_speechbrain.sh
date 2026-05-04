#!/usr/bin/env bash
#SBATCH --job-name=asr_t4_2a_install_speechbrain
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

# T4.2a: Install the SpeechBrain optional stack into PREFIX, validate imports
# and module origins inside Apptainer, and write a verify JSON for tracker evidence.
#
# Steps when submitted:
#   1. pip dry-run (no --target; sees /opt/conda) — resolves what needs installing
#   2. Parse dry-run report; apply forbidden-stack guard; write filtered set
#   3. pip install --no-deps --target PREFIX using exact filtered pins
#   4a. Post-install forbidden-path guard (walks PREFIX for contamination)
#   4b. Import + origin validation; write t4_2a_verify_<JID>.json
#
# This job does NOT run enhancement, Whisper, or any other Slurm job.
# It does NOT modify repo files or update trackers.
#
# Strict runtime discipline (carried forward from T1.2):
#   --env PYTHONNOUSERSITE=1
#   python3 -s
#   PYTHONPATH="$REPO:$PREFIX"
#
# Forbidden stack — must remain image-resident under /opt/conda, never in PREFIX:
#   torch  torchaudio  torchvision  torchtext  numpy  triton  nvidia-*
#
# Submission (sbatch is not in PATH on datamove1):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t4_2a_install_speechbrain.sh

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
PIP_CACHE="$TRAIN_ROOT/cache/pip"
DEPDIR="$TRAIN_ROOT/dependency_reports"
JOBID="${SLURM_JOB_ID:-local}"

DRYRUN_REPORT="$DEPDIR/t4_2a_dryrun_report_${JOBID}.json"
DRYRUN_ALL="$DEPDIR/t4_2a_dryrun_all_${JOBID}.txt"
RESOLVED_FILTERED="$DEPDIR/t4_2a_resolved_filtered_${JOBID}.txt"
VERIFY_JSON="$DEPDIR/t4_2a_verify_${JOBID}.json"

mkdir -p "$TRAIN_ROOT/logs" "$DEPDIR" "$PIP_CACHE" "$PREFIX"

# Capture git state before entering Apptainer (git is not in the container).
GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")

echo "=== T4.2a: SpeechBrain dependency install gate ==="
echo "Host            : $(hostname)"
echo "Date            : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container       : $CONTAINER"
echo "Repo            : $REPO"
echo "PREFIX          : $PREFIX"
echo "PIP_CACHE       : $PIP_CACHE"
echo "DEPDIR          : $DEPDIR"
echo "JOBID           : $JOBID"
echo "Git commit      : $GIT_COMMIT_AT_RUN"
echo "Dryrun report   : $DRYRUN_REPORT"
echo "Dryrun all      : $DRYRUN_ALL"
echo "Filtered set    : $RESOLVED_FILTERED"
echo "Verify JSON     : $VERIFY_JSON"
echo ""

# Verify PREFIX is writable inside the container before doing anything else.
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import os, sys
prefix = '$PREFIX'
if not os.path.isdir(prefix):
    print(f'ERROR: PREFIX is not a directory: {prefix}', file=sys.stderr)
    sys.exit(10)
if not os.access(prefix, os.W_OK):
    print(f'ERROR: PREFIX is not writable: {prefix}', file=sys.stderr)
    sys.exit(9)
print(f'OK: PREFIX writable: {prefix}')
"

# -----------------------------------------------------------------------
# STEP 1: pip dry-run — resolve SpeechBrain stack
#
# No --target, no --ignore-installed. pip sees the active interpreter
# (/opt/conda), so torch/torchaudio/numpy already satisfy their
# requirements and will NOT appear in the install plan.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 1: pip dry-run ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_CACHE_DIR="$PIP_CACHE" \
  "$CONTAINER" \
  python3 -s -m pip install \
    --dry-run \
    --report "$DRYRUN_REPORT" \
    --quiet \
    speechbrain hyperpyyaml huggingface_hub sentencepiece

echo "Dry-run report written: $DRYRUN_REPORT"
ls -la "$DRYRUN_REPORT"

# -----------------------------------------------------------------------
# STEP 2: parse dry-run report; apply forbidden-stack guard
#
# Writes:
#   DRYRUN_ALL       — raw resolved set (name==version, sorted)
#   RESOLVED_FILTERED — forbidden stack removed (safe to install)
#
# Exits non-zero if:
#   - report is missing or malformed
#   - resolved set is empty
#   - filtered set is empty after guard
#   - any forbidden package appears AND cannot be safely excluded
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 2: parse + forbidden-stack guard ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import json, re, sys

report_path       = '$DRYRUN_REPORT'
out_all_path      = '$DRYRUN_ALL'
out_filtered_path = '$RESOLVED_FILTERED'
forbidden_exact   = {'torch', 'torchaudio', 'torchvision', 'torchtext', 'numpy', 'triton'}

def norm(name):
    return re.sub(r'[-_.]+', '-', name).lower()

with open(report_path) as f:
    report = json.load(f)

installs = report.get('install', []) or []
if not installs:
    print('ERROR: pip dry-run resolved an empty install list', file=sys.stderr)
    sys.exit(1)

all_lines      = []
filtered_lines = []
forbidden_hits = []
for entry in installs:
    meta    = entry.get('metadata') or {}
    name    = meta.get('name', '')
    version = meta.get('version', '')
    if not name or not version:
        continue
    n      = norm(name)
    pinned = f'{name}=={version}'
    all_lines.append(pinned)
    if n in forbidden_exact or n.startswith('nvidia-'):
        forbidden_hits.append(pinned)
    else:
        filtered_lines.append(pinned)

with open(out_all_path, 'w') as f:
    f.write('\n'.join(sorted(all_lines)) + '\n')

if forbidden_hits:
    print('Forbidden-stack packages found in dry-run plan (removed before install):')
    for h in sorted(forbidden_hits):
        print(f'  REMOVED (forbidden): {h}')

if not filtered_lines:
    print('ERROR: filtered install set is empty after forbidden-stack guard', file=sys.stderr)
    sys.exit(1)

with open(out_filtered_path, 'w') as f:
    f.write('\n'.join(sorted(filtered_lines)) + '\n')

print(f'Raw resolved set  : {len(all_lines)} packages -> {out_all_path}')
print(f'Filtered set      : {len(filtered_lines)} packages -> {out_filtered_path}')
for p in sorted(filtered_lines):
    print(f'  INSTALL: {p}')
"

echo ""
echo "--- Filtered set (will be installed) ---"
cat "$RESOLVED_FILTERED"

# -----------------------------------------------------------------------
# STEP 3: install filtered set into PREFIX with --no-deps
#
# --no-deps ensures no second resolution pass can pull in forbidden stack.
# Exact pinned versions (from the filtered file) are installed as-is.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 3: pip install into PREFIX ---"
set -x
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PIP_CACHE_DIR="$PIP_CACHE" \
  "$CONTAINER" \
  python3 -s -m pip install \
    --no-warn-script-location \
    --target "$PREFIX" \
    --no-deps \
    -r "$RESOLVED_FILTERED"
set +x
echo "Install complete."

# -----------------------------------------------------------------------
# STEP 4a: post-install forbidden-path guard
#
# Walks PREFIX and fails if any forbidden directory or .dist-info for a
# forbidden package is found. Checks both dir names and dist-info names.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 4a: post-install forbidden-path guard ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import os, sys
prefix              = '$PREFIX'
forbidden_dir_names = {'torch', 'torchaudio', 'torchvision', 'torchtext',
                       'numpy', 'numpy.libs', 'triton', 'nvidia'}
forbidden_dist_pfx  = ('torch-', 'torchaudio-', 'torchvision-', 'torchtext-',
                       'numpy-', 'triton-', 'nvidia-')
violations = []
if not os.path.isdir(prefix):
    print(f'ERROR: PREFIX not a directory: {prefix}', file=sys.stderr)
    sys.exit(10)
for name in sorted(os.listdir(prefix)):
    full = os.path.join(prefix, name)
    if name in forbidden_dir_names and os.path.isdir(full):
        violations.append(('forbidden_dir', name, full))
    n_lower = name.lower()
    if any(n_lower.startswith(p) for p in forbidden_dist_pfx) and (
        name.endswith('.dist-info') or name.endswith('.data')
    ):
        violations.append(('forbidden_distinfo', name, full))
if violations:
    print('FORBIDDEN-PATH VIOLATIONS in PREFIX:')
    for kind, name, full in violations:
        print(f'  {kind:20s}  {name:48s}  {full}')
    print('BLOCKER: forbidden_stack_contaminated_prefix')
    sys.exit(7)
print('OK: no forbidden paths under PREFIX')
"

# -----------------------------------------------------------------------
# STEP 4b: import/origin validation; write verify JSON
#
# Verifies each required package resolves from PREFIX, and each forbidden
# package still resolves from /opt/conda (not from PREFIX).
# Writes VERIFY_JSON regardless of pass/fail for post-mortem use.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 4b: import/origin validation ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env T4_2A_VERIFY_JSON="$VERIFY_JSON" \
  --env T4_2A_GIT_COMMIT="$GIT_COMMIT_AT_RUN" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
from __future__ import annotations
import importlib.metadata
import importlib.util
import json
import os
import sys
from pathlib import Path

PREFIX    = "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/python_env/site-packages-py310"
OPT_CONDA = "/opt/conda"

REQUIRED = ["speechbrain", "hyperpyyaml", "huggingface_hub", "sentencepiece"]
FORBIDDEN = ["torch", "torchaudio", "numpy"]

verify_json = Path(os.environ["T4_2A_VERIFY_JSON"])
git_commit  = os.environ.get("T4_2A_GIT_COMMIT", "unknown")

results: dict = {
    "git_commit_at_run": git_commit,
    "required": {},
    "forbidden_origins": {},
    "contamination_detected": False,
    "validation_passed": False,
}
ok = True

for name in REQUIRED:
    spec   = importlib.util.find_spec(name)
    origin = str(spec.origin) if spec and spec.origin else None
    in_prefix = bool(origin and PREFIX in origin)
    try:
        ver = importlib.metadata.version(name)
    except Exception:
        ver = "unknown"
    results["required"][name] = {
        "origin": origin, "in_prefix": in_prefix, "version": ver,
    }
    if in_prefix:
        print(f"  OK (PREFIX): {name}=={ver}")
    else:
        print(f"FAIL: {name} not in PREFIX — origin={origin}", file=sys.stderr)
        ok = False

for name in FORBIDDEN:
    spec   = importlib.util.find_spec(name)
    origin = str(spec.origin) if spec and spec.origin else None
    in_prefix    = bool(origin and PREFIX in origin)
    in_opt_conda = bool(origin and OPT_CONDA in origin)
    try:
        ver = importlib.metadata.version(name)
    except Exception:
        ver = "unknown"
    results["forbidden_origins"][name] = {
        "origin": origin, "in_prefix": in_prefix, "in_opt_conda": in_opt_conda, "version": ver,
    }
    if in_prefix:
        print(f"CONTAMINATION: {name} in PREFIX — {origin}", file=sys.stderr)
        results["contamination_detected"] = True
        ok = False
    elif in_opt_conda:
        print(f"  OK (/opt/conda): {name}=={ver}")
    else:
        print(f"WARNING: {name} origin unexpected: {origin}", file=sys.stderr)

results["validation_passed"] = ok
verify_json.parent.mkdir(parents=True, exist_ok=True)
verify_json.write_text(json.dumps(results, indent=2))
print(f"\nVerify JSON: {verify_json}")

if not ok:
    sys.exit(1)
print("\nT4.2a import/origin validation PASSED")
PYEOF

echo ""
echo "=== T4.2a COMPLETE ==="
echo "Dry-run report : $DRYRUN_REPORT"
echo "Raw set        : $DRYRUN_ALL"
echo "Filtered set   : $RESOLVED_FILTERED"
echo "Verify JSON    : $VERIFY_JSON"
echo "Date           : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
