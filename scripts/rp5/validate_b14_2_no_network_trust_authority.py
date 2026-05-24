#!/usr/bin/env python3
"""
B14.2 no-network-trust-authority invariants validator.

Verifies on loopback only that no network-trust surrogate header
satisfies the recruiter HTTPBasic gate. The application-layer authority
must depend solely on the canonical Authorization Basic recruiter
credential pair; any forwarded-header or identity-claim header sent
without a valid Authorization header must still receive a 401
recruiter challenge.

Surrogate headers exercised:

  * X-Forwarded-For
  * X-Real-IP
  * X-Forwarded-Host
  * X-Forwarded-Proto
  * Tailscale-User-Login
  * Tailscale-User-Name
  * Tailscale-User-Profile-Pic
  * CF-Connecting-IP

The validator runs in two modes:

  Live HTTP mode (default; --base-url):
    Performs loopback requests against a running uvicorn instance,
    sending each surrogate header in isolation (no Authorization
    header) and asserting that the recruiter gate still rejects with
    a canonical 401 challenge.

  Selftest mode (--selftest --fixtures DIR):
    Walks each fixture subdirectory and reads its observations.json
    file, asserting the same invariants declaratively against the
    recorded per-route observations.

Sentinels:
  OK_B14_2_NO_NETWORK_TRUST_AUTHORITY            on success
  B14_2_NETWORK_TRUST_AUTHORITY_DETECTED         on any invariant failure

The validator runs no public-network command, binds no port, and
exposes no surface. Loopback (127.0.0.1) is the only network address
referenced. Credential values are never echoed or recorded.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import urllib.error
import urllib.request


SENTINEL_PASS = "OK_B14_2_NO_NETWORK_TRUST_AUTHORITY"
SENTINEL_FAIL = "B14_2_NETWORK_TRUST_AUTHORITY_DETECTED"
RECRUITER_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'

# Surrogate headers that must NOT be honoured as authority by the
# application-layer gate. Values are fixture-only tokens; the loopback
# placeholder 127.0.0.1 carries no operator semantics.
SURROGATE_HEADERS: dict[str, str] = {
    "X-Forwarded-For": "127.0.0.1",
    "X-Real-IP": "127.0.0.1",
    "X-Forwarded-Host": "loopback.invalid",
    "X-Forwarded-Proto": "https",
    "Tailscale-User-Login": "b14_2-fixture-user",
    "Tailscale-User-Name": "b14_2-fixture",
    "Tailscale-User-Profile-Pic": "http://127.0.0.1/none",
    "CF-Connecting-IP": "127.0.0.1",
}

# Subset of committed /demo/* routes used as the probe surface. The
# application-layer gate is identical across all /demo/* routes (see
# validate_b14_2_application_layer_gate_invariants), so a representative
# subset is sufficient to prove the no-network-trust invariant without
# producing a combinatorial output explosion.
PROBE_ROUTES: list[tuple[str, str]] = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("POST", "/demo/upload"),
    ("GET", "/demo/jobs/b14_2_fixture_job/result"),
]


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _http_probe(base_url: str, method: str, path: str,
                headers: dict[str, str],
                timeout: float = 5.0) -> dict:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url=url, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    if method in ("POST", "PUT", "PATCH"):
        req.data = b""
        lower = {h.lower() for h in headers}
        if "content-type" not in lower:
            req.add_header("Content-Type", "application/octet-stream")
    status = -1
    body = b""
    www_authenticate = ""
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
        "method": method,
        "path": path,
        "header_name": next(iter(headers)) if headers else None,
        "status": status,
        "www_authenticate": www_authenticate,
        "body_len": len(body),
        "error": error,
    }


def _collect_live_observations(base_url: str) -> dict:
    """Probe every (route, surrogate-header) pair in isolation (no auth)."""
    observations = []
    for header_name, header_value in SURROGATE_HEADERS.items():
        for method, path in PROBE_ROUTES:
            obs = _http_probe(
                base_url, method, path,
                headers={header_name: header_value},
            )
            observations.append({
                "method": method,
                "path": path,
                "surrogate_header_name": header_name,
                "response": {
                    "status": obs["status"],
                    "www_authenticate": obs["www_authenticate"],
                    "body_len": obs["body_len"],
                    "error": obs["error"],
                },
            })
    return {
        "case_name": "live",
        "surrogate_headers_exercised": sorted(SURROGATE_HEADERS),
        "observations": observations,
    }


def _apply_invariants(record: dict) -> list[dict]:
    results: list[dict] = []
    observations = record.get("observations", [])

    headers_seen = {obs.get("surrogate_header_name") for obs in observations}
    headers_seen.discard(None)
    missing_headers = sorted(set(SURROGATE_HEADERS) - headers_seen)
    results.append(_check(
        "every_required_surrogate_header_exercised",
        len(missing_headers) == 0,
        f"missing surrogate headers: {missing_headers}" if missing_headers else
        f"all {len(SURROGATE_HEADERS)} surrogate headers exercised",
    ))

    bad_status = []
    for obs in observations:
        r = obs.get("response") or {}
        if r.get("status") != 401:
            bad_status.append((
                obs.get("surrogate_header_name"),
                obs.get("method"),
                obs.get("path"),
                r.get("status"),
            ))
    results.append(_check(
        "surrogate_header_alone_does_not_satisfy_recruiter_gate",
        len(bad_status) == 0,
        f"surrogate-header probes producing non-401 status: {bad_status}"
        if bad_status else
        "every surrogate-header-only probe returned 401",
    ))

    bad_realm = []
    for obs in observations:
        r = obs.get("response") or {}
        if r.get("www_authenticate", "") != EXPECTED_WWW_AUTHENTICATE:
            bad_realm.append((
                obs.get("surrogate_header_name"),
                obs.get("method"),
                obs.get("path"),
                r.get("www_authenticate"),
            ))
    results.append(_check(
        "every_surrogate_header_401_carries_canonical_recruiter_www_authenticate",
        len(bad_realm) == 0,
        f"non-canonical WWW-Authenticate: {bad_realm}" if bad_realm else
        f'every surrogate-header 401 carried WWW-Authenticate=={EXPECTED_WWW_AUTHENTICATE!r}',
    ))

    bad_body = []
    for obs in observations:
        r = obs.get("response") or {}
        if r.get("body_len", 0) != 0:
            bad_body.append((
                obs.get("surrogate_header_name"),
                obs.get("method"),
                obs.get("path"),
                r.get("body_len"),
            ))
    results.append(_check(
        "every_surrogate_header_401_body_is_empty",
        len(bad_body) == 0,
        f"non-empty surrogate-header 401 bodies: {bad_body}"
        if bad_body else
        "every surrogate-header 401 carried an empty body",
    ))

    return results


def _load_fixture_record(case_dir: pathlib.Path) -> dict:
    obs_file = case_dir / "observations.json"
    if not obs_file.exists():
        return {"case_name": case_dir.name, "observations": [],
                "_error": f"missing {obs_file}"}
    return json.loads(obs_file.read_text(encoding="utf-8"))


def _selftest_walk(fixtures_root: pathlib.Path) -> tuple[list[dict], list[dict]]:
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
        "# B14.2 No-Network-Trust-Authority Invariants",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"mode: {mode}",
        f"base_url: {base_url if base_url else 'n/a'}",
        f"recruiter_realm: {RECRUITER_REALM}",
        f"checks: {len(results)}",
        f"failures: {sum(1 for r in results if not r['passed'])}",
        "",
        "## Surrogate Headers Exercised",
        "",
    ]
    for h in sorted(SURROGATE_HEADERS):
        lines.append(f"- {h}")
    lines += ["", "## Probe Routes", ""]
    for m, p in PROBE_ROUTES:
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
