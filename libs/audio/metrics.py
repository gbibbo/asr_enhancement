"""Shared ASR evaluation metrics for the Surrey training branch.

Provides text normalization, Word Error Rate, and Word Accuracy.
No external library dependencies — self-contained.
"""
from __future__ import annotations

import re

from libs.common.versions import METRICS_VERSION  # single source of truth

__all__ = ["METRICS_VERSION", "normalize_text", "word_error_rate", "word_accuracy"]


def normalize_text(text: str) -> str:
    """Normalize text for WER computation.

    Steps: strip → lowercase → keep only [a-z0-9 ] → collapse spaces → strip.
    Applied identically to both reference and hypothesis.
    """
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r" +", " ", text).strip()
    return text


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate between reference and hypothesis strings.

    Both strings are normalized before tokenization.
    WER = (S + D + I) / max(len(reference_tokens), 1).
    Raw float — may exceed 1.0 when insertions outnumber reference words.
    Returns 1.0 if reference is empty.
    """
    ref_tokens = normalize_text(reference).split()
    hyp_tokens = normalize_text(hypothesis).split()

    n_ref = len(ref_tokens)
    if n_ref == 0:
        return 1.0 if hyp_tokens else 0.0

    n_hyp = len(hyp_tokens)

    # Standard Levenshtein DP on word sequences.
    # dp[i][j] = edit distance between ref_tokens[:i] and hyp_tokens[:j]
    dp = list(range(n_hyp + 1))
    for i in range(1, n_ref + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n_hyp + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j - 1], prev[j], dp[j - 1])

    return dp[n_hyp] / n_ref


def word_accuracy(wer: float) -> float:
    """Compute Word Accuracy from WER, clamped to [0, 1]."""
    return max(0.0, 1.0 - wer)
