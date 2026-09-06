"""B12.2 alert_disk script integration test.

Invokes scripts.demo.alert_disk:main() with monkeypatched probes and alert
functions. Verifies:
- Script returns 0 on all paths (dry-run, fire, error).
- URL string never appears in any log record.
- Fire path calls send_alert with correct event name.
- Internal exception does not propagate.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.common.demo_settings import DemoSettings
from libs.demo.persistence import init_schema
from libs.observability.alerts import AlertResult


def _make_settings(tmp_path: Path, used_percent: float = 85.0, threshold: float = 80.0) -> DemoSettings:
    db_path = tmp_path / "demo.db"
    init_schema(db_path)
    return DemoSettings(
        demo_runtime_root=tmp_path,
        demo_db_path=db_path,
        demo_alert_email_enabled=False,
        demo_alert_disk_threshold_percent=threshold,
    )


_DISK_DATA_HIGH = {
    "scope": "demo_runtime_root",
    "used_percent": 85.0,
    "total_bytes": 30_000_000_000,
    "free_bytes": 4_000_000_000,
    "used_bytes": 26_000_000_000,
}

_DISK_DATA_LOW = {
    "scope": "demo_runtime_root",
    "used_percent": 50.0,
    "total_bytes": 30_000_000_000,
    "free_bytes": 15_000_000_000,
    "used_bytes": 15_000_000_000,
}


def test_script_exits_zero_dry_run(tmp_path):
    settings = _make_settings(tmp_path)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("libs.demo.probes.read_disk_usage", return_value=_DISK_DATA_HIGH):
            from scripts.demo.alert_disk import main
            result = main()
    assert result == 0


def test_script_exits_zero_below_threshold(tmp_path):
    settings = _make_settings(tmp_path, used_percent=50.0, threshold=80.0)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("libs.demo.probes.read_disk_usage", return_value=_DISK_DATA_LOW):
            from scripts.demo.alert_disk import main
            result = main()
    assert result == 0


def test_script_exits_zero_on_internal_exception(tmp_path):
    """Even if DemoSettings raises, the script returns 0."""
    with patch(
        "libs.common.demo_settings.DemoSettings",
        side_effect=RuntimeError("Simulated settings error"),
    ):
        from scripts.demo.alert_disk import main
        result = main()
    assert result == 0


def test_script_fire_path_calls_send_alert(tmp_path):
    settings = _make_settings(tmp_path, used_percent=85.0, threshold=80.0)
    sent_calls = []

    def mock_send_alert(s, *, event, severity, fields):
        sent_calls.append({"event": event, "severity": severity})
        return AlertResult(delivered=False, dry_run=True, error_class=None)

    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("libs.demo.probes.read_disk_usage", return_value=_DISK_DATA_HIGH):
            with patch("libs.observability.alerts.send_alert", side_effect=mock_send_alert):
                from scripts.demo.alert_disk import main
                result = main()

    assert result == 0
    assert len(sent_calls) >= 1
    assert sent_calls[0]["event"] == "disk_usage_high"
    assert sent_calls[0]["severity"] == "warning"


def test_script_no_url_string_in_logs(tmp_path, caplog):
    """The disk script has no URL; verify no URL leaks from any settings value."""
    settings = _make_settings(tmp_path)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("libs.demo.probes.read_disk_usage", return_value=_DISK_DATA_HIGH):
            with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
                from scripts.demo.alert_disk import main
                main()

    for record in caplog.records:
        msg = record.getMessage()
        assert "http://" not in msg
        assert "https://" not in msg


def test_script_send_alert_event_fields_no_forbidden_data(tmp_path):
    """Fields passed to send_alert must not contain any forbidden values."""
    settings = _make_settings(tmp_path)
    captured_fields = []

    def mock_send_alert(s, *, event, severity, fields):
        captured_fields.append(fields.copy())
        return AlertResult(delivered=False, dry_run=True, error_class=None)

    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("libs.demo.probes.read_disk_usage", return_value=_DISK_DATA_HIGH):
            with patch("libs.observability.alerts.send_alert", side_effect=mock_send_alert):
                from scripts.demo.alert_disk import main
                main()

    assert len(captured_fields) >= 1
    f = captured_fields[0]
    # Must have scope label, not a path.
    assert f.get("scope") == "demo_runtime_root"
    assert "/home/" not in str(f.values())
    assert "/tmp/" not in str(f.values())
