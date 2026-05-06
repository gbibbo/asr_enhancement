# RP5 Soak Test Runbook (B13.1)

## Overview

B13.1 validates the demo runtime under a 24–48 h light-load soak on the
Raspberry Pi 5. This runbook covers preparation, start, monitoring, stop,
and post-soak evaluation. The soak does **not** touch Cloudflare and does
**not** call AssemblyAI — both require Phase B14+ work.

## Workload

- Every 15 minutes: 1 random cached `/demo/run-cached` call.
- Every 6 hours: 1 forced-recomputation upload (curated clean WAV via
  `provider="whisper"`).
- Every 2 hours: 1 synthetic 10 s upload (`provider="whisper"`).
- Every 1 minute: a metrics sample (`/demo/health`, `/demo/examples` latency,
  CPU temperature, disk usage, container memory, log file sizes, SQLite
  active/failed job counts).

Acceptance (plan §B13.1 done-when):

1. zero crashes;
2. cached-path P95 < 2 × baseline cached-path P95;
3. RAM is not growing continuously;
4. sustained CPU temperature < 75 °C;
5. disk use is stable;
6. cleanup works.

## Prerequisites

- On host `asr-rp5`, repo at `/home/gbibbo/code/asr_enhancement`,
  branch `feature/demo-runtime-rp5-v1`, working tree clean.
- Demo runtime root populated: `/home/gbibbo/asr_enhancement_runtime/`.
- Curated examples materialised (Phase B6.x) so `/demo/run-cached` returns
  `status="cache_hit"` for at least one `(example_id, degradation_id)` pair.

## Pre-soak validation

```bash
cd /home/gbibbo/code/asr_enhancement
git status --short
git branch --show-current
git log --oneline -3

docker compose -f infra/compose/docker-compose.demo.yml config >/dev/null
docker compose -f infra/compose/docker-compose.demo.yml up -d
docker compose -f infra/compose/docker-compose.demo.yml ps
curl -sf http://localhost:8001/demo/health | python3 -m json.tool

pytest tests/demo/test_b13_1_soak_runner.py -q
pytest tests/demo/test_b12_1_admin_stats_shape.py \
       tests/demo/test_b12_2_alert_state_disk.py \
       tests/demo/test_b12_2_alert_state_health.py -q
```

If any of the above fails, do not start the soak.

## Starting the soak

The runner is host-side, stdlib-only, and starts in `nohup`. It writes a
pointer file at `runs/b13_1_current_run.txt` so a later session can resume
without shell variables.

```bash
cd /home/gbibbo/code/asr_enhancement
mkdir -p runs
TS=$(date -u +%Y%m%dT%H%M%SZ)
RUN_DIR="$PWD/runs/soak_${TS}"
mkdir -p "$RUN_DIR/tmp"

nohup python3 -u scripts/demo/soak_runner.py \
    --duration 48h \
    --target http://localhost:8001 \
    --runtime-root /home/gbibbo/asr_enhancement_runtime \
    --db-path /home/gbibbo/asr_enhancement_runtime/db/demo.db \
    --examples-config config/demo_examples.json \
    --out "$RUN_DIR" \
    > "$RUN_DIR/nohup.log" 2>&1 &

echo $! > "$RUN_DIR/pid"
echo "$RUN_DIR" > runs/b13_1_current_run.txt

echo "soak started"
echo "  run dir : $RUN_DIR"
echo "  pid     : $(cat "$RUN_DIR/pid")"
echo "  pointer : runs/b13_1_current_run.txt"
```

The runner itself writes `state.json` at startup containing PID, start
time UTC, requested duration, target URL, branch, and HEAD commit.

## Monitoring (read-only spot-checks)

Safe to run any time during the soak:

```bash
cd /home/gbibbo/code/asr_enhancement
RUN_DIR="$(cat runs/b13_1_current_run.txt)"

# Recent samples
tail -n 5 "$RUN_DIR/metrics.jsonl"
tail -n 5 "$RUN_DIR/cached.jsonl"
tail -n 5 "$RUN_DIR/jobs.jsonl"

# Host vitals
ls -lh /home/gbibbo/asr_enhancement_runtime/logs/
df -h /home/gbibbo/asr_enhancement_runtime
cat /sys/class/thermal/thermal_zone0/temp
docker stats --no-stream
```

## Cleanup dry-run during the soak

Run `cleanup_uploads.py` in **dry-run only** twice during the soak:

```bash
RUN_DIR="$(cat runs/b13_1_current_run.txt)"

# Early dry-run, after the first 2 h (one synthetic upload submitted)
docker compose -f infra/compose/docker-compose.demo.yml run --rm --no-deps \
    -v "$PWD/scripts:/app/scripts:ro" \
    demo-api python scripts/cleanup_uploads.py --dry-run \
    > "$RUN_DIR/cleanup_dryrun.early.log" 2>&1

# Late dry-run, near the end of the soak
docker compose -f infra/compose/docker-compose.demo.yml run --rm --no-deps \
    -v "$PWD/scripts:/app/scripts:ro" \
    demo-api python scripts/cleanup_uploads.py --dry-run \
    > "$RUN_DIR/cleanup_dryrun.late.log" 2>&1
```

Do **not** run `--apply` during the soak. The summarizer reads these two
log files when it builds `summary.md`.

## Stopping the soak

The soak stops automatically after `--duration` elapses. To stop early:

```bash
RUN_DIR="$(cat runs/b13_1_current_run.txt)"
PID="$(cat "$RUN_DIR/pid")"
kill -TERM "$PID"
while ps -p "$PID" >/dev/null 2>&1; do sleep 2; done
echo "soak stopped"
tail -n 50 "$RUN_DIR/runner.log"
python3 -m json.tool < "$RUN_DIR/state.json"
```

`wait` is not used: the PID belongs to a different shell session, so we
poll `ps -p` instead.

## Post-soak evaluation (closure session)

```bash
RUN_DIR="$(cat runs/b13_1_current_run.txt)"
python3 scripts/demo/soak_summarize.py --run-dir "$RUN_DIR"
cat "$RUN_DIR/summary.md"
```

Verify the redaction guards before promoting the summary:

```bash
# No raw runtime artefacts have been staged.
git status --short | grep -E "^[ AM?]+ +runs/" && echo "FAIL: runs staged" || echo "ok"

# No secrets, headers, AssemblyAI traffic, or full paths leaked into the summary.
grep -E "ASSEMBLYAI|SMTP|PASSWORD|TOKEN|Authorization|X-Demo-Session-Id" \
     "$RUN_DIR/summary.md" "$RUN_DIR/runner.log" \
     && echo "FAIL: secret/header leak" || echo "ok"
grep -E '"provider"\s*:\s*"assemblyai"' "$RUN_DIR/jobs.jsonl" \
     && echo "FAIL: AssemblyAI used" || echo "ok"
grep -F "/home/gbibbo" "$RUN_DIR/summary.md" \
     && echo "FAIL: path leak in summary" || echo "ok"
```

## Final cleanup verification (closure session, optional `--apply`)

After all jobs are terminal, queue depth is 0, and the summary captures
pre-cleanup state, the operator may run a single `--apply`:

```bash
RUN_DIR="$(cat runs/b13_1_current_run.txt)"

# Snapshot before
ls -1 /home/gbibbo/asr_enhancement_runtime/artifacts/examples > "$RUN_DIR/examples_basenames.before.txt"
sqlite3 /home/gbibbo/asr_enhancement_runtime/db/demo.db \
    "SELECT COUNT(*) FROM cache_entries; SELECT COUNT(*) FROM jobs;" \
    > "$RUN_DIR/db_counts.before.txt"
ls -l /home/gbibbo/asr_enhancement_runtime/logs/ > "$RUN_DIR/logs.before.txt"

docker compose -f infra/compose/docker-compose.demo.yml run --rm --no-deps \
    -v "$PWD/scripts:/app/scripts:ro" \
    demo-api python scripts/cleanup_uploads.py --apply \
    > "$RUN_DIR/cleanup_apply.log" 2>&1

# Snapshot after
ls -1 /home/gbibbo/asr_enhancement_runtime/artifacts/examples > "$RUN_DIR/examples_basenames.after.txt"
sqlite3 /home/gbibbo/asr_enhancement_runtime/db/demo.db \
    "SELECT COUNT(*) FROM cache_entries; SELECT COUNT(*) FROM jobs;" \
    > "$RUN_DIR/db_counts.after.txt"
ls -l /home/gbibbo/asr_enhancement_runtime/logs/ > "$RUN_DIR/logs.after.txt"

diff "$RUN_DIR/examples_basenames.before.txt" "$RUN_DIR/examples_basenames.after.txt"
diff "$RUN_DIR/db_counts.before.txt" "$RUN_DIR/db_counts.after.txt"
```

`diff` of the curated example basenames must be empty. The `cache_entries`
row count must be unchanged. Log files are byte-untouched (compare sizes).
Only eligible generated upload files and per-job artefact dirs may have
been deleted.

If any verification fails, B13.1 is **blocked**, not done.

## Outputs and what to commit

Under `runs/soak_<TS>/` (gitignored — never committed):

- `state.json`, `host.txt`, `pid`, `nohup.log`
- `cache_hit_pairs.json`, `baseline.json`
- `metrics.jsonl`, `cached.jsonl`, `jobs.jsonl`
- `runner.log`
- `tmp/` (deleted as each upload terminates)
- `cleanup_dryrun.{early,late}.log`, `cleanup_apply.log` (if `--apply` was run)
- `summary.md`, `summary.json`

In the closure session, **only** the redacted summary is promoted to
`reports/demo/b13_1_soak_summary.md` and the trackers are advanced —
all raw JSONL/logs stay under `runs/`.

## Closure rules

B13.1 is closed only when:

1. The full requested duration has elapsed (the runner exited normally,
   not via SIGTERM).
2. All acceptance criteria pass per §B13.1 done-when.
3. Final cleanup verification passes per the section above.

Until then `current_task` stays `B13.1` and `last_completed_task` stays
`B12.2`. If any blocker is hit (sustained ≥75 °C, P95 ratio ≥ 2,
RAM growth, disk pressure, log rotation broken, alert spam, AssemblyAI
or Cloudflare needed, privacy leak), the task is marked
`blocked: true` with a short reason — not closed.
