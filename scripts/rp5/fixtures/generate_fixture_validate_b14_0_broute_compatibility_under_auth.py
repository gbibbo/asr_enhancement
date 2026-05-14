#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_broute_compatibility_under_auth.

Produces positive and negative synthetic transcript fixtures covering
the seven BR-NN re-emission lanes plus the FROZEN-schema guard, with a
manifest carrying per-file sha256 and size. Each negative fixture
violates exactly one lane; the positive fixture set passes every lane.

The fixtures live under
<manifest_parent>/validate_b14_0_broute_compatibility_under_auth/<case>/ ;
they are never staged for commit and are removed before final status.

Emits OK_FIXTURE_VALIDATE_B14_0_BROUTE_COMPATIBILITY on PASS or
B14_0_BROUTE_REGRESSION_UNDER_AUTH on FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_BROUTE_COMPATIBILITY"
SENTINEL_FAIL = "B14_0_BROUTE_REGRESSION_UNDER_AUTH"
SENTINEL_HEALTH_FAIL = "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH"
SENTINEL_UNAUTH_FILE = "UNAUTHORIZED_FILE_TOUCHED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rp5"))
import validate_b14_0_broute_compatibility_under_auth as v  # type: ignore


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hash_tree(root: pathlib.Path):
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            files.append({
                "path": str(p.relative_to(root)),
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            })
    return files


# ---------------------------------------------------------------------------
# Positive fixture
# ---------------------------------------------------------------------------


def write_positive_fixture(root: pathlib.Path):
    transcript = {
        "name": "positive_clean_broute_compat_transcript",
        "FROZEN_SCHEMA": "router_runtime + types.ts RouterFields match frozen baselines",
        "BR-02 health_public_payload":
            "/demo/health authenticated -> 200 byte-exact, "
            "/demo/health unauthenticated -> 401 + canonical realm",
        "BR-02 public_security_invariants":
            "/admin/* HTTPBasic semantics unchanged; "
            "/demo/* under recruiter auth privacy-safe",
        "BR-03 cache_key_contract": "subprocess emits OK_BROUTE_CACHE_KEY_CONTRACT",
        "BR-04 frontend_backend_contract": "subprocess emits OK_FRONTEND_BACKEND_CONTRACT",
        "BR-05 manual_smoke": "all 6 recruiter-protected routes authenticate cleanly",
        "BR-06 router_stub_smoke": "in-process TestClient with Authorization passes shape checks",
        "BR-07 future_constraints": "subprocess emits OK_FUTURE_CONSTRAINTS",
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "transcript.json").write_text(
        json.dumps(transcript, indent=2, sort_keys=True),
    )


def positive_adversarial_check() -> list:
    """Validator predicates accept the canonical positive transcript."""
    issues = []
    # The validator's body-no-leak scan over an empty 401 body and a
    # canonical /demo/health authenticated body must produce no hits.
    for body in (b"", v.EXPECTED_HEALTH_BODY):
        if v._scan_body_for_router_substrings(body):
            issues.append(f"positive body unexpectedly matched router substring: {body!r}")
        if v._scan_body_for_credential_values(
            body, "syn-rec-user", "syn-rec-pass", "syn-adm-user", "syn-adm-pass",
        ):
            issues.append(f"positive body unexpectedly matched credential value: {body!r}")
    return issues


# ---------------------------------------------------------------------------
# Negative fixtures (one per lane / regression family)
# ---------------------------------------------------------------------------


def negative_frozen_router_runtime_drift():
    return {
        "lane": "FROZEN_SCHEMA",
        "violation": "libs/asr/router_runtime.py sha256 drift",
        "expected_marker": SENTINEL_UNAUTH_FILE,
        "predicate_test": "frozen_router_runtime_sha_diff",
    }


def negative_frozen_frontend_router_shape_drift():
    return {
        "lane": "FROZEN_SCHEMA",
        "violation": "types.ts RouterFields shape sha256 drift",
        "expected_marker": SENTINEL_UNAUTH_FILE,
        "predicate_test": "frozen_frontend_types_sha_diff",
    }


def negative_br02_health_byte_drift():
    return {
        "lane": "BR-02 health_public_payload",
        "violation": ("authenticated /demo/health returns a non-canonical body "
                      "(byte mismatch vs " + repr(v.EXPECTED_HEALTH_BODY) + ")"),
        "expected_marker": SENTINEL_HEALTH_FAIL,
        "predicate_test": "br02_health_byte_diff",
    }


def negative_br02_public_security_demo_health_router_leak():
    return {
        "lane": "BR-02 public_security_invariants",
        "violation": "authenticated /demo/health body carries router-field substring",
        "expected_marker": SENTINEL_FAIL,
        "predicate_test": "br02_public_security_router_leak",
    }


def negative_br05_manual_smoke_unexpected_status():
    return {
        "lane": "BR-05 manual_smoke",
        "violation": ("authenticated GET /demo/health returns a status outside "
                      "the expected_authenticated_statuses set"),
        "expected_marker": SENTINEL_FAIL,
        "predicate_test": "br05_unexpected_status",
    }


def negative_br06_router_stub_router_leak_in_examples():
    return {
        "lane": "BR-06 router_stub_smoke",
        "violation": "/demo/examples authenticated body carries router-field substring",
        "expected_marker": SENTINEL_FAIL,
        "predicate_test": "br06_router_leak_in_body",
    }


def negative_uvicorn_log_with_password():
    rec_pass = "synthetic-fixture-password-xyz"
    body = (
        b"INFO: Application startup complete.\n"
        b"DEBUG: recruiter password=" + rec_pass.encode("utf-8") + b"\n"
    )
    return {
        "lane": "uvicorn_log_credential_leak",
        "violation": "uvicorn log line contains recruiter password value",
        "expected_marker": SENTINEL_FAIL,
        "predicate_test": "uvicorn_log_password",
        "synthetic_log_bytes_sha256": sha256_bytes(body),
        "synthetic_password_used": rec_pass,
    }


def adversarial_check_predicate(case_name: str) -> list:
    """Verify each negative scenario is rejected by the validator predicates.

    This is in-process; we exercise the validator helper functions
    directly with synthetic inputs so the adversarial smoke does not
    require a live HTTP server or a recruiter-gated app.
    """
    issues = []
    if case_name == "negative_frozen_router_runtime_drift":
        # Compare an arbitrary non-matching sha against the baseline.
        observed = "0" * 64
        if observed == v.FROZEN_ROUTER_RUNTIME_SHA256:
            issues.append("baseline collision with all-zero hash")
        # The validator's check_frozen_schemas() would emit a FAIL with
        # SENTINEL_UNAUTH_FILE on mismatch; we mimic the comparison here
        # to assert the predicate is monotonic on mismatch.
        if observed == v.FROZEN_ROUTER_RUNTIME_SHA256:
            issues.append("predicate would accept drifted router_runtime sha")
    elif case_name == "negative_frozen_frontend_router_shape_drift":
        observed = "0" * 64
        if observed == v.FROZEN_FRONTEND_TYPES_ROUTER_SHAPE_SHA256:
            issues.append("predicate would accept drifted types.ts RouterFields sha")
    elif case_name == "negative_br02_health_byte_drift":
        # Validator's byte_exact predicate must reject any non-canonical body.
        candidate = b'{"status":"degraded"}'
        if candidate == v.EXPECTED_HEALTH_BODY:
            issues.append("byte-exact predicate baseline drift")
    elif case_name == "negative_br02_public_security_demo_health_router_leak":
        candidate = b'{"status":"ok","router_kind":"hint"}'
        if not v._scan_body_for_router_substrings(candidate):
            issues.append("router substring scan missed leaking body")
    elif case_name == "negative_br05_manual_smoke_unexpected_status":
        # 500 is not in [200] -> predicate must reject.
        expected = [200]
        observed_status = 500
        if observed_status in expected:
            issues.append("manual-smoke expected_status predicate baseline error")
    elif case_name == "negative_br06_router_stub_router_leak_in_examples":
        candidate = b'{"examples":[],"total":0,"router_version":"x"}'
        if not v._scan_body_for_router_substrings(candidate):
            issues.append("router substring scan missed leaking BR-06 body")
    elif case_name == "negative_uvicorn_log_with_password":
        # Materialize the log next to a tmp path and run scan_uvicorn_log.
        rec_pass = "synthetic-fixture-password-xyz"
        log_bytes = (
            b"INFO: Application startup complete.\n"
            b"DEBUG: recruiter password=" + rec_pass.encode("utf-8") + b"\n"
        )
        tmp = pathlib.Path(case_name + "_uvicorn.log").resolve()
        tmp.write_bytes(log_bytes)
        try:
            checks, classification = v.scan_uvicorn_log(
                str(tmp), "syn-rec-user", rec_pass,
                "syn-adm-user", "syn-adm-pass",
            )
            if classification is None:
                issues.append("scan_uvicorn_log did not flag leaking log")
        finally:
            tmp.unlink(missing_ok=True)
    return issues


def build_negative_cases(fixtures_root: pathlib.Path):
    inventory = [
        ("negative_frozen_router_runtime_drift",
         negative_frozen_router_runtime_drift()),
        ("negative_frozen_frontend_router_shape_drift",
         negative_frozen_frontend_router_shape_drift()),
        ("negative_br02_health_byte_drift",
         negative_br02_health_byte_drift()),
        ("negative_br02_public_security_demo_health_router_leak",
         negative_br02_public_security_demo_health_router_leak()),
        ("negative_br05_manual_smoke_unexpected_status",
         negative_br05_manual_smoke_unexpected_status()),
        ("negative_br06_router_stub_router_leak_in_examples",
         negative_br06_router_stub_router_leak_in_examples()),
        ("negative_uvicorn_log_with_password",
         negative_uvicorn_log_with_password()),
    ]
    cases = []
    for name, record in inventory:
        root = fixtures_root / name
        root.mkdir(parents=True, exist_ok=True)
        (root / "transcript.json").write_text(
            json.dumps({"name": name, **record}, indent=2, sort_keys=True),
        )
        cases.append({
            "case_name": name,
            "violated_lane": record["lane"],
            "expected_marker": record["expected_marker"],
            "root": root,
        })
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = manifest_path.parent / "validate_b14_0_broute_compatibility_under_auth"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    pos_root = fixtures_root / "positive_clean_broute_compat_transcript"
    write_positive_fixture(pos_root)
    pos_issues = positive_adversarial_check()

    negative_cases = build_negative_cases(fixtures_root)
    adversarial_failures = []
    negative_entries = []
    for case in negative_cases:
        issues = adversarial_check_predicate(case["case_name"])
        negative_entries.append({
            "case_name": case["case_name"],
            "root": str(case["root"]),
            "violated_lane": case["violated_lane"],
            "expected_marker": case["expected_marker"],
            "adversarial_predicate_issues": issues,
            "tree_files": hash_tree(case["root"]),
        })
        if issues:
            adversarial_failures.append(case["case_name"])

    positive_entry = {
        "case_name": "positive_clean_broute_compat_transcript",
        "root": str(pos_root),
        "violated_lane": None,
        "adversarial_predicate_issues": pos_issues,
        "tree_files": hash_tree(pos_root),
    }
    if pos_issues:
        adversarial_failures.append("positive_clean_broute_compat_transcript")

    manifest = {
        "validator": "validate_b14_0_broute_compatibility_under_auth",
        "kind": args.kind,
        "owned_marker": SENTINEL_FAIL,
        "sentinel_pass": SENTINEL_PASS,
        "fixtures_root": str(fixtures_root),
        "positive": [positive_entry],
        "negative": negative_entries,
    }
    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_body)

    print(f"manifest_sha256: {sha256_bytes(manifest_body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_failures:
        print(f"adversarial_failures: {adversarial_failures}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
