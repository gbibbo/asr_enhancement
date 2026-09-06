from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import libs.common.versions as versions


@dataclass(frozen=True)
class MetricsResult:
    wer: Optional[float]
    word_accuracy: Optional[float]
    metrics_version: str
    available: bool


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _word_edit_distance(ref_tokens: List[str], hyp_tokens: List[str]) -> int:
    r, h = len(ref_tokens), len(hyp_tokens)
    row = list(range(h + 1))
    for i in range(1, r + 1):
        new_row = [i] + [0] * h
        for j in range(1, h + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                new_row[j] = row[j - 1]
            else:
                new_row[j] = 1 + min(row[j - 1], row[j], new_row[j - 1])
        row = new_row
    return row[h]


def compute_metrics(
    hypothesis: str,
    reference: Optional[str],
) -> MetricsResult:
    if reference is None:
        return MetricsResult(
            wer=None,
            word_accuracy=None,
            metrics_version=versions.METRICS_VERSION,
            available=False,
        )

    norm_ref = normalize_text(reference)
    if not norm_ref:
        return MetricsResult(
            wer=None,
            word_accuracy=None,
            metrics_version=versions.METRICS_VERSION,
            available=False,
        )

    norm_hyp = normalize_text(hypothesis)
    ref_tokens = norm_ref.split()
    hyp_tokens = norm_hyp.split()

    edit_dist = _word_edit_distance(ref_tokens, hyp_tokens)
    wer_value = edit_dist / len(ref_tokens)
    word_accuracy = max(0.0, min(1.0, 1.0 - wer_value))

    return MetricsResult(
        wer=wer_value,
        word_accuracy=word_accuracy,
        metrics_version=versions.METRICS_VERSION,
        available=True,
    )
