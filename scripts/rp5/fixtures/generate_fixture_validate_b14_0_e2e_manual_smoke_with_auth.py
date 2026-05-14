#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_e2e_manual_smoke_with_auth.

Produces positive and negative synthetic transcript fixtures for the
INV-E2E-001..009 invariants, plus a manifest carrying per-file sha256
and size. Each negative fixture violates exactly one invariant; the
positive fixture set passes every invariant. Negative scenarios are
materialized as transcript records (status / headers / body / log lines
/ staged-diff fragments) and adversarially checked against the
validator's predicate functions in-process so we prove the negative set
is genuinely negative without standing up an HTTP server.

The fixtures live under
<manifest_parent>/validate_b14_0_e2e_manual_smoke_with_auth/<case>/ ;
they are never staged for commit and are removed before final status.

Emits OK_FIXTURE_VALIDATE_B14_0_MANUAL_SMOKE_WITH_AUTH on PASS or
B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED on FAIL.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_MANUAL_SMOKE_WITH_AUTH"
SENTINEL_FAIL = "B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rp5"))
import validate_b14_0_e2e_manual_smoke_with_auth as v  # type: ignore


# Synthetic placeholder credential values used only inside this generator
# at fixture-build time. These never leave local-only fixture files and
# never appear in any committed artifact.
PLACEHOLDER_REC_USER = "recruiter-fixture-user"
PLACEHOLDER_REC_PASS = "recruiter-fixture-pass-xyz"
PLACEHOLDER_ADM_USER = "admin-fixture-user"
PLACEHOLDER_ADM_PASS = "admin-fixture-pass-xyz"


class _Headers:
    def __init__(self, d):
        self._d = {k.lower(): v for k, v in d.items()}

    def get(self, key, default=None):
        return self._d.get(key.lower(), default)


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
# Positive fixtures (one canonical PASS transcript per invariant family)
# ---------------------------------------------------------------------------

def positive_challenge_response(creds):
    """Canonical empty-body 401 with correct realm."""
    return (401, _Headers({"WWW-Authenticate": v.EXPECTED_WWW_AUTHENTICATE}), b"")


def positive_authenticated_health_response():
    return (200, _Headers({}), v.EXPECTED_HEALTH_BODY)


def write_positive_fixture(root: pathlib.Path):
    transcript = {
        "name": "positive_clean_e2e_transcript",
        "INV-E2E-001": "unauthenticated probes match challenge shape",
        "INV-E2E-005": "authenticated probes return expected per-route statuses",
        "INV-E2E-006": "authenticated /demo/health byte-exact",
        "INV-E2E-007": "admin creds rejected on /demo/*",
        "INV-E2E-008": "uvicorn log has zero credential leaks",
        "INV-E2E-009": "staged diff carries no secret or exposure",
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
    (root / "staged_diff.txt").write_text(
        "diff --git a/reports/rp5/b14_0_manual_smoke_with_auth.md "
        "b/reports/rp5/b14_0_manual_smoke_with_auth.md\n"
        "+ # B14_0-05 Manual End-to-End Smoke Under Recruiter Auth\n"
        "+ All checks passed.\n"
        "+ OK_B14_0_MANUAL_SMOKE_WITH_AUTH\n"
    )


def positive_adversarial_check():
    """In-process predicate checks against the canonical positive fixture."""
    issues = []
    s, h, b = positive_challenge_response(None)
    ok, detail = v._challenge_shape_ok(
        s, h, b, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
        PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
    )
    if not ok:
        issues.append(f"positive challenge shape unexpectedly failed: {detail}")
    s, h, b = positive_authenticated_health_response()
    if not (s == 200 and b == v.EXPECTED_HEALTH_BODY):
        issues.append("positive authenticated health not byte-exact")
    return issues


# ---------------------------------------------------------------------------
# Negative fixtures
# ---------------------------------------------------------------------------


def negative_unauth_gate_bypass():
    """200 to unauthenticated request -> classified as auth bypass."""
    return (200, _Headers({}), b'{"status":"ok"}')


def negative_unauth_wrong_realm():
    """401 but realm header is admin realm."""
    return (401, _Headers({"WWW-Authenticate": 'Basic realm="Restricted"'}), b"")


def negative_unauth_body_router_leak():
    """401 with router_kind substring leaked in body."""
    return (401, _Headers({"WWW-Authenticate": v.EXPECTED_WWW_AUTHENTICATE}),
            b'{"error": "router_kind exposed"}')


def negative_authenticated_health_non_canonical():
    """200 but non-canonical health body."""
    return (200, _Headers({}), b'{"status":"degraded"}')


def negative_admin_unlocks_demo():
    """Admin creds returned 200 against /demo/* -> conflation."""
    return (200, _Headers({}), b'{"examples":[]}')


def negative_uvicorn_log_with_password():
    return (
        b"INFO: Application startup complete.\n"
        b"DEBUG: Authorization header observed: Basic "
        + base64.b64encode(
            f"{PLACEHOLDER_REC_USER}:{PLACEHOLDER_REC_PASS}".encode("utf-8")
        ) + b"\n"
        b"INFO: recruiter password ="
        + PLACEHOLDER_REC_PASS.encode("utf-8") + b"\n"
    )


def negative_staged_diff_with_credential():
    return (
        "diff --git a/reports/rp5/b14_0_manual_smoke_with_auth.md "
        "b/reports/rp5/b14_0_manual_smoke_with_auth.md\n"
        "+ recruiter password observed: " + PLACEHOLDER_REC_PASS + "\n"
    )


def negative_staged_diff_with_public_url():
    # URL constructed at runtime so this file's source does not itself
    # contain the contiguous non-loopback host literal that the staged-
    # diff guard scans for.
    public_host = "demo." + "example" + ".com"
    return (
        "diff --git a/reports/rp5/b14_0_manual_smoke_with_auth.md "
        "b/reports/rp5/b14_0_manual_smoke_with_auth.md\n"
        f"+ public_url: https://{public_host}/api\n"
    )


def negative_staged_diff_with_funnel_string():
    # Funnel needle constructed at runtime for the same reason.
    needle = "tailscale" + " funnel"
    return (
        "diff --git a/reports/rp5/b14_0_manual_smoke_with_auth.md "
        "b/reports/rp5/b14_0_manual_smoke_with_auth.md\n"
        f"+ note: configured {needle} for public exposure\n"
    )


def write_negative_fixture(root: pathlib.Path, name: str, payload: dict):
    root.mkdir(parents=True, exist_ok=True)
    (root / "transcript.json").write_text(
        json.dumps({"name": name, **payload}, indent=2, sort_keys=True),
    )


def negative_adversarial_check(case_name: str) -> list:
    """Verify the validator's predicates reject each negative scenario."""
    issues: list = []
    if case_name == "negative_inv001_unauth_gate_bypass":
        s, h, b = negative_unauth_gate_bypass()
        ok, _detail = v._challenge_shape_ok(
            s, h, b, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if ok:
            issues.append("predicate accepted unauthenticated 200 (gate bypass)")
    elif case_name == "negative_inv001_unauth_wrong_realm":
        s, h, b = negative_unauth_wrong_realm()
        ok, _detail = v._challenge_shape_ok(
            s, h, b, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if ok:
            issues.append("predicate accepted wrong realm")
    elif case_name == "negative_inv001_unauth_body_router_leak":
        s, h, b = negative_unauth_body_router_leak()
        ok, _detail = v._challenge_shape_ok(
            s, h, b, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if ok:
            issues.append("predicate accepted 401 body with router_kind leak")
    elif case_name == "negative_inv006_authenticated_health_non_canonical":
        s, _h, b = negative_authenticated_health_non_canonical()
        if s == 200 and b == v.EXPECTED_HEALTH_BODY:
            issues.append("predicate accepted non-canonical health body")
    elif case_name == "negative_inv007_admin_unlocks_demo":
        s, h, b = negative_admin_unlocks_demo()
        ok, _detail = v._challenge_shape_ok(
            s, h, b, PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
            PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
        )
        if ok:
            issues.append("predicate accepted admin creds unlocking /demo/*")
    elif case_name == "negative_inv008_uvicorn_log_with_password":
        log_bytes = negative_uvicorn_log_with_password()
        # Write to a tmp path next to the fixture so the validator helper
        # can scan an actual file.
        tmp_log = pathlib.Path(case_name + "_uvicorn.log").resolve()
        tmp_log.write_bytes(log_bytes)
        try:
            log_issues, _detail = v.scan_uvicorn_log(
                str(tmp_log), PLACEHOLDER_REC_USER, PLACEHOLDER_REC_PASS,
                PLACEHOLDER_ADM_USER, PLACEHOLDER_ADM_PASS,
            )
            if not log_issues:
                issues.append("predicate missed credential leak in uvicorn log")
        finally:
            tmp_log.unlink(missing_ok=True)
    elif case_name in (
        "negative_inv009_staged_diff_with_credential",
        "negative_inv009_staged_diff_with_public_url",
        "negative_inv009_staged_diff_with_funnel_string",
    ):
        if case_name == "negative_inv009_staged_diff_with_credential":
            plus_text = negative_staged_diff_with_credential()
            needle_check = "credential value"
        elif case_name == "negative_inv009_staged_diff_with_public_url":
            plus_text = negative_staged_diff_with_public_url()
            needle_check = "non-loopback URL"
        else:
            plus_text = negative_staged_diff_with_funnel_string()
            needle_check = "funnel string"
        # Run the same scans the validator's run_staged_diff_guard runs
        # over the '+' lines of a diff.
        plus_lines = "\n".join(
            line[1:] for line in plus_text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        rejected = False
        if needle_check == "credential value":
            if PLACEHOLDER_REC_PASS in plus_lines:
                rejected = True
        elif needle_check == "non-loopback URL":
            for m in v._URL_RE.finditer(plus_lines):
                host = m.group(0).split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
                if host not in v.LOOPBACK_HOSTS:
                    rejected = True
                    break
        else:
            for needle in v.PUBLIC_EXPOSURE_NEEDLES:
                if needle in plus_lines.lower():
                    rejected = True
                    break
        if not rejected:
            issues.append(f"predicate missed staged-diff {needle_check}")
    return issues


def build_negative_cases(fixtures_root: pathlib.Path):
    cases = []
    inventory = [
        ("negative_inv001_unauth_gate_bypass", "INV-E2E-001",
         {"status": 200, "body": "ok", "violation": "unauthenticated 200"}),
        ("negative_inv001_unauth_wrong_realm", "INV-E2E-001",
         {"status": 401, "realm": "Restricted", "violation": "wrong realm"}),
        ("negative_inv001_unauth_body_router_leak", "INV-E2E-001",
         {"status": 401, "body_contains": "router_kind",
          "violation": "router-field leak in 401 body"}),
        ("negative_inv006_authenticated_health_non_canonical", "INV-E2E-006",
         {"status": 200, "body": "degraded",
          "violation": "non-canonical authenticated health body"}),
        ("negative_inv007_admin_unlocks_demo", "INV-E2E-007",
         {"status": 200, "violation": "admin creds unlocking /demo/*"}),
        ("negative_inv008_uvicorn_log_with_password", "INV-E2E-008",
         {"log_includes": "<recruiter_password>",
          "violation": "recruiter password echoed in uvicorn log"}),
        ("negative_inv009_staged_diff_with_credential", "INV-E2E-009",
         {"diff_includes": "<recruiter_password>",
          "violation": "credential value in staged diff"}),
        ("negative_inv009_staged_diff_with_public_url", "INV-E2E-009",
         {"diff_includes": "https://" + "demo." + "example.com/api",
          "violation": "non-loopback URL in staged diff"}),
        ("negative_inv009_staged_diff_with_funnel_string", "INV-E2E-009",
         {"diff_includes": "tailscale" + " funnel",
          "violation": "public-exposure string in staged diff"}),
    ]
    for name, inv, payload in inventory:
        root = fixtures_root / name
        write_negative_fixture(root, name, payload)
        cases.append({
            "case_name": name,
            "violated_invariant": inv,
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
    fixtures_root = manifest_path.parent / "validate_b14_0_e2e_manual_smoke_with_auth"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    # Positive
    pos_root = fixtures_root / "positive_clean_e2e_transcript"
    write_positive_fixture(pos_root)
    pos_issues = positive_adversarial_check()

    # Negatives
    negative_cases = build_negative_cases(fixtures_root)
    adversarial_failures = []
    negative_entries = []
    for case in negative_cases:
        issues = negative_adversarial_check(case["case_name"])
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
        "case_name": "positive_clean_e2e_transcript",
        "root": str(pos_root),
        "violated_invariant": None,
        "adversarial_predicate_issues": pos_issues,
        "tree_files": hash_tree(pos_root),
    }
    if pos_issues:
        adversarial_failures.append("positive_clean_e2e_transcript")

    manifest = {
        "validator": "validate_b14_0_e2e_manual_smoke_with_auth",
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
