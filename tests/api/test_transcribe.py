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
async def transcribe_client(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    monkeypatch.setattr(
        "services.api.app.main._create_job",
        lambda db_url, mode, provider: FAKE_JOB_ID,
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
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_transcribe_returns_202(transcribe_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 202


@pytest.mark.anyio
async def test_transcribe_response_body(transcribe_client):
    files = {"file": ("clip.wav", b"\x00" * 100, "audio/wav")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    data = response.json()
    assert "job_id" in data
    assert uuid.UUID(data["job_id"])   # parseable as UUID
    assert data["status"] == "queued"


# ---------------------------------------------------------------------------
# _upload_raw_audio key unit test (sync — proves deterministic object key)
# ---------------------------------------------------------------------------

def test_upload_raw_audio_key(tmp_path, monkeypatch):
    tmp_file = tmp_path / "input.wav"
    tmp_file.write_bytes(b"\x00" * 10)

    mock_sc = MagicMock()
    mock_sc.put.return_value = f"s3://asr-platform/raw_audio/{FAKE_JOB_ID}/input.wav"

    with patch("services.api.app.main.StorageClient") as mock_cls:
        mock_cls.from_settings.return_value = mock_sc

        from libs.common.settings import Settings
        settings = Settings(
            database_url="postgresql+psycopg://x:x@localhost/x",
            redis_url="redis://localhost:6379/0",
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
        )
        _upload_raw_audio(settings, FAKE_JOB_ID, tmp_file, ".wav", "audio/wav")

    mock_sc.put.assert_called_once_with(
        f"raw_audio/{FAKE_JOB_ID}/input.wav",
        tmp_file,
        content_type="audio/wav",
    )


# ---------------------------------------------------------------------------
# Temp file cleanup
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_transcribe_temp_file_deleted_on_success(monkeypatch, tmp_path, transcribe_client):
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
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 202
    assert not sentinel.exists()


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_transcribe_415_bad_extension(transcribe_client):
    files = {"file": ("malware.exe", b"\x00" * 10, "application/octet-stream")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 415
    data = response.json()
    assert "error" in data
    assert "detail" in data


@pytest.mark.anyio
async def test_transcribe_413_file_too_large(monkeypatch, transcribe_client):
    monkeypatch.setenv("UPLOAD_LIMIT_BYTES", "10")
    get_settings.cache_clear()
    files = {"file": ("clip.wav", b"\x00" * 11, "audio/wav")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert "detail" in data


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_transcribe_500_on_job_creation_failure(monkeypatch, transcribe_client):
    def _raise(*a, **kw):
        raise RuntimeError("DB down")

    monkeypatch.setattr("services.api.app.main._create_job", _raise)
    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 500


@pytest.mark.anyio
async def test_transcribe_marks_job_failed_on_storage_error(monkeypatch, transcribe_client):
    def _raise(*a, **kw):
        raise RuntimeError("MinIO down")

    fail_calls: list[uuid.UUID] = []

    monkeypatch.setattr("services.api.app.main._upload_raw_audio", _raise)
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, job_id, msg: fail_calls.append(job_id),
    )

    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    await transcribe_client.post("/v1/transcribe", files=files)
    assert FAKE_JOB_ID in fail_calls


@pytest.mark.anyio
async def test_transcribe_returns_500_on_storage_error(monkeypatch, transcribe_client):
    def _raise(*a, **kw):
        raise RuntimeError("MinIO down")

    monkeypatch.setattr("services.api.app.main._upload_raw_audio", _raise)
    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 500


@pytest.mark.anyio
async def test_transcribe_marks_job_failed_on_enqueue_error(monkeypatch, transcribe_client):
    def _raise(*a, **kw):
        raise RuntimeError("Redis down")

    fail_calls: list[uuid.UUID] = []

    monkeypatch.setattr("services.api.app.main._enqueue_transcribe", _raise)
    monkeypatch.setattr(
        "services.api.app.main._mark_job_failed",
        lambda db_url, job_id, msg: fail_calls.append(job_id),
    )

    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    await transcribe_client.post("/v1/transcribe", files=files)
    assert FAKE_JOB_ID in fail_calls


@pytest.mark.anyio
async def test_transcribe_returns_500_on_enqueue_error(monkeypatch, transcribe_client):
    def _raise(*a, **kw):
        raise RuntimeError("Redis down")

    monkeypatch.setattr("services.api.app.main._enqueue_transcribe", _raise)
    files = {"file": ("clip.wav", b"\x00" * 10, "audio/wav")}
    response = await transcribe_client.post("/v1/transcribe", files=files)
    assert response.status_code == 500
