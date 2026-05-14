#!/usr/bin/env python3
"""Build the 8-entry public demo manifest for P8.2.

Selects exactly 8 deterministic public demo audio files from the
operator-staged demo reference pool at:
    /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/demo_reference_artifacts/examples/

Writes:
    --out-audio-dir/<unique_name>.wav  (8 files; 16 kHz mono PCM16)
    --out-manifest                       (JSON; exactly 8 entries)

Verifies disjointness from the locked LibriSpeech and degradation_v1
eval manifests by audio_id, speaker_id, and audio_sha256.

Stdout:  OK_DEMO_EXAMPLES with 8 selected.
Exit:    0 PASS, 1 FAIL.

Routing notes (P8.2):
- claims_enabled.ood_real == false, BLOCKED_OOD_PUBLIC active ->
  LibriSpeech-derived public path; --reserved-demo unused.
- Source pool is the demo reference reserve (provisioned by the
  operator and authorized read-only for P8.2 in
  configs/robust_asr/reuse_policy_v1.yaml).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import wave
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pyarrow.parquet as pq
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE_ROOT = Path(
    "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/"
    "demo_reference_artifacts/examples"
)

LOCKED_MANIFESTS = [
    REPO_ROOT / "artifacts/robust_asr/manifests/librispeech_lora_train.parquet",
    REPO_ROOT / "artifacts/robust_asr/manifests/librispeech_router_train.parquet",
    REPO_ROOT / "artifacts/robust_asr/manifests/librispeech_validation.parquet",
    REPO_ROOT / "artifacts/robust_asr/manifests/librispeech_locked_test.parquet",
    REPO_ROOT / "artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet",
    REPO_ROOT / "artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet",
]

# Deterministic 8-entry selection (sorted by speaker_id then family).
# Each tuple: (speaker_id, source_filename, family, tier, notes)
SELECTION: List[Tuple[str, str, str, str, str]] = [
    ("ex001", "clean.wav",          "clean",           "id",
     "Section 4.7 ID family: clean."),
    ("ex003", "cafe_background.wav", "cafe_noise",     "id",
     "Section 4.7 ID family: cafe_noise (cafe_background reference)."),
    ("ex004", "phone_call.wav",     "phone_band",      "id",
     "Section 4.7 ID family: phone_band (phone_call reference)."),
    ("ex007", "far_field_room.wav", "far_field_room",  "id",
     "Section 4.7 ID family: far_field_room."),
    ("ex010", "muffled.wav",        "muffled_lowpass", "id",
     "Section 4.7 ID family: muffled_lowpass (muffled reference)."),
    ("ex001", "broadband_hiss.wav", "broadband_hiss",  "ood_param_illustrative",
     "OOD-param illustrative: broadband_hiss outside Section 3 families; "
     "BLOCKED_OOD_PUBLIC + claims_enabled.ood_real=false. Not used for any "
     "claim; not drawn from common_voice_demo_reserved."),
    ("ex003", "broadband_hiss.wav", "broadband_hiss",  "ood_param_illustrative",
     "OOD-param illustrative: broadband_hiss outside Section 3 families; "
     "BLOCKED_OOD_PUBLIC + claims_enabled.ood_real=false. Not used for any "
     "claim; not drawn from common_voice_demo_reserved."),
    ("ex004", "broadband_hiss.wav", "broadband_hiss",  "ood_param_illustrative",
     "OOD-param illustrative: broadband_hiss outside Section 3 families; "
     "BLOCKED_OOD_PUBLIC + claims_enabled.ood_real=false. Not used for any "
     "claim; not drawn from common_voice_demo_reserved."),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wav_duration_s(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def assert_pcm16_mono_16k(path: Path) -> None:
    with wave.open(str(path), "rb") as w:
        if w.getframerate() != 16000:
            raise SystemExit(f"FAIL: {path} sample_rate {w.getframerate()} != 16000")
        if w.getnchannels() != 1:
            raise SystemExit(f"FAIL: {path} channels {w.getnchannels()} != 1")
        if w.getsampwidth() != 2:
            raise SystemExit(f"FAIL: {path} sampwidth {w.getsampwidth()} != 2 (PCM16)")


def load_locked_index() -> Tuple[Set[str], Set[str], Set[str]]:
    audio_ids: Set[str] = set()
    speaker_ids: Set[str] = set()
    audio_sha256s: Set[str] = set()
    for p in LOCKED_MANIFESTS:
        if not p.exists():
            raise SystemExit(f"FAIL: locked manifest missing: {p}")
        df = pq.read_table(str(p)).to_pandas()
        audio_ids.update(df["audio_id"].astype(str).unique())
        speaker_ids.update(df["speaker_id"].astype(str).unique())
        if "audio_sha256" in df.columns:
            audio_sha256s.update(df["audio_sha256"].astype(str).unique())
    return audio_ids, speaker_ids, audio_sha256s


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eval-manifests", required=True,
                    help="Path to configs/robust_asr/eval_manifests_v1.yaml (read).")
    ap.add_argument("--reference-root", default=str(DEFAULT_REFERENCE_ROOT),
                    help="Operator-staged demo reference reserve root (read).")
    ap.add_argument("--reserved-demo", default=None,
                    help="OOD-real Common Voice reserved demo parquet. "
                         "Required only if claims_enabled.ood_real == true.")
    ap.add_argument("--out-manifest", required=True,
                    help="Output manifest JSON.")
    ap.add_argument("--out-audio-dir", required=True,
                    help="Output audio directory; will contain exactly 8 WAVs.")
    args = ap.parse_args(argv)

    eval_manifests_path = Path(args.eval_manifests).resolve()
    if not eval_manifests_path.exists():
        print(f"FAIL: eval_manifests yaml missing: {eval_manifests_path}", file=sys.stderr)
        return 1
    with open(eval_manifests_path, "r", encoding="utf-8") as fh:
        _ = yaml.safe_load(fh)  # parse-only check

    ref_root = Path(args.reference_root).resolve()
    if not ref_root.is_dir():
        print(f"FAIL: reference root missing: {ref_root}", file=sys.stderr)
        return 1

    out_manifest = Path(args.out_manifest).resolve()
    out_audio_dir = Path(args.out_audio_dir).resolve()
    out_audio_dir.mkdir(parents=True, exist_ok=True)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)

    # Refuse to silently overwrite a manifest pointing at unrelated files;
    # but a clean rerun under the same selection is fine. Wipe the audio dir
    # first so the final state is deterministic.
    for existing in sorted(out_audio_dir.iterdir()):
        if existing.is_file() and existing.suffix == ".wav":
            existing.unlink()
        elif existing.is_dir():
            print(f"FAIL: refusing to clear nested dir under {out_audio_dir}: {existing}",
                  file=sys.stderr)
            return 1

    locked_audio_ids, locked_speakers, locked_sha256s = load_locked_index()

    examples: List[Dict] = []
    seen_dst: Set[Path] = set()
    seen_audio_ids: Set[str] = set()
    seen_sha256s: Set[str] = set()

    for speaker_id, src_filename, family, tier, notes in SELECTION:
        src = ref_root / speaker_id / src_filename
        if not src.exists():
            print(f"FAIL: source audio missing: {src}", file=sys.stderr)
            return 1

        stem = src_filename.rsplit(".", 1)[0]
        dst_name = f"{speaker_id}__{stem}.wav"
        dst = out_audio_dir / dst_name
        if dst in seen_dst:
            print(f"FAIL: duplicate output filename: {dst}", file=sys.stderr)
            return 1
        seen_dst.add(dst)

        shutil.copyfile(src, dst)
        assert_pcm16_mono_16k(dst)
        sha = sha256_file(dst)
        dur = wav_duration_s(dst)

        # audio_id format: demo/<speaker_id>/<stem> (deterministic, disjoint
        # from `librispeech/...` audio_ids in locked manifests).
        audio_id = f"demo/{speaker_id}/{stem}"

        # Disjointness checks (audio_id / speaker_id / audio_sha256).
        if audio_id in locked_audio_ids:
            print(f"FAIL: audio_id {audio_id} is in a locked manifest", file=sys.stderr)
            return 1
        if speaker_id in locked_speakers:
            print(f"FAIL: speaker_id {speaker_id} is in a locked manifest", file=sys.stderr)
            return 1
        if sha in locked_sha256s:
            print(f"FAIL: audio_sha256 {sha} is in a locked manifest "
                  f"(file: {dst})", file=sys.stderr)
            return 1
        if audio_id in seen_audio_ids:
            print(f"FAIL: duplicate demo audio_id: {audio_id}", file=sys.stderr)
            return 1
        if sha in seen_sha256s:
            print(f"FAIL: duplicate demo audio_sha256: {sha}", file=sys.stderr)
            return 1
        seen_audio_ids.add(audio_id)
        seen_sha256s.add(sha)

        rel_path = dst.relative_to(REPO_ROOT).as_posix()
        examples.append({
            "audio_id": audio_id,
            "speaker_id": speaker_id,
            "family": family,
            "tier": tier,
            "source": (
                "demo_reference_artifacts/v1 "
                "(operator-staged public demo reserve; reuse_policy P8.2 read_only)"
            ),
            "license": "demo_reserve_public",
            "duration_s": round(dur, 6),
            "audio_sha256": sha,
            "file_path": rel_path,
            "notes": notes,
        })

    if len(examples) != 8:
        print(f"FAIL: expected 8 entries, got {len(examples)}", file=sys.stderr)
        return 1

    # Confirm exactly 8 files now exist in out_audio_dir.
    on_disk = sorted(p for p in out_audio_dir.iterdir()
                     if p.is_file() and p.suffix == ".wav")
    if len(on_disk) != 8:
        print(f"FAIL: expected 8 wav files on disk, got {len(on_disk)}", file=sys.stderr)
        return 1
    for entry in examples:
        if not (REPO_ROOT / entry["file_path"]).exists():
            print(f"FAIL: manifest file_path missing: {entry['file_path']}", file=sys.stderr)
            return 1

    families_present = {e["family"] for e in examples if e["tier"] == "id"}
    required_id_families = {
        "clean", "cafe_noise", "phone_band", "far_field_room", "muffled_lowpass",
    }
    missing = required_id_families - families_present
    if missing:
        print(f"FAIL: required ID families missing: {sorted(missing)}", file=sys.stderr)
        return 1
    n_ood = sum(1 for e in examples if e["tier"] == "ood_param_illustrative")
    if n_ood != 3:
        print(f"FAIL: expected 3 ood_param_illustrative entries, got {n_ood}",
              file=sys.stderr)
        return 1

    payload = {
        "manifest_set": "demo_examples_v1",
        "produced_by_task": "P8.2",
        "claims_enabled_ood_real": False,
        "blocked_ood_public_active": True,
        "selection_rule": (
            "Deterministic 8-entry selection from the operator-staged "
            "demo_reference_artifacts/examples/ pool. 5 ID-family entries "
            "(clean, cafe_noise, phone_band, far_field_room, muffled_lowpass) "
            "drawn one each from sorted speakers (ex001, ex003, ex004, ex007, "
            "ex010); 3 OOD-param illustrative entries (broadband_hiss, family "
            "outside Section 3) drawn one each from sorted speakers (ex001, "
            "ex003, ex004). Per agent plan Section 4.7 BLOCKED_OOD_PUBLIC "
            "branch (claims_enabled.ood_real=false): no entry from "
            "common_voice_demo_reserved."
        ),
        "n_examples": len(examples),
        "examples": examples,
    }

    with open(out_manifest, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")

    print(f"OK_DEMO_EXAMPLES with {len(examples)} selected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
