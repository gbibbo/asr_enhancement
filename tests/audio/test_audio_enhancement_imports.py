from __future__ import annotations

import io
import wave
from pathlib import Path

import pytest


def _make_minimal_wav(path: Path) -> None:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x01" * 1600)  # 0.1 s at 16 kHz, 16-bit, non-silent
    path.write_bytes(buf.getvalue())


def test_apply_preset_importable():
    from libs.audio.enhancement import apply_preset  # noqa: F401


def test_enhancement_result_importable():
    from libs.audio.enhancement import EnhancementResult  # noqa: F401


def test_resolve_preset_importable():
    from libs.audio.enhancement import resolve_preset  # noqa: F401


def test_unknown_preset_error_importable():
    from libs.audio.enhancement import UnknownPresetError  # noqa: F401


def test_package_init_importable():
    from libs.audio import apply_preset  # noqa: F401


def test_bypass_roundtrip(tmp_path: Path):
    from libs.audio.enhancement import apply_preset

    input_wav = tmp_path / "input.wav"
    _make_minimal_wav(input_wav)

    result = apply_preset("bypass", input_wav, tmp_path / "out")

    assert result.output_path == input_wav
    assert result.enhanced is False
    assert result.enhancement_fallback is False
    assert result.preset_applied == "bypass"
    assert result.diagnostic == {}
