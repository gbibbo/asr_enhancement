# Claude Task Progress

## History

| Task | Status | Date       | Notes                                                                 |
|------|--------|------------|-----------------------------------------------------------------------|
| 0.1  | done   | 2026-04-29 | Fresh repo: only CLAUDE.md and plan.md. No git, remote_missing.       |
| 0.2  | done   | 2026-04-29 | Created docs/claude_task_progress.yaml and docs/claude_task_progress.md. |
| 0.3  | done   | 2026-04-29 | git init, git identity set. Created README.md, .gitignore, .env.example. No commit. |
| 1.1  | done   | 2026-04-29 | Created package skeleton: services/api/app/, services/worker/app/, libs/common/, libs/asr_adapter/, libs/audio_pipeline/, tests/. PYTHONPATH import checks passed. |
| 1.2  | done   | 2026-04-29 | Created pyproject.toml with Cut A deps. Venv at .venv/. Third-party and project-module imports verified. pytest --collect-only exits with code 5 (no tests, no import errors). |
| 1.3  | done   | 2026-04-29 | Created libs/common/settings.py (pydantic-settings BaseSettings). 18 settings unit tests pass. Provider normalized/validated; upload_limit_bytes validated >0; cache behavior verified. No FastAPI/Celery/DB/storage touched. |
| 1.4  | done   | 2026-04-29 | FastAPI skeleton: /health, /ready placeholder, safe unhandled-exception JSON handler. 6 API tests pass. |
| 1.5  | done   | 2026-04-29 | Celery skeleton: celery_app.py + debug.ping task. 3 worker tests pass. No Redis required. |
| 1.6  | done   | 2026-04-29 | Docker Compose backend stack verified externally: exactly api, worker, postgres, redis, minio; no later-cut services; stack builds/starts; postgres, redis, minio healthy; only API exposes host port 8000; /health ok; API reaches Postgres, Redis, MinIO; worker reaches Redis; host pytest 27 passed; compose down ran without -v. Note: direct psycopg reachability checks require normalizing the SQLAlchemy URL from postgresql+psycopg:// to postgresql://. |
| 2.1  | done    | 2026-04-29 | Files: libs/common/db.py, libs/common/models.py (JobStatus, JobMode, Job — 15 fields), alembic.ini, alembic/env.py, alembic/script.py.mako, alembic/versions/496c2c194ab1_create_jobs_table.py, tests/db/__init__.py, tests/db/test_models_unit.py, tests/db/test_models_integration.py, infra/compose/Dockerfile.backend (added COPY alembic.ini/alembic/tests + pip install .[dev]). Login-node checks: unit tests 4/4 passed; existing 27 passed; offline upgrade/downgrade SQL correct. External WSL Docker verification passed: docker compose down -v; fresh postgres volume; alembic upgrade head ran from zero (Running upgrade -> 496c2c194ab1, create_jobs_table); \dt jobs confirmed table exists; \d jobs and \dT+ confirmed all columns and job_status/job_mode enum types; alembic downgrade base removed table and types; re-upgrade succeeded; pytest tests/db/test_models_unit.py 4 passed; pytest tests/db/test_models_integration.py 4 passed; pytest tests/ --ignore=tests/db 27 passed. |
| 2.2  | done    | 2026-04-29 | Files: libs/common/storage.py (StorageClient, 5 error classes, make_storage_client), tests/storage/__init__.py, tests/storage/test_storage_unit.py (14 tests), tests/storage/test_storage_integration.py (7 tests). URI format: s3://{bucket}/{key}. No Dockerfile changes needed. Login-node checks: 14/14 storage unit tests passed; 45/45 full suite passed (excluding integration tests). External WSL Docker verification passed (commit f43cc25): docker compose down -v; docker compose build api (confirmed COPY alembic.ini, alembic/, tests/, pip install .[dev]); docker compose up -d minio; docker compose run --rm api pytest tests/storage/test_storage_unit.py -v — 14 passed; docker compose run --rm api pytest tests/storage/test_storage_integration.py -v — 7 passed; docker compose run --rm api pytest tests/ --ignore=tests/db/test_models_integration.py -v — 52 passed. |
| 2.3  | done    | 2026-04-29 | Files: services/api/app/main.py (replaced /ready placeholder with real checks: _check_postgres, _check_redis, _check_storage; asyncio.to_thread + asyncio.wait_for; 5 s timeout per dep; HTTP 200 all ok / 503 any degraded), tests/api/test_health.py (13 tests: healthy 200, per-dep 503 failure, missing-bucket 503, unit test verifying ensure_bucket(create_if_missing=False)). Login-node: 52/52 passed. External WSL Docker verification passed (commit 8a667d8): docker compose build api; docker compose down -v; docker compose up -d; with bucket absent /ready returned 503 storage.status=error ("Bucket 'asr-platform' does not exist"); after bucket creation via storage client /ready returned 200 all ok; pytest tests/api/test_health.py -v — 13 passed; pytest tests/ --ignore=tests/db/test_models_integration.py --ignore=tests/storage/test_storage_integration.py -v — 52 passed; stopping Redis → 503 redis.status=error; stopping Postgres → 503 postgres.status=error. |
| 3.1  | done    | 2026-04-29 | Files created: libs/asr_adapter/errors.py (AdapterError, InputFileNotFoundError, AdapterTranscriptionError), libs/asr_adapter/schema.py (ASRResult dataclass, 8 fields), libs/asr_adapter/base.py (ASRAdapter ABC), libs/asr_adapter/fake.py (FakeASRAdapter), tests/asr_adapter/__init__.py, tests/asr_adapter/test_fake_adapter.py (17 tests). Files modified: libs/asr_adapter/__init__.py (public exports), libs/common/settings.py (fake_transcript field), tests/libs/test_settings.py (2 new tests). Login-node: 71/71 passed (52 prior + 17 adapter + 2 settings). No network, credentials, or running services required. |
| 3.2  | done    | 2026-04-29 | Files created: services/api/app/upload_validation.py (ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES, UploadValidationError, ValidatedUpload dataclass, validate_and_buffer_upload), tests/api/test_upload_validation.py (18 tests). main.py unchanged; HTTP mapping deferred to Task 3.3. Extension is authoritative; content type normalized but never gates acceptance when extension is valid (Cut A policy). Temp file created via mkstemp, deleted on any failure. Login-node: 18/18 new tests passed; 89/89 full non-integration suite passed. No external services required. |
| 3.3  | done    | 2026-04-29 | Files modified: pyproject.toml (added python-multipart>=0.0.9), services/api/app/main.py (UploadValidationError handler, 5 transcribe helpers, POST /v1/transcribe route), services/worker/app/celery_app.py (include=["services.worker.app.tasks"] in Celery constructor). Files created: services/worker/app/tasks.py (worker.transcribe_job stub), tests/api/test_transcribe.py (11 tests), tests/worker/test_celery_app.py updated (+1 registration test = 4 total). Login-node: 101/101 non-integration tests passed. External WSL Docker verification passed (commit bce632b): docker compose build api worker; clean stack with fresh DB volume; alembic upgrade head; MinIO bucket created; /ready 200; pytest tests/api/test_transcribe.py 11 passed; pytest full non-integration suite 101 passed; POST /v1/transcribe returned 202 with job_id 33feafb6-8a3b-4abe-9bfb-06ce9c2fbe2b, status queued; DB row confirmed (status=queued, mode=transcribe_only, raw_audio_uri=s3://asr-platform/raw_audio/33feafb6.../input.wav); worker logs show worker.transcribe_job registered and stub executed; no "Received unregistered task" error. |
| 3.4  | done    | 2026-04-30 | Files modified: services/worker/app/tasks.py (JobSnapshot dataclass, _load_job/_mark_job_running/_mark_job_completed/_mark_job_failed/_uri_to_key helpers, full transcribe_job task with malformed-UUID guard, 4-state idempotency, raw-audio download, FakeASRAdapter call, transcript JSON upload, artifact existence check, mark-completed, mark-failed on any error). Files created: tests/worker/test_transcribe_task.py (14 tests using fresh-import fixture + .run() to bypass Celery proxy), tests/worker/conftest.py (bootstrap env vars for collection-time celery_app import). Login-node: 14/14 new tests passed; 115/115 full non-integration suite passed. External WSL Docker verification passed (commit 09ddcc1): git pull --ff-only synced; docker compose build api worker; clean stack (down -v, up -d); alembic upgrade head; MinIO bucket created; pytest tests/worker/test_transcribe_task.py 14 passed; pytest full non-integration suite 115 passed; POST /v1/transcribe submitted tiny WAV; job ec57fba0-8e8c-4282-a622-4d8cc8318c55 reached status=completed on first poll; transcript_text="This is a deterministic fake transcript for local testing."; transcript_uri=s3://asr-platform/transcripts/ec57fba0.../transcript.json; error_message=null; StorageClient verified exists=True, JSON has text/language=en/provider=fake/raw_payload={}; worker logs show task received and "transcribe_job completed job_id=ec57fba0..."; task succeeded. |
| 3.5  | done    | 2026-04-30 | Files modified: services/api/app/main.py (dataclass/datetime/Union imports, JobStatusSnapshot frozen dataclass with 13 fields — status/mode typed Union[Enum,str], _load_job helper mapping ORM→snapshot inside session, _enum_or_str helper, GET /v1/jobs/{job_id} route). Files created: tests/api/test_job_status.py (10 tests, including regression for plain-string status/mode from PostgreSQL). Login-node: 10/10 new tests passed; 125/125 full non-integration suite passed. Bugfix: first Docker run returned 500 AttributeError 'str' has no 'value' — PostgreSQL returns plain strings for enum columns; fixed with _enum_or_str. External WSL Docker verification passed (commit 5a2ed82): git pull --ff-only; docker compose build api worker; clean stack down -v / up -d; alembic upgrade head; bucket created; pytest tests/api/test_job_status.py 10 passed; full suite 125 passed; GET /v1/jobs/00000000-... → 404; GET /v1/jobs/not-a-uuid → 422; POST /v1/transcribe submitted tiny WAV → job 48480ebf-ff12-43a2-a3c7-0cef698196c0; GET /v1/jobs/48480ebf-... → 200 with status="queued", mode="transcribe_only", raw_audio_uri present, transcript_uri=null. |
| 3.6  | done    | 2026-04-30 | Files modified: services/api/app/main.py (GET /v1/jobs/{job_id}/result route — reuses _load_job, _mark_job_failed, _enum_or_str; 5-branch logic: 404 not found, 202 queued/running, 200 failed+error_message, 200 completed, 500 completed-missing-artifact+best-effort-mark-failed; no MinIO fetch; no provider_payload_uri). Files created: tests/api/test_job_result.py (10 tests: 200 completed, response fields, 404, 422, 202 queued, 202 running, 200 failed, 500 missing transcript_text, 500 missing transcript_uri, plain-string status regression). Login-node: 10/10 new tests passed; 135/135 full non-integration suite passed (125 baseline + 10 new). External WSL Docker verification passed (commit b974f44): git pull --ff-only; docker compose build api worker; clean stack down -v / up -d; alembic upgrade head; bucket created; pytest tests/api/test_job_result.py — 10 passed; full non-integration suite — 135 passed; with worker stopped POST /v1/transcribe submitted tiny WAV → job 20de9071-2589-4e19-a5c6-a2d7b8813a38; GET /v1/jobs/20de9071-.../result → 202 {"status":"queued","detail":"Job is not yet complete."}; after worker start polling reached 200 on iteration 6 → {"status":"completed","transcript_text":"This is a deterministic fake transcript for local testing.","transcript_uri":"s3://asr-platform/transcripts/20de9071-.../transcript.json","completed_at":"2026-04-30T01:09:09.241409+00:00"}; GET /v1/jobs/00000000-.../result → 404; GET /v1/jobs/not-a-uuid/result → 422. |
| 3.7  | done    | 2026-04-30 | Files created: tests/smoke/__init__.py, tests/smoke/test_cut_a_smoke.py (1 async smoke test: POST /v1/transcribe → poll until completed → GET /v1/jobs/{job_id}/result → assert transcript_text, transcript_uri, completed_at, MinIO raw_audio object, MinIO transcript object). Login-node: 135/135 non-integration suite passed (tests/smoke/ excluded). External WSL Docker verification passed (commit 1bac54c): git pull --ff-only synced; git ls-files tests/smoke confirmed both files present; docker compose build api worker; clean stack down -v / up -d; alembic upgrade head; MinIO bucket created; curl /health → 200 {"status":"ok"}; curl /ready → 200 postgres+redis+storage all ok; pytest tests/smoke/test_cut_a_smoke.py — 1 passed; full non-integration suite — 135 passed. Cut A complete: upload works, raw audio persisted, job queued, worker processed, transcript persisted, status endpoint works, result endpoint works, MinIO artifacts exist, no real provider credentials required. |
| —    | —       | 2026-04-30 | **CUT A COMPLETE.** Next pending task: 4.1 (AssemblyAI adapter). |
| 4.1  | done    | 2026-04-30 | Files created: libs/asr_adapter/assemblyai.py (AssemblyAIAdapter — upload/submit/poll flow, plain httpx, constructor-injected _http_client and _sleep for deterministic tests, safe error messages with no key leakage), libs/asr_adapter/factory.py (make_asr_adapter(settings)), tests/asr_adapter/test_assemblyai_adapter.py (24 tests: interface, missing file, result fields, HTTP request shape, timeout values, multi-poll, error cases, key safety), tests/asr_adapter/test_factory.py (3 tests). Files modified: pyproject.toml (httpx>=0.27 promoted from dev to prod dep), libs/asr_adapter/__init__.py (exports AssemblyAIAdapter + make_asr_adapter), services/worker/app/tasks.py (replaced hardcoded FakeASRAdapter with make_asr_adapter(settings), added provider payload persistence to provider_payloads/{job_id}/provider_response.json, updated _mark_job_completed signature with provider_payload_uri=None), tests/worker/test_transcribe_task.py (patched make_asr_adapter in tests 1/9/10/11/12, updated _mark_job_completed lambdas to accept *_, added 5 new worker tests: fake path regression, assemblyai success stores payload_uri, missing key marks failed, provider failure marks failed, empty raw_payload no upload). Login-node: 167/167 non-integration tests passed (135 baseline + 32 new: 24 adapter + 3 factory + 5 worker). No real credentials used. No real network calls made. Checkout path deviation: CLAUDE.md default is /mnt/fast/nobackup/users/gb0048/asr_enhancement but active checkout confirmed at /mnt/fast/nobackup/users/gb0048/asr_enhancement_platform; CLAUDE.md rule applied (treat directory containing CLAUDE.md as repo root); remote git@github.com:gbibbo/asr_enhancement.git is correct. Next task: 4.2. |
| 4.2  | done    | 2026-04-30 | Files created: tests/integration/__init__.py, tests/integration/test_live_assemblyai.py (1 test: @pytest.mark.live_provider, module-level skip when RUN_LIVE_ASSEMBLYAI_TEST!=1 or ASSEMBLYAI_API_KEY missing, 1-s silent WAV via stdlib wave+io.BytesIO written to tmp_path, AssemblyAIAdapter with poll_interval=5s/max_wait=300s, asserts ASRResult/provider/provider_job_id/text type). Files modified: pyproject.toml (added norecursedirs=["integration"], markers entry). Skip-mode verification: pytest --collect-only → 0 hits for tests/integration path (norecursedirs working); pytest tests/integration/test_live_assemblyai.py -v → 1 skipped, 0 failed (both missing vars named in skip message); pytest tests/ → 167 passed, 0 failed (baseline unchanged, no regressions). No live provider call made. First external live run failed: HTTP 400 on transcript submit. Fix (commit 3248ff7): libs/asr_adapter/assemblyai.py updated — added speech_models=["universal"] to submit JSON body; removed headers dict parameter from _upload/_submit/_poll (auth header now built inline in each httpx call to prevent Authorization value from appearing in pytest frame locals). Second external live run failed: provider returned status=error "language_detection cannot be performed on files with no spoken audio." Fix (current): libs/asr_adapter/assemblyai.py updated — added language_code constructor param (default "en"); submit body now includes language_code when not None, omits it when None. tests/asr_adapter/test_assemblyai_adapter.py updated: test_submit_post_called_with_correct_json_body_and_audio_url asserts language_code in body; 3 new tests added (test_submit_default_language_code_is_en, test_submit_custom_language_code_honored, test_submit_none_language_code_omits_field). Post-fix: 31/31 adapter tests pass, 51/51 asr_adapter suite passed, 174/174 default suite passed. External live verification passed: Gabriel ran RUN_LIVE_ASSEMBLYAI_TEST=1 ASSEMBLYAI_API_KEY=<redacted> pytest tests/integration/test_live_assemblyai.py -v -s — result: 1 passed in 8.18s. No API key committed or printed in tracker. Next task: 5.1. |
| 5.1  | done    | 2026-04-30 | Files created: libs/audio_pipeline/errors.py (UnknownPresetError(ValueError) with preset_id attribute), libs/audio_pipeline/presets.py (EnhancementPreset frozen dataclass, PRESET_REGISTRY with 4 presets: bypass/light_clean/denoise/denoise_dereverb, KNOWN_PRESET_IDS frozenset, get_preset(), resolve_preset(), BYPASS_PRESET_ID constant), tests/audio_pipeline/__init__.py, tests/audio_pipeline/test_presets.py (22 unit tests). No existing files modified. No DSP logic, no HTTP route changes, no DB schema changes. Login-node: 22/22 preset tests passed; full non-integration suite (--ignore integration --ignore db/test_models_integration.py --ignore storage/test_storage_integration.py) 196 passed + 1 pre-existing smoke-test failure (test_cut_a_full_flow requires live Postgres — unchanged). No Docker, MinIO, Redis, or Postgres required for unit tests. Next task: 5.2. |
| 5.2  | done    | 2026-04-30 | Files created: libs/audio_pipeline/pipeline.py (EnhancementResult frozen dataclass, apply_preset(), _apply_dsp(), _normalize_gain(), _highpass(), _validate_output(); bypass returns input_path unchanged without creating output_dir; non-bypass presets call output_dir.mkdir(parents=True, exist_ok=True) before I/O; light_clean applies gain normalization to 0.95 peak; denoise/denoise_dereverb apply 4th-order Butterworth high-pass at 80 Hz + gain normalization; dereverb records diagnostic={"dereverb_applied": False}; DSP failures return enhancement_fallback=True + fallback_reason without raising), tests/audio_pipeline/test_pipeline.py (35 tests). Files modified: libs/audio_pipeline/__init__.py (added EnhancementResult, apply_preset, UnknownPresetError exports), pyproject.toml (added soundfile>=0.12, scipy>=1.11, numpy>=1.24 to dependencies). soundfile/scipy/numpy were already installed in .venv; added to pyproject.toml for reproducibility. No API, worker, DB, storage, or ASR adapter changes. Login-node: 35/35 new tests passed; 57/57 audio_pipeline suite passed; 231/231 full non-integration suite passed. No Docker, MinIO, Redis, or Postgres required. Not blocked. Commit: 7c35458. Next task: 5.3. |
| 5.3  | done    | 2026-04-30 | Files created: services/api/app/main.py (POST /v1/enhance-and-transcribe route; Form preset param; resolve_preset validation before job creation; UnknownPresetError → HTTP 400 {"error":"unknown_preset"}; _create_job extended with preset="bypass" 4th param; enhanced_audio_uri added to JobStatusSnapshot, _load_job, and GET /v1/jobs/{job_id} response; Form+File imports), services/worker/app/tasks.py (_enum_or_str helper; apply_preset+UnknownPresetError+JobMode imports; JobSnapshot.mode/preset with defaults; _load_job populates mode/preset via _enum_or_str; _mark_job_completed extended with enhanced_audio_uri=None; enhancement branch in transcribe_job: apply_preset → upload enhanced_audio/{job_id}/output.wav when enhanced=True; fallback uses raw audio; enhancement_meta merged into transcript JSON), tests/api/test_enhance_and_transcribe.py (13 tests), tests/api/test_job_status.py (2 new tests for enhanced_audio_uri), tests/worker/test_enhance_task.py (10 tests). Files modified: tests/api/test_job_result.py (_make_snapshot gets enhanced_audio_uri=None default), tests/worker/test_transcribe_task.py (2 lambda signatures updated for 6th arg). No DB migration needed (schema already has enhanced_audio_uri and enhance_and_transcribe mode). Login-node: 256/256 non-integration tests passed (231 baseline + 25 new). Commit: 5933dc9. External WSL Docker verification passed (commit 5933dc9): docker compose build api worker; clean stack (down -v / up -d); alembic upgrade head from zero (496c2c194ab1); bucket created; pytest tests/api/test_enhance_and_transcribe.py tests/worker/test_enhance_task.py — 23 passed; full non-integration Docker suite — 256 passed; pytest tests/smoke/test_cut_a_smoke.py — 1 passed (Cut A regression ok); manual E2E: unknown preset → {"error":"unknown_preset"} HTTP 400; light_clean job reached completed with mode=enhance_and_transcribe, preset=light_clean, enhanced_audio_uri non-null, transcript_text=deterministic fake text; ALL ASSERTIONS PASSED. No secrets printed or committed. Next task: 6.1. |
| 6.1  | done    | 2026-04-30 | Files created: libs/observability/__init__.py, libs/observability/logging.py (JSONFormatter + configure_logging; remove-then-add handler design; defensive redaction for key/secret/token/authorization/auth_header field names), tests/observability/__init__.py, tests/observability/test_json_formatter.py (15 tests: 7 formatter + 5 redaction + 3 configure_logging), tests/api/test_logging.py (7 tests: request middleware + job_created/enqueued log events), tests/worker/test_worker_logging.py (6 tests: malformed/not-found/received/running/completed/failed). Files modified: services/api/app/main.py (asynccontextmanager lifespan with configure_logging("api"); @app.middleware("http") request logger emitting api.request with method/path/status_code/duration_ms; unhandled exception handler now logs api.unhandled_exception; all job-related logger calls gain extra={"job_id": ...}; new api.job_created and api.job_enqueued info logs after create/enqueue steps in both routes), services/worker/app/tasks.py (worker.job_received log after UUID parse; worker.job_running log after mark-running; worker.job_completed replaces old completion log; worker.job_failed replaces old exception log; all existing logger calls gain extra={"job_id": ...}), services/worker/app/celery_app.py (worker_process_init signal → configure_logging("worker"); signal fires only in live worker process, never in pytest). No new dependencies; pyproject.toml unchanged. Login-node: 284/284 non-integration non-smoke tests passed (256 baseline + 28 new). No Docker required. JSON smoke check: two valid JSON lines with all required fields. Not blocked. Next task: 6.2. |
| 6.2  | done        | 2026-04-30 | Files created: libs/observability/metrics.py (isolated CollectorRegistry; API_REQUESTS/API_ERRORS/JOB_COUNTER/WORKER_HEARTBEAT metrics; get_metrics_output()/start_worker_metrics_server() helpers), infra/compose/prometheus.yml (scrape asr_api:8000 + asr_worker:9091), tests/observability/test_metrics.py (13 tests), tests/api/test_metrics_endpoint.py (10 tests), tests/worker/test_worker_metrics.py (4 tests). Files modified: pyproject.toml (prometheus-client>=0.20), libs/observability/__init__.py (metrics exports), services/api/app/main.py (GET /metrics route; API_REQUESTS increment in middleware; API_ERRORS in exception handler; JOB_COUNTER queued in both POST routes), services/worker/app/celery_app.py (start_worker_metrics_server(9091) + heartbeat thread on worker_process_init), services/worker/app/tasks.py (JOB_COUNTER running/completed/failed at state transitions), infra/compose/docker-compose.yml (Prometheus service; --concurrency=1 on worker; port 9091). Login-node: 311/311 non-integration non-smoke tests passed (284 baseline + 27 new). External WSL Docker verification passed (commit 1a5ca50): full stack (api, worker, prometheus, postgres, redis, minio) up and healthy; GET /metrics → 200 with asr_api_requests_total and asr_jobs_total definitions; GET http://localhost:9091/metrics → asr_worker_heartbeat_timestamp_seconds present; POST /v1/transcribe returned {"job_id":"...","status":"queued"} and asr_jobs_total{mode="transcribe_only",status="queued"} 1.0 visible in API metrics; Prometheus API confirmed both named targets UP: asr_api and asr_worker. No secrets printed or committed. Next task: 6.3. |

| 6.3  | blocked     | 2026-04-30 | Files created: libs/observability/tracing.py (_TRACING_CONFIGURED guard, configure_tracing with injected exporter=SimpleSpanProcessor or OTLP BatchSpanProcessor, _reset_tracing_for_tests resets both _TRACER_PROVIDER and _TRACER_PROVIDER_SET_ONCE), infra/otel/otel-collector-config.yml (OTLP HTTP receiver + debug exporter), tests/observability/test_tracing.py (14 tests: configure_tracing returns TracerProvider, sets global, idempotency × 4, injected exporter uses SimpleSpanProcessor, no exporter without env, span captured, job.id attribute, service.name resource, propagation inject/extract, child span linking, root span, _reset_tracing_for_tests clears all state including _TRACER_PROVIDER_SET_ONCE), tests/worker/test_worker_tracing.py (8 tests: span created, job.id/job.mode attributes, valid traceparent links to parent trace_id, None traceparent is root, failure records exception+StatusCode.ERROR, enqueue injects traceparent inside span, enqueue passes None outside span), tests/api/test_tracing.py (3 tests: instrument_app idempotent, health request produces span, double TestClient no duplicate spans). Files modified: pyproject.toml (4 OTel deps: opentelemetry-api/sdk/exporter-otlp-proto-http/instrumentation-fastapi), libs/observability/__init__.py (configure_tracing export), services/api/app/main.py (lifespan: configure_tracing + FastAPIInstrumentor guard; _enqueue_transcribe: propagate.inject → traceparent arg), services/worker/app/celery_app.py (configure_tracing("asr-worker") in worker_process_init), services/worker/app/tasks.py (traceparent Optional param; manual span with job.id/job.mode/job.preset attributes; _mark_job_running moved inside try/except so failures are recorded on span; span.record_exception + StatusCode.ERROR on failure), infra/compose/docker-compose.yml (otel-collector service; OTEL_EXPORTER_OTLP_ENDPOINT on api and worker). Login-node: 336/336 non-integration non-smoke tests passed. Key fixes during implementation: _reset_tracing_for_tests must reset both _TRACER_PROVIDER and _TRACER_PROVIDER_SET_ONCE (Once()); injected test exporters must use SimpleSpanProcessor not BatchSpanProcessor; celery module-level patch requires importlib.import_module (not from-package-import) to guarantee sys.modules registration after tasks_mod teardown pop; FastAPIInstrumentor captures tracer into build_middleware_stack closure at instrument_app() call time — between tests, uninstrument_app + reinstrument_app is required to refresh the closure with the new provider's tracer. Blocked: OTel collector trace verification requires Docker + OTel collector running in WSL. |
| 6.3* | blocked     | 2026-04-30 | **WSL verification on commit a674f90 FAILED — fix applied, awaiting re-verification.** WSL failure summary: stack came up healthy; alembic upgrade ok; bucket created; POST /v1/transcribe returned JOB_ID=9b00e91e-2862-47be-91fe-428274b3e83b; job polled to status=completed; collector logs contained ONE resource span only — service.name=asr-worker, name=worker.transcribe_job, job.id=9b00e91e-..., job.mode=transcribe_only, job.preset=bypass, Parent ID empty; NO asr-api resource span; trace IDs therefore did not match. Root cause: lifespan-time instrumentation is too late. Starlette builds and caches `app.middleware_stack` lazily on the FIRST ASGI call, which is the lifespan event itself. Sequence: (1) uvicorn calls `app(lifespan_scope, …)`; (2) `Starlette.__call__` builds `middleware_stack` (no OTel, since `instrument_app` has not run); (3) the lifespan event reaches the `lifespan()` handler; (4) `configure_tracing("asr-api")` + `FastAPIInstrumentor().instrument_app(app)` runs — patches `app.build_middleware_stack` and sets `_is_instrumented_by_opentelemetry=True`, but `app.middleware_stack` is already cached from step 2; (5) every subsequent HTTP request reuses the cached non-OTel stack → no API spans, no traceparent injected, worker span has empty parent. The login-node `test_health_request_produces_span` masked the bug because its fixture pre-instruments AND resets `app.middleware_stack = None` manually. Files changed: services/api/app/main.py (move `configure_tracing("asr-api")` and `FastAPIInstrumentor().instrument_app(app)` from lifespan to module level — directly after `app = FastAPI(...)` and before any ASGI call; lifespan now only calls `configure_logging("api")`); tests/api/test_tracing.py (+2 regression tests: `test_app_is_instrumented_at_module_import` runs a subprocess that imports `services.api.app.main` and asserts `_is_instrumented_by_opentelemetry is True` at import time, isolated from any in-process fixture cycle — verified to FAIL on the buggy code (`stdout='0'`) and PASS on the fix; `test_post_v1_transcribe_during_request_sends_traceparent_to_celery` builds a tiny WAV, stubs `_create_job`/`_upload_raw_audio`/`_set_raw_audio_uri`/`_mark_job_failed`, patches `celery_app.celery_app` via `importlib.import_module`, posts /v1/transcribe through TestClient, asserts exactly one `send_task` call with args=[job_id, traceparent], traceparent starts with `00-`, and the `/v1/transcribe` API span's trace_id equals the traceparent's trace_id field). Login-node after fix: 338/338 non-integration non-smoke tests passed (336 baseline + 2 new regression tests); summary line `============================= 338 passed in 3.61s ==============================` recorded in /tmp/task63_login_pytest_after_fix.log. Still blocked: WSL Docker verification must be rerun against this commit; the hardened script in "Task 6.3 WSL verification commands" remains the source of truth. |
| 6.3** | blocked    | 2026-04-30 | **WSL verification on commit 0db0a8b FAILED — propagation fix applied, awaiting re-verification.** WSL failure summary: API span and worker span both now appear in collector logs; `job.id` key is present; submitted JOB_ID=92bc8c06-a30b-446f-abbc-828bb7275c38 value is present; but the trace IDs do not match — API trace_id=8769e65dfb68b381ed80aa1b909f738d, worker trace_id=278a66843c34754163aa8d604c4990bd. Worker created a fresh root trace, meaning it received traceparent=None at task time. Root cause: `_enqueue_transcribe` ran inside `await asyncio.to_thread(...)` and called `propagate.inject(carrier)` from inside the threadpool worker. Although the route's async context had the FastAPIInstrumentor server span active, contextvars propagation across the threadpool boundary did not preserve the active span under uvicorn in production (it did under TestClient — which is why the unit test on a674f90 passed). The carrier received no `traceparent` key, the second positional arg to Celery's `send_task` was None, and the worker's `propagate.extract({})` produced an empty context, so `start_as_current_span(..., context=Context())` created a root span with a brand new trace_id. Files changed: services/api/app/main.py (added `_current_traceparent()` helper; changed `_enqueue_transcribe(job_id, traceparent=None)` signature; both routes now capture `traceparent = _current_traceparent()` in the async context and pass it explicitly to `_enqueue_transcribe` via `await asyncio.to_thread(_enqueue_transcribe, str(job_id), traceparent)` — no reliance on contextvars propagation through the threadpool); tests/api/test_tracing.py (+1 regression test `test_route_captures_traceparent_outside_threadpool`: monkeypatches `_enqueue_transcribe` with a capturing stub, posts /v1/transcribe through TestClient, asserts the route called `_enqueue_transcribe` with TWO positional args [job_id, traceparent] — the buggy code that captures inside the threadpool would only pass one arg; verified to FAIL on the buggy code with `Got args=('1f839fa6-...',)` and PASS on the fix); tests/api/test_transcribe.py, tests/api/test_enhance_and_transcribe.py, tests/api/test_logging.py, tests/api/test_metrics_endpoint.py (4 files: `lambda job_id: None` stubs updated to `lambda job_id, traceparent=None: None` to match the new signature); docs/claude_task_progress.md (WSL parser hardened: prefer exact span name `POST /v1/transcribe` over child spans like `POST /v1/transcribe http send`/`http receive`; worker span match tightened to exact `worker.transcribe_job`; failure messages include span names alongside trace IDs). Login-node after fix: 339/339 non-integration non-smoke tests passed (338 baseline + 1 new regression); summary line `============================= 339 passed in 3.82s ==============================` recorded in /tmp/task63_login_pytest_after_propagation_fix.log. Still blocked: WSL Docker verification must be rerun. |
| 6.3  | done        | 2026-04-30 | **Task 6.3 closed.** External WSL Docker OTel collector verification PASSED on commit 62c81da. Stack: `docker compose build --no-cache api worker` + `down -v` + `up -d postgres redis minio otel-collector` + collector readiness + `alembic upgrade head` + bucket creation + `up -d api worker` + API readiness — all completed. Job flow: tiny WAV generated; POST /v1/transcribe returned JOB_ID=a587f7c6-af0e-425b-84c6-d2dd575f0ee6; polling GET /v1/jobs/{JOB_ID} reached status=completed (no failure, no timeout). Diagnostic trace logs from the API and worker containers showed the full propagation chain intact: API `api.task_enqueued` traceparent_present=true, traceparent_trace_id=c7ffa478c9b8d59cefcfab81ebbfb370; worker `worker.job_received` traceparent_present=true, received_trace_id=c7ffa478c9b8d59cefcfab81ebbfb370; worker `worker.span_started` span_trace_id=c7ffa478c9b8d59cefcfab81ebbfb370 — API captured, worker received, worker span used the same trace_id. OTel collector parser output: API span `POST /v1/transcribe` and worker span `worker.transcribe_job` shared trace_id=c7ffa478c9b8d59cefcfab81ebbfb370; job.id=a587f7c6-af0e-425b-84c6-d2dd575f0ee6 present in collector logs; parser printed `PASS: API and worker share trace_id c7ffa478c9b8d59cefcfab81ebbfb370` and `PASS: job.id=a587f7c6-af0e-425b-84c6-d2dd575f0ee6 present in collector logs`. Docker pytest suite: `docker compose run --rm api pytest tests/ --ignore=tests/integration --ignore=tests/db/test_models_integration.py --ignore=tests/storage/test_storage_integration.py --ignore=tests/smoke -v` completed with `============================= 340 passed in 8.46s ==============================`. No secrets were printed or committed. Task 6.4 (Grafana dashboard and alerts) was NOT started. Next task: 6.4. |
| 6.4  | done        | 2026-04-30 | **Task 6.4 closed.** External WSL Docker verification PASSED on commit 28fc948 after the Dockerfile fix. Gabriel pulled master and reran the deterministic WSL verification script. Results: Grafana health check passed; Prometheus targets check passed (asr_api and asr_worker both up); Grafana dashboard provisioning check passed for `uid: asr-operational`; Prometheus alert rules check passed for all three alerts (ASRApiErrorRateHigh, ASRQueueBacklogHigh, ASRWorkerHeartbeatMissing); worker `/metrics` exposed `asr_queue_backlog_jobs`; Docker pytest `docker compose -f infra/compose/docker-compose.yml run --rm api python3 -m pytest tests/ --ignore=tests/integration --ignore=tests/db/test_models_integration.py --ignore=tests/storage/test_storage_integration.py --ignore=tests/smoke -v` finished with `============================= 356 passed in 9.05s ==============================`; final script line `TASK 6.4 WSL VERIFICATION OK` printed. No secrets were printed or committed. Task 7.1 (frontend scaffolding) was NOT started. Next task: 7.1. |
| 6.4* | blocked     | 2026-04-30 | **WSL verification on commit 0f05dfb FAILED at the Docker pytest step; fix applied, awaiting re-verification.** WSL failure summary: stack came up, infra services started, migrations + bucket setup ok, prometheus/grafana endpoints ready; Docker pytest produced `======================== 9 failed, 347 passed in 8.99s =========================`. All 9 failures were `FileNotFoundError` from the new Grafana/Prometheus config tests inside the `api` container (e.g. `/app/infra/grafana/provisioning/datasources/prometheus.yml not found`, `/app/infra/grafana/provisioning/dashboards/dashboards.yml not found`, `/app/infra/grafana/dashboards/asr_operational.json not found`, `/app/infra/prometheus/alerts.yml not found`, `/app/infra/compose/docker-compose.yml not found`). Root cause: `infra/` was not copied into the backend Docker image — `infra/compose/Dockerfile.backend` only copied `pyproject.toml`, `README.md`, `libs`, `services`, `alembic.ini`, `alembic`, and `tests`. The new tests under `tests/observability/test_grafana_provisioning.py` and `tests/observability/test_prometheus_alerts.py` use `Path(__file__).resolve().parents[2]` (= `/app` inside the container) and read config files under `infra/`, so they raised `FileNotFoundError` against the missing tree. Fix applied: `infra/compose/Dockerfile.backend` now also runs `COPY infra ./infra`. The whole `infra/` tree is 36K of pure config (8 files: otel collector config, Dockerfile.backend itself, docker-compose.yml, prometheus.yml, alerts.yml, asr_operational.json, two grafana provisioning YAMLs). No runtime data, no secrets, no `.env`, no heavy artifacts; no `.dockerignore` exists. Files changed: infra/compose/Dockerfile.backend (one line: `COPY infra ./infra`), docs/claude_task_progress.yaml (blocker reason updated), docs/claude_task_progress.md (this row). No test files modified — the config-file tests are correct; the bug was in the image build. Login-node after fix: `python3 -m pytest -q tests/observability/test_metrics.py tests/observability/test_queue_backlog_metric.py tests/observability/test_grafana_provisioning.py tests/observability/test_prometheus_alerts.py` → `29 passed in 0.27s`. Tracker stays blocked with `blocker: "WSL Docker verification failed because infra config files were missing from the api Docker image; fix pushed, repeat WSL verification pending"`. WSL Docker verification must be rerun against the new commit; the script in "Task 6.4 WSL verification commands" is unchanged. |
| 6.4  | blocked     | 2026-04-30 | **Task 6.4 implementation complete on datamove1; blocked pending WSL Docker verification.** Files created: infra/grafana/provisioning/datasources/prometheus.yml (uid: prometheus, url http://prometheus:9090, isDefault, editable=false), infra/grafana/provisioning/dashboards/dashboards.yml (file provider, path /var/lib/grafana/dashboards, folder ASR), infra/grafana/dashboards/asr_operational.json (uid asr-operational, 6 panels: API request rate by status_code, API error ratio (5m), Jobs by status (5m), Jobs by mode (5m), Worker heartbeat freshness with 60s/90s thresholds, Queue backlog; every panel target uses datasource {type:prometheus, uid:prometheus}), infra/prometheus/alerts.yml (3 alerts: ASRApiErrorRateHigh expr `sum(rate(asr_api_requests_total{status_code=~"5.."}[5m]))/clamp_min(sum(rate(asr_api_requests_total[5m])),1e-9)>0.05` for 5m severity warning; ASRQueueBacklogHigh expr `asr_queue_backlog_jobs > 50` for 5m severity warning; ASRWorkerHeartbeatMissing expr `(time()-asr_worker_heartbeat_timestamp_seconds)>90 or absent(asr_worker_heartbeat_timestamp_seconds)` for 2m severity critical), tests/observability/test_queue_backlog_metric.py (7 tests: gauge importable, output contains def, value after set, _resolve_default_queue_name uses celery_app.conf.task_default_queue, _resolve_default_queue_name falls back to "celery", _poll_queue_backlog_once sets gauge from llen, _poll_queue_backlog_once propagates redis errors), tests/observability/test_grafana_provisioning.py (3 tests: datasource yaml uid==prometheus, dashboards provider yaml, dashboard json uid==asr-operational + every panel target datasource uid==prometheus + no forbidden panel titles WER/CER/preset ranking/experiment/quality/business), tests/observability/test_prometheus_alerts.py (6 tests: alerts yaml parses with exactly one group of three rules, alert names present, api error rate uses asr_api_requests_total, queue backlog uses asr_queue_backlog_jobs, heartbeat alert covers stale AND absent(, compose mounts alert rules + grafana service exists with port 3000:3000 and depends on prometheus). Files modified: pyproject.toml (added PyYAML>=6 to dev optional-dependencies for new file-validation tests), libs/observability/metrics.py (added QUEUE_BACKLOG Gauge for asr_queue_backlog_jobs), services/worker/app/celery_app.py (added _resolve_default_queue_name, _poll_queue_backlog_once, _start_queue_backlog_thread; thread polls Redis LLEN of celery_app.conf.task_default_queue or "celery" every 5s and sets gauge; thread loop catches all exceptions so transient Redis outages just log a warning and retry; thread is started from worker_process_init alongside the existing heartbeat thread), infra/compose/prometheus.yml (added rule_files: [/etc/prometheus/alerts.yml]), infra/compose/docker-compose.yml (added grafana service grafana/grafana:10.4.2 on port 3000 with admin/admin demo creds and anonymous Viewer, mounting infra/grafana/provisioning ro and infra/grafana/dashboards ro plus asr_grafana_data named volume, depends_on prometheus; mounted infra/prometheus/alerts.yml into prometheus container; **removed prometheus.depends_on [api, worker]** so the WSL script can start prometheus after migrations and bucket setup without it implicitly starting api/worker first — Prometheus tolerates targets coming up later). Login-node: 356/356 non-integration non-smoke tests passed (340 baseline + 16 new); summary line `356 passed in 3.99s` from .venv pytest. Config parse check via PyYAML+json across all six new/modified files printed `CONFIG OK`. Decision rationale: alerts defined as Prometheus rule files (not Grafana unified alerts) — alerts only need to be "defined as configuration"; Prometheus evaluates them natively at the existing scrape cadence, no Alertmanager added. Datasource uid hard-coded to "prometheus" so dashboard JSON datasource references are deterministic. Heartbeat alert covers both stale series and absent metric (worker never came up) — required because subtraction yields no samples when gauge is absent. New metric asr_queue_backlog_jobs is the smallest deterministic option to make the queue backlog alert evaluable: same /metrics endpoint, no new exporter service. Blocked: WSL Docker verification of Grafana dashboard provisioning, Prometheus alert rules, and queue backlog metric requires Docker which is unavailable on datamove1 — see "Task 6.4 WSL verification commands" section below for the exact deterministic script Gabriel must run locally. |
| 7.2  | done        | 2026-04-30 | **Task 7.2 closed.** External WSL Node + Docker verification PASSED on commit `9256d818fd8dd6eec075097931e2193c44e46a87`. WSL backend startup: `git pull --ff-only`, `docker compose down -v`, `docker compose build api worker`, `up -d postgres redis minio otel-collector`, `alembic upgrade head`, MinIO bucket creation, `up -d api worker prometheus grafana` — all completed; `/ready` became usable for the frontend flow. WSL frontend Node checks: `npm install --no-audit --no-fund` completed; `npm run lint` passed with no ESLint warnings or errors; `npm run typecheck` passed; `npm run build` passed; `npm run dev` served the app on `http://localhost:3001` because port 3000 was already in use locally — same-origin proxy semantics are unchanged. Manual browser check A (`transcribe_only`): submitted `/tmp/asr_72_test.wav`; UI showed `job_id=9827a977-c486-4d80-a9e7-bd85d6d9cd3c`; final state reached `completed`; Mode row showed `transcribe_only`; no preset row was rendered; transcript text rendered non-empty as `This is a deterministic fake transcript for local testing.`; "Original audio: stored at <s3:// URI>" availability line appeared; **no `<audio>` element** rendered for the `s3://` artifact; timing summary rendered Created, Started, Completed, Time in queue, Processing time, and Total time; all durations were numeric and non-negative. Manual browser check B (`enhance_and_transcribe` with preset `denoise`): submitted `/tmp/asr_72_test.wav`; UI showed `job_id=030167d1-603b-4c30-aad2-e984b3f6e1f7`; previous job panel was replaced (deterministic cleanup of polling effect on `jobId` change); final state reached `completed`; Mode row showed `enhance_and_transcribe`; Preset row showed `denoise`; transcript text rendered non-empty; original-audio and enhanced-audio availability lines both appeared with `s3://` URIs; no `<audio>` element rendered for either; timing summary rendered with non-negative durations. Manual browser check C (backend unreachable): after `docker compose stop api worker`, submitting again showed exactly the canonical English message `Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.` — the page did not crash. Manual browser check D (admin surface absent): `curl http://localhost:3001/admin` returned `404`; `grep -ri "admin" services/frontend/app` returned no matches. Local cleanup performed on WSL: `services/frontend/next-env.d.ts` had only a generated Next comment change and was reverted locally; `services/frontend/tsconfig.tsbuildinfo` was removed locally; no WSL source changes need to be committed for Task 7.2 — closure is tracker-only. No secrets were printed or committed. Task 7.3 (demo limits) was NOT started. Next task: 7.3. |
| 7.2  | blocked     | 2026-04-30 | **Task 7.2 implementation complete on datamove1; blocked pending WSL Node + Docker verification.** Files modified: services/frontend/app/page.tsx (extended the existing client component with polling and a result view; module-scope constants `POLL_INTERVAL_MS = 2000` and `POLL_MAX_ATTEMPTS = 60`; new state `jobSnapshot/result/polling/pollError/pollTimedOut/resultError`; `useEffect` watches `jobId` and starts a recursive `setTimeout` poll loop fetching `GET /api/v1/jobs/{job_id}` through the existing route-handler proxy with a single `AbortController`; cleanup function aborts the controller, clears the pending timeout, and sets a captured `cancelled` flag so any in-flight fetch ignores its own resolution after cancellation — covers component unmount AND the new-job-while-polling case deterministically; on `completed` issues a single `GET /api/v1/jobs/{job_id}/result` and stops; status-side errors map to "Job not found." (404), `Backend returned ${status}` (other non-2xx), `UNREACHABLE_MSG` (503+matching detail or fetch throw), "Unexpected response from backend." (malformed/missing status); result-side non-`completed` payloads map to "Job result is not available." (404), "Job result is not yet available." (202), "Job result reports failed: ..." (200 failed), "Job completed but transcript is not available." (500 transcript_missing), `Result endpoint returned ${status}.` (other non-2xx), "Cannot reach backend API while loading the result." (network/parse); polling stops in all terminal/error cases; max-attempts exhausted sets `pollTimedOut` and renders "Polling timed out. The job may still be running. Last status: <status>."; result panel shows `job_id`, `status`, `mode`, `preset` (only when `mode === enhance_and_transcribe`); transcript precedence is `result.transcript_text` → `jobSnapshot.transcript_text` → "Transcript text is not available."; `isPlayableUrl` helper accepts `http://`, `https://`, `data:`, `blob:`, and `/`-prefixed URLs only — `s3://` URIs render as availability text without an `<audio>` element; original-audio block shows when `raw_audio_uri` is non-null, enhanced-audio block shows only when `enhanced_audio_uri` is non-null; timing summary renders when at least one of `created_at/started_at/completed_at` is present, derived durations use `Math.max(0, ...)` so values may legitimately read `0.0 s`), services/frontend/app/globals.css (added `.status`, `.field`, `.field-label`, `.result`, `.audio`, `.timing`, `.transcript`, and `audio` rules; minimal layout, no animations, no new fonts), services/frontend/README.md (moved polling, status display, transcript display, audio artifact availability, and timing summary from "Deferred" to the implemented scope; explicit note that audio players appear only when URLs are browser-playable and that current backend artifact URIs use `s3://`, so the UI shows availability text rather than an audio player; Task 7.3 demo limits stay deferred), docs/claude_task_progress.yaml (`blocked: true`, blocker text, `tasks."7.2": blocked`), docs/claude_task_progress.md (this row). No backend, libs/, infra/, alembic/, services/api, services/worker, root pyproject.toml, package.json, package-lock.json, route-handler proxy, observability, Grafana, Prometheus, OTel, DB, storage, ASR adapter, or enhancement code modified. No new dependencies. No new files. No backend CORS. No streaming/batch/auth/admin/dashboards/experiment/WER/CER/preset-ranking/Kubernetes additions. Page does not read `process.env`; the literal `BACKEND_API_BASE_URL` substring in [page.tsx](services/frontend/app/page.tsx) is part of the user-facing English error message inherited verbatim from Task 7.1 — it is not an env var read. datamove1 verification: all required greps matched — `POLL_INTERVAL_MS=2000` line 40, `POLL_MAX_ATTEMPTS=60` line 41, `/api/v1/jobs/` lines 105 and 171, `AbortController` line 100, `controller.abort` line 276, `clearTimeout` line 278, `isPlayableUrl` lines 43/485/499, `Cannot reach backend API` lines 36/108/117, `Job not found` line 197, `Polling timed out` line 460, `Transcript text is not available` line 474; `grep -ri admin services/frontend/app` returns nothing; `grep -n "process\.env" services/frontend/app/page.tsx` returns nothing. Backend pytest baseline: `env $(grep -v '^#' .env.example \| xargs) .venv/bin/pytest tests/ --ignore=tests/integration --ignore=tests/db/test_models_integration.py --ignore=tests/storage/test_storage_integration.py --ignore=tests/smoke -q` → `356 passed in 3.47s` (matches 7.1 baseline; backend untouched). Login-node Node-driven checks not run (datamove1 has no npm). Tracker stays blocked with `blocker: "Task 7.2 implementation pushed; awaiting WSL Node + Docker verification (npm install / npm run lint / npm run typecheck / npm run build, then manual browser checks A-D against the backend on localhost:8000)."` Task 7.3 was NOT started. WSL verification (backend startup, frontend verification, manual browser checks A–D) is recorded in the "Task 7.2 WSL verification commands" section below. |
| 7.1  | done        | 2026-04-30 | **Task 7.1 closed.** External WSL Node + Docker verification PASSED. Lockfile commit: `dac7955` (Gabriel ran `npm install` on WSL and pushed `services/frontend/package-lock.json`; npm is unavailable on datamove1 so the lockfile could not be generated on the login node). WSL backend startup: `git pull --ff-only`, `docker compose down -v`, `docker compose build api worker`, `up -d postgres redis minio`, `alembic upgrade head`, MinIO bucket creation, `up -d api worker`, `/ready` reached 200 — all completed. WSL frontend Node checks: `npm install` generated `services/frontend/package-lock.json`; `npm run lint` passed; `npm run typecheck` passed; `npm run build` passed; `npm run dev` served http://localhost:3000. Frontend proxy checks: `POST http://localhost:3000/api/v1/enhance-and-transcribe` returned `job_id=ef5b30bf-61e3-461d-ba51-3096cb860d24` `status=queued`; `POST http://localhost:3000/api/v1/transcribe` returned `job_id=c2f1b077-004b-4cb4-b2b5-836707951083` `status=queued` — confirming the route-handler proxy at `services/frontend/app/api/[...path]/route.ts` correctly forwards same-origin browser requests to `${BACKEND_API_BASE_URL}/v1/...`. Eleven manual browser checks: (1) page loaded at http://localhost:3000; (2) all visible UI text was English; (3) default mode was `transcribe_only`; (4) preset default was `bypass` and disabled in `transcribe_only`; (5) switching to `enhance_and_transcribe` enabled the preset selector; (6) `denoise` could be selected and persisted; (7) `enhance_and_transcribe` submit returned a `job_id` with no error region; (8) switching back to `transcribe_only` reset preset to `bypass` and disabled the selector; (9) `transcribe_only` submit returned a second `job_id`; (10) after `docker compose down`, submitting again showed the exact English message `Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.` — confirming the route-handler proxy's `503 {"detail": UNREACHABLE_MSG}` path triggered correctly when the upstream `fetch` threw and the submit handler matched on `status===503 && detail===UNREACHABLE_MSG`; (11) `/admin` returned `404` and `grep -ri admin services/frontend/app` returned nothing. Cleanup performed on WSL: `services/frontend/tsconfig.tsbuildinfo` removed and not committed; `services/frontend/next-env.d.ts` generated comment-only change reverted and not committed; only `package-lock.json` committed. No secrets were printed or committed. Task 7.2 (polling and result view) was NOT started. Next task: 7.2. |
| 7.1  | blocked     | 2026-04-30 | **Task 7.1 implementation complete on datamove1; blocked pending WSL Node verification.** Files created: services/frontend/package.json (next 14.2.15, react 18.3.1, react-dom 18.3.1, typescript 5.5.4, @types/node 20.14.10, @types/react 18.3.3, @types/react-dom 18.3.0, eslint 8.57.0, eslint-config-next 14.2.15; scripts dev/build/start/lint/typecheck; engines.node ">=18.18.0"), services/frontend/tsconfig.json (Next 14 strict App Router config, noEmit true, paths {"@/*":["./*"]}), services/frontend/next.config.mjs ({reactStrictMode:true} only — no rewrites; route-handler proxy is in app/api/[...path]/route.ts), services/frontend/next-env.d.ts (canonical Next reference shim), services/frontend/.eslintrc.json ({"extends":"next/core-web-vitals"}), services/frontend/.gitignore (/.next/, /node_modules/, /out/, /.env.local), services/frontend/.env.example (BACKEND_API_BASE_URL=http://localhost:8000), services/frontend/README.md (env var, dev commands, scope note: polling/result view deferred to 7.2, demo limits deferred to 7.3, frontend Compose deferred), services/frontend/app/layout.tsx (server component, <html lang="en">, metadata={title:"ASR Demo"}, imports ./globals.css), services/frontend/app/page.tsx ("use client", upload form with file input/mode selector/preset selector/submit button; default mode=transcribe_only, default preset=bypass; preset disabled and forced to bypass when mode=transcribe_only via useEffect; submit button disabled while submitting or when no file; submit handler routes to /api/v1/transcribe or /api/v1/enhance-and-transcribe with FormData {file, optional preset}; on !res.ok parses JSON detail — if status===503 and detail===UNREACHABLE_MSG shows the canonical English error, else shows backend detail, else shows "Backend returned ${status}"; on browser fetch throw shows UNREACHABLE_MSG; success renders queued job_id only — no polling, no transcript, no audio player, no timing summary, no admin UI), services/frontend/app/globals.css (minimal styles), services/frontend/app/api/[...path]/route.ts (frontend-only Next.js route-handler proxy; exports GET=POST=proxy and dynamic="force-dynamic"; reads BACKEND_API_BASE_URL server-side only with default http://localhost:8000; forwards content-type and request body server-side; on backend fetch failure returns NextResponse.json({detail: "Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct."}, {status:503}); otherwise passes through upstream status and content-type with arrayBuffer body). Files modified: docs/claude_task_progress.md (this row), docs/claude_task_progress.yaml (blocked: true, blocker text, tasks."7.1": blocked). No backend code, libs, infra/compose, root pyproject.toml, observability, Grafana, Prometheus, OTel, DB, storage, ASR adapter, or enhancement code modified. No backend CORS added. No next.config.mjs rewrites used. No tests added. No secrets. datamove1 verification: file presence OK for all twelve files; package.json/tsconfig.json/.eslintrc.json JSON parse OK; next.config.mjs has no `rewrites`; route handler shape lint OK (BACKEND_API_BASE_URL, "Cannot reach backend API", `export const dynamic = "force-dynamic"`, `export const POST`, `export const GET`, `status: 503`); page.tsx shape lint OK ("use client", /api/v1/transcribe, /api/v1/enhance-and-transcribe, transcribe_only, enhance_and_transcribe, bypass, denoise_dereverb, "Cannot reach backend API", "Backend returned"); `grep -ri admin services/frontend/app/` returns nothing; layout.tsx has `lang="en"`; .env.example has exact line `BACKEND_API_BASE_URL=http://localhost:8000`. Backend pytest baseline: `env $(grep -v '^#' .env.example | xargs) .venv/bin/pytest tests/ --ignore=tests/integration --ignore=tests/db/test_models_integration.py --ignore=tests/storage/test_storage_integration.py --ignore=tests/smoke -q` → `356 passed in 3.54s` (matches 6.4 baseline; backend untouched). Tracker stays blocked with `blocker: "Task 7.1 implementation pushed; awaiting WSL Node verification (Node >=18.18, npm install must generate services/frontend/package-lock.json, npm run lint/typecheck/build/dev) and the eleven manual browser checks against the backend on localhost:8000. package-lock.json must be committed before closure."` `services/frontend/package-lock.json` is **not** yet committed and **must be committed before Task 7.1 is closed** (datamove1 has no npm so the lockfile cannot be generated on the login node). Task 7.2 was NOT started. WSL verification (backend startup, frontend verification, eleven manual browser checks) recorded in the "Task 7.1 WSL verification commands" section below. |
| 7.3  | done        | 2026-04-30 | **Task 7.3 closed.** External WSL Node + Docker verification PASSED on commit `8734ecf`. Backend curl checks: API + worker restarted; `/ready` became healthy; `/tmp/asr_73_test.wav` generated; `POST /v1/transcribe` with `/etc/hostname` returned **415**; `POST /v1/transcribe` with a 200 MB sparse `.wav` returned **413**; after a fresh 60 s rate-limit window, 35 valid `POST /v1/transcribe` requests produced both **202** and **429** responses; a captured 429 response included `Retry-After`; the 429 JSON detail was exactly `Too many requests. Please try again in a moment.`; `/health`, `/ready`, and `/metrics` never returned 429 after 50 requests each — exclusion matrix held. API and worker were restarted again to clear the in-process limiter; `/ready` became healthy after the final restart. Frontend Node checks: `npm run typecheck` passed; `npm run lint` passed with no ESLint warnings or errors; `npm run build` passed; `npm run dev` served the app at `http://localhost:3000`. Manual browser checks: uploading a `.txt` file showed exactly `File type not allowed. Allowed types: .wav, .mp3, .m4a, .flac.` (no network request); uploading a 200 MB `.wav` showed exactly `File is too large. Maximum allowed size is 100 MB.` (no network request); uploading `/tmp/asr_73_test.wav` completed the happy path and rendered the transcript; rapid re-submission eventually showed exactly `Too many requests. Please try again in a moment.`; after stopping the backend, submitting again showed exactly `Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.`. Local cleanup performed on WSL: `services/frontend/next-env.d.ts` generated comment-only change was reverted locally; `services/frontend/tsconfig.tsbuildinfo` was removed locally; `/tmp/asr_73_big.wav` was removed; WSL `git status` was clean after cleanup — closure is tracker-only. No secrets were printed or committed. Task 8.1 (CI baseline) was NOT started. Next task: 8.1. |
| 7.3  | blocked     | 2026-04-30 | **Task 7.3 implementation complete on datamove1; blocked pending WSL Node + Docker verification.** Files created: services/api/app/rate_limit.py (RateLimiter class — instance-local asyncio.Lock created lazily on first await, instance-local dict[str, tuple[int, float]] mapping client IP → (count, window_start_monotonic), fixed 60 s window, per_minute<=0 short-circuits to (True, 0), retry_after = max(1, ceil(window_start + 60 - now)), reset() clears dict and is test-only — explicit comment "Per-process counter; for the demo's single-replica API container this is sufficient. Do not add Redis, slowapi, or any new dependency."), tests/api/conftest.py (autouse fixture _disable_rate_limit_by_default sets RATE_LIMIT_PER_MINUTE=0, clears get_settings cache, replaces app.state.rate_limiter with RateLimiter(0) before every test in tests/api/; module-level _DEFAULTS provides DATABASE_URL/REDIS_URL/MINIO_* via os.environ.setdefault so collection-time imports of celery_app — which calls get_settings at module level — succeed), tests/api/test_rate_limit.py (6 tests using the pinned httpx.ASGITransport(app=app, client=("ip", 0)) mechanism: test_third_post_returns_429_with_exact_body_and_retry_after — RateLimiter(2), three POSTs, first two 202, third 429 with body exactly {"error":"rate_limited","detail":"Too many requests. Please try again in a moment."} and Retry-After header parseable as integer ≥ 1; test_independent_ips_have_independent_buckets — RateLimiter(1) with two transports for 1.2.3.4 and 5.6.7.8, first POST from each → 202, second POST from each → 429; test_per_minute_zero_disables_limiter — 20 POSTs all 202; test_excluded_endpoints_never_429 — RateLimiter(1), one POST consumed and confirmed tripped, then 5 iterations of GET /health, GET /ready (deps mocked), GET /metrics, GET /v1/jobs/{id}, GET /v1/jobs/{id}/result — none return 429; test_trailing_slash_and_similar_paths_not_limited — POST /v1/transcribe/ and POST /v1/transcribexx never 429; test_get_on_upload_path_not_limited — GET /v1/transcribe never 429). Files modified: libs/common/settings.py (added rate_limit_per_minute: int = 30 with @field_validator rejecting negatives, accepting 0 as disabled), services/api/app/main.py (added `from services.api.app.rate_limit import RateLimiter` and `_RATE_LIMITED_PATHS = frozenset({"/v1/transcribe", "/v1/enhance-and-transcribe"})`; instantiate `app.state.rate_limiter = RateLimiter(get_settings().rate_limit_per_minute)` once at module load; new `@app.middleware("http")` `_rate_limit_middleware` registered AFTER `_request_logger` — Starlette wraps middlewares in reverse-add order so _request_logger remains the outermost wrapper, keeping API_REQUESTS labels and api.request log lines on 429 responses; middleware short-circuits unless `request.method == "POST"` AND `request.url.path` is exactly one of _RATE_LIMITED_PATHS; client_key = `request.client.host if request.client else "unknown"` — no X-Forwarded-For consultation; on reject returns JSONResponse status_code=429, body {"error":"rate_limited","detail":"Too many requests. Please try again in a moment."}, header Retry-After=str(retry_after_seconds)), .env.example (added UPLOAD_LIMIT_BYTES=104857600, RATE_LIMIT_PER_MINUTE=30), services/frontend/.env.example (added NEXT_PUBLIC_MAX_UPLOAD_BYTES=104857600 with comment "Frontend size check is a UX pre-flight only; the backend remains authoritative."), services/frontend/app/page.tsx (module-level `ALLOWED_EXTENSIONS = [".wav", ".mp3", ".m4a", ".flac"]` and `resolveMaxUploadBytes()`/`MAX_UPLOAD_BYTES`/`MAX_UPLOAD_MB` constants reading NEXT_PUBLIC_MAX_UPLOAD_BYTES with finite-positive fallback to 104_857_600; in onSubmit, after `setError(null); setJobId(null);` and BEFORE `setSubmitting(true)`, two pre-flight checks against `file.name.toLowerCase()` and `file.size` — extension miss → setError("File type not allowed. Allowed types: .wav, .mp3, .m4a, .flac.") and return, size miss → setError("File is too large. Maximum allowed size is " + MAX_UPLOAD_MB + " MB.") and return; file input `accept` changed from "audio/*" to ".wav,.mp3,.m4a,.flac,audio/*"; label text changed from "Audio file" to `"Audio file (max " + MAX_UPLOAD_MB + " MB; .wav, .mp3, .m4a, .flac)"`), tests/libs/test_settings.py (4 new tests: test_rate_limit_default==30, test_rate_limit_custom_positive=5, test_rate_limit_zero_accepted, test_rate_limit_negative_raises), tests/api/test_transcribe.py (added `from services.api.app.rate_limit import RateLimiter`; transcribe_client fixture installs `app.state.rate_limiter = RateLimiter(0)` after cache_clear), tests/api/test_enhance_and_transcribe.py (same pattern: import + enhance_client fixture installs RateLimiter(0)). No changes to: services/api/app/upload_validation.py (415/413 already authoritative), services/frontend/app/api/[...path]/route.ts (already preserves status + JSON body — 429 propagates through unchanged), ASR adapter, enhancement, storage client, Grafana/Prometheus/OTel configs, DB schema, Compose files. No new Python or Node dependencies. No Redis-backed limiter, no slowapi. Datamove1 verification (.venv pytest, RATE_LIMIT_PER_MINUTE=0, required env vars set): pre-implementation baseline `356 passed in 3.48s`; focused tests (tests/libs/test_settings.py + tests/api/test_upload_validation.py + tests/api/test_transcribe.py + tests/api/test_enhance_and_transcribe.py + tests/api/test_rate_limit.py) `72 passed in 1.44s`; full non-integration non-smoke regression `366 passed in 3.72s` (baseline 356 + 10 new = 366; 6 new rate-limit tests + 4 new settings tests); import smoke `python -c "from services.api.app.main import app; print(app.title)"` printed `ASR Enhancement Platform`. Tracker stays blocked with blocker "Frontend tsc/lint/build and end-to-end browser flow require Gabriel's local WSL+Docker; datamove1 has no npm/Docker." Task 8.1 was NOT started. WSL verification commands and manual browser checks for Task 7.3 are recorded in the "Task 7.3 WSL verification commands" section below. |
| 6.3*** | blocked   | 2026-04-30 | **WSL verification on commit 658c0d2 FAILED again — diagnostic logging + stronger test added; production still cannot be reproduced in tests.** WSL failure summary: stack came up healthy; POST /v1/transcribe returned JOB_ID=aa809beb-0ad3-4b6e-a6e2-d473b224cc81; job polled to status=completed; collector logs contained both API and worker spans; job.id key and JOB_ID value were present; but trace IDs still differ — parser-picked API trace_id=e2edc764d8c0a269d6ac9b3ab92b5759, worker trace_id=fb4d17964289b8fe040d12ee104115dd. The span list also included "POST /v1/transcribe" exact server span with a third trace_id 578c45429dc7a65d1f369f056a48fa96 — even the exact server span did not match the worker's trace, confirming the propagation chain is still broken end-to-end. Diagnosis to date: every in-process test we can write passes — `test_route_captures_traceparent_outside_threadpool` proves the route hands [job_id, traceparent] to `_enqueue_transcribe` with the right trace_id; `test_celery_apply_with_kwargs_propagates_traceparent_to_worker_span` proves Celery's task dispatch (Signature → apply → task-call) preserves the second positional arg and the worker's `propagate.extract` correctly applies it as parent context. Important finding while writing the eager test: Celery's `task_always_eager` config has NO effect on `celery_app.send_task()` — Celery emits `AlwaysEagerIgnored: task_always_eager has no effect on send_task` and tries to reach the broker. The send_task → broker → worker-pulls-message → worker calls task path therefore CANNOT be exercised in unit tests without real Redis; the apply() test is the closest in-process equivalent. Files changed: services/api/app/main.py (`_enqueue_transcribe` now emits a safe `api.task_enqueued` structured log with `job_id`, `traceparent_present` bool, and `traceparent_trace_id` extracted from the W3C traceparent — no secrets); services/worker/app/tasks.py (`worker.job_received` log extended with `traceparent_present` and `received_trace_id`; new `worker.span_started` log emits the actual `span_trace_id` of the worker.transcribe_job span — these three structured fields, compared between API and worker containers, will identify exactly which link in the chain drops the traceparent in the next WSL run); tests/worker/test_worker_tracing.py (+1 test `test_celery_apply_with_kwargs_propagates_traceparent_to_worker_span` exercising Task.apply() through Celery's full dispatcher — passes, proving the worker code correctly extracts and applies traceparent when handed to it via the same dispatcher Celery uses after pulling a message); docs/claude_task_progress.md (WSL script switched to `docker compose build --no-cache api worker` to guarantee no stale image layers; added a diagnostic-log dump section that runs `docker compose logs api/worker` and greps the three structured events so the operator can compare API `traceparent_trace_id`, worker `received_trace_id`, and worker `span_trace_id` directly without re-parsing collector output). Login-node after this iteration: 340/340 non-integration non-smoke tests passed (339 baseline + 1 new Celery-apply test); summary line `============================= 340 passed in 4.08s ==============================` recorded in /tmp/task63_login_pytest_after_second_propagation_fix.log. Still blocked: WSL Docker verification must be rerun on the new commit. The diagnostic logs from that run will conclusively identify whether the API is capturing a non-empty traceparent, whether Celery is delivering it to the worker, and whether the worker is creating its span with the right context. |

## Task 6.2 WSL verification commands

Run these commands from the WSL Docker checkout to complete verification.

```bash
cd ~/code/asr_enhancement
git pull --ff-only
cd infra/compose

docker compose build api worker
docker compose down -v
docker compose up -d postgres redis minio

docker compose run --rm api alembic upgrade head

docker compose run --rm api python - <<'PY'
from libs.common.settings import get_settings
from libs.common.storage import StorageClient
StorageClient.from_settings(get_settings()).ensure_bucket(create_if_missing=True)
print("bucket ready")
PY

docker compose up -d api worker prometheus

python3 - <<'PY'
import wave
from pathlib import Path

p = Path("/tmp/asr_metrics_test.wav")
with wave.open(str(p), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(b"\x00\x00" * 1600)
print(p)
PY

for i in $(seq 1 12); do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/metrics)
    [ "$status" = "200" ] && echo "API metrics ready" && break
    echo "Waiting for API metrics... ($i)"
    sleep 5
done

curl -s http://localhost:8000/metrics | grep "asr_api_requests_total"
curl -s http://localhost:8000/metrics | grep "asr_jobs_total"

for i in $(seq 1 18); do
    body=$(curl -s http://localhost:9091/metrics 2>/dev/null)
    echo "$body" | grep -q "asr_worker_heartbeat_timestamp_seconds" \
        && echo "Worker heartbeat metric found" && break
    echo "Waiting for worker heartbeat... ($i)"
    sleep 5
done

curl -s -X POST http://localhost:8000/v1/transcribe \
    -F "file=@/tmp/asr_metrics_test.wav;type=audio/wav;filename=test.wav" \
    --max-time 5 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d); assert 'job_id' in d"

curl -s http://localhost:8000/metrics | grep 'asr_jobs_total{.*status="queued"'

for i in $(seq 1 18); do
    targets=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null)
    result=$(echo "$targets" | python3 -c "
import json, sys
data = json.load(sys.stdin)
active = data.get('data', {}).get('activeTargets', [])
required = {'asr_api', 'asr_worker'}
up = {t.get('labels', {}).get('job') for t in active if t.get('health') == 'up'}
missing = required - up
print('OK' if not missing else 'MISSING: ' + ', '.join(sorted(missing)))
" 2>/dev/null || echo "ERROR")
    [ "$result" = "OK" ] && echo "Both Prometheus targets UP (asr_api, asr_worker)" && break
    echo "Waiting for Prometheus targets ($result)... ($i)"
    sleep 5
done

docker compose down
```

## Task 6.3 WSL verification commands

Run these commands from the WSL Docker checkout to complete verification. The goal is to confirm that traces from the API and worker appear in the OTel collector logs with matching trace IDs and that the Docker pytest suite passes.

```bash
#!/usr/bin/env bash
set -euo pipefail

cd ~/code/asr_enhancement
git pull --ff-only
cd infra/compose

# Force a clean rebuild — guards against stale image layers on the host
docker compose build --no-cache api worker
docker compose down -v
docker compose up -d postgres redis minio otel-collector

# Wait for OTel collector to be ready (exits non-zero on timeout)
collector_ready=0
for i in $(seq 1 12); do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4318/ 2>/dev/null || echo "000")
    [ "$status" != "000" ] && collector_ready=1 && echo "OTel collector ready" && break
    echo "Waiting for OTel collector... ($i/12)"
    sleep 5
done
[ "$collector_ready" = "1" ] || { echo "ERROR: OTel collector never became ready"; exit 1; }

docker compose run --rm api alembic upgrade head

docker compose run --rm api python3 - <<'PY'
from libs.common.settings import get_settings
from libs.common.storage import StorageClient
StorageClient.from_settings(get_settings()).ensure_bucket(create_if_missing=True)
print("bucket ready")
PY

docker compose up -d api worker

# Wait for API /health to return 200 (exits non-zero on timeout)
api_ready=0
for i in $(seq 1 12); do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    [ "$status" = "200" ] && api_ready=1 && echo "API ready" && break
    echo "Waiting for API... ($i/12)"
    sleep 5
done
[ "$api_ready" = "1" ] || { echo "ERROR: API never became ready"; exit 1; }

# Generate test WAV
python3 - <<'PY'
import wave
from pathlib import Path
p = Path("/tmp/asr_task63_test.wav")
with wave.open(str(p), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b"\x00\x00" * 1600)
print("WAV written:", p)
PY

# Submit job and capture JOB_ID
JOB_ID=$(curl -s -X POST http://localhost:8000/v1/transcribe \
    -F "file=@/tmp/asr_task63_test.wav;type=audio/wav;filename=test.wav" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['job_id'])")
echo "Submitted job_id: $JOB_ID"

# Poll until completed, fail on failed or timeout
job_done=0
for i in $(seq 1 24); do
    job_status=$(curl -s "http://localhost:8000/v1/jobs/${JOB_ID}" \
        | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])")
    echo "Poll $i: status=$job_status"
    [ "$job_status" = "completed" ] && job_done=1 && echo "Job completed" && break
    [ "$job_status" = "failed" ] && { echo "ERROR: job failed"; exit 1; }
    sleep 5
done
[ "$job_done" = "1" ] || { echo "ERROR: job did not complete within timeout"; exit 1; }

# Wait for BatchSpanProcessor to flush to collector
sleep 10

# --- Diagnostic logs (added 2026-04-30 for Task 6.3 propagation triage) ---
# These structured JSON lines reveal exactly what each side observed for the
# traceparent. Compare API "traceparent_trace_id" with worker "received_trace_id"
# and "span_trace_id" — they MUST all be identical for propagation to be working.
echo "=== API diagnostic: api.task_enqueued ==="
docker compose logs api 2>&1 | grep '"event": "api.task_enqueued"' | tail -3
echo "=== Worker diagnostic: worker.job_received ==="
docker compose logs worker 2>&1 | grep '"event": "worker.job_received"' | tail -3
echo "=== Worker diagnostic: worker.span_started ==="
docker compose logs worker 2>&1 | grep '"event": "worker.span_started"' | tail -3
echo "=========================================="

# Save collector logs to file for deterministic parsing
docker compose logs otel-collector > /tmp/otel-collector.log 2>&1
echo "Collector log saved to /tmp/otel-collector.log ($(wc -l < /tmp/otel-collector.log) lines)"

# Parse and assert trace propagation
python3 - /tmp/otel-collector.log "$JOB_ID" <<'PYEOF'
import sys, re

log_path = sys.argv[1]
job_id   = sys.argv[2]

with open(log_path) as f:
    text = f.read()

# Extract (span_name, trace_id) pairs from OTel debug exporter blocks
spans = []
for block in text.split("Trace ID"):
    trace_m = re.search(r":\s+([0-9a-f]{32})", block)
    name_m  = re.search(r"Name\s*:\s+(.+)", block)
    if trace_m and name_m:
        spans.append((name_m.group(1).strip(), trace_m.group(1).strip()))

print(f"Spans found: {len(spans)}")
for n, t in spans:
    print(f"  {t}  {n}")

# Prefer the exact server-span name "POST /v1/transcribe" over child spans
# such as "POST /v1/transcribe http send" / "http receive". The trace_id is
# shared, but picking the server span deterministically removes ambiguity.
all_transcribe = [(n, t) for n, t in spans if "/v1/transcribe" in n]
exact_post     = [(n, t) for n, t in all_transcribe if n == "POST /v1/transcribe"]
api_spans      = exact_post if exact_post else all_transcribe
worker_spans   = [(n, t) for n, t in spans if n == "worker.transcribe_job"]

assert api_spans,    f"FAIL: no API span for /v1/transcribe. All: {spans}"
assert worker_spans, f"FAIL: no worker.transcribe_job span. All: {spans}"

api_trace_id    = api_spans[0][1]
worker_trace_id = worker_spans[0][1]
assert api_trace_id == worker_trace_id, (
    f"FAIL: trace_id mismatch — API={api_spans[0][0]}={api_trace_id}, "
    f"worker={worker_spans[0][0]}={worker_trace_id}"
)

assert "job.id" in text, "FAIL: 'job.id' key not found in collector logs"
assert job_id in text,   f"FAIL: submitted job_id {job_id!r} not found in collector logs"

print(f"PASS: API and worker share trace_id {api_trace_id}")
print(f"PASS: job.id={job_id} present in collector logs")
PYEOF

# Run Docker pytest suite
docker compose run --rm api pytest tests/ \
    --ignore=tests/integration \
    --ignore=tests/db/test_models_integration.py \
    --ignore=tests/storage/test_storage_integration.py \
    --ignore=tests/smoke \
    -v 2>&1 | tee /tmp/task63_docker_pytest.log
tail -5 /tmp/task63_docker_pytest.log

docker compose down
```

## Task 6.4 WSL verification commands

Run on Gabriel's local WSL/Docker checkout. Fail-fast (`set -euo pipefail`); every condition is enforced by shell or Python and exits non-zero on failure. Critical ordering: only true infrastructure (`postgres`, `redis`, `minio`, `otel-collector`) starts before migrations; `prometheus` and `grafana` start in the same step as `api`/`worker` (the `prometheus.depends_on` was removed in this commit so `up -d prometheus` no longer pulls `api`/`worker` along).

```bash
#!/usr/bin/env bash
set -euo pipefail

cd ~/code/asr_enhancement

# 1. Pull the commit pushed from datamove1
git pull --ff-only

COMPOSE="docker compose -f infra/compose/docker-compose.yml"

# A. Clean slate
$COMPOSE down -v
$COMPOSE build

# B. Start ONLY true infrastructure first
$COMPOSE up -d postgres redis minio otel-collector

# C. Wait for Postgres
for i in $(seq 1 30); do
  if $COMPOSE exec -T postgres pg_isready -U asr -d asr >/dev/null 2>&1; then break; fi
  sleep 2
  if [ "$i" = "30" ]; then echo "postgres not ready"; exit 1; fi
done

# D. Run DB migrations
$COMPOSE run --rm api alembic upgrade head

# E. Create MinIO bucket
$COMPOSE run --rm api python3 - <<'PY'
from libs.common.settings import get_settings
from libs.common.storage import StorageClient
StorageClient.from_settings(get_settings()).ensure_bucket(create_if_missing=True)
print("bucket ready")
PY

# F. Start app and observability services
$COMPOSE up -d api worker prometheus grafana

# G1. Wait for API /ready
for i in $(seq 1 30); do
  if curl -fsS http://localhost:8000/ready >/dev/null 2>&1; then break; fi
  sleep 2
  if [ "$i" = "30" ]; then echo "api not ready"; exit 1; fi
done

# G2. Wait for Prometheus /-/ready
for i in $(seq 1 30); do
  if curl -fsS http://localhost:9090/-/ready >/dev/null 2>&1; then break; fi
  sleep 2
  if [ "$i" = "30" ]; then echo "prometheus not ready"; exit 1; fi
done

# G3. Wait for Grafana /api/health (database == ok)
grafana_ready=0
for i in $(seq 1 30); do
  if python3 - <<'PY' >/dev/null 2>&1
import json, urllib.request, sys
data = json.loads(urllib.request.urlopen("http://localhost:3000/api/health", timeout=5).read())
sys.exit(0 if data.get("database") == "ok" else 1)
PY
  then grafana_ready=1; break; fi
  echo "Waiting for Grafana... ($i)"
  sleep 2
done
[ "$grafana_ready" = "1" ] || { echo "grafana not ready"; exit 1; }
echo "grafana health ok"

# H1. Prometheus targets retry loop (asr_api AND asr_worker both up)
targets_ready=0
for i in $(seq 1 30); do
  if python3 - <<'PY'
import json, urllib.request, sys
data = json.loads(urllib.request.urlopen("http://localhost:9090/api/v1/targets", timeout=5).read())
active = data["data"]["activeTargets"]
up_jobs = {t["labels"].get("job") for t in active if t.get("health") == "up"}
missing = {"asr_api", "asr_worker"} - up_jobs
if missing:
    print("missing up targets:", sorted(missing))
    sys.exit(1)
print("prometheus targets ok:", sorted(up_jobs))
PY
  then targets_ready=1; break; fi
  echo "Waiting for Prometheus targets... ($i)"
  sleep 2
done
[ "$targets_ready" = "1" ] || { echo "Prometheus targets did not become ready"; exit 1; }

# H2. Grafana dashboard provisioned retry loop (uid == asr-operational)
dashboard_ready=0
for i in $(seq 1 30); do
  if python3 - <<'PY'
import json, urllib.request, sys
req = urllib.request.Request("http://localhost:3000/api/search?type=dash-db",
                             headers={"Accept": "application/json"})
data = json.loads(urllib.request.urlopen(req, timeout=5).read())
uids = [d.get("uid") for d in data]
if "asr-operational" not in uids:
    print("dashboard not yet provisioned:", uids)
    sys.exit(1)
print("dashboard provisioned: asr-operational")
PY
  then dashboard_ready=1; break; fi
  echo "Waiting for Grafana dashboard provisioning... ($i)"
  sleep 2
done
[ "$dashboard_ready" = "1" ] || { echo "asr-operational dashboard not provisioned"; exit 1; }

# H3. Prometheus alert rules (all three alerts present)
python3 - <<'PY'
import json, urllib.request, sys
data = json.loads(urllib.request.urlopen("http://localhost:9090/api/v1/rules", timeout=5).read())
alert_names = set()
for g in data["data"]["groups"]:
    for r in g["rules"]:
        if r.get("type") == "alerting":
            alert_names.add(r["name"])
expected = {"ASRApiErrorRateHigh", "ASRQueueBacklogHigh", "ASRWorkerHeartbeatMissing"}
missing = expected - alert_names
assert not missing, f"missing alerts: {missing}; have: {alert_names}"
print("alerts provisioned:", sorted(expected))
PY

# H4. Worker /metrics exposes asr_queue_backlog_jobs (retry loop)
backlog_ready=0
for i in $(seq 1 30); do
  if python3 - <<'PY'
import urllib.request, re, sys
try:
    text = urllib.request.urlopen("http://localhost:9091/metrics", timeout=5).read().decode("utf-8")
except Exception as e:
    print("metrics fetch failed:", e); sys.exit(1)
m = re.search(r"^asr_queue_backlog_jobs(\{[^}]*\})?\s+([0-9eE+\-.]+)$", text, re.M)
if not m:
    print("asr_queue_backlog_jobs not yet exposed"); sys.exit(1)
print("queue backlog metric exposed, value =", m.group(2))
PY
  then backlog_ready=1; break; fi
  echo "Waiting for queue backlog metric... ($i)"
  sleep 2
done
[ "$backlog_ready" = "1" ] || { echo "asr_queue_backlog_jobs metric never exposed"; exit 1; }

# I. Docker pytest suite (non-integration, non-smoke), pipefail-safe tee
set -o pipefail
$COMPOSE run --rm api python3 -m pytest tests/ \
  --ignore=tests/integration \
  --ignore=tests/db/test_models_integration.py \
  --ignore=tests/storage/test_storage_integration.py \
  --ignore=tests/smoke \
  -v 2>&1 | tee /tmp/task64_docker_pytest.log
tail -5 /tmp/task64_docker_pytest.log

echo "TASK 6.4 WSL VERIFICATION OK"
```

After this script prints `TASK 6.4 WSL VERIFICATION OK`, report:
- the final pytest summary line from `/tmp/task64_docker_pytest.log`
- the value reported by H4 for `asr_queue_backlog_jobs` (expected `0` on idle stack)
- which alerts H3 listed as provisioned

On success, the trackers will be updated to: `tasks."6.4": done`, `last_completed_task: "6.4"`, `current_task: "7.1"`, `blocked: false`, `blocker: null`.

## Task 7.1 WSL verification commands

Task 7.1 is implemented and pushed but blocked: datamove1 has no Node, npm, or Docker. The lockfile (`services/frontend/package-lock.json`) and end-to-end browser flow can only be verified on Gabriel's WSL machine. Closure requires the lockfile to be committed.

### Files included in this commit

```text
services/frontend/.env.example
services/frontend/.eslintrc.json
services/frontend/.gitignore
services/frontend/README.md
services/frontend/app/api/[...path]/route.ts
services/frontend/app/globals.css
services/frontend/app/layout.tsx
services/frontend/app/page.tsx
services/frontend/next-env.d.ts
services/frontend/next.config.mjs
services/frontend/package.json
services/frontend/tsconfig.json
docs/claude_task_progress.md
docs/claude_task_progress.yaml
```

`services/frontend/package-lock.json` is **NOT** in this commit. It will be generated by `npm install` on WSL and committed in the closure commit. Task 7.1 stays blocked until then.

### Step 1 — WSL backend startup (deterministic)

Run from the WSL Docker checkout. The script must be run as a single block; any failure leaves Task 7.1 blocked.

```bash
cd ~/code/asr_enhancement
git pull --ff-only

docker compose -f infra/compose/docker-compose.yml down -v
docker compose -f infra/compose/docker-compose.yml build api worker
docker compose -f infra/compose/docker-compose.yml up -d postgres redis minio
docker compose -f infra/compose/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/compose/docker-compose.yml run --rm api python3 - <<'PY'
from libs.common.settings import get_settings
from libs.common.storage import StorageClient

StorageClient.from_settings(get_settings()).ensure_bucket(create_if_missing=True)
print("bucket ready")
PY
docker compose -f infra/compose/docker-compose.yml up -d api worker

ok=0
for i in $(seq 1 60); do
  if curl -fsS -o /dev/null -w "%{http_code}" http://localhost:8000/ready | grep -q '^200$'; then
    ok=1; break
  fi
  sleep 2
done
if [ "$ok" != "1" ]; then
  echo "ERROR: backend /ready did not reach 200 within 120s" >&2
  docker compose -f infra/compose/docker-compose.yml logs --tail=200 api worker postgres redis minio
  exit 1
fi
echo "backend ready"
```

### Step 2 — WSL frontend verification (deterministic)

After backend `/ready` is 200, run from `services/frontend/`:

```bash
cd ~/code/asr_enhancement/services/frontend

node_version=$(node --version | sed 's/^v//')
node_major=${node_version%%.*}
node_minor=$(echo "$node_version" | cut -d. -f2)
if [ "$node_major" -lt 18 ] || { [ "$node_major" -eq 18 ] && [ "$node_minor" -lt 18 ]; }; then
  echo "ERROR: Node $node_version < 18.18; install Node >= 18.18 and rerun." >&2
  exit 1
fi
npm --version

npm install
git status --short          # must list "?? services/frontend/package-lock.json"
test -f package-lock.json   # hard fail if missing — Task 7.1 stays blocked

npm run lint
npm run typecheck
npm run build
npm run dev                 # serves on http://localhost:3000 in this terminal
```

If any of these steps fails, stop and keep Task 7.1 blocked.

### Step 3 — Eleven manual browser checks (closure evidence)

While `npm run dev` is running and the backend is up:

1. Page loads at `http://localhost:3000` (HTTP 200, no Next error overlay).
2. Every visible string is English (header, labels, buttons, error text, button states).
3. Mode selector default value is `transcribe_only`.
4. Preset selector default value is `bypass` and the selector is disabled while mode is `transcribe_only`.
5. Switching mode to `enhance_and_transcribe` enables the preset selector.
6. Selecting `denoise` from the preset selector works and persists in the field.
7. Submitting a small WAV in `enhance_and_transcribe` mode returns a `job_id` (rendered in the queued-job line; no error region shown).
8. Switching back to `transcribe_only` resets preset to `bypass` and disables the preset selector.
9. Submitting a small WAV in `transcribe_only` mode returns a second `job_id`.
10. Run `docker compose -f infra/compose/docker-compose.yml down` (Next.js dev server must stay running). Submit again. The error region must show **the exact text**: `Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.` Any other text — including `Backend returned 500`, `Backend returned 502`, `Backend returned 503`, `Backend returned 504`, an empty error, or a Next error overlay — is a **fail** and Task 7.1 stays blocked.
11. No `/admin` route or admin text exists: `grep -ri admin services/frontend/app` returns nothing, and `curl -o /dev/null -w "%{http_code}\n" http://localhost:3000/admin` returns `404`.

Check 10 is the headline regression criterion for the route-handler proxy.

### Step 4 — Closure commit (after all checks pass)

```bash
cd ~/code/asr_enhancement
git status --short          # expect untracked services/frontend/package-lock.json
git config user.name        # "Gabriel Bibbó"
git config user.email       # must be present
git remote -v               # git@github.com:gbibbo/asr_enhancement.git or https form

git add services/frontend/package-lock.json
git add docs/claude_task_progress.md docs/claude_task_progress.yaml
git diff --cached --stat    # expect exactly 3 files

git commit -m "Close Task 7.1: Next.js frontend scaffold lockfile and tracker"
git push origin "$(git branch --show-current)"
```

Tracker closure content (after WSL pass and lockfile commit):

- `docs/claude_task_progress.yaml`: `tasks."7.1": done`, `last_completed_task: "7.1"`, `current_task: "7.2"`, `blocked: false`, `blocker: null`.
- `docs/claude_task_progress.md`: append a `done` row for 7.1 citing WSL Node version, lockfile commit hash, lint/typecheck/build results, and pass/fail for each of the eleven manual checks. Check 10 must record the literal English message verified.

Do **not** start Task 7.2 until closure has been recorded.

## Task 7.2 WSL verification commands

Run these on Gabriel's WSL Docker + Node checkout. datamove1 has no `npm` and no Docker, so the binding gates below must pass on WSL before Task 7.2 can be closed.

### Step 1 — Backend startup (terminal 1)

```bash
cd ~/code/asr_enhancement
git pull --ff-only
cd infra/compose

docker compose down -v
docker compose build api worker
docker compose up -d postgres redis minio otel-collector
docker compose run --rm api alembic upgrade head
docker compose run --rm api python - <<'PY'
from libs.common.settings import get_settings
from libs.common.storage import StorageClient
StorageClient.from_settings(get_settings()).ensure_bucket(create_if_missing=True)
print("bucket ready")
PY
docker compose up -d api worker prometheus grafana
curl -fsS http://localhost:8000/ready
```

`/ready` must return `200` with `postgres`, `redis`, and `storage` all `ok`.

### Step 2 — Frontend startup (terminal 2)

```bash
cd ~/code/asr_enhancement/services/frontend
cp -n .env.example .env.local        # leaves existing .env.local intact if present

npm install --no-audit --no-fund
npm run lint
npm run typecheck
npm run build
npm run dev   # http://localhost:3000
```

All four `npm run` commands must finish with no errors. `npm run dev` must serve `http://localhost:3000`.

### Step 3 — Generate a tiny WAV (terminal 3)

```bash
python3 - <<'PY'
import wave
from pathlib import Path
p = Path("/tmp/asr_72_test.wav")
with wave.open(str(p), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b"\x00\x00" * 1600)   # 0.1 s of silence
print(p)
PY
```

### Step 4 — Manual browser checks A–D

Open `http://localhost:3000` in a browser. Pass criteria are deterministic; do **not** require observing `queued`/`running`, mid-flight cancellation, or stopping the backend mid-flight.

#### Check A — `transcribe_only` end-to-end

Submit `/tmp/asr_72_test.wav` with mode `transcribe_only`.

- A status panel for the submitted `job_id` appears.
- Polling starts (DevTools Network shows `GET /api/v1/jobs/<id>` requests).
- Final terminal state becomes `completed` within 120 s.
- Observing `queued` or `running` is **not** required for closure; observing only `completed` is acceptable.
- Mode row shows `transcribe_only`.
- No preset row is rendered for `transcribe_only`.
- Transcript text is rendered and non-empty (canonical fake content "This is a deterministic fake transcript for local testing." is the expected value, but the binding check is "non-empty transcript").
- If `raw_audio_uri` is present in the snapshot:
  - An "Original audio: stored at <uri>" line appears.
  - The displayed URI begins with `s3://` (literal scheme check; bucket and key text are not asserted).
  - **No `<audio>` element** is rendered for the `s3://` URI (verify in DevTools "Elements" → search "audio").
- If at least one of `created_at/started_at/completed_at` is non-null:
  - The Timing block is rendered.
  - Listed ISO fields render for any timestamp present.
  - Derived durations are numeric and non-negative (may legitimately read `0.0 s`).
  - When both `total` and `processing` are present, `total >= processing`.

#### Check B — `enhance_and_transcribe` with preset `denoise`

Submit `/tmp/asr_72_test.wav` with mode `enhance_and_transcribe` and preset `denoise`.

- The UI updates to show the **new** `job_id` (the previous job's panel is replaced — confirms the polling cleanup ran when `jobId` changed; deterministic cancellation is verified separately by the `controller.abort` + `clearTimeout` greps in [page.tsx](services/frontend/app/page.tsx)).
- Polling starts.
- Final terminal state becomes `completed` within 120 s.
- Mode row shows `enhance_and_transcribe`.
- Preset row shows `denoise`.
- Transcript text is rendered and non-empty.
- If `enhanced_audio_uri` is present:
  - An "Enhanced audio: stored at <uri>" line appears.
  - The displayed URI begins with `s3://`.
  - **No `<audio>` element** is rendered.
- If `raw_audio_uri` is present, the original-audio availability line also appears with the same `s3://` / no-player rules.

#### Check C — backend-unreachable submit-path message

Run only after Check B has reached `completed` (no in-flight job):

```bash
docker compose -f infra/compose/docker-compose.yml stop api worker
```

Submit any WAV through the form again. The page must display the canonical English message verbatim:

```
Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.
```

Restart with `docker compose -f infra/compose/docker-compose.yml start api worker` afterwards. No requirement to verify polling-time unreachable behaviour from the browser — that path is verified deterministically by the grep checks plus typecheck/lint on the unified handler.

#### Check D — admin surface absent

```bash
curl -o /dev/null -w "%{http_code}\n" http://localhost:3000/admin   # expect 404
grep -ri "admin" services/frontend/app                              # expect no matches
```

If any of A–D fails, Task 7.2 stays blocked — record the failure verbatim and amend the implementation before re-running.

### Step 5 — Closure (after all checks pass)

Tracker closure content (after WSL pass):

- `docs/claude_task_progress.yaml`: `tasks."7.2": done`, `last_completed_task: "7.2"`, `current_task: "7.3"`, `blocked: false`, `blocker: null`.
- `docs/claude_task_progress.md`: append a `done` row for 7.2 citing WSL Node version, `npm run lint/typecheck/build` outcomes, and pass/fail for each of the four manual checks. Check C must record the literal English message verified.

Do **not** start Task 7.3 until closure has been recorded.

## Task 7.3 WSL verification commands

Run these from the WSL Docker checkout. The order is deterministic: backend curl checks (415 → 413 → 429) run first, then API + worker are restarted to clear the in-process limiter, `/ready` is re-polled, then the frontend manual checks run against a fresh limiter bucket.

### Step 0. Sync the WSL checkout

```bash
cd ~/code/asr_enhancement
git pull --ff-only
```

### Step 1. Deterministic backend startup

```bash
cd ~/code/asr_enhancement

docker compose -f infra/compose/docker-compose.yml down -v
docker compose -f infra/compose/docker-compose.yml build api worker
docker compose -f infra/compose/docker-compose.yml up -d postgres redis minio
docker compose -f infra/compose/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/compose/docker-compose.yml run --rm api python3 - <<'PY'
from libs.common.settings import get_settings
from libs.common.storage import StorageClient

StorageClient.from_settings(get_settings()).ensure_bucket(create_if_missing=True)
print("bucket ready")
PY
docker compose -f infra/compose/docker-compose.yml up -d api worker
```

### Step 2. /ready retry loop (must exit non-zero on timeout)

```bash
ATTEMPTS=0
MAX=30
until curl -fs http://localhost:8000/ready >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -ge "$MAX" ]; then
    echo "FAIL: /ready did not become healthy in $MAX attempts"
    exit 1
  fi
  sleep 1
done
echo "OK: /ready healthy after $ATTEMPTS attempts"
```

### Step 3. Generate a tiny valid WAV (do not assume a fixture exists)

```bash
python3 - <<'PY'
import wave
from pathlib import Path

p = Path("/tmp/asr_73_test.wav")
with wave.open(str(p), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(16000)
    w.writeframes(b"\x00\x00" * 1600)

print(p)
PY
```

### Step 4. 415 / 413 checks (RATE_LIMIT_PER_MINUTE=30 default; budget large enough for 415+413 not to consume the 429 budget — Step 5 then waits for a fresh 60 s window before the 429 check)

```bash
status=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F "file=@/etc/hostname" http://localhost:8000/v1/transcribe)
[ "$status" = "415" ] || { echo "FAIL 415: got $status"; exit 1; }
echo "OK 415"

truncate -s 200M /tmp/asr_73_big.wav
status=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F "file=@/tmp/asr_73_big.wav" http://localhost:8000/v1/transcribe)
[ "$status" = "413" ] || { echo "FAIL 413: got $status"; exit 1; }
rm -f /tmp/asr_73_big.wav
echo "OK 413"
```

### Step 5. 429 check (fresh 60 s window)

```bash
echo "Waiting 65 s for a fresh rate-limit window..."
sleep 65

codes_file=$(mktemp)
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST \
    -F "file=@/tmp/asr_73_test.wav" http://localhost:8000/v1/transcribe \
    >> "$codes_file"
done

grep -q '^202$' "$codes_file" || { echo "FAIL: no 202 observed"; cat "$codes_file"; exit 1; }
grep -q '^429$' "$codes_file" || { echo "FAIL: no 429 observed"; cat "$codes_file"; exit 1; }
echo "OK 429 status codes: 202 and 429 both observed"
rm -f "$codes_file"

attempt=0
while [ "$attempt" -lt 10 ]; do
  resp=$(curl -s -i -X POST -F "file=@/tmp/asr_73_test.wav" http://localhost:8000/v1/transcribe)
  if echo "$resp" | head -n 1 | grep -q '429'; then
    echo "$resp" | grep -i '^retry-after:' >/dev/null \
      || { echo "FAIL: 429 missing Retry-After"; echo "$resp"; exit 1; }
    body=$(echo "$resp" | awk 'BEGIN{b=0} /^\r?$/{b=1; next} b{print}')
    echo "$body" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['detail']=='Too many requests. Please try again in a moment.', d" \
      || { echo "FAIL: 429 detail mismatch"; echo "$body"; exit 1; }
    echo "OK 429 has Retry-After and exact detail"
    break
  fi
  attempt=$((attempt + 1))
  sleep 1
done
[ "$attempt" -lt 10 ] || { echo "FAIL: could not capture a 429 within 10 attempts"; exit 1; }
```

### Step 6. Confirm exclusion matrix (these endpoints must never 429)

```bash
for path in /health /ready /metrics; do
  for i in $(seq 1 50); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000${path}")
    [ "$code" != "429" ] || { echo "FAIL: $path returned 429"; exit 1; }
  done
done
echo "OK: /health, /ready, /metrics never 429"
```

### Step 7. Reset the in-process limiter before browser checks

The 429 curl loop in Step 5 has exhausted the per-IP bucket for the WSL host's address. Restart API + worker to drop the in-memory limiter state, then wait for `/ready`. **Do not skip this step** — the browser happy-path upload in Step 9 must run against a fresh limiter.

```bash
cd ~/code/asr_enhancement
docker compose -f infra/compose/docker-compose.yml restart api worker

ATTEMPTS=0
MAX=30
until curl -fs http://localhost:8000/ready >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ "$ATTEMPTS" -ge "$MAX" ]; then
    echo "FAIL: /ready did not become healthy after restart in $MAX attempts"
    exit 1
  fi
  sleep 1
done
echo "OK: /ready healthy after API/worker restart"
```

### Step 8. Frontend static checks, production build, and dev server

```bash
cd ~/code/asr_enhancement/services/frontend
npm install      # only on first run after a fresh checkout
npm run typecheck
npm run lint
npm run build
npm run dev      # http://localhost:3000
```

### Step 9. Manual browser checks at http://localhost:3000

Run in this order so the happy path runs against a fresh limiter, then the 429 case is triggered intentionally afterward:

1. **Frontend pre-flight, extension** — Upload a `.txt` file. The error region must show:
   `File type not allowed. Allowed types: .wav, .mp3, .m4a, .flac.`
   No network request must be sent (verify in DevTools → Network).

2. **Frontend pre-flight, size** — `truncate -s 200M /tmp/asr_73_big.wav`, upload it. The error region must show:
   `File is too large. Maximum allowed size is 100 MB.`
   No network request must be sent. Then `rm -f /tmp/asr_73_big.wav`.

3. **Happy path (fresh limiter)** — Upload `/tmp/asr_73_test.wav`. Submission succeeds; polling reaches `completed`; transcript is rendered.

4. **Browser 429 (intentional)** — Re-submit `/tmp/asr_73_test.wav` rapidly until the limiter trips. The error region must show exactly:
   `Too many requests. Please try again in a moment.`

5. **Backend unreachable regression** —
   ```
   docker compose -f infra/compose/docker-compose.yml stop api
   ```
   Submit again; the error region must show:
   `Cannot reach backend API. Check that the backend is running and BACKEND_API_BASE_URL is correct.`
   Restart with `docker compose -f infra/compose/docker-compose.yml start api`.

### Pass criteria on WSL

- Steps 0–8 all exit zero.
- `npm run typecheck` passes.
- `npm run lint` passes.
- `npm run build` passes.
- `npm run dev` serves the app at http://localhost:3000.
- All five Step 9 browser scenarios behave as listed in the stated order.
- Existing Task 7.2 happy path still works (Step 9.3 covers this).

### Closure (after all WSL checks pass)

- `docs/claude_task_progress.yaml`: set `tasks."7.3": done`, `last_completed_task: "7.3"`, `current_task: "8.1"`, `blocked: false`, `blocker: null`.
- `docs/claude_task_progress.md`: append a follow-up `done` row for 7.3 citing WSL Node version, `npm run typecheck/lint/build` outcomes, and pass/fail for each of the five Step 9 manual checks (Check 4 must record the literal English 429 message verified).
- Do **not** start Task 8.1 until closure has been recorded.

## Task 8.1 — Add CI baseline (blocked, awaiting external verification)

Status: **blocked** on datamove1; awaiting GitHub Actions CI verification on `master` after push, plus Gabriel's WSL Docker build and Node frontend checks.

### Files added

- `.github/workflows/ci.yml` — single workflow with three jobs (`backend`, `frontend`, `docker-image`).

### Files modified (configuration)

- `pyproject.toml` — added `[project.optional-dependencies] lint` group with exact pins `ruff==0.6.9` and `mypy==1.11.2`; added `[tool.ruff]` (`target-version = "py311"`, `line-length = 100`, `extend-exclude = ["alembic/versions", "services/frontend", ".venv", "build", "dist"]`); added `[tool.ruff.lint]` (`select = ["E", "F", "W", "I"]`, `ignore = ["E501"]`); added `[tool.mypy]` (`python_version = "3.11"`, `ignore_missing_imports = true`, `warn_unused_ignores = true`, `namespace_packages = true`, `explicit_package_bases = true`).
- `docs/claude_task_progress.yaml` — set `tasks."8.1": blocked`, `blocked: true`, blocker description.
- `docs/claude_task_progress.md` — this entry.

### Files modified (minimal source fixes for ruff and mypy)

These changes were strictly required for `ruff check .` and `mypy libs services/api services/worker` to pass under the configuration above. No behavior change.

- **`libs/common/settings.py`** (mypy): `from typing import Any, Optional` (was: `Optional`); `validate_upload_limit(cls, v: Any) -> int` and `validate_rate_limit(cls, v: Any) -> int` (was: `v: object`, which mypy could not narrow for the `int(v)` overload); `return Settings()  # type: ignore[call-arg]` in `get_settings()` (pydantic-settings reads required fields from environment at runtime; mypy without the pydantic plugin reports them as missing kwargs).
- **`libs/observability/metrics.py`** (autofix correction): re-added `CONTENT_TYPE_LATEST` to the `prometheus_client` import block with `# noqa: F401  (re-exported for libs.observability and services.api)`. Required because `libs/observability/__init__.py` and `services/api/app/main.py` import `CONTENT_TYPE_LATEST` from this module; the initial ruff autofix had removed it, breaking the re-export.
- **`libs/observability/tracing.py`** (mypy `warn_unused_ignores`): removed two obsolete `# type: ignore[attr-defined]` comments on `_t._TRACER_PROVIDER` and `_t._TRACER_PROVIDER_SET_ONCE`. Under `ignore_missing_imports = true`, the OpenTelemetry attribute access is no longer flagged, so the ignores are now reported as unused.
- **`tests/observability/test_tracing.py`** (ruff F841): removed unused `as child_span` binding in `test_propagation_links_child_span` — the variable was never read; the test logic uses `parent_span` and the exporter, not the child span.

### Files modified by `ruff check . --fix --no-unsafe-fixes`

The ruff autofixer was run with the safe-fix flag only. Two rule categories were applied automatically; both are mechanical and behavior-preserving (mypy still passes after the fixes):

- **I001** (import block sort) on: `alembic/env.py`, `libs/observability/tracing.py`, `services/api/app/main.py`, `services/worker/app/celery_app.py`, `tests/api/test_metrics_endpoint.py`, `tests/asr_adapter/test_fake_adapter.py`, `tests/audio_pipeline/test_pipeline.py`, `tests/observability/test_json_formatter.py`, `tests/observability/test_tracing.py`, `tests/worker/test_celery_app.py`, `tests/worker/test_worker_tracing.py`.
- **F401** (unused-import removal) on: `libs/asr_adapter/schema.py`, `services/api/app/main.py`, `services/worker/app/tasks.py`, `tests/api/test_enhance_and_transcribe.py`, `tests/api/test_tracing.py`, `tests/api/test_transcribe.py`, `tests/api/test_upload_validation.py`, `tests/asr_adapter/test_assemblyai_adapter.py`, `tests/observability/test_queue_backlog_metric.py`, `tests/observability/test_tracing.py`, `tests/storage/test_storage_unit.py`, `tests/worker/test_transcribe_task.py`, `tests/worker/test_worker_tracing.py`.

### `E501` line-length rule

Project-level `lint.ignore = ["E501"]` was added to `[tool.ruff.lint]`, justified per the approved plan §11.2 procedure: 37 occurrences across 10 files (`libs/asr_adapter/assemblyai.py`, `libs/audio_pipeline/presets.py`, `services/api/app/main.py`, `services/worker/app/tasks.py`, `tests/audio_pipeline/test_pipeline.py`, `tests/observability/test_tracing.py`, `tests/worker/test_enhance_task.py`, `tests/worker/test_transcribe_task.py`, `tests/worker/test_worker_metrics.py`, `tests/worker/test_worker_tracing.py`). Reformatting all 37 lines was outside Task 8.1's minimal-fix constraint; explicit ignore in `pyproject.toml` is clearer than 37 per-line `# noqa` comments. All other E-, F-, W-, and I- rules remain enforced.

### Datamove1 checks run

- `git status`, `git remote -v`, `git branch --show-current`, `git config user.name`, `git config user.email`, `git diff --stat`: clean (only `.codex` untracked, untouched); remote `git@github.com:gbibbo/asr_enhancement.git`; branch `master`; identity `Gabriel Bibbó <gabobibbo@gmail.com>`.
- `.venv/bin/python -m pip install -e ".[dev,lint]"` → installed `ruff==0.6.9` and `mypy==1.11.2` (exact pins).
- `.venv/bin/ruff check .` → `All checks passed!`.
- `.venv/bin/mypy libs services/api services/worker` → `Success: no issues found in 27 source files`.
- `.venv/bin/pytest --collect-only -q | tee /tmp/asr_81_pytest_collect.txt` → `378 tests collected`.
- `grep -F 'tests/smoke/test_cut_a_smoke.py::test_cut_a_full_flow' /tmp/asr_81_pytest_collect.txt` → present.
- `! grep -F 'tests/integration/test_live_assemblyai.py' /tmp/asr_81_pytest_collect.txt` → absent (correctly excluded by `norecursedirs`).
- Workflow YAML parses; jobs `["backend", "frontend", "docker-image"]`; backend job step list includes both `Run unit and integration tests (fake adapter)` (`pytest -q`) and `Run fake-adapter smoke test (explicit gate)` (`pytest -q tests/smoke/test_cut_a_smoke.py`).

### External verification required (Gabriel)

#### WSL local mirror (early signal)

```bash
cd ~/code/asr_enhancement
git pull

docker compose -f infra/compose/docker-compose.yml build api

cd services/frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

#### GitHub Actions (authoritative)

Open https://github.com/gbibbo/asr_enhancement/actions on the pushed `master` commit and confirm **all three** jobs are green:

- `backend` — ruff, mypy, MinIO readiness, bucket creation, `alembic upgrade head`, `pytest -q`, and the explicit `pytest -q tests/smoke/test_cut_a_smoke.py` smoke gate.
- `frontend` — `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`.
- `docker-image` — `docker buildx` of `infra/compose/Dockerfile.backend`.

### Closure (after all external verification passes)

- `docs/claude_task_progress.yaml`: set `tasks."8.1": done`, `last_completed_task: "8.1"`, `current_task: "8.2"`, `blocked: false`, `blocker: null`.
- `docs/claude_task_progress.md`: append a follow-up `done` row for 8.1 citing the GitHub Actions run URL/commit and per-job outcome.
- Do **not** start Task 8.2 until Gabriel explicitly asks.

## Task 8.1 — CI smoke worker startup fix (still blocked)

Status: still **blocked**. First GitHub Actions run on commit `34ae648` failed; a CI-only fix has been pushed and the workflow needs to be re-run.

### Failed run observation

- WSL local checks on commit `34ae648` passed:
  - `docker compose -f infra/compose/docker-compose.yml build api` — green.
  - `cd services/frontend && npm ci && npm run lint && npm run typecheck && npm run build` — green.
- GitHub Actions on commit `34ae648`:
  - `frontend` — passed.
  - `docker-image` — passed.
  - `backend` — **failed** at step `Run unit and integration tests (fake adapter)`. Specifically `tests/smoke/test_cut_a_smoke.py::test_cut_a_full_flow` timed out: the job stayed at status `queued` for the full 30-second poll window. Cause: `pytest -q` runs the in-process FastAPI app and `POST /v1/transcribe` enqueues a Celery task, but no Celery worker process was running in the CI job to consume it.

### CI fix in this commit

CI-only change to `.github/workflows/ci.yml` backend job (no application code, no test code, no other CI jobs touched):

1. **Split the smoke test from the rest of the suite.** Step `Run unit and integration tests (fake adapter)` now runs `pytest -q --ignore=tests/smoke` so the unit and adapter integration tests still execute even if the worker isn't ready yet.
2. **Start a Celery worker in the background** before the smoke gate, using the existing project entrypoint and a deterministic CI shape (no fork pool, no gossip, no mingle, no heartbeat):
   ```bash
   celery -A services.worker.app.celery_app:celery_app worker \
     --loglevel=info \
     --concurrency=1 \
     --pool=solo \
     --without-gossip \
     --without-mingle \
     --without-heartbeat \
     > /tmp/asr_celery_worker.log 2>&1 &
   echo $! > /tmp/asr_celery_worker.pid
   ```
3. **Wait for worker readiness** by polling `celery inspect ping -t 2` for up to 60 s; on failure the step prints the worker log and exits non-zero so the CI surfaces the cause without masking it.
4. **Run the smoke gate** with `pytest -q tests/smoke/test_cut_a_smoke.py` only after the worker has answered `pong`.
5. **Cleanup** — an `if: always()` step kills the recorded worker PID (best-effort, no `set -e` masking) and prints the worker log tail. This step always runs, including after step failure, so the worker log is visible in the CI output without overriding the actual failure status.

The worker inherits the same job-level env (`ASR_PROVIDER=fake`, `DATABASE_URL`, `REDIS_URL`, `MINIO_*`, `RATE_LIMIT_PER_MINUTE=0`), so it talks to the same Postgres service container, Redis service container, and the explicit MinIO container started earlier in the job. No application or adapter behavior is changed.

### Files changed in this follow-up

- `.github/workflows/ci.yml` — backend job: split smoke from `pytest -q`, start Celery worker, wait for readiness, run smoke gate, `if: always()` cleanup.
- `docs/claude_task_progress.yaml` — blocker text updated; `tasks."8.1"` remains `blocked`.
- `docs/claude_task_progress.md` — this entry.

No application code, no test code, no other workflow jobs, and no `pyproject.toml` changes in this commit.

### Datamove1 checks run for the follow-up

- `git status`, `git remote -v`, `git branch --show-current`, `git config user.name`, `git config user.email`, `git diff --stat`: clean (only `.codex` untracked, untouched); remote `git@github.com:gbibbo/asr_enhancement.git`; branch `master`; identity `Gabriel Bibbó <gabobibbo@gmail.com>`.
- `.venv/bin/ruff check .` → `All checks passed!`
- `.venv/bin/mypy libs services/api services/worker` → `Success: no issues found in 27 source files`.
- `.venv/bin/pytest --collect-only -q | tee /tmp/asr_81_pytest_collect_after_fix.txt` → 378 tests collected.
- `grep -F 'tests/smoke/test_cut_a_smoke.py::test_cut_a_full_flow' /tmp/asr_81_pytest_collect_after_fix.txt` → present.
- `! grep -F 'tests/integration/test_live_assemblyai.py' /tmp/asr_81_pytest_collect_after_fix.txt` → absent.
- Workflow YAML parses; backend job step list now includes `Run unit and integration tests (fake adapter, excluding smoke)`, `Start Celery worker in background`, `Wait for Celery worker readiness`, `Run fake-adapter smoke test (explicit gate)`, `Stop Celery worker and dump log` (`if: always()`).

### External verification still required (Gabriel)

Open https://github.com/gbibbo/asr_enhancement/actions on the new pushed `master` commit and confirm **all three** jobs are green:

- `backend` — ruff, mypy, MinIO readiness, bucket creation, `alembic upgrade head`, `pytest -q --ignore=tests/smoke`, Celery worker startup + readiness, the explicit `pytest -q tests/smoke/test_cut_a_smoke.py` smoke gate, and the `if: always()` cleanup.
- `frontend` — `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`.
- `docker-image` — `docker buildx` of `infra/compose/Dockerfile.backend`.

Task 8.1 stays `blocked` and Task 8.2 stays unstarted until that re-run is green.

## Task 8.1 — done

Status: **done**.

External verification on commit `df5548788511760e4633ed528a1e9ba5e73aa21b` passed on GitHub Actions:

- `backend` — passed, including the new CI-only Celery worker startup/readiness/smoke gate (`Start Celery worker in background`, `Wait for Celery worker readiness`, `Run fake-adapter smoke test (explicit gate)`, and the `if: always()` `Stop Celery worker and dump log` cleanup).
- `frontend` — passed (`npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`).
- `docker-image` — passed (`docker buildx` build of `infra/compose/Dockerfile.backend`).

WSL Docker/Node mirror checks had already passed on the previous Task 8.1 implementation commit (`34ae648`) and were not repeated, because the follow-up commit `df55487` changed only `.github/workflows/ci.yml` and the trackers — no application, test, or Docker/Compose code was touched.

Tracker state on closure:

- `tasks."8.1"`: `done`
- `last_completed_task`: `"8.1"`
- `current_task`: `"8.2"`
- `blocked`: `false`
- `blocker`: `null`

Task 8.1 is closed. Task 8.2 is the next task per `plan.md` §14 (Add smoke test documentation). Task 8.2 has **not** been started.

## Task 8.2 — in progress (blocked on external WSL/Docker walk-through)

Status: **in_progress / blocked**.

Scope per `plan.md` §14 (Phase 8, Task 8.2):

> Actions: document how to start the stack; document how to run Cut A smoke test; document how to run enhancement flow; document how to run AssemblyAI live smoke test; document how to inspect logs and result endpoints.
> Done when: setup can be followed from a clean checkout; fake path works without secrets; real provider path has explicit environment gating.

### Files changed in this commit

- `docs/smoke_tests.md` — new English smoke-test guide covering all five plan.md actions: Overview, Prerequisites, Where artifacts go, Start the stack, One-time stack setup (Alembic + MinIO bucket), Wait for readiness, Cut A smoke test, Enhance-and-transcribe flow, AssemblyAI live smoke test (gated by `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY`, opt-in, never required for closure), Inspect logs, Inspect job state via API, Stop the stack, CI parity reference.
- `docs/claude_task_progress.yaml` — `tasks."8.2": blocked`, `blocked: true`, `blocker` describes the external WSL/Docker walk-through still required.
- `docs/claude_task_progress.md` — this entry.

No application code, no test code, no Compose, no CI workflow, and no project-config changes in this commit. README, plan.md, and CLAUDE.md were not touched. `.codex` remains untracked and unstaged.

### Decisions encoded in the doc

- Pip extras are quoted in every command: `python3 -m pip install -e ".[dev]"`.
- The Cut A smoke runs **inside a one-shot `api` container** (`docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api pytest -q tests/smoke/test_cut_a_smoke.py`) because `tests/smoke/test_cut_a_smoke.py` uses `ASGITransport(app=app)` in-process and Postgres / Redis are intentionally compose-internal.
- One-time setup commands are explicit: `alembic upgrade head` and a deterministic MinIO bucket-create snippet using the `minio` Python client, both via `docker compose ... run --rm --no-deps api …`. Without these, `/ready` returns 503 (`/ready` calls `sc.ensure_bucket(create_if_missing=False)`).
- API readiness wait: `until curl -fsS http://localhost:8000/ready >/dev/null; do sleep 2; done`.
- Worker readiness wait: `celery -A services.worker.app.celery_app:celery_app inspect ping -t 2`, mirroring CI.
- Live AssemblyAI test is opt-in and requires **both** `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY=<your-key>`. CI does not set the gate. The doc never prints a real key value.

### Datamove1 checks run for Task 8.2

Run with `set -euo pipefail` from `/mnt/fast/nobackup/users/gb0048/asr_enhancement_platform`:

- `test -s docs/smoke_tests.md`.
- All required commands present in `docs/smoke_tests.md`: `docker compose -f infra/compose/docker-compose.yml up -d --build`, `... run --rm --no-deps api alembic upgrade head`, `... run --rm --no-deps api python -c`, `pytest -q tests/smoke/test_cut_a_smoke.py`, `pytest -v tests/api/test_enhance_and_transcribe.py`, `tests/integration/test_live_assemblyai.py`, `RUN_LIVE_ASSEMBLYAI_TEST=1`, `ASSEMBLYAI_API_KEY`, `celery -A services.worker.app.celery_app:celery_app inspect ping`, `curl -fsS http://localhost:8000/ready`, `/v1/jobs/`, `/health`, `... logs`, `... down`.
- Artifact-location guidance present (`raw_audio/{job_id}/input`, `transcripts/{job_id}/transcript.json`).
- No unquoted `pip install -e .[dev]` form anywhere; quoted form `python3 -m pip install -e ".[dev]"` present.
- No real `ASSEMBLYAI_API_KEY` value (only the placeholder `<your-key>`).
- Even number of fenced code blocks (balanced).
- No AI-authorship trailers in any new or edited file (case-insensitive grep against the standard list of forbidden markers returned no matches).
- `docs/claude_task_progress.yaml` parsed and verified: `tasks."8.1": done`, `tasks."8.2": blocked`, `current_task: "8.2"`, `last_completed_task: "8.1"`, `blocked: true`, `blocker` non-empty.
- `docs/claude_task_progress.md` includes a `Task 8.2` heading.
- `git status` + diff scope check: only the three planned paths are changed (`docs/smoke_tests.md`, `docs/claude_task_progress.md`, `docs/claude_task_progress.yaml`); `.codex` remains untracked and unstaged.

### External verification still required (Gabriel, on WSL/Docker)

The plan.md done-criterion *"setup can be followed from a clean checkout"* can only be proved by walking the doc on a host that has Docker. Datamove1 has no Docker. Gabriel runs the following commands from a clean WSL checkout of `master` after this commit lands:

```bash
git fetch origin && git checkout master && git pull
cp .env.example .env

docker compose -f infra/compose/docker-compose.yml up -d --build

# one-time setup
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api alembic upgrade head
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

# wait for readiness
until curl -fsS http://localhost:8000/ready >/dev/null; do sleep 2; done
until docker compose -f infra/compose/docker-compose.yml exec -T worker \
        celery -A services.worker.app.celery_app:celery_app inspect ping -t 2 >/dev/null 2>&1; do
  sleep 2
done

# fake-path verification (must both exit 0)
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -q tests/smoke/test_cut_a_smoke.py
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -v tests/api/test_enhance_and_transcribe.py

# spot-check logs (just to confirm doc command works)
docker compose -f infra/compose/docker-compose.yml logs api    | head -n 20
docker compose -f infra/compose/docker-compose.yml logs worker | head -n 20

# tear down
docker compose -f infra/compose/docker-compose.yml down
```

Pass criteria:

- the smoke test (`tests/smoke/test_cut_a_smoke.py`) exits 0 and pytest reports a passing test run.
- the enhance-and-transcribe suite (`tests/api/test_enhance_and_transcribe.py`) exits 0 and pytest reports a passing test run.
- the documented commands match exactly what was run (no improvisation).

The live AssemblyAI test is **not required** to close Task 8.2 — it is opt-in and costs money. Gabriel runs it only if he wants to sanity-check provider gating.

Task 8.2 is **not closed yet**. Tracker state on this commit:

- `tasks."8.2"`: `blocked`
- `current_task`: `"8.2"`
- `last_completed_task`: `"8.1"`
- `blocked`: `true`
- `blocker`: `"Awaiting WSL/Docker walk-through of docs/smoke_tests.md (compose up + alembic + bucket-create + pytest tests/smoke + pytest tests/api/test_enhance_and_transcribe.py)."`

Task 8.3 has **not** been started.

## Task 8.2 — done

Status: **done**.

External WSL/Docker walk-through passed on commit `bb77a1a43aee5ff96e382ee03765e625993f71ca`. Gabriel ran the documented commands from `docs/smoke_tests.md` against a clean WSL checkout of `master` and reported:

- `docker compose -f infra/compose/docker-compose.yml up -d --build` completed successfully.
- `docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api alembic upgrade head` completed successfully.
- MinIO bucket creation snippet completed successfully and printed `bucket ready: asr-platform`.
- `docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api pytest -q tests/smoke/test_cut_a_smoke.py` exited 0 and reported `1 passed`.
- `docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api pytest -v tests/api/test_enhance_and_transcribe.py` exited 0 and reported `13 passed`.
- `docker compose -f infra/compose/docker-compose.yml logs api` and `... logs worker` produced readable output.
- `docker compose -f infra/compose/docker-compose.yml down` completed successfully.

The live AssemblyAI test was not run, by design — it is opt-in and not required for Task 8.2 closure.

The plan.md done-criteria for Task 8.2 are satisfied:

- *setup can be followed from a clean checkout* — confirmed end-to-end on WSL.
- *fake path works without secrets* — Cut A smoke and Cut B enhance-and-transcribe suites both passed with `ASR_PROVIDER=fake`.
- *real provider path has explicit environment gating* — documented as gated by both `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY=<your-key>`; CI does not set the gate; no real key value appears in any committed file.

Tracker state on closure:

- `tasks."8.2"`: `done`
- `last_completed_task`: `"8.2"`
- `current_task`: `"8.3"`
- `blocked`: `false`
- `blocker`: `null`

Task 8.2 is closed. Task 8.3 (Add deployment path documentation, `plan.md` §14 Phase 8) is next per `plan.md`. Task 8.3 has **not** been started.

## Task 8.3 — implemented (blocked)

Status: **blocked**, awaiting external WSL/Docker walk-through.

### Scope summary

Per `plan.md` §14 Phase 8 Task 8.3 ("Add deployment path documentation"), this task adds a single new file, `docs/deployment.md`, that documents the single-VPS Docker Compose deployment path: clone + `.env`, `docker compose up`, one-time Alembic migration and MinIO bucket-create, readiness waits for `/ready` and Celery, post-deploy smoke against the fake provider, and tear-down.

The doc is backend-only by design. The Next.js frontend at `services/frontend/` is **not yet integrated** into `infra/compose/docker-compose.yml`; its README defers Compose integration to a later demo task. The deployment guide records this gap in a `## Known limitations` section. The guide does not add host-side `npm` production-run instructions, does not add a frontend Compose service, and does not add reverse-proxy frontend routing.

The reverse-proxy section documents Caddy as **operator-managed on the VPS host, outside the Compose stack**. The Caddyfile snippet uses `reverse_proxy 127.0.0.1:8000` (the host-published API port). The doc explicitly does not claim Caddy is on the Compose network and does not use the compose-internal hostname `api`.

Object storage covers two variants: local MinIO on the VPS (with a backup warning for `asr_minio_data`) and managed S3-compatible storage (overriding `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`). All secrets appear only as placeholders (`<minio-access-key>`, `<minio-secret-key>`, `<assemblyai-api-key>`); no real key values are printed.

### Files changed in this commit

Only the three allowlisted files:

- `docs/deployment.md` — new file, backend VPS deployment runbook.
- `docs/claude_task_progress.md` — this section, appended.
- `docs/claude_task_progress.yaml` — tracker flipped to `tasks."8.3": blocked`, `blocked: true`, with a `blocker` describing the missing external verification.

`.codex` remains untracked and unstaged. No other path is modified.

### Datamove1 checks run for Task 8.3

Run with `set -euo pipefail` from `/mnt/fast/nobackup/users/gb0048/asr_enhancement_platform`:

- `test -s docs/deployment.md`.
- All required headings present in `docs/deployment.md`: `# Deployment guide`, `## Single VPS with Docker Compose`, `## Required environment variables`, `## Secrets handling`, `## Reverse proxy`, `## Post-deploy smoke test`, `## Object storage and backups`, `## Known limitations`.
- All required commands present: `docker compose -f infra/compose/docker-compose.yml up -d --build`, `... run --rm --no-deps api alembic upgrade head`, `... run --rm --no-deps api python -c`, `pytest -q tests/smoke/test_cut_a_smoke.py`, `pytest -v tests/api/test_enhance_and_transcribe.py`, `celery -A services.worker.app.celery_app:celery_app inspect ping`, `curl -fsS http://localhost:8000/ready`, `docker compose -f infra/compose/docker-compose.yml down`.
- All required env-var names present: `ASR_PROVIDER`, `DATABASE_URL`, `REDIS_URL`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`, `ASSEMBLYAI_API_KEY`, `UPLOAD_LIMIT_BYTES`, `RATE_LIMIT_PER_MINUTE`.
- Decision-rule coverage strings present: `server IP`, `Caddy`, `127.0.0.1:8000`, `backup`, `S3-compatible`.
- Caddy/Compose consistency: no `reverse_proxy api:8000`, no phrasing claiming Caddy is on the Compose network or inside Compose.
- No real-looking secret values: no `ASSEMBLYAI_API_KEY=[A-Za-z0-9]{16,}`; only placeholder or `minioadmin` values appear after `MINIO_SECRET_KEY=`.
- Narrow no-AI-authorship grep across the three changed files: zero matches against the standard provenance-marker regex defined in the approved Task 8.3 plan (covers assistant co-author trailers, generation-provenance phrases, and vendor product names; bare common words excluded to avoid false positives).
- Even, non-zero count of fenced code blocks in `docs/deployment.md`.
- `docs/claude_task_progress.yaml` parsed and verified: `current_phase: 8`, `current_task: "8.3"`, `last_completed_task: "8.2"`, `tasks."8.3": blocked`, `blocked: true`, `blocker` non-empty.
- `docs/claude_task_progress.md` includes the heading `## Task 8.3 — implemented (blocked)`.
- Exact changed-file allowlist: tracked + staged + untracked-non-`.codex` set equals exactly `docs/claude_task_progress.md`, `docs/claude_task_progress.yaml`, `docs/deployment.md`.
- `.codex` remains untracked and is not staged.

### External verification still required (Gabriel, on WSL/Docker)

The `plan.md` done-criteria *"demo deployment path is reproducible"* and *"smoke test passes after deploy"* require a host with Docker. Datamove1 has no Docker. Gabriel runs the following commands from a clean WSL checkout. The walk-through uses a fresh, isolated directory (`~/tmp/asr_83_deployment_walkthrough`) so unrelated edits in any other working copy cannot influence the result, and starts with a destructive `down -v` preflight to drop any old volumes from previous walkthroughs.

```bash
mkdir -p ~/tmp
rm -rf ~/tmp/asr_83_deployment_walkthrough
cd ~/tmp
git clone https://github.com/gbibbo/asr_enhancement.git asr_83_deployment_walkthrough
cd asr_83_deployment_walkthrough
git checkout master
git pull

# DESTRUCTIVE preflight — drop any old volumes from previous walkthroughs.
# This is for the verification walkthrough only. Do NOT run on a real
# deployment you want to preserve.
docker compose -f infra/compose/docker-compose.yml down -v

cp .env.example .env

docker compose -f infra/compose/docker-compose.yml up -d --build

docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api alembic upgrade head
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

until curl -fsS http://localhost:8000/ready >/dev/null; do sleep 2; done
until docker compose -f infra/compose/docker-compose.yml exec -T worker \
        celery -A services.worker.app.celery_app:celery_app inspect ping -t 2 >/dev/null 2>&1; do
  sleep 2
done

docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -q tests/smoke/test_cut_a_smoke.py
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps api \
  pytest -v tests/api/test_enhance_and_transcribe.py

docker compose -f infra/compose/docker-compose.yml logs api    | head -n 20
docker compose -f infra/compose/docker-compose.yml logs worker | head -n 20

# DESTRUCTIVE tear-down for the verification walkthrough only.
docker compose -f infra/compose/docker-compose.yml down -v
```

### Pass criteria for the WSL walk-through

- `pytest -q tests/smoke/test_cut_a_smoke.py` exits 0 and pytest reports a passing test run.
- `pytest -v tests/api/test_enhance_and_transcribe.py` exits 0 and pytest reports a passing test run.
- The documented commands match exactly what was run (no improvisation, no env-var fix-ups outside `.env`).
- No real `ASSEMBLYAI_API_KEY` was used or printed; the live AssemblyAI test is **not required** to close Task 8.3.

### Tracker state on this commit

- `tasks."8.3"`: `blocked`
- `current_task`: `"8.3"`
- `last_completed_task`: `"8.2"`
- `blocked`: `true`
- `blocker`: `"Awaiting external WSL/Docker walk-through of docs/deployment.md (compose up + alembic + bucket-create + readiness wait + post-deploy smoke pytest)."`

Task 8.3 is **not closed yet**. No later task has been started.
