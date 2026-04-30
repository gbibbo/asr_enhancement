from __future__ import annotations

import importlib
import logging
import sys
import uuid
from unittest.mock import MagicMock

import pytest

from libs.asr_adapter.errors import AdapterTranscriptionError
from libs.asr_adapter.schema import ASRResult
from libs.common.models import JobStatus
from libs.common.settings import get_settings

# conftest.py already sets required env vars at collection time.

_REQUIRED_ENVS = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
    "MINIO_BUCKET": "asr-platform",
}


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


FAKE_JOB_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FAKE_JOB_ID_STR = str(FAKE_JOB_ID)
FAKE_BUCKET = "asr-platform"
FAKE_RAW_AUDIO_URI = f"s3://{FAKE_BUCKET}/raw_audio/{FAKE_JOB_ID}/input.wav"
FAKE_TRANSCRIPT_URI = f"s3://{FAKE_BUCKET}/transcripts/{FAKE_JOB_ID}/transcript.json"
FAKE_RESULT = ASRResult(
    text="deterministic fake text",
    language="en",
    duration_seconds=None,
    segments=[],
    words=[],
    provider="fake",
    provider_job_id=None,
    raw_payload={},
)


def _make_snapshot(tasks_mod, status=JobStatus.queued, raw_audio_uri=FAKE_RAW_AUDIO_URI):
    return tasks_mod.JobSnapshot(id=FAKE_JOB_ID, status=status, raw_audio_uri=raw_audio_uri)


def _make_mock_storage(put_uri=FAKE_TRANSCRIPT_URI, exists_result=True):
    mock = MagicMock()
    mock.get_to_file.return_value = None
    mock.put.return_value = put_uri
    mock.exists.return_value = exists_result
    return mock


def _setup_happy_path(tasks_mod, monkeypatch):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda db, jid, text, uri, *_: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)
    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)
    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda settings: mock_adapter)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_malformed_job_id_logged(tasks_mod, caplog):
    with caplog.at_level(logging.ERROR, logger="services.worker.app.tasks"):
        tasks_mod.transcribe_job.run("not-a-uuid")
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) >= 1
    assert any("malformed" in r.getMessage() for r in error_records)


def test_job_not_found_logged(tasks_mod, monkeypatch, caplog):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: None)
    with caplog.at_level(logging.ERROR, logger="services.worker.app.tasks"):
        tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) >= 1
    found_record = next(
        (r for r in error_records if getattr(r, "job_id", None) == FAKE_JOB_ID_STR),
        None,
    )
    assert found_record is not None, "Expected an error record with job_id attribute"


def test_job_received_logged(tasks_mod, monkeypatch, caplog):
    _setup_happy_path(tasks_mod, monkeypatch)
    with caplog.at_level(logging.INFO, logger="services.worker.app.tasks"):
        tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)
    received = [r for r in caplog.records if r.getMessage() == "worker.job_received"]
    assert len(received) >= 1
    assert received[0].job_id == FAKE_JOB_ID_STR


def test_job_running_logged(tasks_mod, monkeypatch, caplog):
    _setup_happy_path(tasks_mod, monkeypatch)
    with caplog.at_level(logging.INFO, logger="services.worker.app.tasks"):
        tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)
    running = [r for r in caplog.records if r.getMessage() == "worker.job_running"]
    assert len(running) >= 1
    assert running[0].job_id == FAKE_JOB_ID_STR
    assert hasattr(running[0], "mode")
    assert hasattr(running[0], "preset")


def test_job_completed_logged(tasks_mod, monkeypatch, caplog):
    _setup_happy_path(tasks_mod, monkeypatch)
    with caplog.at_level(logging.INFO, logger="services.worker.app.tasks"):
        tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)
    completed = [r for r in caplog.records if r.getMessage() == "worker.job_completed"]
    assert len(completed) >= 1
    assert completed[0].job_id == FAKE_JOB_ID_STR


def test_job_failed_logged(tasks_mod, monkeypatch, caplog):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)
    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.side_effect = AdapterTranscriptionError("adapter boom")
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda settings: mock_adapter)

    with caplog.at_level(logging.ERROR, logger="services.worker.app.tasks"):
        tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    failed = [r for r in caplog.records if r.getMessage() == "worker.job_failed"]
    assert len(failed) >= 1
    assert failed[0].job_id == FAKE_JOB_ID_STR
