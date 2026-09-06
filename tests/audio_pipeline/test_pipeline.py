from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from libs.audio_pipeline.errors import UnknownPresetError
from libs.audio_pipeline.pipeline import EnhancementResult, apply_preset

# ---------------------------------------------------------------------------
# Fixture helper
# ---------------------------------------------------------------------------

def _make_wav(tmp_path: Path, *, sr: int = 16000, duration: float = 0.1, silent: bool = False) -> Path:
    n = int(sr * duration)
    if silent:
        samples = np.zeros(n, dtype=np.float64)
    else:
        samples = (0.5 * np.sin(2 * np.pi * 440 * np.arange(n) / sr)).astype(np.float64)
    p = tmp_path / "input.wav"
    sf.write(p, samples, sr)
    return p


# ---------------------------------------------------------------------------
# bypass
# ---------------------------------------------------------------------------

class TestBypass:
    def test_returns_input_path(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("bypass", wav, tmp_path / "out")
        assert result.output_path == wav

    def test_enhanced_is_false(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("bypass", wav, tmp_path / "out")
        assert result.enhanced is False

    def test_fallback_is_false(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("bypass", wav, tmp_path / "out")
        assert result.enhancement_fallback is False

    def test_preset_applied_is_bypass(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("bypass", wav, tmp_path / "out")
        assert result.preset_applied == "bypass"

    def test_diagnostic_is_empty(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("bypass", wav, tmp_path / "out")
        assert result.diagnostic == {}

    def test_does_not_create_output_dir(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        apply_preset("bypass", wav, out_dir)
        assert not out_dir.exists()

    def test_result_is_enhancement_result(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("bypass", wav, tmp_path / "out")
        assert isinstance(result, EnhancementResult)


# ---------------------------------------------------------------------------
# light_clean
# ---------------------------------------------------------------------------

class TestLightClean:
    def test_creates_output_dir_when_missing(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        assert not out_dir.exists()
        apply_preset("light_clean", wav, out_dir)
        assert out_dir.exists()

    def test_output_path_differs_from_input(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        assert result.output_path != wav

    def test_output_file_is_inside_output_dir(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        result = apply_preset("light_clean", wav, out_dir)
        assert result.output_path.parent == out_dir

    def test_output_is_valid_wav(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        info = sf.info(result.output_path)
        assert info.frames > 0

    def test_enhanced_is_true(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        assert result.enhanced is True

    def test_fallback_is_false(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        assert result.enhancement_fallback is False

    def test_peak_near_095(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        samples, _ = sf.read(result.output_path, dtype="float64")
        assert abs(float(np.max(np.abs(samples))) - 0.95) < 0.02

    def test_silent_audio_no_exception(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path, silent=True)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        assert isinstance(result, EnhancementResult)

    def test_output_preserves_sample_rate(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path, sr=8000)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        assert sf.info(result.output_path).samplerate == 8000

    def test_diagnostic_is_empty(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("light_clean", wav, tmp_path / "out")
        assert result.diagnostic == {}


# ---------------------------------------------------------------------------
# denoise
# ---------------------------------------------------------------------------

class TestDenoise:
    def test_creates_output_dir_when_missing(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        assert not out_dir.exists()
        apply_preset("denoise", wav, out_dir)
        assert out_dir.exists()

    def test_output_file_is_inside_output_dir(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        result = apply_preset("denoise", wav, out_dir)
        assert result.output_path.parent == out_dir

    def test_output_is_valid_wav(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise", wav, tmp_path / "out")
        assert sf.info(result.output_path).frames > 0

    def test_enhanced_is_true(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise", wav, tmp_path / "out")
        assert result.enhanced is True

    def test_fallback_is_false(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise", wav, tmp_path / "out")
        assert result.enhancement_fallback is False

    def test_diagnostic_is_empty(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise", wav, tmp_path / "out")
        assert result.diagnostic == {}

    def test_output_preserves_sample_rate(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path, sr=8000)
        result = apply_preset("denoise", wav, tmp_path / "out")
        assert sf.info(result.output_path).samplerate == 8000


# ---------------------------------------------------------------------------
# denoise_dereverb
# ---------------------------------------------------------------------------

class TestDenoiseDeReverb:
    def test_creates_output_dir_when_missing(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        assert not out_dir.exists()
        apply_preset("denoise_dereverb", wav, out_dir)
        assert out_dir.exists()

    def test_output_file_is_inside_output_dir(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        out_dir = tmp_path / "out"
        result = apply_preset("denoise_dereverb", wav, out_dir)
        assert result.output_path.parent == out_dir

    def test_output_is_valid_wav(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise_dereverb", wav, tmp_path / "out")
        assert sf.info(result.output_path).frames > 0

    def test_enhanced_is_true(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise_dereverb", wav, tmp_path / "out")
        assert result.enhanced is True

    def test_fallback_is_false(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise_dereverb", wav, tmp_path / "out")
        assert result.enhancement_fallback is False

    def test_diagnostic_contains_dereverb_applied_false(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        result = apply_preset("denoise_dereverb", wav, tmp_path / "out")
        assert result.diagnostic.get("dereverb_applied") is False


# ---------------------------------------------------------------------------
# error handling and fallback
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_unknown_preset_raises_unknown_preset_error(self, tmp_path: Path) -> None:
        wav = _make_wav(tmp_path)
        with pytest.raises(UnknownPresetError):
            apply_preset("not_a_preset", wav, tmp_path / "out")

    def test_corrupt_input_triggers_fallback(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.wav"
        corrupt.write_bytes(b"not a wav file at all")
        result = apply_preset("light_clean", corrupt, tmp_path / "out")
        assert result.enhancement_fallback is True

    def test_fallback_output_path_is_input_path(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.wav"
        corrupt.write_bytes(b"not a wav file at all")
        result = apply_preset("light_clean", corrupt, tmp_path / "out")
        assert result.output_path == corrupt

    def test_fallback_has_fallback_reason_in_diagnostic(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.wav"
        corrupt.write_bytes(b"not a wav file at all")
        result = apply_preset("light_clean", corrupt, tmp_path / "out")
        assert "fallback_reason" in result.diagnostic

    def test_fallback_enhanced_is_false(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.wav"
        corrupt.write_bytes(b"not a wav file at all")
        result = apply_preset("denoise", corrupt, tmp_path / "out")
        assert result.enhanced is False
