#!/usr/bin/env python3
"""
B-route frontend/backend contract validator.
Static text analysis of services/frontend/app/demo/types.ts.
Verifies DemoHealthResponse matches the BR-02 exact {"status":"ok"} payload,
forbidden diagnostics are absent from the type, and optional router-aware
view types match agent_plan.md section 2 field sets if present.
Emits OK_FRONTEND_BACKEND_CONTRACT or FRONTEND_BACKEND_DRIFT.
"""
import argparse
import datetime
import pathlib
import re
import sys


FORBIDDEN_DIAGNOSTIC_FIELDS = [
    "mode", "db_ok", "queue_depth", "version", "build", "commit", "uptime",
    "cache_stats", "worker_count", "model_name", "provider_state",
    "env_flags", "hostname",
]

ROUTER_DECISION_FIELDS = [
    "selected_backend", "router_kind", "router_version", "routing_profile",
    "allow_third_party", "third_party_provider", "cost_policy",
    "estimated_cost_usd", "predicted_confidence", "predicted_ask_repeat",
    "routing_explanation", "router_latency_ms",
]

ASSEMBLED_RESPONSE_TOP_FIELDS = [
    "transcript_text", "selected_backend", "router_kind", "router_version",
    "routing_profile", "allow_third_party", "third_party_provider",
    "estimated_cost_usd", "cost_usd", "backend_confidence", "ask_repeat",
    "latency_ms", "routing_explanation",
]

LATENCY_MS_SUBFIELDS = ["backend", "server", "end_to_end"]

FILE_LEVEL_FORBIDDEN_SUBSTRINGS = [
    "ASSEMBLYAI_API_KEY", "http://", "https://", "hostname",
    "raw_payload", "session_id_hash", "ledger_id", "key_configured",
]


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def extract_type_block(text, type_name):
    pattern = rf"export\s+type\s+{re.escape(type_name)}\s*=\s*\{{([^}}]*)\}}\s*;"
    m = re.search(pattern, text)
    return m.group(1) if m else None


def field_names_in_block(block_text):
    return set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", block_text, re.MULTILINE))


def run_checks(types_file):
    results = []

    if not types_file.exists():
        results.append(_check("types_file_present", False, f"file does not exist: {types_file}"))
        return results
    results.append(_check("types_file_present", True, str(types_file)))

    text = types_file.read_text(encoding="utf-8")

    dh_block = extract_type_block(text, "DemoHealthResponse")
    if dh_block is None:
        results.append(_check("DemoHealthResponse_block_parseable", False, "could not isolate type body"))
        return results
    results.append(_check("DemoHealthResponse_block_parseable", True, "type body isolated"))

    fields = field_names_in_block(dh_block)
    only_status = fields == {"status"}
    results.append(_check(
        "DemoHealthResponse_only_has_status_field",
        only_status,
        f"fields={sorted(fields)}",
    ))

    status_literal_ok = bool(re.search(r"\bstatus\s*:\s*\"ok\"\s*;", dh_block))
    results.append(_check(
        "DemoHealthResponse_status_value_is_ok",
        status_literal_ok,
        "status literal is \"ok\"" if status_literal_ok else "status literal not \"ok\"",
    ))

    leaked_diag = [f for f in FORBIDDEN_DIAGNOSTIC_FIELDS if f in fields]
    results.append(_check(
        "DemoHealthResponse_no_forbidden_diagnostic_fields",
        len(leaked_diag) == 0,
        f"leaked: {leaked_diag}" if leaked_diag else "no forbidden diagnostic fields in block",
    ))

    rdv_block = extract_type_block(text, "RouterDecisionView")
    if rdv_block is not None:
        rdv_fields = field_names_in_block(rdv_block)
        missing = [f for f in ROUTER_DECISION_FIELDS if f not in rdv_fields]
        results.append(_check(
            "RouterDecisionView_fields_complete",
            len(missing) == 0,
            f"missing: {missing}" if missing else f"all {len(ROUTER_DECISION_FIELDS)} fields present",
        ))
    else:
        results.append(_check("RouterDecisionView_optional", True, "not declared (additive type is optional)"))

    arv_block = extract_type_block(text, "AssembledResponseView")
    if arv_block is not None:
        arv_fields = field_names_in_block(arv_block)
        missing_top = [f for f in ASSEMBLED_RESPONSE_TOP_FIELDS if f not in arv_fields]
        results.append(_check(
            "AssembledResponseView_top_fields_complete",
            len(missing_top) == 0,
            f"missing: {missing_top}" if missing_top else f"all {len(ASSEMBLED_RESPONSE_TOP_FIELDS)} top fields present",
        ))
        lat_block = extract_type_block(text, "LatencyMs")
        if lat_block is not None:
            lat_fields = field_names_in_block(lat_block)
            missing_lat = [f for f in LATENCY_MS_SUBFIELDS if f not in lat_fields]
            results.append(_check(
                "LatencyMs_subfields_complete",
                len(missing_lat) == 0,
                f"missing: {missing_lat}" if missing_lat else f"all {len(LATENCY_MS_SUBFIELDS)} subfields present",
            ))
        else:
            results.append(_check(
                "LatencyMs_present_when_AssembledResponseView_present",
                False,
                "AssembledResponseView declared but LatencyMs is not",
            ))
    else:
        results.append(_check("AssembledResponseView_optional", True, "not declared (additive type is optional)"))

    text_no_comments = _strip_ts_comments(text)
    forbidden_hits = [s for s in FILE_LEVEL_FORBIDDEN_SUBSTRINGS if s in text_no_comments]
    results.append(_check(
        "file_omits_secrets_urls_diagnostics_outside_comments",
        len(forbidden_hits) == 0,
        f"forbidden substrings present in code: {forbidden_hits}" if forbidden_hits else "no forbidden substrings in code (comments scanned separately and ignored)",
    ))

    return results


def _strip_ts_comments(text):
    no_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    no_line = re.sub(r"//[^\n]*", "", no_block)
    return no_line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--types-file", default="services/frontend/app/demo/types.ts")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    types_file = pathlib.Path(args.types_file)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = run_checks(types_file)
    failures = [r for r in results if not r["passed"]]

    lines = [
        "# BR-04 Frontend/Backend Contract Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"types_file: {types_file}",
        f"checks: {len(results)}",
        f"failures: {len(failures)}",
        "",
        "## Check Results",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")

    if failures:
        lines += ["", "## Result: FRONTEND_BACKEND_DRIFT", "", "FRONTEND_BACKEND_DRIFT"]
        sentinel = "FRONTEND_BACKEND_DRIFT"
    else:
        lines += ["", "## Result: OK_FRONTEND_BACKEND_CONTRACT", "", f"All {len(results)} checks passed.", "", "OK_FRONTEND_BACKEND_CONTRACT"]
        sentinel = "OK_FRONTEND_BACKEND_CONTRACT"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_FRONTEND_BACKEND_CONTRACT" else 1


if __name__ == "__main__":
    sys.exit(main())
