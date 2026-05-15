#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_1_no_tunnel_secret_leak.

Materializes positive and negative content samples that exercise the
three forbidden pattern classes the validator owns:

  * Tailscale auth-key prefix shape (tskey-<opaque>)
  * Cloudflare tunnel JWT-shaped token (eyJ<opaque>)
  * HTTP Authorization header values (Basic or Bearer)

Each negative case is written to its own subtree under the fixtures
root, then re-staged into a fresh temporary --root and replayed against
the validator in --scope template mode. The generator asserts that each
negative subtree yields B14_1_TUNNEL_SECRET_COMMITTED and that the
positive subtree yields OK_B14_1_NO_TUNNEL_SECRET_LEAK.

Synthetic placeholder material is assembled at runtime from neutral
segments so the generator source itself does not embed a literal
tskey-, eyJ-, or Authorization-header token.

Emits OK_FIXTURE_VALIDATE_B14_1_NO_TUNNEL_SECRET_LEAK on PASS or
B14_1_TUNNEL_SECRET_COMMITTED on FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_NO_TUNNEL_SECRET_LEAK"
SENTINEL_FAIL = "B14_1_TUNNEL_SECRET_COMMITTED"
VALIDATOR_PASS = "OK_B14_1_NO_TUNNEL_SECRET_LEAK"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    REPO_ROOT / "scripts" / "rp5"
    / "validate_b14_1_no_tunnel_secret_leak.py"
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
    "Tunnel template using env-var-name references only:\n"
    "  auth_key_env_var_name: TAILSCALE_AUTHKEY\n"
    "  stable_hostname_env_var_name: PUBLIC_DEMO_STABLE_HOSTNAME\n"
    "  public_exposure_flag_env_var_name: PUBLIC_DEMO_EXPOSURE\n"
    "  auth_key_supplied_as_host_env: false\n"
    "  ready_to_run: false\n"
    "No auth-key literal, no token literal, no Authorization header.\n"
)


def negative_bodies() -> dict[str, str]:
    # Synthetic placeholders assembled at runtime so the generator
    # source itself never carries a literal secret prefix.
    tskey_prefix = "ts" + "key-"
    jwt_prefix = "ey" + "J"
    auth_header_name = "Authoriza" + "tion"
    return {
        "negative_tailscale_authkey": (
            "Forbidden Tailscale auth-key literal:\n"
            f"  TAILSCALE_AUTHKEY={tskey_prefix}AbCdEf1234567890XyZ\n"
        ),
        "negative_cloudflare_tunnel_token": (
            "Forbidden Cloudflare tunnel token literal:\n"
            f"  CLOUDFLARE_TUNNEL_TOKEN={jwt_prefix}AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCdEfGh\n"
        ),
        "negative_authorization_basic_header": (
            "Forbidden Authorization Basic header value:\n"
            f"  {auth_header_name}: Basic dXNlcjpwYXNzd29yZA==\n"
        ),
        "negative_authorization_bearer_header": (
            "Forbidden Authorization Bearer header value:\n"
            f"  {auth_header_name}: Bearer abcdef0123456789ABCDEF\n"
        ),
    }


def run_validator_template_scope(root: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(
        suffix=".md", delete=False, mode="w"
    ) as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--scope", "template",
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
    fixtures_root = manifest_path.parent / "b14_1_no_tunnel_secret_leak"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    pos_root = fixtures_root / "positive"
    pos_root.mkdir(parents=True, exist_ok=True)
    pos_file = pos_root / "sample.txt"
    pos_file.write_text(POSITIVE_BODY, encoding="utf-8")

    neg_root = fixtures_root / "negative"
    neg_root.mkdir(parents=True, exist_ok=True)

    adversarial_failures: list[str] = []
    neg_entries: list[dict] = []

    for case_name, body in negative_bodies().items():
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        sample_file = case_root / "sample.txt"
        sample_file.write_text(body, encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            (tmp_path / "sample.txt").write_text(body, encoding="utf-8")
            sentinel = run_validator_template_scope(tmp_path)
        if sentinel != SENTINEL_FAIL:
            adversarial_failures.append(
                f"{case_name}: expected {SENTINEL_FAIL} got {sentinel!r}"
            )
        neg_entries.append({
            "case_name": case_name,
            "root": str(case_root.relative_to(fixtures_root)),
            "expected_marker": SENTINEL_FAIL,
            "observed_sentinel": sentinel,
            "tree_files": hash_tree(case_root),
        })

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        (tmp_path / "sample.txt").write_text(POSITIVE_BODY, encoding="utf-8")
        pos_sentinel = run_validator_template_scope(tmp_path)
    if pos_sentinel != VALIDATOR_PASS:
        adversarial_failures.append(
            f"positive: expected {VALIDATOR_PASS} got {pos_sentinel!r}"
        )

    positive_entry = {
        "case_name": "positive",
        "root": "positive",
        "expected_sentinel": VALIDATOR_PASS,
        "observed_sentinel": pos_sentinel,
        "tree_files": hash_tree(pos_root),
    }

    manifest = {
        "validator": "validate_b14_1_no_tunnel_secret_leak",
        "kind": args.kind,
        "owned_markers": [SENTINEL_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_pass_sentinel": VALIDATOR_PASS,
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
