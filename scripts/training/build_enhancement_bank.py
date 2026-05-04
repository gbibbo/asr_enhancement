"""T4.2c: Build the MetricGAN+ enhancement bank for all degraded records.

Reads the degraded manifest, loads SpectralMaskEnhancement ONCE per process,
enhances each record, writes enhanced WAVs to the audio root, and produces an
enhanced JSONL manifest for T4.2d Whisper evaluation.

Heavy imports (torch, torchaudio, speechbrain) are deferred to main() so the
module can be syntax-checked and imported without those libraries installed.

Usage (smoke — 5 per family = 25 records):
  python3 -s scripts/training/build_enhancement_bank.py \\
    --manifest     $TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl \\
    --audio-root   $TRAIN_ROOT/runs/t4_2c_enhance_smoke_<JID>/enhanced_audio \\
    --out-manifest $TRAIN_ROOT/runs/t4_2c_enhance_smoke_<JID>/enhanced_manifest_smoke.jsonl \\
    --out-dir      $TRAIN_ROOT/runs/t4_2c_enhance_smoke_<JID> \\
    --mode         smoke \\
    --max-records-per-family 5

Usage (full — 13 465 records, input manifest order preserved):
  python3 -s scripts/training/build_enhancement_bank.py \\
    --manifest     $TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl \\
    --audio-root   $TRAIN_ROOT/datasets/enhanced/metricgan_plus_pretrained/enhancement_v1 \\
    --out-manifest $TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl \\
    --out-dir      $TRAIN_ROOT/runs/t4_2c_enhance_full_<JID> \\
    --mode         full
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys
import time


EXPECTED_DEGRADED_MANIFEST_SHA256 = (
    "c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c"
)
EXPECTED_DEGRADED_MANIFEST_RECORDS = 13465
EXPECTED_DATASET_VERSION = "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8"
EXPECTED_DEGRADATION_VERSION = "degradation_v1"
EXPECTED_FAMILIES = frozenset(
    {"broadband_hiss", "cafe_background", "far_field_room", "muffled", "phone_call"}
)
EXPECTED_PER_FAMILY_COUNT = 2693
ENHANCER_VERSION = "metricgan_plus_pretrained"
ENHANCEMENT_VERSION = "enhancement_v1"


def _sha256_of_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _git_commit() -> str:
    return os.environ.get("GIT_COMMIT_AT_RUN", "unknown")


def _validate_wav(path: pathlib.Path, input_duration: float) -> dict:
    import soundfile as sf  # lazy; available from PREFIX inside Apptainer
    info = sf.info(str(path))
    dur = info.frames / info.samplerate if info.samplerate else 0.0
    in_range = (
        (input_duration * 0.9 <= dur <= input_duration * 1.1)
        if input_duration > 0.0
        else True
    )
    return {
        "frames": info.frames,
        "samplerate": info.samplerate,
        "channels": info.channels,
        "duration_seconds": round(dur, 4),
        "frames_nonzero": info.frames > 0,
        "samplerate_16khz": info.samplerate == 16000,
        "channels_mono": info.channels == 1,
        "duration_in_range": in_range,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build MetricGAN+ enhancement bank from degraded manifest."
    )
    p.add_argument("--manifest", type=pathlib.Path, required=True,
                   help="Path to degraded manifest JSONL.")
    p.add_argument("--audio-root", type=pathlib.Path, required=True,
                   help="Root directory for enhanced WAV files (<family>/<utterance_id>.wav).")
    p.add_argument("--out-manifest", type=pathlib.Path, required=True,
                   help="Path for the enhanced manifest JSONL (written atomically).")
    p.add_argument("--out-dir", type=pathlib.Path, required=True,
                   help="Run directory for run_summary.json and failures.jsonl.")
    p.add_argument("--mode", choices=["smoke", "full"], default="full",
                   help="smoke selects --max-records-per-family per family; full processes all records.")
    p.add_argument("--max-records-per-family", type=int, default=5,
                   help="Records per family in smoke mode (default: 5).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    jobid = os.environ.get("SLURM_JOB_ID", "local")
    ts = datetime.datetime.utcnow

    print("=== T4.2c: MetricGAN+ enhancement bank ===")
    print(f"Mode          : {args.mode}")
    print(f"Job ID        : {jobid}")
    print(f"Git commit    : {_git_commit()}")
    print(f"Manifest      : {args.manifest}")
    print(f"Audio root    : {args.audio_root}")
    print(f"Out manifest  : {args.out_manifest}")
    print(f"Out dir       : {args.out_dir}")
    print(f"Date          : {ts().isoformat()}Z")
    print()

    # ------------------------------------------------------------------
    # Step 1: Validate input manifest.
    # ------------------------------------------------------------------
    print("--- Step 1: validate input manifest ---")
    if not args.manifest.exists():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    manifest_bytes = args.manifest.read_bytes()
    manifest_sha256 = _sha256_of_bytes(manifest_bytes)
    if manifest_sha256 != EXPECTED_DEGRADED_MANIFEST_SHA256:
        print("ERROR: manifest SHA-256 mismatch", file=sys.stderr)
        print(f"  expected: {EXPECTED_DEGRADED_MANIFEST_SHA256}", file=sys.stderr)
        print(f"  actual  : {manifest_sha256}", file=sys.stderr)
        return 1
    print(f"OK: manifest SHA-256 verified: {manifest_sha256}")

    records: list[dict] = []
    for lineno, raw_line in enumerate(manifest_bytes.decode("utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            print(f"ERROR: manifest parse error at line {lineno}: {exc}", file=sys.stderr)
            return 1

    if args.mode == "full" and len(records) != EXPECTED_DEGRADED_MANIFEST_RECORDS:
        print(
            f"ERROR: expected {EXPECTED_DEGRADED_MANIFEST_RECORDS} records, "
            f"got {len(records)}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: manifest records loaded: {len(records)}")

    # Spot-check first record's version fields.
    if records:
        first = records[0]
        dv = first.get("dataset_version", "")
        dgv = first.get("degradation_version", "")
        if dv and dv != EXPECTED_DATASET_VERSION:
            print(
                f"ERROR: dataset_version mismatch: {dv!r} != {EXPECTED_DATASET_VERSION!r}",
                file=sys.stderr,
            )
            return 1
        if dgv and dgv != EXPECTED_DEGRADATION_VERSION:
            print(
                f"ERROR: degradation_version mismatch: {dgv!r} != {EXPECTED_DEGRADATION_VERSION!r}",
                file=sys.stderr,
            )
            return 1

    families_seen = {r.get("family", "") for r in records}
    missing_families = EXPECTED_FAMILIES - families_seen
    if missing_families:
        print(f"ERROR: missing families in manifest: {sorted(missing_families)}", file=sys.stderr)
        return 1
    print(f"OK: families present: {sorted(families_seen & EXPECTED_FAMILIES)}")

    # ------------------------------------------------------------------
    # Step 2: Determine processing set.
    # ------------------------------------------------------------------
    print()
    print("--- Step 2: determine processing set ---")

    if args.mode == "smoke":
        max_per_fam = args.max_records_per_family
        fam_counts: dict[str, int] = {}
        processing_set: list[dict] = []
        for r in records:
            fam = r.get("family", "")
            if fam_counts.get(fam, 0) < max_per_fam:
                processing_set.append(r)
                fam_counts[fam] = fam_counts.get(fam, 0) + 1
        print(f"Smoke mode: {len(processing_set)} records (up to {max_per_fam} per family)")
        print(f"Per-family selected: { {f: fam_counts.get(f, 0) for f in EXPECTED_FAMILIES} }")
    else:
        # Full mode: preserve exact input manifest order.
        processing_set = records
        print(f"Full mode: {len(processing_set)} records (input manifest order preserved)")

    # ------------------------------------------------------------------
    # Step 3: Load SpeechBrain model ONCE.
    # ------------------------------------------------------------------
    print()
    print("--- Step 3: load SpeechBrain model ---")

    import torch
    import torchaudio
    from speechbrain.inference.enhancement import SpectralMaskEnhancement

    cache_root = os.environ.get("ASR_CACHE_ROOT")
    if cache_root:
        savedir = pathlib.Path(cache_root) / "speechbrain" / "metricgan_plus_voicebank"
    else:
        savedir = args.out_dir / "_speechbrain_savedir"

    savedir.mkdir(parents=True, exist_ok=True)
    print(f"SpeechBrain savedir : {savedir}")

    t_load_start = time.monotonic()
    model = SpectralMaskEnhancement.from_hparams(
        source="speechbrain/metricgan-plus-voicebank",
        savedir=str(savedir),
    )
    t_load_end = time.monotonic()
    print(f"OK: model loaded in {t_load_end - t_load_start:.1f}s")

    # ------------------------------------------------------------------
    # Step 4: Process records.
    # ------------------------------------------------------------------
    print()
    print(f"--- Step 4: enhance {len(processing_set)} records ---")

    args.audio_root.mkdir(parents=True, exist_ok=True)
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)

    enhanced_records: list[dict] = []
    failures: list[dict] = []
    skipped_count = 0
    newly_enhanced_count = 0
    failure_count = 0

    t_proc_start = time.monotonic()

    for idx, rec in enumerate(processing_set):
        utterance_id = rec.get("utterance_id", f"unknown_{idx}")
        family = rec.get("family", "unknown")
        input_path = pathlib.Path(rec["degraded_audio_path"])
        input_duration = float(rec.get("duration_seconds", 0.0))

        out_wav = args.audio_root / family / f"{utterance_id}.wav"
        out_wav.parent.mkdir(parents=True, exist_ok=True)

        # Resume check: only in full mode. Smoke always re-enhances for isolation.
        if args.mode == "full" and out_wav.exists():
            try:
                wav_info = _validate_wav(out_wav, input_duration)
                if (
                    wav_info["frames_nonzero"]
                    and wav_info["samplerate_16khz"]
                    and wav_info["channels_mono"]
                ):
                    sha256 = _sha256_of_file(out_wav)
                    enhanced_records.append({
                        **rec,
                        "enhanced_audio_path": str(out_wav),
                        "enhanced_audio_sha256": sha256,
                        "enhanced": True,
                        "enhancement_fallback": False,
                        "enhancer_version": ENHANCER_VERSION,
                        "enhancement_version": ENHANCEMENT_VERSION,
                        "enhancement_run_id": jobid,
                    })
                    skipped_count += 1
                    if (idx + 1) % 1000 == 0:
                        el = time.monotonic() - t_proc_start
                        rate = (idx + 1) / el if el > 0 else 0.0
                        print(
                            f"  [{idx+1}/{len(processing_set)}] "
                            f"skip={skipped_count} new={newly_enhanced_count} "
                            f"fail={failure_count} {rate:.2f} rec/s"
                        )
                    continue
                # Invalid existing WAV: fall through to re-enhance.
            except Exception:
                pass  # Unreadable WAV: fall through to re-enhance.

        # Enhance this record.
        try:
            if not input_path.exists():
                raise FileNotFoundError(f"input WAV not found: {input_path}")

            waveform, sr = torchaudio.load(str(input_path))
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000)
                waveform = resampler(waveform)
                sr = 16000

            with torch.no_grad():
                lengths = torch.tensor([1.0])
                enhanced_wav = model.enhance_batch(waveform, lengths=lengths)

            if enhanced_wav.dim() == 1:
                enhanced_wav = enhanced_wav.unsqueeze(0)

            torchaudio.save(
                str(out_wav),
                enhanced_wav.cpu(),
                16000,
                encoding="PCM_S",
                bits_per_sample=16,
            )

            wav_info = _validate_wav(out_wav, input_duration)
            bad_checks = [
                k for k in ("frames_nonzero", "samplerate_16khz", "channels_mono")
                if not wav_info[k]
            ]
            if bad_checks:
                raise RuntimeError(f"output WAV failed checks: {bad_checks}")

            sha256 = _sha256_of_file(out_wav)
            enhanced_records.append({
                **rec,
                "enhanced_audio_path": str(out_wav),
                "enhanced_audio_sha256": sha256,
                "enhanced": True,
                "enhancement_fallback": False,
                "enhancer_version": ENHANCER_VERSION,
                "enhancement_version": ENHANCEMENT_VERSION,
                "enhancement_run_id": jobid,
            })
            newly_enhanced_count += 1

        except Exception as exc:
            failure_count += 1
            failures.append({
                "utterance_id": utterance_id,
                "family": family,
                "error": str(exc),
                "input_path": str(input_path),
            })
            print(f"  FAIL [{idx+1}] {utterance_id} ({family}): {exc}", file=sys.stderr)

        if (idx + 1) % 500 == 0 or idx < 5:
            el = time.monotonic() - t_proc_start
            rate = (idx + 1) / el if el > 0 else 0.0
            print(
                f"  [{idx+1}/{len(processing_set)}] "
                f"skip={skipped_count} new={newly_enhanced_count} "
                f"fail={failure_count} {rate:.2f} rec/s"
            )

    t_proc_end = time.monotonic()
    processing_seconds = t_proc_end - t_proc_start
    enhanced_count = skipped_count + newly_enhanced_count

    print()
    print(
        f"Processing complete: total={enhanced_count} skip={skipped_count} "
        f"new={newly_enhanced_count} fail={failure_count} "
        f"elapsed={processing_seconds:.1f}s"
    )

    # ------------------------------------------------------------------
    # Step 5: Post-processing count validation (full mode only).
    # ------------------------------------------------------------------
    print()
    print("--- Step 5: post-processing validation ---")

    per_family_counts: dict[str, int] = {}
    for r in enhanced_records:
        fam = r.get("family", "unknown")
        per_family_counts[fam] = per_family_counts.get(fam, 0) + 1
    print(f"Per-family counts: {per_family_counts}")

    if args.mode == "full":
        count_errors: list[str] = []
        if enhanced_count != EXPECTED_DEGRADED_MANIFEST_RECORDS:
            count_errors.append(
                f"enhanced_count={enhanced_count} != {EXPECTED_DEGRADED_MANIFEST_RECORDS}"
            )
        for fam in sorted(EXPECTED_FAMILIES):
            got = per_family_counts.get(fam, 0)
            if got != EXPECTED_PER_FAMILY_COUNT:
                count_errors.append(
                    f"per_family_counts[{fam}]={got} != {EXPECTED_PER_FAMILY_COUNT}"
                )
        if count_errors:
            print("ERROR: count validation failed:", file=sys.stderr)
            for e in count_errors:
                print(f"  {e}", file=sys.stderr)
            failure_count += len(count_errors)

    if failure_count > 0:
        print(f"ERROR: failure_count={failure_count}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Step 6: Write outputs.
    # ------------------------------------------------------------------
    print()
    print("--- Step 6: write outputs ---")

    failures_path = args.out_dir / "failures.jsonl"
    with failures_path.open("w") as fh:
        for f_rec in failures:
            fh.write(json.dumps(f_rec) + "\n")
    print(f"Failures written : {failures_path} ({len(failures)} entries)")

    # Atomic write: .tmp then os.replace.
    manifest_tmp = pathlib.Path(str(args.out_manifest) + ".tmp")
    manifest_tmp.parent.mkdir(parents=True, exist_ok=True)
    with manifest_tmp.open("w") as fh:
        for r in enhanced_records:
            fh.write(json.dumps(r) + "\n")
    os.replace(str(manifest_tmp), str(args.out_manifest))

    enhanced_manifest_sha256 = _sha256_of_file(args.out_manifest)
    enhanced_manifest_records = len(enhanced_records)
    print(f"Enhanced manifest: {args.out_manifest}")
    print(f"  records : {enhanced_manifest_records}")
    print(f"  sha256  : {enhanced_manifest_sha256}")

    validation_passed = failure_count == 0
    summary = {
        "job_id": jobid,
        "git_commit_at_run": _git_commit(),
        "mode": args.mode,
        "manifest": str(args.manifest),
        "manifest_sha256": manifest_sha256,
        "audio_root": str(args.audio_root),
        "out_manifest": str(args.out_manifest),
        "enhanced_manifest_sha256": enhanced_manifest_sha256,
        "enhanced_manifest_records": enhanced_manifest_records,
        "processing_set_count": len(processing_set),
        "enhanced_count": enhanced_count,
        "skipped_count": skipped_count,
        "newly_enhanced_count": newly_enhanced_count,
        "failure_count": failure_count,
        "per_family_counts": per_family_counts,
        "model_load_seconds": round(t_load_end - t_load_start, 2),
        "processing_seconds": round(processing_seconds, 2),
        "enhancer_version": ENHANCER_VERSION,
        "enhancement_version": ENHANCEMENT_VERSION,
        "speechbrain_savedir": str(savedir),
        "validation_passed": validation_passed,
        "timestamp_utc": ts().isoformat() + "Z",
    }
    summary_path = args.out_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"Run summary      : {summary_path}")

    print()
    print("=== T4.2c enhancement bank complete ===")
    print(f"enhanced_count    : {enhanced_count}")
    print(f"failure_count     : {failure_count}")
    print(f"validation_passed : {validation_passed}")
    print(f"Date              : {ts().isoformat()}Z")

    return 0 if validation_passed else 1


if __name__ == "__main__":
    sys.exit(main())
