from __future__ import annotations

import json
from pathlib import Path

import pytest

_CANDIDATE_FILE = Path("config/demo_example_candidates.json")
_DEMO_EXAMPLES_FILE = Path("config/demo_examples.json")
_EXPECTED_IDS = [f"ex{i:03d}" for i in range(1, 11)]
_EXPECTED_SOURCE_RECORDING_IDS = [
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
_VALID_GENDERS = {"M", "F", "unknown"}


def _load() -> list[dict]:
    if not _CANDIDATE_FILE.is_file():
        pytest.skip(
            f"{_CANDIDATE_FILE} does not exist yet — "
            "run scripts/demo/select_demo_candidates.py first"
        )
    return json.loads(_CANDIDATE_FILE.read_text(encoding="utf-8"))


def test_candidates_file_exists():
    assert _CANDIDATE_FILE.is_file(), (
        f"{_CANDIDATE_FILE} not found — run scripts/demo/select_demo_candidates.py first"
    )


def test_candidates_has_ten_entries():
    data = _load()
    assert len(data) == 10, f"Expected 10 entries, got {len(data)}"


def test_all_example_ids_are_ex001_through_ex010():
    data = _load()
    actual = [e["example_id"] for e in data]
    assert actual == _EXPECTED_IDS, f"example_id sequence mismatch: {actual}"


def test_all_example_ids_unique():
    data = _load()
    ids = [e["example_id"] for e in data]
    assert len(ids) == len(set(ids)), f"Duplicate example_ids: {ids}"


def test_all_recording_ids_unique():
    data = _load()
    rids = [e["source_recording_id"] for e in data]
    assert len(rids) == len(set(rids)), f"Duplicate source_recording_ids: {rids}"


def test_all_recording_ids_match_datamove1_reserved_set():
    data = _load()
    actual = [e["source_recording_id"] for e in data]
    assert actual == _EXPECTED_SOURCE_RECORDING_IDS, (
        f"source_recording_id list does not match the datamove1 reserved set.\n"
        f"Expected: {_EXPECTED_SOURCE_RECORDING_IDS}\n"
        f"Got:      {actual}"
    )


def test_source_recording_id_matches_speaker_chapter_utterance():
    data = _load()
    for e in data:
        expected = f"{e['speaker_id']}-{e['chapter_id']}-{e['utterance_id']}"
        assert e["source_recording_id"] == expected, (
            f"example_id={e['example_id']}: source_recording_id {e['source_recording_id']!r} "
            f"!= {expected!r}"
        )


def test_all_durations_in_valid_range():
    data = _load()
    for e in data:
        dur = e["duration_seconds"]
        assert 3.0 <= dur <= 10.0, (
            f"example_id={e['example_id']}: duration {dur} outside [3.0, 10.0]"
        )


def test_exactly_ten_distinct_speakers():
    data = _load()
    speakers = {e["speaker_id"] for e in data}
    assert len(speakers) == 10, f"Expected 10 distinct speakers, got {len(speakers)}: {speakers}"


def test_all_have_nonempty_ground_truth():
    data = _load()
    for e in data:
        assert e.get("ground_truth", "").strip(), (
            f"example_id={e['example_id']}: ground_truth is empty"
        )


def test_all_excluded_from_training():
    data = _load()
    for e in data:
        assert e.get("excluded_from_training") is True, (
            f"example_id={e['example_id']}: excluded_from_training is not True"
        )


def test_all_source_split_is_dev_clean():
    data = _load()
    for e in data:
        assert e.get("source_split") == "dev-clean", (
            f"example_id={e['example_id']}: source_split={e.get('source_split')!r}"
        )


def test_all_source_dataset_is_librispeech():
    data = _load()
    for e in data:
        assert e.get("source_dataset") == "librispeech", (
            f"example_id={e['example_id']}: source_dataset={e.get('source_dataset')!r}"
        )


def test_speaker_gender_field_valid():
    data = _load()
    for e in data:
        g = e.get("speaker_gender")
        assert g in _VALID_GENDERS, (
            f"example_id={e['example_id']}: speaker_gender={g!r} not in {_VALID_GENDERS}"
        )


def test_all_speaker_genders_unknown():
    data = _load()
    for e in data:
        assert e.get("speaker_gender") == "unknown", (
            f"example_id={e['example_id']}: speaker_gender={e.get('speaker_gender')!r}, "
            "expected 'unknown' (gender metadata not available in datamove1)"
        )


def test_all_content_review_completed():
    data = _load()
    for e in data:
        assert e.get("public_content_review") == "passed_manual_review", (
            f"example_id={e['example_id']}: public_content_review={e.get('public_content_review')!r}. "
            "Review the entry and set it to 'passed_manual_review' before committing."
        )


def test_no_audio_path_inside_repo():
    data = _load()
    for e in data:
        for field in ("source_audio_relpath", "source_transcript_relpath"):
            val = e.get(field, "")
            assert not Path(val).is_absolute(), (
                f"example_id={e['example_id']}: {field}={val!r} must be a relative path"
            )


def test_audio_sha256_present():
    data = _load()
    for e in data:
        assert "audio_sha256" in e, (
            f"example_id={e['example_id']}: audio_sha256 field missing"
        )
        assert e["audio_sha256"], (
            f"example_id={e['example_id']}: audio_sha256 is empty"
        )


def test_required_provenance_fields_present():
    required = {
        "audio_sha256",
        "chapter_id",
        "duration_seconds",
        "example_id",
        "excluded_from_training",
        "ground_truth",
        "ground_truth_source",
        "public_content_review",
        "selection_notes",
        "source_audio_relpath",
        "source_dataset",
        "source_recording_id",
        "source_split",
        "source_transcript_relpath",
        "speaker_gender",
        "speaker_id",
        "utterance_id",
    }
    data = _load()
    for e in data:
        missing = required - e.keys()
        assert not missing, (
            f"example_id={e.get('example_id', '?')}: missing fields: {sorted(missing)}"
        )


def test_demo_examples_json_does_not_exist():
    assert not _DEMO_EXAMPLES_FILE.is_file(), (
        f"{_DEMO_EXAMPLES_FILE} must not exist in B6.1 — audio sourcing is B6.2"
    )
