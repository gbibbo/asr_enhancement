from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT",
    "DEMO_DB_PATH",
    "DEMO_UPLOAD_DIR",
    "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR",
    "DEMO_LOGS_DIR",
    "DEMO_WORKER_CONCURRENCY",
    "DEMO_QUEUE_MAX",
    "DEMO_UPLOAD_LIMIT_BYTES",
    "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "ASSEMBLYAI_API_KEY",
    "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD",
]


@pytest.fixture()
def isolated_env(monkeypatch, tmp_path):
    """Change to a tmp directory (no .env.demo) and clear all demo env vars."""
    monkeypatch.chdir(tmp_path)
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    yield


def test_demo_settings_loads_without_platform_env_vars(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_runtime_root is not None


def test_default_queue_max(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_queue_max == 10


def test_default_worker_concurrency(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_worker_concurrency == 1


def test_derived_db_path_under_runtime_root(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_db_path == s.demo_runtime_root / "db" / "demo.db"


def test_derived_upload_dir_under_runtime_root(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_upload_dir == s.demo_runtime_root / "uploads"


def test_derived_paths_under_runtime_root(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_cache_dir == s.demo_runtime_root / "cache"
    assert s.demo_artifacts_dir == s.demo_runtime_root / "artifacts"
    assert s.demo_logs_dir == s.demo_runtime_root / "logs"


def test_custom_runtime_root_propagates(monkeypatch, tmp_path):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    custom_root = tmp_path / "custom_runtime"
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(custom_root))
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_runtime_root == custom_root
    assert s.demo_db_path == custom_root / "db" / "demo.db"
    assert s.demo_upload_dir == custom_root / "uploads"


def test_custom_db_path_overrides_derivation(monkeypatch, tmp_path):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    custom_db = tmp_path / "my.db"
    monkeypatch.setenv("DEMO_DB_PATH", str(custom_db))
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_db_path == custom_db


def test_empty_string_db_path_falls_back_to_derived(monkeypatch, tmp_path):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.setenv("DEMO_DB_PATH", "")
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.demo_db_path == tmp_path / "db" / "demo.db"


def test_assemblyai_key_defaults_none(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.assemblyai_api_key is None


def test_enhancer_version_defaults_bypass(isolated_env):
    from libs.common.demo_settings import DemoSettings

    s = DemoSettings()
    assert s.enhancer_version == "bypass"


def test_demo_main_does_not_import_platform_settings():
    """demo_main must not import libs.common.settings.Settings."""
    # Reload to get a clean module state
    mod_name = "services.api.app.demo_main"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    importlib.import_module(mod_name)
    # libs.common.settings is allowed to be imported by other things,
    # but demo_main itself must not reference Settings
    demo_main_src = Path("services/api/app/demo_main.py").read_text()
    assert "from libs.common.settings" not in demo_main_src
    assert "libs.common.settings.Settings" not in demo_main_src
