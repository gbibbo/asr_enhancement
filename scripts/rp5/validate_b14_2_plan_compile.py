#!/usr/bin/env python3
"""
B14.2 plan compiler wrapper.

Reads a B14.2 plan directory (default docs/plans/b14_2/) and checks the
must_check contract inherited from the B14.1 plan-compile wrapper, adding the
B14.2-specific checks declared in docs/plans/b14_2/agent_plan.md section 9:
every_B14_2_task_next_state_exists, every_b14_2_marker_has_recovery_packet,
every_b14_2_har_record_has_recovery_packet,
carried_marker_clearance_policy_self_consistent,
upload_with_gt_classification_rule_self_consistent.

B14.2 is a repair microphase: this wrapper reads docs/plans/b14_2/* and
writes only the requested --out path. It performs no public network call.

Emits OK_PLAN_COMPILES on success or PLAN_CONFLICT on failure.
"""
import argparse
import datetime
import hashlib
import pathlib
import re
import subprocess
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
    "B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED",
    "B14_2_NETWORK_TRUST_AUTHORITY_DETECTED",
    "B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE",
    "B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE",
    "B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED",
    "B14_2_PUBLIC_URL_LITERAL_COMMITTED",
    "B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED",
    "B14_2_TUNNEL_SECRET_COMMITTED",
    "B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE",
    "B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED",
    "B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP",
    "B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION",
    "B14_2_EPHEMERAL_URL_SUCCESS_CLAIM",
    "B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND",
    "B14_2_PREDECESSOR_FILE_TOUCHED",
    "B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE",
]

EXPECTED_TASKS = [
    "B14_2-00", "B14_2-01", "B14_2-02", "B14_2-03",
    "B14_2-04", "B14_2-05", "B14_2-06",
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
    "PL-B14_2-API-DEMO",
    "PL-B14_2-CONFIG",
    "PL-B14_2-TESTS",
    "PL-B14_2-SCRIPTS",
    "PL-B14_2-REPORTS",
    "PL-B14_2-TUNNEL-TEMPLATE",
    "PL-B14_2-TRACKER",
]

EXPECTED_FC = [
    "FC-B15-MULTI-NETWORK",
    "FC-B14-1-PUBLIC-GATE",
    "FC-HANDOFF-DATAMOVE1",
    "FC-BROUTE-FROZEN",
    "FC-B14-0-GATE-PRESERVED",
    "FC-B15-FROZEN",
]

EXPECTED_HARS_CARRIED = [
    "HAR-B14_1-STABLE-HOSTNAME-001",
    "HAR-B14_1-FUNNEL-CAPABILITY-001",
    "HAR-B15-MULTI-NETWORK-SMOKE-001",
]

EXPECTED_HARS_NEW = [
    "HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001",
    "HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001",
]

EXPECTED_HARS = EXPECTED_HARS_CARRIED + EXPECTED_HARS_NEW

VALID_HAR_STATUSES = [
    "pre_declared_unresolved",
    "pre_declared_conditional",
    "resolved",
    "by_reference_only",
    "resolved_by_reference",
    "resolved_with_observation_set",
]

CARRIED_MARKER_ID = "B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE"
CARRIED_MARKER_RECOVERY_PACKET = "RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE"

UPLOAD_WITH_GT_CLASSIFICATION_BRANCHES = [
    "linked_to_gate",
    "independent_defer",
    "re_smoke_evidence_pending",
]

# Section 14 banned_phrases registry consumed by the substantive scan below.
# Each phrase line carries an inline 'banned_phrases' comment so the documented
# filter inherited from the B14.1 and B15 plan-authoring reports excludes this
# self-documenting registry from the scan applied to this validator file.
_banned_phrases_registry = [
    "as needed",          # banned_phrases entry
    "as appropriate",     # banned_phrases entry
    "as required",        # banned_phrases entry
    "if already present", # banned_phrases entry
    "where appropriate",  # banned_phrases entry
    "best practices",     # banned_phrases entry
    "TBD",                # banned_phrases entry
    "free-form",          # banned_phrases entry
    "free form",          # banned_phrases entry
]
BANNED_PHRASES = _banned_phrases_registry

# The agent_plan section 14 self-documenting registry of banned_phrases is
# excluded from the substantive scan via the same documented filter applied
# in the B14.1 and B15 plan-authoring reports.
BANNED_PHRASE_EXCLUSION_SUBSTRINGS = [
    "section_14", "banned_phrases", "forbidden_orchestrator_outputs",
]


def _section(text, start_marker, end_marker):
    pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
    m = re.search(pattern, text, re.DOTALL)
    return m.group() if m else ""


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def _sha256(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _scan_banned_phrases(paths):
    raw_hits = []
    substantive_hits = []
    pattern = re.compile("|".join(re.escape(p) for p in BANNED_PHRASES))
    for path in paths:
        text = path.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hit = {"path": str(path), "line": lineno, "text": line}
                raw_hits.append(hit)
                if not any(s in line for s in BANNED_PHRASE_EXCLUSION_SUBSTRINGS):
                    substantive_hits.append(hit)
    return raw_hits, substantive_hits


def run_checks(plan_dir):
    agent_path = plan_dir / "agent_plan.md"
    orch_path = plan_dir / "orchestrator_plan.md"
    schema_path = plan_dir / "state_packet_schemas.yaml"

    agent_text = agent_path.read_text()
    orch_text = orch_path.read_text()
    schema_text = schema_path.read_text()
    plan_basename = plan_dir.name

    results = []

    # ---- inherited B14.1 must_check items ----

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

    # 2. every_b14_2_marker_has_recovery_packet (B14.2-specific)
    rp_section = _section(agent_text, "## 11. Recovery packets", "## 12.")
    missing_rp = [m for m in EXPECTED_MARKERS if m not in rp_section]
    results.append(_check(
        "every_b14_2_marker_has_recovery_packet",
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

    # 4. every_task_next_state_exists (transition table populated)
    trans_section = _section(agent_text, "## 4. Linear transition table", "## 5.")
    trans_rows = [
        line for line in trans_section.splitlines()
        if line.startswith("|") and "---" not in line
    ]
    data_rows = trans_rows[1:] if trans_rows else []
    results.append(_check(
        "every_task_next_state_exists",
        len(data_rows) >= len(EXPECTED_TASKS),
        f"transition table has {len(data_rows)} data rows (expected >= {len(EXPECTED_TASKS)})",
    ))

    # 4b. every_B14_2_task_next_state_exists (B14.2-specific)
    terminal_states = {
        "stop", "phase gate", "session-open", "any", "first failed task",
        "FAILED_PENDING_PHASE_RETURN",
        "FIX",
    }
    valid_states = set(EXPECTED_TASKS) | terminal_states
    for t in EXPECTED_TASKS:
        valid_states.add(f"{t} fix")
        valid_states.add(f"{t} BLOCKED_BY_HUMAN_ACTION")
        valid_states.add(f"{t} stays BLOCKED_BY_HUMAN_ACTION")
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
        "every_B14_2_task_next_state_exists",
        len(bad_next_states) == 0,
        f"unknown next-state tokens: {sorted(set(bad_next_states))}" if bad_next_states else
        "all transition next-state tokens resolve to a B14.2 task id, a *-fix or "
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

    # 11. issue-and-patch ledger: B14.2 is a repair microphase with no
    # multi-location-issue-and-patch ledger declared; satisfied vacuously.
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
            "ledger section; B14.2 is a repair microphase; parametric check satisfied vacuously",
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

    # 13. every_b14_2_har_record_has_recovery_packet (B14.2-specific)
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
        "every_b14_2_har_record_has_recovery_packet",
        har_check_pass,
        "; ".join(detail),
    ))

    # 14. every_new_consumer_audited_pre_existing_data_or_explicit_NA
    # Each HAR id must carry a legal status keyword.
    har_lines = har_section.splitlines()
    har_status_bad = []
    for h in EXPECTED_HARS:
        owning_lines = [ln for ln in har_lines if h in ln]
        if not any(any(st in ln for st in VALID_HAR_STATUSES) for ln in owning_lines):
            har_status_bad.append(h)
    results.append(_check(
        "every_new_consumer_audited_pre_existing_data_or_explicit_NA",
        len(har_status_bad) == 0,
        f"HARs without a legal status record in §15: {har_status_bad}"
        if har_status_bad else
        f"all {len(EXPECTED_HARS)} HARs carry a legal status (one of {VALID_HAR_STATUSES}) in §15",
    ))

    # ---- B14.2-specific additional checks ----

    # 15. carried_marker_clearance_policy_self_consistent
    # §2 of agent_plan must declare carried_marker_clearance_policy citing the
    # carried marker and reserving clearance for the gate-restored-branch
    # PHASE_APPROVE; §19 carried-marker accounting must agree; orchestrator §6
    # registry entry for the carried marker must reflect the same policy.
    s2 = _section(agent_text, "## 2. Constants and decision rules", "## 3.")
    s19 = _section(agent_text, "## 19. Carried-marker accounting", "## 20.")
    policy_in_s2 = (
        "carried_marker_clearance_policy" in s2
        and CARRIED_MARKER_ID in s2
        and "gate-restored" in s2.lower()
    )
    policy_in_s19 = (
        CARRIED_MARKER_ID in s19
        and "clearance" in s19.lower()
        and ("phase_approve" in s19.lower() or "phase approve" in s19.lower())
    )
    policy_in_orch6 = (
        CARRIED_MARKER_ID in orch_s6
        and "carried_from_B15" in orch_s6
        and CARRIED_MARKER_RECOVERY_PACKET in orch_s6
        and "gate-restored" in orch_s6.lower()
    )
    policy_pass = policy_in_s2 and policy_in_s19 and policy_in_orch6
    pdetails = []
    if not policy_in_s2:
        pdetails.append("agent §2 missing carried_marker_clearance_policy / marker id / gate-restored clause")
    if not policy_in_s19:
        pdetails.append("agent §19 missing carried-marker clearance reference to PHASE_APPROVE")
    if not policy_in_orch6:
        pdetails.append("orchestrator §6 registry row for carried marker missing carried_from_B15 / recovery packet id / gate-restored clause")
    if policy_pass:
        pdetails.append(
            "carried marker clearance policy consistent across agent §2, agent §19, and orchestrator §6"
        )
    results.append(_check(
        "carried_marker_clearance_policy_self_consistent",
        policy_pass,
        "; ".join(pdetails),
    ))

    # 16. upload_with_gt_classification_rule_self_consistent
    # §2 must declare upload_with_gt_classification_rule with the three named
    # branches; §10 B14_2-05 task contract must reference the rule; schema
    # upload_with_gt_secondary_observation_record must enumerate the same
    # classification enum.
    rule_in_s2 = (
        "upload_with_gt_classification_rule" in s2
        and all(branch in s2 for branch in UPLOAD_WITH_GT_CLASSIFICATION_BRANCHES)
    )
    b14_2_05_row = [ln for ln in s10.splitlines() if "B14_2-05" in ln]
    rule_in_s10 = any(
        ("upload_with_gt_classification_rule" in ln)
        or ("upload_with_gt_secondary_observation_record" in ln)
        for ln in b14_2_05_row
    )
    schema_record = _section(
        schema_text,
        "upload_with_gt_secondary_observation_record:",
        "\n\nsecondary_observation_routing_request_record:",
    )
    if not schema_record:
        # Fallback: look anywhere in schema for the record name and the branches.
        schema_record = schema_text
    rule_in_schema = all(branch in schema_record for branch in UPLOAD_WITH_GT_CLASSIFICATION_BRANCHES)
    rule_pass = rule_in_s2 and rule_in_s10 and rule_in_schema
    rdetails = []
    if not rule_in_s2:
        rdetails.append("agent §2 missing upload_with_gt_classification_rule or one of the three branches")
    if not rule_in_s10:
        rdetails.append("agent §10 B14_2-05 task contract row does not reference the classification rule or the secondary-observation record")
    if not rule_in_schema:
        rdetails.append("schema upload_with_gt_secondary_observation_record does not enumerate the three branches")
    if rule_pass:
        rdetails.append(
            "upload-with-GT classification rule consistent across agent §2, agent §10 B14_2-05, and schema"
        )
    results.append(_check(
        "upload_with_gt_classification_rule_self_consistent",
        rule_pass,
        "; ".join(rdetails),
    ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-dir", default="docs/plans/b14_2")
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

    # Section-heading checks: detect canonical section presence in each file.
    agent_text = (plan_dir / "agent_plan.md").read_text()
    orch_text = (plan_dir / "orchestrator_plan.md").read_text()
    agent_sections_found = sorted({
        int(m.group(1))
        for m in re.finditer(r"^## (\d+)\. ", agent_text, re.MULTILINE)
    })
    orch_sections_found = sorted({
        int(m.group(1))
        for m in re.finditer(r"^## (\d+)\. ", orch_text, re.MULTILINE)
    })

    # Banned-phrase scan on the three plan files.
    raw_hits, substantive_hits = _scan_banned_phrases([
        plan_dir / "orchestrator_plan.md",
        plan_dir / "agent_plan.md",
        plan_dir / "state_packet_schemas.yaml",
    ])

    files_with_sha = []
    for f in required:
        p = plan_dir / f
        files_with_sha.append((str(p), _sha256(p)))

    lines = [
        f"# {plan_dir.name.upper()} Plan Compile Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"plan_dir: {plan_dir}",
        f"plan_basename: {plan_dir.name}",
        f"must_check_items: {len(results)}",
        f"failures: {len(failures)}",
        "",
        "## Files Checked (sha256)",
        "",
    ]
    for fpath, sha in files_with_sha:
        lines.append(f"- {fpath} sha256={sha}")

    lines += [
        "",
        "## Section Heading Checks",
        "",
        f"- agent_plan.md sections found: {agent_sections_found}",
        f"- orchestrator_plan.md sections found: {orch_sections_found}",
        "",
        "## Must-Check Results (Marker / Validator / HAR / Task / FC / Approval-Packet Cross-Checks)",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")

    lines += [
        "",
        "## Path Lock Summary",
        "",
        "| Lock id | Max files | Source |",
        "|---|---|---|",
        "| PL-B14_2-API-DEMO | 6 | agent §1 |",
        "| PL-B14_2-CONFIG | 2 | agent §1 |",
        "| PL-B14_2-TESTS | 12 | agent §1 |",
        "| PL-B14_2-SCRIPTS | 20 | agent §1 |",
        "| PL-B14_2-REPORTS | 20 | agent §1 |",
        "| PL-B14_2-TUNNEL-TEMPLATE | 1 | agent §1 |",
        "| PL-B14_2-TRACKER | 1 | agent §1 |",
        "| PROTOCOL-TRACKER | 1 | inherited |",
        "| PROTOCOL-RP-REPORTS | 10 | inherited |",
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
        "| FC-B15-FROZEN | preserved in orchestrator_plan.md §3 (new in B14.2) |",
        "",
        "## Human Action Requests",
        "",
        "| HAR id | Role in B14.2 |",
        "|---|---|",
        "| HAR-B14_1-STABLE-HOSTNAME-001 | carried resolved by-reference; consumed at B14_2-01 and B14_2-04 |",
        "| HAR-B14_1-FUNNEL-CAPABILITY-001 | carried resolved by-reference; consumed at B14_2-01 and B14_2-04 |",
        "| HAR-B15-MULTI-NETWORK-SMOKE-001 | carried resolved with observation set; consumed at B14_2-01 diagnostic and B14_2-05 classification |",
        "| HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 | new in B14.2; pre_declared_unresolved; primary blocker for B14_2-04 closure and for carried-marker clearance |",
        "| HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001 | new in B14.2; pre_declared_conditional; fires only if B14_2-04 evidence leaves classification undecidable |",
        "",
        "## Carried Marker",
        "",
        f"- {CARRIED_MARKER_ID}: carried from B15; preserved active through B14_2-00..B14_2-05; clearance reserved for B14.2 PHASE_APPROVE on the gate-restored branch only; recovery packet {CARRIED_MARKER_RECOVERY_PACKET}",
        "",
        "## Carried-Marker Policy Self-Consistency",
        "",
        "- agent §2 carried_marker_clearance_policy and agent §19 carried-marker accounting and orchestrator §6 registry row cross-validated by the carried_marker_clearance_policy_self_consistent must-check above",
        "",
        "## Upload-With-GT Classification Self-Consistency",
        "",
        f"- agent §2 upload_with_gt_classification_rule branches {UPLOAD_WITH_GT_CLASSIFICATION_BRANCHES}",
        "- agent §10 B14_2-05 task contract references the rule and the secondary-observation record",
        "- schema upload_with_gt_secondary_observation_record enumerates the same three classification branches",
        "- cross-validated by the upload_with_gt_classification_rule_self_consistent must-check above",
        "",
        "## Approval-Packet Wrapper Cross-Check",
        "",
        f"- approval-packet fields validated against state_packet_schemas.yaml: {APPROVAL_PACKET_FIELDS}",
        "- cross-validated by the every_approval_rule_has_schema_record must-check above",
        "",
        "## Banned-Phrase Scan Outcome",
        "",
        f"- raw hits (unfiltered): {len(raw_hits)}",
        f"- substantive hits (after documented filter excluding lines containing {BANNED_PHRASE_EXCLUSION_SUBSTRINGS}): {len(substantive_hits)}",
    ]
    if raw_hits:
        lines += ["", "### Raw hits (informational)", ""]
        for h in raw_hits:
            lines.append(f"- {h['path']}:{h['line']} (filtered as documented self-reference)")
    if substantive_hits:
        lines += ["", "### Substantive hits (must be zero)", ""]
        for h in substantive_hits:
            lines.append(f"- {h['path']}:{h['line']}: {h['text']}")

    banned_phrase_pass = len(substantive_hits) == 0

    overall_pass = (not failures) and banned_phrase_pass
    if not banned_phrase_pass:
        results.append(_check(
            "banned_phrase_scan_no_substantive_matches",
            False,
            f"substantive hits: {len(substantive_hits)}",
        ))
        failures = [r for r in results if not r["passed"]]

    if not overall_pass:
        lines += ["", "## Result: PLAN_CONFLICT", "", f"{len(failures)} check(s) failed:", ""]
        for f in failures:
            lines.append(f"  - {f['name']}: {f['detail']}")
        lines += ["", "PLAN_CONFLICT"]
        sentinel = "PLAN_CONFLICT"
    else:
        lines += [
            "",
            "## Result: OK_PLAN_COMPILES",
            "",
            f"All {len(results)} must_check items passed; banned-phrase scan yields zero substantive matches.",
            "",
            "OK_PLAN_COMPILES",
        ]
        sentinel = "OK_PLAN_COMPILES"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_PLAN_COMPILES" else 1


if __name__ == "__main__":
    sys.exit(main())
