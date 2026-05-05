"""B11.1c version-pin drift guard.

Pins the constants exported from services/frontend/app/demo/versions.ts to
libs/common/versions.py so any future Python-side bump (METRICS_VERSION,
DEGRADATION_VERSION, DEFAULT_ENHANCER_VERSION) must be reflected on the
frontend in the same change. Mirrors the regex-based static-test pattern
established by tests/demo/test_b11_1a_degradation_id_drift.py — keeps the
gate cheap on RP5 without adding a JS test framework.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from libs.common import versions as backend_versions


_VERSIONS_TS = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "frontend"
    / "app"
    / "demo"
    / "versions.ts"
)


def _read_versions_ts() -> str:
    if not _VERSIONS_TS.is_file():
        pytest.fail(f"Expected versions.ts at {_VERSIONS_TS}, but file is missing.")
    return _VERSIONS_TS.read_text(encoding="utf-8")


def _extract_const(text: str, name: str) -> str:
    pattern = re.compile(
        rf'export\s+const\s+{re.escape(name)}\s*=\s*"([^"]+)"\s*;',
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match is None:
        pytest.fail(
            f"Could not find `export const {name} = \"...\";` in versions.ts. "
            "B11.1c requires this constant to be present and pinned."
        )
    return match.group(1)


def test_degradation_version_pinned_to_backend() -> None:
    text = _read_versions_ts()
    ts_value = _extract_const(text, "DEGRADATION_VERSION")
    assert ts_value == backend_versions.DEGRADATION_VERSION, (
        "versions.ts DEGRADATION_VERSION drift: "
        f"frontend={ts_value!r}, backend={backend_versions.DEGRADATION_VERSION!r}"
    )


def test_metrics_version_pinned_to_backend() -> None:
    text = _read_versions_ts()
    ts_value = _extract_const(text, "METRICS_VERSION")
    assert ts_value == backend_versions.METRICS_VERSION, (
        "versions.ts METRICS_VERSION drift: "
        f"frontend={ts_value!r}, backend={backend_versions.METRICS_VERSION!r}"
    )


def test_default_enhancer_version_pinned_to_backend() -> None:
    text = _read_versions_ts()
    ts_value = _extract_const(text, "DEFAULT_ENHANCER_VERSION")
    assert ts_value == backend_versions.DEFAULT_ENHANCER_VERSION, (
        "versions.ts DEFAULT_ENHANCER_VERSION drift: "
        f"frontend={ts_value!r}, "
        f"backend={backend_versions.DEFAULT_ENHANCER_VERSION!r}"
    )


def test_default_enhancer_version_is_not_bypass_synonym() -> None:
    """DEFAULT_ENHANCER_VERSION must not be the literal string "bypass".

    B11.1c bypass detection uses ``enhancer_version === "bypass"`` literally
    (matches BYPASS_ENHANCER_VERSION in libs/audio/enhancement.py). If a
    future refactor makes DEFAULT_ENHANCER_VERSION == "bypass", page.tsx
    rendering of the bypass note must be re-audited; this test fails first.
    """
    assert backend_versions.DEFAULT_ENHANCER_VERSION != "bypass", (
        "DEFAULT_ENHANCER_VERSION became 'bypass' on the backend; "
        "page.tsx bypass detection must be re-audited."
    )
