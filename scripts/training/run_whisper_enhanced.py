"""T4.2d: Run Whisper base.en on the MetricGAN+ enhanced manifest.

Runs openai-whisper base.en on every enhanced record produced at T4.2c, computes
per-record WER and Word Accuracy via libs.audio.metrics, aggregates per-family
and macro-over-families, and records a record_micro consistency check (mean of
per-record values across all 13 465 predictions). The macro is the headline.

Compares enhanced macro and per-family results against the T3.2 degraded baseline
(primary) and the T3.1 clean baseline (secondary, macro only). Assigns a tier:
  strong            macro WA delta vs degraded >= +0.05
  partial           0 < macro WA delta vs degraded < +0.05
  null_or_negative  macro WA delta vs degraded <= 0

This script does not run enhancement and does not modify the enhanced manifest
or enhanced audio. Reserved demo IDs are read at runtime from
configs/training/reserved_public_demo_examples.yaml; no hard-coded copy is kept
in this script.

Usage:
  python3 -s scripts/training/run_whisper_enhanced.py \\
    --enhanced-manifest          $TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl \\
    --degraded-source-manifest   $TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl \\
    --exclusion-config           configs/training/public_examples_excluded.yaml \\
    --dataset-version-config     configs/training/dataset_version.yaml \\
    --reserved-demo-config       configs/training/reserved_public_demo_examples.yaml \\
    --clean-baseline-report      reports/training/baseline_clean_wer.md \\
    --degraded-baseline-report   reports/training/baseline_degraded_wer.md \\
    --model                      base.en \\
    --whisper-cache              $TRAIN_ROOT/cache/whisper \\
    --out-dir                    $TRAIN_ROOT/runs/t4_2d_whisper_enhanced_<JID> \\
    [--max-records-per-family 5] \\
    [--summary-md reports/training/metricgan_plus_wer.md]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.metadata
import json
import math
import os
import pathlib
import sys
import time


EXPECTED_DATASET_VERSION = "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8"
EXPECTED_DEGRADATION_VERSION = "degradation_v1"
EXPECTED_ENHANCER_VERSION = "metricgan_plus_pretrained"
EXPECTED_ENHANCEMENT_VERSION = "enhancement_v1"
EXPECTED_MANIFEST_RECORDS = 13465
EXPECTED_ENHANCED_MANIFEST_SHA256 = (
    "544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9"
)
EXPECTED_DEGRADED_SOURCE_MANIFEST_SHA256 = (
    "c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c"
)

# Reference metrics from T3.1 clean and T3.2 degraded reports (frozen).
EXPECTED_CLEAN_BASELINE_WER = 0.0645
EXPECTED_CLEAN_BASELINE_WA = 0.9361

EXPECTED_DEGRADED_MACRO_WER = 0.1843
EXPECTED_DEGRADED_MACRO_WA = 0.8213
EXPECTED_DEGRADED_PER_FAMILY = {
    "broadband_hiss":   {"wer": 0.1271, "wa": 0.8742},
    "cafe_background":  {"wer": 0.1632, "wa": 0.8390},
    "far_field_room":   {"wer": 0.1659, "wa": 0.8356},
    "muffled":          {"wer": 0.3863, "wa": 0.6361},
    "phone_call":       {"wer": 0.0789, "wa": 0.9217},
}

EXPECTED_FAMILIES = frozenset(EXPECTED_DEGRADED_PER_FAMILY.keys())
EXPECTED_SR = 16000
EXPECTED_PER_FAMILY_COUNT = 2693  # 13465 / 5

TIER_STRONG = "strong"
TIER_PARTIAL = "partial"
TIER_NULL_OR_NEGATIVE = "null_or_negative"
TIER_STRONG_THRESHOLD = 0.05


def _git_rev_parse_head() -> str:
    val = os.environ.get("GIT_COMMIT_AT_RUN", "")
    return val or "unknown"


def _git_status_short() -> str:
    val = os.environ.get("GIT_STATUS_SHORT_AT_RUN", None)
    return "" if val is None else val


def _whisper_version() -> str:
    try:
        import whisper
        return getattr(whisper, "__version__", None) or importlib.metadata.version("openai-whisper")
    except Exception:
        return "unknown"


def _sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def _load_reserved_ids(reserved_config: pathlib.Path) -> set:
    import yaml
    if not reserved_config.exists():
        raise FileNotFoundError(f"reserved demo examples config not found: {reserved_config}")
    cfg = yaml.safe_load(reserved_config.read_text())
    if not isinstance(cfg, dict):
        raise ValueError(f"reserved config not a mapping: {reserved_config}")
    examples = cfg.get("examples")
    if not isinstance(examples, list) or len(examples) == 0:
        raise ValueError(f"reserved config has no 'examples' list or list is empty: {reserved_config}")
    ids = set()
    for entry in examples:
        if not isinstance(entry, dict) or "utterance_id" not in entry:
            raise ValueError(f"reserved config entry missing utterance_id: {entry!r}")
        ids.add(entry["utterance_id"])
    if not ids:
        raise ValueError(f"reserved config produced empty utterance_id set: {reserved_config}")
    return ids


def _validate_clean_baseline_report(path: pathlib.Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"clean baseline report not found: {path}")
    text = path.read_text(encoding="utf-8")
    needle_wer = f"| Mean WER | {EXPECTED_CLEAN_BASELINE_WER:.4f} |"
    needle_wa = f"| Mean Word Accuracy | {EXPECTED_CLEAN_BASELINE_WA:.4f} |"
    if needle_wer not in text or needle_wa not in text:
        raise ValueError(
            f"clean baseline reference drift: expected '{needle_wer}' and '{needle_wa}' in {path}"
        )


def _validate_degraded_baseline_report(path: pathlib.Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"degraded baseline report not found: {path}")
    text = path.read_text(encoding="utf-8")
    needle_wer = f"| Mean per-record WER | {EXPECTED_DEGRADED_MACRO_WER:.4f} |"
    needle_wa = f"| Mean per-record Word Accuracy | {EXPECTED_DEGRADED_MACRO_WA:.4f} |"
    if needle_wer not in text or needle_wa not in text:
        raise ValueError(
            f"degraded baseline macro drift: expected '{needle_wer}' and '{needle_wa}' in {path}"
        )
    for fam, ref in EXPECTED_DEGRADED_PER_FAMILY.items():
        fam_needle = (
            f"| {fam} | {EXPECTED_PER_FAMILY_COUNT} | "
            f"{ref['wer']:.4f} | {ref['wa']:.4f} |"
        )
        if fam_needle not in text:
            raise ValueError(
                f"degraded baseline per-family drift for {fam}: expected '{fam_needle}' in {path}"
            )


def _classify_tier(delta_macro_wa_vs_degraded: float) -> str:
    if delta_macro_wa_vs_degraded >= TIER_STRONG_THRESHOLD:
        return TIER_STRONG
    if delta_macro_wa_vs_degraded > 0.0:
        return TIER_PARTIAL
    return TIER_NULL_OR_NEGATIVE


def main() -> int:
    parser = argparse.ArgumentParser(description="T4.2d Whisper-on-enhanced evaluation")
    parser.add_argument("--enhanced-manifest", required=True)
    parser.add_argument("--degraded-source-manifest", required=True)
    parser.add_argument("--exclusion-config", required=True)
    parser.add_argument("--dataset-version-config", required=True)
    parser.add_argument("--reserved-demo-config", required=True)
    parser.add_argument("--clean-baseline-report", required=True)
    parser.add_argument("--degraded-baseline-report", required=True)
    parser.add_argument("--model", default="base.en")
    parser.add_argument("--whisper-cache", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument(
        "--max-records-per-family",
        type=int,
        default=None,
        help="If set, restrict each family to its first N utterance_ids (sorted). "
             "Smoke mode uses 5; full mode omits this flag.",
    )
    parser.add_argument("--summary-md", default=None)
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = out_dir / "predictions.jsonl"
    failures_path = out_dir / "failures.jsonl"
    metrics_summary_path = out_dir / "metrics_summary.json"
    config_snapshot_path = out_dir / "config_snapshot.json"
    run_summary_md_path = out_dir / "run_summary.md"

    if predictions_path.exists():
        print(f"BLOCKER: stale predictions.jsonl found at {predictions_path} — remove before rerunning")
        return 1

    slurm_job_id = os.environ.get("SLURM_JOB_ID", "local")
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"
    git_commit = _git_rev_parse_head()
    git_status = _git_status_short()

    # ------------------------------------------------------------------
    # PRE-FLIGHT CHECKS
    # ------------------------------------------------------------------
    import yaml

    excl_path = pathlib.Path(args.exclusion_config)
    if not excl_path.exists():
        print(f"BLOCKER: exclusion config not found: {excl_path}")
        return 1
    excl_cfg = yaml.safe_load(excl_path.read_text())
    if excl_cfg.get("status") != "complete":
        print(f"BLOCKER: public_examples_excluded.yaml status is {excl_cfg.get('status')!r}, expected 'complete'")
        return 1

    dv_path = pathlib.Path(args.dataset_version_config)
    if not dv_path.exists():
        print(f"BLOCKER: dataset version config not found: {dv_path}")
        return 1
    dv_cfg = yaml.safe_load(dv_path.read_text())
    if dv_cfg.get("dataset_version") != EXPECTED_DATASET_VERSION:
        print(
            f"BLOCKER: dataset_version mismatch: got {dv_cfg.get('dataset_version')!r}, "
            f"expected {EXPECTED_DATASET_VERSION!r}"
        )
        return 1

    reserved_path = pathlib.Path(args.reserved_demo_config)
    try:
        reserved_ids = _load_reserved_ids(reserved_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"BLOCKER: reserved demo examples config: {exc}")
        return 1

    clean_report_path = pathlib.Path(args.clean_baseline_report)
    try:
        _validate_clean_baseline_report(clean_report_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"BLOCKER: clean baseline reference drift: {exc}")
        return 1

    degraded_report_path = pathlib.Path(args.degraded_baseline_report)
    try:
        _validate_degraded_baseline_report(degraded_report_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"BLOCKER: degraded baseline reference drift: {exc}")
        return 1

    degraded_source_manifest_path = pathlib.Path(args.degraded_source_manifest)
    if not degraded_source_manifest_path.exists():
        print(f"BLOCKER: degraded source manifest not found: {degraded_source_manifest_path}")
        return 1
    degraded_source_sha = _sha256_of_bytes(degraded_source_manifest_path.read_bytes())
    if degraded_source_sha != EXPECTED_DEGRADED_SOURCE_MANIFEST_SHA256:
        print(
            f"BLOCKER: degraded source manifest SHA changed: got {degraded_source_sha}, "
            f"expected {EXPECTED_DEGRADED_SOURCE_MANIFEST_SHA256}"
        )
        return 1

    enhanced_manifest_path = pathlib.Path(args.enhanced_manifest)
    if not enhanced_manifest_path.exists():
        print(f"BLOCKER: enhanced manifest not found: {enhanced_manifest_path}")
        return 1
    enhanced_manifest_bytes = enhanced_manifest_path.read_bytes()
    enhanced_manifest_sha = _sha256_of_bytes(enhanced_manifest_bytes)
    if enhanced_manifest_sha != EXPECTED_ENHANCED_MANIFEST_SHA256:
        print(
            f"BLOCKER: enhanced manifest SHA mismatch: got {enhanced_manifest_sha}, "
            f"expected {EXPECTED_ENHANCED_MANIFEST_SHA256}"
        )
        return 1
    lines = enhanced_manifest_bytes.decode("utf-8").splitlines()
    if len(lines) != EXPECTED_MANIFEST_RECORDS:
        print(
            f"BLOCKER: enhanced manifest line count is {len(lines)}, "
            f"expected {EXPECTED_MANIFEST_RECORDS}"
        )
        return 1

    records: list[dict] = []
    per_family_counts: dict[str, int] = {f: 0 for f in EXPECTED_FAMILIES}
    for lineno, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"BLOCKER: JSON parse error at manifest line {lineno}: {exc}")
            return 1
        uid = rec.get("utterance_id", "")
        fam = rec.get("family", "")
        if uid in reserved_ids:
            print(f"BLOCKER: reserved demo example present in enhanced manifest: {uid}")
            return 1
        if fam not in EXPECTED_FAMILIES:
            print(f"BLOCKER: unexpected family {fam!r} at line {lineno} (uid={uid!r})")
            return 1
        if rec.get("dataset_version") != EXPECTED_DATASET_VERSION:
            print(
                f"BLOCKER: dataset_version mismatch at line {lineno}: "
                f"got {rec.get('dataset_version')!r}, expected {EXPECTED_DATASET_VERSION!r}"
            )
            return 1
        if rec.get("degradation_version") != EXPECTED_DEGRADATION_VERSION:
            print(
                f"BLOCKER: degradation_version mismatch at line {lineno}: "
                f"got {rec.get('degradation_version')!r}, expected {EXPECTED_DEGRADATION_VERSION!r}"
            )
            return 1
        if rec.get("enhancer_version") != EXPECTED_ENHANCER_VERSION:
            print(
                f"BLOCKER: enhancer_version mismatch at line {lineno}: "
                f"got {rec.get('enhancer_version')!r}, expected {EXPECTED_ENHANCER_VERSION!r}"
            )
            return 1
        if rec.get("enhancement_version") != EXPECTED_ENHANCEMENT_VERSION:
            print(
                f"BLOCKER: enhancement_version mismatch at line {lineno}: "
                f"got {rec.get('enhancement_version')!r}, expected {EXPECTED_ENHANCEMENT_VERSION!r}"
            )
            return 1
        if rec.get("enhanced") is not True:
            print(f"BLOCKER: enhanced != True at line {lineno} (uid={uid!r})")
            return 1
        if rec.get("enhancement_fallback") is not False:
            print(f"BLOCKER: enhancement_fallback != False at line {lineno} (uid={uid!r})")
            return 1
        if rec.get("sample_rate") != EXPECTED_SR:
            print(
                f"BLOCKER: sample_rate mismatch at line {lineno}: "
                f"got {rec.get('sample_rate')!r}, expected {EXPECTED_SR}"
            )
            return 1
        if not rec.get("enhanced_audio_path"):
            print(f"BLOCKER: missing enhanced_audio_path at line {lineno} (uid={uid!r})")
            return 1
        per_family_counts[fam] += 1
        records.append(rec)

    for fam in EXPECTED_FAMILIES:
        if per_family_counts[fam] != EXPECTED_PER_FAMILY_COUNT:
            print(
                f"BLOCKER: per-family count mismatch for {fam}: "
                f"{per_family_counts[fam]} != {EXPECTED_PER_FAMILY_COUNT}"
            )
            return 1

    for lineno, rec in enumerate(records, 1):
        p = pathlib.Path(rec["enhanced_audio_path"])
        if not p.exists():
            print(f"BLOCKER: missing enhanced_audio_path at line {lineno}: {p}")
            return 1

    try:
        from libs.common.versions import DEGRADATION_VERSION as LIB_DEGRADATION_VERSION
    except ImportError as exc:
        print(f"BLOCKER: cannot import libs.common.versions: {exc}")
        return 1
    if LIB_DEGRADATION_VERSION != EXPECTED_DEGRADATION_VERSION:
        print(
            f"BLOCKER: DEGRADATION_VERSION drift: libs.common.versions={LIB_DEGRADATION_VERSION!r}, "
            f"expected {EXPECTED_DEGRADATION_VERSION!r}"
        )
        return 1
    try:
        from libs.audio.metrics import (
            METRICS_VERSION,
            normalize_text,
            word_error_rate,
            word_accuracy,
        )
    except ImportError as exc:
        print(f"BLOCKER: cannot import libs.audio.metrics: {exc}")
        return 1
    if METRICS_VERSION != "metrics_v1":
        print(f"BLOCKER: METRICS_VERSION drift: got {METRICS_VERSION!r}, expected 'metrics_v1'")
        return 1

    try:
        import whisper  # noqa: F401
        whisper_ver = _whisper_version()
    except ImportError as exc:
        print(f"BLOCKER: cannot import whisper: {exc}")
        return 1

    print("PRE-FLIGHT OK")
    print(f"  enhanced manifest records:       {len(records)}")
    print(f"  enhanced manifest sha256:        {enhanced_manifest_sha}")
    print(f"  degraded source manifest sha256: {degraded_source_sha}")
    print(f"  per-family counts:               {per_family_counts}")
    print(f"  dataset_version:                 {EXPECTED_DATASET_VERSION}")
    print(f"  degradation_version:             {EXPECTED_DEGRADATION_VERSION}")
    print(f"  enhancer_version:                {EXPECTED_ENHANCER_VERSION}")
    print(f"  enhancement_version:             {EXPECTED_ENHANCEMENT_VERSION}")
    print(f"  exclusion status:                complete")
    print(f"  METRICS_VERSION:                 {METRICS_VERSION}")
    print(f"  whisper version:                 {whisper_ver}")
    print(f"  model:                           {args.model}")
    print(f"  whisper cache:                   {args.whisper_cache}")
    print(f"  reserved IDs (count):            {len(reserved_ids)} (from {reserved_path})")
    print(f"  out_dir:                         {out_dir}")
    print(f"  max_records_per_family:          {args.max_records_per_family}")
    print(f"  git_commit_at_run:               {git_commit}")
    print(f"  git_status_at_run:               {git_status!r}")
    print(f"  slurm_job_id:                    {slurm_job_id}")

    sorted_records = sorted(records, key=lambda r: (r["utterance_id"], r["family"]))
    if args.max_records_per_family is not None:
        n = args.max_records_per_family
        selected_uids: list[str] = []
        seen = set()
        for r in sorted_records:
            uid = r["utterance_id"]
            if uid not in seen:
                seen.add(uid)
                selected_uids.append(uid)
                if len(selected_uids) == n:
                    break
        selected_uid_set = set(selected_uids)
        records_to_process = [r for r in sorted_records if r["utterance_id"] in selected_uid_set]
        expected_count = n * len(EXPECTED_FAMILIES)
        if len(records_to_process) != expected_count:
            print(
                f"BLOCKER: smoke selection produced {len(records_to_process)} records, "
                f"expected {expected_count}"
            )
            return 1
    else:
        records_to_process = sorted_records

    print(f"\nProcessing {len(records_to_process)} records ...")

    _write_json(
        config_snapshot_path,
        {
            "enhanced_manifest": str(enhanced_manifest_path),
            "degraded_source_manifest": str(degraded_source_manifest_path),
            "exclusion_config": str(excl_path),
            "dataset_version_config": str(dv_path),
            "reserved_demo_config": str(reserved_path),
            "clean_baseline_report": str(clean_report_path),
            "degraded_baseline_report": str(degraded_report_path),
            "model": args.model,
            "whisper_cache": args.whisper_cache,
            "out_dir": str(out_dir),
            "max_records_per_family": args.max_records_per_family,
            "summary_md": args.summary_md,
            "expected_dataset_version": EXPECTED_DATASET_VERSION,
            "expected_degradation_version": EXPECTED_DEGRADATION_VERSION,
            "expected_enhancer_version": EXPECTED_ENHANCER_VERSION,
            "expected_enhancement_version": EXPECTED_ENHANCEMENT_VERSION,
            "expected_enhanced_manifest_sha256": EXPECTED_ENHANCED_MANIFEST_SHA256,
            "expected_degraded_source_manifest_sha256": EXPECTED_DEGRADED_SOURCE_MANIFEST_SHA256,
            "expected_clean_baseline_per_record_wer": EXPECTED_CLEAN_BASELINE_WER,
            "expected_clean_baseline_per_record_word_accuracy": EXPECTED_CLEAN_BASELINE_WA,
            "expected_degraded_macro_per_record_wer": EXPECTED_DEGRADED_MACRO_WER,
            "expected_degraded_macro_per_record_word_accuracy": EXPECTED_DEGRADED_MACRO_WA,
            "expected_degraded_per_family": EXPECTED_DEGRADED_PER_FAMILY,
            "expected_families": sorted(EXPECTED_FAMILIES),
            "reserved_ids_count": len(reserved_ids),
            "enhanced_manifest_sha256_observed": enhanced_manifest_sha,
            "degraded_source_manifest_sha256_observed": degraded_source_sha,
            "manifest_records_observed": len(records),
            "per_family_counts_observed": per_family_counts,
            "records_to_process": len(records_to_process),
            "slurm_job_id": slurm_job_id,
            "git_commit_at_run": git_commit,
            "timestamp_utc": timestamp_utc,
            "metrics_version": METRICS_VERSION,
            "whisper_model": args.model,
            "whisper_version": whisper_ver,
        },
    )

    whisper_cache = pathlib.Path(args.whisper_cache)
    whisper_cache.mkdir(parents=True, exist_ok=True)
    print(f"\nLoading whisper model '{args.model}' from cache {whisper_cache} ...")
    model_load_start = time.monotonic()
    model = whisper.load_model(args.model, download_root=str(whisper_cache))
    print(f"Model loaded in {time.monotonic() - model_load_start:.1f}s")

    failure_count = 0
    per_family_wer: dict[str, list[float]] = {f: [] for f in EXPECTED_FAMILIES}
    per_family_wa: dict[str, list[float]] = {f: [] for f in EXPECTED_FAMILIES}
    all_wer: list[float] = []
    all_wa: list[float] = []
    predictions_uids_seen: set = set()

    inference_start = time.monotonic()
    with predictions_path.open("w", encoding="utf-8") as pred_fh, failures_path.open(
        "w", encoding="utf-8"
    ) as fail_fh:
        for i, rec in enumerate(records_to_process):
            uid = rec["utterance_id"]
            family = rec["family"]
            enhanced_audio_path = rec["enhanced_audio_path"]
            enhanced_audio_sha256 = rec.get("enhanced_audio_sha256", "")
            degraded_audio_path = rec.get("degraded_audio_path", "")
            clean_audio_path = rec.get("clean_audio_path", "")
            reference = rec.get("transcript", "")
            duration_s = rec.get("duration_seconds", 0.0)

            t_start = time.monotonic()
            try:
                result = model.transcribe(
                    str(enhanced_audio_path), language="en", fp16=False, verbose=False
                )
                hypothesis = result["text"]
                wer = word_error_rate(reference, hypothesis)
                wa = word_accuracy(wer)
                ref_norm = normalize_text(reference)
                hyp_norm = normalize_text(hypothesis)
                processing_time = time.monotonic() - t_start

                entry = {
                    "utterance_id": uid,
                    "family": family,
                    "split": rec.get("split", ""),
                    "speaker_id": rec.get("speaker_id", ""),
                    "duration_seconds": duration_s,
                    "clean_audio_path": clean_audio_path,
                    "degraded_audio_path": degraded_audio_path,
                    "enhanced_audio_path": enhanced_audio_path,
                    "enhanced_audio_sha256": enhanced_audio_sha256,
                    "reference_normalized": ref_norm,
                    "hypothesis_normalized": hyp_norm,
                    "wer": wer,
                    "word_accuracy": wa,
                    "processing_time_s": round(processing_time, 3),
                    "whisper_model": args.model,
                    "whisper_version": whisper_ver,
                    "metrics_version": METRICS_VERSION,
                    "dataset_version": EXPECTED_DATASET_VERSION,
                    "degradation_version": EXPECTED_DEGRADATION_VERSION,
                    "enhancer_version": EXPECTED_ENHANCER_VERSION,
                    "enhancement_version": EXPECTED_ENHANCEMENT_VERSION,
                }
                per_family_wer[family].append(wer)
                per_family_wa[family].append(wa)
                all_wer.append(wer)
                all_wa.append(wa)
                predictions_uids_seen.add(uid)
                pred_fh.write(json.dumps(entry) + "\n")
                pred_fh.flush()
            except Exception as exc:
                failure_count += 1
                fail_fh.write(
                    json.dumps(
                        {
                            "utterance_id": uid,
                            "family": family,
                            "enhanced_audio_path": enhanced_audio_path,
                            "stage": "whisper_or_metric",
                            "error": str(exc),
                        }
                    )
                    + "\n"
                )
                fail_fh.flush()

            if (i + 1) % 100 == 0 or (i + 1) == len(records_to_process):
                elapsed = time.monotonic() - inference_start
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(
                    f"  [{i + 1}/{len(records_to_process)}]  failures={failure_count}"
                    f"  rate={rate:.2f} rec/s  elapsed={elapsed:.0f}s"
                )

    if failure_count > 0:
        print(f"\nT4.2d FAILED: failure_count={failure_count} of {len(records_to_process)}")
        print(f"predictions.jsonl preserved at: {predictions_path}")
        print(f"failures.jsonl preserved at:    {failures_path}")
        return 1

    if reserved_ids & predictions_uids_seen:
        print(
            f"BLOCKER: reserved demo IDs present in predictions: "
            f"{sorted(reserved_ids & predictions_uids_seen)}"
        )
        return 1

    per_family_processed = {f: len(per_family_wer[f]) for f in EXPECTED_FAMILIES}
    if args.max_records_per_family is None:
        for f in EXPECTED_FAMILIES:
            if per_family_processed[f] != EXPECTED_PER_FAMILY_COUNT:
                print(
                    f"BLOCKER: per-family processed count for {f} is {per_family_processed[f]}, "
                    f"expected {EXPECTED_PER_FAMILY_COUNT}"
                )
                return 1
    else:
        for f in EXPECTED_FAMILIES:
            if per_family_processed[f] != args.max_records_per_family:
                print(
                    f"BLOCKER: per-family processed count for {f} is {per_family_processed[f]}, "
                    f"expected {args.max_records_per_family}"
                )
                return 1

    post_enhanced_sha = _sha256_of_bytes(enhanced_manifest_path.read_bytes())
    if post_enhanced_sha != EXPECTED_ENHANCED_MANIFEST_SHA256:
        print(f"BLOCKER: enhanced manifest SHA changed during run: {post_enhanced_sha}")
        return 1
    post_degraded_source_sha = _sha256_of_bytes(degraded_source_manifest_path.read_bytes())
    if post_degraded_source_sha != EXPECTED_DEGRADED_SOURCE_MANIFEST_SHA256:
        print(f"BLOCKER: degraded source manifest SHA changed during run: {post_degraded_source_sha}")
        return 1

    per_family_summary: dict[str, dict] = {}
    for fam in sorted(EXPECTED_FAMILIES):
        wers = per_family_wer[fam]
        was = per_family_wa[fam]
        n = len(wers)
        mean_wer = sum(wers) / n
        mean_wa = sum(was) / n
        per_family_summary[fam] = {
            "count": n,
            "mean_per_record_wer": mean_wer,
            "mean_per_record_word_accuracy": mean_wa,
            "min_wer": min(wers),
            "max_wer": max(wers),
            "std_wer": (
                math.sqrt(sum((x - mean_wer) ** 2 for x in wers) / n) if n > 0 else 0.0
            ),
        }

    macro_wer = sum(per_family_summary[f]["mean_per_record_wer"] for f in EXPECTED_FAMILIES) / len(EXPECTED_FAMILIES)
    macro_wa = sum(per_family_summary[f]["mean_per_record_word_accuracy"] for f in EXPECTED_FAMILIES) / len(EXPECTED_FAMILIES)

    record_micro_wer = sum(all_wer) / len(all_wer)
    record_micro_wa = sum(all_wa) / len(all_wa)

    macro_record_micro_equivalent = (
        abs(macro_wer - record_micro_wer) < 1e-9 and abs(macro_wa - record_micro_wa) < 1e-9
    )
    if not macro_record_micro_equivalent:
        print(
            f"BLOCKER: macro vs record_micro mismatch: "
            f"macro_wer={macro_wer} record_micro_wer={record_micro_wer} "
            f"macro_wa={macro_wa} record_micro_wa={record_micro_wa}"
        )
        return 1

    delta_macro_wer_vs_clean = macro_wer - EXPECTED_CLEAN_BASELINE_WER
    delta_macro_wa_vs_clean = macro_wa - EXPECTED_CLEAN_BASELINE_WA
    delta_macro_wer_vs_degraded = macro_wer - EXPECTED_DEGRADED_MACRO_WER
    delta_macro_wa_vs_degraded = macro_wa - EXPECTED_DEGRADED_MACRO_WA

    per_family_deltas_vs_degraded = {
        f: {
            "delta_per_record_wer": (
                per_family_summary[f]["mean_per_record_wer"]
                - EXPECTED_DEGRADED_PER_FAMILY[f]["wer"]
            ),
            "delta_per_record_word_accuracy": (
                per_family_summary[f]["mean_per_record_word_accuracy"]
                - EXPECTED_DEGRADED_PER_FAMILY[f]["wa"]
            ),
        }
        for f in EXPECTED_FAMILIES
    }
    per_family_deltas_vs_clean = {
        f: {
            "delta_per_record_wer": (
                per_family_summary[f]["mean_per_record_wer"] - EXPECTED_CLEAN_BASELINE_WER
            ),
            "delta_per_record_word_accuracy": (
                per_family_summary[f]["mean_per_record_word_accuracy"]
                - EXPECTED_CLEAN_BASELINE_WA
            ),
        }
        for f in EXPECTED_FAMILIES
    }

    tier = _classify_tier(delta_macro_wa_vs_degraded)

    summary = {
        "task": "T4.2d",
        "success": True,
        "mode": "smoke" if args.max_records_per_family is not None else "full",
        "timestamp_utc": timestamp_utc,
        "total_manifest_records": len(records),
        "processed_records": len(records_to_process),
        "failure_count": 0,
        "per_family": per_family_summary,
        "per_family_processed_counts": per_family_processed,
        "overall_macro_per_record_wer": macro_wer,
        "overall_macro_per_record_word_accuracy": macro_wa,
        "record_micro_wer": record_micro_wer,
        "record_micro_word_accuracy": record_micro_wa,
        "macro_record_micro_equivalent": macro_record_micro_equivalent,
        "abs_macro_record_micro_wer_diff": abs(macro_wer - record_micro_wer),
        "abs_macro_record_micro_wa_diff": abs(macro_wa - record_micro_wa),
        "clean_baseline_per_record_wer": EXPECTED_CLEAN_BASELINE_WER,
        "clean_baseline_per_record_word_accuracy": EXPECTED_CLEAN_BASELINE_WA,
        "degraded_baseline_macro_per_record_wer": EXPECTED_DEGRADED_MACRO_WER,
        "degraded_baseline_macro_per_record_word_accuracy": EXPECTED_DEGRADED_MACRO_WA,
        "degraded_baseline_per_family": EXPECTED_DEGRADED_PER_FAMILY,
        "delta_macro_per_record_wer_vs_clean": delta_macro_wer_vs_clean,
        "delta_macro_per_record_word_accuracy_vs_clean": delta_macro_wa_vs_clean,
        "delta_macro_per_record_wer_vs_degraded": delta_macro_wer_vs_degraded,
        "delta_macro_per_record_word_accuracy_vs_degraded": delta_macro_wa_vs_degraded,
        "per_family_deltas_vs_degraded": per_family_deltas_vs_degraded,
        "per_family_deltas_vs_clean": per_family_deltas_vs_clean,
        "tier_classification": tier,
        "tier_strong_threshold": TIER_STRONG_THRESHOLD,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "degradation_version": EXPECTED_DEGRADATION_VERSION,
        "enhancer_version": EXPECTED_ENHANCER_VERSION,
        "enhancement_version": EXPECTED_ENHANCEMENT_VERSION,
        "metrics_version": METRICS_VERSION,
        "whisper_model": args.model,
        "whisper_version": whisper_ver,
        "enhanced_manifest_path": str(enhanced_manifest_path),
        "degraded_source_manifest_path": str(degraded_source_manifest_path),
        "enhanced_manifest_sha256": enhanced_manifest_sha,
        "degraded_source_manifest_sha256": degraded_source_sha,
        "enhanced_manifest_sha256_unchanged": True,
        "degraded_source_manifest_sha256_unchanged": True,
        "reserved_demo_config_path": str(reserved_path),
        "reserved_demo_ids_count": len(reserved_ids),
        "reserved_demo_ids_absent_from_manifest": True,
        "reserved_demo_ids_absent_from_predictions": True,
        "git_commit_at_run": git_commit,
        "git_status_short_at_run": git_status,
        "result_commit": "PENDING_RESULT_COMMIT",
        "slurm_job_id": slurm_job_id,
    }
    _write_json(metrics_summary_path, summary)

    pf_table_lines = [
        "| Family | Count | Mean per-record WER | Mean per-record Word Accuracy "
        "| Δ WER vs degraded | Δ WA vs degraded | Δ WER vs clean | Δ WA vs clean |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for fam in sorted(EXPECTED_FAMILIES):
        s = per_family_summary[fam]
        d_deg = per_family_deltas_vs_degraded[fam]
        d_cln = per_family_deltas_vs_clean[fam]
        pf_table_lines.append(
            f"| {fam} | {s['count']} | {s['mean_per_record_wer']:.4f} | "
            f"{s['mean_per_record_word_accuracy']:.4f} | "
            f"{d_deg['delta_per_record_wer']:+.4f} | {d_deg['delta_per_record_word_accuracy']:+.4f} | "
            f"{d_cln['delta_per_record_wer']:+.4f} | {d_cln['delta_per_record_word_accuracy']:+.4f} |"
        )
    pf_table = "\n".join(pf_table_lines)

    deg_ref_table_lines = [
        "| Family | Count | Mean per-record WER | Mean per-record Word Accuracy |",
        "|---|---|---|---|",
    ]
    for fam in sorted(EXPECTED_FAMILIES):
        ref = EXPECTED_DEGRADED_PER_FAMILY[fam]
        deg_ref_table_lines.append(
            f"| {fam} | {EXPECTED_PER_FAMILY_COUNT} | {ref['wer']:.4f} | {ref['wa']:.4f} |"
        )
    deg_ref_table = "\n".join(deg_ref_table_lines)

    mode_str = summary["mode"]
    run_md = (
        f"# T4.2d Run Summary ({mode_str})\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Dataset version | `{EXPECTED_DATASET_VERSION}` |\n"
        f"| Degradation version | `{EXPECTED_DEGRADATION_VERSION}` |\n"
        f"| Enhancer version | `{EXPECTED_ENHANCER_VERSION}` |\n"
        f"| Enhancement version | `{EXPECTED_ENHANCEMENT_VERSION}` |\n"
        f"| Enhanced manifest SHA-256 | `{enhanced_manifest_sha}` |\n"
        f"| Degraded source manifest SHA-256 | `{degraded_source_sha}` |\n"
        f"| Manifest records | {len(records)} |\n"
        f"| Processed records | {len(records_to_process)} |\n"
        f"| Failure count | 0 |\n"
        f"| Whisper model | `{args.model}` (openai-whisper {whisper_ver}) |\n"
        f"| Metrics version | `{METRICS_VERSION}` |\n"
        f"| Slurm job ID | `{slurm_job_id}` |\n"
        f"| Git commit at run | `{git_commit}` |\n"
        f"| Result commit | `PENDING_RESULT_COMMIT` |\n"
        f"| Tier classification | `{tier}` |\n"
        f"| Timestamp (UTC) | `{timestamp_utc}` |\n\n"
        f"## Per-family results\n\n"
        f"{pf_table}\n\n"
        f"## Overall — macro over families (headline)\n\n"
        f"| Metric | Value | Δ vs degraded | Δ vs clean |\n|---|---|---|---|\n"
        f"| Mean per-record WER | {macro_wer:.4f} | {delta_macro_wer_vs_degraded:+.4f} | {delta_macro_wer_vs_clean:+.4f} |\n"
        f"| Mean per-record Word Accuracy | {macro_wa:.4f} | {delta_macro_wa_vs_degraded:+.4f} | {delta_macro_wa_vs_clean:+.4f} |\n\n"
        f"## Consistency check — record_micro\n\n"
        f"| Metric | Value | abs(macro − record_micro) |\n|---|---|---|\n"
        f"| Mean per-record WER | {record_micro_wer:.4f} | {abs(macro_wer - record_micro_wer):.2e} |\n"
        f"| Mean per-record Word Accuracy | {record_micro_wa:.4f} | {abs(macro_wa - record_micro_wa):.2e} |\n"
    )
    run_summary_md_path.write_text(run_md, encoding="utf-8")

    if args.summary_md:
        summary_md_path = pathlib.Path(args.summary_md)
        summary_md_path.parent.mkdir(parents=True, exist_ok=True)
        body = (
            f"# T4.2d MetricGAN+ Pretrained — Whisper Evaluation\n\n"
            f"Status: complete\n\n"
            f"Mode: {mode_str}\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Dataset version | `{EXPECTED_DATASET_VERSION}` |\n"
            f"| Degradation version | `{EXPECTED_DEGRADATION_VERSION}` |\n"
            f"| Enhancer version | `{EXPECTED_ENHANCER_VERSION}` |\n"
            f"| Enhancement version | `{EXPECTED_ENHANCEMENT_VERSION}` |\n"
            f"| Enhanced manifest SHA-256 | `{enhanced_manifest_sha}` |\n"
            f"| Degraded source manifest SHA-256 | `{degraded_source_sha}` |\n"
            f"| Manifest records | {len(records)} |\n"
            f"| Processed records | {len(records_to_process)} |\n"
            f"| Failure count | 0 |\n"
            f"| Whisper model | `{args.model}` (openai-whisper {whisper_ver}) |\n"
            f"| Metrics version | `{METRICS_VERSION}` |\n"
            f"| Code commit at run | `{git_commit}` |\n"
            f"| Result commit | `PENDING_RESULT_COMMIT` |\n"
            f"| Slurm job ID | `{slurm_job_id}` |\n"
            f"| Tier classification | `{tier}` |\n"
            f"| Date (UTC) | `{timestamp_utc}` |\n\n"
            f"## Per-family results (mean per-record WER and Word Accuracy)\n\n"
            f"{pf_table}\n\n"
            f"## Overall — macro over families (headline)\n\n"
            f"| Metric | Value | Δ vs degraded | Δ vs clean |\n|---|---|---|---|\n"
            f"| Mean per-record WER | {macro_wer:.4f} | {delta_macro_wer_vs_degraded:+.4f} | {delta_macro_wer_vs_clean:+.4f} |\n"
            f"| Mean per-record Word Accuracy | {macro_wa:.4f} | {delta_macro_wa_vs_degraded:+.4f} | {delta_macro_wa_vs_clean:+.4f} |\n\n"
            f"## Consistency check — record_micro\n\n"
            f"This is NOT corpus WER. It is the mean of per-record values across all predictions. "
            f"Because per-family counts are equal ({EXPECTED_PER_FAMILY_COUNT} each in full mode), "
            f"this matches the macro headline.\n\n"
            f"| Metric | Value | abs(macro − record_micro) |\n|---|---|---|\n"
            f"| Mean per-record WER | {record_micro_wer:.4f} | {abs(macro_wer - record_micro_wer):.2e} |\n"
            f"| Mean per-record Word Accuracy | {record_micro_wa:.4f} | {abs(macro_wa - record_micro_wa):.2e} |\n\n"
            f"## Reference clean baseline (T3.1)\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Mean per-record WER | {EXPECTED_CLEAN_BASELINE_WER:.4f} |\n"
            f"| Mean per-record Word Accuracy | {EXPECTED_CLEAN_BASELINE_WA:.4f} |\n\n"
            f"## Reference degraded baseline (T3.2)\n\n"
            f"{deg_ref_table}\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Macro mean per-record WER | {EXPECTED_DEGRADED_MACRO_WER:.4f} |\n"
            f"| Macro mean per-record Word Accuracy | {EXPECTED_DEGRADED_MACRO_WA:.4f} |\n\n"
            f"## Tier classification\n\n"
            f"Tier is assigned on the macro Word Accuracy delta vs the T3.2 degraded baseline:\n\n"
            f"- `strong` if Δ WA ≥ +{TIER_STRONG_THRESHOLD:.2f}\n"
            f"- `partial` if 0 < Δ WA < +{TIER_STRONG_THRESHOLD:.2f}\n"
            f"- `null_or_negative` if Δ WA ≤ 0\n\n"
            f"Δ macro Word Accuracy vs degraded: {delta_macro_wa_vs_degraded:+.4f}. "
            f"Tier: `{tier}`.\n"
        )
        summary_md_path.write_text(body, encoding="utf-8")

    print("\n=== T4.2d COMPLETE ===")
    print(f"  mode:                                   {mode_str}")
    print(f"  processed_records:                      {len(records_to_process)}")
    print(f"  failure_count:                          0")
    for fam in sorted(EXPECTED_FAMILIES):
        s = per_family_summary[fam]
        print(
            f"  {fam:<16}  count={s['count']:<5}  "
            f"mean_per_record_wer={s['mean_per_record_wer']:.4f}  "
            f"mean_per_record_word_accuracy={s['mean_per_record_word_accuracy']:.4f}"
        )
    print(f"  overall_macro_per_record_wer:           {macro_wer:.4f}")
    print(f"  overall_macro_per_record_word_accuracy: {macro_wa:.4f}")
    print(f"  record_micro_wer:                       {record_micro_wer:.4f}")
    print(f"  record_micro_word_accuracy:             {record_micro_wa:.4f}")
    print(f"  delta_macro_per_record_wer  vs clean:    {delta_macro_wer_vs_clean:+.4f}")
    print(f"  delta_macro_per_record_wa   vs clean:    {delta_macro_wa_vs_clean:+.4f}")
    print(f"  delta_macro_per_record_wer  vs degraded: {delta_macro_wer_vs_degraded:+.4f}")
    print(f"  delta_macro_per_record_wa   vs degraded: {delta_macro_wa_vs_degraded:+.4f}")
    print(f"  tier_classification:                    {tier}")
    print(f"  predictions:                            {predictions_path}")
    print(f"  metrics_summary:                        {metrics_summary_path}")
    if args.summary_md:
        print(f"  summary_md:                             {args.summary_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
