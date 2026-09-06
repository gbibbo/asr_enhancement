from __future__ import annotations

import libs.common.versions as _versions
from libs.demo.cache import build_cache_key


def test_build_cache_key_is_deterministic():
    kwargs = dict(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
    )
    assert build_cache_key(**kwargs) == build_cache_key(**kwargs)


def test_build_cache_key_contains_all_required_fields():
    key = build_cache_key(
        example_id="my_example",
        degradation_id="noise_snr10",
        asr_provider="assemblyai",
        asr_model_version="best",
    )
    assert "my_example" in key
    assert "noise_snr10" in key
    assert "assemblyai" in key
    assert "best" in key


def test_build_cache_key_includes_degradation_version():
    key = build_cache_key(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
    )
    assert _versions.DEGRADATION_VERSION in key


def test_build_cache_key_includes_metrics_version():
    key = build_cache_key(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
    )
    assert _versions.METRICS_VERSION in key


def test_build_cache_key_reads_degradation_version_from_libs_common(monkeypatch):
    monkeypatch.setattr(_versions, "DEGRADATION_VERSION", "TEST_DV")
    key = build_cache_key(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
    )
    assert "TEST_DV" in key


def test_build_cache_key_reads_metrics_version_from_libs_common(monkeypatch):
    monkeypatch.setattr(_versions, "METRICS_VERSION", "TEST_MV")
    key = build_cache_key(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
    )
    assert "TEST_MV" in key


def test_build_cache_key_defaults_enhancer_version():
    key = build_cache_key(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
        enhancer_version=None,
    )
    assert _versions.DEFAULT_ENHANCER_VERSION in key


def test_build_cache_key_uses_explicit_enhancer_version():
    key = build_cache_key(
        example_id="ex1",
        degradation_id="deg1",
        asr_provider="fake",
        asr_model_version="1.0",
        enhancer_version="custom-1.5",
    )
    assert "custom-1.5" in key
