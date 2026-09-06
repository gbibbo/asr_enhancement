"""Validate every row in the demo SQLite ``cache_entries`` table.

Per-row checks:

1. ``cache_key`` recomputes from the row's components via
   ``libs.demo.cache.build_cache_key``.
2. ``degradation_version`` and ``metrics_version`` match the current
   ``libs.common.versions`` constants. Mismatch => ``stale_version``.
3. ``artifact_root`` exists, is a directory, and is contained inside the
   configured artifacts root.
4. ``result_json`` parses as JSON and contains ``audio_path_relative``,
   ``audio_sha256``. The audio file exists at
   ``Path(artifact_root) / audio_path_relative`` and its sha256 matches.

Writes a JSON + Markdown report. Exits 0 by default; ``--strict`` makes it
exit 1 on any non-``ok`` row. With ``--mark-validated``, ``ok`` rows have
``validated_at`` updated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from libs.common import versions  # noqa: E402
from libs.common.demo_settings import DemoSettings  # noqa: E402
from libs.demo import persistence  # noqa: E402
from libs.demo.cache import build_cache_key  # noqa: E402


OUTCOME_ORDER = [
    "ok",
    "stale_version",
    "key_mismatch",
    "missing_artifact",
    "sha256_mismatch",
    "bad_payload",
]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _classify_row(row: dict, artifacts_root: Path) -> tuple[str, str | None]:
    if (
        row["degradation_version"] != versions.DEGRADATION_VERSION
        or row["metrics_version"] != versions.METRICS_VERSION
    ):
        return "stale_version", (
            f"row versions (deg={row['degradation_version']}, "
            f"metrics={row['metrics_version']}) != current "
            f"(deg={versions.DEGRADATION_VERSION}, "
            f"metrics={versions.METRICS_VERSION})"
        )

    expected_key = build_cache_key(
        example_id=row["example_id"],
        degradation_id=row["degradation_id"],
        asr_provider=row["asr_provider"],
        asr_model_version=row["asr_model_version"],
        enhancer_version=row["enhancer_version"],
    )
    if expected_key != row["cache_key"]:
        return "key_mismatch", (
            f"recomputed key {expected_key} != stored {row['cache_key']}"
        )

    artifact_root = Path(row["artifact_root"])
    if not artifact_root.is_dir():
        return "missing_artifact", f"artifact_root not a directory: {artifact_root}"

    artifacts_root_resolved = artifacts_root.resolve()
    artifact_root_resolved = artifact_root.resolve()
    if (
        artifact_root_resolved != artifacts_root_resolved
        and not artifact_root_resolved.is_relative_to(artifacts_root_resolved)
    ):
        return "missing_artifact", (
            f"artifact_root {artifact_root_resolved} not under "
            f"configured artifacts root {artifacts_root_resolved}"
        )

    try:
        payload = json.loads(row["result_json"])
    except (TypeError, ValueError) as exc:
        return "bad_payload", f"result_json not valid JSON: {exc}"

    rel = payload.get("audio_path_relative")
    sha = payload.get("audio_sha256")
    if not rel or not sha:
        return "bad_payload", (
            "result_json missing 'audio_path_relative' or 'audio_sha256'"
        )

    audio_path = (artifact_root / rel).resolve()
    if not audio_path.is_file():
        return "missing_artifact", f"audio not found: {audio_path}"
    if not audio_path.is_relative_to(artifact_root_resolved):
        return "missing_artifact", f"audio path escapes artifact_root: {audio_path}"

    actual_sha = _sha256_file(audio_path)
    if actual_sha != sha:
        return "sha256_mismatch", (
            f"sha256 mismatch for {audio_path} "
            f"(expected {sha}, got {actual_sha})"
        )

    return "ok", None


def _render_md(report: dict) -> str:
    lines = [
        "# B8.1 — Cache validation report",
        "",
        f"- host: `{report['host']}`",
        f"- generated_at: `{report['generated_at']}`",
        f"- db_path: `{report['db_path']}`",
        f"- artifacts_root: `{report['artifacts_root']}`",
        f"- DEGRADATION_VERSION: `{report['versions']['degradation_version']}`",
        f"- METRICS_VERSION: `{report['versions']['metrics_version']}`",
        f"- DEFAULT_ENHANCER_VERSION: "
        f"`{report['versions']['default_enhancer_version']}`",
        f"- total rows: **{report['total_rows']}**",
        "",
        "## Outcomes",
        "",
        "| outcome | count |",
        "| --- | --- |",
    ]
    for outcome in OUTCOME_ORDER:
        lines.append(f"| {outcome} | {report['outcomes'].get(outcome, 0)} |")
    lines.append("")
    failures = [r for r in report["rows"] if r["outcome"] != "ok"]
    if failures:
        lines.append("## Failures")
        lines.append("")
        lines.append("| cache_key | outcome | detail |")
        lines.append("| --- | --- | --- |")
        for row in failures:
            detail = (row.get("detail") or "").replace("|", "\\|")
            lines.append(
                f"| `{row['cache_key']}` | {row['outcome']} | {detail} |"
            )
        lines.append("")
    else:
        lines.append("All rows validated as `ok`.")
        lines.append("")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    settings = DemoSettings()
    parser = argparse.ArgumentParser(
        description="Validate cache_entries rows against the current versions and on-disk audio."
    )
    parser.add_argument("--db", type=Path, default=settings.demo_db_path)
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=settings.demo_artifacts_dir / "examples",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("reports/demo/b8_1_cache_validation.json"),
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=Path("reports/demo/b8_1_cache_validation.md"),
    )
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--mark-validated", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db_path: Path = args.db
    artifacts_root: Path = args.artifacts_root.resolve()

    if not db_path.is_file():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 1

    rows = persistence.list_cache_entries(db_path)
    outcomes: dict[str, int] = {k: 0 for k in OUTCOME_ORDER}
    row_records: list[dict] = []

    for row in rows:
        outcome, detail = _classify_row(row, artifacts_root)
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        row_records.append(
            {
                "cache_key": row["cache_key"],
                "example_id": row["example_id"],
                "degradation_id": row["degradation_id"],
                "asr_provider": row["asr_provider"],
                "asr_model_version": row["asr_model_version"],
                "enhancer_version": row["enhancer_version"],
                "outcome": outcome,
                "detail": detail,
            }
        )
        if outcome == "ok" and args.mark_validated:
            persistence.mark_cache_entry_validated(db_path, row["cache_key"])

    report = {
        "task": "B8.1",
        "host": socket.gethostname(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "artifacts_root": str(artifacts_root),
        "versions": {
            "degradation_version": versions.DEGRADATION_VERSION,
            "metrics_version": versions.METRICS_VERSION,
            "default_enhancer_version": versions.DEFAULT_ENHANCER_VERSION,
        },
        "total_rows": len(rows),
        "outcomes": outcomes,
        "rows": row_records,
    }

    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(_render_md(report), encoding="utf-8")

    summary = ", ".join(f"{k}={outcomes[k]}" for k in OUTCOME_ORDER)
    print(f"validated {len(rows)} rows ({summary})")

    non_ok = sum(v for k, v in outcomes.items() if k != "ok")
    if args.strict and non_ok > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
