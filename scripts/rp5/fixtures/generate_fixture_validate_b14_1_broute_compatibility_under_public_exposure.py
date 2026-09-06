#!/usr/bin/env python3
"""
Fixture generator paired with
validate_b14_1_broute_compatibility_under_public_exposure.

Produces declarative compatibility-scenario fixtures for the B14_1-07
adversarial round-trip. Each fixture is a directory containing a
descriptor.json describing one observed compatibility scenario:

  router_runtime_sha256       -- observed SHA-256 of libs/asr/router_runtime.py
  types_router_shape_sha256   -- observed RouterFields-shape SHA-256 of
                                 services/frontend/app/demo/types.ts
  health_probe                -- simulated loopback /demo/health probe
                                 under PUBLIC_DEMO_EXPOSURE=true

One positive (everything frozen + canonical BR-02 health payload) plus
three negatives, each violating exactly one invariant:

  * router-schema-edit          -- router_runtime SHA-256 drifts.
  * routerfields-shape-edit     -- types.ts RouterFields shape drifts.
  * non-canonical BR-02 payload -- authenticated /demo/health body is not
                                   byte-exact b'{"status":"ok"}'.

The positive embeds the deterministic git-derived frozen anchors, so the
paired validator classifies it PASS; the negatives are classified FAIL.
The generator adversarially asserts that round-trip before emitting its
sentinel.

Emits OK_FIXTURE_VALIDATE_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE
on PASS or B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE on FAIL.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

VALIDATOR_PASS = "OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (REPO_ROOT / "scripts" / "rp5"
                  / "validate_b14_1_broute_compatibility_under_public_exposure.py")

FIXTURE_DIR_NAME = "validate_b14_1_broute_compatibility_under_public_exposure"

CANONICAL_HEALTH_BODY = b'{"status":"ok"}'
NON_CANONICAL_HEALTH_BODY = b'{"status":"degraded"}'
EXPECTED_WWW_AUTHENTICATE = 'Basic realm="asr-demo-recruiter"'

# Deterministic bogus fingerprints for the negative fixtures. Derived from
# fixed marker strings so they are stable across runs and unambiguously
# distinct from any real frozen anchor.
BOGUS_ROUTER_SHA = hashlib.sha256(
    b"b14_1_07-negative-router-schema-edit").hexdigest()
BOGUS_TYPES_SHA = hashlib.sha256(
    b"b14_1_07-negative-routerfields-shape-edit").hexdigest()


def _load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "_b14_1_07_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_health_probe(auth_body):
    return {
        "unauth_status": 401,
        "unauth_www_authenticate": EXPECTED_WWW_AUTHENTICATE,
        "auth_status": 200,
        "auth_body_b64": base64.b64encode(auth_body).decode("ascii"),
    }


def _sha256(b):
    return hashlib.sha256(b).hexdigest()


def build_descriptors(router_anchor, types_anchor):
    """Return list of (fixture_id, kind, descriptor_dict)."""
    descriptors = []

    descriptors.append((
        "positive_frozen_compatible", "positive",
        {
            "fixture_id": "positive_frozen_compatible",
            "kind": "positive",
            "violated_rule": None,
            "expected_sentinel": VALIDATOR_PASS,
            "router_runtime_sha256": router_anchor,
            "types_router_shape_sha256": types_anchor,
            "health_probe": _canonical_health_probe(CANONICAL_HEALTH_BODY),
        },
    ))

    descriptors.append((
        "negative_router_schema_edit", "negative",
        {
            "fixture_id": "negative_router_schema_edit",
            "kind": "negative",
            "violated_rule": "libs/asr/router_runtime.py SHA-256 drifted "
                             "from the frozen anchor (FC-BROUTE-FROZEN)",
            "expected_sentinel": SENTINEL_FAIL,
            "router_runtime_sha256": BOGUS_ROUTER_SHA,
            "types_router_shape_sha256": types_anchor,
            "health_probe": _canonical_health_probe(CANONICAL_HEALTH_BODY),
        },
    ))

    descriptors.append((
        "negative_routerfields_shape_edit", "negative",
        {
            "fixture_id": "negative_routerfields_shape_edit",
            "kind": "negative",
            "violated_rule": "services/frontend/app/demo/types.ts "
                             "RouterFields shape drifted from the frozen "
                             "anchor (FC-BROUTE-FROZEN)",
            "expected_sentinel": SENTINEL_FAIL,
            "router_runtime_sha256": router_anchor,
            "types_router_shape_sha256": BOGUS_TYPES_SHA,
            "health_probe": _canonical_health_probe(CANONICAL_HEALTH_BODY),
        },
    ))

    descriptors.append((
        "negative_noncanonical_health_payload", "negative",
        {
            "fixture_id": "negative_noncanonical_health_payload",
            "kind": "negative",
            "violated_rule": "authenticated /demo/health body is not "
                             "byte-exact {\"status\":\"ok\"} under public "
                             "exposure (BR-02 health invariant regressed)",
            "expected_sentinel": SENTINEL_FAIL,
            "router_runtime_sha256": router_anchor,
            "types_router_shape_sha256": types_anchor,
            "health_probe": _canonical_health_probe(NON_CANONICAL_HEALTH_BODY),
        },
    ))

    return descriptors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True,
                        choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    validator = _load_validator_module()
    router_anchor, types_anchor, anchors_error = validator.derive_anchors()
    if anchors_error is not None:
        print(f"anchor_derivation_error: {anchors_error}")
        print(SENTINEL_FAIL)
        return 1

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = manifest_path.parent / FIXTURE_DIR_NAME
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    descriptors = build_descriptors(router_anchor, types_anchor)

    manifest = {
        "validator": "validate_b14_1_broute_compatibility_under_public_exposure",
        "kind": args.kind,
        "owned_marker": SENTINEL_FAIL,
        "sentinel_pass": SENTINEL_PASS,
        "frozen_anchor_commit": validator.FROZEN_ANCHOR_COMMIT,
        "positive": [],
        "negative": [],
    }

    adversarial_issues = []

    for fixture_id, kind, descriptor in descriptors:
        fixture_subdir = fixtures_dir / fixture_id
        fixture_subdir.mkdir(parents=True, exist_ok=True)
        body = json.dumps(descriptor, indent=2, sort_keys=True).encode("utf-8")
        desc_path = fixture_subdir / "descriptor.json"
        desc_path.write_bytes(body)

        # Adversarial round-trip: classify the scenario and confirm it
        # matches the descriptor's declared expected_sentinel.
        scenario = validator._scenario_from_descriptor(descriptor)
        verdict, _checks = validator.classify_scenario(
            scenario, router_anchor, types_anchor)
        if verdict != descriptor["expected_sentinel"]:
            adversarial_issues.append(
                f"{fixture_id}: classified {verdict} but descriptor expects "
                f"{descriptor['expected_sentinel']}")

        entry = {
            "fixture_id": fixture_id,
            "path": str(desc_path.relative_to(manifest_path.parent)),
            "sha256": _sha256(body),
            "size_bytes": len(body),
            "kind": kind,
            "expected_sentinel": descriptor["expected_sentinel"],
        }
        if kind == "positive":
            manifest["positive"].append(entry)
        else:
            manifest["negative"].append(entry)

    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_body)

    print(f"manifest_sha256: {_sha256(manifest_body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_issues:
        for issue in adversarial_issues:
            print(f"adversarial_issue: {issue}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
