#!/usr/bin/env python3
"""
Fixture generator paired with
validate_b14_1_recruiter_gate_preserved_under_public_exposure.

Produces declarative response-shape fixtures asserting the contract:
under PUBLIC_DEMO_EXPOSURE=true, the recruiter HTTPBasic gate remains
preserved end-to-end.

Three probe categories:
  * unauth_demo: unauthenticated GET on a recruiter-protected /demo/*
    route MUST yield 401 + Basic realm="asr-demo-recruiter".
  * auth_demo_health: authenticated GET /demo/health MUST yield 200.
  * recruiter_into_admin: GET /admin/health with recruiter credentials
    MUST NOT yield 200 (admin/recruiter separation preserved).

Each fixture is a JSON descriptor of an observed HTTP response. The
generator adversarially asserts the validator's acceptance predicate
against positives and negatives.

Emits OK_FIXTURE_VALIDATE_B14_1_RECRUITER_GATE_PRESERVED on PASS or
B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_RECRUITER_GATE_PRESERVED"
SENTINEL_FAIL = "B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

EXPECTED_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'

POSITIVE_UNAUTH_DEMO = {
    "label": "positive_unauth_demo_health_401",
    "kind": "unauth_demo",
    "route": "/demo/health",
    "method": "GET",
    "authorization_header": None,
    "observed_status": 401,
    "observed_www_authenticate": EXPECTED_REALM_HEADER,
    "expected_validator_outcome": "PASS",
}

NEGATIVE_FIXTURES = [
    {
        "label": "negative_unauth_demo_health_200",
        "based_on": "POSITIVE_UNAUTH_DEMO",
        "mutation": {
            "kind": "unauth_demo",
            "observed_status": 200,
            "observed_www_authenticate": None,
        },
        "violated_rule": "unauthenticated /demo/* must return 401 with canonical realm",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
    {
        "label": "negative_recruiter_into_admin_health_200",
        "based_on": "POSITIVE_UNAUTH_DEMO",
        "mutation": {
            "kind": "recruiter_into_admin",
            "route": "/admin/health",
            "authorization_header": "Basic <recruiter-ephemeral>",
            "observed_status": 200,
            "observed_www_authenticate": None,
        },
        "violated_rule": "recruiter credentials must NOT authorize /admin/* (separation)",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
]

POSITIVE_FIXTURES = [POSITIVE_UNAUTH_DEMO]

_POSITIVES_BY_NAME = {"POSITIVE_UNAUTH_DEMO": POSITIVE_UNAUTH_DEMO}


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
    kind = fix.get("kind")
    if kind == "unauth_demo":
        return (fix.get("observed_status") == 401
                and fix.get("observed_www_authenticate") == EXPECTED_REALM_HEADER)
    if kind == "auth_demo_health":
        return fix.get("observed_status") == 200
    if kind == "recruiter_into_admin":
        return fix.get("observed_status") != 200
    return False


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
                    / "generate_fixture_validate_b14_1_recruiter_gate_preserved_under_public_exposure")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    positives = POSITIVE_FIXTURES
    negatives = [_materialize_negative(n) for n in NEGATIVE_FIXTURES]

    adversarial_issues = _adversarial_check(positives, negatives)

    manifest = {
        "validator": "validate_b14_1_recruiter_gate_preserved_under_public_exposure",
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
            "kind": fix.get("kind"),
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
            "kind": fix.get("kind"),
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
