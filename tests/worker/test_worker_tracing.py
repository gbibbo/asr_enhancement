from __future__ import annotations

import importlib
import sys
import uuid
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from opentelemetry import propagate, trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from libs.asr_adapter.schema import ASRResult
from libs.common.models import JobStatus
from libs.common.settings import get_settings
from libs.observability.tracing import _reset_tracing_for_tests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAKE_JOB_ID = uuid.UUID("aaaabbbb-cccc-dddd-eeee-ffffffffffff")
FAKE_JOB_ID_STR = str(FAKE_JOB_ID)
FAKE_BUCKET = "asr-platform"
FAKE_RAW_AUDIO_URI = f"s3://{FAKE_BUCKET}/raw_audio/{FAKE_JOB_ID}/input.wav"
FAKE_TRANSCRIPT_KEY = f"transcripts/{FAKE_JOB_ID}/transcript.json"
FAKE_TRANSCRIPT_URI = f"s3://{FAKE_BUCKET}/{FAKE_TRANSCRIPT_KEY}"

FAKE_RESULT = ASRResult(
    text="Fake transcript.",
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
def otel_exporter():
    """Install a fresh InMemorySpanExporter as the global OTel provider.
    Resets before and after each test to prevent inter-test state leaks.
    """
    _reset_tracing_for_tests()

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    assert trace.get_tracer_provider() is provider, (
        "Provider replacement failed — _reset_tracing_for_tests may not have cleared the set-once guard"
    )

    yield exporter

    _reset_tracing_for_tests()
    exporter.clear()


@pytest.fixture
def tasks_mod(monkeypatch):
    """Fresh import of tasks module with env vars and no Celery Redis connection."""
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


def _wire_happy_path(tasks_mod, monkeypatch):
    """Patch all DB/storage/ASR calls for a successful job run."""
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_completed", lambda db, jid, text, uri, *_: None)
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)
    mock_storage = _make_mock_storage()
    monkeypatch.setattr(tasks_mod.StorageClient, "from_settings", lambda s: mock_storage)
    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_mod, "make_asr_adapter", lambda s: mock_adapter)
    return mock_storage


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_transcribe_job_creates_span(otel_exporter, tasks_mod, monkeypatch):
    _wire_happy_path(tasks_mod, monkeypatch)
    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    spans = otel_exporter.get_finished_spans()
    worker_spans = [s for s in spans if s.name == "worker.transcribe_job"]
    assert len(worker_spans) == 1


def test_transcribe_job_span_has_job_id(otel_exporter, tasks_mod, monkeypatch):
    _wire_happy_path(tasks_mod, monkeypatch)
    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    spans = [s for s in otel_exporter.get_finished_spans() if s.name == "worker.transcribe_job"]
    assert spans[0].attributes["job.id"] == FAKE_JOB_ID_STR


def test_transcribe_job_span_has_mode(otel_exporter, tasks_mod, monkeypatch):
    _wire_happy_path(tasks_mod, monkeypatch)
    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    spans = [s for s in otel_exporter.get_finished_spans() if s.name == "worker.transcribe_job"]
    assert "job.mode" in spans[0].attributes
    assert spans[0].attributes["job.mode"] == "transcribe_only"


def test_transcribe_job_with_valid_traceparent_links_to_parent(otel_exporter, tasks_mod, monkeypatch):
    # Create a parent span using the same provider (otel_exporter fixture installed it as global)
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("api-parent") as parent_span:
        carrier: dict = {}
        propagate.inject(carrier)
        traceparent = carrier.get("traceparent")

    parent_trace_id = parent_span.get_span_context().trace_id

    _wire_happy_path(tasks_mod, monkeypatch)
    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR, traceparent)

    spans = [s for s in otel_exporter.get_finished_spans() if s.name == "worker.transcribe_job"]
    assert len(spans) == 1
    worker_trace_id = spans[0].context.trace_id
    assert worker_trace_id == parent_trace_id, (
        f"Worker trace_id ({worker_trace_id:#x}) does not match parent trace_id ({parent_trace_id:#x})"
    )


def test_transcribe_job_with_none_traceparent_is_root(otel_exporter, tasks_mod, monkeypatch):
    _wire_happy_path(tasks_mod, monkeypatch)
    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR, None)

    spans = [s for s in otel_exporter.get_finished_spans() if s.name == "worker.transcribe_job"]
    assert len(spans) == 1
    assert spans[0].parent is None


def test_transcribe_job_failure_records_exception_on_span(otel_exporter, tasks_mod, monkeypatch):
    # Simulate failure by making _mark_job_running raise.
    monkeypatch.setattr(tasks_mod, "_load_job", lambda db, jid: _make_snapshot(tasks_mod))
    monkeypatch.setattr(tasks_mod, "_mark_job_running", lambda db, jid: (_ for _ in ()).throw(RuntimeError("db down")))
    monkeypatch.setattr(tasks_mod, "_mark_job_failed", lambda db, jid, msg: None)

    tasks_mod.transcribe_job.run(FAKE_JOB_ID_STR)

    spans = [s for s in otel_exporter.get_finished_spans() if s.name == "worker.transcribe_job"]
    assert len(spans) == 1
    span = spans[0]
    assert span.status.status_code == StatusCode.ERROR
    exception_events = [e for e in span.events if e.name == "exception"]
    assert len(exception_events) >= 1


def _patch_celery_app(monkeypatch, fake_send_task):
    """Patch celery_app.celery_app using importlib.import_module so sys.modules is always current.

    tasks_mod fixture tears down by popping services.worker.app.celery_app from sys.modules.
    A plain `from package import submodule` after the pop retrieves the stale package attribute
    without re-registering the module in sys.modules, so _enqueue_transcribe's lazy import
    triggers a fresh reimport that bypasses the patch. importlib.import_module always ensures
    sys.modules registration.
    """
    import importlib
    from unittest.mock import MagicMock
    celery_module = importlib.import_module("services.worker.app.celery_app")
    mock_app = MagicMock()
    mock_app.send_task = fake_send_task
    monkeypatch.setattr(celery_module, "celery_app", mock_app)


def test_enqueue_injects_traceparent_when_inside_span(otel_exporter, monkeypatch):
    from services.api.app.main import _enqueue_transcribe

    sent_args: list = []

    def fake_send_task(name, args=None, **kwargs):
        sent_args.extend(args or [])

    _patch_celery_app(monkeypatch, fake_send_task)

    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("api-request"):
        _enqueue_transcribe(FAKE_JOB_ID_STR)

    assert len(sent_args) == 2
    assert sent_args[0] == FAKE_JOB_ID_STR
    traceparent = sent_args[1]
    assert traceparent is not None
    assert traceparent.startswith("00-"), f"Expected W3C traceparent, got: {traceparent!r}"


def test_enqueue_traceparent_is_none_outside_span(otel_exporter, monkeypatch):
    from services.api.app.main import _enqueue_transcribe

    sent_args: list = []

    def fake_send_task(name, args=None, **kwargs):
        sent_args.extend(args or [])

    _patch_celery_app(monkeypatch, fake_send_task)

    # Call outside any active span — no current context to inject
    _enqueue_transcribe(FAKE_JOB_ID_STR)

    assert len(sent_args) == 2
    assert sent_args[0] == FAKE_JOB_ID_STR
    assert sent_args[1] is None


def test_celery_apply_with_kwargs_propagates_traceparent_to_worker_span(otel_exporter, monkeypatch):
    """End-to-end Celery dispatch test using task.apply().

    Note: Celery's task_always_eager has no effect on celery_app.send_task() — only
    on Task.apply_async() / Task.delay(). The path send_task → broker → worker pulls
    → worker calls task is impossible to exercise without real Redis.  task.apply()
    uses the exact same downstream dispatcher (Signature -> apply -> task-call) that
    the worker process uses after pulling a message from Redis, so it covers the
    serialisation-equivalent argument passing and the worker's traceparent handling.

    This test verifies:
      1. The worker task receives the second positional arg (traceparent).
      2. The worker's propagate.extract(carrier) recognises the traceparent.
      3. The resulting context becomes the worker span's parent (same trace_id).

    A failure here would prove the bug is in our worker code, not in Celery transport.
    """
    for k, v in _REQUIRED_ENVS.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()

    sys.modules.pop("services.worker.app.tasks", None)
    sys.modules.pop("services.worker.app.celery_app", None)

    importlib.import_module("services.worker.app.celery_app")
    tasks_module = importlib.import_module("services.worker.app.tasks")

    # Stub all worker side-effects so transcribe_job runs to completion
    fake_snapshot = tasks_module.JobSnapshot(
        id=FAKE_JOB_ID,
        status=JobStatus.queued,
        raw_audio_uri=FAKE_RAW_AUDIO_URI,
    )
    monkeypatch.setattr(tasks_module, "_load_job", lambda db, jid: fake_snapshot)
    monkeypatch.setattr(tasks_module, "_mark_job_running", lambda db, jid: None)
    monkeypatch.setattr(tasks_module, "_mark_job_completed", lambda *a, **kw: None)
    monkeypatch.setattr(tasks_module, "_mark_job_failed", lambda *a, **kw: None)

    mock_storage = MagicMock()
    mock_storage.get_to_file.return_value = None
    mock_storage.put.return_value = FAKE_TRANSCRIPT_URI
    mock_storage.exists.return_value = True
    monkeypatch.setattr(tasks_module.StorageClient, "from_settings", lambda s: mock_storage)

    mock_adapter = MagicMock()
    mock_adapter.transcribe.return_value = FAKE_RESULT
    monkeypatch.setattr(tasks_module, "make_asr_adapter", lambda s: mock_adapter)

    # Dispatch from inside an active parent span (the API server-span analogue).
    tracer = trace.get_tracer("test-api")
    with tracer.start_as_current_span("api-server-span") as parent_span:
        parent_trace_id_hex = format(parent_span.get_span_context().trace_id, "032x")
        carrier: dict = {}
        propagate.inject(carrier)
        traceparent = carrier["traceparent"]

        # Task.apply() — synchronous dispatch through Celery's task pipeline.
        tasks_module.transcribe_job.apply(args=[FAKE_JOB_ID_STR, traceparent])

    spans = otel_exporter.get_finished_spans()
    worker_spans = [s for s in spans if s.name == "worker.transcribe_job"]
    assert worker_spans, (
        f"No worker.transcribe_job span emitted. All spans: {[s.name for s in spans]!r}"
    )
    worker_trace_id_hex = format(worker_spans[0].context.trace_id, "032x")
    assert worker_trace_id_hex == parent_trace_id_hex, (
        f"Trace IDs differ — parent={parent_trace_id_hex}, worker={worker_trace_id_hex}. "
        "The worker is not extracting/applying the traceparent as parent context."
    )

    # cleanup so subsequent tests get a fresh celery_app / tasks
    sys.modules.pop("services.worker.app.tasks", None)
    sys.modules.pop("services.worker.app.celery_app", None)
    get_settings.cache_clear()
