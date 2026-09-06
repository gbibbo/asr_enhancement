"""Rotating file handler factory for the demo runtime (B12.1).

Returns a ``logging.handlers.RotatingFileHandler`` writing JSON lines via the
shared ``JSONFormatter``. The handler is tagged so
``libs.observability.logging.configure_logging`` removes it cleanly on the
next reconfiguration. Failures (missing directory permissions, disk full)
fall back to a single warning on the root logger and return ``None`` — the
caller's stderr handler keeps logs visible.

Filename pattern: ``{prefix}.{short_service}.log`` where ``short_service``
is the ``service`` argument with any leading ``demo-`` stripped (so
``demo-api`` -> ``api``, ``demo-worker`` -> ``worker``). The shortening is
intentional and matches the §B12.1 plan: the filename is part of the
operator-facing path and should be readable without redundant prefixes.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from libs.common.demo_settings import DemoSettings
from libs.observability.logging import JSONFormatter


def short_service(service: str) -> str:
    """Strip a leading ``demo-`` from the service tag for filename use."""
    return service[5:] if service.startswith("demo-") else service


def build_rotating_file_handler(
    settings: DemoSettings,
    *,
    service: str,
) -> Optional[logging.handlers.RotatingFileHandler]:
    """Return a configured rotating file handler or ``None`` on opt-out/failure.

    The caller is responsible for installing the returned handler via
    ``configure_logging(..., extra_handlers=[handler])`` so the idempotency
    and tagging contract stays in one place.
    """
    if not settings.demo_log_to_file:
        return None
    if settings.demo_logs_dir is None:
        return None

    log_dir = Path(settings.demo_logs_dir)
    filename = f"{settings.demo_log_filename_prefix}.{short_service(service)}.log"
    log_path = log_dir / filename

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler: logging.handlers.RotatingFileHandler = (
            logging.handlers.RotatingFileHandler(
                str(log_path),
                maxBytes=settings.demo_log_max_bytes,
                backupCount=settings.demo_log_backup_count,
                encoding="utf-8",
                delay=True,
            )
        )
    except OSError as exc:  # permission denied, read-only fs, etc.
        logging.getLogger(service).warning(
            "demo.log_rotation_unavailable",
            extra={
                "log_path_kind": "rotating_file",
                "error_class": type(exc).__name__,
            },
        )
        return None

    handler.setFormatter(JSONFormatter(service))
    handler._asr_managed = True  # type: ignore[attr-defined]
    handler._asr_managed_kind = "file"  # type: ignore[attr-defined]
    # _asr_managed_service is set by configure_logging when the handler is
    # registered, but pre-tag here so an inspection-only test can read it.
    handler._asr_managed_service = service  # type: ignore[attr-defined]
    return handler
