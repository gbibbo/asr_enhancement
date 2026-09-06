#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_no_network_trust_authority.py.

Materializes:

  * one positive observations.json (every surrogate header sent in
    isolation produces a canonical 401 challenge);
  * two negative observations.json fixtures, each carrying one
    surrogate-header probe whose response was non-401, simulating the
    server honouring that header as authority:
      - negative_x_forwarded_for_accepted
      - negative_tailscale_user_login_accepted.

The generator drives the paired validator in --selftest mode against
the aggregate fixture tree (positive + negatives) and additionally
re-exercises each negative case in isolation (treated as a single
positive case) to confirm that the validator emits
B14_2_NETWORK_TRUST_AUTHORITY_DETECTED on each adversarial defect.

No public-network call. No literal public URL, hostname, auth-key,
token, password, or non-loopback IP address is written.

Emits OK_FIXTURE_VALIDATE_B14_2_NO_NETWORK_TRUST on success or
B14_2_NETWORK_TRUST_AUTHORITY_DETECTED on any adversarial-expectation
violation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_NO_NETWORK_TRUST"
SENTINEL_FAIL = "B14_2_NETWORK_TRUST_AUTHORITY_DETECTED"
VALIDATOR_OK = "OK_B14_2_NO_NETWORK_TRUST_AUTHORITY"
VALIDATOR_FAIL = "B14_2_NETWORK_TRUST_AUTHORITY_DETECTED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    REPO_ROOT / "scripts" / "rp5" /
    "validate_b14_2_no_network_trust_authority.py"
)
RECRUITER_REALM = "asr-demo-recruiter"
CANONICAL_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'

SURROGATE_HEADERS = {
    "X-Forwarded-For": "127.0.0.1",
    "X-Real-IP": "127.0.0.1",
    "X-Forwarded-Host": "loopback.invalid",
    "X-Forwarded-Proto": "https",
    "Tailscale-User-Login": "b14_2-fixture-user",
    "Tailscale-User-Name": "b14_2-fixture",
    "Tailscale-User-Profile-Pic": "http://127.0.0.1/none",
    "CF-Connecting-IP": "127.0.0.1",
}

PROBE_ROUTES: list[tuple[str, str]] = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("POST", "/demo/upload"),
    ("GET", "/demo/jobs/b14_2_fixture_job/result"),
]


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


def _canonical_401() -> dict:
    return {
        "status": 401,
        "www_authenticate": CANONICAL_WWW_AUTHENTICATE,
        "body_len": 0,
        "error": None,
    }


def positive_observations() -> dict:
    observations = []
    for header_name in sorted(SURROGATE_HEADERS):
        for method, path in PROBE_ROUTES:
            observations.append({
                "method": method,
                "path": path,
                "surrogate_header_name": header_name,
                "response": _canonical_401(),
            })
    return {
        "case_name": "positive",
        "surrogate_headers_exercised": sorted(SURROGATE_HEADERS),
        "observations": observations,
    }


def _negative_header_accepted(target_header: str, target_method: str,
                              target_path: str, accepted_status: int,
                              case_name: str) -> dict:
    record = positive_observations()
    record["case_name"] = case_name
    for obs in record["observations"]:
        if (obs["surrogate_header_name"] == target_header
                and obs["method"] == target_method
                and obs["path"] == target_path):
            obs["response"] = {
                "status": accepted_status,
                "www_authenticate": "",
                "body_len": 0,
                "error": None,
            }
            break
    return record


def negative_observations() -> dict[str, dict]:
    return {
        "negative_x_forwarded_for_accepted": _negative_header_accepted(
            "X-Forwarded-For", "GET", "/demo/health",
            accepted_status=200,
            case_name="negative_x_forwarded_for_accepted",
        ),
        "negative_tailscale_user_login_accepted": _negative_header_accepted(
            "Tailscale-User-Login", "POST", "/demo/upload",
            accepted_status=202,
            case_name="negative_tailscale_user_login_accepted",
        ),
    }


def _write_case(case_root: pathlib.Path, record: dict) -> None:
    case_root.mkdir(parents=True, exist_ok=True)
    body = json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    (case_root / "observations.json").write_bytes(body)


def _wipe(p: pathlib.Path) -> None:
    if not p.exists():
        return
    for child in sorted(p.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    p.rmdir()


def run_validator_selftest(fixtures_root: pathlib.Path) -> str:
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATOR_PATH),
            "--selftest",
            "--fixtures", str(fixtures_root),
        ],
        capture_output=True, text=True,
    )
    out = proc.stdout.strip().splitlines()
    return out[-1] if out else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = (
        manifest_path.parent /
        "generate_fixture_validate_b14_2_no_network_trust_authority"
    )
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    _write_case(fixtures_root / "positive" / "positive", positive_observations())
    neg_records = negative_observations()
    for case_name, record in sorted(neg_records.items()):
        _write_case(fixtures_root / "negative" / case_name, record)

    aggregate_sentinel = run_validator_selftest(fixtures_root)

    adversarial_failures: list[str] = []
    per_case_observations: list[dict] = []
    for case_name, record in sorted(neg_records.items()):
        per_case_root = fixtures_root / "_per_case" / case_name
        _write_case(per_case_root / "positive" / case_name, record)
        decoy = positive_observations()
        decoy["case_name"] = f"decoy_negative_for_{case_name}"
        decoy["observations"][0]["response"] = {
            "status": 200,
            "www_authenticate": "",
            "body_len": 0,
            "error": None,
        }
        _write_case(per_case_root / "negative" / f"decoy_for_{case_name}", decoy)
        observed = run_validator_selftest(per_case_root)
        per_case_observations.append({
            "case_name": case_name,
            "observed_sentinel": observed,
        })
        if observed != VALIDATOR_FAIL:
            adversarial_failures.append(
                f"{case_name}: per-case adversarial expected {VALIDATOR_FAIL}, "
                f"got {observed!r}"
            )

    if aggregate_sentinel != VALIDATOR_OK:
        adversarial_failures.append(
            f"aggregate: expected {VALIDATOR_OK} got {aggregate_sentinel!r}"
        )

    _wipe(fixtures_root / "_per_case")

    manifest = {
        "validator": "validate_b14_2_no_network_trust_authority",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "aggregate_selftest_sentinel": aggregate_sentinel,
        "positive": [{
            "case_name": "positive",
            "root": "positive/positive",
            "expected_sentinel_under_aggregate_selftest": VALIDATOR_OK,
        }],
        "negative": [
            {
                "case_name": name,
                "root": f"negative/{name}",
                "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
                "observed_sentinel": next(
                    (o["observed_sentinel"] for o in per_case_observations
                     if o["case_name"] == name), None
                ),
            }
            for name in sorted(neg_records)
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
