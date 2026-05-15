#!/usr/bin/env python3
"""
Reusable protocol helper: pending human-action-request summary.

Materialized by the B15-04 scope-change repair (orchestrator decision
APPROVE_SCOPE_CHANGE_EXECUTION, scope=scope_change, task_id=B15-04). It was
previously referenced by the B15 plan -- the B15-04 verification column and
recovery packet RP-HUMAN-ACTION-REQUIRED -- as a reusable protocol helper
"invoked directly" but had never been materialized in reachable HEAD.

This is a pure, read-only, local diagnostic helper. It reads the rp5 tracker
and summarizes every human-action request by request_id and status,
partitioned into resolved and pending. It supports the B15-04 diagnostic
need: confirming the two carried B14.1 HARs are resolved and that
HAR-B15-MULTI-NETWORK-SMOKE-001 remains pending.

Sources read from the tracker:
  * the top-level `human_action_requests` mapping;
  * `plan_authoring_approvals.B15.har_carried_forward` (a list), when present.

Secret hygiene: the helper prints only non-secret fields -- request_id,
status, result_kind, accepted_by_orchestrator_decision, evidence_reference,
and the boolean flags of supplied_values. It never prints a literal
hostname, public URL, auth-key, token, password, or any other secret. Any
non-boolean value of a flag-style field is omitted rather than printed.

It emits no OK_* sentinel: it is a diagnostic, not a pass/fail validator.
It exits 0 on a successful read and non-zero on a missing or unparseable
tracker. It mutates no project state and performs no network call.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import sys

import yaml

DEFAULT_TRACKER = "docs/progress/rp5_progress.yaml"
DEFAULT_OUT = "/tmp/print_pending_human_action_requests_out.md"

RESOLVED_STATUS = "resolved"

# String fields whose values are non-secret by design and safe to print.
SAFE_STRING_FIELDS = frozenset({
    "request_id", "status", "result_kind", "evidence_reference",
})


def _safe_value(key, value):
    """Render a value for display without leaking any secret literal."""
    if isinstance(value, bool):
        return str(value)
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if key in SAFE_STRING_FIELDS:
            return value
        return "<non-boolean value omitted>"
    return "<complex value omitted>"


def _collect_hars(tracker: dict):
    """Return {request_id: {status, fields}} merged from the two sources."""
    hars = {}

    section = tracker.get("human_action_requests")
    if isinstance(section, dict):
        for rid, rec in section.items():
            rec = rec if isinstance(rec, dict) else {}
            hars[rid] = {
                "status": rec.get("status", "unknown"),
                "source": "human_action_requests",
                "record": rec,
            }

    approvals = tracker.get("plan_authoring_approvals")
    if isinstance(approvals, dict):
        b15 = approvals.get("B15")
        carried = b15.get("har_carried_forward") if isinstance(b15, dict) else None
        if isinstance(carried, list):
            for entry in carried:
                if not isinstance(entry, dict):
                    continue
                rid = entry.get("id")
                if not rid:
                    continue
                if rid in hars:
                    hars[rid].setdefault("also_in", []).append(
                        "plan_authoring_approvals.B15.har_carried_forward"
                    )
                else:
                    hars[rid] = {
                        "status": entry.get("status", "unknown"),
                        "source": "plan_authoring_approvals.B15.har_carried_forward",
                        "record": entry,
                    }
    return hars


def _format_har(rid, info):
    rec = info["record"]
    lines = [
        f"- request_id: {rid}",
        f"  status: {info['status']}",
        f"  source: {info['source']}",
    ]
    for field in ("result_kind", "accepted_by_orchestrator_decision",
                  "evidence_reference"):
        if field in rec:
            lines.append(f"  {field}: {_safe_value(field, rec[field])}")
    supplied = rec.get("supplied_values")
    if isinstance(supplied, dict) and supplied:
        lines.append("  supplied_values:")
        for k, v in supplied.items():
            lines.append(f"    {k}: {_safe_value(k, v)}")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracker-path", default=DEFAULT_TRACKER,
                        help="path to the rp5 progress tracker")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="path for the transient summary report")
    args = parser.parse_args()

    tracker_path = pathlib.Path(args.tracker_path)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not tracker_path.is_file():
        msg = f"ERROR: tracker not found: {args.tracker_path}"
        out_path.write_text(msg + "\n")
        print(msg)
        return 1

    try:
        tracker = yaml.safe_load(tracker_path.read_text())
    except yaml.YAMLError as err:
        msg = f"ERROR: tracker did not parse as YAML: {err}"
        out_path.write_text(msg + "\n")
        print(msg)
        return 1
    if not isinstance(tracker, dict):
        msg = "ERROR: tracker did not parse to a mapping"
        out_path.write_text(msg + "\n")
        print(msg)
        return 1

    hars = _collect_hars(tracker)
    resolved = {r: i for r, i in hars.items() if i["status"] == RESOLVED_STATUS}
    pending = {r: i for r, i in hars.items() if i["status"] != RESOLVED_STATUS}

    lines = [
        "# Pending Human-Action Requests",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"tracker: {args.tracker_path}",
        f"human_action_requests_total: {len(hars)}",
        f"resolved: {len(resolved)}",
        f"pending: {len(pending)}",
        "",
        "## Resolved",
        "",
    ]
    if resolved:
        for rid in sorted(resolved):
            lines += _format_har(rid, resolved[rid])
    else:
        lines.append("- (none)")
    lines += ["", "## Pending", ""]
    if pending:
        for rid in sorted(pending):
            lines += _format_har(rid, pending[rid])
    else:
        lines.append("- (none)")
    lines.append("")

    text = "\n".join(lines) + "\n"
    out_path.write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
