"""B10.2 — upload-specific AssemblyAI rules.

Covers the API pre-queue gate (provider validation, provider-state ordering,
session header, de-duplicated 3 uses / 24h limit, defense-in-depth duration),
the worker integration with ``transcribe_with_ledger``, the bypass second-call
optimization, the idempotent ``jobs.session_id_hash`` migration, and every
privacy contract on the public/admin endpoints.

No AssemblyAI network call is made anywhere in this suite.
``DemoAssemblyAIAdapter.transcribe`` is patched to return a deterministic
``ASRResult``.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import sqlite3
import uuid
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from libs.asr.errors import AdapterTimeoutError
from libs.asr.schema import ASRResult


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
    "DEMO_ASSEMBLYAI_DAILY_SOFT_CAP_USD",
    "DEMO_ASSEMBLYAI_WARNING_CAP_USD",
    "DEMO_ASSEMBLYAI_HARD_CAP_USD",
    "DEMO_ASSEMBLYAI_USD_PER_SECOND",
]


def _clear_demo_env(monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _wav_bytes(seconds: float = 1.0, samplerate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(b"\x00\x00" * int(round(seconds * samplerate)))
    return buf.getvalue()


def _write_wav(path: Path, seconds: float = 1.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_wav_bytes(seconds))
    return path


def _hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def _settings_of(client: TestClient):
    return client.app.state.settings


def _db_of(client: TestClient) -> Path:
    return _settings_of(client).demo_db_path


def _upload_dir_of(client: TestClient) -> Path:
    return _settings_of(client).demo_upload_dir


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings(tmp_path, monkeypatch):
    _clear_demo_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from libs.common.demo_settings import DemoSettings
    return DemoSettings()


@pytest.fixture()
def db_path(settings):
    from libs.demo.persistence import ensure_runtime_dirs, init_schema
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    return settings.demo_db_path


@pytest.fixture()
def client(tmp_path, monkeypatch):
    _clear_demo_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client_with_key(tmp_path, monkeypatch):
    _clear_demo_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "sk-test-fake-not-real")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------


def _seed_ledger(
    db_path: Path,
    *,
    session_id_hash: str,
    status: str,
    job_id: Optional[str] = None,
    minutes_ago: float = 1.0,
    cost: float = 0.001,
    cap_state: str = "below",
) -> str:
    from libs.demo.persistence import insert_usage_ledger
    iso = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    return insert_usage_ledger(
        db_path,
        provider="assemblyai",
        audio_duration_seconds=10.0,
        estimated_cost_usd=cost,
        status=status,
        cap_state=cap_state,
        session_id_hash=session_id_hash,
        job_id=job_id,
        now=iso,
    )


def _seed_job(
    db_path: Path,
    *,
    session_id_hash: Optional[str],
    provider: str = "assemblyai",
    status: str = "queued",
    minutes_ago: float = 1.0,
    job_id: Optional[str] = None,
) -> str:
    job_id = job_id or str(uuid.uuid4())
    iso = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            INSERT INTO jobs
              (job_id, status, created_at, updated_at, provider,
               degradation_id, enhancer_version, input_artifact_path,
               session_id_hash)
            VALUES (?, ?, ?, ?, ?, NULL, 'bypass', NULL, ?)
            """,
            (job_id, status, iso, iso, provider, session_id_hash),
        )
        conn.commit()
    finally:
        conn.close()
    return job_id


def _make_asr_result(text: str = "hello world") -> ASRResult:
    return ASRResult(
        text=text,
        language="en",
        duration_seconds=1.0,
        segments=[],
        words=[],
        provider="assemblyai",
        provider_job_id="t-1",
        raw_payload={"id": "t-1"},
    )


def _seed_upload_job(
    db_path: Path,
    upload_dir: Path,
    *,
    session_id_hash: Optional[str],
    provider: str = "assemblyai",
) -> dict:
    job_id = str(uuid.uuid4())
    audio = upload_dir / f"{job_id}.wav"
    _write_wav(audio, 1.0)
    iso = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            INSERT INTO jobs
              (job_id, status, created_at, updated_at, provider,
               degradation_id, enhancer_version, input_artifact_path,
               session_id_hash)
            VALUES (?, 'queued', ?, ?, ?, NULL, 'bypass', ?, ?)
            """,
            (job_id, iso, iso, provider, str(audio), session_id_hash),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "job_id": job_id,
        "status": "queued",
        "created_at": iso,
        "updated_at": iso,
        "provider": provider,
        "degradation_id": None,
        "enhancer_version": "bypass",
        "input_artifact_path": str(audio),
        "session_id_hash": session_id_hash,
    }


# ---------------------------------------------------------------------------
# Section 1 — Provider validation and gate ordering
# ---------------------------------------------------------------------------


def test_unsupported_provider_returns_422_and_unlinks(client):
    from libs.demo.persistence import count_active_jobs, count_usage_rows

    upload_dir = _upload_dir_of(client)
    pre = sorted(p.name for p in upload_dir.iterdir())
    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post("/demo/upload", files=files, data={"provider": "madeup"})
    assert resp.status_code == 422
    assert "Unsupported provider 'madeup'" in resp.json()["detail"]

    assert sorted(p.name for p in upload_dir.iterdir()) == pre
    assert count_active_jobs(_db_of(client)) == 0
    assert count_usage_rows(_db_of(client), provider="assemblyai") == 0


def test_assemblyai_no_key_returns_400_disabled(client):
    from libs.demo.persistence import count_active_jobs, count_usage_rows
    from libs.demo.usage import MSG_DISABLED

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == MSG_DISABLED
    assert sorted(_upload_dir_of(client).iterdir()) == []
    assert count_active_jobs(_db_of(client)) == 0
    assert count_usage_rows(_db_of(client), provider="assemblyai") == 0


def test_assemblyai_state_disabled_short_circuits_before_session_header(client):
    """State check fires even when the header is also missing."""
    from libs.demo.usage import MSG_DISABLED

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == MSG_DISABLED


def test_assemblyai_soft_cap_returns_503_daily_quota(client_with_key):
    from libs.demo.persistence import count_active_jobs, count_usage_rows
    from libs.demo.usage import MSG_DAILY_QUOTA_REACHED

    _seed_ledger(
        _db_of(client_with_key),
        session_id_hash=_hash("anyone"),
        status="completed",
        cost=5.5,
        cap_state="soft_reached",
    )

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == MSG_DAILY_QUOTA_REACHED
    assert sorted(_upload_dir_of(client_with_key).iterdir()) == []
    assert count_active_jobs(_db_of(client_with_key)) == 0
    assert count_usage_rows(_db_of(client_with_key), provider="assemblyai") == 1


def test_assemblyai_hard_cap_returns_503_quota_exhausted(client_with_key):
    from libs.demo.usage import MSG_HARD_QUOTA_EXHAUSTED

    _seed_ledger(
        _db_of(client_with_key),
        session_id_hash=_hash("anyone"),
        status="completed",
        cost=46.0,
        cap_state="hard_reached",
    )

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == MSG_HARD_QUOTA_EXHAUSTED
    assert sorted(_upload_dir_of(client_with_key).iterdir()) == []


def test_assemblyai_state_check_fires_before_session_header(client_with_key):
    """When the cap is at hard, the user gets the cap message even with no header."""
    from libs.demo.usage import MSG_HARD_QUOTA_EXHAUSTED

    _seed_ledger(
        _db_of(client_with_key),
        session_id_hash=_hash("anyone"),
        status="completed",
        cost=46.0,
        cap_state="hard_reached",
    )

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        # no X-Demo-Session-Id
    )
    assert resp.status_code == 503
    assert resp.json()["detail"] == MSG_HARD_QUOTA_EXHAUSTED


def test_assemblyai_missing_session_header_returns_400(client_with_key):
    from libs.demo.persistence import count_active_jobs, count_usage_rows
    from libs.demo.usage import MSG_SESSION_HEADER_REQUIRED

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == MSG_SESSION_HEADER_REQUIRED
    assert sorted(_upload_dir_of(client_with_key).iterdir()) == []
    assert count_active_jobs(_db_of(client_with_key)) == 0
    assert count_usage_rows(_db_of(client_with_key), provider="assemblyai") == 0


def test_assemblyai_empty_session_header_returns_400(client_with_key):
    from libs.demo.usage import MSG_SESSION_HEADER_REQUIRED

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": ""},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == MSG_SESSION_HEADER_REQUIRED


def test_whisper_does_not_require_session_header(client):
    from libs.demo.persistence import count_active_jobs

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post(
        "/demo/upload",
        files=files,
        data={"provider": "whisper"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"
    assert "job_id" in body
    assert count_active_jobs(_db_of(client)) == 1


# ---------------------------------------------------------------------------
# Section 2 — De-duplicated session count (3 uses / 24h)
# ---------------------------------------------------------------------------


def test_dedup_zero_ledger_zero_pending_allows(db_path):
    from libs.demo.persistence import count_effective_session_assemblyai_uses
    from libs.demo.usage import rolling_24h_start_iso

    n = count_effective_session_assemblyai_uses(
        db_path, session_id_hash=_hash("s"), since_iso=rolling_24h_start_iso()
    )
    assert n == 0


def test_dedup_two_completed_no_pending_allows(db_path):
    from libs.demo.persistence import count_effective_session_assemblyai_uses
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    _seed_ledger(db_path, session_id_hash=h, status="completed")
    _seed_ledger(db_path, session_id_hash=h, status="completed")
    assert count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h, since_iso=rolling_24h_start_iso()
    ) == 2


def test_dedup_three_completed_rejects_with_429(client_with_key):
    from libs.demo.persistence import count_active_jobs
    from libs.demo.usage import MSG_SESSION_LIMIT_REACHED

    h = _hash("browser-1")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_ledger(db, session_id_hash=h, status="completed")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 429
    assert resp.json()["detail"] == MSG_SESSION_LIMIT_REACHED
    assert sorted(_upload_dir_of(client_with_key).iterdir()) == []
    assert count_active_jobs(db) == 0


def test_dedup_two_completed_plus_one_queued_rejects(client_with_key):
    from libs.demo.usage import MSG_SESSION_LIMIT_REACHED

    h = _hash("browser-1")
    db = _db_of(client_with_key)
    _seed_ledger(db, session_id_hash=h, status="completed")
    _seed_ledger(db, session_id_hash=h, status="completed")
    _seed_job(db, session_id_hash=h, status="queued")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 429
    assert resp.json()["detail"] == MSG_SESSION_LIMIT_REACHED


def test_dedup_three_queued_assemblyai_jobs_rejects(client_with_key):
    from libs.demo.usage import MSG_SESSION_LIMIT_REACHED

    h = _hash("browser-1")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_job(db, session_id_hash=h, status="queued")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 429
    assert resp.json()["detail"] == MSG_SESSION_LIMIT_REACHED


def test_dedup_running_with_started_ledger_counts_once(db_path):
    """Job A running + 1 started ledger row for job A → effective=1."""
    from libs.demo.persistence import count_effective_session_assemblyai_uses
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    job_id = _seed_job(db_path, session_id_hash=h, status="running")
    _seed_ledger(db_path, session_id_hash=h, status="started", job_id=job_id)

    n = count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h, since_iso=rolling_24h_start_iso()
    )
    assert n == 1


def test_dedup_completed_plus_running_with_started_counts_two(db_path):
    """1 completed ledger + 1 started ledger for running job A + job A running → effective=2."""
    from libs.demo.persistence import count_effective_session_assemblyai_uses
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    _seed_ledger(db_path, session_id_hash=h, status="completed")
    job_id = _seed_job(db_path, session_id_hash=h, status="running")
    _seed_ledger(db_path, session_id_hash=h, status="started", job_id=job_id)

    n = count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h, since_iso=rolling_24h_start_iso()
    )
    assert n == 2


def test_dedup_two_completed_plus_running_with_started_blocks_next_upload(
    client_with_key,
):
    from libs.demo.usage import MSG_SESSION_LIMIT_REACHED

    h = _hash("browser-1")
    db = _db_of(client_with_key)
    _seed_ledger(db, session_id_hash=h, status="completed")
    _seed_ledger(db, session_id_hash=h, status="completed")
    job_id = _seed_job(db, session_id_hash=h, status="running")
    _seed_ledger(db, session_id_hash=h, status="started", job_id=job_id)

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 429
    assert resp.json()["detail"] == MSG_SESSION_LIMIT_REACHED


def test_dedup_queued_assemblyai_with_completed_ledger_sharing_job_id(db_path):
    """A queued job whose job_id already has a completed ledger row counts once."""
    from libs.demo.persistence import count_effective_session_assemblyai_uses
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    job_id = _seed_job(db_path, session_id_hash=h, status="queued")
    _seed_ledger(db_path, session_id_hash=h, status="completed", job_id=job_id)

    n = count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h, since_iso=rolling_24h_start_iso()
    )
    assert n == 1


def test_dedup_whisper_jobs_do_not_count(client_with_key):
    h = _hash("browser-1")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_job(db, session_id_hash=h, provider="whisper", status="queued")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 202


def test_dedup_other_session_does_not_count(client_with_key):
    other = _hash("browser-other")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_job(db, session_id_hash=other, status="queued")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 202


def test_dedup_failed_ledger_rows_do_not_count(client_with_key):
    h = _hash("browser-1")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_ledger(db, session_id_hash=h, status="failed")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 202


def test_dedup_completed_jobs_do_not_count(client_with_key):
    """A jobs row in 'completed' status without a paired ledger row does not consume quota."""
    h = _hash("browser-1")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_job(db, session_id_hash=h, status="completed")

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 202


def test_dedup_old_rows_outside_24h_window_do_not_count(client_with_key):
    h = _hash("browser-1")
    db = _db_of(client_with_key)
    for _ in range(3):
        _seed_ledger(
            db,
            session_id_hash=h,
            status="completed",
            minutes_ago=25 * 60,
        )

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 202


def test_dedup_boundary_at_24h_inclusive(db_path):
    """Rows whose created_at is exactly now-24h are still counted (created_at >= since)."""
    from libs.demo.persistence import (
        count_effective_session_assemblyai_uses,
        insert_usage_ledger,
    )
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    boundary_iso = rolling_24h_start_iso()
    insert_usage_ledger(
        db_path,
        provider="assemblyai",
        audio_duration_seconds=10.0,
        estimated_cost_usd=0.001,
        status="completed",
        cap_state="below",
        session_id_hash=h,
        now=boundary_iso,
    )
    n = count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h, since_iso=boundary_iso
    )
    assert n == 1


def test_dedup_session_helper_wrappers_independently(db_path):
    """Both half-helpers behave correctly in isolation."""
    from libs.demo.persistence import (
        count_pending_session_assemblyai_jobs,
        count_session_assemblyai_usage,
    )
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    _seed_ledger(db_path, session_id_hash=h, status="completed")
    _seed_job(db_path, session_id_hash=h, status="queued")
    _seed_job(db_path, session_id_hash=h, status="completed")  # not counted

    since = rolling_24h_start_iso()
    assert count_session_assemblyai_usage(
        db_path, session_id_hash=h, since_iso=since
    ) == 1
    assert count_pending_session_assemblyai_jobs(
        db_path, session_id_hash=h, since_iso=since
    ) == 1


# ---------------------------------------------------------------------------
# Section 3 — Migration and idempotency
# ---------------------------------------------------------------------------


def test_init_schema_adds_session_id_hash_to_old_jobs_table(settings):
    """Idempotent ALTER TABLE adds the column to a pre-B10.2 jobs table."""
    from libs.demo.persistence import ensure_runtime_dirs, init_schema

    ensure_runtime_dirs(settings)
    db = settings.demo_db_path
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            provider TEXT NOT NULL,
            degradation_id TEXT,
            enhancer_version TEXT,
            input_artifact_path TEXT,
            degraded_artifact_path TEXT,
            enhanced_artifact_path TEXT,
            result_json TEXT,
            error_message TEXT,
            expires_at TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()

    init_schema(db)

    conn = sqlite3.connect(str(db))
    cols = {row[1]: row for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    conn.close()
    assert "session_id_hash" in cols
    assert cols["session_id_hash"][2] == "TEXT"
    assert cols["session_id_hash"][3] == 0  # nullable


def test_init_schema_idempotent_on_already_migrated_db(db_path):
    """Running init_schema twice does not duplicate the column or raise."""
    from libs.demo.persistence import init_schema

    init_schema(db_path)  # second call
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("PRAGMA table_info(jobs)").fetchall()
    conn.close()
    names = [r[1] for r in rows]
    assert names.count("session_id_hash") == 1


def test_try_create_job_round_trip_with_session_id_hash(settings, db_path):
    from libs.demo.persistence import get_job, try_create_job

    job_id = try_create_job(
        db_path,
        queue_max=settings.demo_queue_max,
        provider="assemblyai",
        session_id_hash="abc",
    )
    row = get_job(db_path, job_id)
    assert row is not None
    assert row["session_id_hash"] == "abc"


def test_fresh_db_has_session_id_hash_column(db_path):
    """Fresh DB created via init_schema includes the column directly."""
    conn = sqlite3.connect(str(db_path))
    cols = [r[1] for r in conn.execute("PRAGMA table_info(jobs)").fetchall()]
    conn.close()
    assert "session_id_hash" in cols


def test_migrated_null_rows_do_not_match_active_session_hash(db_path):
    from libs.demo.persistence import count_effective_session_assemblyai_uses
    from libs.demo.usage import rolling_24h_start_iso

    for _ in range(3):
        _seed_job(db_path, session_id_hash=None, status="queued")

    n = count_effective_session_assemblyai_uses(
        db_path, session_id_hash=_hash("browser-1"), since_iso=rolling_24h_start_iso()
    )
    assert n == 0


# ---------------------------------------------------------------------------
# Section 4 — Privacy / leak-proofing
# ---------------------------------------------------------------------------


def test_get_demo_job_does_not_expose_session_id_hash(client_with_key):
    """After an AssemblyAI upload, /demo/jobs/{id} must not echo session_id_hash."""
    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-secret"},
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    detail = client_with_key.get(f"/demo/jobs/{job_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert "session_id_hash" not in body
    blob = json.dumps(body)
    assert _hash("browser-secret") not in blob
    assert "browser-secret" not in blob


def test_get_demo_job_result_does_not_expose_session_id_hash(client_with_key):
    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-secret"},
    )
    job_id = resp.json()["job_id"]

    pending = client_with_key.get(f"/demo/jobs/{job_id}/result")
    # 202 because queued, no worker running in TestClient context.
    assert pending.status_code == 202
    body = pending.json()
    assert "session_id_hash" not in body
    blob = json.dumps(body)
    assert _hash("browser-secret") not in blob
    assert "browser-secret" not in blob


def test_public_provider_status_payload_remains_two_keys_only(client):
    """Exact-key-set assertion against the live FastAPI TestClient."""
    resp = client.get("/demo/providers/assemblyai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"assemblyai"}
    inner = body["assemblyai"]
    assert set(inner.keys()) == {"state", "cap_state"}
    assert inner["state"] in {
        "available", "daily_quota_reached", "quota_exhausted", "disabled",
    }
    assert inner["cap_state"] in {
        "below", "warning_reached", "soft_reached", "hard_reached",
    }


def test_no_session_id_in_logs_after_assemblyai_upload(client_with_key, caplog):
    """Neither the plain header value nor its hash appears in any captured log line."""
    caplog.set_level(logging.DEBUG)
    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-secret"},
    )
    assert resp.status_code == 202

    for record in caplog.records:
        msg = record.getMessage()
        assert "browser-secret" not in msg
        assert _hash("browser-secret") not in msg


# ---------------------------------------------------------------------------
# Section 5 — Worker / transcribe_with_ledger integration
# ---------------------------------------------------------------------------


def test_worker_assemblyai_creates_one_completed_ledger_row(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.persistence import count_usage_rows
    from libs.demo.processing import process_upload_job

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    class _StubAdapter:
        def transcribe(self, audio_path, job_id):
            return _make_asr_result()

    outcome = process_upload_job(
        job, settings,
        asr_factory=lambda _name: _StubAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "completed"
    assert count_usage_rows(db_path, provider="assemblyai", status="completed") == 1
    assert count_usage_rows(db_path, provider="assemblyai", status="started") == 0
    assert count_usage_rows(db_path, provider="assemblyai", status="failed") == 0


def test_worker_bypass_optimization_avoids_duplicate_ledger_row(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.persistence import count_usage_rows
    from libs.demo.processing import process_upload_job

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    calls = []

    class _StubAdapter:
        def transcribe(self, audio_path, job_id):
            calls.append(audio_path)
            return _make_asr_result()

    outcome = process_upload_job(
        job, settings,
        asr_factory=lambda _name: _StubAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "completed"
    assert len(calls) == 1
    assert count_usage_rows(db_path, provider="assemblyai") == 1


def test_worker_adapter_timeout_marks_ledger_failed_and_job_failed(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.persistence import count_usage_rows
    from libs.demo.processing import process_upload_job

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    class _BoomAdapter:
        def transcribe(self, audio_path, job_id):
            raise AdapterTimeoutError("upstream timeout")

    outcome = process_upload_job(
        job, settings,
        asr_factory=lambda _name: _BoomAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "failed"
    assert count_usage_rows(db_path, provider="assemblyai", status="failed") == 1
    assert count_usage_rows(db_path, provider="assemblyai", status="completed") == 0


def test_worker_cap_blocked_during_call_marks_job_failed(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.persistence import count_usage_rows, insert_usage_ledger
    from libs.demo.processing import process_upload_job
    from libs.demo.usage import MSG_DAILY_QUOTA_REACHED

    insert_usage_ledger(
        db_path,
        provider="assemblyai",
        audio_duration_seconds=10.0,
        estimated_cost_usd=5.5,
        status="completed",
        cap_state="soft_reached",
    )

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    class _StubAdapter:
        def transcribe(self, audio_path, job_id):
            raise AssertionError("adapter must not be called when cap blocks")

    outcome = process_upload_job(
        job, settings,
        asr_factory=lambda _name: _StubAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "failed"
    assert outcome.error_message == MSG_DAILY_QUOTA_REACHED
    # No new usage_ledger row created by the blocked reservation.
    assert count_usage_rows(db_path, provider="assemblyai") == 1


def test_worker_ledger_write_failure_returns_unavailable(
    settings, db_path, monkeypatch
):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo import processing as proc
    from libs.demo.usage import LedgerWriteError, MSG_LEDGER_UNAVAILABLE

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    def _boom(*args, **kwargs):
        raise LedgerWriteError("simulated DB write failure")

    monkeypatch.setattr(proc, "transcribe_with_ledger", _boom)

    class _StubAdapter:
        def transcribe(self, audio_path, job_id):
            raise AssertionError("adapter must not be called")

    outcome = proc.process_upload_job(
        job, settings,
        asr_factory=lambda _name: _StubAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )
    assert outcome.status == "failed"
    assert outcome.error_message == MSG_LEDGER_UNAVAILABLE


def test_asr_model_version_universal_for_assemblyai():
    from libs.demo.processing import (
        ASSEMBLYAI_MODEL_VERSION,
        DEFAULT_WHISPER_MODEL_VERSION,
        _asr_model_version,
    )

    a = ASRResult(
        text="x", language="en", duration_seconds=None, segments=[], words=[],
        provider="assemblyai", provider_job_id=None, raw_payload={},
    )
    assert _asr_model_version("assemblyai", a) == ASSEMBLYAI_MODEL_VERSION
    assert ASSEMBLYAI_MODEL_VERSION == "universal"

    w_named = ASRResult(
        text="x", language="en", duration_seconds=None, segments=[], words=[],
        provider="whisper", provider_job_id=None, raw_payload={"model": "tiny.en"},
    )
    assert _asr_model_version("whisper", w_named) == "tiny.en"

    w_default = ASRResult(
        text="x", language="en", duration_seconds=None, segments=[], words=[],
        provider="whisper", provider_job_id=None, raw_payload={},
    )
    assert _asr_model_version("whisper", w_default) == DEFAULT_WHISPER_MODEL_VERSION


# ---------------------------------------------------------------------------
# Section 6 — result_json shape and forbidden fields
# ---------------------------------------------------------------------------


_FORBIDDEN_RESULT_KEYS = (
    "session_id",
    "session_id_hash",
    "ledger_id",
    "ground_truth",
    "gt",
    "reference_text",
    "wer",
    "cer",
    "word_accuracy",
)


def _walk_keys(obj, hits):
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits.add(k)
            _walk_keys(v, hits)
    elif isinstance(obj, list):
        for x in obj:
            _walk_keys(x, hits)


def test_assemblyai_result_json_shape_and_no_forbidden_fields(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    class _StubAdapter:
        def transcribe(self, audio_path, job_id):
            return _make_asr_result(text="hello universe")

    outcome = process_upload_job(
        job, settings,
        asr_factory=lambda _name: _StubAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )
    assert outcome.status == "completed"
    r = outcome.result
    assert r["provider"] == "assemblyai"
    assert r["asr_model_version"] == "universal"
    assert r["metrics"] == {}
    assert r["raw"]["transcript"] == "hello universe"
    assert r["enhanced"]["transcript"] == "hello universe"

    keys: set[str] = set()
    _walk_keys(r, keys)
    for forbidden in _FORBIDDEN_RESULT_KEYS:
        assert forbidden not in keys, f"forbidden key leaked: {forbidden!r}"


def test_assemblyai_result_does_not_mention_whisper_fallback(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    h = _hash("browser-1")
    job = _seed_upload_job(db_path, settings.demo_upload_dir, session_id_hash=h)

    class _StubAdapter:
        def transcribe(self, audio_path, job_id):
            return _make_asr_result()

    outcome = process_upload_job(
        job, settings,
        asr_factory=lambda _name: _StubAdapter(),
        enhancer_factory=lambda _v: BypassEnhancer(),
        update_artifacts=lambda **kw: None,
    )
    assert outcome.result["provider"] == "assemblyai"
    blob = json.dumps(outcome.result)
    assert "whisper" not in blob.lower()


# ---------------------------------------------------------------------------
# Section 7 — Defense-in-depth duration check
# ---------------------------------------------------------------------------


def test_b9_1_duration_cap_fires_before_assemblyai_gate(client_with_key):
    """A 31 s upload is rejected by B9.1 before the AssemblyAI gate runs."""
    files = {"file": ("long.wav", _wav_bytes(31.0), "audio/wav")}
    resp = client_with_key.post(
        "/demo/upload",
        files=files,
        data={"provider": "assemblyai"},
        headers={"X-Demo-Session-Id": "browser-1"},
    )
    assert resp.status_code == 422
    assert "30 seconds" in resp.json()["detail"].lower()
    assert sorted(_upload_dir_of(client_with_key).iterdir()) == []


# ---------------------------------------------------------------------------
# Section 8 — Whisper sanity (B9.x regression)
# ---------------------------------------------------------------------------


def test_whisper_upload_is_unaffected_by_b10_2(client):
    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post("/demo/upload", files=files, data={"provider": "whisper"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "queued"


def test_whisper_job_stores_null_session_id_hash(client):
    from libs.demo.persistence import get_job

    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post(
        "/demo/upload",
        files=files,
        data={"provider": "whisper"},
        headers={"X-Demo-Session-Id": "ignored-by-whisper"},
    )
    assert resp.status_code == 202
    job = get_job(_db_of(client), resp.json()["job_id"])
    assert job is not None
    assert job["session_id_hash"] is None


def test_get_demo_job_for_whisper_has_no_session_id_hash_field(client):
    files = {"file": ("clip.wav", _wav_bytes(1.0), "audio/wav")}
    resp = client.post("/demo/upload", files=files, data={"provider": "whisper"})
    job_id = resp.json()["job_id"]

    detail = client.get(f"/demo/jobs/{job_id}")
    assert detail.status_code == 200
    assert "session_id_hash" not in detail.json()


def test_dedup_helpers_filter_by_session_strict(db_path):
    """Helpers must scope by session_id_hash and not bleed across sessions."""
    from libs.demo.persistence import (
        count_effective_session_assemblyai_uses,
        count_pending_session_assemblyai_jobs,
        count_session_assemblyai_usage,
    )
    from libs.demo.usage import rolling_24h_start_iso

    h_a = _hash("a")
    h_b = _hash("b")
    _seed_ledger(db_path, session_id_hash=h_a, status="completed")
    _seed_job(db_path, session_id_hash=h_a, status="queued")
    _seed_ledger(db_path, session_id_hash=h_b, status="completed")
    _seed_job(db_path, session_id_hash=h_b, status="running")

    since = rolling_24h_start_iso()

    assert count_session_assemblyai_usage(
        db_path, session_id_hash=h_a, since_iso=since
    ) == 1
    assert count_pending_session_assemblyai_jobs(
        db_path, session_id_hash=h_a, since_iso=since
    ) == 1
    assert count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h_a, since_iso=since
    ) == 2  # both rows are independent (no shared job_id)
    assert count_effective_session_assemblyai_uses(
        db_path, session_id_hash=h_b, since_iso=since
    ) == 2


def test_count_pending_excludes_completed_and_failed_jobs(db_path):
    """count_pending must only see queued/running."""
    from libs.demo.persistence import count_pending_session_assemblyai_jobs
    from libs.demo.usage import rolling_24h_start_iso

    h = _hash("browser-1")
    _seed_job(db_path, session_id_hash=h, status="queued")
    _seed_job(db_path, session_id_hash=h, status="running")
    _seed_job(db_path, session_id_hash=h, status="completed")
    _seed_job(db_path, session_id_hash=h, status="failed")

    n = count_pending_session_assemblyai_jobs(
        db_path, session_id_hash=h, since_iso=rolling_24h_start_iso()
    )
    assert n == 2  # only queued + running


def test_session_id_hash_is_64_hex_chars():
    h = _hash("browser-some-id")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_assemblyai_factory_returns_demo_adapter_when_key_set(settings, monkeypatch):
    from libs.asr.demo_assemblyai_provider import DemoAssemblyAIAdapter
    from libs.demo.processing import default_asr_factory

    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "sk-fake-not-real")
    from libs.common.demo_settings import DemoSettings
    s = DemoSettings()
    factory = default_asr_factory(s)
    adapter = factory("assemblyai")
    assert isinstance(adapter, DemoAssemblyAIAdapter)


def test_default_asr_factory_no_key_raises_disabled(settings):
    from libs.demo.processing import ProviderDisabledError, default_asr_factory
    from libs.demo.usage import MSG_DISABLED

    factory = default_asr_factory(settings)
    with pytest.raises(ProviderDisabledError) as exc:
        factory("assemblyai")
    assert str(exc.value) == MSG_DISABLED


def test_default_asr_factory_unknown_provider_raises(settings):
    from libs.demo.processing import ProviderDisabledError, default_asr_factory

    factory = default_asr_factory(settings)
    with pytest.raises(ProviderDisabledError):
        factory("madeup")
