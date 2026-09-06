# B14_1 Plan Compile Report

generated_at_utc: 2026-05-14T15:58:58.116983
plan_dir: docs/plans/b14_1
plan_basename: b14_1
must_check_items: 15
failures: 0

## Must-Check Results

- [PASS] every_marker_in_registry_has_transition_row: all 25 markers have transition rows in orchestrator §6 marker registry
- [PASS] every_b14_1_marker_has_recovery_packet: all 25 markers have recovery packets
- [PASS] every_validator_owned_failure_marker_exists: all validator owned failure markers in registry
- [PASS] every_task_next_state_exists: transition table has 11 data rows
- [PASS] every_B14_1_task_next_state_exists: all transition next-state tokens resolve to a B14.1 task id, a *-fix variant, or a terminal state
- [PASS] every_report_referenced_by_agent_has_schema: all referenced report shapes in state_packet_schemas.yaml
- [PASS] every_approval_rule_has_schema_record: all 8 approval packet fields in schema and orchestrator
- [PASS] every_path_lock_reference_resolves_to_file_or_directory_policy: all 7 path locks defined
- [PASS] every_action_has_matching_deliverable: all 9 tasks have contracts with deliverables
- [PASS] every_deliverable_has_producing_action: section 0 artifacts list present with reports/rp5/b14_1_plan_compile.md
- [PASS] every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record: all 5 future constraints in orchestrator_plan.md
- [PASS] every_patch_with_N_locations_modified_has_acceptance_check_per_location: explicit_NA: plan-dir basename 'b14_1' declares no issue-and-patch ledger section; parametric check satisfied vacuously
- [PASS] every_new_entity_has_full_registration_set_for_its_type: marker bijection: agent§0=25, agent§11=25, orch§6=25 (expected 25 each)
- [PASS] every_b14_1_har_record_has_recovery_packet: all 2 HAR records present in §15 and RP-HUMAN-ACTION-REQUIRED recovery packet present in §11
- [PASS] every_new_consumer_audited_pre_existing_data_or_explicit_NA: all B14.1 HARs pre_declared_unresolved in §15; tracker schema audited in §5

## Path Lock Summary

| Lock id | Max files |
|---|---|
| PL-B14_1-API-DEMO | 6 |
| PL-B14_1-FRONTEND | 4 |
| PL-B14_1-CONFIG | 2 |
| PL-B14_1-TESTS | 12 |
| PL-B14_1-SCRIPTS | 18 |
| PL-B14_1-REPORTS | 20 |
| PL-B14_1-TUNNEL-TEMPLATE | 1 |

## Future Constraints Preserved

| Constraint | Status |
|---|---|
| FC-B14-1-FUNNEL | preserved in orchestrator_plan.md §3 |
| FC-B15-MULTI-NETWORK | preserved in orchestrator_plan.md §3 |
| FC-HANDOFF-DATAMOVE1 | preserved in orchestrator_plan.md §3 |
| FC-BROUTE-FROZEN | preserved in orchestrator_plan.md §3 |
| FC-B14-0-GATE-PRESERVED | preserved in orchestrator_plan.md §3 |

## Pre-declared Human Action Requests

| HAR id | Status |
|---|---|
| HAR-B14_1-FUNNEL-CAPABILITY-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |
| HAR-B14_1-STABLE-HOSTNAME-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |

## Result: OK_PLAN_COMPILES

All 15 must_check items passed.

OK_PLAN_COMPILES
