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
    demo_upload_retention_hours: int = 24

    assemblyai_api_key: Optional[str] = None
    enhancer_version: str = "bypass"
    admin_stats_username: str = "admin"
    admin_stats_password: Optional[str] = None
    demo_examples_config: Path = Path("config/demo_examples.json")

    # B10.1 AssemblyAI cost-control settings. usd_per_second is a duration-based
    # estimate, not a billed amount; operators may override per host via env.
    demo_assemblyai_daily_soft_cap_usd: float = 5.0
    demo_assemblyai_warning_cap_usd: float = 35.0
    demo_assemblyai_hard_cap_usd: float = 45.0
    demo_assemblyai_usd_per_second: float = 0.000103

    @model_validator(mode="after")
    def fill_derived_paths(self) -> "DemoSettings":
        root = self.demo_runtime_root

        def _unset(p: Optional[Path]) -> bool:
            # pydantic-settings converts EMPTY_VAR="" to Path("."); treat as unset
            return p is None or str(p) == "."

        if _unset(self.demo_db_path):
            self.demo_db_path = root / "db" / "demo.db"
        if _unset(self.demo_upload_dir):
            self.demo_upload_dir = root / "uploads"
        if _unset(self.demo_cache_dir):
            self.demo_cache_dir = root / "cache"
        if _unset(self.demo_artifacts_dir):
            self.demo_artifacts_dir = root / "artifacts"
        if _unset(self.demo_logs_dir):
            self.demo_logs_dir = root / "logs"
        return self
