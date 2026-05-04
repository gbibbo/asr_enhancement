#!/usr/bin/env bash
#SBATCH --job-name=asr_t4_2b_smoke_enhance
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

# T4.2b: MetricGAN+ one-file enhancement smoke gate.
#
# Runs exactly one real degraded WAV through MetricGANPlusEnhancer inside
# Apptainer to prove end-to-end inference: model download, weight caching
# under TRAIN_ROOT, audio enhancement, and output validation.
#
# Steps:
#   0. Verify input WAV SHA-256.
#   1. Place start marker for cache pollution check.
#   2. Run enhance_metricgan_plus.py; capture raw stdout separately from stderr.
#   3. Extract and validate JSON from raw stdout; verify enhanced/fallback fields.
#   4. Validate output WAV (frames, rate, channels, duration).
#   5. Cache pollution check (Bash find -newer marker) under $HOME/.cache and $HOME/.local.
#   6. Verify SpeechBrain savedir exists under TRAIN_ROOT/cache.
#   7. Write consolidated verify JSON.
#
# This job does NOT run Whisper, submit other jobs, update trackers, or commit.
#
# Strict runtime discipline (carried forward from T1.2 / T4.2a):
#   --env PYTHONNOUSERSITE=1
#   python3 -s
#   PYTHONPATH="$REPO:$PREFIX"
#
# Submission (sbatch is not in PATH on datamove1):
#   ./slurm/tools/on_submit.sh sbatch \
#     /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t4_2b_smoke_enhance.sh

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
PREFIX="$TRAIN_ROOT/python_env/site-packages-py310"
JOBID="${SLURM_JOB_ID:-local}"

RUNDIR="$TRAIN_ROOT/runs/t4_2b_smoke_enhance_${JOBID}"
VERIFY_JSON="$TRAIN_ROOT/artifacts/t4_2b_smoke_verify_${JOBID}.json"
RAW_STDOUT="$RUNDIR/enhance_stdout_raw.txt"
RESULT_JSON="$RUNDIR/enhance_result.json"
MARKER="$TRAIN_ROOT/artifacts/t4_2b_start_marker_${JOBID}"
ENHANCED_WAV="$RUNDIR/metricgan_plus_pretrained.wav"

# Deterministic input: line 1 of the degraded manifest.
INPUT_WAV="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degraded/degradation_v1/broadband_hiss/1272-128104-0001.wav"
INPUT_SHA256="abebf43b4c73b0cf644b838a52f0794932f16c86565399ef37b53c369a7a8446"

mkdir -p \
  "$TRAIN_ROOT/logs" \
  "$TRAIN_ROOT/artifacts" \
  "$RUNDIR" \
  "$TRAIN_ROOT/cache/huggingface/hub" \
  "$TRAIN_ROOT/cache/speechbrain" \
  "$TRAIN_ROOT/cache/xdg" \
  "$TRAIN_ROOT/cache/pip"

GIT_COMMIT_AT_RUN=$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo "unknown")

echo "=== T4.2b: MetricGAN+ one-file smoke ==="
echo "Host          : $(hostname)"
echo "Date          : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Container     : $CONTAINER"
echo "Repo          : $REPO"
echo "TRAIN_ROOT    : $TRAIN_ROOT"
echo "PREFIX        : $PREFIX"
echo "JOBID         : $JOBID"
echo "Git commit    : $GIT_COMMIT_AT_RUN"
echo "Input WAV     : $INPUT_WAV"
echo "Run dir       : $RUNDIR"
echo "Verify JSON   : $VERIFY_JSON"
echo ""

# -----------------------------------------------------------------------
# STEP 0: Verify input WAV exists and SHA-256 matches hardcoded value.
# -----------------------------------------------------------------------
echo "--- STEP 0: input WAV verification ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  "$CONTAINER" \
  python3 -s -c "
import hashlib, sys
path     = '$INPUT_WAV'
expected = '$INPUT_SHA256'
try:
    with open(path, 'rb') as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != expected:
        print(f'ERROR: SHA-256 mismatch for {path}', file=sys.stderr)
        print(f'  expected: {expected}', file=sys.stderr)
        print(f'  actual  : {actual}', file=sys.stderr)
        sys.exit(1)
    print(f'OK: SHA-256 verified: {actual}')
    print(f'   path: {path}')
except FileNotFoundError:
    print(f'ERROR: input WAV not found: {path}', file=sys.stderr)
    sys.exit(1)
"

# -----------------------------------------------------------------------
# STEP 1: Place start marker for cache pollution check (Step 5).
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 1: place start marker ---"
touch "$MARKER"
echo "Marker: $MARKER"

# -----------------------------------------------------------------------
# STEP 2: Run enhancement; capture raw stdout.
#
# enhance_metricgan_plus.py writes one JSON object to stdout and returns
# exit code 0 if enhanced=True, 1 otherwise.
# SpeechBrain download progress and Python logging go to stderr.
# Raw stdout is captured to $RAW_STDOUT for safe JSON extraction in Step 3.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 2: run MetricGANPlusEnhancer ---"

ENHANCE_EXIT=0
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  --env HF_HOME="$TRAIN_ROOT/cache/huggingface" \
  --env HUGGINGFACE_HUB_CACHE="$TRAIN_ROOT/cache/huggingface/hub" \
  --env TRANSFORMERS_CACHE="$TRAIN_ROOT/cache/huggingface/hub" \
  --env XDG_CACHE_HOME="$TRAIN_ROOT/cache/xdg" \
  "$CONTAINER" \
  python3 -s "$REPO/scripts/training/enhance_metricgan_plus.py" \
    --input    "$INPUT_WAV" \
    --output-dir "$RUNDIR" \
    --job-id   "t4_2b_smoke_${JOBID}" \
  > "$RAW_STDOUT" || ENHANCE_EXIT=$?

echo "enhance_metricgan_plus.py exit code: $ENHANCE_EXIT"
echo ""
echo "--- Raw stdout (enhance_metricgan_plus.py) ---"
cat "$RAW_STDOUT"
echo "--- End raw stdout ---"
echo ""

if [ "$ENHANCE_EXIT" -ne 0 ]; then
  echo "ERROR: enhance_metricgan_plus.py exited with $ENHANCE_EXIT (enhanced=false or exception)" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# STEP 3: Extract and validate JSON from raw stdout.
#
# Parses the raw stdout safely: tries full-text parse first, then scans
# for the last complete JSON object by brace depth.
# Validates enhanced, enhancement_fallback, model_id, output_sample_rate_hz.
# Writes clean JSON to $RESULT_JSON.
# -----------------------------------------------------------------------
echo "--- STEP 3: extract and validate JSON result ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env T4_2B_RAW_STDOUT="$RAW_STDOUT" \
  --env T4_2B_RESULT_JSON="$RESULT_JSON" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import json, os, sys
from pathlib import Path

raw_path = Path(os.environ["T4_2B_RAW_STDOUT"])
out_path = Path(os.environ["T4_2B_RESULT_JSON"])
raw_text = raw_path.read_text()

# Attempt 1: whole stdout is valid JSON.
payload = None
try:
    payload = json.loads(raw_text)
except json.JSONDecodeError:
    pass

# Attempt 2: find the last top-level JSON object by brace depth.
if payload is None:
    depth, start, candidates = 0, None, []
    for i, ch in enumerate(raw_text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                candidates.append(raw_text[start:i+1])
    for block in reversed(candidates):
        try:
            payload = json.loads(block)
            break
        except json.JSONDecodeError:
            continue

if payload is None:
    print("ERROR: could not extract valid JSON from enhance stdout", file=sys.stderr)
    print("Raw stdout follows:", file=sys.stderr)
    print(raw_text, file=sys.stderr)
    sys.exit(1)

errors = []
if payload.get("enhanced") is not True:
    errors.append(f"enhanced={payload.get('enhanced')!r} (expected True)")
if payload.get("enhancement_fallback") is not False:
    errors.append(f"enhancement_fallback={payload.get('enhancement_fallback')!r} (expected False)")
diag = payload.get("diagnostic", {})
if diag.get("model_id") != "speechbrain/metricgan-plus-voicebank":
    errors.append(f"diagnostic.model_id={diag.get('model_id')!r} (expected speechbrain/metricgan-plus-voicebank)")
if diag.get("output_sample_rate_hz") != 16000:
    errors.append(f"diagnostic.output_sample_rate_hz={diag.get('output_sample_rate_hz')!r} (expected 16000)")

out_path.write_text(json.dumps(payload, indent=2))

if errors:
    print("ERROR: JSON result validation failed:", file=sys.stderr)
    for e in errors:
        print(f"  {e}", file=sys.stderr)
    sys.exit(1)

print(f"OK: JSON extracted and validated -> {out_path}")
print(f"  enhanced={payload['enhanced']}, enhancement_fallback={payload['enhancement_fallback']}")
print(f"  model_id={diag.get('model_id')}, output_sample_rate_hz={diag.get('output_sample_rate_hz')}")
PYEOF

# -----------------------------------------------------------------------
# STEP 4: Validate output WAV (frames, rate, channels, duration).
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 4: validate output WAV ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env T4_2B_WAV="$ENHANCED_WAV" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import soundfile as sf, os, sys
from pathlib import Path

wav_path = Path(os.environ["T4_2B_WAV"])

if not wav_path.exists():
    print(f"ERROR: output WAV not found: {wav_path}", file=sys.stderr)
    sys.exit(1)

info = sf.info(str(wav_path))
dur  = info.frames / info.samplerate

checks = {
    "frames_nonzero"   : info.frames > 0,
    "samplerate_16kHz" : info.samplerate == 16000,
    "channels_mono"    : info.channels == 1,
    "duration_in_range": 3.0 <= dur <= 7.0,
}

print(f"WAV info: frames={info.frames}, rate={info.samplerate}, ch={info.channels}, dur={dur:.3f}s")

failures = [k for k, v in checks.items() if not v]
if failures:
    print(f"ERROR: WAV checks failed: {failures}", file=sys.stderr)
    sys.exit(1)

print(f"OK: all WAV checks passed: {list(checks.keys())}")
PYEOF

# -----------------------------------------------------------------------
# STEP 5: Cache pollution check (Bash; outside Apptainer).
#
# Reports any file written under $HOME/.cache or $HOME/.local after the
# start marker. Fails the job if pollution is detected.
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
  echo "ERROR: cache pollution detected under home paths" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# STEP 6: Verify SpeechBrain savedir exists under TRAIN_ROOT/cache.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 6: verify SpeechBrain savedir ---"
SAVEDIR="$TRAIN_ROOT/cache/speechbrain/metricgan_plus_voicebank"
if [ -d "$SAVEDIR" ]; then
  SAVEDIR_COUNT=$(find "$SAVEDIR" -type f | wc -l || echo 0)
  echo "OK: savedir exists: $SAVEDIR"
  echo "   file count: $SAVEDIR_COUNT"
  ls -la "$SAVEDIR" | head -20
else
  echo "ERROR: SpeechBrain savedir not found: $SAVEDIR" >&2
  exit 1
fi

# -----------------------------------------------------------------------
# STEP 7: Write consolidated verify JSON.
# -----------------------------------------------------------------------
echo ""
echo "--- STEP 7: write consolidated verify JSON ---"
apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env PYTHONPATH="$REPO:$PREFIX" \
  --env T4_2B_RESULT_JSON="$RESULT_JSON" \
  --env T4_2B_WAV="$ENHANCED_WAV" \
  --env T4_2B_VERIFY_JSON="$VERIFY_JSON" \
  --env T4_2B_GIT_COMMIT="$GIT_COMMIT_AT_RUN" \
  --env T4_2B_JOBID="$JOBID" \
  "$CONTAINER" \
  python3 -s - << 'PYEOF'
import soundfile as sf, json, os
from pathlib import Path

result_path = Path(os.environ["T4_2B_RESULT_JSON"])
wav_path    = Path(os.environ["T4_2B_WAV"])
verify_path = Path(os.environ["T4_2B_VERIFY_JSON"])
git_commit  = os.environ.get("T4_2B_GIT_COMMIT", "unknown")
jobid       = os.environ.get("T4_2B_JOBID", "unknown")

result = json.loads(result_path.read_text())
info   = sf.info(str(wav_path))
dur    = info.frames / info.samplerate

wav_checks = {
    "frames_nonzero"   : info.frames > 0,
    "samplerate_16kHz" : info.samplerate == 16000,
    "channels_mono"    : info.channels == 1,
    "duration_in_range": 3.0 <= dur <= 7.0,
}

verify = {
    "job_id"              : jobid,
    "git_commit_at_run"   : git_commit,
    "input_wav"           : "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degraded/degradation_v1/broadband_hiss/1272-128104-0001.wav",
    "input_sha256"        : "abebf43b4c73b0cf644b838a52f0794932f16c86565399ef37b53c369a7a8446",
    "enhanced"            : result.get("enhanced"),
    "enhancement_fallback": result.get("enhancement_fallback"),
    "enhancer_version"    : result.get("enhancer_version"),
    "diagnostic"          : result.get("diagnostic"),
    "output_wav"          : str(wav_path),
    "wav_frames"          : info.frames,
    "wav_samplerate"      : info.samplerate,
    "wav_channels"        : info.channels,
    "wav_duration_seconds": round(dur, 4),
    "wav_checks"          : wav_checks,
    "validation_passed"   : (
        result.get("enhanced") is True
        and result.get("enhancement_fallback") is False
        and all(wav_checks.values())
    ),
}

verify_path.parent.mkdir(parents=True, exist_ok=True)
verify_path.write_text(json.dumps(verify, indent=2))
print(f"Verify JSON written: {verify_path}")
print(f"validation_passed: {verify['validation_passed']}")
PYEOF

echo ""
echo "=== T4.2b COMPLETE ==="
echo "Run dir     : $RUNDIR"
echo "Verify JSON : $VERIFY_JSON"
echo "Date        : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
