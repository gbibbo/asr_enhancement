from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from libs.audio_pipeline.errors import UnknownPresetError

BYPASS_PRESET_ID = "bypass"


@dataclass(frozen=True)
class EnhancementPreset:
    id: str
    description: str


PRESET_REGISTRY: dict[str, EnhancementPreset] = {
    "bypass": EnhancementPreset(
        id="bypass",
        description="No enhancement; raw audio is passed directly to ASR.",
    ),
    "light_clean": EnhancementPreset(
        id="light_clean",
        description="Gain normalization only.",
    ),
    "denoise": EnhancementPreset(
        id="denoise",
        description="High-pass filter plus gain normalization.",
    ),
    "denoise_dereverb": EnhancementPreset(
        id="denoise_dereverb",
        description="High-pass filter plus gain normalization; dereverb_applied recorded as false for MVP.",
    ),
}

KNOWN_PRESET_IDS: frozenset[str] = frozenset(PRESET_REGISTRY)


def get_preset(preset_id: str) -> EnhancementPreset:
    """Return the EnhancementPreset for preset_id, or raise UnknownPresetError."""
    try:
        return PRESET_REGISTRY[preset_id]
    except KeyError:
        raise UnknownPresetError(preset_id)


def resolve_preset(preset_id: Optional[str]) -> str:
    """Return preset_id if valid, or BYPASS_PRESET_ID if None. Raises UnknownPresetError for unknown non-None values."""
    if preset_id is None:
        return BYPASS_PRESET_ID
    get_preset(preset_id)  # raises UnknownPresetError if unknown
    return preset_id
