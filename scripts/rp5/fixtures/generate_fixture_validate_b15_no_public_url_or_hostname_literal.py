#!/usr/bin/env python3
"""
Fixture generator paired with validate_b15_no_public_url_or_hostname_literal.

Materializes positive and negative content samples that exercise the
three forbidden classes the B15 validator recognises: public URLs,
stable tunnel hostnames, and tunnel secrets. The generator runs the
validator in-process against a temporary --root for each sample and
asserts that each negative case is flagged with the expected marker
while the positive case passes.

Hostname-shaped and secret-shaped material in the negative fixtures is
assembled at runtime from synthetic placeholder segments intentionally
distinct from any real operator hostname or credential; this generator
source never embeds an operator-owned literal.

Emits OK_FIXTURE_VALIDATE_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL on PASS
or B15_PUBLIC_URL_LITERAL_COMMITTED on FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
SENTINEL_FAIL = "B15_PUBLIC_URL_LITERAL_COMMITTED"
MARKER_HOSTNAME = "B15_STABLE_HOSTNAME_LITERAL_COMMITTED"
MARKER_TUNNEL_SECRET = "B15_TUNNEL_SECRET_COMMITTED"
VALIDATOR_OK = "OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    REPO_ROOT / "scripts" / "rp5"
    / "validate_b15_no_public_url_or_hostname_literal.py"
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hash_tree(root: pathlib.Path) -> list[dict]:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            files.append({
                "path": str(p.relative_to(root)),
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            })
    return files


POSITIVE_BODY = (
    "Loopback only — these patterns are allowed:\n"
    "  http://127.0.0.1:8001/demo/health\n"
    "  https://127.0.0.1/demo/health\n"
    "  https://[::1]/demo/health\n"
    "No public hostnames, no public URLs, no tunnel secrets.\n"
)


def negative_bodies() -> dict[str, tuple[str, str]]:
    # Each entry: case_name -> (file body, expected marker).
    # Placeholder segments assembled at runtime so this generator source
    # itself contains no literal public host or secret string.
    placeholder_label = "synthetic-placeholder"
    ts_segment = "ts" + "." + "net"
    cf_try_segment = "trycloudflare" + "." + "com"
    cf_arg_segment = "cfargotunnel" + "." + "com"
    authkey = "tskey-" + "Synthetic0Placeholder0Key0Value"
    cf_token = "eyJ" + "A" * 60
    auth_header = "Authorization: Bearer " + "U3ludGhldGljVG9rZW4xMjM0NQ=="
    return {
        "negative_tailscale_funnel_url": (
            f"Public URL literal pointing at a Tailscale Funnel host:\n"
            f"  https://{placeholder_label}.{ts_segment}/demo/health\n",
            SENTINEL_FAIL,
        ),
        "negative_cloudflare_tunnel_url": (
            f"Public URL literal pointing at a Cloudflare Tunnel host:\n"
            f"  https://{placeholder_label}.{cf_try_segment}/demo/health\n",
            SENTINEL_FAIL,
        ),
        "negative_tailscale_funnel_hostname": (
            f"Bare hostname literal: {placeholder_label}.{ts_segment}\n",
            MARKER_HOSTNAME,
        ),
        "negative_cloudflare_cfargotunnel_hostname": (
            f"Bare hostname literal: {placeholder_label}.{cf_arg_segment}\n",
            MARKER_HOSTNAME,
        ),
        "negative_tailscale_authkey": (
            f"Tailscale auth-key literal: TAILSCALE_AUTHKEY={authkey}\n",
            MARKER_TUNNEL_SECRET,
        ),
        "negative_cloudflare_tunnel_token": (
            f"Cloudflare tunnel token literal: TUNNEL_TOKEN={cf_token}\n",
            MARKER_TUNNEL_SECRET,
        ),
        "negative_authorization_header_value": (
            f"{auth_header}\n",
            MARKER_TUNNEL_SECRET,
        ),
    }


def run_validator(root: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(
        suffix=".md", delete=False, mode="w"
    ) as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--root", str(root),
                "--out", str(transcript),
            ],
            capture_output=True, text=True,
        )
        out = proc.stdout.strip().splitlines()
        return out[-1] if out else ""
    finally:
        transcript.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = (
        manifest_path.parent
        / "generate_fixture_validate_b15_no_public_url_or_hostname_literal"
    )
    fixtures_root.mkdir(parents=True, exist_ok=True)

    pos_root = fixtures_root / "positive"
    pos_root.mkdir(parents=True, exist_ok=True)
    (pos_root / "sample.txt").write_text(POSITIVE_BODY, encoding="utf-8")

    neg_root = fixtures_root / "negative"
    neg_root.mkdir(parents=True, exist_ok=True)

    adversarial_failures: list[str] = []
    neg_entries: list[dict] = []

    for case_name, (body, expected_marker) in negative_bodies().items():
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        (case_root / "sample.txt").write_text(body, encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            (tmp_path / "sample.txt").write_text(body, encoding="utf-8")
            sentinel = run_validator(tmp_path)
        if sentinel != expected_marker:
            adversarial_failures.append(
                f"{case_name}: expected {expected_marker} got {sentinel!r}"
            )
        neg_entries.append({
            "case_name": case_name,
            "root": str(case_root.relative_to(fixtures_root)),
            "expected_marker": expected_marker,
            "observed_sentinel": sentinel,
            "tree_files": hash_tree(case_root),
        })

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        (tmp_path / "sample.txt").write_text(POSITIVE_BODY, encoding="utf-8")
        pos_sentinel = run_validator(tmp_path)
    if pos_sentinel != VALIDATOR_OK:
        adversarial_failures.append(
            f"positive: expected {VALIDATOR_OK} got {pos_sentinel!r}"
        )

    positive_entry = {
        "case_name": "positive",
        "root": "positive",
        "expected_sentinel": VALIDATOR_OK,
        "observed_sentinel": pos_sentinel,
        "tree_files": hash_tree(pos_root),
    }

    manifest = {
        "validator": "validate_b15_no_public_url_or_hostname_literal",
        "kind": args.kind,
        "owned_markers": [SENTINEL_FAIL, MARKER_HOSTNAME, MARKER_TUNNEL_SECRET],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "positive": [positive_entry],
        "negative": neg_entries,
    }
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(body)
    print(f"manifest_sha256: {sha256_bytes(body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_failures:
        for f in adversarial_failures:
            print(f"adversarial_failure: {f}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
