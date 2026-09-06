from __future__ import annotations

import io
import wave
from pathlib import Path

import pytest

from libs.audio.enhancement import (
    BYPASS_ENHANCER_VERSION,
    METRICGAN_PLUS_ENHANCER_VERSION,
    BypassEnhancer,
    EnhancerAdapter,
    EnhancementResult,
    MetricGANPlusEnhancer,
)


def _make_minimal_wav(path: Path) -> None:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x01" * 1600)
    path.write_bytes(buf.getvalue())


# ---------------------------------------------------------------------------
# EnhancerAdapter (abstract)
# ---------------------------------------------------------------------------

def test_enhancer_adapter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        EnhancerAdapter()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# BypassEnhancer
# ---------------------------------------------------------------------------

def test_bypass_enhancer_is_subclass_of_enhancer_adapter():
    assert issubclass(BypassEnhancer, EnhancerAdapter)


def test_bypass_enhancer_version_string():
    assert BypassEnhancer().enhancer_version == "bypass"


def test_bypass_enhancer_version_constant():
    assert BYPASS_ENHANCER_VERSION == "bypass"


def test_bypass_enhancer_version_matches_constant():
    assert BypassEnhancer().enhancer_version == BYPASS_ENHANCER_VERSION


def test_bypass_enhancer_enhance_returns_enhancement_result(tmp_path: Path):
    wav = tmp_path / "input.wav"
    _make_minimal_wav(wav)
    result = BypassEnhancer().enhance(wav, tmp_path / "out", "job-bypass-01")
    assert isinstance(result, EnhancementResult)


def test_bypass_enhancer_enhance_enhanced_is_false(tmp_path: Path):
    wav = tmp_path / "input.wav"
    _make_minimal_wav(wav)
    result = BypassEnhancer().enhance(wav, tmp_path / "out", "job-bypass-02")
    assert result.enhanced is False


def test_bypass_enhancer_enhance_fallback_is_false(tmp_path: Path):
    wav = tmp_path / "input.wav"
    _make_minimal_wav(wav)
    result = BypassEnhancer().enhance(wav, tmp_path / "out", "job-bypass-03")
    assert result.enhancement_fallback is False


def test_bypass_enhancer_enhance_output_path_is_input_path(tmp_path: Path):
    wav = tmp_path / "input.wav"
    _make_minimal_wav(wav)
    result = BypassEnhancer().enhance(wav, tmp_path / "out", "job-bypass-04")
    assert result.output_path == wav


# ---------------------------------------------------------------------------
# MetricGANPlusEnhancer
# ---------------------------------------------------------------------------

def test_metricgan_plus_enhancer_is_subclass_of_enhancer_adapter():
    assert issubclass(MetricGANPlusEnhancer, EnhancerAdapter)


def test_metricgan_plus_enhancer_version_is_nonempty_string():
    v = MetricGANPlusEnhancer().enhancer_version
    assert isinstance(v, str) and len(v) > 0


def test_metricgan_plus_enhancer_version_constant():
    assert METRICGAN_PLUS_ENHANCER_VERSION == "metricgan_plus_pretrained"


def test_metricgan_plus_enhancer_version_matches_constant():
    assert MetricGANPlusEnhancer().enhancer_version == METRICGAN_PLUS_ENHANCER_VERSION


def test_metricgan_plus_enhancer_enhance_raises_not_implemented(tmp_path: Path):
    wav = tmp_path / "input.wav"
    _make_minimal_wav(wav)
    with pytest.raises(NotImplementedError):
        MetricGANPlusEnhancer().enhance(wav, tmp_path / "out", "job-mgp-01")


def test_both_share_enhance_method():
    for cls in (BypassEnhancer, MetricGANPlusEnhancer):
        assert callable(getattr(cls, "enhance", None))


# ---------------------------------------------------------------------------
# Package-level exports from libs.audio
# ---------------------------------------------------------------------------

def test_package_level_exports_importable():
    from libs.audio import (  # noqa: F401
        BYPASS_ENHANCER_VERSION,
        METRICGAN_PLUS_ENHANCER_VERSION,
        BypassEnhancer,
        EnhancerAdapter,
        MetricGANPlusEnhancer,
    )
    assert BYPASS_ENHANCER_VERSION == "bypass"
    assert METRICGAN_PLUS_ENHANCER_VERSION == "metricgan_plus_pretrained"
    assert issubclass(BypassEnhancer, EnhancerAdapter)
    assert issubclass(MetricGANPlusEnhancer, EnhancerAdapter)
