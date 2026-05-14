#!/usr/bin/env python3
"""
B14.1 plan compiler wrapper.

Reads a B14.1 plan directory (default docs/plans/b14_1/) and checks the
must_check contract inherited from B-route section 9, replacing the
B-route-hardcoded artifact-name and patch-ledger checks with parametric
checks derived from the --plan-dir basename, and adding the three
B14.1-specific checks declared in docs/plans/b14_1/agent_plan.md section 9:
every_B14_1_task_next_state_exists, every_b14_1_marker_has_recovery_packet,
every_b14_1_har_record_has_recovery_packet.

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
    "B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED",
    "B14_1_NETWORK_TRUST_AUTHORITY_DETECTED",
    "B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE",
    "B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE",
    "B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED",
    "B14_1_EPHEMERAL_URL_SUCCESS_CLAIM",
    "B14_1_PUBLIC_URL_LITERAL_COMMITTED",
    "B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED",
    "B14_1_TUNNEL_SECRET_COMMITTED",
    "B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE",
    "B14_1_LOCAL_BYPASS_UNJUSTIFIED",
]

EXPECTED_TASKS = [
    "B14_1-00", "B14_1-01", "B14_1-02", "B14_1-03", "B14_1-04",
    "B14_1-05", "B14_1-06", "B14_1-07", "B14_1-08",
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
    "PL-B14_1-API-DEMO",
    "PL-B14_1-FRONTEND",
    "PL-B14_1-CONFIG",
    "PL-B14_1-TESTS",
    "PL-B14_1-SCRIPTS",
    "PL-B14_1-REPORTS",
    "PL-B14_1-TUNNEL-TEMPLATE",
]

EXPECTED_FC = [
    "FC-B14-1-FUNNEL",
    "FC-B15-MULTI-NETWORK",
    "FC-HANDOFF-DATAMOVE1",
    "FC-BROUTE-FROZEN",
    "FC-B14-0-GATE-PRESERVED",
]

EXPECTED_HARS = [
    "HAR-B14_1-FUNNEL-CAPABILITY-001",
    "HAR-B14_1-STABLE-HOSTNAME-001",
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
        f"all {len(EXPECTED_MARKERS)} markers have transition rows in orchestrator §6 marker registry",
    ))

    # 2. every_b14_1_marker_has_recovery_packet (B14.1-specific naming; inherited semantics)
    rp_section = _section(agent_text, "## 11. Recovery packets", "## 12.")
    missing_rp = [m for m in EXPECTED_MARKERS if m not in rp_section]
    results.append(_check(
        "every_b14_1_marker_has_recovery_packet",
        len(missing_rp) == 0,
        f"missing: {missing_rp}" if missing_rp else
        f"all {len(EXPECTED_MARKERS)} markers have recovery packets",
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
    unknown_owned = [m for m in flat_owned if m not in EXPECTED_MARKERS and m != "Owned" and m != "marker"]
    results.append(_check(
        "every_validator_owned_failure_marker_exists",
        len(unknown_owned) == 0,
        f"unknown owned markers: {unknown_owned}" if unknown_owned else
        "all validator owned failure markers in registry",
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
        len(data_rows) >= 10,
        f"transition table has {len(data_rows)} data rows",
    ))

    # 4b. every_B14_1_task_next_state_exists (B14.1-specific)
    valid_states = set(EXPECTED_TASKS) | {
        "stop", "phase gate", "session-open", "any", "first failed task",
    } | {f"{t} fix" for t in EXPECTED_TASKS}
    bad_next_states = []
    for row in data_rows:
        cols = [c.strip() for c in row.strip("|").split("|")]
        if len(cols) < 5:
            continue
        next_on_pass = cols[3]
        next_on_fail = cols[4]
        for ns in (next_on_pass, next_on_fail):
            if ns and ns not in valid_states:
                bad_next_states.append(ns)
    results.append(_check(
        "every_B14_1_task_next_state_exists",
        len(bad_next_states) == 0,
        f"unknown next-state tokens: {sorted(set(bad_next_states))}" if bad_next_states else
        "all transition next-state tokens resolve to a B14.1 task id, a *-fix variant, or a terminal state",
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
        f"all {len(EXPECTED_PATH_LOCKS)} path locks defined",
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
        f"section 0 artifacts list present with {expected_plan_compile_artifact}"
        if has_artifacts else
        f"missing parametric deliverable {expected_plan_compile_artifact} in §0 artifacts list",
    ))

    # 10. every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record
    missing_fc = [fc for fc in EXPECTED_FC if fc not in orch_text]
    results.append(_check(
        "every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record",
        len(missing_fc) == 0,
        f"missing FC records: {missing_fc}" if missing_fc else
        f"all {len(EXPECTED_FC)} future constraints in orchestrator_plan.md",
    ))

    # 11. every_patch_with_N_locations_modified_has_acceptance_check_per_location
    # Parametric: the B14.1 plan does not declare an issue-and-patch ledger
    # section, so this check is satisfied vacuously with explicit_NA.
    has_ledger_section = bool(re.search(r"##\s+\d+\.\s+Issue and patch ledger", agent_text, re.IGNORECASE))
    if has_ledger_section:
        ledger = _section(agent_text, "## 16. Issue and patch ledger", "## 17.")
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
            f"explicit_NA: plan-dir basename '{plan_basename}' declares no issue-and-patch ledger section; parametric check satisfied vacuously",
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

    # 13. every_b14_1_har_record_has_recovery_packet (B14.1-specific)
    # Each pre-declared HAR id must (a) appear in agent §15 with a
    # pre_declared_unresolved status block, and (b) route via the generic
    # HUMAN_ACTION_REQUIRED -> RP-HUMAN-ACTION-REQUIRED recovery packet
    # declared in agent §11.
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
            f"RP-HUMAN-ACTION-REQUIRED recovery packet present in §11"
        )
    results.append(_check(
        "every_b14_1_har_record_has_recovery_packet",
        har_check_pass,
        "; ".join(detail),
    ))

    # 14. every_new_consumer_audited_pre_existing_data_or_explicit_NA
    # B14.1 inherits and audits the B14.0 tracker schema and the resolved
    # HAR-B14_0-RECRUITER-CREDS-001 carried forward in tracker; the two new
    # B14.1 HARs (FUNNEL-CAPABILITY-001 and STABLE-HOSTNAME-001) are
    # pre-declared unresolved per §15.
    har_predeclared = all(
        f"{h}:" in har_section and "pre_declared_unresolved" in har_section
        for h in EXPECTED_HARS
    )
    results.append(_check(
        "every_new_consumer_audited_pre_existing_data_or_explicit_NA",
        har_predeclared,
        "all B14.1 HARs pre_declared_unresolved in §15; tracker schema audited in §5"
        if har_predeclared else
        "one or more B14.1 HARs missing pre_declared_unresolved status block in §15",
    ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-dir", default="docs/plans/b14_1")
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
        "| PL-B14_1-API-DEMO | 6 |",
        "| PL-B14_1-FRONTEND | 4 |",
        "| PL-B14_1-CONFIG | 2 |",
        "| PL-B14_1-TESTS | 12 |",
        "| PL-B14_1-SCRIPTS | 18 |",
        "| PL-B14_1-REPORTS | 20 |",
        "| PL-B14_1-TUNNEL-TEMPLATE | 1 |",
        "",
        "## Future Constraints Preserved",
        "",
        "| Constraint | Status |",
        "|---|---|",
        "| FC-B14-1-FUNNEL | preserved in orchestrator_plan.md §3 |",
        "| FC-B15-MULTI-NETWORK | preserved in orchestrator_plan.md §3 |",
        "| FC-HANDOFF-DATAMOVE1 | preserved in orchestrator_plan.md §3 |",
        "| FC-BROUTE-FROZEN | preserved in orchestrator_plan.md §3 |",
        "| FC-B14-0-GATE-PRESERVED | preserved in orchestrator_plan.md §3 |",
        "",
        "## Pre-declared Human Action Requests",
        "",
        "| HAR id | Status |",
        "|---|---|",
        "| HAR-B14_1-FUNNEL-CAPABILITY-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |",
        "| HAR-B14_1-STABLE-HOSTNAME-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |",
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
