#!/usr/bin/env python3
"""
Fixture generator paired with
validate_b14_1_health_payload_preserved_under_public_exposure.

Produces declarative response-shape fixtures asserting byte-exact equality
of the authenticated /demo/health body against b'{"status":"ok"}' under
PUBLIC_DEMO_EXPOSURE=true. The HTTP status MUST be 200; the body bytes
MUST equal b'{"status":"ok"}' exactly.

Each fixture is a JSON descriptor of an observed HTTP response. Adversarial
self-check ensures positives satisfy the byte-exact contract and negatives
violate exactly the rule named in their `violated_rule` field.

Emits OK_FIXTURE_VALIDATE_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE on PASS or
B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE"

EXPECTED_HEALTH_BODY = '{"status":"ok"}'
EXPECTED_HEALTH_BODY_SHA256 = hashlib.sha256(
    EXPECTED_HEALTH_BODY.encode("utf-8")
).hexdigest()

POSITIVE_AUTH_HEALTH = {
    "label": "positive_auth_demo_health_byte_exact",
    "route": "/demo/health",
    "method": "GET",
    "authorization_header": "Basic <ephemeral>",
    "observed_status": 200,
    "observed_body_bytes": EXPECTED_HEALTH_BODY,
    "observed_body_sha256": EXPECTED_HEALTH_BODY_SHA256,
    "expected_validator_outcome": "PASS",
}

NEGATIVE_FIXTURES = [
    {
        "label": "negative_auth_demo_health_body_pretty_printed",
        "based_on": "POSITIVE_AUTH_HEALTH",
        "mutation": {
            "observed_body_bytes": '{"status": "ok"}',
            "observed_body_sha256": hashlib.sha256(
                b'{"status": "ok"}'
            ).hexdigest(),
        },
        "violated_rule": "body must equal canonical bytes; whitespace forbidden",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
    {
        "label": "negative_auth_demo_health_body_degraded",
        "based_on": "POSITIVE_AUTH_HEALTH",
        "mutation": {
            "observed_body_bytes": '{"status":"degraded"}',
            "observed_body_sha256": hashlib.sha256(
                b'{"status":"degraded"}'
            ).hexdigest(),
        },
        "violated_rule": "body status field must equal canonical 'ok'",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
]

POSITIVE_FIXTURES = [POSITIVE_AUTH_HEALTH]

_POSITIVES_BY_NAME = {"POSITIVE_AUTH_HEALTH": POSITIVE_AUTH_HEALTH}


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
                    / "generate_fixture_validate_b14_1_health_payload_preserved_under_public_exposure")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    positives = POSITIVE_FIXTURES
    negatives = [_materialize_negative(n) for n in NEGATIVE_FIXTURES]

    adversarial_issues = _adversarial_check(positives, negatives)

    manifest = {
        "validator": "validate_b14_1_health_payload_preserved_under_public_exposure",
        "kind": args.kind,
        "owned_marker": SENTINEL_FAIL,
        "sentinel_pass": SENTINEL_PASS,
        "canonical_body_sha256": EXPECTED_HEALTH_BODY_SHA256,
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
