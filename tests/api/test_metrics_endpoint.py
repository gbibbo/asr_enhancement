from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.settings import get_settings
from libs.observability.metrics import get_metrics_output
from services.api.app.main import app

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}

FAKE_JOB_ID = uuid.UUID("aaaabbbb-cccc-dddd-eeee-ffffaaaabbbb")
_FAKE_URI = f"s3://asr-platform/raw_audio/{FAKE_JOB_ID}/input.wav"


def _samples(output: str, metric_name: str) -> list[str]:
    """Return non-comment data lines for the given metric name."""
    return [
        line for line in output.splitlines()
        if (
            line.startswith(metric_name + "{") or line.startswith(metric_name + " ")
        ) and not line.startswith("#")
    ]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def api_client(monkeypatch):
    """Client with all DB/storage/queue helpers mocked for transcribe routes."""
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    monkeypatch.setattr(
        "services.api.app.main._create_job",
        lambda db_url, mode, provider, preset="bypass": FAKE_JOB_ID,
    )
    monkeypatch.setattr(
        "services.api.app.main._upload_raw_audio",
        lambda s, job_id, path, ext, ct: _FAKE_URI,
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
        lambda job_id, traceparent=None: None,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Basic endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_metrics_returns_200(client):
    response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_metrics_content_type_contains_text_plain(client):
    response = await client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.anyio
async def test_metrics_body_is_utf8(client):
    response = await client.get("/metrics")
    response.text.encode("utf-8")  # raises if not valid UTF-8


@pytest.mark.anyio
async def test_metrics_body_contains_api_requests_definition(client):
    response = await client.get("/metrics")
    assert "asr_api_requests_total" in response.text


@pytest.mark.anyio
async def test_metrics_body_contains_job_counter_definition(client):
    response = await client.get("/metrics")
    assert "asr_jobs_total" in response.text


@pytest.mark.anyio
async def test_metrics_body_contains_worker_heartbeat_definition(client):
    response = await client.get("/metrics")
    assert "asr_worker_heartbeat_timestamp_seconds" in response.text


# ---------------------------------------------------------------------------
# Request counter instrumentation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_request_counter_labeled_sample_after_health(client):
    await client.get("/health")
    metrics_resp = await client.get("/metrics")
    samples = _samples(metrics_resp.text, "asr_api_requests_total")
    assert any(
        'method="GET"' in s and 'path="/health"' in s and 'status_code="200"' in s
        for s in samples
    )


# ---------------------------------------------------------------------------
# Job queued counter instrumentation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_transcribe_increments_queued_counter(api_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    response = await api_client.post("/v1/transcribe", files=files)
    assert response.status_code == 202

    metrics_resp = await api_client.get("/metrics")
    samples = _samples(metrics_resp.text, "asr_jobs_total")
    assert any(
        'status="queued"' in s and 'mode="transcribe_only"' in s
        for s in samples
    )


@pytest.mark.anyio
async def test_enhance_and_transcribe_increments_queued_counter(api_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    data = {"preset": "bypass"}
    response = await api_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert response.status_code == 202

    metrics_resp = await api_client.get("/metrics")
    samples = _samples(metrics_resp.text, "asr_jobs_total")
    assert any(
        'status="queued"' in s and 'mode="enhance_and_transcribe"' in s
        for s in samples
    )


# ---------------------------------------------------------------------------
# Error counter instrumentation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_unhandled_error_handler_increments_api_errors(client):
    # Call _unhandled_exception_handler directly to verify the wiring.
    # Using the HTTP path is unreliable in this Starlette version because
    # exceptions from asyncio.to_thread can escape the middleware call_next
    # boundary before ExceptionMiddleware catches them.
    from unittest.mock import MagicMock
    from services.api.app.main import _unhandled_exception_handler

    mock_request = MagicMock()
    mock_request.url.path = "/v1/jobs/direct-test-path"

    await _unhandled_exception_handler(mock_request, RuntimeError("forced"))

    metrics_resp = await client.get("/metrics")
    samples = _samples(metrics_resp.text, "asr_api_errors_total")
    assert any(
        'path="/v1/jobs/direct-test-path"' in s
        for s in samples
    )
