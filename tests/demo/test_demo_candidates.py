from __future__ import annotations

import json
from pathlib import Path

import pytest

_CANDIDATE_FILE = Path("config/demo_example_candidates.json")
_EXPECTED_IDS = [f"ex{i:03d}" for i in range(1, 11)]
_VALID_GENDERS = {"M", "F", "unknown"}
_TRAINING_SPLITS = {"train-clean-100", "train-clean-360", "train-other-500"}


def _load() -> list[dict]:
    if not _CANDIDATE_FILE.is_file():
        pytest.skip(f"{_CANDIDATE_FILE} does not exist yet (B6.1 blocked on LibriSpeech data)")
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
        assert 5.0 <= dur <= 15.0, (
            f"example_id={e['example_id']}: duration {dur} outside [5.0, 15.0]"
        )


def test_at_least_five_distinct_speakers():
    data = _load()
    speakers = {e["speaker_id"] for e in data}
    assert len(speakers) >= 5, f"Only {len(speakers)} distinct speakers: {speakers}"


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


def test_all_source_split_is_test_clean():
    data = _load()
    for e in data:
        assert e.get("source_split") == "test-clean", (
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


def test_required_provenance_fields_present():
    required = {
        "chapter_id", "duration_seconds", "example_id", "excluded_from_training",
        "ground_truth", "ground_truth_source", "public_content_review", "selection_notes",
        "source_audio_relpath", "source_dataset", "source_recording_id", "source_split",
        "source_transcript_relpath", "speaker_gender", "speaker_id", "utterance_id",
    }
    data = _load()
    for e in data:
        missing = required - e.keys()
        assert not missing, (
            f"example_id={e.get('example_id', '?')}: missing fields: {sorted(missing)}"
        )
