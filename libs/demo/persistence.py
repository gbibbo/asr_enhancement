from __future__ import annotations

import logging
import math
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from libs.common.demo_settings import DemoSettings

_log = logging.getLogger("demo-api.persistence")


class QueueFullError(Exception):
    pass


_DDL = """\
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    provider TEXT NOT NULL,
    degradation_id TEXT,
    enhancer_version TEXT,
    input_artifact_path TEXT,
    degraded_artifact_path TEXT,
    enhanced_artifact_path TEXT,
    result_json TEXT,
    error_message TEXT,
    expires_at TIMESTAMP,
    session_id_hash TEXT
);

CREATE TABLE IF NOT EXISTS cache_entries (
    cache_key TEXT PRIMARY KEY,
    example_id TEXT NOT NULL,
    degradation_id TEXT NOT NULL,
    degradation_version TEXT NOT NULL,
    asr_provider TEXT NOT NULL,
    asr_model_version TEXT NOT NULL,
    enhancer_version TEXT NOT NULL,
    metrics_version TEXT NOT NULL,
    result_json TEXT NOT NULL,
    artifact_root TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    validated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_ledger (
    ledger_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    session_id_hash TEXT,
    job_id TEXT,
    audio_duration_seconds REAL NOT NULL,
    estimated_cost_usd REAL NOT NULL,
    status TEXT NOT NULL,
    cap_state TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
"""


def _open(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def ensure_runtime_dirs(settings: DemoSettings) -> None:
    for path in (
        settings.demo_db_path.parent,
        settings.demo_upload_dir,
        settings.demo_cache_dir,
        settings.demo_artifacts_dir,
        settings.demo_logs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def init_schema(db_path: Path) -> None:
    conn = _open(db_path)
    try:
        conn.executescript(_DDL)
        # Idempotent migration: pre-B10.2 jobs tables lack session_id_hash.
        cols = {row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}
        if "session_id_hash" not in cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN session_id_hash TEXT")
    finally:
        conn.close()


def count_active_jobs(db_path: Path) -> int:
    conn = _open(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('queued', 'running')"
        ).fetchone()
        return row[0]
    finally:
        conn.close()


def try_create_job(
    db_path: Path,
    *,
    queue_max: int,
    provider: str,
    degradation_id: Optional[str] = None,
    enhancer_version: Optional[str] = None,
    input_artifact_path: Optional[str] = None,
    session_id_hash: Optional[str] = None,
) -> str:
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
    in_transaction = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        in_transaction = True
        active = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('queued', 'running')"
        ).fetchone()[0]
        if active >= queue_max:
            conn.execute("ROLLBACK")
            in_transaction = False
            raise QueueFullError(f"Queue full: {active} active jobs (max {queue_max})")
        conn.execute(
            """
            INSERT INTO jobs
              (job_id, status, created_at, updated_at, provider, degradation_id,
               enhancer_version, input_artifact_path, session_id_hash)
            VALUES (?, 'queued', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                now,
                now,
                provider,
                degradation_id,
                enhancer_version,
                input_artifact_path,
                session_id_hash,
            ),
        )
        conn.execute("COMMIT")
        in_transaction = False
        return job_id
    finally:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
        conn.close()


def get_job(db_path: Path, job_id: str) -> Optional[dict]:
    conn = _open(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_job_status(
    db_path: Path,
    job_id: str,
    status: str,
    *,
    error_message: Optional[str] = None,
    result_json: Optional[str] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
    try:
        conn.execute(
            """
            UPDATE jobs SET status=?, updated_at=?, error_message=?, result_json=?
            WHERE job_id=?
            """,
            (status, now, error_message, result_json, job_id),
        )
    finally:
        conn.close()


def update_job_artifacts(
    db_path: Path,
    job_id: str,
    *,
    degraded_artifact_path: Optional[str] = None,
    enhanced_artifact_path: Optional[str] = None,
) -> None:
    """Update only the artifact-path columns and ``updated_at``.

    Pass ``None`` to leave a column unchanged. Calling with both arguments
    ``None`` is a no-op (does not touch ``updated_at``) so callers can invoke
    the helper unconditionally without spuriously bumping the timestamp.
    """
    assignments: list[str] = []
    params: list = []
    if degraded_artifact_path is not None:
        assignments.append("degraded_artifact_path = ?")
        params.append(degraded_artifact_path)
    if enhanced_artifact_path is not None:
        assignments.append("enhanced_artifact_path = ?")
        params.append(enhanced_artifact_path)
    if not assignments:
        return
    assignments.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(job_id)
    sql = f"UPDATE jobs SET {', '.join(assignments)} WHERE job_id = ?"
    conn = _open(db_path)
    try:
        conn.execute(sql, tuple(params))
    finally:
        conn.close()


def claim_next_job(db_path: Path) -> Optional[dict]:
    now = datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
    in_transaction = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        in_transaction = True
        row = conn.execute(
            "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if row is None:
            conn.execute("ROLLBACK")
            in_transaction = False
            return None
        job = dict(row)
        conn.execute(
            "UPDATE jobs SET status='running', updated_at=? WHERE job_id=?",
            (now, job["job_id"]),
        )
        conn.execute("COMMIT")
        in_transaction = False
        job["status"] = "running"
        job["updated_at"] = now
        return job
    finally:
        if in_transaction:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
        conn.close()


def get_cache_entry(db_path: Path, cache_key: str) -> Optional[dict]:
    conn = _open(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM cache_entries WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def upsert_cache_entry(
    db_path: Path,
    *,
    cache_key: str,
    example_id: str,
    degradation_id: str,
    degradation_version: str,
    asr_provider: str,
    asr_model_version: str,
    enhancer_version: str,
    metrics_version: str,
    result_json: str,
    artifact_root: str,
) -> str:
    """Insert or replace a cache_entries row.

    Returns "inserted" or "updated" depending on whether a row with the same
    cache_key existed before the call.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
    try:
        existing = conn.execute(
            "SELECT 1 FROM cache_entries WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        action = "updated" if existing else "inserted"
        conn.execute(
            """
            INSERT INTO cache_entries (
                cache_key, example_id, degradation_id, degradation_version,
                asr_provider, asr_model_version, enhancer_version, metrics_version,
                result_json, artifact_root, created_at, validated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(cache_key) DO UPDATE SET
                example_id=excluded.example_id,
                degradation_id=excluded.degradation_id,
                degradation_version=excluded.degradation_version,
                asr_provider=excluded.asr_provider,
                asr_model_version=excluded.asr_model_version,
                enhancer_version=excluded.enhancer_version,
                metrics_version=excluded.metrics_version,
                result_json=excluded.result_json,
                artifact_root=excluded.artifact_root,
                created_at=excluded.created_at,
                validated_at=NULL
            """,
            (
                cache_key,
                example_id,
                degradation_id,
                degradation_version,
                asr_provider,
                asr_model_version,
                enhancer_version,
                metrics_version,
                result_json,
                artifact_root,
                now,
            ),
        )
        return action
    finally:
        conn.close()


def list_cache_entries(db_path: Path) -> list[dict]:
    conn = _open(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM cache_entries ORDER BY cache_key"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_cache_entries(
    db_path: Path,
    *,
    where_sql: str,
    params: tuple,
    dry_run: bool = True,
) -> tuple[int, list[str]]:
    """Delete cache_entries rows matching the supplied WHERE clause.

    Returns (matched_count, sample_cache_keys). When dry_run is True, no rows
    are deleted; the function only counts matches and returns up to 10 sample
    cache_keys for preview.
    """
    if not where_sql.strip():
        raise ValueError("where_sql must not be empty (refusing unfiltered delete)")
    conn = _open(db_path)
    try:
        count_row = conn.execute(
            f"SELECT COUNT(*) FROM cache_entries WHERE {where_sql}", params
        ).fetchone()
        matched = int(count_row[0])
        sample_rows = conn.execute(
            f"SELECT cache_key FROM cache_entries WHERE {where_sql} "
            f"ORDER BY cache_key LIMIT 10",
            params,
        ).fetchall()
        sample = [r[0] for r in sample_rows]
        if not dry_run and matched > 0:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    f"DELETE FROM cache_entries WHERE {where_sql}", params
                )
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        return matched, sample
    finally:
        conn.close()


def mark_cache_entry_validated(db_path: Path, cache_key: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
    try:
        conn.execute(
            "UPDATE cache_entries SET validated_at = ? WHERE cache_key = ?",
            (now, cache_key),
        )
    finally:
        conn.close()


def get_jobs_stats(db_path: Path) -> dict:
    conn = _open(db_path)
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM jobs GROUP BY status"
        ).fetchall()
        result: dict = {"queued": 0, "running": 0, "completed": 0, "failed": 0}
        for row in rows:
            status, count = row[0], row[1]
            if status in result:
                result[status] = count
        return result
    finally:
        conn.close()


def set_admin_state(db_path: Path, key: str, value: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO admin_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now),
        )
    finally:
        conn.close()


def get_admin_state_value(db_path: Path, key: str) -> Optional[str]:
    conn = _open(db_path)
    try:
        row = conn.execute(
            "SELECT value FROM admin_state WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# B10.1 usage_ledger helpers
# ---------------------------------------------------------------------------

_LEDGER_SUM_WARNED = False


def _safe_cost(value: object) -> float:
    """Coerce an estimated_cost_usd cell to a non-negative finite float.

    Non-finite or negative values are treated as 0.0 and a single structured
    warning is emitted across the process lifetime so that operator review is
    possible without flooding logs.
    """
    global _LEDGER_SUM_WARNED
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        f = float("nan")
    if not math.isfinite(f) or f < 0.0:
        if not _LEDGER_SUM_WARNED:
            _log.warning("usage_ledger contains a non-finite or negative cost value; treating as 0.0")
            _LEDGER_SUM_WARNED = True
        return 0.0
    return f


def insert_usage_ledger(
    db_path: Path,
    *,
    provider: str,
    audio_duration_seconds: float,
    estimated_cost_usd: float,
    status: str,
    cap_state: str,
    session_id_hash: Optional[str] = None,
    job_id: Optional[str] = None,
    now: Optional[str] = None,
) -> str:
    """Insert a usage_ledger row and return the generated ledger_id."""
    ledger_id = uuid.uuid4().hex
    created_at = now or datetime.now(timezone.utc).isoformat()
    conn = _open(db_path)
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
                provider,
                session_id_hash,
                job_id,
                float(audio_duration_seconds),
                float(estimated_cost_usd),
                status,
                cap_state,
                created_at,
            ),
        )
        return ledger_id
    finally:
        conn.close()


def update_usage_ledger_status(
    db_path: Path, ledger_id: str, status: str
) -> None:
    """Update only the status column of a usage_ledger row.

    No row-existence assertion: an UPDATE matching no rows is a silent no-op.
    Other columns (cap_state, estimated_cost_usd, created_at) are left intact
    so that the precheck snapshot is preserved.
    """
    conn = _open(db_path)
    try:
        conn.execute(
            "UPDATE usage_ledger SET status = ? WHERE ledger_id = ?",
            (status, ledger_id),
        )
    finally:
        conn.close()


def get_usage_ledger_row(db_path: Path, ledger_id: str) -> Optional[dict]:
    conn = _open(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM usage_ledger WHERE ledger_id = ?", (ledger_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _sum_usage_cost_in_conn(
    conn: sqlite3.Connection,
    *,
    provider: str,
    status: str,
    since_iso: Optional[str] = None,
) -> float:
    """Sum estimated_cost_usd for a provider/status, optionally since an ISO ts.

    Operates inside the caller's connection so it can participate in a
    BEGIN IMMEDIATE transaction. Non-finite/negative values are treated as 0
    via _safe_cost.
    """
    if since_iso is None:
        rows = conn.execute(
            "SELECT estimated_cost_usd FROM usage_ledger "
            "WHERE provider = ? AND status = ?",
            (provider, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT estimated_cost_usd FROM usage_ledger "
            "WHERE provider = ? AND status = ? AND created_at >= ?",
            (provider, status, since_iso),
        ).fetchall()
    return sum(_safe_cost(r[0]) for r in rows)


def sum_completed_usage_cost(
    db_path: Path,
    *,
    provider: str,
    since_iso: Optional[str] = None,
) -> float:
    """Sum estimated_cost_usd over status='completed' rows for provider."""
    conn = _open(db_path)
    try:
        return _sum_usage_cost_in_conn(
            conn, provider=provider, status="completed", since_iso=since_iso
        )
    finally:
        conn.close()


def sum_reserved_usage_cost(
    db_path: Path,
    *,
    provider: str,
    since_iso: Optional[str] = None,
) -> float:
    """Sum estimated_cost_usd over status='started' rows for provider."""
    conn = _open(db_path)
    try:
        return _sum_usage_cost_in_conn(
            conn, provider=provider, status="started", since_iso=since_iso
        )
    finally:
        conn.close()


def count_usage_rows(
    db_path: Path,
    *,
    provider: str,
    status: Optional[str] = None,
    since_iso: Optional[str] = None,
) -> int:
    conn = _open(db_path)
    try:
        sql = "SELECT COUNT(*) FROM usage_ledger WHERE provider = ?"
        params: list = [provider]
        if status is not None:
            sql += " AND status = ?"
            params.append(status)
        if since_iso is not None:
            sql += " AND created_at >= ?"
            params.append(since_iso)
        return int(conn.execute(sql, tuple(params)).fetchone()[0])
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# B10.2 session-limit helpers
# ---------------------------------------------------------------------------


def count_session_assemblyai_usage(
    db_path: Path,
    *,
    session_id_hash: str,
    since_iso: str,
) -> int:
    """Count usage_ledger rows that consume the user's session quota."""
    conn = _open(db_path)
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM usage_ledger
            WHERE provider = 'assemblyai'
              AND session_id_hash = ?
              AND status IN ('started', 'completed')
              AND created_at >= ?
            """,
            (session_id_hash, since_iso),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def count_pending_session_assemblyai_jobs(
    db_path: Path,
    *,
    session_id_hash: str,
    since_iso: str,
) -> int:
    """Count queued/running AssemblyAI jobs for this session in the window."""
    conn = _open(db_path)
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) FROM jobs
            WHERE provider = 'assemblyai'
              AND session_id_hash = ?
              AND status IN ('queued', 'running')
              AND created_at >= ?
            """,
            (session_id_hash, since_iso),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def count_effective_session_assemblyai_uses(
    db_path: Path,
    *,
    session_id_hash: str,
    since_iso: str,
) -> int:
    """De-duplicated session count used by the API gate.

    Counts AssemblyAI uses for a single session in the rolling window without
    double-counting a job that is simultaneously ``running`` and already has a
    ``started`` ledger row. The ledger row is the canonical entry; pending
    jobs are added only when no ledger row exists yet for that ``job_id``.
    """
    conn = _open(db_path)
    try:
        row = conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM usage_ledger
                 WHERE provider = 'assemblyai'
                   AND session_id_hash = ?
                   AND status IN ('started', 'completed')
                   AND created_at >= ?)
              +
              (SELECT COUNT(*) FROM jobs
                 WHERE provider = 'assemblyai'
                   AND session_id_hash = ?
                   AND status IN ('queued', 'running')
                   AND created_at >= ?
                   AND job_id NOT IN (
                     SELECT job_id FROM usage_ledger
                       WHERE provider = 'assemblyai'
                         AND session_id_hash = ?
                         AND status IN ('started', 'completed')
                         AND created_at >= ?
                         AND job_id IS NOT NULL
                   ))
            """,
            (
                session_id_hash, since_iso,
                session_id_hash, since_iso,
                session_id_hash, since_iso,
            ),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()
