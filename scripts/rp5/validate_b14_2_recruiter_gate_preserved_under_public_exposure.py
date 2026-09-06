#!/usr/bin/env python3
"""
B14.2 recruiter-gate-preserved-under-public-exposure invariants validator.

Re-emits the recruiter HTTPBasic gate invariant at loopback under
PUBLIC_DEMO_EXPOSURE=true, asserting that:

  * every committed /demo/* route returns 401 + canonical
    WWW-Authenticate 'Basic realm="asr-demo-recruiter"' + empty body
    to an unauthenticated request;
  * a request supplying recruiter HTTPBasic credentials reaches the
    route's normal non-401 behaviour.

Loopback-only enforcement: --base-url MUST start with
http://127.0.0.1 or http://localhost. Credential values are read from
the validator's own process env (RECRUITER_USERNAME / RECRUITER_PASSWORD
by default; both override-able via --recruiter-username-env /
--recruiter-password-env) and are NEVER written into the report or
stdout.

Modes:
  Live HTTP mode (default; --base-url):
    Live probe against a running uvicorn instance.
  Selftest mode (--selftest --fixtures DIR):
    Walks each fixture subdirectory and reads its observations.json,
    asserting invariants declaratively.

Sentinels:
  OK_B14_2_RECRUITER_GATE_PRESERVED                       on success
  B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE   on failure
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


SENTINEL_PASS = "OK_B14_2_RECRUITER_GATE_PRESERVED"
SENTINEL_FAIL = "B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE"
RECRUITER_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'

# Mirror of the committed /demo/* route set in services/api/app/demo_main.py
# at HEAD post B14_2-02.
DEMO_ROUTES: list[tuple[str, str]] = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("GET", "/demo/examples/b14_2_fixture/audio/clean"),
    ("GET", "/demo/examples/b14_2_fixture/audio/degraded/b14_2_fixture_degradation"),
    ("POST", "/demo/jobs"),
    ("POST", "/demo/run-cached"),
    ("POST", "/demo/upload"),
    ("GET", "/demo/providers/assemblyai/status"),
    ("GET", "/demo/jobs/b14_2_fixture_job"),
    ("GET", "/demo/jobs/b14_2_fixture_job/result"),
]


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _basic_header(username: str, password: str) -> str:
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _http(method: str, url: str, headers: dict | None = None,
          timeout: float = 5.0) -> dict:
    req = urllib.request.Request(url=url, method=method, headers=headers or {})
    if method in ("POST", "PUT", "PATCH"):
        req.data = b""
        if "content-type" not in {h.lower() for h in (headers or {})}:
            req.add_header("Content-Type", "application/octet-stream")
    status = -1
    www_authenticate = ""
    body = b""
    error: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            www_authenticate = resp.headers.get("WWW-Authenticate", "") or ""
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        if exc.headers is not None:
            www_authenticate = exc.headers.get("WWW-Authenticate", "") or ""
        try:
            body = exc.read()
        except Exception:  # noqa: BLE001
            body = b""
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    return {
        "status": status,
        "www_authenticate": www_authenticate,
        "body_len": len(body),
        "error": error,
    }


def _collect_live(base_url: str, username: str, password: str) -> dict:
    auth_header = {"Authorization": _basic_header(username, password)}
    observations = []
    for method, path in DEMO_ROUTES:
        url = base_url.rstrip("/") + path
        unauth = _http(method, url)
        creds = _http(method, url, headers=auth_header)
        observations.append({
            "method": method,
            "path": path,
            "unauth": {
                "status": unauth["status"],
                "www_authenticate": unauth["www_authenticate"],
                "body_len": unauth["body_len"],
                "error": unauth["error"],
            },
            "creds": {
                "status": creds["status"],
                "www_authenticate": creds["www_authenticate"],
                "body_len": creds["body_len"],
                "error": creds["error"],
            },
        })
    return {
        "case_name": "live",
        "credentialed_probe_attempted": True,
        "observations": observations,
    }


def _apply_invariants(record: dict) -> list[dict]:
    results: list[dict] = []
    observations = record.get("observations", [])
    expected_paths = set(DEMO_ROUTES)
    observed_paths = {(o.get("method"), o.get("path")) for o in observations}
    missing = sorted(expected_paths - observed_paths)
    results.append(_check(
        "every_committed_demo_route_observed",
        len(missing) == 0,
        f"missing routes: {missing}" if missing else
        f"all {len(expected_paths)} committed /demo/* routes present",
    ))

    bad_status = []
    bad_realm = []
    bad_body = []
    bad_creds = []
    for obs in observations:
        u = obs.get("unauth") or {}
        if u.get("status") != 401:
            bad_status.append((obs["method"], obs["path"], u.get("status")))
        if u.get("www_authenticate", "") != EXPECTED_WWW_AUTHENTICATE:
            bad_realm.append((obs["method"], obs["path"], u.get("www_authenticate")))
        if u.get("body_len", 0) != 0:
            bad_body.append((obs["method"], obs["path"], u.get("body_len")))
        c = obs.get("creds")
        if c is not None and c.get("status") == 401:
            bad_creds.append((obs["method"], obs["path"], c.get("status")))

    results.append(_check(
        "every_demo_route_returns_401_to_unauthenticated_request",
        len(bad_status) == 0,
        f"non-401 unauth: {bad_status}" if bad_status else
        "every /demo/* unauthenticated probe returned 401",
    ))
    results.append(_check(
        "every_demo_401_carries_canonical_recruiter_www_authenticate",
        len(bad_realm) == 0,
        f"non-canonical WWW-Authenticate: {bad_realm}" if bad_realm else
        f'every 401 carried WWW-Authenticate=={EXPECTED_WWW_AUTHENTICATE!r}',
    ))
    results.append(_check(
        "every_demo_401_body_is_empty",
        len(bad_body) == 0,
        f"non-empty 401 bodies: {bad_body}" if bad_body else
        "every 401 carried an empty body",
    ))
    if record.get("credentialed_probe_attempted", True):
        results.append(_check(
            "credentialed_requests_reach_route_handler_non_401",
            len(bad_creds) == 0,
            f"credentialed probes still 401: {bad_creds}" if bad_creds else
            "every credentialed probe returned non-401 (auth boundary passed)",
        ))
    else:
        results.append(_check(
            "credentialed_requests_reach_route_handler_non_401",
            False, "credentialed probe not attempted",
        ))
    return results


def _selftest_walk(fixtures_root: pathlib.Path) -> tuple[list, list]:
    pos_cases = []
    neg_cases = []
    for kind, target in (("positive", pos_cases), ("negative", neg_cases)):
        root = fixtures_root / kind
        if not root.is_dir():
            continue
        for case in sorted(root.iterdir()):
            if not case.is_dir():
                continue
            obs_file = case / "observations.json"
            if not obs_file.exists():
                continue
            record = json.loads(obs_file.read_text(encoding="utf-8"))
            results = _apply_invariants(record)
            target.append({
                "case_name": f"{kind}/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    return pos_cases, neg_cases


def write_report(out_path: pathlib.Path, mode: str, base_url: str | None,
                 results: list, sentinel: str,
                 selftest_summary: dict | None = None) -> None:
    lines = [
        "# B14.2 Recruiter Gate Preserved Under Public Exposure",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"mode: {mode}",
        f"base_url: {base_url if base_url else 'n/a'}",
        f"recruiter_realm: {RECRUITER_REALM}",
        "public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true",
        f"checks: {len(results)}",
        f"failures: {sum(1 for r in results if not r['passed'])}",
        "",
        "## Routes Probed",
        "",
    ]
    for m, p in DEMO_ROUTES:
        lines.append(f"- {m} {p}")
    lines += ["", "## Invariant Results", ""]
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
        pos_cases, neg_cases = _selftest_walk(pathlib.Path(args.fixtures))
        pos_ok = bool(pos_cases) and all(c["all_passed"] for c in pos_cases)
        neg_ok = bool(neg_cases) and all(not c["all_passed"] for c in neg_cases)
        sentinel = SENTINEL_PASS if (pos_ok and neg_ok) else SENTINEL_FAIL
        flat = [_check(
            f"positive_case_{c['case_name']}_emits_PASS", c["all_passed"],
            "all invariants PASS" if c["all_passed"] else "at least one invariant FAIL",
        ) for c in pos_cases] + [_check(
            f"negative_case_{c['case_name']}_emits_FAIL", not c["all_passed"],
            "at least one invariant FAIL (expected)" if not c["all_passed"]
            else "all invariants PASS (negative did not exercise defect)",
        ) for c in neg_cases]
        if args.out:
            write_report(pathlib.Path(args.out), "selftest", None, flat, sentinel,
                         {"positive": pos_cases, "negative": neg_cases})
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
                f"{SENTINEL_FAIL}: env vars {args.recruiter_username_env} and "
                f"{args.recruiter_password_env} must be non-empty.\n"
            )
        print(SENTINEL_FAIL)
        return 1

    record = _collect_live(args.base_url, username, password)
    results = _apply_invariants(record)
    sentinel = SENTINEL_PASS if all(r["passed"] for r in results) else SENTINEL_FAIL
    if args.out:
        write_report(pathlib.Path(args.out), "live", args.base_url, results, sentinel)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
