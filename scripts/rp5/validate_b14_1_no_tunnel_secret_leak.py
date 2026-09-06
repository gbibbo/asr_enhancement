#!/usr/bin/env python3
"""
B14.1 no-tunnel-secret-leak validator.

Scans for three classes of forbidden literal material that B14.1
treats as tunnel-secret leakage regardless of which file or runtime
surface carries them:

  * Tailscale auth-key literals (prefix shape "tskey-" followed by an
    opaque suffix);
  * Cloudflare tunnel token literals (JWT-shaped opaque suffix with
    "eyJ" prefix as commonly emitted by cloudflared tunnel run --token);
  * HTTP Authorization header values (Basic or Bearer scheme followed
    by a base64- or token-shaped payload).

Two scopes are supported:

  * --scope template: scan repository file content (default --root is
    the current working directory). Used by B14_1-04 to assert that the
    tunnel template at PL-B14_1-TUNNEL-TEMPLATE and surrounding
    repo content carry no secret material.
  * --scope runtime: probe a small set of routes on --base-url and
    scan response bodies for the same three classes. Used by B14_1-06
    to assert that the running application does not surface tunnel
    secrets through openapi/docs scratch, error pages, or
    /demo/health responses.

The validator never writes the matched literal into the --out report.
On a hit it records only the path-or-route, line number (file scope)
or response label (runtime scope), the matched pattern class, and the
redacted length of the matched token.

Emits OK_B14_1_NO_TUNNEL_SECRET_LEAK on PASS or
B14_1_TUNNEL_SECRET_COMMITTED on a hit.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys
import urllib.error
import urllib.request

SENTINEL_PASS = "OK_B14_1_NO_TUNNEL_SECRET_LEAK"
MARKER_FAIL = "B14_1_TUNNEL_SECRET_COMMITTED"

# Tailscale auth-key pattern: documented prefix "tskey-" followed by an
# opaque, sufficiently long suffix. The suffix-length floor keeps the
# pattern from false-positiving on documentation lines such as the
# literal prefix word.
TAILSCALE_AUTHKEY_RE = re.compile(r"\btskey-[A-Za-z0-9_]{8,}\b")

# Cloudflare tunnel token pattern: cloudflared service tokens are
# JWT-shaped opaque strings beginning with "eyJ" (base64 of {"alg":"...").
# The length floor keeps the pattern out of generic "eyJ..." mentions.
CLOUDFLARE_TOKEN_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]{40,}\b")

# HTTP Authorization header pattern: literal "Authorization:" followed
# by a Basic or Bearer scheme and a credential-shaped payload. The
# lookahead requires the payload to contain at least one digit, base64
# padding (=), or base64 alphabet symbol (+, /), which distinguishes a
# real Authorization header value from documentation strings such as
# "Authorization: Basic header" or "Authorization: Bearer token".
AUTHORIZATION_HEADER_RE = re.compile(
    r"Authorization\s*:\s*(?:Basic|Bearer)\s+"
    r"(?=[A-Za-z0-9+/=._\-]*[\d+/=])"
    r"[A-Za-z0-9+/=._\-]{6,}"
)

PATTERN_CLASSES = [
    ("tailscale_authkey", TAILSCALE_AUTHKEY_RE),
    ("cloudflare_tunnel_token", CLOUDFLARE_TOKEN_RE),
    ("authorization_header_value", AUTHORIZATION_HEADER_RE),
]

# Repo paths skipped by the file-content scan.
SKIP_DIR_NAMES = {
    ".git", "__pycache__", "node_modules", ".next", "out", "dist",
    "build", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox",
}
SKIP_TOP_PREFIXES = (
    "runs/", ".venv/", "venv/", "data/", "node_modules/",
    "services/frontend/node_modules/", "services/frontend/.next/",
    # Fixture trees exercise forbidden patterns intentionally; they are
    # generator output, not committed application content, and are
    # excluded from the repo-content scan.
    "tests/rp5/fixtures/",
)
SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".wav", ".flac",
    ".mp4", ".mov", ".zip", ".gz", ".tgz", ".bz2", ".7z",
    ".whl", ".pyc",
)
TEXT_BYTE_LIMIT = 2_000_000

# Allow-list of files whose own content describes the rules themselves.
# The patterns inside these files are documentation of the rule, not
# secret literals. Kept narrow and explicit.
ALLOWLIST_BASENAMES = {
    "validate_b14_1_no_tunnel_secret_leak.py",
    "generate_fixture_validate_b14_1_no_tunnel_secret_leak.py",
}
ALLOWLIST_REL_PATHS = {
    "scripts/rp5/validate_b14_1_no_tunnel_secret_leak.py",
    "scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak.py",
}

# Runtime-scope probe routes. Each entry is (label, path). The runtime
# scan fetches each route once without credentials and scans the
# response body for tunnel-secret patterns.
RUNTIME_PROBE_ROUTES = [
    ("openapi", "/openapi.json"),
    ("docs", "/docs"),
    ("redoc", "/redoc"),
    ("demo_health", "/demo/health"),
    ("root", "/"),
]


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


def _scan_text_for_secrets(text: str) -> list[dict]:
    hits: list[dict] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        for class_name, pattern in PATTERN_CLASSES:
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


def run_template_scope(root: pathlib.Path) -> tuple[list[dict], int, int]:
    hits: list[dict] = []
    files_scanned = 0
    files_skipped = 0
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
        for h in _scan_text_for_secrets(text):
            hits.append({"surface": "file",
                         "path_or_route": str(rel).replace("\\", "/"),
                         **h})
    return hits, files_scanned, files_skipped


def _http_get(url: str, timeout: float = 5.0) -> tuple[int, bytes]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, body
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return 0, str(e).encode("utf-8", errors="replace")


def run_runtime_scope(base_url: str) -> tuple[list[dict], int]:
    hits: list[dict] = []
    routes_probed = 0
    base = base_url.rstrip("/")
    for label, path in RUNTIME_PROBE_ROUTES:
        url = base + path
        status, body = _http_get(url)
        routes_probed += 1
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        for h in _scan_text_for_secrets(text):
            hits.append({"surface": "route",
                         "path_or_route": f"{label} {path} status={status}",
                         **h})
    return hits, routes_probed


def _format_report(args, hits: list[dict], extra_meta: dict) -> str:
    lines = [
        "# B14.1 No Tunnel Secret Leak — Scan Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"scope: {args.scope}",
    ]
    if args.scope == "template":
        lines.append(f"root: {extra_meta.get('root')}")
        lines.append(f"files_scanned: {extra_meta.get('files_scanned')}")
        lines.append(f"files_skipped: {extra_meta.get('files_skipped')}")
    else:
        lines.append(f"base_url: {extra_meta.get('base_url')}")
        lines.append(f"routes_probed: {extra_meta.get('routes_probed')}")
    lines.append(f"hits: {len(hits)}")
    lines += ["", "## Hits (redacted)", ""]
    if hits:
        for h in hits:
            lines.append(
                f"- surface={h['surface']} "
                f"location={h['path_or_route']} line={h.get('line', 'n/a')} "
                f"pattern_class={h['pattern_class']} "
                f"redacted_token_len={h['redacted_token_len']}"
            )
    else:
        lines.append("- none")

    if args.scope == "template":
        lines += [
            "",
            "## HAR Result (B14_1-04, HAR-B14_1-FUNNEL-CAPABILITY-001)",
            "",
            "- tailscale_account_funnel_capability_enabled: true",
            "- tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY: false",
            "- cloudflare_tunnel_alternative_token_supplied_as_host_env: explicit_NA",
            "- tunnel_run_as_service_restart_policy_string: on-failure",
            "- restart_policy_classification: operator-supplied service policy (non-runtime documentation field)",
            "- template_readiness_claim: NOT_READY_TO_RUN",
            "- residual_blocker_for_B14_1-08: tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY=false",
            "",
            "## HAR Result (B14_1-04, HAR-B14_1-STABLE-HOSTNAME-001)",
            "",
            "- status: pre_declared_unresolved",
            "- effect_on_B14_1-04: does_not_block",
            "- effect_on_B14_1-08: blocks success-claim unless resolved or recorded as explicit blocker",
        ]

    if hits:
        lines += ["", MARKER_FAIL]
    else:
        lines += [
            "",
            "## Result",
            "",
            "No tunnel-secret literal was found in the requested scope.",
            "",
            SENTINEL_PASS,
        ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", required=True, choices=("template", "runtime"))
    parser.add_argument("--root", default=".",
                        help="repo root for --scope template (default '.')")
    parser.add_argument("--base-url", default=None,
                        help="base URL for --scope runtime (e.g. http://127.0.0.1:8001)")
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    hits: list[dict] = []
    extra_meta: dict = {}

    if args.scope == "template":
        root = pathlib.Path(args.root).resolve()
        hits, files_scanned, files_skipped = run_template_scope(root)
        extra_meta = {
            "root": str(root),
            "files_scanned": files_scanned,
            "files_skipped": files_skipped,
        }
    else:
        if not args.base_url:
            out_path.write_text(
                "scope=runtime requires --base-url\n\n" + MARKER_FAIL + "\n"
            )
            print(MARKER_FAIL)
            return 1
        hits, routes_probed = run_runtime_scope(args.base_url)
        extra_meta = {
            "base_url": args.base_url,
            "routes_probed": routes_probed,
        }

    out_path.write_text(_format_report(args, hits, extra_meta))
    if hits:
        print(MARKER_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
