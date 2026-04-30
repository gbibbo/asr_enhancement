from __future__ import annotations

import os

import pytest

from libs.common.settings import get_settings

# Ensure required backend env vars are present at collection time so any
# module-level get_settings() call (e.g. via celery_app imports) succeeds.
_DEFAULTS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
    "MINIO_BUCKET": "asr-platform",
}
for _k, _v in _DEFAULTS.items():
    os.environ.setdefault(_k, _v)


@pytest.fixture(autouse=True)
def _disable_rate_limit_by_default(monkeypatch):
    """Default the rate limiter to disabled for every API test.

    Tests that exercise the limiter explicitly install their own RateLimiter
    on app.state.rate_limiter; this fixture prevents accidental 429s in
    every other test by both clearing the settings cache (so a fresh
    Settings reads RATE_LIMIT_PER_MINUTE=0) and resetting any limiter
    already attached to the global app instance.
    """
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")
    get_settings.cache_clear()

    from services.api.app.main import app  # imported lazily to avoid cycles
    from services.api.app.rate_limit import RateLimiter

    app.state.rate_limiter = RateLimiter(0)
    yield
    get_settings.cache_clear()
