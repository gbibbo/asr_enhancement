from __future__ import annotations

import logging
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.settings import get_settings
from services.api.app.main import app

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}

FAKE_JOB_ID = uuid.UUID("aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def log_client(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    monkeypatch.setattr(
        "services.api.app.main._create_job",
        lambda db_url, mode, provider, preset="bypass": FAKE_JOB_ID,
    )
    monkeypatch.setattr(
        "services.api.app.main._upload_raw_audio",
        lambda s, job_id, path, ext, ct: f"s3://asr-platform/raw_audio/{job_id}/input{ext}",
    )
    monkeypatch.setattr(
        "services.api.app.main._set_raw_audio_uri",
        lambda db_url, job_id, uri: None,
    )
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, job_id, msg: None,
    )
    monkeypatch.setattr(
        "services.api.app.main._enqueue_transcribe",
        lambda job_id: None,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Request middleware tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_request_middleware_logs_api_request_event(log_client, caplog):
    with caplog.at_level(logging.INFO):
        await log_client.get("/health")
    events = [r.getMessage() for r in caplog.records]
    assert "api.request" in events


@pytest.mark.anyio
async def test_request_middleware_logs_method(log_client, caplog):
    with caplog.at_level(logging.INFO):
        await log_client.get("/health")
    req_records = [r for r in caplog.records if r.getMessage() == "api.request"]
    assert len(req_records) >= 1
    assert req_records[-1].method == "GET"


@pytest.mark.anyio
async def test_request_middleware_logs_status_code(log_client, caplog):
    with caplog.at_level(logging.INFO):
        await log_client.get("/health")
    req_records = [r for r in caplog.records if r.getMessage() == "api.request"]
    assert len(req_records) >= 1
    assert req_records[-1].status_code == 200


@pytest.mark.anyio
async def test_request_middleware_logs_duration_ms(log_client, caplog):
    with caplog.at_level(logging.INFO):
        await log_client.get("/health")
    req_records = [r for r in caplog.records if r.getMessage() == "api.request"]
    assert len(req_records) >= 1
    duration = req_records[-1].duration_ms
    assert isinstance(duration, float)
    assert duration >= 0.0


@pytest.mark.anyio
async def test_request_middleware_no_authorization_in_logs(log_client, caplog):
    with caplog.at_level(logging.DEBUG):
        await log_client.get("/health")
    for record in caplog.records:
        assert not hasattr(record, "authorization"), "authorization field must not appear in logs"
        assert not hasattr(record, "auth_header"), "auth_header field must not appear in logs"


@pytest.mark.anyio
async def test_job_created_log_includes_job_id(log_client, caplog):
    with caplog.at_level(logging.INFO):
        files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
        response = await log_client.post("/v1/transcribe", files=files)
    assert response.status_code == 202
    created = [r for r in caplog.records if r.getMessage() == "api.job_created"]
    assert len(created) >= 1
    assert created[0].job_id == str(FAKE_JOB_ID)


@pytest.mark.anyio
async def test_job_enqueued_log_includes_job_id(log_client, caplog):
    with caplog.at_level(logging.INFO):
        files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
        response = await log_client.post("/v1/transcribe", files=files)
    assert response.status_code == 202
    enqueued = [r for r in caplog.records if r.getMessage() == "api.job_enqueued"]
    assert len(enqueued) >= 1
    assert enqueued[0].job_id == str(FAKE_JOB_ID)
