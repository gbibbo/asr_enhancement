import os

# Set required env vars before test collection so that celery_app.py (which calls
# get_settings() at module level) can be imported when test modules are collected.
# Tests that need per-test isolation use monkeypatch.setenv on top of these defaults.
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
