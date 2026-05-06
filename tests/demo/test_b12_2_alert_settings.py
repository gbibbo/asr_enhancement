"""B12.2 DemoSettings alert-field contract.

Covers:
- All new demo_alert_* fields have correct defaults.
- is_alert_ready returns (False, n) for disabled or partial config.
- is_alert_ready returns (True, 0) for full valid config.
- demo_alert_health_state_file derives to <root>/state/health_check.json
  via fill_derived_paths when unset.
- Existing settings fields are not broken.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from libs.common.demo_settings import DemoSettings
from libs.observability.alerts import is_alert_ready


def _settings(**kwargs) -> DemoSettings:
    """Build a DemoSettings with test overrides.

    Passes demo_runtime_root to avoid defaulting to the real RP5 path
    (callers may override). The runtime container's .env.demo / compose
    env can otherwise leak through pydantic-settings, so the helper
    explicitly pins fields the test cares about; callers can override
    any field by passing it in **kwargs.
    """
    kwargs.setdefault("demo_runtime_root", Path("/tmp/test_root"))
    # Pin B12.1 file-logging behavior to the library default so the
    # compose-level DEMO_LOG_TO_FILE=true does not leak into these tests.
    kwargs.setdefault("demo_log_to_file", False)
    return DemoSettings(**kwargs)


def test_alert_email_enabled_defaults_false():
    s = _settings()
    assert s.demo_alert_email_enabled is False


def test_alert_smtp_fields_default_none_or_sensible():
    s = _settings()
    # Pydantic-settings turns an empty env var (e.g. DEMO_ALERT_EMAIL_TO=)
    # into the empty string, not None. The is_alert_ready check uses
    # truthiness, so both None and "" are treated as missing — accept either.
    assert s.demo_alert_email_to in (None, "")
    assert s.demo_alert_email_from in (None, "")
    assert s.demo_alert_smtp_host in (None, "")
    assert s.demo_alert_smtp_port == 587
    assert s.demo_alert_smtp_username in (None, "")
    assert s.demo_alert_smtp_password in (None, "")
    assert s.demo_alert_smtp_use_starttls is True
    assert s.demo_alert_smtp_timeout_seconds == 10.0


def test_alert_disk_defaults():
    s = _settings()
    assert s.demo_alert_disk_threshold_percent == 80.0
    assert s.demo_alert_disk_cooldown_hours == 6.0


def test_alert_health_defaults():
    s = _settings()
    assert s.demo_alert_health_consecutive_failures == 3
    assert s.demo_alert_health_cooldown_minutes == 30.0
    assert s.demo_alert_health_url == "http://localhost:8001/demo/health"


def test_alert_health_state_file_derived_from_runtime_root():
    root = Path("/tmp/my_runtime_root")
    s = _settings(demo_runtime_root=root)
    assert s.demo_alert_health_state_file == root / "state" / "health_check.json"


def test_alert_health_state_file_explicit_override():
    explicit = Path("/tmp/custom_state.json")
    s = _settings(demo_alert_health_state_file=explicit)
    assert s.demo_alert_health_state_file == explicit


def test_is_alert_ready_disabled_by_default():
    s = _settings()
    ready, missing = is_alert_ready(s)
    assert ready is False
    assert missing > 0


def test_is_alert_ready_enabled_but_no_smtp_fields():
    s = _settings(demo_alert_email_enabled=True)
    ready, missing = is_alert_ready(s)
    assert ready is False
    assert missing == 5  # all five required fields missing


def test_is_alert_ready_partial_config():
    s = _settings(
        demo_alert_email_enabled=True,
        demo_alert_smtp_host="smtp.example.com",
        demo_alert_smtp_username="user@example.com",
        # password, email_to, email_from still missing
    )
    ready, missing = is_alert_ready(s)
    assert ready is False
    assert missing == 3


def test_is_alert_ready_full_config():
    s = _settings(
        demo_alert_email_enabled=True,
        demo_alert_smtp_host="smtp.example.com",
        demo_alert_smtp_username="user@example.com",
        demo_alert_smtp_password="s3cr3t",
        demo_alert_email_to="alert@example.com",
        demo_alert_email_from="sender@example.com",
    )
    ready, missing = is_alert_ready(s)
    assert ready is True
    assert missing == 0


def test_is_alert_ready_returns_tuple():
    s = _settings()
    result = is_alert_ready(s)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_existing_settings_fields_unchanged():
    """Regression: existing settings fields are not removed or renamed."""
    s = _settings()
    assert s.demo_runtime_root == Path("/tmp/test_root")
    assert s.demo_worker_concurrency == 1
    assert s.demo_queue_max == 10
    assert s.demo_upload_limit_bytes == 5_242_880
    assert s.demo_assemblyai_daily_soft_cap_usd == 5.0
    assert s.demo_log_to_file is False
    assert s.demo_admin_recent_errors == 20
