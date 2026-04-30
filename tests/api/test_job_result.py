from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.models import JobMode, JobStatus
from libs.common.settings import get_settings
from services.api.app.main import JobStatusSnapshot, app

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}

FAKE_JOB_ID = uuid.UUID("aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb")
_CREATED_AT = datetime(2026, 4, 30, 10, 0, 0, tzinfo=timezone.utc)
_COMPLETED_AT = datetime(2026, 4, 30, 10, 0, 5, tzinfo=timezone.utc)


def _make_snapshot(**overrides) -> JobStatusSnapshot:
    defaults: dict = dict(
        id=FAKE_JOB_ID,
        status=JobStatus.completed,
        mode=JobMode.transcribe_only,
        provider="fake",
        preset="bypass",
        raw_audio_uri="s3://asr-platform/raw_audio/aaaabbbb-.../input.wav",
        enhanced_audio_uri=None,
        transcript_uri="s3://asr-platform/transcripts/aaaabbbb-.../result.json",
        transcript_text="This is a deterministic fake transcript for local testing.",
        error_message=None,
        created_at=_CREATED_AT,
        updated_at=_COMPLETED_AT,
        started_at=_CREATED_AT,
        completed_at=_COMPLETED_AT,
    )
    defaults.update(overrides)
    return JobStatusSnapshot(**defaults)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def job_result_client(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# 200 — completed job
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_200_completed(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_result_response_fields(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    data = response.json()

    assert uuid.UUID(data["job_id"]) == FAKE_JOB_ID
    assert data["status"] == "completed"
    assert data["transcript_text"] == "This is a deterministic fake transcript for local testing."
    assert data["transcript_uri"] is not None
    assert data["completed_at"] is not None
    assert "provider_payload_uri" not in data


# ---------------------------------------------------------------------------
# 404 — job not found
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_404_not_found(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: None,
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 404
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# 422 — malformed UUID (FastAPI path validation; no monkeypatching needed)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_422_malformed_uuid(job_result_client):
    response = await job_result_client.get("/v1/jobs/not-a-uuid/result")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 202 — queued and running
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_202_queued(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(status=JobStatus.queued),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 202
    assert "detail" in response.json()


@pytest.mark.anyio
async def test_get_result_202_running(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(status=JobStatus.running),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 202
    assert "detail" in response.json()


# ---------------------------------------------------------------------------
# 200 — failed job (result is the failure report)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_200_failed(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(
            status=JobStatus.failed,
            error_message="ASR failed",
        ),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_message"] == "ASR failed"


# ---------------------------------------------------------------------------
# 500 — completed job missing required transcript data
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_500_missing_transcript_text(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(transcript_text=None),
    )
    calls: list = []
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, jid, msg: calls.append((jid, msg)),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 500
    assert len(calls) == 1
    assert calls[0][0] == FAKE_JOB_ID


@pytest.mark.anyio
async def test_get_result_500_missing_transcript_uri(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(transcript_uri=None),
    )
    calls: list = []
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, jid, msg: calls.append((jid, msg)),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 500
    assert len(calls) == 1
    assert calls[0][0] == FAKE_JOB_ID


# ---------------------------------------------------------------------------
# Regression: PostgreSQL may return plain strings for enum columns, not Enum
# instances. Ensure the endpoint does not crash and returns the string as-is.
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_result_status_as_plain_string(monkeypatch, job_result_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(status="completed"),
    )
    response = await job_result_client.get(f"/v1/jobs/{FAKE_JOB_ID}/result")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
