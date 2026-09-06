"""B11.1c frontend static guards.

Extends the B11.1b static-regex pattern (no JS test framework) to cover the
new comparison panel, the new pure-TS scoring module, and the new versions
mirror. The executable scoring self-test in test_b11_1c_scoring_executable.py
exercises the numerical correctness; this file pins privacy invariants and
visible labels.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_FRONTEND_ROOT = (
    Path(__file__).resolve().parents[2] / "services" / "frontend" / "app" / "demo"
)
_PAGE_TSX = _FRONTEND_ROOT / "page.tsx"
_SCORING_TS = _FRONTEND_ROOT / "scoring.ts"
_VERSIONS_TS = _FRONTEND_ROOT / "versions.ts"


def _read(path: Path) -> str:
    if not path.is_file():
        pytest.fail(f"Expected {path} to exist for B11.1c.")
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# B11.1b regression-safe extension: privacy line + GT leak guards
# --------------------------------------------------------------------------


_PRIVACY_LINE = (
    "Optional ground truth is used only to calculate accuracy for this session. "
    "It is not stored."
)


def test_privacy_line_still_present_verbatim() -> None:
    text = _read(_PAGE_TSX)
    assert _PRIVACY_LINE in text, (
        "B11.1c must not regress the B11.1b privacy line. The exact wording "
        "must remain verbatim in services/frontend/app/demo/page.tsx."
    )


def test_no_ground_truth_appended_to_formdata() -> None:
    text = _read(_PAGE_TSX)
    pattern = re.compile(
        r"\.append\s*\(\s*['\"](ground[_ ]?truth|gt|reference|reference_text)['\"]",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    assert matches == [], (
        "Manual ground truth must never be appended to FormData. "
        f"Matches found: {matches!r}"
    )


def test_no_console_logging_in_demo_files() -> None:
    pattern = re.compile(r"console\.(log|debug|info|warn|error)\b")
    for path in (_PAGE_TSX, _SCORING_TS, _VERSIONS_TS):
        matches = pattern.findall(_read(path))
        assert matches == [], (
            f"{path.name} must not contain console.* logging. "
            f"Matches found: {matches!r}"
        )


def test_no_ground_truth_persisted_in_browser_storage() -> None:
    text = _read(_PAGE_TSX)
    storage_pattern = re.compile(
        r"(localStorage|sessionStorage|indexedDB|document\.cookie)",
    )
    storage_lines = [line for line in text.splitlines() if storage_pattern.search(line)]
    gt_term_pattern = re.compile(r"(ground[_ ]?truth|\bgt\b|reference)", re.IGNORECASE)
    offending = [line for line in storage_lines if gt_term_pattern.search(line)]
    assert offending == [], (
        "Manual ground truth must not be written to localStorage, "
        "sessionStorage, IndexedDB, or cookies. Offending lines: "
        f"{offending!r}"
    )


def test_page_tsx_has_no_localstorage_setitem() -> None:
    """Pin: page.tsx must not write to localStorage directly. The only allowed
    localStorage write lives in services/frontend/app/demo/session.ts for the
    B10.2/B11.1a demo_session_id (B11.1b guard, regression-pinned for B11.1c).
    """

    text = _read(_PAGE_TSX)
    set_item_pattern = re.compile(r"localStorage\.setItem\s*\(\s*['\"]([^'\"]+)['\"]")
    keys = set(set_item_pattern.findall(text))
    assert keys == set(), (
        "page.tsx must not call localStorage.setItem. Keys found: "
        f"{sorted(keys)!r}"
    )


# --------------------------------------------------------------------------
# scoring.ts purity guard: no I/O, no storage, no logging
# --------------------------------------------------------------------------


def _strip_ts_comments(text: str) -> str:
    """Strip // line comments and /* ... */ block comments, leaving only code.

    The B11.1b/B11.1c scoring.ts header explicitly mentions the forbidden APIs
    (fetch, XMLHttpRequest, localStorage, ...) by name to document that they
    must not appear; running the regex over comment text would self-trip.
    """
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    return no_line


def test_scoring_ts_has_no_network_or_storage_or_logging() -> None:
    text = _strip_ts_comments(_read(_SCORING_TS))
    forbidden = [
        r"\bfetch\s*\(",
        r"\bXMLHttpRequest\b",
        r"\blocalStorage\b",
        r"\bsessionStorage\b",
        r"\bindexedDB\b",
        r"document\.cookie",
        r"navigator\.sendBeacon",
        r"console\.(log|debug|info|warn|error)\b",
    ]
    offenders: list[str] = []
    for pat in forbidden:
        if re.search(pat, text):
            offenders.append(pat)
    assert offenders == [], (
        "scoring.ts must be a pure helper — no fetch, XMLHttpRequest, "
        "browser storage, cookies, sendBeacon, or console.*. "
        f"Offending patterns: {offenders!r}"
    )


def test_scoring_ts_exports_required_symbols() -> None:
    text = _read(_SCORING_TS)
    assert re.search(r"export\s+function\s+normalizeText\b", text), (
        "scoring.ts must export `normalizeText` for the executable self-test."
    )
    assert re.search(r"export\s+function\s+computeMetrics\b", text), (
        "scoring.ts must export `computeMetrics` for the executable self-test."
    )


# --------------------------------------------------------------------------
# Forbidden fields must not be rendered (pipeline/comparison panel)
# --------------------------------------------------------------------------


_FORBIDDEN_FIELD_SUBSTRINGS = (
    "cache_key",
    "session_id_hash",
    "ledger_id",
    "key_configured",
    "audio_sha256",
    "source_report",
    "input_audio_path",
    "degraded_audio_path",
    "enhanced_audio_path",
)


def test_no_forbidden_fields_referenced_in_page_tsx() -> None:
    text = _read(_PAGE_TSX)
    offenders: list[str] = []
    for s in _FORBIDDEN_FIELD_SUBSTRINGS:
        # Use word boundaries so e.g. degraded_audio_path (singular, filesystem
        # path on the upload result_json) trips this guard while
        # degraded_audio_paths (plural, public DemoExample audio map shipped in
        # B11.1b) does not.
        if re.search(rf"\b{re.escape(s)}\b", text):
            offenders.append(s)
    assert offenders == [], (
        "page.tsx must not reference forbidden fields (B11.1a/B11.1b/B11.1c "
        "privacy discipline). Offending substrings: "
        f"{offenders!r}"
    )


# --------------------------------------------------------------------------
# Visible comparison labels and Pipeline details
# --------------------------------------------------------------------------


def test_comparison_panel_labels_present() -> None:
    text = _read(_PAGE_TSX)
    for label in ("Raw transcript", "Enhanced transcript", "Pipeline details"):
        assert label in text, (
            f"page.tsx must render the visible label {label!r} for the "
            "B11.1c comparison panel."
        )


def test_metric_labels_present_when_reference_available() -> None:
    text = _read(_PAGE_TSX)
    assert "Word Accuracy" in text, "page.tsx must render the 'Word Accuracy' label."
    assert "WER" in text, "page.tsx must render the 'WER' label."


def test_compute_metrics_imported_from_scoring() -> None:
    text = _read(_PAGE_TSX)
    assert re.search(
        r'import\s*\{[^}]*\bcomputeMetrics\b[^}]*\}\s*from\s*["\']\./scoring["\']',
        text,
    ), "page.tsx must import computeMetrics from ./scoring."


def test_pipeline_details_uses_collapsed_details_element() -> None:
    text = _read(_PAGE_TSX)
    assert "<details" in text and "<summary>" in text, (
        "Pipeline details must use a native <details>/<summary> element so "
        "it collapses by default on mobile (plan §B11.1c decision rule 4)."
    )


def test_pipeline_field_keys_rendered() -> None:
    text = _read(_PAGE_TSX)
    for key in (
        "provider",
        "asr_model_version",
        "enhancer_version",
        "degradation_id",
        "degradation_version",
        "metrics_version",
        "latency_seconds",
        "cache status",
    ):
        assert key in text, (
            f"page.tsx must render the pipeline field {key!r} in the "
            "B11.1c Pipeline details block."
        )


# --------------------------------------------------------------------------
# Bypass detection uses the literal string, not DEFAULT_ENHANCER_VERSION
# --------------------------------------------------------------------------


def test_bypass_detected_by_literal_string_only() -> None:
    text = _read(_PAGE_TSX)
    # Must contain the literal-string bypass check.
    assert re.search(r'enhancer_?[Vv]ersion\s*===\s*"bypass"', text), (
        "page.tsx must detect the bypass enhancer with the literal string "
        "comparison `enhancer_version === \"bypass\"` (or its camelCase "
        "equivalent inside the panel). DEFAULT_ENHANCER_VERSION is not a "
        "synonym for bypass."
    )
    # Must NOT use DEFAULT_ENHANCER_VERSION as a synonym for bypass.
    assert not re.search(
        r"DEFAULT_ENHANCER_VERSION\s*[!=]==\s*['\"]bypass['\"]", text
    ), "Do not compare DEFAULT_ENHANCER_VERSION to 'bypass'."
    assert not re.search(
        r"=== \s*DEFAULT_ENHANCER_VERSION", text
    ), "Do not use DEFAULT_ENHANCER_VERSION as a bypass marker."


def test_bypass_note_text_is_visible() -> None:
    text = _read(_PAGE_TSX)
    assert "Enhancer is bypass" in text, (
        "page.tsx must render the honest bypass note when "
        'enhancer_version === "bypass" (plan §B11.1c decision rule 1).'
    )
