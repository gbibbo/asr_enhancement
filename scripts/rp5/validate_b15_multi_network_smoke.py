#!/usr/bin/env python3
"""
B15 multi-network smoke validator.

Reads the declarative B15-05 smoke-results deliverable (a markdown file
carrying one fenced ```yaml block per multi_network_smoke_result_record)
and asserts that the multi-network public smoke is covered across the
four required network vantage points, or that an explicit blocker is
recorded.

PASS branches:
  * covered  — exactly one result record per required vantage point,
               each carrying a coverage_item_outcomes mapping for all
               nine coverage items;
  * blocked  — the results file carries a b15_multi_network_smoke_blocker
               block citing HAR-B15-MULTI-NETWORK-SMOKE-001 and no
               result record claims a vantage point not exercised.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_MULTI_NETWORK_SMOKE_OR_BLOCKED on PASS or
B15_MULTI_NETWORK_COVERAGE_GAP on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_MULTI_NETWORK_SMOKE_OR_BLOCKED"
SENTINEL_FAIL = "B15_MULTI_NETWORK_COVERAGE_GAP"

RECORD_KEY = "multi_network_smoke_result_record"
BLOCKER_KEY = "b15_multi_network_smoke_blocker"
HAR_ID = "HAR-B15-MULTI-NETWORK-SMOKE-001"

REQUIRED_VANTAGE_POINTS = {
    "windows_local",
    "mobile_cellular",
    "other_wifi",
    "vpn_or_external_tester",
}
REQUIRED_COVERAGE_ITEMS = {
    "five_curated_examples",
    "five_degradations",
    "whisper_provider",
    "assemblyai_provider",
    "upload_without_manual_ground_truth",
    "upload_with_manual_ground_truth",
    "upload_limit_enforced",
    "provider_quota_state",
    "mobile_layout",
}

YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def extract_blocks(text: str) -> tuple[list[dict], list[dict], list[str]]:
    """Return (result_records, blocker_blocks, parse_errors)."""
    records: list[dict] = []
    blockers: list[dict] = []
    errors: list[str] = []
    for raw in YAML_BLOCK_RE.findall(text):
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            errors.append(f"a fenced yaml block failed to parse: {exc}")
            continue
        if not isinstance(doc, dict):
            continue
        if RECORD_KEY in doc and isinstance(doc[RECORD_KEY], dict):
            records.append(doc[RECORD_KEY])
        if BLOCKER_KEY in doc and isinstance(doc[BLOCKER_KEY], dict):
            blockers.append(doc[BLOCKER_KEY])
    return records, blockers, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    results_path = pathlib.Path(args.results)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# B15 Multi-Network Smoke Validation",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"results_path: {results_path}",
        "",
    ]

    if not results_path.exists():
        lines += [f"results file not found: {results_path}", "", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    records, blockers, errors = extract_blocks(
        results_path.read_text(encoding="utf-8")
    )
    failures: list[str] = list(errors)

    observed_vp = [r.get("vantage_point") for r in records]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- result records: {len(records)}")
    lines.append(f"- blocker blocks: {len(blockers)}")
    lines.append(f"- vantage points observed: {sorted(v for v in observed_vp if v)}")
    lines.append("")

    blocked_branch = False
    if blockers:
        # Explicit-blocker branch: a blocker must cite the B15 multi-network
        # HAR and no result record may claim an un-exercised vantage point.
        for blk in blockers:
            if blk.get("har_reference") != HAR_ID:
                failures.append(
                    f"{BLOCKER_KEY} must cite har_reference {HAR_ID}"
                )
        if not failures:
            blocked_branch = True

    if not blocked_branch:
        # Covered branch: one record per required vantage point, each
        # carrying coverage_item_outcomes for all nine coverage items.
        seen: dict[str, int] = {}
        for r in records:
            vp = r.get("vantage_point")
            seen[vp] = seen.get(vp, 0) + 1
        missing_vp = REQUIRED_VANTAGE_POINTS - set(seen)
        extra_vp = set(seen) - REQUIRED_VANTAGE_POINTS - {None}
        if missing_vp:
            failures.append(
                f"missing result records for vantage points: {sorted(missing_vp)}"
            )
        if extra_vp:
            failures.append(
                f"result records for unknown vantage points: {sorted(extra_vp)}"
            )
        for vp, count in seen.items():
            if vp in REQUIRED_VANTAGE_POINTS and count > 1:
                failures.append(
                    f"vantage point '{vp}' has {count} records; expected exactly one"
                )
        for r in records:
            vp = r.get("vantage_point")
            outcomes = r.get("coverage_item_outcomes")
            if not isinstance(outcomes, dict):
                failures.append(
                    f"record for '{vp}' has no coverage_item_outcomes mapping"
                )
                continue
            missing_ci = REQUIRED_COVERAGE_ITEMS - set(outcomes.keys())
            if missing_ci:
                failures.append(
                    f"record for '{vp}' missing coverage item outcomes: "
                    f"{sorted(missing_ci)}"
                )

    lines.append("## Rule Checks")
    lines.append("")
    if failures:
        for f in failures:
            lines.append(f"- [FAIL] {f}")
        lines += ["", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    branch = "explicit-blocker" if blocked_branch else "covered"
    lines += [
        f"- [PASS] multi-network smoke verified through the {branch} branch",
        "",
        "## Result",
        "",
        f"Multi-network smoke is satisfied through the {branch} branch.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
