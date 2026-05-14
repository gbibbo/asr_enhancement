#!/usr/bin/env python3
"""
B14_1-03 BR-02 health-payload preservation validator under public exposure.

Asserts byte-exact equality of the authenticated /demo/health body against
the canonical BR-02 payload b'{"status":"ok"}' when PUBLIC_DEMO_EXPOSURE=true.
The HTTP status MUST be 200; the body bytes MUST equal b'{"status":"ok"}'
with no surrounding whitespace, alternative spacing, or extra fields.

Loopback-only enforcement: --base-url must start with http://127.0.0.1 or
http://localhost.

Credential-handling contract:
  * Credentials are read from os.environ via env-var NAMES passed on the CLI.
  * Credential bytes are never written into the report body or stdout.

Emits OK_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE on PASS or
B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE on FAIL.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import os
import pathlib
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE"

EXPECTED_HEALTH_BODY = b'{"status":"ok"}'
EXPECTED_HEALTH_BODY_SHA256 = hashlib.sha256(EXPECTED_HEALTH_BODY).hexdigest()


class _CIHeaders:
    def __init__(self, items):
        self._items = list(items)
        self._lower = {k.lower(): v for k, v in self._items}

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)


def _http(method, url, headers=None, timeout=5.0):
    req = urllib.request.Request(url, method=method, headers=headers or {})
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

    auth_header = _basic_header(username, password)
    status, _h, resp_body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
        headers={"Authorization": auth_header},
    )

    status_ok = status == 200
    checks.append(_check(
        "authenticated_demo_health_status_200", status_ok,
        f"status={status}",
    ))
    if not status_ok:
        classification = classification or SENTINEL_FAIL

    body_byte_exact = resp_body == EXPECTED_HEALTH_BODY
    observed_sha = hashlib.sha256(resp_body).hexdigest() if resp_body is not None else "<none>"
    checks.append(_check(
        "authenticated_demo_health_body_byte_exact_canonical", body_byte_exact,
        f"observed_len={len(resp_body) if resp_body is not None else 0} "
        f"observed_sha256={observed_sha} "
        f"expected_sha256={EXPECTED_HEALTH_BODY_SHA256}",
    ))
    if not body_byte_exact:
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
        "# B14_1-03 BR-02 Health Payload Preserved Under Public Exposure",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"base_url: {args.base_url}",
        f"recruiter_username_env: {args.recruiter_username_env}",
        f"recruiter_password_env: {args.recruiter_password_env}",
        "",
        "## canonical_payload_record",
        "",
        "```yaml",
        "invariant_id: HPP-B14_1-03",
        "route: /demo/health",
        "required_status_when_authenticated: 200",
        'required_authenticated_health_payload: \'{"status":"ok"}\'',
        f"required_authenticated_health_payload_sha256: {EXPECTED_HEALTH_BODY_SHA256}",
        "validator: validate_b14_1_health_payload_preserved_under_public_exposure",
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
        lines += ["", "## Result", "", "Body byte-exact equality holds.", "", SENTINEL_PASS]
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
