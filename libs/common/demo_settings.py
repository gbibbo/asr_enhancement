from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DemoSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.demo",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    demo_runtime_root: Path = Path("/home/gbibbo/asr_enhancement_runtime")
    demo_db_path: Optional[Path] = None
    demo_upload_dir: Optional[Path] = None
    demo_cache_dir: Optional[Path] = None
    demo_artifacts_dir: Optional[Path] = None
    demo_logs_dir: Optional[Path] = None

    demo_worker_concurrency: int = 1
    demo_queue_max: int = 10
    demo_upload_limit_bytes: int = 5_242_880
    demo_upload_max_duration_seconds: int = 30

    assemblyai_api_key: Optional[str] = None
    enhancer_version: str = "bypass"
    admin_stats_username: str = "admin"
    admin_stats_password: Optional[str] = None

    @model_validator(mode="after")
    def fill_derived_paths(self) -> "DemoSettings":
        root = self.demo_runtime_root
        if self.demo_db_path is None:
            self.demo_db_path = root / "db" / "demo.db"
        if self.demo_upload_dir is None:
            self.demo_upload_dir = root / "uploads"
        if self.demo_cache_dir is None:
            self.demo_cache_dir = root / "cache"
        if self.demo_artifacts_dir is None:
            self.demo_artifacts_dir = root / "artifacts"
        if self.demo_logs_dir is None:
            self.demo_logs_dir = root / "logs"
        return self
