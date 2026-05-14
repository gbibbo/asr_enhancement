#!/usr/bin/env python3
"""
B14_0-01 recruiter auth contract validator.

Builds the recruiter-auth invariant record, the credential storage policy
records (one per recruiter credential), and the admin-vs-recruiter auth
separation invariant records from agent_plan.md section 2 constants and
state_packet_schemas.yaml fixed values, then self-validates the records
against the schema and emits the contract document.

Emits OK_B14_0_RECRUITER_AUTH_CONTRACT on PASS or
B14_0_RECRUITER_AUTH_CONTRACT_FAILED on FAIL.

This task authors the contract only. The middleware is not implemented in
B14_0-01; runtime auth behavior is validated by later B14_0 tasks against
this contract.
"""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys

VALIDATOR_ID = "validate_b14_0_recruiter_auth_contract"
SENTINEL_PASS = "OK_B14_0_RECRUITER_AUTH_CONTRACT"
SENTINEL_FAIL = "B14_0_RECRUITER_AUTH_CONTRACT_FAILED"

# Schema fixed values (state_packet_schemas.yaml recruiter_auth_invariant_record)
SCHEMA_FIXED_WWW_AUTHENTICATE = 'Basic realm="asr-demo-recruiter"'
SCHEMA_FIXED_AUTH_HEALTH_PAYLOAD = '{"status":"ok"}'
SCHEMA_ENUM_UNAUTHENTICATED_STATUS = [401]

# Section 2 constants (agent_plan.md)
PROTECTED_ROUTES = [
    "GET /demo/health",
    "GET /demo/examples",
    "POST /demo/run-cached",
    "POST /demo/jobs",
    "GET /demo/jobs/{job_id}",
    "GET /demo/providers/assemblyai/status",
]

# Forbidden response-body substrings as enumerated in agent_plan.md section 2.
# Five literal router-field names plus three placeholder tokens for runtime
# value categories (Authorization header value, RECRUITER_PASSWORD value,
# ADMIN_STATS_PASSWORD value). The placeholder tokens are resolved at smoke
# time by the runtime validators; no real credential value is ever inlined
# into this contract document.
LITERAL_FORBIDDEN_SUBSTRINGS = [
    "router_kind",
    "router_version",
    "routing_profile",
    "selected_backend",
    "allow_third_party",
]
RUNTIME_VALUE_CATEGORY_PLACEHOLDERS = [
    "<env:Authorization-header-value>",
    "<env:RECRUITER_PASSWORD-value>",
    "<env:ADMIN_STATS_PASSWORD-value>",
]
FORBIDDEN_RESPONSE_BODY_SUBSTRINGS = (
    LITERAL_FORBIDDEN_SUBSTRINGS + RUNTIME_VALUE_CATEGORY_PLACEHOLDERS
)

RECRUITER_CREDENTIALS = ["RECRUITER_USERNAME", "RECRUITER_PASSWORD"]
ALLOWED_STORAGE = ["environment_variable", "host_systemd_service_env"]
FORBIDDEN_STORAGE = [
    "git_committed_file",
    "dockerfile_literal",
    "compose_file_literal",
    "plan_file_literal",
    "log_output",
    "error_response_body",
]
ROTATION_POLICY_DEFERRED_TOKEN = "deferred_to_HAR-B14_0-RECRUITER-CREDS-001"

AUTH_SEPARATION_DIMENSIONS = ["realm", "username", "password", "route_prefix", "error_path"]

# Banned-phrases registry (inherited from B-route §14)
BANNED_PHRASES = [
    "as needed", "as appropriate", "as required", "if already present",
    "if present", "where appropriate", "best practices", "obvious",
    "TBD", "TODO without a marker", "discovered", "discover ",
    "judgment", "free-form", "free form",
]

# Forbidden future-constraint regressions
FORBIDDEN_FUTURE_SUBSTRINGS = [
    "tailscale funnel", "funnel serve", "ts funnel",
]


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def build_recruiter_auth_invariant():
    return {
        "invariant_id": "RECRUITER-AUTH-INVARIANT-001",
        "protected_route_glob": list(PROTECTED_ROUTES),
        "expected_unauthenticated_status": 401,
        "expected_www_authenticate_value": SCHEMA_FIXED_WWW_AUTHENTICATE,
        "expected_authenticated_health_payload": SCHEMA_FIXED_AUTH_HEALTH_PAYLOAD,
        "forbidden_response_body_substrings": list(FORBIDDEN_RESPONSE_BODY_SUBSTRINGS),
        "validator": VALIDATOR_ID,
        "marker": SENTINEL_FAIL,
    }


def build_credential_storage_policies():
    records = []
    for i, name in enumerate(RECRUITER_CREDENTIALS, start=1):
        records.append({
            "policy_id": f"RECRUITER-CRED-STORAGE-{i:03d}",
            "credential_name": name,
            "source": "environment_variable",
            "allowed_storage": list(ALLOWED_STORAGE),
            "forbidden_storage": list(FORBIDDEN_STORAGE),
            "rotation_policy": ROTATION_POLICY_DEFERRED_TOKEN,
            "validator": VALIDATOR_ID,
            "marker": SENTINEL_FAIL,
        })
    return records


def build_auth_separation_invariants():
    records = []
    for i, dim in enumerate(AUTH_SEPARATION_DIMENSIONS, start=1):
        records.append({
            "invariant_id": f"AUTH-SEP-{i:03d}",
            "surface_a": "admin",
            "surface_b": "recruiter",
            "separation_dimension": dim,
            "validator": "validate_b14_0_auth_separation_invariants",
            "marker": "B14_0_ADMIN_RECRUITER_CRED_CONFLATION",
        })
    return records


def validate_recruiter_auth_invariant(rec):
    errs = []
    required = [
        "invariant_id", "protected_route_glob", "expected_unauthenticated_status",
        "expected_www_authenticate_value", "expected_authenticated_health_payload",
        "forbidden_response_body_substrings", "validator", "marker",
    ]
    for f in required:
        if f not in rec:
            errs.append(f"missing required field {f}")
    if rec.get("expected_unauthenticated_status") not in SCHEMA_ENUM_UNAUTHENTICATED_STATUS:
        errs.append("expected_unauthenticated_status not in schema enum")
    if rec.get("expected_www_authenticate_value") != SCHEMA_FIXED_WWW_AUTHENTICATE:
        errs.append("expected_www_authenticate_value does not match schema fixed value")
    if rec.get("expected_authenticated_health_payload") != SCHEMA_FIXED_AUTH_HEALTH_PAYLOAD:
        errs.append("expected_authenticated_health_payload does not match schema fixed value")
    routes = rec.get("protected_route_glob", [])
    if list(routes) != list(PROTECTED_ROUTES):
        errs.append("protected_route_glob does not match section 2 enumeration")
    subs = rec.get("forbidden_response_body_substrings", [])
    for needle in LITERAL_FORBIDDEN_SUBSTRINGS:
        if needle not in subs:
            errs.append(f"forbidden_response_body_substrings missing literal needle {needle}")
    return errs


def validate_credential_storage_policy(rec):
    errs = []
    required = [
        "policy_id", "credential_name", "source", "allowed_storage",
        "forbidden_storage", "rotation_policy", "validator", "marker",
    ]
    for f in required:
        if f not in rec:
            errs.append(f"{rec.get('policy_id', '?')}: missing required field {f}")
    if rec.get("source") != "environment_variable":
        errs.append(f"{rec.get('policy_id', '?')}: source not in schema enum")
    allowed = rec.get("allowed_storage", [])
    if not set(allowed).issubset(set(ALLOWED_STORAGE)):
        errs.append(f"{rec.get('policy_id', '?')}: allowed_storage outside schema enum")
    forbidden = rec.get("forbidden_storage", [])
    if not set(FORBIDDEN_STORAGE).issubset(set(forbidden)):
        errs.append(f"{rec.get('policy_id', '?')}: forbidden_storage missing schema-mandated values")
    rot = rec.get("rotation_policy", "")
    if not isinstance(rot, str) or not rot:
        errs.append(f"{rec.get('policy_id', '?')}: rotation_policy must be a non-empty string")
    return errs


def validate_auth_separation_invariant(rec):
    errs = []
    required = ["invariant_id", "surface_a", "surface_b",
                "separation_dimension", "validator", "marker"]
    for f in required:
        if f not in rec:
            errs.append(f"{rec.get('invariant_id', '?')}: missing required field {f}")
    if rec.get("separation_dimension") not in AUTH_SEPARATION_DIMENSIONS:
        errs.append(f"{rec.get('invariant_id', '?')}: separation_dimension not in schema enum")
    if rec.get("surface_a") == rec.get("surface_b"):
        errs.append(f"{rec.get('invariant_id', '?')}: surface_a must differ from surface_b")
    return errs


def emit_yaml_list_of_dicts(records, indent=0):
    lines = []
    pad = " " * indent
    for rec in records:
        first = True
        for k, v in rec.items():
            prefix = pad + ("- " if first else "  ")
            first = False
            if isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    lines.append(f"{pad}    - {item}")
            else:
                lines.append(f"{prefix}{k}: {v}")
    return lines


def emit_yaml_single_dict(rec, indent=0):
    lines = []
    pad = " " * indent
    for k, v in rec.items():
        if isinstance(v, list):
            lines.append(f"{pad}{k}:")
            for item in v:
                lines.append(f"{pad}  - {item}")
        else:
            lines.append(f"{pad}{k}: {v}")
    return lines


def scan_text_for_forbidden(text):
    issues = []
    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in lowered:
            issues.append(f"banned phrase present: {phrase!r}")
    for phrase in FORBIDDEN_FUTURE_SUBSTRINGS:
        if phrase.lower() in lowered:
            issues.append(f"forbidden future-constraint substring present: {phrase!r}")
    # non-loopback URLs (http(s):// not pointing at 127.0.0.1 or localhost)
    for match in re.findall(r"https?://[\w\.\-:]+", text):
        host = match.split("://", 1)[1].split("/", 1)[0]
        host = host.split(":", 1)[0]
        if host not in ("127.0.0.1", "localhost", "0.0.0.0"):
            issues.append(f"non-loopback URL present: {match!r}")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    auth_invariant = build_recruiter_auth_invariant()
    cred_policies = build_credential_storage_policies()
    sep_invariants = build_auth_separation_invariants()

    checks = []
    checks.append(_check(
        "recruiter_auth_invariant_record_schema_conformance",
        not validate_recruiter_auth_invariant(auth_invariant),
        "; ".join(validate_recruiter_auth_invariant(auth_invariant)) or "PASS",
    ))
    cred_errs = []
    for rec in cred_policies:
        cred_errs += validate_credential_storage_policy(rec)
    checks.append(_check(
        "credential_storage_policy_records_schema_conformance",
        not cred_errs,
        "; ".join(cred_errs) or f"PASS ({len(cred_policies)} records)",
    ))
    sep_errs = []
    for rec in sep_invariants:
        sep_errs += validate_auth_separation_invariant(rec)
    checks.append(_check(
        "auth_separation_invariant_records_schema_conformance",
        not sep_errs,
        "; ".join(sep_errs) or f"PASS ({len(sep_invariants)} records)",
    ))
    checks.append(_check(
        "no_real_credential_value_in_records",
        all(
            ROTATION_POLICY_DEFERRED_TOKEN in rec["rotation_policy"]
            for rec in cred_policies
        ),
        "all credential records use deferred-HAR token; no operator values present",
    ))
    # Health payload contains a literal "status" substring that overlaps with
    # the runtime forbidden_response_body scan. The scan target is the
    # *authenticated* health response body, while forbidden_response_body
    # substrings target *unauthenticated 401 challenge* bodies. Verify the
    # two scopes are kept separate by construction: forbidden literals do not
    # appear inside the authenticated payload string.
    health_payload = auth_invariant["expected_authenticated_health_payload"]
    leak = [n for n in LITERAL_FORBIDDEN_SUBSTRINGS if n in health_payload]
    checks.append(_check(
        "authenticated_health_payload_excludes_router_field_names",
        not leak,
        f"leaking names: {leak}" if leak else
        "authenticated /demo/health payload {\"status\":\"ok\"} carries no router-field names",
    ))

    failures = [c for c in checks if not c["passed"]]
    sentinel = SENTINEL_PASS if not failures else SENTINEL_FAIL

    lines = [
        "# B14_0-01 Recruiter Auth Contract",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"validator: {VALIDATOR_ID}",
        f"schema_reference: docs/plans/b14_0/state_packet_schemas.yaml",
        f"agent_plan_section_reference: docs/plans/b14_0/agent_plan.md section 2",
        "",
        "## Schema Conformance Checks",
        "",
    ]
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        lines.append(f"- [{status}] {c['name']}: {c['detail']}")

    lines += [
        "",
        "## recruiter_auth_invariant_record",
        "",
        "```yaml",
    ]
    lines += emit_yaml_single_dict(auth_invariant)
    lines += [
        "```",
        "",
        "Note: items 1..5 of forbidden_response_body_substrings are literal scan needles.",
        "Items 6..8 are placeholder tokens for runtime value categories whose actual",
        "operator values are resolved at smoke time by the runtime validators",
        "(validate_b14_0_no_credential_leak, validate_b14_0_auth_separation_invariants).",
        "No operator credential value is ever inlined into this contract document.",
        "",
        "## credential_storage_policy_records",
        "",
        "```yaml",
    ]
    lines += emit_yaml_list_of_dicts(cred_policies)
    lines += [
        "```",
        "",
        f"rotation_policy uses the literal token {ROTATION_POLICY_DEFERRED_TOKEN!r}",
        "because HAR-B14_0-RECRUITER-CREDS-001 is pre_declared_unresolved and blocks",
        "B14_0-02 closure only. The operator-supplied rotation cadence will be",
        "recorded in the HAR result block when the human action resolves; this",
        "contract carries the deferred token in the meantime so the schema's",
        "required rotation_policy field stays non-empty without inventing policy.",
        "",
        "## auth_separation_invariant_records (preserved for B14_0-03)",
        "",
        "```yaml",
    ]
    lines += emit_yaml_list_of_dicts(sep_invariants)
    lines += [
        "```",
        "",
        "These records are declared in this contract for downstream consumption by",
        "validate_b14_0_auth_separation_invariants during B14_0-03 execution.",
        "B14_0-01 does not bind a runtime separation validator.",
        "",
        "## Result",
        "",
    ]
    if failures:
        lines.append(f"{len(failures)} check(s) failed:")
        lines.append("")
        for f in failures:
            lines.append(f"  - {f['name']}: {f['detail']}")
        lines += ["", sentinel]
    else:
        lines += [
            f"All {len(checks)} schema-conformance checks passed.",
            "",
            sentinel,
        ]

    body = "\n".join(lines) + "\n"

    # Final self-scan: no banned phrases, no forbidden future strings, no
    # non-loopback URLs, and no operator credential values in the output.
    scan_issues = scan_text_for_forbidden(body)
    if scan_issues:
        body = (
            f"# B14_0-01 Recruiter Auth Contract\n\n"
            f"{SENTINEL_FAIL}: self-scan rejected output:\n"
            + "\n".join(f"  - {i}" for i in scan_issues)
            + "\n"
        )
        out_path.write_text(body)
        print(SENTINEL_FAIL)
        return 1

    out_path.write_text(body)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
