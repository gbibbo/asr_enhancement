#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_no_credential_leak.

Produces positive and negative synthetic transcript fixtures for the
INV-CL-001..010 invariants, plus a manifest carrying per-file sha256
and size. Each negative fixture violates exactly one invariant; the
positive fixture set passes every invariant. Negative scenarios are
materialized as transcript records (status / headers / body / log
lines) and adversarially checked against the validator's predicate
functions in-process so we prove the negative set is genuinely
negative without standing up an HTTP server.

The fixtures live under
<manifest_parent>/validate_b14_0_no_credential_leak/<case>/ ; they are
never staged for commit and are removed before final status.

Emits OK_FIXTURE_VALIDATE_B14_0_NO_CRED_LEAK on PASS or
B14_0_CRED_LEAK_DETECTED on FAIL.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_NO_CRED_LEAK"
SENTINEL_FAIL = "B14_0_CRED_LEAK_DETECTED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rp5"))
import validate_b14_0_no_credential_leak as v  # type: ignore


# Synthetic placeholder credential values used only inside this generator
# at fixture-build time. Never leave local-only fixture files.
PLACEHOLDER_REC_USER = "recruiter-fixture-user"
PLACEHOLDER_REC_PASS = "recruiter-fixture-pass-xyz"
PLACEHOLDER_ADM_USER = "admin-fixture-user"
PLACEHOLDER_ADM_PASS = "admin-fixture-pass-xyz"


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
# Positive fixture (single canonical clean transcript)
# ---------------------------------------------------------------------------

def write_positive_fixture(root: pathlib.Path):
    transcript = {
        "name": "positive_clean_no_leak_transcript",
        "INV-CL-001..004": "401 bodies empty, no credential bytes",
        "INV-CL-005": "wrong-auth 401 body empty, no Authorization echo",
        "INV-CL-006": "no credential bytes in non-WWW-Authenticate headers",
        "INV-CL-007": "error-path bodies free of credential bytes",
        "INV-CL-008": "401 bodies free of router-field substrings",
        "INV-CL-009": "uvicorn log free of credential or Authorization base64",
        "INV-CL-010": "Pydantic 422 bodies free of credential bytes",
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "transcript.json").write_text(
        json.dumps(transcript, indent=2, sort_keys=True),
    )
    (root / "uvicorn.log").write_bytes(
        b"INFO: Application startup complete.\n"
        b"INFO: Uvicorn running on http://127.0.0.1:8001\n"
        b'INFO: 127.0.0.1 - "GET /demo/health HTTP/1.1" 401\n'
        b'INFO: 127.0.0.1 - "GET /demo/health HTTP/1.1" 200\n'
    )


def positive_adversarial_check() -> list:
    issues = []
    # Empty 401 body and a typical /demo/health-shape 200 body — both
    # carry zero credential bytes for any synthetic value.
    body_401 = b""
    body_200 = b'{"status":"ok"}'
    for body in (body_401, body_200):
        hits = v._scan_body_for_credential_values(
            body, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if hits:
            issues.append(f"positive body unexpectedly matched credential value: {hits}")
        rhits = v._scan_bytes_for_forbidden_router(body)
        if rhits:
            issues.append(f"positive body unexpectedly matched router substring: {rhits}")
    return issues


# ---------------------------------------------------------------------------
# Negative fixtures
# ---------------------------------------------------------------------------


def write_negative_fixture(root: pathlib.Path, name: str, payload: dict):
    root.mkdir(parents=True, exist_ok=True)
    (root / "transcript.json").write_text(
        json.dumps({"name": name, **payload}, indent=2, sort_keys=True),
    )


def negative_inv001_recruiter_password_in_body():
    return (b'{"error":"recruiter password=' +
            PLACEHOLDER_REC_PASS.encode("utf-8") + b'"}')


def negative_inv002_recruiter_username_in_body():
    return (b'{"error":"recruiter user=' +
            PLACEHOLDER_REC_USER.encode("utf-8") + b'"}')


def negative_inv003_admin_password_in_body():
    return (b'{"error":"admin password=' +
            PLACEHOLDER_ADM_PASS.encode("utf-8") + b'"}')


def negative_inv004_admin_username_in_body():
    return (b'{"error":"admin user=' +
            PLACEHOLDER_ADM_USER.encode("utf-8") + b'"}')


def negative_inv006_header_carries_credential():
    return {
        "X-Echo-Credential": PLACEHOLDER_REC_PASS,
        "WWW-Authenticate": v.EXPECTED_WWW_AUTHENTICATE,
    }


def negative_inv008_body_with_router_substring():
    # Use the validator's own forbidden-substring list so the fixture is
    # always consistent with what the validator scans for.
    needle = v.FORBIDDEN_ROUTER_SUBSTRINGS[0].decode("ascii")
    return (b'{"error":"diagnostic:' + needle.encode("ascii") + b'"}')


def negative_inv009_uvicorn_log_with_password():
    return (
        b"INFO: Application startup complete.\n"
        b"DEBUG: recruiter password=" +
        PLACEHOLDER_REC_PASS.encode("utf-8") + b"\n"
    )


def negative_inv009_uvicorn_log_with_auth_b64():
    b64 = base64.b64encode(
        f"{PLACEHOLDER_REC_USER}:{PLACEHOLDER_REC_PASS}".encode("utf-8"),
    )
    return (
        b"INFO: Application startup complete.\n"
        b"DEBUG: Authorization header observed: Basic " + b64 + b"\n"
    )


def negative_adversarial_check(case_name: str, payload_artifact) -> list:
    """In-process predicate checks against the negative transcript."""
    issues: list = []
    if case_name in (
        "negative_inv001_recruiter_password_in_body",
        "negative_inv002_recruiter_username_in_body",
        "negative_inv003_admin_password_in_body",
        "negative_inv004_admin_username_in_body",
    ):
        body = payload_artifact
        hits = v._scan_body_for_credential_values(
            body, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if not hits:
            issues.append(f"predicate missed credential value in body for {case_name}")
    elif case_name == "negative_inv006_header_carries_credential":
        hits = v._scan_headers_for_credential_material(
            v._CIHeaders(list(payload_artifact.items())),
            PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if not hits:
            issues.append("predicate missed credential value in non-WWW-Authenticate header")
    elif case_name == "negative_inv008_body_with_router_substring":
        hits = v._scan_bytes_for_forbidden_router(payload_artifact)
        if not hits:
            issues.append("predicate missed router forbidden substring in body")
    elif case_name in (
        "negative_inv009_uvicorn_log_with_password",
        "negative_inv009_uvicorn_log_with_auth_b64",
    ):
        tmp = pathlib.Path(f"{case_name}_uvicorn.log").resolve()
        tmp.write_bytes(payload_artifact)
        try:
            checks, classification = v.scan_uvicorn_log(
                str(tmp), PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
                PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
            )
            if classification is None:
                issues.append("scan_uvicorn_log did not flag the leaking fixture")
        finally:
            tmp.unlink(missing_ok=True)
    return issues


def build_negative_cases(fixtures_root: pathlib.Path):
    inventory = [
        ("negative_inv001_recruiter_password_in_body", "INV-CL-001",
         negative_inv001_recruiter_password_in_body()),
        ("negative_inv002_recruiter_username_in_body", "INV-CL-002",
         negative_inv002_recruiter_username_in_body()),
        ("negative_inv003_admin_password_in_body", "INV-CL-003",
         negative_inv003_admin_password_in_body()),
        ("negative_inv004_admin_username_in_body", "INV-CL-004",
         negative_inv004_admin_username_in_body()),
        ("negative_inv006_header_carries_credential", "INV-CL-006",
         negative_inv006_header_carries_credential()),
        ("negative_inv008_body_with_router_substring", "INV-CL-008",
         negative_inv008_body_with_router_substring()),
        ("negative_inv009_uvicorn_log_with_password", "INV-CL-009",
         negative_inv009_uvicorn_log_with_password()),
        ("negative_inv009_uvicorn_log_with_auth_b64", "INV-CL-009",
         negative_inv009_uvicorn_log_with_auth_b64()),
    ]
    cases = []
    for name, inv, artifact in inventory:
        root = fixtures_root / name
        record = {"violated_invariant": inv}
        if isinstance(artifact, dict):
            record["headers_keys"] = sorted(artifact.keys())
        else:
            record["artifact_size_bytes"] = len(artifact)
        write_negative_fixture(root, name, record)
        cases.append({
            "case_name": name,
            "violated_invariant": inv,
            "root": root,
            "artifact": artifact,
        })
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = manifest_path.parent / "validate_b14_0_no_credential_leak"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    # Positive
    pos_root = fixtures_root / "positive_clean_no_leak_transcript"
    write_positive_fixture(pos_root)
    pos_issues = positive_adversarial_check()

    # Negatives
    negative_cases = build_negative_cases(fixtures_root)
    adversarial_failures = []
    negative_entries = []
    for case in negative_cases:
        issues = negative_adversarial_check(case["case_name"], case["artifact"])
        negative_entries.append({
            "case_name": case["case_name"],
            "root": str(case["root"]),
            "violated_invariant": case["violated_invariant"],
            "adversarial_predicate_issues": issues,
            "tree_files": hash_tree(case["root"]),
        })
        if issues:
            adversarial_failures.append(case["case_name"])

    positive_entry = {
        "case_name": "positive_clean_no_leak_transcript",
        "root": str(pos_root),
        "violated_invariant": None,
        "adversarial_predicate_issues": pos_issues,
        "tree_files": hash_tree(pos_root),
    }
    if pos_issues:
        adversarial_failures.append("positive_clean_no_leak_transcript")

    manifest = {
        "validator": "validate_b14_0_no_credential_leak",
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
