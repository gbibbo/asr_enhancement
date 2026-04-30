from __future__ import annotations

from libs.observability.metrics import (
    API_ERRORS,
    API_REQUESTS,
    CONTENT_TYPE_LATEST,
    JOB_COUNTER,
    WORKER_HEARTBEAT,
    get_metrics_output,
)


def _samples(output: str, metric_name: str) -> list[str]:
    """Return non-comment data lines for the given metric name."""
    return [
        line for line in output.splitlines()
        if (
            line.startswith(metric_name + "{") or line.startswith(metric_name + " ")
        ) and not line.startswith("#")
    ]


# ---------------------------------------------------------------------------
# Import / existence tests
# ---------------------------------------------------------------------------

def test_api_requests_counter_is_importable():
    assert API_REQUESTS is not None


def test_api_errors_counter_is_importable():
    assert API_ERRORS is not None


def test_job_counter_is_importable():
    assert JOB_COUNTER is not None


def test_worker_heartbeat_gauge_is_importable():
    assert WORKER_HEARTBEAT is not None


def test_content_type_latest_is_importable():
    assert CONTENT_TYPE_LATEST is not None
    assert "text/plain" in CONTENT_TYPE_LATEST


# ---------------------------------------------------------------------------
# get_metrics_output tests
# ---------------------------------------------------------------------------

def test_get_metrics_output_returns_bytes():
    assert isinstance(get_metrics_output(), bytes)


def test_output_contains_api_requests_definition():
    output = get_metrics_output().decode("utf-8")
    assert "asr_api_requests_total" in output


def test_output_contains_api_errors_definition():
    output = get_metrics_output().decode("utf-8")
    assert "asr_api_errors_total" in output


def test_output_contains_job_counter_definition():
    output = get_metrics_output().decode("utf-8")
    assert "asr_jobs_total" in output


def test_output_contains_worker_heartbeat_definition():
    output = get_metrics_output().decode("utf-8")
    assert "asr_worker_heartbeat_timestamp_seconds" in output


# ---------------------------------------------------------------------------
# Sample appearance tests (increments + set)
# ---------------------------------------------------------------------------

def test_api_requests_sample_appears_after_inc():
    API_REQUESTS.labels(method="GET", path="/unit_test_path", status_code="200").inc()
    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_api_requests_total")
    assert any(
        'method="GET"' in s and 'path="/unit_test_path"' in s and 'status_code="200"' in s
        for s in samples
    )


def test_job_counter_sample_appears_after_inc():
    JOB_COUNTER.labels(status="queued", mode="transcribe_only_unit_test").inc()
    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_jobs_total")
    assert any(
        'status="queued"' in s and 'mode="transcribe_only_unit_test"' in s
        for s in samples
    )


def test_worker_heartbeat_value_appears_after_set():
    WORKER_HEARTBEAT.set(1234567890.0)
    output = get_metrics_output().decode("utf-8")
    # prometheus-client may render large floats in scientific notation (e.g. 1.23456789e+09)
    lines = [
        ln for ln in output.splitlines()
        if ln.startswith("asr_worker_heartbeat_timestamp_seconds ")
    ]
    assert len(lines) > 0, "Expected a data line for asr_worker_heartbeat_timestamp_seconds"
    value = float(lines[0].split()[-1])
    assert abs(value - 1234567890.0) < 1.0
