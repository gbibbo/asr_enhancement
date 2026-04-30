from __future__ import annotations

import asyncio
import io
import wave

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.settings import get_settings
from libs.common.storage import StorageClient
from services.api.app.main import app

_FAKE_TRANSCRIPT = "This is a deterministic fake transcript for local testing."
_POLL_MAX = 30
_POLL_INTERVAL = 1.0


def _make_minimal_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00" * 3200)  # 0.1 s at 16 kHz, 16-bit
    return buf.getvalue()


def _uri_to_key(uri: str, bucket: str) -> str:
    prefix = f"s3://{bucket}/"
    assert uri.startswith(prefix), f"unexpected URI format: {uri!r}"
    return uri[len(prefix):]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_cut_a_full_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:

        # 1. Submit a minimal WAV file
        wav_bytes = _make_minimal_wav()
        submit_resp = await client.post(
            "/v1/transcribe",
            files={"file": ("smoke.wav", wav_bytes, "audio/wav")},
        )
        assert submit_resp.status_code == 202, (
            f"Expected 202 from POST /v1/transcribe, got {submit_resp.status_code}: "
            f"{submit_resp.text}"
        )
        submit_body = submit_resp.json()
        assert "job_id" in submit_body, f"No job_id in response: {submit_body}"
        job_id = submit_body["job_id"]

        # 2. Poll GET /v1/jobs/{job_id} until completed or timeout
        final_status = None
        raw_audio_uri = None
        for _ in range(_POLL_MAX):
            status_resp = await client.get(f"/v1/jobs/{job_id}")
            assert status_resp.status_code == 200, (
                f"GET /v1/jobs/{job_id} returned {status_resp.status_code}"
            )
            status_data = status_resp.json()
            final_status = status_data["status"]
            if final_status == "completed":
                raw_audio_uri = status_data.get("raw_audio_uri")
                break
            if final_status == "failed":
                pytest.fail(
                    f"Job {job_id} failed: {status_data.get('error_message')}"
                )
            await asyncio.sleep(_POLL_INTERVAL)
        else:
            pytest.fail(
                f"Job {job_id} did not reach 'completed' within {_POLL_MAX}s. "
                f"Last status: {final_status!r}. "
                "Check worker logs: docker compose logs worker"
            )

        assert final_status == "completed"
        assert raw_audio_uri, "raw_audio_uri must be non-empty in completed job status"

        # 3. Fetch result
        result_resp = await client.get(f"/v1/jobs/{job_id}/result")
        assert result_resp.status_code == 200, (
            f"GET /v1/jobs/{job_id}/result returned {result_resp.status_code}: "
            f"{result_resp.text}"
        )
        result = result_resp.json()

        # 4. Verify transcript fields
        assert result["transcript_text"] == _FAKE_TRANSCRIPT, (
            f"Unexpected transcript_text: {result['transcript_text']!r}"
        )
        assert result.get("transcript_uri"), "transcript_uri must be non-empty"
        assert result.get("completed_at"), "completed_at must be present"
        transcript_uri = result["transcript_uri"]

        # 5. Verify artifact objects exist in MinIO
        settings = get_settings()
        sc = StorageClient.from_settings(settings)
        bucket = settings.minio_bucket

        raw_key = _uri_to_key(raw_audio_uri, bucket)
        assert sc.exists(raw_key), (
            f"raw audio object not found in MinIO: key={raw_key!r}"
        )

        transcript_key = _uri_to_key(transcript_uri, bucket)
        assert sc.exists(transcript_key), (
            f"transcript object not found in MinIO: key={transcript_key!r}"
        )
