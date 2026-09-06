#!/usr/bin/env python3
"""
B14_0-02 health-payload-under-auth validator.

Drives a live demo-api base URL with an env-var-supplied recruiter Basic
credential pair and validates the request-time fail-closed contract from
docs/plans/b14_0/agent_plan.md section 2 and reports/rp5/b14_0_recruiter_
auth_contract.md.

Probe matrix (live):
  * unauthenticated GET on each of the six protected routes -> 401 +
    WWW-Authenticate: Basic realm="asr-demo-recruiter" + forbidden-substring
    scan
  * wrong-credentials GET /demo/health -> 401 with same realm
  * malformed Authorization GET /demo/health -> 401 with same realm
  * correct-credentials GET /demo/health -> 200 with byte-exact body
    b'{"status":"ok"}' (BR-02 invariant preserved)

Embedded sub-check (in-process):
  * import services.api.app.recruiter_auth and call recruiter_auth_dependency
    with RECRUITER_USERNAME and RECRUITER_PASSWORD popped from os.environ;
    expect RecruiterAuthChallenge -> proves request-time fail-closed for the
    env-unset path without requiring a second uvicorn process

Internal log scan: if --uvicorn-log is supplied, scan the log for credential
value leaks (supplied username/password tokens, Authorization header
material).

Emits OK_B14_0_HEALTH_UNDER_AUTH on PASS or one of:
  B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH
  B14_0_AUTH_BYPASS_DETECTED
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import datetime
import os
import pathlib
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_0_HEALTH_UNDER_AUTH"
SENTINEL_HEALTH_FAIL = "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH"
SENTINEL_BYPASS = "B14_0_AUTH_BYPASS_DETECTED"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'

PROTECTED_ROUTES = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("POST", "/demo/run-cached"),
    ("POST", "/demo/jobs"),
    ("GET", "/demo/jobs/probe-no-such-job"),
    ("GET", "/demo/providers/assemblyai/status"),
]

LITERAL_FORBIDDEN_SUBSTRINGS = [
    b"router_kind",
    b"router_version",
    b"routing_profile",
    b"selected_backend",
    b"allow_third_party",
]


class _CIHeaders:
    """Minimal case-insensitive header container."""
    def __init__(self, items):
        self._items = list(items)
        self._lower = {k.lower(): v for k, v in self._items}
    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)
    def items(self):
        return list(self._items)


def _http(method, url, headers=None, body=None, timeout=5.0):
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


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def _scan_body_for_forbidden(body, supplied_password_bytes, supplied_admin_password_bytes):
    """Return list of issues found in a 401 challenge body."""
    issues = []
    for needle in LITERAL_FORBIDDEN_SUBSTRINGS:
        if needle in body:
            issues.append(f"forbidden literal substring {needle.decode()!r} present in body")
    if supplied_password_bytes and supplied_password_bytes in body:
        issues.append("recruiter password value present in body")
    if supplied_admin_password_bytes and supplied_admin_password_bytes in body:
        issues.append("admin password value present in body")
    return issues


def run_live_probes(base_url, username, password, admin_password_env_value):
    """Run the live probe matrix. Returns (checks, classification)."""
    checks = []
    classification = None  # None == PASS, else the failure sentinel
    pw_bytes = password.encode("utf-8") if password else b""
    admin_pw_bytes = (admin_password_env_value or "").encode("utf-8")

    # Unauthenticated probe on each protected route -> 401 + realm
    for method, path in PROTECTED_ROUTES:
        url = base_url.rstrip("/") + path
        body = b"{}" if method == "POST" else None
        headers = {"Content-Type": "application/json"} if method == "POST" else {}
        status_code, resp_headers, resp_body = _http(method, url, headers=headers, body=body)
        ok_status = status_code == 401
        ok_realm = resp_headers.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE
        leaks = _scan_body_for_forbidden(resp_body, pw_bytes, admin_pw_bytes)
        ok = ok_status and ok_realm and not leaks
        checks.append(_check(
            f"unauth_{method}_{path}",
            ok,
            f"status={status_code} realm_header={resp_headers.get('WWW-Authenticate')!r} "
            f"body_len={len(resp_body)} leaks={leaks}",
        ))
        if not ok:
            if not ok_status:
                classification = classification or SENTINEL_BYPASS
            elif leaks:
                classification = classification or SENTINEL_HEALTH_FAIL
            else:
                classification = classification or SENTINEL_BYPASS

    # Wrong-credentials probe on /demo/health
    wrong_header = _basic_header(username + "x", password + "x")
    status_code, resp_headers, resp_body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
        headers={"Authorization": wrong_header},
    )
    ok_wrong = (status_code == 401
                and resp_headers.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE
                and not _scan_body_for_forbidden(resp_body, pw_bytes, admin_pw_bytes))
    checks.append(_check(
        "wrong_creds_health_401",
        ok_wrong,
        f"status={status_code} realm_header={resp_headers.get('WWW-Authenticate')!r} "
        f"body_len={len(resp_body)}",
    ))
    if not ok_wrong:
        classification = classification or SENTINEL_BYPASS

    # Malformed Authorization probe on /demo/health (non-Basic scheme)
    status_code, resp_headers, resp_body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
        headers={"Authorization": "Bearer abc"},
    )
    ok_mal = (status_code == 401
              and resp_headers.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE)
    checks.append(_check(
        "malformed_auth_health_401",
        ok_mal,
        f"status={status_code} realm_header={resp_headers.get('WWW-Authenticate')!r}",
    ))
    if not ok_mal:
        classification = classification or SENTINEL_BYPASS

    # Correct-credentials probe on /demo/health -> 200 + byte-exact body
    correct_header = _basic_header(username, password)
    status_code, resp_headers, resp_body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
        headers={"Authorization": correct_header},
    )
    ok_auth_status = status_code == 200
    ok_byte_exact = resp_body == EXPECTED_HEALTH_BODY
    checks.append(_check(
        "authenticated_health_byte_exact",
        ok_auth_status and ok_byte_exact,
        f"status={status_code} body={resp_body!r} (expected {EXPECTED_HEALTH_BODY!r})",
    ))
    if not (ok_auth_status and ok_byte_exact):
        classification = classification or SENTINEL_HEALTH_FAIL

    return checks, classification


def run_embedded_env_unset_subcheck():
    """In-process sub-check: recruiter dependency must raise when env is unset."""
    saved_user = os.environ.pop("RECRUITER_USERNAME", None)
    saved_pass = os.environ.pop("RECRUITER_PASSWORD", None)
    try:
        # Import lazily so callers without the FastAPI app on PYTHONPATH can
        # still drive the live-only probes.
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
        from services.api.app.recruiter_auth import (
            RecruiterAuthChallenge,
            recruiter_auth_dependency,
            _reset_misconfig_log_state,
        )

        _reset_misconfig_log_state()

        class _StubRequest:
            headers: dict = {}

        try:
            asyncio.get_event_loop().run_until_complete(
                recruiter_auth_dependency(_StubRequest())
            )
        except RuntimeError:
            # No running loop; create a fresh one.
            asyncio.new_event_loop().run_until_complete(
                recruiter_auth_dependency(_StubRequest())
            )
        return False, "dependency did not raise RecruiterAuthChallenge with env unset"
    except Exception as exc:  # noqa: BLE001 — must surface any raise type for diagnosis
        from services.api.app.recruiter_auth import RecruiterAuthChallenge
        if isinstance(exc, RecruiterAuthChallenge):
            return True, "RecruiterAuthChallenge raised as expected with env unset"
        return False, f"unexpected exception type: {type(exc).__name__}: {exc!r}"
    finally:
        if saved_user is not None:
            os.environ["RECRUITER_USERNAME"] = saved_user
        if saved_pass is not None:
            os.environ["RECRUITER_PASSWORD"] = saved_pass


def scan_uvicorn_log(log_path, username_value, password_value, admin_password_value):
    if not log_path or not pathlib.Path(log_path).exists():
        return [], "log path not supplied or missing; scan skipped"
    try:
        content = pathlib.Path(log_path).read_bytes()
    except OSError as exc:
        return [f"could not read log: {exc}"], "log read error"
    issues = []
    if password_value and password_value.encode("utf-8") in content:
        issues.append("recruiter password value appears in uvicorn log")
    if admin_password_value and admin_password_value.encode("utf-8") in content:
        issues.append("admin password value appears in uvicorn log")
    # Authorization header value (Basic <b64>) heuristic: the b64 of user:pass
    if username_value and password_value:
        raw = f"{username_value}:{password_value}".encode("utf-8")
        b64 = base64.b64encode(raw)
        if b64 in content:
            issues.append("Authorization header base64 value appears in uvicorn log")
    return issues, f"scanned {log_path} ({len(content)} bytes)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--admin-password-env", default="ADMIN_STATS_PASSWORD")
    parser.add_argument("--uvicorn-log", default=None,
                        help="optional path to uvicorn stdout/stderr log for credential-leak scan")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    username = os.environ.get(args.recruiter_username_env, "")
    password = os.environ.get(args.recruiter_password_env, "")
    admin_password = os.environ.get(args.admin_password_env, "")
    if not username or not password:
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            f"{SENTINEL_BYPASS}: validator invoked with empty recruiter env vars; "
            "supply non-empty values to drive the authenticated probe.\n"
        )
        print(SENTINEL_BYPASS)
        return 1

    live_checks, classification = run_live_probes(
        args.base_url, username, password, admin_password,
    )

    sub_ok, sub_detail = run_embedded_env_unset_subcheck()
    live_checks.append(_check("env_unset_dependency_raises", sub_ok, sub_detail))
    if not sub_ok:
        classification = classification or SENTINEL_BYPASS

    log_issues, log_detail = scan_uvicorn_log(
        args.uvicorn_log, username, password, admin_password,
    )
    live_checks.append(_check(
        "uvicorn_log_no_credential_leak",
        not log_issues,
        f"{log_detail}; issues={log_issues}",
    ))
    if log_issues:
        classification = classification or SENTINEL_HEALTH_FAIL

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# B14_0-02 Health Payload Preserved Under Auth",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"base_url: {args.base_url}",
        f"recruiter_username_env: {args.recruiter_username_env}",
        f"recruiter_password_env: {args.recruiter_password_env}",
        f"protected_routes_probed: {len(PROTECTED_ROUTES)}",
        f"check_count: {len(live_checks)}",
        "",
        "## Checks",
        "",
    ]
    for c in live_checks:
        status = "PASS" if c["passed"] else "FAIL"
        lines.append(f"- [{status}] {c['name']}: {c['detail']}")

    if classification is None:
        sentinel = SENTINEL_PASS
        lines += ["", "## Result", "", "All checks passed.", "", SENTINEL_PASS]
    else:
        sentinel = classification
        failed = [c for c in live_checks if not c["passed"]]
        lines += ["", "## Result", "", f"{len(failed)} check(s) failed:", ""]
        for c in failed:
            lines.append(f"  - {c['name']}: {c['detail']}")
        lines += ["", sentinel]

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
