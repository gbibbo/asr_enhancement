#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_recruiter_gate_preserved_under_public_exposure.py.

Materializes:
  * one positive observations.json (every committed /demo/* route returns
    canonical 401 challenge unauth and non-401 with credentials);
  * one negative observations.json (one /demo/* route returns 200 to an
    unauthenticated probe, simulating the recruiter dependency missing
    after a regression).

Drives the paired validator in --selftest mode against the aggregate
fixture tree and runs an adversarial per-case selftest where the
negative observation is recast as the positive case (the validator must
then emit B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE).

No public-network call. No literal public URL, hostname, auth-key, token,
password, or non-loopback IP committed.

Emits OK_FIXTURE_VALIDATE_B14_2_RECRUITER_GATE_PRESERVED on success or
B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE on any adversarial
failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_RECRUITER_GATE_PRESERVED"
SENTINEL_FAIL = "B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE"
VALIDATOR_OK = "OK_B14_2_RECRUITER_GATE_PRESERVED"
VALIDATOR_FAIL = "B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (REPO_ROOT / "scripts" / "rp5" /
                  "validate_b14_2_recruiter_gate_preserved_under_public_exposure.py")
RECRUITER_REALM = "asr-demo-recruiter"
CANONICAL_WWW = f'Basic realm="{RECRUITER_REALM}"'

DEMO_ROUTES = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("GET", "/demo/examples/b14_2_fixture/audio/clean"),
    ("GET", "/demo/examples/b14_2_fixture/audio/degraded/b14_2_fixture_degradation"),
    ("POST", "/demo/jobs"),
    ("POST", "/demo/run-cached"),
    ("POST", "/demo/upload"),
    ("GET", "/demo/providers/assemblyai/status"),
    ("GET", "/demo/jobs/b14_2_fixture_job"),
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


def positive_record() -> dict:
    observations = []
    for method, path in DEMO_ROUTES:
        observations.append({
            "method": method, "path": path,
            "unauth": {"status": 401, "www_authenticate": CANONICAL_WWW,
                       "body_len": 0, "error": None},
            "creds": {"status": 200 if method == "GET" else 202,
                      "www_authenticate": "", "body_len": 0, "error": None},
        })
    return {"case_name": "positive", "credentialed_probe_attempted": True,
            "observations": observations}


def negative_record() -> dict:
    rec = positive_record()
    rec["case_name"] = "negative_unauthenticated_demo_route_returns_200"
    # Simulate /demo/upload missing the recruiter dependency.
    for obs in rec["observations"]:
        if obs["method"] == "POST" and obs["path"] == "/demo/upload":
            obs["unauth"] = {"status": 200, "www_authenticate": "",
                             "body_len": 0, "error": None}
            break
    return rec


def _write(case_root: pathlib.Path, record: dict) -> None:
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / "observations.json").write_bytes(
        json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    )


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
                     "generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure")
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    _write(fixtures_root / "positive" / "positive", positive_record())
    neg = negative_record()
    _write(fixtures_root / "negative" / neg["case_name"], neg)

    aggregate = run_validator_selftest(fixtures_root)

    # Adversarial per-case: cast the negative observation as positive
    # alongside a decoy negative that legitimately fails — validator must
    # emit VALIDATOR_FAIL.
    per_case_root = fixtures_root / "_per_case" / neg["case_name"]
    _write(per_case_root / "positive" / neg["case_name"], neg)
    decoy = positive_record()
    decoy["case_name"] = "decoy_negative"
    decoy["observations"][0]["unauth"]["status"] = 200
    _write(per_case_root / "negative" / "decoy_negative", decoy)
    per_case_sentinel = run_validator_selftest(per_case_root)
    _wipe(fixtures_root / "_per_case")

    adversarial_failures = []
    if aggregate != VALIDATOR_OK:
        adversarial_failures.append(f"aggregate: expected {VALIDATOR_OK} got {aggregate!r}")
    if per_case_sentinel != VALIDATOR_FAIL:
        adversarial_failures.append(
            f"per_case_{neg['case_name']}: expected {VALIDATOR_FAIL} got {per_case_sentinel!r}"
        )

    manifest = {
        "validator": "validate_b14_2_recruiter_gate_preserved_under_public_exposure",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "aggregate_selftest_sentinel": aggregate,
        "positive": [{"case_name": "positive", "root": "positive/positive",
                      "expected_sentinel_under_aggregate_selftest": VALIDATOR_OK}],
        "negative": [{"case_name": neg["case_name"],
                      "root": f"negative/{neg['case_name']}",
                      "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
                      "observed_sentinel": per_case_sentinel}],
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
