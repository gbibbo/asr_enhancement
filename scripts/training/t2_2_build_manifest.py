#!/usr/bin/env python3
"""T2.2 LibriSpeech manifest generator.

Reads configs/training/librispeech_sources.yaml, discovers which
config-present splits are usable (have FLAC + transcript files), then
writes a JSONL manifest with one record per utterance.

Strict error policy for included splits:
  - missing FLAC referenced by transcript  -> failure, no manifest written
  - soundfile.info() error                 -> failure, no manifest written
  - duplicate utterance_id                 -> failure, no manifest written
  - sample_rate != 16000                   -> failure at validation stage
  - empty transcript                        -> failure, no manifest written

Config-present splits with zero FLAC or zero transcript files are
classified as present_empty anomalies and excluded from the manifest
(not a failure by themselves).

Exit 0 on full success; exit 1 on any failure.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

_EXPECTED_SAMPLE_RATE = 16000

_REQUIRED_FIELDS = [
    "dataset",
    "split",
    "speaker_id",
    "chapter_id",
    "utterance_id",
    "audio_path",
    "transcript",
    "transcript_path",
    "duration_seconds",
    "sample_rate",
    "source_root",
    "relative_path",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="T2.2 LibriSpeech manifest generator")
    parser.add_argument("--config", required=True, type=Path,
                        help="Path to librispeech_sources.yaml")
    parser.add_argument("--out-manifest", required=True, type=Path,
                        help="Output JSONL manifest path")
    parser.add_argument("--summary", required=True, type=Path,
                        help="Summary/evidence JSON output path")
    args = parser.parse_args()

    import yaml
    import soundfile as sf

    evidence: dict = {
        "task": "T2.2",
        "success": False,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "pythonnousersite_env": os.environ.get("PYTHONNOUSERSITE", "NOT_SET"),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
        "config_path": str(args.config),
        "manifest_path": str(args.out_manifest),
    }
    failures: list[str] = []

    if evidence["pythonnousersite_env"] != "1":
        failures.append(
            f"PYTHONNOUSERSITE is not '1': {evidence['pythonnousersite_env']}"
        )

    # ------------------------------------------------------------------ #
    # Phase 1: Config loading                                              #
    # ------------------------------------------------------------------ #
    cfg: dict | None = None
    if not failures:
        try:
            with open(args.config) as fh:
                cfg = yaml.safe_load(fh)
        except Exception as exc:
            failures.append(f"FATAL: cannot load config {args.config}: {exc}")

    source_root: Path | None = None
    if cfg is not None and not failures:
        if "dataset_root" not in cfg:
            failures.append("FATAL: dataset_root key missing from config")
        else:
            source_root = Path(cfg["dataset_root"])
            evidence["source_root"] = str(source_root)
            if "authoritative_source_root" in cfg:
                alt = str(cfg["authoritative_source_root"])
                if str(source_root) != alt:
                    failures.append(
                        f"FATAL: dataset_root ({source_root}) and "
                        f"authoritative_source_root ({alt}) disagree in config"
                    )

    if failures:
        _write_summary_and_exit(args.summary, evidence, failures)

    # ------------------------------------------------------------------ #
    # Phase 2: Pre-scan — determine usable splits                         #
    # ------------------------------------------------------------------ #
    assert source_root is not None
    assert cfg is not None

    splits_cfg: dict = cfg.get("splits", {})
    config_present_splits: list[str] = sorted(
        name
        for name, info in splits_cfg.items()
        if info.get("split_status") == "present"
    )
    evidence["config_present_splits"] = config_present_splits

    usable_splits: list[str] = []
    skipped_present_splits: list[str] = []
    skipped_present_split_reasons: dict[str, str] = {}
    per_split_flac_counts: dict[str, int] = {}
    per_split_transcript_counts: dict[str, int] = {}

    for split in config_present_splits:
        split_dir = source_root / split
        if split_dir.is_dir():
            flac_count = sum(1 for _ in split_dir.rglob("*.flac"))
            trans_count = sum(1 for _ in split_dir.rglob("*.trans.txt"))
        else:
            flac_count = 0
            trans_count = 0
        per_split_flac_counts[split] = flac_count
        per_split_transcript_counts[split] = trans_count

        if flac_count > 0 and trans_count > 0:
            usable_splits.append(split)
        else:
            skipped_present_splits.append(split)
            skipped_present_split_reasons[split] = "no_flac_no_transcripts"
            print(
                f"ANOMALY: split '{split}' is config-present but has "
                f"{flac_count} FLAC and {trans_count} transcript files; skipping"
            )

    evidence.update({
        "usable_splits": usable_splits,
        "skipped_present_splits": skipped_present_splits,
        "skipped_present_split_reasons": skipped_present_split_reasons,
        "per_split_flac_counts": per_split_flac_counts,
        "per_split_transcript_counts": per_split_transcript_counts,
    })

    if not usable_splits:
        failures.append(
            "FATAL: no usable splits found — all config-present splits are empty"
        )
        _write_summary_and_exit(args.summary, evidence, failures)

    manifest_scope = (
        "all_present_splits" if not skipped_present_splits else "partial_present_splits"
    )
    evidence["manifest_scope"] = manifest_scope

    # ------------------------------------------------------------------ #
    # Phase 3: Manifest generation                                        #
    # ------------------------------------------------------------------ #
    records: list[dict] = []
    seen_utterance_ids: dict[str, dict] = {}
    missing_flac_records: list[dict] = []
    soundfile_error_records: list[dict] = []
    duplicate_utterance_id_records: list[dict] = []
    missing_transcript_chapter_count = 0
    per_split_manifest_record_counts: dict[str, int] = {}

    for split in sorted(usable_splits):
        split_dir = source_root / split
        split_count = 0

        for speaker_dir in sorted(split_dir.iterdir()):
            if not speaker_dir.is_dir():
                continue
            speaker_id = speaker_dir.name

            for chapter_dir in sorted(speaker_dir.iterdir()):
                if not chapter_dir.is_dir():
                    continue
                chapter_id = chapter_dir.name

                trans_files = sorted(chapter_dir.glob("*.trans.txt"))
                if not trans_files:
                    print(f"WARNING: no trans.txt in {chapter_dir}; skipping chapter")
                    missing_transcript_chapter_count += 1
                    continue

                for trans_path in trans_files:
                    with open(trans_path) as fh:
                        trans_lines = fh.readlines()

                    for lineno, raw_line in enumerate(trans_lines, 1):
                        line = raw_line.strip()
                        if not line:
                            continue

                        parts = line.split()
                        utterance_id = parts[0]
                        transcript = " ".join(parts[1:])

                        if not transcript:
                            failures.append(
                                f"empty transcript: utterance_id={utterance_id} "
                                f"path={trans_path} line={lineno}"
                            )
                            continue

                        flac_path = chapter_dir / (utterance_id + ".flac")

                        # Duplicate utterance_id is a hard failure
                        if utterance_id in seen_utterance_ids:
                            dup_info = {
                                "utterance_id": utterance_id,
                                "split": split,
                                "transcript_path": str(trans_path),
                                "line_number": lineno,
                                "first_seen_transcript_path": (
                                    seen_utterance_ids[utterance_id]["transcript_path"]
                                ),
                            }
                            duplicate_utterance_id_records.append(dup_info)
                            failures.append(
                                f"duplicate utterance_id '{utterance_id}' "
                                f"in {trans_path} line {lineno}"
                            )
                            continue

                        seen_utterance_ids[utterance_id] = {
                            "transcript_path": str(trans_path),
                            "line_number": lineno,
                        }

                        # Missing FLAC is a hard failure
                        if not flac_path.exists():
                            missing_flac_records.append({
                                "utterance_id": utterance_id,
                                "split": split,
                                "expected_path": str(flac_path),
                            })
                            failures.append(f"missing FLAC: {flac_path}")
                            continue

                        # soundfile.info() failure is a hard failure
                        try:
                            info = sf.info(str(flac_path))
                            duration_seconds = round(info.frames / info.samplerate, 6)
                            sample_rate = info.samplerate
                        except Exception as exc:
                            soundfile_error_records.append({
                                "utterance_id": utterance_id,
                                "path": str(flac_path),
                                "error": str(exc),
                            })
                            failures.append(
                                f"soundfile.info() failed for {flac_path}: {exc}"
                            )
                            continue

                        records.append({
                            "dataset": "LibriSpeech",
                            "split": split,
                            "speaker_id": speaker_id,
                            "chapter_id": chapter_id,
                            "utterance_id": utterance_id,
                            "audio_path": str(flac_path),
                            "transcript": transcript,
                            "transcript_path": str(trans_path),
                            "duration_seconds": duration_seconds,
                            "sample_rate": sample_rate,
                            "source_root": str(source_root),
                            "relative_path": str(
                                flac_path.relative_to(source_root)
                            ),
                        })
                        split_count += 1

        per_split_manifest_record_counts[split] = split_count
        print(f"SPLIT {split}: {split_count} records")

    evidence.update({
        "missing_flac_count": len(missing_flac_records),
        "missing_flac_records": missing_flac_records,
        "soundfile_error_count": len(soundfile_error_records),
        "soundfile_error_records": soundfile_error_records,
        "duplicate_utterance_id_count": len(duplicate_utterance_id_records),
        "duplicate_utterance_id_records": duplicate_utterance_id_records,
        "missing_transcript_chapter_count": missing_transcript_chapter_count,
        "per_split_manifest_record_counts": per_split_manifest_record_counts,
        "total_records": len(records),
    })

    # Do not write the manifest if any generation failures were found
    if failures:
        _write_summary_and_exit(args.summary, evidence, failures)

    # ------------------------------------------------------------------ #
    # Phase 4: Sort and write manifest                                    #
    # ------------------------------------------------------------------ #
    records.sort(
        key=lambda r: (r["split"], r["speaker_id"], r["chapter_id"], r["utterance_id"])
    )

    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_manifest, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ #
    # Phase 5: Full manifest validation (every line)                      #
    # ------------------------------------------------------------------ #
    validation_failures: list[str] = []
    validation_seen_ids: set[str] = set()
    lines_checked = 0

    with open(args.out_manifest) as fh:
        for lineno, raw_line in enumerate(fh, 1):
            lines_checked += 1
            try:
                rec = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                validation_failures.append(f"line {lineno}: JSON parse error: {exc}")
                continue

            for field in _REQUIRED_FIELDS:
                if field not in rec:
                    validation_failures.append(f"line {lineno}: missing field '{field}'")

            if not rec.get("transcript", "X"):
                validation_failures.append(f"line {lineno}: empty transcript")

            dur = rec.get("duration_seconds")
            if isinstance(dur, (int, float)) and dur <= 0:
                validation_failures.append(
                    f"line {lineno}: duration_seconds <= 0: {dur}"
                )

            sr = rec.get("sample_rate")
            if isinstance(sr, int) and sr != _EXPECTED_SAMPLE_RATE:
                validation_failures.append(
                    f"line {lineno}: sample_rate {sr} != {_EXPECTED_SAMPLE_RATE}"
                )

            audio_path = rec.get("audio_path", "")
            if audio_path and not Path(audio_path).exists():
                validation_failures.append(
                    f"line {lineno}: audio_path not found on disk: {audio_path}"
                )

            uid = rec.get("utterance_id", "")
            if uid:
                if uid in validation_seen_ids:
                    validation_failures.append(
                        f"line {lineno}: duplicate utterance_id in manifest: {uid}"
                    )
                validation_seen_ids.add(uid)

    if lines_checked != len(records):
        validation_failures.append(
            f"line count mismatch: written {len(records)}, re-read {lines_checked}"
        )

    evidence.update({
        "validation_lines_checked": lines_checked,
        "validation_failures": validation_failures,
        "validation_passed": len(validation_failures) == 0,
    })

    if validation_failures:
        failures.extend(validation_failures)
        _write_summary_and_exit(args.summary, evidence, failures)

    # ------------------------------------------------------------------ #
    # Success                                                             #
    # ------------------------------------------------------------------ #
    evidence["success"] = True
    evidence["all_failures"] = []
    evidence["timestamp_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with open(args.summary, "w") as fh:
        json.dump(evidence, fh, indent=2)

    print()
    print(f"manifest_scope          : {manifest_scope}")
    print(f"config_present_splits   : {config_present_splits}")
    print(f"usable_splits           : {usable_splits}")
    print(f"skipped_present_splits  : {skipped_present_splits}")
    print(f"total_records           : {len(records)}")
    print(f"validation_lines_checked: {lines_checked}")
    print(f"manifest_path           : {args.out_manifest}")
    print(f"summary_path            : {args.summary}")
    print()
    print("T2.2 COMPLETE")
    sys.exit(0)


def _write_summary_and_exit(
    summary_path: Path,
    evidence: dict,
    failures: list[str],
) -> None:
    evidence["success"] = False
    evidence["all_failures"] = failures
    evidence["timestamp_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    try:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w") as fh:
            json.dump(evidence, fh, indent=2)
        print(f"summary_path (failure)  : {summary_path}")
    except Exception as exc:
        print(f"WARNING: could not write summary JSON: {exc}")
    print()
    print(f"T2.2 FAILED: {failures}")
    sys.exit(1)


if __name__ == "__main__":
    main()
