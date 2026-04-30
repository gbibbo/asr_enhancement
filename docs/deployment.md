# Deployment guide

This guide describes how to deploy the ASR Enhancement Platform backend to a single VPS using Docker Compose. It documents the minimum reproducible path required by `plan.md` §14 Task 8.3: bring up the backend stack, run one-time setup (database migrations and the MinIO bucket), wait for readiness, and run the post-deploy smoke test against the **fake** ASR provider.

This is the deployment runbook. The smoke-test reference for local development lives in `docs/smoke_tests.md`; the post-deploy smoke section below restates the minimum subset so this guide is self-contained.

## Single VPS with Docker Compose

The deployment target is a single Linux VPS with Docker and Docker Compose v2 installed. The backend stack (`api`, `worker`, `postgres`, `redis`, `minio`, plus the observability sidecars `otel-collector`, `prometheus`, `grafana`) is brought up from `infra/compose/docker-compose.yml`.

Step-by-step:

```bash
git clone https://github.com/gbibbo/asr_enhancement.git
cd asr_enhancement
cp .env.example .env
# edit .env: set MINIO_ACCESS_KEY, MINIO_SECRET_KEY, optionally ASSEMBLYAI_API_KEY
```

```bash
docker compose -f infra/compose/docker-compose.yml up -d --build
```

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

Wait for readiness before submitting work:

```bash
until curl -fsS http://localhost:8000/ready >/dev/null; do sleep 2; done
```

```bash
until docker compose -f infra/compose/docker-compose.yml exec -T worker \
        celery -A services.worker.app.celery_app:celery_app inspect ping -t 2 >/dev/null 2>&1; do
  sleep 2
done
```

The API is now reachable on the VPS at `http://<vps-ip>:8000`. If no domain is available, access the demo by **server IP** at `http://<vps-ip>:8000`. If a domain is available, terminate HTTPS in front of the API with a host-managed reverse proxy as documented in `## Reverse proxy`.

Exposed host ports (declared in `infra/compose/docker-compose.yml`):

| Service          | Host port |
|------------------|-----------|
| api              | 8000      |
| worker (metrics) | 9091      |
| MinIO (S3)       | 9000      |
| OTel collector   | 4318      |
| Prometheus       | 9090      |
| Grafana          | 3000      |

Postgres (5432) and Redis (6379) are intentionally not exposed to the host. They are reachable only from inside the Compose network. The one-time setup commands above use `docker compose ... run --rm --no-deps api` so they reach Postgres, Redis, and MinIO over the Compose network using the service names baked into the `api` container environment.

To stop the stack without dropping data:

```bash
docker compose -f infra/compose/docker-compose.yml down
```

Adding `-v` to `down` also drops the named Docker volumes (`asr_postgres_data`, `asr_redis_data`, `asr_minio_data`, `asr_grafana_data`). That is destructive: it deletes job state, queued tasks, and every stored audio object. Only use `down -v` when retiring the deployment or when intentionally resetting a verification environment.

## Required environment variables

All variables and their non-secret defaults live in `.env.example`. Copy it to `.env` on the VPS and edit only the secret-shaped values. Do not commit `.env`.

| Name | Required for | Notes |
|------|--------------|-------|
| `ASR_PROVIDER` | always | `fake` for the demo; set `assemblyai` only if a real API key is configured |
| `DATABASE_URL` | always | Compose-internal default `postgresql+psycopg://asr:asr@postgres:5432/asr` |
| `REDIS_URL` | always | Compose-internal default `redis://redis:6379/0` |
| `MINIO_ENDPOINT` | always | Compose-internal default `minio:9000`; for managed S3-compatible storage point this at the provider endpoint |
| `MINIO_ACCESS_KEY` | always | Change for production; placeholder `<minio-access-key>` only in this doc |
| `MINIO_SECRET_KEY` | always | Change for production; placeholder `<minio-secret-key>` only in this doc |
| `MINIO_BUCKET` | always | Default `asr-platform`; change to the bucket your storage account owns |
| `MINIO_SECURE` | always | `false` for the local Compose MinIO; `true` for managed S3-compatible storage over HTTPS |
| `ASSEMBLYAI_API_KEY` | only if `ASR_PROVIDER=assemblyai` | Placeholder `<assemblyai-api-key>` only; never committed |
| `UPLOAD_LIMIT_BYTES` | always | Default `104857600` (100 MiB) |
| `RATE_LIMIT_PER_MINUTE` | always | Default `30` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | optional | Compose-internal default `http://otel-collector:4318` |

## Secrets handling

- Only `.env.example` is committed. The real `.env` file is never committed.
- On the VPS, copy `.env.example` to `.env`, then edit `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and (only when `ASR_PROVIDER=assemblyai`) `ASSEMBLYAI_API_KEY` with values that are not stored in the repository.
- Never commit a real `MINIO_SECRET_KEY` or `ASSEMBLYAI_API_KEY`. In this guide they appear only as placeholders: `<minio-access-key>`, `<minio-secret-key>`, `<assemblyai-api-key>`.
- Do not print real key values in logs, screenshots, commit messages, pull-request descriptions, or status reports. Redact them before sharing any output.
- The Compose default `minioadmin` / `minioadmin` for the local MinIO service is acceptable for the development walkthrough only. Replace it on any VPS that is reachable from the public internet.
- The live AssemblyAI smoke test in `docs/smoke_tests.md` is opt-in and gated by both `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY=<assemblyai-api-key>`. Closing the deployment task does not require running it.

## Reverse proxy

The deployment supports two access models, driven by `plan.md` §14 Task 8.3 decision rules:

1. **No domain available** — access the deployment by **server IP** at `http://<vps-ip>:8000`. No reverse proxy is needed.
2. **Domain available** — terminate HTTPS at a reverse proxy on the VPS host. The recommended option is Caddy, which issues HTTPS certificates automatically.

Caddy is **operator-managed on the VPS host, outside the Compose stack**. Run it as a host binary, an OS package, or a separately managed container started outside `infra/compose/docker-compose.yml`. Caddy is not added to `infra/compose/docker-compose.yml` by this deployment guide.

Because the proxy runs on the host, it reaches the API through the port that Compose publishes on the host loopback (`127.0.0.1:8000`). The proxy is therefore outside the Compose service mesh, and the snippet below does not address the compose-internal hostname `api`.

Minimal Caddyfile for the domain variant:

```text
demo.example.com {
    encode zstd gzip
    reverse_proxy 127.0.0.1:8000
}
```

Replace `demo.example.com` with the real domain. With a reachable A/AAAA record and ports 80/443 open on the VPS, Caddy obtains a certificate automatically. If no domain is configured, skip the reverse proxy entirely and use `http://<vps-ip>:8000`.

## Post-deploy smoke test

The post-deploy smoke runs against the fake ASR provider, requires no external credentials, and proves that the deployed stack can complete a transcribe-only job end-to-end and accept an enhance-and-transcribe job. Run it after the readiness waits above:

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -q tests/smoke/test_cut_a_smoke.py
```

```bash
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -v tests/api/test_enhance_and_transcribe.py
```

Pass criteria: each command exits 0 and pytest reports a passing test run. The smoke test imports the FastAPI app in-process via `ASGITransport`, which is why it runs inside a one-shot `api` container — Postgres and Redis are intentionally Compose-internal and only reachable from the Compose network.

If either command fails, capture API and worker logs before iterating:

```bash
docker compose -f infra/compose/docker-compose.yml logs api    | head -n 50
docker compose -f infra/compose/docker-compose.yml logs worker | head -n 50
```

`docs/smoke_tests.md` covers the same recipe with extra debugging context (log fields, job-state inspection through the API). Treat that document as the deeper reference; this section is the minimum required for deploy validation.

## Object storage and backups

The Compose stack uses named Docker volumes declared at the bottom of `infra/compose/docker-compose.yml`:

- `asr_postgres_data` — Postgres data directory (the source of truth for job state).
- `asr_redis_data` — Redis append-only file (`redis-server --appendonly yes`).
- `asr_minio_data` — MinIO object store (raw audio, enhanced audio, transcripts, provider payloads).
- `asr_grafana_data` — Grafana database.

Object key patterns inside `MINIO_BUCKET` (consistent with `plan.md` §9):

| Artifact         | Object key pattern                                  |
|------------------|------------------------------------------------------|
| Raw audio        | `raw_audio/{job_id}/input.{ext}`                     |
| Enhanced audio   | `enhanced_audio/{job_id}/output.wav`                 |
| Transcript JSON  | `transcripts/{job_id}/transcript.json`               |
| Provider payload | `provider_payloads/{job_id}/provider_response.json`  |

If you keep the local Compose MinIO on the VPS, the contents of `asr_minio_data` are the only copy of the audio and transcript artifacts. Schedule a regular **backup** of that volume (for example `docker run --rm -v asr_minio_data:/data -v "$PWD":/backup alpine tar -czf /backup/minio-$(date +%F).tgz -C /data .`) and store the archive off the VPS. The same applies to `asr_postgres_data` if you need durable job history.

If you prefer to use **managed S3-compatible storage** instead of the local MinIO, set the following variables in `.env` before bringing the stack up and skip the local backup task:

| Name | Value for managed S3-compatible storage |
|------|------------------------------------------|
| `MINIO_ENDPOINT` | provider endpoint, for example `s3.eu-west-1.amazonaws.com` (no scheme, no path) |
| `MINIO_ACCESS_KEY` | access key issued by the provider |
| `MINIO_SECRET_KEY` | secret key issued by the provider |
| `MINIO_BUCKET` | bucket name owned by the deployment |
| `MINIO_SECURE` | `true` to use HTTPS against the managed endpoint |

When using managed storage, the local MinIO service in Compose still starts but is unused. You can leave it running or comment it out in your own deployment overlay (do not modify `infra/compose/docker-compose.yml` itself for this purpose).

The non-Docker runtime roots `ASR_RUNTIME_ROOT`, `ASR_ARTIFACTS_ROOT`, and `ASR_CACHE_ROOT` listed in `.env.example` apply only to host-side, non-Compose runs. The VPS Compose deployment uses the named volumes above; those three variables can stay at their `.env.example` defaults.

## Known limitations

- The Next.js frontend at `services/frontend/` is **not yet integrated into `infra/compose/docker-compose.yml`**. Its README explicitly defers the frontend Compose service and Dockerfile to a later demo task. This deployment guide therefore documents only the backend Compose path. There is no host-side `npm` production-run recipe here, no frontend container, and no reverse-proxy routing for the frontend. The deployed API can be exercised directly with `curl` or any HTTP client; the demo UI will be wired in by a later task.
- The reverse-proxy section covers only the API. Once the frontend is added to Compose, the Caddyfile will need a second `reverse_proxy` directive; that change belongs to the future frontend deployment task, not to this guide.
- The live AssemblyAI smoke test is documented in `docs/smoke_tests.md` and is intentionally not part of the post-deploy smoke. It costs money and requires a real provider key. CI never runs it, and Task 8.3 closure does not depend on it.
- This guide assumes the VPS has Docker and Docker Compose v2 already installed. Bootstrapping the VPS itself (firewall, automatic upgrades, swap, monitoring agents) is out of scope for the MVP deployment runbook.
