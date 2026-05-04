"""B11.1b privacy guard for the /demo client component.

The B11.1b additions introduce two privacy-sensitive surfaces in the
frontend:

1. an optional manual ground-truth textarea for uploads, whose content must
   never leave the browser (no FormData append, no localStorage /
   sessionStorage / IndexedDB / cookie write, no log line);
2. an object-URL-backed <audio> player for the user's own upload, which must
   be created and revoked through the document API rather than leaked.

We avoid pulling in a JS test framework on RP5 (no host Node) — the same
approach as the B11.1a degradation-id drift guard. Static regex checks over
services/frontend/app/demo/page.tsx surface regressions in CI without adding
toolchain weight.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


PRIVACY_LINE = (
    "Optional ground truth is used only to calculate accuracy for this session. "
    "It is not stored."
)


def _page_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "services"
        / "frontend"
        / "app"
        / "demo"
        / "page.tsx"
    )


def _read_page() -> str:
    p = _page_path()
    if not p.exists():
        pytest.fail(f"Expected /demo page at {p}, but file is missing.")
    return p.read_text(encoding="utf-8")


def test_privacy_line_present_verbatim() -> None:
    text = _read_page()
    assert PRIVACY_LINE in text, (
        "B11.1b requires the exact privacy line to be present verbatim in "
        "services/frontend/app/demo/page.tsx."
    )


def test_no_ground_truth_appended_to_formdata() -> None:
    text = _read_page()
    pattern = re.compile(
        r"\.append\s*\(\s*['\"](ground[_ ]?truth|gt|reference|reference_text)['\"]",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    assert matches == [], (
        "Manual ground truth must never be appended to FormData. "
        f"Matches found: {matches!r}"
    )


def test_no_console_logging_in_demo_page() -> None:
    text = _read_page()
    pattern = re.compile(r"console\.(log|debug|info|warn|error)\b")
    matches = pattern.findall(text)
    assert matches == [], (
        "services/frontend/app/demo/page.tsx must not contain console.* "
        f"logging. Matches found: {matches!r}"
    )


def test_object_url_lifecycle_apis_are_present() -> None:
    text = _read_page()
    assert "URL.createObjectURL" in text, (
        "Upload preview must use URL.createObjectURL(uploadFile) per B11.1b."
    )
    assert "URL.revokeObjectURL" in text, (
        "Object URL must be revoked on file change / unmount / explicit reset "
        "to avoid leaks. Note: revocation must NOT happen on submit success "
        "or job completion — playback must remain available after submit."
    )


def test_no_ground_truth_persisted_in_browser_storage() -> None:
    text = _read_page()
    storage_pattern = re.compile(
        r"(localStorage|sessionStorage|indexedDB|document\.cookie)",
    )
    storage_lines = [
        line for line in text.splitlines() if storage_pattern.search(line)
    ]
    gt_term_pattern = re.compile(r"(ground[_ ]?truth|\bgt\b|reference)", re.IGNORECASE)
    offending = [line for line in storage_lines if gt_term_pattern.search(line)]
    assert offending == [], (
        "Manual ground truth must not be written to localStorage, "
        "sessionStorage, IndexedDB, or cookies. Offending lines: "
        f"{offending!r}"
    )


def test_session_storage_use_is_limited_to_demo_session_id() -> None:
    """Sanity: any localStorage write in this file must only target the
    pre-existing demo_session_id key (B10.2 / B11.1a). New B11.1b code must
    not introduce any other localStorage write key.
    """

    text = _read_page()
    set_item_pattern = re.compile(r"localStorage\.setItem\s*\(\s*['\"]([^'\"]+)['\"]")
    keys = set(set_item_pattern.findall(text))
    # page.tsx should not call setItem at all today (B10.2 puts the only
    # localStorage write in services/frontend/app/demo/session.ts). We pin
    # that here so a new write surface in page.tsx is caught immediately.
    assert keys == set(), (
        "services/frontend/app/demo/page.tsx must not write to localStorage "
        f"directly. Keys found: {sorted(keys)!r}"
    )
