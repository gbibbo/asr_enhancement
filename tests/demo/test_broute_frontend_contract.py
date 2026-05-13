"""BR-04 frontend/backend contract static checks.

Mirrors the BR-02 public health payload and BR-01/BR-03 router-aware response
fields against services/frontend/app/demo/types.ts. Uses Python regex/text
scanning (same approach as test_b11_1b/c_*) — no Node toolchain is required
on RP5.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TYPES_FILE = _REPO_ROOT / "services/frontend/app/demo/types.ts"


_FORBIDDEN_DIAGNOSTIC_FIELDS = [
    "mode", "db_ok", "queue_depth", "version", "build", "commit", "uptime",
    "cache_stats", "worker_count", "model_name", "provider_state",
    "env_flags", "hostname",
]

_ROUTER_DECISION_FIELDS = [
    "selected_backend", "router_kind", "router_version", "routing_profile",
    "allow_third_party", "third_party_provider", "cost_policy",
    "estimated_cost_usd", "predicted_confidence", "predicted_ask_repeat",
    "routing_explanation", "router_latency_ms",
]

_ASSEMBLED_RESPONSE_TOP_FIELDS = [
    "transcript_text", "selected_backend", "router_kind", "router_version",
    "routing_profile", "allow_third_party", "third_party_provider",
    "estimated_cost_usd", "cost_usd", "backend_confidence", "ask_repeat",
    "latency_ms", "routing_explanation",
]

_LATENCY_MS_SUBFIELDS = ["backend", "server", "end_to_end"]

_FILE_LEVEL_FORBIDDEN_SUBSTRINGS = [
    "ASSEMBLYAI_API_KEY", "http://", "https://", "hostname",
    "raw_payload", "session_id_hash", "ledger_id", "key_configured",
]


def _types_text() -> str:
    return _TYPES_FILE.read_text(encoding="utf-8")


def _extract_block(text: str, type_name: str) -> str | None:
    pattern = rf"export\s+type\s+{re.escape(type_name)}\s*=\s*\{{([^}}]*)\}}\s*;"
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _field_names(block: str) -> set[str]:
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", block, re.MULTILINE))


def _strip_ts_comments(text: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    return no_line


def test_demo_health_response_is_status_only():
    block = _extract_block(_types_text(), "DemoHealthResponse")
    assert block is not None, "DemoHealthResponse block not found"
    fields = _field_names(block)
    assert fields == {"status"}, f"unexpected fields: {sorted(fields)}"
    assert re.search(r'\bstatus\s*:\s*"ok"\s*;', block), "status literal is not \"ok\""


def test_demo_health_response_omits_forbidden_diagnostic_fields():
    block = _extract_block(_types_text(), "DemoHealthResponse")
    assert block is not None
    fields = _field_names(block)
    leaked = [f for f in _FORBIDDEN_DIAGNOSTIC_FIELDS if f in fields]
    assert leaked == [], f"leaked diagnostic fields in DemoHealthResponse: {leaked}"


def test_router_decision_view_fields_complete():
    text = _types_text()
    block = _extract_block(text, "RouterDecisionView")
    if block is None:
        pytest.skip("RouterDecisionView is optional and not declared")
    fields = _field_names(block)
    missing = [f for f in _ROUTER_DECISION_FIELDS if f not in fields]
    assert missing == [], f"RouterDecisionView missing fields: {missing}"


def test_assembled_response_view_fields_complete():
    text = _types_text()
    block = _extract_block(text, "AssembledResponseView")
    if block is None:
        pytest.skip("AssembledResponseView is optional and not declared")
    fields = _field_names(block)
    missing_top = [f for f in _ASSEMBLED_RESPONSE_TOP_FIELDS if f not in fields]
    assert missing_top == [], f"AssembledResponseView missing top fields: {missing_top}"
    lat_block = _extract_block(text, "LatencyMs")
    assert lat_block is not None, "LatencyMs must be declared when AssembledResponseView is declared"
    lat_fields = _field_names(lat_block)
    missing_lat = [f for f in _LATENCY_MS_SUBFIELDS if f not in lat_fields]
    assert missing_lat == [], f"LatencyMs missing subfields: {missing_lat}"


def test_types_file_omits_secrets_urls_diagnostics():
    text = _strip_ts_comments(_types_text())
    hits = [s for s in _FILE_LEVEL_FORBIDDEN_SUBSTRINGS if s in text]
    assert hits == [], f"forbidden substrings present in types.ts code (comments excluded): {hits}"
