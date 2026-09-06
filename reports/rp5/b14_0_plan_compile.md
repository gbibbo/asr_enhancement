# B14_0 Plan Compile Report

generated_at_utc: 2026-05-14T02:44:01.619469
plan_dir: docs/plans/b14_0
plan_basename: b14_0
must_check_items: 14
failures: 0

## Must-Check Results

- [PASS] every_marker_in_registry_has_transition_row: all 21 markers have transition rows in orchestrator §6 marker registry
- [PASS] every_marker_has_recovery_packet: all 21 markers have recovery packets
- [PASS] every_validator_owned_failure_marker_exists: all validator owned failure markers in registry
- [PASS] every_task_next_state_exists: transition table has 11 data rows
- [PASS] every_B14_0_task_next_state_exists: all transition next-state tokens resolve to a B14.0 task id, a *-fix variant, or a terminal state
- [PASS] every_report_referenced_by_agent_has_schema: all referenced report shapes in state_packet_schemas.yaml
- [PASS] every_approval_rule_has_schema_record: all 8 approval packet fields in schema and orchestrator
- [PASS] every_path_lock_reference_resolves_to_file_or_directory_policy: all 6 path locks defined
- [PASS] every_action_has_matching_deliverable: all 9 tasks have contracts with deliverables
- [PASS] every_deliverable_has_producing_action: section 0 artifacts list present with reports/rp5/b14_0_plan_compile.md
- [PASS] every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record: all 4 future constraints in orchestrator_plan.md
- [PASS] every_patch_with_N_locations_modified_has_acceptance_check_per_location: explicit_NA: plan-dir basename 'b14_0' declares no issue-and-patch ledger section; parametric check satisfied vacuously
- [PASS] every_new_entity_has_full_registration_set_for_its_type: marker bijection: agent§0=21, agent§11=21, orch§6=21 (expected 21 each)
- [PASS] every_new_consumer_audited_pre_existing_data_or_explicit_NA: HAR-B14_0-RECRUITER-CREDS-001 pre_declared_unresolved; tracker schema audited in §5

## Path Lock Summary

| Lock id | Max files |
|---|---|
| PL-B14_0-API-DEMO | 6 |
| PL-B14_0-FRONTEND | 8 |
| PL-B14_0-CONFIG | 2 |
| PL-B14_0-TESTS | 12 |
| PL-B14_0-SCRIPTS | 18 |
| PL-B14_0-REPORTS | 20 |

## Future Constraints Preserved

| Constraint | Status |
|---|---|
| FC-B14-1-FUNNEL | preserved in orchestrator_plan.md §3 |
| FC-B15-MULTI-NETWORK | preserved in orchestrator_plan.md §3 |
| FC-HANDOFF-DATAMOVE1 | preserved in orchestrator_plan.md §3 |
| FC-BROUTE-FROZEN | preserved in orchestrator_plan.md §3 |

## Result: OK_PLAN_COMPILES

All 14 must_check items passed.

OK_PLAN_COMPILES
