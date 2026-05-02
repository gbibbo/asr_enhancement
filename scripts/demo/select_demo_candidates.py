"""Import the datamove1 reserved public demo examples as B6.1 candidate manifest.

Usage:
    python scripts/demo/select_demo_candidates.py \
        [--reserved-yaml-ref origin/feature/training-datamove1-v1] \
        [--reserved-yaml-path configs/training/reserved_public_demo_examples.yaml] \
        [--output config/demo_example_candidates.json]

Reads the 10 reserved examples from the datamove1 branch via `git show`.
Writes config/demo_example_candidates.json with public_content_review set to
"pending_manual_review". Gabriel must review each entry and confirm approval
before B6.1 can be marked done.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML is required. Install with: pip install PyYAML",
        file=sys.stderr,
    )
    sys.exit(1)

_DEFAULT_REF = "origin/feature/training-datamove1-v1"
_DEFAULT_YAML_PATH = "configs/training/reserved_public_demo_examples.yaml"
_DEFAULT_OUTPUT = "config/demo_example_candidates.json"
_EXPECTED_COUNT = 10


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--reserved-yaml-ref",
        default=_DEFAULT_REF,
        metavar="REF",
        help=f"Git ref to read the reserved YAML from (default: {_DEFAULT_REF})",
    )
    p.add_argument(
        "--reserved-yaml-path",
        default=_DEFAULT_YAML_PATH,
        metavar="PATH",
        help=f"Path inside the ref to the reserved YAML (default: {_DEFAULT_YAML_PATH})",
    )
    p.add_argument(
        "--output",
        default=_DEFAULT_OUTPUT,
        metavar="FILE",
        help=f"Output JSON path (default: {_DEFAULT_OUTPUT})",
    )
    return p.parse_args()


def _git_show(ref: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"ERROR: `git show {ref}:{path}` failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout


def _git_rev_parse(ref: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", ref],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"ERROR: `git rev-parse {ref}` failed (exit {result.returncode}):\n"
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout.strip()


def _require(example: dict, field: str, index: int) -> object:
    if field not in example:
        print(
            f"ERROR: entry [{index}] is missing required field '{field}'.",
            file=sys.stderr,
        )
        sys.exit(1)
    return example[field]


def main() -> None:
    args = _parse_args()
    ref: str = args.reserved_yaml_ref
    yaml_path: str = args.reserved_yaml_path
    output = Path(args.output)

    yaml_text = _git_show(ref, yaml_path)

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse YAML from {ref}:{yaml_path}:\n{exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict) or "examples" not in data:
        print(
            f"ERROR: Expected a mapping with 'examples' key in {ref}:{yaml_path}.",
            file=sys.stderr,
        )
        sys.exit(1)

    examples = data["examples"]
    if not isinstance(examples, list):
        print("ERROR: 'examples' must be a list.", file=sys.stderr)
        sys.exit(1)

    if len(examples) != _EXPECTED_COUNT:
        print(
            f"ERROR: Expected exactly {_EXPECTED_COUNT} examples, got {len(examples)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    commit_sha = _git_rev_parse(ref)
    print(f"Reading from {ref} at commit {commit_sha}", file=sys.stderr)

    entries: list[dict] = []
    for i, ex in enumerate(examples):
        rec_id = str(_require(ex, "utterance_id", i))
        parts = rec_id.split("-")
        if len(parts) != 3:
            print(
                f"ERROR: entry [{i}] utterance_id '{rec_id}' is not in "
                "speaker-chapter-utterance format.",
                file=sys.stderr,
            )
            sys.exit(1)
        utterance_part = parts[2]
        speaker_id = str(_require(ex, "speaker_id", i))
        chapter_id = str(_require(ex, "chapter_id", i))
        expected_rec_id = f"{speaker_id}-{chapter_id}-{utterance_part}"
        if expected_rec_id != rec_id:
            print(
                f"ERROR: entry [{i}] rec_id mismatch: "
                f"speaker_id/chapter_id give '{expected_rec_id}' but utterance_id is '{rec_id}'.",
                file=sys.stderr,
            )
            sys.exit(1)

        split = str(_require(ex, "split", i))
        transcript = str(_require(ex, "transcript", i)).strip()
        if not transcript:
            print(f"ERROR: entry [{i}] has an empty transcript.", file=sys.stderr)
            sys.exit(1)
        duration_seconds = float(_require(ex, "duration_seconds", i))

        source_audio_relpath = f"{split}/{speaker_id}/{chapter_id}/{rec_id}.flac"
        source_transcript_relpath = (
            f"{split}/{speaker_id}/{chapter_id}/{speaker_id}-{chapter_id}.trans.txt"
        )

        selection_notes = (
            f"Imported from datamove1 reserved set. "
            f"Source ref: {ref} (commit {commit_sha}). "
            f"Selection policy: one_per_speaker_deterministic_sort over dev-clean, "
            f"duration 3.0-10.0s, exactly 10 distinct speakers. "
            f"Gender metadata was not available in the datamove1 reserved YAML; "
            f"speaker_gender is set to 'unknown' for all entries."
        )

        entry: dict = {
            "chapter_id": chapter_id,
            "duration_seconds": duration_seconds,
            "example_id": f"ex{i + 1:03d}",
            "excluded_from_training": True,
            "ground_truth": transcript,
            "ground_truth_source": "librispeech_transcript",
            "public_content_review": "pending_manual_review",
            "selection_notes": selection_notes,
            "source_audio_relpath": source_audio_relpath,
            "source_dataset": "librispeech",
            "source_recording_id": rec_id,
            "source_split": split,
            "source_transcript_relpath": source_transcript_relpath,
            "speaker_gender": "unknown",
            "speaker_id": speaker_id,
            "utterance_id": utterance_part,
        }

        sha256 = ex.get("audio_sha256")
        if sha256 is not None:
            entry["audio_sha256"] = str(sha256)

        entries.append(entry)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} candidates to {output}", file=sys.stderr)
    print(
        "IMPORTANT: public_content_review is 'pending_manual_review' for all entries. "
        "Show the candidates to Gabriel and wait for explicit approval before changing "
        "to 'passed_manual_review'.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
