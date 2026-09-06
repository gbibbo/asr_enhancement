#!/usr/bin/env python3
"""
B14_1-03 OpenAPI / interactive-docs visibility validator.

Asserts the openapi_docs_visibility_record contract from
docs/plans/b14_1/state_packet_schemas.yaml under PUBLIC_DEMO_EXPOSURE=true:

  * /openapi.json MUST NOT be mounted_unprotected (route_state=unmounted
    or mounted_admin_only).
  * /docs MUST NOT be mounted_unprotected.
  * /redoc MUST NOT be mounted_unprotected.

Live HTTP probes against --base-url (loopback only). For each route the
validator records the observed unauthenticated status:

  * 404 -> route_state=unmounted (PASS).
  * 401 with WWW-Authenticate header AND a non-recruiter realm -> the route
    is admin-protected; route_state=mounted_admin_only (PASS, narrow
    admin-only exception).
  * 200 -> route_state=mounted_unprotected (FAIL).
  * any other status with a body that smells like an OpenAPI schema or
    interactive UI -> mounted_unprotected (FAIL).

This task does not enact the narrow admin-only exception; the default plan
is unmounted under PUBLIC_DEMO_EXPOSURE=true.

Emits OK_B14_1_OPENAPI_DOCS_OFF on PASS or
B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_1_OPENAPI_DOCS_OFF"
SENTINEL_FAIL = "B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED"

RECRUITER_REALM_HEADER = 'Basic realm="asr-demo-recruiter"'

PROBED_ROUTES = [
    ("openapi", "/openapi.json"),
    ("docs", "/docs"),
    ("redoc", "/redoc"),
]


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


def _classify_state(status, www_authenticate, body_bytes):
    if status == 404:
        return "unmounted", True, "status=404"
    if status == 401 and www_authenticate:
        if www_authenticate == RECRUITER_REALM_HEADER:
            return ("mounted_unprotected", False,
                    "status=401 but recruiter realm protects docs surface; "
                    "default plan requires unmounted")
        return ("mounted_admin_only", True,
                f"status=401 with non-recruiter realm {www_authenticate!r}")
    if status == 200:
        return ("mounted_unprotected", False,
                f"status=200 body_len={len(body_bytes) if body_bytes else 0}")
    snippet = (body_bytes[:200] if body_bytes else b"").lower()
    if (b"openapi" in snippet or b"swagger" in snippet
            or b"redoc" in snippet or b"<html" in snippet):
        return ("mounted_unprotected", False,
                f"status={status} body smells like docs surface")
    return "unmounted", True, f"status={status} (treated as unmounted)"


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def run_live_probes(base_url):
    checks = []
    classification = None
    states = {}

    for label, path in PROBED_ROUTES:
        url = base_url.rstrip("/") + path
        status, h, body = _http("GET", url)
        wa = h.get("WWW-Authenticate")
        state, ok, detail = _classify_state(status, wa, body)
        states[label] = state
        checks.append(_check(
            f"{label}_route_state_under_public_exposure", ok,
            f"path={path} state={state} {detail}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL

    return checks, classification, states


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
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

    checks, classification, states = run_live_probes(args.base_url)

    lines = [
        "# B14_1-03 OpenAPI / Interactive Docs Visibility",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"base_url: {args.base_url}",
        f"routes_probed: {len(PROBED_ROUTES)}",
        "",
        "## openapi_docs_visibility_record",
        "",
        "```yaml",
        "visibility_id: ODV-B14_1-03",
        "public_exposure_flag: PUBLIC_DEMO_EXPOSURE_true",
        f"openapi_route_state: {states.get('openapi', 'unknown')}",
        f"docs_route_state: {states.get('docs', 'unknown')}",
        f"redoc_route_state: {states.get('redoc', 'unknown')}",
        "narrow_admin_only_exception_path: not_enacted",
        "validator: validate_b14_1_openapi_docs_visibility",
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
        lines += ["", "## Result", "",
                  "All probed docs routes are unmounted or admin-only under "
                  "PUBLIC_DEMO_EXPOSURE=true.",
                  "", SENTINEL_PASS]
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
