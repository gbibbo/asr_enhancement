# orchestrator_plan.md

Plan state: APPROVED_FOR_EXECUTION
Project scope: RP5 B-route router-ready seam. B14.0, B14.1, B15, and B-handoff are preserved as future constraints and are not executable in this file.
Authoritative pre-plan: preplan_rp5_consolidado.md
Protocol: Dual-Agent Adversarial 4x4 Plan Convergence Protocol v4.6.2-prompt-patch

## 0. Authority model

This file owns compile-time orchestration, approval, phase gate authority, final closure, hard stops, audit requirements, communication rules, and PLAN_CONFLICT handling.

| Surface | Owner | Forbidden ownership |
|---|---|---|
| report shapes, entity types, enums, required fields, approval wrapper | state_packet_schemas.yaml | runtime values, commands, approval decisions |
| executable task order, commands, validators, fixtures, markers, transitions, recovery packets, tracker mutations, path locks, report skeleton references | agent_plan.md | approval decisions, phase gate authority outside task bodies, schema definitions |
| approval protocol, phase gate authority, final closure, hard stops, audits, communication | orchestrator_plan.md | implementation commands, validator scripts, tracker schema details |
| current state, statuses, decisions, evidence, approvals, artifacts, blockers | runtime tracker | template structure, schema authority |

Cross-document invariant:

```yaml
if_any_canonical_file_disagrees_with_another_on_marker_task_report_approval_or_schema:
  marker_to_emit: PLAN_CONFLICT
  agent_registry_location: agent_plan.md section 3
  transition_row_location: agent_plan.md section 4
  recovery_packet_location: agent_plan.md section 11
  hard_stop_location: orchestrator_plan.md sections 7 and 10
  closure_blocked_until_resolved: true
```

## 1. Approval protocol

Implementation PASS is not orchestration closure. Every transition after a task report requires an ORCHESTRATOR_DECISION packet recorded by the agent before the next task starts.

| Step | Owner | Required artifact |
|---|---|---|
| derive next tracker-valid task | agent | state_packet |
| propose task plan | agent | planning_report |
| approve or reject plan | orchestrator | ORCHESTRATOR_DECISION |
| execute one approved task | agent | execution_report |
| close task or require fix | orchestrator | ORCHESTRATOR_DECISION |
| record approval before the next task | agent | tracker approval record |

Allowed decisions:

```yaml
task_level: [APPROVE_PLAN, REVISE_PLAN, STOP_SCOPE_CONFLICT, CLOSE_TASK, FIX_BEFORE_CLOSE]
phase_level: [PHASE_APPROVE, PHASE_REJECT, CHANGE_SCOPE]
human_action_marker_policy:
  HUMAN_ACTION_REQUIRED: CHANGE_SCOPE_with_human_action_request_id
rejected_option:
  PAUSE_AND_AWAIT_HUMAN_ACTION_RESULT:
    rejected_because: would introduce a new decision enum in three files; existing CHANGE_SCOPE covers the handoff without enum expansion
```

## 2. Approval packet shape with ORCHESTRATOR_DECISION wrapper

Every approval packet is a single YAML mapping with exactly one top-level key. All 8 keys inside ORCHESTRATOR_DECISION are required. Null content is allowed only for string_or_null fields.

```yaml
ORCHESTRATOR_DECISION:
  scope: task | phase | scope_change
  task_id: string_or_null
  phase: string_or_null
  decision: APPROVE_PLAN | REVISE_PLAN | STOP_SCOPE_CONFLICT | CLOSE_TASK | FIX_BEFORE_CLOSE | PHASE_APPROVE | PHASE_REJECT | CHANGE_SCOPE
  accepted_report_commit: string_or_null
  next_expected_task: string_or_null
  required_fix: string_or_null
  rationale: one_sentence
```

The shape above must match `state_packet_schemas.yaml > approval_packet`. Any mismatch emits PLAN_CONFLICT.

## 3. Phase gate authority

Phase gate authority lives here. Agent task bodies may reference phase gates but may not define approval authority.

Current detailed phase:

```yaml
phase: B-route
purpose: insert router-ready seam before public exposure work
preconditions:
  - last_completed_task == B13.1
  - B-route is the next detailed work item in the pre-plan
  - blocked == false
phase_gate_pass_iff:
  - BR-01 through BR-08 are PASS
  - backend tests pass
  - frontend tests pass
  - manual mode end-to-end smoke passes
  - router mode end-to-end smoke with deterministic stub passes
  - /demo/health payload is exactly {"status":"ok"}
  - cache key contains all pre-plan fields
  - no protected public exposure invariant regressed
  - no active marker in blocking_marker_set
phase_gate_on_pass:
  next_phase: B14.0
  requires_orchestrator_decision: PHASE_APPROVE
phase_gate_on_fail:
  next_state: return_to_first_failed_B_route_task
  requires_orchestrator_decision: PHASE_REJECT_or_FIX_BEFORE_CLOSE
```

Future constraint preservation records:

| constraint_id | source_preplan_section | current_scope_impact | must_preserve_in_current_plan | forbidden_current_plan_regression | validator_or_review_check | future_phase_owner | out_of_scope_but_preserved |
|---|---|---|---|---|---|---|---|
| FC-B14-0-PUBLIC-GATE | preplan §4 | B-route must not expose public routes | B14.0 starts after B-route PASS | adding recruiter auth or public tunnel work inside B-route | validate_future_constraints | B14.0 | true |
| FC-B14-1-FUNNEL | preplan §5 | B-route must keep loopback binding compatible | B14.1 starts after B14.0 PASS | adding Funnel, serve, URL, or systemd work inside B-route | validate_future_constraints | B14.1 | true |
| FC-B15-MULTI-NETWORK | preplan §6 | B-route response fields must remain smokeable | B15 starts after B14.1 PASS | claiming public smoke coverage from local B-route tests | validate_future_constraints | B15 | true |
| FC-HANDOFF-DATAMOVE1 | preplan §7 | B-route schema must be adapter-compatible | handoff swap waits for datamove1 tag | changing schema after handoff compatibility gate without diff report | validate_future_constraints | B-handoff | true |

## 4. Decision freeze rules

Decision freeze starts only when both agents have produced STOP_PROPOSED after the minimum loop and all axes are EQUAL or STRONGER. Before that point, any remaining issue reopens a revision cycle in the protocol transcript, not in the canonical plan state.

```yaml
decision_freeze_enters_when:
  minimum_loop_satisfied: true
  two_consecutive_stop_proposed_roles_differ: true
  all_nine_axes_equal_or_stronger: true
  cross_document_consistency_audit_pass: true
  mature_mechanism_inventory_pass: true
  operational_stress_pack_pass: true
decision_freeze_breaks_when:
  any_canonical_file_changes_after_stop_proposed: true
  any_new_counterexample_accepted: true
```

## 5. Final closure rules

Final closure is independent from the last implementation task. BR-08 may PASS and the phase may still be rejected by the orchestrator.

```yaml
final_closure_allowed_only_if:
  phase_gate_report: PASS
  all_task_reports_have_falseability_fields: true
  approval_packet_shape_matches_schema: true
  all_B_ROUTE_markers_cleared: true
  future_constraints_report_exists: true
  no_public_url_literal_committed: true
  no_forbidden_public_health_fields: true
  changed_files_pass_path_locks: true
  reviewer_minimum_loop_satisfied: true
```

## 6. Marker registry

| Marker | Orchestrator effect | Agent registry required | Closure effect |
|---|---|---|---|
| PLAN_CONFLICT | change scope or block approval | yes | blocks phase gate or task closure |
| PREPLAN_THRESHOLD_GAP | change scope or block approval | yes | blocks phase gate or task closure |
| TRACKER_MISSING | reject report and require fix | yes | blocks phase gate or task closure |
| TRACKER_MISMATCH | reject report and require fix | yes | blocks phase gate or task closure |
| REPORT_SCHEMA_INVALID | reject report and require fix | yes | blocks phase gate or task closure |
| APPROVAL_PACKET_MALFORMED | reject report and require fix | yes | blocks phase gate or task closure |
| EXECUTION_RAIL_GAP | reject report and require fix | yes | blocks phase gate or task closure |
| PATH_LOCK_TOO_BROAD | reject report and require fix | yes | blocks phase gate or task closure |
| VALIDATOR_MATERIALIZATION_GAP | reject report and require fix | yes | blocks phase gate or task closure |
| RECOVERY_PACKET_GAP | reject report and require fix | yes | blocks phase gate or task closure |
| PUBLIC_SECURITY_REGRESSION | reject report and require fix | yes | blocks phase gate or task closure |
| ROUTER_SCHEMA_DRIFT | reject report and require fix | yes | blocks phase gate or task closure |
| FRONTEND_BACKEND_DRIFT | reject report and require fix | yes | blocks phase gate or task closure |
| FUTURE_CONSTRAINT_REGRESSION | change scope or block approval | yes | blocks phase gate or task closure |
| UNAUTHORIZED_FILE_TOUCHED | reject report and require fix | yes | blocks phase gate or task closure |
| HUMAN_ACTION_REQUIRED | change scope or block approval | yes | blocks phase gate or task closure |
| B_ROUTE_BACKEND_TEST_FAILED | reject task and require fix | yes | blocks phase gate or task closure |
| B_ROUTE_FRONTEND_TEST_FAILED | reject task and require fix | yes | blocks phase gate or task closure |
| B_ROUTE_MANUAL_SMOKE_FAILED | reject task and require fix | yes | blocks phase gate or task closure |
| B_ROUTE_ROUTER_SMOKE_FAILED | reject task and require fix | yes | blocks phase gate or task closure |
| B_ROUTE_HEALTH_PAYLOAD_REGRESSION | reject task and require fix | yes | blocks phase gate or task closure |
| B_ROUTE_CACHE_KEY_INCOMPLETE | reject task and require fix | yes | blocks phase gate or task closure |
| B_ROUTE_STUB_DRIFT | reject task and require fix | yes | blocks phase gate or task closure |


## 7. Hard stop rules

| Marker | Required orchestrator decision | Required agent response | Clears when |
|---|---|---|---|
| PLAN_CONFLICT | CHANGE_SCOPE | use RP-PLAN-CONFLICT | recovery packet passes and tracker records cleared marker |
| PREPLAN_THRESHOLD_GAP | CHANGE_SCOPE | use RP-PREPLAN-THRESHOLD-GAP | recovery packet passes and tracker records cleared marker |
| TRACKER_MISSING | STOP_SCOPE_CONFLICT | use RP-TRACKER-MISSING | recovery packet passes and tracker records cleared marker |
| TRACKER_MISMATCH | STOP_SCOPE_CONFLICT | use RP-TRACKER-MISMATCH | recovery packet passes and tracker records cleared marker |
| REPORT_SCHEMA_INVALID | REVISE_PLAN | use RP-REPORT-SCHEMA-INVALID | recovery packet passes and tracker records cleared marker |
| APPROVAL_PACKET_MALFORMED | REVISE_PLAN | use RP-APPROVAL-PACKET-MALFORMED | recovery packet passes and tracker records cleared marker |
| EXECUTION_RAIL_GAP | REVISE_PLAN | use RP-EXECUTION-RAIL-GAP | recovery packet passes and tracker records cleared marker |
| PATH_LOCK_TOO_BROAD | REVISE_PLAN | use RP-PATH-LOCK-TOO-BROAD | recovery packet passes and tracker records cleared marker |
| VALIDATOR_MATERIALIZATION_GAP | REVISE_PLAN | use RP-VALIDATOR-MATERIALIZATION-GAP | recovery packet passes and tracker records cleared marker |
| RECOVERY_PACKET_GAP | REVISE_PLAN | use RP-RECOVERY-PACKET-GAP | recovery packet passes and tracker records cleared marker |
| PUBLIC_SECURITY_REGRESSION | FIX_BEFORE_CLOSE | use RP-PUBLIC-SECURITY-REGRESSION | recovery packet passes and tracker records cleared marker |
| ROUTER_SCHEMA_DRIFT | FIX_BEFORE_CLOSE | use RP-ROUTER-SCHEMA-DRIFT | recovery packet passes and tracker records cleared marker |
| FRONTEND_BACKEND_DRIFT | FIX_BEFORE_CLOSE | use RP-FRONTEND-BACKEND-DRIFT | recovery packet passes and tracker records cleared marker |
| FUTURE_CONSTRAINT_REGRESSION | CHANGE_SCOPE | use RP-FUTURE-CONSTRAINT-REGRESSION | recovery packet passes and tracker records cleared marker |
| UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | use RP-UNAUTHORIZED-FILE-TOUCHED | recovery packet passes and tracker records cleared marker |
| HUMAN_ACTION_REQUIRED | CHANGE_SCOPE | use RP-HUMAN-ACTION-REQUIRED | recovery packet passes and tracker records cleared marker |
| B_ROUTE_BACKEND_TEST_FAILED | FIX_BEFORE_CLOSE | use RP-BROUTE-BACKEND-TEST-FAILED | recovery packet passes and tracker records cleared marker |
| B_ROUTE_FRONTEND_TEST_FAILED | FIX_BEFORE_CLOSE | use RP-BROUTE-FRONTEND-TEST-FAILED | recovery packet passes and tracker records cleared marker |
| B_ROUTE_MANUAL_SMOKE_FAILED | FIX_BEFORE_CLOSE | use RP-BROUTE-MANUAL-SMOKE-FAILED | recovery packet passes and tracker records cleared marker |
| B_ROUTE_ROUTER_SMOKE_FAILED | FIX_BEFORE_CLOSE | use RP-BROUTE-ROUTER-SMOKE-FAILED | recovery packet passes and tracker records cleared marker |
| B_ROUTE_HEALTH_PAYLOAD_REGRESSION | FIX_BEFORE_CLOSE | use RP-BROUTE-HEALTH-PAYLOAD-REGRESSION | recovery packet passes and tracker records cleared marker |
| B_ROUTE_CACHE_KEY_INCOMPLETE | FIX_BEFORE_CLOSE | use RP-BROUTE-CACHE-KEY-INCOMPLETE | recovery packet passes and tracker records cleared marker |
| B_ROUTE_STUB_DRIFT | FIX_BEFORE_CLOSE | use RP-BROUTE-STUB-DRIFT | recovery packet passes and tracker records cleared marker |


Forbidden public regressions audited by orchestrator and enforced by `validate_public_security_invariants`:

```yaml
forbidden_public_regressions:
  runtime_owner: validate_public_security_invariants
  patterns:
    - PUBLIC_DEMO_EXPOSURE_true_allows_gate_bypass
    - Authorization_header_logged
    - recruiter_password_logged
    - raw_uploaded_filename_logged_when_user_identifying
    - /demo/health_exposes_version_commit_uptime_queue_model_provider_env_hostname
    - /demo/upload_reads_body_before_auth_rejection
    - CORS_wildcard_in_public_mode
    - docs_or_openapi_enabled_by_default_in_public_mode
```


## 8. Audit checklist

| Audit id | Source validator | PASS evidence required | Negative case disproof |
|---|---|---|---|
| AUD-REPORT-SHAPE | validate_report_shape | OK_REPORT_SHAPE and schema hash | malformed report fixture fails |
| AUD-APPROVAL-PACKET | validate_approval_packet | OK_APPROVAL_PACKET and wrapper hash | missing wrapper fixture fails |
| AUD-PATH-LOCK | validate_changed_files_against_path_locks | OK_CHANGED_FILES_PATH_LOCKED and diff range | unauthorized file fixture fails |
| AUD-FUTURE-CONSTRAINTS | validate_future_constraints | OK_FUTURE_CONSTRAINTS and FC table | B14.1 work inside B-route fixture fails |
| AUD-NO-IMPROVISATION | validate_no_banned_phrases | OK_NO_BANNED_PHRASES | forbidden phrase fixture fails |

## 9. Communication rules

Agent reports must be self-contained. The orchestrator never infers state from repository memory or from a previous ZIP.

```yaml
planning_report_required_before_execution: true
execution_report_required_before_closure: true
phase_gate_report_required_before_phase_approval: true
supplemental_evidence_read_only: true
human_action_request_transport: CHANGE_SCOPE_with_human_action_request_id
```

## 10. Cross-document conflict resolution

PLAN_CONFLICT activates when any of these predicates hold:

```yaml
conflict_predicates:
  - marker_in_agent_registry_missing_from_orchestrator_registry
  - marker_in_orchestrator_registry_missing_from_agent_registry
  - hard_stop_marker_without_recovery_packet
  - recovery_packet_marker_missing_from_marker_registry
  - approval_packet_fields_disagree_between_orchestrator_and_schema
  - report_shape_named_by_agent_missing_from_schema
  - schema_field_order_disagrees_with_report_skeleton
  - phase_gate_authority_appears_inside_agent_task_body
  - tracker_runtime_values_appear_inside_schema
resolution:
  stop_current_task: true
  required_decision: CHANGE_SCOPE
  required_patch_scope: all_disagreeing_files_in_same_patch
```
