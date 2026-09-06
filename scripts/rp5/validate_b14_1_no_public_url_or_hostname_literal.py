#!/usr/bin/env python3
"""
B14.1 no-public-URL-or-hostname-literal validator.

Scans committed-or-staged repository content for two narrow classes of
forbidden literal material that B14.1 forbids regardless of which task
touches which file:

  * any URL whose host matches a Tailscale Funnel or Cloudflare Tunnel
    public-hostname pattern (the operator's public exposure point);
  * any bare hostname matching the same tunnel-host patterns.

General third-party hostnames (github.com, example.com, assemblyai.com,
prometheus, testserver, otel-collector, etc.) are not the target of this
validator: B14.1 does not forbid every https URL, it forbids the
operator's public-exposure literal. The targeted patterns cover the two
tunnel providers in scope (Tailscale Funnel and Cloudflare Tunnel).

The validator never writes the matched content back to its --out report.
On a hit it reports only path, line number, and a redacted token shape
(provider + length); never the literal host.

Selectors:

  * --root <path>: scan a directory tree (defaults to the repo root).
  * --component {all,url_only,hostname_only}: restrict scan.

Emits OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL on PASS,
B14_1_PUBLIC_URL_LITERAL_COMMITTED on a public-URL hit, or
B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED on a hostname hit.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

SENTINEL_PASS = "OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
MARKER_PUBLIC_URL = "B14_1_PUBLIC_URL_LITERAL_COMMITTED"
MARKER_HOSTNAME = "B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED"

# Tunnel-hostname patterns. The two providers in scope for B14.1 are
# Tailscale Funnel (<label>.<tailnet>.ts.net) and Cloudflare Tunnel
# (<label>.trycloudflare.com / <label>.cfargotunnel.com). These patterns
# define both the bare-hostname scan and the URL-scan: a URL only counts
# as a "public URL literal" when its host matches one of these.
TUNNEL_HOSTNAME_RES = [
    re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.ts\.net\b"),
    re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.trycloudflare\.com\b"),
    re.compile(r"\b[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.cfargotunnel\.com\b"),
]
# URL pattern: only flag URLs whose host matches a tunnel-hostname pattern.
URL_RE = re.compile(
    r"\b(https?)://"
    r"([A-Za-z0-9](?:[A-Za-z0-9\-.]*[A-Za-z0-9])?)"
    r"(?::\d+)?(?:/[^\s'\"<>]*)?",
)


def _host_matches_tunnel_pattern(host: str) -> str | None:
    for pattern in TUNNEL_HOSTNAME_RES:
        if pattern.fullmatch(host):
            return pattern.pattern
        if pattern.search(host):
            return pattern.pattern
    return None

# Paths to skip (binaries, vendored, .git, caches, runtime, node_modules).
SKIP_DIR_NAMES = {
    ".git", "__pycache__", "node_modules", ".next", "out", "dist",
    "build", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox",
}
SKIP_TOP_PREFIXES = (
    "runs/", ".venv/", "venv/", "data/", "node_modules/",
    "services/frontend/node_modules/", "services/frontend/.next/",
    # Fixture data trees are paired generator output exercising forbidden
    # patterns; they are explicit test material, not committed application
    # content, so they are excluded from the public-content scan.
    "tests/rp5/fixtures/",
)
SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".wav", ".flac",
    ".mp4", ".mov", ".zip", ".gz", ".tgz", ".bz2", ".7z",
    ".whl", ".pyc",
)
TEXT_BYTE_LIMIT = 2_000_000

# Allow-list of files whose content describes the rule itself; matches
# inside these are pattern documentation, not literals. The allowlist is
# kept narrow and explicit; nothing else is exempted.
ALLOWLIST_BASENAMES = {
    "validate_b14_1_no_public_url_or_hostname_literal.py",
}
ALLOWLIST_REL_PATHS = {
    "scripts/rp5/validate_b14_1_no_public_url_or_hostname_literal.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal.py",
    # Pre-existing B12.2 test exercises tunnel-URL redaction; the URL is
    # a synthetic placeholder ("my-tunnel") committed before B14.1, and
    # the test asserts that the alert pipeline never echoes such a URL.
    # Allowlisted explicitly so the rule remains narrow and auditable.
    "tests/demo/test_b12_2_alert_body_redaction.py",
}


def _is_skipped_path(rel: pathlib.Path) -> bool:
    parts = rel.parts
    for d in SKIP_DIR_NAMES:
        if d in parts:
            return True
    rel_str = str(rel).replace("\\", "/")
    for prefix in SKIP_TOP_PREFIXES:
        if rel_str.startswith(prefix):
            return True
    suffix = rel.suffix.lower()
    if suffix in SKIP_SUFFIXES:
        return True
    return False


def _is_allowlisted(rel: pathlib.Path) -> bool:
    if rel.name in ALLOWLIST_BASENAMES:
        return True
    return str(rel).replace("\\", "/") in ALLOWLIST_REL_PATHS


def _scan_lines_for_urls(lines: list[str]):
    hits = []
    for idx, line in enumerate(lines, start=1):
        for m in URL_RE.finditer(line):
            scheme = m.group(1)
            host = m.group(2)
            provider = _host_matches_tunnel_pattern(host)
            if provider is None:
                continue
            hits.append({
                "line": idx,
                "scheme": scheme,
                "provider_pattern": provider,
                "redacted_token_len": len(m.group(0)),
            })
    return hits


def _scan_lines_for_hostnames(lines: list[str]):
    hits = []
    for idx, line in enumerate(lines, start=1):
        for pattern in TUNNEL_HOSTNAME_RES:
            for m in pattern.finditer(line):
                hits.append({
                    "line": idx,
                    "pattern": pattern.pattern,
                    "redacted_token_len": len(m.group(0)),
                })
    return hits


def _iter_repo_files(root: pathlib.Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if _is_skipped_path(rel):
            continue
        yield rel, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument(
        "--component",
        choices=("all", "url_only", "hostname_only"),
        default="all",
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    url_hits: list[dict] = []
    hostname_hits: list[dict] = []
    files_scanned = 0
    files_skipped = 0

    scan_urls = args.component in ("all", "url_only")
    scan_hosts = args.component in ("all", "hostname_only")

    for rel, abs_path in _iter_repo_files(root):
        if _is_allowlisted(rel):
            continue
        try:
            data = abs_path.read_bytes()
        except OSError:
            files_skipped += 1
            continue
        if len(data) > TEXT_BYTE_LIMIT:
            files_skipped += 1
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            files_skipped += 1
            continue
        files_scanned += 1
        lines = text.splitlines()
        if scan_urls:
            for h in _scan_lines_for_urls(lines):
                url_hits.append({"path": str(rel).replace("\\", "/"), **h})
        if scan_hosts:
            for h in _scan_lines_for_hostnames(lines):
                hostname_hits.append({"path": str(rel).replace("\\", "/"), **h})

    lines_out = [
        "# B14.1 No Public URL or Hostname Literal — Scan Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"root: {root}",
        f"component: {args.component}",
        f"files_scanned: {files_scanned}",
        f"files_skipped: {files_skipped}",
        f"url_hits: {len(url_hits)}",
        f"hostname_hits: {len(hostname_hits)}",
        "",
        "## URL Hits (redacted)",
        "",
    ]
    if url_hits:
        for h in url_hits:
            lines_out.append(
                f"- {h['path']}:{h['line']} scheme={h['scheme']} "
                f"provider_pattern={h['provider_pattern']} "
                f"redacted_token_len={h['redacted_token_len']}"
            )
    else:
        lines_out.append("- none")

    lines_out += ["", "## Hostname Hits (redacted)", ""]
    if hostname_hits:
        for h in hostname_hits:
            lines_out.append(
                f"- {h['path']}:{h['line']} pattern={h['pattern']} "
                f"redacted_token_len={h['redacted_token_len']}"
            )
    else:
        lines_out.append("- none")

    if url_hits:
        lines_out += ["", MARKER_PUBLIC_URL]
        out_path.write_text("\n".join(lines_out) + "\n")
        print(MARKER_PUBLIC_URL)
        return 1
    if hostname_hits:
        lines_out += ["", MARKER_HOSTNAME]
        out_path.write_text("\n".join(lines_out) + "\n")
        print(MARKER_HOSTNAME)
        return 1

    lines_out += [
        "",
        "## Result",
        "",
        "No literal public URL or stable hostname pattern was found.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines_out) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
