from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


def test_app_imports():
    assert app is not None


@pytest.mark.anyio
async def test_health_status_200(client):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_body(client):
    response = await client.get("/health")
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_ready_status_200(client):
    response = await client.get("/ready")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_ready_body(client):
    response = await client.get("/ready")
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_unknown_route_returns_json_error(client):
    response = await client.get("/nonexistent")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
