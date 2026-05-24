#!/usr/bin/env python3
"""
B14.2 OpenAPI / docs / redoc visibility validator under public exposure.

Under PUBLIC_DEMO_EXPOSURE=true the FastAPI app must NOT mount the
interactive docs surfaces. Asserts that GET /openapi.json, /docs, and
/redoc each return HTTP 404 (route unmounted).

Loopback-only enforcement: --base-url MUST start with http://127.0.0.1
or http://localhost.

Modes:
  Live HTTP (default; --base-url).
  Selftest (--selftest --fixtures DIR): walk fixture subdirs and apply
  invariants against recorded per-route observations.

Sentinels:
  OK_B14_2_OPENAPI_DOCS_OFF                on success
  B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED      on failure
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import urllib.error
import urllib.request


SENTINEL_PASS = "OK_B14_2_OPENAPI_DOCS_OFF"
SENTINEL_FAIL = "B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED"
EXPECTED_UNMOUNTED_STATUS = 404

DOCS_ROUTES: list[tuple[str, str]] = [
    ("openapi", "/openapi.json"),
    ("docs", "/docs"),
    ("redoc", "/redoc"),
]


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _http_get(url: str, timeout: float = 5.0) -> dict:
    req = urllib.request.Request(url, method="GET")
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
    return {"status": status, "body_len": len(body), "error": error}


def _collect_live(base_url: str) -> dict:
    observations = []
    for name, path in DOCS_ROUTES:
        url = base_url.rstrip("/") + path
        probe = _http_get(url)
        observations.append({
            "route_name": name,
            "path": path,
            "response": {
                "status": probe["status"],
                "body_len": probe["body_len"],
                "error": probe["error"],
            },
        })
    return {"case_name": "live", "observations": observations}


def _apply_invariants(record: dict) -> list[dict]:
    results: list[dict] = []
    observations = record.get("observations", [])
    expected_names = {n for n, _ in DOCS_ROUTES}
    observed_names = {o.get("route_name") for o in observations}
    missing = sorted(expected_names - observed_names)
    results.append(_check(
        "every_docs_route_observed",
        len(missing) == 0,
        f"missing routes: {missing}" if missing else
        f"all {len(expected_names)} docs routes observed",
    ))
    bad_mounted = []
    for obs in observations:
        r = obs.get("response") or {}
        if r.get("status") != EXPECTED_UNMOUNTED_STATUS:
            bad_mounted.append((obs.get("route_name"), obs.get("path"), r.get("status")))
    results.append(_check(
        "every_docs_route_returns_404_under_public_exposure_true",
        len(bad_mounted) == 0,
        f"routes returning non-404 (potentially mounted): {bad_mounted}"
        if bad_mounted else "every docs route returned 404 (unmounted)",
    ))
    return results


def _selftest_walk(fixtures_root: pathlib.Path) -> tuple[list, list]:
    pos, neg = [], []
    for kind, target in (("positive", pos), ("negative", neg)):
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
    return pos, neg


def write_report(out_path: pathlib.Path, mode: str, base_url: str | None,
                 results: list, sentinel: str,
                 selftest_summary: dict | None = None) -> None:
    lines = [
        "# B14.2 OpenAPI / Docs / Redoc Visibility Under Public Exposure",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"mode: {mode}",
        f"base_url: {base_url if base_url else 'n/a'}",
        "public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true",
        "expected_route_state: unmounted (HTTP 404)",
        f"checks: {len(results)}",
        f"failures: {sum(1 for r in results if not r['passed'])}",
        "",
        "## Routes Probed",
        "",
    ]
    for n, p in DOCS_ROUTES:
        lines.append(f"- {n}: {p}")
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
    record = _collect_live(args.base_url)
    results = _apply_invariants(record)
    sentinel = SENTINEL_PASS if all(r["passed"] for r in results) else SENTINEL_FAIL
    if args.out:
        write_report(pathlib.Path(args.out), "live", args.base_url, results, sentinel)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
