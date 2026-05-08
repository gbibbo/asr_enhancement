"""Robust ASR shared metrics: WER, CER, Word Accuracy, paired bootstrap CI.

Produced by P1.2 per docs/plans/robust_asr_agent_plan_v3_4_7.md
Section 3 ("WA = 1 - WER. All comparisons use normalized reference
and normalized transcript.") and Section 4 (paired bootstrap CI
helpers).

Distinct from libs/audio/metrics.py (training profile), which remains
the read-only training-branch metrics module. libs/common.metrics is
the canonical robust_asr metrics module; all robust_asr backends and
evaluation scripts must import from here.

Both reference and hypothesis are normalized through
`libs.common.normalization.normalize_text` before tokenization. WER
operates on whitespace-split word tokens; CER operates on the
normalized character sequence with whitespace preserved as tokens.
"""

from __future__ import annotations

import random
from typing import Iterable, List, Sequence, Tuple

from libs.common.normalization import normalize_text

__all__ = [
    "wer",
    "cer",
    "wa",
    "paired_bootstrap_ci",
    "paired_bootstrap_ci_delta",
]


def _levenshtein(a: Sequence, b: Sequence) -> int:
    n_a = len(a)
    n_b = len(b)
    if n_a == 0:
        return n_b
    if n_b == 0:
        return n_a
    dp = list(range(n_b + 1))
    for i in range(1, n_a + 1):
        prev = dp[:]
        dp[0] = i
        ai = a[i - 1]
        for j in range(1, n_b + 1):
            if ai == b[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j - 1], prev[j], dp[j - 1])
    return dp[n_b]


def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate on normalized inputs.

    Returns 1.0 if the normalized reference is empty and the hypothesis
    is non-empty, 0.0 if both are empty. Raw float; may exceed 1.0 when
    insertions outnumber reference words.
    """
    ref_tokens = normalize_text(reference).split()
    hyp_tokens = normalize_text(hypothesis).split()
    n_ref = len(ref_tokens)
    if n_ref == 0:
        return 0.0 if not hyp_tokens else 1.0
    return _levenshtein(ref_tokens, hyp_tokens) / n_ref


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate on normalized inputs.

    Operates on the normalized character sequence including spaces.
    Returns 1.0 if the normalized reference is empty and hypothesis
    non-empty, 0.0 if both are empty.
    """
    ref_chars = normalize_text(reference)
    hyp_chars = normalize_text(hypothesis)
    n_ref = len(ref_chars)
    if n_ref == 0:
        return 0.0 if not hyp_chars else 1.0
    return _levenshtein(ref_chars, hyp_chars) / n_ref


def wa(reference_or_wer, hypothesis: str = None) -> float:
    """Word Accuracy = max(0, 1 - WER). Clamped to [0, 1].

    Two call modes:
      - ``wa(reference_str, hypothesis_str)``  -> compute then clamp.
      - ``wa(wer_value)``                       -> clamp an existing WER.
    """
    if hypothesis is None:
        return max(0.0, min(1.0, 1.0 - float(reference_or_wer)))
    return max(0.0, min(1.0, 1.0 - wer(reference_or_wer, hypothesis)))


def _percentile(values: List[float], q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def paired_bootstrap_ci(
    values: Sequence[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """Bootstrap CI for the mean of a paired-sample vector.

    Use for a single backend's per-utterance metric (e.g. mean WER on a
    locked test set). Resamples utterance indices with replacement.

    Returns ``(mean, lo, hi)`` at the requested two-sided confidence
    level. Deterministic given the seed.
    """
    n = len(values)
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    means: List[float] = []
    for _ in range(n_resamples):
        s = 0.0
        for _ in range(n):
            s += values[rng.randrange(n)]
        means.append(s / n)
    alpha = (1.0 - confidence) / 2.0
    lo = _percentile(means, alpha)
    hi = _percentile(means, 1.0 - alpha)
    mean = sum(values) / n
    return (mean, lo, hi)


def paired_bootstrap_ci_delta(
    a: Sequence[float],
    b: Sequence[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """Paired bootstrap CI for ``mean(a) - mean(b)``.

    Inputs must be aligned (one entry per utterance); resamples a
    common index set so both vectors are perturbed identically per
    resample, preserving pairing.

    Returns ``(delta_mean, lo, hi)`` at the requested two-sided
    confidence level. Deterministic given the seed.
    """
    n = len(a)
    if n == 0 or len(b) != n:
        raise ValueError("a and b must be non-empty and the same length")
    rng = random.Random(seed)
    deltas: List[float] = []
    for _ in range(n_resamples):
        s = 0.0
        for _ in range(n):
            i = rng.randrange(n)
            s += a[i] - b[i]
        deltas.append(s / n)
    alpha = (1.0 - confidence) / 2.0
    lo = _percentile(deltas, alpha)
    hi = _percentile(deltas, 1.0 - alpha)
    delta_mean = (sum(a) - sum(b)) / n
    return (delta_mean, lo, hi)
