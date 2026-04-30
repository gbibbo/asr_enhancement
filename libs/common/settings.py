from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ALLOWED_PROVIDERS = {"fake", "assemblyai"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider
    asr_provider: str = "fake"
    assemblyai_api_key: Optional[str] = None
    # Fake adapter fixture text (optional; empty string treated as unset)
    fake_transcript: Optional[str] = None

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Object storage
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "asr-platform"
    minio_secure: bool = False

    # Upload limit (bytes); default 100 MB
    upload_limit_bytes: int = 104_857_600

    # Demo rate limit (requests per minute per client IP, applied only to
    # POST /v1/transcribe and POST /v1/enhance-and-transcribe). 0 disables.
    rate_limit_per_minute: int = 30

    # HPC / runtime paths (optional; not required at startup)
    asr_repo_root: Optional[Path] = None
    asr_runtime_root: Optional[Path] = None
    asr_artifacts_root: Optional[Path] = None
    asr_cache_root: Optional[Path] = None

    @field_validator("asr_provider", mode="before")
    @classmethod
    def normalize_asr_provider(cls, v: object) -> str:
        normalized = str(v).strip().lower()
        if normalized not in _ALLOWED_PROVIDERS:
            raise ValueError(
                f"asr_provider must be one of {sorted(_ALLOWED_PROVIDERS)!r}; got {v!r}"
            )
        return normalized

    @field_validator("upload_limit_bytes", mode="before")
    @classmethod
    def validate_upload_limit(cls, v: Any) -> int:
        value = int(v)
        if value <= 0:
            raise ValueError("upload_limit_bytes must be greater than 0")
        return value

    @field_validator("rate_limit_per_minute", mode="before")
    @classmethod
    def validate_rate_limit(cls, v: Any) -> int:
        value = int(v)
        if value < 0:
            raise ValueError("rate_limit_per_minute must be >= 0")
        return value

    @property
    def assemblyai_configured(self) -> bool:
        """True only when provider is assemblyai and the key is present."""
        return self.asr_provider == "assemblyai" and bool(self.assemblyai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
