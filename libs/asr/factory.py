from __future__ import annotations

from libs.asr.assemblyai_provider import AssemblyAIAdapter
from libs.asr.base import ASRAdapter
from libs.asr.errors import AdapterTranscriptionError
from libs.asr.fake_provider import FakeASRAdapter
from libs.common.settings import Settings


def make_asr_adapter(settings: Settings) -> ASRAdapter:
    """Construct the correct ASR adapter from application settings."""
    if settings.asr_provider == "assemblyai":
        if not settings.assemblyai_api_key:
            raise AdapterTranscriptionError(
                "AssemblyAI provider selected but ASSEMBLYAI_API_KEY is not set"
            )
        return AssemblyAIAdapter(api_key=settings.assemblyai_api_key)
    return FakeASRAdapter(fake_transcript=settings.fake_transcript)
