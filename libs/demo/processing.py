"""Per-job upload processing pipeline (B9.2).

The worker delegates each claimed job to ``process_upload_job`` here. The
function is pure Python and side-effect controlled: it never deletes uploads
or per-job artifacts (cleanup is owned by B9.4), never reads or writes
``cache_entries`` (curated cache is disjoint from uploads), never logs
transcripts, ground truth, or original upload filenames, and refuses to
silently fall back from one provider to another.
"""

from __future__ import annotations

import dataclasses
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from libs.audio.degradations import (
    KNOWN_DEGRADATION_IDS,
    apply_degradation,
)
from libs.audio.enhancement import (
    BYPASS_ENHANCER_VERSION,
    BypassEnhancer,
    EnhancerAdapter,
)
from libs.asr.errors import AdapterError
from libs.asr.schema import ASRResult
from libs.asr.whisper_provider import WhisperAdapter
from libs.common.demo_settings import DemoSettings


log = logging.getLogger("demo-worker.processing")


PROVIDER_WHISPER = "whisper"
PROVIDER_ASSEMBLYAI = "assemblyai"
DEFAULT_WHISPER_MODEL_VERSION = "tiny.en"

_ASSEMBLYAI_GATED_MESSAGE = (
    "AssemblyAI is not enabled for uploads in B9.2. "
    "Switch provider to 'whisper'."
)
_METRICGAN_GATED_MESSAGE = (
    "Enhancer 'metricgan_plus_pretrained' is owned by training task T4.1 "
    "and is not enabled in the demo runtime. Use 'bypass'."
)


class ProviderDisabledError(Exception):
    """Raised by an ASR factory when the requested provider is disabled."""


class EnhancerNotSupportedError(Exception):
    """Raised by the enhancer factory when the requested enhancer is rejected."""


class _ASRAdapterLike(Protocol):
    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult: ...


ASRFactory = Callable[[str], _ASRAdapterLike]
EnhancerFactory = Callable[[str], EnhancerAdapter]
UpdateArtifacts = Callable[..., None]


@dataclasses.dataclass(frozen=True)
class ProcessingOutcome:
    status: str  # "completed" | "failed"
    result: Optional[dict] = None
    error_message: Optional[str] = None


def default_asr_factory(settings: DemoSettings) -> ASRFactory:
    """Return a factory that maps provider name to an ASR adapter.

    Whisper returns a ``WhisperAdapter`` (faster-whisper tiny.en).
    AssemblyAI is gated for uploads in B9.2 and raises
    ``ProviderDisabledError``; no silent fallback.
    """
    del settings  # currently unused; kept for forward compatibility

    def _factory(provider: str) -> _ASRAdapterLike:
        if provider == PROVIDER_WHISPER:
            return WhisperAdapter()
        if provider == PROVIDER_ASSEMBLYAI:
            raise ProviderDisabledError(_ASSEMBLYAI_GATED_MESSAGE)
        raise ProviderDisabledError(
            f"Unsupported provider {provider!r}. Use 'whisper'."
        )

    return _factory


def default_enhancer_factory(settings: DemoSettings) -> EnhancerFactory:
    """Return a factory that maps enhancer_version to an enhancer adapter."""
    del settings

    def _factory(enhancer_version: str) -> EnhancerAdapter:
        if enhancer_version == BYPASS_ENHANCER_VERSION:
            return BypassEnhancer()
        if enhancer_version == "metricgan_plus_pretrained":
            raise EnhancerNotSupportedError(_METRICGAN_GATED_MESSAGE)
        raise EnhancerNotSupportedError(
            f"Unsupported enhancer {enhancer_version!r}. Use 'bypass'."
        )

    return _factory


def _safe_message(prefix: str, exc: BaseException) -> str:
    """Build a user-facing error message that does not leak transcript bodies."""
    msg = str(exc).strip() or exc.__class__.__name__
    if len(msg) > 240:
        msg = msg[:237] + "..."
    return f"{prefix}: {msg}"


def _resolve_enhancer_version(job: dict, settings: DemoSettings) -> str:
    raw = job.get("enhancer_version")
    if raw is None or raw == "":
        return settings.enhancer_version
    return str(raw)


def _resolve_provider(job: dict) -> str:
    raw = job.get("provider")
    if raw is None or raw == "":
        return PROVIDER_WHISPER
    return str(raw)


def _asr_model_version(provider: str, asr_result: ASRResult) -> str:
    if provider == PROVIDER_WHISPER:
        model = asr_result.raw_payload.get("model")
        if isinstance(model, str) and model:
            return model
        return DEFAULT_WHISPER_MODEL_VERSION
    return provider


def _language_probability(asr_result: ASRResult) -> Optional[float]:
    val = asr_result.raw_payload.get("language_probability")
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _time_transcribe(
    asr: _ASRAdapterLike, audio_path: Path, job_id: str
) -> tuple[ASRResult, float]:
    t0 = time.monotonic()
    result = asr.transcribe(audio_path, job_id)
    return result, time.monotonic() - t0


def process_upload_job(
    job: dict,
    settings: DemoSettings,
    *,
    asr_factory: ASRFactory,
    enhancer_factory: EnhancerFactory,
    update_artifacts: UpdateArtifacts,
) -> ProcessingOutcome:
    """Process one claimed upload job end-to-end.

    The worker is responsible for translating the returned ``ProcessingOutcome``
    into a single ``update_job_status`` call. This function only writes the
    ``degraded_artifact_path`` / ``enhanced_artifact_path`` columns via the
    injected ``update_artifacts`` callback when those paths become known.

    No GT, transcripts, or upload filenames are logged.
    """
    job_id = job["job_id"]
    provider = _resolve_provider(job)
    enhancer_version = _resolve_enhancer_version(job, settings)
    degradation_id = job.get("degradation_id")
    input_artifact_path = job.get("input_artifact_path")

    log.info(
        "job=%s provider=%s enhancer=%s degradation=%s start",
        job_id, provider, enhancer_version, degradation_id,
    )

    if not input_artifact_path:
        return ProcessingOutcome(
            status="failed",
            error_message="Uploaded audio file is missing.",
        )
    input_path = Path(input_artifact_path)
    if not input_path.is_file():
        return ProcessingOutcome(
            status="failed",
            error_message="Uploaded audio file is missing.",
        )

    try:
        enhancer = enhancer_factory(enhancer_version)
    except EnhancerNotSupportedError as exc:
        log.info(
            "job=%s rejected enhancer=%s reason=unsupported",
            job_id, enhancer_version,
        )
        return ProcessingOutcome(status="failed", error_message=str(exc))

    try:
        asr = asr_factory(provider)
    except ProviderDisabledError as exc:
        log.info(
            "job=%s rejected provider=%s reason=disabled",
            job_id, provider,
        )
        return ProcessingOutcome(status="failed", error_message=str(exc))

    job_artifacts_dir = settings.demo_artifacts_dir / "jobs" / job_id
    job_artifacts_dir.mkdir(parents=True, exist_ok=True)

    degraded_audio_path: Optional[Path] = None
    degradation_version: Optional[str] = None
    degradation_applied = False

    if degradation_id is not None and degradation_id != "":
        if degradation_id not in KNOWN_DEGRADATION_IDS:
            return ProcessingOutcome(
                status="failed",
                error_message=f"Unknown degradation_id: {degradation_id!r}.",
            )
        try:
            degraded = apply_degradation(
                degradation_id, input_path, job_artifacts_dir, seed=0
            )
        except Exception as exc:  # pragma: no cover - exercised by integration smoke
            return ProcessingOutcome(
                status="failed",
                error_message=_safe_message("Degradation failed", exc),
            )
        degraded_audio_path = degraded.output_path
        degradation_version = degraded.degradation_version
        degradation_applied = True
        update_artifacts(degraded_artifact_path=str(degraded_audio_path))

    raw_input_path = degraded_audio_path if degraded_audio_path is not None else input_path

    # Raw ASR (B9.2 action 4)
    try:
        raw_result, raw_latency = _time_transcribe(asr, raw_input_path, job_id)
    except AdapterError as exc:
        log.info("job=%s raw_asr=failed", job_id)
        return ProcessingOutcome(
            status="failed",
            error_message=_safe_message("Raw ASR failed", exc),
        )
    log.info(
        "job=%s raw_asr=succeeded latency=%.3fs language=%s",
        job_id, raw_latency, raw_result.language,
    )

    asr_model_version = _asr_model_version(provider, raw_result)

    # Enhanced ASR (B9.2 action 5).
    # Decision rule 3: if the enhanced path fails, complete the job with raw + enhanced_error.
    enhanced_block: Optional[dict] = None
    enhanced_error: Optional[str] = None
    enhanced_audio_path: Optional[Path] = None
    try:
        enhancement = enhancer.enhance(raw_input_path, job_artifacts_dir, job_id)
        if enhancement.output_path != raw_input_path:
            enhanced_audio_path = enhancement.output_path
            update_artifacts(enhanced_artifact_path=str(enhanced_audio_path))
        enhanced_result, enhanced_latency = _time_transcribe(
            asr, enhancement.output_path, job_id
        )
    except Exception as exc:  # noqa: BLE001
        # Decision rule 3: never abort the job because the enhanced path failed
        # after raw succeeded.
        log.info("job=%s enhanced_path=failed", job_id)
        enhanced_error = _safe_message("Enhanced path unavailable", exc)
    else:
        log.info(
            "job=%s enhanced_asr=succeeded latency=%.3fs preset=%s enhanced_flag=%s fallback=%s",
            job_id,
            enhanced_latency,
            enhancement.preset_applied,
            enhancement.enhanced,
            enhancement.enhancement_fallback,
        )
        enhanced_block = {
            "transcript": enhanced_result.text,
            "latency_seconds": float(enhanced_latency),
            "preset_applied": enhancement.preset_applied,
            "enhanced_flag": bool(enhancement.enhanced),
            "enhancement_fallback": bool(enhancement.enhancement_fallback),
        }

    result_payload: dict[str, Any] = {
        "source_type": "upload",
        "provider": provider,
        "asr_model_version": asr_model_version,
        "enhancer_version": enhancer_version,
        "degradation_id": degradation_id,
        "degradation_version": degradation_version,
        "degradation_applied": degradation_applied,
        "input_audio_path": str(input_path),
        "degraded_audio_path": str(degraded_audio_path) if degraded_audio_path else None,
        "enhanced_audio_path": str(enhanced_audio_path) if enhanced_audio_path else None,
        "raw": {
            "transcript": raw_result.text,
            "language": raw_result.language,
            "language_probability": _language_probability(raw_result),
            "latency_seconds": float(raw_latency),
        },
        "enhanced": enhanced_block,
        "enhanced_error": enhanced_error,
        "metrics": {},
        "warnings": [],
    }

    log.info("job=%s result=completed", job_id)
    return ProcessingOutcome(status="completed", result=result_payload)
