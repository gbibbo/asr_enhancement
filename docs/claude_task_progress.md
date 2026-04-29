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
| 2.1  | blocked | 2026-04-29 | Implementation complete. Files created: libs/common/db.py, libs/common/models.py (JobStatus, JobMode, Job — all 15 fields with correct SQL types), alembic.ini, alembic/env.py, alembic/script.py.mako, alembic/versions/496c2c194ab1_create_jobs_table.py, tests/db/__init__.py, tests/db/test_models_unit.py, tests/db/test_models_integration.py. Verified on login node: unit tests 4/4 passed; existing 27 tests still pass; offline alembic upgrade/downgrade SQL correct. External Docker verification attempted and failed: (1) pytest not found — Dockerfile only installed runtime deps; (2) alembic upgrade head failed — alembic.ini and alembic/ not in image. Fix applied: infra/compose/Dockerfile.backend now COPYs alembic.ini, alembic/, tests/ and runs pip install .[dev]. Image must be rebuilt (docker compose build api). Awaiting rerun of full verification sequence. Do not mark done until all commands pass and outputs are reported. |
