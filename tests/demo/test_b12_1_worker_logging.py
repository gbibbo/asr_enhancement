"""B12.1 demo-worker logging parity guard.

Static guard: the demo-worker must use libs.observability.logging.configure_logging
("demo-worker") rather than the plain logging.basicConfig call that was in
place pre-B12.1. We assert this via a source-level grep so we do not need
to start the worker loop in the test.
"""

from __future__ import annotations

import re
from pathlib import Path


_WORKER_PATH = (
    Path(__file__).resolve().parents[2]
    / "services" / "worker" / "app" / "demo_worker_main.py"
)


def _read_worker_source() -> str:
    return _WORKER_PATH.read_text(encoding="utf-8")


def test_worker_imports_configure_logging():
    src = _read_worker_source()
    assert re.search(
        r"from\s+libs\.observability\.logging\s+import\s+(?:[^#\n]*?)configure_logging",
        src,
    ), "demo_worker_main.py must import configure_logging from libs.observability.logging"


def test_worker_calls_configure_logging_with_service_tag():
    src = _read_worker_source()
    assert re.search(
        r'configure_logging\s*\(\s*[\'"]demo-worker[\'"]',
        src,
    ), "demo_worker_main.py must call configure_logging(\"demo-worker\", ...)"


def test_worker_does_not_use_logging_basicConfig():
    src = _read_worker_source()
    assert "logging.basicConfig" not in src, (
        "demo_worker_main.py must not call logging.basicConfig — use "
        "libs.observability.logging.configure_logging instead so JSON "
        "logging and the hard-deny redaction set are in effect."
    )


def test_worker_attaches_rotating_file_handler():
    src = _read_worker_source()
    assert re.search(
        r"build_rotating_file_handler\s*\(", src
    ), "demo_worker_main.py must wire the rotating file handler when DEMO_LOG_TO_FILE=true"
