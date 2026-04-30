from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from libs.observability.tracing import _reset_tracing_for_tests, configure_tracing
from services.api.app.main import app


@pytest.fixture
def otel_exporter():
    """Set up a fresh OTel provider and force re-instrumentation with that provider's tracer.

    FastAPIInstrumentor captures the tracer into a build_middleware_stack closure at
    instrument_app() call time.  If a prior test cleared the provider (via
    _reset_tracing_for_tests) and the idempotency guard prevents re-instrumentation,
    the stale tracer from the cleared provider is reused and spans are dropped.
    Explicitly uninstrumenting and reinstrumenting with the new tracer avoids this.
    """
    _reset_tracing_for_tests()
    exporter = InMemorySpanExporter()
    configure_tracing("asr-api", exporter=exporter)
    FastAPIInstrumentor.uninstrument_app(app)
    FastAPIInstrumentor().instrument_app(app)
    app.middleware_stack = None
    assert isinstance(trace.get_tracer_provider(), TracerProvider)
    yield exporter
    _reset_tracing_for_tests()
    FastAPIInstrumentor.uninstrument_app(app)
    exporter.clear()


def test_instrument_app_is_idempotent(otel_exporter):
    FastAPIInstrumentor().instrument_app(app)
    assert app._is_instrumented_by_opentelemetry is True
    FastAPIInstrumentor().instrument_app(app)
    assert app._is_instrumented_by_opentelemetry is True


def test_health_request_produces_span(otel_exporter):
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    spans = otel_exporter.get_finished_spans()
    assert len(spans) > 0
    assert any("/health" in s.name or "GET /health" in s.name for s in spans)


def test_double_testclient_does_not_duplicate_spans(otel_exporter):
    with TestClient(app) as client:
        client.get("/health")

    spans_first = len(otel_exporter.get_finished_spans())
    otel_exporter.clear()

    with TestClient(app) as client:
        client.get("/health")

    spans_second = len(otel_exporter.get_finished_spans())
    assert spans_first == spans_second
    assert app._is_instrumented_by_opentelemetry is True


def test_app_is_instrumented_at_module_import():
    """Regression for the WSL Docker failure on commit a674f90.

    Lifespan-time instrumentation came too late: Starlette built and cached
    app.middleware_stack on the first ASGI call (the lifespan event itself),
    so FastAPIInstrumentor().instrument_app(app) inside lifespan patched
    build_middleware_stack but never reached the cached stack. HTTP requests
    reused the cached non-OTel stack and produced no spans.

    Run in a subprocess to verify the fresh import-time state of the module,
    independent of any in-process pytest fixture instrument/uninstrument cycle.
    """
    code = (
        "import os; "
        "os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://x:x@localhost/x'); "
        "os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0'); "
        "os.environ.setdefault('MINIO_ENDPOINT', 'localhost:9000'); "
        "os.environ.setdefault('MINIO_ACCESS_KEY', 'k'); "
        "os.environ.setdefault('MINIO_SECRET_KEY', 's'); "
        "from services.api.app.main import app; "
        "print(int(getattr(app, '_is_instrumented_by_opentelemetry', False)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"Module import failed.\nstdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )
    assert result.stdout.strip() == "1", (
        f"App was not instrumented at module import. stdout: {result.stdout!r}"
    )


def test_post_v1_transcribe_during_request_sends_traceparent_to_celery(
    otel_exporter, monkeypatch, tmp_path
):
    """Regression: a real instrumented HTTP request to /v1/transcribe must
    inject a non-empty traceparent into the Celery task args, and that
    traceparent's trace_id must match the API request span's trace_id."""
    import importlib

    from libs.common.settings import get_settings
    from services.api.app import main as main_mod

    # Settings used by the /v1/transcribe route
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:x@localhost/x")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "k")
    monkeypatch.setenv("MINIO_SECRET_KEY", "s")
    monkeypatch.setenv("MINIO_BUCKET", "asr-platform")
    get_settings.cache_clear()

    # Capture send_task args
    sent: list = []

    def fake_send_task(name, args=None, **kwargs):
        sent.append({"name": name, "args": args})

    # Patch celery_app.celery_app at the module level (importlib ensures sys.modules
    # registration); _enqueue_transcribe imports lazily and will pick up the mock.
    celery_module = importlib.import_module("services.worker.app.celery_app")
    mock_celery = MagicMock()
    mock_celery.send_task = fake_send_task
    monkeypatch.setattr(celery_module, "celery_app", mock_celery)

    # Stub all DB / storage / job-creation side effects so the request reaches
    # _enqueue_transcribe without external services.
    import uuid as _uuid

    fake_job_id = _uuid.uuid4()
    monkeypatch.setattr(main_mod, "_create_job", lambda *a, **kw: fake_job_id)
    monkeypatch.setattr(main_mod, "_upload_raw_audio", lambda *a, **kw: f"s3://bucket/raw_audio/{fake_job_id}/input.wav")
    monkeypatch.setattr(main_mod, "_set_raw_audio_uri", lambda *a, **kw: None)
    monkeypatch.setattr(main_mod, "_mark_job_failed", lambda *a, **kw: None)

    # Build a tiny WAV file so the upload validator passes
    import wave
    wav_path = tmp_path / "tiny.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)

    with TestClient(app) as client:
        with wav_path.open("rb") as f:
            resp = client.post(
                "/v1/transcribe",
                files={"file": ("tiny.wav", f, "audio/wav")},
            )
    assert resp.status_code == 202, resp.text

    # Exactly one Celery enqueue with [job_id, traceparent]
    assert len(sent) == 1, f"Expected 1 send_task call, got {len(sent)}: {sent}"
    name = sent[0]["name"]
    args = sent[0]["args"]
    assert name == "worker.transcribe_job"
    assert isinstance(args, list) and len(args) == 2
    job_id_arg, traceparent = args
    assert job_id_arg == str(fake_job_id)
    assert traceparent is not None and traceparent.startswith("00-"), (
        f"Expected non-empty W3C traceparent, got {traceparent!r}"
    )

    # API span trace_id must match the traceparent's trace_id field (00-<trace>-<span>-<flags>)
    spans = otel_exporter.get_finished_spans()
    assert spans, "No API span captured; FastAPIInstrumentor not active on the request path."
    transcribe_spans = [s for s in spans if "/v1/transcribe" in s.name]
    assert transcribe_spans, f"No /v1/transcribe span. Spans seen: {[s.name for s in spans]}"
    api_trace_id_hex = format(transcribe_spans[0].context.trace_id, "032x")
    traceparent_trace_id = traceparent.split("-")[1]
    assert api_trace_id_hex == traceparent_trace_id, (
        f"trace_id mismatch — API span={api_trace_id_hex}, traceparent={traceparent_trace_id}"
    )


def test_route_captures_traceparent_outside_threadpool(otel_exporter, monkeypatch, tmp_path):
    """Regression for the WSL Docker failure on commit 0db0a8b.

    A previous implementation injected traceparent INSIDE _enqueue_transcribe,
    which runs via asyncio.to_thread.  In production under uvicorn, the active
    OTel server span's contextvars did not propagate reliably into the threadpool
    worker, so propagate.inject(carrier) returned an empty carrier and the worker
    received traceparent=None — creating a fresh root span with a different
    trace_id.

    The fix captures traceparent in the async route context (where the
    FastAPIInstrumentor server span is guaranteed active) and passes it to
    _enqueue_transcribe as an explicit positional argument.

    This test verifies the route hands a non-None traceparent — matching the
    /v1/transcribe span's trace_id — directly into _enqueue_transcribe, with no
    reliance on contextvars propagation through asyncio.to_thread.
    """
    import importlib

    from libs.common.settings import get_settings
    from services.api.app import main as main_mod

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:x@localhost/x")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "k")
    monkeypatch.setenv("MINIO_SECRET_KEY", "s")
    monkeypatch.setenv("MINIO_BUCKET", "asr-platform")
    get_settings.cache_clear()

    # Capture _enqueue_transcribe's actual call args. If the route did not pass
    # traceparent as the second positional, this test will fail.
    captured: list = []

    def capturing_enqueue(*args, **kwargs):
        captured.append({"args": args, "kwargs": kwargs})

    monkeypatch.setattr(main_mod, "_enqueue_transcribe", capturing_enqueue)

    import uuid as _uuid
    fake_job_id = _uuid.uuid4()
    monkeypatch.setattr(main_mod, "_create_job", lambda *a, **kw: fake_job_id)
    monkeypatch.setattr(main_mod, "_upload_raw_audio", lambda *a, **kw: f"s3://bucket/raw_audio/{fake_job_id}/input.wav")
    monkeypatch.setattr(main_mod, "_set_raw_audio_uri", lambda *a, **kw: None)
    monkeypatch.setattr(main_mod, "_mark_job_failed", lambda *a, **kw: None)

    import wave
    wav_path = tmp_path / "tiny.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)

    with TestClient(app) as client:
        with wav_path.open("rb") as f:
            resp = client.post(
                "/v1/transcribe",
                files={"file": ("tiny.wav", f, "audio/wav")},
            )
    assert resp.status_code == 202, resp.text

    # Exactly one _enqueue_transcribe call with both job_id AND traceparent.
    assert len(captured) == 1, f"Expected 1 _enqueue_transcribe call, got {len(captured)}"
    args = captured[0]["args"]
    assert len(args) == 2, (
        f"Route must pass traceparent as second positional. Got args={args!r}. "
        "Capturing inside asyncio.to_thread is the bug this test guards against."
    )
    job_id_arg, traceparent = args
    assert job_id_arg == str(fake_job_id)
    assert traceparent is not None, (
        "traceparent is None — route did not capture it in async context."
    )
    assert traceparent.startswith("00-"), f"Bad W3C traceparent: {traceparent!r}"

    # And the captured traceparent must reference the /v1/transcribe span.
    spans = otel_exporter.get_finished_spans()
    transcribe_spans = [s for s in spans if "/v1/transcribe" in s.name]
    assert transcribe_spans, f"No /v1/transcribe span. Spans: {[s.name for s in spans]}"
    api_trace_id_hex = format(transcribe_spans[0].context.trace_id, "032x")
    traceparent_trace_id = traceparent.split("-")[1]
    assert api_trace_id_hex == traceparent_trace_id, (
        f"Captured traceparent's trace_id ({traceparent_trace_id}) does not match "
        f"the API span's trace_id ({api_trace_id_hex})."
    )
