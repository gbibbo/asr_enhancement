"""Select 10 LibriSpeech test-clean utterances as B6.1 candidate examples.

Usage:
    python scripts/demo/select_demo_candidates.py \\
        --librispeech-root /path/to/LibriSpeech \\
        --output config/demo_example_candidates.json \\
        [--num-examples 10] \\
        [--min-duration 5.0] \\
        [--max-duration 15.0]

--librispeech-root must point to the LibriSpeech root directory containing
both test-clean/ and SPEAKERS.TXT, NOT directly to test-clean/.

All 10 output entries have public_content_review: "pending_manual_review".
Gabriel must review each entry and change this to "passed_manual_review"
before B6.1 can be marked done.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import soundfile as sf
except ImportError:  # pragma: no cover
    print("ERROR: soundfile is required. Install it with: pip install soundfile", file=sys.stderr)
    sys.exit(1)

_TRAINING_SPLITS = frozenset({"train-clean-100", "train-clean-360", "train-other-500"})
_TARGET_SPLIT = "test-clean"
_SOURCE_DATASET = "librispeech"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--librispeech-root", required=True, metavar="DIR",
                   help="LibriSpeech root containing test-clean/ and SPEAKERS.TXT")
    p.add_argument("--output", required=True, metavar="FILE",
                   help="Output JSON path, e.g. config/demo_example_candidates.json")
    p.add_argument("--num-examples", type=int, default=10, metavar="N",
                   help="Number of examples to select (default: 10)")
    p.add_argument("--min-duration", type=float, default=5.0, metavar="SEC",
                   help="Minimum duration in seconds (default: 5.0)")
    p.add_argument("--max-duration", type=float, default=15.0, metavar="SEC",
                   help="Maximum duration in seconds (default: 15.0)")
    return p.parse_args()


def _validate_root(root: Path) -> None:
    root_name = root.name.rstrip("/")
    if root_name in ("test-clean", "test_clean"):
        print(
            "ERROR: --librispeech-root must point to the LibriSpeech root containing "
            "test-clean/ and SPEAKERS.TXT, not directly to test-clean/.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not root.is_dir():
        print(f"ERROR: --librispeech-root does not exist or is not a directory: {root}", file=sys.stderr)
        sys.exit(1)
    if not (root / _TARGET_SPLIT).is_dir():
        print(f"ERROR: {root / _TARGET_SPLIT} not found. Is this the LibriSpeech root?", file=sys.stderr)
        sys.exit(1)
    if not (root / "SPEAKERS.TXT").is_file():
        print(f"ERROR: SPEAKERS.TXT not found at {root / 'SPEAKERS.TXT'}.", file=sys.stderr)
        sys.exit(1)


def _parse_speakers(speakers_txt: Path) -> dict[str, str]:
    gender: dict[str, str] = {}
    for line in speakers_txt.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            sid = parts[0].strip()
            sex = parts[1].strip().upper()
            gender[sid] = sex if sex in ("M", "F") else "unknown"
    return gender


def _collect_candidates(
    root: Path,
    gender_map: dict[str, str],
    min_dur: float,
    max_dur: float,
) -> list[dict]:
    candidates = []
    split_dir = root / _TARGET_SPLIT
    for trans_file in sorted(split_dir.rglob("*.trans.txt")):
        speaker_id = trans_file.parts[-3]
        chapter_id = trans_file.parts[-2]
        for line in trans_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec_id, _, transcript = line.partition(" ")
            if not transcript:
                continue
            parts = rec_id.split("-")
            if len(parts) != 3:
                continue
            s_id, c_id, u_id = parts
            flac_path = trans_file.parent / f"{rec_id}.flac"
            if not flac_path.is_file():
                continue
            try:
                info = sf.info(str(flac_path))
                duration = info.duration
            except Exception:
                continue
            if not (min_dur <= duration <= max_dur):
                continue
            candidates.append({
                "speaker_id": speaker_id,
                "chapter_id": chapter_id,
                "utterance_id": u_id,
                "source_recording_id": rec_id,
                "speaker_gender": gender_map.get(speaker_id, "unknown"),
                "duration_seconds": round(duration, 3),
                "ground_truth": transcript,
                "source_audio_relpath": f"{_TARGET_SPLIT}/{speaker_id}/{chapter_id}/{rec_id}.flac",
                "source_transcript_relpath": f"{_TARGET_SPLIT}/{speaker_id}/{chapter_id}/{speaker_id}-{chapter_id}.trans.txt",
            })
    return candidates


def _select_with_gender_balance(
    candidates: list[dict],
    num: int,
) -> list[dict]:
    by_speaker: dict[str, list[dict]] = {}
    for c in candidates:
        by_speaker.setdefault(c["speaker_id"], []).append(c)

    m_speakers = sorted(sid for sid, items in by_speaker.items() if items[0]["speaker_gender"] == "M")
    f_speakers = sorted(sid for sid, items in by_speaker.items() if items[0]["speaker_gender"] == "F")
    u_speakers = sorted(sid for sid, items in by_speaker.items() if items[0]["speaker_gender"] == "unknown")

    ordered_speakers: list[str] = []
    m_i, f_i = 0, 0
    while len(ordered_speakers) < len(by_speaker):
        if m_i < len(m_speakers):
            ordered_speakers.append(m_speakers[m_i]); m_i += 1
        if f_i < len(f_speakers):
            ordered_speakers.append(f_speakers[f_i]); f_i += 1
    for s in u_speakers:
        if s not in ordered_speakers:
            ordered_speakers.append(s)

    selected: list[dict] = []
    speaker_pool = list(ordered_speakers)
    pool_idx = 0
    while len(selected) < num and pool_idx < len(speaker_pool) * num:
        sid = speaker_pool[pool_idx % len(speaker_pool)]
        pool_idx += 1
        already_used = {c["source_recording_id"] for c in selected}
        for cand in by_speaker[sid]:
            if cand["source_recording_id"] not in already_used:
                selected.append(cand)
                break

    return selected[:num]


def main() -> None:
    args = _parse_args()
    root = Path(args.librispeech_root).resolve()
    output = Path(args.output)
    num = args.num_examples
    min_dur = args.min_duration
    max_dur = args.max_duration

    _validate_root(root)

    speakers_txt = root / "SPEAKERS.TXT"
    gender_map = _parse_speakers(speakers_txt)
    print(f"Parsed {len(gender_map)} speakers from SPEAKERS.TXT", file=sys.stderr)

    candidates = _collect_candidates(root, gender_map, min_dur, max_dur)
    print(f"Found {len(candidates)} candidates in [{min_dur}, {max_dur}]s range", file=sys.stderr)

    if len(candidates) < num:
        print(
            f"ERROR: Only {len(candidates)} candidates in [{min_dur}, {max_dur}]s range; "
            f"need {num}. Widen duration range or check LibriSpeech root.",
            file=sys.stderr,
        )
        sys.exit(1)

    distinct_speakers = {c["speaker_id"] for c in candidates}
    if len(distinct_speakers) < 5:
        print(
            f"ERROR: Only {len(distinct_speakers)} distinct speakers in candidate pool; "
            "need at least 5.",
            file=sys.stderr,
        )
        sys.exit(1)

    selected = _select_with_gender_balance(candidates, num)

    if len(selected) < num:
        print(
            f"ERROR: Could only select {len(selected)} examples after gender-balance pass; "
            f"need {num}. Add more speakers or widen duration range.",
            file=sys.stderr,
        )
        sys.exit(1)

    selected_speakers = {c["speaker_id"] for c in selected}
    if len(selected_speakers) < 5:
        print(
            f"ERROR: Selected set has only {len(selected_speakers)} distinct speakers; "
            "need at least 5.",
            file=sys.stderr,
        )
        sys.exit(1)

    entries = []
    for i, cand in enumerate(selected, start=1):
        entries.append({
            "chapter_id": cand["chapter_id"],
            "duration_seconds": cand["duration_seconds"],
            "example_id": f"ex{i:03d}",
            "excluded_from_training": True,
            "ground_truth": cand["ground_truth"],
            "ground_truth_source": "librispeech_transcript",
            "public_content_review": "pending_manual_review",
            "selection_notes": "",
            "source_audio_relpath": cand["source_audio_relpath"],
            "source_dataset": _SOURCE_DATASET,
            "source_recording_id": cand["source_recording_id"],
            "source_split": _TARGET_SPLIT,
            "source_transcript_relpath": cand["source_transcript_relpath"],
            "speaker_gender": cand["speaker_gender"],
            "speaker_id": cand["speaker_id"],
            "utterance_id": cand["utterance_id"],
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} candidates to {output}", file=sys.stderr)
    print(
        "IMPORTANT: public_content_review is 'pending_manual_review' for all entries. "
        "Review each entry and change to 'passed_manual_review' before committing.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
