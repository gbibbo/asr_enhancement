from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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


def _insert_job(db_path: Path, status: str) -> str:
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider) VALUES (?, ?, ?, ?, ?)",
        (job_id, status, now, now, "whisper"),
    )
    conn.commit()
    conn.close()
    return job_id


@pytest.fixture()
def client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from services.api.app.demo_main import app
    with TestClient(app) as test_client:
        yield test_client


def _db_path(client: TestClient) -> Path:
    return client.app.state.settings.demo_db_path


def _queue_max(client: TestClient) -> int:
    return client.app.state.settings.demo_queue_max


# --- health ---

def test_health_returns_ok(client):
    resp = client.get("/demo/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "mode": "demo"}


# --- POST /demo/jobs ---

def test_create_job_returns_202(client):
    resp = client.post("/demo/jobs")
    assert resp.status_code == 202
    body = resp.json()
    assert "job_id" in body
    assert body["status"] == "queued"


def test_create_job_persists_in_db(client):
    from libs.demo.persistence import get_job
    resp = client.post("/demo/jobs")
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    row = get_job(_db_path(client), job_id)
    assert row is not None
    assert row["status"] == "queued"


def test_create_job_returns_503_when_queue_full(client):
    db = _db_path(client)
    qmax = _queue_max(client)
    for _ in range(qmax):
        _insert_job(db, "queued")
    resp = client.post("/demo/jobs")
    assert resp.status_code == 503
    assert "Queue full" in resp.json()["detail"]


def test_completed_jobs_do_not_trigger_503(client):
    db = _db_path(client)
    qmax = _queue_max(client)
    for _ in range(qmax):
        _insert_job(db, "completed")
    resp = client.post("/demo/jobs")
    assert resp.status_code == 202


def test_failed_jobs_do_not_trigger_503(client):
    db = _db_path(client)
    qmax = _queue_max(client)
    for _ in range(qmax):
        _insert_job(db, "failed")
    resp = client.post("/demo/jobs")
    assert resp.status_code == 202


# --- isolation check ---

def test_demo_main_does_not_import_platform_settings():
    src = Path("services/api/app/demo_main.py").read_text()
    assert "from libs.common.settings" not in src
    assert "libs.common.settings.Settings" not in src
