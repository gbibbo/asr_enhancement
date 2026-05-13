from __future__ import annotations

import inspect

import pytest

from libs.asr.router_runtime import build_cache_key


_REQUIRED_FIELDS = {
    "audio_hash",
    "selected_backend",
    "asr_model_and_version",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "degradation_version",
    "metrics_or_features_version",
}

_BASELINE = dict(
    audio_hash="sha256_baseline_abc",
    selected_backend="whisper_base_ct2_int8",
    asr_model_and_version="whisper_base:int8",
    router_kind="deterministic_selector",
    router_version="stub-v0",
    routing_profile="balanced",
    allow_third_party=False,
    degradation_version="degradation_v1",
    metrics_or_features_version="1.0",
)

_FORBIDDEN_SUBSTRINGS = [
    "ASSEMBLYAI_API_KEY",
    "http://",
    "https://",
    "hostname",
    "transcript",
    "hypothesis",
    "ground_truth",
    "session_id_hash",
    "raw_payload",
    "@",
]


def test_broute_build_cache_key_has_all_required_fields():
    sig = inspect.signature(build_cache_key)
    assert _REQUIRED_FIELDS.issubset(set(sig.parameters))


def test_broute_build_cache_key_is_deterministic():
    key_a = build_cache_key(**_BASELINE)
    key_b = build_cache_key(**_BASELINE)
    assert key_a == key_b
    assert isinstance(key_a, str)
    assert key_a != ""


@pytest.mark.parametrize(
    "field",
    [
        "audio_hash",
        "selected_backend",
        "asr_model_and_version",
        "router_kind",
        "router_version",
        "routing_profile",
        "degradation_version",
        "metrics_or_features_version",
    ],
)
def test_broute_build_cache_key_sensitive_to_each_string_field(field):
    baseline = build_cache_key(**_BASELINE)
    varied_kwargs = dict(_BASELINE)
    varied_kwargs[field] = _BASELINE[field] + "_VARIED"
    varied = build_cache_key(**varied_kwargs)
    assert varied != baseline, f"key did not change when {field} changed"


def test_broute_build_cache_key_sensitive_to_allow_third_party():
    false_key = build_cache_key(**{**_BASELINE, "allow_third_party": False})
    true_key = build_cache_key(**{**_BASELINE, "allow_third_party": True})
    assert false_key != true_key


def test_broute_build_cache_key_encodes_allow_third_party_boolean_deterministically():
    true_key_a = build_cache_key(**{**_BASELINE, "allow_third_party": True})
    true_key_b = build_cache_key(**{**_BASELINE, "allow_third_party": True})
    false_key_a = build_cache_key(**{**_BASELINE, "allow_third_party": False})
    false_key_b = build_cache_key(**{**_BASELINE, "allow_third_party": False})
    assert true_key_a == true_key_b
    assert false_key_a == false_key_b
    assert true_key_a != false_key_a


def test_broute_build_cache_key_omits_forbidden_content():
    baseline = build_cache_key(**_BASELINE)
    for needle in _FORBIDDEN_SUBSTRINGS:
        assert needle not in baseline, f"forbidden substring {needle!r} appeared in baseline cache key"
