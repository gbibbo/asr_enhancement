from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root is on sys.path when running this script directly.
# __file__ is .../scripts/demo/materialize_demo_examples.py; parents[2] = repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import soundfile as sf

from libs.audio.degradations import apply_degradation
from libs.audio.metrics import compute_metrics
from libs.asr.whisper_provider import WhisperAdapter

_DEGRADATION_IDS: list[str] = [
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
]
_DOWNLOAD_URL = "https://www.openslr.org/resources/12/dev-clean.tar.gz"
_ASR_PASS_THRESHOLD = 0.01
_DURATION_TOLERANCE = 0.5
_EXPECTED_SAMPLE_RATE = 16000
_TITLE_MAX_LEN = 60


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Materialize public demo examples and verify ASR drop.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Main mode  (requires --source-dir or --allow-download):\n"
            "  materialize_demo_examples.py --source-dir /path/to/flac\n"
            "  materialize_demo_examples.py --allow-download\n\n"
            "ASR-only mode (no FLAC sourcing):\n"
            "  materialize_demo_examples.py --asr-only"
        ),
    )
    p.add_argument("--asr-only", action="store_true",
                   help="Skip materialization; only run ASR drop check and write reports")
    source = p.add_mutually_exclusive_group()
    source.add_argument("--source-dir", type=Path, metavar="PATH",
                        help="Path containing the 10 LibriSpeech FLAC files")
    source.add_argument("--allow-download", action="store_true",
                        help="Download dev-clean.tar.gz (~337 MB) from OpenSLR")
    p.add_argument("--candidates-config", type=Path,
                   default=Path("config/demo_example_candidates.json"),
                   metavar="PATH",
                   help="Path to demo_example_candidates.json (default: config/demo_example_candidates.json)")
    p.add_argument("--output", type=Path,
                   default=Path("config/demo_examples.json"),
                   metavar="PATH",
                   help="Where to write demo_examples.json (default: config/demo_examples.json)")
    p.add_argument("--examples-config", type=Path,
                   default=Path("config/demo_examples.json"),
                   metavar="PATH",
                   help="Path to demo_examples.json for --asr-only (default: config/demo_examples.json)")
    p.add_argument("--reports-dir", type=Path,
                   default=Path("reports/demo"),
                   metavar="PATH",
                   help="Where to write ASR drop reports (default: reports/demo)")
    p.add_argument("--run-asr", action="store_true",
                   help="Also run ASR drop verification after materialization")
    p.add_argument("--keep-archive", action="store_true",
                   help="Do not delete dev-clean.tar.gz after extraction")
    args = p.parse_args()

    if not args.asr_only and not args.source_dir and not args.allow_download:
        print(
            "Error: no audio source specified.\n"
            "  --source-dir PATH   use a local path containing the 10 FLAC files\n"
            "  --allow-download    download dev-clean.tar.gz (~337 MB) from OpenSLR",
            file=sys.stderr,
        )
        sys.exit(1)

    return args


def _load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _locate_flac(source_dir: Path, candidate: dict) -> Path:
    """Locate FLAC using standard layout first, then recursive search."""
    standard = source_dir / candidate["source_audio_relpath"]
    if standard.is_file():
        return standard

    recording_id = candidate["source_recording_id"]
    matches = list(source_dir.rglob(f"{recording_id}.flac"))
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        print(
            f"ERROR: FLAC not found for example_id={candidate['example_id']}, "
            f"source_recording_id={recording_id}\n"
            f"  Searched: {source_dir}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(
        f"ERROR: Multiple FLAC matches for {recording_id}:",
        file=sys.stderr,
    )
    for m in matches:
        print(f"  {m}", file=sys.stderr)
    sys.exit(1)


def _verify_sha256(flac_path: Path, candidate: dict) -> None:
    expected = candidate["audio_sha256"]
    actual = _sha256(flac_path)
    if actual != expected:
        print(
            f"ERROR: SHA256 mismatch for example_id={candidate['example_id']}\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}",
            file=sys.stderr,
        )
        sys.exit(1)


def _validate_wav(path: Path, expected_duration: float) -> bool:
    try:
        info = sf.info(str(path))
        if info.samplerate != _EXPECTED_SAMPLE_RATE:
            return False
        if info.channels != 1:
            return False
        if abs(info.duration - expected_duration) > _DURATION_TOLERANCE:
            return False
        return True
    except Exception:
        return False


def _flac_to_wav(flac_path: Path, wav_path: Path) -> None:
    data, sr = sf.read(str(flac_path), dtype="float64", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    sf.write(str(wav_path), data, sr, subtype="PCM_16")


def _get_artifacts_examples_dir() -> Path:
    runtime_root = Path(
        os.environ.get("DEMO_RUNTIME_ROOT", "/home/gbibbo/asr_enhancement_runtime")
    )
    artifacts_dir_env = os.environ.get("DEMO_ARTIFACTS_DIR", "")
    if artifacts_dir_env and artifacts_dir_env != ".":
        artifacts_dir = Path(artifacts_dir_env)
    else:
        artifacts_dir = runtime_root / "artifacts"
    return artifacts_dir / "examples"


def _materialize_example(
    candidate: dict, flac_path: Path, artifacts_dir: Path
) -> dict[str, object]:
    example_id = candidate["example_id"]
    expected_dur = candidate["duration_seconds"]
    example_dir = artifacts_dir / example_id
    example_dir.mkdir(parents=True, exist_ok=True)

    clean_wav = example_dir / "clean.wav"
    if clean_wav.is_file() and _validate_wav(clean_wav, expected_dur):
        print(f"  clean.wav: skip (valid)")
    else:
        if clean_wav.is_file():
            clean_wav.unlink()
        _flac_to_wav(flac_path, clean_wav)
        print(f"  clean.wav: written")

    for deg_id in _DEGRADATION_IDS:
        deg_wav = example_dir / f"{deg_id}.wav"
        if deg_wav.is_file() and _validate_wav(deg_wav, expected_dur):
            print(f"  {deg_id}.wav: skip (valid)")
        else:
            if deg_wav.is_file():
                deg_wav.unlink()
            apply_degradation(deg_id, clean_wav, example_dir, seed=0)
            print(f"  {deg_id}.wav: written")

    return {
        "clean_audio_path": f"{example_id}/clean.wav",
        "degraded_audio_paths": {d: f"{example_id}/{d}.wav" for d in _DEGRADATION_IDS},
    }


def _download_dev_clean(cache_dir: Path, keep: bool) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_dir / "dev-clean.tar.gz"
    if dest.is_file():
        print(f"Archive already cached at {dest}")
    else:
        print(f"Downloading {_DOWNLOAD_URL} ...")
        urllib.request.urlretrieve(_DOWNLOAD_URL, str(dest))
        print(f"Downloaded to {dest}")
    return dest


def _extract_flacs(archive_path: Path, candidates: list[dict], extract_dir: Path) -> None:
    needed = {c["source_audio_relpath"] for c in candidates}
    prefixed = {f"LibriSpeech/{r}" for r in needed}
    found = set()
    with tarfile.open(archive_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name in prefixed:
                rel = member.name[len("LibriSpeech/"):]
                out_path = extract_dir / rel
                out_path.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(member)
                if src is not None:
                    out_path.write_bytes(src.read())
                    print(f"  Extracted: {rel}")
                    found.add(rel)
    missing = needed - found
    if missing:
        print(f"ERROR: not extracted from archive: {sorted(missing)}", file=sys.stderr)
        sys.exit(1)


def _truncate_title(text: str) -> str:
    if len(text) <= _TITLE_MAX_LEN:
        return text
    truncated = text[:_TITLE_MAX_LEN]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "…"


def _run_asr_verification(
    candidates: list[dict],
    examples: list[dict],
    artifacts_dir: Path,
    reports_dir: Path,
    whisper_cache: Path,
) -> bool:
    print("\nRunning ASR drop verification...")
    adapter = WhisperAdapter(
        model_name="tiny.en",
        model_cache_dir=str(whisper_cache),
    )
    cand_by_id = {c["example_id"]: c for c in candidates}
    results = []
    overall_pass = True

    for ex in examples:
        example_id = ex["example_id"]
        cand = cand_by_id[example_id]
        ground_truth = cand["ground_truth"]
        print(f"  [{example_id}]", end="", flush=True)

        clean_wav = artifacts_dir / ex["clean_audio_path"]
        clean_res = adapter.transcribe(clean_wav, job_id=f"{example_id}-clean")
        clean_m = compute_metrics(clean_res.text, ground_truth)

        deg_results: dict[str, dict] = {}
        example_pass = False
        for deg_id in _DEGRADATION_IDS:
            deg_wav = artifacts_dir / ex["degraded_audio_paths"][deg_id]
            deg_res = adapter.transcribe(deg_wav, job_id=f"{example_id}-{deg_id}")
            deg_m = compute_metrics(deg_res.text, ground_truth)
            drop = (clean_m.word_accuracy or 0.0) - (deg_m.word_accuracy or 0.0)
            passes = drop >= _ASR_PASS_THRESHOLD
            if passes:
                example_pass = True
            deg_results[deg_id] = {
                "hypothesis": deg_res.text,
                "wer": round(deg_m.wer or 0.0, 4),
                "word_accuracy": round(deg_m.word_accuracy or 0.0, 4),
                "drop_vs_clean": round(drop, 4),
                "pass": passes,
            }

        if not example_pass:
            overall_pass = False
        print(f" {'PASS' if example_pass else 'FAIL'}")

        results.append({
            "example_id": example_id,
            "source_recording_id": cand["source_recording_id"],
            "ground_truth": ground_truth,
            "clean": {
                "hypothesis": clean_res.text,
                "wer": round(clean_m.wer or 0.0, 4),
                "word_accuracy": round(clean_m.word_accuracy or 0.0, 4),
            },
            "degradations": deg_results,
            "example_pass": example_pass,
        })

    runtime_root = Path(
        os.environ.get("DEMO_RUNTIME_ROOT", "/home/gbibbo/asr_enhancement_runtime")
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "whisper_model": "tiny.en",
        "model_cache_path": str(whisper_cache),
        "candidates_config": "config/demo_example_candidates.json",
        "examples_config": "config/demo_examples.json",
        "pass_threshold": _ASR_PASS_THRESHOLD,
        "results": results,
        "overall_pass": overall_pass,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "demo_examples_asr_drop.json"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {json_path}")

    md_path = reports_dir / "demo_examples_asr_drop.md"
    _write_md_report(report, md_path)
    print(f"Wrote {md_path}")

    if not overall_pass:
        print(
            f"\nERROR: ASR drop criterion NOT met (threshold >= {_ASR_PASS_THRESHOLD}).",
            file=sys.stderr,
        )
        for r in results:
            if not r["example_pass"]:
                print(
                    f"  example_id={r['example_id']}: no degradation with "
                    f"clean_word_accuracy - degraded_word_accuracy >= {_ASR_PASS_THRESHOLD}",
                    file=sys.stderr,
                )
        return False

    print(f"ASR drop criterion passed for all {len(examples)} examples.")
    return True


def _write_md_report(report: dict, path: Path) -> None:
    lines = [
        "# Demo Examples ASR Drop Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Whisper model: `{report['whisper_model']}`",
        f"- Model cache: `{report['model_cache_path']}`",
        f"- Pass threshold: `clean_word_accuracy - degraded_word_accuracy >= {report['pass_threshold']}`",
        f"- Overall pass: **{report['overall_pass']}**",
        "",
        "| example_id | source_recording_id | clean WA | degradation | deg WA | drop | pass |",
        "|------------|---------------------|----------|-------------|--------|------|------|",
    ]
    for r in report["results"]:
        clean_wa = r["clean"]["word_accuracy"]
        for deg_id, d in r["degradations"].items():
            lines.append(
                f"| {r['example_id']} | {r['source_recording_id']} | {clean_wa:.3f}"
                f" | {deg_id} | {d['word_accuracy']:.3f} | {d['drop_vs_clean']:.3f}"
                f" | {d['pass']} |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = _parse_args()

    candidates = _load_json(args.candidates_config)
    runtime_root = Path(
        os.environ.get("DEMO_RUNTIME_ROOT", "/home/gbibbo/asr_enhancement_runtime")
    )
    artifacts_dir = _get_artifacts_examples_dir()
    whisper_cache = runtime_root / "cache" / "whisper"

    if args.asr_only:
        examples = _load_json(args.examples_config)
        ok = _run_asr_verification(
            candidates, examples, artifacts_dir, args.reports_dir, whisper_cache
        )
        sys.exit(0 if ok else 1)

    # Main mode: source FLACs
    if args.source_dir:
        flac_dir = args.source_dir
    else:
        # --allow-download
        cache_dir = runtime_root / "cache"
        archive = _download_dev_clean(cache_dir, args.keep_archive)
        extract_dir = cache_dir / "dev-clean-extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        print("Extracting 10 FLAC files from archive...")
        _extract_flacs(archive, candidates, extract_dir)
        flac_dir = extract_dir
        if not args.keep_archive:
            archive.unlink()
            print(f"Deleted {archive}")

    print(f"\nMaterializing {len(candidates)} examples into {artifacts_dir}")
    example_configs: list[dict] = []

    for candidate in candidates:
        example_id = candidate["example_id"]
        print(f"\n[{example_id}]")

        flac_path = _locate_flac(flac_dir, candidate)
        print(f"  FLAC: {flac_path}")

        _verify_sha256(flac_path, candidate)
        print(f"  SHA256: OK")

        paths = _materialize_example(candidate, flac_path, artifacts_dir)

        example_configs.append({
            "example_id": example_id,
            "title": _truncate_title(candidate["ground_truth"]),
            "description": f"LibriSpeech dev-clean, speaker {candidate['speaker_id']}",
            "duration_seconds": candidate["duration_seconds"],
            "degradation_ids": list(_DEGRADATION_IDS),
            "ground_truth": candidate["ground_truth"],
            "audio_available": True,
            "clean_audio_path": paths["clean_audio_path"],
            "degraded_audio_paths": paths["degraded_audio_paths"],
        })

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(example_configs, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {output_path}")

    if args.run_asr:
        ok = _run_asr_verification(
            candidates, example_configs, artifacts_dir, args.reports_dir, whisper_cache
        )
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
