"""B9.4 — cleanup script tests.

Covers ``libs/demo/cleanup.py`` and ``scripts/cleanup_uploads.py``.
No real audio, no AssemblyAI, no Whisper, no network. Files are seeded
with byte payloads and aged via ``os.utime``.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import sqlite3
import sys
import uuid
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "cleanup_uploads.py"


_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT",
    "DEMO_DB_PATH",
    "DEMO_UPLOAD_DIR",
    "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR",
    "DEMO_LOGS_DIR",
    "DEMO_WORKER_CONCURRENCY",
    "DEMO_QUEUE_MAX",
    "DEMO_UPLOAD_LIMIT_BYTES",
    "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "DEMO_UPLOAD_RETENTION_HOURS",
    "ASSEMBLYAI_API_KEY",
    "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD",
    "DEMO_EXAMPLES_CONFIG",
]


@pytest.fixture()
def settings(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from libs.common.demo_settings import DemoSettings
    return DemoSettings()


@pytest.fixture()
def runtime(settings):
    from libs.demo.persistence import ensure_runtime_dirs, init_schema
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    (settings.demo_artifacts_dir / "jobs").mkdir(parents=True, exist_ok=True)
    (settings.demo_artifacts_dir / "examples").mkdir(parents=True, exist_ok=True)
    return settings


@pytest.fixture()
def script_mod():
    spec = importlib.util.spec_from_file_location(
        "b9_4_cleanup_under_test", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hex32() -> str:
    return uuid.uuid4().hex  # 32 hex chars


def _write_upload(upload_dir: Path, *, age_hours: float, ext: str = "wav",
                  size: int = 100, basename: str | None = None) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = basename if basename is not None else f"{_hex32()}.{ext}"
    path = upload_dir / name
    path.write_bytes(b"x" * size)
    if age_hours > 0:
        ts = datetime.now(timezone.utc).timestamp() - age_hours * 3600
        os.utime(path, (ts, ts))
    return path


def _write_job_dir(jobs_root: Path, *, age_hours: float,
                   job_id: str | None = None,
                   files: tuple[tuple[str, int], ...] = (("muffled.wav", 200),),
                   ) -> tuple[Path, str]:
    jobs_root.mkdir(parents=True, exist_ok=True)
    jid = job_id if job_id is not None else str(uuid.uuid4())
    d = jobs_root / jid
    d.mkdir()
    for fname, size in files:
        (d / fname).write_bytes(b"y" * size)
    if age_hours > 0:
        ts = datetime.now(timezone.utc).timestamp() - age_hours * 3600
        for child in d.rglob("*"):
            os.utime(child, (ts, ts))
        os.utime(d, (ts, ts))
    return d, jid


def _insert_job(db_path: Path, *, job_id: str, status: str,
                input_artifact_path: str | None = None,
                provider: str = "whisper") -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO jobs "
        "(job_id, status, created_at, updated_at, provider, input_artifact_path) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, status, now, now, provider, input_artifact_path),
    )
    conn.commit()
    conn.close()


def _table_snapshot(db_path: Path, table: str) -> list[tuple]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
        return rows
    finally:
        conn.close()


def _admin_state_snapshot(db_path: Path) -> dict[str, str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT key, value FROM admin_state").fetchall()
        return {k: v for (k, v) in rows}
    finally:
        conn.close()


def _run(script_mod, args: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = script_mod.main(args)
    return rc, out.getvalue(), err.getvalue()


def _parse_summary_json(stdout: str) -> dict:
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("event") == "cleanup":
            return obj
    raise AssertionError(f"no cleanup JSON line in stdout: {stdout!r}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dry_run_default_deletes_nothing(runtime, script_mod):
    p = _write_upload(runtime.demo_upload_dir, age_hours=48)
    job_dir, _ = _write_job_dir(runtime.demo_artifacts_dir / "jobs", age_hours=48)

    rc, stdout, _ = _run(script_mod, [])
    assert rc == 0
    assert p.exists()
    assert job_dir.exists()
    summary = _parse_summary_json(stdout)
    assert summary["mode"] == "dry-run"
    assert summary["uploads"]["deleted"] == 1  # "would delete"
    assert summary["job_artifact_dirs"]["deleted"] == 1
    # last_cleanup_at must NOT be set on dry-run.
    assert "last_cleanup_at" not in _admin_state_snapshot(runtime.demo_db_path)


def test_apply_deletes_expired_uploads(runtime, script_mod):
    expired = _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc, stdout, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert not expired.exists()
    summary = _parse_summary_json(stdout)
    assert summary["mode"] == "apply"
    assert summary["uploads"]["deleted"] == 1
    assert summary["uploads"]["bytes_freed"] >= 100
    assert "last_cleanup_at" in _admin_state_snapshot(runtime.demo_db_path)


def test_apply_keeps_recent_uploads(runtime, script_mod):
    recent = _write_upload(runtime.demo_upload_dir, age_hours=1)
    rc, stdout, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert recent.exists()
    summary = _parse_summary_json(stdout)
    assert summary["uploads"]["deleted"] == 0
    assert summary["uploads"]["kept_recent"] == 1


def test_apply_keeps_in_flight_uploads(runtime, script_mod):
    in_flight = _write_upload(runtime.demo_upload_dir, age_hours=48)
    job_id = str(uuid.uuid4())
    _insert_job(
        runtime.demo_db_path,
        job_id=job_id,
        status="running",
        input_artifact_path=str(in_flight),
    )
    rc, stdout, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert in_flight.exists(), "in-flight upload must be preserved"
    summary = _parse_summary_json(stdout)
    assert summary["uploads"]["kept_in_flight"] == 1
    assert summary["uploads"]["deleted"] == 0


def test_apply_deletes_completed_job_artifact_dirs(runtime, script_mod):
    job_dir, jid = _write_job_dir(
        runtime.demo_artifacts_dir / "jobs", age_hours=48
    )
    _insert_job(runtime.demo_db_path, job_id=jid, status="completed")
    rc, _, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert not job_dir.exists()


def test_apply_keeps_running_job_artifact_dirs(runtime, script_mod):
    job_dir, jid = _write_job_dir(
        runtime.demo_artifacts_dir / "jobs", age_hours=48
    )
    _insert_job(runtime.demo_db_path, job_id=jid, status="running")
    rc, stdout, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert job_dir.exists()
    summary = _parse_summary_json(stdout)
    assert summary["job_artifact_dirs"]["kept_in_flight"] == 1


def test_apply_deletes_orphan_job_dirs(runtime, script_mod):
    """UUID-named job dir with no matching jobs row → eligible after retention."""
    job_dir, _jid = _write_job_dir(
        runtime.demo_artifacts_dir / "jobs", age_hours=48
    )
    rc, _, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert not job_dir.exists()


def test_aborts_on_invalid_uuid_job_dir(runtime, script_mod):
    bad_dir = runtime.demo_artifacts_dir / "jobs" / "not-a-uuid"
    bad_dir.mkdir(parents=True)
    (bad_dir / "data.bin").write_bytes(b"z" * 50)
    # Also seed an otherwise-deletable upload to confirm nothing else gets
    # deleted in the same aborted run.
    other = _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc, stdout, stderr = _run(script_mod, ["--apply"])
    assert rc == 1
    assert "safety_violation=invalid_job_dir" in stderr
    assert bad_dir.exists()
    assert other.exists(), "no other deletions in aborted run"
    assert "last_cleanup_at" not in _admin_state_snapshot(runtime.demo_db_path)


def test_refuses_to_touch_curated_examples(runtime, script_mod):
    ex_dir = runtime.demo_artifacts_dir / "examples" / "ex001"
    ex_dir.mkdir(parents=True)
    ex_file = ex_dir / "clean.wav"
    ex_file.write_bytes(b"audio")
    ts = datetime.now(timezone.utc).timestamp() - 100 * 3600
    os.utime(ex_file, (ts, ts))
    os.utime(ex_dir, (ts, ts))
    rc, _, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert ex_file.exists()
    assert ex_file.read_bytes() == b"audio"


def test_refuses_to_touch_cache_dir(runtime, script_mod):
    cache_file = runtime.demo_cache_dir / "whisper" / "x.bin"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(b"cache")
    ts = datetime.now(timezone.utc).timestamp() - 100 * 3600
    os.utime(cache_file, (ts, ts))
    # Also confirm cache_entries row counts unchanged.
    from libs.demo.persistence import upsert_cache_entry
    upsert_cache_entry(
        runtime.demo_db_path,
        cache_key="cache-test-key",
        example_id="ex001",
        degradation_id="clean",
        degradation_version="degradation_v1",
        asr_provider="whisper",
        asr_model_version="tiny.en",
        enhancer_version="bypass",
        metrics_version="metrics_v1",
        result_json="{}",
        artifact_root=str(runtime.demo_cache_dir),
    )
    before = _table_snapshot(runtime.demo_db_path, "cache_entries")
    rc, _, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert cache_file.exists()
    assert cache_file.read_bytes() == b"cache"
    after = _table_snapshot(runtime.demo_db_path, "cache_entries")
    assert after == before


def test_refuses_to_touch_logs_db_tmp(runtime, script_mod):
    log_file = runtime.demo_logs_dir / "demo.log"
    log_file.write_bytes(b"log")
    tmp_file = runtime.demo_runtime_root / "tmp" / "scratch.bin"
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(b"tmp")
    ts = datetime.now(timezone.utc).timestamp() - 100 * 3600
    os.utime(log_file, (ts, ts))
    os.utime(tmp_file, (ts, ts))
    rc, _, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert log_file.exists() and log_file.read_bytes() == b"log"
    assert tmp_file.exists() and tmp_file.read_bytes() == b"tmp"
    assert runtime.demo_db_path.is_file()


def test_symlink_under_uploads_is_refused(runtime, script_mod):
    target = runtime.demo_runtime_root.parent / "external_target.txt"
    target.write_bytes(b"do-not-touch")
    link = runtime.demo_upload_dir / f"{_hex32()}.wav"
    runtime.demo_upload_dir.mkdir(parents=True, exist_ok=True)
    os.symlink(str(target), str(link))
    # Also seed another expired upload to confirm no deletion happens in
    # the aborted run.
    other = _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc, _stdout, stderr = _run(script_mod, ["--apply"])
    assert rc == 1
    assert "safety_violation=symlink" in stderr
    assert link.is_symlink()
    assert target.exists() and target.read_bytes() == b"do-not-touch"
    assert other.exists()
    assert "last_cleanup_at" not in _admin_state_snapshot(runtime.demo_db_path)


def test_unrecognized_filename_is_skipped_not_deleted(runtime, script_mod):
    runtime.demo_upload_dir.mkdir(parents=True, exist_ok=True)
    notes = _write_upload(
        runtime.demo_upload_dir, age_hours=48, basename="notes.txt"
    )
    partial = _write_upload(
        runtime.demo_upload_dir, age_hours=48, basename=".partial"
    )
    expired = _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc, stdout, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    assert notes.exists()
    assert partial.exists()
    assert not expired.exists()
    summary = _parse_summary_json(stdout)
    assert "notes.txt" in summary["uploads"]["skipped_unrecognized"]
    assert ".partial" in summary["uploads"]["skipped_unrecognized"]
    assert summary["uploads"]["deleted"] == 1


def test_idempotency(runtime, script_mod):
    expired = _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc1, _, _ = _run(script_mod, ["--apply"])
    rc2, stdout2, _ = _run(script_mod, ["--apply"])
    assert rc1 == 0 and rc2 == 0
    assert not expired.exists()
    summary2 = _parse_summary_json(stdout2)
    assert summary2["uploads"]["deleted"] == 0
    assert summary2["uploads"]["scanned"] == 0
    assert "last_cleanup_at" in _admin_state_snapshot(runtime.demo_db_path)


def test_retention_hours_override(runtime, script_mod):
    recent = _write_upload(runtime.demo_upload_dir, age_hours=1)
    rc, stdout, _ = _run(script_mod, ["--apply", "--retention-hours", "0"])
    assert rc == 0
    assert not recent.exists()
    summary = _parse_summary_json(stdout)
    assert summary["retention_hours"] == 0


def test_summary_json_well_formed(runtime, script_mod):
    _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc, stdout, _ = _run(script_mod, [])
    assert rc == 0
    summary = _parse_summary_json(stdout)
    for key in ("event", "mode", "retention_hours", "now", "uploads",
                "job_artifact_dirs", "errors"):
        assert key in summary, f"missing key {key}"
    for key in ("scanned", "deleted", "kept_in_flight", "kept_recent",
                "skipped_unrecognized", "skipped_stat_error", "bytes_freed"):
        assert key in summary["uploads"], f"missing uploads.{key}"
    for key in ("scanned", "deleted", "kept_in_flight", "kept_recent",
                "bytes_freed"):
        assert key in summary["job_artifact_dirs"], f"missing job_artifact_dirs.{key}"


def test_does_not_log_original_upload_filenames(runtime, script_mod):
    # Files on disk are hex-named by upload.py contract; the test asserts no
    # "Content-Disposition"-style original name leaks into stdout. The fixture
    # name "secret_recording.wav" should never appear (we don't seed it; but
    # we DO seed an unrecognized name, which IS allowed in stdout under
    # skipped_unrecognized). The structural property: no filename outside the
    # set of seeded basenames + skip-list appears.
    seeded_hex = _write_upload(runtime.demo_upload_dir, age_hours=48)
    rc, stdout, _ = _run(script_mod, ["--apply"])
    assert rc == 0
    # The hex basename may appear in the JSON summary (it's already on disk)
    # — but the canonical "no original filename" assertion is that nothing
    # like "Content-Disposition" or "filename=" tokens leak.
    assert "Content-Disposition" not in stdout
    assert "filename=" not in stdout


def test_apply_dry_run_mutually_exclusive(runtime, script_mod):
    rc, _, stderr = _run(script_mod, ["--apply", "--dry-run"])
    assert rc == 1
    assert "mutually exclusive" in stderr


def test_only_admin_state_last_cleanup_at_is_written(runtime, script_mod):
    # Seed deletable items and DB rows in every protected table.
    _write_upload(runtime.demo_upload_dir, age_hours=48)
    job_dir, jid = _write_job_dir(
        runtime.demo_artifacts_dir / "jobs", age_hours=48
    )
    _insert_job(runtime.demo_db_path, job_id=jid, status="completed")

    from libs.demo.persistence import (
        set_admin_state,
        upsert_cache_entry,
    )
    upsert_cache_entry(
        runtime.demo_db_path,
        cache_key="ck-1",
        example_id="ex001",
        degradation_id="clean",
        degradation_version="degradation_v1",
        asr_provider="whisper",
        asr_model_version="tiny.en",
        enhancer_version="bypass",
        metrics_version="metrics_v1",
        result_json="{}",
        artifact_root=str(runtime.demo_cache_dir),
    )
    # Insert a usage_ledger row directly (B10 helper not yet present).
    conn = sqlite3.connect(str(runtime.demo_db_path))
    conn.execute(
        "INSERT INTO usage_ledger "
        "(ledger_id, provider, audio_duration_seconds, estimated_cost_usd, "
        " status, cap_state, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("led-1", "assemblyai", 12.5, 0.005, "ok", "available",
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()

    set_admin_state(runtime.demo_db_path, "startup_time", "2026-05-01T00:00:00+00:00")
    set_admin_state(runtime.demo_db_path, "other_key", "other_value")

    jobs_before = _table_snapshot(runtime.demo_db_path, "jobs")
    cache_before = _table_snapshot(runtime.demo_db_path, "cache_entries")
    ledger_before = _table_snapshot(runtime.demo_db_path, "usage_ledger")
    admin_before = _admin_state_snapshot(runtime.demo_db_path)

    rc, _, _ = _run(script_mod, ["--apply"])
    assert rc == 0

    jobs_after = _table_snapshot(runtime.demo_db_path, "jobs")
    cache_after = _table_snapshot(runtime.demo_db_path, "cache_entries")
    ledger_after = _table_snapshot(runtime.demo_db_path, "usage_ledger")
    admin_after = _admin_state_snapshot(runtime.demo_db_path)

    assert jobs_after == jobs_before, "jobs rows must not change"
    assert cache_after == cache_before, "cache_entries must not change"
    assert ledger_after == ledger_before, "usage_ledger must not change"

    # admin_state diff: only last_cleanup_at appears or changes.
    assert "last_cleanup_at" in admin_after
    expected_unchanged = {k: v for k, v in admin_after.items()
                          if k != "last_cleanup_at"}
    assert expected_unchanged == admin_before

    # The on-disk side effects must have happened.
    assert not job_dir.exists()


def test_outside_root_symlink_target_is_refused(runtime, script_mod):
    """Even if a symlink's target lands inside root, refuse the symlink."""
    inside_target = runtime.demo_artifacts_dir / "examples" / "decoy.wav"
    inside_target.parent.mkdir(parents=True, exist_ok=True)
    inside_target.write_bytes(b"decoy")
    runtime.demo_upload_dir.mkdir(parents=True, exist_ok=True)
    link = runtime.demo_upload_dir / f"{_hex32()}.wav"
    os.symlink(str(inside_target), str(link))
    rc, _, stderr = _run(script_mod, ["--apply"])
    assert rc == 1
    assert "safety_violation=symlink" in stderr
    assert link.is_symlink()
    assert inside_target.exists() and inside_target.read_bytes() == b"decoy"
