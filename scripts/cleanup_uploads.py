"""Delete expired uploads and per-job artifact directories on the demo runtime.

Defaults to dry-run. Requires ``--apply`` to perform deletions. The script
refuses by construction to touch curated examples, the cache directory, the
SQLite database, log files, ``tmp/``, source code, configs, or anything
outside ``DEMO_RUNTIME_ROOT``.

Cron (host-level, install manually with ``crontab -e`` on RP5; not committed):

    17 * * * * /usr/bin/docker compose \\
      -f /home/gbibbo/code/asr_enhancement/infra/compose/docker-compose.demo.yml \\
      run --rm \\
      -v /home/gbibbo/code/asr_enhancement/scripts:/app/scripts \\
      demo-api python scripts/cleanup_uploads.py --apply \\
      >> /home/gbibbo/asr_enhancement_runtime/logs/cleanup.log 2>&1
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from libs.common.demo_settings import DemoSettings  # noqa: E402
from libs.demo import cleanup as cleanup_lib  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete expired upload files and per-job artifact directories."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete. Without this flag the script runs dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly request dry-run mode. Mutually exclusive with --apply.",
    )
    parser.add_argument(
        "--retention-hours",
        type=float,
        default=None,
        help="Override DEMO_UPLOAD_RETENTION_HOURS. Files/dirs older than this "
        "(in hours) become candidates. Default comes from DemoSettings.",
    )
    parser.add_argument(
        "--now",
        type=str,
        default=None,
        help="ISO-8601 wall clock (test-only). Defaults to current UTC time.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def _resolve_now(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _format_human(summary: cleanup_lib.CleanupSummary) -> str:
    obj = summary.as_json_obj()
    u = obj["uploads"]
    j = obj["job_artifact_dirs"]
    label = "would delete" if obj["mode"] == "dry-run" else "deleted"
    lines = [
        f"mode={obj['mode']} retention_hours={obj['retention_hours']} now={obj['now']}",
        f"uploads:           scanned={u['scanned']} {label}={u['deleted']} "
        f"kept_in_flight={u['kept_in_flight']} kept_recent={u['kept_recent']} "
        f"skipped_unrecognized={len(u['skipped_unrecognized'])} "
        f"skipped_stat_error={len(u['skipped_stat_error'])} "
        f"bytes_freed={u['bytes_freed']}",
        f"job_artifact_dirs: scanned={j['scanned']} {label}={j['deleted']} "
        f"kept_in_flight={j['kept_in_flight']} kept_recent={j['kept_recent']} "
        f"bytes_freed={j['bytes_freed']}",
    ]
    if u["skipped_unrecognized"]:
        sample = u["skipped_unrecognized"][:10]
        lines.append(f"skipped_unrecognized_sample: {sample}")
    if obj["errors"]:
        lines.append(f"errors: {obj['errors']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.apply and args.dry_run:
        print(
            "Refusing to run: --apply and --dry-run are mutually exclusive.",
            file=sys.stderr,
        )
        return 1

    settings = DemoSettings()
    retention_hours = (
        float(args.retention_hours)
        if args.retention_hours is not None
        else float(settings.demo_upload_retention_hours)
    )
    if retention_hours < 0:
        print("Refusing to run: --retention-hours must be >= 0.", file=sys.stderr)
        return 1

    try:
        now = _resolve_now(args.now)
    except ValueError as exc:
        print(f"Invalid --now value: {exc}", file=sys.stderr)
        return 1

    if not settings.demo_runtime_root.is_dir():
        print(
            f"DEMO_RUNTIME_ROOT not found: {settings.demo_runtime_root}",
            file=sys.stderr,
        )
        return 1

    try:
        summary = cleanup_lib.run_cleanup(
            upload_dir=settings.demo_upload_dir,
            artifacts_dir=settings.demo_artifacts_dir,
            runtime_root=settings.demo_runtime_root,
            db_path=settings.demo_db_path,
            retention_hours=retention_hours,
            now=now,
            apply=args.apply,
        )
    except cleanup_lib.SafetyViolation as exc:
        # Hard abort: do not advance last_cleanup_at, do not touch anything else.
        err = {
            "event": "cleanup",
            "mode": "apply" if args.apply else "dry-run",
            "aborted": True,
            "safety_violation": exc.kind,
            "path": str(exc.path),
            "detail": exc.detail,
        }
        print(json.dumps(err, ensure_ascii=False), file=sys.stdout)
        print(f"safety_violation={exc.kind} path={exc.path}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(json.dumps(summary.as_json_obj(), ensure_ascii=False))
        print(_format_human(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
