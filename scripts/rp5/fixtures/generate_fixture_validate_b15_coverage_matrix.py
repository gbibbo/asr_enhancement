#!/usr/bin/env python3
"""
Fixture generator paired with validate_b15_coverage_matrix.

Materializes one positive and four negative declarative-record samples
for the B15 multi-network smoke coverage-matrix validator and runs the
validator in-process against each, asserting that the positive sample
passes and every negative sample is flagged with B15_MULTI_NETWORK_COVERAGE_GAP.

Negative cases exercised:
  * a record missing one required vantage point;
  * a record missing one required coverage item;
  * a record with an illegal planned status;
  * a record using EXPLICIT_NA_PROVIDER_DISABLED on a coverage item
    other than assemblyai_provider.

The generator performs no public network call.

Emits OK_FIXTURE_VALIDATE_B15_COVERAGE_MATRIX on PASS or
B15_MULTI_NETWORK_COVERAGE_GAP on FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B15_COVERAGE_MATRIX"
SENTINEL_FAIL = "B15_MULTI_NETWORK_COVERAGE_GAP"
VALIDATOR_OK = "OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "rp5" / "validate_b15_coverage_matrix.py"

ALL_VANTAGE_POINTS = [
    "windows_local",
    "mobile_cellular",
    "other_wifi",
    "vpn_or_external_tester",
]
ALL_COVERAGE_ITEMS = [
    "ten_curated_examples",
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


def render_record_md(vantage_points: list[str],
                     coverage_items: list[str],
                     planned: dict[str, str]) -> str:
    """Render a coverage-matrix markdown file embedding one record."""
    lines = [
        "# B15 Coverage Matrix Fixture",
        "",
        "```yaml",
        "multi_network_smoke_coverage_record:",
        "  coverage_id: B15-COVERAGE-MATRIX-FIXTURE",
        "  vantage_points:",
    ]
    for vp in vantage_points:
        lines.append(f"    - {vp}")
    lines.append("  coverage_items:")
    for ci in coverage_items:
        lines.append(f"    - {ci}")
    lines.append("  planned_status_per_item:")
    for item, status in planned.items():
        lines.append(f"    {item}: {status}")
    lines += [
        "  blocker_if_unsupplied: HAR-B15-MULTI-NETWORK-SMOKE-001",
        "  validator: validate_b15_coverage_matrix",
        "  marker: B15_MULTI_NETWORK_COVERAGE_GAP",
        "```",
        "",
    ]
    return "\n".join(lines)


def positive_body() -> str:
    planned = {item: "PENDING_OPERATOR_EVIDENCE" for item in ALL_COVERAGE_ITEMS}
    return render_record_md(ALL_VANTAGE_POINTS, ALL_COVERAGE_ITEMS, planned)


def negative_bodies() -> dict[str, str]:
    full_planned = {item: "PENDING_OPERATOR_EVIDENCE" for item in ALL_COVERAGE_ITEMS}

    # missing one vantage point
    missing_vp = render_record_md(
        ALL_VANTAGE_POINTS[:-1], ALL_COVERAGE_ITEMS, dict(full_planned)
    )

    # missing one coverage item (from both the list and the status map)
    short_items = ALL_COVERAGE_ITEMS[:-1]
    short_planned = {item: "PENDING_OPERATOR_EVIDENCE" for item in short_items}
    missing_item = render_record_md(
        ALL_VANTAGE_POINTS, short_items, short_planned
    )

    # illegal planned status value
    illegal_planned = dict(full_planned)
    illegal_planned["whisper_provider"] = "MAYBE_COVERED"
    illegal_status = render_record_md(
        ALL_VANTAGE_POINTS, ALL_COVERAGE_ITEMS, illegal_planned
    )

    # EXPLICIT_NA_PROVIDER_DISABLED on a non-assemblyai item
    na_planned = dict(full_planned)
    na_planned["whisper_provider"] = "EXPLICIT_NA_PROVIDER_DISABLED"
    na_misuse = render_record_md(
        ALL_VANTAGE_POINTS, ALL_COVERAGE_ITEMS, na_planned
    )

    return {
        "negative_missing_vantage_point": missing_vp,
        "negative_missing_coverage_item": missing_item,
        "negative_illegal_planned_status": illegal_status,
        "negative_explicit_na_on_non_assemblyai_item": na_misuse,
    }


def run_validator(record_file: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(
        suffix=".md", delete=False, mode="w"
    ) as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--record", str(record_file),
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
        manifest_path.parent / "generate_fixture_validate_b15_coverage_matrix"
    )
    fixtures_root.mkdir(parents=True, exist_ok=True)

    adversarial_failures: list[str] = []

    # positive
    pos_root = fixtures_root / "positive"
    pos_root.mkdir(parents=True, exist_ok=True)
    pos_file = pos_root / "coverage_matrix.md"
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

    # negatives
    neg_root = fixtures_root / "negative"
    neg_root.mkdir(parents=True, exist_ok=True)
    neg_entries: list[dict] = []
    for case_name, body in negative_bodies().items():
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        case_file = case_root / "coverage_matrix.md"
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
        "validator": "validate_b15_coverage_matrix",
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
