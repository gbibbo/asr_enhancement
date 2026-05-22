# B15 Plan Compile Report

generated_at_utc: 2026-05-22T19:54:49.584810
plan_dir: docs/plans/b15
plan_basename: b15
must_check_items: 15
failures: 0

## Must-Check Results

- [PASS] every_marker_in_registry_has_transition_row: all 27 markers have rows in orchestrator §6 marker registry
- [PASS] every_b15_marker_has_recovery_packet: all 27 markers have recovery packets in agent §11
- [PASS] every_validator_owned_failure_marker_exists: all validator owned failure markers in agent §9 resolve to the marker registry
- [PASS] every_task_next_state_exists: transition table has 21 data rows
- [PASS] every_B15_task_next_state_exists: all transition next-state tokens resolve to a B15 task id, a *-fix or *-BLOCKED_BY_HUMAN_ACTION variant, or a terminal state
- [PASS] every_report_referenced_by_agent_has_schema: all referenced report shapes in state_packet_schemas.yaml
- [PASS] every_approval_rule_has_schema_record: all 8 approval packet fields in schema and orchestrator
- [PASS] every_path_lock_reference_resolves_to_file_or_directory_policy: all 5 path locks defined in agent §1
- [PASS] every_action_has_matching_deliverable: all 8 tasks have contracts with deliverables
- [PASS] every_deliverable_has_producing_action: §0 artifacts list present with reports/rp5/b15_plan_compile.md
- [PASS] every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record: all 5 future constraints in orchestrator_plan.md
- [PASS] every_patch_with_N_locations_modified_has_acceptance_check_per_location: explicit_NA: plan-dir basename 'b15' declares no issue-and-patch ledger section; B15 is verification-only; parametric check satisfied vacuously
- [PASS] every_new_entity_has_full_registration_set_for_its_type: marker bijection: agent§0=27, agent§11=27, orch§6=27 (expected 27 each)
- [PASS] every_b15_har_record_has_recovery_packet: all 3 HAR records present in §15 and RP-HUMAN-ACTION-REQUIRED recovery packet present in §11
- [PASS] every_new_consumer_audited_pre_existing_data_or_explicit_NA: all B15 HARs carry a legal status (pre_declared_unresolved or partially_resolved_at_B14_1-04_threshold) in §15; tracker schema audited in §5

## Path Lock Summary

| Lock id | Max files |
|---|---|
| PL-B15-PLANS | 3 |
| PL-B15-REPORTS | 14 |
| PL-B15-SCRIPTS | 20 |
| PL-B15-TESTS | 14 |
| PL-B15-CONFIG | 1 |

## Future Constraints Preserved

| Constraint | Status |
|---|---|
| FC-B15-MULTI-NETWORK | preserved in orchestrator_plan.md §3 |
| FC-B14-1-PUBLIC-GATE | preserved in orchestrator_plan.md §3 |
| FC-HANDOFF-DATAMOVE1 | preserved in orchestrator_plan.md §3 |
| FC-BROUTE-FROZEN | preserved in orchestrator_plan.md §3 |
| FC-B14-0-GATE-PRESERVED | preserved in orchestrator_plan.md §3 |

## Carried Human Action Requests

| HAR id | Status entering B15 |
|---|---|
| HAR-B14_1-STABLE-HOSTNAME-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |
| HAR-B14_1-FUNNEL-CAPABILITY-001 | partially_resolved_at_B14_1-04_threshold; routed via RP-HUMAN-ACTION-REQUIRED |
| HAR-B15-MULTI-NETWORK-SMOKE-001 | pre_declared_unresolved; routed via RP-HUMAN-ACTION-REQUIRED |

## Result: OK_PLAN_COMPILES

All 15 must_check items passed.

OK_PLAN_COMPILES
