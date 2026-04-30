from __future__ import annotations


class UnknownPresetError(ValueError):
    def __init__(self, preset_id: str) -> None:
        self.preset_id = preset_id
        super().__init__(f"Unknown enhancement preset: {preset_id!r}")
