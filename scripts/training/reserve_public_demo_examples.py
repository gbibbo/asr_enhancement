"""T2.3b: Reserve public demo examples from the dev-clean manifest.

Two explicit phases:

Phase A — Select and validate the reserve set:
  - Apply deterministic selection rule (one per speaker, sort by speaker_id/utterance_id).
  - Compute SHA-256 of each selected audio file.
  - Validate the set against mandatory criteria.
  - Compare selected IDs (in order) against the expected sanity-check list; stop if mismatch.
  - Write configs/training/reserved_public_demo_examples.yaml.

Phase B — Update exclusion config (only after Phase A passes):
  - Overwrite configs/training/public_examples_excluded.yaml with status: complete.
  - Re-read and verify the written file.

Exit 0 only if both phases succeed.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys

import yaml


# ---------------------------------------------------------------------------
# Expected sanity-check list (ordered, exact).
# The script derives the actual selection from the manifest.
# If the derived order differs, Phase A stops without writing anything.
# ---------------------------------------------------------------------------
EXPECTED_ORDERED_IDS = [
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
]

FILTERED_MANIFEST_PATH = (
    "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
    "/datasets/librispeech_manifest_v1_filtered.jsonl"
)


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _write_summary(path: str, evidence: dict) -> None:
    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)


def _select_examples(manifest_path: pathlib.Path) -> list[dict]:
    """Apply the deterministic selection rule and return 10 records in order."""
    qualifying = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (
                r.get("split") == "dev-clean"
                and 3.0 <= r.get("duration_seconds", 0.0) <= 10.0
                and r.get("transcript", "").strip()
                and r.get("sample_rate") == 16000
            ):
                qualifying.append(r)

    # Sort by (speaker_id, utterance_id) — lexicographic
    qualifying.sort(key=lambda r: (r["speaker_id"], r["utterance_id"]))

    # Keep first qualifying utterance per speaker
    seen_speakers: dict[str, dict] = {}
    for r in qualifying:
        spk = r["speaker_id"]
        if spk not in seen_speakers:
            seen_speakers[spk] = r

    # Sort representatives by speaker_id and take first 10
    representatives = sorted(seen_speakers.values(), key=lambda r: r["speaker_id"])
    return representatives[:10]


def main() -> int:
    parser = argparse.ArgumentParser(description="T2.3b reserve public demo examples")
    parser.add_argument("--manifest", required=True, help="Path to librispeech_manifest_v1.jsonl")
    parser.add_argument("--sources-config", required=True, help="Path to librispeech_sources.yaml")
    parser.add_argument("--exclusion-config", required=True,
                        help="Path to public_examples_excluded.yaml (updated in phase B)")
    parser.add_argument("--out-reserved", required=True,
                        help="Output path for reserved_public_demo_examples.yaml")
    parser.add_argument("--summary", required=True, help="Path for scratch JSON evidence artifact")
    args = parser.parse_args()

    failures: list[str] = []
    evidence: dict = {
        "task": "T2.3b",
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
        "pythonnousersite_env": os.environ.get("PYTHONNOUSERSITE", "NOT_SET"),
        "manifest_path": args.manifest,
        "exclusion_config_path": args.exclusion_config,
        "out_reserved_path": args.out_reserved,
        "reserve_phase_success": False,
        "exclusion_config_update_success": False,
        "selected_utterance_ids": [],
        "selected_audio_sha256": [],
        "reserved_examples_config": None,
        "success": False,
        "all_failures": failures,
    }

    # --- Guard: PYTHONNOUSERSITE ---
    if evidence["pythonnousersite_env"] != "1":
        failures.append(f"PYTHONNOUSERSITE is not '1': {evidence['pythonnousersite_env']}")
        _write_summary(args.summary, evidence)
        print(f"T2.3b FAILED: {failures}")
        return 1

    # --- Verify inputs exist ---
    manifest_path = pathlib.Path(args.manifest)
    if not manifest_path.exists() or manifest_path.stat().st_size == 0:
        failures.append(f"FATAL: manifest not found or empty: {args.manifest}")
        _write_summary(args.summary, evidence)
        print(f"T2.3b FAILED: {failures}")
        return 1

    excl_config_path = pathlib.Path(args.exclusion_config)
    if not excl_config_path.exists():
        failures.append(f"FATAL: exclusion config not found: {args.exclusion_config}")
        _write_summary(args.summary, evidence)
        print(f"T2.3b FAILED: {failures}")
        return 1

    # -----------------------------------------------------------------------
    # PHASE A — Select and validate the reserve set
    # -----------------------------------------------------------------------
    out_reserved = pathlib.Path(args.out_reserved)

    # Resume-safe: if already reserved and valid, skip Phase A writes
    phase_a_skipped = False
    if out_reserved.exists():
        try:
            existing = yaml.safe_load(out_reserved.read_text())
            if (
                existing.get("status") == "reserved_for_public_demo"
                and isinstance(existing.get("examples"), list)
                and len(existing["examples"]) == 10
            ):
                print("PHASE A: skipped (reserved_public_demo_examples.yaml already exists and validates)")
                phase_a_skipped = True
                selected_examples = existing["examples"]
            else:
                failures.append(
                    f"FATAL: {args.out_reserved} exists but is not a valid reserved set "
                    f"(status={existing.get('status')}, examples count={len(existing.get('examples', []))})"
                )
                _write_summary(args.summary, evidence)
                print(f"T2.3b FAILED: {failures}")
                return 1
        except Exception as exc:
            failures.append(f"FATAL: failed to read existing reserved file: {exc}")
            _write_summary(args.summary, evidence)
            print(f"T2.3b FAILED: {failures}")
            return 1

    if not phase_a_skipped:
        print("=== PHASE A: Selecting reserve set ===")
        selected_records = _select_examples(manifest_path)
        print(f"Selected {len(selected_records)} records from manifest")

        if len(selected_records) < 10:
            failures.append(
                f"FATAL: selection rule produced only {len(selected_records)} examples; "
                f"expected 10. Check manifest qualifying records."
            )
            _write_summary(args.summary, evidence)
            print(f"T2.3b FAILED: {failures}")
            return 1

        # --- Order-explicit sanity check ---
        selected_ids_ordered = [r["utterance_id"] for r in selected_records]
        if selected_ids_ordered != EXPECTED_ORDERED_IDS:
            failures.append(
                f"FATAL: selected IDs differ from expected ordered list.\n"
                f"  Selected (ordered): {selected_ids_ordered}\n"
                f"  Expected (ordered): {EXPECTED_ORDERED_IDS}\n"
                "  Do not update public_examples_excluded.yaml. "
                "  Investigate manifest drift before proceeding."
            )
            _write_summary(args.summary, evidence)
            print(f"T2.3b FAILED: {failures}")
            return 1

        print("SANITY CHECK: selected IDs match expected ordered list. OK")

        # --- Compute SHA-256 of each audio file ---
        print("Computing SHA-256 for selected audio files...")
        selected_examples: list[dict] = []
        for rec in selected_records:
            audio_path = pathlib.Path(rec["audio_path"])
            try:
                sha256 = _sha256_file(audio_path)
            except OSError as exc:
                failures.append(f"FATAL: cannot hash {audio_path}: {exc}")
                continue

            if len(sha256) != 64:
                failures.append(f"FATAL: SHA-256 not 64 chars for {audio_path}: {sha256!r}")
                continue

            selected_examples.append({
                "utterance_id": rec["utterance_id"],
                "split": rec["split"],
                "speaker_id": rec["speaker_id"],
                "chapter_id": rec["chapter_id"],
                "transcript": rec["transcript"],
                "audio_path": rec["audio_path"],
                "audio_sha256": sha256,
                "duration_seconds": rec["duration_seconds"],
                "sample_rate": rec["sample_rate"],
            })
            print(f"  {rec['utterance_id']}  sha256={sha256[:16]}…  dur={rec['duration_seconds']}s")

        if failures:
            _write_summary(args.summary, evidence)
            print(f"T2.3b FAILED: {failures}")
            return 1

        # --- Full validation of reserve set ---
        ids_seen: set[str] = set()
        speakers_seen: set[str] = set()
        for ex in selected_examples:
            uid = ex["utterance_id"]
            spk = ex["speaker_id"]
            if uid in ids_seen:
                failures.append(f"FATAL: duplicate utterance_id in reserve set: {uid}")
            ids_seen.add(uid)
            if spk in speakers_seen:
                failures.append(f"FATAL: duplicate speaker_id in reserve set: {spk}")
            speakers_seen.add(spk)
            if not (3.0 <= ex["duration_seconds"] <= 10.0):
                failures.append(f"FATAL: {uid} duration {ex['duration_seconds']} out of [3.0, 10.0]")
            if ex["sample_rate"] != 16000:
                failures.append(f"FATAL: {uid} sample_rate {ex['sample_rate']} != 16000")
            if not ex["transcript"].strip():
                failures.append(f"FATAL: {uid} has empty transcript")
            if not pathlib.Path(ex["audio_path"]).exists():
                failures.append(f"FATAL: {uid} audio file not found: {ex['audio_path']}")
            if len(ex["audio_sha256"]) != 64:
                failures.append(f"FATAL: {uid} audio_sha256 is not 64 chars")

        if failures:
            _write_summary(args.summary, evidence)
            print(f"T2.3b FAILED: {failures}")
            return 1

        # --- Write reserved_public_demo_examples.yaml ---
        sources_cfg = yaml.safe_load(pathlib.Path(args.sources_config).read_text())
        dataset_version_before = "librispeech_devclean_v1_exclpending_sha256_bacd6f7ba89c"

        reserved_doc = {
            "status": "reserved_for_public_demo",
            "reserved_by": "training_datamove1",
            "reserved_for_future_demo_task": "B6.2",
            "source_manifest": args.manifest,
            "dataset_version_before_exclusion": dataset_version_before,
            "selection_policy": {
                "rule": "one_per_speaker_deterministic_sort",
                "criteria": {
                    "split": "dev-clean",
                    "duration_seconds_min": 3.0,
                    "duration_seconds_max": 10.0,
                    "transcript_non_empty": True,
                    "sample_rate": 16000,
                },
                "sort_key": ["speaker_id", "utterance_id"],
                "max_examples": 10,
                "tiebreaker": "first_qualifying_utterance_per_speaker_sorted_by_speaker_id",
            },
            "examples": selected_examples,
        }

        out_reserved.parent.mkdir(parents=True, exist_ok=True)
        with out_reserved.open("w", encoding="utf-8") as fh:
            yaml.dump(reserved_doc, fh, default_flow_style=False, allow_unicode=True,
                      sort_keys=False)

        print(f"Written: {args.out_reserved}")
        print("PHASE A: reserve_phase_success: true")

    # Capture IDs and hashes for evidence and phase B
    reserved_data = yaml.safe_load(out_reserved.read_text())
    excluded_ids = [ex["utterance_id"] for ex in reserved_data["examples"]]
    excluded_hashes = [ex["audio_sha256"] for ex in reserved_data["examples"]]

    evidence["selected_utterance_ids"] = excluded_ids
    evidence["selected_audio_sha256"] = excluded_hashes
    evidence["reserve_phase_success"] = True
    evidence["reserved_examples_config"] = args.out_reserved

    # -----------------------------------------------------------------------
    # PHASE B — Update public_examples_excluded.yaml to status: complete
    # -----------------------------------------------------------------------
    print("=== PHASE B: Updating exclusion config ===")

    exclusion_doc = {
        "status": "complete",
        "source_manifest": args.manifest,
        "filtered_manifest": FILTERED_MANIFEST_PATH,
        "filled_by": "training_datamove1_reserved_demo_examples",
        "filled_for_future_demo_task": "B6.2",
        "excluded_ids": excluded_ids,
        "excluded_audio_sha256": excluded_hashes,
        "t3_blocked_while_pending": False,
        "rerun_required_after_b6_2": False,
        "notes": (
            "Reserved 10 public demo examples selected deterministically from dev-clean "
            "manifest by training_datamove1 (T2.3b). B6.2 must consume this reserved set "
            "from configs/training/reserved_public_demo_examples.yaml rather than selecting "
            "independently. Selection rule: one per speaker, sort by (speaker_id, "
            "utterance_id), first 10 speakers, duration 3-10s, sample_rate 16000, "
            "non-empty transcript."
        ),
    }

    with excl_config_path.open("w", encoding="utf-8") as fh:
        yaml.dump(exclusion_doc, fh, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)

    # Verify written file
    written = yaml.safe_load(excl_config_path.read_text())
    phase_b_ok = (
        written.get("status") == "complete"
        and len(written.get("excluded_ids", [])) == 10
        and len(written.get("excluded_audio_sha256", [])) == 10
        and written.get("t3_blocked_while_pending") is False
    )

    if not phase_b_ok:
        failures.append(
            f"FATAL: exclusion config verification failed after write. "
            f"status={written.get('status')}, "
            f"excluded_ids count={len(written.get('excluded_ids', []))}, "
            f"excluded_audio_sha256 count={len(written.get('excluded_audio_sha256', []))}"
        )
        evidence["all_failures"] = failures
        _write_summary(args.summary, evidence)
        print(f"T2.3b FAILED: {failures}")
        return 1

    print(f"Written: {args.exclusion_config}")
    print(f"  status: {written['status']}")
    print(f"  excluded_ids count: {len(written['excluded_ids'])}")
    print(f"  excluded_audio_sha256 count: {len(written['excluded_audio_sha256'])}")
    print(f"  t3_blocked_while_pending: {written['t3_blocked_while_pending']}")
    print("PHASE B: exclusion_config_update_success: true")

    # --- Final evidence ---
    evidence["exclusion_config_update_success"] = True
    evidence["success"] = True
    evidence["all_failures"] = []
    _write_summary(args.summary, evidence)

    print()
    print(f"reserved_examples_config : {args.out_reserved}")
    print(f"exclusion_config         : {args.exclusion_config}")
    print(f"summary_artifact         : {args.summary}")
    print()
    print("RESERVE AND EXCLUSION UPDATE COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
