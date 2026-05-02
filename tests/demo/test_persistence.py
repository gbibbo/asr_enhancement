from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT",
    "DEMO_DB_PATH",
    "DEMO_UPLOAD_DIR",
    "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR",
    "DEMO_LOGS_DIR",
    "DEMO_WORKER_CONCURRENCY",
    "DEMO_QUEUE_MAX",
    "DEMO_UPLOAD_LIMIT_BYTES",
    "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "ASSEMBLYAI_API_KEY",
    "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD",
]


@pytest.fixture()
def settings(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from libs.common.demo_settings import DemoSettings
    return DemoSettings()


@pytest.fixture()
def db_path(settings):
    from libs.demo.persistence import ensure_runtime_dirs, init_schema
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    return settings.demo_db_path


def _insert_job(db_path: Path, status: str, provider: str = "whisper") -> str:
    from datetime import datetime, timezone
    import uuid
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider) VALUES (?, ?, ?, ?, ?)",
        (job_id, status, now, now, provider),
    )
    conn.commit()
    conn.close()
    return job_id


# --- schema ---

def test_init_schema_creates_all_tables(db_path):
    conn = sqlite3.connect(str(db_path))
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"jobs", "cache_entries", "usage_ledger", "admin_state"} <= tables


def test_init_schema_is_idempotent(settings):
    from libs.demo.persistence import ensure_runtime_dirs, init_schema
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    init_schema(settings.demo_db_path)  # second call must not raise


# --- try_create_job ---

def test_try_create_job_returns_string_uuid(db_path, settings):
    from libs.demo.persistence import try_create_job
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    assert isinstance(job_id, str) and len(job_id) > 0


def test_try_create_job_inserts_queued_row(db_path, settings):
    from libs.demo.persistence import get_job, try_create_job
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    row = get_job(db_path, job_id)
    assert row is not None
    assert row["status"] == "queued"
    assert row["provider"] == "whisper"


def test_try_create_job_raises_queue_full_at_max(db_path, settings):
    from libs.demo.persistence import QueueFullError, try_create_job
    for _ in range(settings.demo_queue_max):
        _insert_job(db_path, "queued")
    with pytest.raises(QueueFullError):
        try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")


def test_try_create_job_allows_job_when_below_max(db_path, settings):
    from libs.demo.persistence import try_create_job
    for _ in range(settings.demo_queue_max - 1):
        _insert_job(db_path, "queued")
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    assert isinstance(job_id, str)


def test_try_create_job_completed_jobs_do_not_count(db_path, settings):
    from libs.demo.persistence import try_create_job
    for _ in range(settings.demo_queue_max):
        _insert_job(db_path, "completed")
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    assert isinstance(job_id, str)


def test_try_create_job_failed_jobs_do_not_count(db_path, settings):
    from libs.demo.persistence import try_create_job
    for _ in range(settings.demo_queue_max):
        _insert_job(db_path, "failed")
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    assert isinstance(job_id, str)


# --- get_job ---

def test_get_job_returns_none_for_missing_id(db_path):
    from libs.demo.persistence import get_job
    assert get_job(db_path, "00000000-0000-0000-0000-000000000000") is None


# --- count_active_jobs ---

def test_count_active_jobs_counts_queued(db_path):
    from libs.demo.persistence import count_active_jobs
    _insert_job(db_path, "queued")
    assert count_active_jobs(db_path) == 1


def test_count_active_jobs_counts_running(db_path):
    from libs.demo.persistence import count_active_jobs
    _insert_job(db_path, "running")
    assert count_active_jobs(db_path) == 1


def test_count_active_jobs_excludes_completed(db_path):
    from libs.demo.persistence import count_active_jobs
    _insert_job(db_path, "completed")
    assert count_active_jobs(db_path) == 0


def test_count_active_jobs_excludes_failed(db_path):
    from libs.demo.persistence import count_active_jobs
    _insert_job(db_path, "failed")
    assert count_active_jobs(db_path) == 0


# --- update_job_status ---

def test_update_job_status_to_failed(db_path, settings):
    from libs.demo.persistence import get_job, try_create_job, update_job_status
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    update_job_status(db_path, job_id, "failed")
    assert get_job(db_path, job_id)["status"] == "failed"


def test_update_job_status_sets_error_message(db_path, settings):
    from libs.demo.persistence import get_job, try_create_job, update_job_status
    job_id = try_create_job(db_path, queue_max=settings.demo_queue_max, provider="whisper")
    update_job_status(db_path, job_id, "failed", error_message="oops")
    assert get_job(db_path, job_id)["error_message"] == "oops"


# --- claim_next_job ---

def test_claim_next_job_returns_oldest_first(db_path):
    from libs.demo.persistence import claim_next_job
    first = _insert_job(db_path, "queued")
    _insert_job(db_path, "queued")
    claimed = claim_next_job(db_path)
    assert claimed is not None
    assert claimed["job_id"] == first


def test_claim_next_job_transitions_to_running(db_path):
    from libs.demo.persistence import claim_next_job, get_job
    _insert_job(db_path, "queued")
    claimed = claim_next_job(db_path)
    assert claimed["status"] == "running"
    assert get_job(db_path, claimed["job_id"])["status"] == "running"


def test_claim_next_job_returns_none_when_empty(db_path):
    from libs.demo.persistence import claim_next_job
    assert claim_next_job(db_path) is None


# --- ensure_runtime_dirs ---

def test_ensure_runtime_dirs_creates_exactly_five_directories(settings, tmp_path):
    from libs.demo.persistence import ensure_runtime_dirs
    ensure_runtime_dirs(settings)
    assert settings.demo_db_path.parent.is_dir()
    assert settings.demo_upload_dir.is_dir()
    assert settings.demo_cache_dir.is_dir()
    assert settings.demo_artifacts_dir.is_dir()
    assert settings.demo_logs_dir.is_dir()


# --- isolation checks ---

def test_persistence_does_not_import_sqlalchemy():
    src = Path("libs/demo/persistence.py").read_text()
    assert "from sqlalchemy" not in src
    assert "import sqlalchemy" not in src


def test_persistence_does_not_import_platform_db():
    src = Path("libs/demo/persistence.py").read_text()
    assert "from libs.common.db" not in src
