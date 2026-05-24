#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_no_tunnel_secret_leak.py.

Materializes mini-repo fixture trees under positive/<case>/repo/ and
negative/<case>/repo/. Negative cases plant a synthetic tunnel-secret
literal that the validator must detect.

Positive case: repo files reference only env-var NAMES (TAILSCALE_AUTHKEY,
PUBLIC_DEMO_STABLE_HOSTNAME) and contain no real secret.

Negative cases:
  * negative_tailscale_authkey_committed     — file contains 'tskey-<...>'
  * negative_cloudflare_token_committed      — file contains 'eyJ<...>.<...>'

Emits OK_FIXTURE_VALIDATE_B14_2_NO_TUNNEL_SECRET_LEAK on success or
B14_2_TUNNEL_SECRET_COMMITTED on adversarial failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_NO_TUNNEL_SECRET_LEAK"
SENTINEL_FAIL = "B14_2_TUNNEL_SECRET_COMMITTED"
VALIDATOR_OK = "OK_B14_2_NO_TUNNEL_SECRET_LEAK"
VALIDATOR_FAIL = "B14_2_TUNNEL_SECRET_COMMITTED"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (REPO_ROOT / "scripts" / "rp5" /
                  "validate_b14_2_no_tunnel_secret_leak.py")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hash_tree(root: pathlib.Path) -> list[dict]:
    return [{"path": str(p.relative_to(root)),
             "sha256": sha256_bytes(p.read_bytes()),
             "size_bytes": p.stat().st_size}
            for p in sorted(root.rglob("*")) if p.is_file()]


def _wipe(p: pathlib.Path) -> None:
    if not p.exists():
        return
    for child in sorted(p.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    p.rmdir()


def _write_minirepo(case_root: pathlib.Path, files: dict[str, str]) -> None:
    repo = case_root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def positive_files() -> dict[str, str]:
    return {
        ".env.example": (
            "PUBLIC_DEMO_EXPOSURE=false\n"
            "TAILSCALE_AUTHKEY=\n"
            "PUBLIC_DEMO_STABLE_HOSTNAME=\n"
            "RECRUITER_USERNAME=\n"
            "RECRUITER_PASSWORD=\n"
        ),
        "README.md": (
            "Auth-key is referenced by env-var name only: TAILSCALE_AUTHKEY.\n"
        ),
    }


# Synthetic fixture-only auth-key shape; clearly not a real Tailscale
# auth-key value (the prefix is real, but the body is fixture filler).
NEGATIVE_TSKEY = "tskey-" + "FIXTUREFILLER" * 4


# Synthetic Cloudflare-tunnel-token-shaped string used only inside
# fixture mini-repos to exercise the validator's regex. Not a real token.
NEGATIVE_CF_TOKEN = "eyJ" + "FIXTURE" + ("A" * 40) + ".FIXTURE_PAYLOAD_TOKEN"


def negative_files_tskey() -> dict[str, str]:
    # File suffix is 'env_fixture' (not '.env') so the repository's
    # default '.gitignore' does not skip the committed negative fixture.
    return {"ops/env_fixture.txt": f"TAILSCALE_AUTHKEY={NEGATIVE_TSKEY}\n"}


def negative_files_cf() -> dict[str, str]:
    return {"ops/env_fixture.txt": f"CLOUDFLARE_TUNNEL_TOKEN={NEGATIVE_CF_TOKEN}\n"}


def run_selftest(fixtures_root: pathlib.Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--selftest",
         "--fixtures", str(fixtures_root)],
        capture_output=True, text=True,
    )
    out = proc.stdout.strip().splitlines()
    return out[-1] if out else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = (manifest_path.parent /
                     "generate_fixture_validate_b14_2_no_tunnel_secret_leak")
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    _write_minirepo(fixtures_root / "positive" / "positive", positive_files())
    _write_minirepo(fixtures_root / "negative" / "negative_tailscale_authkey_committed",
                    negative_files_tskey())
    _write_minirepo(fixtures_root / "negative" / "negative_cloudflare_token_committed",
                    negative_files_cf())

    aggregate = run_selftest(fixtures_root)

    per_case_observations = []
    failures = []
    for case_name, files_fn in (
        ("negative_tailscale_authkey_committed", negative_files_tskey),
        ("negative_cloudflare_token_committed", negative_files_cf),
    ):
        per_case_root = fixtures_root / "_per_case" / case_name
        _write_minirepo(per_case_root / "positive" / case_name, files_fn())
        _write_minirepo(per_case_root / "negative" / "decoy_negative",
                        negative_files_tskey())
        sentinel = run_selftest(per_case_root)
        per_case_observations.append({"case_name": case_name, "observed_sentinel": sentinel})
        if sentinel != VALIDATOR_FAIL:
            failures.append(
                f"per_case_{case_name}: expected {VALIDATOR_FAIL} got {sentinel!r}"
            )
    _wipe(fixtures_root / "_per_case")

    if aggregate != VALIDATOR_OK:
        failures.append(f"aggregate: expected {VALIDATOR_OK} got {aggregate!r}")

    manifest = {
        "validator": "validate_b14_2_no_tunnel_secret_leak",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "aggregate_selftest_sentinel": aggregate,
        "positive": [{"case_name": "positive", "root": "positive/positive",
                      "expected_sentinel_under_aggregate_selftest": VALIDATOR_OK}],
        "negative": [
            {"case_name": "negative_tailscale_authkey_committed",
             "root": "negative/negative_tailscale_authkey_committed",
             "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
             "observed_sentinel": next((o["observed_sentinel"] for o in per_case_observations
                                        if o["case_name"] == "negative_tailscale_authkey_committed"), None)},
            {"case_name": "negative_cloudflare_token_committed",
             "root": "negative/negative_cloudflare_token_committed",
             "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
             "observed_sentinel": next((o["observed_sentinel"] for o in per_case_observations
                                        if o["case_name"] == "negative_cloudflare_token_committed"), None)},
        ],
        "tree_files": hash_tree(fixtures_root),
    }
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(body)
    print(f"manifest_sha256: {sha256_bytes(body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if failures:
        for f in failures:
            print(f"adversarial_failure: {f}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
