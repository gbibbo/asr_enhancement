"""T3.2a: Build the degradation bank for the degraded-audio Whisper baseline.

Reads the filtered LibriSpeech manifest (2693 dev-clean records) and applies the
five degradation_v1 families to each record. Audio is written first to a per-job
staging tree; only after all validation passes is the staging tree atomically
promoted to the final tree. The degraded manifest stores the FINAL paths so
T3.2 can read it directly post-promotion.

Usage:
  python3 -s scripts/training/build_degradation_bank.py \\
    --manifest                <filtered manifest JSONL> \\
    --exclusion-config        configs/training/public_examples_excluded.yaml \\
    --dataset-version-config  configs/training/dataset_version.yaml \\
    --mode                    smoke|full \\
    --staging-audio-root      <per-job staging audio root> \\
    --staging-manifest-tmp    <per-job staging manifest .tmp> \\
    --final-audio-root        <final audio root> \\
    --final-degraded-manifest <final degraded manifest> \\
    --out-dir                 <run dir under scratch> \\
    [--max-records N] [--summary-md PATH] [--validation-sample-size N]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

import numpy as np
import soundfile as sf
import yaml

from libs.audio.degradations import (
    DEGRADATION_FAMILIES,
    DEGRADATION_PARAMS,
    DEGRADATION_VERSION,
    apply_degradation,
    utterance_seed,
)


EXPECTED_DATASET_VERSION = "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8"
EXPECTED_MANIFEST_RECORDS = 2693
EXPECTED_MANIFEST_SHA256 = (
    "dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b"
)
EXPECTED_SR = 16000
TARGET_PEAK_TOLERANCE = 0.95001

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

FAMILY_ORDER = [
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
]  # alphabetical for deterministic iteration


def _git_rev_parse_head() -> str:
    val = os.environ.get("GIT_COMMIT_AT_RUN", "")
    if val:
        return val
    return "unknown"


def _git_status_short() -> str:
    val = os.environ.get("GIT_STATUS_SHORT_AT_RUN", None)
    if val is not None:
        return val
    return ""


def _sha256_of_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def _count_lines(path: pathlib.Path) -> int:
    n = 0
    with path.open("r", encoding="utf-8") as fh:
        for _ in fh:
            n += 1
    return n


def main() -> int:
    p = argparse.ArgumentParser(description="T3.2a degradation bank builder")
    p.add_argument("--manifest", required=True)
    p.add_argument("--exclusion-config", required=True)
    p.add_argument("--dataset-version-config", required=True)
    p.add_argument("--mode", required=True, choices=["smoke", "full"])
    p.add_argument("--staging-audio-root", required=True)
    p.add_argument("--staging-manifest-tmp", required=True)
    p.add_argument("--final-audio-root", required=True)
    p.add_argument("--final-degraded-manifest", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--max-records", type=int, default=None)
    p.add_argument("--summary-md", default=None)
    p.add_argument("--validation-sample-size", type=int, default=50)
    args = p.parse_args()

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    staging_audio_root = pathlib.Path(args.staging_audio_root)
    staging_manifest_tmp = pathlib.Path(args.staging_manifest_tmp)
    final_audio_root = pathlib.Path(args.final_audio_root)
    final_manifest = pathlib.Path(args.final_degraded_manifest)
    failures_path = out_dir / "failures.jsonl"
    file_sha256_tsv = out_dir / "file_sha256.tsv"
    config_snapshot_path = out_dir / "config_snapshot.json"
    generation_summary_path = out_dir / "generation_summary.json"
    run_summary_md_path = out_dir / "run_summary.md"

    slurm_job_id = os.environ.get("SLURM_JOB_ID", "local")
    timestamp_utc = datetime.datetime.utcnow().isoformat() + "Z"

    # ------------------------------------------------------------------
    # Pre-flight checks
    # ------------------------------------------------------------------
    excl_path = pathlib.Path(args.exclusion_config)
    if not excl_path.exists():
        print(f"BLOCKER: exclusion config not found: {excl_path}")
        return 1
    excl_cfg = yaml.safe_load(excl_path.read_text())
    if excl_cfg.get("status") != "complete":
        print(
            f"BLOCKER: public_examples_excluded.yaml status is {excl_cfg.get('status')!r}, expected 'complete'"
        )
        return 1

    dv_path = pathlib.Path(args.dataset_version_config)
    dv_cfg = yaml.safe_load(dv_path.read_text())
    if dv_cfg.get("dataset_version") != EXPECTED_DATASET_VERSION:
        print(
            f"BLOCKER: dataset_version mismatch: got {dv_cfg.get('dataset_version')!r}, "
            f"expected {EXPECTED_DATASET_VERSION!r}"
        )
        return 1

    manifest_path = pathlib.Path(args.manifest)
    if not manifest_path.exists():
        print(f"BLOCKER: manifest not found: {manifest_path}")
        return 1
    manifest_bytes = manifest_path.read_bytes()
    manifest_sha256 = _sha256_of_bytes(manifest_bytes)
    if manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        print(
            f"BLOCKER: source manifest SHA-256 mismatch: got {manifest_sha256}, "
            f"expected {EXPECTED_MANIFEST_SHA256}"
        )
        return 1
    total_manifest_records = manifest_bytes.count(b"\n")
    if not manifest_bytes.endswith(b"\n"):
        total_manifest_records += 1
    if total_manifest_records != EXPECTED_MANIFEST_RECORDS:
        print(
            f"BLOCKER: manifest line count is {total_manifest_records}, "
            f"expected {EXPECTED_MANIFEST_RECORDS}"
        )
        return 1

    records: list[dict] = []
    for lineno, line in enumerate(manifest_bytes.decode("utf-8").splitlines(), 1):
        rec = json.loads(line)
        uid = rec.get("utterance_id", "")
        if uid in RESERVED_IDS:
            print(f"BLOCKER: reserved demo example found in manifest: {uid}")
            return 1
        if rec.get("sample_rate") != EXPECTED_SR:
            print(
                f"BLOCKER: record {uid!r} has sample_rate={rec.get('sample_rate')!r}, expected {EXPECTED_SR}"
            )
            return 1
        records.append(rec)

    if DEGRADATION_VERSION != "degradation_v1":
        print(f"BLOCKER: DEGRADATION_VERSION={DEGRADATION_VERSION!r}, expected 'degradation_v1'")
        return 1
    expected_families = {
        "broadband_hiss",
        "cafe_background",
        "far_field_room",
        "muffled",
        "phone_call",
    }
    if set(DEGRADATION_FAMILIES) != expected_families:
        print(
            f"BLOCKER: DEGRADATION_FAMILIES mismatch: {set(DEGRADATION_FAMILIES)} != {expected_families}"
        )
        return 1

    # Final and staging targets must be absent
    if final_audio_root.exists():
        print(f"BLOCKER: stale final output exists at {final_audio_root}")
        return 1
    if final_manifest.exists():
        print(f"BLOCKER: stale final output exists at {final_manifest}")
        return 1
    if staging_audio_root.exists():
        print(f"BLOCKER: stale staging output at {staging_audio_root}")
        return 1
    if staging_manifest_tmp.exists():
        print(f"BLOCKER: stale staging output at {staging_manifest_tmp}")
        return 1

    # Determine processed record set
    if args.max_records is not None:
        records_to_process = records[: args.max_records]
    else:
        records_to_process = records
    expected_files = len(records_to_process) * len(expected_families)

    # Disk space check
    total_seconds = sum(float(r.get("duration_seconds", 0.0)) for r in records_to_process)
    expected_total_bytes = int(len(expected_families) * total_seconds * EXPECTED_SR * 2)
    parent = staging_audio_root.parent
    parent.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(parent).free
    required_bytes = max(2 * expected_total_bytes, 100 * 1024 * 1024)  # 100 MiB floor
    if free_bytes < required_bytes:
        print(
            f"BLOCKER: insufficient disk: free={free_bytes} required={required_bytes} "
            f"(2x estimated {expected_total_bytes})"
        )
        return 1

    # df -h logging (best effort)
    try:
        df_out = subprocess.check_output(["df", "-h", str(parent)], text=True)
    except Exception as exc:
        df_out = f"df failed: {exc}"

    print("PRE-FLIGHT OK")
    print(f"  manifest records:           {total_manifest_records}")
    print(f"  manifest sha256:            {manifest_sha256}")
    print(f"  dataset_version:            {EXPECTED_DATASET_VERSION}")
    print(f"  exclusion status:           complete")
    print(f"  DEGRADATION_VERSION:        {DEGRADATION_VERSION}")
    print(f"  mode:                       {args.mode}")
    print(f"  records to process:         {len(records_to_process)}")
    print(f"  expected output files:      {expected_files}")
    print(f"  staging audio root:         {staging_audio_root}")
    print(f"  staging manifest tmp:       {staging_manifest_tmp}")
    print(f"  final audio root:           {final_audio_root}")
    print(f"  final degraded manifest:    {final_manifest}")
    print(f"  estimated bytes:            {expected_total_bytes}")
    print(f"  available bytes (parent):   {free_bytes}")
    print(f"  out_dir:                    {out_dir}")
    print(f"  slurm_job_id:               {slurm_job_id}")
    print(f"  df -h (parent):\n{df_out}")

    # Snapshot config
    _write_json(
        config_snapshot_path,
        {
            "manifest": str(manifest_path),
            "exclusion_config": str(excl_path),
            "dataset_version_config": str(dv_path),
            "mode": args.mode,
            "staging_audio_root": str(staging_audio_root),
            "staging_manifest_tmp": str(staging_manifest_tmp),
            "final_audio_root": str(final_audio_root),
            "final_degraded_manifest": str(final_manifest),
            "out_dir": str(out_dir),
            "max_records": args.max_records,
            "summary_md": args.summary_md,
            "validation_sample_size": args.validation_sample_size,
            "degradation_version": DEGRADATION_VERSION,
            "dataset_version": EXPECTED_DATASET_VERSION,
            "manifest_sha256": manifest_sha256,
            "manifest_records": total_manifest_records,
            "expected_output_files": expected_files,
            "estimated_bytes": expected_total_bytes,
            "available_bytes": free_bytes,
            "slurm_job_id": slurm_job_id,
            "timestamp_utc": timestamp_utc,
            "degradation_params": DEGRADATION_PARAMS,
        },
    )

    # ------------------------------------------------------------------
    # Generation loop — write to staging only; manifest carries final paths
    # ------------------------------------------------------------------
    staging_audio_root.mkdir(parents=True, exist_ok=False)
    for fam in FAMILY_ORDER:
        (staging_audio_root / fam).mkdir(parents=True, exist_ok=False)

    failure_count = 0
    per_family_counts = {fam: 0 for fam in FAMILY_ORDER}
    file_sha_lines: list[str] = []  # accumulated; written at end (smaller IO)

    t_start = time.monotonic()
    sorted_records = sorted(records_to_process, key=lambda r: r["utterance_id"])

    with staging_manifest_tmp.open("w", encoding="utf-8") as mfh, failures_path.open(
        "w", encoding="utf-8"
    ) as failfh:
        for idx, rec in enumerate(sorted_records):
            uid = rec["utterance_id"]
            clean_path = pathlib.Path(rec["audio_path"])
            try:
                samples, sr = sf.read(clean_path, dtype="float64", always_2d=False)
                if samples.ndim != 1:
                    raise ValueError(f"clean audio is not mono: shape={samples.shape}")
                if sr != EXPECTED_SR:
                    raise ValueError(f"clean audio sample_rate={sr}, expected {EXPECTED_SR}")
            except Exception as exc:
                failure_count += 1
                failfh.write(
                    json.dumps(
                        {"utterance_id": uid, "stage": "read_clean", "error": str(exc)}
                    )
                    + "\n"
                )
                failfh.flush()
                continue

            for fam in FAMILY_ORDER:
                staging_path = staging_audio_root / fam / f"{uid}.wav"
                final_path = final_audio_root / fam / f"{uid}.wav"
                try:
                    processed = apply_degradation(samples, sr, fam, uid)
                    if len(processed) != len(samples):
                        raise AssertionError(
                            f"length contract violated: {len(processed)} != {len(samples)}"
                        )
                    if not np.isfinite(processed).all():
                        raise AssertionError("non-finite output")
                    peak = float(np.max(np.abs(processed)))
                    if peak > TARGET_PEAK_TOLERANCE:
                        raise AssertionError(f"peak {peak} > {TARGET_PEAK_TOLERANCE}")
                    sf.write(staging_path, processed, EXPECTED_SR, subtype="PCM_16")
                    sha = _sha256_of_file(staging_path)
                    seed = utterance_seed(uid, fam)

                    line = {
                        "utterance_id": uid,
                        "family": fam,
                        "split": rec.get("split", ""),
                        "speaker_id": rec.get("speaker_id", ""),
                        "chapter_id": rec.get("chapter_id", ""),
                        "transcript": rec.get("transcript", ""),
                        "duration_seconds": rec.get("duration_seconds", 0.0),
                        "sample_rate": EXPECTED_SR,
                        "clean_audio_path": str(clean_path),
                        "degraded_audio_path": str(final_path),
                        "degraded_audio_sha256": sha,
                        "dataset_version": EXPECTED_DATASET_VERSION,
                        "degradation_version": DEGRADATION_VERSION,
                        "seed": seed,
                    }
                    mfh.write(json.dumps(line) + "\n")
                    mfh.flush()
                    file_sha_lines.append(f"{uid}\t{fam}\t{sha}\n")
                    per_family_counts[fam] += 1
                except Exception as exc:
                    failure_count += 1
                    failfh.write(
                        json.dumps(
                            {
                                "utterance_id": uid,
                                "family": fam,
                                "stage": "apply_degradation_or_write",
                                "error": str(exc),
                            }
                        )
                        + "\n"
                    )
                    failfh.flush()

            if (idx + 1) % 100 == 0 or (idx + 1) == len(sorted_records):
                elapsed = time.monotonic() - t_start
                rate = (idx + 1) / elapsed if elapsed > 0 else 0.0
                print(
                    f"  [{idx + 1}/{len(sorted_records)}] failures={failure_count} "
                    f"rate={rate:.2f} rec/s elapsed={elapsed:.0f}s"
                )

    # Write file_sha256.tsv
    file_sha256_tsv.write_text("".join(file_sha_lines), encoding="utf-8")

    # Strict failure policy
    if failure_count > 0:
        print(f"\nBANK FAILED: failure_count={failure_count}")
        print(f"  staging_audio_root preserved at: {staging_audio_root}")
        print(f"  staging_manifest_tmp preserved at: {staging_manifest_tmp}")
        print(f"  failures.jsonl: {failures_path}")
        return 1

    # ------------------------------------------------------------------
    # Pre-promotion validation against staging
    # ------------------------------------------------------------------
    actual_lines = _count_lines(staging_manifest_tmp)
    if actual_lines != expected_files:
        print(
            f"BLOCKER: staging manifest line count {actual_lines} != expected {expected_files}"
        )
        return 1
    for fam in FAMILY_ORDER:
        if per_family_counts[fam] != len(records_to_process):
            print(
                f"BLOCKER: family {fam} count {per_family_counts[fam]} != {len(records_to_process)}"
            )
            return 1

    # Re-verify source manifest unchanged
    post_sha = _sha256_of_bytes(manifest_path.read_bytes())
    if post_sha != EXPECTED_MANIFEST_SHA256:
        print(f"BLOCKER: source manifest SHA-256 changed during run: {post_sha}")
        return 1

    # Reserved IDs absent in degraded manifest
    grep_failures = []
    with staging_manifest_tmp.open("r", encoding="utf-8") as fh:
        for line in fh:
            for rid in RESERVED_IDS:
                if f'"utterance_id": "{rid}"' in line:
                    grep_failures.append(rid)
    if grep_failures:
        print(f"BLOCKER: reserved IDs found in staging manifest: {grep_failures}")
        return 1

    # Build deterministic validation sample (first N entries by (utterance_id, family) order)
    sample_pairs: list[dict] = []
    seen = 0
    sample_size = args.validation_sample_size
    with staging_manifest_tmp.open("r", encoding="utf-8") as fh:
        manifest_records = [json.loads(ln) for ln in fh]
    manifest_records_sorted = sorted(
        manifest_records, key=lambda r: (r["utterance_id"], r["family"])
    )
    sample = manifest_records_sorted[:sample_size]

    deterministic_validation_sample = []
    for r in sample:
        # Map final -> staging by replacing root prefix
        final_path = pathlib.Path(r["degraded_audio_path"])
        try:
            relative = final_path.relative_to(final_audio_root)
        except ValueError:
            print(
                f"BLOCKER: degraded_audio_path {final_path} is not under final_audio_root {final_audio_root}"
            )
            return 1
        staging_path = staging_audio_root / relative
        if not staging_path.exists():
            print(f"BLOCKER: staging file missing for sample entry: {staging_path}")
            return 1
        # Verify recorded sha matches staging file
        actual_sha = _sha256_of_file(staging_path)
        if actual_sha != r["degraded_audio_sha256"]:
            print(
                f"BLOCKER: sha mismatch for {staging_path}: "
                f"recorded={r['degraded_audio_sha256']} actual={actual_sha}"
            )
            return 1
        # Format check
        info = sf.info(str(staging_path))
        if info.samplerate != EXPECTED_SR or info.channels != 1:
            print(
                f"BLOCKER: format check failed for {staging_path}: "
                f"sr={info.samplerate} channels={info.channels}"
            )
            return 1
        # Length contract check
        expected_frames = int(round(r["duration_seconds"] * EXPECTED_SR))
        if abs(info.frames - expected_frames) > 1:
            print(
                f"BLOCKER: length mismatch for {staging_path}: "
                f"frames={info.frames} expected~{expected_frames}"
            )
            return 1
        # Determinism spot-check via re-application
        clean = pathlib.Path(r["clean_audio_path"])
        sclean, sr_clean = sf.read(clean, dtype="float64", always_2d=False)
        redone = apply_degradation(sclean, sr_clean, r["family"], r["utterance_id"])
        # Write to a temp file, hash, compare
        tmp_repro = out_dir / f"_repro_{r['utterance_id']}_{r['family']}.wav"
        sf.write(tmp_repro, redone, EXPECTED_SR, subtype="PCM_16")
        repro_sha = _sha256_of_file(tmp_repro)
        tmp_repro.unlink(missing_ok=True)
        if repro_sha != actual_sha:
            print(
                f"BLOCKER: determinism spot-check failed for "
                f"{r['utterance_id']}/{r['family']}: recorded={actual_sha} repro={repro_sha}"
            )
            return 1
        deterministic_validation_sample.append(
            {
                "utterance_id": r["utterance_id"],
                "family": r["family"],
                "degraded_audio_sha256": r["degraded_audio_sha256"],
            }
        )

    # ------------------------------------------------------------------
    # Atomic promotion
    # ------------------------------------------------------------------
    final_audio_root.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(staging_audio_root), str(final_audio_root))
    final_manifest.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(staging_manifest_tmp), str(final_manifest))

    # Post-promotion: every degraded_audio_path must exist
    with final_manifest.open("r", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            fp = pathlib.Path(r["degraded_audio_path"])
            if not fp.exists():
                print(f"BLOCKER (post-promotion): missing final file: {fp}")
                return 1

    # Final manifest sha256
    final_manifest_sha256 = _sha256_of_bytes(final_manifest.read_bytes())

    # ------------------------------------------------------------------
    # Write summary outputs
    # ------------------------------------------------------------------
    git_commit = _git_rev_parse_head()
    git_status = _git_status_short()

    summary = {
        "task": "T3.2a",
        "success": True,
        "mode": args.mode,
        "timestamp_utc": timestamp_utc,
        "degradation_version": DEGRADATION_VERSION,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "manifest_path": str(manifest_path),
        "manifest_records": total_manifest_records,
        "manifest_sha256": manifest_sha256,
        "source_manifest_sha256_unchanged": True,
        "processed_records": len(records_to_process),
        "expected_output_files": expected_files,
        "files_generated": expected_files,
        "failure_count": 0,
        "per_family_counts": per_family_counts,
        "final_audio_root": str(final_audio_root),
        "final_degraded_manifest": str(final_manifest),
        "final_degraded_manifest_records": expected_files,
        "final_degraded_manifest_sha256": final_manifest_sha256,
        "file_sha256_tsv": str(file_sha256_tsv),
        "deterministic_validation_sample_size": len(deterministic_validation_sample),
        "deterministic_validation_sample": deterministic_validation_sample,
        "audio_format": "WAV PCM_16, 16 kHz mono",
        "length_contract": "output_samples == input_samples (apply_degradation)",
        "git_commit_at_run": git_commit,
        "git_status_short_at_run": git_status,
        "result_commit": "PENDING_RESULT_COMMIT",
        "slurm_job_id": slurm_job_id,
        "degradation_params": DEGRADATION_PARAMS,
    }
    _write_json(generation_summary_path, summary)

    run_md = (
        f"# T3.2a Run Summary ({args.mode})\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Degradation version | `{DEGRADATION_VERSION}` |\n"
        f"| Dataset version | `{EXPECTED_DATASET_VERSION}` |\n"
        f"| Source manifest SHA-256 | `{manifest_sha256}` |\n"
        f"| Source manifest unchanged | `True` |\n"
        f"| Processed records | {len(records_to_process)} |\n"
        f"| Files generated | {expected_files} |\n"
        f"| Per-family counts | `{per_family_counts}` |\n"
        f"| Failure count | 0 |\n"
        f"| Final audio root | `{final_audio_root}` |\n"
        f"| Final degraded manifest | `{final_manifest}` |\n"
        f"| Final degraded manifest SHA-256 | `{final_manifest_sha256}` |\n"
        f"| Validation sample size | {len(deterministic_validation_sample)} |\n"
        f"| Slurm job ID | `{slurm_job_id}` |\n"
        f"| Git commit at run | `{git_commit}` |\n"
        f"| Result commit | `PENDING_RESULT_COMMIT` |\n"
        f"| Timestamp (UTC) | `{timestamp_utc}` |\n"
    )
    run_summary_md_path.write_text(run_md, encoding="utf-8")

    if args.summary_md:
        summary_md_path = pathlib.Path(args.summary_md)
        summary_md_path.parent.mkdir(parents=True, exist_ok=True)
        body = (
            f"# T3.2a Degradation Bank ({DEGRADATION_VERSION})\n\n"
            f"Status: complete  \n"
            f"Mode: {args.mode}  \n"
            f"Degradation version: `{DEGRADATION_VERSION}`  \n"
            f"Dataset version: `{EXPECTED_DATASET_VERSION}`  \n"
            f"Source manifest records: {total_manifest_records}  \n"
            f"Source manifest SHA-256: `{manifest_sha256}`  \n"
            f"Source manifest SHA-256 unchanged: True  \n"
            f"Degraded files: {expected_files}  \n"
            f"Per-family count: "
            f"`{per_family_counts}`  \n"
            f"Final audio root: `{final_audio_root}`  \n"
            f"Final degraded manifest path: `{final_manifest}`  \n"
            f"Final degraded manifest SHA-256: `{final_manifest_sha256}`  \n"
            f"file_sha256.tsv path: `{file_sha256_tsv}`  \n"
            f"Deterministic validation sample size: {len(deterministic_validation_sample)}  \n"
            f"Audio format: WAV, 16 kHz mono, PCM_16  \n"
            f"Length contract: output_samples == input_samples (apply_degradation)  \n"
            f"Code commit at run: `{git_commit}`  \n"
            f"Result commit: `PENDING_RESULT_COMMIT`  \n"
            f"Slurm job ID: `{slurm_job_id}`  \n"
            f"Date (UTC): `{timestamp_utc}`  \n\n"
            f"## Families and parameters (frozen)\n\n"
            f"| Family | Stochastic | Parameters |\n|---|---|---|\n"
            f"| far_field_room   | yes | IR length 0.8 s (12800 samples), RT60 0.6 s, "
            f"tau = RT60/ln(1000), DRR -6 dB, direct sample at index 0 |\n"
            f"| cafe_background  | yes | Speech-shaped Gaussian (Butterworth bandpass "
            f"200-4000 Hz, order 4), SNR 5 dB |\n"
            f"| phone_call       | no  | Butterworth bandpass 300-3400 Hz order 6 -> "
            f"resample 16->8 kHz -> mu-law G.711 round-trip -> resample 8->16 kHz |\n"
            f"| muffled          | no  | Butterworth lowpass 800 Hz order 4, then -6 dB attenuation |\n"
            f"| broadband_hiss   | yes | Gaussian white noise, SNR 10 dB |\n\n"
            f"All numeric constants are duplicated in `DEGRADATION_PARAMS` in "
            f"`libs/audio/degradations.py`.\n"
        )
        summary_md_path.write_text(body, encoding="utf-8")

    print("\n=== T3.2a COMPLETE ===")
    print(f"  mode:                    {args.mode}")
    print(f"  files_generated:         {expected_files}")
    print(f"  per_family_counts:       {per_family_counts}")
    print(f"  failure_count:           0")
    print(f"  final_audio_root:        {final_audio_root}")
    print(f"  final_degraded_manifest: {final_manifest}")
    print(f"  final_manifest_sha256:   {final_manifest_sha256}")
    print(f"  generation_summary:      {generation_summary_path}")
    if args.summary_md:
        print(f"  summary_md:              {args.summary_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
