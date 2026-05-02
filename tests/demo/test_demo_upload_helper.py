from __future__ import annotations

import asyncio
import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from libs.demo.upload import (
    DEMO_ALLOWED_EXTENSIONS,
    FileTooLargeError,
    UnsupportedExtensionError,
    save_upload,
)


def _make_upload(content: bytes, filename: str = "test.wav") -> MagicMock:
    mock = MagicMock()
    mock.filename = filename
    buf = io.BytesIO(content)

    async def read(size: int = -1) -> bytes:
        return buf.read(size)

    mock.read = read
    return mock


def test_wav_extension_accepted(tmp_path):
    upload = _make_upload(b"x" * 100, filename="audio.wav")
    path, ext = asyncio.run(save_upload(upload, tmp_path, limit_bytes=10_000))
    assert ext == ".wav"
    assert path.exists()


def test_mp3_extension_accepted(tmp_path):
    upload = _make_upload(b"x" * 100, filename="audio.mp3")
    path, ext = asyncio.run(save_upload(upload, tmp_path, limit_bytes=10_000))
    assert ext == ".mp3"
    assert path.exists()


def test_disallowed_extension_raises(tmp_path):
    upload = _make_upload(b"data", filename="audio.txt")
    with pytest.raises(UnsupportedExtensionError):
        asyncio.run(save_upload(upload, tmp_path, limit_bytes=10_000))


def test_no_extension_raises(tmp_path):
    upload = _make_upload(b"data", filename="audiofile")
    with pytest.raises(UnsupportedExtensionError):
        asyncio.run(save_upload(upload, tmp_path, limit_bytes=10_000))


def test_file_too_large_raises(tmp_path):
    upload = _make_upload(b"x" * 20, filename="audio.wav")
    with pytest.raises(FileTooLargeError):
        asyncio.run(save_upload(upload, tmp_path, limit_bytes=5))


def test_file_within_limit_accepted(tmp_path):
    upload = _make_upload(b"x" * 10, filename="audio.wav")
    path, ext = asyncio.run(save_upload(upload, tmp_path, limit_bytes=100))
    assert path.exists()
    assert ext == ".wav"


def test_saved_filename_does_not_contain_original_name(tmp_path):
    upload = _make_upload(b"x" * 10, filename="my_recording.wav")
    path, _ = asyncio.run(save_upload(upload, tmp_path, limit_bytes=1000))
    assert "my_recording" not in path.name


def test_saved_file_exists_and_no_tmp_left(tmp_path):
    upload = _make_upload(b"x" * 10, filename="audio.wav")
    path, _ = asyncio.run(save_upload(upload, tmp_path, limit_bytes=1000))
    assert path.exists()
    tmp_files = [f for f in tmp_path.iterdir() if f.suffix == ".tmp"]
    assert tmp_files == []


def test_no_partial_file_left_on_size_error(tmp_path):
    upload = _make_upload(b"x" * 100, filename="audio.wav")
    with pytest.raises(FileTooLargeError):
        asyncio.run(save_upload(upload, tmp_path, limit_bytes=5))
    remaining = [f for f in tmp_path.iterdir() if f.is_file()]
    assert remaining == []
