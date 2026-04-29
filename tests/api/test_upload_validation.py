from __future__ import annotations

import io

import pytest
from starlette.datastructures import Headers, UploadFile

from services.api.app.upload_validation import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    UploadValidationError,
    ValidatedUpload,
    validate_and_buffer_upload,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _make_upload(data: bytes, filename: str, content_type: str | None) -> UploadFile:
    headers = (
        Headers({"content-type": content_type})
        if content_type is not None
        else Headers({})
    )
    return UploadFile(file=io.BytesIO(data), filename=filename, headers=headers)


# --- Per-extension acceptance ---

@pytest.mark.anyio
async def test_valid_wav_accepted(tmp_path):
    up = _make_upload(b"RIFF" + b"\x00" * 40, "clip.wav", "audio/wav")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert isinstance(result, ValidatedUpload)
    assert result.path.exists()
    assert result.extension == ".wav"
    result.path.unlink()


@pytest.mark.anyio
async def test_valid_mp3_accepted(tmp_path):
    up = _make_upload(b"\xff\xfb" + b"\x00" * 40, "clip.mp3", "audio/mpeg")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.extension == ".mp3"
    result.path.unlink()


@pytest.mark.anyio
async def test_valid_m4a_accepted(tmp_path):
    up = _make_upload(b"\x00" * 44, "clip.m4a", "audio/mp4")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.extension == ".m4a"
    result.path.unlink()


@pytest.mark.anyio
async def test_valid_flac_accepted(tmp_path):
    up = _make_upload(b"fLaC" + b"\x00" * 40, "clip.flac", "audio/flac")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.extension == ".flac"
    result.path.unlink()


# --- Content-type policy matrix ---

@pytest.mark.anyio
async def test_allowed_ext_allowed_ct_accepted(tmp_path):
    up = _make_upload(b"\x00" * 10, "clip.wav", "audio/wav")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.path.exists()
    result.path.unlink()


@pytest.mark.anyio
async def test_allowed_ext_missing_ct_accepted(tmp_path):
    up = _make_upload(b"\x00" * 10, "clip.wav", None)
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.path.exists()
    assert result.content_type is None
    result.path.unlink()


@pytest.mark.anyio
async def test_allowed_ext_suspicious_ct_accepted(tmp_path):
    # Cut A: suspicious content type does not override a valid extension
    up = _make_upload(b"\x00" * 10, "clip.wav", "text/plain")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.path.exists()
    assert result.content_type == "text/plain"
    result.path.unlink()


@pytest.mark.anyio
async def test_suspicious_ext_allowed_ct_rejected():
    up = _make_upload(b"\x00" * 10, "clip.pdf", "audio/wav")
    with pytest.raises(UploadValidationError) as exc_info:
        await validate_and_buffer_upload(up, 1_048_576)
    assert exc_info.value.status_code == 415


@pytest.mark.anyio
async def test_suspicious_ext_suspicious_ct_rejected():
    up = _make_upload(b"\x00" * 10, "clip.txt", "text/plain")
    with pytest.raises(UploadValidationError) as exc_info:
        await validate_and_buffer_upload(up, 1_048_576)
    assert exc_info.value.status_code == 415


# --- Content-type parameter normalization ---

@pytest.mark.anyio
async def test_content_type_params_stripped(tmp_path):
    up = _make_upload(b"\x00" * 10, "clip.wav", "audio/wav; codecs=pcm")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.content_type == "audio/wav"
    result.path.unlink()


# --- Extension edge cases ---

@pytest.mark.anyio
async def test_no_extension_rejected():
    up = _make_upload(b"\x00" * 10, "audiofile", "audio/wav")
    with pytest.raises(UploadValidationError) as exc_info:
        await validate_and_buffer_upload(up, 1_048_576)
    assert exc_info.value.status_code == 415


@pytest.mark.anyio
async def test_empty_filename_rejected():
    up = _make_upload(b"\x00" * 10, "", "audio/wav")
    with pytest.raises(UploadValidationError) as exc_info:
        await validate_and_buffer_upload(up, 1_048_576)
    assert exc_info.value.status_code == 415


@pytest.mark.anyio
async def test_uppercase_extension_normalized(tmp_path):
    up = _make_upload(b"\x00" * 10, "AUDIO.WAV", "audio/wav")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.extension == ".wav"
    result.path.unlink()


# --- Size enforcement ---

@pytest.mark.anyio
async def test_file_exactly_at_limit_accepted(tmp_path):
    data = b"x" * 1024
    up = _make_upload(data, "clip.wav", "audio/wav")
    result = await validate_and_buffer_upload(up, 1024, tmp_path)
    assert result.size_bytes == 1024
    result.path.unlink()


@pytest.mark.anyio
async def test_file_one_byte_over_limit_rejected():
    data = b"x" * 1025
    up = _make_upload(data, "clip.wav", "audio/wav")
    with pytest.raises(UploadValidationError) as exc_info:
        await validate_and_buffer_upload(up, 1024)
    assert exc_info.value.status_code == 413


@pytest.mark.anyio
async def test_no_temp_file_leaked_on_size_error(tmp_path):
    data = b"x" * 1025
    up = _make_upload(data, "clip.wav", "audio/wav")
    files_before = set(tmp_path.iterdir())
    with pytest.raises(UploadValidationError):
        await validate_and_buffer_upload(up, 1024, tmp_path)
    files_after = set(tmp_path.iterdir())
    assert files_after == files_before


# --- Return value correctness ---

@pytest.mark.anyio
async def test_size_bytes_matches_data(tmp_path):
    data = b"x" * 512
    up = _make_upload(data, "clip.flac", "audio/flac")
    result = await validate_and_buffer_upload(up, 1_048_576, tmp_path)
    assert result.size_bytes == len(data)
    result.path.unlink()


# --- Sync unit tests ---

def test_upload_validation_error_attributes():
    err = UploadValidationError(415, "unsupported_media_type", "bad ext")
    assert err.status_code == 415
    assert err.error == "unsupported_media_type"
    assert err.detail == "bad ext"
