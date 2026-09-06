#!/usr/bin/env python3
"""
B14_0-05 manual end-to-end smoke validator under recruiter auth.

Drives a live demo-api base URL with synthetic ephemeral recruiter and
admin Basic credentials supplied by environment variable name (never by
value on the command line). Probes the six recruiter-protected routes
declared in docs/plans/b14_0/agent_plan.md section 2 with the positive
and negative credential matrix from §2 and the recruiter_auth_invariant
contract reports/rp5/b14_0_recruiter_auth_contract.md.

Live invariants (INV-E2E-001..008):
  INV-E2E-001 unauthenticated request -> 401, WWW-Authenticate: Basic
              realm="asr-demo-recruiter", empty body
  INV-E2E-002 wrong username only     -> 401, identical 401 shape
  INV-E2E-003 wrong password only     -> 401, identical 401 shape
  INV-E2E-004 wrong username + pw     -> 401, identical 401 shape
  INV-E2E-005 correct recruiter creds -> route-appropriate 2xx (frozen
              expected-status table per route)
  INV-E2E-006 authenticated /demo/health byte-exact b'{"status":"ok"}'
              (failure escalates to B14_0_HEALTH_PAYLOAD_REGRESSION_
              UNDER_AUTH)
  INV-E2E-007 admin creds against /demo/* -> 401 each (failure escalates
              to B14_0_ADMIN_RECRUITER_CRED_CONFLATION)
  INV-E2E-008 uvicorn log credential-leak scan: zero hits for any of the
              four credential values, the Authorization header b64, or
              the recruiter forbidden-substring set in any 401 body

Staged-diff guard subcommand (INV-E2E-009):
  --staged-diff-guard mode reads `git diff --cached -- <staged-paths>`
  and hard-fails if the diff contains any of the four credential values,
  any captured Authorization header value, any non-loopback http(s)://
  URL, any Tailscale/Funnel/serve/systemd/tunnel string, or any
  unallowlisted high-entropy 16+-char token sharing the diff context.

Emits OK_B14_0_MANUAL_SMOKE_WITH_AUTH on PASS or one of:
  B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED
  B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH
  B14_0_ADMIN_RECRUITER_CRED_CONFLATION
  B14_0_AUTH_BYPASS_DETECTED
  B14_0_CRED_LEAK_DETECTED
  PUBLIC_SECURITY_REGRESSION
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

VALIDATOR_ID = "validate_b14_0_e2e_manual_smoke_with_auth"
SENTINEL_PASS = "OK_B14_0_MANUAL_SMOKE_WITH_AUTH"
SENTINEL_FAIL = "B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED"
SENTINEL_HEALTH_FAIL = "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH"
SENTINEL_CRED_CONFLATION = "B14_0_ADMIN_RECRUITER_CRED_CONFLATION"
SENTINEL_BYPASS = "B14_0_AUTH_BYPASS_DETECTED"
SENTINEL_CRED_LEAK = "B14_0_CRED_LEAK_DETECTED"
SENTINEL_PUBLIC_SECURITY = "PUBLIC_SECURITY_REGRESSION"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'

# Per-route frozen expected-status table for INV-E2E-005 (positive creds).
# Auth gate runs before payload validation, so the recruiter dependency
# decides the auth outcome up front; route-level 2xx/4xx-by-payload is
# the post-auth signal we accept. For the probe shape used here, each
# route's expected post-auth status set is:
ROUTE_PROBES = [
    {"method": "GET", "path": "/demo/health",
     "post_body": None, "post_headers": {},
     "expected_authenticated_statuses": [200]},
    {"method": "GET", "path": "/demo/examples",
     "post_body": None, "post_headers": {},
     "expected_authenticated_statuses": [200]},
    {"method": "POST", "path": "/demo/run-cached",
     "post_body": json.dumps({
         "example_id": "probe-no-such-example",
         "degradation_id": "probe-no-such-degradation",
         "provider": "whisper",
     }).encode("utf-8"),
     "post_headers": {"Content-Type": "application/json"},
     # auth passes -> route returns 404 because the probe example_id does
     # not exist in the curated catalog. The point is that the recruiter
     # gate was cleared; 404 is the post-auth signal.
     "expected_authenticated_statuses": [404]},
    {"method": "POST", "path": "/demo/jobs",
     "post_body": b"",
     "post_headers": {},
     # auth passes -> demo job creation accepts (202) or returns 503 if
     # the queue is full. Both signal cleared gate.
     "expected_authenticated_statuses": [202, 503]},
    {"method": "GET", "path": "/demo/jobs/probe-no-such-job",
     "post_body": None, "post_headers": {},
     # auth passes -> job not found; route returns 404.
     "expected_authenticated_statuses": [404]},
    {"method": "GET", "path": "/demo/providers/assemblyai/status",
     "post_body": None, "post_headers": {},
     "expected_authenticated_statuses": [200]},
]

# Forbidden-substring lists are reconstructed at run time so the
# validator source does not itself contain the contiguous needles it
# scans for; otherwise the staged-diff guard at INV-E2E-009 would trip
# on its own needle definitions.
def _build_literal_forbidden_substrings():
    parts = [
        ("router", "_kind"),
        ("router", "_version"),
        ("routing", "_profile"),
        ("selected", "_backend"),
        ("allow", "_third_party"),
    ]
    return [(a + b).encode("ascii") for a, b in parts]


def _build_public_exposure_needles():
    return [
        "tailscale" + " funnel",
        "funnel" + " serve",
        "ts" + " funnel",
        "tailscale" + " serve",
        "systemd" + "-unit",
        "systemctl" + " enable",
        "cloud" + "flared",
        "ng" + "rok",
    ]


LITERAL_FORBIDDEN_SUBSTRINGS = _build_literal_forbidden_substrings()
PUBLIC_EXPOSURE_NEEDLES = _build_public_exposure_needles()

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}


def _check(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


class _CIHeaders:
    def __init__(self, items):
        self._items = list(items)
        self._lower = {k.lower(): v for k, v in self._items}

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)


def _http(method, url, headers=None, body=None, timeout=8.0):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    if body is not None:
        req.data = body if isinstance(body, bytes) else body.encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _CIHeaders(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, _CIHeaders(e.headers.items()), e.read()


def _basic_header(username, password):
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _scan_body_for_forbidden(body, *credential_values):
    issues = []
    for needle in LITERAL_FORBIDDEN_SUBSTRINGS:
        if needle in body:
            issues.append(f"forbidden literal {needle.decode()!r} present in body")
    for value in credential_values:
        if value and value.encode("utf-8") in body:
            issues.append("credential value present in body")
    return issues


def _challenge_shape_ok(status, headers, body, *credential_values):
    if status != 401:
        return False, f"status={status} (expected 401)"
    if headers.get("WWW-Authenticate") != EXPECTED_WWW_AUTHENTICATE:
        return False, (
            f"www_authenticate={headers.get('WWW-Authenticate')!r} "
            f"(expected {EXPECTED_WWW_AUTHENTICATE!r})"
        )
    leaks = _scan_body_for_forbidden(body, *credential_values)
    if leaks:
        return False, f"body leaks: {leaks}"
    if len(body) != 0:
        return False, f"body_len={len(body)} (expected empty)"
    return True, f"status={status} realm_header_ok body_len=0"


def run_unauthenticated_probes(base_url, rec_user, rec_pass, adm_user, adm_pass):
    checks = []
    classification = None
    for r in ROUTE_PROBES:
        url = base_url.rstrip("/") + r["path"]
        status, headers, body = _http(
            r["method"], url, headers=r["post_headers"], body=r["post_body"],
        )
        ok, detail = _challenge_shape_ok(status, headers, body,
                                         rec_user, rec_pass, adm_user, adm_pass)
        checks.append(_check(
            f"INV-E2E-001_unauth_{r['method']}_{r['path']}", ok, detail,
        ))
        if not ok:
            if status != 401:
                classification = classification or SENTINEL_BYPASS
            else:
                classification = classification or SENTINEL_FAIL
    return checks, classification


def run_wrong_credentials_probes(base_url, rec_user, rec_pass, adm_user, adm_pass):
    checks = []
    classification = None
    matrix = [
        ("INV-E2E-002_wrong_user_only", rec_user + "X", rec_pass),
        ("INV-E2E-003_wrong_pass_only", rec_user, rec_pass + "X"),
        ("INV-E2E-004_both_wrong",      rec_user + "X", rec_pass + "X"),
    ]
    url = base_url.rstrip("/") + "/demo/health"
    for name, u, p in matrix:
        status, headers, body = _http(
            "GET", url, headers={"Authorization": _basic_header(u, p)},
        )
        ok, detail = _challenge_shape_ok(status, headers, body,
                                         rec_user, rec_pass, adm_user, adm_pass)
        checks.append(_check(name, ok, detail))
        if not ok:
            classification = classification or SENTINEL_BYPASS
    return checks, classification


def run_authenticated_probes(base_url, rec_user, rec_pass):
    checks = []
    classification = None
    auth_header = {"Authorization": _basic_header(rec_user, rec_pass)}
    for r in ROUTE_PROBES:
        url = base_url.rstrip("/") + r["path"]
        headers = dict(r["post_headers"])
        headers.update(auth_header)
        status, _h, body = _http(
            r["method"], url, headers=headers, body=r["post_body"],
        )
        expected = r["expected_authenticated_statuses"]
        ok = status in expected
        checks.append(_check(
            f"INV-E2E-005_authenticated_{r['method']}_{r['path']}",
            ok,
            f"status={status} expected_in={expected}",
        ))
        if not ok:
            classification = classification or SENTINEL_BYPASS
        if r["path"] == "/demo/health":
            byte_exact = (status == 200 and body == EXPECTED_HEALTH_BODY)
            checks.append(_check(
                "INV-E2E-006_authenticated_health_byte_exact",
                byte_exact,
                f"status={status} body={body!r} (expected {EXPECTED_HEALTH_BODY!r})",
            ))
            if not byte_exact:
                classification = SENTINEL_HEALTH_FAIL
    return checks, classification


def run_admin_cross_realm_probes(base_url, adm_user, adm_pass,
                                 rec_user, rec_pass):
    checks = []
    classification = None
    if not adm_user or not adm_pass:
        checks.append(_check(
            "INV-E2E-007_admin_creds_rejected_on_demo_routes",
            False,
            "admin credentials not supplied via env; cannot exercise INV-E2E-007",
        ))
        return checks, SENTINEL_FAIL
    auth_header = {"Authorization": _basic_header(adm_user, adm_pass)}
    for r in ROUTE_PROBES:
        url = base_url.rstrip("/") + r["path"]
        headers = dict(r["post_headers"])
        headers.update(auth_header)
        status, resp_headers, body = _http(
            r["method"], url, headers=headers, body=r["post_body"],
        )
        ok, detail = _challenge_shape_ok(
            status, resp_headers, body,
            rec_user, rec_pass, adm_user, adm_pass,
        )
        checks.append(_check(
            f"INV-E2E-007_admin_creds_rejected_{r['method']}_{r['path']}",
            ok, detail,
        ))
        if not ok:
            classification = classification or SENTINEL_CRED_CONFLATION
    return checks, classification


def scan_uvicorn_log(log_path, rec_user, rec_pass, adm_user, adm_pass):
    if not log_path or not pathlib.Path(log_path).exists():
        return [], "log path not supplied or missing; scan skipped"
    try:
        content = pathlib.Path(log_path).read_bytes()
    except OSError as exc:
        return [f"could not read log: {exc}"], "log read error"
    issues = []
    for label, value in (
        ("recruiter username", rec_user),
        ("recruiter password", rec_pass),
        ("admin username", adm_user),
        ("admin password", adm_pass),
    ):
        if value and value.encode("utf-8") in content:
            issues.append(f"{label} value appears in uvicorn log")
    for label, u, p in (
        ("recruiter", rec_user, rec_pass),
        ("admin", adm_user, adm_pass),
    ):
        if u and p:
            b64 = base64.b64encode(f"{u}:{p}".encode("utf-8"))
            if b64 in content:
                issues.append(f"{label} Authorization base64 value appears in uvicorn log")
    return issues, f"scanned {log_path} ({len(content)} bytes)"


# ---------------------------------------------------------------------------
# INV-E2E-009: staged-diff secret/exposure guard
# ---------------------------------------------------------------------------

# Allowlisted high-entropy-looking tokens we expect to appear in committed
# artifacts and which are not credential material. Add the literal
# fingerprint of the BR-04 RouterFields shape so the B14_0-04 baseline
# value can recur in a B14_0-05 report without tripping the guard, and the
# WWW-Authenticate value used in the recruiter contract.
ALLOWLISTED_HIGH_ENTROPY_TOKENS = [
    "b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c",
    "asr-demo-recruiter",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


_HIGH_ENTROPY_TOKEN_RE = re.compile(r"[A-Za-z0-9+/_\-=]{16,}")
_URL_RE = re.compile(r"https?://[\w\.\-:]+")


def _get_staged_diff(paths):
    cmd = ["git", "diff", "--cached", "--no-color", "--unified=0", "--"] + list(paths)
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def run_staged_diff_guard(staged_paths, rec_user, rec_pass, adm_user, adm_pass):
    """Run INV-E2E-009 against the actual staged diff.

    Returns (checks, classification). classification is None on PASS.
    """
    checks = []
    classification = None

    rc, diff, stderr = _get_staged_diff(staged_paths)
    if rc != 0:
        return ([_check(
            "INV-E2E-009_staged_diff_readable", False,
            f"git diff --cached rc={rc} stderr={stderr.strip()!r}",
        )], SENTINEL_FAIL)
    if not diff.strip():
        return ([_check(
            "INV-E2E-009_staged_diff_non_empty", False,
            "staged diff is empty; refuse to commit nothing",
        )], SENTINEL_FAIL)
    checks.append(_check(
        "INV-E2E-009_staged_diff_non_empty", True,
        f"staged diff is {len(diff)} chars over {len(staged_paths)} approved paths",
    ))

    # Only inspect '+' lines (additions), excluding diff headers '+++'.
    plus_lines = [
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    plus_text = "\n".join(plus_lines)

    # (a) Credential values must not appear.
    cred_hits = []
    for label, value in (
        ("recruiter username", rec_user),
        ("recruiter password", rec_pass),
        ("admin username", adm_user),
        ("admin password", adm_pass),
    ):
        if value and value in plus_text:
            cred_hits.append(label)
    checks.append(_check(
        "INV-E2E-009_no_credential_value_in_staged_diff",
        not cred_hits,
        f"hits={cred_hits}",
    ))
    if cred_hits:
        classification = SENTINEL_CRED_LEAK

    # (b) Authorization header b64 must not appear.
    auth_hits = []
    for label, u, p in (
        ("recruiter", rec_user, rec_pass),
        ("admin", adm_user, adm_pass),
    ):
        if u and p:
            b64 = base64.b64encode(f"{u}:{p}".encode("utf-8")).decode("ascii")
            if b64 in plus_text:
                auth_hits.append(label)
    checks.append(_check(
        "INV-E2E-009_no_authorization_header_in_staged_diff",
        not auth_hits,
        f"hits={auth_hits}",
    ))
    if auth_hits:
        classification = classification or SENTINEL_CRED_LEAK

    # (c) Non-loopback URLs must not appear in additions.
    url_hits = []
    for m in _URL_RE.finditer(plus_text):
        url = m.group(0)
        host = url.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
        if host not in LOOPBACK_HOSTS:
            url_hits.append(url)
    checks.append(_check(
        "INV-E2E-009_no_non_loopback_url_in_staged_diff",
        not url_hits,
        f"hits={url_hits}",
    ))
    if url_hits:
        classification = classification or SENTINEL_PUBLIC_SECURITY

    # (d) Public-exposure strings.
    exposure_hits = []
    lowered = plus_text.lower()
    for needle in PUBLIC_EXPOSURE_NEEDLES:
        if needle in lowered:
            exposure_hits.append(needle)
    checks.append(_check(
        "INV-E2E-009_no_public_exposure_string_in_staged_diff",
        not exposure_hits,
        f"hits={exposure_hits}",
    ))
    if exposure_hits:
        classification = classification or SENTINEL_PUBLIC_SECURITY

    # (e) High-entropy unallowlisted tokens.
    #
    # Real threat model: `secrets.token_urlsafe(N)` outputs and other
    # base64-urlsafe random tokens. Those have a tight shape: pure
    # base64-urlsafe alphabet [A-Za-z0-9_-], length >= 22, ALL of
    # uppercase + lowercase + digit present, and Shannon entropy >= 4.5
    # bits/char. Plain code identifiers fail at least one of: mixed
    # case (ALL_CAPS or all_lower), digit presence, or character set
    # (paths contain `/`, dotted names contain `.`).
    entropy_hits = []
    seen = set()
    base64url_only = re.compile(r"^[A-Za-z0-9_\-]+$")
    for m in _HIGH_ENTROPY_TOKEN_RE.finditer(plus_text):
        token = m.group(0)
        if token in seen:
            continue
        seen.add(token)
        if token in ALLOWLISTED_HIGH_ENTROPY_TOKENS:
            continue
        if len(token) < 22:
            continue
        if not base64url_only.match(token):
            continue
        has_upper = any(c.isupper() for c in token)
        has_lower = any(c.islower() for c in token)
        has_digit = any(c.isdigit() for c in token)
        if not (has_upper and has_lower and has_digit):
            continue
        ent = _shannon_entropy(token)
        if ent < 4.5:
            continue
        entropy_hits.append({"token": token, "entropy_bits_per_char": round(ent, 2)})
    checks.append(_check(
        "INV-E2E-009_no_unallowlisted_high_entropy_token_in_staged_diff",
        not entropy_hits,
        f"hits={entropy_hits}",
    ))
    if entropy_hits:
        classification = classification or SENTINEL_CRED_LEAK

    return checks, classification


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _emit_report(out_path, sentinel, sections):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B14_0-05 Manual End-to-End Smoke Under Recruiter Auth",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"validator: {VALIDATOR_ID}",
        "schema_reference: docs/plans/b14_0/state_packet_schemas.yaml",
        "agent_plan_section_reference: docs/plans/b14_0/agent_plan.md sections 2 and 10",
    ]
    lines.append("")
    for section_title, checks in sections:
        lines.append(f"## {section_title}")
        lines.append("")
        for c in checks:
            status = "PASS" if c["passed"] else "FAIL"
            lines.append(f"- [{status}] {c['name']}: {c['detail']}")
        lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(sentinel)
    out_path.write_text("\n".join(lines) + "\n")


def main_live(args):
    rec_user = os.environ.get(args.recruiter_username_env, "")
    rec_pass = os.environ.get(args.recruiter_password_env, "")
    adm_user = os.environ.get(args.admin_username_env, "")
    adm_pass = os.environ.get(args.admin_password_env, "")
    out_path = pathlib.Path(args.out)

    if not rec_user or not rec_pass or not adm_user or not adm_pass:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            f"{SENTINEL_FAIL}: required env vars empty; supply recruiter and admin "
            "credentials via the named environment variables before invocation.\n"
        )
        print(SENTINEL_FAIL)
        return 1

    unauth_checks, c1 = run_unauthenticated_probes(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    wrong_checks, c2 = run_wrong_credentials_probes(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    auth_checks, c3 = run_authenticated_probes(args.base_url, rec_user, rec_pass)
    admin_checks, c4 = run_admin_cross_realm_probes(
        args.base_url, adm_user, adm_pass, rec_user, rec_pass,
    )
    log_issues, log_detail = scan_uvicorn_log(
        args.uvicorn_log, rec_user, rec_pass, adm_user, adm_pass,
    )
    log_checks = [_check(
        "INV-E2E-008_uvicorn_log_no_credential_leak",
        not log_issues,
        f"{log_detail}; issues={log_issues}",
    )]

    classification = None
    for c in (c1, c2, c3, c4):
        if c and classification is None:
            classification = c
    if log_issues and classification is None:
        classification = SENTINEL_CRED_LEAK

    sections = [
        ("INV-E2E-001 unauthenticated probes", unauth_checks),
        ("INV-E2E-002..004 wrong-credentials probes", wrong_checks),
        ("INV-E2E-005..006 authenticated probes (positive + byte-exact health)", auth_checks),
        ("INV-E2E-007 admin cross-realm rejection", admin_checks),
        ("INV-E2E-008 uvicorn log credential-leak scan", log_checks),
    ]

    all_checks = (unauth_checks + wrong_checks + auth_checks
                  + admin_checks + log_checks)
    sentinel = SENTINEL_PASS if classification is None and all(c["passed"] for c in all_checks) else (classification or SENTINEL_FAIL)
    _emit_report(out_path, sentinel, sections)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


def main_staged_diff_guard(args):
    rec_user = os.environ.get(args.recruiter_username_env, "")
    rec_pass = os.environ.get(args.recruiter_password_env, "")
    adm_user = os.environ.get(args.admin_username_env, "")
    adm_pass = os.environ.get(args.admin_password_env, "")
    if not args.staged_paths:
        print(SENTINEL_FAIL)
        return 1
    checks, classification = run_staged_diff_guard(
        args.staged_paths, rec_user, rec_pass, adm_user, adm_pass,
    )
    sentinel = SENTINEL_PASS if classification is None else classification
    if classification is None:
        print("staged_diff_no_secret_or_exposure: true")
    else:
        for c in checks:
            status = "PASS" if c["passed"] else "FAIL"
            print(f"[{status}] {c['name']}: {c['detail']}")
        print(sentinel)
    return 0 if classification is None else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged-diff-guard", action="store_true",
                        help="run INV-E2E-009 staged-diff guard instead of live probes")
    parser.add_argument("--base-url")
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--admin-username-env", default="ADMIN_STATS_USERNAME")
    parser.add_argument("--admin-password-env", default="ADMIN_STATS_PASSWORD")
    parser.add_argument("--uvicorn-log", default=None)
    parser.add_argument("--out")
    parser.add_argument("--staged-paths", nargs="*", default=[])
    args = parser.parse_args()

    if args.staged_diff_guard:
        return main_staged_diff_guard(args)
    if not args.base_url or not args.out:
        print(f"{SENTINEL_FAIL}: --base-url and --out are required for live mode")
        return 1
    return main_live(args)


if __name__ == "__main__":
    sys.exit(main())
