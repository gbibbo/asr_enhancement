#!/usr/bin/env python3
"""
Fixture generator paired with
validate_b15_recruiter_gate_preserved_under_public_smoke.

Materializes one positive and two negative declarative smoke-results
samples and runs the validator in-process against each, asserting that
the positive sample passes and every negative sample is flagged with
B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE.

Negative cases exercised:
  * a record reporting recruiter_gate_observed_status=
    unauthenticated_access_observed;
  * a record reporting an illegal recruiter_gate_observed_status value.

The generator performs no public network call and starts no public
exposure.

Emits OK_FIXTURE_VALIDATE_B15_RECRUITER_GATE_PRESERVED on PASS or
B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE on FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

import yaml

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B15_RECRUITER_GATE_PRESERVED"
SENTINEL_FAIL = "B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE"
VALIDATOR_OK = "OK_B15_RECRUITER_GATE_PRESERVED"
KINDS_ALLOWED = ["positive_and_negative"]

VALIDATOR_NAME = "validate_b15_recruiter_gate_preserved_under_public_smoke"
FIELD = "recruiter_gate_observed_status"
BAD_VALUE = "unauthenticated_access_observed"
ILLEGAL_VALUE = "network_trusted_bypass"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "rp5" / f"{VALIDATOR_NAME}.py"

ALL_VANTAGE_POINTS = [
    "windows_local",
    "mobile_cellular",
    "other_wifi",
    "vpn_or_external_tester",
]
ALL_COVERAGE_ITEMS = [
    "five_curated_examples",
    "five_degradations",
    "whisper_provider",
    "assemblyai_provider",
    "upload_without_manual_ground_truth",
    "upload_with_manual_ground_truth",
    "upload_limit_enforced",
    "provider_quota_state",
    "mobile_layout",
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


def good_record(vp: str) -> dict:
    return {
        "result_id": f"B15-SMOKE-RESULT-{vp}",
        "vantage_point": vp,
        "coverage_item_outcomes": {item: "COVERED" for item in ALL_COVERAGE_ITEMS},
        "recruiter_gate_observed_status": "authenticated_access_only",
        "quota_state_observed": "AssemblyAI available",
        "upload_limit_observed": "enforced",
        "mobile_layout_observed": "no_horizontal_scroll",
        "cached_example_observed": "all_curated_examples_resolved",
        "evidence_reference": f"B15-OPERATOR-EVIDENCE-{vp}",
        "har_reference": "HAR-B15-MULTI-NETWORK-SMOKE-001",
        "validator": VALIDATOR_NAME,
        "marker": SENTINEL_FAIL,
    }


def render_results(records: list[dict]) -> str:
    parts = ["# B15 Smoke Results Fixture", ""]
    for rec in records:
        block = yaml.safe_dump(
            {"multi_network_smoke_result_record": rec},
            sort_keys=False, default_flow_style=False,
        )
        parts += ["```yaml", block.rstrip("\n"), "```", ""]
    return "\n".join(parts) + "\n"


def positive_body() -> str:
    return render_results([good_record(vp) for vp in ALL_VANTAGE_POINTS])


def negative_bodies() -> dict[str, str]:
    bad = [good_record(vp) for vp in ALL_VANTAGE_POINTS]
    bad[0][FIELD] = BAD_VALUE
    illegal = [good_record(vp) for vp in ALL_VANTAGE_POINTS]
    illegal[1][FIELD] = ILLEGAL_VALUE
    return {
        f"negative_{BAD_VALUE}": render_results(bad),
        "negative_illegal_value": render_results(illegal),
    }


def run_validator(results_file: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--results", str(results_file),
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
    fixtures_root = manifest_path.parent / f"generate_fixture_{VALIDATOR_NAME}"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    adversarial_failures: list[str] = []

    pos_root = fixtures_root / "positive"
    pos_root.mkdir(parents=True, exist_ok=True)
    pos_file = pos_root / "smoke_results.md"
    pos_file.write_text(positive_body(), encoding="utf-8")
    pos_sentinel = run_validator(pos_file)
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

    neg_root = fixtures_root / "negative"
    neg_root.mkdir(parents=True, exist_ok=True)
    neg_entries: list[dict] = []
    for case_name, body in negative_bodies().items():
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        case_file = case_root / "smoke_results.md"
        case_file.write_text(body, encoding="utf-8")
        sentinel = run_validator(case_file)
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

    manifest = {
        "validator": VALIDATOR_NAME,
        "kind": args.kind,
        "owned_markers": [SENTINEL_FAIL],
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
