"""B12.2 credential/recipient non-leakage in logs.

Captures all caplog records during send_alert execution and asserts that
the fake credentials and recipient address never appear in:
- Any log record message, args, or extra dict value
- Any captured email body (captured via mock SMTP.send_message)
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.common.demo_settings import DemoSettings
from libs.observability.alerts import send_alert

_FAKE_PASSWORD = "SECRETxyz123"
_FAKE_USERNAME = "user@host"
_FAKE_RECIPIENT = "recipient@example.invalid"
_FAKE_FROM = "sender@example.com"
_FAKE_HOST = "smtp.example.com"

_EVENT = "disk_usage_high"
_SEVERITY = "warning"
_FIELDS = {"disk_used_percent": 85.0, "scope": "demo_runtime_root"}


def _full_settings() -> DemoSettings:
    return DemoSettings(
        demo_runtime_root=Path("/tmp/test_root"),

        demo_alert_email_enabled=True,
        demo_alert_smtp_host=_FAKE_HOST,
        demo_alert_smtp_port=587,
        demo_alert_smtp_username=_FAKE_USERNAME,
        demo_alert_smtp_password=_FAKE_PASSWORD,
        demo_alert_email_to=_FAKE_RECIPIENT,
        demo_alert_email_from=_FAKE_FROM,
        demo_alert_smtp_use_starttls=True,
    )


def _record_str(record: logging.LogRecord) -> str:
    """Combine all string-representable content of a log record."""
    parts = [record.getMessage()]
    for key, val in record.__dict__.items():
        if isinstance(val, str):
            parts.append(val)
    return " ".join(parts)


def test_credentials_not_in_any_log_record_on_success(caplog):
    settings = _full_settings()
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)

    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance):
        with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
            send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)

    for record in caplog.records:
        combined = _record_str(record)
        assert _FAKE_PASSWORD not in combined, (
            f"Password leaked in log record: {combined!r}"
        )
        assert _FAKE_USERNAME not in combined, (
            f"Username leaked in log record: {combined!r}"
        )
        assert _FAKE_RECIPIENT not in combined, (
            f"Recipient leaked in log record: {combined!r}"
        )


def test_recipient_not_in_email_body(caplog):
    settings = _full_settings()
    captured_messages = []
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)

    def capture_send_message(msg):
        captured_messages.append(msg)

    mock_instance.send_message.side_effect = capture_send_message

    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance):
        with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
            send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)

    assert len(captured_messages) == 1
    msg = captured_messages[0]
    body = msg.get_payload()
    # The recipient must appear in envelope headers only (To:), not the body.
    assert _FAKE_RECIPIENT not in body, (
        f"Recipient {_FAKE_RECIPIENT!r} leaked into email body: {body!r}"
    )
    assert _FAKE_PASSWORD not in body
    assert _FAKE_USERNAME not in body


def test_credentials_not_in_any_log_record_on_smtp_failure(caplog):
    settings = _full_settings()
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)
    # send_alert catches (smtplib.SMTPException, OSError) — use a real
    # smtplib subclass so the failure path is exercised (not a generic Exception
    # which would escape and indicate the contract is wrong).
    import smtplib
    mock_instance.starttls.side_effect = smtplib.SMTPException("auth error")

    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance):
        with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
            send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)

    for record in caplog.records:
        combined = _record_str(record)
        assert _FAKE_PASSWORD not in combined
        assert _FAKE_USERNAME not in combined
        assert _FAKE_RECIPIENT not in combined


def test_credentials_not_in_dry_run_log(caplog):
    """Dry-run path (disabled) also must not log credentials."""
    settings = DemoSettings(
        demo_runtime_root=Path("/tmp/test_root"),

        demo_alert_email_enabled=False,
        demo_alert_smtp_password=_FAKE_PASSWORD,
        demo_alert_smtp_username=_FAKE_USERNAME,
        demo_alert_email_to=_FAKE_RECIPIENT,
    )
    with patch("libs.observability.alerts.smtplib.SMTP"):
        with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
            send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)

    for record in caplog.records:
        combined = _record_str(record)
        assert _FAKE_PASSWORD not in combined
        assert _FAKE_USERNAME not in combined
        assert _FAKE_RECIPIENT not in combined
