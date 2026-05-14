#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_1_openapi_docs_visibility.

Produces declarative response-shape fixtures for the openapi_docs_visibility
contract under PUBLIC_DEMO_EXPOSURE=true:

  * /openapi.json must NOT be mounted_unprotected.
  * /docs       must NOT be mounted_unprotected.
  * /redoc      must NOT be mounted_unprotected.

Acceptance maps observed status -> route_state classification:
  * 404 -> unmounted (PASS)
  * 401 with non-recruiter realm -> mounted_admin_only (PASS)
  * 401 with recruiter realm -> mounted_unprotected (FAIL: docs surface
    behind recruiter realm is still a leak under the default plan)
  * 200 -> mounted_unprotected (FAIL)

Each fixture is a JSON descriptor of an observed unauthenticated probe.
Adversarial self-check verifies positives classify to a PASS state and
negatives classify to mounted_unprotected.

Emits OK_FIXTURE_VALIDATE_B14_1_OPENAPI_DOCS on PASS or
B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_OPENAPI_DOCS"
SENTINEL_FAIL = "B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED"

RECRUITER_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'
ADMIN_LIKE_REALM_HEADER = 'Basic realm="asr-demo-admin"'

POSITIVE_OPENAPI_UNMOUNTED = {
    "label": "positive_openapi_json_unmounted_404",
    "route": "/openapi.json",
    "method": "GET",
    "observed_status": 404,
    "observed_www_authenticate": None,
    "observed_body_snippet": "",
    "expected_route_state": "unmounted",
    "expected_validator_outcome": "PASS",
}

NEGATIVE_FIXTURES = [
    {
        "label": "negative_openapi_json_mounted_unprotected_200",
        "based_on": "POSITIVE_OPENAPI_UNMOUNTED",
        "mutation": {
            "observed_status": 200,
            "observed_body_snippet": '{"openapi": "3.1.0", "info": {}}',
            "expected_route_state": "mounted_unprotected",
        },
        "violated_rule": "openapi route mounted unprotected under public exposure",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
    {
        "label": "negative_openapi_behind_recruiter_realm",
        "based_on": "POSITIVE_OPENAPI_UNMOUNTED",
        "mutation": {
            "observed_status": 401,
            "observed_www_authenticate": RECRUITER_REALM_HEADER,
            "expected_route_state": "mounted_unprotected",
        },
        "violated_rule": "docs surface gated by recruiter realm is still a leak under default plan",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
]

POSITIVE_FIXTURES = [POSITIVE_OPENAPI_UNMOUNTED]

_POSITIVES_BY_NAME = {"POSITIVE_OPENAPI_UNMOUNTED": POSITIVE_OPENAPI_UNMOUNTED}


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


def _classify(status, www_authenticate, body_snippet):
    if status == 404:
        return "unmounted"
    if status == 401 and www_authenticate:
        if www_authenticate == RECRUITER_REALM_HEADER:
            return "mounted_unprotected"
        return "mounted_admin_only"
    if status == 200:
        return "mounted_unprotected"
    snippet = (body_snippet or "").lower()
    if ("openapi" in snippet or "swagger" in snippet
            or "redoc" in snippet or "<html" in snippet):
        return "mounted_unprotected"
    return "unmounted"


def _fixture_passes(fix: dict) -> bool:
    state = _classify(
        fix.get("observed_status"),
        fix.get("observed_www_authenticate"),
        fix.get("observed_body_snippet"),
    )
    return state in ("unmounted", "mounted_admin_only")


def _adversarial_check(positives, negatives):
    issues = []
    for fix in positives:
        if not _fixture_passes(fix):
            issues.append(f"positive {fix['label']!r} did not pass classifier")
    for fix in negatives:
        if _fixture_passes(fix):
            issues.append(f"negative {fix['label']!r} unexpectedly passes classifier")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = (manifest_path.parent
                    / "generate_fixture_validate_b14_1_openapi_docs_visibility")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    positives = POSITIVE_FIXTURES
    negatives = [_materialize_negative(n) for n in NEGATIVE_FIXTURES]

    adversarial_issues = _adversarial_check(positives, negatives)

    manifest = {
        "validator": "validate_b14_1_openapi_docs_visibility",
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
            "expected_route_state": fix["expected_route_state"],
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
            "expected_route_state": fix["expected_route_state"],
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
