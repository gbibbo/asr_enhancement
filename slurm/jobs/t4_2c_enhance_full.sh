#!/usr/bin/env bash
#SBATCH --job-name=asr_t4_2c_enhance_full
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=16:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# T4.2c full: all 13 465 degraded records enhanced with MetricGAN+.
#
# Enhanced WAVs go to the final dataset root under $TRAIN_ROOT/datasets/enhanced.
# Full enhanced manifest written to $TRAIN_ROOT/datasets.
# Resume-safe: existing valid WAVs at the final path are skipped.
#
# Wall-time estimate: ~3 s/record × 13 465 records ≈ 11 h; 16 h gives ~45% margin.
# Refine estimate from smoke elapsed before submitting if desired.
#
# Steps:
#   0. Verify input manifest SHA-256.
#   1. Place start marker for cache pollution check.
#   2. Run build_enhancement_bank.py (full mode, all records, resume-safe).
#   3. Parse run_summary.json: assert failure_count==0, enhanced_count==13465,
#      per-family counts all==2693.
#   4. Validate enhanced manifest record count and first-record fields.
#   5. Cache pollution check (find -newer marker under $HOME/.cache and $HOME/.local).
#   6. Write consolidated verify JSON to $TRAIN_ROOT/artifacts.
#
# Submit ONLY after smoke gate (t4_2c_enhance_smoke.sh) passes.
# This job does NOT submit other jobs, run Whisper, or update trackers.
#
# Strict runtime discipline (carried forward from T1.2 / T4.2b):
#   --env PYTHONNOUSERSITE=1
#   python3 -s
#   PYTHONPATH="$REPO:$PREFIX"
#
# Submission (sbatch is not in PATH on datamove1):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t4_2c_enhance_full.sh

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
JOBID="${SLURM_JOB_ID:-local}"

RUNDIR="$TRAIN_ROOT/runs/t4_2c_enhance_full_${JOBID}"
FULL_AUDIO_ROOT="$TRAIN_ROOT/datasets/enhanced/metricgan_plus_pretrained/enhancement_v1"
FULL_MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl"
MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl"
MANIFEST_SHA256="c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c"
VERIFY_JSON="$TRAIN_ROOT/artifacts/t4_2c_full_verify_${JOBID}.json"
MARKER="$TRAIN_ROOT/artifacts/t4_2c_full_start_marker_${JOBID}"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/artifacts" \
  "$RUNDIR" \
  "$FULL_AUDIO_ROOT" \
  "$TRAIN_ROOT/cache/huggingface/hub" \
  "$TRAIN_ROOT/cache/speechbrain" \
  "$TRAIN_ROOT/cache/xdg"

GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_STATUS_SHORT_AT_RUN=$(git -C "$REPO" status --short 2>/dev/null || echo "")

echo "=== T4.2c: MetricGAN+ enhancement bank full (13 465 records) ==="
echo "Host          : $(hostname)"
echo "Date          : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container     : $CONTAINER"
echo "JOBID         : $JOBID"
echo "Manifest      : $MANIFEST"
echo "Audio root    : $FULL_AUDIO_ROOT"
echo "Out manifest  : $FULL_MANIFEST"
echo "Run dir       : $RUNDIR"
echo "Git commit    : $GIT_COMMIT_AT_RUN"
echo ""

df -h "$TRAIN_ROOT" || true
echo ""

# -----------------------------------------------------------------------
# STEP 0: Verify input manifest SHA-256.
# -----------------------------------------------------------------------
echo "--- STEP 0: verify manifest SHA-256 ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import hashlib, sys
path     = '$MANIFEST'
expected = '$MANIFEST_SHA256'
try:
    with open(path, 'rb') as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != expected:
        print(f'ERROR: SHA-256 mismatch', file=sys.stderr)
        print(f'  expected: {expected}', file=sys.stderr)
        print(f'  actual  : {actual}', file=sys.stderr)
        sys.exit(1)
    print(f'OK: SHA-256 verified: {actual}')
except FileNotFoundError:
    print(f'ERROR: manifest not found: {path}', file=sys.stderr)
    sys.exit(1)
"

# -----------------------------------------------------------------------
# STEP 1: Place start marker for cache pollution check.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 1: place start marker ---"
touch "$MARKER"
echo "Marker: $MARKER"

# -----------------------------------------------------------------------
# STEP 2: Run bulk enhancement (full mode, all 13 465 records, resume-safe).
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 2: run build_enhancement_bank.py (full) ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env HF_HOME="$TRAIN_ROOT/cache/huggingface" \
  --env HUGGINGFACE_HUB_CACHE="$TRAIN_ROOT/cache/huggingface/hub" \
  --env TRANSFORMERS_CACHE="$TRAIN_ROOT/cache/huggingface/hub" \
  --env XDG_CACHE_HOME="$TRAIN_ROOT/cache/xdg" \
  --env SLURM_JOB_ID="$JOBID" \
  --env GIT_COMMIT_AT_RUN="$GIT_COMMIT_AT_RUN" \
  --env GIT_STATUS_SHORT_AT_RUN="$GIT_STATUS_SHORT_AT_RUN" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/build_enhancement_bank.py" \
    --manifest     "$MANIFEST" \
    --audio-root   "$FULL_AUDIO_ROOT" \
    --out-manifest "$FULL_MANIFEST" \
    --out-dir      "$RUNDIR" \
    --mode         full

# -----------------------------------------------------------------------
# STEP 3: Parse run_summary.json; assert counts and failure_count==0.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 3: validate run summary ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env T4C_RUNDIR="$RUNDIR" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import json, os, sys
from pathlib import Path
summary_path = Path(os.environ["T4C_RUNDIR"]) / "run_summary.json"
if not summary_path.exists():
    print(f"ERROR: run_summary.json not found: {summary_path}", file=sys.stderr)
    sys.exit(1)
s = json.loads(summary_path.read_text())
errors = []
if s.get("failure_count", -1) != 0:
    errors.append(f"failure_count={s.get('failure_count')} (expected 0)")
if s.get("enhanced_count", -1) != 13465:
    errors.append(f"enhanced_count={s.get('enhanced_count')} (expected 13465)")
if not s.get("validation_passed"):
    errors.append("validation_passed=False")
expected_fams = {"broadband_hiss", "cafe_background", "far_field_room", "muffled", "phone_call"}
per_fam = s.get("per_family_counts", {})
for fam in sorted(expected_fams):
    got = per_fam.get(fam, 0)
    if got != 2693:
        errors.append(f"per_family_counts[{fam}]={got} (expected 2693)")
if errors:
    print("ERROR: run summary validation failed:", file=sys.stderr)
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)
print(f"OK: enhanced_count={s['enhanced_count']} failure_count={s['failure_count']}")
print(f"  skipped_count={s.get('skipped_count')} newly_enhanced_count={s.get('newly_enhanced_count')}")
print(f"  per_family_counts={per_fam}")
print(f"  enhanced_manifest_sha256={s.get('enhanced_manifest_sha256')}")
print(f"  enhanced_manifest_records={s.get('enhanced_manifest_records')}")
PYEOF

# -----------------------------------------------------------------------
# STEP 4: Validate enhanced manifest record count and first-record fields.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 4: validate enhanced manifest ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env T4C_FULL_MANIFEST="$FULL_MANIFEST" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import hashlib, json, os, sys
from pathlib import Path
mpath = Path(os.environ["T4C_FULL_MANIFEST"])
if not mpath.exists():
    print(f"ERROR: enhanced manifest not found: {mpath}", file=sys.stderr)
    sys.exit(1)
content = mpath.read_bytes()
sha256  = hashlib.sha256(content).hexdigest()
lines   = [l for l in content.decode("utf-8").splitlines() if l.strip()]
count   = len(lines)
print(f"OK: enhanced manifest: {mpath}")
print(f"  records : {count}")
print(f"  sha256  : {sha256}")
if count != 13465:
    print(f"ERROR: expected 13465 records, got {count}", file=sys.stderr)
    sys.exit(1)
required = [
    "utterance_id", "family", "enhanced_audio_path", "enhanced_audio_sha256",
    "enhanced", "enhancement_fallback", "enhancer_version", "enhancement_version",
]
first = json.loads(lines[0])
missing = [f for f in required if f not in first]
if missing:
    print(f"ERROR: first record missing fields: {missing}", file=sys.stderr)
    sys.exit(1)
print(f"OK: first record has all required fields")
print(f"  utterance_id={first.get('utterance_id')} family={first.get('family')}")
print(f"  enhancer_version={first.get('enhancer_version')} enhancement_version={first.get('enhancement_version')}")
PYEOF

# -----------------------------------------------------------------------
# STEP 5: Cache pollution check (Bash; outside Apptainer).
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 5: cache pollution check ---"
CACHE_POLLUTED=0
for CHECK_DIR in "${HOME}/.cache" "${HOME}/.local"; do
  if [ -d "$CHECK_DIR" ]; then
    NEW_FILES=$(find "$CHECK_DIR" -newer "$MARKER" -type f 2>/dev/null | head -20 || true)
    if [ -n "$NEW_FILES" ]; then
      echo "ERROR: new files under $CHECK_DIR since marker:"
      echo "$NEW_FILES"
      CACHE_POLLUTED=1
    else
      echo "OK: no new files under $CHECK_DIR"
    fi
  else
    echo "OK: $CHECK_DIR does not exist (skip)"
  fi
done
if [ "$CACHE_POLLUTED" -ne 0 ]; then
  echo "ERROR: cache pollution detected" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# STEP 6: Write consolidated verify JSON.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 6: write verify JSON ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env T4C_RUNDIR="$RUNDIR" \
  --env T4C_VERIFY_JSON="$VERIFY_JSON" \
  --env T4C_JOBID="$JOBID" \
  --env T4C_GIT_COMMIT="$GIT_COMMIT_AT_RUN" \
  --env T4C_FULL_MANIFEST="$FULL_MANIFEST" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import hashlib, json, os
from pathlib import Path
rundir      = Path(os.environ["T4C_RUNDIR"])
verify_path = Path(os.environ["T4C_VERIFY_JSON"])
mpath       = Path(os.environ["T4C_FULL_MANIFEST"])
summary     = json.loads((rundir / "run_summary.json").read_text())
manifest_sha256 = (
    hashlib.sha256(mpath.read_bytes()).hexdigest() if mpath.exists() else None
)
verify = {
    "gate"                     : "T4.2c_full",
    "job_id"                   : os.environ.get("T4C_JOBID", "unknown"),
    "git_commit_at_run"        : os.environ.get("T4C_GIT_COMMIT", "unknown"),
    "mode"                     : summary.get("mode"),
    "enhanced_count"           : summary.get("enhanced_count"),
    "skipped_count"            : summary.get("skipped_count"),
    "newly_enhanced_count"     : summary.get("newly_enhanced_count"),
    "failure_count"            : summary.get("failure_count"),
    "per_family_counts"        : summary.get("per_family_counts"),
    "enhanced_manifest"        : str(mpath),
    "enhanced_manifest_sha256" : manifest_sha256,
    "enhanced_manifest_records": summary.get("enhanced_manifest_records"),
    "validation_passed"        : summary.get("validation_passed"),
}
verify_path.parent.mkdir(parents=True, exist_ok=True)
verify_path.write_text(json.dumps(verify, indent=2))
print(f"Verify JSON: {verify_path}")
print(f"validation_passed: {verify['validation_passed']}")
PYEOF

echo ""
echo "=== T4.2c full COMPLETE ==="
echo "Run dir      : $RUNDIR"
echo "Audio root   : $FULL_AUDIO_ROOT"
echo "Manifest     : $FULL_MANIFEST"
echo "Verify JSON  : $VERIFY_JSON"
echo "Date         : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
