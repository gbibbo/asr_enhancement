"""rp5_inference.py — robust_asr deterministic selector (Outcome E).

Stdlib-only wrapper around the Section 5.5 deterministic_select
predicate. Constants are loaded from the sibling
deterministic_selector.json so that runtime behavior cannot drift from
the packaged metadata.

Public API:

    predict(decode_features, assemblyai_available=False) -> dict
        Returns {"action", "confidence", "reason"}.

    selector_constants() -> dict
        Returns the loaded constants (read-only view).

This module is imported by the RP5 runtime; it MUST NOT import any
third-party packages.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent
_CFG_PATH = _HERE / "deterministic_selector.json"

ACTION_BASELINE = "whisper_base_ct2_int8"
ACTION_CLOUD = "assemblyai"
ACTION_ASK_REPEAT = "ask_repeat"


def _load_cfg() -> Dict[str, Any]:
    with _CFG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


_CFG = _load_cfg()
_CONSTANTS = dict(_CFG["constants"])


def selector_constants() -> Dict[str, Any]:
    """Return a copy of the loaded Section 5.5 constants."""
    return dict(_CONSTANTS)


def predict(
    decode_features: Dict[str, Any],
    assemblyai_available: bool = False,
) -> Dict[str, Any]:
    """Apply the Section 5.5 deterministic selector.

    decode_features: mapping with optional keys
        "no_speech_prob" (float; default 0.0) and
        "avg_logprob"    (float; default 0.0).
    assemblyai_available: runtime probe result. Defaults to False to
        match OUTCOME_E_DETERMINISTIC_SELECTOR (BLOCKED_API).

    Returns a dict {"action", "confidence", "reason"}. The selector is
    deterministic, so confidence is always 1.0; "reason" identifies the
    Section 5.5 branch that fired.
    """
    no_speech_prob = float(decode_features.get("no_speech_prob", 0.0))
    avg_logprob = float(decode_features.get("avg_logprob", 0.0))

    no_speech_threshold = _CONSTANTS["no_speech_threshold"]
    ask_repeat_threshold = _CONSTANTS["ask_repeat_threshold"]
    escalate_threshold = _CONSTANTS["escalate_threshold"]

    if no_speech_prob > no_speech_threshold:
        return {
            "action": ACTION_ASK_REPEAT,
            "confidence": 1.0,
            "reason": "no_speech",
        }
    if avg_logprob < ask_repeat_threshold:
        return {
            "action": ACTION_ASK_REPEAT,
            "confidence": 1.0,
            "reason": "low_logprob",
        }
    if assemblyai_available and avg_logprob < escalate_threshold:
        return {
            "action": ACTION_CLOUD,
            "confidence": 1.0,
            "reason": "escalate_cloud",
        }
    return {
        "action": ACTION_BASELINE,
        "confidence": 1.0,
        "reason": "baseline",
    }
