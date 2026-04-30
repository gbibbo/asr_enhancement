from __future__ import annotations

import dataclasses

import pytest

from libs.audio_pipeline.errors import UnknownPresetError
from libs.audio_pipeline.presets import (
    BYPASS_PRESET_ID,
    KNOWN_PRESET_IDS,
    PRESET_REGISTRY,
    EnhancementPreset,
    get_preset,
    resolve_preset,
)

# ---------------------------------------------------------------------------
# Registry membership
# ---------------------------------------------------------------------------

def test_bypass_preset_is_registered():
    assert "bypass" in PRESET_REGISTRY


def test_light_clean_preset_is_registered():
    assert "light_clean" in PRESET_REGISTRY


def test_denoise_preset_is_registered():
    assert "denoise" in PRESET_REGISTRY


def test_denoise_dereverb_preset_is_registered():
    assert "denoise_dereverb" in PRESET_REGISTRY


def test_registry_has_exactly_four_entries():
    assert len(PRESET_REGISTRY) == 4


# ---------------------------------------------------------------------------
# KNOWN_PRESET_IDS
# ---------------------------------------------------------------------------

def test_known_preset_ids_is_frozenset():
    assert isinstance(KNOWN_PRESET_IDS, frozenset)


def test_known_preset_ids_matches_registry_keys():
    assert KNOWN_PRESET_IDS == frozenset(PRESET_REGISTRY)


# ---------------------------------------------------------------------------
# EnhancementPreset field invariants
# ---------------------------------------------------------------------------

def test_preset_id_field_matches_registry_key():
    for key, preset in PRESET_REGISTRY.items():
        assert preset.id == key


def test_preset_descriptions_are_nonempty():
    for preset in PRESET_REGISTRY.values():
        assert isinstance(preset.description, str)
        assert len(preset.description) > 0


def test_enhancement_preset_is_frozen():
    preset = get_preset("bypass")
    with pytest.raises(dataclasses.FrozenInstanceError):
        preset.id = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# get_preset
# ---------------------------------------------------------------------------

def test_get_preset_bypass_returns_correct_id():
    assert get_preset("bypass").id == "bypass"


def test_get_preset_returns_enhancement_preset_instance():
    assert isinstance(get_preset("denoise"), EnhancementPreset)


def test_get_preset_unknown_raises_unknown_preset_error():
    with pytest.raises(UnknownPresetError):
        get_preset("not_a_real_preset")


def test_get_preset_unknown_raises_value_error():
    with pytest.raises(ValueError):
        get_preset("not_a_real_preset")


def test_unknown_preset_error_carries_preset_id():
    bad_id = "bad_preset"
    with pytest.raises(UnknownPresetError) as exc_info:
        get_preset(bad_id)
    assert exc_info.value.preset_id == bad_id


# ---------------------------------------------------------------------------
# resolve_preset
# ---------------------------------------------------------------------------

def test_resolve_preset_none_returns_bypass():
    assert resolve_preset(None) == "bypass"


def test_resolve_preset_bypass_returns_bypass():
    assert resolve_preset("bypass") == "bypass"


def test_resolve_preset_light_clean_returns_light_clean():
    assert resolve_preset("light_clean") == "light_clean"


def test_resolve_preset_denoise_returns_denoise():
    assert resolve_preset("denoise") == "denoise"


def test_resolve_preset_denoise_dereverb_returns_denoise_dereverb():
    assert resolve_preset("denoise_dereverb") == "denoise_dereverb"


def test_resolve_preset_unknown_raises():
    with pytest.raises(UnknownPresetError):
        resolve_preset("garbage")


# ---------------------------------------------------------------------------
# BYPASS_PRESET_ID constant
# ---------------------------------------------------------------------------

def test_bypass_preset_id_constant():
    assert BYPASS_PRESET_ID == "bypass"
