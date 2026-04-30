from __future__ import annotations

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
