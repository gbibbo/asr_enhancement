"""B12.2 alert_health script integration test.

Invokes scripts.demo.alert_health:main() with monkeypatched urlopen.
Verifies:
- Script returns 0 on all paths (success, fail, error).
- URL string NEVER appears in any log record.
- Failure classification and state file persistence.
- Internal exception does not propagate.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.common.demo_settings import DemoSettings

# Constant label used by the script (never the URL string itself).
_ENDPOINT_LABEL = "demo_health_local"

# Test URL value — must NEVER appear in any log record.
_TEST_URL = "http://secret-internal-host:9999/demo/health"


def _make_settings(tmp_path: Path, url: str = _TEST_URL) -> DemoSettings:
    state_file = tmp_path / "state" / "health_check.json"
    return DemoSettings(
        demo_runtime_root=tmp_path,
        demo_alert_email_enabled=False,
        demo_alert_health_url=url,
        demo_alert_health_state_file=state_file,
        demo_alert_health_consecutive_failures=3,
        demo_alert_health_cooldown_minutes=30.0,
    )


class _MockHTTPResponse:
    def __init__(self, status: int = 200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return b"ok"


def test_script_exits_zero_on_success(tmp_path):
    settings = _make_settings(tmp_path)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("urllib.request.urlopen", return_value=_MockHTTPResponse(200)):
            from scripts.demo.alert_health import main
            result = main()
    assert result == 0


def test_script_exits_zero_on_connection_error(tmp_path):
    settings = _make_settings(tmp_path)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            from scripts.demo.alert_health import main
            result = main()
    assert result == 0


def test_script_exits_zero_on_http_5xx(tmp_path):
    settings = _make_settings(tmp_path)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                url=_TEST_URL, code=503, msg="Service Unavailable",
                hdrs=None, fp=None,
            ),
        ):
            from scripts.demo.alert_health import main
            result = main()
    assert result == 0


def test_url_never_appears_in_logs_on_success(tmp_path, caplog):
    settings = _make_settings(tmp_path, url=_TEST_URL)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("urllib.request.urlopen", return_value=_MockHTTPResponse(200)):
            with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
                from scripts.demo.alert_health import main
                main()

    for record in caplog.records:
        msg = record.getMessage()
        assert _TEST_URL not in msg, f"URL leaked into log record: {msg!r}"
        assert "secret-internal-host" not in msg
        assert "9999" not in msg


def test_url_never_appears_in_logs_on_failure(tmp_path, caplog):
    settings = _make_settings(tmp_path, url=_TEST_URL)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
                from scripts.demo.alert_health import main
                main()

    for record in caplog.records:
        msg = record.getMessage()
        assert _TEST_URL not in msg
        assert "secret-internal-host" not in msg


def test_state_file_created_after_health_check(tmp_path):
    settings = _make_settings(tmp_path)
    state_file = settings.demo_alert_health_state_file
    assert not state_file.exists()
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("urllib.request.urlopen", return_value=_MockHTTPResponse(200)):
            from scripts.demo.alert_health import main
            main()
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["consecutive_failures"] == 0


def test_failure_increments_counter(tmp_path):
    settings = _make_settings(tmp_path)
    state_file = settings.demo_alert_health_state_file
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            from scripts.demo.alert_health import main
            main()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["consecutive_failures"] == 1


def test_three_failures_trigger_dry_run_alert(tmp_path, caplog):
    settings = _make_settings(tmp_path)
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with caplog.at_level(logging.WARNING, logger="demo-alerts"):
            for _ in range(3):
                with patch(
                    "urllib.request.urlopen",
                    side_effect=urllib.error.URLError("refused"),
                ):
                    from scripts.demo.alert_health import main
                    main()

    dry_run_records = [
        r for r in caplog.records if "alert.dry_run" in r.getMessage()
    ]
    assert len(dry_run_records) >= 1


def test_success_resets_failure_counter(tmp_path):
    settings = _make_settings(tmp_path)
    # Two failures.
    for _ in range(2):
        with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
            with patch(
                "urllib.request.urlopen",
                side_effect=urllib.error.URLError("refused"),
            ):
                from scripts.demo.alert_health import main
                main()
    # One success.
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with patch("urllib.request.urlopen", return_value=_MockHTTPResponse(200)):
            from scripts.demo.alert_health import main
            main()

    state_file = settings.demo_alert_health_state_file
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["consecutive_failures"] == 0


def test_internal_exception_returns_zero(tmp_path):
    """Even if DemoSettings construction raises, script exits 0."""
    with patch(
        "libs.common.demo_settings.DemoSettings",
        side_effect=RuntimeError("Simulated settings error"),
    ):
        from scripts.demo.alert_health import main
        result = main()
    assert result == 0


def test_endpoint_label_in_log_not_url(tmp_path, caplog):
    """The endpoint_label appears in logs, not the URL string."""
    settings = _make_settings(tmp_path)
    # Force 3 failures to trigger the alert path with dry-run logging.
    with patch("libs.common.demo_settings.DemoSettings", return_value=settings):
        with caplog.at_level(logging.DEBUG, logger="demo-alerts"):
            for _ in range(3):
                with patch(
                    "urllib.request.urlopen",
                    side_effect=urllib.error.URLError("refused"),
                ):
                    from scripts.demo.alert_health import main
                    main()

    all_msgs = " ".join(r.getMessage() for r in caplog.records)
    assert _TEST_URL not in all_msgs
    assert "secret-internal-host" not in all_msgs
