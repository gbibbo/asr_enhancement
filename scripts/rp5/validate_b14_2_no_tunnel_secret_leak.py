#!/usr/bin/env python3
"""
B14.2 no-tunnel-secret-leak validator.

Two evidence classes:

  1. Repository scan (default; --root):
       * Tailscale auth-key prefix shape: '\\btskey-[A-Za-z0-9_-]{8,}\\b'.
       * Cloudflare tunnel token shape: 'eyJ...' opaque JSON-blob token
         pattern attached to a 'cloudflared tunnel run --token' context.
       * Real-value-shaped recruiter/admin password literals are not
         scanned by this validator (covered by repository .env policy);
         it scans only the tunnel-secret family.
       * Synthetic protocol-identifier fixture trees under
         tests/rp5/fixtures/ are skipped (B14.2 fixtures encode
         non-real protocol tokens).
  2. Live response-header probe (--base-url; optional):
       * GET /demo/health unauthenticated MUST NOT include the
         Authorization request header reflected back into the response
         (the recruiter handler returns an empty body; no header echo).

Sentinels:
  OK_B14_2_NO_TUNNEL_SECRET_LEAK    on success
  B14_2_TUNNEL_SECRET_COMMITTED     on any hit
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys
import urllib.error
import urllib.request


SENTINEL_PASS = "OK_B14_2_NO_TUNNEL_SECRET_LEAK"
SENTINEL_FAIL = "B14_2_TUNNEL_SECRET_COMMITTED"

TAILSCALE_AUTHKEY_RE = re.compile(r"\btskey-[A-Za-z0-9_\-]{8,}\b")
# Cloudflare tunnel-run token shape: long opaque base64-y blob; we use
# a conservative "eyJ" JSON-header prefix followed by base64 chars, of
# at least 40 chars (real tokens are far longer; 40 keeps false positives
# low against typical eyJ JSON-y constants in source).
CLOUDFLARE_TOKEN_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]{37,}\.[A-Za-z0-9_\-]{8,}")

DEFAULT_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
DEFAULT_SKIP_FILE_RELS = {"tests/rp5/fixtures"}


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _mask(line: str, max_len: int = 80) -> str:
    line = line.strip().replace("\n", " ").replace("\r", " ")
    if len(line) <= max_len:
        return line
    return line[:max_len] + "..."


def _iter_repo_files(root: pathlib.Path, skip_rels: list[str]):
    skip_prefix = tuple(skip_rels)
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(rel == s or rel.startswith(s + "/") for s in skip_prefix):
            continue
        if any(part in DEFAULT_SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf",
                                 ".wav", ".mp3", ".ogg", ".flac", ".bin",
                                 ".zip", ".tar", ".gz", ".pyc"}:
            continue
        yield p


def scan_repo(root: pathlib.Path, skip_rels: list[str]) -> dict:
    tskey_hits = []
    cf_hits = []
    files_scanned = 0
    for p in _iter_repo_files(root, skip_rels):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        files_scanned += 1
        rel = p.relative_to(root).as_posix()
        for i, line in enumerate(text.splitlines(), start=1):
            if TAILSCALE_AUTHKEY_RE.search(line):
                tskey_hits.append((rel, i, _mask(line)))
            if CLOUDFLARE_TOKEN_RE.search(line):
                cf_hits.append((rel, i, _mask(line)))
    return {
        "files_scanned": files_scanned,
        "tailscale_authkey_hits": tskey_hits,
        "cloudflare_token_hits": cf_hits,
    }


def _http_get(url: str, headers: dict | None = None,
              timeout: float = 5.0) -> dict:
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    status = -1
    resp_headers_lower: dict[str, str] = {}
    body = b""
    error: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            for k, v in resp.headers.items():
                resp_headers_lower[k.lower()] = v
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        if exc.headers is not None:
            for k, v in exc.headers.items():
                resp_headers_lower[k.lower()] = v
        try:
            body = exc.read()
        except Exception:  # noqa: BLE001
            body = b""
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
    return {"status": status, "headers_lower": resp_headers_lower,
            "body_len": len(body), "error": error}


def _runtime_probe(base_url: str) -> list[dict]:
    """Check that the loopback /demo/health 401 challenge response does
    NOT echo Authorization, Cookie, X-Demo-Session-Id, or any tskey-/eyJ
    secret shape in any response header."""
    results = []
    url = base_url.rstrip("/") + "/demo/health"
    probe = _http_get(url, headers={"X-Probe-Marker": "b14_2_no_tunnel_secret"})
    headers = probe["headers_lower"]
    forbidden_headers = {"authorization", "cookie", "x-demo-session-id"}
    leaked = sorted(h for h in headers if h in forbidden_headers)
    results.append(_check(
        "loopback_response_does_not_echo_credentialed_request_headers",
        len(leaked) == 0,
        f"leaked headers: {leaked}" if leaked else
        "no credentialed request-header name echoed in the response",
    ))
    suspicious = []
    for h, v in headers.items():
        if TAILSCALE_AUTHKEY_RE.search(v):
            suspicious.append(("tskey", h))
        if CLOUDFLARE_TOKEN_RE.search(v):
            suspicious.append(("cf-token", h))
    results.append(_check(
        "no_tunnel_secret_shape_in_response_headers",
        len(suspicious) == 0,
        f"suspicious response-header values: {suspicious}" if suspicious else
        "no tunnel-secret-shaped value in any response header",
    ))
    return results


def _apply_repo_invariants(scan: dict) -> list[dict]:
    results = []
    results.append(_check(
        "no_tailscale_authkey_prefix_committed",
        len(scan["tailscale_authkey_hits"]) == 0,
        f"{len(scan['tailscale_authkey_hits'])} tskey- hit(s)"
        if scan["tailscale_authkey_hits"] else
        "no tskey- prefix observed",
    ))
    results.append(_check(
        "no_cloudflare_tunnel_token_shape_committed",
        len(scan["cloudflare_token_hits"]) == 0,
        f"{len(scan['cloudflare_token_hits'])} cloudflare-token shape hit(s)"
        if scan["cloudflare_token_hits"] else
        "no cloudflare tunnel token shape observed",
    ))
    return results


def write_report(out_path: pathlib.Path, root: pathlib.Path | None,
                 base_url: str | None, scan: dict, results: list,
                 sentinel: str,
                 selftest_summary: dict | None = None) -> None:
    lines = [
        "# B14.2 No Tunnel Secret Leak",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"root: {root if root else 'n/a'}",
        f"base_url: {base_url if base_url else 'n/a'}",
        f"files_scanned: {scan.get('files_scanned', 0)}",
        f"tailscale_authkey_hits: {len(scan.get('tailscale_authkey_hits', []))}",
        f"cloudflare_token_hits: {len(scan.get('cloudflare_token_hits', []))}",
        f"checks: {len(results)}",
        f"failures: {sum(1 for r in results if not r['passed'])}",
        "",
        "## Invariant Results",
        "",
    ]
    for r in results:
        lines.append(f"- [{'PASS' if r['passed'] else 'FAIL'}] {r['name']}: {r['detail']}")
    if scan.get("tailscale_authkey_hits"):
        lines += ["", "## Tailscale Auth-Key Hits (file:line — masked excerpt)", ""]
        for rel, i, excerpt in scan["tailscale_authkey_hits"]:
            lines.append(f"- {rel}:{i}: {excerpt}")
    if scan.get("cloudflare_token_hits"):
        lines += ["", "## Cloudflare Token Hits (file:line — masked excerpt)", ""]
        for rel, i, excerpt in scan["cloudflare_token_hits"]:
            lines.append(f"- {rel}:{i}: {excerpt}")
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


def _selftest_walk(fixtures_root: pathlib.Path) -> tuple[list, list]:
    pos, neg = [], []
    for kind, target in (("positive", pos), ("negative", neg)):
        root = fixtures_root / kind
        if not root.is_dir():
            continue
        for case in sorted(root.iterdir()):
            if not case.is_dir():
                continue
            mini = case / "repo"
            if not mini.is_dir():
                continue
            scan = scan_repo(mini, list(DEFAULT_SKIP_FILE_RELS))
            results = _apply_repo_invariants(scan)
            target.append({
                "case_name": f"{kind}/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    return pos, neg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--base-url", default=None,
                        help="optional loopback URL for response-header probe")
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
            write_report(pathlib.Path(args.out), pathlib.Path(args.fixtures), None,
                         {"files_scanned": 0, "tailscale_authkey_hits": [],
                          "cloudflare_token_hits": []},
                         flat, sentinel,
                         {"positive": pos, "negative": neg})
        print(sentinel)
        return 0 if sentinel == SENTINEL_PASS else 1

    root = pathlib.Path(args.root).resolve()
    scan = scan_repo(root, list(DEFAULT_SKIP_FILE_RELS))
    results = _apply_repo_invariants(scan)
    if args.base_url:
        if not args.base_url.startswith(("http://127.0.0.1", "http://localhost")):
            if args.out:
                pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                pathlib.Path(args.out).write_text(
                    f"{SENTINEL_FAIL}: --base-url must be loopback; got {args.base_url}\n"
                )
            print(SENTINEL_FAIL)
            return 1
        results += _runtime_probe(args.base_url)
    sentinel = SENTINEL_PASS if all(r["passed"] for r in results) else SENTINEL_FAIL
    if args.out:
        write_report(pathlib.Path(args.out), root, args.base_url, scan, results, sentinel)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
