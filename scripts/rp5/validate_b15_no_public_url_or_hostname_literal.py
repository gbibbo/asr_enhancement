#!/usr/bin/env python3
"""
B15 no-public-URL-or-hostname-literal validator.

Scans committed-or-staged repository content for forbidden literal
material that B15 forbids regardless of which task touches which file.
Three component classes are recognised:

  * url        — any URL whose host matches a Tailscale Funnel or
                 Cloudflare Tunnel public-hostname pattern;
  * hostname   — any bare hostname matching the same tunnel-host
                 patterns;
  * tunnel_secret — Tailscale auth-key literals, Cloudflare tunnel
                 token literals, and HTTP Authorization header values.

General third-party hostnames (github.com, example.com, assemblyai.com,
prometheus, testserver, otel-collector, etc.) are not the target of this
validator: B15 does not forbid every https URL, it forbids the operator's
public-exposure literal and tunnel-secret material.

Selectors:

  * --root <path>: scan a directory tree (required).
  * --component {all,url_only,hostname_only,tunnel_secret}: restrict scan.

The validator never writes the matched content back to its --out report.
On a hit it reports only path, line number, and a redacted token shape
(pattern + length); never the literal host or secret.

Emits OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL on PASS,
B15_PUBLIC_URL_LITERAL_COMMITTED on a public-URL hit,
B15_STABLE_HOSTNAME_LITERAL_COMMITTED on a hostname hit, or
B15_TUNNEL_SECRET_COMMITTED on a tunnel-secret hit.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

SENTINEL_PASS = "OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
MARKER_PUBLIC_URL = "B15_PUBLIC_URL_LITERAL_COMMITTED"
MARKER_HOSTNAME = "B15_STABLE_HOSTNAME_LITERAL_COMMITTED"
MARKER_TUNNEL_SECRET = "B15_TUNNEL_SECRET_COMMITTED"

# Tunnel-hostname patterns. The two providers in scope are Tailscale
# Funnel (<label>.<tailnet>.ts.net) and Cloudflare Tunnel
# (<label>.trycloudflare.com / <label>.cfargotunnel.com).
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

# Tunnel-secret patterns (semantics inherited from the B14.1
# no-tunnel-secret-leak validator). Length floors keep each pattern
# from false-positiving on documentation lines such as a bare prefix.
TAILSCALE_AUTHKEY_RE = re.compile(r"\btskey-[A-Za-z0-9_]{8,}\b")
CLOUDFLARE_TOKEN_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]{40,}\b")
AUTHORIZATION_HEADER_RE = re.compile(
    r"Authorization\s*:\s*(?:Basic|Bearer)\s+"
    r"(?=[A-Za-z0-9+/=._\-]*[\d+/=])"
    r"[A-Za-z0-9+/=._\-]{6,}"
)
TUNNEL_SECRET_CLASSES = [
    ("tailscale_authkey", TAILSCALE_AUTHKEY_RE),
    ("cloudflare_tunnel_token", CLOUDFLARE_TOKEN_RE),
    ("authorization_header_value", AUTHORIZATION_HEADER_RE),
]


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

# Allow-list of files whose content describes the rules themselves;
# matches inside these are pattern documentation, not literals. Kept
# narrow and explicit; nothing else is exempted.
ALLOWLIST_BASENAMES = {
    "validate_b15_no_public_url_or_hostname_literal.py",
    "generate_fixture_validate_b15_no_public_url_or_hostname_literal.py",
}
ALLOWLIST_REL_PATHS = {
    "scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b15_no_public_url_or_hostname_literal.py",
    # Pre-existing B14.1 validators and B12.2 test that document the same
    # tunnel patterns; they carry no operator-owned literal and are
    # allowlisted explicitly so the B15 rule remains narrow and auditable.
    "scripts/rp5/validate_b14_1_no_public_url_or_hostname_literal.py",
    "scripts/rp5/validate_b14_1_no_tunnel_secret_leak.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak.py",
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


def _scan_lines_for_urls(lines: list[str]) -> list[dict]:
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


def _scan_lines_for_hostnames(lines: list[str]) -> list[dict]:
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


def _scan_lines_for_tunnel_secrets(lines: list[str]) -> list[dict]:
    hits = []
    for idx, line in enumerate(lines, start=1):
        for class_name, pattern in TUNNEL_SECRET_CLASSES:
            for m in pattern.finditer(line):
                hits.append({
                    "line": idx,
                    "pattern_class": class_name,
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
        choices=("all", "url_only", "hostname_only", "tunnel_secret"),
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
    tunnel_secret_hits: list[dict] = []
    files_scanned = 0
    files_skipped = 0

    scan_urls = args.component in ("all", "url_only")
    scan_hosts = args.component in ("all", "hostname_only")
    scan_secrets = args.component in ("all", "tunnel_secret")

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
        rel_str = str(rel).replace("\\", "/")
        if scan_urls:
            for h in _scan_lines_for_urls(lines):
                url_hits.append({"path": rel_str, **h})
        if scan_hosts:
            for h in _scan_lines_for_hostnames(lines):
                hostname_hits.append({"path": rel_str, **h})
        if scan_secrets:
            for h in _scan_lines_for_tunnel_secrets(lines):
                tunnel_secret_hits.append({"path": rel_str, **h})

    lines_out = [
        "# B15 No Public URL or Hostname Literal — Scan Report",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"root: {root}",
        f"component: {args.component}",
        f"files_scanned: {files_scanned}",
        f"files_skipped: {files_skipped}",
        f"url_hits: {len(url_hits)}",
        f"hostname_hits: {len(hostname_hits)}",
        f"tunnel_secret_hits: {len(tunnel_secret_hits)}",
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

    lines_out += ["", "## Tunnel Secret Hits (redacted)", ""]
    if tunnel_secret_hits:
        for h in tunnel_secret_hits:
            lines_out.append(
                f"- {h['path']}:{h['line']} "
                f"pattern_class={h['pattern_class']} "
                f"redacted_token_len={h['redacted_token_len']}"
            )
    else:
        lines_out.append("- none")

    # Hit precedence: url, then hostname, then tunnel secret.
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
    if tunnel_secret_hits:
        lines_out += ["", MARKER_TUNNEL_SECRET]
        out_path.write_text("\n".join(lines_out) + "\n")
        print(MARKER_TUNNEL_SECRET)
        return 1

    lines_out += [
        "",
        "## Result",
        "",
        "No literal public URL, stable hostname, or tunnel secret was found.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines_out) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
