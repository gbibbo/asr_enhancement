"""B12.2 alert state management.

Disk state: stored in admin_state SQLite table (existing, no DDL change).
Health state: stored in a JSON file on disk (so it works even if the API is down).

Both helpers are stateless functions for testability — all mutable state
lives in the DB row or JSON file, not in module globals.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from libs.common.demo_settings import DemoSettings
from libs.demo.persistence import get_admin_state_value, set_admin_state

# Keys used in admin_state table for disk alert tracking.
_DISK_ALERT_KEY = "last_alert_disk_usage_high_at"
_DISK_CLEARED_KEY = "last_alert_disk_usage_cleared_at"

# Key used in admin_state table for the AssemblyAI usage-rate alert.
_AAI_USAGE_ALERT_KEY = "last_alert_assemblyai_usage_high_at"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 string to an aware datetime, or return None."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Disk alert state
# ---------------------------------------------------------------------------


def should_fire_disk(
    settings: DemoSettings,
    *,
    used_percent: float,
    db_path: Path,
    now: Optional[datetime] = None,
) -> bool:
    """Return True if a disk-usage alert should fire now.

    Fires when used_percent > settings.demo_alert_disk_threshold_percent AND
    (no prior alert row exists OR cooldown has elapsed since last alert).
    """
    effective_now = now or _now_utc()
    if used_percent <= settings.demo_alert_disk_threshold_percent:
        return False

    last_str = get_admin_state_value(db_path, _DISK_ALERT_KEY)
    if last_str is None:
        return True

    last_dt = _parse_iso(last_str)
    if last_dt is None:
        return True

    cooldown = timedelta(hours=settings.demo_alert_disk_cooldown_hours)
    return (effective_now - last_dt) >= cooldown


def mark_disk_alert_sent(db_path: Path, *, now: Optional[datetime] = None) -> None:
    """Record that a disk alert was sent at now (or utcnow)."""
    effective_now = now or _now_utc()
    set_admin_state(db_path, _DISK_ALERT_KEY, effective_now.isoformat())


def mark_disk_alert_cleared(db_path: Path, *, now: Optional[datetime] = None) -> None:
    """Record that disk usage has dropped back below threshold."""
    effective_now = now or _now_utc()
    set_admin_state(db_path, _DISK_CLEARED_KEY, effective_now.isoformat())


# ---------------------------------------------------------------------------
# AssemblyAI usage-rate alert state (admin_state table, cooldown-gated)
# ---------------------------------------------------------------------------


def should_fire_assemblyai_usage(
    *,
    usage_count: int,
    threshold: int,
    cooldown_hours: float,
    db_path: Path,
    now: Optional[datetime] = None,
) -> bool:
    """Return True if an AssemblyAI usage-rate alert should fire now.

    Fires when usage_count > threshold AND (no prior alert row exists OR the
    cooldown has elapsed since the last alert).
    """
    effective_now = now or _now_utc()
    if usage_count <= threshold:
        return False

    last_str = get_admin_state_value(db_path, _AAI_USAGE_ALERT_KEY)
    if last_str is None:
        return True

    last_dt = _parse_iso(last_str)
    if last_dt is None:
        return True

    return (effective_now - last_dt) >= timedelta(hours=cooldown_hours)


def mark_assemblyai_usage_alert_sent(db_path: Path, *, now: Optional[datetime] = None) -> None:
    """Record that an AssemblyAI usage-rate alert was sent at now (or utcnow)."""
    effective_now = now or _now_utc()
    set_admin_state(db_path, _AAI_USAGE_ALERT_KEY, effective_now.isoformat())


# ---------------------------------------------------------------------------
# Health check alert state (JSON file, not SQLite)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HealthDecision:
    should_fire: bool
    consecutive_failures: int
    last_status_kind: str  # "ok" | "connection_error" | "timeout" | "http_4xx" | "http_5xx"


_VALID_STATUS_KINDS = frozenset({
    "ok", "connection_error", "timeout", "http_4xx", "http_5xx",
})

_DEFAULT_HEALTH_STATE: dict = {
    "consecutive_failures": 0,
    "last_alert_at": None,
    "last_check_at": None,
}


def _read_health_state(state_path: Path) -> dict:
    """Read the health state JSON file, returning defaults on any error."""
    try:
        raw = state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return {
            "consecutive_failures": int(data.get("consecutive_failures", 0)),
            "last_alert_at": data.get("last_alert_at"),
            "last_check_at": data.get("last_check_at"),
        }
    except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
        return dict(_DEFAULT_HEALTH_STATE)


def _write_health_state(state_path: Path, state: dict) -> None:
    """Write the health state atomically (write-temp + os.replace)."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(state, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(str(tmp_path), str(state_path))


def update_health_state(
    state_path: Path,
    *,
    success: bool,
    status_kind: str,
    threshold: int,
    cooldown_minutes: float,
    now: Optional[datetime] = None,
) -> HealthDecision:
    """Update the health state file and return a HealthDecision.

    On success: resets consecutive_failures to 0, updates last_check_at.
    On failure: increments counter; if counter >= threshold AND (no prior alert
    OR cooldown elapsed) → should_fire=True and updates last_alert_at.
    Always writes the updated state atomically.
    """
    effective_now = now or _now_utc()
    now_iso = effective_now.isoformat()

    state = _read_health_state(state_path)

    if success:
        new_failures = 0
        new_state = {
            "consecutive_failures": 0,
            "last_alert_at": state["last_alert_at"],
            "last_check_at": now_iso,
        }
        _write_health_state(state_path, new_state)
        return HealthDecision(
            should_fire=False,
            consecutive_failures=0,
            last_status_kind=status_kind,
        )

    # Failure path.
    new_failures = state["consecutive_failures"] + 1
    should_fire = False

    if new_failures >= threshold:
        last_alert_dt = _parse_iso(state["last_alert_at"])
        if last_alert_dt is None:
            should_fire = True
        else:
            cooldown = timedelta(minutes=cooldown_minutes)
            if (effective_now - last_alert_dt) >= cooldown:
                should_fire = True

    new_last_alert_at = state["last_alert_at"]
    if should_fire:
        new_last_alert_at = now_iso

    new_state = {
        "consecutive_failures": new_failures,
        "last_alert_at": new_last_alert_at,
        "last_check_at": now_iso,
    }
    _write_health_state(state_path, new_state)

    return HealthDecision(
        should_fire=should_fire,
        consecutive_failures=new_failures,
        last_status_kind=status_kind,
    )
