from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

DEMO_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".wav", ".mp3", ".m4a", ".flac"})

_CHUNK = 65_536


class UnsupportedExtensionError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class InvalidAudioError(Exception):
    pass


async def save_upload(
    upload: UploadFile,
    upload_dir: Path,
    limit_bytes: int,
) -> tuple[Path, str]:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in DEMO_ALLOWED_EXTENSIONS:
        raise UnsupportedExtensionError(
            f"Extension {ext!r} is not allowed. Allowed: {sorted(DEMO_ALLOWED_EXTENSIONS)}"
        )

    upload_dir.mkdir(parents=True, exist_ok=True)

    tmp_file = upload_dir / (uuid4().hex + ".tmp")
    final_file = upload_dir / (uuid4().hex + ext)

    try:
        written = 0
        with tmp_file.open("wb") as f:
            while True:
                chunk = await upload.read(_CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > limit_bytes:
                    raise FileTooLargeError(
                        f"File exceeds maximum size of {limit_bytes} bytes."
                    )
                f.write(chunk)
        tmp_file.rename(final_file)
        return (final_file, ext)
    except BaseException:
        tmp_file.unlink(missing_ok=True)
        raise


def probe_audio_duration(path: Path) -> float:
    """Return the audio duration in seconds by reading only the file header.

    Uses soundfile.info(), which parses the container header without decoding
    samples. Raises InvalidAudioError if the header cannot be read.
    """
    import soundfile as sf  # imported lazily so import-time cost is not paid by callers that never validate

    try:
        info = sf.info(str(path))
    except Exception as exc:
        raise InvalidAudioError("Audio could not be decoded.") from exc

    samplerate = getattr(info, "samplerate", 0) or 0
    frames = getattr(info, "frames", 0) or 0
    if samplerate <= 0:
        raise InvalidAudioError("Audio could not be decoded.")
    return float(frames) / float(samplerate)


async def validate_and_save_upload(
    upload: UploadFile,
    upload_dir: Path,
    limit_bytes: int,
    max_duration_seconds: float,
) -> tuple[Path, str, float]:
    """Save the upload, then probe its duration. Reject undecodable or over-length audio.

    Order of checks: extension and size are enforced inside save_upload (415 / 413
    via UnsupportedExtensionError / FileTooLargeError). Duration and decodability
    are enforced here (422 via InvalidAudioError). On any audio-validation failure,
    the saved file is unlinked before the exception propagates.
    """
    saved_path, ext = await save_upload(upload, upload_dir, limit_bytes)
    try:
        duration = probe_audio_duration(saved_path)
    except InvalidAudioError:
        saved_path.unlink(missing_ok=True)
        raise
    except BaseException:
        saved_path.unlink(missing_ok=True)
        raise
    if duration > float(max_duration_seconds):
        saved_path.unlink(missing_ok=True)
        raise InvalidAudioError("Audio exceeds 30 seconds maximum.")
    return (saved_path, ext, duration)
