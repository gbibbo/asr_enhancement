from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import IO, Any, Iterable

_STDLIB_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message",
})

_REDACT_PATTERNS = frozenset({"key", "secret", "token", "authorization", "auth_header"})

# B12.1 hard-deny field set: dropped before serialization regardless of redaction.
# These names are not "redacted" with a placeholder; their PRESENCE is the
# signal we want to suppress from the log surface so that even an accidental
# extra={...} call cannot leak them. Single source of truth — JSONFormatter
# AND libs/observability/error_buffer must both go through sanitize_extra().
_DROP_FIELDS = frozenset({
    # transcripts and references
    "transcript", "text", "hypothesis",
    "reference", "reference_text", "ground_truth", "gt",
    # provider raw payloads
    "raw_payload", "provider_payload",
    # session identifiers (B10.2 invariant)
    "session_id", "session_id_hash",
    # ledger row identifiers (B10.1 invariant)
    "ledger_id",
    # filesystem paths and per-job artifact paths
    "audio_path", "input_path", "degraded_path", "enhanced_path",
    "input_artifact_path", "degraded_artifact_path",
    "enhanced_artifact_path", "result_path",
    # upload filenames
    "filename", "original_filename", "upload_filename",
    # cloudflared
    "cloudflared_url", "tunnel_token",
})


def _should_redact(field_name: str) -> bool:
    name_lower = field_name.lower()
    return any(pattern in name_lower for pattern in _REDACT_PATTERNS)


def _should_drop(field_name: str) -> bool:
    return field_name.lower() in _DROP_FIELDS


def sanitize_extra(extra: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``extra`` with hard-deny fields dropped and redactable
    fields replaced by ``[REDACTED]``. Single source of truth for log-surface
    privacy filtering — used by JSONFormatter and the error ring buffer.
    """
    out: dict[str, Any] = {}
    for key, value in extra.items():
        if _should_drop(key):
            continue
        if _should_redact(key):
            out[key] = "[REDACTED]"
        else:
            out[key] = value
    return out


class JSONFormatter(logging.Formatter):
    def __init__(self, service: str) -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
        timestamp = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(record.msecs):03d}Z"

        output: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "event": record.getMessage(),
            "service": self._service,
            "logger": record.name,
        }

        record_extras: dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key in _STDLIB_RECORD_ATTRS:
                continue
            record_extras[key] = value
        for key, value in sanitize_extra(record_extras).items():
            output[key] = value

        if record.exc_info:
            output["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(output)


def _is_managed_handler(handler: logging.Handler) -> bool:
    """Return True for handlers this module installed (any kind/service)."""
    return bool(getattr(handler, "_asr_managed", False)) or bool(
        getattr(handler, "_asr_json_logging", False)
    )


def _matches_service(handler: logging.Handler, service: str) -> bool:
    """Return True for managed handlers tagged for the given service.

    Untagged legacy stream handlers (only `_asr_json_logging`) are treated as
    matching any service so the legacy single-stream-handler invariant is
    preserved across upgrades.
    """
    if not _is_managed_handler(handler):
        return False
    tagged = getattr(handler, "_asr_managed_service", None)
    if tagged is None:
        # Legacy ASR JSON stream handler with no service tag — replace.
        return True
    return tagged == service


def configure_logging(
    service: str,
    level: str = "INFO",
    stream: IO[str] | None = None,
    *,
    extra_handlers: Iterable[logging.Handler] | None = None,
) -> None:
    """Install one stream JSON handler at the root logger plus any extras.

    Idempotent across repeated calls with the same ``service``: previously
    installed managed handlers tagged for this service are removed and
    closed before the new handlers are added, so the handler count does not
    grow when (e.g.) a TestClient lifespan re-runs lifespan setup. Handlers
    from other origins (pytest's caplog, other services) are preserved.

    ``extra_handlers`` may carry e.g. a RotatingFileHandler from
    libs.observability.log_rotation or an ErrorBufferHandler from
    libs.observability.error_buffer. Each extra handler is tagged so the
    next configure_logging call drops it cleanly.
    """
    if stream is None:
        stream = sys.stderr

    root = logging.root

    # Drop previously managed handlers for THIS service (and any legacy
    # untagged ASR stream handler). Close file/stream handlers we owned so
    # OS-level handles do not leak across reconfigurations.
    keep: list[logging.Handler] = []
    for h in root.handlers:
        if _matches_service(h, service):
            try:
                h.close()
            except Exception:  # noqa: BLE001
                pass
            continue
        keep.append(h)
    root.handlers = keep

    # Install exactly one new ASR JSON stream handler tagged for this service.
    stream_handler = logging.StreamHandler(stream)
    stream_handler.setFormatter(JSONFormatter(service))
    stream_handler._asr_json_logging = True  # type: ignore[attr-defined]
    stream_handler._asr_managed = True  # type: ignore[attr-defined]
    stream_handler._asr_managed_kind = "stream"  # type: ignore[attr-defined]
    stream_handler._asr_managed_service = service  # type: ignore[attr-defined]
    root.addHandler(stream_handler)

    if extra_handlers:
        for h in extra_handlers:
            if h is None:
                continue
            # Tag externally-provided extras so the next configure_logging
            # call removes them cleanly. Callers may set `_asr_managed_kind`
            # themselves; we only set defaults if missing.
            if not getattr(h, "_asr_managed", False):
                h._asr_managed = True  # type: ignore[attr-defined]
            if not getattr(h, "_asr_managed_kind", None):
                h._asr_managed_kind = "extra"  # type: ignore[attr-defined]
            h._asr_managed_service = service  # type: ignore[attr-defined]
            root.addHandler(h)

    root.setLevel(level)
