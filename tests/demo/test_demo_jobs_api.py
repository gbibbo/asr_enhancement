from __future__ import annotations

import io
import json
import sqlite3
import struct
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path

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
]

_MINIMAL_EXAMPLE = {
    "example_id": "ex001",
    "title": "Test",
    "duration_seconds": 5.0,
    "degradation_ids": ["far_field_room"],
    "ground_truth": "hello world",
}


def _minimal_wav() -> bytes:
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 1, 16000, 32000, 2, 16)
    data = struct.pack("<4sI", b"data", 0)
    riff = struct.pack("<4sI4s", b"RIFF", 4 + len(fmt) + len(data), b"WAVE")
    return riff + fmt + data


_B9_SAMPLERATE = 16000


def _wav_bytes_for_frames(frames: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_B9_SAMPLERATE)
        w.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def _wav_bytes_for_seconds(seconds: float) -> bytes:
    return _wav_bytes_for_frames(int(round(seconds * _B9_SAMPLERATE)))


def _insert_job(db_path: Path, status: str) -> str:
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider) VALUES (?, ?, ?, ?, ?)",
        (job_id, status, now, now, "whisper"),
    )
    conn.commit()
    conn.close()
    return job_id


def _insert_cache_entry(db_path: Path, cache_key: str, result_json: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """INSERT INTO cache_entries
           (cache_key, example_id, degradation_id, degradation_version,
            asr_provider, asr_model_version, enhancer_version, metrics_version,
            result_json, artifact_root, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cache_key, "ex001", "far_field_room", "1.0",
            "whisper", "tiny.en", "1.0", "1.0",
            result_json, "/tmp", now,
        ),
    )
    conn.commit()
    conn.close()


def _db_path(c: TestClient) -> Path:
    return c.app.state.settings.demo_db_path


def _queue_max(c: TestClient) -> int:
    return c.app.state.settings.demo_queue_max


@pytest.fixture()
def client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def client_with_example(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo_examples.json").write_text(
        json.dumps([_MINIMAL_EXAMPLE]), encoding="utf-8"
    )
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def small_client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("DEMO_UPLOAD_LIMIT_BYTES", "10")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /demo/jobs/{job_id}
# ---------------------------------------------------------------------------

def test_get_job_404_for_unknown(client):
    resp = client.get(f"/demo/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_job_200_queued_status(client):
    db = _db_path(client)
    job_id = _insert_job(db, "queued")
    resp = client.get(f"/demo/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"
    assert resp.json()["job_id"] == job_id


# ---------------------------------------------------------------------------
# GET /demo/jobs/{job_id}/result
# ---------------------------------------------------------------------------

def test_get_job_result_404_for_unknown(client):
    resp = client.get(f"/demo/jobs/{uuid.uuid4()}/result")
    assert resp.status_code == 404


def test_get_job_result_202_while_queued(client):
    db = _db_path(client)
    job_id = _insert_job(db, "queued")
    resp = client.get(f"/demo/jobs/{job_id}/result")
    assert resp.status_code == 202
    assert resp.json()["status"] == "queued"


def test_get_job_result_200_for_completed(client):
    db = _db_path(client)
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider, result_json)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "completed", now, now, "whisper", '{"transcript": "hello"}'),
    )
    conn.commit()
    conn.close()
    resp = client.get(f"/demo/jobs/{job_id}/result")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["result"]["transcript"] == "hello"


def test_get_job_result_200_for_completed_upload_b9_2_schema(client):
    """B9.2: GET /demo/jobs/{id}/result surfaces the upload result_json schema verbatim."""
    db = _db_path(client)
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "source_type": "upload",
        "provider": "whisper",
        "asr_model_version": "tiny.en",
        "enhancer_version": "bypass",
        "degradation_id": None,
        "degradation_version": None,
        "degradation_applied": False,
        "input_audio_path": "/abs/uploads/u.wav",
        "degraded_audio_path": None,
        "enhanced_audio_path": None,
        "raw": {
            "transcript": "hello",
            "language": "en",
            "language_probability": 0.99,
            "latency_seconds": 0.42,
        },
        "enhanced": {
            "transcript": "hello",
            "latency_seconds": 0.41,
            "preset_applied": "bypass",
            "enhanced_flag": False,
            "enhancement_fallback": False,
        },
        "enhanced_error": None,
        "metrics": {},
        "warnings": [],
    }
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider, result_json)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "completed", now, now, "whisper", json.dumps(payload)),
    )
    conn.commit()
    conn.close()
    resp = client.get(f"/demo/jobs/{job_id}/result")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["result"] == payload
    assert "ground_truth" not in json.dumps(body)
    assert body["result"]["metrics"] == {}


def test_get_job_result_200_for_failed(client):
    db = _db_path(client)
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider, error_message)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "failed", now, now, "whisper", "processing not yet implemented (B5)"),
    )
    conn.commit()
    conn.close()
    resp = client.get(f"/demo/jobs/{job_id}/result")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert "B5" in body["error"]


# ---------------------------------------------------------------------------
# POST /demo/run-cached
# ---------------------------------------------------------------------------

def test_run_cached_404_unknown_example(client):
    resp = client.post(
        "/demo/run-cached",
        json={"example_id": "nonexistent", "degradation_id": "far_field_room", "provider": "whisper"},
    )
    assert resp.status_code == 404


def test_run_cached_404_unknown_degradation(client_with_example):
    resp = client_with_example.post(
        "/demo/run-cached",
        json={"example_id": "ex001", "degradation_id": "unknown_deg", "provider": "whisper"},
    )
    assert resp.status_code == 404


def test_run_cached_miss_returns_200_cache_miss(client_with_example):
    resp = client_with_example.post(
        "/demo/run-cached",
        json={"example_id": "ex001", "degradation_id": "far_field_room", "provider": "whisper"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cache_miss"


def test_run_cached_miss_does_not_create_job(client_with_example):
    db = _db_path(client_with_example)
    conn = sqlite3.connect(str(db))
    before = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()

    resp = client_with_example.post(
        "/demo/run-cached",
        json={"example_id": "ex001", "degradation_id": "far_field_room", "provider": "whisper"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cache_miss"

    conn = sqlite3.connect(str(db))
    after = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    assert after == before


def test_run_cached_hit_returns_result(client_with_example):
    from libs.demo.cache import build_cache_key

    db = _db_path(client_with_example)
    cache_key = build_cache_key(
        example_id="ex001",
        degradation_id="far_field_room",
        asr_provider="whisper",
        asr_model_version="tiny.en",
        enhancer_version=None,
    )
    _insert_cache_entry(db, cache_key, '{"transcript": "hello world"}')

    resp = client_with_example.post(
        "/demo/run-cached",
        json={"example_id": "ex001", "degradation_id": "far_field_room", "provider": "whisper"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cache_hit"
    assert body["result"]["transcript"] == "hello world"
    assert "cache_key" in body


# ---------------------------------------------------------------------------
# POST /demo/upload
# ---------------------------------------------------------------------------

def test_upload_creates_queued_job_202(client):
    wav = _minimal_wav()
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", wav, "audio/wav")},
        data={"provider": "whisper"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert "job_id" in body
    assert body["status"] == "queued"

    from libs.demo.persistence import get_job
    row = get_job(_db_path(client), body["job_id"])
    assert row is not None
    assert row["status"] == "queued"


def test_upload_job_has_input_artifact_path(client):
    wav = _minimal_wav()
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", wav, "audio/wav")},
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    from libs.demo.persistence import get_job
    row = get_job(_db_path(client), job_id)
    assert row is not None
    artifact = row["input_artifact_path"]
    assert artifact is not None
    upload_dir = client.app.state.settings.demo_upload_dir
    assert Path(artifact).is_relative_to(upload_dir)


def test_upload_too_large_returns_413(small_client):
    content = b"x" * 20
    resp = small_client.post(
        "/demo/upload",
        files={"file": ("audio.wav", content, "audio/wav")},
    )
    assert resp.status_code == 413


def test_upload_bad_extension_returns_415(client):
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.txt", b"data", "text/plain")},
    )
    assert resp.status_code == 415


def test_upload_503_when_queue_full_no_orphan(client):
    db = _db_path(client)
    qmax = _queue_max(client)
    for _ in range(qmax):
        _insert_job(db, "queued")

    wav = _minimal_wav()
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", wav, "audio/wav")},
    )
    assert resp.status_code == 503

    upload_dir = client.app.state.settings.demo_upload_dir
    if upload_dir.exists():
        remaining = [f for f in upload_dir.iterdir() if f.is_file()]
        assert remaining == []


# ---------------------------------------------------------------------------
# B9.1 — backend upload validation: 422 paths
# ---------------------------------------------------------------------------

def test_upload_corrupt_audio_returns_422(client):
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", b"\x00" * 100, "audio/wav")},
    )
    assert resp.status_code == 422
    assert "could not be decoded" in resp.json()["detail"].lower()


def test_upload_too_long_returns_422(client):
    wav = _wav_bytes_for_seconds(31.0)
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", wav, "audio/wav")},
    )
    assert resp.status_code == 422
    assert "exceeds 30 seconds" in resp.json()["detail"].lower()


def test_upload_422_removes_saved_file(client):
    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", b"\x00" * 100, "audio/wav")},
    )
    assert resp.status_code == 422

    upload_dir = client.app.state.settings.demo_upload_dir
    if upload_dir.exists():
        remaining = [f for f in upload_dir.iterdir() if f.is_file()]
        assert remaining == []


def test_upload_422_does_not_change_queue_depth(client):
    db = _db_path(client)
    conn = sqlite3.connect(str(db))
    before = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status IN ('queued', 'running')"
    ).fetchone()[0]
    conn.close()

    resp = client.post(
        "/demo/upload",
        files={"file": ("audio.wav", _wav_bytes_for_seconds(31.0), "audio/wav")},
    )
    assert resp.status_code == 422

    conn = sqlite3.connect(str(db))
    after = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE status IN ('queued', 'running')"
    ).fetchone()[0]
    conn.close()
    assert after == before


# ---------------------------------------------------------------------------
# GET /admin/stats
# ---------------------------------------------------------------------------

def test_admin_stats_401_without_credentials(client):
    resp = client.get("/admin/stats")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Unauthorized"


def test_admin_stats_401_when_password_not_configured(client):
    resp = client.get("/admin/stats", auth=("admin", "anything"))
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Unauthorized"
