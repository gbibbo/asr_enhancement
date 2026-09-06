"""B12.1 admin stats field coverage.

Covers:
- authenticated GET returns all 14 plan-required fields with correct shapes;
- counters reflect middleware/run-cached activity;
- disk block contains scope only (no path / no /home/);
- cpu_temperature falls back to unavailable when sysfs is missing;
- cloudflare_tunnel state is unavailable (no probe in B12.1);
- last_cleanup_at honours admin_state writes;
- public privacy regression for /demo/health and
  /demo/providers/assemblyai/status (membership only — no hardcoded state);
- provider_state admin block still includes B10.1 spend invariants;
- full-string scan rejects transcripts/GT/session_id_hash/ledger_id/
  raw_payload/audio_path/filename/original_filename/"/home/" anywhere in the
  public OR the admin response.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT",
    "DEMO_DB_PATH",
    "DEMO_UPLOAD_DIR",
    "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR",
    "DEMO_LOGS_DIR",
    "DEMO_WORKER_CONCURRENCY",
    "DEMO_QUEUE_MAX",
    "DEMO_UPLOAD_LIMIT_BYTES",
    "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "ASSEMBLYAI_API_KEY",
    "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD",
    "DEMO_EXAMPLES_CONFIG",
    "DEMO_LOG_TO_FILE",
    "DEMO_LOG_MAX_BYTES",
    "DEMO_LOG_BACKUP_COUNT",
    "DEMO_LOG_FILENAME_PREFIX",
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
def auth_client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ADMIN_STATS_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_STATS_PASSWORD", "shh-test-only")
    # Force file logging off in tests so we do not leave handlers writing to
    # tmp_path between tests; rotation has its own dedicated test.
    monkeypatch.setenv("DEMO_LOG_TO_FILE", "false")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo_examples.json").write_text(
        json.dumps([_MINIMAL_EXAMPLE]), encoding="utf-8"
    )
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


def _admin_get(client: TestClient):
    return client.get("/admin/stats", auth=("admin", "shh-test-only"))


def test_admin_stats_authenticated_returns_all_b12_1_keys(auth_client):
    resp = _admin_get(auth_client)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    expected_top = {
        "startup_time", "uptime_seconds", "queue_depth", "jobs_by_status",
        "provider_state", "request_count_total", "cache", "disk",
        "cpu_temperature", "last_errors", "cloudflare_tunnel",
        "last_cleanup_at",
    }
    assert expected_top.issubset(set(body.keys()))
    # uptime_seconds is a non-negative float
    assert isinstance(body["uptime_seconds"], (int, float))
    assert body["uptime_seconds"] >= 0


def test_admin_stats_request_count_increments(auth_client):
    auth_client.get("/demo/health")
    auth_client.get("/demo/health")
    auth_client.get("/demo/health")
    body = _admin_get(auth_client).json()
    # The middleware also counts the /admin/stats GET itself, so >= 4 is
    # the right lower bound after 3 health probes plus this admin call.
    assert body["request_count_total"] >= 4


def test_admin_stats_cache_hit_rate_reflects_run_cached(auth_client):
    settings = auth_client.app.state.settings
    cache_key = "ex001|far_field_room|degradation_v1|whisper|tiny.en|bypass|1.0"
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(settings.demo_db_path))
    conn.execute(
        "INSERT INTO cache_entries (cache_key, example_id, degradation_id,"
        " degradation_version, asr_provider, asr_model_version, enhancer_version,"
        " metrics_version, result_json, artifact_root, created_at) VALUES"
        " (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            cache_key, "ex001", "far_field_room", "degradation_v1",
            "whisper", "tiny.en", "bypass", "1.0",
            json.dumps({"hypothesis": "hello world"}), "/tmp", now,
        ),
    )
    conn.commit()
    conn.close()

    # one HIT
    h = auth_client.post(
        "/demo/run-cached",
        json={
            "example_id": "ex001", "degradation_id": "far_field_room",
            "provider": "whisper", "enhancer_version": "bypass",
        },
    )
    assert h.json()["status"] == "cache_hit"
    # one MISS (different enhancer_version)
    m = auth_client.post(
        "/demo/run-cached",
        json={
            "example_id": "ex001", "degradation_id": "far_field_room",
            "provider": "whisper", "enhancer_version": "1.0",
        },
    )
    assert m.json()["status"] == "cache_miss"

    body = _admin_get(auth_client).json()
    cache = body["cache"]
    assert cache["hits_total"] >= 1
    assert cache["misses_total"] >= 1
    assert 0.0 <= cache["hit_rate"] <= 1.0
    # entries_total counts the inserted row
    assert cache["entries_total"] >= 1


def test_admin_stats_disk_no_path_no_home(auth_client):
    body = _admin_get(auth_client).json()
    disk = body["disk"]
    assert set(disk.keys()) == {
        "scope", "total_bytes", "used_bytes", "free_bytes", "used_percent",
    }
    assert "path" not in disk
    assert disk["scope"] == "demo_runtime_root"
    # Whole-response scan: no filesystem path leakage anywhere.
    serialized = json.dumps(body)
    assert "/home/" not in serialized
    assert "/var/" not in serialized
    assert "/etc/" not in serialized
    assert "/tmp/" not in serialized
    # Sanity: numeric ranges
    assert disk["total_bytes"] >= disk["used_bytes"] >= 0
    assert 0.0 <= disk["used_percent"] <= 100.0


def test_admin_stats_cpu_temperature_unavailable_fallback(auth_client, monkeypatch, tmp_path):
    # Point the probe at a nonexistent path so the fallback fires.
    from libs.demo import probes as probes_mod
    missing = tmp_path / "no_thermal_zone"
    monkeypatch.setattr(probes_mod, "_CPU_TEMP_PATH_DEFAULT", missing)
    body = _admin_get(auth_client).json()
    cpu = body["cpu_temperature"]
    assert cpu == {"state": "unavailable"}


def test_admin_stats_cpu_temperature_available_when_sysfs_readable(auth_client, monkeypatch, tmp_path):
    fake = tmp_path / "fake_thermal_temp"
    fake.write_text("48123\n", encoding="utf-8")
    from libs.demo import probes as probes_mod
    monkeypatch.setattr(probes_mod, "_CPU_TEMP_PATH_DEFAULT", fake)
    body = _admin_get(auth_client).json()
    cpu = body["cpu_temperature"]
    assert cpu["state"] == "available"
    assert isinstance(cpu["celsius"], float)
    assert abs(cpu["celsius"] - 48.123) < 0.0011


def test_admin_stats_cloudflare_tunnel_unavailable(auth_client):
    body = _admin_get(auth_client).json()
    assert body["cloudflare_tunnel"] == {"state": "unavailable"}


def test_admin_stats_last_cleanup_at_round_trip(auth_client):
    from libs.demo.persistence import set_admin_state
    settings = auth_client.app.state.settings
    body_before = _admin_get(auth_client).json()
    assert body_before["last_cleanup_at"] is None

    iso = "2026-05-05T12:34:56+00:00"
    set_admin_state(settings.demo_db_path, "last_cleanup_at", iso)
    body_after = _admin_get(auth_client).json()
    assert body_after["last_cleanup_at"] == iso


def test_admin_stats_provider_state_b10_1_invariants(auth_client):
    body = _admin_get(auth_client).json()
    aa = body["provider_state"]["assemblyai"]
    for key in (
        "state", "cap_state", "key_configured",
        "daily_usd", "total_usd", "reserved_usd",
        "daily_soft_cap_usd", "warning_cap_usd", "hard_cap_usd",
        "usd_per_second_estimate", "as_of",
    ):
        assert key in aa, f"missing {key} in admin provider_state"


def test_public_health_shape_unchanged(auth_client):
    resp = auth_client.get("/demo/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok"}
    assert sorted(body.keys()) == ["status"]


def test_admin_health_requires_auth(auth_client):
    resp = auth_client.get("/admin/health", auth=None)
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Basic"


def test_admin_health_returns_diagnostics_with_auth(auth_client):
    resp = auth_client.get("/admin/health", auth=("admin", "shh-test-only"))
    assert resp.status_code == 200
    body = resp.json()
    assert "db_ok" in body
    assert "queue_depth" in body
    assert "mode" in body


def test_public_provider_state_shape_no_state_assumption(auth_client):
    resp = auth_client.get("/demo/providers/assemblyai/status")
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
    forbidden = {
        "daily_usd", "total_usd", "reserved_usd", "daily_soft_cap_usd",
        "warning_cap_usd", "hard_cap_usd", "usd_per_second_estimate",
        "key_configured", "as_of", "spend", "caps", "ledger_id",
        "session_id_hash", "row_count",
    }
    assert forbidden.isdisjoint(set(aa.keys()))


def test_public_endpoints_full_string_scan_no_privacy_leakage(auth_client):
    health = auth_client.get("/demo/health").text
    public_pa = auth_client.get("/demo/providers/assemblyai/status").text
    admin = _admin_get(auth_client).text
    for blob in (health, public_pa, admin):
        for needle in (
            "transcript", "hypothesis", "ground_truth", "reference_text",
            "session_id_hash", "ledger_id", "raw_payload",
            "audio_path", "input_artifact_path", "degraded_artifact_path",
            "enhanced_artifact_path",
            "original_filename", "upload_filename",
            "/home/", "cloudflared_url", "tunnel_token",
        ):
            assert needle not in blob, (
                f"forbidden token {needle!r} found in response: {blob[:200]!r}"
            )


def test_admin_stats_401_without_credentials(auth_client):
    resp = auth_client.get("/admin/stats")
    assert resp.status_code == 401


def test_admin_stats_401_for_bad_password(auth_client):
    resp = auth_client.get("/admin/stats", auth=("admin", "wrong"))
    assert resp.status_code == 401


def test_admin_stats_last_errors_is_list(auth_client):
    body = _admin_get(auth_client).json()
    assert isinstance(body["last_errors"], list)
