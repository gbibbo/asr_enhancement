from __future__ import annotations

import asyncio
import io
import wave
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from libs.demo.upload import (
    InvalidAudioError,
    probe_audio_duration,
    save_upload,
    validate_and_save_upload,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLERATE = 16000


def _wav_bytes_for_seconds(seconds: float) -> bytes:
    frames = int(round(seconds * _SAMPLERATE))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_SAMPLERATE)
        w.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def _wav_bytes_for_frames(frames: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_SAMPLERATE)
        w.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def _make_upload(content: bytes, filename: str = "audio.wav") -> MagicMock:
    mock = MagicMock()
    mock.filename = filename
    buf = io.BytesIO(content)

    async def read(size: int = -1) -> bytes:
        return buf.read(size)

    mock.read = read
    return mock


# ---------------------------------------------------------------------------
# probe_audio_duration
# ---------------------------------------------------------------------------

def test_probe_returns_seconds_for_valid_wav(tmp_path):
    p = tmp_path / "one_second.wav"
    p.write_bytes(_wav_bytes_for_seconds(1.0))
    duration = probe_audio_duration(p)
    assert duration == pytest.approx(1.0, abs=1e-3)


def test_probe_returns_seconds_for_30s_wav(tmp_path):
    p = tmp_path / "thirty.wav"
    p.write_bytes(_wav_bytes_for_seconds(30.0))
    duration = probe_audio_duration(p)
    assert duration == pytest.approx(30.0, abs=1e-3)


def test_probe_raises_on_corrupt_audio(tmp_path):
    p = tmp_path / "corrupt.wav"
    p.write_bytes(b"\x00" * 100)
    with pytest.raises(InvalidAudioError) as exc_info:
        probe_audio_duration(p)
    assert "could not be decoded" in str(exc_info.value).lower()


def test_probe_raises_on_random_bytes_with_wav_extension(tmp_path):
    p = tmp_path / "garbage.wav"
    p.write_bytes(b"NOTAWAVEFILE" * 12)
    with pytest.raises(InvalidAudioError):
        probe_audio_duration(p)


def test_probe_raises_on_empty_file(tmp_path):
    p = tmp_path / "empty.wav"
    p.write_bytes(b"")
    with pytest.raises(InvalidAudioError):
        probe_audio_duration(p)


# ---------------------------------------------------------------------------
# validate_and_save_upload — success paths
# ---------------------------------------------------------------------------

def test_validate_accepts_valid_1s_wav(tmp_path):
    upload = _make_upload(_wav_bytes_for_seconds(1.0), filename="clip.wav")
    path, ext, duration = asyncio.run(
        validate_and_save_upload(
            upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
        )
    )
    assert path.exists()
    assert ext == ".wav"
    assert duration == pytest.approx(1.0, abs=1e-3)


def test_validate_accepts_exactly_30s_wav(tmp_path):
    frames = int(30 * _SAMPLERATE)
    upload = _make_upload(_wav_bytes_for_frames(frames), filename="thirty.wav")
    path, _, duration = asyncio.run(
        validate_and_save_upload(
            upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
        )
    )
    assert path.exists()
    assert duration == pytest.approx(30.0, abs=1e-6)


# ---------------------------------------------------------------------------
# validate_and_save_upload — rejection paths
# ---------------------------------------------------------------------------

def test_validate_rejects_just_over_30s(tmp_path):
    frames = int(30 * _SAMPLERATE) + 1
    upload = _make_upload(_wav_bytes_for_frames(frames), filename="too_long.wav")
    with pytest.raises(InvalidAudioError) as exc_info:
        asyncio.run(
            validate_and_save_upload(
                upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
            )
        )
    assert "exceeds 30 seconds" in str(exc_info.value).lower()


def test_validate_rejects_31s_wav(tmp_path):
    upload = _make_upload(_wav_bytes_for_seconds(31.0), filename="long.wav")
    with pytest.raises(InvalidAudioError) as exc_info:
        asyncio.run(
            validate_and_save_upload(
                upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
            )
        )
    assert "exceeds 30 seconds" in str(exc_info.value).lower()


def test_validate_rejects_corrupt_wav(tmp_path):
    upload = _make_upload(b"\x00" * 100, filename="corrupt.wav")
    with pytest.raises(InvalidAudioError) as exc_info:
        asyncio.run(
            validate_and_save_upload(
                upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
            )
        )
    assert "could not be decoded" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# validate_and_save_upload — file cleanup
# ---------------------------------------------------------------------------

def test_validate_unlinks_file_on_too_long(tmp_path):
    frames = int(30 * _SAMPLERATE) + 1
    upload = _make_upload(_wav_bytes_for_frames(frames), filename="too_long.wav")
    with pytest.raises(InvalidAudioError):
        asyncio.run(
            validate_and_save_upload(
                upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
            )
        )
    remaining = [f for f in tmp_path.iterdir() if f.is_file()]
    assert remaining == []


def test_validate_unlinks_file_on_corrupt(tmp_path):
    upload = _make_upload(b"\x00" * 100, filename="corrupt.wav")
    with pytest.raises(InvalidAudioError):
        asyncio.run(
            validate_and_save_upload(
                upload, tmp_path, limit_bytes=5_242_880, max_duration_seconds=30
            )
        )
    remaining = [f for f in tmp_path.iterdir() if f.is_file()]
    assert remaining == []


# ---------------------------------------------------------------------------
# Back-compat: save_upload alone does NOT probe duration
# ---------------------------------------------------------------------------

def test_save_upload_does_not_probe_duration(tmp_path):
    """save_upload must remain a pure size+extension check; duration probing
    only happens in validate_and_save_upload. Verifies B9.1 keeps the layered
    helper API intact."""
    # 31s wav must save through save_upload without raising.
    upload = _make_upload(_wav_bytes_for_seconds(31.0), filename="long.wav")
    path, ext = asyncio.run(save_upload(upload, tmp_path, limit_bytes=5_242_880))
    assert path.exists()
    assert ext == ".wav"
