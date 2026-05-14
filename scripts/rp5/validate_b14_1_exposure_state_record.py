#!/usr/bin/env python3
"""
B14.1 exposure-state record validator.

Reads a declarative record (markdown carrying YAML blocks) and asserts
the two schema rules pinned by docs/plans/b14_1/state_packet_schemas.yaml:

  * exposure_state_record.exposure_mode MUST NOT be ephemeral_only.
  * public_exposure_claim_record.rules:
      - claim_status=SUCCESS_WITH_STABLE_NAMED_EXPOSURE
            ⇒ stable_named_exposure_supplied_by_reference=true
              AND explicit_blocker_id=null
      - claim_status starts with BLOCKED
            ⇒ explicit_blocker_id non-null
              AND blocker_recovery_packet exists

Emits OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED on PASS or
B14_1_EPHEMERAL_URL_SUCCESS_CLAIM on FAIL.

The validator never echoes hostname or credential material; record fields
are read only as enum / boolean / id-by-reference values.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

SENTINEL_PASS = "OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED"
SENTINEL_FAIL = "B14_1_EPHEMERAL_URL_SUCCESS_CLAIM"

EXPOSURE_MODE_FORBIDDEN = "ephemeral_only"
EXPOSURE_MODE_ALLOWED = ("loopback_only", "application_gated_stable_hostname")
CLAIM_STATUS_ALLOWED = (
    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE",
    "BLOCKED_PENDING_HUMAN_ACTION",
    "BLOCKED_PENDING_INFRA",
)


def _scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _parse_yaml_blocks(text: str) -> list[dict]:
    blocks: list[dict] = []
    in_block = False
    current: dict = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if line.strip().startswith("```yaml"):
            in_block = True
            current = {}
            continue
        if in_block and line.strip().startswith("```"):
            in_block = False
            blocks.append(current)
            current = {}
            continue
        if not in_block:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        current[key] = _scalar(value)
    return blocks


def _find_record(blocks: list[dict], required_keys: set[str]) -> dict | None:
    for block in blocks:
        if required_keys.issubset(block.keys()):
            return block
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    record_path = pathlib.Path(args.record)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not record_path.exists():
        out_path.write_text(
            f"{SENTINEL_FAIL}: record file not found: {record_path}\n"
        )
        print(SENTINEL_FAIL)
        return 1

    text = record_path.read_text(encoding="utf-8")
    blocks = _parse_yaml_blocks(text)

    esr = _find_record(blocks, {"exposure_mode", "public_exposure_flag"})
    pecr = _find_record(blocks, {"claim_status"})

    failures: list[str] = []

    if esr is None:
        failures.append("exposure_state_record block not found")
    else:
        mode = esr.get("exposure_mode", "")
        if mode == EXPOSURE_MODE_FORBIDDEN:
            failures.append("exposure_mode is the forbidden value ephemeral_only")
        elif mode not in EXPOSURE_MODE_ALLOWED:
            failures.append(
                f"exposure_mode '{mode}' is not in allowed set {EXPOSURE_MODE_ALLOWED}"
            )

    if pecr is None:
        failures.append("public_exposure_claim_record block not found")
    else:
        status = pecr.get("claim_status", "")
        if status not in CLAIM_STATUS_ALLOWED:
            failures.append(
                f"claim_status '{status}' is not in allowed set {CLAIM_STATUS_ALLOWED}"
            )
        elif status == "SUCCESS_WITH_STABLE_NAMED_EXPOSURE":
            supplied = pecr.get(
                "stable_named_exposure_supplied_by_reference", ""
            ).lower()
            blocker_id = pecr.get("explicit_blocker_id", "")
            if supplied != "true":
                failures.append(
                    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE requires "
                    "stable_named_exposure_supplied_by_reference=true"
                )
            if blocker_id and blocker_id.lower() != "null":
                failures.append(
                    "SUCCESS_WITH_STABLE_NAMED_EXPOSURE requires "
                    "explicit_blocker_id=null"
                )
        elif status.startswith("BLOCKED"):
            blocker_id = pecr.get("explicit_blocker_id", "")
            recovery = pecr.get("blocker_recovery_packet", "")
            if not blocker_id or blocker_id.lower() == "null":
                failures.append(
                    f"{status} requires non-null explicit_blocker_id"
                )
            if not recovery or recovery.lower() == "null":
                failures.append(
                    f"{status} requires blocker_recovery_packet to exist"
                )

    lines = [
        "# B14.1 Exposure State Record Validation",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"record_path: {record_path}",
        f"yaml_blocks_parsed: {len(blocks)}",
        "",
        "## Rule Checks",
        "",
    ]
    if esr is not None:
        lines.append(f"- exposure_mode: {esr.get('exposure_mode', '<missing>')}")
    if pecr is not None:
        lines.append(f"- claim_status: {pecr.get('claim_status', '<missing>')}")
        lines.append(
            f"- explicit_blocker_id: {pecr.get('explicit_blocker_id', '<missing>')}"
        )
        lines.append(
            "- blocker_recovery_packet: "
            f"{pecr.get('blocker_recovery_packet', '<missing>')}"
        )

    if failures:
        lines += ["", "## Failures", ""]
        for f in failures:
            lines.append(f"- {f}")
        lines += ["", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    lines += [
        "",
        "## Result",
        "",
        "exposure_state_record is stable-named-or-blocked-with-explicit-id.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
