#!/usr/bin/env bash
#SBATCH --job-name=asr_t4_2c_enhance_smoke
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

# T4.2c smoke: 5 records per family = 25 records.
#
# Enhanced WAVs go to the smoke-specific audio root inside the run dir —
# never the final full dataset root — to prevent partial smoke outputs
# from contaminating the enhancement bank. The smoke manifest is also
# written inside the run dir.
#
# Steps:
#   0. Verify input manifest SHA-256.
#   1. Place start marker for cache pollution check.
#   2. Run build_enhancement_bank.py (smoke mode, 5 per family).
#   3. Parse run_summary.json: assert failure_count==0, enhanced_count==25.
#   4. Spot-check one WAV per family.
#   5. Cache pollution check (find -newer marker under $HOME/.cache and $HOME/.local).
#   6. Write consolidated verify JSON to $TRAIN_ROOT/artifacts.
#
# This job does NOT submit other jobs, run Whisper, or update trackers.
#
# Strict runtime discipline (carried forward from T1.2 / T4.2b):
#   --env PYTHONNOUSERSITE=1
#   python3 -s
#   PYTHONPATH="$REPO:$PREFIX"
#
# Submission (sbatch is not in PATH on datamove1):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t4_2c_enhance_smoke.sh

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
JOBID="${SLURM_JOB_ID:-local}"

RUNDIR="$TRAIN_ROOT/runs/t4_2c_enhance_smoke_${JOBID}"
SMOKE_AUDIO_ROOT="$RUNDIR/enhanced_audio"
SMOKE_MANIFEST="$RUNDIR/enhanced_manifest_smoke.jsonl"
MANIFEST="$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl"
MANIFEST_SHA256="c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c"
VERIFY_JSON="$TRAIN_ROOT/artifacts/t4_2c_smoke_verify_${JOBID}.json"
MARKER="$TRAIN_ROOT/artifacts/t4_2c_smoke_start_marker_${JOBID}"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/artifacts" \
  "$RUNDIR" \
  "$TRAIN_ROOT/cache/huggingface/hub" \
  "$TRAIN_ROOT/cache/speechbrain" \
  "$TRAIN_ROOT/cache/xdg"

GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")

echo "=== T4.2c: MetricGAN+ enhancement bank smoke (5 per family = 25 records) ==="
echo "Host         : $(hostname)"
echo "Date         : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container    : $CONTAINER"
echo "JOBID        : $JOBID"
echo "Manifest     : $MANIFEST"
echo "Audio root   : $SMOKE_AUDIO_ROOT"
echo "Smoke manif  : $SMOKE_MANIFEST"
echo "Run dir      : $RUNDIR"
echo "Git commit   : $GIT_COMMIT_AT_RUN"
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
# STEP 2: Run bulk enhancement (smoke mode, 5 per family).
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 2: run build_enhancement_bank.py (smoke) ---"
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
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/build_enhancement_bank.py" \
    --manifest               "$MANIFEST" \
    --audio-root             "$SMOKE_AUDIO_ROOT" \
    --out-manifest           "$SMOKE_MANIFEST" \
    --out-dir                "$RUNDIR" \
    --mode                   smoke \
    --max-records-per-family 5

# -----------------------------------------------------------------------
# STEP 3: Parse run_summary.json; assert failure_count==0, enhanced==25.
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
if s.get("enhanced_count", -1) != 25:
    errors.append(f"enhanced_count={s.get('enhanced_count')} (expected 25)")
if not s.get("validation_passed"):
    errors.append("validation_passed=False")
if errors:
    print("ERROR: run summary validation failed:", file=sys.stderr)
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)
print(f"OK: enhanced_count={s['enhanced_count']} failure_count={s['failure_count']}")
print(f"  per_family_counts={s.get('per_family_counts')}")
print(f"  enhanced_manifest_sha256={s.get('enhanced_manifest_sha256')}")
PYEOF

# -----------------------------------------------------------------------
# STEP 4: Spot-check one WAV per family.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 4: spot-check WAVs (one per family) ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env T4C_SMOKE_MANIFEST="$SMOKE_MANIFEST" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import json, os, sys, soundfile as sf
from pathlib import Path
manifest_path = Path(os.environ["T4C_SMOKE_MANIFEST"])
records = [json.loads(l) for l in manifest_path.read_text().splitlines() if l.strip()]
first_per_family = {}
for r in records:
    fam = r["family"]
    if fam not in first_per_family:
        first_per_family[fam] = r
errors = []
for fam, r in sorted(first_per_family.items()):
    wav = Path(r["enhanced_audio_path"])
    if not wav.exists():
        errors.append(f"{fam}: WAV not found: {wav}")
        continue
    info = sf.info(str(wav))
    dur = info.frames / info.samplerate
    ok = info.frames > 0 and info.samplerate == 16000 and info.channels == 1
    if not ok:
        errors.append(
            f"{fam}: checks failed frames={info.frames} "
            f"rate={info.samplerate} ch={info.channels}"
        )
    else:
        print(f"OK: {fam}: frames={info.frames} rate={info.samplerate} "
              f"ch={info.channels} dur={dur:.3f}s")
if errors:
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
print(f"Spot-checked {len(first_per_family)} families, all OK")
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
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import json, os
from pathlib import Path
rundir      = Path(os.environ["T4C_RUNDIR"])
verify_path = Path(os.environ["T4C_VERIFY_JSON"])
summary     = json.loads((rundir / "run_summary.json").read_text())
verify = {
    "gate"                    : "T4.2c_smoke",
    "job_id"                  : os.environ.get("T4C_JOBID", "unknown"),
    "git_commit_at_run"       : os.environ.get("T4C_GIT_COMMIT", "unknown"),
    "mode"                    : summary.get("mode"),
    "enhanced_count"          : summary.get("enhanced_count"),
    "failure_count"           : summary.get("failure_count"),
    "per_family_counts"       : summary.get("per_family_counts"),
    "enhanced_manifest_sha256": summary.get("enhanced_manifest_sha256"),
    "enhanced_manifest_records": summary.get("enhanced_manifest_records"),
    "validation_passed"       : summary.get("validation_passed"),
}
verify_path.parent.mkdir(parents=True, exist_ok=True)
verify_path.write_text(json.dumps(verify, indent=2))
print(f"Verify JSON: {verify_path}")
print(f"validation_passed: {verify['validation_passed']}")
PYEOF

echo ""
echo "=== T4.2c smoke COMPLETE ==="
echo "Run dir     : $RUNDIR"
echo "Verify JSON : $VERIFY_JSON"
echo "Date        : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
