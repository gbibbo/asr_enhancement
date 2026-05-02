"""T2.3: Exclude public demo examples from the LibriSpeech manifest.

Placeholder mode: when status == pending_public_examples, records source manifest
integrity and exits 0 without writing a filtered manifest.

Complete mode: reads exclusion IDs and SHA-256 hashes from config, filters source
manifest, writes filtered JSONL, validates every line, exits 0 on success.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys

import yaml


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _count_lines(path: pathlib.Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for _ in fh:
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="T2.3 exclude public demo examples")
    parser.add_argument("--config", required=True, help="Path to public_examples_excluded.yaml")
    parser.add_argument("--source-manifest", required=True, help="Source JSONL manifest (T2.2 output)")
    parser.add_argument("--out-manifest", required=True, help="Output filtered JSONL path (not written in placeholder mode)")
    parser.add_argument("--summary", required=True, help="Path for JSON summary artifact")
    args = parser.parse_args()

    failures = []
    evidence = {
        "task": "T2.3",
        "mode": None,
        "success": False,
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
        "exclusion_config_path": args.config,
        "exclusion_status": None,
        "filled_after_demo_task": None,
        "source_manifest_path": args.source_manifest,
        "source_manifest_records": None,
        "source_manifest_size_bytes": None,
        "source_manifest_mtime": None,
        "filtered_manifest_path": None,
        "excluded_count": 0,
        "excluded_ids": [],
        "excluded_by_hash_count": 0,
        "remaining_records": None,
        "validation_passed": None,
        "all_failures": failures,
        "note": "",
    }

    # --- Phase 1: Config loading ---
    config_path = pathlib.Path(args.config)
    if not config_path.exists():
        failures.append(f"FATAL: config not found: {args.config}")
        evidence["all_failures"] = failures
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    with config_path.open("r") as fh:
        cfg = yaml.safe_load(fh)

    for key in ("status", "excluded_ids", "excluded_audio_sha256"):
        if key not in cfg:
            failures.append(f"FATAL: missing key in config: {key}")

    if failures:
        evidence["all_failures"] = failures
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    status = cfg["status"]
    evidence["exclusion_status"] = status
    evidence["filled_after_demo_task"] = cfg.get("filled_after_demo_task")

    accepted_statuses = ("pending_public_examples", "complete")
    if status not in accepted_statuses:
        failures.append(f"FATAL: unknown status '{status}' — expected one of {accepted_statuses}")
        evidence["all_failures"] = failures
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    # --- Phase 2: Source manifest check ---
    source_path = pathlib.Path(args.source_manifest)
    if not source_path.exists() or source_path.stat().st_size == 0:
        failures.append(f"FATAL: source manifest not found or empty: {args.source_manifest}")
        evidence["all_failures"] = failures
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    stat = source_path.stat()
    evidence["source_manifest_size_bytes"] = stat.st_size
    evidence["source_manifest_mtime"] = datetime.datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
    source_line_count = _count_lines(source_path)
    evidence["source_manifest_records"] = source_line_count
    print(f"Source manifest: {args.source_manifest} — {source_line_count} lines")

    # Check for stale filtered manifest
    out_path = pathlib.Path(args.out_manifest)
    if out_path.exists():
        failures.append(
            f"FATAL: stale filtered manifest found at {args.out_manifest} — remove it or investigate before rerunning T2.3"
        )
        evidence["all_failures"] = failures
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    # --- Phase 3a: Placeholder mode ---
    if status == "pending_public_examples":
        evidence["mode"] = "placeholder"
        excluded_ids = cfg.get("excluded_ids", [])
        excluded_hashes = cfg.get("excluded_audio_sha256", [])

        print(f"EXCLUSION STATUS: pending_public_examples")
        print(f"excluded_ids: {excluded_ids} ({len(excluded_ids)} items)")
        print(f"excluded_audio_sha256: {excluded_hashes} ({len(excluded_hashes)} items)")
        print("No filtered manifest written (placeholder mode).")

        evidence["excluded_ids"] = excluded_ids
        evidence["excluded_count"] = 0
        evidence["excluded_by_hash_count"] = 0
        evidence["filtered_manifest_path"] = None
        evidence["remaining_records"] = None
        evidence["validation_passed"] = None
        evidence["success"] = True
        evidence["note"] = (
            "Placeholder mode: no exclusions applied. Filtered manifest not written. "
            "T3 tasks gated by pending_public_examples status."
        )
        evidence["all_failures"] = []
        _write_summary(args.summary, evidence)

        print(f"Summary artifact: {args.summary}")
        print("T2.3 COMPLETE (PLACEHOLDER MODE)")
        print("Filtered manifest: NOT WRITTEN — rerun T2.3 after B6.2 closes")
        return 0

    # --- Phase 3b: Complete mode ---
    evidence["mode"] = "complete"
    excluded_ids = cfg.get("excluded_ids", [])
    excluded_hashes = cfg.get("excluded_audio_sha256", [])
    excluded_id_set = set(excluded_ids)
    excluded_hash_set = set(excluded_hashes)

    print(f"EXCLUSION STATUS: complete")
    print(f"excluded_ids: {len(excluded_id_set)} items")
    print(f"excluded_audio_sha256: {len(excluded_hash_set)} items")

    kept_records = []
    excluded_records = []
    excluded_by_hash_count = 0

    with source_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.rstrip("\n")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"line {lineno}: JSON parse error: {exc}")
                continue

            utterance_id = record.get("utterance_id", "")
            id_hit = utterance_id in excluded_id_set

            hash_hit = False
            if excluded_hash_set and not id_hit:
                audio_path = pathlib.Path(record.get("audio_path", ""))
                try:
                    file_hash = _sha256_file(audio_path)
                    if file_hash in excluded_hash_set:
                        hash_hit = True
                        excluded_by_hash_count += 1
                except OSError as exc:
                    failures.append(f"line {lineno}: IO error hashing {audio_path}: {exc}")
                    continue

            if id_hit or hash_hit:
                excluded_records.append({"utterance_id": utterance_id, "id_hit": id_hit, "hash_hit": hash_hit})
            else:
                kept_records.append(line)

    if failures:
        evidence["all_failures"] = failures
        evidence["excluded_count"] = len(excluded_records)
        evidence["excluded_by_hash_count"] = excluded_by_hash_count
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    # Write filtered manifest
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for line in kept_records:
            fh.write(line + "\n")

    # --- Phase 4: Validation ---
    written_line_count = _count_lines(out_path)
    expected_count = source_line_count - len(excluded_records)
    if written_line_count != expected_count:
        failures.append(
            f"FATAL: line count mismatch — written {written_line_count}, expected {expected_count}"
        )

    seen_ids = set()
    with out_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"validation line {lineno}: JSON parse error: {exc}")
                continue

            uid = record.get("utterance_id", "")
            if uid in excluded_id_set:
                failures.append(f"validation line {lineno}: excluded utterance_id still present: {uid}")
            if excluded_hash_set:
                audio_path = pathlib.Path(record.get("audio_path", ""))
                try:
                    fh2 = _sha256_file(audio_path)
                    if fh2 in excluded_hash_set:
                        failures.append(f"validation line {lineno}: excluded audio hash still present: {fh2}")
                except OSError as exc:
                    failures.append(f"validation line {lineno}: IO error hashing {audio_path}: {exc}")

            if uid in seen_ids:
                failures.append(f"validation line {lineno}: duplicate utterance_id: {uid}")
            seen_ids.add(uid)

    evidence["excluded_count"] = len(excluded_records)
    evidence["excluded_ids"] = [r["utterance_id"] for r in excluded_records]
    evidence["excluded_by_hash_count"] = excluded_by_hash_count
    evidence["remaining_records"] = len(kept_records)
    evidence["filtered_manifest_path"] = str(out_path)
    evidence["validation_passed"] = len(failures) == 0

    if failures:
        evidence["all_failures"] = failures
        evidence["success"] = False
        _write_summary(args.summary, evidence)
        print(f"T2.3 FAILED: {failures}")
        return 1

    evidence["success"] = True
    evidence["all_failures"] = []
    evidence["note"] = (
        f"Complete mode: {len(excluded_records)} records excluded "
        f"({excluded_by_hash_count} by hash). "
        f"Filtered manifest: {len(kept_records)} records."
    )
    _write_summary(args.summary, evidence)

    print(f"Excluded records: {len(excluded_records)}")
    print(f"Remaining records: {len(kept_records)}")
    print(f"Filtered manifest: {out_path}")
    print(f"Summary artifact: {args.summary}")
    print("T2.3 COMPLETE")
    return 0


def _write_summary(path: str, evidence: dict) -> None:
    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)


if __name__ == "__main__":
    sys.exit(main())
