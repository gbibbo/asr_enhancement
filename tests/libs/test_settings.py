from pathlib import Path

import pytest
from pydantic import ValidationError

from libs.common.settings import Settings, get_settings

REQUIRED = {
    "DATABASE_URL": "postgresql://asr:asr@localhost:5432/asr",
    "REDIS_URL": "redis://localhost:6379/0",
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}


@pytest.fixture(autouse=True)
def clear_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make(monkeypatch, extra=None, drop=None) -> Settings:
    """Set REQUIRED vars plus any extras; remove keys in drop."""
    env = {**REQUIRED, **(extra or {})}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    for k in drop or []:
        monkeypatch.delenv(k, raising=False)
    return Settings(_env_file=None)


# --- provider normalization and validation ---

def test_asr_provider_defaults_to_fake(monkeypatch):
    s = make(monkeypatch, drop=["ASR_PROVIDER"])
    assert s.asr_provider == "fake"


def test_asr_provider_explicit_fake(monkeypatch):
    s = make(monkeypatch, extra={"ASR_PROVIDER": "fake"})
    assert s.asr_provider == "fake"


def test_asr_provider_uppercase_fake(monkeypatch):
    s = make(monkeypatch, extra={"ASR_PROVIDER": "FAKE"})
    assert s.asr_provider == "fake"


def test_asr_provider_mixed_case_assemblyai(monkeypatch):
    s = make(monkeypatch, extra={"ASR_PROVIDER": "AssemblyAI"})
    assert s.asr_provider == "assemblyai"


def test_asr_provider_invalid_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, extra={"ASR_PROVIDER": "invalid"})


# --- required field validation ---

def test_database_url_missing_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, drop=["DATABASE_URL"])


def test_redis_url_missing_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, drop=["REDIS_URL"])


def test_minio_endpoint_missing_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, drop=["MINIO_ENDPOINT"])


def test_minio_access_key_missing_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, drop=["MINIO_ACCESS_KEY"])


def test_minio_secret_key_missing_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, drop=["MINIO_SECRET_KEY"])


# --- assemblyai_configured property ---

def test_assemblyai_not_configured_when_key_missing(monkeypatch):
    s = make(monkeypatch, extra={"ASR_PROVIDER": "assemblyai"}, drop=["ASSEMBLYAI_API_KEY"])
    assert s.assemblyai_configured is False


def test_assemblyai_configured_when_key_present(monkeypatch):
    s = make(monkeypatch, extra={"ASR_PROVIDER": "assemblyai", "ASSEMBLYAI_API_KEY": "testkey"})
    assert s.assemblyai_configured is True


# --- upload_limit_bytes ---

def test_upload_limit_default(monkeypatch):
    s = make(monkeypatch, drop=["UPLOAD_LIMIT_BYTES"])
    assert s.upload_limit_bytes == 104_857_600


def test_upload_limit_custom(monkeypatch):
    s = make(monkeypatch, extra={"UPLOAD_LIMIT_BYTES": "52428800"})
    assert s.upload_limit_bytes == 52_428_800


def test_upload_limit_zero_raises(monkeypatch):
    with pytest.raises(ValidationError):
        make(monkeypatch, extra={"UPLOAD_LIMIT_BYTES": "0"})


# --- optional path roots ---

def test_runtime_root_defaults_to_none(monkeypatch):
    s = make(monkeypatch, drop=["ASR_RUNTIME_ROOT"])
    assert s.asr_runtime_root is None


def test_runtime_root_parsed_as_path(monkeypatch):
    s = make(monkeypatch, extra={"ASR_RUNTIME_ROOT": "/tmp/rt"})
    assert s.asr_runtime_root == Path("/tmp/rt")


# --- get_settings caching ---

# --- fake_transcript ---

def test_fake_transcript_defaults_to_none(monkeypatch):
    s = make(monkeypatch, drop=["FAKE_TRANSCRIPT"])
    assert s.fake_transcript is None


def test_fake_transcript_from_env(monkeypatch):
    s = make(monkeypatch, extra={"FAKE_TRANSCRIPT": "custom text"})
    assert s.fake_transcript == "custom text"


# --- get_settings caching ---

def test_get_settings_caching(monkeypatch):
    for k, v in REQUIRED.items():
        monkeypatch.setenv(k, v)

    first = get_settings()
    second = get_settings()
    assert first is second

    get_settings.cache_clear()
    third = get_settings()
    assert third is not first
