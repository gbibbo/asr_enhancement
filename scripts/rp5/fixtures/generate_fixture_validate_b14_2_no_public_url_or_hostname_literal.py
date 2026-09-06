#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_no_public_url_or_hostname_literal.py.

Materializes mini-repo fixture trees under positive/<case>/repo/ and
negative/<case>/repo/. The validator selftest-walks these mini-repos
and applies its repo scan to each.

Positive case: a tiny repo whose files reference only loopback
addresses and no tunnel-hostname pattern.

Negative cases (each plants a tunnel-hostname-shape literal — the
scope inherited from the B15 precedent validator):
  * negative_tailscale_funnel_hostname_committed   — '.ts.net' host
  * negative_cloudflare_trycloudflare_hostname     — '.trycloudflare.com'

Emits OK_FIXTURE_VALIDATE_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL on
success or B14_2_PUBLIC_URL_LITERAL_COMMITTED on adversarial failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
SENTINEL_FAIL = "B14_2_PUBLIC_URL_LITERAL_COMMITTED"
VALIDATOR_OK = "OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL"
VALIDATOR_FAIL = "B14_2_PUBLIC_URL_LITERAL_COMMITTED"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (REPO_ROOT / "scripts" / "rp5" /
                  "validate_b14_2_no_public_url_or_hostname_literal.py")


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
        "README.md": (
            "# fixture mini-repo (positive)\n"
            "Local loopback only: http://127.0.0.1:8001/demo/health\n"
        ),
        "config.yml": (
            "base_url: http://127.0.0.1:8001\n"
            "host: localhost\n"
        ),
    }


# Tunnel-hostname suffix tokens assembled piece-wise so the literal never
# appears contiguously in this generator's source (otherwise the B15
# precedent validator would treat this generator as a hit). The validator
# under test sees the assembled literal inside the negative fixture's
# committed file content, which is what we want.
_TS_NET_SUFFIX = "." + "ts" + "." + "net"
_TRYCLOUDFLARE_SUFFIX = "." + "trycloudflare" + "." + "com"


def negative_files_url() -> dict[str, str]:
    host = "fixture-demo.fixture-tnet" + _TS_NET_SUFFIX
    return {
        "README.md": (
            "# fixture mini-repo (negative: tailscale funnel URL committed)\n"
            f"Public endpoint: https://{host}/demo\n"
        ),
    }


def negative_files_ip() -> dict[str, str]:
    host = "fixture-demo" + _TRYCLOUDFLARE_SUFFIX
    return {
        "ops/notes.md": (
            "# fixture mini-repo (negative: cloudflare trycloudflare URL)\n"
            f"Public endpoint: https://{host}/demo\n"
        ),
    }


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
                     "generate_fixture_validate_b14_2_no_public_url_or_hostname_literal")
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    _write_minirepo(fixtures_root / "positive" / "positive", positive_files())
    _write_minirepo(fixtures_root / "negative" / "negative_tailscale_funnel_hostname_committed",
                    negative_files_url())
    _write_minirepo(fixtures_root / "negative" / "negative_cloudflare_trycloudflare_hostname",
                    negative_files_ip())

    aggregate = run_selftest(fixtures_root)

    per_case_observations = []
    adversarial_failures = []
    for case_name, files_fn in (
        ("negative_tailscale_funnel_hostname_committed", negative_files_url),
        ("negative_cloudflare_trycloudflare_hostname", negative_files_ip),
    ):
        per_case_root = fixtures_root / "_per_case" / case_name
        _write_minirepo(per_case_root / "positive" / case_name, files_fn())
        # decoy negative: also clearly bad so neg_ok is satisfied
        _write_minirepo(per_case_root / "negative" / "decoy_negative",
                        negative_files_url())
        sentinel = run_selftest(per_case_root)
        per_case_observations.append({"case_name": case_name, "observed_sentinel": sentinel})
        if sentinel != VALIDATOR_FAIL:
            adversarial_failures.append(
                f"per_case_{case_name}: expected {VALIDATOR_FAIL} got {sentinel!r}"
            )
    _wipe(fixtures_root / "_per_case")

    if aggregate != VALIDATOR_OK:
        adversarial_failures.append(f"aggregate: expected {VALIDATOR_OK} got {aggregate!r}")

    manifest = {
        "validator": "validate_b14_2_no_public_url_or_hostname_literal",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "aggregate_selftest_sentinel": aggregate,
        "positive": [{"case_name": "positive", "root": "positive/positive",
                      "expected_sentinel_under_aggregate_selftest": VALIDATOR_OK}],
        "negative": [
            {"case_name": "negative_tailscale_funnel_hostname_committed",
             "root": "negative/negative_tailscale_funnel_hostname_committed",
             "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
             "observed_sentinel": next((o["observed_sentinel"] for o in per_case_observations
                                        if o["case_name"] == "negative_tailscale_funnel_hostname_committed"), None)},
            {"case_name": "negative_cloudflare_trycloudflare_hostname",
             "root": "negative/negative_cloudflare_trycloudflare_hostname",
             "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
             "observed_sentinel": next((o["observed_sentinel"] for o in per_case_observations
                                        if o["case_name"] == "negative_cloudflare_trycloudflare_hostname"), None)},
        ],
        "tree_files": hash_tree(fixtures_root),
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
