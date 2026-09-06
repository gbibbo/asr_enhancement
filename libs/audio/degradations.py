from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

import libs.common.versions as versions


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DegradationSpec:
    id: str
    description: str
    params: dict[str, Any]


@dataclass(frozen=True)
class DegradationResult:
    output_path: Path
    degradation_id: str
    params_applied: dict[str, Any]
    degradation_version: str


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DEGRADATION_REGISTRY: dict[str, DegradationSpec] = {
    "far_field_room": DegradationSpec(
        id="far_field_room",
        description="Simulates far-field recording with room reverberation.",
        params={"rt60": 0.3, "gain_db": -6.0},
    ),
    "cafe_background": DegradationSpec(
        id="cafe_background",
        description="Adds band-limited background noise at SNR 10 dB.",
        params={"snr_db": 10.0},
    ),
    "phone_call": DegradationSpec(
        id="phone_call",
        description="Bandpass filter 300–3400 Hz simulating telephone codec.",
        params={"low_hz": 300.0, "high_hz": 3400.0, "order": 4},
    ),
    "muffled": DegradationSpec(
        id="muffled",
        description="Low-pass filter at 1000 Hz simulating muffled recording.",
        params={"cutoff_hz": 1000.0, "order": 4},
    ),
    "broadband_hiss": DegradationSpec(
        id="broadband_hiss",
        description="Adds white noise hiss at SNR 30 dB.",
        params={"snr_db": 30.0},
    ),
}

KNOWN_DEGRADATION_IDS: frozenset[str] = frozenset(DEGRADATION_REGISTRY)


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------


class UnknownDegradationError(ValueError):
    def __init__(self, degradation_id: str) -> None:
        self.degradation_id = degradation_id
        super().__init__(f"Unknown degradation: {degradation_id!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_degradation(degradation_id: str) -> DegradationSpec:
    """Return DegradationSpec or raise UnknownDegradationError."""
    try:
        return DEGRADATION_REGISTRY[degradation_id]
    except KeyError:
        raise UnknownDegradationError(degradation_id)


def apply_degradation(
    degradation_id: str,
    input_path: Path,
    output_dir: Path,
    *,
    seed: int = 0,
) -> DegradationResult:
    """Apply named degradation to input_path, write WAV to output_dir.

    Reads versions.DEGRADATION_VERSION at call time.
    Raises UnknownDegradationError for unknown ids.
    """
    spec = get_degradation(degradation_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{degradation_id}.wav"

    samples, sr = sf.read(input_path, dtype="float64", always_2d=False)
    rng = np.random.default_rng(seed)
    processed = _dispatch(degradation_id, samples, sr, spec.params, rng)
    sf.write(out_path, processed, sr, subtype="PCM_16")

    return DegradationResult(
        output_path=out_path,
        degradation_id=degradation_id,
        params_applied=dict(spec.params),
        degradation_version=versions.DEGRADATION_VERSION,
    )


# ---------------------------------------------------------------------------
# Private dispatch
# ---------------------------------------------------------------------------


def _dispatch(
    degradation_id: str,
    samples: np.ndarray,
    sr: int,
    params: dict[str, Any],
    rng: np.random.Generator,
) -> np.ndarray:
    if degradation_id == "far_field_room":
        return _apply_far_field_room(samples, sr, rt60=params["rt60"], gain_db=params["gain_db"], rng=rng)
    if degradation_id == "cafe_background":
        return _apply_cafe_background(samples, sr, snr_db=params["snr_db"], rng=rng)
    if degradation_id == "phone_call":
        return _apply_phone_call(samples, sr, low_hz=params["low_hz"], high_hz=params["high_hz"], order=int(params["order"]))
    if degradation_id == "muffled":
        return _apply_muffled(samples, sr, cutoff_hz=params["cutoff_hz"], order=int(params["order"]))
    if degradation_id == "broadband_hiss":
        return _apply_broadband_hiss(samples, sr, snr_db=params["snr_db"], rng=rng)
    raise UnknownDegradationError(degradation_id)


# ---------------------------------------------------------------------------
# DSP helpers
# ---------------------------------------------------------------------------


def _apply_far_field_room(
    samples: np.ndarray,
    sr: int,
    *,
    rt60: float,
    gain_db: float,
    rng: np.random.Generator,
) -> np.ndarray:
    ir_length = int(rt60 * sr)
    if ir_length < 1:
        ir_length = 1
    t = np.arange(ir_length, dtype=np.float64)
    ir = np.exp(-6.9 * t / (rt60 * sr))
    ir /= np.sum(np.abs(ir)) + 1e-12
    convolved = np.convolve(samples.astype(np.float64), ir, mode="full")[: len(samples)]
    gain = 10.0 ** (gain_db / 20.0)
    return (convolved * gain).astype(samples.dtype)


def _apply_cafe_background(
    samples: np.ndarray,
    sr: int,
    *,
    snr_db: float,
    rng: np.random.Generator,
) -> np.ndarray:
    s = samples.astype(np.float64)
    signal_rms = float(np.sqrt(np.mean(s ** 2)))
    if signal_rms < 1e-9:
        signal_rms = 1e-9
    noise_rms = signal_rms / (10.0 ** (snr_db / 20.0))
    noise = rng.standard_normal(len(s)) * noise_rms
    # Band-limit noise 200–4000 Hz
    low = 200.0 / (sr / 2.0)
    high = min(4000.0 / (sr / 2.0), 0.99)
    if low < high:
        sos = butter(4, [low, high], btype="band", output="sos")
        noise = sosfilt(sos, noise)
    return (s + noise).astype(samples.dtype)


def _apply_phone_call(
    samples: np.ndarray,
    sr: int,
    *,
    low_hz: float,
    high_hz: float,
    order: int,
) -> np.ndarray:
    nyq = sr / 2.0
    low = low_hz / nyq
    high = min(high_hz / nyq, 0.99)
    sos = butter(order, [low, high], btype="band", output="sos")
    filtered = sosfilt(sos, samples.astype(np.float64), axis=0)
    return filtered.astype(samples.dtype)


def _apply_muffled(
    samples: np.ndarray,
    sr: int,
    *,
    cutoff_hz: float,
    order: int,
) -> np.ndarray:
    nyq = sr / 2.0
    cutoff = min(cutoff_hz / nyq, 0.99)
    sos = butter(order, cutoff, btype="low", output="sos")
    filtered = sosfilt(sos, samples.astype(np.float64), axis=0)
    return filtered.astype(samples.dtype)


def _apply_broadband_hiss(
    samples: np.ndarray,
    sr: int,
    *,
    snr_db: float,
    rng: np.random.Generator,
) -> np.ndarray:
    s = samples.astype(np.float64)
    signal_rms = float(np.sqrt(np.mean(s ** 2)))
    if signal_rms < 1e-9:
        signal_rms = 1e-9
    noise_rms = signal_rms / (10.0 ** (snr_db / 20.0))
    noise = rng.standard_normal(len(s)) * noise_rms
    return (s + noise).astype(samples.dtype)
