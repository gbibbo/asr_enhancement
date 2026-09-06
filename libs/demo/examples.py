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


def get_safe_audio_path(audio_root: Path, path_str: str | None) -> Path | None:
    if not path_str:
        return None
    relative_path = Path(path_str)
    if relative_path.is_absolute():
        return None
    root = audio_root.resolve()
    resolved = (root / relative_path).resolve()
    if not resolved.is_relative_to(root):
        return None
    if not resolved.is_file():
        return None
    return resolved
