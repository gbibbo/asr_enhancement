#!/usr/bin/env python3
"""
B14.2 B-route compatibility validator under public exposure.

Verifies that the FC-BROUTE-FROZEN and FC-B14-0-GATE-PRESERVED future
constraints remain intact under the repaired public-exposure surface:

  1. Frozen-fingerprint guard:
       * SHA-256 of libs/asr/router_runtime.py at HEAD equals the SHA-256
         of the same blob at the B14.0 phase-approval tracker-closure
         commit (FROZEN_ANCHOR_COMMIT).
       * Canonical RouterFields-shape fingerprint of
         services/frontend/app/demo/types.ts at HEAD equals the same
         fingerprint at FROZEN_ANCHOR_COMMIT.
       Both anchors are derived deterministically at runtime via
       `git cat-file`; no ambiguous SHA-256 literal is hardcoded.
  2. Loopback BR-02 health invariant re-emission:
       * unauthenticated GET /demo/health -> 401 + canonical recruiter
         realm.
       * recruiter-authenticated GET /demo/health -> 200 + byte-exact
         b'{"status":"ok"}'.

Loopback-only enforcement: --base-url MUST start with http://127.0.0.1
or http://localhost. Credential values are read from process env via
--recruiter-username-env / --recruiter-password-env and are NEVER
written into the report or stdout.

Modes:
  Live HTTP (default; --base-url): runs both evidence classes.
  Selftest (--selftest --fixtures DIR): walks fixture subdirs and
  applies invariants declaratively.

Sentinels:
  OK_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE      on success
  B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE            on failure
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request


SENTINEL_PASS = "OK_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

RECRUITER_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# B14.0 phase-approval tracker-closure commit, recorded in
# docs/progress/rp5_progress.yaml under
# phase_approvals.B14.0.accepted_tracker_closure_commit.
FROZEN_ANCHOR_COMMIT = "7730a4f53744eeb99d118f6f5b283c2f1c35dfc8"
ROUTER_RUNTIME_PATH = "libs/asr/router_runtime.py"
FRONTEND_TYPES_PATH = "services/frontend/app/demo/types.ts"
ROUTER_TYPE_BLOCK_NAMES = ["RouterDecisionView", "AssembledResponseView"]


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _git_blob(commit: str, path: str) -> bytes | None:
    res = subprocess.run(
        ["git", "cat-file", "-p", f"{commit}:{path}"],
        capture_output=True, cwd=str(REPO_ROOT),
    )
    if res.returncode != 0:
        return None
    return res.stdout


def _router_shape_fingerprint(types_ts_bytes: bytes) -> str:
    text = types_ts_bytes.decode("utf-8")
    parts = []
    rx_tmpl = r"export\s+type\s+{name}\s*=\s*\{{(?P<body>[^}}]*)\}}\s*;"
    for name in ROUTER_TYPE_BLOCK_NAMES:
        rx = re.compile(rx_tmpl.format(name=name), re.DOTALL)
        m = rx.search(text)
        if not m:
            parts.append(f"{name}:MISSING")
        else:
            canonical = [ln.strip() for ln in m.group("body").splitlines() if ln.strip()]
            parts.append(f"{name}:" + "\n".join(canonical))
    blob = ("\n----\n".join(parts)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def derive_anchors() -> tuple[str | None, str | None, str | None]:
    router_blob = _git_blob(FROZEN_ANCHOR_COMMIT, ROUTER_RUNTIME_PATH)
    if router_blob is None:
        return None, None, f"git cat-file failed for {FROZEN_ANCHOR_COMMIT}:{ROUTER_RUNTIME_PATH}"
    types_blob = _git_blob(FROZEN_ANCHOR_COMMIT, FRONTEND_TYPES_PATH)
    if types_blob is None:
        return None, None, f"git cat-file failed for {FROZEN_ANCHOR_COMMIT}:{FRONTEND_TYPES_PATH}"
    return (
        hashlib.sha256(router_blob).hexdigest(),
        _router_shape_fingerprint(types_blob),
        None,
    )


def _basic_header(u: str, p: str) -> str:
    raw = f"{u}:{p}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _http(method: str, url: str, headers: dict | None = None,
          timeout: float = 5.0) -> dict:
    req = urllib.request.Request(url, method=method, headers=headers or {})
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
    return {"status": status, "www_authenticate": www_authenticate,
            "body_b64": base64.b64encode(body).decode("ascii"),
            "body_len": len(body), "error": error}


def _collect_live(base_url: str, username: str, password: str) -> dict:
    health_url = base_url.rstrip("/") + "/demo/health"
    unauth = _http("GET", health_url)
    auth = _http("GET", health_url,
                 headers={"Authorization": _basic_header(username, password)})
    # HEAD fingerprints
    router_path = REPO_ROOT / ROUTER_RUNTIME_PATH
    types_path = REPO_ROOT / FRONTEND_TYPES_PATH
    head_router_sha = (hashlib.sha256(router_path.read_bytes()).hexdigest()
                       if router_path.exists() else "missing")
    head_types_sha = (_router_shape_fingerprint(types_path.read_bytes())
                      if types_path.exists() else "missing")
    return {
        "case_name": "live",
        "head_router_runtime_sha256": head_router_sha,
        "head_types_router_shape_sha256": head_types_sha,
        "health_probe": {
            "unauth_status": unauth["status"],
            "unauth_www_authenticate": unauth["www_authenticate"],
            "auth_status": auth["status"],
            "auth_body_b64": auth["body_b64"],
        },
    }


def _apply_invariants(record: dict, router_anchor: str | None,
                      types_anchor: str | None) -> list[dict]:
    results: list[dict] = []

    head_router = record.get("head_router_runtime_sha256")
    results.append(_check(
        "FROZEN_router_runtime_sha256_matches_anchor",
        router_anchor is not None and head_router == router_anchor,
        f"observed={head_router} anchor={router_anchor}",
    ))

    head_types = record.get("head_types_router_shape_sha256")
    results.append(_check(
        "FROZEN_router_fields_shape_fingerprint_matches_anchor",
        types_anchor is not None and head_types == types_anchor,
        f"observed={head_types} anchor={types_anchor}",
    ))

    probe = record.get("health_probe") or {}
    results.append(_check(
        "BR02_demo_health_unauthenticated_401_canonical_realm",
        probe.get("unauth_status") == 401
        and probe.get("unauth_www_authenticate") == EXPECTED_WWW_AUTHENTICATE,
        f"unauth_status={probe.get('unauth_status')} "
        f"realm={probe.get('unauth_www_authenticate')!r}",
    ))

    auth_body_b64 = probe.get("auth_body_b64", "")
    try:
        auth_body = base64.b64decode(auth_body_b64) if auth_body_b64 else b""
    except Exception:  # noqa: BLE001
        auth_body = b""
    results.append(_check(
        "BR02_demo_health_authenticated_byte_exact_under_public_exposure",
        probe.get("auth_status") == 200 and auth_body == EXPECTED_HEALTH_BODY,
        f"auth_status={probe.get('auth_status')} "
        f"auth_body_len={len(auth_body)} "
        f"expected_body_sha256={hashlib.sha256(EXPECTED_HEALTH_BODY).hexdigest()}",
    ))
    return results


def _selftest_walk(fixtures_root: pathlib.Path, router_anchor: str | None,
                   types_anchor: str | None) -> tuple[list, list]:
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
            results = _apply_invariants(record, router_anchor, types_anchor)
            target.append({
                "case_name": f"{kind}/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    return pos, neg


def write_report(out_path: pathlib.Path, mode: str, base_url: str | None,
                 router_anchor: str | None, types_anchor: str | None,
                 record: dict, results: list, sentinel: str,
                 selftest_summary: dict | None = None) -> None:
    lines = [
        "# B14.2 B-route Compatibility Under Public Exposure",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"mode: {mode}",
        f"base_url: {base_url if base_url else 'n/a'}",
        f"frozen_anchor_commit: {FROZEN_ANCHOR_COMMIT}",
        f"router_runtime_anchor_sha256: {router_anchor}",
        f"router_fields_shape_anchor_sha256: {types_anchor}",
        f"head_router_runtime_sha256: {record.get('head_router_runtime_sha256', 'n/a')}",
        f"head_router_fields_shape_sha256: {record.get('head_types_router_shape_sha256', 'n/a')}",
        f"public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true",
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

    router_anchor, types_anchor, err = derive_anchors()
    if err is not None:
        if args.out:
            pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(args.out).write_text(f"{SENTINEL_FAIL}: {err}\n")
        print(SENTINEL_FAIL)
        return 1

    if args.selftest:
        if args.fixtures is None:
            print(SENTINEL_FAIL)
            return 1
        pos, neg = _selftest_walk(pathlib.Path(args.fixtures), router_anchor, types_anchor)
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
            write_report(pathlib.Path(args.out), "selftest", None, router_anchor,
                         types_anchor, {}, flat, sentinel,
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
    results = _apply_invariants(record, router_anchor, types_anchor)
    sentinel = SENTINEL_PASS if all(r["passed"] for r in results) else SENTINEL_FAIL
    if args.out:
        write_report(pathlib.Path(args.out), "live", args.base_url,
                     router_anchor, types_anchor, record, results, sentinel)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
