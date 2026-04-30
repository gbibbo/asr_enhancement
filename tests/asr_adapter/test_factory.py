from __future__ import annotations

import pytest

from libs.asr_adapter.assemblyai import AssemblyAIAdapter
from libs.asr_adapter.errors import AdapterTranscriptionError
from libs.asr_adapter.factory import make_asr_adapter
from libs.asr_adapter.fake import FakeASRAdapter
from libs.common.settings import Settings


def _settings(**overrides) -> Settings:
    base = {
        "database_url": "postgresql+psycopg://test:test@localhost/test",
        "redis_url": "redis://localhost:6379/0",
        "minio_endpoint": "localhost:9000",
        "minio_access_key": "minioadmin",
        "minio_secret_key": "minioadmin",
    }
    base.update(overrides)
    return Settings(**base)


def test_make_asr_adapter_returns_fake_adapter_when_provider_is_fake():
    settings = _settings(asr_provider="fake")
    adapter = make_asr_adapter(settings)
    assert isinstance(adapter, FakeASRAdapter)


def test_make_asr_adapter_returns_assemblyai_adapter_when_configured():
    settings = _settings(asr_provider="assemblyai", assemblyai_api_key="sk-live-abc")
    adapter = make_asr_adapter(settings)
    assert isinstance(adapter, AssemblyAIAdapter)


def test_make_asr_adapter_raises_when_assemblyai_selected_and_key_missing():
    settings = _settings(asr_provider="assemblyai", assemblyai_api_key=None)
    with pytest.raises(AdapterTranscriptionError, match="ASSEMBLYAI_API_KEY"):
        make_asr_adapter(settings)
