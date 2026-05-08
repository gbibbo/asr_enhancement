"""Single shared text normalization for robust_asr.

Section 3 of docs/plans/robust_asr_agent_plan_v3_4_7.md mandates one
normalization function used by every backend (Whisper base CT2 INT8,
Whisper LoRA FP16, Whisper LoRA CT2 INT8, AssemblyAI, router-driven,
deterministic-selector-driven). All WER/CER/WA computations use the
output of `normalize_text` on both reference and hypothesis.

Algorithm (frozen at NORMALIZATION_VERSION = "normalization_v1"):
    1. NFKC Unicode compatibility decomposition.
    2. Lowercase.
    3. Replace any character not in [a-z0-9 ] with a single space.
    4. Collapse runs of whitespace to a single space.
    5. Strip leading and trailing whitespace.

The algorithm is intentionally English-only and ASR-evaluation-shaped:
it removes punctuation, hyphenation, smart quotes, and non-ASCII
glyphs, and preserves digits as digits (no number-words conversion).
This matches the existing libs/audio/metrics.py training-profile
normalizer; the two implementations agree on the LibriSpeech eval
domain. libs/common is now the single source of truth for robust_asr.
"""

from __future__ import annotations

import re
import unicodedata

from libs.common.versions import NORMALIZATION_VERSION

__all__ = ["NORMALIZATION_VERSION", "normalize_text"]

_KEEP_RE = re.compile(r"[^a-z0-9 ]")
_WS_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Normalize a transcript for WER/CER/WA computation.

    Idempotent: ``normalize_text(normalize_text(s)) == normalize_text(s)``.
    Returns the empty string for ``""`` and for any input made entirely
    of punctuation or non-ASCII characters.
    """
    if text is None:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = _KEEP_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text
