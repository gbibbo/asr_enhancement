from libs.asr.base import ASRAdapter
from libs.asr.schema import ASRResult
from libs.asr.errors import AdapterError, InputFileNotFoundError, AdapterTranscriptionError
from libs.asr.fake_provider import FakeASRAdapter
from libs.asr.assemblyai_provider import AssemblyAIAdapter
from libs.asr.factory import make_asr_adapter


def test_fake_provider_is_asr_adapter():
    assert issubclass(FakeASRAdapter, ASRAdapter)


def test_assemblyai_provider_is_asr_adapter():
    assert issubclass(AssemblyAIAdapter, ASRAdapter)


def test_asr_result_is_dataclass():
    from dataclasses import fields
    assert len(fields(ASRResult)) > 0


def test_error_hierarchy():
    assert issubclass(InputFileNotFoundError, AdapterError)
    assert issubclass(AdapterTranscriptionError, AdapterError)


def test_make_asr_adapter_returns_fake_by_default(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:x@localhost/x")
    monkeypatch.setenv("REDIS_URL", "redis://localhost/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setenv("ASR_PROVIDER", "fake")
    from libs.common.settings import Settings
    settings = Settings()
    adapter = make_asr_adapter(settings)
    assert isinstance(adapter, FakeASRAdapter)
