#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_1_no_network_trust_authority.

Produces positive and negative declarative fixtures matching the
no-network-trust-authority contract: under PUBLIC_DEMO_EXPOSURE=true,
unauthenticated /demo/* probes with spoofed trust headers MUST still
return 401 with the canonical recruiter realm; the application source
surface MUST contain no forbidden network-origin tokens.

Two fixture categories:
  * runtime_response: an HTTP response shape observed under a spoofed
    trust header. Positive = 401 + canonical realm; negative = 200 (bypass).
  * source_snippet: a synthetic source-fragment containing or omitting the
    forbidden tokens. Positive = clean; negative = trust-by-header or
    trust-by-IP authority decision.

Emits OK_FIXTURE_VALIDATE_B14_1_NO_NETWORK_TRUST on PASS or
B14_1_NETWORK_TRUST_AUTHORITY_DETECTED on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_NO_NETWORK_TRUST"
SENTINEL_FAIL = "B14_1_NETWORK_TRUST_AUTHORITY_DETECTED"

EXPECTED_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'

FORBIDDEN_TOKEN_PATTERNS = [
    re.compile(r"\bX-Forwarded-For\b", re.IGNORECASE),
    re.compile(r"\bX-Real-IP\b", re.IGNORECASE),
    re.compile(r"\bX-Forwarded-Proto\b", re.IGNORECASE),
    re.compile(r"\bREMOTE_ADDR\b"),
    re.compile(r"\bTailscale-User-Login\b", re.IGNORECASE),
    re.compile(r"\bTailscale-User-Name\b", re.IGNORECASE),
    re.compile(r"\bX-Tailscale-Identity\b", re.IGNORECASE),
    re.compile(r"\bTailscale-Identity\b", re.IGNORECASE),
    re.compile(r"request\.client\.host"),
]

POSITIVE_RUNTIME_FIXTURES = [
    {
        "label": "positive_unauth_xff_10_0_0_1_still_401",
        "kind": "runtime_response",
        "spoofed_header": {"X-Forwarded-For": "10.0.0.1"},
        "route": "/demo/health",
        "observed_status": 401,
        "observed_www_authenticate": EXPECTED_REALM_HEADER,
        "expected_validator_outcome": "PASS",
    },
]

POSITIVE_SOURCE_FIXTURES = [
    {
        "label": "positive_source_no_forbidden_tokens",
        "kind": "source_snippet",
        "synthetic_source": (
            "async def recruiter_auth_dependency(request: Request) -> None:\n"
            "    expected = _read_env_credentials()\n"
            "    if expected is None:\n"
            "        raise RecruiterAuthChallenge()\n"
        ),
        "expected_validator_outcome": "PASS",
    },
]

NEGATIVE_RUNTIME_FIXTURES = [
    {
        "label": "negative_unauth_xff_returned_200",
        "kind": "runtime_response",
        "spoofed_header": {"X-Forwarded-For": "127.0.0.1"},
        "route": "/demo/health",
        "observed_status": 200,
        "observed_www_authenticate": None,
        "violated_rule": "spoofed X-Forwarded-For must not bypass recruiter gate",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
    {
        "label": "negative_unauth_tailscale_id_returned_200",
        "kind": "runtime_response",
        "spoofed_header": {"X-Tailscale-Identity": "ts-id-placeholder"},
        "route": "/demo/health",
        "observed_status": 200,
        "observed_www_authenticate": None,
        "violated_rule": "spoofed Tailscale identity header must not bypass recruiter gate",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
]

NEGATIVE_SOURCE_FIXTURES = [
    {
        "label": "negative_source_trust_by_xff",
        "kind": "source_snippet",
        "synthetic_source": (
            "if request.headers.get('X-Forwarded-For') == '127.0.0.1':\n"
            "    return Response(status_code=200)\n"
        ),
        "violated_rule": "authority decision keyed on X-Forwarded-For",
        "expected_validator_outcome": "FAIL",
        "expected_classification": SENTINEL_FAIL,
    },
]


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _runtime_satisfies_contract(fix: dict) -> bool:
    return (fix.get("observed_status") == 401
            and fix.get("observed_www_authenticate") == EXPECTED_REALM_HEADER)


def _source_has_forbidden_token(fix: dict) -> bool:
    src = fix.get("synthetic_source", "")
    return any(pat.search(src) for pat in FORBIDDEN_TOKEN_PATTERNS)


def _adversarial_check(positives, negatives):
    issues = []
    for fix in positives:
        if fix.get("kind") == "runtime_response":
            if not _runtime_satisfies_contract(fix):
                issues.append(f"positive runtime {fix['label']!r} did not satisfy contract")
        elif fix.get("kind") == "source_snippet":
            if _source_has_forbidden_token(fix):
                issues.append(f"positive source {fix['label']!r} unexpectedly contains forbidden token")
    for fix in negatives:
        if fix.get("kind") == "runtime_response":
            if _runtime_satisfies_contract(fix):
                issues.append(f"negative runtime {fix['label']!r} unexpectedly satisfies contract")
        elif fix.get("kind") == "source_snippet":
            if not _source_has_forbidden_token(fix):
                issues.append(f"negative source {fix['label']!r} missing forbidden token")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = (manifest_path.parent
                    / "generate_fixture_validate_b14_1_no_network_trust_authority")
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    positives = POSITIVE_RUNTIME_FIXTURES + POSITIVE_SOURCE_FIXTURES
    negatives = NEGATIVE_RUNTIME_FIXTURES + NEGATIVE_SOURCE_FIXTURES

    adversarial_issues = _adversarial_check(positives, negatives)

    manifest = {
        "validator": "validate_b14_1_no_network_trust_authority",
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
