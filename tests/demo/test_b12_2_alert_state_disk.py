"""B12.2 disk alert state logic.

Uses a temp SQLite DB initialized via init_schema (existing pattern from
libs/demo/persistence.py). Tests the should_fire_disk / mark_disk_alert_sent /
mark_disk_alert_cleared sequence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from libs.common.demo_settings import DemoSettings
from libs.demo.persistence import get_admin_state_value, init_schema
from libs.observability.alert_state import (
    mark_disk_alert_cleared,
    mark_disk_alert_sent,
    should_fire_disk,
)


def _settings(threshold: float = 80.0, cooldown_hours: float = 6.0) -> DemoSettings:
    return DemoSettings(
        demo_runtime_root=Path("/tmp/test_root"),

        demo_alert_disk_threshold_percent=threshold,
        demo_alert_disk_cooldown_hours=cooldown_hours,
    )


@pytest.fixture()
def db_path(tmp_path) -> Path:
    path = tmp_path / "test_demo.db"
    init_schema(path)
    return path


def _ts(offset_hours: float = 0.0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=offset_hours)


def test_above_threshold_no_prior_alert_fires(db_path):
    s = _settings(threshold=80.0)
    result = should_fire_disk(s, used_percent=85.0, db_path=db_path)
    assert result is True


def test_below_threshold_does_not_fire(db_path):
    s = _settings(threshold=80.0)
    result = should_fire_disk(s, used_percent=75.0, db_path=db_path)
    assert result is False


def test_at_threshold_does_not_fire(db_path):
    """Boundary: used_percent == threshold is NOT above — does not fire."""
    s = _settings(threshold=80.0)
    result = should_fire_disk(s, used_percent=80.0, db_path=db_path)
    assert result is False


def test_within_cooldown_does_not_refire(db_path):
    s = _settings(threshold=80.0, cooldown_hours=6.0)
    now = _ts(0.0)
    mark_disk_alert_sent(db_path, now=now)
    # 3 hours later — still within cooldown.
    later = _ts(3.0)
    result = should_fire_disk(s, used_percent=85.0, db_path=db_path, now=later)
    assert result is False


def test_after_cooldown_refires(db_path):
    s = _settings(threshold=80.0, cooldown_hours=6.0)
    now = _ts(0.0)
    mark_disk_alert_sent(db_path, now=now)
    # 7 hours later — cooldown elapsed.
    later = _ts(7.0)
    result = should_fire_disk(s, used_percent=85.0, db_path=db_path, now=later)
    assert result is True


def test_mark_disk_alert_sent_writes_state_row(db_path):
    now = _ts()
    mark_disk_alert_sent(db_path, now=now)
    value = get_admin_state_value(db_path, "last_alert_disk_usage_high_at")
    assert value is not None
    assert "T" in value  # ISO-8601 format sanity check


def test_mark_disk_alert_cleared_writes_cleared_row(db_path):
    now = _ts()
    mark_disk_alert_cleared(db_path, now=now)
    value = get_admin_state_value(db_path, "last_alert_disk_usage_cleared_at")
    assert value is not None
    assert "T" in value


def test_below_threshold_after_prior_alert_writes_cleared_row(db_path):
    """When disk drops below threshold after a prior high-water alert, mark cleared."""
    now = _ts()
    mark_disk_alert_sent(db_path, now=now)
    # Simulate disk dropping.
    s = _settings(threshold=80.0)
    fires = should_fire_disk(s, used_percent=70.0, db_path=db_path)
    assert fires is False
    # The script logic (not should_fire_disk) calls mark_disk_alert_cleared;
    # test that cleared marker can be written after a prior sent marker.
    mark_disk_alert_cleared(db_path)
    cleared = get_admin_state_value(db_path, "last_alert_disk_usage_cleared_at")
    assert cleared is not None


def test_second_above_threshold_call_within_cooldown_no_fire(db_path):
    """Full sequence: fire → sent → still above → no refire within cooldown."""
    s = _settings(threshold=80.0, cooldown_hours=6.0)
    now = _ts()
    # First call fires.
    assert should_fire_disk(s, used_percent=85.0, db_path=db_path, now=now) is True
    mark_disk_alert_sent(db_path, now=now)
    # Second call 1 hour later — still within cooldown.
    result = should_fire_disk(s, used_percent=85.0, db_path=db_path, now=_ts(1.0))
    assert result is False
