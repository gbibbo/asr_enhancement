from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    generate_latest,
    start_http_server,
)

REGISTRY = CollectorRegistry()

API_REQUESTS = Counter(
    "asr_api_requests_total",
    "Total HTTP requests handled",
    ["method", "path", "status_code"],
    registry=REGISTRY,
)

API_ERRORS = Counter(
    "asr_api_errors_total",
    "Total unhandled API errors",
    ["path"],
    registry=REGISTRY,
)

JOB_COUNTER = Counter(
    "asr_jobs_total",
    "Total jobs by status and mode",
    ["status", "mode"],
    registry=REGISTRY,
)

WORKER_HEARTBEAT = Gauge(
    "asr_worker_heartbeat_timestamp_seconds",
    "Unix timestamp of last worker heartbeat",
    registry=REGISTRY,
)

QUEUE_BACKLOG = Gauge(
    "asr_queue_backlog_jobs",
    "Number of jobs waiting in the Celery default queue",
    registry=REGISTRY,
)


def get_metrics_output() -> bytes:
    """Return Prometheus text format for the ASR registry."""
    return generate_latest(REGISTRY)


def start_worker_metrics_server(port: int = 9091) -> None:
    """Start a Prometheus HTTP metrics server exposing the ASR registry."""
    start_http_server(port, registry=REGISTRY)
