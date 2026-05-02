"""Tests for libs.audio.metrics — WER, Word Accuracy, normalization."""
from __future__ import annotations

import pytest

from libs.audio.metrics import METRICS_VERSION, normalize_text, word_accuracy, word_error_rate
from libs.common.versions import METRICS_VERSION as VERSIONS_METRICS_VERSION


def test_metrics_version_single_source_of_truth():
    assert METRICS_VERSION == VERSIONS_METRICS_VERSION == "metrics_v1"


def test_normalize_text_basic():
    assert normalize_text("Hello, World!") == "hello world"


def test_normalize_text_apostrophe_removed():
    assert normalize_text("don't") == "dont"


def test_normalize_text_numbers_kept():
    assert normalize_text("Room 101") == "room 101"


def test_normalize_text_extra_spaces():
    assert normalize_text("  a   b  ") == "a b"


def test_normalize_text_empty():
    assert normalize_text("") == ""


def test_wer_exact_match():
    assert word_error_rate("a b c d", "a b c d") == 0.0


def test_wer_one_substitution():
    result = word_error_rate("a b c d", "a b x d")
    assert abs(result - 0.25) < 1e-9


def test_wer_one_deletion():
    result = word_error_rate("a b c d", "a b c")
    assert abs(result - 0.25) < 1e-9


def test_wer_one_insertion():
    result = word_error_rate("a b c d", "a b c d e")
    assert abs(result - 0.25) < 1e-9


def test_wer_all_wrong():
    result = word_error_rate("a b c d", "x y z w")
    assert abs(result - 1.0) < 1e-9


def test_wer_empty_reference():
    assert word_error_rate("", "") == 0.0
    assert word_error_rate("", "some words") == 1.0


def test_wer_case_and_punct_normalized():
    assert word_error_rate("HELLO WORLD", "hello world") == 0.0
    assert word_error_rate("Hello, world!", "hello world") == 0.0


def test_word_accuracy_perfect():
    assert word_accuracy(0.0) == 1.0


def test_word_accuracy_zero():
    assert word_accuracy(1.0) == 0.0


def test_word_accuracy_clamp_negative():
    assert word_accuracy(1.25) == 0.0


def test_word_accuracy_partial():
    result = word_accuracy(0.25)
    assert abs(result - 0.75) < 1e-9
