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
