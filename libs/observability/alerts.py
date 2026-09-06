"""B12.2 email alert delivery primitive.

Privacy guarantees:
- The full email body is never logged.
- The recipient address is never logged; only recipient_set (bool) is logged.
- SMTP credentials (username, password) are never logged.
- The URL used by the health probe is never logged.
- Body fields go through a CLOSED ALLOWLIST and then sanitize_extra.
- Logger name is "demo-alerts" so it passes through configure_logging's
  sanitization pipeline.
- No HTML, no attachments, text/plain only.
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional

from libs.common.demo_settings import DemoSettings
from libs.observability.logging import sanitize_extra

_log = logging.getLogger("demo-alerts")

# Closed allowlist of field names permitted in the email body.
# Anything outside this set is silently dropped before body construction.
_BODY_ALLOWLIST: frozenset[str] = frozenset({
    "threshold_percent",
    "disk_used_percent",
    "disk_total_bytes",
    "disk_free_bytes",
    "scope",
    "endpoint_label",
    "consecutive_failures",
    "last_status_kind",
    "last_check_at_utc",
    # AssemblyAI usage-rate alert (count-based, no PII).
    "provider",
    "assemblyai_usage_count",
    "assemblyai_usage_threshold",
    "window_hours",
})

# Required SMTP/email fields that must all be non-empty for real sends.
_REQUIRED_FIELDS = (
    "demo_alert_smtp_host",
    "demo_alert_smtp_username",
    "demo_alert_smtp_password",
    "demo_alert_email_to",
    "demo_alert_email_from",
)


@dataclass(frozen=True)
class AlertResult:
    delivered: bool
    dry_run: bool
    error_class: Optional[str]


def is_alert_ready(settings: DemoSettings) -> tuple[bool, int]:
    """Return (ready, missing_count).

    ready is True only when demo_alert_email_enabled is True AND all five
    required string fields are non-empty. missing_count is the count of
    fields that are falsy (None or empty string) among the required set.
    """
    if not settings.demo_alert_email_enabled:
        return False, len(_REQUIRED_FIELDS)
    missing = sum(
        1 for field in _REQUIRED_FIELDS
        if not getattr(settings, field, None)
    )
    return missing == 0, missing


def build_alert_body(event: str, severity: str, *, fields: dict) -> str:
    """Construct the text/plain email body.

    Fields are filtered against the closed allowlist then passed through
    sanitize_extra as defense in depth. The constant header block is always
    emitted.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"service: demo",
        f"event: {event}",
        f"severity: {severity}",
        f"timestamp_utc: {now_iso}",
        f"host: asr-rp5",
        "",
    ]
    # Apply closed allowlist first.
    safe_fields = {k: v for k, v in fields.items() if k in _BODY_ALLOWLIST}
    # Defense in depth: pass through sanitize_extra.
    safe_fields = sanitize_extra(safe_fields)
    for key, value in safe_fields.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def send_alert(
    settings: DemoSettings,
    *,
    event: str,
    severity: str,
    fields: dict,
    now: Optional[datetime] = None,
) -> AlertResult:
    """Send an alert email, or dry-run if config is incomplete.

    On success: logs alert.delivered (safe meta only), returns delivered=True.
    On dry-run: logs alert.dry_run (safe meta only), returns dry_run=True.
    On SMTP/OS error: logs alert.send_failed (error_class only), returns
        delivered=False with error_class set. Never raises.
    """
    ready, missing_count = is_alert_ready(settings)

    if not ready:
        _log.warning(
            "alert.dry_run",
            extra={
                "event": event,
                "severity": severity,
                "host": "asr-rp5",
                "recipient_set": bool(settings.demo_alert_email_to),
                "dry_run": True,
                "missing_config_count": missing_count,
            },
        )
        return AlertResult(delivered=False, dry_run=True, error_class=None)

    subject = f"[asr-demo][{severity}] {event} on asr-rp5"
    body = build_alert_body(event, severity, fields=fields)

    msg = EmailMessage()
    msg["From"] = settings.demo_alert_email_from
    msg["To"] = settings.demo_alert_email_to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(
            settings.demo_alert_smtp_host,
            settings.demo_alert_smtp_port,
            timeout=settings.demo_alert_smtp_timeout_seconds,
        ) as smtp:
            if settings.demo_alert_smtp_use_starttls:
                smtp.starttls()
            smtp.login(settings.demo_alert_smtp_username, settings.demo_alert_smtp_password)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        error_class = type(exc).__name__
        _log.error(
            "alert.send_failed",
            extra={
                "event": event,
                "severity": severity,
                "host": "asr-rp5",
                "error_class": error_class,
            },
        )
        return AlertResult(delivered=False, dry_run=False, error_class=error_class)

    _log.info(
        "alert.delivered",
        extra={
            "event": event,
            "severity": severity,
            "host": "asr-rp5",
            "recipient_set": bool(settings.demo_alert_email_to),
            "delivered": True,
        },
    )
    return AlertResult(delivered=True, dry_run=False, error_class=None)
