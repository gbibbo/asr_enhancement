#!/usr/bin/env python3
"""
B14.2 application-layer recruiter HTTPBasic gate invariants validator.

Verifies on loopback only that every committed /demo/* route is gated by
the application-layer recruiter HTTPBasic dependency declared in
services/api/app/recruiter_auth.py (B14.0 contract):

  * an unauthenticated request returns HTTP 401;
  * the 401 response carries WWW-Authenticate exactly equal to
    'Basic realm="asr-demo-recruiter"';
  * the 401 response body is empty (canonical empty-body challenge);
  * a request supplying valid recruiter HTTPBasic credentials reaches
    the route's normal non-401 behaviour (any status code other than 401
    proves authentication succeeded — the validator does not inspect
    route-handler semantics beyond the auth boundary).

The validator runs in two modes:

  Live HTTP mode (default; --base-url):
    Performs loopback requests against a running uvicorn instance.
    Recruiter credentials are read from the validator's own environment
    (RECRUITER_USERNAME / RECRUITER_PASSWORD); credential values are
    never echoed, written to the report, or recorded in logs.

  Selftest mode (--selftest --fixtures DIR):
    Walks each fixture subdirectory and reads its observations.json
    file, asserting the same invariants declaratively against the
    recorded per-route observations. Used by the paired fixture
    generator scripts/rp5/fixtures/
    generate_fixture_validate_b14_2_application_layer_gate_invariants.py
    to confirm that positive fixtures emit
    OK_B14_2_APPLICATION_LAYER_GATE and negative fixtures emit
    B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED.

Sentinels:
  OK_B14_2_APPLICATION_LAYER_GATE          on success
  B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED   on any invariant failure

This validator runs no public-network command, binds no port, and
exposes no surface. Loopback (127.0.0.1) is the only network address
referenced.
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


SENTINEL_PASS = "OK_B14_2_APPLICATION_LAYER_GATE"
SENTINEL_FAIL = "B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED"
RECRUITER_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'

# Every committed /demo/* route. Parameterised paths use ephemeral
# fixture-only placeholders that never appear elsewhere in the repo and
# carry no operator semantics. The FastAPI dependency runs before any
# route-handler body parsing, so unauthenticated POSTs return 401
# without the validator needing to send a real payload.
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


def _basic_auth_header(username: str, password: str) -> str:
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _http_probe(base_url: str, method: str, path: str,
                headers: dict | None = None,
                timeout: float = 5.0) -> dict:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url=url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if method in ("POST", "PUT", "PATCH"):
        req.data = b""
        if "content-type" not in {h.lower() for h in (headers or {})}:
            req.add_header("Content-Type", "application/octet-stream")
    status = -1
    body = b""
    www_authenticate = ""
    error: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            # urllib HTTPMessage offers case-insensitive lookup.
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
    except Exception as exc:  # noqa: BLE001 — capture network-level errors
        error = f"{type(exc).__name__}: {exc}"
    return {
        "method": method,
        "path": path,
        "status": status,
        "www_authenticate": www_authenticate,
        "body_len": len(body),
        "error": error,
    }


def _collect_live_observations(base_url: str) -> dict:
    auth_header: dict[str, str] = {}
    creds_provided = False
    username = os.environ.get("RECRUITER_USERNAME", "")
    password = os.environ.get("RECRUITER_PASSWORD", "")
    if username and password:
        auth_header = {"Authorization": _basic_auth_header(username, password)}
        creds_provided = True

    observations = []
    for method, path in DEMO_ROUTES:
        unauth = _http_probe(base_url, method, path)
        creds = None
        if creds_provided:
            creds = _http_probe(base_url, method, path, headers=auth_header)
        observations.append({
            "method": method,
            "path": path,
            "unauth": {
                "status": unauth["status"],
                "www_authenticate": unauth["www_authenticate"],
                "body_len": unauth["body_len"],
                "error": unauth["error"],
            },
            "creds": (
                None if creds is None else {
                    "status": creds["status"],
                    "www_authenticate": creds["www_authenticate"],
                    "body_len": creds["body_len"],
                    "error": creds["error"],
                }
            ),
        })
    return {
        "case_name": "live",
        "credentialed_probe_attempted": creds_provided,
        "observations": observations,
    }


def _apply_invariants(record: dict) -> list[dict]:
    results: list[dict] = []
    observations = record.get("observations", [])

    observed_paths = {
        (obs.get("method"), obs.get("path")) for obs in observations
    }
    expected_paths = set(DEMO_ROUTES)
    missing_routes = sorted(expected_paths - observed_paths)
    results.append(_check(
        "every_committed_demo_route_observed",
        len(missing_routes) == 0,
        f"missing routes: {missing_routes}" if missing_routes else
        f"all {len(expected_paths)} committed /demo/* routes present in observations",
    ))

    bad_status = []
    for obs in observations:
        u = obs.get("unauth") or {}
        if u.get("status") != 401:
            bad_status.append((obs["method"], obs["path"], u.get("status")))
    results.append(_check(
        "every_demo_route_returns_401_to_unauthenticated_request",
        len(bad_status) == 0,
        f"non-401 unauth observations: {bad_status}" if bad_status else
        "every /demo/* unauthenticated probe returned 401",
    ))

    bad_realm = []
    for obs in observations:
        u = obs.get("unauth") or {}
        if u.get("www_authenticate", "") != EXPECTED_WWW_AUTHENTICATE:
            bad_realm.append((obs["method"], obs["path"], u.get("www_authenticate")))
    results.append(_check(
        "every_demo_401_carries_canonical_recruiter_www_authenticate",
        len(bad_realm) == 0,
        f"non-canonical WWW-Authenticate: {bad_realm}" if bad_realm else
        f'every 401 carried WWW-Authenticate=={EXPECTED_WWW_AUTHENTICATE!r}',
    ))

    bad_body = []
    for obs in observations:
        u = obs.get("unauth") or {}
        if u.get("body_len", 0) != 0:
            bad_body.append((obs["method"], obs["path"], u.get("body_len")))
    results.append(_check(
        "every_demo_401_body_is_empty",
        len(bad_body) == 0,
        f"non-empty 401 bodies: {bad_body}" if bad_body else
        "every 401 carried an empty body",
    ))

    if record.get("credentialed_probe_attempted", True):
        bad_creds = []
        for obs in observations:
            c = obs.get("creds")
            if c is None:
                bad_creds.append((obs["method"], obs["path"], "no_creds_probe"))
                continue
            if c.get("status") == 401:
                bad_creds.append((obs["method"], obs["path"], c.get("status")))
        results.append(_check(
            "credentialed_requests_reach_route_handler_non_401",
            len(bad_creds) == 0,
            f"credentialed probes still 401: {bad_creds}" if bad_creds else
            "every credentialed probe returned a non-401 status (auth boundary passed)",
        ))
    else:
        results.append(_check(
            "credentialed_requests_reach_route_handler_non_401",
            False,
            "RECRUITER_USERNAME / RECRUITER_PASSWORD not set; credentialed probe skipped",
        ))

    return results


def _load_fixture_record(case_dir: pathlib.Path) -> dict:
    obs_file = case_dir / "observations.json"
    if not obs_file.exists():
        return {"case_name": case_dir.name, "observations": [],
                "credentialed_probe_attempted": False,
                "_error": f"missing {obs_file}"}
    return json.loads(obs_file.read_text(encoding="utf-8"))


def _selftest_walk(fixtures_root: pathlib.Path) -> tuple[list[dict], list[dict]]:
    """Return (positive_results, negative_results) for selftest mode."""
    pos_cases = []
    neg_cases = []
    pos_root = fixtures_root / "positive"
    neg_root = fixtures_root / "negative"
    if pos_root.is_dir():
        for case in sorted(pos_root.iterdir()):
            if not case.is_dir():
                continue
            record = _load_fixture_record(case)
            results = _apply_invariants(record)
            pos_cases.append({
                "case_name": f"positive/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
        # also accept fixtures_root/positive/observations.json directly
        if (pos_root / "observations.json").exists() and not pos_cases:
            record = _load_fixture_record(pos_root)
            results = _apply_invariants(record)
            pos_cases.append({
                "case_name": "positive",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    if neg_root.is_dir():
        for case in sorted(neg_root.iterdir()):
            if not case.is_dir():
                continue
            record = _load_fixture_record(case)
            results = _apply_invariants(record)
            neg_cases.append({
                "case_name": f"negative/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    return pos_cases, neg_cases


def write_report(out_path: pathlib.Path, mode: str, base_url: str | None,
                 results: list[dict], sentinel: str,
                 selftest_summary: dict | None = None) -> None:
    lines = [
        "# B14.2 Application-Layer Recruiter HTTPBasic Gate Invariants",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"mode: {mode}",
        f"base_url: {base_url if base_url else 'n/a'}",
        f"recruiter_realm: {RECRUITER_REALM}",
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
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")
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
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--fixtures", default=None)
    args = parser.parse_args()

    if args.selftest:
        if args.fixtures is None:
            print(SENTINEL_FAIL)
            if args.out:
                pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                pathlib.Path(args.out).write_text(
                    f"{SENTINEL_FAIL}: --selftest requires --fixtures DIR\n"
                )
            return 1
        fixtures_root = pathlib.Path(args.fixtures)
        pos_cases, neg_cases = _selftest_walk(fixtures_root)
        # Positive cases must all pass invariants; negative cases must fail
        # at least one invariant (otherwise the fixture does not exercise
        # the negative-case predicate).
        pos_ok = all(case["all_passed"] for case in pos_cases) and len(pos_cases) > 0
        neg_ok = all(not case["all_passed"] for case in neg_cases) and len(neg_cases) > 0
        sentinel = SENTINEL_PASS if (pos_ok and neg_ok) else SENTINEL_FAIL
        flat_results = []
        for case in pos_cases:
            flat_results.append(_check(
                f"positive_case_{case['case_name']}_emits_PASS",
                case["all_passed"],
                "expected all invariants PASS; "
                + ("observed PASS" if case["all_passed"] else "observed at least one FAIL"),
            ))
        for case in neg_cases:
            flat_results.append(_check(
                f"negative_case_{case['case_name']}_emits_FAIL",
                not case["all_passed"],
                "expected at least one invariant FAIL; "
                + ("observed FAIL" if not case["all_passed"] else "observed all PASS (negative not exercising defect)"),
            ))
        if args.out:
            write_report(
                pathlib.Path(args.out), mode="selftest", base_url=None,
                results=flat_results, sentinel=sentinel,
                selftest_summary={"positive": pos_cases, "negative": neg_cases},
            )
        print(sentinel)
        return 0 if sentinel == SENTINEL_PASS else 1

    # Live HTTP mode
    record = _collect_live_observations(args.base_url)
    results = _apply_invariants(record)
    sentinel = SENTINEL_PASS if all(r["passed"] for r in results) else SENTINEL_FAIL
    if args.out:
        write_report(
            pathlib.Path(args.out), mode="live", base_url=args.base_url,
            results=results, sentinel=sentinel,
        )
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
