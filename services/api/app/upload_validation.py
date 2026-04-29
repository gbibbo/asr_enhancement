from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".wav", ".mp3", ".m4a", ".flac"})

ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({
    # WAV
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    # MP3
    "audio/mpeg",
    "audio/mp3",
    "audio/x-mpeg",
    # M4A
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
    "audio/aac",
    # FLAC
    "audio/flac",
    "audio/x-flac",
    # Generic binary (browser fallback)
    "application/octet-stream",
})

_CHUNK = 65_536


class UploadValidationError(Exception):
    def __init__(self, status_code: int, error: str, detail: str) -> None:
        self.status_code = status_code
        self.error = error
        self.detail = detail


@dataclass
class ValidatedUpload:
    path: Path
    original_filename: str
    extension: str        # lowercased suffix, e.g. ".wav"
    content_type: str | None  # params stripped; None when absent
    size_bytes: int


async def validate_and_buffer_upload(
    upload: UploadFile,
    upload_limit_bytes: int,
    tmp_dir: Path | None = None,
) -> ValidatedUpload:
    """
    Validate extension, normalize content type, stream to a temp file,
    and enforce the size limit.

    Extension is authoritative:
    - Disallowed extension → UploadValidationError(415) regardless of content type.
    - Allowed extension → accepted regardless of content type (Cut A policy).
    - Missing content type → accepted when extension is allowed.

    Raises UploadValidationError(415) for bad extension.
    Raises UploadValidationError(413) when file exceeds upload_limit_bytes.
    Returns ValidatedUpload on success; caller owns the temp file lifetime.
    """
    # Step 1: extension check
    filename = upload.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            415,
            "unsupported_media_type",
            f"File type not supported. Allowed extensions: "
            f"{', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    # Step 2: normalize content type (never gates acceptance when extension is valid)
    raw_ct = upload.content_type or ""
    normalized_ct: str | None = raw_ct.split(";")[0].strip().lower() or None

    # Step 3: stream to temp file, enforce size limit
    fd, tmp_path_str = tempfile.mkstemp(
        suffix=ext,
        dir=str(tmp_dir) if tmp_dir is not None else None,
    )
    tmp = Path(tmp_path_str)
    try:
        written = 0
        with os.fdopen(fd, "wb") as f:
            while True:
                chunk = await upload.read(_CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > upload_limit_bytes:
                    raise UploadValidationError(
                        413,
                        "file_too_large",
                        f"File exceeds the maximum allowed size of "
                        f"{upload_limit_bytes} bytes.",
                    )
                f.write(chunk)
    except UploadValidationError:
        tmp.unlink(missing_ok=True)
        raise
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    return ValidatedUpload(
        path=tmp,
        original_filename=filename,
        extension=ext,
        content_type=normalized_ct,
        size_bytes=written,
    )
