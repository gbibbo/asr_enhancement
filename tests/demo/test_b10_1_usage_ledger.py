"""B10.1 — usage ledger, cap-state derivation, provider-state endpoint."""

from __future__ import annotations

import base64
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient

from libs.asr.schema import ASRResult
from libs.common.demo_settings import DemoSettings
from libs.demo import persistence as p
from libs.demo import usage as u

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
    "DEMO_UPLOAD_RETENTION_HOURS",
    "ASSEMBLYAI_API_KEY",
    "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD",
    "DEMO_EXAMPLES_CONFIG",
    "DEMO_ASSEMBLYAI_DAILY_SOFT_CAP_USD",
    "DEMO_ASSEMBLYAI_WARNING_CAP_USD",
    "DEMO_ASSEMBLYAI_HARD_CAP_USD",
    "DEMO_ASSEMBLYAI_USD_PER_SECOND",
]


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    db = tmp_path / "demo.db"
    p.init_schema(db)
    return db


def _insert_completed(
    db: Path, *, cost: float, when: Optional[datetime] = None, provider: str = u.PROVIDER_ASSEMBLYAI
) -> str:
    return p.insert_usage_ledger(
        db,
        provider=provider,
        audio_duration_seconds=10.0,
        estimated_cost_usd=cost,
        status=u.LEDGER_STATUS_COMPLETED,
        cap_state=u.CAP_BELOW,
        now=(when or datetime.now(timezone.utc)).isoformat(),
    )


def _insert_started(db: Path, *, cost: float) -> str:
    return p.insert_usage_ledger(
        db,
        provider=u.PROVIDER_ASSEMBLYAI,
        audio_duration_seconds=10.0,
        estimated_cost_usd=cost,
        status=u.LEDGER_STATUS_STARTED,
        cap_state=u.CAP_BELOW,
    )


# ---------------------------------------------------------------------------
# Schema regression
# ---------------------------------------------------------------------------


def test_usage_ledger_schema_columns_match_contract(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("PRAGMA table_info(usage_ledger)").fetchall()
    finally:
        conn.close()
    cols = {r[1] for r in rows}
    expected = {
        "ledger_id",
        "provider",
        "session_id_hash",
        "job_id",
        "audio_duration_seconds",
        "estimated_cost_usd",
        "status",
        "cap_state",
        "created_at",
    }
    assert cols == expected


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def test_insert_usage_ledger_returns_hex_id_and_roundtrips(db_path: Path):
    lid = p.insert_usage_ledger(
        db_path,
        provider=u.PROVIDER_ASSEMBLYAI,
        audio_duration_seconds=12.5,
        estimated_cost_usd=0.00125,
        status=u.LEDGER_STATUS_STARTED,
        cap_state=u.CAP_BELOW,
        session_id_hash="abc123",
        job_id="job-7",
    )
    assert isinstance(lid, str) and len(lid) == 32
    int(lid, 16)
    row = p.get_usage_ledger_row(db_path, lid)
    assert row is not None
    assert row["provider"] == u.PROVIDER_ASSEMBLYAI
    assert row["audio_duration_seconds"] == 12.5
    assert row["estimated_cost_usd"] == 0.00125
    assert row["status"] == u.LEDGER_STATUS_STARTED
    assert row["cap_state"] == u.CAP_BELOW
    assert row["session_id_hash"] == "abc123"
    assert row["job_id"] == "job-7"


def test_update_usage_ledger_status_changes_only_status(db_path: Path):
    lid = _insert_started(db_path, cost=0.01)
    before = p.get_usage_ledger_row(db_path, lid)
    p.update_usage_ledger_status(db_path, lid, u.LEDGER_STATUS_COMPLETED)
    after = p.get_usage_ledger_row(db_path, lid)
    assert after["status"] == u.LEDGER_STATUS_COMPLETED
    for col in (
        "ledger_id",
        "cap_state",
        "created_at",
        "estimated_cost_usd",
        "audio_duration_seconds",
        "provider",
    ):
        assert before[col] == after[col]


def test_update_usage_ledger_status_no_match_is_noop(db_path: Path):
    p.update_usage_ledger_status(db_path, uuid.uuid4().hex, u.LEDGER_STATUS_FAILED)


def test_sum_completed_filters_provider_and_status(db_path: Path):
    _insert_completed(db_path, cost=1.0)
    _insert_completed(db_path, cost=2.0)
    _insert_started(db_path, cost=10.0)
    _insert_completed(db_path, cost=99.0, provider="other")
    assert p.sum_completed_usage_cost(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 3.0


def test_sum_reserved_filters_started_only(db_path: Path):
    _insert_completed(db_path, cost=1.0)
    _insert_started(db_path, cost=2.5)
    _insert_started(db_path, cost=0.5)
    assert p.sum_reserved_usage_cost(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 3.0


def test_sum_completed_since_iso_filter(db_path: Path):
    old = datetime.now(timezone.utc) - timedelta(days=2)
    _insert_completed(db_path, cost=1.0, when=old)
    new = datetime.now(timezone.utc)
    _insert_completed(db_path, cost=2.0, when=new)
    cutoff = (new - timedelta(hours=1)).isoformat()
    assert p.sum_completed_usage_cost(
        db_path, provider=u.PROVIDER_ASSEMBLYAI, since_iso=cutoff
    ) == 2.0


def test_count_usage_rows_filters(db_path: Path):
    _insert_completed(db_path, cost=1.0)
    _insert_completed(db_path, cost=1.0)
    _insert_started(db_path, cost=1.0)
    assert p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 3
    assert (
        p.count_usage_rows(
            db_path, provider=u.PROVIDER_ASSEMBLYAI, status=u.LEDGER_STATUS_COMPLETED
        )
        == 2
    )


def test_non_finite_or_negative_cost_treated_as_zero(db_path: Path, caplog):
    p._LEDGER_SUM_WARNED = False  # reset module flag for deterministic logging
    _insert_completed(db_path, cost=1.0)
    # Bypass the helper to insert a corrupt row directly.
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO usage_ledger "
            "(ledger_id, provider, audio_duration_seconds, estimated_cost_usd, "
            " status, cap_state, created_at) "
            "VALUES (?, 'assemblyai', 10.0, ?, 'completed', 'below', ?)",
            (uuid.uuid4().hex, -5.0, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    with caplog.at_level("WARNING", logger="demo-api.persistence"):
        total = p.sum_completed_usage_cost(db_path, provider=u.PROVIDER_ASSEMBLYAI)
    assert total == 1.0
    # Row must still be present (no auto-delete).
    assert p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 2


# ---------------------------------------------------------------------------
# Pure logic
# ---------------------------------------------------------------------------


def test_estimate_cost_usd_zero_duration_is_zero():
    assert u.estimate_cost_usd(0, 0.000103) == 0.0
    assert u.estimate_cost_usd(0.0, 1.5) == 0.0


def test_estimate_cost_usd_negative_duration_raises():
    with pytest.raises(ValueError):
        u.estimate_cost_usd(-0.1, 0.000103)


def test_estimate_cost_usd_non_numeric_raises_typeerror():
    with pytest.raises(TypeError):
        u.estimate_cost_usd("30", 0.000103)
    with pytest.raises(TypeError):
        u.estimate_cost_usd(30.0, "0.000103")
    with pytest.raises(TypeError):
        u.estimate_cost_usd(None, 0.000103)
    with pytest.raises(TypeError):
        u.estimate_cost_usd(True, 0.000103)


def test_estimate_cost_usd_negative_rate_raises_valueerror():
    with pytest.raises(ValueError):
        u.estimate_cost_usd(30.0, -0.000103)


def test_estimate_cost_usd_rounds_six_decimals():
    assert u.estimate_cost_usd(30.0, 0.000103) == round(30 * 0.000103, 6)
    assert u.estimate_cost_usd(1.0, 1 / 7) == round(1 / 7, 6)


@pytest.mark.parametrize(
    "daily,total,expected",
    [
        (0.0, 0.0, u.CAP_BELOW),
        (4.99, 0.0, u.CAP_BELOW),
        (4.99, 34.99, u.CAP_BELOW),
        (4.99, 35.0, u.CAP_WARNING_REACHED),
        (4.99, 44.99, u.CAP_WARNING_REACHED),
        (5.0, 0.0, u.CAP_SOFT_REACHED),
        (5.0, 35.0, u.CAP_SOFT_REACHED),
        (4.99, 45.0, u.CAP_HARD_REACHED),
        (5.0, 45.0, u.CAP_HARD_REACHED),
        (5.0, 50.0, u.CAP_HARD_REACHED),
    ],
)
def test_derive_cap_state_priority(daily, total, expected):
    assert (
        u.derive_cap_state(
            daily,
            total,
            daily_soft_cap_usd=5.0,
            warning_cap_usd=35.0,
            hard_cap_usd=45.0,
        )
        == expected
    )


@pytest.mark.parametrize(
    "key,cap_state,expected",
    [
        (None, u.CAP_BELOW, u.STATE_DISABLED),
        ("", u.CAP_BELOW, u.STATE_DISABLED),
        (None, u.CAP_HARD_REACHED, u.STATE_DISABLED),
        ("k", u.CAP_HARD_REACHED, u.STATE_QUOTA_EXHAUSTED),
        ("k", u.CAP_SOFT_REACHED, u.STATE_DAILY_QUOTA_REACHED),
        ("k", u.CAP_WARNING_REACHED, u.STATE_AVAILABLE),
        ("k", u.CAP_BELOW, u.STATE_AVAILABLE),
    ],
)
def test_derive_provider_state_mapping(key, cap_state, expected):
    assert u.derive_provider_state(key, cap_state) == expected


def test_assemblyai_quota_exhausted_set():
    assert u.assemblyai_quota_exhausted(u.STATE_DAILY_QUOTA_REACHED) is True
    assert u.assemblyai_quota_exhausted(u.STATE_QUOTA_EXHAUSTED) is True
    assert u.assemblyai_quota_exhausted(u.STATE_DISABLED) is True
    assert u.assemblyai_quota_exhausted(u.STATE_AVAILABLE) is False


# ---------------------------------------------------------------------------
# Reservation helper
# ---------------------------------------------------------------------------


def _settings(tmp_path: Path) -> DemoSettings:
    s = DemoSettings(
        demo_runtime_root=tmp_path,
        assemblyai_api_key="dummy-key",
    )
    return s


def _audio(tmp_path: Path) -> Path:
    f = tmp_path / "in.wav"
    f.write_bytes(b"\x00" * 16)
    return f


def _asr_result() -> ASRResult:
    return ASRResult(
        text="hello",
        language="en",
        duration_seconds=10.0,
        segments=[],
        words=[],
        provider="assemblyai",
        provider_job_id="ext-1",
        raw_payload={},
    )


def test_transcribe_with_ledger_happy_path(tmp_path: Path, db_path: Path):
    s = _settings(tmp_path)
    adapter = MagicMock()
    adapter.transcribe.return_value = _asr_result()
    result = u.transcribe_with_ledger(
        adapter,
        _audio(tmp_path),
        "j1",
        db_path=db_path,
        settings=s,
        audio_duration_seconds=10.0,
    )
    assert result.text == "hello"
    adapter.transcribe.assert_called_once()
    rows = p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI)
    assert rows == 1
    completed = p.count_usage_rows(
        db_path, provider=u.PROVIDER_ASSEMBLYAI, status=u.LEDGER_STATUS_COMPLETED
    )
    assert completed == 1


def test_transcribe_with_ledger_blocks_on_soft_cap(tmp_path: Path, db_path: Path):
    s = _settings(tmp_path)
    # Pre-load completed rows summing to >= 5 USD today.
    _insert_completed(db_path, cost=5.0)
    adapter = MagicMock()
    with pytest.raises(u.CapBlockedError) as exc_info:
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=db_path,
            settings=s,
            audio_duration_seconds=10.0,
        )
    assert exc_info.value.cap_state == u.CAP_SOFT_REACHED
    adapter.transcribe.assert_not_called()
    # No new ledger row was inserted by the blocked precheck.
    assert p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 1


def test_transcribe_with_ledger_blocks_on_hard_cap(tmp_path: Path, db_path: Path):
    s = _settings(tmp_path)
    old = datetime.now(timezone.utc) - timedelta(days=10)
    _insert_completed(db_path, cost=45.0, when=old)
    adapter = MagicMock()
    with pytest.raises(u.CapBlockedError) as exc_info:
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=db_path,
            settings=s,
            audio_duration_seconds=10.0,
        )
    assert exc_info.value.cap_state == u.CAP_HARD_REACHED
    adapter.transcribe.assert_not_called()
    assert p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 1


def test_transcribe_with_ledger_warning_continues_and_logs(
    tmp_path: Path, db_path: Path, caplog
):
    s = _settings(tmp_path)
    # Pre-load lifetime completed spend exactly at the warning cap, well below
    # the hard cap, on a day other than today so the soft daily cap is not hit.
    old = datetime.now(timezone.utc) - timedelta(days=10)
    _insert_completed(db_path, cost=35.0, when=old)
    adapter = MagicMock()
    adapter.transcribe.return_value = _asr_result()
    with caplog.at_level("WARNING", logger="demo-api.usage"):
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=db_path,
            settings=s,
            audio_duration_seconds=10.0,
        )
    adapter.transcribe.assert_called_once()
    warnings = [r for r in caplog.records if "assemblyai_warning_cap_projected" in r.getMessage()]
    assert len(warnings) == 1
    # The new row's cap_state should be warning_reached.
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT cap_state, status FROM usage_ledger WHERE status = 'completed' ORDER BY created_at DESC LIMIT 1"
        ).fetchall()
    finally:
        conn.close()
    assert rows[0][0] == u.CAP_WARNING_REACHED


def test_transcribe_with_ledger_db_failure_blocks_call(
    tmp_path: Path, monkeypatch
):
    bad_db = tmp_path / "missing_dir" / "demo.db"  # parent dir does not exist
    s = _settings(tmp_path)
    adapter = MagicMock()
    with pytest.raises(u.LedgerWriteError):
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=bad_db,
            settings=s,
            audio_duration_seconds=10.0,
        )
    adapter.transcribe.assert_not_called()


def test_transcribe_with_ledger_adapter_failure_marks_failed_and_reraises(
    tmp_path: Path, db_path: Path
):
    s = _settings(tmp_path)
    adapter = MagicMock()
    boom = RuntimeError("upstream blew up")
    adapter.transcribe.side_effect = boom
    with pytest.raises(RuntimeError) as exc_info:
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=db_path,
            settings=s,
            audio_duration_seconds=10.0,
        )
    assert exc_info.value is boom
    failed = p.count_usage_rows(
        db_path, provider=u.PROVIDER_ASSEMBLYAI, status=u.LEDGER_STATUS_FAILED
    )
    assert failed == 1


def test_transcribe_with_ledger_negative_duration_blocks_call(
    tmp_path: Path, db_path: Path
):
    s = _settings(tmp_path)
    adapter = MagicMock()
    with pytest.raises(ValueError):
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=db_path,
            settings=s,
            audio_duration_seconds=-1.0,
        )
    adapter.transcribe.assert_not_called()
    assert p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 0


def test_transcribe_with_ledger_non_numeric_duration_blocks_call(
    tmp_path: Path, db_path: Path
):
    s = _settings(tmp_path)
    adapter = MagicMock()
    with pytest.raises(TypeError):
        u.transcribe_with_ledger(
            adapter,
            _audio(tmp_path),
            "j1",
            db_path=db_path,
            settings=s,
            audio_duration_seconds="30",  # type: ignore[arg-type]
        )
    adapter.transcribe.assert_not_called()
    assert p.count_usage_rows(db_path, provider=u.PROVIDER_ASSEMBLYAI) == 0


def test_cap_blocked_error_rejects_invalid_cap_state():
    with pytest.raises(ValueError):
        u.CapBlockedError(u.CAP_WARNING_REACHED)
    with pytest.raises(ValueError):
        u.CapBlockedError(u.CAP_BELOW)


# ---------------------------------------------------------------------------
# Public + admin endpoints
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from services.api.app.demo_main import app

    with TestClient(app) as test_client:
        yield test_client


def _db(client: TestClient) -> Path:
    return client.app.state.settings.demo_db_path


def test_public_endpoint_disabled_when_no_key(client: TestClient):
    body = client.get("/demo/providers/assemblyai/status").json()
    assert body == {
        "assemblyai": {
            "state": u.STATE_DISABLED,
            "cap_state": u.CAP_BELOW,
        }
    }


def test_public_endpoint_available_when_key_present_and_no_spend(
    tmp_path, monkeypatch
):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test-key")
    from services.api.app.demo_main import app

    with TestClient(app) as c:
        body = c.get("/demo/providers/assemblyai/status").json()
    assert body == {
        "assemblyai": {
            "state": u.STATE_AVAILABLE,
            "cap_state": u.CAP_BELOW,
        }
    }


def test_public_endpoint_soft_cap(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test-key")
    from services.api.app.demo_main import app

    with TestClient(app) as c:
        _insert_completed(c.app.state.settings.demo_db_path, cost=5.0)
        body = c.get("/demo/providers/assemblyai/status").json()
    assert body == {
        "assemblyai": {
            "state": u.STATE_DAILY_QUOTA_REACHED,
            "cap_state": u.CAP_SOFT_REACHED,
        }
    }


def test_public_endpoint_hard_cap(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test-key")
    from services.api.app.demo_main import app

    with TestClient(app) as c:
        old = datetime.now(timezone.utc) - timedelta(days=10)
        _insert_completed(c.app.state.settings.demo_db_path, cost=45.0, when=old)
        body = c.get("/demo/providers/assemblyai/status").json()
    assert body == {
        "assemblyai": {
            "state": u.STATE_QUOTA_EXHAUSTED,
            "cap_state": u.CAP_HARD_REACHED,
        }
    }


def test_public_endpoint_payload_only_two_keys(client: TestClient):
    body = client.get("/demo/providers/assemblyai/status").json()
    assert list(body.keys()) == ["assemblyai"]
    assert set(body["assemblyai"].keys()) == {"state", "cap_state"}
    forbidden = {
        "daily_usd",
        "total_usd",
        "reserved_usd",
        "daily_soft_cap_usd",
        "warning_cap_usd",
        "hard_cap_usd",
        "usd_per_second_estimate",
        "daily_remaining_usd",
        "key_configured",
        "as_of",
        "job_id",
        "session_id_hash",
    }
    assert forbidden.isdisjoint(body["assemblyai"].keys())


# /admin/stats
_USER = "admin"
_PASS = "secret-test-password"


def _basic(user: str, pwd: str) -> dict:
    raw = f"{user}:{pwd}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode()}


def test_admin_stats_unauthenticated_returns_401(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ADMIN_STATS_PASSWORD", _PASS)
    from services.api.app.demo_main import app

    with TestClient(app) as c:
        resp = c.get("/admin/stats")
    assert resp.status_code == 401


def test_admin_stats_includes_provider_state_block(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ADMIN_STATS_PASSWORD", _PASS)
    from services.api.app.demo_main import app

    with TestClient(app) as c:
        resp = c.get("/admin/stats", headers=_basic(_USER, _PASS))
    assert resp.status_code == 200
    body = resp.json()
    assert "provider_state" in body
    aa = body["provider_state"]["assemblyai"]
    expected_keys = {
        "state",
        "cap_state",
        "key_configured",
        "daily_usd",
        "total_usd",
        "reserved_usd",
        "daily_soft_cap_usd",
        "warning_cap_usd",
        "hard_cap_usd",
        "usd_per_second_estimate",
        "as_of",
    }
    assert set(aa.keys()) == expected_keys
    assert aa["key_configured"] is False
    assert aa["state"] == u.STATE_DISABLED
    assert aa["cap_state"] == u.CAP_BELOW
    assert aa["daily_soft_cap_usd"] == 5.0
    assert aa["warning_cap_usd"] == 35.0
    assert aa["hard_cap_usd"] == 45.0
    assert aa["usd_per_second_estimate"] == 0.000103


def test_admin_stats_does_not_echo_api_key_string(tmp_path, monkeypatch):
    secret = "super-secret-key-XYZ"
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ADMIN_STATS_PASSWORD", _PASS)
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", secret)
    from services.api.app.demo_main import app

    with TestClient(app) as c:
        resp = c.get("/admin/stats", headers=_basic(_USER, _PASS))
    assert resp.status_code == 200
    assert secret not in resp.text
    body = resp.json()
    assert body["provider_state"]["assemblyai"]["key_configured"] is True


# ---------------------------------------------------------------------------
# Compose env propagation (parse-time only, no subprocess)
# ---------------------------------------------------------------------------


def test_compose_env_whitelist_includes_new_keys():
    """Validates that the compose file propagates the four new env keys with
    explicit numeric defaults. Skipped if the compose file is not visible to
    the test process (e.g. when run inside a container that does not bind-mount
    ``infra/``); Stage 0 of the validation runbook also checks this end-to-end.
    """
    compose_path = Path("infra/compose/docker-compose.demo.yml")
    if not compose_path.exists():
        pytest.skip(
            "infra/compose/docker-compose.demo.yml not visible (bind-mount infra/ to enable)"
        )
    data = yaml.safe_load(compose_path.read_text())
    env = data["x-demo-env"]
    assert "DEMO_ASSEMBLYAI_DAILY_SOFT_CAP_USD" in env
    assert "DEMO_ASSEMBLYAI_WARNING_CAP_USD" in env
    assert "DEMO_ASSEMBLYAI_HARD_CAP_USD" in env
    assert "DEMO_ASSEMBLYAI_USD_PER_SECOND" in env
    # Defaults must be numeric, not empty.
    assert env["DEMO_ASSEMBLYAI_DAILY_SOFT_CAP_USD"].endswith(":-5.0}")
    assert env["DEMO_ASSEMBLYAI_WARNING_CAP_USD"].endswith(":-35.0}")
    assert env["DEMO_ASSEMBLYAI_HARD_CAP_USD"].endswith(":-45.0}")
    assert env["DEMO_ASSEMBLYAI_USD_PER_SECOND"].endswith(":-0.000103}")
