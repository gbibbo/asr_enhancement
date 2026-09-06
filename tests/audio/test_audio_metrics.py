from __future__ import annotations

import dataclasses

import pytest

from libs.audio.metrics import MetricsResult, compute_metrics, normalize_text


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_lowercases(self) -> None:
        assert normalize_text("Hello World") == "hello world"

    def test_removes_punctuation(self) -> None:
        assert normalize_text("hello, world!") == "hello world"

    def test_collapses_whitespace(self) -> None:
        assert normalize_text("a  b   c") == "a b c"

    def test_strips_leading_trailing(self) -> None:
        assert normalize_text("  hi  ") == "hi"

    def test_empty_string(self) -> None:
        assert normalize_text("") == ""


# ---------------------------------------------------------------------------
# compute_metrics — normal cases
# ---------------------------------------------------------------------------

class TestComputeMetricsNormal:
    def test_identical_wer_zero(self) -> None:
        result = compute_metrics("hello world", "hello world")
        assert result.wer == 0.0

    def test_identical_word_accuracy_one(self) -> None:
        result = compute_metrics("hello world", "hello world")
        assert result.word_accuracy == 1.0

    def test_available_true(self) -> None:
        result = compute_metrics("hello world", "hello world")
        assert result.available is True

    def test_returns_metrics_result(self) -> None:
        result = compute_metrics("hello world", "hello world")
        assert isinstance(result, MetricsResult)

    def test_wer_positive_for_different(self) -> None:
        result = compute_metrics("goodbye world", "hello world")
        assert result.wer > 0.0

    def test_word_accuracy_decreases_with_more_errors(self) -> None:
        result_one = compute_metrics("the cat sat on mat", "the cat sat on the mat")
        result_all = compute_metrics("completely wrong text here now", "the cat sat on the mat")
        assert result_one.word_accuracy > result_all.word_accuracy

    def test_case_insensitive(self) -> None:
        result = compute_metrics("HELLO WORLD", "hello world")
        assert result.wer == 0.0

    def test_punctuation_ignored(self) -> None:
        result = compute_metrics("hello, world!", "hello world")
        assert result.wer == 0.0


# ---------------------------------------------------------------------------
# compute_metrics — unavailable reference
# ---------------------------------------------------------------------------

class TestComputeMetricsUnavailable:
    def test_none_reference_available_false(self) -> None:
        result = compute_metrics("hello", None)
        assert result.available is False

    def test_none_reference_wer_is_none(self) -> None:
        result = compute_metrics("hello", None)
        assert result.wer is None

    def test_none_reference_word_accuracy_is_none(self) -> None:
        result = compute_metrics("hello", None)
        assert result.word_accuracy is None

    def test_empty_string_reference_available_false(self) -> None:
        result = compute_metrics("hello", "")
        assert result.available is False

    def test_whitespace_only_reference_available_false(self) -> None:
        result = compute_metrics("hello", "   ")
        assert result.available is False


# ---------------------------------------------------------------------------
# compute_metrics — Word Accuracy bounds and edge cases
# ---------------------------------------------------------------------------

class TestComputeMetricsBoundsAndEdges:
    def test_word_accuracy_not_below_zero(self) -> None:
        # One reference word, hypothesis has many insertions → WER > 1.0
        result = compute_metrics("totally different long sentence here x y z", "cat")
        assert result.word_accuracy >= 0.0

    def test_word_accuracy_not_above_one(self) -> None:
        result = compute_metrics("hello", "hello")
        assert result.word_accuracy <= 1.0

    def test_empty_hypothesis_nonempty_reference(self) -> None:
        result = compute_metrics("", "hello world")
        # All reference words deleted → wer = 1.0, word_accuracy = 0.0
        assert result.available is True
        assert result.wer == 1.0
        assert result.word_accuracy == 0.0

    def test_metrics_version_field(self) -> None:
        import libs.common.versions as _versions
        result = compute_metrics("hello", "hello")
        assert result.metrics_version == _versions.METRICS_VERSION

    def test_wer_and_word_accuracy_complement(self) -> None:
        result = compute_metrics("the cat sat", "the cat mat")
        assert abs(result.word_accuracy - (1.0 - result.wer)) < 1e-9

    def test_frozen_cannot_be_mutated(self) -> None:
        result = compute_metrics("hello", "hello")
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.wer = 0.5  # type: ignore[misc]

    def test_both_empty_after_normalization(self) -> None:
        # Punctuation-only reference → empty after normalization → unavailable
        result = compute_metrics("!!!", "...,,,")
        assert result.available is False
        assert result.wer is None
        assert result.word_accuracy is None
