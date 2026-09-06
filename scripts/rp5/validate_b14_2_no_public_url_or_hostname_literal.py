#!/usr/bin/env python3
"""
B14.2 no-public-URL-or-hostname-literal repository scan validator.

Mirrors the B15 precedent scope (validate_b15_no_public_url_or_hostname_literal):
only flag URL / hostname literals whose host matches an operator-owned
tunnel hostname pattern:

  * <label>.ts.net           (Tailscale Funnel)
  * <label>.trycloudflare.com (Cloudflare quick tunnel)
  * <label>.cfargotunnel.com  (Cloudflare named tunnel)

Generic third-party hostnames (github.com, example.com, assemblyai.com,
loopback addresses, etc.) are NOT flagged: they were committed under
prior approved phases and are operational documentation, not B14.2
public-exposure literals.

A complementary --component selector restricts the scan to URL-only,
hostname-only, or all checks.

Skip lists follow the B15 precedent (gitignored caches, vendored
frontend trees, fixture data trees, binary suffixes).

Sentinels:
  OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL              on success
  B14_2_PUBLIC_URL_LITERAL_COMMITTED                      on URL hit
  B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED                 on bare-hostname hit
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys


SENTINEL_PASS = "OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
MARKER_URL = "B14_2_PUBLIC_URL_LITERAL_COMMITTED"
MARKER_HOSTNAME = "B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED"

# Only flag tunnel-hostname-pattern hosts. Generic operator/operational
# URLs (github.com, assemblyai.com, etc.) are not B14.2 literals.
TUNNEL_HOSTNAME_RES = [
    re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.ts\.net\b"),
    re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.trycloudflare\.com\b"),
    re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.cfargotunnel\.com\b"),
]
URL_RE = re.compile(r"https?://([A-Za-z0-9.\-]+)(?::\d+)?")

SKIP_DIR_NAMES = {
    ".git", "__pycache__", "node_modules", ".next", "out", "dist",
    "build", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox",
}
SKIP_TOP_PREFIXES = (
    "runs/", ".venv/", "venv/", "data/", "node_modules/",
    "services/frontend/node_modules/", "services/frontend/.next/",
    # Fixture trees encode synthetic protocol identifiers authorised by
    # the active B14.2 plan (and prior B14.1/B15 plans); they carry no
    # operator-owned literal.
    "tests/rp5/fixtures/",
)
SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".wav", ".flac",
    ".mp4", ".mov", ".zip", ".gz", ".tgz", ".bz2", ".7z",
    ".whl", ".pyc",
)
TEXT_BYTE_LIMIT = 2_000_000

# Allow-list of files whose content describes the rules themselves;
# matches inside these are pattern documentation, not literals.
ALLOWLIST_REL_PATHS = {
    "scripts/rp5/validate_b14_2_no_public_url_or_hostname_literal.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_public_url_or_hostname_literal.py",
    # Pre-existing predecessor validators carrying the same regex documentation.
    "scripts/rp5/validate_b14_1_no_public_url_or_hostname_literal.py",
    "scripts/rp5/validate_b14_1_no_tunnel_secret_leak.py",
    "scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak.py",
    # Pre-existing B12.2 alert-body-redaction test carrying a synthetic
    # cloudflared URL string used as a redaction fixture; allowlisted by
    # the B15 precedent for the same reason.
    "tests/demo/test_b12_2_alert_body_redaction.py",
    # The validator's own output report can re-list its matches; skip
    # the canonical out-path so consecutive runs converge to PASS once
    # the underlying repo is clean.
    "reports/rp5/b14_2_no_public_url_or_hostname_literal.md",
}


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def _is_skipped(rel: str, p: pathlib.Path) -> bool:
    if any(rel.startswith(pref) for pref in SKIP_TOP_PREFIXES):
        return True
    if any(part in SKIP_DIR_NAMES for part in p.parts):
        return True
    if p.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def _iter_repo_files(root: pathlib.Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if _is_skipped(rel, p):
            continue
        yield p, rel


def _mask(line: str, max_len: int = 80) -> str:
    line = line.strip().replace("\n", " ").replace("\r", " ")
    if len(line) <= max_len:
        return line
    return line[:max_len] + "..."


def _host_matches_tunnel(host: str) -> bool:
    return any(rx.search(host) for rx in TUNNEL_HOSTNAME_RES)


def scan_repo(root: pathlib.Path, component: str) -> dict:
    url_hits, host_hits = [], []
    files_scanned = 0
    for p, rel in _iter_repo_files(root):
        if rel in ALLOWLIST_REL_PATHS:
            continue
        try:
            if p.stat().st_size > TEXT_BYTE_LIMIT:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        files_scanned += 1
        for i, line in enumerate(text.splitlines(), start=1):
            if component in ("all", "url_only"):
                for m in URL_RE.finditer(line):
                    host = m.group(1)
                    if _host_matches_tunnel(host):
                        url_hits.append((rel, i, _mask(line)))
            if component in ("all", "hostname_only"):
                for rx in TUNNEL_HOSTNAME_RES:
                    if rx.search(line):
                        host_hits.append((rel, i, _mask(line)))
                        break
    return {
        "files_scanned": files_scanned,
        "url_hits": url_hits,
        "host_hits": host_hits,
    }


def _apply_invariants(scan: dict) -> tuple[list[dict], str]:
    results = []
    sentinel = SENTINEL_PASS
    results.append(_check(
        "no_tunnel_hostname_pattern_in_url_literal_committed",
        len(scan["url_hits"]) == 0,
        f"{len(scan['url_hits'])} hit(s)" if scan["url_hits"] else
        "no tunnel-hostname-pattern URL literal observed",
    ))
    if scan["url_hits"]:
        sentinel = MARKER_URL
    results.append(_check(
        "no_tunnel_hostname_pattern_committed",
        len(scan["host_hits"]) == 0,
        f"{len(scan['host_hits'])} hit(s)" if scan["host_hits"] else
        "no tunnel-hostname-pattern bare-hostname literal observed",
    ))
    if scan["host_hits"] and sentinel == SENTINEL_PASS:
        sentinel = MARKER_HOSTNAME
    return results, sentinel


def write_report(out_path: pathlib.Path, root: pathlib.Path, scan: dict,
                 results: list, sentinel: str, component: str,
                 selftest_summary: dict | None = None) -> None:
    lines = [
        "# B14.2 No Public URL or Hostname Literal",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"root: {root}",
        f"component: {component}",
        f"files_scanned: {scan.get('files_scanned', 0)}",
        f"url_hits: {len(scan.get('url_hits', []))}",
        f"host_hits: {len(scan.get('host_hits', []))}",
        "scope_note: only tunnel-hostname-pattern hosts (*.ts.net, "
        "*.trycloudflare.com, *.cfargotunnel.com) are flagged; the scope "
        "mirrors the B15 precedent validator.",
        "",
        "## Invariant Results",
        "",
    ]
    for r in results:
        lines.append(f"- [{'PASS' if r['passed'] else 'FAIL'}] {r['name']}: {r['detail']}")
    if scan.get("url_hits"):
        lines += ["", "## Tunnel URL Hits (file:line — masked excerpt)", ""]
        for rel, i, excerpt in scan["url_hits"]:
            lines.append(f"- {rel}:{i}: {excerpt}")
    if scan.get("host_hits"):
        lines += ["", "## Tunnel Hostname Hits (file:line — masked excerpt)", ""]
        for rel, i, excerpt in scan["host_hits"]:
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


def _selftest_walk(fixtures_root: pathlib.Path, component: str) -> tuple[list, list]:
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
            scan = scan_repo(mini, component)
            results, _ = _apply_invariants(scan)
            target.append({
                "case_name": f"{kind}/{case.name}",
                "results": results,
                "all_passed": all(r["passed"] for r in results),
            })
    return pos, neg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default=None)
    parser.add_argument("--component", default="all",
                        choices=("all", "url_only", "hostname_only"))
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--fixtures", default=None)
    args = parser.parse_args()

    if args.selftest:
        if args.fixtures is None:
            print(MARKER_URL)
            return 1
        pos, neg = _selftest_walk(pathlib.Path(args.fixtures), args.component)
        pos_ok = bool(pos) and all(c["all_passed"] for c in pos)
        neg_ok = bool(neg) and all(not c["all_passed"] for c in neg)
        sentinel = SENTINEL_PASS if (pos_ok and neg_ok) else MARKER_URL
        flat = [_check(
            f"positive_case_{c['case_name']}_emits_PASS", c["all_passed"],
            "all invariants PASS" if c["all_passed"] else "at least one invariant FAIL",
        ) for c in pos] + [_check(
            f"negative_case_{c['case_name']}_emits_FAIL", not c["all_passed"],
            "at least one invariant FAIL (expected)" if not c["all_passed"]
            else "all invariants PASS (negative did not exercise defect)",
        ) for c in neg]
        if args.out:
            write_report(pathlib.Path(args.out), pathlib.Path(args.fixtures),
                         {"files_scanned": 0, "url_hits": [], "host_hits": []},
                         flat, sentinel, args.component,
                         {"positive": pos, "negative": neg})
        print(sentinel)
        return 0 if sentinel == SENTINEL_PASS else 1

    root = pathlib.Path(args.root).resolve()
    scan = scan_repo(root, args.component)
    results, sentinel = _apply_invariants(scan)
    if args.out:
        write_report(pathlib.Path(args.out), root, scan, results, sentinel,
                     args.component)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
