from __future__ import annotations

import os
import pytest

from opentelemetry import propagate, trace
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from libs.observability.tracing import (
    _reset_tracing_for_tests,
    configure_tracing,
    _TRACING_CONFIGURED,
)


@pytest.fixture(autouse=False)
def clean_tracing():
    """Reset OTel global state before and after each test that touches configure_tracing."""
    _reset_tracing_for_tests()
    yield
    _reset_tracing_for_tests()


# ---------------------------------------------------------------------------
# configure_tracing behaviour
# ---------------------------------------------------------------------------

def test_configure_tracing_returns_tracer_provider(clean_tracing):
    result = configure_tracing("test-svc")
    assert isinstance(result, TracerProvider)


def test_configure_tracing_sets_global_provider(clean_tracing):
    provider = configure_tracing("test-svc")
    assert trace.get_tracer_provider() is provider


def test_configure_tracing_is_idempotent_returns_same_provider(clean_tracing):
    p1 = configure_tracing("test-svc")
    p2 = configure_tracing("test-svc")
    assert p1 is p2


def test_configure_tracing_is_idempotent_no_duplicate_set_tracer_provider(clean_tracing, monkeypatch):
    call_count = 0

    original = trace.set_tracer_provider

    def counting_set(provider):
        nonlocal call_count
        call_count += 1
        original(provider)

    monkeypatch.setattr(trace, "set_tracer_provider", counting_set)
    configure_tracing("test-svc")
    configure_tracing("test-svc")
    assert call_count == 1


def test_configure_tracing_different_service_name_returns_first(clean_tracing):
    p_a = configure_tracing("svc-a")
    p_b = configure_tracing("svc-b")
    assert p_a is p_b  # second call returns first provider


def test_injected_exporter_uses_simple_span_processor(clean_tracing):
    exporter = InMemorySpanExporter()
    provider = configure_tracing("test-svc", exporter=exporter)
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("my-span"):
        pass
    finished = exporter.get_finished_spans()
    assert len(finished) == 1
    assert finished[0].name == "my-span"


def test_no_exporter_when_no_endpoint_env(clean_tracing, monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    provider = configure_tracing("test-svc")
    assert isinstance(provider, TracerProvider)
    # No assertion on span count — spans are silently dropped with no processor.


# ---------------------------------------------------------------------------
# Local provider — span attribute tests (do not touch global)
# ---------------------------------------------------------------------------

def _local_provider_with_exporter():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def test_span_captured_with_in_memory_exporter():
    provider, exporter = _local_provider_with_exporter()
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("local-span"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "local-span"


def test_span_job_id_attribute():
    provider, exporter = _local_provider_with_exporter()
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("span", attributes={"job.id": "uuid-123"}):
        pass
    span = exporter.get_finished_spans()[0]
    assert span.attributes["job.id"] == "uuid-123"


def test_span_has_service_name_resource(clean_tracing):
    exporter = InMemorySpanExporter()
    provider = configure_tracing("my-service", exporter=exporter)
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("span"):
        pass
    span = exporter.get_finished_spans()[0]
    assert span.resource.attributes[SERVICE_NAME] == "my-service"


# ---------------------------------------------------------------------------
# Propagation tests — local provider only
# ---------------------------------------------------------------------------

def test_traceparent_inject_and_extract():
    provider, exporter = _local_provider_with_exporter()
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("parent") as parent_span:
        carrier: dict = {}
        propagate.inject(carrier)
        assert "traceparent" in carrier
        ctx = propagate.extract(carrier)
        span_ctx = trace.get_current_span(ctx).get_span_context()
    assert span_ctx.trace_id == parent_span.get_span_context().trace_id


def test_propagation_links_child_span():
    provider, exporter = _local_provider_with_exporter()
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("parent") as parent_span:
        carrier: dict = {}
        propagate.inject(carrier)
        ctx = propagate.extract(carrier)

    with tracer.start_as_current_span("child", context=ctx) as child_span:
        pass

    child = exporter.get_finished_spans()[1]  # parent finishes first, child second
    assert child.parent is not None
    assert child.parent.span_id == parent_span.get_span_context().span_id


def test_independent_span_with_no_traceparent():
    provider, exporter = _local_provider_with_exporter()
    tracer = provider.get_tracer("test")
    ctx = propagate.extract({})
    with tracer.start_as_current_span("root", context=ctx):
        pass
    span = exporter.get_finished_spans()[0]
    assert span.parent is None


# ---------------------------------------------------------------------------
# _reset_tracing_for_tests correctness
# ---------------------------------------------------------------------------

def test_reset_tracing_for_tests_clears_state(clean_tracing):
    import libs.observability.tracing as tracing_mod
    configure_tracing("test-svc")
    assert tracing_mod._TRACING_CONFIGURED is True
    assert tracing_mod._TRACING_PROVIDER is not None

    _reset_tracing_for_tests()

    import opentelemetry.trace as _t
    assert tracing_mod._TRACING_CONFIGURED is False
    assert tracing_mod._TRACING_PROVIDER is None
    assert _t._TRACER_PROVIDER is None  # type: ignore[attr-defined]
