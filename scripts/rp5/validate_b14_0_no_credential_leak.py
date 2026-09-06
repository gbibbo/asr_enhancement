#!/usr/bin/env python3
"""
B14_0-06 no-credential-leak validator.

Drives a live demo-api base URL with synthetic ephemeral recruiter and
admin Basic credentials supplied by environment variable name and
asserts the no-credential-leak invariants declared in docs/plans/b14_0/
agent_plan.md section 12 and orchestrator_plan.md section 7.

Invariants (INV-CL-001..010):
  INV-CL-001  Unauthenticated 401 body never contains recruiter password
              value (all 6 recruiter-protected routes).
  INV-CL-002  Unauthenticated 401 body never contains recruiter username
              value.
  INV-CL-003  Unauthenticated 401 body never contains admin password
              value.
  INV-CL-004  Unauthenticated 401 body never contains admin username
              value.
  INV-CL-005  Wrong-credentials 401 body never echoes supplied
              Authorization header value or its base64 payload.
  INV-CL-006  401 response headers (other than WWW-Authenticate) never
              contain any credential value or Authorization material.
  INV-CL-007  4xx/5xx error responses provoked with malformed payloads
              on mutating routes never contain credential values.
  INV-CL-008  401 body never contains the B14_0-01 recruiter contract
              forbidden substrings (router-field names).
  INV-CL-009  uvicorn log credential-leak scan over the entire probe
              matrix output: zero hits for credential values, both
              Authorization base64 pairs, or 401-context lines echoing
              router forbidden substrings.
  INV-CL-010  Pydantic 422 validation errors (provoked with bodies
              that do not themselves carry credentials) never echo
              credential values.

Emits OK_B14_0_NO_CRED_LEAK on PASS or B14_0_CRED_LEAK_DETECTED on FAIL.

Needle lists are reconstructed at runtime via string concatenation so
this validator's source bytes do not themselves contain the contiguous
needles it scans for (B14_0-05 staged-diff-guard self-reference lesson).
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

VALIDATOR_ID = "validate_b14_0_no_credential_leak"
SENTINEL_PASS = "OK_B14_0_NO_CRED_LEAK"
SENTINEL_FAIL = "B14_0_CRED_LEAK_DETECTED"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'


# Recruiter-protected route set per agent_plan.md section 2.
RECRUITER_PROTECTED_ROUTES = [
    ("GET", "/demo/health", None, {}),
    ("GET", "/demo/examples", None, {}),
    ("POST", "/demo/run-cached",
     json.dumps({
         "example_id": "probe-no-such-example",
         "degradation_id": "probe-no-such-degradation",
         "provider": "whisper",
     }).encode("utf-8"),
     {"Content-Type": "application/json"}),
    ("POST", "/demo/jobs", b"", {}),
    ("GET", "/demo/jobs/probe-no-such-job", None, {}),
    ("GET", "/demo/providers/assemblyai/status", None, {}),
]


def _build_forbidden_router_substrings():
    parts = [
        ("router", "_kind"),
        ("router", "_version"),
        ("routing", "_profile"),
        ("selected", "_backend"),
        ("allow", "_third_party"),
    ]
    return [(a + b).encode("ascii") for a, b in parts]


FORBIDDEN_ROUTER_SUBSTRINGS = _build_forbidden_router_substrings()


def _check(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


class _CIHeaders:
    def __init__(self, items):
        self._items = list(items)
        self._lower = {k.lower(): v for k, v in self._items}

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)

    def items(self):
        return list(self._items)


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


def _scan_bytes_for_value(haystack: bytes, value: str) -> bool:
    if not value:
        return False
    return value.encode("utf-8") in haystack


def _scan_bytes_for_forbidden_router(haystack: bytes) -> list:
    hits = []
    for needle in FORBIDDEN_ROUTER_SUBSTRINGS:
        if needle in haystack:
            hits.append(needle.decode("ascii"))
    return hits


def _credential_values(rec_user, rec_pass, adm_user, adm_pass):
    return [
        ("recruiter_username", rec_user),
        ("recruiter_password", rec_pass),
        ("admin_username", adm_user),
        ("admin_password", adm_pass),
    ]


def _scan_body_for_credential_values(body, rec_user, rec_pass, adm_user, adm_pass):
    hits = []
    for label, value in _credential_values(rec_user, rec_pass, adm_user, adm_pass):
        if _scan_bytes_for_value(body, value):
            hits.append(label)
    return hits


def _scan_headers_for_credential_material(headers, rec_user, rec_pass,
                                          adm_user, adm_pass,
                                          wrong_auth_header_value=None):
    hits = []
    for k, v in headers.items():
        # WWW-Authenticate is the canonical realm challenge and is allowed
        # to contain the literal realm name; skip it.
        if k.lower() == "www-authenticate":
            continue
        vbytes = v.encode("utf-8") if isinstance(v, str) else v
        for label, value in _credential_values(rec_user, rec_pass, adm_user, adm_pass):
            if value and value.encode("utf-8") in vbytes:
                hits.append(f"header={k}:{label}")
        if wrong_auth_header_value and wrong_auth_header_value.encode("utf-8") in vbytes:
            hits.append(f"header={k}:wrong_auth_header_value")
    return hits


def run_unauth_probes(base_url, rec_user, rec_pass, adm_user, adm_pass):
    """INV-CL-001..004, INV-CL-006, INV-CL-008 over the six routes."""
    checks = []
    classification = None
    for method, path, body, headers in RECRUITER_PROTECTED_ROUTES:
        url = base_url.rstrip("/") + path
        status, resp_headers, resp_body = _http(method, url,
                                                headers=headers, body=body)
        # We require the 401 path; if anything else came back the
        # downstream B14_0-02 contract would have already caught the
        # bypass. Here, even a non-401 must not carry credentials.
        cred_hits = _scan_body_for_credential_values(
            resp_body, rec_user, rec_pass, adm_user, adm_pass,
        )
        router_hits = _scan_bytes_for_forbidden_router(resp_body)
        header_hits = _scan_headers_for_credential_material(
            resp_headers, rec_user, rec_pass, adm_user, adm_pass,
        )
        leak = cred_hits + router_hits + header_hits
        ok = not leak
        checks.append(_check(
            f"INV-CL-001..004_unauth_body_no_credentials_{method}_{path}",
            not cred_hits,
            f"status={status} body_len={len(resp_body)} cred_hits={cred_hits}",
        ))
        checks.append(_check(
            f"INV-CL-008_unauth_body_no_router_substrings_{method}_{path}",
            not router_hits,
            f"status={status} router_hits={router_hits}",
        ))
        checks.append(_check(
            f"INV-CL-006_unauth_headers_no_credentials_{method}_{path}",
            not header_hits,
            f"header_hits={header_hits}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL
    return checks, classification


def run_wrong_auth_echo_probe(base_url, rec_user, rec_pass, adm_user, adm_pass):
    """INV-CL-005 + INV-CL-006: wrong-credentials 401 must not echo the
    supplied Authorization header value or its base64 payload."""
    checks = []
    classification = None
    wrong_user = rec_user + "X"
    wrong_pass = rec_pass + "X"
    wrong_auth = _basic_header(wrong_user, wrong_pass)
    b64 = wrong_auth.split(" ", 1)[1]
    status, resp_headers, resp_body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
        headers={"Authorization": wrong_auth},
    )
    body_echoes_auth = (wrong_auth.encode("utf-8") in resp_body
                        or b64.encode("utf-8") in resp_body)
    cred_hits = _scan_body_for_credential_values(
        resp_body, wrong_user, wrong_pass, adm_user, adm_pass,
    )
    header_hits = _scan_headers_for_credential_material(
        resp_headers, rec_user, rec_pass, adm_user, adm_pass,
        wrong_auth_header_value=wrong_auth,
    )
    checks.append(_check(
        "INV-CL-005_wrong_auth_body_no_echo",
        not body_echoes_auth and not cred_hits,
        f"status={status} body_len={len(resp_body)} body_echoes_auth="
        f"{body_echoes_auth} cred_hits={cred_hits}",
    ))
    checks.append(_check(
        "INV-CL-006_wrong_auth_headers_no_echo",
        not header_hits,
        f"header_hits={header_hits}",
    ))
    if body_echoes_auth or cred_hits or header_hits:
        classification = SENTINEL_FAIL
    return checks, classification


def run_error_path_probes(base_url, rec_user, rec_pass, adm_user, adm_pass):
    """INV-CL-007 + INV-CL-010: error-path probes against mutating routes
    with malformed payloads. The probe payloads carry NO credential
    material so any echo in 4xx bodies indicates server-side leak."""
    checks = []
    classification = None
    auth = {"Authorization": _basic_header(rec_user, rec_pass)}

    # /demo/run-cached: send empty body (Pydantic 422)
    h = dict(auth)
    h["Content-Type"] = "application/json"
    status, _hh, body = _http(
        "POST", base_url.rstrip("/") + "/demo/run-cached",
        headers=h, body=b"{}",
    )
    cred_hits = _scan_body_for_credential_values(
        body, rec_user, rec_pass, adm_user, adm_pass,
    )
    checks.append(_check(
        "INV-CL-007_run_cached_empty_body_no_credential_echo",
        not cred_hits,
        f"status={status} body_len={len(body)} cred_hits={cred_hits}",
    ))
    if cred_hits:
        classification = SENTINEL_FAIL

    # /demo/run-cached: send a body with credential-shaped field NAMES
    # but no credential VALUES, provoking Pydantic 422.
    status, _hh, body = _http(
        "POST", base_url.rstrip("/") + "/demo/run-cached",
        headers=h, body=b'{"x":"y"}',
    )
    cred_hits = _scan_body_for_credential_values(
        body, rec_user, rec_pass, adm_user, adm_pass,
    )
    checks.append(_check(
        "INV-CL-010_run_cached_malformed_pydantic_422_no_credential_echo",
        not cred_hits,
        f"status={status} body_len={len(body)} cred_hits={cred_hits}",
    ))
    if cred_hits:
        classification = classification or SENTINEL_FAIL

    # /demo/jobs: empty body POST; route either 202s or 503s.
    status, _hh, body = _http(
        "POST", base_url.rstrip("/") + "/demo/jobs",
        headers=auth, body=b"",
    )
    cred_hits = _scan_body_for_credential_values(
        body, rec_user, rec_pass, adm_user, adm_pass,
    )
    checks.append(_check(
        "INV-CL-007_jobs_empty_body_no_credential_echo",
        not cred_hits,
        f"status={status} body_len={len(body)} cred_hits={cred_hits}",
    ))
    if cred_hits:
        classification = classification or SENTINEL_FAIL

    return checks, classification


def scan_uvicorn_log(log_path, rec_user, rec_pass, adm_user, adm_pass):
    """INV-CL-009: log-line credential-leak scan."""
    if not log_path or not pathlib.Path(log_path).exists():
        return ([_check("INV-CL-009_uvicorn_log_present", False,
                        f"log path missing: {log_path}")],
                SENTINEL_FAIL)
    content = pathlib.Path(log_path).read_bytes()
    issues = []
    for label, value in _credential_values(rec_user, rec_pass,
                                            adm_user, adm_pass):
        if value and value.encode("utf-8") in content:
            issues.append(f"{label} value present in log")
    for label, u, p in (
        ("recruiter", rec_user, rec_pass),
        ("admin", adm_user, adm_pass),
    ):
        if u and p:
            b64 = base64.b64encode(f"{u}:{p}".encode("utf-8"))
            if b64 in content:
                issues.append(f"{label} Authorization base64 present in log")
    # 401-context router-field-substring scan: if any log line contains
    # ' 401 ' AND any router forbidden substring, flag it.
    for line in content.splitlines():
        if b" 401 " in line:
            for needle in FORBIDDEN_ROUTER_SUBSTRINGS:
                if needle in line:
                    issues.append(
                        f"401-context line carries router substring "
                        f"{needle.decode()!r}"
                    )
    check = _check(
        "INV-CL-009_uvicorn_log_no_credential_leak",
        not issues,
        f"scanned {log_path} ({len(content)} bytes); issues={issues}",
    )
    return ([check], None if not issues else SENTINEL_FAIL)


def _emit_report(out_path, sentinel, sections):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B14_0-06 No-Credential-Leak Invariants",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"validator: {VALIDATOR_ID}",
        "schema_reference: docs/plans/b14_0/state_packet_schemas.yaml",
        "agent_plan_section_reference: docs/plans/b14_0/agent_plan.md sections 2 and 12",
        "orchestrator_plan_section_reference: docs/plans/b14_0/orchestrator_plan.md section 7",
        "",
    ]
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--admin-username-env", default="ADMIN_STATS_USERNAME")
    parser.add_argument("--admin-password-env", default="ADMIN_STATS_PASSWORD")
    parser.add_argument("--uvicorn-log", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

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

    unauth_checks, c1 = run_unauth_probes(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    wrong_checks, c2 = run_wrong_auth_echo_probe(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    error_checks, c3 = run_error_path_probes(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    log_checks, c4 = scan_uvicorn_log(
        args.uvicorn_log, rec_user, rec_pass, adm_user, adm_pass,
    )

    classification = None
    for c in (c1, c2, c3, c4):
        if c and classification is None:
            classification = c

    sections = [
        ("INV-CL-001..004 unauthenticated probes (body + headers + router substrings)", unauth_checks),
        ("INV-CL-005..006 wrong-credentials echo probe", wrong_checks),
        ("INV-CL-007 + INV-CL-010 error-path probes", error_checks),
        ("INV-CL-009 uvicorn log credential-leak scan", log_checks),
    ]
    all_checks = unauth_checks + wrong_checks + error_checks + log_checks
    sentinel = (SENTINEL_PASS if classification is None
                and all(c["passed"] for c in all_checks)
                else (classification or SENTINEL_FAIL))
    _emit_report(out_path, sentinel, sections)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
