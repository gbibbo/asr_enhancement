from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import IO, Any

_STDLIB_RECORD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message",
})

_REDACT_PATTERNS = frozenset({"key", "secret", "token", "authorization", "auth_header"})


def _should_redact(field_name: str) -> bool:
    name_lower = field_name.lower()
    return any(pattern in name_lower for pattern in _REDACT_PATTERNS)


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

        for key, value in record.__dict__.items():
            if key in _STDLIB_RECORD_ATTRS:
                continue
            if _should_redact(key):
                output[key] = "[REDACTED]"
            else:
                output[key] = value

        if record.exc_info:
            output["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(output)


def configure_logging(
    service: str,
    level: str = "INFO",
    stream: IO[str] | None = None,
) -> None:
    if stream is None:
        stream = sys.stderr

    root = logging.root

    # Remove any previously installed ASR JSON handlers
    root.handlers = [
        h for h in root.handlers if not getattr(h, "_asr_json_logging", False)
    ]

    # Install exactly one new ASR JSON handler
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter(service))
    handler._asr_json_logging = True  # type: ignore[attr-defined]
    root.addHandler(handler)

    root.setLevel(level)
