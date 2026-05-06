"""B12.1 RotatingFileHandler smoke.

Configures the rotating file handler against a tmp_path log dir with a tiny
maxBytes so that emitting a few KB of JSON forces at least one rotation.
Asserts the produced files match the demo.${short_service}.log pattern and
that rotated backups exist.
"""

from __future__ import annotations

import logging
import os

import pytest

from libs.common.demo_settings import DemoSettings
from libs.observability.log_rotation import (
    build_rotating_file_handler,
    short_service,
)
from libs.observability.logging import configure_logging


def test_short_service_strips_demo_prefix():
    assert short_service("demo-api") == "api"
    assert short_service("demo-worker") == "worker"
    assert short_service("api") == "api"
    assert short_service("custom") == "custom"


def _make_settings(tmp_path):
    return DemoSettings(
        demo_runtime_root=tmp_path,
        demo_log_to_file=True,
        demo_log_max_bytes=512,
        demo_log_backup_count=2,
        demo_log_filename_prefix="demo",
    )


def test_rotating_file_handler_disabled_when_flag_off(tmp_path):
    settings = DemoSettings(demo_runtime_root=tmp_path, demo_log_to_file=False)
    h = build_rotating_file_handler(settings, service="demo-api")
    assert h is None


def test_rotating_file_handler_writes_and_rotates(tmp_path):
    settings = _make_settings(tmp_path)
    handler = build_rotating_file_handler(settings, service="demo-api")
    if handler is None:
        pytest.skip("rotating file handler unavailable in this runtime")
    try:
        configure_logging("demo-api", extra_handlers=[handler])
        log = logging.getLogger("demo-api.test_rotation")
        # Emit enough lines to overflow maxBytes=512 several times.
        for i in range(60):
            log.error(
                "demo.test_rotation",
                extra={"job_id": "00000000-0000-0000-0000-000000000000", "i": i},
            )
        handler.flush()
    finally:
        # Replace handlers back to default so we don't keep file handles open.
        configure_logging("demo-api")

    files = sorted(os.listdir(tmp_path / "logs"))
    api_log_files = [f for f in files if f.startswith("demo.api.log")]
    assert "demo.api.log" in api_log_files
    rotated = [f for f in api_log_files if f != "demo.api.log"]
    assert len(rotated) >= 1, f"expected at least one rotated backup, saw {api_log_files}"
    # Each rotated backup must be at or below maxBytes.
    for f in rotated:
        size = (tmp_path / "logs" / f).stat().st_size
        assert size <= 512


def test_rotating_file_handler_uses_correct_filename(tmp_path):
    settings = _make_settings(tmp_path)
    a = build_rotating_file_handler(settings, service="demo-api")
    w = build_rotating_file_handler(settings, service="demo-worker")
    assert a is not None and w is not None
    assert a.baseFilename.endswith("/demo.api.log")
    assert w.baseFilename.endswith("/demo.worker.log")
    a.close()
    w.close()
