from __future__ import annotations

from pathlib import Path
from typing import Optional

from libs.asr.base import ASRAdapter
from libs.asr.errors import InputFileNotFoundError
from libs.asr.schema import ASRResult

_DEFAULT_TRANSCRIPT = "This is a deterministic fake transcript for local testing."


class FakeASRAdapter(ASRAdapter):
    def __init__(self, fake_transcript: Optional[str] = None) -> None:
        self._text = fake_transcript if fake_transcript else _DEFAULT_TRANSCRIPT

    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult:
        if not audio_path.exists():
            raise InputFileNotFoundError(f"Input file not found: {audio_path}")
        _ = audio_path.stat().st_size  # existence + size check only; content never read
        return ASRResult(
            text=self._text,
            language="en",
            duration_seconds=None,
            segments=[],
            words=[],
            provider="fake",
            provider_job_id=None,
            raw_payload={},
        )
