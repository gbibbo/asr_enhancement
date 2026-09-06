#!/usr/bin/env python3
"""
Fixture generator paired with validate_b15_public_exposure_smoke_claim.

Materializes one positive and two negative declarative smoke-adjudication
samples and runs the validator in-process against each, asserting that
the positive sample passes and every negative sample is flagged with
B15_EPHEMERAL_URL_SUCCESS_CLAIM.

Negative cases exercised:
  * a SUCCESS_WITH_STABLE_NAMED_EXPOSURE claim without
    stable_named_exposure_supplied_by_reference (a success claim keyed
    on an ephemeral URL alone);
  * a BLOCKED_PENDING_HUMAN_ACTION claim with a null explicit_blocker_id.

The generator performs no public network call and starts no public
exposure.

Emits OK_FIXTURE_VALIDATE_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM on PASS or
B15_EPHEMERAL_URL_SUCCESS_CLAIM on FAIL.
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

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM"
SENTINEL_FAIL = "B15_EPHEMERAL_URL_SUCCESS_CLAIM"
VALIDATOR_OK = "OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED"
KINDS_ALLOWED = ["positive_and_negative"]

VALIDATOR_NAME = "validate_b15_public_exposure_smoke_claim"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "rp5" / f"{VALIDATOR_NAME}.py"


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


def render_adjudication(claim: dict, routing: dict | None = None) -> str:
    parts = ["# B15 Smoke Adjudication Fixture", ""]
    parts += [
        "```yaml",
        yaml.safe_dump(
            {"public_exposure_smoke_claim_record": claim},
            sort_keys=False, default_flow_style=False,
        ).rstrip("\n"),
        "```",
        "",
    ]
    if routing is not None:
        parts += [
            "```yaml",
            yaml.safe_dump(
                {"b15_decision_rule_routing_record": routing},
                sort_keys=False, default_flow_style=False,
            ).rstrip("\n"),
            "```",
            "",
        ]
    return "\n".join(parts) + "\n"


def success_claim() -> dict:
    return {
        "claim_id": "B15-SMOKE-CLAIM-001",
        "claim_status": "SUCCESS_WITH_STABLE_NAMED_EXPOSURE",
        "stable_named_exposure_supplied_by_reference": True,
        "all_coverage_items_passed": True,
        "explicit_blocker_id": None,
        "blocker_recovery_packet": None,
        "validator": VALIDATOR_NAME,
        "marker": SENTINEL_FAIL,
    }


def positive_body() -> str:
    return render_adjudication(success_claim())


def negative_bodies() -> dict[str, str]:
    ephemeral = success_claim()
    ephemeral["stable_named_exposure_supplied_by_reference"] = False

    blocked_no_id = {
        "claim_id": "B15-SMOKE-CLAIM-002",
        "claim_status": "BLOCKED_PENDING_HUMAN_ACTION",
        "stable_named_exposure_supplied_by_reference": False,
        "all_coverage_items_passed": False,
        "explicit_blocker_id": None,
        "blocker_recovery_packet": None,
        "validator": VALIDATOR_NAME,
        "marker": SENTINEL_FAIL,
    }
    return {
        "negative_ephemeral_url_success_claim": render_adjudication(ephemeral),
        "negative_blocked_without_explicit_blocker_id": render_adjudication(
            blocked_no_id
        ),
    }


def run_validator(adjudication_file: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--adjudication", str(adjudication_file),
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
    pos_file = pos_root / "smoke_adjudication.md"
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
        case_file = case_root / "smoke_adjudication.md"
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
