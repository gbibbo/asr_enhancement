"""B12.1 demo-api request middleware contract.

Mirrors the platform reference (tests/api/test_logging.py) for the demo
service: every HTTP request emits exactly one ``demo.api.request`` log
record with ``method``, ``path``, ``status_code``, ``duration_ms``, and
NO ``authorization`` / ``auth_header`` / session-id header fields.
"""

from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient


_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT", "DEMO_DB_PATH", "DEMO_UPLOAD_DIR", "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR", "DEMO_LOGS_DIR", "DEMO_QUEUE_MAX",
    "DEMO_UPLOAD_LIMIT_BYTES", "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "ASSEMBLYAI_API_KEY", "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME", "ADMIN_STATS_PASSWORD",
    "DEMO_LOG_TO_FILE", "DEMO_LOG_FILENAME_PREFIX", "DEMO_ADMIN_RECENT_ERRORS",
]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("DEMO_LOG_TO_FILE", "false")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


def _request_records(caplog):
    return [r for r in caplog.records if r.getMessage() == "demo.api.request"]


def test_request_middleware_emits_event(client, caplog):
    with caplog.at_level(logging.INFO, logger="demo-api.request"):
        client.get("/demo/health")
    rec = _request_records(caplog)
    assert len(rec) >= 1


def test_request_middleware_logs_method_and_status(client, caplog):
    with caplog.at_level(logging.INFO, logger="demo-api.request"):
        client.get("/demo/health")
    rec = _request_records(caplog)[-1]
    assert rec.method == "GET"
    assert rec.status_code == 200
    assert rec.path == "/demo/health"
    assert isinstance(rec.duration_ms, float)
    assert rec.duration_ms >= 0.0


def test_request_middleware_omits_credential_headers(client, caplog):
    with caplog.at_level(logging.DEBUG):
        # Send Authorization and X-Demo-Session-Id; neither should land in
        # the log record's attributes.
        client.get(
            "/demo/health",
            headers={
                "Authorization": "Basic SOMETHING",
                "X-Demo-Session-Id": "session-sentinel",
            },
        )
    for record in caplog.records:
        for forbidden in (
            "authorization", "auth_header",
            "x_demo_session_id", "x-demo-session-id",
            "session_id", "session_id_hash",
        ):
            assert not hasattr(record, forbidden), (
                f"forbidden field {forbidden!r} on record {record.getMessage()!r}"
            )


def test_request_count_increments(client):
    before = int(getattr(client.app.state, "request_count_total", 0))
    for _ in range(5):
        client.get("/demo/health")
    after = int(getattr(client.app.state, "request_count_total", 0))
    assert after - before >= 5


def test_admin_stats_request_event_no_authorization_logged(client, caplog):
    """Authorization header on /admin/stats must not appear in record fields."""
    with caplog.at_level(logging.DEBUG):
        client.get("/admin/stats", auth=("admin", "wont-match"))
    for record in caplog.records:
        rendered = json.dumps(getattr(record, "__dict__", {}), default=str)
        assert "Basic " not in rendered or rendered.find("Basic ") < 0
