from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import libs.common.versions as _versions
from libs.audio.degradations import (
    DEGRADATION_REGISTRY,
    KNOWN_DEGRADATION_IDS,
    DegradationResult,
    UnknownDegradationError,
    apply_degradation,
    get_degradation,
)

DEGRADATION_IDS = [
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
]


def _make_wav(tmp_path: Path, *, sr: int = 16000, duration: float = 0.5, silent: bool = False) -> Path:
    n = int(sr * duration)
    if silent:
        samples = np.zeros(n, dtype=np.float64)
    else:
        samples = (0.5 * np.sin(2 * np.pi * 440 * np.arange(n) / sr)).astype(np.float64)
    p = tmp_path / "input.wav"
    sf.write(p, samples, sr)
    return p


# ---------------------------------------------------------------------------
# Registry and catalog
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_registry_has_five_entries(self) -> None:
        assert len(DEGRADATION_REGISTRY) == 5

    def test_all_known_ids_in_registry(self) -> None:
        assert KNOWN_DEGRADATION_IDS == frozenset(DEGRADATION_REGISTRY)

    def test_known_ids_is_frozenset(self) -> None:
        assert isinstance(KNOWN_DEGRADATION_IDS, frozenset)

    @pytest.mark.parametrize("degradation_id", DEGRADATION_IDS)
    def test_each_spec_has_nonempty_id_and_description(self, degradation_id: str) -> None:
        spec = DEGRADATION_REGISTRY[degradation_id]
        assert spec.id == degradation_id
        assert isinstance(spec.description, str) and spec.description

    @pytest.mark.parametrize("degradation_id", DEGRADATION_IDS)
    def test_each_spec_params_is_nonempty_dict(self, degradation_id: str) -> None:
        spec = DEGRADATION_REGISTRY[degradation_id]
        assert isinstance(spec.params, dict)
        assert len(spec.params) > 0


# ---------------------------------------------------------------------------
# Error path
# ---------------------------------------------------------------------------


class TestErrorPath:
    def test_unknown_degradation_raises_unknown_degradation_error(self) -> None:
        with pytest.raises(UnknownDegradationError):
            apply_degradation("nonexistent_id", Path("/dev/null"), Path("/tmp"))

    def test_unknown_degradation_error_message_contains_id(self) -> None:
        with pytest.raises(UnknownDegradationError, match="nonexistent_id"):
            get_degradation("nonexistent_id")


# ---------------------------------------------------------------------------
# Per-degradation behavioral — parametrized
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("degradation_id", DEGRADATION_IDS)
def test_produces_output_file(tmp_path: Path, degradation_id: str) -> None:
    wav = _make_wav(tmp_path)
    out_dir = tmp_path / f"out_{degradation_id}"
    result = apply_degradation(degradation_id, wav, out_dir, seed=0)
    assert result.output_path.exists()


@pytest.mark.parametrize("degradation_id", DEGRADATION_IDS)
def test_output_has_nonzero_frames(tmp_path: Path, degradation_id: str) -> None:
    wav = _make_wav(tmp_path)
    out_dir = tmp_path / f"out_{degradation_id}"
    result = apply_degradation(degradation_id, wav, out_dir, seed=0)
    info = sf.info(result.output_path)
    assert info.frames > 0


@pytest.mark.parametrize("degradation_id", DEGRADATION_IDS)
def test_result_degradation_id_matches(tmp_path: Path, degradation_id: str) -> None:
    wav = _make_wav(tmp_path)
    out_dir = tmp_path / f"out_{degradation_id}"
    result = apply_degradation(degradation_id, wav, out_dir, seed=0)
    assert result.degradation_id == degradation_id


@pytest.mark.parametrize("degradation_id", DEGRADATION_IDS)
def test_result_degradation_version_matches_constant(tmp_path: Path, degradation_id: str) -> None:
    wav = _make_wav(tmp_path)
    out_dir = tmp_path / f"out_{degradation_id}"
    result = apply_degradation(degradation_id, wav, out_dir, seed=0)
    assert result.degradation_version == _versions.DEGRADATION_VERSION


# ---------------------------------------------------------------------------
# Determinism and output directory
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_seed_produces_identical_arrays(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result_a = apply_degradation("broadband_hiss", wav, tmp_path / "a", seed=0)
        result_b = apply_degradation("broadband_hiss", wav, tmp_path / "b", seed=0)
        arr_a, _ = sf.read(result_a.output_path, dtype="float64")
        arr_b, _ = sf.read(result_b.output_path, dtype="float64")
        assert np.allclose(arr_a, arr_b)

    def test_different_seeds_produce_different_arrays(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result_0 = apply_degradation("broadband_hiss", wav, tmp_path / "seed0", seed=0)
        result_1 = apply_degradation("broadband_hiss", wav, tmp_path / "seed1", seed=1)
        arr_0, _ = sf.read(result_0.output_path, dtype="float64")
        arr_1, _ = sf.read(result_1.output_path, dtype="float64")
        assert not np.allclose(arr_0, arr_1)

    def test_output_written_to_output_dir(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        result = apply_degradation("muffled", wav, out_dir, seed=0)
        assert result.output_path.parent == out_dir


# ---------------------------------------------------------------------------
# DegradationResult structure
# ---------------------------------------------------------------------------


class TestDegradationResult:
    def test_params_applied_matches_spec_params(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_degradation("phone_call", wav, tmp_path / "out", seed=0)
        spec = DEGRADATION_REGISTRY["phone_call"]
        assert result.params_applied == dict(spec.params)

    def test_result_is_frozen(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_degradation("muffled", wav, tmp_path / "out", seed=0)
        assert isinstance(result, DegradationResult)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.degradation_id = "other"  # type: ignore[misc]
