"""T3.1: Run clean-audio Whisper baseline on the filtered LibriSpeech manifest.

Runs openai-whisper on clean audio, computes WER and Word Accuracy using the shared
metrics implementation, and writes results outside the repository.

Usage:
  python3 -s scripts/training/run_whisper_baseline.py \
    --manifest $TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl \
    --exclusion-config configs/training/public_examples_excluded.yaml \
    --dataset-version-config configs/training/dataset_version.yaml \
    --model base.en \
    --whisper-cache $TRAIN_ROOT/cache/whisper \
    --out-dir $TRAIN_ROOT/runs/t3_1_baseline_<job_id> \
    [--max-records 50] \
    [--summary-md reports/training/baseline_clean_wer.md]
"""
from __future__ import annotations

import argparse
import datetime
import importlib.metadata
import json
import os
import pathlib
import subprocess
import sys
import time


EXPECTED_DATASET_VERSION = "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8"
EXPECTED_MANIFEST_RECORDS = 2693

RESERVED_IDS = {
    "1272-128104-0000",
    "1462-170138-0001",
    "1673-143396-0002",
    "174-168635-0000",
    "1919-142785-0003",
    "1988-147956-0002",
    "1993-147149-0000",
    "2035-147960-0000",
    "2078-142845-0009",
    "2086-149214-0000",
}


def _git_rev_parse_head(repo: pathlib.Path) -> str:
    # Prefer env var set by the Slurm shell (git not available inside Apptainer).
    val = os.environ.get("GIT_COMMIT_AT_RUN", "")
    if val:
        return val
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def _git_status_short(repo: pathlib.Path) -> str:
    # Prefer env var set by the Slurm shell (git not available inside Apptainer).
    val = os.environ.get("GIT_STATUS_SHORT_AT_RUN", None)
    if val is not None:
        return val
    try:
        return subprocess.check_output(
            ["git", "status", "--short"], cwd=repo, text=True
        ).strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def _whisper_version() -> str:
    try:
        import whisper
        return getattr(whisper, "__version__", None) or importlib.metadata.version("openai-whisper")
    except Exception:
        return "unknown"


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def _count_lines(path: pathlib.Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for _ in fh:
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="T3.1 Whisper baseline")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--exclusion-config", required=True)
    parser.add_argument("--dataset-version-config", required=True)
    parser.add_argument("--model", default="base.en")
    parser.add_argument("--whisper-cache", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--summary-md", default=None)
    args = parser.parse_args()

    repo = pathlib.Path(__file__).resolve().parent.parent.parent
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = out_dir / "predictions.jsonl"
    if predictions_path.exists():
        print(f"BLOCKER: stale predictions.jsonl found at {predictions_path} — remove before rerunning")
        return 1

    slurm_job_id = os.environ.get("SLURM_JOB_ID", "local")
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"
    git_commit = _git_rev_parse_head(repo)
    git_status = _git_status_short(repo)

    # -------------------------------------------------------------------------
    # PRE-FLIGHT CHECKS
    # -------------------------------------------------------------------------
    import yaml

    # 1. Exclusion config status
    excl_path = pathlib.Path(args.exclusion_config)
    if not excl_path.exists():
        print(f"BLOCKER: exclusion config not found: {excl_path}")
        return 1
    with excl_path.open() as fh:
        excl_cfg = yaml.safe_load(fh)
    if excl_cfg.get("status") != "complete":
        print(f"BLOCKER: public_examples_excluded.yaml status is {excl_cfg.get('status')!r}, expected 'complete'")
        return 1

    # 2. Dataset version config
    dv_path = pathlib.Path(args.dataset_version_config)
    if not dv_path.exists():
        print(f"BLOCKER: dataset version config not found: {dv_path}")
        return 1
    with dv_path.open() as fh:
        dv_cfg = yaml.safe_load(fh)
    actual_version = dv_cfg.get("dataset_version", "")
    if actual_version != EXPECTED_DATASET_VERSION:
        print(f"BLOCKER: dataset_version mismatch: got {actual_version!r}, expected {EXPECTED_DATASET_VERSION!r}")
        return 1

    # 3. Manifest line count
    manifest_path = pathlib.Path(args.manifest)
    if not manifest_path.exists():
        print(f"BLOCKER: manifest not found: {manifest_path}")
        return 1
    total_manifest_records = _count_lines(manifest_path)
    if total_manifest_records != EXPECTED_MANIFEST_RECORDS:
        print(f"BLOCKER: manifest line count is {total_manifest_records}, expected {EXPECTED_MANIFEST_RECORDS}")
        return 1

    # 4. Reserved IDs absent from manifest
    with manifest_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                print(f"BLOCKER: JSON parse error at manifest line {lineno}")
                return 1
            uid = rec.get("utterance_id", "")
            if uid in RESERVED_IDS:
                print(f"BLOCKER: reserved demo example found in manifest: {uid}")
                return 1

    # Also load full manifest records into memory for inference
    records = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            records.append(json.loads(line.rstrip("\n")))

    # 5. Metrics import
    try:
        from libs.audio.metrics import METRICS_VERSION, normalize_text, word_error_rate, word_accuracy
    except ImportError as exc:
        print(f"BLOCKER: cannot import libs.audio.metrics: {exc}")
        return 1

    # 6. Whisper import
    try:
        import whisper
        whisper_ver = _whisper_version()
    except ImportError as exc:
        print(f"BLOCKER: cannot import whisper: {exc}")
        return 1

    print("PRE-FLIGHT OK")
    print(f"  manifest records:    {total_manifest_records}")
    print(f"  dataset_version:     {EXPECTED_DATASET_VERSION}")
    print(f"  exclusion status:    complete")
    print(f"  METRICS_VERSION:     {METRICS_VERSION}")
    print(f"  whisper version:     {whisper_ver}")
    print(f"  model:               {args.model}")
    print(f"  whisper cache:       {args.whisper_cache}")
    print(f"  out_dir:             {out_dir}")
    print(f"  max_records:         {args.max_records}")
    print(f"  git_commit_at_run:   {git_commit}")
    print(f"  git_status_at_run:   {git_status!r}")
    print(f"  slurm_job_id:        {slurm_job_id}")

    # -------------------------------------------------------------------------
    # LOAD MODEL
    # -------------------------------------------------------------------------
    whisper_cache = pathlib.Path(args.whisper_cache)
    whisper_cache.mkdir(parents=True, exist_ok=True)

    print(f"\nLoading whisper model '{args.model}' from cache {whisper_cache} ...")
    model_load_start = time.monotonic()
    model = whisper.load_model(args.model, download_root=str(whisper_cache))
    print(f"Model loaded in {time.monotonic() - model_load_start:.1f}s")

    # -------------------------------------------------------------------------
    # INFERENCE LOOP
    # -------------------------------------------------------------------------
    processed_target = args.max_records if args.max_records is not None else len(records)
    processed_target = min(processed_target, len(records))

    print(f"\nRunning inference on {processed_target} records ...")

    wer_values = []
    wa_values = []
    failure_count = 0

    with predictions_path.open("w", encoding="utf-8") as pred_fh:
        for i, rec in enumerate(records[:processed_target]):
            uid = rec["utterance_id"]
            audio_path = rec["audio_path"]
            reference = rec.get("transcript", "")
            duration_s = rec.get("duration_seconds", 0.0)

            t_start = time.monotonic()
            try:
                result = model.transcribe(
                    str(audio_path), language="en", fp16=False, verbose=False
                )
                hypothesis = result["text"]
                wer = word_error_rate(reference, hypothesis)
                wa = word_accuracy(wer)
                ref_norm = normalize_text(reference)
                hyp_norm = normalize_text(hypothesis)
                processing_time = time.monotonic() - t_start

                entry = {
                    "utterance_id": uid,
                    "split": rec.get("split", ""),
                    "speaker_id": rec.get("speaker_id", ""),
                    "duration_seconds": duration_s,
                    "reference_normalized": ref_norm,
                    "hypothesis_normalized": hyp_norm,
                    "wer": wer,
                    "word_accuracy": wa,
                    "processing_time_s": round(processing_time, 3),
                    "whisper_model": args.model,
                    "whisper_version": whisper_ver,
                    "metrics_version": METRICS_VERSION,
                    "dataset_version": EXPECTED_DATASET_VERSION,
                }
                wer_values.append(wer)
                wa_values.append(wa)
            except Exception as exc:
                failure_count += 1
                entry = {
                    "utterance_id": uid,
                    "wer": None,
                    "word_accuracy": None,
                    "error": str(exc),
                    "whisper_model": args.model,
                    "metrics_version": METRICS_VERSION,
                    "dataset_version": EXPECTED_DATASET_VERSION,
                }

            pred_fh.write(json.dumps(entry) + "\n")
            pred_fh.flush()

            if (i + 1) % 50 == 0 or (i + 1) == processed_target:
                elapsed = time.monotonic() - model_load_start
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                print(
                    f"  [{i + 1}/{processed_target}]  failures={failure_count}"
                    f"  rate={rate:.2f} rec/s  elapsed={elapsed:.0f}s"
                )

    # -------------------------------------------------------------------------
    # FAILURE CHECK
    # -------------------------------------------------------------------------
    if failure_count > 0:
        print(f"\nBASELINE FAILED: failure_count={failure_count} of {processed_target}")
        print(f"predictions.jsonl preserved at: {predictions_path}")
        return 1

    # -------------------------------------------------------------------------
    # WRITE OUTPUTS
    # -------------------------------------------------------------------------
    mean_wer = sum(wer_values) / len(wer_values)
    mean_wa = sum(wa_values) / len(wa_values)

    summary = {
        "task": "T3.1",
        "success": True,
        "timestamp_utc": timestamp_utc,
        "total_manifest_records": total_manifest_records,
        "processed_records": processed_target,
        "failure_count": 0,
        "mean_wer": mean_wer,
        "mean_word_accuracy": mean_wa,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "manifest_path": str(manifest_path),
        "manifest_records": total_manifest_records,
        "whisper_model": args.model,
        "whisper_version": whisper_ver,
        "metrics_version": METRICS_VERSION,
        "git_commit_at_run": git_commit,
        "git_status_short_at_run": git_status,
        "result_commit": "PENDING_RESULT_COMMIT",
        "slurm_job_id": slurm_job_id,
    }
    _write_json(out_dir / "metrics_summary.json", summary)

    config_snap = {
        "manifest": str(manifest_path),
        "exclusion_config": str(excl_path),
        "dataset_version_config": str(dv_path),
        "model": args.model,
        "whisper_cache": args.whisper_cache,
        "out_dir": str(out_dir),
        "max_records": args.max_records,
        "summary_md": args.summary_md,
    }
    _write_json(out_dir / "config_snapshot.json", config_snap)

    run_md = (
        f"# T3.1 Run Summary\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Dataset version | `{EXPECTED_DATASET_VERSION}` |\n"
        f"| Manifest records | {total_manifest_records} |\n"
        f"| Processed records | {processed_target} |\n"
        f"| Failure count | 0 |\n"
        f"| Mean WER | {mean_wer:.4f} |\n"
        f"| Mean Word Accuracy | {mean_wa:.4f} |\n"
        f"| Whisper model | `{args.model}` (openai-whisper {whisper_ver}) |\n"
        f"| Metrics version | `{METRICS_VERSION}` |\n"
        f"| Slurm job ID | `{slurm_job_id}` |\n"
        f"| Git commit at run | `{git_commit}` |\n"
        f"| Result commit | `PENDING_RESULT_COMMIT` |\n"
        f"| Timestamp (UTC) | `{timestamp_utc}` |\n"
    )
    (out_dir / "run_summary.md").write_text(run_md, encoding="utf-8")

    # Write Git-committed summary if requested
    if args.summary_md:
        summary_md_path = pathlib.Path(args.summary_md)
        summary_md_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "smoke" if args.max_records is not None else "complete"
        summary_md_path.write_text(
            f"# T3.1 Clean-Audio Whisper Baseline\n\n"
            f"Status: {mode}\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Dataset version | `{EXPECTED_DATASET_VERSION}` |\n"
            f"| Manifest records | {total_manifest_records} |\n"
            f"| Processed records | {processed_target} |\n"
            f"| Failure count | 0 |\n"
            f"| Whisper model | `{args.model}` (openai-whisper {whisper_ver}) |\n"
            f"| Metrics version | `{METRICS_VERSION}` |\n"
            f"| Code commit at run | `{git_commit}` |\n"
            f"| Result commit | `PENDING_RESULT_COMMIT` |\n"
            f"| Slurm job ID | `{slurm_job_id}` |\n"
            f"| Date (UTC) | `{timestamp_utc}` |\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Mean WER | {mean_wer:.4f} |\n"
            f"| Mean Word Accuracy | {mean_wa:.4f} |\n",
            encoding="utf-8",
        )

    print(f"\n=== T3.1 COMPLETE ===")
    print(f"  processed_records:    {processed_target}")
    print(f"  failure_count:        0")
    print(f"  mean_wer:             {mean_wer:.4f}")
    print(f"  mean_word_accuracy:   {mean_wa:.4f}")
    print(f"  predictions:          {predictions_path}")
    print(f"  metrics_summary:      {out_dir / 'metrics_summary.json'}")
    if args.summary_md:
        print(f"  summary_md:           {args.summary_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
