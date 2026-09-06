#!/usr/bin/env python3
"""
B14_1-02 no-network-trust-authority validator.

Asserts that no application-layer authority decision under PUBLIC_DEMO_EXPOSURE
=true is keyed on network origin (client IP, source interface, Tailscale
identity headers, X-Forwarded-For, X-Real-IP, X-Forwarded-Proto, or any other
header the public surface cannot independently authenticate).

Two stages:
  1) Live HTTP probes: unauthenticated GET /demo/health with each forbidden
     trust header spoofed individually. Each request MUST still return 401 +
     WWW-Authenticate: Basic realm="asr-demo-recruiter".
  2) Static inspection: scan the /demo/* authority surface
     (services/api/app/recruiter_auth.py, public_exposure.py, demo_main.py)
     for any occurrence of the forbidden tokens. Any occurrence FAILs.

Emits OK_B14_1_NO_NETWORK_TRUST_AUTHORITY on PASS or
B14_1_NETWORK_TRUST_AUTHORITY_DETECTED on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_1_NO_NETWORK_TRUST_AUTHORITY"
SENTINEL_FAIL = "B14_1_NETWORK_TRUST_AUTHORITY_DETECTED"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'

SPOOFED_HEADERS = [
    ("X-Forwarded-For", "127.0.0.1"),
    ("X-Forwarded-For", "10.0.0.1"),
    ("X-Real-IP", "10.0.0.1"),
    ("X-Forwarded-Proto", "https"),
    ("Tailscale-User-Login", "demo@example.invalid"),
    ("Tailscale-User-Name", "demo"),
    ("X-Tailscale-Identity", "ts-id-placeholder"),
]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUTH_SURFACE_FILES = [
    REPO_ROOT / "services" / "api" / "app" / "recruiter_auth.py",
    REPO_ROOT / "services" / "api" / "app" / "public_exposure.py",
    REPO_ROOT / "services" / "api" / "app" / "demo_main.py",
]

FORBIDDEN_TOKEN_PATTERNS = [
    re.compile(r"\bX-Forwarded-For\b", re.IGNORECASE),
    re.compile(r"\bX-Real-IP\b", re.IGNORECASE),
    re.compile(r"\bX-Forwarded-Proto\b", re.IGNORECASE),
    re.compile(r"\bREMOTE_ADDR\b"),
    re.compile(r"\bTailscale-User-Login\b", re.IGNORECASE),
    re.compile(r"\bTailscale-User-Name\b", re.IGNORECASE),
    re.compile(r"\bX-Tailscale-Identity\b", re.IGNORECASE),
    re.compile(r"\bTailscale-Identity\b", re.IGNORECASE),
    re.compile(r"request\.client\.host"),
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


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def run_live_header_probes(base_url):
    checks = []
    classification = None
    target = base_url.rstrip("/") + "/demo/health"
    for hname, hval in SPOOFED_HEADERS:
        status, h, _ = _http("GET", target, headers={hname: hval})
        ok = (status == 401
              and h.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE)
        checks.append(_check(
            f"unauth_trust_header_{hname}", ok,
            f"status={status} realm_header={h.get('WWW-Authenticate')!r}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL
    return checks, classification


def run_static_inspection():
    checks = []
    classification = None
    for f in AUTH_SURFACE_FILES:
        if not f.exists():
            checks.append(_check(
                f"static_inspect_{f.relative_to(REPO_ROOT)}_present", False,
                f"file not found: {f}",
            ))
            classification = classification or SENTINEL_FAIL
            continue
        text = f.read_text(encoding="utf-8")
        hits = []
        for pat in FORBIDDEN_TOKEN_PATTERNS:
            for m in pat.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                hits.append(f"{pat.pattern} at line {line_no}")
        ok = not hits
        checks.append(_check(
            f"static_inspect_{f.relative_to(REPO_ROOT)}", ok,
            f"forbidden_token_hits={hits if hits else 'none'}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL
    return checks, classification


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

    live_checks, live_class = run_live_header_probes(args.base_url)
    static_checks, static_class = run_static_inspection()
    all_checks = live_checks + static_checks
    classification = live_class or static_class

    lines = [
        "# B14_1-02 No Network-Trust Authority",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"base_url: {args.base_url}",
        f"spoofed_headers_tested: {len(SPOOFED_HEADERS)}",
        f"static_files_scanned: {len(AUTH_SURFACE_FILES)}",
        "",
        "## Checks",
        "",
    ]
    for c in all_checks:
        status = "PASS" if c["passed"] else "FAIL"
        lines.append(f"- [{status}] {c['name']}: {c['detail']}")

    if classification is None:
        sentinel = SENTINEL_PASS
        lines += ["", "## Result", "", "All checks passed.", "", SENTINEL_PASS]
    else:
        sentinel = classification
        failed = [c for c in all_checks if not c["passed"]]
        lines += ["", "## Result", "", f"{len(failed)} check(s) failed:", ""]
        for c in failed:
            lines.append(f"  - {c['name']}: {c['detail']}")
        lines += ["", sentinel]

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
