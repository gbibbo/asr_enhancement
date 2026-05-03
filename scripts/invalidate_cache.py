"""Delete cache_entries rows by version / provider / example filters.

Defaults to dry-run. Requires ``--apply`` to actually delete. Refuses to run
without at least one filter. Never touches audio files on disk.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from libs.common.demo_settings import DemoSettings  # noqa: E402
from libs.demo import persistence  # noqa: E402


_FILTER_TO_COLUMN = {
    "by_degradation_version": "degradation_version",
    "by_metrics_version": "metrics_version",
    "by_enhancer_version": "enhancer_version",
    "by_asr_provider": "asr_provider",
    "by_asr_model_version": "asr_model_version",
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    settings = DemoSettings()
    parser = argparse.ArgumentParser(
        description="Delete cache_entries rows matching explicit filters."
    )
    parser.add_argument("--db", type=Path, default=settings.demo_db_path)
    parser.add_argument("--by-degradation-version")
    parser.add_argument("--by-metrics-version")
    parser.add_argument("--by-enhancer-version")
    parser.add_argument("--by-asr-provider")
    parser.add_argument("--by-asr-model-version")
    parser.add_argument(
        "--by-example-id",
        action="append",
        default=[],
        help="Repeatable. Targets cache_entries.example_id.",
    )
    parser.add_argument(
        "--mode",
        choices=["match", "not-match"],
        default="match",
        help="match: delete rows where columns equal filters. "
        "not-match: delete rows where columns differ from filters.",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def _build_where(args: argparse.Namespace) -> tuple[str, tuple]:
    operator = "=" if args.mode == "match" else "!="
    in_keyword = "IN" if args.mode == "match" else "NOT IN"
    clauses: list[str] = []
    params: list = []

    for attr, column in _FILTER_TO_COLUMN.items():
        value = getattr(args, attr)
        if value is not None:
            clauses.append(f"{column} {operator} ?")
            params.append(value)

    if args.by_example_id:
        placeholders = ", ".join("?" for _ in args.by_example_id)
        clauses.append(f"example_id {in_keyword} ({placeholders})")
        params.extend(args.by_example_id)

    return " AND ".join(clauses), tuple(params)


def _has_any_filter(args: argparse.Namespace) -> bool:
    if args.by_example_id:
        return True
    return any(
        getattr(args, attr) is not None for attr in _FILTER_TO_COLUMN
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if not _has_any_filter(args):
        print(
            "Refusing to run: at least one filter is required "
            "(--by-degradation-version, --by-metrics-version, "
            "--by-enhancer-version, --by-asr-provider, "
            "--by-asr-model-version, --by-example-id).",
            file=sys.stderr,
        )
        return 1

    if not args.db.is_file():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    where_sql, params = _build_where(args)

    matched, sample = persistence.delete_cache_entries(
        args.db,
        where_sql=where_sql,
        params=params,
        dry_run=not args.apply,
    )

    if not args.quiet:
        print(f"filters: {where_sql}")
        print(f"params: {params}")
        print(f"mode: {args.mode}")
        print(f"matched: {matched}")
        if sample:
            print("sample cache_keys:")
            for key in sample:
                print(f"  - {key}")

    if args.apply:
        print(f"deleted {matched} rows")
    else:
        print(f"[dry-run] would delete {matched} rows; pass --apply to commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
