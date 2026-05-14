#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_auth_separation_invariants.

Emits one positive fixture (a canonical observation set across the five
separation dimensions plus the cred_separation env attestation) and one
negative fixture per violation rule (realm collapse, cross-credential
username acceptance, cross-credential password acceptance, route_prefix
overlap, byte-equal 401 bodies, conflated env credentials). Adversarial
in-process check confirms every positive passes the validator's structural
predicates and every negative is rejected by at least one predicate.

Fixtures contain only realm strings, status codes, route prefixes, body
length / equality flags, and boolean attestations. They never contain
credential values.

Emits OK_FIXTURE_VALIDATE_B14_0_AUTH_SEPARATION on PASS or
B14_0_AUTH_BYPASS_DETECTED (or B14_0_ADMIN_RECRUITER_CRED_CONFLATION for
cred_separation negatives) on FAIL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_AUTH_SEPARATION"
SENTINEL_BYPASS = "B14_0_AUTH_BYPASS_DETECTED"
SENTINEL_CONFLATION = "B14_0_ADMIN_RECRUITER_CRED_CONFLATION"

RECRUITER_REALM = 'Basic realm="asr-demo-recruiter"'
ADMIN_REALM = "Basic"

POSITIVE = {
    "label": "positive_canonical_separation",
    "observations": {
        "realm.demo_health_realm": RECRUITER_REALM,
        "realm.admin_health_realm": ADMIN_REALM,
        "username.admin_creds_at_demo_status": 401,
        "username.admin_creds_at_demo_realm": RECRUITER_REALM,
        "username.recruiter_creds_at_admin_status": 401,
        "username.recruiter_creds_at_admin_realm": ADMIN_REALM,
        "password.recruiter_user_admin_pass_at_demo_status": 401,
        "password.admin_user_recruiter_pass_at_admin_status": 401,
        "route_prefix.recruiter_routes_all_under_demo": True,
        "route_prefix.admin_routes_all_under_admin": True,
        "route_prefix.sets_disjoint": True,
        "error_path.demo_body_length": 0,
        "error_path.admin_body_length_gt_zero": True,
        "error_path.bodies_distinct": True,
        "cred_separation.usernames_distinct": True,
        "cred_separation.passwords_distinct": True,
    },
    "expected_validator_outcome": "PASS",
}

NEGATIVES = [
    {
        "label": "negative_realm_collapse",
        "mutation": {"realm.admin_health_realm": RECRUITER_REALM},
        "violated_rule": "admin surface must not advertise the recruiter realm string",
        "expected_classification": SENTINEL_BYPASS,
    },
    {
        "label": "negative_admin_creds_accepted_at_demo",
        "mutation": {"username.admin_creds_at_demo_status": 200,
                     "username.admin_creds_at_demo_realm": None},
        "violated_rule": "recruiter surface must reject admin credentials",
        "expected_classification": SENTINEL_BYPASS,
    },
    {
        "label": "negative_recruiter_creds_accepted_at_admin",
        "mutation": {"username.recruiter_creds_at_admin_status": 200,
                     "username.recruiter_creds_at_admin_realm": None},
        "violated_rule": "admin surface must reject recruiter credentials",
        "expected_classification": SENTINEL_BYPASS,
    },
    {
        "label": "negative_route_prefix_overlap",
        "mutation": {"route_prefix.sets_disjoint": False,
                     "route_prefix.recruiter_routes_all_under_demo": False},
        "violated_rule": "recruiter-dependency routes must all live under /demo/ and be disjoint from /admin/",
        "expected_classification": SENTINEL_BYPASS,
    },
    {
        "label": "negative_error_path_collapse",
        "mutation": {"error_path.bodies_distinct": False,
                     "error_path.demo_body_length": 24,
                     "error_path.admin_body_length_gt_zero": True},
        "violated_rule": "401 bodies of /admin/health and /demo/health must not be byte-equal",
        "expected_classification": SENTINEL_BYPASS,
    },
    {
        "label": "negative_cred_separation_username_conflated",
        "mutation": {"cred_separation.usernames_distinct": False},
        "violated_rule": "admin and recruiter usernames must be byte-distinct",
        "expected_classification": SENTINEL_CONFLATION,
    },
    {
        "label": "negative_cred_separation_password_conflated",
        "mutation": {"cred_separation.passwords_distinct": False},
        "violated_rule": "admin and recruiter passwords must be byte-distinct",
        "expected_classification": SENTINEL_CONFLATION,
    },
]


def _materialize_negative(neg):
    out = copy.deepcopy(POSITIVE)
    out["label"] = neg["label"]
    out["observations"].update(neg["mutation"])
    out["violated_rule"] = neg["violated_rule"]
    out["expected_validator_outcome"] = "FAIL"
    out["expected_classification"] = neg["expected_classification"]
    return out


def _adversarial_check(positive, negatives):
    issues = []

    def violates(obs):
        v = []
        if obs.get("realm.demo_health_realm") != RECRUITER_REALM:
            v.append("realm.demo")
        if obs.get("realm.admin_health_realm") == RECRUITER_REALM:
            v.append("realm.collision")
        if obs.get("username.admin_creds_at_demo_status") != 401:
            v.append("username.admin_at_demo")
        if obs.get("username.recruiter_creds_at_admin_status") != 401:
            v.append("username.recruiter_at_admin")
        if obs.get("password.recruiter_user_admin_pass_at_demo_status") != 401:
            v.append("password.demo")
        if obs.get("password.admin_user_recruiter_pass_at_admin_status") != 401:
            v.append("password.admin")
        if not obs.get("route_prefix.sets_disjoint", False):
            v.append("route_prefix.disjoint")
        if not obs.get("route_prefix.recruiter_routes_all_under_demo", False):
            v.append("route_prefix.recruiter_under_demo")
        if not obs.get("route_prefix.admin_routes_all_under_admin", False):
            v.append("route_prefix.admin_under_admin")
        if not obs.get("error_path.bodies_distinct", False):
            v.append("error_path.distinct")
        if obs.get("error_path.demo_body_length", 0) != 0:
            v.append("error_path.demo_empty")
        if not obs.get("cred_separation.usernames_distinct", True):
            v.append("cred_separation.user")
        if not obs.get("cred_separation.passwords_distinct", True):
            v.append("cred_separation.pass")
        return v

    pos_v = violates(positive["observations"])
    if pos_v:
        issues.append(f"positive unexpectedly flagged: {pos_v}")

    for neg in negatives:
        v = violates(neg["observations"])
        if not v:
            issues.append(f"negative {neg['label']!r} did not violate any predicate")

    return issues


def _sha256(b):
    return hashlib.sha256(b).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = manifest_path.parent / "validate_b14_0_auth_separation_invariants"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    negatives_materialized = [_materialize_negative(n) for n in NEGATIVES]

    manifest = {
        "validator": "validate_b14_0_auth_separation_invariants",
        "kind": args.kind,
        "positive": [],
        "negative": [],
        "owned_markers": [SENTINEL_BYPASS, SENTINEL_CONFLATION],
        "sentinel_pass": SENTINEL_PASS,
    }

    body = json.dumps(POSITIVE, indent=2, sort_keys=True).encode("utf-8")
    path = fixtures_dir / f"{POSITIVE['label']}.json"
    path.write_bytes(body)
    manifest["positive"].append({
        "path": str(path),
        "sha256": _sha256(body),
        "size_bytes": len(body),
        "expected_validator_outcome": POSITIVE["expected_validator_outcome"],
    })

    for neg in negatives_materialized:
        body = json.dumps(neg, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / f"{neg['label']}.json"
        path.write_bytes(body)
        manifest["negative"].append({
            "path": str(path),
            "sha256": _sha256(body),
            "size_bytes": len(body),
            "violated_rule": neg["violated_rule"],
            "expected_validator_outcome": neg["expected_validator_outcome"],
            "expected_classification": neg["expected_classification"],
        })

    issues = _adversarial_check(POSITIVE, negatives_materialized)
    manifest["adversarial_check_issues"] = issues

    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_body)
    print(f"manifest_sha256: {_sha256(manifest_body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if issues:
        for i in issues:
            print(f"adversarial_issue: {i}")
        print(SENTINEL_BYPASS)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
