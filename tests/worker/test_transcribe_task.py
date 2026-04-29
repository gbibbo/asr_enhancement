from __future__ import annotations

import importlib
import json
import sys
import uuid
from typing import Optional
from unittest.mock import MagicMock

import pytest

from libs.asr_adapter.errors import AdapterTranscriptionError
from libs.asr_adapter.schema import ASRResult
from libs.common.models import JobStatus
from libs.common.settings import get_settings
from libs.common.storage import ObjectNotFoundError, ObjectUploadError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAKE_JOB_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FAKE_JOB_ID_STR = str(FAKE_JOB_ID)
FAKE_BUCKET = "asr-platform"
FAKE_RAW_AUDIO_URI = f"s3://{FAKE_BUCKET}/raw_audio/{FAKE_JOB_ID}/input.wav"
FAKE_TRANSCRIPT_KEY = f"transcripts/{FAKE_JOB_ID}/transcript.json"
FAKE_TRANSCRIPT_URI = f"s3://{FAKE_BUCKET}/{FAKE_TRANSCRIPT_KEY}"
FAKE_TRANSCRIPT_TEXT = "This is a deterministic fake transcript for local testing."

FAKE_RESULT = ASRResult(
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
    """Fresh import of tasks module with env vars set.

    Mirrors the approach in test_celery_app.py: pops both celery_app and tasks
    from sys.modules before and after each test to avoid cross-test module
    identity pollution from Celery's global task registry.
    """
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


def _make_snapshot(tasks_mod, status=JobStatus.queued, raw_audio_uri=FAKE_RAW_AUDIO_URI):
    return tasks_mod.JobSnapshot(id=FAKE_JOB_ID, status=status, raw_audio_uri=raw_audio_uri)


def _make_mock_storage(put_uri=FAKE_TRANSCRIPT_URI, exists_result=True):
    mock = MagicMock()
    mock.get_to_file.return_value = None
    mock.put.return_value = put_uri
    mock.exists.return_value = exists_result
    return mock


# ---------------------------------------------------------------------------
# Test 1: Happy path
# ---------------------------------------------------------------------------

def test_happy_path(tasks_mod, monkeypatch):
    running_calls: list[uuid.UUID] = []
    completed_calls: list[tuple] = []
    failed_calls: list[tuple] = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: running_calls.append(jid))
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: completed_calls.append((jid, text, uri)),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "FakeASRAdapter", lambda fake_transcript=None: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    # _mark_job_running called with correct UUID
    assert running_calls == [FAKE_JOB_ID]

    # storage.get_to_file called with the raw audio key (not the full URI)
    expected_audio_key = f"raw_audio/{FAKE_JOB_ID}/input.wav"
    get_call = mock_storage.get_to_file.call_args
    assert get_call is not None
    assert get_call.args[0] == expected_audio_key

    # storage.put called with transcript key
    put_call = mock_storage.put.call_args
    assert put_call is not None
    assert put_call.args[0] == FAKE_TRANSCRIPT_KEY
    # uploaded bytes decode as valid JSON with required fields
    uploaded_bytes = put_call.args[1]
    doc = json.loads(uploaded_bytes.decode("utf-8"))
    assert "text" in doc
    assert "language" in doc
    assert "provider" in doc
    assert "raw_payload" in doc

    # storage.exists checked for transcript key before _mark_job_completed
    mock_storage.exists.assert_called_once_with(FAKE_TRANSCRIPT_KEY)

    # _mark_job_completed called with correct values
    assert len(completed_calls) == 1
    assert completed_calls[0] == (FAKE_JOB_ID, FAKE_TRANSCRIPT_TEXT, FAKE_TRANSCRIPT_URI)

    # _mark_job_failed never called
    assert failed_calls == []


# ---------------------------------------------------------------------------
# Test 2: Unknown job ID exits gracefully
# ---------------------------------------------------------------------------

def test_unknown_job_id_exits_gracefully(tasks_mod, monkeypatch):
    running_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: running_calls.append(jid))
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert running_calls == []
    assert failed_calls == []


# ---------------------------------------------------------------------------
# Test 3: Already completed exits without modification
# ---------------------------------------------------------------------------

def test_already_completed_exits_without_modification(tasks_mod, monkeypatch):
    running_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(
        tasks_mod, "_load_job",
        lambda db, jid: _make_snapshot(tasks_mod, status=JobStatus.completed),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: running_calls.append(jid))
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert running_calls == []
    assert failed_calls == []


# ---------------------------------------------------------------------------
# Test 4: Failed job exits without modification
# ---------------------------------------------------------------------------

def test_failed_job_exits_without_modification(tasks_mod, monkeypatch):
    running_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(
        tasks_mod, "_load_job",
        lambda db, jid: _make_snapshot(tasks_mod, status=JobStatus.failed),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: running_calls.append(jid))
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert running_calls == []
    assert failed_calls == []


# ---------------------------------------------------------------------------
# Test 5: Running job exits without modification
# ---------------------------------------------------------------------------

def test_running_job_exits_without_modification(tasks_mod, monkeypatch):
    running_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(
        tasks_mod, "_load_job",
        lambda db, jid: _make_snapshot(tasks_mod, status=JobStatus.running),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: running_calls.append(jid))
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert running_calls == []
    assert failed_calls == []


# ---------------------------------------------------------------------------
# Test 6: Malformed job_id exits gracefully
# ---------------------------------------------------------------------------

def test_malformed_job_id_exits_gracefully(tasks_mod, monkeypatch):
    load_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: load_calls.append(jid))
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: failed_calls.append(jid))

    tasks_mod.transcribe_job.run("not-a-uuid")

    assert load_calls == []
    assert failed_calls == []


# ---------------------------------------------------------------------------
# Test 7: Missing raw_audio_uri marks job failed
# ---------------------------------------------------------------------------

def test_missing_raw_audio_uri_marks_failed(tasks_mod, monkeypatch):
    running_calls: list = []
    completed_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(
        tasks_mod, "_load_job",
        lambda db, jid: _make_snapshot(tasks_mod, raw_audio_uri=None),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: running_calls.append(jid))
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: completed_calls.append(jid),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert running_calls == [FAKE_JOB_ID]
    assert len(failed_calls) == 1
    assert failed_calls[0][0] == FAKE_JOB_ID
    assert completed_calls == []


# ---------------------------------------------------------------------------
# Test 8: Audio download fails marks job failed
# ---------------------------------------------------------------------------

def test_audio_download_fails_marks_job_failed(tasks_mod, monkeypatch):
    completed_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: completed_calls.append(jid),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    mock_storage = MagicMock()
    mock_storage.get_to_file.side_effect = ObjectNotFoundError("audio missing")
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(failed_calls) == 1
    assert failed_calls[0][0] == FAKE_JOB_ID
    assert completed_calls == []


# ---------------------------------------------------------------------------
# Test 9: ASR adapter fails marks job failed
# ---------------------------------------------------------------------------

def test_asr_adapter_fails_marks_job_failed(tasks_mod, monkeypatch):
    completed_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: completed_calls.append(jid),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.side_effect = AdapterTranscriptionError("ASR failed")
    monkeypatch.setattr(tasks_mod, "FakeASRAdapter", lambda fake_transcript=None: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(failed_calls) == 1
    assert failed_calls[0][0] == FAKE_JOB_ID
    assert completed_calls == []


# ---------------------------------------------------------------------------
# Test 10: Transcript upload fails marks job failed
# ---------------------------------------------------------------------------

def test_transcript_upload_fails_marks_job_failed(tasks_mod, monkeypatch):
    completed_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: completed_calls.append(jid),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.side_effect = ObjectUploadError("MinIO down")
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "FakeASRAdapter", lambda fake_transcript=None: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(failed_calls) == 1
    assert failed_calls[0][0] == FAKE_JOB_ID
    assert completed_calls == []


# ---------------------------------------------------------------------------
# Test 11: Artifact check fails marks job failed
# ---------------------------------------------------------------------------

def test_artifact_check_fails_marks_job_failed(tasks_mod, monkeypatch):
    completed_calls: list = []
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: completed_calls.append(jid),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    mock_storage = _make_mock_storage(exists_result=False)
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "FakeASRAdapter", lambda fake_transcript=None: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(failed_calls) == 1
    assert failed_calls[0][0] == FAKE_JOB_ID
    assert completed_calls == []


# ---------------------------------------------------------------------------
# Test 12: _mark_job_completed raises marks job failed
# ---------------------------------------------------------------------------

def test_mark_completed_fails_marks_job_failed(tasks_mod, monkeypatch):
    failed_calls: list = []

    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(
        tasks_mod, "_mark_job_completed",
        lambda db, jid, text, uri: (_ for _ in ()).throw(RuntimeError("DB write failed")),
    )
    monkeypatch.setattr(
        tasks_mod, "_mark_job_failed",
        lambda db, jid, msg: failed_calls.append((jid, msg)),
    )

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "FakeASRAdapter", lambda fake_transcript=None: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    assert len(failed_calls) == 1
    assert failed_calls[0][0] == FAKE_JOB_ID


# ---------------------------------------------------------------------------
# Tests 13–14: _uri_to_key
# ---------------------------------------------------------------------------

def test_uri_to_key_parses_correctly(tasks_mod):
    assert tasks_mod._uri_to_key("s3://bucket/a/b/c", "bucket") == "a/b/c"


def test_uri_to_key_rejects_wrong_bucket(tasks_mod):
    with pytest.raises(ValueError):
        tasks_mod._uri_to_key("s3://other-bucket/a/b/c", "bucket")
