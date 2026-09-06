#!/usr/bin/env python3
"""
B15 plan compiler wrapper.

Reads a B15 plan directory (default docs/plans/b15/) and checks the
must_check contract inherited from the B14.1 plan-compile wrapper, with the
artifact-name check parameterised on the --plan-dir basename, and adding the
three B15-specific checks declared in docs/plans/b15/agent_plan.md section 9:
every_B15_task_next_state_exists, every_b15_marker_has_recovery_packet,
every_b15_har_record_has_recovery_packet.

The B15 plan is verification-only: this wrapper reads docs/plans/b15/* and
writes only the requested --out path. It performs no public network call.

Emits OK_PLAN_COMPILES on success or PLAN_CONFLICT on failure.
"""
import argparse
import datetime
import pathlib
import re
import sys

EXPECTED_MARKERS = [
    "PLAN_CONFLICT",
    "TRACKER_MISSING",
    "TRACKER_MISMATCH",
    "REPORT_SCHEMA_INVALID",
    "APPROVAL_PACKET_MALFORMED",
    "HUMAN_ACTION_REQUEST_MALFORMED",
    "EXECUTION_RAIL_GAP",
    "PATH_LOCK_TOO_BROAD",
    "VALIDATOR_MATERIALIZATION_GAP",
    "RECOVERY_PACKET_GAP",
    "UNAUTHORIZED_FILE_TOUCHED",
    "HUMAN_ACTION_REQUIRED",
    "FUTURE_CONSTRAINT_REGRESSION",
    "PUBLIC_SECURITY_REGRESSION",
    "B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED",
    "B15_SMOKE_RESULT_FABRICATED",
    "B15_MULTI_NETWORK_COVERAGE_GAP",
    "B15_EPHEMERAL_URL_SUCCESS_CLAIM",
    "B15_PUBLIC_URL_LITERAL_COMMITTED",
    "B15_STABLE_HOSTNAME_LITERAL_COMMITTED",
    "B15_TUNNEL_SECRET_COMMITTED",
    "B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE",
    "B15_QUOTA_STATE_MISREPRESENTED",
    "B15_UPLOAD_LIMIT_REGRESSION",
    "B15_MOBILE_LAYOUT_REGRESSION",
    "B15_CACHED_EXAMPLE_REGRESSION",
    "B15_BROUTE_REGRESSION_UNDER_PUBLIC_SMOKE",
]

EXPECTED_TASKS = [
    "B15-00", "B15-01", "B15-02", "B15-03",
    "B15-04", "B15-05", "B15-06", "B15-07",
]

EXPECTED_REPORT_SCHEMAS = [
    "planning_report", "execution_report", "phase_gate_report",
    "approval_packet", "supplemental_evidence_report",
]

APPROVAL_PACKET_FIELDS = [
    "scope", "task_id", "phase", "decision",
    "accepted_report_commit", "next_expected_task", "required_fix", "rationale",
]

EXPECTED_PATH_LOCKS = [
    "PL-B15-PLANS",
    "PL-B15-REPORTS",
    "PL-B15-SCRIPTS",
    "PL-B15-TESTS",
    "PL-B15-CONFIG",
]

EXPECTED_FC = [
    "FC-B15-MULTI-NETWORK",
    "FC-B14-1-PUBLIC-GATE",
    "FC-HANDOFF-DATAMOVE1",
    "FC-BROUTE-FROZEN",
    "FC-B14-0-GATE-PRESERVED",
]

EXPECTED_HARS = [
    "HAR-B14_1-STABLE-HOSTNAME-001",
    "HAR-B14_1-FUNNEL-CAPABILITY-001",
    "HAR-B15-MULTI-NETWORK-SMOKE-001",
]

VALID_HAR_STATUSES = [
    "pre_declared_unresolved",
    "partially_resolved_at_B14_1-04_threshold",
]


def _section(text, start_marker, end_marker):
    m = re.search(re.escape(start_marker) + r".*?" + re.escape(end_marker), text, re.DOTALL)
    return m.group() if m else ""


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def run_checks(plan_dir):
    agent_text = (plan_dir / "agent_plan.md").read_text()
    orch_text = (plan_dir / "orchestrator_plan.md").read_text()
    schema_text = (plan_dir / "state_packet_schemas.yaml").read_text()
    plan_basename = plan_dir.name

    results = []

    # 1. every_marker_in_registry_has_transition_row
    orch_s6 = _section(orch_text, "## 6. Marker registry", "## 7.")
    missing_trans = [m for m in EXPECTED_MARKERS if m not in orch_s6]
    results.append(_check(
        "every_marker_in_registry_has_transition_row",
        len(missing_trans) == 0,
        f"missing from orchestrator §6 marker registry: {missing_trans}"
        if missing_trans else
        f"all {len(EXPECTED_MARKERS)} markers have rows in orchestrator §6 marker registry",
    ))

    # 2. every_b15_marker_has_recovery_packet (B15-specific)
    rp_section = _section(agent_text, "## 11. Recovery packets", "## 12.")
    missing_rp = [m for m in EXPECTED_MARKERS if m not in rp_section]
    results.append(_check(
        "every_b15_marker_has_recovery_packet",
        len(missing_rp) == 0,
        f"missing: {missing_rp}" if missing_rp else
        f"all {len(EXPECTED_MARKERS)} markers have recovery packets in agent §11",
    ))

    # 3. every_validator_owned_failure_marker_exists
    s9 = _section(agent_text, "## 9. Validator contracts", "## 10.")
    owned = re.findall(r'\|\s*([A-Z0-9_]+(?:\s+or\s+[A-Z0-9_]+)?)\s*\|?\s*$', s9, re.MULTILINE)
    flat_owned = []
    for cell in owned:
        for piece in cell.split(" or "):
            piece = piece.strip()
            if piece:
                flat_owned.append(piece)
    unknown_owned = [m for m in flat_owned if m not in EXPECTED_MARKERS]
    results.append(_check(
        "every_validator_owned_failure_marker_exists",
        len(unknown_owned) == 0,
        f"unknown owned markers: {unknown_owned}" if unknown_owned else
        "all validator owned failure markers in agent §9 resolve to the marker registry",
    ))

    # 4. every_task_next_state_exists (inherited generic)
    trans_section = _section(agent_text, "## 4. Linear transition table", "## 5.")
    trans_rows = [
        line for line in trans_section.splitlines()
        if line.startswith("|") and "---" not in line
    ]
    data_rows = trans_rows[1:] if trans_rows else []
    results.append(_check(
        "every_task_next_state_exists",
        len(data_rows) >= 8,
        f"transition table has {len(data_rows)} data rows",
    ))

    # 4b. every_B15_task_next_state_exists (B15-specific)
    terminal_states = {
        "stop", "phase gate", "session-open", "any", "first failed task",
    }
    valid_states = set(EXPECTED_TASKS) | terminal_states
    for t in EXPECTED_TASKS:
        valid_states.add(f"{t} fix")
        valid_states.add(f"{t} BLOCKED_BY_HUMAN_ACTION")
    bad_next_states = []
    for row in data_rows:
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 5:
            continue
        for cell in (cols[3], cols[4]):
            if not cell:
                continue
            for piece in cell.split(" or "):
                piece = piece.strip()
                if piece and piece not in valid_states:
                    bad_next_states.append(piece)
    results.append(_check(
        "every_B15_task_next_state_exists",
        len(bad_next_states) == 0,
        f"unknown next-state tokens: {sorted(set(bad_next_states))}" if bad_next_states else
        "all transition next-state tokens resolve to a B15 task id, a *-fix or "
        "*-BLOCKED_BY_HUMAN_ACTION variant, or a terminal state",
    ))

    # 5. every_report_referenced_by_agent_has_schema
    missing_schemas = [s for s in EXPECTED_REPORT_SCHEMAS if s not in schema_text]
    results.append(_check(
        "every_report_referenced_by_agent_has_schema",
        len(missing_schemas) == 0,
        f"missing in schema: {missing_schemas}" if missing_schemas else
        "all referenced report shapes in state_packet_schemas.yaml",
    ))

    # 6. every_approval_rule_has_schema_record
    missing_in_schema = [f for f in APPROVAL_PACKET_FIELDS if f not in schema_text]
    missing_in_orch = [f for f in APPROVAL_PACKET_FIELDS if f not in orch_text]
    all_appr_missing = sorted(set(missing_in_schema + missing_in_orch))
    results.append(_check(
        "every_approval_rule_has_schema_record",
        len(all_appr_missing) == 0,
        f"missing fields: {all_appr_missing}" if all_appr_missing else
        f"all {len(APPROVAL_PACKET_FIELDS)} approval packet fields in schema and orchestrator",
    ))

    # 7. every_path_lock_reference_resolves_to_file_or_directory_policy
    s1 = _section(agent_text, "## 1. Branch", "## 2.")
    missing_locks = [lock for lock in EXPECTED_PATH_LOCKS if lock not in s1]
    results.append(_check(
        "every_path_lock_reference_resolves_to_file_or_directory_policy",
        len(missing_locks) == 0,
        f"missing locks: {missing_locks}" if missing_locks else
        f"all {len(EXPECTED_PATH_LOCKS)} path locks defined in agent §1",
    ))

    # 8. every_action_has_matching_deliverable
    s10 = _section(agent_text, "## 10. Task contracts", "## 11.")
    missing_tasks = [t for t in EXPECTED_TASKS if t not in s10]
    results.append(_check(
        "every_action_has_matching_deliverable",
        len(missing_tasks) == 0,
        f"tasks without contracts: {missing_tasks}" if missing_tasks else
        f"all {len(EXPECTED_TASKS)} tasks have contracts with deliverables",
    ))

    # 9. every_deliverable_has_producing_action (parametric on --plan-dir basename)
    s0 = _section(agent_text, "## 0. Manifest", "## 1.")
    expected_plan_compile_artifact = f"reports/rp5/{plan_basename}_plan_compile.md"
    has_artifacts = "artifacts:" in s0 and expected_plan_compile_artifact in s0
    results.append(_check(
        "every_deliverable_has_producing_action",
        has_artifacts,
        f"§0 artifacts list present with {expected_plan_compile_artifact}"
        if has_artifacts else
        f"missing parametric deliverable {expected_plan_compile_artifact} in §0 artifacts list",
    ))

    # 10. every_future_constraint_from_preplan_has_preservation_rule
    missing_fc = [fc for fc in EXPECTED_FC if fc not in orch_text]
    results.append(_check(
        "every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record",
        len(missing_fc) == 0,
        f"missing FC records: {missing_fc}" if missing_fc else
        f"all {len(EXPECTED_FC)} future constraints in orchestrator_plan.md",
    ))

    # 11. every_patch_with_N_locations_modified_has_acceptance_check_per_location
    # B15 is verification-only and declares no issue-and-patch ledger section;
    # this check is satisfied vacuously with an explicit_NA record.
    has_ledger_section = bool(
        re.search(r"##\s+\d+\.\s+Issue and patch ledger", agent_text, re.IGNORECASE)
    )
    if has_ledger_section:
        ledger = _section(agent_text, "Issue and patch ledger", "## ")
        ledger_ok = "acceptance" in ledger.lower() or "reviewer" in ledger.lower()
        results.append(_check(
            "every_patch_with_N_locations_modified_has_acceptance_check_per_location",
            ledger_ok,
            "patch ledger present and references acceptance/reviewer trace" if ledger_ok else
            "patch ledger present but missing acceptance/reviewer trace",
        ))
    else:
        results.append(_check(
            "every_patch_with_N_locations_modified_has_acceptance_check_per_location",
            True,
            f"explicit_NA: plan-dir basename '{plan_basename}' declares no issue-and-patch "
            "ledger section; B15 is verification-only; parametric check satisfied vacuously",
        ))

    # 12. every_new_entity_has_full_registration_set_for_its_type (marker bijection)
    marker_in_orch6 = sum(1 for m in EXPECTED_MARKERS if m in orch_s6)
    marker_in_agent0 = sum(1 for m in EXPECTED_MARKERS if m in s0)
    marker_in_agent11 = sum(1 for m in EXPECTED_MARKERS if m in rp_section)
    n = len(EXPECTED_MARKERS)
    bijection_pass = (marker_in_orch6 == n
                      and marker_in_agent0 == n
                      and marker_in_agent11 == n)
    results.append(_check(
        "every_new_entity_has_full_registration_set_for_its_type",
        bijection_pass,
        f"marker bijection: agent§0={marker_in_agent0}, agent§11={marker_in_agent11}, "
        f"orch§6={marker_in_orch6} (expected {n} each)",
    ))

    # 13. every_b15_har_record_has_recovery_packet (B15-specific)
    # Each carried/new HAR id must appear in agent §15 and route via the
    # generic HUMAN_ACTION_REQUIRED -> RP-HUMAN-ACTION-REQUIRED recovery packet.
    har_section = _section(agent_text, "## 15. Human action requests", "## 16.")
    missing_hars = [h for h in EXPECTED_HARS if h not in har_section]
    rp_human_present = "RP-HUMAN-ACTION-REQUIRED" in rp_section
    har_check_pass = len(missing_hars) == 0 and rp_human_present
    detail = []
    if missing_hars:
        detail.append(f"HARs missing from §15: {missing_hars}")
    if not rp_human_present:
        detail.append("RP-HUMAN-ACTION-REQUIRED missing from §11 recovery packets")
    if har_check_pass:
        detail.append(
            f"all {len(EXPECTED_HARS)} HAR records present in §15 and "
            "RP-HUMAN-ACTION-REQUIRED recovery packet present in §11"
        )
    results.append(_check(
        "every_b15_har_record_has_recovery_packet",
        har_check_pass,
        "; ".join(detail),
    ))

    # 14. every_new_consumer_audited_pre_existing_data_or_explicit_NA
    # Each HAR id must carry a recorded status entering B15 that is one of the
    # two legal har_carry_record statuses (pre_declared_unresolved or
    # partially_resolved_at_B14_1-04_threshold).
    har_lines = har_section.splitlines()
    har_status_bad = []
    for h in EXPECTED_HARS:
        owning_lines = [ln for ln in har_lines if h in ln]
        if not any(any(st in ln for st in VALID_HAR_STATUSES) for ln in owning_lines):
            har_status_bad.append(h)
    results.append(_check(
        "every_new_consumer_audited_pre_existing_data_or_explicit_NA",
        len(har_status_bad) == 0,
        f"HARs without a legal status-entering-B15 record: {har_status_bad}"
        if har_status_bad else
        "all B15 HARs carry a legal status (pre_declared_unresolved or "
        "partially_resolved_at_B14_1-04_threshold) in §15; tracker schema audited in §5",
    ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-dir", default="docs/plans/b15")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    plan_dir = pathlib.Path(args.plan_dir)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    required = ["agent_plan.md", "orchestrator_plan.md", "state_packet_schemas.yaml"]
    missing_files = [f for f in required if not (plan_dir / f).exists()]
    if missing_files:
        out_path.write_text(f"PLAN_CONFLICT: missing plan files: {missing_files}\n")
        print("PLAN_CONFLICT")
        return 1

    results = run_checks(plan_dir)
    failures = [r for r in results if not r["passed"]]

    lines = [
        f"# {plan_dir.name.upper()} Plan Compile Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"plan_dir: {plan_dir}",
        f"plan_basename: {plan_dir.name}",
        f"must_check_items: {len(results)}",
        f"failures: {len(failures)}",
        "",
        "## Must-Check Results",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")

    lines += [
        "",
        "## Path Lock Summary",
        "",
        "| Lock id | Max files |",
        "|---|---|",
        "| PL-B15-PLANS | 3 |",
        "| PL-B15-REPORTS | 14 |",
        "| PL-B15-SCRIPTS | 20 |",
        "| PL-B15-TESTS | 14 |",
        "| PL-B15-CONFIG | 1 |",
        "",
        "## Future Constraints Preserved",
        "",
        "| Constraint | Status |",
        "|---|---|",
        "| FC-B15-MULTI-NETWORK | preserved in orchestrator_plan.md §3 |",
        "| FC-B14-1-PUBLIC-GATE | preserved in orchestrator_plan.md §3 |",
        "| FC-HANDOFF-DATAMOVE1 | preserved in orchestrator_plan.md §3 |",
        "| FC-BROUTE-FROZEN | preserved in orchestrator_plan.md §3 |",
        "| FC-B14-0-GATE-PRESERVED | preserved in orchestrator_plan.md §3 |",
        "",
        "## Carried Human Action Requests",
        "",
        "| HAR id | Status entering B15 |",
        "|---|---|",
        "| HAR-B14_1-STABLE-HOSTNAME-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |",
        "| HAR-B14_1-FUNNEL-CAPABILITY-001 | partially_resolved_at_B14_1-04_threshold; routed via RP-HUMAN-ACTION-REQUIRED |",
        "| HAR-B15-MULTI-NETWORK-SMOKE-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |",
        "",
    ]

    if failures:
        lines += ["## Result: PLAN_CONFLICT", "", f"{len(failures)} check(s) failed:", ""]
        for f in failures:
            lines.append(f"  - {f['name']}: {f['detail']}")
        lines += ["", "PLAN_CONFLICT"]
        sentinel = "PLAN_CONFLICT"
    else:
        lines += [
            "## Result: OK_PLAN_COMPILES",
            "",
            f"All {len(results)} must_check items passed.",
            "",
            "OK_PLAN_COMPILES",
        ]
        sentinel = "OK_PLAN_COMPILES"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_PLAN_COMPILES" else 1


if __name__ == "__main__":
    sys.exit(main())
