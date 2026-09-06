"""Cleanup helpers for B9.4: prune expired uploads and per-job artifact dirs.

Pure library functions used by ``scripts/cleanup_uploads.py``. Deletion is
gated by a strict path allowlist:

* upload files live directly under ``DemoSettings.demo_upload_dir`` and must
  match ``^[0-9a-f]{32}\\.(wav|mp3|m4a|flac|tmp)$``;
* per-job artifact directories live under
  ``DemoSettings.demo_artifacts_dir / "jobs" / <uuid4>``.

Anything outside that envelope (curated examples, cache, db, logs, tmp,
config, reports, source) is refused. Symlinks are refused. Files under
``uploads/`` whose basename does not match the allowed pattern are skipped
(not deleted, not fatal). The only persisted side effect is upserting the
``last_cleanup_at`` row in ``admin_state`` after a successful ``--apply``.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


UPLOAD_NAME_RE = re.compile(r"^[0-9a-f]{32}\.(wav|mp3|m4a|flac|tmp)$")
JOB_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
TERMINAL_JOB_STATUSES: frozenset[str] = frozenset({"completed", "failed"})
IN_FLIGHT_JOB_STATUSES: frozenset[str] = frozenset({"queued", "running"})

LAST_CLEANUP_KEY = "last_cleanup_at"


class SafetyViolation(Exception):
    """Raised when a candidate path fails a hard safety check."""

    def __init__(self, kind: str, path: Path, detail: str = "") -> None:
        super().__init__(f"{kind}: {path}{(' — ' + detail) if detail else ''}")
        self.kind = kind
        self.path = path
        self.detail = detail


@dataclass
class UploadCandidate:
    path: Path
    size_bytes: int
    mtime: datetime
    age_seconds: float


@dataclass
class JobDirCandidate:
    path: Path
    job_id: str
    size_bytes: int
    mtime: datetime
    age_seconds: float
    job_status: Optional[str]  # None if no matching jobs row


@dataclass
class CleanupSummary:
    mode: str  # "dry-run" | "apply"
    retention_hours: float
    now_iso: str
    uploads_scanned: int = 0
    uploads_deleted: int = 0
    uploads_kept_in_flight: int = 0
    uploads_kept_recent: int = 0
    uploads_skipped_unrecognized: list[str] = field(default_factory=list)
    uploads_skipped_stat_error: list[str] = field(default_factory=list)
    upload_bytes_freed: int = 0
    job_dirs_scanned: int = 0
    job_dirs_deleted: int = 0
    job_dirs_kept_in_flight: int = 0
    job_dirs_kept_recent: int = 0
    job_dir_bytes_freed: int = 0
    errors: list[str] = field(default_factory=list)

    def as_json_obj(self) -> dict:
        return {
            "event": "cleanup",
            "mode": self.mode,
            "retention_hours": self.retention_hours,
            "now": self.now_iso,
            "uploads": {
                "scanned": self.uploads_scanned,
                "deleted": self.uploads_deleted,
                "kept_in_flight": self.uploads_kept_in_flight,
                "kept_recent": self.uploads_kept_recent,
                "skipped_unrecognized": list(self.uploads_skipped_unrecognized),
                "skipped_stat_error": list(self.uploads_skipped_stat_error),
                "bytes_freed": self.upload_bytes_freed,
            },
            "job_artifact_dirs": {
                "scanned": self.job_dirs_scanned,
                "deleted": self.job_dirs_deleted,
                "kept_in_flight": self.job_dirs_kept_in_flight,
                "kept_recent": self.job_dirs_kept_recent,
                "bytes_freed": self.job_dir_bytes_freed,
            },
            "errors": list(self.errors),
        }


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


def _resolve_root(runtime_root: Path) -> Path:
    return runtime_root.resolve(strict=True)


def assert_inside_root(candidate: Path, runtime_root: Path) -> Path:
    """Resolve ``candidate`` and raise SafetyViolation if it escapes the root.

    Symlinks raise ``SafetyViolation('symlink', ...)`` even if their target
    happens to land back inside the root — the policy refuses symlinks
    outright.
    """
    if candidate.is_symlink():
        raise SafetyViolation("symlink", candidate)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SafetyViolation("missing", candidate, str(exc)) from exc
    root = _resolve_root(runtime_root)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SafetyViolation("outside_root", candidate, str(exc)) from exc
    return resolved


def _first_segment(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).parts[0]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _safe_stat_mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _dir_size_bytes(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file() and not child.is_symlink():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def discover_upload_candidates(
    upload_dir: Path,
    *,
    runtime_root: Path,
    now: datetime,
    retention_seconds: float,
    summary: CleanupSummary,
) -> list[UploadCandidate]:
    """Return upload files older than retention. Skips unrecognized basenames.

    Hard safety: refuses symlinks and any path outside the runtime root.
    Files whose basename does not match ``UPLOAD_NAME_RE`` are skipped
    (recorded in ``summary.uploads_skipped_unrecognized``) — they are not
    deleted and do not abort the run.
    """
    candidates: list[UploadCandidate] = []
    if not upload_dir.is_dir():
        return candidates
    # Defensive: confirm upload_dir is itself inside the runtime root and is
    # the expected ``uploads`` segment.
    upload_dir_resolved = assert_inside_root(upload_dir, runtime_root)
    root_resolved = _resolve_root(runtime_root)
    if upload_dir_resolved.relative_to(root_resolved).parts[:1] != ("uploads",):
        raise SafetyViolation(
            "protected_segment",
            upload_dir,
            f"expected first segment 'uploads', got {upload_dir_resolved.relative_to(root_resolved).parts[:1]}",
        )

    for entry in sorted(upload_dir.iterdir()):
        # Hard safety on every child.
        if entry.is_symlink():
            raise SafetyViolation("symlink", entry)
        if not entry.is_file():
            # Subdirectories under uploads/ are unexpected; skip without
            # touching them (do not recurse, do not delete).
            continue
        if not UPLOAD_NAME_RE.match(entry.name):
            summary.uploads_skipped_unrecognized.append(entry.name)
            continue
        summary.uploads_scanned += 1
        mtime_ts = _safe_stat_mtime(entry)
        if mtime_ts is None:
            summary.uploads_skipped_stat_error.append(entry.name)
            continue
        mtime = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)
        age = (now - mtime).total_seconds()
        if age < retention_seconds:
            summary.uploads_kept_recent += 1
            continue
        try:
            size = entry.stat().st_size
        except OSError:
            size = 0
        candidates.append(
            UploadCandidate(
                path=entry,
                size_bytes=size,
                mtime=mtime,
                age_seconds=age,
            )
        )
    return candidates


def discover_job_dir_candidates(
    artifacts_dir: Path,
    *,
    runtime_root: Path,
    now: datetime,
    retention_seconds: float,
    job_status_lookup: dict[str, str],
    summary: CleanupSummary,
) -> list[JobDirCandidate]:
    """Return per-job artifact dirs older than retention with terminal/missing job.

    Aborts with SafetyViolation if a non-UUID directory is encountered under
    ``artifacts/jobs/`` — the cleaner refuses to make a guess about whether
    such a directory is operator-placed or corrupted. Symlinks are refused.
    Subdirectories under non-UUID segments are not recursed into.
    """
    jobs_root = artifacts_dir / "jobs"
    if not jobs_root.is_dir():
        return []

    jobs_root_resolved = assert_inside_root(jobs_root, runtime_root)
    root_resolved = _resolve_root(runtime_root)
    expected_prefix = ("artifacts", "jobs")
    if jobs_root_resolved.relative_to(root_resolved).parts[:2] != expected_prefix:
        raise SafetyViolation(
            "protected_segment",
            jobs_root,
            f"expected first two segments {expected_prefix}, got {jobs_root_resolved.relative_to(root_resolved).parts[:2]}",
        )

    candidates: list[JobDirCandidate] = []
    for entry in sorted(jobs_root.iterdir()):
        if entry.is_symlink():
            raise SafetyViolation("symlink", entry)
        if not entry.is_dir():
            # An unexpected file directly under artifacts/jobs/. Skip without
            # touching, but do not abort.
            continue
        if not JOB_UUID_RE.match(entry.name):
            raise SafetyViolation(
                "invalid_job_dir",
                entry,
                "directory name does not match UUID4 pattern",
            )
        summary.job_dirs_scanned += 1
        mtime_ts = _safe_stat_mtime(entry)
        if mtime_ts is None:
            continue
        mtime = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)
        age = (now - mtime).total_seconds()
        if age < retention_seconds:
            summary.job_dirs_kept_recent += 1
            continue
        status = job_status_lookup.get(entry.name)
        if status in IN_FLIGHT_JOB_STATUSES:
            summary.job_dirs_kept_in_flight += 1
            continue
        if status is not None and status not in TERMINAL_JOB_STATUSES:
            # Unknown status — treat as in-flight defensively.
            summary.job_dirs_kept_in_flight += 1
            continue
        candidates.append(
            JobDirCandidate(
                path=entry,
                job_id=entry.name,
                size_bytes=_dir_size_bytes(entry),
                mtime=mtime,
                age_seconds=age,
                job_status=status,
            )
        )
    return candidates


# ---------------------------------------------------------------------------
# DB helpers (read-only except for last_cleanup_at)
# ---------------------------------------------------------------------------


def load_in_flight_input_paths(db_path: Path) -> set[str]:
    if not db_path.is_file():
        return set()
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT input_artifact_path FROM jobs "
            "WHERE status IN ('queued', 'running') "
            "AND input_artifact_path IS NOT NULL"
        ).fetchall()
        return {row[0] for row in rows if row[0]}
    finally:
        conn.close()


def load_job_status_lookup(db_path: Path) -> dict[str, str]:
    if not db_path.is_file():
        return {}
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT job_id, status FROM jobs").fetchall()
        return {row[0]: row[1] for row in rows}
    finally:
        conn.close()


def record_last_cleanup_at(db_path: Path, now_iso: str) -> None:
    """Upsert admin_state['last_cleanup_at'] = now_iso. Idempotent."""
    if not db_path.is_file():
        return
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO admin_state (key, value, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, "
            "updated_at=excluded.updated_at",
            (LAST_CLEANUP_KEY, now_iso, now_iso),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------


def delete_upload_safely(
    candidate: UploadCandidate, *, runtime_root: Path
) -> int:
    """Delete a single upload file after re-running safety checks.

    Returns the number of bytes freed. Raises SafetyViolation on any
    irregularity (symlink, escapes root). The caller must not catch and
    silently continue — by design any safety violation aborts the whole run.
    """
    assert_inside_root(candidate.path, runtime_root)
    if candidate.path.is_symlink():
        raise SafetyViolation("symlink", candidate.path)
    size = candidate.size_bytes
    candidate.path.unlink()
    return size


def delete_job_dir_safely(
    candidate: JobDirCandidate, *, runtime_root: Path
) -> int:
    """Delete a per-job artifact directory after re-running safety checks."""
    assert_inside_root(candidate.path, runtime_root)
    if candidate.path.is_symlink():
        raise SafetyViolation("symlink", candidate.path)
    if not JOB_UUID_RE.match(candidate.path.name):
        raise SafetyViolation(
            "invalid_job_dir",
            candidate.path,
            "directory name does not match UUID4 pattern",
        )
    # Refuse to follow any symlink found inside the tree by passing
    # ``onerror=raise``-equivalent: rmtree by default does not follow symlinks
    # for directories (Python 3.11+), but symlinked files would be unlinked,
    # which is fine — we only care that we don't escape the tree. Defensive:
    # walk the tree and abort if we see a symlink that points outside root.
    root_resolved = _resolve_root(runtime_root)
    for child in candidate.path.rglob("*"):
        if child.is_symlink():
            try:
                target = child.resolve(strict=False)
                target.relative_to(root_resolved)
            except ValueError as exc:
                raise SafetyViolation(
                    "symlink", child, "symlink escapes runtime root"
                ) from exc
    size = candidate.size_bytes
    shutil.rmtree(candidate.path)
    return size


def filter_uploads_against_in_flight(
    candidates: Iterable[UploadCandidate],
    *,
    in_flight_paths: set[str],
    summary: CleanupSummary,
) -> list[UploadCandidate]:
    kept: list[UploadCandidate] = []
    for c in candidates:
        if str(c.path) in in_flight_paths:
            summary.uploads_kept_in_flight += 1
            continue
        kept.append(c)
    return kept


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_cleanup(
    *,
    upload_dir: Path,
    artifacts_dir: Path,
    runtime_root: Path,
    db_path: Path,
    retention_hours: float,
    now: datetime,
    apply: bool,
) -> CleanupSummary:
    """Top-level orchestration. Returns a populated CleanupSummary."""
    summary = CleanupSummary(
        mode="apply" if apply else "dry-run",
        retention_hours=retention_hours,
        now_iso=now.isoformat(),
    )
    retention_seconds = float(retention_hours) * 3600.0

    # Discover candidates (may raise SafetyViolation; caller surfaces exit 1).
    upload_candidates = discover_upload_candidates(
        upload_dir,
        runtime_root=runtime_root,
        now=now,
        retention_seconds=retention_seconds,
        summary=summary,
    )
    in_flight_paths = load_in_flight_input_paths(db_path)
    upload_candidates = filter_uploads_against_in_flight(
        upload_candidates,
        in_flight_paths=in_flight_paths,
        summary=summary,
    )

    job_status_lookup = load_job_status_lookup(db_path)
    job_dir_candidates = discover_job_dir_candidates(
        artifacts_dir,
        runtime_root=runtime_root,
        now=now,
        retention_seconds=retention_seconds,
        job_status_lookup=job_status_lookup,
        summary=summary,
    )

    if not apply:
        # Dry-run: we don't delete, just count what would happen.
        for c in upload_candidates:
            summary.uploads_deleted += 1
            summary.upload_bytes_freed += c.size_bytes
        for c in job_dir_candidates:
            summary.job_dirs_deleted += 1
            summary.job_dir_bytes_freed += c.size_bytes
        # Reset "deleted" labels so the JSON is honest about dry-run intent.
        # We use the `mode` field and the human summary to disambiguate; the
        # numeric counts represent "would delete" when mode=dry-run.
        return summary

    # Apply: actually delete. Any SafetyViolation aborts (propagates).
    for c in upload_candidates:
        freed = delete_upload_safely(c, runtime_root=runtime_root)
        summary.uploads_deleted += 1
        summary.upload_bytes_freed += freed
    for c in job_dir_candidates:
        freed = delete_job_dir_safely(c, runtime_root=runtime_root)
        summary.job_dirs_deleted += 1
        summary.job_dir_bytes_freed += freed

    # Record cleanup completion only after all deletions succeeded.
    record_last_cleanup_at(db_path, now.isoformat())
    return summary
