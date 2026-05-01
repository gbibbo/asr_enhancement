from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ASRResult:
    text: str
    language: Optional[str]
    duration_seconds: Optional[float]
    segments: list[dict[str, Any]]
    words: list[dict[str, Any]]
    provider: str
    provider_job_id: Optional[str]
    raw_payload: dict[str, Any]
