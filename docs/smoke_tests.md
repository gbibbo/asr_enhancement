# Smoke test guide

## Overview

This document describes how to bring up the ASR Enhancement Platform locally with Docker Compose and verify the Cut A (transcribe-only) and Cut B (enhance-and-transcribe) backend paths against the **fake** ASR provider, without any external credentials.

The Cut A smoke test imports the FastAPI app in-process via `ASGITransport`, so it must be run **inside** a one-shot `api` container that joins the compose network. Postgres and Redis are intentionally compose-internal (only MinIO, the API, the worker metrics endpoint, OTel, Prometheus, and Grafana are exposed to the host).

The same checks run automatically in CI without Compose. The CI workflow at `.github/workflows/ci.yml` is the source of truth for the no-Compose path; this guide is the source of truth for the manual Compose-based path.

## Prerequisites

- Docker
- Docker Compose v2
- Python 3.11+ — only required for the optional host-side AssemblyAI live run

Clean checkout setup:

```bash
git clone git@github.com:gbibbo/asr_enhancement.git
cd asr_enhancement
cp .env.example .env
```

The default `ASR_PROVIDER=fake` requires no credentials. AssemblyAI is opt-in and described in the "AssemblyAI live smoke test" section below.

## Where artifacts go

When jobs run, the backend persists artifacts in the configured MinIO bucket and (for non-Compose runs) under the configured runtime / artifact roots:

| Artifact            | Object key pattern                              | Bucket               |
|---------------------|-------------------------------------------------|----------------------|
| Raw audio           | `raw_audio/{job_id}/input.{ext}`                | `${MINIO_BUCKET}`    |
| Enhanced audio      | `enhanced_audio/{job_id}/output.wav`            | `${MINIO_BUCKET}`    |
| Transcript JSON     | `transcripts/{job_id}/transcript.json`          | `${MINIO_BUCKET}`    |
| Provider payload    | `provider_payloads/{job_id}/provider_response.json` | `${MINIO_BUCKET}` |

Non-Compose runtime / cache roots (from `.env.example`):

- `ASR_RUNTIME_ROOT` — temporary runtime data
- `ASR_ARTIFACTS_ROOT` — durable artifacts outside the repo
- `ASR_CACHE_ROOT` — local caches

These are not used inside the Compose stack (Compose uses named Docker volumes), but they apply to host-side / CI-style runs.

## Start the stack

```bash
docker compose -f infra/compose/docker-compose.yml up -d --build
```

Exposed ports:

| Service        | Host port |
|----------------|-----------|
| api            | 8000      |
| worker (metrics) | 9091    |
| MinIO (S3)     | 9000      |
| OTel collector | 4318      |
| Prometheus     | 9090      |
| Grafana        | 3000      |

Postgres (5432) and Redis (6379) are intentionally **not** exposed to the host — they are reachable only from inside the compose network. That is why the smoke tests below run inside a one-shot `api` container.

## One-time stack setup (Alembic migrations and MinIO bucket)

The `api` and `worker` containers do not run migrations or create the bucket on startup. Both must be performed once, after the stack is up:

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api alembic upgrade head
```

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api python -c '
import os
from minio import Minio
c = Minio(
    os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
)
b = os.environ["MINIO_BUCKET"]
if not c.bucket_exists(b):
    c.make_bucket(b)
print("bucket ready:", b)
'
```

The `--no-deps` flag keeps the persistent stack as the source of truth for Postgres, Redis, MinIO, and the worker; the one-shot container reaches them via the compose service names baked into the `api` service environment.

## Wait for readiness

The `/ready` endpoint reports 200 only when Postgres, Redis, **and** the MinIO bucket are all reachable. The Celery worker container has no built-in healthcheck, so a separate readiness wait is required before submitting work.

```bash
# API ready (postgres + redis + bucket all OK)
until curl -fsS http://localhost:8000/ready >/dev/null; do sleep 2; done
```

```bash
# Celery worker ready
until docker compose -f infra/compose/docker-compose.yml exec -T worker \
        celery -A services.worker.app.celery_app:celery_app inspect ping -t 2 >/dev/null 2>&1; do
  sleep 2
done
```

## Cut A smoke test (transcribe-only, fake provider)

Runs the in-process end-to-end smoke that submits a tiny WAV, polls until completion, fetches the result, and verifies that the raw audio and transcript objects exist in MinIO:

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -q tests/smoke/test_cut_a_smoke.py
```

The test generates an in-memory 0.1-second WAV — there is no audio fixture file in the repo. It requires the migrations and the bucket from the previous section. Pass criterion: the command exits 0 and pytest reports a passing test run.

## Enhance-and-transcribe flow (Cut B, fake provider)

Runs the API-level suite for `POST /v1/enhance-and-transcribe` (preset validation, upload-limit handling, happy path) against the fake adapter:

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -v tests/api/test_enhance_and_transcribe.py
```

Pass criterion: the command exits 0 and pytest reports a passing test run.

## AssemblyAI live smoke test (gated, opt-in)

The live AssemblyAI test calls the real AssemblyAI API. It is **gated by both** of these environment variables:

- `RUN_LIVE_ASSEMBLYAI_TEST=1`
- `ASSEMBLYAI_API_KEY=<your-key>`

If either is missing, the test self-skips at collection time without contacting the provider. CI does **not** set `RUN_LIVE_ASSEMBLYAI_TEST=1`, so this test never runs in CI. The live test is **not required** to verify the platform — it is purely an opt-in provider sanity check.

Two equivalent run options. **Never commit a real key value.** Substitute `<your-key>` with your AssemblyAI API key at the shell only.

Inside Compose (preferred for parity with the other smoke commands):

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps \
  -e RUN_LIVE_ASSEMBLYAI_TEST=1 \
  -e ASSEMBLYAI_API_KEY=<your-key> \
  api pytest -v -s tests/integration/test_live_assemblyai.py
```

From the host (requires a local Python 3.11+ venv with the project installed):

```bash
python3 -m pip install -e ".[dev]"
RUN_LIVE_ASSEMBLYAI_TEST=1 \
ASSEMBLYAI_API_KEY=<your-key> \
  pytest -v -s tests/integration/test_live_assemblyai.py
```

Pass criterion: the command exits 0 and pytest reports a passing test run; the test verifies that the AssemblyAI adapter returns a normalized `ASRResult` with `provider="assemblyai"` and a non-empty `provider_job_id`.

## Inspect logs

```bash
docker compose -f infra/compose/docker-compose.yml logs api
docker compose -f infra/compose/docker-compose.yml logs worker
docker compose -f infra/compose/docker-compose.yml logs api worker --tail=100 -f
```

The API and worker emit JSON-structured logs. Common fields you can grep for:

- `event` — application event name (for example `api.task_enqueued`, `worker.job_received`, `worker.span_started`)
- `job_id` — set on every job-related log line
- request fields — `method`, `path`, `status_code`, `duration_ms` on each `api.request` log

## Inspect job state via API

After submitting a job through one of the endpoints, query its state and result. Replace `JOB_ID` with the `job_id` returned by the submit call.

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/ready
curl -fsS http://localhost:8000/v1/jobs/$JOB_ID
curl -fsS http://localhost:8000/v1/jobs/$JOB_ID/result
```

Status semantics (defined in `plan.md` §3.6):

- `GET /v1/jobs/{id}` — 404 if the job does not exist; 200 otherwise.
- `GET /v1/jobs/{id}/result` — 404 unknown; 202 while `queued` or `running`; 200 with persisted error message when `failed`; 200 with transcript text and URI when `completed`.

## Stop the stack

```bash
docker compose -f infra/compose/docker-compose.yml down
# add -v to drop the named volumes (postgres, redis, minio, grafana)
```

## CI parity (reference only)

CI runs the same `pytest -q tests/smoke/test_cut_a_smoke.py` line at `.github/workflows/ci.yml`, but without Compose: it provisions Postgres and Redis as GitHub Actions services, runs MinIO via a `docker run` step, applies migrations with `alembic upgrade head`, creates the bucket with the same Python+`minio` snippet shown above, starts the Celery worker natively, polls Celery readiness with `celery -A services.worker.app.celery_app:celery_app inspect ping -t 2`, and only then runs the smoke. The CI workflow file is the source of truth for that no-Compose recipe.
