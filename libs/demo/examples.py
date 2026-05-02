from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class DemoExample(BaseModel):
    example_id: str
    title: str
    description: str = ""
    duration_seconds: float
    degradation_ids: list[str]
    ground_truth: str
    audio_available: bool = False
    clean_audio_path: Optional[str] = None
    degraded_audio_paths: dict[str, str] = Field(default_factory=dict)


def load_examples(config_path: Path) -> list[DemoExample]:
    if not config_path.is_file():
        return []
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return [DemoExample(**item) for item in data]
