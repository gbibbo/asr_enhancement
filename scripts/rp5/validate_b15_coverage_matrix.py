#!/usr/bin/env python3
"""
B15 multi-network smoke coverage-matrix validator.

Reads the declarative B15-01 deliverable (a markdown file carrying one
fenced ```yaml block holding a multi_network_smoke_coverage_record) and
asserts the schema rules pinned by
docs/plans/b15/state_packet_schemas.yaml > multi_network_smoke_coverage_record:

  * the record carries every required field;
  * vantage_points enumerates exactly the four required vantage points
    (windows_local, mobile_cellular, other_wifi, vpn_or_external_tester);
  * coverage_items enumerates exactly the nine required coverage items;
  * planned_status_per_item carries a legal planned status for every one
    of the nine coverage items;
  * the planned status EXPLICIT_NA_PROVIDER_DISABLED is used only for the
    assemblyai_provider coverage item.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED on PASS or
B15_MULTI_NETWORK_COVERAGE_GAP on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED"
SENTINEL_FAIL = "B15_MULTI_NETWORK_COVERAGE_GAP"

RECORD_KEY = "multi_network_smoke_coverage_record"

REQUIRED_FIELDS = [
    "coverage_id",
    "vantage_points",
    "coverage_items",
    "planned_status_per_item",
    "blocker_if_unsupplied",
    "validator",
    "marker",
]

REQUIRED_VANTAGE_POINTS = {
    "windows_local",
    "mobile_cellular",
    "other_wifi",
    "vpn_or_external_tester",
}

REQUIRED_COVERAGE_ITEMS = {
    "ten_curated_examples",
    "five_degradations",
    "whisper_provider",
    "assemblyai_provider",
    "upload_without_manual_ground_truth",
    "upload_with_manual_ground_truth",
    "upload_limit_enforced",
    "provider_quota_state",
    "mobile_layout",
}

LEGAL_PLANNED_STATUS = {
    "PENDING_OPERATOR_EVIDENCE",
    "COVERED",
    "BLOCKED_PENDING_HUMAN_ACTION",
    "EXPLICIT_NA_PROVIDER_DISABLED",
}

# EXPLICIT_NA_PROVIDER_DISABLED is legal only for this coverage item.
EXPLICIT_NA_ALLOWED_ITEM = "assemblyai_provider"

YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def _extract_record(text: str) -> tuple[dict | None, list[str]]:
    """Return (record, errors). record is the inner mapping of the
    multi_network_smoke_coverage_record found in a fenced yaml block."""
    errors: list[str] = []
    found: list[dict] = []
    for raw in YAML_BLOCK_RE.findall(text):
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            errors.append(f"a fenced yaml block failed to parse: {exc}")
            continue
        if not isinstance(doc, dict):
            continue
        if RECORD_KEY in doc and isinstance(doc[RECORD_KEY], dict):
            found.append(doc[RECORD_KEY])
        elif REQUIRED_FIELDS[0] in doc and "coverage_items" in doc:
            # record written without the top-level wrapper key
            found.append(doc)
    if not found:
        errors.append(
            f"no {RECORD_KEY} found in any fenced yaml block"
        )
        return None, errors
    if len(found) > 1:
        errors.append(
            f"more than one {RECORD_KEY} found ({len(found)}); expected exactly one"
        )
        return None, errors
    return found[0], errors


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    return []


def validate_record(record: dict) -> list[str]:
    failures: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in record or record[field] in (None, "", []):
            failures.append(f"required field missing or empty: {field}")

    vantage_points = set(_as_list(record.get("vantage_points")))
    missing_vp = REQUIRED_VANTAGE_POINTS - vantage_points
    extra_vp = vantage_points - REQUIRED_VANTAGE_POINTS
    if missing_vp:
        failures.append(
            f"vantage_points missing required values: {sorted(missing_vp)}"
        )
    if extra_vp:
        failures.append(
            f"vantage_points contains values outside the enum: {sorted(extra_vp)}"
        )

    coverage_items = set(_as_list(record.get("coverage_items")))
    missing_ci = REQUIRED_COVERAGE_ITEMS - coverage_items
    extra_ci = coverage_items - REQUIRED_COVERAGE_ITEMS
    if missing_ci:
        failures.append(
            f"coverage_items missing required values: {sorted(missing_ci)}"
        )
    if extra_ci:
        failures.append(
            f"coverage_items contains values outside the enum: {sorted(extra_ci)}"
        )

    planned = record.get("planned_status_per_item")
    if not isinstance(planned, dict):
        failures.append(
            "planned_status_per_item must be a mapping of "
            "coverage_item -> planned status"
        )
    else:
        planned_keys = set(planned.keys())
        missing_status = REQUIRED_COVERAGE_ITEMS - planned_keys
        extra_status = planned_keys - REQUIRED_COVERAGE_ITEMS
        if missing_status:
            failures.append(
                "planned_status_per_item missing entries for coverage items: "
                f"{sorted(missing_status)}"
            )
        if extra_status:
            failures.append(
                "planned_status_per_item has entries for unknown coverage items: "
                f"{sorted(extra_status)}"
            )
        for item, status in planned.items():
            if status not in LEGAL_PLANNED_STATUS:
                failures.append(
                    f"planned_status_per_item['{item}'] has illegal status "
                    f"'{status}'"
                )
            if (
                status == "EXPLICIT_NA_PROVIDER_DISABLED"
                and item != EXPLICIT_NA_ALLOWED_ITEM
            ):
                failures.append(
                    "planned_status_per_item: EXPLICIT_NA_PROVIDER_DISABLED is "
                    f"legal only for {EXPLICIT_NA_ALLOWED_ITEM}, found on '{item}'"
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    record_path = pathlib.Path(args.record)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# B15 Multi-Network Smoke Coverage Matrix Validation",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"record_path: {record_path}",
        "",
    ]

    if not record_path.exists():
        lines += [f"record file not found: {record_path}", "", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    text = record_path.read_text(encoding="utf-8")
    record, extract_errors = _extract_record(text)

    failures: list[str] = list(extract_errors)
    if record is not None:
        failures += validate_record(record)
        lines.append("## Record Summary")
        lines.append("")
        lines.append(f"- coverage_id: {record.get('coverage_id', '<missing>')}")
        lines.append(
            f"- vantage_points: {len(_as_list(record.get('vantage_points')))}"
        )
        lines.append(
            f"- coverage_items: {len(_as_list(record.get('coverage_items')))}"
        )
        planned = record.get("planned_status_per_item")
        if isinstance(planned, dict):
            lines.append(f"- planned_status_per_item entries: {len(planned)}")
        lines.append(f"- validator: {record.get('validator', '<missing>')}")
        lines.append(f"- marker: {record.get('marker', '<missing>')}")
        lines.append("")

    lines.append("## Rule Checks")
    lines.append("")
    if failures:
        for f in failures:
            lines.append(f"- [FAIL] {f}")
        lines += ["", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    lines += [
        "- [PASS] all four required vantage points enumerated",
        "- [PASS] all nine required coverage items enumerated",
        "- [PASS] every coverage item carries a legal planned status",
        "- [PASS] EXPLICIT_NA_PROVIDER_DISABLED restricted to assemblyai_provider",
        "",
        "## Result",
        "",
        "The multi_network_smoke_coverage_record is complete and every "
        "coverage item carries a legal planned status.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
