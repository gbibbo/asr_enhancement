# ASR Enhancement Platform

End-to-end platform for pre-recorded speech enhancement optimized for automatic speech recognition (ASR).

**Project case study:** https://gbibbo.github.io/work/asr-enhancement/

> ## ▶️ Live demo — try it now
>
> **https://asr-rp5.tail072b8f.ts.net/demo/**
>
> When the browser asks, sign in with:
>
> - **Username:** `recruiter`
> - **Password:** `asr-demo-2026`

## Purpose

Compare two transcription paths on the same audio file:

- Raw transcription — upload and transcribe without modification.
- Enhanced transcription — apply a speech enhancement preset before transcribing.

Job state, audio artifacts, transcripts, and provider payloads are persisted and inspectable through the API.

## System map

| # | Block | Components | Flow / role |
|---|---|---|---|
| 1 | **Entry point & API** | Next.js, FastAPI, HTTP | upload → select path → job ID → status/result |
| 2 | **Async execution** | Celery, Redis | API → broker → worker |
| 3 | **Audio enhancement** | Python DSP, presets | raw audio → optional enhancement → processed audio |
| 4 | **ASR layer** | provider adapter, Fake, AssemblyAI | audio → provider → transcript |
| 5 | **Persistence** | PostgreSQL, MinIO/S3 | job state → Postgres; artifacts → object storage |
| 6 | **Observability** | JSON logs, Prometheus, OpenTelemetry, Grafana | logs + metrics + traces → dashboard/alerts |
| 7 | **Deployment** | Docker, Docker Compose | containerized services → single-VPS stack |
| 8 | **Testing & CI** | pytest, Ruff, mypy, GitHub Actions, Buildx | lint + types + tests + smoke + build |

**End-to-end:** Client → FastAPI → Redis → Celery worker → enhancement → ASR → PostgreSQL/MinIO → API → Client

## Status

Phase 8 / Cut C is complete. The MVP backend vertical slice — `transcribe-only` and `enhance-and-transcribe` — runs end-to-end against the **fake provider** with a single-VPS Docker Compose deployment path, JSON structured logs, Prometheus metrics, OpenTelemetry traces, one provisioned Grafana dashboard, three basic alerts, and a passing CI on GitHub Actions.

The MVP is **pre-recorded only** and **not production-hardened**. The demo Next.js frontend exists under [`services/frontend/`](services/frontend/) but is **not yet integrated into [`infra/compose/docker-compose.yml`](infra/compose/docker-compose.yml)** — the deployment runbook is backend-only for now (deferred to a later demo task per [`services/frontend/README.md`](services/frontend/README.md)).

For the full implementation plan see [`plan.md`](plan.md). For per-task execution history see [`docs/claude_task_progress.md`](docs/claude_task_progress.md) and [`docs/claude_task_progress.yaml`](docs/claude_task_progress.yaml).

## MVP capabilities

- FastAPI service exposing `GET /health`, `GET /ready`, `POST /v1/transcribe`, `POST /v1/enhance-and-transcribe`, `GET /v1/jobs/{job_id}`, `GET /v1/jobs/{job_id}/result`, and `GET /metrics`.
- Celery worker for asynchronous job processing.
- PostgreSQL job state, Redis broker, MinIO (S3-compatible) object storage.
- ASR providers: **fake provider** by default (deterministic, no secrets) and **AssemblyAI** pre-recorded adapter behind opt-in gating (see "AssemblyAI (opt-in, gated)" below).
- Enhancement presets: `bypass`, `light_clean`, `denoise`, `denoise_dereverb` (deterministic DSP, no neural models).
- Observability: JSON structured logs, Prometheus metrics endpoint, OpenTelemetry traces, one provisioned Grafana dashboard, three basic alerts (API error rate, queue backlog, worker heartbeat missing).
- CI on GitHub Actions: ruff lint, mypy type check, unit and integration tests with the fake adapter, in-stack Cut A smoke, frontend lint/type/build, backend Docker image build — see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Architecture overview

The backend Compose stack is defined in [`infra/compose/docker-compose.yml`](infra/compose/docker-compose.yml):

| Service          | Role                                              | Host port   |
|------------------|---------------------------------------------------|-------------|
| `api`            | FastAPI HTTP entrypoint                           | 8000        |
| `worker`         | Celery worker (metrics endpoint)                  | 9091        |
| `postgres`       | Job state (Postgres 16)                           | not exposed |
| `redis`          | Celery broker                                     | not exposed |
| `minio`          | S3-compatible object storage                      | 9000        |
| `otel-collector` | OpenTelemetry collector                           | 4318        |
| `prometheus`     | Metrics scrape and alerts                         | 9090        |
| `grafana`        | One provisioned operational dashboard             | 3000        |

Postgres (5432) and Redis (6379) are intentionally not exposed to the host — they are reachable only from inside the Compose network.

The demo Next.js frontend at [`services/frontend/`](services/frontend/) is **not** part of the Compose stack; backend-only deployment is the only documented path for now.

## Quick start (fake provider, local Docker Compose)

This is the no-secrets local recipe against the fake provider. It mirrors [`docs/smoke_tests.md`](docs/smoke_tests.md). For the full single-VPS deployment runbook (env vars, secrets handling, reverse proxy, backups), see [`docs/deployment.md`](docs/deployment.md).

```bash
git clone git@github.com:gbibbo/asr_enhancement.git
cd asr_enhancement
cp .env.example .env
```

The default `ASR_PROVIDER=fake` requires no credentials. The bundled local MinIO credentials `minioadmin` / `minioadmin` are the local-only Compose default and **must be changed** for any internet-reachable deployment.

```bash
docker compose -f infra/compose/docker-compose.yml up -d --build
```

One-time setup — Alembic migrations and MinIO bucket. Both must be performed once after the stack is up:

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

Wait for readiness:

```bash
until curl -fsS http://localhost:8000/ready >/dev/null; do sleep 2; done
until docker compose -f infra/compose/docker-compose.yml exec -T worker \
        celery -A services.worker.app.celery_app:celery_app inspect ping -t 2 >/dev/null 2>&1; do
  sleep 2
done
```

Run the smoke tests against the fake provider:

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -q tests/smoke/test_cut_a_smoke.py
```

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -v tests/api/test_enhance_and_transcribe.py
```

Each command must exit 0 with a passing pytest run. The Cut A smoke imports the FastAPI app in-process via `ASGITransport`, which is why it runs inside a one-shot `api` container that joins the Compose network.

For the full local recipe (artifact layout, log fields, job-state inspection through the API) see [`docs/smoke_tests.md`](docs/smoke_tests.md). For the single-VPS deployment runbook see [`docs/deployment.md`](docs/deployment.md).

## AssemblyAI (opt-in, gated)

Live AssemblyAI transcription is **not required** for the MVP. CI never runs it. The live test runs only when **both** of these environment variables are set at the shell:

- `RUN_LIVE_ASSEMBLYAI_TEST=1`
- `ASSEMBLYAI_API_KEY=<your-key>`

If either is missing, the live test self-skips at collection time without contacting the provider. Real key values must never be committed to the repository or printed in logs, screenshots, or status reports. The exact run commands live in [`docs/smoke_tests.md`](docs/smoke_tests.md).

## CI status

GitHub Actions runs three jobs on every push and pull request to `master` — see [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

- **`backend`** — installs the package with dev/lint extras, runs `ruff` lint and `mypy` type checks, applies Alembic migrations, runs unit and integration tests against the fake adapter (excluding the smoke directory), starts a Celery worker in the background, and runs `pytest -q tests/smoke/test_cut_a_smoke.py` as the explicit smoke gate.
- **`frontend`** — runs `npm run lint`, `npm run typecheck`, and `npm run build` against [`services/frontend/`](services/frontend/).
- **`docker-image`** — builds the backend Docker image via Buildx (no push).

CI sets `ASR_PROVIDER=fake` and never requires AssemblyAI credentials.

## Persistent data and artifacts

- Job state lives in Postgres (Docker named volume `asr_postgres_data`).
- Audio and transcript artifacts live in MinIO (Docker named volume `asr_minio_data`) under deterministic, job-scoped object keys: `raw_audio/{job_id}/input.{ext}`, `enhanced_audio/{job_id}/output.wav`, `transcripts/{job_id}/transcript.json`, `provider_payloads/{job_id}/provider_response.json`.
- For long-term storage and backup guidance (Postgres dump and MinIO volume archive), see the **Object storage and backups** section of [`docs/deployment.md`](docs/deployment.md).

## Known limitations

- The demo Next.js frontend is **not** integrated into [`infra/compose/docker-compose.yml`](infra/compose/docker-compose.yml). Frontend deployment is deferred to a later demo task; the deployment runbook is backend-only for now and there is no host-side `npm` production-run recipe in this repository.
- The bundled local MinIO credentials (`minioadmin` / `minioadmin` in [`.env.example`](.env.example)) are for the local development walkthrough only. They must be changed before any internet-reachable deployment.
- Live AssemblyAI calls cost money, are gated by `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY`, are not part of the post-deploy smoke, and are never run in CI.
- The Cut A smoke test imports the FastAPI app in-process via `ASGITransport` inside a one-shot `api` container — it must be run on the Compose network, not from the host.

## Out of scope (post-MVP)

The MVP does not include any of the following. They are deferred to post-MVP work and are not implemented in this repository:

- live streaming and WebSocket transcription
- batch submission API and hyperparameter sweeps
- experiment tracking, preset promotion, and preset ranking workflows
- heavy neural enhancement models
- Kubernetes and managed-cloud orchestration
- enterprise auth, multi-tenant features, and admin console
- advanced quality dashboards (WER, CER, experiment comparison, business analytics)
- production hardening (high availability, automated backups, advanced rate-limiting beyond the basic per-minute limit, secrets management beyond a `.env` file)

See [`plan.md`](plan.md) §3 and §16 for the full post-MVP roadmap.

## Repository layout

```text
asr_enhancement/
  CLAUDE.md
  plan.md
  README.md
  alembic/                   # database migrations
  alembic.ini
  pyproject.toml
  .env.example
  docs/
    smoke_tests.md
    deployment.md
    claude_task_progress.md
    claude_task_progress.yaml
  services/
    api/                     # FastAPI service
    worker/                  # Celery worker
    frontend/                # Next.js demo (not in Compose)
  libs/                      # shared modules: settings, ASR adapter, audio pipeline, observability, common
  infra/
    compose/                 # docker-compose.yml + Dockerfile.backend + prometheus.yml
    grafana/
    otel/
    prometheus/
  tests/                     # unit, integration, smoke
  .github/
    workflows/ci.yml
```
