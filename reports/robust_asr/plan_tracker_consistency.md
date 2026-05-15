# Robust ASR — Plan-Tracker Consistency Report

Sentinel: **OK_PLAN_TRACKER_CONSISTENCY**

## Inputs

- plan-orchestrator: `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` (sha256 `df11e424281b9be9843682908bafff5f8e7debe6c5358d4343003dd498d11e16`)
- plan-agent: `docs/plans/robust_asr_agent_plan_v3_4_7.md` (sha256 `1bbe14f12c2cbf0c28f50d8990f82758da23df8da5eae3ace9ae15e92af25397`)
- tracker: `docs/progress/robust_asr_progress.yaml` (sha256 `5b9d277794c79f7b1d68096aede96ab5e90ea45da051e7219f55a39fe6609a91`)
- schemas: `docs/plans/state_packet_schemas_v1.yaml`

## Assertions A01–A17

| ID  | Result | Evidence |
|-----|--------|----------|
| A01 | **PASS** | all 31 agent-plan task IDs (P0.0..P10.3) present in tracker.tasks |
| A02 | **PASS** | every canonical tracker task key matches a §9 task ID; non-canonical keys (gates, scope-changes) ignored |
| A03 | **PASS** | all phase-gate fields present in tracker (project_status, current_phase, current_task, last_completed_task, phase_summary.P0..P10, orchestrator_approvals.P0..P10, markers, claims_enabled, blocked) |
| A04 | **PASS** | all referenced markers covered by §7 vocabulary or deviation scope (tracker.markers=['BLOCKED_API', 'BLOCKED_OOD_PUBLIC', 'OUTCOME_E_DETERMINISTIC_SELECTOR']; deviation_scope=[]) |
| A05 | **PASS** | all claims_enabled keys boolean (not 'pending'): cloud_tradeoff=False, ood_real=False, positive_lora=False, positive_system=False |
| A06 | **PASS** | all 42 script references satisfied (on_disk=25; contract_only=17 — Branch-A-only validators contract-defined under OUTCOME_E_DETERMINISTIC_SELECTOR: ['scripts/robust_asr/build_oracle_table.py', 'scripts/robust_asr/build_router_matrices.py', 'scripts/robust_asr/evaluate_full_lora.py', 'scripts/robust_asr/evaluate_lora_checkpoints.py', 'scripts/robust_asr/evaluate_lora_int8_preservation.py', 'scripts/robust_asr/evaluate_router.py', 'scripts/robust_asr/export_lora_ct2_int8.py', 'scripts/robust_asr/extract_router_features.py', 'scripts/robust_asr/merge_lora_to_fp16.py', 'scripts/robust_asr/package_router.py', 'scripts/robust_asr/resolve_long_running_queue.py', 'scripts/robust_asr/select_lora_checkpoint.py', 'scripts/robust_asr/select_router.py', 'scripts/robust_asr/train_lora_full.py', 'scripts/robust_asr/train_router_candidates.py', 'scripts/robust_asr/validate_oracle_table.py', 'scripts/robust_asr/validate_router_matrices.py']) |
| A07 | **PASS** | all PASS phases have PHASE_APPROVE: ['P0', 'P1', 'P2', 'P3', 'P5', 'P6', 'P7', 'P8', 'P9'] |
| A08 | **PASS** | state_transport has all required fields (6): ['latest_state_capsule', 'latest_planning_report', 'latest_execution_report', 'latest_approval_packet', 'last_accepted_report_commit', 'expected_next_task'] |
| A09 | **PASS** | artifacts.state_capsule.path=docs/progress/robust_asr_state_capsule.md resolves on disk |
| A10 | **PASS** | all 23 completed tasks after P0.1 have task reports under reports/robust_asr/task_reports/ |
| A11 | **PASS** | all 31 transition-table task IDs resolve to tracker entries |
| A12 | **PASS** | all skip statuses in §0.1 transitions (['SKIPPED_BY_DECISION_A', 'SKIPPED_BY_OUTCOME_E']) are recognised; tracker uses: ['SKIPPED_BY_DECISION_A', 'SKIPPED_BY_OUTCOME_E'] |
| A13 | **PASS** | OUTCOME_E routing confirmed: P6.2=SKIPPED_BY_OUTCOME_E; P7.1/P7.2=SKIPPED_BY_OUTCOME_E (or absent); P7.3=PASS (selector packaged) |
| A14 | **PASS** | tracker.repo_integration points to configs/robust_asr/reuse_policy_v1.yaml, reports/robust_asr/repo_integration_policy.md, reports/robust_asr/touch_policy.md; all present on disk |
| A15 | **PASS** | CLAUDE.md ROBUST_ASR_PROFILE block matches docs/profiles/CLAUDE.robust_asr.md content (stripped equality) |
| A16 | **PASS** | literal_pass=4; compatibility_exception_pass=20 (closed via orchestrator approval packets / phase approvals recorded in tracker; no new broad exception). literal: ['P0.2', 'P0.3', 'P0.4', 'P10.3']; exception: ['P0.1', 'P0.5', 'P1.1', 'P1.2', 'P1.3', 'P1.4', 'P2.1', 'P2.2', 'P3.1', 'P3.2', 'P5.1', 'P6.1', 'P7.3', 'P8.1', 'P8.2', 'P9.0', 'P9.1', 'P9.2', 'P10.1', 'P10.2'] |
| A17 | **PASS** | scripts/robust_asr/validate_report_shape.py exists; fixtures emit OK_REPORT_SHAPE (exit 0) |

## Overall verdict

Overall: **PASS**
Sentinel: **OK_PLAN_TRACKER_CONSISTENCY**

