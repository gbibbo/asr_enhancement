from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.settings import get_settings
from services.api.app.main import app
from services.api.app.rate_limit import RateLimiter

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}

FAKE_JOB_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
WAV_BYTES = b"\x00" * 100


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mocked_job_pipeline(monkeypatch):
    """Patch DB/storage/Celery so /v1/transcribe and /v1/enhance-and-transcribe
    return 202 without touching real services."""
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
        lambda job_id, traceparent=None: None,
    )
    yield
    get_settings.cache_clear()


def _install_limiter(per_minute: int) -> RateLimiter:
    limiter = RateLimiter(per_minute)
    app.state.rate_limiter = limiter
    return limiter


def _files() -> dict:
    return {"file": ("clip.wav", WAV_BYTES, "audio/wav")}


# ---------------------------------------------------------------------------
# Limit triggers on uploads
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_third_post_returns_429_with_exact_body_and_retry_after(mocked_job_pipeline):
    _install_limiter(2)
    transport = ASGITransport(app=app, client=("10.0.0.1", 0))
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        r1 = await c.post("/v1/transcribe", files=_files())
        r2 = await c.post("/v1/transcribe", files=_files())
        r3 = await c.post("/v1/transcribe", files=_files())

    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r3.status_code == 429
    assert r3.json() == {
        "error": "rate_limited",
        "detail": "Too many requests. Please try again in a moment.",
    }
    retry_after = r3.headers.get("Retry-After")
    assert retry_after is not None
    assert int(retry_after) >= 1


# ---------------------------------------------------------------------------
# Independent IPs
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_independent_ips_have_independent_buckets(mocked_job_pipeline):
    _install_limiter(1)
    transport_a = ASGITransport(app=app, client=("1.2.3.4", 0))
    transport_b = ASGITransport(app=app, client=("5.6.7.8", 0))

    async with AsyncClient(transport=transport_a, base_url="http://testserver") as ca, \
            AsyncClient(transport=transport_b, base_url="http://testserver") as cb:
        ra1 = await ca.post("/v1/transcribe", files=_files())
        rb1 = await cb.post("/v1/transcribe", files=_files())
        ra2 = await ca.post("/v1/transcribe", files=_files())
        rb2 = await cb.post("/v1/transcribe", files=_files())

    assert ra1.status_code == 202
    assert rb1.status_code == 202
    assert ra2.status_code == 429
    assert rb2.status_code == 429


# ---------------------------------------------------------------------------
# Disabled when 0
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_per_minute_zero_disables_limiter(mocked_job_pipeline):
    _install_limiter(0)
    transport = ASGITransport(app=app, client=("10.0.0.2", 0))
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        for _ in range(20):
            r = await c.post("/v1/transcribe", files=_files())
            assert r.status_code == 202


# ---------------------------------------------------------------------------
# Exclusion matrix
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_excluded_endpoints_never_429(mocked_job_pipeline, monkeypatch):
    # Mock /ready dependency probes so it returns 200 without real services.
    monkeypatch.setattr(
        "services.api.app.main._check_postgres",
        lambda url: {"status": "ok"},
    )
    monkeypatch.setattr(
        "services.api.app.main._check_redis",
        lambda url: {"status": "ok"},
    )
    monkeypatch.setattr(
        "services.api.app.main._check_storage",
        lambda settings: {"status": "ok"},
    )
    # Mock _load_job so /v1/jobs/{id} and /v1/jobs/{id}/result return 404
    # without opening a real DB connection.
    fake_id = "12345678-1234-5678-1234-567812345678"
    monkeypatch.setattr(
        "services.api.app.main._load_job",
        lambda db_url, job_id: None,
    )

    _install_limiter(1)
    transport = ASGITransport(app=app, client=("10.0.0.3", 0))
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        # Consume the single allowed POST slot first.
        first = await c.post("/v1/transcribe", files=_files())
        assert first.status_code == 202

        # Confirm the limiter is now tripped for the same IP on uploads.
        tripped = await c.post("/v1/transcribe", files=_files())
        assert tripped.status_code == 429

        # None of these excluded endpoints must ever return 429, even when
        # hit many times.
        for _ in range(5):
            assert (await c.get("/health")).status_code != 429
            assert (await c.get("/ready")).status_code != 429
            assert (await c.get("/metrics")).status_code != 429
            # job status / result endpoints — they may 404 (no DB row) but
            # MUST NOT be limited.
            assert (await c.get(f"/v1/jobs/{fake_id}")).status_code != 429
            assert (await c.get(f"/v1/jobs/{fake_id}/result")).status_code != 429


# ---------------------------------------------------------------------------
# Path matching is exact
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_trailing_slash_and_similar_paths_not_limited(mocked_job_pipeline):
    _install_limiter(1)
    transport = ASGITransport(app=app, client=("10.0.0.4", 0))
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        # Consume the slot with a real exact-match upload.
        ok = await c.post("/v1/transcribe", files=_files())
        assert ok.status_code == 202

        # Trailing slash and similarly-named paths — they will 404, but the
        # rate limiter must not match them, so the response is NOT 429.
        r1 = await c.post("/v1/transcribe/", files=_files())
        r2 = await c.post("/v1/transcribexx", files=_files())
        assert r1.status_code != 429
        assert r2.status_code != 429


# ---------------------------------------------------------------------------
# Method matching
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_on_upload_path_not_limited(mocked_job_pipeline):
    _install_limiter(1)
    transport = ASGITransport(app=app, client=("10.0.0.5", 0))
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        # Consume the slot with a real POST.
        ok = await c.post("/v1/transcribe", files=_files())
        assert ok.status_code == 202

        # GET /v1/transcribe will 405 (method not allowed); MUST NOT be 429.
        r = await c.get("/v1/transcribe")
        assert r.status_code != 429
