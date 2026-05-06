"""B12.2 send_alert with mocked SMTP.

Verifies:
- Disabled config: smtplib.SMTP never instantiated; returns dry_run=True.
- Partial config: same dry_run behavior.
- Full config: smtplib.SMTP instantiated exactly once; STARTTLS called;
  returns delivered=True, dry_run=False.
- SMTP exception: caught and returned as AlertResult(delivered=False,
  error_class="SMTPException"); no exception escapes.
- OSError: caught similarly.
- Patch is at libs.observability.alerts.smtplib.SMTP (module namespace).
"""

from __future__ import annotations

import smtplib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.common.demo_settings import DemoSettings
from libs.observability.alerts import AlertResult, send_alert


def _disabled_settings(**kwargs) -> DemoSettings:
    kwargs.setdefault("demo_runtime_root", Path("/tmp/test_root"))
    kwargs.setdefault("demo_alert_email_enabled", False)
    return DemoSettings(**kwargs)


def _partial_settings(**kwargs) -> DemoSettings:
    kwargs.setdefault("demo_runtime_root", Path("/tmp/test_root"))
    kwargs.setdefault("demo_alert_email_enabled", True)
    kwargs.setdefault("demo_alert_smtp_host", "smtp.example.com")
    # Missing: username, password, email_to, email_from
    return DemoSettings(**kwargs)


def _full_settings(**kwargs) -> DemoSettings:
    kwargs.setdefault("demo_runtime_root", Path("/tmp/test_root"))
    kwargs.setdefault("demo_alert_email_enabled", True)
    kwargs.setdefault("demo_alert_smtp_host", "smtp.example.com")
    kwargs.setdefault("demo_alert_smtp_port", 587)
    kwargs.setdefault("demo_alert_smtp_username", "user@example.com")
    kwargs.setdefault("demo_alert_smtp_password", "SECRETxyz123")
    kwargs.setdefault("demo_alert_email_to", "recipient@example.invalid")
    kwargs.setdefault("demo_alert_email_from", "sender@example.com")
    kwargs.setdefault("demo_alert_smtp_use_starttls", True)
    return DemoSettings(**kwargs)


_EVENT = "disk_usage_high"
_SEVERITY = "warning"
_FIELDS = {"disk_used_percent": 85.0, "scope": "demo_runtime_root"}


def test_disabled_config_smtp_not_called():
    settings = _disabled_settings()
    with patch("libs.observability.alerts.smtplib.SMTP") as mock_smtp:
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert mock_smtp.called is False
    assert result.dry_run is True
    assert result.delivered is False
    assert result.error_class is None


def test_partial_config_smtp_not_called():
    settings = _partial_settings()
    with patch("libs.observability.alerts.smtplib.SMTP") as mock_smtp:
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert mock_smtp.called is False
    assert result.dry_run is True
    assert result.delivered is False


def test_full_config_smtp_called_once():
    settings = _full_settings()
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)
    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance) as mock_smtp:
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert mock_smtp.call_count == 1
    assert result.delivered is True
    assert result.dry_run is False
    assert result.error_class is None


def test_full_config_starttls_called():
    settings = _full_settings(demo_alert_smtp_use_starttls=True)
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)
    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance):
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    mock_instance.starttls.assert_called_once()
    assert result.delivered is True


def test_full_config_no_starttls_when_disabled():
    settings = _full_settings(demo_alert_smtp_use_starttls=False)
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)
    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance):
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    mock_instance.starttls.assert_not_called()
    assert result.delivered is True


def test_smtp_exception_caught_returns_error_result():
    settings = _full_settings()
    mock_instance = MagicMock()
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=False)
    mock_instance.starttls.side_effect = smtplib.SMTPException("auth failed")
    with patch("libs.observability.alerts.smtplib.SMTP", return_value=mock_instance):
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert result.delivered is False
    assert result.dry_run is False
    assert result.error_class == "SMTPException"


def test_smtp_connect_exception_caught():
    """smtplib.SMTP constructor raising SMTPException is caught."""
    settings = _full_settings()
    with patch(
        "libs.observability.alerts.smtplib.SMTP",
        side_effect=smtplib.SMTPConnectError(421, "Service temporarily unavailable"),
    ):
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert result.delivered is False
    assert result.dry_run is False
    assert "SMTP" in result.error_class


def test_os_error_caught_returns_error_result():
    settings = _full_settings()
    with patch(
        "libs.observability.alerts.smtplib.SMTP",
        side_effect=OSError("Connection refused"),
    ):
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert result.delivered is False
    assert result.dry_run is False
    assert result.error_class == "OSError"


def test_disabled_config_returns_alert_result_type():
    settings = _disabled_settings()
    with patch("libs.observability.alerts.smtplib.SMTP"):
        result = send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    assert isinstance(result, AlertResult)


def test_dry_run_emits_exactly_one_log(caplog):
    import logging
    settings = _disabled_settings()
    with patch("libs.observability.alerts.smtplib.SMTP"):
        with caplog.at_level(logging.WARNING, logger="demo-alerts"):
            send_alert(settings, event=_EVENT, severity=_SEVERITY, fields=_FIELDS)
    dry_run_records = [r for r in caplog.records if "alert.dry_run" in r.getMessage()]
    assert len(dry_run_records) == 1
