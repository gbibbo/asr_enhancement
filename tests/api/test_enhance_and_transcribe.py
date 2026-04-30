from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.settings import get_settings
from services.api.app.main import (
    _upload_raw_audio,
    app,
)
from services.api.app.rate_limit import RateLimiter
from services.api.app.upload_validation import ValidatedUpload

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}

FAKE_JOB_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def enhance_client(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    app.state.rate_limiter = RateLimiter(0)

    created_jobs: list[tuple] = []

    monkeypatch.setattr(
        "services.api.app.main._create_job",
        lambda db_url, mode, provider, preset="bypass": (
            created_jobs.append((mode, provider, preset)) or FAKE_JOB_ID
        ),
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
        lambda job_id, traceparent=None: None,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c._created_jobs = created_jobs  # expose for assertions
        yield c

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_enhance_returns_202(enhance_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    data = {"preset": "light_clean"}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert response.status_code == 202


@pytest.mark.anyio
async def test_enhance_response_body(enhance_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    data = {"preset": "light_clean"}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    body = response.json()
    assert "job_id" in body
    assert uuid.UUID(body["job_id"])
    assert body["status"] == "queued"


@pytest.mark.anyio
async def test_enhance_default_preset_is_bypass(enhance_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files)
    assert response.status_code == 202
    assert len(enhance_client._created_jobs) == 1
    _, _, preset = enhance_client._created_jobs[0]
    assert preset == "bypass"


@pytest.mark.anyio
async def test_enhance_known_preset_accepted(enhance_client):
    for preset_name in ("bypass", "light_clean", "denoise", "denoise_dereverb"):
        enhance_client._created_jobs.clear()
        files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
        response = await enhance_client.post(
            "/v1/enhance-and-transcribe", files=files, data={"preset": preset_name}
        )
        assert response.status_code == 202, f"preset={preset_name!r} should be accepted"
        _, _, stored = enhance_client._created_jobs[0]
        assert stored == preset_name


# ---------------------------------------------------------------------------
# Preset validation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_enhance_400_unknown_preset(monkeypatch, enhance_client):
    created: list = []
    monkeypatch.setattr(
        "services.api.app.main._create_job",
        lambda *a, **kw: created.append(1) or FAKE_JOB_ID,
    )

    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    response = await enhance_client.post(
        "/v1/enhance-and-transcribe", files=files, data={"preset": "bogus_preset"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "unknown_preset"
    assert "bogus_preset" in body["detail"]
    assert created == []


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_enhance_415_bad_extension(enhance_client):
    files = {"file": ("malware.exe", b"\x00" * 10, "application/octet-stream")}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files)
    assert response.status_code == 415
    body = response.json()
    assert "error" in body
    assert "detail" in body


@pytest.mark.anyio
async def test_enhance_413_file_too_large(monkeypatch, enhance_client):
    monkeypatch.setenv("UPLOAD_LIMIT_BYTES", "10")
    get_settings.cache_clear()
    files = {"file": ("clip.wav", b"\x00" * 11, "audio/wav")}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files)
    assert response.status_code == 413
    body = response.json()
    assert "error" in body
    assert "detail" in body


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_enhance_500_on_job_creation_failure(monkeypatch, enhance_client):
    def _raise(*a, **kw):
        raise RuntimeError("DB down")

    monkeypatch.setattr("services.api.app.main._create_job", _raise)
    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    data = {"preset": "light_clean"}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert response.status_code == 500


@pytest.mark.anyio
async def test_enhance_marks_job_failed_on_storage_error(monkeypatch, enhance_client):
    def _raise(*a, **kw):
        raise RuntimeError("MinIO down")

    fail_calls: list[uuid.UUID] = []
    monkeypatch.setattr("services.api.app.main._upload_raw_audio", _raise)
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, job_id, msg: fail_calls.append(job_id),
    )

    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    data = {"preset": "light_clean"}
    await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert FAKE_JOB_ID in fail_calls


@pytest.mark.anyio
async def test_enhance_returns_500_on_storage_error(monkeypatch, enhance_client):
    def _raise(*a, **kw):
        raise RuntimeError("MinIO down")

    monkeypatch.setattr("services.api.app.main._upload_raw_audio", _raise)
    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    data = {"preset": "light_clean"}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert response.status_code == 500


@pytest.mark.anyio
async def test_enhance_marks_job_failed_on_enqueue_error(monkeypatch, enhance_client):
    def _raise(*a, **kw):
        raise RuntimeError("Redis down")

    fail_calls: list[uuid.UUID] = []
    monkeypatch.setattr("services.api.app.main._enqueue_transcribe", _raise)
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, job_id, msg: fail_calls.append(job_id),
    )

    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    data = {"preset": "light_clean"}
    await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert FAKE_JOB_ID in fail_calls


@pytest.mark.anyio
async def test_enhance_returns_500_on_enqueue_error(monkeypatch, enhance_client):
    def _raise(*a, **kw):
        raise RuntimeError("Redis down")

    monkeypatch.setattr("services.api.app.main._enqueue_transcribe", _raise)
    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    data = {"preset": "light_clean"}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert response.status_code == 500


@pytest.mark.anyio
async def test_enhance_temp_file_deleted_on_success(monkeypatch, tmp_path, enhance_client):
    sentinel = tmp_path / "sentinel.wav"
    sentinel.write_bytes(b"\x00" * 10)

    async def fake_validate(upload, limit, tmp_dir=None):
        return ValidatedUpload(
            path=sentinel,
            original_filename="clip.wav",
            extension=".wav",
            content_type="audio/wav",
            size_bytes=10,
        )

    monkeypatch.setattr("services.api.app.main.validate_and_buffer_upload", fake_validate)

    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    data = {"preset": "light_clean"}
    response = await enhance_client.post("/v1/enhance-and-transcribe", files=files, data=data)
    assert response.status_code == 202
    assert not sentinel.exists()
