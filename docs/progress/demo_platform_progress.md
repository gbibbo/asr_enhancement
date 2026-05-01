# Demo and Platform Task Progress

Branch: feature/demo-runtime-rp5-v1
Integration branch: demo-rp5-v1
Parallel training branch: feature/training-datamove1-v1
Current track: Refactor
Current phase: Phase R1
Current task: Task R2.1

## Completed

- S0.1: inspected repository state and preserved MVP tag.
- S0.2: created integration and demo feature branches.
- S0.3: added split plan files and root plan router.
- S0.4: created demo/platform trackers.
- S0.5: confirmed all four split branches on origin (master, demo-rp5-v1, feature/demo-runtime-rp5-v1, feature/training-datamove1-v1) and verified RP5 host, Docker 26.1.5, and Compose 2.26.1 on asr-rp5.
- R0.1: verified platform mode locally on 2026-05-01 from feature/demo-runtime-rp5-v1 (tip 7f0d98a). Built and brought up infra/compose/docker-compose.yml; all 8 services running, postgres/redis/minio healthy, api and worker started cleanly. Pytest inside the api container: general suite (tests excluding tests/smoke and tests/integration) 377 passed / 0 failed / 0 skipped; smoke suite 1 passed. Host-side checks: GET /health 200, GET /metrics 200, POST /v1/transcribe round-trip returned the deterministic fake transcript. Classification P (all green). Stack torn down with docker compose down (volumes preserved).
- R0.2: added migration status note to README.md ## Status section on 2026-05-01. Note references platform-mvp-v0 tag (verified present) and demo-rp5-v1 branch (verified present). No live demo URL added.
- R1.1: created libs/asr/ package (7 files: __init__.py, schema.py, errors.py, base.py, fake_provider.py, assemblyai_provider.py, factory.py) and tests/asr/test_asr_package_imports.py on 2026-05-01. Import smoke inside api container: OK. tests/asr/ 5 passed. tests/asr_adapter/ 51 passed (old package untouched). Full non-smoke/non-integration suite 382 passed / 0 failed. Safety diffs confirmed libs/asr_adapter/, tasks.py, main.py, and pyproject.toml unchanged. Stack torn down with docker compose down (volumes preserved).
- R1.2: updated imports and tests for ASR package on 2026-05-01. services/worker/app/tasks.py line 15 updated from libs.asr_adapter.factory to libs.asr.factory. 5 worker test files updated to libs.asr.errors / libs.asr.schema. tests/integration/test_live_assemblyai.py updated to libs.asr.assemblyai_provider / libs.asr.schema (gate still skips in CI). 3 new behavioral test files created: tests/asr/test_fake_provider.py (17 tests), tests/asr/test_assemblyai_provider.py (31 tests), tests/asr/test_asr_factory.py (3 tests). Safety diffs: libs/asr_adapter/, services/api/, pyproject.toml, infra/, .github/workflows/ all empty (no unintended changes). tests/asr/ 56 passed. tests/asr_adapter/ 51 passed (old package untouched). tests/worker/ 52 passed. Integration gate: 1 skipped / 0 failed. Full non-smoke/non-integration suite 433 passed / 0 failed (382 baseline + 51 new). Smoke suite 1 passed. Endpoint round-trip: /v1/transcribe returned deterministic fake transcript. Final import search: no libs.asr_adapter outside libs/asr_adapter/ and tests/asr_adapter/. Stack torn down with docker compose down (volumes preserved).
- R1.3: removed legacy libs/asr_adapter/ (7 files) and tests/asr_adapter/ (4 files) on 2026-05-01. Pre-deletion and post-deletion host-side Select-String confirmed zero active imports of libs.asr_adapter in services/, tests/, libs/. Removed 3 completed ASR mapping rows from CLAUDE.md §9 and docs/profiles/CLAUDE.demo.md §9; audio pipeline rows (libs/audio_pipeline/) retained for R2.x. pytest inside api container: tests/asr/ 56 passed, tests/worker/ 52 passed, full suite 382 passed / 0 failed (433 − 51 deleted), smoke 1 passed. GET /health: {"status": "ok"}. /v1/transcribe round-trip: deterministic fake transcript confirmed. Stack torn down with docker compose down (volumes preserved).

## Current blocker

None.

## Training handoff status

Training branch feature/training-datamove1-v1 already exists on origin from demo-rp5-v1. Split workflow active.

## Next task

Task R2.1. Create audio package and migrate enhancement code.
