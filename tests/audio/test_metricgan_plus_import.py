"""Import-only smoke test for the MetricGAN+ pretrained wrapper (T4.1).

This test does not import SpeechBrain. It only verifies that:
  * libs.audio.enhancement imports without SpeechBrain installed,
  * the version constants are stable,
  * MetricGANPlusEnhancer is a concrete EnhancerAdapter that exposes the
    expected enhancer_version,
  * BypassEnhancer keeps its existing version.

Real-WAV runtime validation is deferred to T4.2 / dependency-validation.
"""
from __future__ import annotations

import inspect


def test_module_imports_without_speechbrain():
    import libs.audio.enhancement as mod

    assert hasattr(mod, "EnhancerAdapter")
    assert hasattr(mod, "BypassEnhancer")
    assert hasattr(mod, "MetricGANPlusEnhancer")
    assert hasattr(mod, "EnhancementResult")
    assert hasattr(mod, "BYPASS_ENHANCER_VERSION")
    assert hasattr(mod, "METRICGAN_PLUS_ENHANCER_VERSION")


def test_version_constants():
    from libs.audio.enhancement import (
        BYPASS_ENHANCER_VERSION,
        METRICGAN_PLUS_ENHANCER_VERSION,
    )

    assert BYPASS_ENHANCER_VERSION == "bypass"
    assert METRICGAN_PLUS_ENHANCER_VERSION == "metricgan_plus_pretrained"


def test_metricgan_plus_is_concrete_enhancer_adapter():
    from libs.audio.enhancement import (
        EnhancerAdapter,
        METRICGAN_PLUS_ENHANCER_VERSION,
        MetricGANPlusEnhancer,
    )

    assert issubclass(MetricGANPlusEnhancer, EnhancerAdapter)
    assert not inspect.isabstract(MetricGANPlusEnhancer)
    enhancer = MetricGANPlusEnhancer()
    assert enhancer.enhancer_version == METRICGAN_PLUS_ENHANCER_VERSION


def test_bypass_enhancer_unchanged():
    from libs.audio.enhancement import (
        BYPASS_ENHANCER_VERSION,
        BypassEnhancer,
        EnhancerAdapter,
    )

    assert issubclass(BypassEnhancer, EnhancerAdapter)
    assert BypassEnhancer().enhancer_version == BYPASS_ENHANCER_VERSION
