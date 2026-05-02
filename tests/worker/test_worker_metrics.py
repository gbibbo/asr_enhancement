from __future__ import annotations

import importlib
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from libs.asr.errors import AdapterTranscriptionError
from libs.asr.schema import ASRResult
from libs.audio.enhancement import EnhancementResult
from libs.common.models import JobStatus
from libs.common.settings import get_settings
from libs.observability.metrics import WORKER_HEARTBEAT, get_metrics_output

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


def _make_snapshot(tasks_mod, mode="transcribe_only", preset="bypass",
                   status=JobStatus.queued, raw_audio_uri=FAKE_RAW_AUDIO_URI):
    return tasks_mod.JobSnapshot(
        id=FAKE_JOB_ID,
        status=status,
        raw_audio_uri=raw_audio_uri,
        mode=mode,
        preset=preset,
    )


def _make_mock_storage():
    mock = MagicMock()
    mock.get_to_file.return_value = None
    mock.put.return_value = FAKE_TRANSCRIPT_URI
    mock.exists.return_value = True
    return mock


def _samples(output: str, metric_name: str) -> list[str]:
    return [
        line for line in output.splitlines()
        if (
            line.startswith(metric_name + "{") or line.startswith(metric_name + " ")
        ) and not line.startswith("#")
    ]


# ---------------------------------------------------------------------------
# Test 1: transcribe_only happy path — running + completed counters wired
# ---------------------------------------------------------------------------

def test_transcribe_only_happy_path_emits_running_and_completed(tasks_mod, monkeypatch):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod, mode="transcribe_only"))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda db, jid, text, uri, *_: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_jobs_total")

    assert any('status="running"' in s and 'mode="transcribe_only"' in s for s in samples), \
        "Expected asr_jobs_total{status='running', mode='transcribe_only'} in metrics output"
    assert any('status="completed"' in s and 'mode="transcribe_only"' in s for s in samples), \
        "Expected asr_jobs_total{status='completed', mode='transcribe_only'} in metrics output"


# ---------------------------------------------------------------------------
# Test 2: transcribe_only adapter failure — failed counter wired
# ---------------------------------------------------------------------------

def test_transcribe_only_adapter_failure_emits_failed(tasks_mod, monkeypatch):
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod, mode="transcribe_only"))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda db, jid, text, uri, *_: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    def _raise(path, job_id):
        raise AdapterTranscriptionError("adapter error")

    mock_adapter = MagicMock()
    mock_adapter.transcribe.side_effect = _raise
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_jobs_total")

    assert any('status="failed"' in s and 'mode="transcribe_only"' in s for s in samples), \
        "Expected asr_jobs_total{status='failed', mode='transcribe_only'} in metrics output"


# ---------------------------------------------------------------------------
# Test 3: enhance_and_transcribe happy path — correct mode label
# ---------------------------------------------------------------------------

def test_enhance_and_transcribe_happy_path_emits_correct_mode(tasks_mod, monkeypatch):
    monkeypatch.setattr(
        tasks_mod, "_load_job",
        lambda db, jid: _make_snapshot(tasks_mod, mode="enhance_and_transcribe", preset="light_clean"),
    )
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda db, jid, text, uri, *_: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    enh_result = EnhancementResult(
        output_path=Path("/tmp/fake_enhanced.wav"),
        preset_applied="light_clean",
        enhanced=False,
        enhancement_fallback=True,
        diagnostic={},
    )
    monkeypatch.setattr(tasks_mod, "apply_preset", lambda preset, inp, out: enh_result)

    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_jobs_total")

    assert any('status="running"' in s and 'mode="enhance_and_transcribe"' in s for s in samples), \
        "Expected asr_jobs_total{status='running', mode='enhance_and_transcribe'} in metrics output"
    assert any('status="completed"' in s and 'mode="enhance_and_transcribe"' in s for s in samples), \
        "Expected asr_jobs_total{status='completed', mode='enhance_and_transcribe'} in metrics output"


# ---------------------------------------------------------------------------
# Test 4: WORKER_HEARTBEAT gauge appears in output after set
# ---------------------------------------------------------------------------

def test_worker_heartbeat_appears_in_output_after_set():
    WORKER_HEARTBEAT.set(9999999999.0)
    output = get_metrics_output().decode("utf-8")
    # prometheus-client may render large floats in scientific notation
    lines = [
        ln for ln in output.splitlines()
        if ln.startswith("asr_worker_heartbeat_timestamp_seconds ")
    ]
    assert len(lines) > 0, "Expected a data line for asr_worker_heartbeat_timestamp_seconds"
    value = float(lines[0].split()[-1])
    assert abs(value - 9999999999.0) < 1.0, \
        f"Expected WORKER_HEARTBEAT value ≈9999999999.0, got {value}"
