"""P1.2 — Tests for shared normalization and metrics.

Covers:
  - normalize_text idempotence and Section 3 normalization invariants.
  - WER, CER, WA correctness on hand-checked inputs.
  - paired_bootstrap_ci / paired_bootstrap_ci_delta shape, determinism,
    and bracket containment.
  - NORMALIZATION_VERSION constant present and stable.
"""

from __future__ import annotations

import math

import pytest

from libs.common.metrics import (
    cer,
    paired_bootstrap_ci,
    paired_bootstrap_ci_delta,
    wa,
    wer,
)
from libs.common.normalization import NORMALIZATION_VERSION, normalize_text
from libs.common import versions as _versions


# --- Normalization ---------------------------------------------------------


def test_normalization_version_constant_present() -> None:
    assert isinstance(NORMALIZATION_VERSION, str) and NORMALIZATION_VERSION
    assert NORMALIZATION_VERSION == _versions.NORMALIZATION_VERSION
    assert NORMALIZATION_VERSION == "normalization_v1"


def test_normalize_idempotent() -> None:
    samples = [
        "Hello, World!",
        "The quick BROWN fox.",
        "  spaced   out\ttext\n",
        "smart “quotes” and — dashes",
        "Café noise 12.34%",
        "",
        "....",
    ]
    for s in samples:
        first = normalize_text(s)
        second = normalize_text(first)
        assert first == second, f"normalize not idempotent on: {s!r}"


def test_normalize_lowercase_and_punctuation_strip() -> None:
    assert normalize_text("Hello, World!") == "hello world"
    assert normalize_text("It's, you know.") == "it s you know"
    assert normalize_text("  Multiple   spaces\t\n") == "multiple spaces"


def test_normalize_keeps_digits() -> None:
    assert normalize_text("Track 7, side B") == "track 7 side b"


def test_normalize_empty_and_pure_punctuation() -> None:
    assert normalize_text("") == ""
    assert normalize_text("???") == ""
    assert normalize_text(None) == ""


def test_normalize_unicode_nfkc() -> None:
    # full-width digits collapse to ASCII via NFKC + the [a-z0-9 ] keep-set.
    assert normalize_text("１２３") == "123"


# --- WER / CER / WA --------------------------------------------------------


def test_wer_perfect_match() -> None:
    assert wer("hello world", "hello world") == 0.0


def test_wer_one_substitution_two_words() -> None:
    # "the cat" vs "the dog" -> 1 sub / 2 ref tokens = 0.5
    assert wer("the cat", "the dog") == pytest.approx(0.5)


def test_wer_one_insertion() -> None:
    # ref 2 tokens, hyp inserts one extra -> 1 / 2 = 0.5
    assert wer("the cat", "the cat sat") == pytest.approx(0.5)


def test_wer_one_deletion() -> None:
    # ref 3 tokens, hyp drops one -> 1 / 3
    assert wer("the cat sat", "the sat") == pytest.approx(1.0 / 3.0)


def test_wer_normalizes_inputs() -> None:
    # punctuation/case differences should not count as errors.
    assert wer("Hello, world!", "hello world") == 0.0


def test_wer_empty_reference_empty_hyp() -> None:
    assert wer("", "") == 0.0


def test_wer_empty_reference_nonempty_hyp() -> None:
    assert wer("", "anything") == 1.0


def test_cer_perfect_match() -> None:
    assert cer("hello", "hello") == 0.0


def test_cer_one_substitution() -> None:
    # "hello" vs "jello" -> 1 / 5
    assert cer("hello", "jello") == pytest.approx(1.0 / 5.0)


def test_cer_normalizes_inputs() -> None:
    assert cer("Hello!", "hello") == 0.0


def test_wa_clamped_and_complementary() -> None:
    assert wa("hello world", "hello world") == 1.0
    assert wa("the cat", "the dog") == pytest.approx(0.5)
    # WA from precomputed WER value:
    assert wa(0.0) == 1.0
    assert wa(1.0) == 0.0
    # Clamp on WER > 1.0 (over-insertion).
    assert wa(1.7) == 0.0


# --- Paired bootstrap CI ---------------------------------------------------


def test_paired_bootstrap_ci_shape_and_bracket() -> None:
    values = [0.1, 0.2, 0.0, 0.3, 0.05, 0.25, 0.15, 0.4, 0.1, 0.2]
    mean, lo, hi = paired_bootstrap_ci(values, n_resamples=400, confidence=0.95, seed=42)
    assert math.isclose(mean, sum(values) / len(values))
    assert lo <= mean <= hi
    assert lo >= min(values) - 1e-9
    assert hi <= max(values) + 1e-9


def test_paired_bootstrap_ci_deterministic() -> None:
    values = [0.0, 0.5, 1.0, 0.25, 0.75]
    a = paired_bootstrap_ci(values, n_resamples=200, seed=7)
    b = paired_bootstrap_ci(values, n_resamples=200, seed=7)
    assert a == b


def test_paired_bootstrap_ci_delta_zero_when_identical() -> None:
    values = [0.1, 0.2, 0.3, 0.4]
    delta_mean, lo, hi = paired_bootstrap_ci_delta(
        values, values, n_resamples=300, seed=0
    )
    assert delta_mean == 0.0
    assert lo == 0.0
    assert hi == 0.0


def test_paired_bootstrap_ci_delta_positive_when_a_larger() -> None:
    a = [0.5, 0.6, 0.7, 0.8, 0.9]
    b = [0.1, 0.2, 0.3, 0.4, 0.5]
    delta_mean, lo, hi = paired_bootstrap_ci_delta(
        a, b, n_resamples=400, seed=11
    )
    assert delta_mean == pytest.approx(0.4)
    assert lo > 0.0
    assert hi > lo


def test_paired_bootstrap_ci_delta_length_mismatch() -> None:
    with pytest.raises(ValueError):
        paired_bootstrap_ci_delta([0.1, 0.2], [0.1], seed=0)
