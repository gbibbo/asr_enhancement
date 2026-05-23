# B14_2 Plan Compile Report

generated_at_utc: 2026-05-23T23:15:07.826407
plan_dir: docs/plans/b14_2
plan_basename: b14_2
must_check_items: 17
failures: 0

## Files Checked (sha256)

- docs/plans/b14_2/agent_plan.md sha256=b70b5254c15c1e355dbfba2423cfea86f08e850c24c34ef9e5950ce7122e01d6
- docs/plans/b14_2/orchestrator_plan.md sha256=58408413b6a79f51f8d8d3e75d3cfd46aab01651415f20a820b6202d541f5233
- docs/plans/b14_2/state_packet_schemas.yaml sha256=31fd1df0a6cd0e0ff5bbbf8918483e2c837faba4199774c103554c95e85d29ca

## Section Heading Checks

- agent_plan.md sections found: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
- orchestrator_plan.md sections found: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

## Must-Check Results (Marker / Validator / HAR / Task / FC / Approval-Packet Cross-Checks)

- [PASS] every_marker_in_registry_has_transition_row: all 30 markers have rows in orchestrator §6 marker registry
- [PASS] every_b14_2_marker_has_recovery_packet: all 30 markers have recovery packets in agent §11
- [PASS] every_validator_owned_failure_marker_exists: all validator owned failure markers in agent §9 resolve to the marker registry
- [PASS] every_task_next_state_exists: transition table has 10 data rows (expected >= 7)
- [PASS] every_B14_2_task_next_state_exists: all transition next-state tokens resolve to a B14.2 task id, a *-fix or *-BLOCKED_BY_HUMAN_ACTION variant, or a terminal state
- [PASS] every_report_referenced_by_agent_has_schema: all referenced report shapes in state_packet_schemas.yaml
- [PASS] every_approval_rule_has_schema_record: all 8 approval packet fields in schema and orchestrator
- [PASS] every_path_lock_reference_resolves_to_file_or_directory_policy: all 7 path locks defined in agent §1
- [PASS] every_action_has_matching_deliverable: all 7 tasks have contracts with deliverables
- [PASS] every_deliverable_has_producing_action: §0 artifacts list present with reports/rp5/b14_2_plan_compile.md
- [PASS] every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record: all 6 future constraints in orchestrator_plan.md
- [PASS] every_patch_with_N_locations_modified_has_acceptance_check_per_location: explicit_NA: plan-dir basename 'b14_2' declares no issue-and-patch ledger section; B14.2 is a repair microphase; parametric check satisfied vacuously
- [PASS] every_new_entity_has_full_registration_set_for_its_type: marker bijection: agent§0=30, agent§11=30, orch§6=30 (expected 30 each)
- [PASS] every_b14_2_har_record_has_recovery_packet: all 5 HAR records present in §15 and RP-HUMAN-ACTION-REQUIRED recovery packet present in §11
- [PASS] every_new_consumer_audited_pre_existing_data_or_explicit_NA: all 5 HARs carry a legal status (one of ['pre_declared_unresolved', 'pre_declared_conditional', 'resolved', 'by_reference_only', 'resolved_by_reference', 'resolved_with_observation_set']) in §15
- [PASS] carried_marker_clearance_policy_self_consistent: carried marker clearance policy consistent across agent §2, agent §19, and orchestrator §6
- [PASS] upload_with_gt_classification_rule_self_consistent: upload-with-GT classification rule consistent across agent §2, agent §10 B14_2-05, and schema

## Path Lock Summary

| Lock id | Max files | Source |
|---|---|---|
| PL-B14_2-API-DEMO | 6 | agent §1 |
| PL-B14_2-CONFIG | 2 | agent §1 |
| PL-B14_2-TESTS | 12 | agent §1 |
| PL-B14_2-SCRIPTS | 20 | agent §1 |
| PL-B14_2-REPORTS | 20 | agent §1 |
| PL-B14_2-TUNNEL-TEMPLATE | 1 | agent §1 |
| PL-B14_2-TRACKER | 1 | agent §1 |
| PROTOCOL-TRACKER | 1 | inherited |
| PROTOCOL-RP-REPORTS | 10 | inherited |

## Future Constraints Preserved

| Constraint | Status |
|---|---|
| FC-B15-MULTI-NETWORK | preserved in orchestrator_plan.md §3 |
| FC-B14-1-PUBLIC-GATE | preserved in orchestrator_plan.md §3 |
| FC-HANDOFF-DATAMOVE1 | preserved in orchestrator_plan.md §3 |
| FC-BROUTE-FROZEN | preserved in orchestrator_plan.md §3 |
| FC-B14-0-GATE-PRESERVED | preserved in orchestrator_plan.md §3 |
| FC-B15-FROZEN | preserved in orchestrator_plan.md §3 (new in B14.2) |

## Human Action Requests

| HAR id | Role in B14.2 |
|---|---|
| HAR-B14_1-STABLE-HOSTNAME-001 | carried resolved by-reference; consumed at B14_2-01 and B14_2-04 |
| HAR-B14_1-FUNNEL-CAPABILITY-001 | carried resolved by-reference; consumed at B14_2-01 and B14_2-04 |
| HAR-B15-MULTI-NETWORK-SMOKE-001 | carried resolved with observation set; consumed at B14_2-01 diagnostic and B14_2-05 classification |
| HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 | new in B14.2; pre_declared_unresolved; primary blocker for B14_2-04 closure and for carried-marker clearance |
| HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001 | new in B14.2; pre_declared_conditional; fires only if B14_2-04 evidence leaves classification undecidable |

## Carried Marker

- B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE: carried from B15; preserved active through B14_2-00..B14_2-05; clearance reserved for B14.2 PHASE_APPROVE on the gate-restored branch only; recovery packet RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE

## Carried-Marker Policy Self-Consistency

- agent §2 carried_marker_clearance_policy and agent §19 carried-marker accounting and orchestrator §6 registry row cross-validated by the carried_marker_clearance_policy_self_consistent must-check above

## Upload-With-GT Classification Self-Consistency

- agent §2 upload_with_gt_classification_rule branches ['linked_to_gate', 'independent_defer', 're_smoke_evidence_pending']
- agent §10 B14_2-05 task contract references the rule and the secondary-observation record
- schema upload_with_gt_secondary_observation_record enumerates the same three classification branches
- cross-validated by the upload_with_gt_classification_rule_self_consistent must-check above

## Approval-Packet Wrapper Cross-Check

- approval-packet fields validated against state_packet_schemas.yaml: ['scope', 'task_id', 'phase', 'decision', 'accepted_report_commit', 'next_expected_task', 'required_fix', 'rationale']
- cross-validated by the every_approval_rule_has_schema_record must-check above

## Banned-Phrase Scan Outcome

- raw hits (unfiltered): 1
- substantive hits (after documented filter excluding lines containing ['section_14', 'banned_phrases', 'forbidden_orchestrator_outputs']): 0

### Raw hits (informational)

- docs/plans/b14_2/agent_plan.md:422 (filtered as documented self-reference)

## Result: OK_PLAN_COMPILES

All 17 must_check items passed; banned-phrase scan yields zero substantive matches.

OK_PLAN_COMPILES
