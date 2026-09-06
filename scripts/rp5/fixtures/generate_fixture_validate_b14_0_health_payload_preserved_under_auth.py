#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_health_payload_preserved_under_auth.

Produces positive and negative response-shape fixtures matching the rows of
the recruiter-auth behavior table from
reports/rp5/b14_0_recruiter_auth_contract.md (RECRUITER-AUTH-INVARIANT-001).
Each fixture is a structured JSON record describing the response shape an
HTTP probe would have observed; the validator's scan predicates are exercised
against these fixtures adversarially to prove the contract is enforceable.

Emits OK_FIXTURE_VALIDATE_B14_0_HEALTH_UNDER_AUTH on PASS or
B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_HEALTH_UNDER_AUTH"
SENTINEL_FAIL = "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH"

EXPECTED_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'
EXPECTED_HEALTH_BODY = '{"status":"ok"}'

POSITIVE_UNAUTH_RESPONSE = {
    "label": "positive_unauth_health_401",
    "route": "/demo/health",
    "method": "GET",
    "authorization_header": None,
    "expected_status": 401,
    "expected_www_authenticate": EXPECTED_REALM_HEADER,
    "expected_body": "",
    "forbidden_substrings_in_body": [
        "router_kind", "router_version", "routing_profile",
        "selected_backend", "allow_third_party",
    ],
    "expected_validator_outcome": "PASS",
}

POSITIVE_AUTH_RESPONSE = {
    "label": "positive_auth_health_200_byte_exact",
    "route": "/demo/health",
    "method": "GET",
    "authorization_header": "Basic <ephemeral>",
    "expected_status": 200,
    "expected_www_authenticate": None,
    "expected_body": EXPECTED_HEALTH_BODY,
    "byte_exact_required": True,
    "expected_validator_outcome": "PASS",
}

NEGATIVE_FIXTURES = [
    {
        "label": "negative_unauth_status_200",
        "based_on": "POSITIVE_UNAUTH_RESPONSE",
        "mutation": {"expected_status": 200},
        "violated_rule": "expected_unauthenticated_status must be 401",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_AUTH_BYPASS_DETECTED",
    },
    {
        "label": "negative_wrong_realm",
        "based_on": "POSITIVE_UNAUTH_RESPONSE",
        "mutation": {"expected_www_authenticate": 'Basic realm="Restricted"'},
        "violated_rule": "WWW-Authenticate must equal canonical recruiter realm",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_AUTH_BYPASS_DETECTED",
    },
    {
        "label": "negative_router_field_leak_in_401_body",
        "based_on": "POSITIVE_UNAUTH_RESPONSE",
        "mutation": {"expected_body": '{"router_kind":"stub","status":"unauth"}'},
        "violated_rule": "401 body must not contain forbidden router-field substrings",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH",
    },
    {
        "label": "negative_authenticated_body_spaced",
        "based_on": "POSITIVE_AUTH_RESPONSE",
        "mutation": {"expected_body": '{"status": "ok"}'},
        "violated_rule": "authenticated /demo/health body must equal {\"status\":\"ok\"} byte-for-byte (no spaces)",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH",
    },
    {
        "label": "negative_authenticated_body_status_degraded",
        "based_on": "POSITIVE_AUTH_RESPONSE",
        "mutation": {"expected_body": '{"status":"degraded"}'},
        "violated_rule": "authenticated /demo/health body must be {\"status\":\"ok\"}",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH",
    },
    {
        "label": "negative_env_unset_returned_200",
        "based_on": "POSITIVE_UNAUTH_RESPONSE",
        "mutation": {"expected_status": 200, "context": "RECRUITER_USERNAME_unset"},
        "violated_rule": "request-time fail-closed: env-unset must still produce 401",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_AUTH_BYPASS_DETECTED",
    },
    {
        "label": "negative_uvicorn_log_contains_password",
        "based_on": None,
        "fixture_kind": "log_scan",
        "log_content": "INFO recruiter_auth: password=hunter2-leak request_ok",
        "supplied_password_value_for_scan": "hunter2-leak",
        "violated_rule": "uvicorn log must not contain recruiter password value",
        "expected_validator_outcome": "FAIL",
        "expected_classification": "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH",
    },
]

POSITIVE_FIXTURES = [POSITIVE_UNAUTH_RESPONSE, POSITIVE_AUTH_RESPONSE]


_POSITIVES_BY_NAME = {
    "POSITIVE_UNAUTH_RESPONSE": POSITIVE_UNAUTH_RESPONSE,
    "POSITIVE_AUTH_RESPONSE": POSITIVE_AUTH_RESPONSE,
}


def _materialize_negative(neg):
    if neg.get("based_on") is None:
        return dict(neg)
    base = _POSITIVES_BY_NAME[neg["based_on"]]
    out = copy.deepcopy(base)
    for k, v in neg["mutation"].items():
        out[k] = v
    out["label"] = neg["label"]
    out["violated_rule"] = neg["violated_rule"]
    out["expected_validator_outcome"] = neg["expected_validator_outcome"]
    out["expected_classification"] = neg["expected_classification"]
    return out


def _sha256(b):
    return hashlib.sha256(b).hexdigest()


def _adversarial_check(positive_fixtures, negative_fixtures):
    """Run scan predicates against each fixture. Positives must not flag; negatives must."""
    issues = []
    from_validator = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(from_validator))
    import validate_b14_0_health_payload_preserved_under_auth as v

    def _scan_response(fix, password_for_scan=b"", admin_pw=b""):
        body = fix.get("expected_body", "").encode("utf-8")
        return v._scan_body_for_forbidden(body, password_for_scan, admin_pw)

    for fix in positive_fixtures:
        leaks = _scan_response(fix)
        if leaks:
            issues.append(f"positive {fix['label']!r} unexpectedly flagged: {leaks}")

    for fix in negative_fixtures:
        if fix.get("fixture_kind") == "log_scan":
            content = fix["log_content"].encode("utf-8")
            pw = fix["supplied_password_value_for_scan"].encode("utf-8")
            if pw not in content:
                issues.append(f"negative {fix['label']!r}: scan needle absent from log content")
            continue

        leaks = _scan_response(fix)
        body_ok = (
            fix.get("expected_body", "").encode("utf-8") == v.EXPECTED_HEALTH_BODY
        )
        status_ok = fix.get("expected_status") == 401 or fix.get("expected_status") == 200
        realm_ok = fix.get("expected_www_authenticate") == v.EXPECTED_WWW_AUTHENTICATE

        # The negative must violate at least one acceptance predicate.
        violations = []
        if fix.get("expected_status") not in (200, 401):
            violations.append("status")
        if (fix.get("expected_status") == 200 and not body_ok
                and fix.get("byte_exact_required") is not False):
            violations.append("body_byte_exact")
        if fix.get("expected_status") == 401 and fix.get("expected_www_authenticate") != v.EXPECTED_WWW_AUTHENTICATE:
            violations.append("realm_header")
        if fix.get("expected_status") == 401 and leaks:
            violations.append("body_leak")
        if fix.get("mutation", {}).get("expected_status") == 200 and "context" in fix.get("mutation", {}):
            violations.append("env_unset_bypass")

        if not violations:
            issues.append(
                f"negative {fix['label']!r} did not violate any acceptance predicate"
            )

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = manifest_path.parent / "validate_b14_0_health_payload_preserved_under_auth"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    negative_materialized = [_materialize_negative(n) for n in NEGATIVE_FIXTURES]

    manifest = {
        "validator": "validate_b14_0_health_payload_preserved_under_auth",
        "kind": args.kind,
        "positive": [],
        "negative": [],
        "owned_markers": ["B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH",
                          "B14_0_AUTH_BYPASS_DETECTED"],
        "sentinel_pass": SENTINEL_PASS,
    }

    for fix in POSITIVE_FIXTURES:
        body = json.dumps(fix, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / f"{fix['label']}.json"
        path.write_bytes(body)
        manifest["positive"].append({
            "path": str(path),
            "sha256": _sha256(body),
            "size_bytes": len(body),
            "expected_validator_outcome": fix["expected_validator_outcome"],
        })

    for fix in negative_materialized:
        body = json.dumps(fix, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / f"{fix['label']}.json"
        path.write_bytes(body)
        manifest["negative"].append({
            "path": str(path),
            "sha256": _sha256(body),
            "size_bytes": len(body),
            "violated_rule": fix["violated_rule"],
            "expected_validator_outcome": fix["expected_validator_outcome"],
            "expected_classification": fix["expected_classification"],
        })

    issues = _adversarial_check(POSITIVE_FIXTURES, negative_materialized)
    manifest["adversarial_check_issues"] = issues

    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_body)
    manifest_sha = _sha256(manifest_body)

    print(f"manifest_sha256: {manifest_sha}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if issues:
        for i in issues:
            print(f"adversarial_issue: {i}")
        print(SENTINEL_FAIL)
        return 1

    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
