# B13.1 — Local Soak Summary (Raspberry Pi 5)

Decision: **PASS** — all six §B13.1 acceptance criteria met under a clean
48 h run. Numbers below are produced by `scripts/demo/soak_summarize.py`
plus the cleanup verification performed in this closure session.

## Run window

- start_time_utc: `2026-05-06T05:23:07Z`
- end_time_utc: `2026-05-08T05:23:22Z`
- elapsed_hours: `48.0`
- requested_duration_hours: `48.0`
- stopped_by_signal: `false` (runner exited normally on `runner.duration_complete`)
- branch at start: `feature/demo-runtime-rp5-v1`
- head_commit at start: `184eb87`
- target: local demo API (no public exposure during the soak)

## Workload counts

- cached `/demo/run-cached` samples: `n = 191`
- upload jobs total: `n = 30`
  - synthetic_upload: `23` (every 2 h)
  - recompute (curated, forced, whisper-local): `7` (every 6 h)
- metric samples: `n = 2718`

## Criterion 1 — zero crashes

- runner_error_events_total: `0`
- runner_error_event_counts: `{}`
- health_non_200_samples: `0`
- jobs_failed_or_timeout: `0`
- result: **pass**

## Criterion 2 — cached P95 < 2× baseline

- baseline_n: `30`
- baseline_p95_ms: `4.7`
- soak_n: `191` (only successful `/demo/run-cached` `cache_hit` records)
- soak_p50_ms: `4.0`
- soak_p95_ms: `4.0`
- ratio (soak / baseline): `0.85`
- result: **pass** (well under 2.0×)

## Criterion 3 — RAM not growing

`docker stats` on this RP5 kernel reports `0 B / 0 B` for both demo
containers, so the docker-cgroups RAM trend in the summarizer is not
authoritative on this host. Host-level memory readings back the
no-growth judgment:

- `free` at run start (host): total `7.9 GiB`, available `5.3 GiB`,
  swap used `0 B`.
- `free` at closure: total `7.9 GiB`, available `6.3 GiB`, swap used `0 B`.
- No OOM events; runner exited normally; queue stayed at `0`.

Note: the docker-cgroups limitation is a known host-level constraint, not
a parser bug. Per the closure rules this does not fail the criterion.
- result: **pass**

## Criterion 4 — CPU temperature

- max_c: `60.6`
- mean_c: `56.3`
- sustained ≥ 75 °C (3+ consecutive samples): `false`
- threshold: `< 75 °C`
- result: **pass**

## Criterion 5 — disk stable

- start_pct: `40.41`
- end_pct: `41.70`
- delta_pct: `+1.29`
- max_pct: `41.70`
- threshold: `|delta| < 5.0`
- result: **pass**

## Queue depth

- final_queue_depth: `0`
- max_queue_depth: `0`

## Job terminal counts

- total: `30`
- by_terminal_status: `{"completed": 30}`
- by_stream:
  - `synthetic_upload`: `{"completed": 23}`
  - `recompute`: `{"completed": 7}`
- failed_or_timeout: `0`

## Log rotation (informational)

- log files seen by sampler: `2`
- max single-file bytes recorded during the soak: `5,049,938`
- rotation thresholds come from `demo_log_max_bytes` /
  `demo_log_backup_count` (B12.1). The configured threshold was not
  reached during this 48 h workload, so no rotation event fired.
  This is informational; the acceptance contract is "no unbounded log
  growth", which holds.

## Criterion 6 — cleanup works (closure-session verification)

The in-soak dry-run hooks were not exercised, so cleanup was verified
end-to-end in this closure session against the live runtime using the
unmodified existing implementation
(`scripts/cleanup_uploads.py` + `libs/demo/cleanup.py`):

- Pre-cleanup gate: `queue_depth = 0`, `jobs_active = 0`.
- Dry-run plan: scanned `38` uploads (would delete `32`, keep `6`),
  scanned `36` job-artefact dirs (would delete `30`, keep `6`),
  `0` errors, `0` skipped-unrecognized, `0` skipped-stat-error.
  Filesystem state unchanged after dry-run.
- Apply: matched the plan exactly — `32` upload files and `30`
  per-job artefact dirs deleted; `6` recent uploads and `6` recent
  job dirs preserved by retention; `0` errors; no `SafetyViolation`.
- Curated examples basenames diff: empty (10 files unchanged).
- DB row counts (comparable schema): `jobs`, `cache_entries`,
  `usage_ledger` all unchanged.
- Pre-cleanup `db_job_state`: `jobs_terminal = jobs_total`,
  `jobs_active = 0`.
- Logs: not deleted, not rotated, not truncated. Inodes unchanged for
  both `demo.api.log` and `demo.worker.log`. `demo.worker.log` is
  byte-identical. `demo.api.log` grew by ~1.1 KiB from concurrent API
  request logging during the cleanup window — strictly ≥ pre-size, no
  rotation event, consistent with the cleanup contract that forbids
  writing to runtime logs.
- result: **pass**

## Operational posture during the run

- external ASR provider was not used during this soak
  (no `assemblyai` provider entries in the run's job records);
- email alerts were not sent during this soak
  (no alert state file mutated; no SMTP traffic);
- no public exposure (Cloudflare tunnel) was active during this soak;
- no privacy leak in committed artefacts (raw run JSONL/logs stay under
  gitignored `runs/<run_id>/`; only this redacted summary is tracked).

## Post-soak operational note (outside the measurement window)

After the runner wrote `runner.duration_complete` and the 48 h
measurement window closed, the RP5 was cleanly shut down for relocation;
during relocation there was one accidental unplug after boot. The unit
was reconnected, the repo stayed clean, and the demo containers came
back healthy with `/demo/health` returning
`{"status":"ok","mode":"demo","db_ok":true,"queue_depth":0}`. This is
recorded only as an operational note — it is not part of the soak
failure criteria, because the duration-complete record was written
before relocation.

## Final decision

**PASS — close B13.1 and advance to B14.1.**
