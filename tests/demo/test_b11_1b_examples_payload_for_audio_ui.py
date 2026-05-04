"""B11.1b payload contract: the /demo audio + ground-truth UI relies on the
public /demo/examples projection exposing ground_truth, audio_available,
clean_audio_path, and degraded_audio_paths consistently. These tests pin the
shape of the data the frontend reads. If a future change drops a field or
introduces a degradation_id without a matching audio path, the audio rows on
/demo would break silently in the browser; this test fails first.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from libs.demo.examples import DemoExample, load_examples


def _config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "demo_examples.json"


def test_demo_example_model_exposes_ground_truth_and_audio_fields() -> None:
    fields = DemoExample.model_fields
    assert "ground_truth" in fields, "DemoExample must expose ground_truth"
    assert "audio_available" in fields, "DemoExample must expose audio_available"
    assert "clean_audio_path" in fields, "DemoExample must expose clean_audio_path"
    assert "degraded_audio_paths" in fields, (
        "DemoExample must expose degraded_audio_paths"
    )


def test_demo_examples_config_is_present() -> None:
    cfg = _config_path()
    if not cfg.is_file():
        pytest.skip(f"Config not present at {cfg}; not a closure gate on a fresh checkout.")
    examples = load_examples(cfg)
    assert examples, "Curated examples list is empty; B11.1b UI has nothing to render."


def test_every_curated_example_has_non_empty_ground_truth() -> None:
    cfg = _config_path()
    if not cfg.is_file():
        pytest.skip(f"Config not present at {cfg}.")
    examples = load_examples(cfg)
    for ex in examples:
        assert isinstance(ex.ground_truth, str), (
            f"ground_truth must be a string for {ex.example_id}"
        )
        assert ex.ground_truth.strip() != "", (
            f"ground_truth must be non-empty for {ex.example_id}"
        )


def test_clean_audio_path_set_when_audio_available() -> None:
    cfg = _config_path()
    if not cfg.is_file():
        pytest.skip(f"Config not present at {cfg}.")
    examples = load_examples(cfg)
    for ex in examples:
        if ex.audio_available:
            assert ex.clean_audio_path is not None and ex.clean_audio_path.strip() != "", (
                f"audio_available=true requires clean_audio_path for {ex.example_id}"
            )


def test_every_advertised_degradation_has_a_matching_audio_path() -> None:
    cfg = _config_path()
    if not cfg.is_file():
        pytest.skip(f"Config not present at {cfg}.")
    examples = load_examples(cfg)
    for ex in examples:
        if not ex.audio_available:
            continue
        for deg_id in ex.degradation_ids:
            assert deg_id in ex.degraded_audio_paths, (
                f"{ex.example_id} advertises degradation_id {deg_id!r} "
                f"but degraded_audio_paths has no key for it"
            )
            path = ex.degraded_audio_paths[deg_id]
            assert isinstance(path, str) and path.strip() != "", (
                f"{ex.example_id} has empty degraded path for {deg_id!r}"
            )


def test_no_orphan_degraded_audio_paths() -> None:
    cfg = _config_path()
    if not cfg.is_file():
        pytest.skip(f"Config not present at {cfg}.")
    examples = load_examples(cfg)
    for ex in examples:
        for key in ex.degraded_audio_paths.keys():
            assert key in ex.degradation_ids, (
                f"{ex.example_id} has degraded path for {key!r} "
                f"but it is not advertised in degradation_ids"
            )
