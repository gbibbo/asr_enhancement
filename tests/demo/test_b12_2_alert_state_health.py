"""B12.2 health check alert state logic (JSON state file).

Tests the update_health_state sequence using tmp_path for the JSON file.
Verifies: fire on 3rd consecutive failure, counter reset on success,
within-cooldown no refire, after-cooldown refire, atomic write (tmp+rename).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from libs.observability.alert_state import HealthDecision, update_health_state


_THRESHOLD = 3
_COOLDOWN_MINUTES = 30.0


def _ts(offset_minutes: float = 0.0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)


def test_success_does_not_fire(tmp_path):
    state_file = tmp_path / "health.json"
    decision = update_health_state(
        state_file,
        success=True,
        status_kind="ok",
        threshold=_THRESHOLD,
        cooldown_minutes=_COOLDOWN_MINUTES,
    )
    assert decision.should_fire is False
    assert decision.consecutive_failures == 0
    assert decision.last_status_kind == "ok"


def test_single_failure_does_not_fire(tmp_path):
    state_file = tmp_path / "health.json"
    decision = update_health_state(
        state_file,
        success=False,
        status_kind="connection_error",
        threshold=_THRESHOLD,
        cooldown_minutes=_COOLDOWN_MINUTES,
    )
    assert decision.should_fire is False
    assert decision.consecutive_failures == 1


def test_two_failures_do_not_fire(tmp_path):
    state_file = tmp_path / "health.json"
    for _ in range(2):
        decision = update_health_state(
            state_file,
            success=False,
            status_kind="http_5xx",
            threshold=_THRESHOLD,
            cooldown_minutes=_COOLDOWN_MINUTES,
        )
    assert decision.should_fire is False
    assert decision.consecutive_failures == 2


def test_third_failure_fires(tmp_path):
    state_file = tmp_path / "health.json"
    # success then 3 consecutive failures
    update_health_state(state_file, success=True, status_kind="ok",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    for i in range(3):
        decision = update_health_state(
            state_file,
            success=False,
            status_kind="connection_error",
            threshold=_THRESHOLD,
            cooldown_minutes=_COOLDOWN_MINUTES,
        )
    assert decision.should_fire is True
    assert decision.consecutive_failures == 3


def test_success_resets_counter(tmp_path):
    state_file = tmp_path / "health.json"
    # Two failures then a success
    for _ in range(2):
        update_health_state(state_file, success=False, status_kind="timeout",
                            threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    decision = update_health_state(state_file, success=True, status_kind="ok",
                                   threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    assert decision.consecutive_failures == 0
    assert decision.should_fire is False


def test_success_then_three_failures_fires(tmp_path):
    state_file = tmp_path / "health.json"
    update_health_state(state_file, success=True, status_kind="ok",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    # Reset counter; now fail 3 times.
    for _ in range(3):
        dec = update_health_state(state_file, success=False, status_kind="http_5xx",
                                  threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    assert dec.should_fire is True


def test_within_cooldown_does_not_refire(tmp_path):
    state_file = tmp_path / "health.json"
    now = _ts()
    # Fail to threshold (fires and records last_alert_at).
    for _ in range(_THRESHOLD):
        update_health_state(state_file, success=False, status_kind="connection_error",
                            threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES, now=now)
    # One more failure within cooldown.
    later = _ts(10.0)  # 10 minutes, within 30-minute cooldown
    decision = update_health_state(state_file, success=False, status_kind="connection_error",
                                   threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES,
                                   now=later)
    assert decision.should_fire is False


def test_after_cooldown_refires(tmp_path):
    state_file = tmp_path / "health.json"
    now = _ts()
    # Fail to threshold.
    for _ in range(_THRESHOLD):
        update_health_state(state_file, success=False, status_kind="http_5xx",
                            threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES, now=now)
    # After cooldown.
    later = _ts(35.0)  # 35 minutes, past 30-minute cooldown
    decision = update_health_state(state_file, success=False, status_kind="http_5xx",
                                   threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES,
                                   now=later)
    assert decision.should_fire is True


def test_state_file_created_on_first_call(tmp_path):
    state_file = tmp_path / "health.json"
    assert not state_file.exists()
    update_health_state(state_file, success=True, status_kind="ok",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    assert state_file.exists()


def test_state_file_is_valid_json(tmp_path):
    state_file = tmp_path / "health.json"
    update_health_state(state_file, success=False, status_kind="connection_error",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert "consecutive_failures" in data
    assert "last_alert_at" in data
    assert "last_check_at" in data
    assert isinstance(data["consecutive_failures"], int)


def test_atomic_write_no_tmp_file_leftover(tmp_path):
    """Verify no .json.tmp file is left after a successful write."""
    state_file = tmp_path / "health.json"
    update_health_state(state_file, success=True, status_kind="ok",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    tmp_file = state_file.with_suffix(".json.tmp")
    assert not tmp_file.exists()


def test_state_file_nested_parent_created(tmp_path):
    """state_path.parent is created automatically if it does not exist."""
    state_file = tmp_path / "state" / "health_check.json"
    assert not state_file.parent.exists()
    update_health_state(state_file, success=True, status_kind="ok",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    assert state_file.exists()


def test_counter_persists_across_calls(tmp_path):
    state_file = tmp_path / "health.json"
    update_health_state(state_file, success=False, status_kind="timeout",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    update_health_state(state_file, success=False, status_kind="timeout",
                        threshold=_THRESHOLD, cooldown_minutes=_COOLDOWN_MINUTES)
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["consecutive_failures"] == 2
