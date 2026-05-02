from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from libs.demo.examples import get_safe_audio_path

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


def _minimal_wav() -> bytes:
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 1, 16000, 32000, 2, 16)
    data = struct.pack("<4sI", b"data", 0)
    riff = struct.pack("<4sI4s", b"RIFF", 4 + len(fmt) + len(data), b"WAVE")
    return riff + fmt + data


@pytest.fixture()
def audio_client(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))

    audio_root = tmp_path / "artifacts" / "examples"
    audio_root.mkdir(parents=True)
    (audio_root / "clean.wav").write_bytes(_minimal_wav())
    (audio_root / "degraded_far.wav").write_bytes(_minimal_wav())

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "ex001",
            "title": "Test",
            "duration_seconds": 3.0,
            "degradation_ids": ["far_field_room"],
            "ground_truth": "hello",
            "audio_available": True,
            "clean_audio_path": "clean.wav",
            "degraded_audio_paths": {"far_field_room": "degraded_far.wav"},
        },
        {
            "example_id": "no_audio",
            "title": "No Audio",
            "duration_seconds": 2.0,
            "degradation_ids": [],
            "ground_truth": "silence",
            "audio_available": False,
            "clean_audio_path": None,
            "degraded_audio_paths": {},
        },
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")

    from services.api.app.demo_main import app
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Unit tests for get_safe_audio_path
# ---------------------------------------------------------------------------

def test_get_safe_audio_path_returns_none_for_none_input(tmp_path):
    assert get_safe_audio_path(tmp_path, None) is None


def test_get_safe_audio_path_returns_none_for_empty_string(tmp_path):
    assert get_safe_audio_path(tmp_path, "") is None


def test_get_safe_audio_path_returns_none_for_absolute_path(tmp_path):
    assert get_safe_audio_path(tmp_path, "/etc/passwd") is None


def test_get_safe_audio_path_returns_none_for_traversal(tmp_path):
    (tmp_path / "secret.wav").write_bytes(b"x")
    assert get_safe_audio_path(tmp_path / "sub", "../secret.wav") is None


def test_get_safe_audio_path_returns_none_for_missing_file(tmp_path):
    assert get_safe_audio_path(tmp_path, "nonexistent.wav") is None


def test_get_safe_audio_path_returns_resolved_path_for_valid_file(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(_minimal_wav())
    result = get_safe_audio_path(tmp_path, "audio.wav")
    assert result == wav.resolve()


def test_get_safe_audio_path_accepts_subdir_relative_path(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    wav = sub / "audio.wav"
    wav.write_bytes(_minimal_wav())
    result = get_safe_audio_path(tmp_path, "sub/audio.wav")
    assert result == wav.resolve()


# ---------------------------------------------------------------------------
# API: clean audio endpoint
# ---------------------------------------------------------------------------

def test_clean_audio_returns_200(audio_client):
    resp = audio_client.get("/demo/examples/ex001/audio/clean")
    assert resp.status_code == 200


def test_clean_audio_content_type_is_wav(audio_client):
    resp = audio_client.get("/demo/examples/ex001/audio/clean")
    assert resp.headers["content-type"].startswith("audio/wav")


def test_clean_audio_returns_404_for_unknown_example(audio_client):
    resp = audio_client.get("/demo/examples/does_not_exist/audio/clean")
    assert resp.status_code == 404


def test_clean_audio_returns_404_when_path_is_none(audio_client):
    resp = audio_client.get("/demo/examples/no_audio/audio/clean")
    assert resp.status_code == 404


def test_clean_audio_returns_404_when_file_missing(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "ex002",
            "title": "Missing",
            "duration_seconds": 1.0,
            "degradation_ids": [],
            "ground_truth": "hi",
            "clean_audio_path": "ghost.wav",
            "degraded_audio_paths": {},
        }
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        resp = c.get("/demo/examples/ex002/audio/clean")
    assert resp.status_code == 404


def test_clean_audio_rejects_path_traversal(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    (tmp_path / "secret.wav").write_bytes(_minimal_wav())
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "evil",
            "title": "Evil",
            "duration_seconds": 1.0,
            "degradation_ids": [],
            "ground_truth": "x",
            "clean_audio_path": "../../secret.wav",
            "degraded_audio_paths": {},
        }
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        resp = c.get("/demo/examples/evil/audio/clean")
    assert resp.status_code == 404


def test_clean_audio_rejects_absolute_path(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "abs",
            "title": "Abs",
            "duration_seconds": 1.0,
            "degradation_ids": [],
            "ground_truth": "x",
            "clean_audio_path": "/etc/passwd",
            "degraded_audio_paths": {},
        }
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        resp = c.get("/demo/examples/abs/audio/clean")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API: degraded audio endpoint
# ---------------------------------------------------------------------------

def test_degraded_audio_returns_200(audio_client):
    resp = audio_client.get("/demo/examples/ex001/audio/degraded/far_field_room")
    assert resp.status_code == 200


def test_degraded_audio_content_type_is_wav(audio_client):
    resp = audio_client.get("/demo/examples/ex001/audio/degraded/far_field_room")
    assert resp.headers["content-type"].startswith("audio/wav")


def test_degraded_audio_returns_404_for_unknown_example(audio_client):
    resp = audio_client.get("/demo/examples/does_not_exist/audio/degraded/far_field_room")
    assert resp.status_code == 404


def test_degraded_audio_returns_404_for_unknown_degradation_id(audio_client):
    resp = audio_client.get("/demo/examples/ex001/audio/degraded/unknown_deg")
    assert resp.status_code == 404


def test_degraded_audio_returns_404_when_file_missing(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "ex003",
            "title": "Missing Deg",
            "duration_seconds": 1.0,
            "degradation_ids": ["cafe"],
            "ground_truth": "hi",
            "clean_audio_path": None,
            "degraded_audio_paths": {"cafe": "ghost_deg.wav"},
        }
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        resp = c.get("/demo/examples/ex003/audio/degraded/cafe")
    assert resp.status_code == 404


def test_degraded_audio_rejects_path_traversal(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    (tmp_path / "secret.wav").write_bytes(_minimal_wav())
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "evil2",
            "title": "Evil2",
            "duration_seconds": 1.0,
            "degradation_ids": ["x"],
            "ground_truth": "x",
            "clean_audio_path": None,
            "degraded_audio_paths": {"x": "../../secret.wav"},
        }
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        resp = c.get("/demo/examples/evil2/audio/degraded/x")
    assert resp.status_code == 404


def test_degraded_audio_rejects_absolute_path(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    examples = [
        {
            "example_id": "abs2",
            "title": "Abs2",
            "duration_seconds": 1.0,
            "degradation_ids": ["x"],
            "ground_truth": "x",
            "clean_audio_path": None,
            "degraded_audio_paths": {"x": "/etc/passwd"},
        }
    ]
    (config_dir / "demo_examples.json").write_text(json.dumps(examples), encoding="utf-8")
    from services.api.app.demo_main import app
    with TestClient(app) as c:
        resp = c.get("/demo/examples/abs2/audio/degraded/x")
    assert resp.status_code == 404
