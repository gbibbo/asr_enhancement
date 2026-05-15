#!/usr/bin/env python3
"""
B15 public-exposure smoke-claim validator.

Reads the declarative B15-06 smoke-adjudication deliverable and asserts
the public_exposure_smoke_claim_record rules pinned by
docs/plans/b15/state_packet_schemas.yaml:

  * claim_status SUCCESS_WITH_STABLE_NAMED_EXPOSURE is legal only when
    stable_named_exposure_supplied_by_reference is true,
    all_coverage_items_passed is true, and explicit_blocker_id is null —
    a success claim must never be keyed on an ephemeral URL alone;
  * a claim_status beginning with BLOCKED requires a non-null
    explicit_blocker_id and a present blocker_recovery_packet;
  * claim_status FAILED_PENDING_PHASE_RETURN requires a
    b15_decision_rule_routing_record whose routing is not
    PROCEED_TO_B_HANDOFF.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED on PASS or
B15_EPHEMERAL_URL_SUCCESS_CLAIM on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED"
SENTINEL_FAIL = "B15_EPHEMERAL_URL_SUCCESS_CLAIM"

CLAIM_KEY = "public_exposure_smoke_claim_record"
ROUTING_KEY = "b15_decision_rule_routing_record"

CLAIM_STATUS_LEGAL = {
    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE",
    "BLOCKED_PENDING_HUMAN_ACTION",
    "BLOCKED_PENDING_INFRA",
    "FAILED_PENDING_PHASE_RETURN",
}
ROUTING_LEGAL = {
    "PROCEED_TO_B_HANDOFF",
    "RETURN_TO_B11",
    "RETURN_TO_B14",
    "RETURN_TO_B10",
    "RETURN_TO_B8",
    "BLOCKED_PENDING_HUMAN_ACTION",
}
CLAIM_REQUIRED_FIELDS = [
    "claim_id",
    "claim_status",
    "stable_named_exposure_supplied_by_reference",
    "all_coverage_items_passed",
    "explicit_blocker_id",
    "blocker_recovery_packet",
    "validator",
    "marker",
]

YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def extract(text: str, key: str) -> list[dict]:
    found: list[dict] = []
    for raw in YAML_BLOCK_RE.findall(text):
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict) and isinstance(doc.get(key), dict):
            found.append(doc[key])
    return found


def _is_true(value) -> bool:
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() == "true"


def _is_null(value) -> bool:
    if value is None:
        return True
    return isinstance(value, str) and value.strip().lower() in ("", "null", "none")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adjudication", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    adj_path = pathlib.Path(args.adjudication)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# B15 Public-Exposure Smoke-Claim Validation",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"adjudication_path: {adj_path}",
        "",
    ]

    if not adj_path.exists():
        lines += [f"adjudication file not found: {adj_path}", "", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    text = adj_path.read_text(encoding="utf-8")
    claims = extract(text, CLAIM_KEY)
    routings = extract(text, ROUTING_KEY)

    failures: list[str] = []
    if not claims:
        failures.append(f"no {CLAIM_KEY} found in the adjudication file")
    elif len(claims) > 1:
        failures.append(
            f"more than one {CLAIM_KEY} found ({len(claims)}); expected one"
        )

    claim = claims[0] if claims else {}
    if claim:
        for field in CLAIM_REQUIRED_FIELDS:
            if field not in claim:
                failures.append(f"required field missing: {field}")
        status = claim.get("claim_status")
        if status not in CLAIM_STATUS_LEGAL:
            failures.append(
                f"claim_status '{status}' is not a legal value "
                f"{sorted(CLAIM_STATUS_LEGAL)}"
            )
        elif status == "SUCCESS_WITH_STABLE_NAMED_EXPOSURE":
            if not _is_true(claim.get("stable_named_exposure_supplied_by_reference")):
                failures.append(
                    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE requires "
                    "stable_named_exposure_supplied_by_reference=true — a "
                    "success claim must not be keyed on an ephemeral URL alone"
                )
            if not _is_true(claim.get("all_coverage_items_passed")):
                failures.append(
                    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE requires "
                    "all_coverage_items_passed=true"
                )
            if not _is_null(claim.get("explicit_blocker_id")):
                failures.append(
                    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE requires "
                    "explicit_blocker_id=null"
                )
        elif status.startswith("BLOCKED"):
            if _is_null(claim.get("explicit_blocker_id")):
                failures.append(
                    f"{status} requires a non-null explicit_blocker_id"
                )
            if _is_null(claim.get("blocker_recovery_packet")):
                failures.append(
                    f"{status} requires blocker_recovery_packet to be present"
                )
        elif status == "FAILED_PENDING_PHASE_RETURN":
            non_proceed = [
                r for r in routings
                if r.get("routing") != "PROCEED_TO_B_HANDOFF"
            ]
            if not non_proceed:
                failures.append(
                    "FAILED_PENDING_PHASE_RETURN requires a "
                    "b15_decision_rule_routing_record with a routing other "
                    "than PROCEED_TO_B_HANDOFF"
                )

    for r in routings:
        routing = r.get("routing")
        if routing not in ROUTING_LEGAL:
            failures.append(
                f"{ROUTING_KEY} routing '{routing}' is not a legal value "
                f"{sorted(ROUTING_LEGAL)}"
            )

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- claim records: {len(claims)}")
    lines.append(f"- routing records: {len(routings)}")
    if claim:
        lines.append(f"- claim_status: {claim.get('claim_status', '<missing>')}")
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
        "- [PASS] the public-exposure smoke claim is a stable-named-exposure "
        "claim or an explicit blocker",
        "",
        "## Result",
        "",
        "The public-exposure smoke claim is stable-named or explicitly "
        "blocked; it is not keyed on an ephemeral URL alone.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
