"""Tests for libs.audio.degradations (T3.2a).

Cover module-level constants, raw family signatures, and the apply_degradation
helper's contracts: length preservation, finiteness, peak normalization, and
correct seed semantics for stochastic vs deterministic families.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pytest

from libs.audio.degradations import (
    DEGRADATION_FAMILIES,
    DEGRADATION_FAMILIES_DETERMINISTIC,
    DEGRADATION_FAMILIES_STOCHASTIC,
    DEGRADATION_PARAMS,
    DEGRADATION_VERSION,
    ZeroSpeechRmsError,
    apply_degradation,
    utterance_seed,
)


SR = 16000
DURATION_S = 1.0


def _tone(seed: int = 0, freq_hz: float = 440.0, duration_s: float = DURATION_S) -> np.ndarray:
    n = int(duration_s * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    base = 0.3 * np.sin(2 * np.pi * freq_hz * t)
    base += 0.05 * rng.standard_normal(n)
    return base.astype(np.float64)


def _sha(arr: np.ndarray) -> str:
    return hashlib.sha256(arr.tobytes()).hexdigest()


def test_degradation_version_constant():
    assert DEGRADATION_VERSION == "degradation_v1"


def test_family_registry_keys():
    expected = {
        "broadband_hiss",
        "cafe_background",
        "far_field_room",
        "muffled",
        "phone_call",
    }
    assert set(DEGRADATION_FAMILIES) == expected
    assert DEGRADATION_FAMILIES_STOCHASTIC == frozenset(
        {"far_field_room", "cafe_background", "broadband_hiss"}
    )
    assert DEGRADATION_FAMILIES_DETERMINISTIC == frozenset({"phone_call", "muffled"})
    assert (
        DEGRADATION_FAMILIES_STOCHASTIC | DEGRADATION_FAMILIES_DETERMINISTIC
        == set(DEGRADATION_FAMILIES)
    )
    assert set(DEGRADATION_PARAMS) == set(DEGRADATION_FAMILIES)


@pytest.mark.parametrize("family", sorted(DEGRADATION_FAMILIES))
def test_raw_family_runs_and_is_finite(family):
    samples = _tone()
    fn = DEGRADATION_FAMILIES[family]
    rng = np.random.default_rng(42)
    out = fn(samples, SR, rng)
    assert isinstance(out, np.ndarray)
    assert out.ndim == 1
    assert out.size > 0
    assert np.isfinite(out).all()


@pytest.mark.parametrize("family", sorted(DEGRADATION_FAMILIES))
def test_apply_degradation_contract(family):
    samples = _tone()
    out = apply_degradation(samples, SR, family, "test-utt-001")
    assert out.ndim == 1
    assert len(out) == len(samples)
    assert np.isfinite(out).all()
    assert float(np.max(np.abs(out))) <= 0.95001


@pytest.mark.parametrize("family", sorted(DEGRADATION_FAMILIES))
def test_apply_degradation_same_utterance_id_is_deterministic(family):
    samples = _tone()
    out1 = apply_degradation(samples, SR, family, "utt-A")
    out2 = apply_degradation(samples, SR, family, "utt-A")
    assert _sha(out1) == _sha(out2)


@pytest.mark.parametrize("family", sorted(DEGRADATION_FAMILIES_STOCHASTIC))
def test_stochastic_family_changes_with_utterance_id(family):
    samples = _tone()
    out_a = apply_degradation(samples, SR, family, "utt-A")
    out_b = apply_degradation(samples, SR, family, "utt-B")
    assert _sha(out_a) != _sha(out_b)


@pytest.mark.parametrize("family", sorted(DEGRADATION_FAMILIES_DETERMINISTIC))
def test_deterministic_family_ignores_utterance_id(family):
    samples = _tone()
    out_a = apply_degradation(samples, SR, family, "utt-A")
    out_b = apply_degradation(samples, SR, family, "utt-B")
    assert _sha(out_a) == _sha(out_b)


def test_zero_rms_input_raises():
    silent = np.zeros(SR, dtype=np.float64)
    with pytest.raises(ZeroSpeechRmsError):
        apply_degradation(silent, SR, "broadband_hiss", "utt-silent")


def test_invalid_sr_raises():
    samples = _tone()
    with pytest.raises(ValueError):
        apply_degradation(samples, 8000, "muffled", "utt-X")


def test_unknown_family_raises():
    samples = _tone()
    with pytest.raises(KeyError):
        apply_degradation(samples, SR, "nonexistent_family", "utt-X")


def test_non_finite_input_raises():
    samples = _tone()
    samples[0] = np.nan
    with pytest.raises(ValueError):
        apply_degradation(samples, SR, "muffled", "utt-X")


def test_utterance_seed_is_deterministic_and_uint64():
    s1 = utterance_seed("utt-1", "muffled")
    s2 = utterance_seed("utt-1", "muffled")
    s3 = utterance_seed("utt-2", "muffled")
    s4 = utterance_seed("utt-1", "phone_call")
    assert s1 == s2
    assert s1 != s3
    assert s1 != s4
    assert 0 <= s1 < 2 ** 64
