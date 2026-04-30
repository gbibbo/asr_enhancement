from __future__ import annotations

import io
import json
import logging

import pytest

from libs.observability import JSONFormatter, configure_logging


# ---------------------------------------------------------------------------
# Autouse fixture: remove ASR-tagged handlers before/after every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_root_handlers():
    _remove_asr_handlers()
    yield
    _remove_asr_handlers()


def _remove_asr_handlers() -> None:
    logging.root.handlers = [
        h for h in logging.root.handlers
        if not getattr(h, "_asr_json_logging", False)
    ]


# ---------------------------------------------------------------------------
# Helper: build a LogRecord with optional extra fields
# ---------------------------------------------------------------------------

def _make_record(
    msg: str = "test message",
    level: int = logging.INFO,
    extra: dict | None = None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test.logger",
        level=level,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    if extra:
        for k, v in extra.items():
            setattr(record, k, v)
    return record


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------

def test_format_produces_valid_json():
    fmt = JSONFormatter("api")
    record = _make_record()
    output = fmt.format(record)
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_format_has_required_fields():
    fmt = JSONFormatter("api")
    record = _make_record()
    parsed = json.loads(fmt.format(record))
    for field in ("timestamp", "level", "event", "service", "logger"):
        assert field in parsed, f"missing field: {field}"


def test_format_includes_safe_extra_fields():
    fmt = JSONFormatter("worker")
    record = _make_record(extra={"job_id": "abc-123"})
    parsed = json.loads(fmt.format(record))
    assert parsed["job_id"] == "abc-123"


def test_format_level_is_string():
    fmt = JSONFormatter("api")
    record = _make_record(level=logging.INFO)
    parsed = json.loads(fmt.format(record))
    assert parsed["level"] == "INFO"
    assert isinstance(parsed["level"], str)


def test_format_event_is_message():
    fmt = JSONFormatter("api")
    record = _make_record(msg="hello %s", extra=None)
    record.args = ("world",)
    parsed = json.loads(fmt.format(record))
    assert parsed["event"] == "hello world"


def test_format_exception_renders_as_string():
    fmt = JSONFormatter("api")
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
    record = _make_record()
    record.exc_info = exc_info
    parsed = json.loads(fmt.format(record))
    assert "exception" in parsed
    assert isinstance(parsed["exception"], str)
    assert "ValueError" in parsed["exception"]


def test_format_no_reserved_field_leakage():
    fmt = JSONFormatter("api")
    record = _make_record()
    parsed = json.loads(fmt.format(record))
    for reserved in ("msg", "args", "levelname", "lineno", "funcName"):
        assert reserved not in parsed, f"reserved field leaked: {reserved}"


# ---------------------------------------------------------------------------
# Redaction tests
# ---------------------------------------------------------------------------

def test_redact_api_key():
    fmt = JSONFormatter("api")
    record = _make_record(extra={"api_key": "mysecret"})
    parsed = json.loads(fmt.format(record))
    assert parsed["api_key"] == "[REDACTED]"


def test_redact_authorization():
    fmt = JSONFormatter("api")
    record = _make_record(extra={"Authorization": "Bearer tok"})
    parsed = json.loads(fmt.format(record))
    assert parsed["Authorization"] == "[REDACTED]"


def test_redact_minio_secret_key():
    fmt = JSONFormatter("api")
    record = _make_record(extra={"minio_secret_key": "s3cr3t"})
    parsed = json.loads(fmt.format(record))
    assert parsed["minio_secret_key"] == "[REDACTED]"


def test_safe_fields_not_redacted():
    fmt = JSONFormatter("api")
    safe = {
        "job_id": "abc",
        "mode": "transcribe_only",
        "preset": "bypass",
        "method": "POST",
        "path": "/v1/transcribe",
        "status_code": 202,
        "duration_ms": 12.3,
    }
    record = _make_record(extra=safe)
    parsed = json.loads(fmt.format(record))
    for field, expected in safe.items():
        assert parsed[field] == expected, f"field {field!r} was unexpectedly redacted"


def test_redacted_value_absent_from_json_string():
    fmt = JSONFormatter("api")
    record = _make_record(extra={"minio_secret_key": "s3cr3t_value"})
    json_string = fmt.format(record)
    assert "s3cr3t_value" not in json_string


# ---------------------------------------------------------------------------
# configure_logging tests
# ---------------------------------------------------------------------------

def test_configure_logging_exactly_one_handler():
    buf = io.StringIO()
    configure_logging("api", stream=buf)
    asr_handlers = [
        h for h in logging.root.handlers
        if getattr(h, "_asr_json_logging", False)
    ]
    assert len(asr_handlers) == 1


def test_configure_logging_idempotent_no_duplicates():
    buf = io.StringIO()
    configure_logging("api", stream=buf)
    configure_logging("api", stream=buf)
    asr_handlers = [
        h for h in logging.root.handlers
        if getattr(h, "_asr_json_logging", False)
    ]
    assert len(asr_handlers) == 1


def test_configure_logging_one_json_line_emitted():
    buf = io.StringIO()
    configure_logging("api", level="DEBUG", stream=buf)
    logging.getLogger("test.emit").info("hello world")
    lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["event"] == "hello world"
    assert parsed["service"] == "api"
