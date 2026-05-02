from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from libs.asr.assemblyai_provider import AssemblyAIAdapter
from libs.asr.errors import (
    AdapterHTTPError,
    AdapterTimeoutError,
    AdapterTranscriptionError,
    InputFileNotFoundError,
)
from libs.asr.schema import ASRResult

_SAFE_ERROR_MESSAGE = (
    "AssemblyAI temporarily unavailable. Try again or use Whisper local."
)
_QUOTA_MESSAGE = (
    "AssemblyAI quota exhausted for today. Use Whisper local instead."
)
_RETRY_WAIT_SECONDS = 2.0


class DemoAssemblyAIAdapter(AssemblyAIAdapter):
    """AssemblyAI adapter for demo mode.

    Adds retry-once on timeout/5xx, quota guard, shorter default timeouts,
    and a status helper. Does not silently fall back to Whisper.
    """

    STATUS_AVAILABLE = "available"
    STATUS_DISABLED = "disabled"

    def __init__(
        self,
        api_key: str,
        *,
        max_wait_seconds: float = 120.0,
        upload_timeout_seconds: float = 30.0,
        quota_exhausted: bool = False,
        **kwargs: Any,
    ) -> None:
        self._quota_exhausted = quota_exhausted
        super().__init__(
            api_key=api_key,
            max_wait_seconds=max_wait_seconds,
            upload_timeout_seconds=upload_timeout_seconds,
            **kwargs,
        )

    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult:
        if self._quota_exhausted:
            raise AdapterTranscriptionError(_QUOTA_MESSAGE)

        try:
            return super().transcribe(audio_path, job_id)
        except InputFileNotFoundError:
            raise
        except (AdapterHTTPError, AdapterTimeoutError) as exc:
            if isinstance(exc, AdapterHTTPError) and exc.status_code < 500:
                raise
            self._sleep(_RETRY_WAIT_SECONDS)

        try:
            return super().transcribe(audio_path, job_id)
        except AdapterTranscriptionError:
            raise AdapterTranscriptionError(_SAFE_ERROR_MESSAGE)

    @staticmethod
    def get_status(api_key: Optional[str]) -> str:
        """Return 'disabled' if key absent or empty, 'available' otherwise."""
        if not api_key:
            return DemoAssemblyAIAdapter.STATUS_DISABLED
        return DemoAssemblyAIAdapter.STATUS_AVAILABLE
