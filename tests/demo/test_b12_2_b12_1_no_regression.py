"""B12.2 adjacent regression guard for B12.1 behavior.

Verifies that B12.2 did not alter:
- compute_public_view output shape (assemblyai state + cap_state only)
- read_disk_usage output shape (scope label only, no path)
- read_cloudflare_tunnel_state output
- build_admin_stats key set
- /admin/stats returns 401 without auth
- /demo/providers/assemblyai/status shape unchanged
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT", "DEMO_DB_PATH", "DEMO_UPLOAD_DIR", "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR", "DEMO_LOGS_DIR", "DEMO_WORKER_CONCURRENCY",
    "DEMO_QUEUE_MAX", "DEMO_UPLOAD_LIMIT_BYTES", "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "ASSEMBLYAI_API_KEY", "ENHANCER_VERSION", "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD", "DEMO_EXAMPLES_CONFIG", "DEMO_LOG_TO_FILE",
    "DEMO_LOG_MAX_BYTES", "DEMO_LOG_BACKUP_COUNT", "DEMO_LOG_FILENAME_PREFIX",
    "DEMO_ADMIN_RECENT_ERRORS",
]


_MINIMAL_EXAMPLE = {
    "example_id": "ex001",
    "title": "Test",
    "duration_seconds": 5.0,
    "degradation_ids": ["far_field_room"],
    "ground_truth": "hello world",
}


@pytest.fixture()
def test_client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ADMIN_STATS_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_STATS_PASSWORD", "shh-test-only")
    monkeypatch.setenv("DEMO_LOG_TO_FILE", "false")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo_examples.json").write_text(
        json.dumps([_MINIMAL_EXAMPLE]), encoding="utf-8"
    )
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


def test_admin_stats_401_without_auth(test_client):
    resp = test_client.get("/admin/stats")
    assert resp.status_code == 401


def test_admin_stats_401_wrong_password(test_client):
    resp = test_client.get("/admin/stats", auth=("admin", "wrong"))
    assert resp.status_code == 401


def test_compute_public_view_shape():
    """compute_public_view returns exactly assemblyai: {state, cap_state}."""
    from pathlib import Path as _Path
    import tempfile
    from libs.demo.persistence import init_schema
    from libs.demo.usage import compute_public_view
    from libs.common.demo_settings import DemoSettings

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = _Path(tmpdir) / "demo.db"
        init_schema(db_path)
        settings = DemoSettings(
            demo_runtime_root=_Path(tmpdir),
            demo_db_path=db_path,
    
        )
        result = compute_public_view(db_path, settings)
        assert set(result.keys()) == {"assemblyai"}
        aa = result["assemblyai"]
        assert set(aa.keys()) == {"state", "cap_state"}


def test_read_disk_usage_scope_label_only(tmp_path):
    from libs.common.demo_settings import DemoSettings
    from libs.demo.probes import read_disk_usage

    settings = DemoSettings(
        demo_runtime_root=tmp_path,

    )
    result = read_disk_usage(settings)
    assert result["scope"] == "demo_runtime_root"
    assert "path" not in result
    assert "/home/" not in str(result)
    expected_keys = {"scope", "total_bytes", "used_bytes", "free_bytes", "used_percent"}
    assert set(result.keys()) == expected_keys


def test_read_cloudflare_tunnel_state_unavailable():
    from libs.demo.probes import read_cloudflare_tunnel_state

    result = read_cloudflare_tunnel_state()
    assert result == {"state": "unavailable"}


def test_build_admin_stats_keys(tmp_path):
    from libs.common.demo_settings import DemoSettings
    from libs.demo.admin_stats import build_admin_stats
    from libs.demo.persistence import init_schema

    db_path = tmp_path / "demo.db"
    init_schema(db_path)
    settings = DemoSettings(
        demo_runtime_root=tmp_path,
        demo_db_path=db_path,

    )
    result = build_admin_stats(
        settings=settings,
        request_count_total=0,
        cache_hit_count=0,
        cache_miss_count=0,
        error_buffer_handler=None,
    )
    expected_keys = {
        "startup_time", "uptime_seconds", "queue_depth", "jobs_by_status",
        "provider_state", "request_count_total", "cache", "disk",
        "cpu_temperature", "last_errors", "cloudflare_tunnel", "last_cleanup_at",
    }
    assert set(result.keys()) == expected_keys


def test_public_provider_state_shape_unchanged(test_client):
    resp = test_client.get("/demo/providers/assemblyai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert sorted(body.keys()) == ["assemblyai"]
    aa = body["assemblyai"]
    assert sorted(aa.keys()) == ["cap_state", "state"]
    assert aa["state"] in {
        "available", "daily_quota_reached", "quota_exhausted", "disabled",
    }
    assert aa["cap_state"] in {
        "below", "warning_reached", "soft_reached", "hard_reached",
    }


def test_admin_stats_disk_block_no_path_leakage(test_client):
    resp = test_client.get("/admin/stats", auth=("admin", "shh-test-only"))
    assert resp.status_code == 200
    body = resp.json()
    disk = body["disk"]
    assert disk["scope"] == "demo_runtime_root"
    serialized = json.dumps(body)
    assert "/home/" not in serialized
    assert "/var/" not in serialized
    assert "/etc/" not in serialized
