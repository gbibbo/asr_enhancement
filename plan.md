# ASR Enhancement Platform: Deterministic Implementation Plan

## 0. How to use this plan

This file is the execution plan for Claude Code. Read it after `CLAUDE.md` and before implementation work.

`CLAUDE.md` defines standing execution rules, repository policy, HPC rules, storage rules, Git identity policy, and scope guardrails. This file defines implementation order, task boundaries, decision rules, gates, and verification criteria.

Do not treat the full MVP as the first target. The first target is the smallest working backend vertical slice.

Execution rule:

1. Read `CLAUDE.md`.
2. Read this file.
3. Read `docs/claude_task_progress.md` and `docs/claude_task_progress.yaml` if they exist.
4. Identify the first pending task.
5. Execute only that task.
6. Run the verification for that task.
7. Update the progress trackers.
8. Stop at gates and report status.

If a task depends on an earlier task that is not complete, do the earlier task first and update the tracker.

## 1. Project goal

Build an end-to-end platform for pre-recorded speech enhancement optimized for ASR.

The product is not a generic transcription app. It compares two paths:

1. raw transcription
2. enhancement plus transcription

The system must keep artifacts, job state, provider responses, and system behavior inspectable.

The first product flow is:

1. upload a recorded audio file
2. choose a processing mode
3. persist the uploaded audio
4. process asynchronously
5. call ASR through an internal adapter
6. persist transcript and provider artifacts
7. expose job status and final result through the API
8. add a small public demo only after the backend path works

The system must remain deployable, measurable, and easy to resume. It must not become an experiment platform before the MVP is stable.

## 2. Execution cuts

Implementation is split into three cuts. A later cut must not start before the previous cut gate passes.

### Cut A. Backend vertical slice

Immediate target: a local backend end-to-end `transcribe-only` flow using the fake ASR adapter.

Cut A includes:

1. repository layout
2. Docker Compose stack for backend services
3. FastAPI API service
4. Celery worker service
5. PostgreSQL job state
6. Redis queue
7. MinIO object storage
8. `GET /health`
9. `GET /ready`
10. `POST /v1/transcribe`
11. `GET /v1/jobs/{job_id}`
12. `GET /v1/jobs/{job_id}/result`
13. fake ASR adapter
14. raw audio persistence
15. transcript persistence
16. one smoke test or script from upload to completed result

Cut A excludes:

1. frontend
2. `enhance-and-transcribe`
3. real AssemblyAI calls
4. Prometheus stack
5. OpenTelemetry stack
6. Grafana
7. alerts
8. CI hardening
9. public deployment
10. streaming
11. batch APIs
12. experiment infrastructure
13. neural enhancement models

Cut A is complete only when a real short audio file moves from upload to persisted completed fake transcript through the API and worker.

### Cut B. MVP backend and demo

Target: extend the working backend with minimal enhancement, real provider support behind environment-controlled execution, basic observability, and a small demo frontend.

Cut B includes:

1. AssemblyAI pre-recorded adapter
2. provider live smoke script with deterministic environment gating
3. preset registry
4. `bypass`
5. lightweight deterministic enhancement presets
6. `POST /v1/enhance-and-transcribe`
7. enhanced audio persistence
8. JSON structured logs
9. Prometheus metrics
10. OpenTelemetry traces
11. one Grafana operational dashboard
12. three basic alerts
13. Next.js public demo
14. rate limits and upload limits for demo use
15. documentation for local run and demo run

### Cut C. MVP hardening

Target: make the MVP reproducible and safe to show publicly.

Cut C includes:

1. CI lint
2. type checks
3. unit tests
4. integration tests
5. Docker image build
6. smoke tests after deployment
7. public demo deployment path using a single VPS with Docker Compose
8. minimal operator documentation

Anything beyond Cut C is post-MVP.

## 3. Fixed MVP scope

The MVP is pre-recorded only.

### Included in the MVP

1. FastAPI inference API
2. Docker Compose local stack
3. PostgreSQL for persistent job state
4. Redis for async jobs
5. MinIO for local object storage with S3-compatible design
6. fake ASR adapter for local tests and CI
7. AssemblyAI pre-recorded adapter for real provider runs
8. `transcribe-only` flow
9. `enhance-and-transcribe` flow
10. job status endpoint
11. job result endpoint
12. small public demo
13. basic observability
14. CI for lint, tests, and image build

### Out of scope for the MVP

Do not implement these before MVP completion:

1. live streaming
2. WebSocket transcription
3. batch submission API
4. hyperparameter sweeps
5. experiment ranking
6. preset promotion workflows
7. large-scale evaluation infrastructure
8. dedicated scheduler service
9. dedicated experiment-runner service
10. heavy neural enhancement models
11. Kubernetes
12. enterprise auth
13. multi-tenant features
14. advanced quality dashboards
15. admin console

## 4. Fixed technical decisions

These decisions are closed for the MVP:

1. API framework: FastAPI
2. Queue model: Celery with Redis
3. Database: PostgreSQL
4. ORM and migrations: SQLAlchemy 2.x and Alembic
5. Object storage: MinIO locally, S3-compatible design
6. Primary external ASR provider: AssemblyAI
7. Default provider for local tests and CI: fake adapter
8. Demo frontend: small Next.js app
9. Local orchestration: Docker Compose
10. Observability: JSON logs, Prometheus metrics, OpenTelemetry traces, Grafana dashboard
11. Public demo deployment: single VPS running Docker Compose

Decision rules:

1. If the repository already contains a complete and tested ORM setup when the task starts, keep it and document the deviation in the progress tracker.
2. Else use SQLAlchemy 2.x and Alembic.
3. If a dependency-management file already exists, extend it.
4. Else create `pyproject.toml`.
5. If a task requires changing a fixed technical decision, stop and report the conflict instead of changing the decision.

## 5. Product language policy

Everything user-facing must be in English.

This applies to:

1. demo UI text
2. button labels
3. status messages
4. form labels
5. validation messages
6. API examples in docs
7. code comments intended for shared project code
8. terminal screenshots used in documentation
9. dashboard titles
10. alert names
11. printed messages in scripts and demo material

If text is visible to users, collaborators, screenshots, logs shown in documentation, or public demo material, write it in English.

If a note is private, not committed, not shown in screenshots, and not product-facing, it may be in Spanish.

## 6. Repository layout target

Use this layout:

```text
asr_enhancement/
  CLAUDE.md
  plan.md
  README.md
  docs/
    claude_task_progress.md
    claude_task_progress.yaml
  services/
    api/
    worker/
  libs/
    audio_pipeline/
    asr_adapter/
    observability/
    common/
  infra/
    compose/
    docker/
  scripts/
  slurm/
    tools/
    jobs/
    templates/
  tests/
```

Cut B adds:

```text
services/frontend/
infra/grafana/
infra/prometheus/
infra/otel/
```

Do not create these directories during MVP implementation:

```text
services/scheduler/
services/experiment_runner/
services/streaming/
```

Decision rules:

1. If the repository is fresh, create the target layout for the current cut only.
2. If the repository already contains compatible directories, reuse them.
3. If the repository contains duplicate or conflicting directories, stop, document the conflict, and choose the path that contains the active code.
4. If a directory belongs to a later cut, do not create it before that cut starts.

## 7. Minimal API surface

### Cut A endpoints

Implement only:

```text
GET  /health
GET  /ready
POST /v1/transcribe
GET  /v1/jobs/{job_id}
GET  /v1/jobs/{job_id}/result
```

### Cut B endpoints

Add:

```text
POST /v1/enhance-and-transcribe
GET  /metrics
```

### Deferred endpoints

Do not implement before MVP completion:

```text
POST /v1/batch/submit
GET  /v1/experiments/{experiment_id}
POST /v1/stream/session
WS   /v1/stream/{session_id}
```

If code generation suggests a deferred endpoint, reject it and keep the API surface above.

## 8. Job model and state contract

PostgreSQL is the source of truth for job state.

Minimum job fields for Cut A:

1. `id`
2. `status`
3. `mode`
4. `provider`
5. `preset`
6. `raw_audio_uri`
7. `enhanced_audio_uri`
8. `transcript_uri`
9. `transcript_text`
10. `provider_payload_uri`
11. `error_message`
12. `created_at`
13. `updated_at`
14. `started_at`
15. `completed_at`

Allowed statuses:

1. `queued`
2. `running`
3. `completed`
4. `failed`

Allowed modes for Cut A:

1. `transcribe_only`

Allowed modes for Cut B:

1. `transcribe_only`
2. `enhance_and_transcribe`

Rules:

1. API result endpoints must read persisted state, not in-memory task state.
2. Worker retries must use deterministic object keys by job ID.
3. If a retry overwrites a partial artifact, it must overwrite the same job-scoped object key.
4. Failed jobs must persist a useful error message.
5. Result endpoints must return a stable internal schema, not raw provider responses.
6. Raw provider responses must be stored as artifacts when available.
7. A job must not be marked `completed` until required artifact existence checks pass.

## 9. Object storage contract

Use object storage for raw audio, enhanced audio, transcripts, and provider payloads.

Object key pattern:

```text
raw_audio/{job_id}/input.{ext}
enhanced_audio/{job_id}/output.wav
transcripts/{job_id}/transcript.json
provider_payloads/{job_id}/provider_response.json
```

Rules:

1. Do not store uploaded audio permanently inside the API container filesystem.
2. Do not store heavy runtime artifacts in the repository.
3. Persist object references in PostgreSQL.
4. Use deterministic object keys by job ID.
5. Validate that required objects exist before marking a job completed.
6. If object upload fails, mark the job `failed` and persist the storage error.
7. If object existence check fails after processing, mark the job `failed`.

## 10. ASR adapter contract

All ASR providers must be called through internal adapters.

Minimum adapter input:

1. local file path
2. job ID
3. provider settings

Minimum normalized result:

1. `text`
2. `language`
3. `duration_seconds`
4. `segments`
5. `words`
6. `provider`
7. `provider_job_id`
8. `raw_payload`

Use `null` or an empty list for unavailable fields. Do not change the schema between providers.

Required adapters:

1. fake adapter for Cut A
2. AssemblyAI pre-recorded adapter for Cut B

Fake adapter rules:

1. deterministic output
2. no network calls
3. suitable for unit tests and CI
4. works without credentials
5. accepts a real uploaded audio file
6. returns the same transcript for the same configured fake fixture

AssemblyAI rules:

1. If `ASR_PROVIDER=fake`, do not require AssemblyAI settings.
2. If `ASR_PROVIDER=assemblyai` and `ASSEMBLYAI_API_KEY` is missing, fail the job cleanly with a persisted configuration error.
3. If `ASR_PROVIDER=assemblyai` and `ASSEMBLYAI_API_KEY` is present, call AssemblyAI through the adapter.
4. CI must set `ASR_PROVIDER=fake`.
5. Live provider smoke tests run only if `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY` is present.
6. If either live-test condition is missing, the live smoke test must skip and record the skip reason.
7. Provider response must be normalized before storage or API return.

## 11. Enhancement strategy

Enhancement starts only after Cut A passes.

Initial presets for Cut B:

1. `bypass`
2. `light_clean`
3. `denoise`
4. `denoise_dereverb`

Implementation rules:

1. `bypass` copies or forwards the input audio without DSP modification.
2. `light_clean` applies deterministic gain normalization.
3. `denoise` applies a deterministic high-pass filter plus gain normalization.
4. `denoise_dereverb` applies the same deterministic high-pass filter plus gain normalization and records `dereverb_applied=false` in diagnostic metadata for the MVP.
5. Do not add heavy neural enhancement models during the MVP.
6. `transcribe-only` must keep working after enhancement is added.
7. Enhancement must optimize ASR handoff, not perceptual restoration.
8. Enhanced audio must be stored in object storage when mode is `enhance_and_transcribe`.
9. If enhancement output validation passes, transcribe enhanced audio.
10. If enhancement output validation fails, transcribe raw audio and record `enhancement_fallback=true`.
11. If raw audio is also unavailable, mark the job `failed`.

Audio dependency rule:

1. If `soundfile` and `scipy` are already available in the project environment, use them for Cut B enhancement.
2. Else add them during Task 5.2.
3. Do not add PyTorch, torchaudio, or neural enhancement dependencies for MVP enhancement.

## 12. Observability strategy

Observability is staged.

### Cut A

Required:

1. clear application logs
2. job status persisted in PostgreSQL
3. error messages persisted on failed jobs
4. request and worker logs sufficient to debug the smoke test

Do not build Prometheus, OpenTelemetry, Grafana, or alerts before Cut A passes.

### Cut B

Add:

1. JSON structured logs
2. `GET /metrics`
3. Prometheus scrape config
4. OpenTelemetry API request traces
5. OpenTelemetry worker task traces using manual job ID and trace context propagation
6. one Grafana dashboard
7. three basic alerts

Basic alerts:

1. API error rate above threshold
2. queue backlog above threshold
3. worker heartbeat missing

Deferred:

1. quality dashboards
2. experiment comparison dashboards
3. preset ranking analytics
4. business analytics

Decision rules:

1. If trace context propagation between API and worker works, link worker spans to the API request trace.
2. Else create worker spans with job ID attributes and record the limitation in the progress tracker.
3. Do not delay Cut B completion for distributed trace linkage if API traces, worker spans, logs, metrics, dashboard, and alerts are present.

## 13. Testing strategy

Tests must follow the execution cut.

### Cut A tests

Required:

1. settings unit tests
2. fake ASR adapter unit tests
3. storage client tests
4. job model tests
5. API tests for `/health` and `/ready`
6. API test for job creation through `POST /v1/transcribe`
7. worker test for transcribe-only processing with fake adapter
8. smoke test or script proving upload to completed result

The Cut A smoke test must verify:

1. upload returns a job ID
2. job reaches `completed`
3. raw audio object exists
4. transcript object exists
5. result endpoint returns persisted transcript text
6. no real provider credentials are required

### Cut B tests

Add:

1. AssemblyAI adapter unit tests with mocked HTTP responses
2. live AssemblyAI smoke test with deterministic skip/run rules
3. preset registry tests
4. enhancement fallback tests
5. end-to-end `enhance-and-transcribe` test with fake ASR
6. metrics endpoint test
7. frontend basic flow test using mocked or local backend API

### Cut C tests

Add:

1. CI lint
2. type checks
3. full unit test run
4. integration test run
5. Docker image build validation
6. post-deploy smoke test

Rules:

1. CI must use fake adapter.
2. CI must not require AssemblyAI credentials.
3. Tests must not write heavy artifacts inside the repository.
4. Test artifacts must use configured runtime or artifact roots.
5. A task is not done until relevant tests or smoke checks have run.
6. If a test cannot run because a dependency is unavailable, stop, record the missing dependency, and do not mark the task complete.

## 14. Implementation phases and tasks

## Phase 0. Bootstrap and guardrails

Goal: make the repository safe for controlled execution.

### Task 0.1. Inspect repository state

Actions:

1. inspect existing files and directories
2. identify whether this is a fresh repo or partial implementation
3. confirm repository root
4. verify Git remote if present
5. inspect current branch
6. do not delete existing code during this task

Done when:

1. current structure is understood
2. no duplicate repo root has been created
3. active branch and remote state are recorded in the tracker
4. next task can be applied to the actual checkout

Decision rules:

1. If the repo is fresh, mark it as `fresh`.
2. If implementation files already exist, mark it as `partial`.
3. If the remote is not `https://github.com/gbibbo/asr_enhancement` or its SSH equivalent, record the mismatch and stop.
4. If no remote exists, continue locally and record `remote_missing`.

### Task 0.2. Create progress trackers

Actions:

1. create `docs/claude_task_progress.md` if missing
2. create `docs/claude_task_progress.yaml` if missing
3. record Phase 0 as in progress
4. record the current execution cut as `backend_vertical_slice`

Done when:

1. both trackers exist
2. next pending task is visible
3. tracker format is simple enough to maintain manually

Decision rules:

1. If trackers already exist, update them without deleting history.
2. If trackers disagree, use the Markdown tracker for human-readable history and the YAML tracker for current state.
3. If both are empty or missing, initialize both from Task 0.1 findings.

### Task 0.3. Add minimal project metadata

Actions:

1. create or update `README.md` with a short English project description
2. create or update `.gitignore`
3. add `.env.example` with non-secret defaults
4. ensure generated artifacts, runtime data, caches, `.env`, and local MinIO data are ignored

Done when:

1. metadata exists
2. secrets are not committed
3. artifact paths are excluded from Git

Decision rules:

1. If `README.md` exists, preserve useful content and add missing MVP description.
2. If `.gitignore` exists, extend it.
3. If `.env.example` exists, update it without adding secrets.
4. If a real `.env` is present, ensure it is ignored and do not print secrets.

## Phase 1. Backend skeleton for Cut A

Goal: boot a minimal backend stack with real dependencies.

### Task 1.1. Create backend package structure

Actions:

1. create API service structure
2. create worker service structure
3. create shared libraries for common settings, storage, ASR adapters, audio pipeline, and models
4. avoid frontend scaffolding

Required files or packages:

```text
services/api/
services/worker/
libs/common/
libs/asr_adapter/
libs/audio_pipeline/
tests/
```

Done when:

1. imports are coherent
2. there are no duplicate settings modules
3. the structure supports API and worker shared code

Decision rules:

1. If a compatible package already exists, extend it.
2. If duplicate packages exist, keep the one imported by the application entrypoint and remove only clearly unused generated duplicates after recording the decision.
3. If no application entrypoint exists, create one under `services/api/`.

### Task 1.2. Add Python project configuration

Actions:

1. create or update dependency management files
2. include FastAPI, Uvicorn, Celery, Redis client, PostgreSQL driver, SQLAlchemy 2.x, Alembic, MinIO or S3-compatible client, Pydantic settings, pytest, and HTTP test client
3. keep dependencies minimal for Cut A
4. do not add DSP, PyTorch, torchaudio, or ML packages in Cut A

Done when:

1. dependencies install in the intended development environment
2. tests can import application modules
3. no heavy neural packages are introduced for Cut A

Decision rules:

1. If `pyproject.toml` exists, extend it.
2. Else create `pyproject.toml`.
3. If another dependency system exists, keep it only if it is already functional and record the decision.
4. If dependency installation fails, stop and record the exact failure.

### Task 1.3. Implement settings

Actions:

1. create a single settings module
2. load environment variables
3. define provider default as `fake`
4. define database URL, Redis URL, object storage endpoint, bucket names, and upload limits
5. include runtime and artifact root variables for non-Docker paths

Done when:

1. settings unit tests pass
2. missing required settings fail clearly
3. fake provider works without secrets

Decision rules:

1. If an existing settings module is present, consolidate into it.
2. If multiple settings modules exist, keep one and redirect imports.
3. If `ASR_PROVIDER` is unset, use `fake`.
4. If `ASR_PROVIDER=assemblyai` and key is missing, allow app startup but fail provider jobs cleanly.

### Task 1.4. Add FastAPI skeleton

Actions:

1. create FastAPI app module
2. implement `GET /health`
3. implement placeholder `GET /ready`
4. add consistent JSON error responses for known application errors

Done when:

1. API imports successfully
2. `/health` returns success
3. API tests for `/health` pass

Decision rules:

1. If an app factory already exists, use it.
2. Else create `services/api/app/main.py`.
3. `/health` must not check external dependencies.
4. `/ready` must be upgraded in Task 2.3.

### Task 1.5. Add Celery skeleton

Actions:

1. create Celery app configuration
2. connect to Redis broker
3. add a diagnostic task named `debug.ping`
4. do not implement ASR processing yet

Done when:

1. worker imports successfully
2. Celery can connect to Redis in Compose
3. `debug.ping` can run in the worker
4. no real provider code is called

Decision rules:

1. If Celery config already exists, extend it.
2. Else create `services/worker/app/celery_app.py`.
3. If Redis is unavailable, worker startup failure is acceptable, but the failure must be clear.

### Task 1.6. Add Docker Compose backend stack

Actions:

1. create Compose files under `infra/compose/`
2. include `api`, `worker`, `postgres`, `redis`, and `minio`
3. use named Docker volumes for Postgres, Redis, and MinIO
4. expose only required development ports
5. do not add frontend, Prometheus, Grafana, or OTel

Done when:

1. backend stack starts
2. API container can reach Postgres, Redis, and MinIO
3. worker container can reach Redis, Postgres, and MinIO
4. no out-of-scope services are started

Decision rules:

1. If a Compose file already exists, modify it to match Cut A services.
2. If it contains later-cut services, disable or remove them for Cut A.
3. If named volumes are used, ensure they are not inside the repository.
4. If bind mounts are used for source code, ensure generated runtime data is ignored.

## Phase 2. Persistence and readiness for Cut A

Goal: make the backend depend on real PostgreSQL, Redis, and object storage.

### Task 2.1. Implement database models and migrations

Actions:

1. define job table
2. create initial Alembic migration
3. include timestamps
4. include object URI fields
5. include error fields
6. include status and mode fields

Done when:

1. migration runs from zero
2. database tests pass
3. job rows can be created and read

Decision rules:

1. If Alembic already exists, add a new migration.
2. Else initialize Alembic.
3. If an existing job table conflicts with this contract, migrate it to the contract rather than creating a second job table.
4. If migration from zero fails, stop and record failure.

### Task 2.2. Implement object storage client

Actions:

1. create storage abstraction for `put`, `get_to_file`, `exists`, and URI generation
2. support MinIO locally
3. create buckets idempotently in development startup or setup script
4. avoid writing final artifacts to application-local folders

Done when:

1. storage tests pass
2. object put and exists checks work
3. missing bucket behavior is clear

Decision rules:

1. If bucket does not exist in development, create it.
2. If bucket does not exist outside development, fail readiness with a clear error.
3. If object upload fails, propagate a typed storage error.
4. If object download fails, propagate a typed storage error.

### Task 2.3. Implement dependency readiness

Actions:

1. update `GET /ready` to check PostgreSQL
2. check Redis
3. check object storage
4. return dependency-specific status

Done when:

1. readiness tests cover healthy dependencies
2. readiness reflects real dependencies
3. `/health` remains a lightweight process check

Decision rules:

1. If all dependencies are healthy, return HTTP 200.
2. If any dependency is unhealthy, return HTTP 503 with dependency details.
3. If a dependency check times out, return HTTP 503 and name the timeout.
4. Do not hide dependency failures behind a generic ready response.

## Phase 3. Cut A transcribe-only backend path

Goal: complete the first working vertical slice.

### Task 3.1. Implement fake ASR adapter

Actions:

1. create adapter interface
2. create fake adapter implementation
3. return deterministic transcript text
4. include normalized metadata
5. write unit tests

Done when:

1. fake adapter works without network
2. fake adapter tests pass
3. normalized result schema is stable

Decision rules:

1. If fake transcript fixture text is configured, return that text.
2. Else return `This is a deterministic fake transcript for local testing.`
3. If input file is missing, raise a typed adapter error.
4. If input file exists, fake adapter must not inspect audio content beyond existence and size checks.

### Task 3.2. Implement upload validation

Actions:

1. accept short recorded audio uploads
2. validate file extension and content type
3. enforce file size limit
4. store upload temporarily only as needed to persist to object storage
5. return useful validation errors in English

Allowed extensions for Cut A:

1. `.wav`
2. `.mp3`
3. `.m4a`
4. `.flac`

Done when:

1. valid short audio is accepted
2. invalid file types are rejected
3. oversized files are rejected
4. validation tests pass

Decision rules:

1. If extension is not allowed, reject with HTTP 415.
2. If file size exceeds configured limit, reject with HTTP 413.
3. If content type is missing, accept only if extension is allowed.
4. If both content type and extension are suspicious, reject with HTTP 415.

### Task 3.3. Implement `POST /v1/transcribe`

Actions:

1. receive audio file
2. create job row with `queued` status
3. persist raw audio to object storage
4. enqueue Celery task
5. return job ID and status
6. do not call ASR synchronously in the request handler

Done when:

1. endpoint creates a persisted job
2. raw audio object exists
3. Celery task is queued
4. API tests pass

Decision rules:

1. If raw audio persistence fails, do not enqueue task and mark job `failed`.
2. If task enqueue fails after raw audio persistence, mark job `failed`.
3. If job creation fails, return HTTP 500 with safe error response.
4. If all steps succeed, return HTTP 202.

### Task 3.4. Implement worker transcribe-only task

Actions:

1. load job by ID
2. mark job `running`
3. resolve raw audio object to local temporary file
4. call fake ASR adapter
5. persist transcript JSON to object storage
6. persist transcript text and artifact URI in PostgreSQL
7. mark job `completed`
8. on failure, mark job `failed` and persist error message

Done when:

1. worker processes queued jobs
2. completed jobs contain transcript text and transcript URI
3. failed jobs contain error message
4. worker tests pass

Decision rules:

1. If job ID is unknown, log error and exit task without creating a new job.
2. If job is already `completed`, exit without modifying it.
3. If job is `running`, continue only if this execution owns the current task attempt.
4. If raw audio download fails, mark job `failed`.
5. If ASR adapter fails, mark job `failed`.
6. If transcript upload fails, mark job `failed`.
7. If completion artifact checks fail, mark job `failed`.

### Task 3.5. Implement job status endpoint

Actions:

1. implement `GET /v1/jobs/{job_id}`
2. read from PostgreSQL
3. return job ID, status, mode, provider, preset, timestamps, and artifact availability
4. return 404 for unknown jobs

Done when:

1. endpoint reflects persisted job state
2. endpoint does not depend on Celery result backend state
3. tests pass

Decision rules:

1. If job exists, return HTTP 200.
2. If job does not exist, return HTTP 404.
3. Do not expose internal stack traces.
4. Do not expose raw provider payload in status response.

### Task 3.6. Implement job result endpoint

Actions:

1. implement `GET /v1/jobs/{job_id}/result`
2. read from PostgreSQL and transcript artifact
3. return stable result for completed jobs
4. return stable response for queued, running, or failed jobs
5. return 404 for unknown jobs

Done when:

1. completed result is returned from persisted state
2. incomplete jobs are handled clearly
3. tests pass

Decision rules:

1. If job does not exist, return HTTP 404.
2. If job is `queued` or `running`, return HTTP 202 with current status.
3. If job is `failed`, return HTTP 200 with status and persisted error message.
4. If job is `completed`, return HTTP 200 with transcript result.
5. If job is `completed` but transcript artifact is missing, mark job `failed` and return HTTP 500 with safe error response.

### Task 3.7. Add Cut A smoke test

Actions:

1. add a tiny test WAV fixture or generate one in the test script
2. submit it to `POST /v1/transcribe`
3. poll job status until completion or timeout
4. fetch result
5. verify fake transcript text
6. verify artifact references exist

Done when:

1. smoke test passes from clean stack
2. no real provider credentials are needed
3. no heavy artifacts are written to the repository
4. progress tracker marks Cut A complete

Decision rules:

1. If smoke test passes, mark Cut A complete and stop.
2. If smoke test fails, keep Cut A incomplete and record the failure.
3. If timeout occurs, record final observed job status and worker logs.
4. Do not start Cut B until Cut A is complete.

Cut A gate: stop after this task and report the result.

## Phase 4. AssemblyAI adapter for Cut B

Goal: add real provider support without making it the default.

### Task 4.1. Implement AssemblyAI adapter with mocked tests

Actions:

1. add AssemblyAI client code behind adapter interface
2. read API key from environment
3. support pre-recorded transcription only
4. normalize provider response
5. persist raw provider payload
6. write mocked HTTP tests

Done when:

1. mocked tests pass
2. missing API key fails cleanly only when AssemblyAI is selected
3. fake provider remains default

Decision rules:

1. If `ASR_PROVIDER=fake`, AssemblyAI code must not execute.
2. If `ASR_PROVIDER=assemblyai` and key is missing, fail the job with a configuration error.
3. If mocked AssemblyAI response contains transcript text, normalize and persist it.
4. If mocked AssemblyAI response indicates provider failure, mark job `failed`.

### Task 4.2. Add live provider smoke test with deterministic gating

Actions:

1. create test or script gated by environment variables
2. skip when gating variables are missing
3. document how to run it manually
4. keep it out of required CI

Done when:

1. test skips safely without credentials
2. test runs when credentials and flag are provided
3. fake path remains unaffected

Decision rules:

1. If `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY` is present, run the live smoke test.
2. Else skip the live smoke test and print the exact missing condition.
3. If live test fails, do not fail CI unless CI explicitly set `RUN_LIVE_ASSEMBLYAI_TEST=1`.
4. If live test passes, record provider smoke success in the tracker.

## Phase 5. Minimal enhancement flow for Cut B

Goal: add `enhance-and-transcribe` without destabilizing `transcribe-only`.

### Task 5.1. Add preset registry

Actions:

1. define preset schema
2. include `bypass`
3. include `light_clean`
4. include `denoise`
5. include `denoise_dereverb`
6. validate preset names
7. write tests

Done when:

1. invalid presets are rejected
2. all four MVP presets are registered
3. tests pass

Decision rules:

1. If preset is missing, default to `bypass`.
2. If preset is unknown, reject request with HTTP 400.
3. If mode is `transcribe_only`, ignore enhancement preset and store `preset=bypass`.
4. If mode is `enhance_and_transcribe`, validate preset before job creation.

### Task 5.2. Implement lightweight enhancement pipeline

Actions:

1. create enhancement interface
2. implement `bypass`
3. implement `light_clean`
4. implement `denoise`
5. implement `denoise_dereverb`
6. validate output file exists and is readable
7. add safe fallback behavior

Done when:

1. `bypass` produces valid handoff audio
2. non-bypass presets produce valid enhanced audio or trigger fallback
3. enhancement tests pass

Decision rules:

1. If preset is `bypass`, use raw audio as ASR input and do not create enhanced artifact.
2. If preset is `light_clean`, create enhanced WAV using gain normalization.
3. If preset is `denoise`, create enhanced WAV using high-pass filter and gain normalization.
4. If preset is `denoise_dereverb`, create enhanced WAV using high-pass filter and gain normalization, and record `dereverb_applied=false`.
5. If enhanced output validates, store it and use it for ASR.
6. If enhanced output does not validate, store fallback metadata and use raw audio for ASR.
7. If raw audio cannot be used, mark job `failed`.

### Task 5.3. Implement `POST /v1/enhance-and-transcribe`

Actions:

1. accept upload and preset
2. create job row with mode `enhance_and_transcribe`
3. persist raw audio
4. enqueue worker task
5. worker applies preset
6. worker stores enhanced audio when applicable
7. worker transcribes selected audio through adapter
8. worker persists final transcript and status

Done when:

1. endpoint works end-to-end with fake ASR
2. enhanced artifact is stored when applicable
3. fallback behavior is tested
4. `transcribe-only` still passes

Decision rules:

1. If preset validation fails, return HTTP 400 and do not create job.
2. If raw upload persistence fails, mark job `failed` and do not enqueue.
3. If enhancement succeeds, transcribe enhanced audio.
4. If enhancement fails validation but raw audio is valid, transcribe raw audio and record fallback.
5. If ASR fails, mark job `failed`.
6. After this task, rerun Cut A smoke test.

## Phase 6. Basic observability for Cut B

Goal: make the system visible without building a quality analytics platform.

### Task 6.1. Add JSON structured logs

Actions:

1. standardize request logs
2. standardize worker logs
3. include job ID in relevant logs
4. avoid logging secrets

Done when:

1. one request can be followed through API and worker logs
2. logs remain readable locally
3. secrets are not present in logs

Decision rules:

1. If a log is related to a job, include `job_id`.
2. If a log is related to a request, include request method, path, status, and duration.
3. If a value may contain a secret, redact it.
4. If structured logging breaks local readability, keep JSON and add clear field names.

### Task 6.2. Add metrics endpoint and Prometheus config

Actions:

1. expose `GET /metrics`
2. track request counts
3. track error counts
4. track job counts by status
5. track worker heartbeat metric
6. add Prometheus service to Compose
7. configure scrape target

Done when:

1. Prometheus can scrape API metrics
2. metrics include enough information to debug the demo path
3. metrics tests pass

Decision rules:

1. If `/metrics` is requested, return Prometheus text format.
2. If Prometheus cannot scrape API, keep task incomplete.
3. If worker heartbeat metric is unavailable from Celery, emit heartbeat from worker process on interval.
4. Do not add advanced quality metrics.

### Task 6.3. Add minimal traces

Actions:

1. add OpenTelemetry instrumentation for API requests
2. add manual span around worker job execution
3. propagate job ID through task payload
4. add OTel collector to Compose
5. export traces to collector

Done when:

1. one API request produces a trace
2. one worker job produces a span with `job_id`
3. instrumentation does not break tests

Decision rules:

1. If automatic FastAPI instrumentation works, use it.
2. Else create middleware span manually.
3. If trace context propagation through Celery works, link worker span to request trace.
4. Else create independent worker span with `job_id` and record limitation.
5. Do not block Cut B on distributed linkage if spans exist and are useful.

### Task 6.4. Add Grafana dashboard and alerts

Actions:

1. add one operational dashboard
2. add alert for API error rate
3. add alert for queue backlog
4. add alert for worker heartbeat missing

Done when:

1. dashboard loads locally
2. alerts are defined as configuration
3. no advanced analytics dashboard is added

Decision rules:

1. If dashboard cannot load from provisioned config, keep task incomplete.
2. If an alert cannot evaluate because metric is missing, add the missing metric or change the alert to an existing MVP metric.
3. Do not add dashboards for WER, CER, preset ranking, or experiments.

## Phase 7. Public demo frontend for Cut B

Goal: create a small UI that proves the backend flow.

### Task 7.1. Scaffold minimal Next.js frontend

Actions:

1. create frontend after Cut A passes
2. keep all UI text in English
3. create upload form
4. create mode selector
5. create preset selector
6. create submit button

Done when:

1. frontend starts locally
2. UI can submit to backend in development
3. no admin console is created

Decision rules:

1. If backend API is unavailable, frontend shows a clear English error.
2. If mode is `transcribe_only`, preset selector is disabled and set to `bypass`.
3. If mode is `enhance_and_transcribe`, preset selector is enabled.
4. Do not add login, admin views, batch uploads, or streaming UI.

### Task 7.2. Implement polling and result view

Actions:

1. poll job status
2. show status
3. show selected mode and preset
4. show transcript text
5. show original audio player when a playable URL is available
6. show enhanced audio player when enhanced audio exists and a playable URL is available
7. show simple timing summary when timestamps are available

Done when:

1. non-technical user can complete the core flow
2. frontend displays backend status
3. no streaming or batch features are present

Decision rules:

1. If job status is `queued` or `running`, keep polling until timeout.
2. If job status is `completed`, fetch and display result.
3. If job status is `failed`, display persisted error message.
4. If playable audio URL is unavailable, show artifact availability without player.
5. If timestamps are missing, hide timing summary.

### Task 7.3. Add demo limits

Actions:

1. enforce file size limit in frontend and backend
2. enforce allowed extensions in frontend and backend
3. add API rate limit
4. show clear English errors

Done when:

1. oversized uploads are rejected clearly
2. invalid extensions are rejected clearly
3. rate limit exists
4. backend and frontend behavior agree

Decision rules:

1. If file exceeds configured limit, reject before upload in frontend and reject again in backend.
2. If extension is not allowed, reject before upload in frontend and reject again in backend.
3. If rate limit is exceeded, return HTTP 429.
4. If frontend and backend validation disagree, backend is authoritative and frontend must be updated.

## Phase 8. CI and MVP hardening for Cut C

Goal: make the MVP reproducible.

### Task 8.1. Add CI baseline

Actions:

1. lint
2. type checks
3. unit tests
4. integration tests with fake adapter
5. Docker image build

Done when:

1. CI passes without real provider credentials
2. CI does not depend on local HPC paths
3. CI does not write heavy artifacts

Decision rules:

1. If type checker is configured, run it.
2. If type checker is not configured, add `mypy` or `pyright` and configure a minimal pass.
3. If Docker build fails, keep task incomplete.
4. If tests require AssemblyAI credentials, fix tests to use fake adapter.

### Task 8.2. Add smoke test documentation

Actions:

1. document how to start the stack
2. document how to run Cut A smoke test
3. document how to run enhancement flow
4. document how to run AssemblyAI live smoke test
5. document how to inspect logs and result endpoints

Done when:

1. setup can be followed from a clean checkout
2. fake path works without secrets
3. real provider path has explicit environment gating

Decision rules:

1. If a command requires secrets, document required variable names but not values.
2. If a command writes artifacts, document where artifacts go.
3. If a command is for live provider testing, mark it as gated by `RUN_LIVE_ASSEMBLYAI_TEST=1`.

### Task 8.3. Add deployment path documentation

Actions:

1. document single VPS Docker Compose deployment
2. document required environment variables
3. document secrets handling
4. document reverse proxy assumption
5. document post-deploy smoke test
6. keep deployment instructions minimal

Done when:

1. demo deployment path is reproducible
2. smoke test passes after deploy
3. no hidden manual steps are required beyond documented secrets

Decision rules:

1. If no domain is available, document deployment by server IP.
2. If a domain is available, document HTTPS through Caddy or equivalent reverse proxy.
3. If object storage is local MinIO on the VPS, document volume backup warning.
4. If using managed S3-compatible storage, document endpoint and bucket variables.

## 15. Progress tracker format

Maintain both trackers.

YAML shape:

```yaml
current_cut: backend_vertical_slice
current_phase: 0
current_task: "0.1"
last_completed_task: null
blocked: false
blocker: null
tasks:
  "0.1": pending
  "0.2": pending
  "0.3": pending
```

Markdown shape:

```markdown
# Claude Task Progress

Current cut: Backend vertical slice
Current phase: Phase 0
Current task: Task 0.1

## Completed

None yet.

## Current blocker

None.

## Next task

Task 0.1. Inspect repository state.
```

After every task:

1. update completed task
2. update next task
3. record tests or checks run
4. record failures or unverified parts
5. do not mark a gate complete without a passing check

Decision rules:

1. If a task passes verification, mark it complete.
2. If a task fails verification, keep it current and record failure.
3. If a task cannot run because of a missing dependency, mark `blocked: true`.
4. If a gate passes, stop and report.
5. If a gate fails, do not advance.

## 16. Post-MVP roadmap

Only after the MVP is stable, move to:

1. batch submission API
2. offline evaluation with WER and CER persistence
3. experiment tracking
4. top-K preset selection
5. preset promotion workflow
6. streaming session creation and live transcription
7. deeper optimization loops
8. larger quality dashboards
9. multi-user features
10. Kubernetes or production orchestration

Do not create post-MVP code during MVP implementation.

## 17. Practical control rules

1. Build the first working backend path before building breadth.
2. Do not implement streaming before the pre-recorded MVP is complete and tested.
3. Do not introduce new services unless the current task requires them.
4. Do not let the public demo become an admin console.
5. Do not make CI depend on real provider calls.
6. Do not build the full observability stack before Cut A passes.
7. Do not over-design enhancement before `transcribe-only` works end-to-end.
8. Keep every task rerunnable, testable, and easy to resume.
9. Use fake ASR by default.
10. Stop at gates and report status before moving to the next cut.
11. If a generated idea conflicts with this plan, follow this plan.
12. If this plan conflicts with `CLAUDE.md`, follow `CLAUDE.md` and record the conflict.

## 18. Short implementation summary

First prove this:

1. recorded audio in
2. raw audio persisted
3. job persisted
4. async worker runs
5. fake ASR adapter returns transcript
6. transcript persisted
7. stable status and result retrieval

Then add:

1. real provider adapter
2. enhancement
3. basic observability
4. small English-language demo
5. CI and deployment hardening

Everything beyond that belongs to post-MVP work.