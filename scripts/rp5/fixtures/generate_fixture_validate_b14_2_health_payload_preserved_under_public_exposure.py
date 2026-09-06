#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_health_payload_preserved_under_public_exposure.py.

Materializes:
  * one positive observations.json (authenticated GET /demo/health
    status=200, body byte-exact b'{"status":"ok"}');
  * one negative observations.json (authenticated GET /demo/health body
    deviates from the canonical payload).

Drives the paired validator in --selftest mode and confirms the
per-case adversarial expectation.

Emits OK_FIXTURE_VALIDATE_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE on success
or B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE on adversarial
failure.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE"
VALIDATOR_OK = "OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE"
VALIDATOR_FAIL = "B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (REPO_ROOT / "scripts" / "rp5" /
                  "validate_b14_2_health_payload_preserved_under_public_exposure.py")
CANONICAL_BODY = b'{"status":"ok"}'
DEVIATED_BODY = b'{"status":"ok","extra":"leak"}'


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hash_tree(root: pathlib.Path) -> list[dict]:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            files.append({"path": str(p.relative_to(root)),
                          "sha256": sha256_bytes(data),
                          "size_bytes": len(data)})
    return files


def positive_record() -> dict:
    return {
        "case_name": "positive",
        "authenticated_demo_health": {
            "status": 200,
            "body_b64": base64.b64encode(CANONICAL_BODY).decode("ascii"),
            "body_len": len(CANONICAL_BODY),
            "error": None,
        },
    }


def negative_record() -> dict:
    return {
        "case_name": "negative_body_deviates_from_canonical",
        "authenticated_demo_health": {
            "status": 200,
            "body_b64": base64.b64encode(DEVIATED_BODY).decode("ascii"),
            "body_len": len(DEVIATED_BODY),
            "error": None,
        },
    }


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
                     "generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure")
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    _write(fixtures_root / "positive" / "positive", positive_record())
    neg = negative_record()
    _write(fixtures_root / "negative" / neg["case_name"], neg)

    aggregate = run_selftest(fixtures_root)

    per_case_root = fixtures_root / "_per_case" / neg["case_name"]
    _write(per_case_root / "positive" / neg["case_name"], neg)
    decoy = positive_record()
    decoy["case_name"] = "decoy_negative"
    decoy["authenticated_demo_health"]["status"] = 500
    _write(per_case_root / "negative" / "decoy_negative", decoy)
    per_case_sentinel = run_selftest(per_case_root)
    _wipe(fixtures_root / "_per_case")

    failures = []
    if aggregate != VALIDATOR_OK:
        failures.append(f"aggregate: expected {VALIDATOR_OK} got {aggregate!r}")
    if per_case_sentinel != VALIDATOR_FAIL:
        failures.append(
            f"per_case_{neg['case_name']}: expected {VALIDATOR_FAIL} got {per_case_sentinel!r}"
        )

    manifest = {
        "validator": "validate_b14_2_health_payload_preserved_under_public_exposure",
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
    if failures:
        for f in failures:
            print(f"adversarial_failure: {f}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
