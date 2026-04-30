from __future__ import annotations

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter

_TRACING_CONFIGURED: bool = False
_TRACING_PROVIDER: Optional[TracerProvider] = None


def configure_tracing(
    service_name: str,
    exporter: Optional[SpanExporter] = None,
) -> TracerProvider:
    """Initialise the global OTel TracerProvider. Idempotent — safe to call multiple times.

    Injected exporter uses SimpleSpanProcessor (synchronous, for tests).
    Runtime OTLP uses BatchSpanProcessor (non-blocking background thread).
    If neither is supplied, a provider is created with no exporter (spans are dropped).
    """
    global _TRACING_CONFIGURED, _TRACING_PROVIDER
    if _TRACING_CONFIGURED and _TRACING_PROVIDER is not None:
        return _TRACING_PROVIDER

    resource = Resource({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    if exporter is not None:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    elif (endpoint := os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        otlp = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(otlp))

    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True
    _TRACING_PROVIDER = provider
    return provider


def _reset_tracing_for_tests() -> None:
    """Reset OTel global provider and its set-once guard. Test-only — never call in production."""
    global _TRACING_CONFIGURED, _TRACING_PROVIDER
    _TRACING_CONFIGURED = False
    _TRACING_PROVIDER = None
    import opentelemetry.trace as _t
    from opentelemetry.util._once import Once
    _t._TRACER_PROVIDER = None
    _t._TRACER_PROVIDER_SET_ONCE = Once()
