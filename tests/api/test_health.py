from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from libs.common.settings import get_settings
from services.api.app.main import _check_storage, app

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def ready_client(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    monkeypatch.setattr(
        "services.api.app.main._check_postgres",
        lambda url: {"status": "ok", "error": None},
    )
    monkeypatch.setattr(
        "services.api.app.main._check_redis",
        lambda url: {"status": "ok", "error": None},
    )
    monkeypatch.setattr(
        "services.api.app.main._check_storage",
        lambda s: {"status": "ok", "error": None},
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    get_settings.cache_clear()


def test_app_imports():
    assert app is not None


# --- /health ---

@pytest.mark.anyio
async def test_health_status_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_body(client):
    response = await client.get("/health")
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_unknown_route_returns_json_error(client):
    response = await client.get("/nonexistent")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


# --- /ready (all healthy) ---

@pytest.mark.anyio
async def test_ready_status_200(ready_client):
    response = await ready_client.get("/ready")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_ready_body(ready_client):
    response = await ready_client.get("/ready")
    data = response.json()
    assert data["status"] == "ok"
    assert "dependencies" in data


@pytest.mark.anyio
async def test_ready_all_dependencies_ok(ready_client):
    response = await ready_client.get("/ready")
    deps = response.json()["dependencies"]
    for name in ("postgres", "redis", "storage"):
        assert deps[name]["status"] == "ok"
        assert deps[name]["error"] is None


# --- /ready (degraded cases) ---

@pytest.mark.anyio
async def test_ready_503_when_postgres_fails(monkeypatch, ready_client):
    monkeypatch.setattr(
        "services.api.app.main._check_postgres",
        lambda url: {"status": "error", "error": "pg down"},
    )
    response = await ready_client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["postgres"]["status"] == "error"
    assert data["dependencies"]["redis"]["status"] == "ok"
    assert data["dependencies"]["storage"]["status"] == "ok"


@pytest.mark.anyio
async def test_ready_503_when_redis_fails(monkeypatch, ready_client):
    monkeypatch.setattr(
        "services.api.app.main._check_redis",
        lambda url: {"status": "error", "error": "redis down"},
    )
    response = await ready_client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["redis"]["status"] == "error"
    assert data["dependencies"]["postgres"]["status"] == "ok"
    assert data["dependencies"]["storage"]["status"] == "ok"


@pytest.mark.anyio
async def test_ready_503_when_storage_fails(monkeypatch, ready_client):
    monkeypatch.setattr(
        "services.api.app.main._check_storage",
        lambda s: {"status": "error", "error": "storage down"},
    )
    response = await ready_client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["storage"]["status"] == "error"
    assert data["dependencies"]["postgres"]["status"] == "ok"
    assert data["dependencies"]["redis"]["status"] == "ok"


@pytest.mark.anyio
async def test_ready_503_missing_bucket(monkeypatch, ready_client):
    monkeypatch.setattr(
        "services.api.app.main._check_storage",
        lambda s: {"status": "error", "error": "Bucket 'asr-platform' does not exist"},
    )
    response = await ready_client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["storage"]["status"] == "error"
    assert "asr-platform" in data["dependencies"]["storage"]["error"]


@pytest.mark.anyio
async def test_ready_degraded_status_in_body(monkeypatch, ready_client):
    monkeypatch.setattr(
        "services.api.app.main._check_redis",
        lambda url: {"status": "error", "error": "timeout"},
    )
    response = await ready_client.get("/ready")
    assert response.json()["status"] == "degraded"


# --- _check_storage unit test ---

def test_check_storage_calls_ensure_bucket_with_create_if_missing_false(monkeypatch):
    mock_sc = MagicMock()
    with patch("services.api.app.main.StorageClient") as mock_cls:
        mock_cls.from_settings.return_value = mock_sc
        mock_sc.ensure_bucket.return_value = None

        from libs.common.settings import Settings
        settings = Settings(
            database_url="postgresql+psycopg://x:x@localhost/x",
            redis_url="redis://localhost:6379/0",
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
        )
        result = _check_storage(settings)

    mock_sc.ensure_bucket.assert_called_once_with(create_if_missing=False)
    assert result["status"] == "ok"
