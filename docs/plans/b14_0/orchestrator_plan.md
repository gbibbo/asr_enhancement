# orchestrator_plan.md

Plan state: APPROVED_FOR_EXECUTION (accepted_plan_revision_commit 8a049d00bdfec5b97c416f3135644ecd78f14bd8)
Project scope: B14.0 recruiter HTTPBasic public-access gate. B14.1 (Tailscale Funnel), B15 (multi-network smoke), and B-handoff (datamove1 router swap) are preserved as future constraints and are not executable in this file.
Authoritative predecessor: docs/plans/broute/ approved at commit a445e5918bf12bf266a46bd960e67739167eefba.

## 0. Authority model

This file owns approvals, phase gate authority, hard stops, final closure, audits, communication rules, and cross-document conflict resolution. Tasks, commands, validators, fixtures, markers, recovery packets, path locks, transitions, and tracker mutation rules live in agent_plan.md. Report shapes, entity types, enums, and approval wrappers live in state_packet_schemas.yaml.

Cross-document invariant:

```yaml
if_any_canonical_file_disagrees_with_another_on_marker_task_report_approval_or_schema:
  marker_to_emit: PLAN_CONFLICT
  resolution: CHANGE_SCOPE with all disagreeing files in the same patch
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
| record approval before next task | agent | tracker approval record |

Allowed decisions:

```yaml
task_level: [APPROVE_PLAN, REVISE_PLAN, STOP_SCOPE_CONFLICT, CLOSE_TASK, FIX_BEFORE_CLOSE]
phase_level: [PHASE_APPROVE, PHASE_REJECT, CHANGE_SCOPE]
human_action_marker_policy: HUMAN_ACTION_REQUIRED maps to CHANGE_SCOPE_with_human_action_request_id
```

## 2. Approval packet shape

Every approval packet is a single YAML mapping with exactly one top-level key ORCHESTRATOR_DECISION carrying eight required fields. Schema reference: state_packet_schemas.yaml > approval_packet.

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

## 3. Phase gate authority

```yaml
phase: B14.0
purpose: gate every public /demo/* route behind recruiter HTTPBasic, preserving the BR-02 health invariant and BR-05 manual_mode_no_router_fields invariant, without enabling any public-network exposure
preconditions:
  - last_completed_phase == B-route
  - phase_approvals.B-route.status == APPROVED
  - tracker current_task is the next B14.0 task in the agent_plan transition table
  - markers == []
phase_gate_pass_iff:
  - B14_0-00 through B14_0-08 are PASS
  - all final-verification sentinels emitted (see agent_plan §7)
  - BR-01 through BR-08 statuses remain PASS in tracker (no B-route rollback)
  - no marker in marker registry active
  - no literal public URL committed
  - no recruiter credential committed
  - BR-02 canonical /demo/health payload preserved under authenticated path
  - admin HTTPBasic semantics unchanged
phase_gate_on_pass:
  next_phase: B14.1_PENDING_ORCHESTRATOR_INSTRUCTION
  requires_orchestrator_decision: PHASE_APPROVE
phase_gate_on_fail:
  next_state: return_to_first_failed_B14_0_task
  requires_orchestrator_decision: PHASE_REJECT_or_FIX_BEFORE_CLOSE
```

Future constraint preservation:

| constraint_id | source | must_preserve_in_B14.0 | forbidden_in_B14.0 | validator | future_owner |
|---|---|---|---|---|---|
| FC-B14-1-FUNNEL | broute orchestrator_plan §3 | recruiter-gated app remains loopback-bound | adding Funnel, serve, public URL, systemd work | validate_future_constraints | B14.1 |
| FC-B15-MULTI-NETWORK | broute orchestrator_plan §3 | response fields remain smokeable | claiming public-network smoke coverage from local B14.0 tests | validate_future_constraints | B15 |
| FC-HANDOFF-DATAMOVE1 | broute orchestrator_plan §3 | router schema adapter-compatible | changing router schema | validate_future_constraints | B-handoff |
| FC-BROUTE-FROZEN | this plan §3 | BR-01..BR-08 deliverables and schemas remain frozen | edits to docs/plans/broute/, libs/asr/router_runtime.py, services/frontend/app/demo/types.ts router-field shape | validate_b14_0_broute_compatibility_under_auth | B-route |

## 4. Decision freeze rules

Decision freeze enters only when both reviewer turns produce STOP_PROPOSED with all axes EQUAL or STRONGER and cross-document audits pass. Decision freeze breaks if any canonical file changes after STOP_PROPOSED or any new counterexample is accepted.

## 5. Final closure rules

```yaml
final_closure_allowed_only_if:
  phase_gate_report: PASS
  all_task_reports_have_falseability_fields: true
  approval_packet_shape_matches_schema: true
  all_B14_0_markers_cleared: true
  future_constraints_report_exists: true
  no_public_url_literal_committed: true
  no_recruiter_credential_committed: true
  no_Authorization_header_value_committed: true
  BR-02_health_invariant_preserved: true
  changed_files_pass_path_locks: true
  reviewer_minimum_loop_satisfied: true
```

## 6. Marker registry

| Marker | Orchestrator effect | Recovery packet (agent_plan §11) | Closure effect |
|---|---|---|---|
| PLAN_CONFLICT | CHANGE_SCOPE | RP-PLAN-CONFLICT | blocks closure |
| TRACKER_MISSING | STOP_SCOPE_CONFLICT | RP-TRACKER-MISSING | blocks closure |
| TRACKER_MISMATCH | STOP_SCOPE_CONFLICT | RP-TRACKER-MISMATCH | blocks closure |
| REPORT_SCHEMA_INVALID | REVISE_PLAN | RP-REPORT-SCHEMA-INVALID | blocks closure |
| APPROVAL_PACKET_MALFORMED | REVISE_PLAN | RP-APPROVAL-PACKET-MALFORMED | blocks closure |
| EXECUTION_RAIL_GAP | REVISE_PLAN | RP-EXECUTION-RAIL-GAP | blocks closure |
| PATH_LOCK_TOO_BROAD | REVISE_PLAN | RP-PATH-LOCK-TOO-BROAD | blocks closure |
| VALIDATOR_MATERIALIZATION_GAP | REVISE_PLAN | RP-VALIDATOR-MATERIALIZATION-GAP | blocks closure |
| RECOVERY_PACKET_GAP | REVISE_PLAN | RP-RECOVERY-PACKET-GAP | blocks closure |
| UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | RP-UNAUTHORIZED-FILE-TOUCHED | blocks closure |
| HUMAN_ACTION_REQUIRED | CHANGE_SCOPE | RP-HUMAN-ACTION-REQUIRED | blocks closure |
| FUTURE_CONSTRAINT_REGRESSION | CHANGE_SCOPE | RP-FUTURE-CONSTRAINT-REGRESSION | blocks closure |
| PUBLIC_SECURITY_REGRESSION | FIX_BEFORE_CLOSE | RP-PUBLIC-SECURITY-REGRESSION | blocks closure |
| B14_0_RECRUITER_AUTH_CONTRACT_FAILED | FIX_BEFORE_CLOSE | RP-B14_0-RECRUITER-AUTH-CONTRACT-FAILED | blocks closure |
| B14_0_AUTH_BYPASS_DETECTED | FIX_BEFORE_CLOSE | RP-B14_0-AUTH-BYPASS-DETECTED | blocks closure |
| B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH | FIX_BEFORE_CLOSE | RP-B14_0-HEALTH-PAYLOAD-REGRESSION | blocks closure |
| B14_0_ADMIN_RECRUITER_CRED_CONFLATION | FIX_BEFORE_CLOSE | RP-B14_0-ADMIN-RECRUITER-CRED-CONFLATION | blocks closure |
| B14_0_FRONTEND_AUTH_UX_DRIFT | FIX_BEFORE_CLOSE | RP-B14_0-FRONTEND-AUTH-UX-DRIFT | blocks closure |
| B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED | FIX_BEFORE_CLOSE | RP-B14_0-MANUAL-SMOKE-WITH-AUTH-FAILED | blocks closure |
| B14_0_CRED_LEAK_DETECTED | FIX_BEFORE_CLOSE | RP-B14_0-CRED-LEAK-DETECTED | blocks closure |
| B14_0_BROUTE_REGRESSION_UNDER_AUTH | FIX_BEFORE_CLOSE | RP-B14_0-BROUTE-REGRESSION-UNDER-AUTH | blocks closure |

## 7. Hard stop rules and forbidden public regressions

Every marker above is a hard stop until its recovery packet PASS is recorded. Forbidden public regressions extend the B-route registry with recruiter-auth invariants:

```yaml
forbidden_public_regressions:
  runtime_owner: validate_b14_0_no_credential_leak and validate_b14_0_auth_separation_invariants
  patterns:
    - PUBLIC_DEMO_EXPOSURE_true_allows_recruiter_gate_bypass
    - Authorization_header_value_logged
    - recruiter_password_logged
    - recruiter_password_committed_to_repository
    - admin_and_recruiter_credentials_share_username_or_password
    - 401_challenge_response_leaks_router_fields_or_diagnostic_payload
    - 401_challenge_response_omits_WWW-Authenticate_Basic_header
    - /demo/health_returns_non_canonical_payload_to_authenticated_request
    - public_URL_literal_committed
    - Funnel_serve_systemd_or_tunnel_artifacts_added_in_B14.0
```

## 8. Audit checklist

| Audit id | Source validator | PASS evidence | Negative case disproof |
|---|---|---|---|
| AUD-REPORT-SHAPE | validate_report_shape | OK_REPORT_SHAPE and schema hash | malformed report fixture fails |
| AUD-APPROVAL-PACKET | validate_approval_packet | OK_APPROVAL_PACKET and wrapper hash | missing wrapper fixture fails |
| AUD-PATH-LOCK | validate_changed_files_against_path_locks | OK_CHANGED_FILES_PATH_LOCKED and diff range | unauthorized file fixture fails |
| AUD-AUTH-SEPARATION | validate_b14_0_auth_separation_invariants | OK_B14_0_AUTH_SEPARATION | shared-credential fixture fails |
| AUD-NO-CRED-LEAK | validate_b14_0_no_credential_leak | OK_B14_0_NO_CRED_LEAK | logged-password fixture fails |
| AUD-FUTURE-CONSTRAINTS | validate_future_constraints | OK_FUTURE_CONSTRAINTS | Funnel-string fixture fails |
| AUD-BROUTE-FROZEN | validate_b14_0_broute_compatibility_under_auth | OK_B14_0_BROUTE_COMPATIBILITY | router-schema-edit fixture fails |
| AUD-NO-IMPROVISATION | validate_no_banned_phrases | OK_NO_BANNED_PHRASES | banned-phrase fixture fails |

## 9. Communication rules

```yaml
planning_report_required_before_execution: true
execution_report_required_before_closure: true
phase_gate_report_required_before_phase_approval: true
supplemental_evidence_read_only: true
human_action_request_transport: CHANGE_SCOPE_with_human_action_request_id
plan_authoring_status: APPROVED_FOR_EXECUTION
accepted_plan_revision_commit: 8a049d00bdfec5b97c416f3135644ecd78f14bd8
plan_approval_packet_path: reports/rp5/b14_0_plan_approval_packet.yaml
no_B14_0_implementation_task_starts_until: an APPROVE_PLAN decision for the first B14.0 task (B14_0-00) is recorded after this plan-package approval
```

## 10. Cross-document conflict resolution

PLAN_CONFLICT activates when any predicate holds: marker mismatch across files, hard-stop marker without recovery packet, recovery-packet marker missing from registry, approval-packet fields disagree with schema, report-shape names missing from schema, phase-gate authority appearing inside a task body, tracker runtime values appearing inside schema. Resolution: CHANGE_SCOPE with all disagreeing files patched in one commit.
