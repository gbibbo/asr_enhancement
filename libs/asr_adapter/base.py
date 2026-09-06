from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from libs.asr_adapter.schema import ASRResult


class ASRAdapter(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult: ...
