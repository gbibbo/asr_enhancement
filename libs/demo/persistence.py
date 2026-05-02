from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from libs.common.demo_settings import DemoSettings


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
    expires_at TIMESTAMP
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
               enhancer_version, input_artifact_path)
            VALUES (?, 'queued', ?, ?, ?, ?, ?, ?)
            """,
            (job_id, now, now, provider, degradation_id, enhancer_version, input_artifact_path),
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
