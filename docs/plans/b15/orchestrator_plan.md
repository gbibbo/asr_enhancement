# orchestrator_plan.md

Plan state: DRAFT_NOT_APPROVED_FOR_EXECUTION
Project scope: B15 public smoke test of the recruiter-gated public-demo surface across multiple networks (Windows local, mobile cellular, other WiFi, VPN/external tester), layered on top of the B14.1 application-gated public-exposure seam. B15 is a verification-only phase: it produces declarative coverage records, smoke-result records, and adjudication records, and it does not modify application, library, infrastructure, or runtime code. B-handoff (datamove1 router swap) and downstream phases (H, C) are preserved as future constraints and are not executable in this file.
Authoritative predecessor: docs/plans/b14_1/ APPROVED. B14.1 phase approval recorded with accepted_phase_gate_report_commit f2a64d5619e34db99802595c0ce4ea9ae2e2d5f1 and accepted_tracker_closure_commit 360bc2bd8a3d7d42a1886d82cccd3f77b5de7d84. B15 plan-authoring discovery report accepted at accepted_report_commit 63fefd061ee56873c51fb72f4baab333aa86740c.
Legacy high-level scope source: docs/plans/demo_platform_plan.md section 37 (Phase B15, Task B15.1). That legacy text is the scope source only; this triad is the deterministic authority.

## 0. Authority model

This file owns approvals, phase gate authority, hard stops, final closure, audits, communication rules, carried-HAR posture, and cross-document conflict resolution. Tasks, commands, validators, fixtures, markers, recovery packets, path locks, transitions, and tracker mutation rules live in agent_plan.md. Report shapes, entity types, enums, and approval wrappers live in state_packet_schemas.yaml.

Cross-document invariant:

```yaml
if_any_canonical_file_disagrees_with_another_on_marker_task_report_approval_or_schema:
  marker_to_emit: PLAN_CONFLICT
  resolution: CHANGE_SCOPE with all disagreeing files in the same patch
```

B14.1-approval posture invariant:

```yaml
b14_1_phase_approval: APPROVED through the explicit-blocker branch only
b14_1_phase_approval_is_a_public_exposure_success_claim: false
carried_forward_unresolved:
  - HAR-B14_1-STABLE-HOSTNAME-001
  - HAR-B14_1-FUNNEL-CAPABILITY-001 (residual auth-key-host-env blocker)
public_exposure_success_state_entering_B15: BLOCKED_PENDING_HUMAN_ACTION
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
plan_authoring_level: [REQUEST_PLAN_AUTHORING, APPROVE_FOR_EXECUTION, REVISE_PLAN, CHANGE_SCOPE]
human_action_marker_policy: HUMAN_ACTION_REQUIRED maps to CHANGE_SCOPE_with_human_action_request_id
```

## 2. Approval packet shape

Every approval packet is a single YAML mapping with exactly one top-level key ORCHESTRATOR_DECISION carrying eight required fields. Schema reference: state_packet_schemas.yaml > approval_packet.

```yaml
ORCHESTRATOR_DECISION:
  scope: task | phase | scope_change | plan_authoring
  task_id: string_or_null
  phase: string_or_null
  decision: APPROVE_PLAN | REVISE_PLAN | STOP_SCOPE_CONFLICT | CLOSE_TASK | FIX_BEFORE_CLOSE | PHASE_APPROVE | PHASE_REJECT | CHANGE_SCOPE | REQUEST_PLAN_AUTHORING | APPROVE_FOR_EXECUTION
  accepted_report_commit: string_or_null
  next_expected_task: string_or_null
  required_fix: string_or_null
  rationale: one_sentence
```

accepted_report_commit semantics: the field is the 40-character commit at which the report that the orchestrator accepted was recorded. A CLOSE_TASK decision sets accepted_report_commit to the commit of the accepted execution_report; the tracker closure that follows is recorded at a distinct accepted_tracker_closure_commit. A PHASE_APPROVE decision sets accepted_report_commit to the commit of the accepted phase_gate_report. A REQUEST_PLAN_AUTHORING or APPROVE_FOR_EXECUTION decision sets accepted_report_commit to the commit of the accepted plan-authoring or plan-audit report.

## 3. Phase gate authority

```yaml
phase: B15
purpose: verify the recruiter-gated public-demo surface is safe to share by running a multi-network public smoke test across Windows local, mobile cellular, other WiFi, and a VPN/external tester, covering 5 curated examples, 5 degradations, the Whisper provider, the AssemblyAI provider, uploads with and without manual ground truth, the upload limit, provider quota states, and the mobile layout, without modifying application, library, infrastructure, or runtime code
preconditions:
  - last_completed_phase == B14.1
  - phase_approvals.B14.1.status == APPROVED
  - phase_approvals.B14.1.accepted_phase_gate_report_commit == f2a64d5619e34db99802595c0ce4ea9ae2e2d5f1
  - phase_approvals.B14.1.accepted_tracker_closure_commit == 360bc2bd8a3d7d42a1886d82cccd3f77b5de7d84
  - plan_authoring_approvals.B15.status == APPROVED_FOR_EXECUTION
  - tracker current_task is the next B15 task in the agent_plan transition table
  - markers == []
phase_gate_pass_full_success_branch_iff:
  - B15-00 through B15-07 are PASS
  - all final-verification sentinels emitted (see agent_plan section 7)
  - public_exposure_smoke_claim_record.claim_status == SUCCESS_WITH_STABLE_NAMED_EXPOSURE
  - HAR-B14_1-STABLE-HOSTNAME-001 resolved with stable hostname supplied by reference
  - HAR-B14_1-FUNNEL-CAPABILITY-001 residual auth-key-host-env input supplied by reference
  - HAR-B15-MULTI-NETWORK-SMOKE-001 resolved with operator-supplied result records for all four network vantage points
  - multi_network_smoke_coverage_record reports every coverage item covered
  - BR-01 through BR-08, B14_0-00 through B14_0-08, and B14_1-00 through B14_1-08 statuses remain PASS in tracker
  - no marker active
  - no literal public URL, stable hostname, Tailscale auth-key, or Cloudflare token committed
phase_gate_pass_explicit_blocker_branch_iff:
  - B15-00 through B15-03 are PASS
  - B15-04, B15-05, B15-06 are BLOCKED_BY_HUMAN_ACTION with an explicit carried-HAR citation
  - B15-07 phase_gate_report records claim_status BLOCKED_PENDING_HUMAN_ACTION and cites HAR-B14_1-STABLE-HOSTNAME-001 (and, where applicable, HAR-B14_1-FUNNEL-CAPABILITY-001 residual and HAR-B15-MULTI-NETWORK-SMOKE-001) as explicit blockers
  - all docs-only and validator-only final-verification sentinels for B15-00 through B15-03 emitted
  - BR-01 through BR-08, B14_0-00 through B14_0-08, and B14_1-00 through B14_1-08 statuses remain PASS in tracker
  - no marker active
  - no literal public URL, stable hostname, Tailscale auth-key, or Cloudflare token committed
phase_gate_fail_iff:
  - any B15-00 through B15-03 task is FAIL or HALTED
  - or any active marker remains
  - or a smoke-result record is fabricated, claimed without operator evidence, or claims a network vantage point not actually exercised
  - or a public-exposure success claim is keyed on an ephemeral URL alone
  - or a public URL, stable hostname, or tunnel secret literal is committed
phase_gate_on_pass:
  next_phase: B-handoff_PENDING_ORCHESTRATOR_INSTRUCTION
  requires_orchestrator_decision: PHASE_APPROVE
phase_gate_on_fail:
  next_state: return_to_first_failed_B15_task
  requires_orchestrator_decision: PHASE_REJECT_or_FIX_BEFORE_CLOSE
```

Explicit non-claim rule: a PHASE_APPROVE recorded through the explicit-blocker branch is not a public-exposure success claim. It does not assert stable public exposure, host readiness, tunnel readiness, Funnel readiness, public URL availability, application_gated_stable_hostname, or SUCCESS_WITH_STABLE_NAMED_EXPOSURE.

Future constraint preservation:

| constraint_id | source | must_preserve_in_B15 | forbidden_in_B15 | validator | future_owner |
|---|---|---|---|---|---|
| FC-B15-MULTI-NETWORK | b14_1 orchestrator_plan section 3 | public-network smokeability of the recruiter-gated surface is verified across the four required network vantage points or an explicit blocker is recorded | claiming multi-network coverage without operator-supplied result records for each vantage point | validate_b15_multi_network_smoke, validate_future_constraints | B15 active implementation |
| FC-B14-1-PUBLIC-GATE | b14_1 orchestrator_plan section 3 | the recruiter HTTPBasic application-layer gate remains the sole authority for public access; application-layer authority does not depend on network trust | bypassing the recruiter gate; claiming success from an ephemeral URL alone | validate_b15_recruiter_gate_preserved_under_public_smoke, validate_b15_public_exposure_smoke_claim | B15 active implementation; preservation owner for B-handoff |
| FC-HANDOFF-DATAMOVE1 | b14_1 orchestrator_plan section 3 | router schema remains adapter-compatible | changing router schema; editing libs/asr/router_runtime.py | validate_future_constraints | B-handoff |
| FC-BROUTE-FROZEN | b14_1 orchestrator_plan section 3 | BR-01..BR-08 deliverables and schemas remain frozen | edits to docs/plans/broute/, docs/plans/b14_0/, docs/plans/b14_1/, libs/asr/router_runtime.py | validate_b15_path_locks, validate_future_constraints | B-route, B14.0, B14.1 (frozen) |
| FC-B14-0-GATE-PRESERVED | b14_1 orchestrator_plan section 3 | recruiter HTTPBasic gate, BR-02 health invariant, and admin/recruiter separation remain intact under public smoke | removing or bypassing the recruiter gate; returning a non-canonical /demo/health payload to an authenticated request | validate_b15_recruiter_gate_preserved_under_public_smoke | B15 active implementation |

## 4. Decision freeze rules

Decision freeze enters only when both reviewer turns produce STOP_PROPOSED with all axes EQUAL or STRONGER and cross-document audits pass. Decision freeze breaks if any canonical file changes after STOP_PROPOSED or any new counterexample is accepted.

## 5. Final closure rules

```yaml
final_closure_allowed_only_if:
  phase_gate_report: PASS through the full-success branch or the explicit-blocker branch
  all_task_reports_have_falseability_fields: true
  approval_packet_shape_matches_schema: true
  all_B15_markers_cleared: true
  future_constraints_report_exists: true
  no_public_url_literal_committed: true
  no_stable_hostname_literal_committed: true
  no_tailscale_auth_key_committed: true
  no_cloudflare_token_committed: true
  no_recruiter_credential_committed: true
  no_admin_credential_committed: true
  no_Authorization_header_value_committed: true
  recruiter_HTTPBasic_gate_preserved_under_public_smoke: true
  application_layer_authority_does_not_depend_on_network_trust: true
  every_smoke_result_record_traces_to_operator_supplied_evidence: true
  no_smoke_result_record_fabricated: true
  public_exposure_smoke_claim_is_stable_named_or_explicit_blocker_recorded: true
  changed_files_pass_path_locks: true
  no_application_library_infra_runtime_file_modified: true
  reviewer_minimum_loop_satisfied: true
```

## 6. Marker registry

| Marker | Orchestrator effect | Recovery packet (agent_plan section 11) | Closure effect |
|---|---|---|---|
| PLAN_CONFLICT | CHANGE_SCOPE | RP-PLAN-CONFLICT | blocks closure |
| TRACKER_MISSING | STOP_SCOPE_CONFLICT | RP-TRACKER-MISSING | blocks closure |
| TRACKER_MISMATCH | STOP_SCOPE_CONFLICT | RP-TRACKER-MISMATCH | blocks closure |
| REPORT_SCHEMA_INVALID | REVISE_PLAN | RP-REPORT-SCHEMA-INVALID | blocks closure |
| APPROVAL_PACKET_MALFORMED | REVISE_PLAN | RP-APPROVAL-PACKET-MALFORMED | blocks closure |
| HUMAN_ACTION_REQUEST_MALFORMED | REVISE_PLAN | RP-HUMAN-ACTION-REQUEST-MALFORMED | blocks closure |
| EXECUTION_RAIL_GAP | REVISE_PLAN | RP-EXECUTION-RAIL-GAP | blocks closure |
| PATH_LOCK_TOO_BROAD | REVISE_PLAN | RP-PATH-LOCK-TOO-BROAD | blocks closure |
| VALIDATOR_MATERIALIZATION_GAP | REVISE_PLAN | RP-VALIDATOR-MATERIALIZATION-GAP | blocks closure |
| RECOVERY_PACKET_GAP | REVISE_PLAN | RP-RECOVERY-PACKET-GAP | blocks closure |
| UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | RP-UNAUTHORIZED-FILE-TOUCHED | blocks closure |
| HUMAN_ACTION_REQUIRED | CHANGE_SCOPE | RP-HUMAN-ACTION-REQUIRED | blocks closure |
| FUTURE_CONSTRAINT_REGRESSION | CHANGE_SCOPE | RP-FUTURE-CONSTRAINT-REGRESSION | blocks closure |
| PUBLIC_SECURITY_REGRESSION | FIX_BEFORE_CLOSE | RP-PUBLIC-SECURITY-REGRESSION | blocks closure |
| B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED | CHANGE_SCOPE | RP-B15-PUBLIC-EXPOSURE-NOT-HUMAN-GATED | blocks closure |
| B15_SMOKE_RESULT_FABRICATED | FIX_BEFORE_CLOSE | RP-B15-SMOKE-RESULT-FABRICATED | blocks closure |
| B15_MULTI_NETWORK_COVERAGE_GAP | FIX_BEFORE_CLOSE | RP-B15-MULTI-NETWORK-COVERAGE-GAP | blocks closure |
| B15_EPHEMERAL_URL_SUCCESS_CLAIM | FIX_BEFORE_CLOSE | RP-B15-EPHEMERAL-URL-SUCCESS-CLAIM | blocks closure |
| B15_PUBLIC_URL_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | RP-B15-PUBLIC-URL-LITERAL-COMMITTED | blocks closure |
| B15_STABLE_HOSTNAME_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | RP-B15-STABLE-HOSTNAME-LITERAL-COMMITTED | blocks closure |
| B15_TUNNEL_SECRET_COMMITTED | FIX_BEFORE_CLOSE | RP-B15-TUNNEL-SECRET-COMMITTED | blocks closure |
| B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE | FIX_BEFORE_CLOSE | RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE | blocks closure |
| B15_QUOTA_STATE_MISREPRESENTED | FIX_BEFORE_CLOSE | RP-B15-QUOTA-STATE-MISREPRESENTED | blocks closure |
| B15_UPLOAD_LIMIT_REGRESSION | FIX_BEFORE_CLOSE | RP-B15-UPLOAD-LIMIT-REGRESSION | blocks closure |
| B15_MOBILE_LAYOUT_REGRESSION | FIX_BEFORE_CLOSE | RP-B15-MOBILE-LAYOUT-REGRESSION | blocks closure |
| B15_CACHED_EXAMPLE_REGRESSION | FIX_BEFORE_CLOSE | RP-B15-CACHED-EXAMPLE-REGRESSION | blocks closure |
| B15_BROUTE_REGRESSION_UNDER_PUBLIC_SMOKE | FIX_BEFORE_CLOSE | RP-B15-BROUTE-REGRESSION-UNDER-PUBLIC-SMOKE | blocks closure |

## 7. Hard stop rules and forbidden public regressions

Every marker above is a hard stop until its recovery packet PASS is recorded.

```yaml
forbidden_public_regressions:
  runtime_owner: validate_b15_recruiter_gate_preserved_under_public_smoke and validate_b15_public_exposure_smoke_claim and validate_b15_no_public_url_or_hostname_literal
  patterns:
    - public_smoke_started_without_human_action_evidence_for_HAR-B14_1-STABLE-HOSTNAME-001
    - public_smoke_started_without_human_action_evidence_for_HAR-B14_1-FUNNEL-CAPABILITY-001_residual
    - multi_network_coverage_claimed_without_operator_supplied_result_record_per_vantage_point
    - smoke_result_record_authored_without_operator_evidence_reference
    - claim_of_success_keyed_on_ephemeral_tunnel_URL_alone
    - public_URL_literal_committed
    - stable_hostname_literal_committed
    - Tailscale_auth_key_committed_to_repository
    - Cloudflare_token_committed_to_repository
    - recruiter_or_admin_password_committed_to_repository
    - recruiter_gate_bypassed_during_public_smoke
    - non_canonical_demo_health_payload_returned_to_authenticated_request_during_public_smoke
    - provider_quota_state_misrepresented_in_a_smoke_result_record
    - upload_limit_not_enforced_in_a_smoke_result_record
    - application_or_library_or_infra_or_runtime_file_modified_by_a_B15_task
```

## 8. Audit checklist

| Audit id | Source validator | PASS evidence | Negative case disproof |
|---|---|---|---|
| AUD-REPORT-SHAPE | validate_report_shape | OK_REPORT_SHAPE and schema hash | malformed report fixture fails |
| AUD-APPROVAL-PACKET | validate_approval_packet | OK_APPROVAL_PACKET and wrapper hash | missing wrapper fixture fails |
| AUD-PATH-LOCK | validate_b15_path_locks | OK_CHANGED_FILES_PATH_LOCKED and diff range | unauthorized file fixture fails |
| AUD-COVERAGE | validate_b15_coverage_matrix | OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED | missing-coverage-item fixture fails |
| AUD-MULTI-NETWORK | validate_b15_multi_network_smoke | OK_B15_MULTI_NETWORK_SMOKE_OR_BLOCKED | missing-vantage-point fixture fails |
| AUD-SMOKE-EVIDENCE | validate_b15_smoke_result_evidence | OK_B15_SMOKE_RESULT_EVIDENCE_TRACED | fabricated-result fixture fails |
| AUD-RECRUITER-GATE | validate_b15_recruiter_gate_preserved_under_public_smoke | OK_B15_RECRUITER_GATE_PRESERVED | unauthenticated-200 fixture fails |
| AUD-QUOTA-STATE | validate_b15_quota_state_accuracy | OK_B15_QUOTA_STATE_ACCURATE | misrepresented-quota fixture fails |
| AUD-UPLOAD-LIMIT | validate_b15_upload_limit_enforced | OK_B15_UPLOAD_LIMIT_ENFORCED | oversize-accepted fixture fails |
| AUD-MOBILE-LAYOUT | validate_b15_mobile_layout | OK_B15_MOBILE_LAYOUT_OK | horizontal-scroll fixture fails |
| AUD-CACHED-EXAMPLE | validate_b15_cached_example_integrity | OK_B15_CACHED_EXAMPLE_OK | cache-miss-on-curated fixture fails |
| AUD-SMOKE-CLAIM | validate_b15_public_exposure_smoke_claim | OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED | ephemeral-only-claim fixture fails |
| AUD-NO-PUBLIC-URL | validate_b15_no_public_url_or_hostname_literal | OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | committed-https-non-loopback fixture fails |
| AUD-FUTURE-CONSTRAINTS | validate_future_constraints | OK_FUTURE_CONSTRAINTS | regressing-FC fixture fails |
| AUD-NO-IMPROVISATION | validate_no_banned_phrases | OK_NO_BANNED_PHRASES | banned-phrase fixture fails |

## 9. Communication rules

```yaml
planning_report_required_before_execution: true
execution_report_required_before_closure: true
phase_gate_report_required_before_phase_approval: true
supplemental_evidence_read_only: true
human_action_request_transport: CHANGE_SCOPE_with_human_action_request_id
plan_authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
plan_authoring_approval_request_recorded_in: reports/rp5/b15_plan_authoring_report.md
plan_authoring_orchestrator_decision_scope: plan_authoring
plan_authoring_orchestrator_decision_input_accepted_report_commit: 63fefd061ee56873c51fb72f4baab333aa86740c
no_B15_implementation_task_starts_until: an APPROVE_FOR_EXECUTION decision for this plan package is recorded by the orchestrator, followed by an APPROVE_PLAN decision for the first B15 task (B15-00)
context_window_hygiene_required: true
context_window_hygiene_policy: after every two or three executed tasks within a phase, or at any phase boundary, the orchestrator should prefer a new Claude window to keep the working context narrow and evidence-focused
```

## 10. Cross-document conflict resolution

PLAN_CONFLICT activates when any predicate holds: marker mismatch across files, hard-stop marker without recovery packet, recovery-packet marker missing from registry, approval-packet fields disagree with schema, report-shape names missing from schema, phase-gate authority appearing inside a task body, tracker runtime values appearing inside schema, B14.1 future-constraint id missing from section 3 preservation table, a B15 task body asserting public-exposure success without an operator-supplied human_action_result. Resolution: CHANGE_SCOPE with all disagreeing files patched in one commit.

## 11. Plan-authoring gate

```yaml
b15_implementation_cannot_begin_until:
  - this plan package (orchestrator_plan.md, agent_plan.md, state_packet_schemas.yaml) is audited by the orchestrator
  - a separate orchestrator decision records plan_authoring scope APPROVE_FOR_EXECUTION for B15
  - tracker.plan_authoring_approvals.B15 is created by that orchestrator decision, not by this draft
  - an APPROVE_PLAN decision for B15-00 is recorded after the plan-package approval
this_draft_does_not:
  - create plan_authoring_approvals.B15
  - create reports/rp5/b15_plan_approval_packet.yaml
  - record phase_approvals.B15
  - start any B15 task execution
  - create any B15 task record
  - resolve HAR-B14_1-STABLE-HOSTNAME-001 or HAR-B14_1-FUNNEL-CAPABILITY-001
```
