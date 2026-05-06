"""Demo-api process-local error ring buffer (B12.1).

A bounded ``collections.deque`` of recent ERROR/CRITICAL events is exposed to
``/admin/stats.last_errors``. The handler runs the same hard-deny + redaction
sanitizer used by ``JSONFormatter`` so even an accidental
``logger.error("...", extra={"transcript": "..."})`` call cannot leak into
the admin response.

**Scope is explicit and process-local**: only events emitted inside the
demo-api process land here. The demo-worker is a separate process; its
errors do NOT appear in this buffer. Worker error visibility is provided by
``demo.worker.log`` once file logging is enabled in the demo Compose. B12.1
does not introduce any cross-process error store (DB row, file tail, IPC) —
sharing errors across processes would require a new safe mechanism that is
out of scope.

Records persisted in the buffer carry only:
``timestamp``, ``level``, ``event``, ``logger``, ``service``, and ``job_id``
(when present and shaped like a UUID).
"""

from __future__ import annotations

import logging
import re
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque

from libs.observability.logging import sanitize_extra

_STDLIB_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message",
})

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class _ErrorBufferHandler(logging.Handler):
    """Append sanitized error records to a bounded deque.

    Module-local state — instances do not share a buffer across processes.
    """

    def __init__(self, *, service: str, maxlen: int) -> None:
        super().__init__(level=logging.ERROR)
        self._service = service
        self._buffer: Deque[dict[str, Any]] = deque(maxlen=maxlen)

    @property
    def buffer(self) -> Deque[dict[str, Any]]:
        return self._buffer

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            ts = datetime.fromtimestamp(record.created, tz=timezone.utc)
            timestamp = ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(record.msecs):03d}Z"

            raw_extras: dict[str, Any] = {}
            for key, value in record.__dict__.items():
                if key in _STDLIB_RECORD_ATTRS:
                    continue
                raw_extras[key] = value
            safe_extras = sanitize_extra(raw_extras)

            entry: dict[str, Any] = {
                "timestamp": timestamp,
                "level": record.levelname,
                "event": record.getMessage(),
                "logger": record.name,
                "service": self._service,
            }
            job_id = safe_extras.get("job_id")
            if isinstance(job_id, str) and _UUID_RE.match(job_id):
                entry["job_id"] = job_id
            self._buffer.append(entry)
        except Exception:  # noqa: BLE001
            # A logging handler must never raise. Drop the record silently.
            self.handleError(record)


def build_error_buffer_handler(
    *,
    service: str = "demo-api",
    maxlen: int = 20,
) -> _ErrorBufferHandler:
    """Return a tagged error-buffer handler ready for configure_logging."""
    handler = _ErrorBufferHandler(service=service, maxlen=maxlen)
    handler._asr_managed = True  # type: ignore[attr-defined]
    handler._asr_managed_kind = "buffer"  # type: ignore[attr-defined]
    handler._asr_managed_service = service  # type: ignore[attr-defined]
    return handler


def buffer_snapshot(handler: _ErrorBufferHandler) -> list[dict[str, Any]]:
    """Return a list copy of the handler's current buffer contents."""
    return list(handler.buffer)
