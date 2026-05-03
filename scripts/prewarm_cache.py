"""Prewarm the demo SQLite ``cache_entries`` table from the B6.5.1 RP5 baseline.

B8.1 scope:

* Only ``asr_provider=whisper``, ``asr_model_version=tiny.en``,
  ``enhancer_version=bypass``, ``--source reports`` are implemented.
* AssemblyAI prewarm and ``--source run`` are explicitly deferred.
* No live ASR, no network, no usage_ledger writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Allow running both as ``python scripts/prewarm_cache.py`` (host) and
# ``python /app/scripts/prewarm_cache.py`` (container) without packaging.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from libs.common import versions  # noqa: E402
from libs.common.demo_settings import DemoSettings  # noqa: E402
from libs.demo import persistence  # noqa: E402
from libs.demo.cache import build_cache_key  # noqa: E402
from libs.demo.examples import load_examples  # noqa: E402


CLEAN_VARIANT_ID = "clean"
SUPPORTED_PROVIDER = "whisper"
SUPPORTED_MODEL = "tiny.en"
SUPPORTED_ENHANCER = "bypass"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_baseline(baseline_path: Path) -> dict:
    if not baseline_path.is_file():
        raise FileNotFoundError(
            f"Baseline report not found: {baseline_path}"
        )
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def _index_baseline(baseline: dict) -> dict[tuple[str, str], dict]:
    rows = baseline.get("results")
    if not isinstance(rows, list):
        raise ValueError(
            "Baseline report missing 'results' array"
        )
    index: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["example_id"], row["degradation_id"])
        if key in index:
            raise ValueError(
                f"Duplicate baseline record for {key}"
            )
        index[key] = row
    return index


def _planned_pairs(examples) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for example in examples:
        pairs.append((example.example_id, CLEAN_VARIANT_ID))
        for deg_id in example.degradation_ids:
            pairs.append((example.example_id, deg_id))
    return pairs


def _build_result_payload(
    *,
    example_id: str,
    degradation_id: str,
    audio_path_relative: str,
    audio_sha256: str,
    baseline_row: dict,
    source_report: str,
) -> dict:
    return {
        "example_id": example_id,
        "degradation_id": degradation_id,
        "asr_provider": SUPPORTED_PROVIDER,
        "asr_model_version": SUPPORTED_MODEL,
        "enhancer_version": SUPPORTED_ENHANCER,
        "audio_path_relative": audio_path_relative,
        "audio_sha256": audio_sha256,
        "hypothesis": baseline_row["hypothesis"],
        "wer": baseline_row["wer"],
        "word_accuracy": baseline_row["word_accuracy"],
        "latency_seconds": baseline_row.get("latency_seconds"),
        "source_report": source_report,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    settings = DemoSettings()
    parser = argparse.ArgumentParser(
        description=(
            "Prewarm cache_entries from the B6.5.1 RP5 baseline report "
            "for whisper/tiny.en/bypass."
        )
    )
    parser.add_argument(
        "--examples",
        type=Path,
        default=Path("config/demo_examples.json"),
        help="Path to demo_examples.json (default: config/demo_examples.json)",
    )
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=settings.demo_artifacts_dir / "examples",
        help="Absolute path to the artifacts root containing per-example WAVs",
    )
    parser.add_argument(
        "--baseline-report",
        type=Path,
        default=Path("reports/demo/b6_5_1_rp5_results.json"),
        help="Path to the B6.5.1 RP5 baseline JSON report",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=settings.demo_db_path,
        help="Path to the demo SQLite database",
    )
    parser.add_argument(
        "--asr-provider",
        choices=["whisper", "assemblyai"],
        default="whisper",
    )
    parser.add_argument("--asr-model", default=SUPPORTED_MODEL)
    parser.add_argument("--enhancer", default=SUPPORTED_ENHANCER)
    parser.add_argument(
        "--source",
        choices=["reports", "run"],
        default="reports",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def _enforce_b81_scope(args: argparse.Namespace) -> int | None:
    if args.asr_provider == "assemblyai":
        print(
            "AssemblyAI cache prewarm is deferred to a later quota-aware task.",
            file=sys.stderr,
        )
        return 2
    if args.source == "run":
        print(
            "Live ASR prewarm (--source run) is deferred to a later task. "
            "Use --source reports.",
            file=sys.stderr,
        )
        return 2
    if args.enhancer != SUPPORTED_ENHANCER:
        print(
            f"Enhancer {args.enhancer!r} is not available for B8.1 prewarm. "
            "MetricGAN+ is owned by T4.1 in feature/training-datamove1-v1; "
            "use --enhancer bypass.",
            file=sys.stderr,
        )
        return 2
    if args.asr_model != SUPPORTED_MODEL:
        print(
            f"asr_model={args.asr_model!r} is not supported in B8.1 prewarm. "
            f"Use --asr-model {SUPPORTED_MODEL}.",
            file=sys.stderr,
        )
        return 2
    return None


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    rejection_code = _enforce_b81_scope(args)
    if rejection_code is not None:
        return rejection_code

    examples_path: Path = args.examples
    artifacts_root: Path = args.artifacts_root.resolve()
    baseline_path: Path = args.baseline_report
    db_path: Path = args.db

    if not examples_path.is_file():
        print(f"Examples config not found: {examples_path}", file=sys.stderr)
        return 1
    if not artifacts_root.is_dir():
        print(
            f"Artifacts root not found or not a directory: {artifacts_root}",
            file=sys.stderr,
        )
        return 1

    examples = load_examples(examples_path)
    if not examples:
        print(
            f"No examples loaded from {examples_path}; nothing to prewarm.",
            file=sys.stderr,
        )
        return 1

    baseline = _load_baseline(baseline_path)
    baseline_index = _index_baseline(baseline)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    persistence.init_schema(db_path)

    inserted = 0
    updated = 0
    missing_in_report = 0
    sha_mismatch_pairs: list[tuple[str, str]] = []

    pairs = _planned_pairs(examples)
    pending_writes: list[dict] = []

    for example_id, variant_id in pairs:
        baseline_row = baseline_index.get((example_id, variant_id))
        if baseline_row is None:
            missing_in_report += 1
            print(
                f"missing_in_report: ({example_id}, {variant_id}) — skipping",
                file=sys.stderr,
            )
            continue

        audio_path_relative = baseline_row["audio_path_relative"]
        audio_path = (artifacts_root / audio_path_relative).resolve()
        if not audio_path.is_file():
            print(
                f"audio missing on disk for ({example_id}, {variant_id}): "
                f"{audio_path}",
                file=sys.stderr,
            )
            return 1
        if not audio_path.is_relative_to(artifacts_root):
            print(
                f"audio path escapes artifacts_root for "
                f"({example_id}, {variant_id}): {audio_path}",
                file=sys.stderr,
            )
            return 1

        actual_sha = _sha256_file(audio_path)
        if actual_sha != baseline_row["audio_sha256"]:
            sha_mismatch_pairs.append((example_id, variant_id))
            continue

        cache_key = build_cache_key(
            example_id=example_id,
            degradation_id=variant_id,
            asr_provider=SUPPORTED_PROVIDER,
            asr_model_version=SUPPORTED_MODEL,
            enhancer_version=SUPPORTED_ENHANCER,
        )
        payload = _build_result_payload(
            example_id=example_id,
            degradation_id=variant_id,
            audio_path_relative=audio_path_relative,
            audio_sha256=actual_sha,
            baseline_row=baseline_row,
            source_report=str(baseline_path),
        )
        pending_writes.append(
            {
                "cache_key": cache_key,
                "example_id": example_id,
                "degradation_id": variant_id,
                "degradation_version": versions.DEGRADATION_VERSION,
                "asr_provider": SUPPORTED_PROVIDER,
                "asr_model_version": SUPPORTED_MODEL,
                "enhancer_version": SUPPORTED_ENHANCER,
                "metrics_version": versions.METRICS_VERSION,
                "result_json": json.dumps(payload, ensure_ascii=False),
                "artifact_root": str(artifacts_root),
            }
        )

    if sha_mismatch_pairs:
        print(
            "Aborting: audio sha256 differs from baseline report for "
            f"{len(sha_mismatch_pairs)} pair(s); fix B6.5.1 first. "
            f"Pairs: {sha_mismatch_pairs}",
            file=sys.stderr,
        )
        return 1

    if args.dry_run:
        print(
            f"[dry-run] would prewarm {len(pending_writes)} entries "
            f"(missing_in_report={missing_in_report})"
        )
        return 0

    for row in pending_writes:
        action = persistence.upsert_cache_entry(db_path, **row)
        if action == "inserted":
            inserted += 1
        else:
            updated += 1

    print(
        f"prewarmed {inserted + updated} entries "
        f"(inserted={inserted}, updated={updated}, "
        f"missing_in_report={missing_in_report}, "
        f"sha_mismatch=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
