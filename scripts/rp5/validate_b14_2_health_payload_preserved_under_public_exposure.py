#!/usr/bin/env python3
"""
B14.2 BR-02 health-payload preservation validator under public exposure.

Asserts byte-exact equality of the authenticated /demo/health body
against the canonical BR-02 payload b'{"status":"ok"}' when
PUBLIC_DEMO_EXPOSURE=true. The HTTP status MUST be 200; the body bytes
MUST equal b'{"status":"ok"}' with no surrounding whitespace,
alternative spacing, or extra fields.

Loopback-only enforcement: --base-url MUST start with http://127.0.0.1
or http://localhost. Credential values are read from process env via
--recruiter-username-env / --recruiter-password-env and are NEVER
written into the report or stdout.

Modes:
  Live HTTP (default; --base-url):
    Probe /demo/health authenticated with the recruiter credentials.
  Selftest (--selftest --fixtures DIR):
    Walk fixture subdirs and apply invariants declaratively.

Sentinels:
  OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE                       on success
  B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE       on failure
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request


SENTINEL_PASS = "OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE"
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'
EXPECTED_HEALTH_BODY_SHA256 = hashlib.sha256(EXPECTED_HEALTH_BODY).hexdigest()


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _basic_header(u: str, p: str) -> str:
    raw = f"{u}:{p}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _http_get(url: str, headers: dict | None = None,
              timeout: float = 5.0) -> dict:
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    status = -1
    body = b""
    error: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            body = exc.read()
        except Exception:  # noqa: BLE001
            body = b""
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    return {"status": status, "body_b64": base64.b64encode(body).decode("ascii"),
            "body_len": len(body), "error": error}


def _collect_live(base_url: str, username: str, password: str) -> dict:
    url = base_url.rstrip("/") + "/demo/health"
    auth_probe = _http_get(url, headers={"Authorization": _basic_header(username, password)})
    return {
        "case_name": "live",
        "authenticated_demo_health": auth_probe,
    }


def _apply_invariants(record: dict) -> list[dict]:
    results: list[dict] = []
    probe = record.get("authenticated_demo_health") or {}
    status = probe.get("status")
    body_b64 = probe.get("body_b64", "")
    try:
        body = base64.b64decode(body_b64) if body_b64 else b""
    except Exception:  # noqa: BLE001
        body = b""
    sha = hashlib.sha256(body).hexdigest()
    results.append(_check(
        "authenticated_demo_health_status_200",
        status == 200,
        f"observed_status={status}",
    ))
    results.append(_check(
        "authenticated_demo_health_body_byte_exact_canonical",
        body == EXPECTED_HEALTH_BODY,
        f"observed_len={len(body)} observed_sha256={sha} "
        f"expected_sha256={EXPECTED_HEALTH_BODY_SHA256}",
    ))
    return results


def _selftest_walk(fixtures_root: pathlib.Path) -> tuple[list, list]:
    pos_cases, neg_cases = [], []
    for kind, target in (("positive", pos_cases), ("negative", neg_cases)):
        root = fixtures_root / kind
        if not root.is_dir():
            continue
        for case in sorted(root.iterdir()):
            if not case.is_dir():
                continue
            obs = case / "observations.json"
            if not obs.exists():
                continue
            record = json.loads(obs.read_text(encoding="utf-8"))
            results = _apply_invariants(record)
            target.append({
                "case_name": f"{kind}/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    return pos_cases, neg_cases


def write_report(out_path: pathlib.Path, mode: str, base_url: str | None,
                 results: list, sentinel: str,
                 selftest_summary: dict | None = None,
                 observed_sha: str | None = None) -> None:
    lines = [
        "# B14.2 BR-02 Health Payload Preserved Under Public Exposure",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"mode: {mode}",
        f"base_url: {base_url if base_url else 'n/a'}",
        "public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true",
        f"expected_health_body_sha256: {EXPECTED_HEALTH_BODY_SHA256}",
        f"observed_health_body_sha256: {observed_sha if observed_sha else 'n/a'}",
        f"checks: {len(results)}",
        f"failures: {sum(1 for r in results if not r['passed'])}",
        "",
        "## Invariant Results",
        "",
    ]
    for r in results:
        lines.append(f"- [{'PASS' if r['passed'] else 'FAIL'}] {r['name']}: {r['detail']}")
    if selftest_summary is not None:
        lines += ["", "## Selftest Summary", ""]
        for case in selftest_summary.get("positive", []):
            ok = "PASS" if case["all_passed"] else "FAIL"
            lines.append(f"- [{ok}] {case['case_name']} (positive)")
        for case in selftest_summary.get("negative", []):
            ok = "PASS" if not case["all_passed"] else "FAIL"
            lines.append(f"- [{ok}] {case['case_name']} (negative; expected failure)")
    lines += ["", "## Sentinel", "", sentinel, ""]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--out", default=None)
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--fixtures", default=None)
    args = parser.parse_args()

    if args.selftest:
        if args.fixtures is None:
            print(SENTINEL_FAIL)
            return 1
        pos, neg = _selftest_walk(pathlib.Path(args.fixtures))
        pos_ok = bool(pos) and all(c["all_passed"] for c in pos)
        neg_ok = bool(neg) and all(not c["all_passed"] for c in neg)
        sentinel = SENTINEL_PASS if (pos_ok and neg_ok) else SENTINEL_FAIL
        flat = [_check(
            f"positive_case_{c['case_name']}_emits_PASS", c["all_passed"],
            "all invariants PASS" if c["all_passed"] else "at least one invariant FAIL",
        ) for c in pos] + [_check(
            f"negative_case_{c['case_name']}_emits_FAIL", not c["all_passed"],
            "at least one invariant FAIL (expected)" if not c["all_passed"]
            else "all invariants PASS (negative did not exercise defect)",
        ) for c in neg]
        if args.out:
            write_report(pathlib.Path(args.out), "selftest", None, flat, sentinel,
                         {"positive": pos, "negative": neg})
        print(sentinel)
        return 0 if sentinel == SENTINEL_PASS else 1

    if not args.base_url.startswith(("http://127.0.0.1", "http://localhost")):
        if args.out:
            pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(args.out).write_text(
                f"{SENTINEL_FAIL}: --base-url must be loopback; got {args.base_url}\n"
            )
        print(SENTINEL_FAIL)
        return 1
    username = os.environ.get(args.recruiter_username_env, "")
    password = os.environ.get(args.recruiter_password_env, "")
    if not username or not password:
        if args.out:
            pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(args.out).write_text(
                f"{SENTINEL_FAIL}: recruiter env vars must be non-empty.\n"
            )
        print(SENTINEL_FAIL)
        return 1

    record = _collect_live(args.base_url, username, password)
    results = _apply_invariants(record)
    sentinel = SENTINEL_PASS if all(r["passed"] for r in results) else SENTINEL_FAIL
    body_b64 = record.get("authenticated_demo_health", {}).get("body_b64", "")
    try:
        observed = hashlib.sha256(base64.b64decode(body_b64)).hexdigest() if body_b64 else None
    except Exception:  # noqa: BLE001
        observed = None
    if args.out:
        write_report(pathlib.Path(args.out), "live", args.base_url, results, sentinel,
                     observed_sha=observed)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
