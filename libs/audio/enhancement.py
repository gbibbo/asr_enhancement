from __future__ import annotations

import abc
import dataclasses
import os
import shutil
import subprocess
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
# DeepFilterNet3 real-time speech enhancement (denoise + dereverb), run via the
# self-contained `deep-filter` binary (no Python/torch). Reconstructs the
# degraded audio before ASR — the honest, on-device stand-in for a hosted
# enhancer while Hecttor SDK access is pending.
DEEPFILTERNET_ENHANCER_VERSION: str = "deepfilternet3"
# Hecttor AI (Saima) enhancer. On-device SDK, no public REST API: activation
# needs the private `hecttor_sdk` wheel and a HECTTOR_API_KEY, both obtained from
# hecttor.ai. The adapter below is wired so activation is trivial once granted.
HECTTOR_ENHANCER_VERSION: str = "hecttor"


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


# ---------------------------------------------------------------------------
# DeepFilterNet3 enhancer (on-device, real reconstruction)
# ---------------------------------------------------------------------------

DEEP_FILTER_BINARY_ENV = "DEEP_FILTER_BIN"
_DEEP_FILTER_TIMEOUT_SECONDS = 120


def resolve_deep_filter_binary() -> Optional[str]:
    """Return the path to the `deep-filter` binary, or None if not installed.

    Honors the DEEP_FILTER_BIN environment override, then falls back to a
    `deep-filter` executable on PATH.
    """
    override = os.environ.get(DEEP_FILTER_BINARY_ENV)
    if override:
        candidate = Path(override)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
        return None
    found = shutil.which("deep-filter")
    return found


class DeepFilterNetEnhancer(EnhancerAdapter):
    """DeepFilterNet3 speech enhancer via the self-contained `deep-filter` CLI.

    Runs denoise + dereverb on the input WAV and returns the reconstructed WAV.
    On any failure (binary missing, non-zero exit, no output) it returns the raw
    input unchanged with ``enhancement_fallback=True`` so the job still
    completes honestly rather than aborting.
    """

    @property
    def enhancer_version(self) -> str:
        return DEEPFILTERNET_ENHANCER_VERSION

    def enhance(self, audio_path: Path, output_dir: Path, job_id: str) -> EnhancementResult:
        binary = resolve_deep_filter_binary()
        if binary is None:
            return EnhancementResult(
                output_path=audio_path,
                preset_applied=DEEPFILTERNET_ENHANCER_VERSION,
                enhanced=False,
                enhancement_fallback=True,
                diagnostic={"fallback_reason": "deep-filter binary not found"},
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        work_dir = output_dir / "deepfilternet"
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            completed = subprocess.run(
                [binary, "--out-dir", str(work_dir), str(audio_path)],
                capture_output=True,
                timeout=_DEEP_FILTER_TIMEOUT_SECONDS,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.decode("utf-8", "replace").strip()[-200:]
                raise RuntimeError(f"deep-filter exit {completed.returncode}: {stderr}")
            produced = sorted(work_dir.glob("*.wav"))
            if not produced:
                raise RuntimeError("deep-filter produced no output file")
            final_path = output_dir / "enhanced_deepfilternet3.wav"
            shutil.move(str(produced[0]), str(final_path))
            if not _validate_output(final_path):
                raise RuntimeError("Enhanced output validation failed")
            return EnhancementResult(
                output_path=final_path,
                preset_applied=DEEPFILTERNET_ENHANCER_VERSION,
                enhanced=True,
                enhancement_fallback=False,
                diagnostic={"backend": "deepfilternet3"},
            )
        except Exception as exc:  # noqa: BLE001 - honest fallback, never abort the job
            return EnhancementResult(
                output_path=audio_path,
                preset_applied=DEEPFILTERNET_ENHANCER_VERSION,
                enhanced=False,
                enhancement_fallback=True,
                diagnostic={"fallback_reason": str(exc)[:240]},
            )


# ---------------------------------------------------------------------------
# GTCRN enhancer (on-device ONNX, real reconstruction — works on 16 KB pages)
# ---------------------------------------------------------------------------

GTCRN_ONNX_PATH_ENV = "GTCRN_ONNX_PATH"
DEFAULT_GTCRN_ONNX_PATH = "/app/models/gtcrn.onnx"
GTCRN_ENHANCER_VERSION: str = "gtcrn"
_GTCRN_SR = 16000
_GTCRN_NFFT = 512
_GTCRN_HOP = 256


class GtcrnOnnxEnhancer(EnhancerAdapter):
    """GTCRN speech enhancer via onnxruntime (ultra-light, on-device).

    Streaming ONNX model: one STFT frame at a time with three recurrent caches
    (init to zeros). STFT/ISTFT match the reference: n_fft=512, hop=256, window
    hann(512)**0.5, center padding. Runs on the Raspberry Pi's 16 KB pages with
    no PyTorch and no jemalloc (unlike the DeepFilterNet binary). Honest fallback
    to the raw input on any failure so the job never aborts.
    """

    _session: Any = None

    @property
    def enhancer_version(self) -> str:
        return GTCRN_ENHANCER_VERSION

    def _get_session(self, model_path: str) -> Any:
        if GtcrnOnnxEnhancer._session is None:
            import onnxruntime as ort

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 1
            opts.inter_op_num_threads = 1
            GtcrnOnnxEnhancer._session = ort.InferenceSession(
                model_path, sess_options=opts, providers=["CPUExecutionProvider"]
            )
        return GtcrnOnnxEnhancer._session

    def enhance(self, audio_path: Path, output_dir: Path, job_id: str) -> EnhancementResult:
        model_path = os.environ.get(GTCRN_ONNX_PATH_ENV, DEFAULT_GTCRN_ONNX_PATH)
        try:
            if not Path(model_path).is_file():
                raise RuntimeError(f"gtcrn model not found at {model_path}")
            session = self._get_session(model_path)

            audio, sr = sf.read(audio_path, dtype="float32", always_2d=False)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            audio = np.ascontiguousarray(audio, dtype=np.float32)
            if sr != _GTCRN_SR:
                from math import gcd

                from scipy.signal import resample_poly

                g = gcd(int(sr), _GTCRN_SR)
                audio = resample_poly(audio, _GTCRN_SR // g, int(sr) // g).astype(np.float32)

            enhanced = self._run(session, audio)

            output_dir.mkdir(parents=True, exist_ok=True)
            final_path = output_dir / "enhanced_gtcrn.wav"
            sf.write(final_path, enhanced, _GTCRN_SR, subtype="PCM_16")
            if not _validate_output(final_path):
                raise RuntimeError("Enhanced output validation failed")
            return EnhancementResult(
                output_path=final_path,
                preset_applied=GTCRN_ENHANCER_VERSION,
                enhanced=True,
                enhancement_fallback=False,
                diagnostic={"backend": "gtcrn"},
            )
        except Exception as exc:  # noqa: BLE001 - honest fallback, never abort the job
            return EnhancementResult(
                output_path=audio_path,
                preset_applied=GTCRN_ENHANCER_VERSION,
                enhanced=False,
                enhancement_fallback=True,
                diagnostic={"fallback_reason": str(exc)[:240]},
            )

    @staticmethod
    def _run(session: Any, audio: np.ndarray) -> np.ndarray:
        n_fft, hop = _GTCRN_NFFT, _GTCRN_HOP
        pad = n_fft // 2
        from scipy.signal.windows import hann

        window = (hann(n_fft, sym=False) ** 0.5).astype(np.float64)

        x = np.pad(audio.astype(np.float64), (pad, pad), mode="reflect")
        if len(x) < n_fft:
            x = np.pad(x, (0, n_fft - len(x)), mode="constant")
        num_frames = 1 + (len(x) - n_fft) // hop

        conv_cache = np.zeros((2, 1, 16, 16, 33), dtype=np.float32)
        tra_cache = np.zeros((2, 3, 1, 1, 16), dtype=np.float32)
        inter_cache = np.zeros((2, 1, 33, 16), dtype=np.float32)

        out = np.zeros(len(x), dtype=np.float64)
        wsum = np.zeros(len(x), dtype=np.float64)
        w2 = window ** 2

        for i in range(num_frames):
            start = i * hop
            seg = x[start : start + n_fft] * window
            spec = np.fft.rfft(seg).astype(np.complex64)
            mix = np.empty((1, n_fft // 2 + 1, 1, 2), dtype=np.float32)
            mix[0, :, 0, 0] = spec.real
            mix[0, :, 0, 1] = spec.imag
            enh, conv_cache, tra_cache, inter_cache = session.run(
                None,
                {
                    "mix": mix,
                    "conv_cache": conv_cache,
                    "tra_cache": tra_cache,
                    "inter_cache": inter_cache,
                },
            )
            enh_spec = enh[0, :, 0, 0] + 1j * enh[0, :, 0, 1]
            frame = np.fft.irfft(enh_spec, n=n_fft) * window
            out[start : start + n_fft] += frame
            wsum[start : start + n_fft] += w2

        nz = wsum > 1e-8
        out[nz] /= wsum[nz]
        out = out[pad : len(out) - pad] if pad > 0 else out
        out = out[: len(audio)]
        return np.clip(out, -1.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# Hecttor AI enhancer (on-device SDK; wired, activated when access is granted)
# ---------------------------------------------------------------------------

HECTTOR_API_KEY_ENV = "HECTTOR_API_KEY"
HECTTOR_MODEL_ENV = "HECTTOR_MODEL"
DEFAULT_HECTTOR_MODEL = "crest-2.0"


def hecttor_is_available() -> bool:
    """True only if the private hecttor_sdk is importable AND an API key is set.

    Both are obtained from Hecttor/Saima AI (hecttor.ai). Until then the demo
    uses DeepFilterNet as the on-device reconstruction stand-in.
    """
    if not os.environ.get(HECTTOR_API_KEY_ENV):
        return False
    try:
        import hecttor_sdk  # type: ignore  # noqa: F401
    except Exception:
        return False
    return True


class HecttorEnhancer(EnhancerAdapter):
    """Hecttor AI speech-reconstruction enhancer.

    Hecttor is an on-device SDK (no public REST API). Activation requires the
    private ``hecttor_sdk`` wheel (platform-specific) and a ``HECTTOR_API_KEY``,
    both from hecttor.ai. This adapter is wired end-to-end; the single call site
    marked below must be reconciled with the real ``hecttor_sdk`` method names
    once evaluation access is granted (models: crest-1.0/2.0, mist-1.0,
    coda-1.0/coda-vi-1.0). Until then the factory does not hand this adapter out.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self._model = model or os.environ.get(HECTTOR_MODEL_ENV, DEFAULT_HECTTOR_MODEL)

    @property
    def enhancer_version(self) -> str:
        return f"{HECTTOR_ENHANCER_VERSION}_{self._model}"

    def enhance(self, audio_path: Path, output_dir: Path, job_id: str) -> EnhancementResult:
        api_key = os.environ.get(HECTTOR_API_KEY_ENV)
        try:
            import hecttor_sdk  # type: ignore
        except Exception as exc:  # noqa: BLE001
            return EnhancementResult(
                output_path=audio_path,
                preset_applied=self.enhancer_version,
                enhanced=False,
                enhancement_fallback=True,
                diagnostic={"fallback_reason": f"hecttor_sdk not installed: {exc}"[:240]},
            )
        if not api_key:
            return EnhancementResult(
                output_path=audio_path,
                preset_applied=self.enhancer_version,
                enhanced=False,
                enhancement_fallback=True,
                diagnostic={"fallback_reason": "HECTTOR_API_KEY not set"},
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        final_path = output_dir / "enhanced_hecttor.wav"
        try:
            samples, sr = sf.read(audio_path, dtype="float32", always_2d=False)
            # === Hecttor SDK call site (reconcile with hecttor_sdk docs on access) ===
            # The Hermes SDK processes PCM audio on-device; the exact constructor
            # and method names are confirmed against the wheel Saima provides.
            enhancer = hecttor_sdk.Enhancer(api_key=api_key, model=self._model)  # type: ignore[attr-defined]
            enhanced = enhancer.process(samples, sample_rate=sr)  # type: ignore[attr-defined]
            # ========================================================================
            sf.write(final_path, np.asarray(enhanced), sr, subtype="PCM_16")
            if not _validate_output(final_path):
                raise RuntimeError("Enhanced output validation failed")
            return EnhancementResult(
                output_path=final_path,
                preset_applied=self.enhancer_version,
                enhanced=True,
                enhancement_fallback=False,
                diagnostic={"backend": "hecttor", "model": self._model},
            )
        except Exception as exc:  # noqa: BLE001 - honest fallback, never abort the job
            return EnhancementResult(
                output_path=audio_path,
                preset_applied=self.enhancer_version,
                enhanced=False,
                enhancement_fallback=True,
                diagnostic={"fallback_reason": str(exc)[:240]},
            )
