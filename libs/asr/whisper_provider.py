from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from libs.asr.base import ASRAdapter
from libs.asr.errors import AdapterTranscriptionError, InputFileNotFoundError
from libs.asr.schema import ASRResult

try:
    from faster_whisper import WhisperModel as _WhisperModel

    _FASTER_WHISPER_AVAILABLE = True
except ImportError:
    _WhisperModel = None  # type: ignore[assignment,misc]
    _FASTER_WHISPER_AVAILABLE = False

_NOT_ENGLISH_THRESHOLD = 0.5


class WhisperAdapter(ASRAdapter):
    MODEL_NAME: str = "tiny.en"

    def __init__(
        self,
        *,
        model_name: str = MODEL_NAME,
        device: str = "cpu",
        compute_type: str = "int8",
        model_cache_dir: Optional[str] = None,
        _model: Optional[Any] = None,
    ) -> None:
        if _model is None and not _FASTER_WHISPER_AVAILABLE:
            raise AdapterTranscriptionError(
                "faster-whisper is not installed. "
                "Install it with: pip install faster-whisper"
            )
        self._model_name = model_name
        self._device = device
        self._compute_type = compute_type
        self._cache_dir = model_cache_dir or os.environ.get("WHISPER_MODEL_CACHE")
        self._model = _model

    def _get_model(self) -> Any:
        if self._model is None:
            kwargs: dict[str, Any] = {
                "device": self._device,
                "compute_type": self._compute_type,
            }
            if self._cache_dir:
                kwargs["download_root"] = self._cache_dir
            self._model = _WhisperModel(self._model_name, **kwargs)
        return self._model

    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult:
        if not audio_path.is_file():
            raise InputFileNotFoundError(f"Input file not found: {audio_path}")
        model = self._get_model()
        segments_iter, info = model.transcribe(str(audio_path), language="en")
        segments = list(segments_iter)
        text = " ".join(s.text.strip() for s in segments if s.text.strip())
        raw: dict[str, Any] = {
            "model": self._model_name,
            "language": info.language,
            "language_probability": info.language_probability,
        }
        if info.language != "en" and info.language_probability > _NOT_ENGLISH_THRESHOLD:
            raw["language_warning"] = (
                "Detected language is not English. This demo is designed for English speech, "
                "so results may be unreliable. Continue?"
            )
        return ASRResult(
            text=text,
            language=info.language,
            duration_seconds=info.duration if hasattr(info, "duration") else None,
            segments=[
                {"start": s.start, "end": s.end, "text": s.text}
                for s in segments
            ],
            words=[],
            provider="whisper",
            provider_job_id=None,
            raw_payload=raw,
        )
