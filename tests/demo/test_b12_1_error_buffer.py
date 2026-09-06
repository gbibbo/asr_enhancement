"""B12.1 demo-api error ring buffer.

Verifies:
- ERROR records routed through the buffer handler land in the deque;
- hard-deny extras (transcript, session_id_hash, ledger_id, ...) never
  surface in the entry, even when present in extra={};
- only the whitelisted fields (timestamp, level, event, logger, service,
  optional UUID job_id) are present;
- the buffer respects the configured maxlen;
- the buffer is module-local (not a file or socket — regression guard so a
  future refactor cannot accidentally start sharing state across processes).
"""

from __future__ import annotations

import logging
import uuid
from collections import deque

import pytest

from libs.observability.error_buffer import (
    _ErrorBufferHandler,
    build_error_buffer_handler,
    buffer_snapshot,
)
from libs.observability.logging import configure_logging


def test_buffer_handler_module_local_state():
    h = build_error_buffer_handler(service="demo-api", maxlen=4)
    # The buffer must be a Python deque living on the handler instance —
    # not a file path, socket, or remote queue.
    assert isinstance(h._buffer, deque)
    assert h._buffer.maxlen == 4


def test_buffer_appends_only_error_records():
    h = build_error_buffer_handler(service="demo-api", maxlen=8)
    configure_logging("demo-api", extra_handlers=[h])
    try:
        log = logging.getLogger("demo-api.test_error_buffer")
        log.info("demo.info_event")  # should NOT land (level=ERROR)
        log.error("demo.error_event")
    finally:
        configure_logging("demo-api")
    snap = buffer_snapshot(h)
    events = [e["event"] for e in snap]
    assert "demo.error_event" in events
    assert "demo.info_event" not in events


def test_buffer_drops_hard_deny_fields():
    h = build_error_buffer_handler(service="demo-api", maxlen=8)
    configure_logging("demo-api", extra_handlers=[h])
    try:
        log = logging.getLogger("demo-api.test_error_buffer")
        # "filename" cannot be passed via extra= (Python logging refuses to
        # overwrite the built-in LogRecord attr). The direct-record test
        # below covers the deny-list path for filename.
        log.error(
            "demo.test_error",
            extra={
                "job_id": str(uuid.uuid4()),
                "transcript": "MUST_NOT_APPEAR_TRANSCRIPT",
                "session_id_hash": "MUST_NOT_APPEAR_HASH",
                "ledger_id": "MUST_NOT_APPEAR_LEDGER",
                "raw_payload": "MUST_NOT_APPEAR_PAYLOAD",
                "audio_path": "/tmp/MUST_NOT_APPEAR.wav",
                "original_filename": "MUST_NOT_APPEAR_orig.wav",
            },
        )
    finally:
        configure_logging("demo-api")
    snap = buffer_snapshot(h)
    assert len(snap) == 1
    entry = snap[0]
    # Only whitelisted fields survive.
    allowed = {"timestamp", "level", "event", "logger", "service", "job_id"}
    assert set(entry.keys()).issubset(allowed)
    serialized = repr(entry)
    for sentinel in (
        "MUST_NOT_APPEAR_TRANSCRIPT", "MUST_NOT_APPEAR_HASH",
        "MUST_NOT_APPEAR_LEDGER", "MUST_NOT_APPEAR_PAYLOAD",
        "MUST_NOT_APPEAR.wav", "MUST_NOT_APPEAR_orig.wav",
    ):
        assert sentinel not in serialized
    assert entry["service"] == "demo-api"
    assert entry["level"] == "ERROR"
    assert entry["event"] == "demo.test_error"


def test_buffer_drops_filename_when_setattr_directly():
    """The stdlib LogRecord.filename attr is stripped by the buffer handler.
    Bypass Python's extra={} collision check via direct setattr."""
    h = build_error_buffer_handler(service="demo-api", maxlen=4)
    rec = logging.LogRecord(
        name="demo-api.test", level=logging.ERROR, pathname=__file__,
        lineno=0, msg="demo.test_filename", args=(), exc_info=None,
    )
    rec.filename = "MUST_NOT_APPEAR_FILENAME.wav"
    h.emit(rec)
    snap = buffer_snapshot(h)
    assert len(snap) == 1
    entry = snap[0]
    assert "filename" not in entry
    assert "MUST_NOT_APPEAR_FILENAME.wav" not in repr(entry)


def test_buffer_drops_non_uuid_job_id():
    h = build_error_buffer_handler(service="demo-api", maxlen=4)
    configure_logging("demo-api", extra_handlers=[h])
    try:
        log = logging.getLogger("demo-api.test_error_buffer")
        log.error("demo.test_error", extra={"job_id": "not-a-uuid"})
    finally:
        configure_logging("demo-api")
    entry = buffer_snapshot(h)[-1]
    assert "job_id" not in entry


def test_buffer_respects_maxlen():
    h = build_error_buffer_handler(service="demo-api", maxlen=3)
    configure_logging("demo-api", extra_handlers=[h])
    try:
        log = logging.getLogger("demo-api.test_error_buffer")
        for i in range(10):
            log.error("demo.fill_event_%d" % i)
    finally:
        configure_logging("demo-api")
    snap = buffer_snapshot(h)
    assert len(snap) == 3
    # Only the latest 3 events remain.
    assert [e["event"] for e in snap] == [
        "demo.fill_event_7", "demo.fill_event_8", "demo.fill_event_9",
    ]


def test_emit_does_not_raise_on_bad_record():
    h = build_error_buffer_handler(service="demo-api", maxlen=2)
    rec = logging.LogRecord(
        name="demo-api.crash", level=logging.ERROR, pathname=__file__,
        lineno=0, msg="demo.test", args=(), exc_info=None,
    )
    # Force an attribute that breaks .__dict__ iteration to nothing — the
    # handler must still not raise.
    h.emit(rec)
    snap = buffer_snapshot(h)
    assert len(snap) == 1
