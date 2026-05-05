"""B11.2 frontend static guard: cached-mode submitCached body shape.

Pins the cached-mode POST /demo/run-cached request body shipped from
services/frontend/app/demo/page.tsx. The prewarm cache key is built with
enhancer_version="bypass" (scripts/prewarm_cache.py::SUPPORTED_ENHANCER),
while libs/common/versions.py::DEFAULT_ENHANCER_VERSION is "1.0" — so the
backend default fallback in libs/demo/cache.py would yield a cache_miss
unless the frontend explicitly pins enhancer_version="bypass" on the
cached-mode request.

This test is pure text inspection: the demo container does not have Node,
so we cannot run the React click handler; instead we extract the
submitCached body literal and assert its shape. A separate proxy curl
smoke (run by the operator) confirms that this canonical body returns
cache_hit through the Next.js proxy.

Pattern mirrors tests/demo/test_b11_1a_degradation_id_drift.py and
tests/demo/test_b11_1c_frontend_comparison_static.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_PAGE_TSX = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "frontend"
    / "app"
    / "demo"
    / "page.tsx"
)


def _read_page() -> str:
    if not _PAGE_TSX.is_file():
        pytest.fail(f"Expected {_PAGE_TSX} to exist for B11.2.")
    return _PAGE_TSX.read_text(encoding="utf-8")


def _extract_submit_cached_body(text: str) -> str:
    """Return the JSON.stringify({...}) literal that submitCached sends to
    POST /api/demo/run-cached.

    We anchor on the run-cached fetch URL and walk forward to the closing
    "})" of the JSON.stringify argument. This intentionally captures only
    the cached-mode request body and not unrelated regions of the file
    (upload mode references "assemblyai" and "manualGt", which must not
    leak into the cached request).
    """
    fetch_idx = text.find('"/api/demo/run-cached"')
    if fetch_idx < 0:
        pytest.fail(
            'Expected services/frontend/app/demo/page.tsx to POST to '
            '"/api/demo/run-cached" in submitCached.'
        )
    stringify_idx = text.find("JSON.stringify(", fetch_idx)
    if stringify_idx < 0:
        pytest.fail(
            "Expected JSON.stringify(...) inside submitCached fetch body."
        )
    open_brace_idx = text.find("{", stringify_idx)
    if open_brace_idx < 0:
        pytest.fail("Could not locate '{' after JSON.stringify( in submitCached.")
    depth = 0
    end_idx = -1
    for i in range(open_brace_idx, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break
    if end_idx < 0:
        pytest.fail("Could not find matching '}' for submitCached body.")
    return text[open_brace_idx:end_idx]


def test_submit_cached_body_pins_enhancer_version_bypass() -> None:
    body = _extract_submit_cached_body(_read_page())
    pattern = re.compile(r'enhancer_version\s*:\s*"bypass"')
    assert pattern.search(body) is not None, (
        "Cached-mode submitCached body must include "
        '`enhancer_version: "bypass"` so the backend cache key matches the '
        "prewarmed entry. Without this pin, build_cache_key falls back to "
        'DEFAULT_ENHANCER_VERSION="1.0" and curated examples always return '
        f"cache_miss. Body literal:\n{body}"
    )


def test_submit_cached_body_keeps_provider_whisper() -> None:
    body = _extract_submit_cached_body(_read_page())
    pattern = re.compile(r'provider\s*:\s*"whisper"')
    assert pattern.search(body) is not None, (
        'Cached-mode submitCached body must keep `provider: "whisper"`. '
        "The cached/curated mode is whisper-only by plan §B11.1a. "
        f"Body literal:\n{body}"
    )


def test_submit_cached_body_does_not_introduce_assemblyai() -> None:
    body = _extract_submit_cached_body(_read_page())
    forbidden = re.compile(r"assemblyai", re.IGNORECASE)
    assert forbidden.search(body) is None, (
        'Cached-mode submitCached body must not reference "assemblyai". '
        "AssemblyAI is upload-mode only; introducing it into cached mode "
        f"would cross-contaminate provider routing. Body literal:\n{body}"
    )


def test_submit_cached_body_does_not_carry_ground_truth() -> None:
    body = _extract_submit_cached_body(_read_page())
    forbidden = re.compile(
        r"\b(manualGt|ground[_ ]?truth|reference|reference_text|\"gt\")\b",
        re.IGNORECASE,
    )
    matches = forbidden.findall(body)
    assert matches == [], (
        "Cached-mode submitCached body must not include any ground-truth "
        "field. GT must never leave the browser. "
        f"Forbidden matches: {matches!r}\nBody literal:\n{body}"
    )
