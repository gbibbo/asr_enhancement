#!/usr/bin/env python3
"""
B14_1-03 recruiter-gate preservation validator under public exposure.

Asserts that the B14.0 recruiter HTTPBasic application-layer gate remains
preserved end-to-end when PUBLIC_DEMO_EXPOSURE=true:

  * Every recruiter-protected /demo/* route returns 401 +
    WWW-Authenticate: Basic realm="asr-demo-recruiter" when unauthenticated.
  * GET /demo/health with correct env-supplied recruiter credentials returns
    HTTP 200.
  * Admin/recruiter separation is preserved: probing /admin/health with
    recruiter credentials must NOT return 200 (admin realm is independent;
    recruiter credentials carry no admin authority).

Loopback-only enforcement: --base-url must start with http://127.0.0.1 or
http://localhost.

Credential-handling contract:
  * Credentials are read from os.environ via env-var NAMES passed on the CLI.
  * Credential bytes are never written into the report body or stdout.

Emits OK_B14_1_RECRUITER_GATE_PRESERVED on PASS or
B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE on FAIL.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import os
import pathlib
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_1_RECRUITER_GATE_PRESERVED"
SENTINEL_FAIL = "B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'

PROTECTED_DEMO_ROUTES = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("POST", "/demo/run-cached"),
    ("POST", "/demo/jobs"),
    ("GET", "/demo/jobs/probe-no-such-job"),
    ("GET", "/demo/providers/assemblyai/status"),
]


class _CIHeaders:
    def __init__(self, items):
        self._items = list(items)
        self._lower = {k.lower(): v for k, v in self._items}

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)


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


def run_live_probes(base_url, username, password):
    checks = []
    classification = None

    for method, path in PROTECTED_DEMO_ROUTES:
        url = base_url.rstrip("/") + path
        body = b"{}" if method == "POST" else None
        headers = {"Content-Type": "application/json"} if method == "POST" else {}
        status, h, _ = _http(method, url, headers=headers, body=body)
        ok = status == 401 and h.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE
        checks.append(_check(
            f"unauth_{method}_{path}_returns_401_with_canonical_realm", ok,
            f"status={status} realm_header={h.get('WWW-Authenticate')!r}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL

    auth_header = _basic_header(username, password)
    status, _h, _body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
        headers={"Authorization": auth_header},
    )
    ok = status == 200
    checks.append(_check(
        "authenticated_demo_health_returns_200", ok,
        f"status={status}",
    ))
    if not ok:
        classification = classification or SENTINEL_FAIL

    recruiter_into_admin = _basic_header(username, password)
    status, _h, _body = _http(
        "GET", base_url.rstrip("/") + "/admin/health",
        headers={"Authorization": recruiter_into_admin},
    )
    ok = status != 200
    checks.append(_check(
        "admin_health_with_recruiter_credentials_does_not_authorize", ok,
        f"status={status} (must not be 200)",
    ))
    if not ok:
        classification = classification or SENTINEL_FAIL

    return checks, classification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not args.base_url.startswith(("http://127.0.0.1", "http://localhost")):
        out_path.write_text(
            f"{SENTINEL_FAIL}: --base-url must be a loopback URL; got {args.base_url}\n"
        )
        print(SENTINEL_FAIL)
        return 1

    username = os.environ.get(args.recruiter_username_env, "")
    password = os.environ.get(args.recruiter_password_env, "")
    if not username or not password:
        out_path.write_text(
            f"{SENTINEL_FAIL}: env vars {args.recruiter_username_env} and "
            f"{args.recruiter_password_env} must be non-empty.\n"
        )
        print(SENTINEL_FAIL)
        return 1

    checks, classification = run_live_probes(args.base_url, username, password)

    lines = [
        "# B14_1-03 Recruiter Gate Preserved Under Public Exposure",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"base_url: {args.base_url}",
        f"recruiter_username_env: {args.recruiter_username_env}",
        f"recruiter_password_env: {args.recruiter_password_env}",
        f"protected_routes_probed: {len(PROTECTED_DEMO_ROUTES)}",
        "",
        "## application_layer_gate_invariant_record",
        "",
        "```yaml",
        "invariant_id: RGP-B14_1-03",
        "protected_route_glob: /demo/*",
        "required_status_when_unauthenticated: 401",
        'required_www_authenticate_value: \'Basic realm="asr-demo-recruiter"\'',
        'required_authenticated_health_payload: \'{"status":"ok"}\'',
        "forbidden_bypass_paths: []",
        "validator: validate_b14_1_recruiter_gate_preserved_under_public_exposure",
        f"marker: {SENTINEL_FAIL}",
        "```",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        status_label = "PASS" if c["passed"] else "FAIL"
        lines.append(f"- [{status_label}] {c['name']}: {c['detail']}")

    if classification is None:
        sentinel = SENTINEL_PASS
        lines += ["", "## Result", "", "All checks passed.", "", SENTINEL_PASS]
    else:
        sentinel = classification
        failed = [c for c in checks if not c["passed"]]
        lines += ["", "## Result", "", f"{len(failed)} check(s) failed:", ""]
        for c in failed:
            lines.append(f"  - {c['name']}: {c['detail']}")
        lines += ["", sentinel]

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
