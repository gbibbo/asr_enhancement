#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_1_application_layer_gate_invariants.

Produces positive and negative declarative response-shape fixtures matching
the application_layer_gate_invariant_record contract pinned by
docs/plans/b14_1/state_packet_schemas.yaml section 144:
  * required_status_when_unauthenticated: 401
  * required_www_authenticate_value: 'Basic realm="asr-demo-recruiter"'
  * required_authenticated_health_payload: '{"status":"ok"}'

Each fixture is a JSON descriptor of an observed HTTP response. The generator
adversarially asserts the validator's acceptance predicate against the
positive and negative fixtures: positives must satisfy the predicate, every
negative must violate exactly the rule named in its `violated_rule` field.

Emits OK_FIXTURE_VALIDATE_B14_1_APPLICATION_LAYER_GATE on PASS or
B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_APPLICATION_LAYER_GATE"
SENTINEL_FAIL = "B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED"

EXPECTED_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'
EXPECTED_HEALTH_BODY = '{"status":"ok"}'

POSITIVE_UNAUTH = {
    "label": "positive_unauth_demo_health_401",
    "route": "/demo/health",
    "method": "GET",
    "authorization_header": None,
    "observed_status": 401,
    "observed_www_authenticate": EXPECTED_REALM_HEADER,
    "observed_body_bytes": "",
    "expected_validator_outcome": "PASS",
}

POSITIVE_AUTH = {
    "label": "positive_auth_demo_health_200_byte_exact",
    "route": "/demo/health",
    "method": "GET",
    "authorization_header": "Basic <ephemeral>",
    "observed_status": 200,
    "observed_www_authenticate": None,
    "observed_body_bytes": EXPECTED_HEALTH_BODY,
    "expected_validator_outcome": "PASS",
}

NEGATIVE_FIXTURES = [
    {
        "label": "negative_unauth_demo_health_200",
        "based_on": "POSITIVE_UNAUTH",
        "mutation": {"observed_status": 200},
        "violated_rule": "required_status_when_unauthenticated must be 401",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
    {
        "label": "negative_unauth_demo_health_wrong_realm",
        "based_on": "POSITIVE_UNAUTH",
        "mutation": {"observed_www_authenticate": 'Basic realm="Restricted"'},
        "violated_rule": "required_www_authenticate_value must equal canonical recruiter realm",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
    {
        "label": "negative_auth_demo_health_body_degraded",
        "based_on": "POSITIVE_AUTH",
        "mutation": {"observed_body_bytes": '{"status":"degraded"}'},
        "violated_rule": "required_authenticated_health_payload must be {\"status\":\"ok\"}",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
]

POSITIVE_FIXTURES = [POSITIVE_UNAUTH, POSITIVE_AUTH]

_POSITIVES_BY_NAME = {
    "POSITIVE_UNAUTH": POSITIVE_UNAUTH,
    "POSITIVE_AUTH": POSITIVE_AUTH,
}


def _materialize_negative(neg):
    base = _POSITIVES_BY_NAME[neg["based_on"]]
    out = copy.deepcopy(base)
    for k, v in neg["mutation"].items():
        out[k] = v
    out["label"] = neg["label"]
    out["violated_rule"] = neg["violated_rule"]
    out["expected_validator_outcome"] = neg["expected_validator_outcome"]
    out["expected_classification"] = neg["expected_classification"]
    return out


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _fixture_satisfies_contract(fix: dict) -> bool:
    """Apply the validator's acceptance predicate to a fixture descriptor.

    A fixture satisfies the contract iff it represents a valid positive
    outcome under one of the two probe categories.
    """
    if fix.get("authorization_header") is None:
        return (fix.get("observed_status") == 401
                and fix.get("observed_www_authenticate") == EXPECTED_REALM_HEADER)
    return (fix.get("observed_status") == 200
            and fix.get("observed_body_bytes") == EXPECTED_HEALTH_BODY)


def _adversarial_check(positives, negatives):
    issues = []
    for fix in positives:
        if not _fixture_satisfies_contract(fix):
            issues.append(f"positive {fix['label']!r} did not satisfy contract")
    for fix in negatives:
        if _fixture_satisfies_contract(fix):
            issues.append(f"negative {fix['label']!r} unexpectedly satisfies contract")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = (manifest_path.parent
                    / "generate_fixture_validate_b14_1_application_layer_gate_invariants")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    positives = POSITIVE_FIXTURES
    negatives = [_materialize_negative(n) for n in NEGATIVE_FIXTURES]

    adversarial_issues = _adversarial_check(positives, negatives)

    manifest = {
        "validator": "validate_b14_1_application_layer_gate_invariants",
        "kind": args.kind,
        "owned_marker": SENTINEL_FAIL,
        "sentinel_pass": SENTINEL_PASS,
        "positive": [],
        "negative": [],
    }

    for fix in positives:
        body = json.dumps(fix, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / f"{fix['label']}.json"
        path.write_bytes(body)
        manifest["positive"].append({
            "path": str(path.relative_to(manifest_path.parent)),
            "sha256": _sha256(body),
            "size_bytes": len(body),
            "expected_validator_outcome": fix["expected_validator_outcome"],
        })

    for fix in negatives:
        body = json.dumps(fix, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / f"{fix['label']}.json"
        path.write_bytes(body)
        manifest["negative"].append({
            "path": str(path.relative_to(manifest_path.parent)),
            "sha256": _sha256(body),
            "size_bytes": len(body),
            "expected_validator_outcome": fix["expected_validator_outcome"],
            "expected_classification": fix["expected_classification"],
        })

    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(body)
    print(f"manifest_sha256: {_sha256(body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_issues:
        for i in adversarial_issues:
            print(f"adversarial_issue: {i}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
