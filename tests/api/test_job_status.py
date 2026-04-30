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

FAKE_JOB_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
_CREATED_AT = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_UPDATED_AT = datetime(2026, 1, 1, 12, 0, 5, tzinfo=timezone.utc)


def _make_snapshot(**overrides) -> JobStatusSnapshot:
    defaults: dict = dict(
        id=FAKE_JOB_ID,
        status=JobStatus.queued,
        mode=JobMode.transcribe_only,
        provider="fake",
        preset="bypass",
        raw_audio_uri=None,
        enhanced_audio_uri=None,
        transcript_uri=None,
        transcript_text=None,
        error_message=None,
        created_at=_CREATED_AT,
        updated_at=_UPDATED_AT,
        started_at=None,
        completed_at=None,
    )
    defaults.update(overrides)
    return JobStatusSnapshot(**defaults)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def job_status_client(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# 200 — job found
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_job_200_found(monkeypatch, job_status_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(),
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_job_response_fields(monkeypatch, job_status_client):
    snap = _make_snapshot(
        raw_audio_uri="s3://asr-platform/raw_audio/12345678-.../input.wav",
    )
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: snap,
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    data = response.json()

    assert uuid.UUID(data["job_id"]) == FAKE_JOB_ID
    assert isinstance(data["status"], str)
    assert isinstance(data["mode"], str)
    assert data["provider"] == "fake"
    assert data["preset"] == "bypass"
    assert data["raw_audio_uri"] is not None
    assert data["transcript_uri"] is None
    assert data["transcript_text"] is None
    assert data["error_message"] is None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    assert data["started_at"] is None
    assert data["completed_at"] is None


# ---------------------------------------------------------------------------
# 404 — job not found
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_job_404_not_found(monkeypatch, job_status_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: None,
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.status_code == 404
    assert "error" in response.json()


# ---------------------------------------------------------------------------
# 422 — malformed UUID (FastAPI path validation; no monkeypatching needed)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_job_422_malformed_uuid(job_status_client):
    response = await job_status_client.get("/v1/jobs/not-a-uuid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Status variants
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_job_status_queued(monkeypatch, job_status_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(status=JobStatus.queued),
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.json()["status"] == "queued"


@pytest.mark.anyio
async def test_get_job_status_running(monkeypatch, job_status_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(
            status=JobStatus.running,
            started_at=datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        ),
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    data = response.json()
    assert data["status"] == "running"
    assert data["started_at"] is not None


@pytest.mark.anyio
async def test_get_job_status_completed(monkeypatch, job_status_client):
    snap = _make_snapshot(
        status=JobStatus.completed,
        raw_audio_uri="s3://asr-platform/raw_audio/12345678-.../input.wav",
        transcript_uri="s3://asr-platform/transcripts/12345678-.../transcript.json",
        transcript_text="This is a deterministic fake transcript for local testing.",
        started_at=datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        completed_at=datetime(2026, 1, 1, 12, 0, 5, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: snap,
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    data = response.json()
    assert data["status"] == "completed"
    assert data["transcript_text"] == "This is a deterministic fake transcript for local testing."
    assert data["transcript_uri"] is not None
    assert data["completed_at"] is not None


@pytest.mark.anyio
async def test_get_job_status_failed(monkeypatch, job_status_client):
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: _make_snapshot(
            status=JobStatus.failed,
            error_message="ASR failed",
        ),
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_message"] == "ASR failed"


# ---------------------------------------------------------------------------
# Null optional fields — no exception when all nullable fields are None
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_job_null_optional_fields(monkeypatch, job_status_client):
    snap = _make_snapshot(
        raw_audio_uri=None,
        transcript_uri=None,
        transcript_text=None,
        error_message=None,
        created_at=None,
        updated_at=None,
        started_at=None,
        completed_at=None,
    )
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: snap,
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.status_code == 200
    data = response.json()
    for field in (
        "raw_audio_uri", "transcript_uri", "transcript_text",
        "error_message", "created_at", "updated_at", "started_at", "completed_at",
    ):
        assert data[field] is None


# ---------------------------------------------------------------------------
# Regression: PostgreSQL may return plain strings for enum columns, not Enum
# instances. Ensure the endpoint does not crash and returns the string as-is.
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_job_status_and_mode_as_plain_strings(monkeypatch, job_status_client):
    snap = _make_snapshot(
        status="completed",
        mode="transcribe_only",
        transcript_text="This is a deterministic fake transcript for local testing.",
        transcript_uri="s3://asr-platform/transcripts/12345678-.../transcript.json",
        raw_audio_uri="s3://asr-platform/raw_audio/12345678-.../input.wav",
    )
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, jid: snap,
    )
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["mode"] == "transcribe_only"


# ---------------------------------------------------------------------------
# enhanced_audio_uri field in status response
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_job_status_includes_enhanced_audio_uri_when_present(monkeypatch, job_status_client):
    uri = f"s3://asr-platform/enhanced_audio/{FAKE_JOB_ID}/output.wav"
    snap = _make_snapshot(
        status=JobStatus.completed,
        mode=JobMode.enhance_and_transcribe,
        preset="light_clean",
        enhanced_audio_uri=uri,
    )
    monkeypatch.setattr("services.api.app.main._load_job", lambda db_url, jid: snap)
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["enhanced_audio_uri"] == uri
    assert data["mode"] == "enhance_and_transcribe"
    assert data["preset"] == "light_clean"


@pytest.mark.anyio
async def test_job_status_enhanced_audio_uri_null_when_absent(monkeypatch, job_status_client):
    snap = _make_snapshot(enhanced_audio_uri=None)
    monkeypatch.setattr("services.api.app.main._load_job", lambda db_url, jid: snap)
    response = await job_status_client.get(f"/v1/jobs/{FAKE_JOB_ID}")
    assert response.status_code == 200
    assert response.json()["enhanced_audio_uri"] is None
