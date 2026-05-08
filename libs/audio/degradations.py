"""Degradation bank for ASR robustness evaluation (degradation_v1).

Five frozen families operate on 16 kHz mono float64 audio:

    far_field_room   - synthetic exp-decay impulse response convolution
    cafe_background  - speech-shaped Gaussian noise added at 5 dB SNR
    phone_call       - bandpass + 16->8->mu-law->8->16 kHz codec round-trip
    muffled          - lowpass at 800 Hz + -6 dB attenuation
    broadband_hiss   - Gaussian white noise added at 10 dB SNR

The public entry point is `apply_degradation(samples, sr, family, utterance_id)`,
which: derives a deterministic per-(utterance, family) seed, calls the raw
family function, enforces output length == input length, requires finite output,
and peak-normalizes to <= 0.95. Raw family functions are exported for tests but
should not be called directly by the generator.

Determinism: the per-(utterance, family) seed is the first 8 bytes of
SHA-256(f"{DEGRADATION_VERSION}|{family}|{utterance_id}") interpreted as a
big-endian uint64. This makes every degraded file reproducible from the
manifest entry alone.

Zero-RMS guard: scaling helpers (cafe_background, broadband_hiss noise scaling
and far_field_room tail scaling) refuse to divide by an RMS below RMS_EPS.
The public helper raises ZeroSpeechRmsError on silent input. Stochastic family
functions raise ZeroNoiseRmsError if their generated noise/tail RMS underflows.

Any change to the formulas, parameters, or registry must bump
DEGRADATION_VERSION in libs/common/versions.py.
"""
from __future__ import annotations

import audioop
import hashlib
import math

import numpy as np
import scipy.signal

from libs.common.versions import DEGRADATION_VERSION

__all__ = [
    "DEGRADATION_VERSION",
    "DEGRADATION_FAMILIES",
    "DEGRADATION_FAMILIES_STOCHASTIC",
    "DEGRADATION_FAMILIES_DETERMINISTIC",
    "DEGRADATION_PARAMS",
    "RMS_EPS",
    "ZeroSpeechRmsError",
    "ZeroNoiseRmsError",
    "utterance_seed",
    "apply_degradation",
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
]


RMS_EPS: float = 1e-7
TARGET_PEAK: float = 0.95
EXPECTED_SR: int = 16000


class ZeroSpeechRmsError(ValueError):
    """Raised when input speech RMS is below RMS_EPS — degradation is undefined."""


class ZeroNoiseRmsError(ValueError):
    """Raised when generated noise/tail RMS is below RMS_EPS — scaling is undefined."""


DEGRADATION_PARAMS: dict[str, dict] = {
    "far_field_room": {
        "ir_length_seconds": 0.8,
        "rt60_seconds": 0.6,
        "drr_db": -6.0,
    },
    "cafe_background": {
        "snr_db": 5.0,
        "bandpass_low_hz": 200.0,
        "bandpass_high_hz": 4000.0,
        "bandpass_order": 4,
    },
    "phone_call": {
        "bandpass_low_hz": 300.0,
        "bandpass_high_hz": 3400.0,
        "bandpass_order": 6,
        "intermediate_sr_hz": 8000,
        "codec": "mu_law_g711",
    },
    "muffled": {
        "lowpass_hz": 800.0,
        "lowpass_order": 4,
        "attenuation_db": -6.0,
    },
    "broadband_hiss": {
        "snr_db": 10.0,
    },
}


def utterance_seed(utterance_id: str, family: str) -> int:
    """Deterministic per-(utterance, family) uint64 seed."""
    digest = hashlib.sha256(
        f"{DEGRADATION_VERSION}|{family}|{utterance_id}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def _butter_sos(cutoff, sr: int, order: int, btype: str) -> np.ndarray:
    nyq = 0.5 * sr
    if isinstance(cutoff, (tuple, list)):
        wn = [c / nyq for c in cutoff]
    else:
        wn = cutoff / nyq
    return scipy.signal.butter(order, wn, btype=btype, output="sos")


# ---------------------------------------------------------------------------
# Raw family functions — return arrays that may differ in length from input.
# Length enforcement, finite check, and peak normalization happen exclusively
# in apply_degradation.
# ---------------------------------------------------------------------------

def far_field_room(samples: np.ndarray, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Convolve with a synthetic exponentially-decaying impulse response.

    IR length 0.8 s (12800 samples at 16 kHz), RT60 = 0.6 s, direct-to-reverberant
    ratio = -6 dB. The IR is regenerated deterministically per call from `rng`.
    Output length is len(samples) + ir_length - 1; apply_degradation truncates.
    """
    p = DEGRADATION_PARAMS["far_field_room"]
    ir_length_samples = int(p["ir_length_seconds"] * sr)
    rt60 = p["rt60_seconds"]
    tau = rt60 / math.log(1000.0)

    t = np.arange(ir_length_samples) / sr
    env = np.exp(-t / tau)
    ir_noise = rng.standard_normal(ir_length_samples)
    ir_tail = ir_noise * env

    direct_amp = 1.0
    tail_rms_target = direct_amp * 10 ** (p["drr_db"] / 20.0)
    current_tail_rms = _rms(ir_tail)
    if current_tail_rms < RMS_EPS:
        raise ZeroNoiseRmsError(
            f"far_field_room: generated IR tail RMS={current_tail_rms!r} below RMS_EPS={RMS_EPS}"
        )
    ir_tail_scaled = ir_tail * (tail_rms_target / current_tail_rms)

    ir = np.zeros(ir_length_samples, dtype=np.float64)
    ir[0] = direct_amp
    ir[1:] = ir_tail_scaled[1:]

    return scipy.signal.fftconvolve(samples, ir, mode="full")


def cafe_background(samples: np.ndarray, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Add speech-shaped Gaussian noise at SNR = 5 dB."""
    p = DEGRADATION_PARAMS["cafe_background"]
    n = len(samples)
    noise = rng.standard_normal(n)
    sos = _butter_sos(
        (p["bandpass_low_hz"], p["bandpass_high_hz"]), sr, p["bandpass_order"], "bandpass"
    )
    noise_filt = scipy.signal.sosfiltfilt(sos, noise)

    speech_rms = _rms(samples)
    # speech_rms is guaranteed >= RMS_EPS by apply_degradation; family is called only via the helper
    noise_rms = _rms(noise_filt)
    if noise_rms < RMS_EPS:
        raise ZeroNoiseRmsError(
            f"cafe_background: filtered noise RMS={noise_rms!r} below RMS_EPS={RMS_EPS}"
        )
    target_noise_rms = speech_rms * 10 ** (-p["snr_db"] / 20.0)
    noise_scaled = noise_filt * (target_noise_rms / noise_rms)
    return samples + noise_scaled


def phone_call(samples: np.ndarray, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Bandpass 300-3400 Hz, downsample to 8 kHz, mu-law G.711 round-trip, upsample back."""
    p = DEGRADATION_PARAMS["phone_call"]
    sos = _butter_sos(
        (p["bandpass_low_hz"], p["bandpass_high_hz"]), sr, p["bandpass_order"], "bandpass"
    )
    bp = scipy.signal.sosfiltfilt(sos, samples)

    # 16 kHz -> 8 kHz
    sr_inter = p["intermediate_sr_hz"]
    down_factor = sr // sr_inter  # 2
    narrow = scipy.signal.resample_poly(bp, up=1, down=down_factor)

    # Encode -> int16 PCM with safe clipping, then mu-law round-trip
    narrow_clipped = np.clip(narrow, -1.0, 1.0)
    pcm_int16 = (narrow_clipped * 32767.0).astype("<i2").tobytes()
    ulaw_bytes = audioop.lin2ulaw(pcm_int16, 2)
    pcm_int16_back = audioop.ulaw2lin(ulaw_bytes, 2)
    narrow_decoded = np.frombuffer(pcm_int16_back, dtype="<i2").astype(np.float64) / 32767.0

    # 8 kHz -> 16 kHz
    upsampled = scipy.signal.resample_poly(narrow_decoded, up=down_factor, down=1)
    return upsampled


def muffled(samples: np.ndarray, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Lowpass at 800 Hz then -6 dB attenuation. Deterministic; rng ignored."""
    p = DEGRADATION_PARAMS["muffled"]
    sos = _butter_sos(p["lowpass_hz"], sr, p["lowpass_order"], "lowpass")
    lp = scipy.signal.sosfiltfilt(sos, samples)
    return lp * 10 ** (p["attenuation_db"] / 20.0)


def broadband_hiss(samples: np.ndarray, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Add Gaussian white noise at SNR = 10 dB."""
    p = DEGRADATION_PARAMS["broadband_hiss"]
    n = len(samples)
    noise = rng.standard_normal(n)
    speech_rms = _rms(samples)
    noise_rms = _rms(noise)
    if noise_rms < RMS_EPS:
        raise ZeroNoiseRmsError(
            f"broadband_hiss: noise RMS={noise_rms!r} below RMS_EPS={RMS_EPS}"
        )
    target_noise_rms = speech_rms * 10 ** (-p["snr_db"] / 20.0)
    noise_scaled = noise * (target_noise_rms / noise_rms)
    return samples + noise_scaled


DEGRADATION_FAMILIES: dict[str, callable] = {
    "far_field_room": far_field_room,
    "cafe_background": cafe_background,
    "phone_call": phone_call,
    "muffled": muffled,
    "broadband_hiss": broadband_hiss,
}

DEGRADATION_FAMILIES_STOCHASTIC: frozenset = frozenset(
    {"far_field_room", "cafe_background", "broadband_hiss"}
)

DEGRADATION_FAMILIES_DETERMINISTIC: frozenset = frozenset({"phone_call", "muffled"})


# ---------------------------------------------------------------------------
# Public helper — single entry point used by the generator and by tests.
# ---------------------------------------------------------------------------

def _enforce_length(out: np.ndarray, target_len: int) -> np.ndarray:
    if len(out) == target_len:
        return out
    if len(out) > target_len:
        return out[:target_len]
    padded = np.zeros(target_len, dtype=np.float64)
    padded[: len(out)] = out
    return padded


def apply_degradation(
    samples: np.ndarray,
    sr: int,
    family: str,
    utterance_id: str,
) -> np.ndarray:
    """Apply degradation deterministically with length, finite, and peak guards."""
    if sr != EXPECTED_SR:
        raise ValueError(f"sr must be {EXPECTED_SR}, got {sr}")
    if samples.ndim != 1:
        raise ValueError(f"samples must be 1-D, got ndim={samples.ndim}")
    if not np.isfinite(samples).all():
        raise ValueError("samples must be finite")
    if family not in DEGRADATION_FAMILIES:
        raise KeyError(f"unknown family {family!r}")

    samples_f64 = samples.astype(np.float64, copy=False)
    speech_rms = _rms(samples_f64)
    if speech_rms < RMS_EPS:
        raise ZeroSpeechRmsError(
            f"speech RMS={speech_rms!r} below RMS_EPS={RMS_EPS} for utterance_id={utterance_id!r}"
        )

    rng = np.random.default_rng(utterance_seed(utterance_id, family))
    raw = DEGRADATION_FAMILIES[family](samples_f64, sr, rng)
    out = _enforce_length(np.asarray(raw, dtype=np.float64), len(samples_f64))

    if not np.isfinite(out).all():
        raise ValueError(f"family {family!r} produced non-finite output")

    peak = float(np.max(np.abs(out)))
    if peak > TARGET_PEAK and peak > 0.0:
        out = out * (TARGET_PEAK / peak)

    return out


# ---------------------------------------------------------------------------
# Robust ASR v3.4.7 P1.4 — sample_<family> wrappers (additive narrow patch).
#
# These functions implement the canonical Section 3 contract:
#
#     sample_<family>(input_wav: str, output_wav: str, seed: int,
#                     params: dict) -> dict
#
# returning {condition_family, random_seed, snr_db, rir_id_or_null,
#            filter_params_json, source_audio_sha256, output_audio_sha256}.
#
# They are additive: existing apply_degradation, DEGRADATION_FAMILIES,
# DEGRADATION_PARAMS, and DEGRADATION_VERSION value are unchanged. The
# v3.4.7 family names (cafe_noise, phone_band, muffled_lowpass, far_field_room,
# clean) are deliberately distinct from the training-profile names
# (cafe_background, phone_call, muffled, far_field_room, broadband_hiss).
# The two surfaces coexist; this module remains read-only for all other tasks.
# ---------------------------------------------------------------------------

import json as _json
import os as _os

import soundfile as _sf

V347_FAMILIES: tuple = (
    "clean",
    "cafe_noise",
    "phone_band",
    "far_field_room",
    "muffled_lowpass",
)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_mono16k(path: str) -> tuple:
    samples, sr = _sf.read(path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    samples = samples.astype(np.float64, copy=False)
    if sr != EXPECTED_SR:
        raise ValueError(f"{path}: sr={sr} != EXPECTED_SR={EXPECTED_SR}")
    if samples.size == 0:
        raise ValueError(f"{path}: empty audio")
    if not np.isfinite(samples).all():
        raise ValueError(f"{path}: non-finite samples")
    return samples, sr


def _write_pcm16(path: str, samples: np.ndarray, sr: int) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16, copy=False)
    _os.makedirs(_os.path.dirname(path), exist_ok=True)
    _sf.write(path, pcm, sr, subtype="PCM_16")


def _peak_normalize(out: np.ndarray) -> np.ndarray:
    out = _enforce_length(np.asarray(out, dtype=np.float64), len(out))
    if not np.isfinite(out).all():
        raise ValueError("non-finite output")
    peak = float(np.max(np.abs(out)))
    if peak > TARGET_PEAK and peak > 0.0:
        out = out * (TARGET_PEAK / peak)
    return out


def sample_clean(input_wav: str, output_wav: str, seed: int, params: dict) -> dict:
    """Identity family: output sha256 == source sha256; no audio rewritten.

    Convention: caller may pass output_wav == input_wav. The function never
    writes; the manifest row points at the source file.
    """
    src_sha = _sha256_file(input_wav)
    return {
        "condition_family": "clean",
        "random_seed": int(seed),
        "snr_db": None,
        "rir_id_or_null": None,
        "filter_params_json": _json.dumps({}, sort_keys=True),
        "source_audio_sha256": src_sha,
        "output_audio_sha256": src_sha,
    }


def sample_cafe_noise(
    input_wav: str, output_wav: str, seed: int, params: dict
) -> dict:
    """Bandpass-filtered Gaussian noise added at requested SNR (dB)."""
    samples, sr = _read_mono16k(input_wav)
    speech_rms = _rms(samples)
    if speech_rms < RMS_EPS:
        raise ZeroSpeechRmsError(f"speech RMS underflow: {input_wav}")
    snr_db = float(params["snr_db"])
    band_low = float(params.get("bandpass_low_hz", 200.0))
    band_high = float(params.get("bandpass_high_hz", 4000.0))
    order = int(params.get("bandpass_order", 4))

    rng = np.random.default_rng(int(seed))
    n = len(samples)
    noise = rng.standard_normal(n)
    sos = _butter_sos((band_low, band_high), sr, order, "bandpass")
    noise_filt = scipy.signal.sosfiltfilt(sos, noise)
    noise_rms = _rms(noise_filt)
    if noise_rms < RMS_EPS:
        raise ZeroNoiseRmsError("cafe_noise: filtered noise RMS underflow")
    target_noise_rms = speech_rms * 10 ** (-snr_db / 20.0)
    out = samples + noise_filt * (target_noise_rms / noise_rms)
    out = _peak_normalize(out)
    _write_pcm16(output_wav, out, sr)

    return {
        "condition_family": "cafe_noise",
        "random_seed": int(seed),
        "snr_db": snr_db,
        "rir_id_or_null": None,
        "filter_params_json": _json.dumps(
            {
                "bandpass_low_hz": band_low,
                "bandpass_high_hz": band_high,
                "bandpass_order": order,
            },
            sort_keys=True,
        ),
        "source_audio_sha256": _sha256_file(input_wav),
        "output_audio_sha256": _sha256_file(output_wav),
    }


def sample_phone_band(
    input_wav: str, output_wav: str, seed: int, params: dict
) -> dict:
    """Bandpass + 16 -> 8 kHz -> mu-law G.711 -> 8 -> 16 kHz round-trip.

    OOD-param tier may request bit_depth < 8 by quantizing the linear PCM
    samples to 2**bit_depth levels before mu-law encoding (additional
    information loss).
    """
    samples, sr = _read_mono16k(input_wav)
    band_low = float(params.get("bandpass_low_hz", 300.0))
    band_high = float(params.get("bandpass_high_hz", 3400.0))
    order = int(params.get("bandpass_order", 6))
    target_sr = int(params.get("target_sr_hz", 8000))
    bit_depth = int(params.get("bit_depth", 8))
    if not (1 <= bit_depth <= 8):
        raise ValueError(f"phone_band: bit_depth must be 1..8, got {bit_depth}")

    sos = _butter_sos((band_low, band_high), sr, order, "bandpass")
    bp = scipy.signal.sosfiltfilt(sos, samples)

    down_factor = sr // target_sr
    if down_factor < 1:
        raise ValueError(f"phone_band: invalid target_sr={target_sr} for sr={sr}")
    narrow = scipy.signal.resample_poly(bp, up=1, down=down_factor)

    narrow_clipped = np.clip(narrow, -1.0, 1.0)
    if bit_depth < 8:
        levels = (1 << bit_depth) - 1
        q = np.round((narrow_clipped + 1.0) * 0.5 * levels) / levels
        narrow_clipped = (q * 2.0 - 1.0)
    pcm_int16 = (narrow_clipped * 32767.0).astype("<i2").tobytes()
    ulaw_bytes = audioop.lin2ulaw(pcm_int16, 2)
    pcm_int16_back = audioop.ulaw2lin(ulaw_bytes, 2)
    narrow_decoded = np.frombuffer(pcm_int16_back, dtype="<i2").astype(np.float64) / 32767.0
    upsampled = scipy.signal.resample_poly(narrow_decoded, up=down_factor, down=1)

    out = _enforce_length(upsampled, len(samples))
    out = _peak_normalize(out)
    _write_pcm16(output_wav, out, sr)

    return {
        "condition_family": "phone_band",
        "random_seed": int(seed),
        "snr_db": None,
        "rir_id_or_null": None,
        "filter_params_json": _json.dumps(
            {
                "bandpass_low_hz": band_low,
                "bandpass_high_hz": band_high,
                "bandpass_order": order,
                "target_sr_hz": target_sr,
                "bit_depth": bit_depth,
                "codec": "mu_law_g711",
            },
            sort_keys=True,
        ),
        "source_audio_sha256": _sha256_file(input_wav),
        "output_audio_sha256": _sha256_file(output_wav),
    }


def sample_far_field_room(
    input_wav: str, output_wav: str, seed: int, params: dict
) -> dict:
    """Convolve with a synthetic exp-decay impulse response.

    rt60_s controls reverberation tail; mic_distance_m attenuates the direct
    path linearly (1/d) and inverts the direct-to-reverberant ratio in dB
    (drr_db = 6 - 6 * log2(d)).
    """
    samples, sr = _read_mono16k(input_wav)
    speech_rms = _rms(samples)
    if speech_rms < RMS_EPS:
        raise ZeroSpeechRmsError(f"speech RMS underflow: {input_wav}")
    rt60_s = float(params["rt60_s"])
    mic_distance_m = float(params.get("mic_distance_m", 1.0))
    ir_length_s = float(params.get("ir_length_s", max(0.5, 1.5 * rt60_s)))
    drr_db = float(params.get("drr_db", 6.0 - 6.0 * math.log2(max(mic_distance_m, 0.5))))

    rng = np.random.default_rng(int(seed))
    ir_len = max(int(ir_length_s * sr), 16)
    tau = rt60_s / math.log(1000.0)
    t = np.arange(ir_len) / sr
    env = np.exp(-t / tau)
    ir_noise = rng.standard_normal(ir_len)
    ir_tail = ir_noise * env
    direct_amp = 1.0 / max(mic_distance_m, 0.5)
    tail_rms_target = direct_amp * 10 ** (drr_db / 20.0)
    cur_rms = _rms(ir_tail)
    if cur_rms < RMS_EPS:
        raise ZeroNoiseRmsError("far_field_room: IR tail RMS underflow")
    ir_tail_scaled = ir_tail * (tail_rms_target / cur_rms)
    ir = np.zeros(ir_len, dtype=np.float64)
    ir[0] = direct_amp
    ir[1:] = ir_tail_scaled[1:]

    convolved = scipy.signal.fftconvolve(samples, ir, mode="full")
    out = _enforce_length(convolved, len(samples))
    out = _peak_normalize(out)
    _write_pcm16(output_wav, out, sr)

    rir_id = hashlib.sha256(
        f"{DEGRADATION_VERSION}|far_field_room|{seed}|{rt60_s}|{mic_distance_m}".encode("utf-8")
    ).hexdigest()[:16]

    return {
        "condition_family": "far_field_room",
        "random_seed": int(seed),
        "snr_db": None,
        "rir_id_or_null": rir_id,
        "filter_params_json": _json.dumps(
            {
                "rt60_s": rt60_s,
                "mic_distance_m": mic_distance_m,
                "ir_length_s": ir_length_s,
                "drr_db": drr_db,
            },
            sort_keys=True,
        ),
        "source_audio_sha256": _sha256_file(input_wav),
        "output_audio_sha256": _sha256_file(output_wav),
    }


def sample_muffled_lowpass(
    input_wav: str, output_wav: str, seed: int, params: dict
) -> dict:
    """Lowpass at lowpass_hz with attenuation_db gain applied to the result."""
    samples, sr = _read_mono16k(input_wav)
    lowpass_hz = float(params["lowpass_hz"])
    attenuation_db = float(params["attenuation_db"])
    order = int(params.get("lowpass_order", 4))

    sos = _butter_sos(lowpass_hz, sr, order, "lowpass")
    lp = scipy.signal.sosfiltfilt(sos, samples)
    out = lp * 10 ** (attenuation_db / 20.0)
    out = _enforce_length(np.asarray(out, dtype=np.float64), len(samples))
    out = _peak_normalize(out)
    _write_pcm16(output_wav, out, sr)

    return {
        "condition_family": "muffled_lowpass",
        "random_seed": int(seed),
        "snr_db": None,
        "rir_id_or_null": None,
        "filter_params_json": _json.dumps(
            {
                "lowpass_hz": lowpass_hz,
                "lowpass_order": order,
                "attenuation_db": attenuation_db,
            },
            sort_keys=True,
        ),
        "source_audio_sha256": _sha256_file(input_wav),
        "output_audio_sha256": _sha256_file(output_wav),
    }


SAMPLE_FUNCTIONS: dict = {
    "clean": sample_clean,
    "cafe_noise": sample_cafe_noise,
    "phone_band": sample_phone_band,
    "far_field_room": sample_far_field_room,
    "muffled_lowpass": sample_muffled_lowpass,
}

__all__ += [
    "V347_FAMILIES",
    "SAMPLE_FUNCTIONS",
    "sample_clean",
    "sample_cafe_noise",
    "sample_phone_band",
    "sample_far_field_room",
    "sample_muffled_lowpass",
]
