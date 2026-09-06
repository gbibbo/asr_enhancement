#!/usr/bin/env python3
"""
B14_0-03 admin-vs-recruiter auth-separation validator.

Drives a live demo-api base URL with two distinct env-var-supplied Basic
credential pairs (admin + recruiter) and validates the five separation
dimensions declared in state_packet_schemas.yaml
auth_separation_invariant_record (realm, username, password, route_prefix,
error_path), plus an env-only cred_separation attestation that the admin
and recruiter usernames and passwords are byte-distinct.

Credential handling contract:
  * Credential values are read from os.environ via the env-var NAMES passed
    on the command line. The CLI never accepts a value.
  * Credential bytes are never written into the report body, into stdout,
    or into any other artifact. Only env-var identifiers, observed status
    codes, public realm strings, and boolean attestations appear in output.
  * A self-scan rejects the report body if any credential byte sequence,
    Authorization header value, non-loopback URL, Tailscale/Funnel literal,
    or banned phrase is found before write.

Emits OK_B14_0_AUTH_SEPARATION on PASS or one of:
  B14_0_AUTH_BYPASS_DETECTED
  B14_0_ADMIN_RECRUITER_CRED_CONFLATION
"""
from __future__ import annotations

import argparse
import base64
import datetime
import os
import pathlib
import re
import secrets
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_0_AUTH_SEPARATION"
SENTINEL_BYPASS = "B14_0_AUTH_BYPASS_DETECTED"
SENTINEL_CONFLATION = "B14_0_ADMIN_RECRUITER_CRED_CONFLATION"

RECRUITER_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'

ALLOWED_COMPONENTS = {
    "realm", "username", "password", "route_prefix",
    "error_path", "cred_separation", "all",
}

BANNED_PHRASES = [
    "as needed", "as appropriate", "as required", "if already present",
    "if present", "where appropriate", "best practices", "obvious",
    "TBD", "TODO without a marker", "discovered", "discover ",
    "judgment", "free-form", "free form",
]
FORBIDDEN_FUTURE_SUBSTRINGS = [
    "tailscale funnel", "funnel serve", "ts funnel",
]


class _CIHeaders:
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


def _basic(u, p):
    return "Basic " + base64.b64encode(f"{u}:{p}".encode("utf-8")).decode("ascii")


def _check(name, dim, passed, detail):
    return {"name": name, "dimension": dim, "passed": passed, "detail": detail}


def probe_realm(base_url):
    out = []
    url_demo = base_url.rstrip("/") + "/demo/health"
    status, h, _ = _http("GET", url_demo)
    demo_realm = h.get("WWW-Authenticate")
    out.append(_check(
        "realm.demo_health_recruiter_realm", "realm",
        status == 401 and demo_realm == RECRUITER_REALM_HEADER,
        f"status={status} www_authenticate={demo_realm!r}",
    ))
    url_admin = base_url.rstrip("/") + "/admin/health"
    status, h, _ = _http("GET", url_admin)
    admin_realm = h.get("WWW-Authenticate")
    out.append(_check(
        "realm.admin_health_distinct_realm", "realm",
        status == 401 and admin_realm is not None and admin_realm != RECRUITER_REALM_HEADER,
        f"status={status} www_authenticate_present={admin_realm is not None} "
        f"distinct_from_recruiter={admin_realm != RECRUITER_REALM_HEADER}",
    ))
    return out


def probe_username_password(base_url, ru, rp, au, ap):
    out = []
    # username dim: admin creds rejected by recruiter surface, recruiter creds
    # rejected by admin surface
    status, h, _ = _http("GET", base_url.rstrip("/") + "/demo/health",
                         headers={"Authorization": _basic(au, ap)})
    out.append(_check(
        "username.admin_creds_rejected_at_demo", "username",
        status == 401 and h.get("WWW-Authenticate") == RECRUITER_REALM_HEADER,
        f"status={status} realm={h.get('WWW-Authenticate')!r}",
    ))
    status, h, _ = _http("GET", base_url.rstrip("/") + "/admin/health",
                         headers={"Authorization": _basic(ru, rp)})
    out.append(_check(
        "username.recruiter_creds_rejected_at_admin", "username",
        status == 401 and h.get("WWW-Authenticate") is not None
        and h.get("WWW-Authenticate") != RECRUITER_REALM_HEADER,
        f"status={status} realm={h.get('WWW-Authenticate')!r}",
    ))
    # password dim: swapped passwords rejected
    status, h, _ = _http("GET", base_url.rstrip("/") + "/demo/health",
                         headers={"Authorization": _basic(ru, ap)})
    out.append(_check(
        "password.recruiter_user_admin_pass_rejected", "password",
        status == 401 and h.get("WWW-Authenticate") == RECRUITER_REALM_HEADER,
        f"status={status} realm={h.get('WWW-Authenticate')!r}",
    ))
    status, h, _ = _http("GET", base_url.rstrip("/") + "/admin/health",
                         headers={"Authorization": _basic(au, rp)})
    out.append(_check(
        "password.admin_user_recruiter_pass_rejected", "password",
        status == 401 and h.get("WWW-Authenticate") is not None
        and h.get("WWW-Authenticate") != RECRUITER_REALM_HEADER,
        f"status={status} realm={h.get('WWW-Authenticate')!r}",
    ))
    return out


def probe_route_prefix():
    """Enumerate FastAPI app.routes and assert prefix separation."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from services.api.app.demo_main import app
    from services.api.app.recruiter_auth import recruiter_auth_dependency

    recruiter_paths = set()
    admin_paths = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if path is None:
            continue
        deps = getattr(route, "dependant", None)
        if deps is not None:
            for sub in getattr(deps, "dependencies", []) or []:
                call = getattr(sub, "call", None)
                if call is recruiter_auth_dependency:
                    recruiter_paths.add(path)
        if path.startswith("/admin/"):
            admin_paths.add(path)

    ok_recruiter_prefix = all(p.startswith("/demo/") for p in recruiter_paths)
    ok_admin_prefix = all(p.startswith("/admin/") for p in admin_paths)
    disjoint = recruiter_paths.isdisjoint(admin_paths)
    ok = ok_recruiter_prefix and ok_admin_prefix and disjoint and len(recruiter_paths) > 0 and len(admin_paths) > 0
    return [_check(
        "route_prefix.disjoint_under_correct_prefixes", "route_prefix",
        ok,
        f"recruiter_routes_under_demo={ok_recruiter_prefix} "
        f"admin_routes_under_admin={ok_admin_prefix} disjoint={disjoint} "
        f"recruiter_count={len(recruiter_paths)} admin_count={len(admin_paths)}",
    )]


def probe_error_path(base_url):
    _, _, demo_body = _http("GET", base_url.rstrip("/") + "/demo/health")
    _, _, admin_body = _http("GET", base_url.rstrip("/") + "/admin/health")
    distinct = demo_body != admin_body
    demo_empty = len(demo_body) == 0
    admin_non_empty = len(admin_body) > 0
    return [_check(
        "error_path.401_bodies_distinct", "error_path",
        distinct and demo_empty and admin_non_empty,
        f"demo_body_len={len(demo_body)} admin_body_len={len(admin_body)} "
        f"distinct={distinct}",
    )]


def cred_separation_env(ru, rp, au, ap):
    # secrets.compare_digest returns True iff bytes are equal. We want both pairs
    # to be unequal (compare_digest -> False). Only the booleans are emitted.
    same_user = secrets.compare_digest(au.encode("utf-8"), ru.encode("utf-8"))
    same_pass = secrets.compare_digest(ap.encode("utf-8"), rp.encode("utf-8"))
    return [_check(
        "cred_separation.usernames_distinct", "cred_separation",
        not same_user,
        f"admin_username_equals_recruiter_username={same_user}",
    ), _check(
        "cred_separation.passwords_distinct", "cred_separation",
        not same_pass,
        f"admin_password_equals_recruiter_password={same_pass}",
    )]


def scan_uvicorn_log(log_path, ru, rp, au, ap):
    if not log_path or not pathlib.Path(log_path).exists():
        return [], "log path not supplied or missing; scan skipped"
    content = pathlib.Path(log_path).read_bytes()
    issues = []
    for needle, label in [
        (rp.encode("utf-8"), "recruiter_password_value"),
        (ap.encode("utf-8"), "admin_password_value"),
        (base64.b64encode(f"{ru}:{rp}".encode("utf-8")), "recruiter_basic_b64"),
        (base64.b64encode(f"{au}:{ap}".encode("utf-8")), "admin_basic_b64"),
    ]:
        if needle and needle in content:
            issues.append(label)
    return issues, f"scanned {log_path} ({len(content)} bytes)"


def report_self_scan(report_text, credential_value_byte_set):
    issues = []
    lowered = report_text.lower()
    for phrase in BANNED_PHRASES:
        if phrase.lower() in lowered:
            issues.append(f"banned_phrase:{phrase!r}")
    for phrase in FORBIDDEN_FUTURE_SUBSTRINGS:
        if phrase.lower() in lowered:
            issues.append(f"forbidden_future_substring:{phrase!r}")
    if "Authorization:" in report_text or "authorization:" in lowered:
        issues.append("authorization_header_in_report")
    for match in re.findall(r"https?://[\w\.\-:]+", report_text):
        host = match.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
        if host not in ("127.0.0.1", "localhost", "0.0.0.0"):
            issues.append(f"non_loopback_url:{match!r}")
    body_bytes = report_text.encode("utf-8")
    for cred in credential_value_byte_set:
        if cred and cred in body_bytes:
            issues.append("credential_value_in_report")
            break
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--recruiter-username-env", required=True)
    parser.add_argument("--recruiter-password-env", required=True)
    parser.add_argument("--admin-username-env", required=True)
    parser.add_argument("--admin-password-env", required=True)
    parser.add_argument("--component", default="all")
    parser.add_argument("--uvicorn-log", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if args.component not in ALLOWED_COMPONENTS:
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(f"{SENTINEL_BYPASS}: unknown --component {args.component!r}\n")
        print(SENTINEL_BYPASS)
        return 1

    ru = os.environ.get(args.recruiter_username_env, "")
    rp = os.environ.get(args.recruiter_password_env, "")
    au = os.environ.get(args.admin_username_env, "")
    ap = os.environ.get(args.admin_password_env, "")
    if not (ru and rp and au and ap):
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            f"{SENTINEL_BYPASS}: validator invoked with at least one empty credential env var; "
            "supply non-empty values for both admin and recruiter pairs.\n"
        )
        print(SENTINEL_BYPASS)
        return 1

    checks = []
    classification = None

    def _run(component, fn):
        nonlocal classification
        results = fn()
        checks.extend(results)
        for c in results:
            if not c["passed"] and classification is None:
                if component == "cred_separation":
                    classification = SENTINEL_CONFLATION
                else:
                    classification = SENTINEL_BYPASS

    components = [args.component] if args.component != "all" else [
        "realm", "username", "password", "route_prefix", "error_path", "cred_separation",
    ]
    if "realm" in components:
        _run("realm", lambda: probe_realm(args.base_url))
    if "username" in components or "password" in components:
        _run("username", lambda: probe_username_password(args.base_url, ru, rp, au, ap))
    if "route_prefix" in components:
        _run("route_prefix", probe_route_prefix)
    if "error_path" in components:
        _run("error_path", lambda: probe_error_path(args.base_url))
    if "cred_separation" in components:
        _run("cred_separation", lambda: cred_separation_env(ru, rp, au, ap))

    log_issues, log_detail = scan_uvicorn_log(args.uvicorn_log, ru, rp, au, ap)
    checks.append(_check(
        "log.no_credential_leak", "log_scan",
        not log_issues,
        f"{log_detail}; issues={log_issues}",
    ))
    if log_issues and classification is None:
        classification = SENTINEL_BYPASS

    sentinel = SENTINEL_PASS if classification is None else classification
    cred_bytes_set = {ru.encode("utf-8"), rp.encode("utf-8"),
                      au.encode("utf-8"), ap.encode("utf-8")}

    lines = [
        "# B14_0-03 Admin vs Recruiter Auth Separation Invariants",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"base_url: {args.base_url}",
        f"component: {args.component}",
        f"recruiter_username_env: {args.recruiter_username_env}",
        f"recruiter_password_env: {args.recruiter_password_env}",
        f"admin_username_env: {args.admin_username_env}",
        f"admin_password_env: {args.admin_password_env}",
        f"check_count: {len(checks)}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        lines.append(f"- [{status}] {c['dimension']}: {c['name']}: {c['detail']}")

    lines += ["", "## Result", ""]
    if sentinel == SENTINEL_PASS:
        lines += [f"All {len(checks)} checks passed.", "", sentinel]
    else:
        failed = [c for c in checks if not c["passed"]]
        lines += [f"{len(failed)} check(s) failed:", ""]
        for c in failed:
            lines.append(f"  - {c['dimension']}: {c['name']}: {c['detail']}")
        lines += ["", sentinel]

    body = "\n".join(lines) + "\n"

    self_scan_issues = report_self_scan(body, cred_bytes_set)
    if self_scan_issues:
        body = (
            "# B14_0-03 Admin vs Recruiter Auth Separation Invariants\n\n"
            f"{SENTINEL_BYPASS}: self-scan rejected report body:\n"
            + "\n".join(f"  - {i}" for i in self_scan_issues)
            + "\n"
        )
        out_path = pathlib.Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body)
        print(SENTINEL_BYPASS)
        return 1

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
