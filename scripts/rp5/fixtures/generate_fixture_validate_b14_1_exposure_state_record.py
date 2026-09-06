#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_1_exposure_state_record.

Materializes positive and negative fixture records that exercise the
schema rules pinned by docs/plans/b14_1/state_packet_schemas.yaml:

  * positive: exposure_mode=loopback_only AND
    claim_status=BLOCKED_PENDING_HUMAN_ACTION with explicit_blocker_id
    non-null and blocker_recovery_packet present.
  * negative: each fixture violates exactly one rule:
      - exposure_mode_ephemeral_only: forbidden enum value.
      - claim_success_without_supplied_reference: SUCCESS_WITH_STABLE_NAMED_EXPOSURE
        but stable_named_exposure_supplied_by_reference=false.
      - claim_success_with_blocker: SUCCESS_WITH_STABLE_NAMED_EXPOSURE
        but explicit_blocker_id is non-null.
      - claim_blocked_without_blocker_id: BLOCKED_PENDING_HUMAN_ACTION
        but explicit_blocker_id is null.

Emits OK_FIXTURE_VALIDATE_B14_1_EXPOSURE_STATE on PASS or
B14_1_EPHEMERAL_URL_SUCCESS_CLAIM on FAIL.

Fixture files never contain hostname, credential, or token literals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_EXPOSURE_STATE"
SENTINEL_FAIL = "B14_1_EPHEMERAL_URL_SUCCESS_CLAIM"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "rp5" / "validate_b14_1_exposure_state_record.py"


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


def render_record(esr: dict, pecr: dict) -> str:
    def yaml_block(d: dict) -> str:
        lines = ["```yaml"]
        for k, v in d.items():
            lines.append(f"{k}: {v}")
        lines.append("```")
        return "\n".join(lines)
    return (
        "# Exposure State Record Fixture\n\n"
        "## exposure_state_record\n\n"
        + yaml_block(esr) + "\n\n"
        "## public_exposure_claim_record\n\n"
        + yaml_block(pecr) + "\n"
    )


def positive_record() -> str:
    esr = {
        "exposure_state_id": "ESR-FIXTURE-POSITIVE",
        "exposure_mode": "loopback_only",
        "public_exposure_flag": "PUBLIC_DEMO_EXPOSURE_false",
        "stable_hostname_source_reference": "env_var_name_PUBLIC_DEMO_STABLE_HOSTNAME",
        "stable_hostname_supplied_by_reference": "false",
        "blocker_if_unsupplied": "HAR-B14_1-STABLE-HOSTNAME-001",
        "validator": "validate_b14_1_exposure_state_record",
        "marker": SENTINEL_FAIL,
    }
    pecr = {
        "claim_id": "PECR-FIXTURE-POSITIVE",
        "claim_status": "BLOCKED_PENDING_HUMAN_ACTION",
        "stable_named_exposure_supplied_by_reference": "false",
        "explicit_blocker_id": "HAR-B14_1-STABLE-HOSTNAME-001",
        "blocker_recovery_packet": "RP-HUMAN-ACTION-REQUIRED",
        "validator": "validate_b14_1_exposure_state_record",
        "marker": SENTINEL_FAIL,
    }
    return render_record(esr, pecr)


def negative_records() -> dict[str, str]:
    base_esr = {
        "exposure_state_id": "ESR-FIXTURE-NEGATIVE",
        "exposure_mode": "loopback_only",
        "public_exposure_flag": "PUBLIC_DEMO_EXPOSURE_false",
        "stable_hostname_source_reference": "env_var_name_PUBLIC_DEMO_STABLE_HOSTNAME",
        "stable_hostname_supplied_by_reference": "false",
        "blocker_if_unsupplied": "HAR-B14_1-STABLE-HOSTNAME-001",
        "validator": "validate_b14_1_exposure_state_record",
        "marker": SENTINEL_FAIL,
    }
    base_pecr = {
        "claim_id": "PECR-FIXTURE-NEGATIVE",
        "claim_status": "BLOCKED_PENDING_HUMAN_ACTION",
        "stable_named_exposure_supplied_by_reference": "false",
        "explicit_blocker_id": "HAR-B14_1-STABLE-HOSTNAME-001",
        "blocker_recovery_packet": "RP-HUMAN-ACTION-REQUIRED",
        "validator": "validate_b14_1_exposure_state_record",
        "marker": SENTINEL_FAIL,
    }
    out: dict[str, str] = {}

    esr1 = dict(base_esr)
    esr1["exposure_mode"] = "ephemeral_only"
    out["negative_exposure_mode_ephemeral_only"] = render_record(esr1, base_pecr)

    pecr2 = dict(base_pecr)
    pecr2["claim_status"] = "SUCCESS_WITH_STABLE_NAMED_EXPOSURE"
    pecr2["stable_named_exposure_supplied_by_reference"] = "false"
    pecr2["explicit_blocker_id"] = "null"
    pecr2["blocker_recovery_packet"] = "null"
    out["negative_claim_success_without_supplied_reference"] = render_record(base_esr, pecr2)

    pecr3 = dict(base_pecr)
    pecr3["claim_status"] = "SUCCESS_WITH_STABLE_NAMED_EXPOSURE"
    pecr3["stable_named_exposure_supplied_by_reference"] = "true"
    pecr3["explicit_blocker_id"] = "HAR-B14_1-STABLE-HOSTNAME-001"
    out["negative_claim_success_with_blocker"] = render_record(base_esr, pecr3)

    pecr4 = dict(base_pecr)
    pecr4["claim_status"] = "BLOCKED_PENDING_HUMAN_ACTION"
    pecr4["explicit_blocker_id"] = "null"
    pecr4["blocker_recovery_packet"] = "null"
    out["negative_claim_blocked_without_blocker_id"] = render_record(base_esr, pecr4)

    return out


def run_validator(record_path: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(
        suffix=".md", delete=False, mode="w"
    ) as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--record", str(record_path),
                "--out", str(transcript),
            ],
            capture_output=True, text=True,
        )
        return proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    finally:
        transcript.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = manifest_path.parent / "generate_fixture_validate_b14_1_exposure_state_record"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    pos_root = fixtures_root / "positive"
    pos_root.mkdir(parents=True, exist_ok=True)
    pos_record = pos_root / "record.md"
    pos_record.write_text(positive_record(), encoding="utf-8")

    neg_root = fixtures_root / "negative"
    neg_root.mkdir(parents=True, exist_ok=True)
    neg_entries: list[dict] = []
    adversarial_failures: list[str] = []

    for case_name, body in negative_records().items():
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        record_file = case_root / "record.md"
        record_file.write_text(body, encoding="utf-8")
        sentinel = run_validator(record_file)
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

    pos_sentinel = run_validator(pos_record)
    if pos_sentinel != "OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED":
        adversarial_failures.append(
            f"positive: expected OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED got {pos_sentinel!r}"
        )

    positive_entry = {
        "case_name": "positive",
        "root": "positive",
        "expected_sentinel": "OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED",
        "observed_sentinel": pos_sentinel,
        "tree_files": hash_tree(pos_root),
    }

    manifest = {
        "validator": "validate_b14_1_exposure_state_record",
        "kind": args.kind,
        "owned_marker": SENTINEL_FAIL,
        "sentinel_pass": SENTINEL_PASS,
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
