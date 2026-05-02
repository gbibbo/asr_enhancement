from __future__ import annotations

import abc
import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt


# ---------------------------------------------------------------------------
# Enhancer adapter interface (B5.3)
#
# BYPASS_ENHANCER_VERSION and METRICGAN_PLUS_ENHANCER_VERSION are the version
# strings returned by each adapter. They feed into the cache key via the worker
# when the enhancer interface is wired (B5.4+).
#
# DEFAULT_ENHANCER_VERSION in libs/common/versions.py is left unchanged by B5.3.
# Cache-key / default-version alignment is deferred to the worker-integration task.
# The demo runtime will explicitly pass BypassEnhancer().enhancer_version once wired.
# ---------------------------------------------------------------------------

BYPASS_ENHANCER_VERSION: str = "bypass"
METRICGAN_PLUS_ENHANCER_VERSION: str = "metricgan_plus_pretrained"


class EnhancerAdapter(abc.ABC):
    """Shared interface for all audio enhancers used by the demo runtime.

    Both BypassEnhancer and MetricGANPlusEnhancer implement this interface so
    the worker can call enhance() without knowing which enhancer is active.
    """

    @property
    @abc.abstractmethod
    def enhancer_version(self) -> str: ...

    @abc.abstractmethod
    def enhance(self, audio_path: Path, output_dir: Path, job_id: str) -> "EnhancementResult": ...


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class UnknownPresetError(ValueError):
    def __init__(self, preset_id: str) -> None:
        self.preset_id = preset_id
        super().__init__(f"Unknown enhancement preset: {preset_id!r}")


# ---------------------------------------------------------------------------
# Preset types and registry
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Enhancement pipeline
# ---------------------------------------------------------------------------

_TARGET_PEAK: float = 0.95
_HP_CUTOFF_HZ: float = 80.0
_HP_ORDER: int = 4


@dataclasses.dataclass(frozen=True)
class EnhancementResult:
    output_path: Path
    preset_applied: str
    enhanced: bool
    enhancement_fallback: bool
    diagnostic: dict[str, Any]


def apply_preset(
    preset_id: str,
    input_path: Path,
    output_dir: Path,
) -> EnhancementResult:
    """Apply the named preset to input_path, writing enhanced audio to output_dir.

    Raises UnknownPresetError for unregistered preset_id.
    Returns EnhancementResult; DSP failures produce enhancement_fallback=True instead of raising.
    """
    get_preset(preset_id)  # raises UnknownPresetError for unknown ids

    if preset_id == BYPASS_PRESET_ID:
        return EnhancementResult(
            output_path=input_path,
            preset_applied=preset_id,
            enhanced=False,
            enhancement_fallback=False,
            diagnostic={},
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{preset_id}.wav"

    try:
        samples, sr = sf.read(input_path, dtype="float64", always_2d=False)
        processed = _apply_dsp(preset_id, samples, sr)
        sf.write(out_path, processed, sr, subtype="PCM_16")
        if not _validate_output(out_path):
            raise RuntimeError("Output validation failed: empty or unreadable")
        diagnostic: dict[str, Any] = {}
        if preset_id == "denoise_dereverb":
            diagnostic = {"dereverb_applied": False}
        return EnhancementResult(
            output_path=out_path,
            preset_applied=preset_id,
            enhanced=True,
            enhancement_fallback=False,
            diagnostic=diagnostic,
        )
    except Exception as exc:
        return EnhancementResult(
            output_path=input_path,
            preset_applied=preset_id,
            enhanced=False,
            enhancement_fallback=True,
            diagnostic={"fallback_reason": str(exc)},
        )


def _apply_dsp(preset_id: str, samples: np.ndarray, sr: int) -> np.ndarray:
    if preset_id == "light_clean":
        return _normalize_gain(samples)
    if preset_id in ("denoise", "denoise_dereverb"):
        filtered = _highpass(samples, sr)
        return _normalize_gain(filtered)
    raise UnknownPresetError(preset_id)


def _normalize_gain(samples: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(samples)))
    if peak < 1e-9:
        return samples.copy()
    return (samples * (_TARGET_PEAK / peak)).astype(samples.dtype)


def _highpass(samples: np.ndarray, sr: int) -> np.ndarray:
    sos = butter(_HP_ORDER, _HP_CUTOFF_HZ, btype="high", fs=sr, output="sos")
    filtered = sosfilt(sos, samples, axis=0)
    return filtered.astype(samples.dtype)


def _validate_output(path: Path) -> bool:
    try:
        info = sf.info(path)
        return info.frames > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Concrete enhancer classes (B5.3)
# ---------------------------------------------------------------------------


class BypassEnhancer(EnhancerAdapter):
    """Honest no-op enhancer. Passes audio to ASR without modification."""

    @property
    def enhancer_version(self) -> str:
        return BYPASS_ENHANCER_VERSION

    def enhance(self, audio_path: Path, output_dir: Path, job_id: str) -> EnhancementResult:
        return apply_preset(BYPASS_PRESET_ID, audio_path, output_dir)


class MetricGANPlusEnhancer(EnhancerAdapter):
    """Empty MetricGAN+ pretrained hook.

    B5.3 owns the interface. T4.1 in feature/training-datamove1-v1 fills this
    class. Do not add a second MetricGAN+ implementation outside this class.
    """

    @property
    def enhancer_version(self) -> str:
        return METRICGAN_PLUS_ENHANCER_VERSION

    def enhance(self, audio_path: Path, output_dir: Path, job_id: str) -> EnhancementResult:
        raise NotImplementedError(
            "MetricGAN+ implementation is owned by task T4.1 in the training branch. "
            "Use BypassEnhancer until T4.1 is merged into demo-rp5-v1."
        )
