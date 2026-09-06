"""B12.1 JSONFormatter hard-deny + redaction contract.

The hard-deny field set in libs.observability.logging is the single source
of truth for log-surface privacy. This test installs the demo-api JSON
stream handler, emits sentinel records, and asserts the rendered JSON
does NOT contain any of the deny-listed field NAMES or VALUES, and that
existing `_REDACT_PATTERNS` continue to redact (not drop) generic key/secret
identifiers.
"""

from __future__ import annotations

import io
import json
import logging

from libs.observability.logging import (
    _DROP_FIELDS,
    JSONFormatter,
    configure_logging,
    sanitize_extra,
)


# Sentinels that we can safely pass via extra={...} (Python logging blocks
# overwriting built-in LogRecord attrs like "filename", so those are tested
# via direct LogRecord construction in the dedicated tests below).
_EXTRA_SAFE_SENTINELS = {
    "transcript": "SENTINEL_TRANSCRIPT_MUST_NOT_APPEAR",
    "hypothesis": "SENTINEL_HYPOTHESIS_MUST_NOT_APPEAR",
    "ground_truth": "SENTINEL_GT_MUST_NOT_APPEAR",
    "raw_payload": "SENTINEL_PAYLOAD_MUST_NOT_APPEAR",
    "session_id_hash": "SENTINEL_SESSION_HASH_MUST_NOT_APPEAR",
    "session_id": "SENTINEL_SESSION_ID_MUST_NOT_APPEAR",
    "ledger_id": "SENTINEL_LEDGER_MUST_NOT_APPEAR",
    "audio_path": "SENTINEL_AUDIO_PATH_MUST_NOT_APPEAR",
    "input_path": "SENTINEL_INPUT_PATH_MUST_NOT_APPEAR",
    "original_filename": "SENTINEL_ORIG_FILENAME_MUST_NOT_APPEAR",
    "cloudflared_url": "SENTINEL_CFD_URL_MUST_NOT_APPEAR",
}

# Full deny-list including names that COLLIDE with stdlib LogRecord attrs.
# These cannot be passed via logger.error(extra={...}) — Python logging
# raises KeyError. They are exercised by direct LogRecord construction so
# we still verify the formatter strips them before serialization.
_DROP_SENTINELS = {
    **_EXTRA_SAFE_SENTINELS,
    "filename": "SENTINEL_FILENAME_MUST_NOT_APPEAR",
}


def test_drop_fields_module_constant_covers_all_sentinels():
    for key in _DROP_SENTINELS:
        assert key in _DROP_FIELDS, f"{key} missing from _DROP_FIELDS"


def test_sanitize_extra_drops_deny_listed_fields_and_redacts_secrets():
    raw = {
        **_DROP_SENTINELS,
        "api_key": "should-be-redacted",
        "auth_header": "Basic should-be-redacted",
        "job_id": "ok-uuid",
        "duration_ms": 1.23,
    }
    out = sanitize_extra(raw)
    for key in _DROP_SENTINELS:
        assert key not in out
    assert out["api_key"] == "[REDACTED]"
    assert out["auth_header"] == "[REDACTED]"
    assert out["job_id"] == "ok-uuid"
    assert out["duration_ms"] == 1.23


def test_jsonformatter_drops_deny_listed_extras_in_rendered_json():
    """Pass deny-listed extras through logger.error(...) and confirm none
    appear in the rendered JSON line.

    "filename" cannot be passed via extra= (Python logging refuses to
    overwrite the built-in LogRecord attr); it is covered by the
    direct-record test below.
    """
    buf = io.StringIO()
    configure_logging("demo-api", stream=buf)
    log = logging.getLogger("demo-api.test_redaction")
    log.error("demo.test_redaction", extra=_EXTRA_SAFE_SENTINELS)
    rendered = buf.getvalue()
    for sentinel in _EXTRA_SAFE_SENTINELS.values():
        assert sentinel not in rendered, (
            f"sentinel value {sentinel!r} leaked into JSON line: {rendered!r}"
        )
    for key in _EXTRA_SAFE_SENTINELS:
        assert f'"{key}"' not in rendered, (
            f"deny-listed key {key!r} appeared in JSON line: {rendered!r}"
        )
    parsed = json.loads(rendered.strip().splitlines()[-1])
    assert parsed["event"] == "demo.test_redaction"
    assert parsed["service"] == "demo-api"
    assert parsed["level"] == "ERROR"


def test_jsonformatter_strips_filename_from_log_records():
    """The stdlib LogRecord ``filename`` attr (source-code filename of the
    log call) is stripped by the formatter's stdlib-skip layer. Construct
    a record directly so we can also exercise the deny-list path: even
    when an attacker bypasses the extra= collision check by setattr-ing
    ``filename`` to a sentinel, the rendered JSON must not include it.
    """
    from libs.observability.logging import JSONFormatter
    fmt = JSONFormatter("demo-api")
    rec = logging.LogRecord(
        name="demo-api.test", level=logging.ERROR, pathname=__file__,
        lineno=0, msg="demo.test_filename", args=(), exc_info=None,
    )
    rec.filename = "SENTINEL_FILENAME_MUST_NOT_APPEAR"
    out = fmt.format(rec)
    assert "SENTINEL_FILENAME_MUST_NOT_APPEAR" not in out
    parsed = json.loads(out)
    assert "filename" not in parsed


def test_jsonformatter_redacts_generic_secrets_without_dropping():
    buf = io.StringIO()
    configure_logging("demo-api", stream=buf)
    log = logging.getLogger("demo-api.test_redaction")
    log.info(
        "demo.test_secret",
        extra={"api_key": "should-not-leak", "authorization": "Bearer x"},
    )
    rendered = buf.getvalue()
    assert "should-not-leak" not in rendered
    assert "Bearer x" not in rendered
    assert "[REDACTED]" in rendered


def test_configure_logging_is_idempotent_does_not_double_log_or_duplicate_stream():
    buf = io.StringIO()
    configure_logging("demo-api", stream=buf)
    configure_logging("demo-api", stream=buf)
    configure_logging("demo-api", stream=buf)
    log = logging.getLogger("demo-api.test_idempotent")
    log.info("demo.test_idempotent")
    rendered = buf.getvalue()
    # Exactly one line per emit, despite three configure_logging calls.
    matching_lines = [
        line for line in rendered.splitlines()
        if '"event": "demo.test_idempotent"' in line
    ]
    assert len(matching_lines) == 1
    # Only one stream handler tagged for service "demo-api" survives.
    root = logging.root
    matching = [
        h for h in root.handlers
        if getattr(h, "_asr_managed_kind", None) == "stream"
        and getattr(h, "_asr_managed_service", None) == "demo-api"
    ]
    assert len(matching) == 1


def test_configure_logging_raw_formatter_uses_jsonformatter():
    fmt = JSONFormatter("demo-worker")
    rec = logging.LogRecord(
        name="demo-worker.test", level=logging.INFO, pathname=__file__,
        lineno=0, msg="demo.test", args=(), exc_info=None,
    )
    rec.transcript = "MUST_NOT_APPEAR"
    out = fmt.format(rec)
    assert "MUST_NOT_APPEAR" not in out
    assert json.loads(out)["service"] == "demo-worker"
