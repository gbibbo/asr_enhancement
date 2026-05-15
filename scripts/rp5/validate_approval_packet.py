#!/usr/bin/env python3
"""
Reusable protocol validator: approval-packet / human-action-request checker.

Materialized by the B15-03 scope-change repair (orchestrator decision
APPROVE_SCOPE_CHANGE_EXECUTION, scope=scope_change, task_id=B15-03). It was
previously referenced by the B15 plan as a reusable protocol validator
"invoked directly" -- including by recovery packet RP-HUMAN-ACTION-REQUEST-
MALFORMED for human_action_request wrappers -- but had never been
materialized in reachable HEAD.

Validates wrapper-shaped packets against docs/plans/b15/state_packet_schemas
.yaml in two modes:

  * approval mode -- an ORCHESTRATOR_DECISION approval packet: a single
    top-level key `ORCHESTRATOR_DECISION` carrying the 8 approval_packet
    fields (orchestrator_plan section 2 / schema approval_packet);
  * human_action mode -- a human_action_request wrapper carrying the 10
    human_action_request fields. When the packet is a b15_human_action_packet,
    every entry in human_action_requests is validated as a human_action_request.

The packet file may be a markdown file embedding one or more fenced ```yaml
blocks, or a plain .yaml / .yml file. Mode is auto-detected by default and
may be pinned with --mode.

Pure: reads the schema file and the packet file, writes only the optional
--out report (default under /tmp). No network call, no project-state
mutation.

Emits OK_APPROVAL_PACKET on PASS. On FAIL emits APPROVAL_PACKET_MALFORMED
(approval mode) or HUMAN_ACTION_REQUEST_MALFORMED (human_action mode).
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_APPROVAL_PACKET"
FAIL_APPROVAL = "APPROVAL_PACKET_MALFORMED"
FAIL_HUMAN_ACTION = "HUMAN_ACTION_REQUEST_MALFORMED"

DEFAULT_SCHEMAS = "docs/plans/b15/state_packet_schemas.yaml"
DEFAULT_OUT = "/tmp/validate_approval_packet_out.md"

APPROVAL_WRAPPER_KEY = "ORCHESTRATOR_DECISION"
HUMAN_ACTION_PACKET_KEY = "b15_human_action_packet"
HUMAN_ACTION_REQUEST_KEY = "human_action_request"

_YAML_BLOCK = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def _extract_yaml_mappings(packet_path: pathlib.Path):
    text = packet_path.read_text()
    raw_blocks = []
    if packet_path.suffix.lower() in (".yaml", ".yml"):
        raw_blocks.append(text)
    raw_blocks.extend(_YAML_BLOCK.findall(text))
    mappings = []
    for raw in raw_blocks:
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict):
            mappings.append(doc)
    return mappings


def _required_fields(schemas: dict, key: str):
    entry = schemas.get(key, {})
    if isinstance(entry, dict):
        return entry.get("required_fields") or entry.get("fields") or []
    return []


def _detect_mode(mappings, forced):
    """Return (mode, payload) where payload is mode-specific."""
    if forced == "approval":
        for m in mappings:
            if APPROVAL_WRAPPER_KEY in m:
                return "approval", m
        return "approval", mappings[0] if mappings else None
    if forced == "human_action":
        for m in mappings:
            if HUMAN_ACTION_PACKET_KEY in m:
                return "human_action", m
        for m in mappings:
            if HUMAN_ACTION_REQUEST_KEY in m:
                return "human_action", m
        return "human_action", mappings[0] if mappings else None
    # auto
    for m in mappings:
        if APPROVAL_WRAPPER_KEY in m:
            return "approval", m
    for m in mappings:
        if HUMAN_ACTION_PACKET_KEY in m:
            return "human_action", m
    for m in mappings:
        if HUMAN_ACTION_REQUEST_KEY in m:
            return "human_action", m
    return None, None


def _validate_approval(mapping, schemas):
    failures = []
    notes = []
    keys = list(mapping.keys())
    if keys != [APPROVAL_WRAPPER_KEY]:
        failures.append(
            f"approval packet must have exactly one top-level key "
            f"'{APPROVAL_WRAPPER_KEY}'; observed {keys}"
        )
        return failures, notes
    body = mapping[APPROVAL_WRAPPER_KEY]
    if not isinstance(body, dict):
        failures.append(f"'{APPROVAL_WRAPPER_KEY}' body is not a mapping")
        return failures, notes
    required = _required_fields(schemas, "approval_packet")
    missing = [f for f in required if f not in body]
    if missing:
        failures.append(f"approval packet missing required fields: {missing}")
    else:
        notes.append(f"all {len(required)} approval_packet fields present")
    return failures, notes


def _validate_human_action(payload, schemas):
    failures = []
    notes = []
    required = _required_fields(schemas, "human_action_request")
    requests = []
    if HUMAN_ACTION_PACKET_KEY in payload:
        packet = payload[HUMAN_ACTION_PACKET_KEY]
        if not isinstance(packet, dict):
            failures.append(f"'{HUMAN_ACTION_PACKET_KEY}' body is not a mapping")
            return failures, notes
        packet_required = _required_fields(schemas, HUMAN_ACTION_PACKET_KEY)
        missing_pkt = [f for f in packet_required if f not in packet]
        if missing_pkt:
            failures.append(
                f"{HUMAN_ACTION_PACKET_KEY} missing required fields: {missing_pkt}"
            )
        entries = packet.get("human_action_requests")
        if not isinstance(entries, list) or not entries:
            failures.append(
                f"{HUMAN_ACTION_PACKET_KEY}.human_action_requests must be a "
                f"non-empty list"
            )
        else:
            requests = entries
            notes.append(
                f"{HUMAN_ACTION_PACKET_KEY} carries {len(entries)} "
                f"human_action_request entr(y/ies)"
            )
    elif HUMAN_ACTION_REQUEST_KEY in payload:
        body = payload[HUMAN_ACTION_REQUEST_KEY]
        requests = [body] if isinstance(body, dict) else []
        if not requests:
            failures.append(f"'{HUMAN_ACTION_REQUEST_KEY}' body is not a mapping")
    else:
        requests = [payload]

    for idx, req in enumerate(requests):
        if not isinstance(req, dict):
            failures.append(f"human_action_request entry #{idx} is not a mapping")
            continue
        rid = req.get("request_id", f"#{idx}")
        missing = [f for f in required if f not in req]
        if missing:
            failures.append(
                f"human_action_request '{rid}' missing required fields: {missing}"
            )
        else:
            notes.append(
                f"human_action_request '{rid}': all {len(required)} fields present"
            )
    return failures, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas", default=DEFAULT_SCHEMAS,
                        help="path to the active B15 state_packet_schemas.yaml")
    parser.add_argument("--packet", required=True,
                        help="path to the packet file to validate")
    parser.add_argument("--mode", choices=["approval", "human_action", "auto"],
                        default="auto", help="validation mode (default: auto-detect)")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="path for the transient validation report")
    args = parser.parse_args()

    schemas_path = pathlib.Path(args.schemas)
    packet_path = pathlib.Path(args.packet)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Approval / Human-Action Packet Validation",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"schemas: {args.schemas}",
        f"packet: {args.packet}",
        f"mode_arg: {args.mode}",
    ]

    def _emit(sentinel, extra=None):
        block = list(lines)
        if extra:
            block += extra
        block += ["", sentinel]
        out_path.write_text("\n".join(block) + "\n")
        print(sentinel)

    if not schemas_path.is_file():
        _emit(FAIL_APPROVAL, [f"schema file not found: {args.schemas}"])
        return 1
    if not packet_path.is_file():
        _emit(FAIL_APPROVAL, [f"packet file not found: {args.packet}"])
        return 1

    schemas = yaml.safe_load(schemas_path.read_text())
    if not isinstance(schemas, dict):
        _emit(FAIL_APPROVAL, ["schema file did not parse to a mapping"])
        return 1

    mappings = _extract_yaml_mappings(packet_path)
    if not mappings:
        _emit(FAIL_APPROVAL,
              ["no fenced ```yaml block or YAML document parsed from the packet"])
        return 1

    mode, payload = _detect_mode(mappings, args.mode)
    if mode is None or payload is None:
        _emit(FAIL_APPROVAL,
              ["could not detect packet mode: expected an ORCHESTRATOR_DECISION "
               "packet, a b15_human_action_packet, or a human_action_request"])
        return 1

    if mode == "approval":
        failures, notes = _validate_approval(payload, schemas)
        fail_sentinel = FAIL_APPROVAL
    else:
        failures, notes = _validate_human_action(payload, schemas)
        fail_sentinel = FAIL_HUMAN_ACTION

    body = ["", f"detected_mode: {mode}", "", "## Notes", ""]
    body += [f"- {n}" for n in notes] or ["- (none)"]

    if failures:
        body += ["", "## Failures", ""]
        body += [f"- {f}" for f in failures]
        _emit(fail_sentinel, body)
        return 1

    body += ["", "## Result", "",
             f"Packet conforms to the {mode} wrapper schema."]
    _emit(SENTINEL_PASS, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
