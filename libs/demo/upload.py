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
