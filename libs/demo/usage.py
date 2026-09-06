"""AssemblyAI usage ledger and cost-control logic (B10.1).

This module owns the demo runtime's vocabulary for AssemblyAI cost control,
the derivations that map spend totals to cap/state strings, and the
transactional reservation helper used by future call sites (B10.2 will be
the first caller).

Vocabulary contract:

* ``cap_state`` ∈ {below, warning_reached, soft_reached, hard_reached}.
* ``state``     ∈ {available, daily_quota_reached, quota_exhausted, disabled}.
* Cap priority: hard_reached > soft_reached > warning_reached > below.
* ``warning_reached`` is non-blocking; only ``soft_reached`` and
  ``hard_reached`` block AssemblyAI calls.

Privacy:

* The ledger row stores no transcript text, no raw payloads, no upload
  filenames, no ground truth, no IP, and no API key.
* ``session_id_hash`` is opaque and pre-hashed by callers (B10.2 will
  populate it). B10.1 callers pass ``None``.
* SMTP delivery for the warning cap is deferred to phase B12 (observability);
  this module only emits one structured log entry per warning-cap crossing.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

from libs.asr.schema import ASRResult
from libs.common.demo_settings import DemoSettings
from libs.demo.persistence import (
    _open,
    _sum_usage_cost_in_conn,
    sum_completed_usage_cost,
    sum_reserved_usage_cost,
    update_usage_ledger_status,
)

_log = logging.getLogger("demo-api.usage")

# Cap state values -----------------------------------------------------------
CAP_BELOW = "below"
CAP_WARNING_REACHED = "warning_reached"
CAP_SOFT_REACHED = "soft_reached"
CAP_HARD_REACHED = "hard_reached"

# Provider state values ------------------------------------------------------
STATE_AVAILABLE = "available"
STATE_DAILY_QUOTA_REACHED = "daily_quota_reached"
STATE_QUOTA_EXHAUSTED = "quota_exhausted"
STATE_DISABLED = "disabled"

# Ledger row status values ---------------------------------------------------
LEDGER_STATUS_STARTED = "started"
LEDGER_STATUS_COMPLETED = "completed"
LEDGER_STATUS_FAILED = "failed"

PROVIDER_ASSEMBLYAI = "assemblyai"

# B10.2 user-facing strings (single source of truth shared by API and worker).
MSG_DISABLED = "AssemblyAI is not configured. Use Whisper local instead."
MSG_DAILY_QUOTA_REACHED = (
    "AssemblyAI daily quota reached. Use Whisper local instead."
)
MSG_HARD_QUOTA_EXHAUSTED = (
    "AssemblyAI quota exhausted. Use Whisper local instead."
)
MSG_SESSION_LIMIT_REACHED = (
    "AssemblyAI session limit reached (3 uses in 24 hours). Use Whisper local instead."
)
MSG_SESSION_HEADER_REQUIRED = (
    "AssemblyAI requires session header. Use Whisper local instead."
)
MSG_LEDGER_UNAVAILABLE = (
    "AssemblyAI temporarily unavailable. Try again or use Whisper local."
)

ALL_CAP_STATES = (CAP_BELOW, CAP_WARNING_REACHED, CAP_SOFT_REACHED, CAP_HARD_REACHED)
ALL_PROVIDER_STATES = (
    STATE_AVAILABLE,
    STATE_DAILY_QUOTA_REACHED,
    STATE_QUOTA_EXHAUSTED,
    STATE_DISABLED,
)


class LedgerWriteError(Exception):
    """Raised only for usage_ledger DB read/write failures."""


class CapBlockedError(Exception):
    """Raised when projected spend would cross soft_reached or hard_reached.

    Carries the projected ``cap_state``. Never raised for
    ``warning_reached`` (non-blocking).
    """

    def __init__(self, cap_state: str, message: Optional[str] = None) -> None:
        if cap_state not in (CAP_SOFT_REACHED, CAP_HARD_REACHED):
            raise ValueError(
                f"CapBlockedError requires soft_reached or hard_reached, got {cap_state!r}"
            )
        self.cap_state = cap_state
        if message is None:
            if cap_state == CAP_SOFT_REACHED:
                message = MSG_DAILY_QUOTA_REACHED
            else:
                message = MSG_HARD_QUOTA_EXHAUSTED
        super().__init__(message)


class _ASRAdapterLike(Protocol):
    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult: ...


# ---------------------------------------------------------------------------
# Pure logic
# ---------------------------------------------------------------------------


def estimate_cost_usd(duration_seconds: Any, usd_per_second: Any) -> float:
    """Estimate the USD cost of a single AssemblyAI call by audio duration.

    * ``duration_seconds`` non-numeric -> ``TypeError``.
    * ``duration_seconds`` < 0        -> ``ValueError``.
    * ``duration_seconds`` == 0       -> ``0.0``.
    * ``usd_per_second`` non-numeric  -> ``TypeError``.
    * ``usd_per_second``  < 0         -> ``ValueError``.
    * Bool inputs are rejected (``True``/``False`` are not durations or rates).
    """
    if isinstance(duration_seconds, bool) or not isinstance(
        duration_seconds, (int, float)
    ):
        raise TypeError(
            f"duration_seconds must be int or float, got {type(duration_seconds).__name__}"
        )
    if isinstance(usd_per_second, bool) or not isinstance(
        usd_per_second, (int, float)
    ):
        raise TypeError(
            f"usd_per_second must be int or float, got {type(usd_per_second).__name__}"
        )
    if duration_seconds < 0:
        raise ValueError(f"duration_seconds must be >= 0, got {duration_seconds!r}")
    if usd_per_second < 0:
        raise ValueError(f"usd_per_second must be >= 0, got {usd_per_second!r}")
    return round(float(duration_seconds) * float(usd_per_second), 6)


def derive_cap_state(
    daily_completed_usd: float,
    total_completed_usd: float,
    *,
    daily_soft_cap_usd: float,
    warning_cap_usd: float,
    hard_cap_usd: float,
) -> str:
    """Map (daily, total) USD spend to a cap_state string.

    Priority: hard_reached > soft_reached > warning_reached > below.
    Equality with a cap triggers that cap (``>=``).
    """
    if total_completed_usd >= hard_cap_usd:
        return CAP_HARD_REACHED
    if daily_completed_usd >= daily_soft_cap_usd:
        return CAP_SOFT_REACHED
    if total_completed_usd >= warning_cap_usd:
        return CAP_WARNING_REACHED
    return CAP_BELOW


def derive_provider_state(api_key: Optional[str], cap_state: str) -> str:
    """Map (api_key, cap_state) to a public provider state string."""
    if not api_key:
        return STATE_DISABLED
    if cap_state == CAP_HARD_REACHED:
        return STATE_QUOTA_EXHAUSTED
    if cap_state == CAP_SOFT_REACHED:
        return STATE_DAILY_QUOTA_REACHED
    if cap_state in (CAP_WARNING_REACHED, CAP_BELOW):
        return STATE_AVAILABLE
    raise ValueError(f"Unknown cap_state: {cap_state!r}")


def assemblyai_quota_exhausted(state: str) -> bool:
    """True for any state in which AssemblyAI must not be called."""
    return state in (
        STATE_DAILY_QUOTA_REACHED,
        STATE_QUOTA_EXHAUSTED,
        STATE_DISABLED,
    )


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def _now(now: Optional[datetime] = None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _utc_day_start_iso(now: Optional[datetime] = None) -> str:
    n = _now(now)
    start = n.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat()


def rolling_24h_start_iso(now: Optional[datetime] = None) -> str:
    """ISO timestamp of (now - 24h) in UTC. Used by the B10.2 session gate."""
    from datetime import timedelta
    n = _now(now)
    return (n - timedelta(hours=24)).isoformat()


# ---------------------------------------------------------------------------
# Endpoint payload builders
# ---------------------------------------------------------------------------


def compute_public_view(
    db_path: Path,
    settings: DemoSettings,
    *,
    now: Optional[datetime] = None,
) -> dict:
    """UI-safe payload for GET /demo/providers/assemblyai/status.

    Exposes only ``state`` and ``cap_state``. No totals, caps, remaining
    budgets, or key-presence flags.
    """
    day_start = _utc_day_start_iso(now)
    daily_completed = sum_completed_usage_cost(
        db_path, provider=PROVIDER_ASSEMBLYAI, since_iso=day_start
    )
    total_completed = sum_completed_usage_cost(
        db_path, provider=PROVIDER_ASSEMBLYAI
    )
    cap_state = derive_cap_state(
        daily_completed,
        total_completed,
        daily_soft_cap_usd=settings.demo_assemblyai_daily_soft_cap_usd,
        warning_cap_usd=settings.demo_assemblyai_warning_cap_usd,
        hard_cap_usd=settings.demo_assemblyai_hard_cap_usd,
    )
    state = derive_provider_state(settings.assemblyai_api_key, cap_state)
    return {"assemblyai": {"state": state, "cap_state": cap_state}}


def compute_admin_view(
    db_path: Path,
    settings: DemoSettings,
    *,
    now: Optional[datetime] = None,
) -> dict:
    """Admin-auth-only payload for /admin/stats provider_state block."""
    n = _now(now)
    day_start = n.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    daily_usd = sum_completed_usage_cost(
        db_path, provider=PROVIDER_ASSEMBLYAI, since_iso=day_start
    )
    total_usd = sum_completed_usage_cost(
        db_path, provider=PROVIDER_ASSEMBLYAI
    )
    reserved_usd = sum_reserved_usage_cost(
        db_path, provider=PROVIDER_ASSEMBLYAI
    )
    cap_state = derive_cap_state(
        daily_usd,
        total_usd,
        daily_soft_cap_usd=settings.demo_assemblyai_daily_soft_cap_usd,
        warning_cap_usd=settings.demo_assemblyai_warning_cap_usd,
        hard_cap_usd=settings.demo_assemblyai_hard_cap_usd,
    )
    state = derive_provider_state(settings.assemblyai_api_key, cap_state)
    return {
        "assemblyai": {
            "state": state,
            "cap_state": cap_state,
            "key_configured": bool(settings.assemblyai_api_key),
            "daily_usd": round(daily_usd, 6),
            "total_usd": round(total_usd, 6),
            "reserved_usd": round(reserved_usd, 6),
            "daily_soft_cap_usd": settings.demo_assemblyai_daily_soft_cap_usd,
            "warning_cap_usd": settings.demo_assemblyai_warning_cap_usd,
            "hard_cap_usd": settings.demo_assemblyai_hard_cap_usd,
            "usd_per_second_estimate": settings.demo_assemblyai_usd_per_second,
            "as_of": n.isoformat(),
        }
    }


# ---------------------------------------------------------------------------
# Reservation flow
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Reservation:
    ledger_id: str
    cap_state: str


def _reserve_in_transaction(
    db_path: Path,
    *,
    settings: DemoSettings,
    audio_duration_seconds: float,
    estimated_cost_usd: float,
    session_id_hash: Optional[str],
    job_id: Optional[str],
    now: Optional[datetime],
) -> _Reservation:
    """Atomic precheck + INSERT inside one BEGIN IMMEDIATE block.

    Raises:
        CapBlockedError: if projected_cap_state is soft_reached or hard_reached.
        LedgerWriteError: on any sqlite3.Error during reads/insert/commit.
    """
    n = _now(now)
    day_start = n.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    created_at = n.isoformat()
    ledger_id = uuid.uuid4().hex

    try:
        conn = _open(db_path)
    except sqlite3.Error as exc:
        raise LedgerWriteError(f"usage_ledger open failed: {exc}") from exc
    in_transaction = False
    try:
        try:
            conn.execute("BEGIN IMMEDIATE")
            in_transaction = True

            daily_completed = _sum_usage_cost_in_conn(
                conn,
                provider=PROVIDER_ASSEMBLYAI,
                status=LEDGER_STATUS_COMPLETED,
                since_iso=day_start,
            )
            total_completed = _sum_usage_cost_in_conn(
                conn,
                provider=PROVIDER_ASSEMBLYAI,
                status=LEDGER_STATUS_COMPLETED,
            )
            daily_reserved = _sum_usage_cost_in_conn(
                conn,
                provider=PROVIDER_ASSEMBLYAI,
                status=LEDGER_STATUS_STARTED,
                since_iso=day_start,
            )
            total_reserved = _sum_usage_cost_in_conn(
                conn,
                provider=PROVIDER_ASSEMBLYAI,
                status=LEDGER_STATUS_STARTED,
            )

            projected_daily = daily_completed + daily_reserved + estimated_cost_usd
            projected_total = total_completed + total_reserved + estimated_cost_usd
            projected_cap_state = derive_cap_state(
                projected_daily,
                projected_total,
                daily_soft_cap_usd=settings.demo_assemblyai_daily_soft_cap_usd,
                warning_cap_usd=settings.demo_assemblyai_warning_cap_usd,
                hard_cap_usd=settings.demo_assemblyai_hard_cap_usd,
            )
        except sqlite3.Error as exc:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            in_transaction = False
            raise LedgerWriteError(f"usage_ledger read failed: {exc}") from exc

        if projected_cap_state in (CAP_SOFT_REACHED, CAP_HARD_REACHED):
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            in_transaction = False
            raise CapBlockedError(projected_cap_state)

        if projected_cap_state == CAP_WARNING_REACHED:
            _log.warning(
                "assemblyai_warning_cap_projected daily_completed=%.6f total_completed=%.6f reserved=%.6f estimated_current=%.6f",
                daily_completed,
                total_completed,
                daily_reserved + total_reserved,
                estimated_cost_usd,
            )

        try:
            conn.execute(
                """
                INSERT INTO usage_ledger
                    (ledger_id, provider, session_id_hash, job_id,
                     audio_duration_seconds, estimated_cost_usd,
                     status, cap_state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ledger_id,
                    PROVIDER_ASSEMBLYAI,
                    session_id_hash,
                    job_id,
                    float(audio_duration_seconds),
                    float(estimated_cost_usd),
                    LEDGER_STATUS_STARTED,
                    projected_cap_state,
                    created_at,
                ),
            )
            conn.execute("COMMIT")
            in_transaction = False
        except sqlite3.Error as exc:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            in_transaction = False
            raise LedgerWriteError(f"usage_ledger insert failed: {exc}") from exc

        return _Reservation(ledger_id=ledger_id, cap_state=projected_cap_state)
    finally:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        conn.close()


def transcribe_with_ledger(
    adapter: _ASRAdapterLike,
    audio_path: Path,
    job_id: str,
    *,
    db_path: Path,
    settings: DemoSettings,
    audio_duration_seconds: float,
    session_id_hash: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ASRResult:
    """Reserve a usage_ledger row, call adapter.transcribe, then finalize.

    This is the only sanctioned entry point for AssemblyAI calls. The
    reservation is atomic (BEGIN IMMEDIATE) and runs precheck + INSERT in
    one connection. The adapter is invoked **after** the reservation row is
    committed.

    Raises:
        TypeError / ValueError: invalid duration or rate (caller bug).
        CapBlockedError: projected cap_state is soft_reached or hard_reached;
            adapter is not called.
        LedgerWriteError: any usage_ledger DB read/write failure;
            adapter is not called.

    On adapter success the row is updated to ``status='completed'``.
    On adapter exception the row is updated to ``status='failed'`` and the
    original exception is re-raised. If the post-call status update itself
    fails, an accounting error is logged but the original adapter exception
    is preserved (never masked by a ledger error).
    """
    estimated = estimate_cost_usd(
        audio_duration_seconds, settings.demo_assemblyai_usd_per_second
    )

    reservation = _reserve_in_transaction(
        db_path,
        settings=settings,
        audio_duration_seconds=audio_duration_seconds,
        estimated_cost_usd=estimated,
        session_id_hash=session_id_hash,
        job_id=job_id,
        now=now,
    )

    try:
        result = adapter.transcribe(audio_path, job_id)
    except BaseException:
        try:
            update_usage_ledger_status(
                db_path, reservation.ledger_id, LEDGER_STATUS_FAILED
            )
        except Exception:  # noqa: BLE001
            _log.error(
                "usage_ledger post-call update to failed status did not persist for ledger_id=%s",
                reservation.ledger_id,
            )
        raise

    try:
        update_usage_ledger_status(
            db_path, reservation.ledger_id, LEDGER_STATUS_COMPLETED
        )
    except Exception:  # noqa: BLE001
        _log.error(
            "usage_ledger post-call update to completed status did not persist for ledger_id=%s",
            reservation.ledger_id,
        )
    return result
