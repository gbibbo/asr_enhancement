from __future__ import annotations

import importlib
import json
import sys
import uuid
from typing import Optional
from unittest.mock import MagicMock

import pytest

from libs.asr.schema import ASRResult
from libs.audio.enhancement import EnhancementResult
from libs.common.models import JobMode, JobStatus
from libs.common.settings import get_settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAKE_JOB_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FAKE_JOB_ID_STR = str(FAKE_JOB_ID)
FAKE_BUCKET = "asr-platform"
FAKE_RAW_AUDIO_URI = f"s3://{FAKE_BUCKET}/raw_audio/{FAKE_JOB_ID}/input.wav"
FAKE_TRANSCRIPT_KEY = f"transcripts/{FAKE_JOB_ID}/transcript.json"
FAKE_TRANSCRIPT_URI = f"s3://{FAKE_BUCKET}/{FAKE_TRANSCRIPT_KEY}"
FAKE_ENHANCED_KEY = f"enhanced_audio/{FAKE_JOB_ID}/output.wav"
FAKE_ENHANCED_URI = f"s3://{FAKE_BUCKET}/{FAKE_ENHANCED_KEY}"
FAKE_TRANSCRIPT_TEXT = "This is a deterministic fake transcript for local testing."

FAKE_ASR_RESULT = ASRResult(
    text=FAKE_TRANSCRIPT_TEXT,
    language="en",
    duration_seconds=None,
    segments=[],
    words=[],
    provider="fake",
    provider_job_id=None,
    raw_payload={},
)

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
    "MINIO_BUCKET": FAKE_BUCKET,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tasks_mod(monkeypatch):
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    sys.modules.pop("services.worker.app.celery_app", None)
    sys.modules.pop("services.worker.app.tasks", None)

    mod = importlib.import_module("services.worker.app.tasks")
    yield mod

    get_settings.cache_clear()
    sys.modules.pop("services.worker.app.tasks", None)
    sys.modules.pop("services.worker.app.celery_app", None)


def _make_snapshot(tasks_mod, mode="enhance_and_transcribe", preset="light_clean",
                   status=JobStatus.queued, raw_audio_uri=FAKE_RAW_AUDIO_URI):
    return tasks_mod.JobSnapshot(
        id=FAKE_JOB_ID,
        status=status,
        raw_audio_uri=raw_audio_uri,
        mode=mode,
        preset=preset,
    )


def _make_enh_result(
    enhanced: bool = True,
    fallback: bool = False,
    preset_applied: str = "light_clean",
    output_path=None,
    diagnostic: Optional[dict] = None,
) -> EnhancementResult:
    from pathlib import Path
    return EnhancementResult(
        output_path=output_path or Path("/tmp/enhanced/light_clean.wav"),
        preset_applied=preset_applied,
        enhanced=enhanced,
        enhancement_fallback=fallback,
        diagnostic=diagnostic or {},
    )


def _make_mock_storage(transcript_uri=FAKE_TRANSCRIPT_URI, enhanced_uri=FAKE_ENHANCED_URI):
    mock = MagicMock()
    mock.get_to_file.return_value = None
    mock.put.side_effect = [enhanced_uri, transcript_uri]
    mock.exists.return_value = True
    return mock


# ---------------------------------------------------------------------------
# Test 1: Happy path — non-bypass preset, enhancement succeeds
# ---------------------------------------------------------------------------

def test_enhance_happy_path_non_bypass(tasks_mod, monkeypatch):
    completed_calls: list[tuple] = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri, payload_uri=None, enhanced_uri=None:
            completed_calls.append((jid, text, uri, payload_uri, enhanced_uri)),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    fake_output = MagicMock()
    fake_output.__fspath__ = lambda self: "/tmp/enhanced/light_clean.wav"
    enh_result = _make_enh_result(enhanced=True, fallback=False)

    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: enh_result)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert failed_calls == []
    assert len(completed_calls) == 1
    jid, text, uri, payload_uri, enhanced_uri = completed_calls[0]
    assert jid == FAKE_JOB_ID
    assert text == FAKE_TRANSCRIPT_TEXT
    assert enhanced_uri == FAKE_ENHANCED_URI

    # ASR was called with the enhanced output path, not the raw audio path
    asr_call_path = mock_adapter.transcribe.call_args.args[0]
    assert asr_call_path == enh_result.output_path


# ---------------------------------------------------------------------------
# Test 2: Bypass preset — no enhanced audio uploaded, ASR on raw
# ---------------------------------------------------------------------------

def test_enhance_bypass_skips_enhancement_upload(tasks_mod, monkeypatch):
    completed_calls: list[tuple] = []

    snap = _make_snapshot(tasks_mod, mode="enhance_and_transcribe", preset="bypass")
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: snap)
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri, payload_uri=None, enhanced_uri=None:
            completed_calls.append((jid, enhanced_uri)),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    bypass_result = _make_enh_result(enhanced=False, fallback=False, preset_applied="bypass")
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: bypass_result)

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.return_value = FAKE_TRANSCRIPT_URI
    mock_storage.exists.return_value = True
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(completed_calls) == 1
    _, enhanced_uri = completed_calls[0]
    assert enhanced_uri is None

    # Only one storage.put (transcript); no enhanced audio put
    assert mock_storage.put.call_count == 1
    assert mock_storage.put.call_args.args[0] == FAKE_TRANSCRIPT_KEY


# ---------------------------------------------------------------------------
# Test 3: Fallback — enhancement fails, ASR on raw audio, job completed
# ---------------------------------------------------------------------------

def test_enhance_fallback_uses_raw_audio(tasks_mod, monkeypatch):
    completed_calls: list[tuple] = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri, payload_uri=None, enhanced_uri=None:
            completed_calls.append((jid, text, enhanced_uri)),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    fallback_result = _make_enh_result(
        enhanced=False, fallback=True, preset_applied="light_clean",
        diagnostic={"fallback_reason": "soundfile error"},
    )
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: fallback_result)

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.return_value = FAKE_TRANSCRIPT_URI
    mock_storage.exists.return_value = True
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    # Job completes successfully (not failed) — ASR ran on raw audio
    assert failed_calls == []
    assert len(completed_calls) == 1
    jid, text, enhanced_uri = completed_calls[0]
    assert jid == FAKE_JOB_ID
    assert text == FAKE_TRANSCRIPT_TEXT
    assert enhanced_uri is None


# ---------------------------------------------------------------------------
# Test 4: Correct enhanced audio object key
# ---------------------------------------------------------------------------

def test_enhance_correct_key(tasks_mod, monkeypatch):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda *a, **kw: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    enh_result = _make_enh_result(enhanced=True, fallback=False)
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: enh_result)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    put_calls = mock_storage.put.call_args_list
    # First put is for enhanced audio
    assert put_calls[0].args[0] == FAKE_ENHANCED_KEY


# ---------------------------------------------------------------------------
# Test 5: Enhanced audio URI is passed to _mark_job_completed
# ---------------------------------------------------------------------------

def test_enhance_uri_in_mark_completed(tasks_mod, monkeypatch):
    completed_calls: list[tuple] = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri, payload_uri=None, enhanced_uri=None:
            completed_calls.append(enhanced_uri),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    enh_result = _make_enh_result(enhanced=True, fallback=False)
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: enh_result)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(completed_calls) == 1
    assert completed_calls[0] == FAKE_ENHANCED_URI


# ---------------------------------------------------------------------------
# Test 6: Fallback — _mark_job_completed receives enhanced_audio_uri=None
# ---------------------------------------------------------------------------

def test_enhance_fallback_mark_completed_with_none_uri(tasks_mod, monkeypatch):
    completed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri, payload_uri=None, enhanced_uri=None:
            completed_calls.append(enhanced_uri),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    fallback_result = _make_enh_result(enhanced=False, fallback=True)
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: fallback_result)

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.return_value = FAKE_TRANSCRIPT_URI
    mock_storage.exists.return_value = True
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert completed_calls == [None]


# ---------------------------------------------------------------------------
# Test 7: Transcript JSON includes enhancement metadata
# ---------------------------------------------------------------------------

def test_enhance_transcript_json_has_enhancement_fields(tasks_mod, monkeypatch):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda *a, **kw: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    enh_result = _make_enh_result(enhanced=True, fallback=False, preset_applied="light_clean")
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: enh_result)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    # The second put is the transcript (first is enhanced audio)
    transcript_put = mock_storage.put.call_args_list[1]
    doc = json.loads(transcript_put.args[1].decode("utf-8"))

    assert "enhancement_preset" in doc
    assert doc["enhancement_preset"] == "light_clean"
    assert "enhancement_applied" in doc
    assert doc["enhancement_applied"] is True
    assert "enhancement_fallback" in doc
    assert doc["enhancement_fallback"] is False


# ---------------------------------------------------------------------------
# Test 8: Fallback — transcript JSON has enhancement_fallback=True
# ---------------------------------------------------------------------------

def test_enhance_fallback_transcript_json_has_fallback_true(tasks_mod, monkeypatch):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda *a, **kw: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    fallback_result = _make_enh_result(
        enhanced=False, fallback=True, preset_applied="light_clean",
        diagnostic={"fallback_reason": "sf.read failed"},
    )
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: fallback_result)

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.return_value = FAKE_TRANSCRIPT_URI
    mock_storage.exists.return_value = True
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    transcript_put = mock_storage.put.call_args_list[0]
    doc = json.loads(transcript_put.args[1].decode("utf-8"))

    assert doc["enhancement_fallback"] is True
    assert "enhancement_diagnostic" in doc


# ---------------------------------------------------------------------------
# Test 9: mode as JobMode enum triggers the enhance branch
# ---------------------------------------------------------------------------

def test_enhance_mode_as_enum_triggers_branch(tasks_mod, monkeypatch):
    apply_calls: list = []

    snap = _make_snapshot(tasks_mod, mode=JobMode.enhance_and_transcribe, preset="denoise")
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: snap)
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda *a, **kw: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    enh_result = _make_enh_result(enhanced=True, fallback=False, preset_applied="denoise")

    def _fake_apply(preset, inp, out):
        apply_calls.append(preset)
        return enh_result

    monkeypatch.setattr(tasks_mod, "apply_preset", _fake_apply)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    # apply_preset must have been called — enum mode was normalised to string correctly
    assert apply_calls == ["denoise"]


# ---------------------------------------------------------------------------
# Test 10: transcribe_only mode — apply_preset never called
# ---------------------------------------------------------------------------

def test_transcribe_only_unchanged_after_enhance_branch(tasks_mod, monkeypatch):
    apply_calls: list = []
    completed_calls: list = []

    snap = _make_snapshot(tasks_mod, mode="transcribe_only", preset="bypass")
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: snap)
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri, payload_uri=None, enhanced_uri=None:
            completed_calls.append((jid, text, enhanced_uri)),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    monkeypatch.setattr(tasks_mod, "apply_preset", lambda *a: apply_calls.append(a))

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.return_value = FAKE_TRANSCRIPT_URI
    mock_storage.exists.return_value = True
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_ASR_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    # apply_preset must NOT have been called for transcribe_only
    assert apply_calls == []
    assert len(completed_calls) == 1
    jid, text, enhanced_uri = completed_calls[0]
    assert jid == FAKE_JOB_ID
    assert text == FAKE_TRANSCRIPT_TEXT
    assert enhanced_uri is None
