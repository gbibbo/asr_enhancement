from __future__ import annotations

import json
from pathlib import Path

import pytest

_CANDIDATES_FILE = Path("config/demo_example_candidates.json")
_EXAMPLES_FILE = Path("config/demo_examples.json")
_EXPECTED_FINAL_IDS = ["ex001", "ex003", "ex004", "ex007", "ex010"]
_EXPECTED_DEGRADATION_IDS = [
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
]


def _load_examples() -> list[dict]:
    if not _EXAMPLES_FILE.is_file():
        pytest.skip(
            f"{_EXAMPLES_FILE} does not exist — "
            "run scripts/demo/materialize_demo_examples.py first"
        )
    return json.loads(_EXAMPLES_FILE.read_text(encoding="utf-8"))


def _load_candidates() -> list[dict]:
    if not _CANDIDATES_FILE.is_file():
        pytest.skip(f"{_CANDIDATES_FILE} does not exist")
    return json.loads(_CANDIDATES_FILE.read_text(encoding="utf-8"))


def test_demo_examples_json_exists():
    assert _EXAMPLES_FILE.is_file(), (
        f"{_EXAMPLES_FILE} not found — run scripts/demo/materialize_demo_examples.py first"
    )


def test_demo_examples_has_five_entries():
    data = _load_examples()
    assert len(data) == 5, f"Expected 5 entries, got {len(data)}"


def test_example_ids_are_expected_final_set():
    data = _load_examples()
    actual = [e["example_id"] for e in data]
    assert actual == _EXPECTED_FINAL_IDS, (
        f"example_id sequence mismatch:\n"
        f"  expected: {_EXPECTED_FINAL_IDS}\n"
        f"  actual:   {actual}"
    )


def test_example_ids_are_subset_of_candidates():
    examples = _load_examples()
    candidates = _load_candidates()
    cand_ids = {c["example_id"] for c in candidates}
    for e in examples:
        assert e["example_id"] in cand_ids, (
            f"example_id={e['example_id']!r} not present in candidates"
        )


def test_degradation_ids_are_canonical_five():
    data = _load_examples()
    for e in data:
        assert e.get("degradation_ids") == _EXPECTED_DEGRADATION_IDS, (
            f"example_id={e['example_id']}: degradation_ids={e.get('degradation_ids')!r}"
        )


def test_degraded_audio_paths_has_five_keys():
    data = _load_examples()
    for e in data:
        paths = e.get("degraded_audio_paths", {})
        assert set(paths.keys()) == set(_EXPECTED_DEGRADATION_IDS), (
            f"example_id={e['example_id']}: "
            f"degraded_audio_paths keys={set(paths.keys())!r}"
        )


def test_ground_truth_matches_candidates():
    examples = _load_examples()
    candidates = _load_candidates()
    cand_by_id = {c["example_id"]: c for c in candidates}
    for e in examples:
        expected = cand_by_id[e["example_id"]]["ground_truth"]
        assert e.get("ground_truth") == expected, (
            f"example_id={e['example_id']}: ground_truth mismatch"
        )


def test_duration_seconds_matches_candidates():
    examples = _load_examples()
    candidates = _load_candidates()
    cand_by_id = {c["example_id"]: c for c in candidates}
    for e in examples:
        expected = cand_by_id[e["example_id"]]["duration_seconds"]
        assert e.get("duration_seconds") == expected, (
            f"example_id={e['example_id']}: duration_seconds mismatch "
            f"(got {e.get('duration_seconds')!r}, expected {expected!r})"
        )


def test_audio_available_is_true():
    data = _load_examples()
    for e in data:
        assert e.get("audio_available") is True, (
            f"example_id={e['example_id']}: audio_available={e.get('audio_available')!r}"
        )


def test_clean_audio_path_is_set_and_relative():
    data = _load_examples()
    for e in data:
        p = e.get("clean_audio_path", "")
        assert p, f"example_id={e['example_id']}: clean_audio_path is empty"
        assert not Path(p).is_absolute(), (
            f"example_id={e['example_id']}: clean_audio_path is absolute: {p!r}"
        )
        assert ".." not in Path(p).parts, (
            f"example_id={e['example_id']}: clean_audio_path contains traversal: {p!r}"
        )


def test_degraded_audio_paths_are_relative():
    data = _load_examples()
    for e in data:
        for deg_id, p in e.get("degraded_audio_paths", {}).items():
            assert p, (
                f"example_id={e['example_id']}: path for {deg_id!r} is empty"
            )
            assert not Path(p).is_absolute(), (
                f"example_id={e['example_id']}: {deg_id} path is absolute: {p!r}"
            )
            assert ".." not in Path(p).parts, (
                f"example_id={e['example_id']}: {deg_id} path contains traversal: {p!r}"
            )


def test_no_absolute_paths_anywhere():
    data = _load_examples()
    for e in data:
        clean = e.get("clean_audio_path", "")
        assert not Path(clean).is_absolute(), (
            f"example_id={e['example_id']}: clean_audio_path is absolute"
        )
        for deg_id, p in e.get("degraded_audio_paths", {}).items():
            assert not Path(p).is_absolute(), (
                f"example_id={e['example_id']}: {deg_id} path is absolute"
            )
