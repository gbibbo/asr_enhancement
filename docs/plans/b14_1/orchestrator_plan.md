# orchestrator_plan.md

Plan state: DRAFT_NOT_APPROVED_FOR_EXECUTION
Project scope: B14.1 public exposure via Tailscale Funnel layered on top of the B14.0 recruiter HTTPBasic application-layer gate, with deterministic stable-named exposure semantics. B15 (multi-network smoke) and B-handoff (datamove1 router swap) are preserved as future constraints and are not executable in this file.
Authoritative predecessor: docs/plans/b14_0/ APPROVED at accepted_plan_revision_commit 8a049d00bdfec5b97c416f3135644ecd78f14bd8 and PHASE_APPROVED at accepted_phase_gate_report_commit 7e9ce1f7067f938d2b58a7a4e8615101b0012c58 (phase approval commit 0bdaea89c665dd5cabd7904556dbf536ef409f9f, tracker closure commit 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8).

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

## 3. Phase gate authority

```yaml
phase: B14.1
purpose: layer Tailscale Funnel public exposure on top of the B14.0 recruiter HTTPBasic application-layer gate, with deterministic stable-named exposure semantics, without introducing any application-layer authority that depends on network trust
preconditions:
  - last_completed_phase == B14.0
  - phase_approvals.B14.0.status == APPROVED
  - phase_approvals.B14.0.accepted_phase_gate_report_commit == 7e9ce1f7067f938d2b58a7a4e8615101b0012c58
  - phase_approvals.B14.0.accepted_tracker_closure_commit == 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8
  - tracker current_task is the next B14.1 task in the agent_plan transition table
  - markers == []
phase_gate_pass_iff:
  - B14_1-00 through B14_1-08 are PASS
  - all final-verification sentinels emitted (see agent_plan §7)
  - BR-01 through BR-08 statuses remain PASS in tracker (no B-route rollback)
  - B14_0-00 through B14_0-08 statuses remain PASS in tracker (no B14.0 rollback)
  - no marker in marker registry active
  - no literal public URL committed
  - no literal stable hostname committed
  - no recruiter, admin, Tailscale auth-key, or Cloudflare token value committed
  - recruiter HTTPBasic application-layer gate remains the sole authority for public /demo/* access at PUBLIC_DEMO_EXPOSURE=true (no network-trust bypass)
  - OpenAPI and interactive docs routes are unmounted under PUBLIC_DEMO_EXPOSURE=true unless a narrow admin-only exception is enacted and validated
  - the exposure_state_record asserts application_gated_stable_hostname or an explicit blocker is recorded under HAR-B14_1-FUNNEL-CAPABILITY-001 or HAR-B14_1-STABLE-HOSTNAME-001
phase_gate_on_pass:
  next_phase: B15_PENDING_ORCHESTRATOR_INSTRUCTION
  requires_orchestrator_decision: PHASE_APPROVE
phase_gate_on_fail:
  next_state: return_to_first_failed_B14_1_task
  requires_orchestrator_decision: PHASE_REJECT_or_FIX_BEFORE_CLOSE
```

Future constraint preservation:

| constraint_id | source | must_preserve_in_B14.1 | forbidden_in_B14.1 | validator | future_owner |
|---|---|---|---|---|---|
| FC-B14-1-FUNNEL | b14_0 orchestrator_plan §3 | application-layer gate remains the sole authority for public access; exposure is gated by recruiter auth, not by network trust | bypassing the recruiter gate via any network-trust assumption; claiming success from an ephemeral URL alone | validate_b14_1_application_layer_gate_invariants, validate_b14_1_exposure_state_record | B14.1 active implementation; preservation owner for B15 and B-handoff |
| FC-B15-MULTI-NETWORK | b14_0 orchestrator_plan §3 | public-network smokeability of the recruiter-gated surface remains intact | claiming multi-network smoke coverage from a single-host B14.1 test | validate_future_constraints | B15 |
| FC-HANDOFF-DATAMOVE1 | b14_0 orchestrator_plan §3 | router schema remains adapter-compatible | changing router schema; editing libs/asr/router_runtime.py | validate_future_constraints, validate_b14_1_broute_compatibility_under_public_exposure | B-handoff |
| FC-BROUTE-FROZEN | b14_0 orchestrator_plan §3 | BR-01..BR-08 deliverables and schemas remain frozen | edits to docs/plans/broute/, libs/asr/router_runtime.py, services/frontend/app/demo/types.ts router-field shape | validate_b14_1_broute_compatibility_under_public_exposure, validate_b14_1_path_locks | B-route |
| FC-B14-0-GATE-PRESERVED | b14_0 orchestrator_plan §3 (FC-B14-0-PUBLIC-GATE preservation seam) | recruiter HTTPBasic gate, BR-02 health invariant, and admin/recruiter separation remain intact under public exposure | removing or bypassing the recruiter gate; returning a non-canonical /demo/health payload to an authenticated request; conflating admin and recruiter credentials | validate_b14_1_application_layer_gate_invariants, validate_b14_1_recruiter_gate_preserved_under_public_exposure, validate_b14_1_health_payload_preserved_under_public_exposure | B14.1 active implementation; preservation owner for B15 and B-handoff |

## 4. Decision freeze rules

Decision freeze enters only when both reviewer turns produce STOP_PROPOSED with all axes EQUAL or STRONGER and cross-document audits pass. Decision freeze breaks if any canonical file changes after STOP_PROPOSED or any new counterexample is accepted.

## 5. Final closure rules

```yaml
final_closure_allowed_only_if:
  phase_gate_report: PASS
  all_task_reports_have_falseability_fields: true
  approval_packet_shape_matches_schema: true
  all_B14_1_markers_cleared: true
  future_constraints_report_exists: true
  no_public_url_literal_committed: true
  no_stable_hostname_literal_committed: true
  no_recruiter_credential_committed: true
  no_admin_credential_committed: true
  no_tailscale_auth_key_committed: true
  no_cloudflare_token_committed: true
  no_Authorization_header_value_committed: true
  BR-02_health_invariant_preserved_under_public_exposure: true
  recruiter_HTTPBasic_gate_preserved_under_public_exposure: true
  application_layer_authority_does_not_depend_on_network_trust: true
  openapi_and_docs_off_by_default_under_public_exposure: true
  exposure_state_record_is_stable_named_or_explicit_blocker_recorded: true
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
| HUMAN_ACTION_REQUEST_MALFORMED | REVISE_PLAN | RP-HUMAN-ACTION-REQUEST-MALFORMED | blocks closure |
| EXECUTION_RAIL_GAP | REVISE_PLAN | RP-EXECUTION-RAIL-GAP | blocks closure |
| PATH_LOCK_TOO_BROAD | REVISE_PLAN | RP-PATH-LOCK-TOO-BROAD | blocks closure |
| VALIDATOR_MATERIALIZATION_GAP | REVISE_PLAN | RP-VALIDATOR-MATERIALIZATION-GAP | blocks closure |
| RECOVERY_PACKET_GAP | REVISE_PLAN | RP-RECOVERY-PACKET-GAP | blocks closure |
| UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | RP-UNAUTHORIZED-FILE-TOUCHED | blocks closure |
| HUMAN_ACTION_REQUIRED | CHANGE_SCOPE | RP-HUMAN-ACTION-REQUIRED | blocks closure |
| FUTURE_CONSTRAINT_REGRESSION | CHANGE_SCOPE | RP-FUTURE-CONSTRAINT-REGRESSION | blocks closure |
| PUBLIC_SECURITY_REGRESSION | FIX_BEFORE_CLOSE | RP-PUBLIC-SECURITY-REGRESSION | blocks closure |
| B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED | FIX_BEFORE_CLOSE | RP-B14_1-APPLICATION-LAYER-GATE-BYPASS | blocks closure |
| B14_1_NETWORK_TRUST_AUTHORITY_DETECTED | FIX_BEFORE_CLOSE | RP-B14_1-NETWORK-TRUST-AUTHORITY-DETECTED | blocks closure |
| B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE | FIX_BEFORE_CLOSE | RP-B14_1-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-EXPOSURE | blocks closure |
| B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE | FIX_BEFORE_CLOSE | RP-B14_1-HEALTH-PAYLOAD-REGRESSION-UNDER-PUBLIC-EXPOSURE | blocks closure |
| B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED | FIX_BEFORE_CLOSE | RP-B14_1-OPENAPI-OR-DOCS-LEAK-DETECTED | blocks closure |
| B14_1_EPHEMERAL_URL_SUCCESS_CLAIM | FIX_BEFORE_CLOSE | RP-B14_1-EPHEMERAL-URL-SUCCESS-CLAIM | blocks closure |
| B14_1_PUBLIC_URL_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | RP-B14_1-PUBLIC-URL-LITERAL-COMMITTED | blocks closure |
| B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | RP-B14_1-STABLE-HOSTNAME-LITERAL-COMMITTED | blocks closure |
| B14_1_TUNNEL_SECRET_COMMITTED | FIX_BEFORE_CLOSE | RP-B14_1-TUNNEL-SECRET-COMMITTED | blocks closure |
| B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE | FIX_BEFORE_CLOSE | RP-B14_1-BROUTE-REGRESSION-UNDER-PUBLIC-EXPOSURE | blocks closure |
| B14_1_LOCAL_BYPASS_UNJUSTIFIED | FIX_BEFORE_CLOSE | RP-B14_1-LOCAL-BYPASS-UNJUSTIFIED | blocks closure |

## 7. Hard stop rules and forbidden public regressions

Every marker above is a hard stop until its recovery packet PASS is recorded. Forbidden public regressions extend the B14.0 registry with public-exposure invariants:

```yaml
forbidden_public_regressions:
  runtime_owner: validate_b14_1_application_layer_gate_invariants and validate_b14_1_no_network_trust_authority and validate_b14_1_no_tunnel_secret_leak
  patterns:
    - PUBLIC_DEMO_EXPOSURE_true_with_unauthenticated_demo_route_response_other_than_401_Basic_realm_asr_demo_recruiter
    - PUBLIC_DEMO_EXPOSURE_true_with_OpenAPI_or_docs_route_mounted_unprotected
    - PUBLIC_DEMO_EXPOSURE_true_with_application_layer_authority_decision_keyed_on_network_origin
    - PUBLIC_DEMO_EXPOSURE_true_with_authenticated_demo_health_payload_other_than_canonical_status_ok
    - recruiter_password_logged_under_public_exposure
    - Tailscale_auth_key_logged
    - Tailscale_auth_key_committed_to_repository
    - Cloudflare_token_committed_to_repository
    - public_URL_literal_committed
    - stable_hostname_literal_committed
    - claim_of_success_keyed_on_ephemeral_tunnel_URL_alone
    - local_dev_bypass_active_when_PUBLIC_DEMO_EXPOSURE_true
    - local_dev_bypass_undocumented_by_a_paired_justification_test_when_PUBLIC_DEMO_EXPOSURE_false
    - bypass_route_introduced_for_funnel_health_probe_under_public_exposure
```

## 8. Audit checklist

| Audit id | Source validator | PASS evidence | Negative case disproof |
|---|---|---|---|
| AUD-REPORT-SHAPE | validate_report_shape | OK_REPORT_SHAPE and schema hash | malformed report fixture fails |
| AUD-APPROVAL-PACKET | validate_approval_packet | OK_APPROVAL_PACKET and wrapper hash | missing wrapper fixture fails |
| AUD-PATH-LOCK | validate_b14_1_path_locks | OK_CHANGED_FILES_PATH_LOCKED and diff range | unauthorized file fixture fails |
| AUD-APP-LAYER-GATE | validate_b14_1_application_layer_gate_invariants | OK_B14_1_APPLICATION_LAYER_GATE | network-trust-bypass fixture fails |
| AUD-NO-NETWORK-TRUST | validate_b14_1_no_network_trust_authority | OK_B14_1_NO_NETWORK_TRUST_AUTHORITY | network-origin-decision fixture fails |
| AUD-RECRUITER-GATE-PRESERVED | validate_b14_1_recruiter_gate_preserved_under_public_exposure | OK_B14_1_RECRUITER_GATE_PRESERVED | unauthenticated-200 fixture fails |
| AUD-HEALTH-UNDER-PUBLIC-EXPOSURE | validate_b14_1_health_payload_preserved_under_public_exposure | OK_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE | non-canonical-payload fixture fails |
| AUD-OPENAPI-DOCS | validate_b14_1_openapi_docs_visibility | OK_B14_1_OPENAPI_DOCS_OFF | mounted-unprotected-openapi fixture fails |
| AUD-EXPOSURE-STATE | validate_b14_1_exposure_state_record | OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED | ephemeral-only-claim fixture fails |
| AUD-NO-TUNNEL-SECRET | validate_b14_1_no_tunnel_secret_leak | OK_B14_1_NO_TUNNEL_SECRET_LEAK | committed-auth-key fixture fails |
| AUD-NO-PUBLIC-URL | validate_b14_1_no_public_url_or_hostname_literal | OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | committed-https-non-loopback fixture fails |
| AUD-LOCAL-BYPASS | validate_b14_1_local_bypass_justification | OK_B14_1_LOCAL_BYPASS_JUSTIFIED | unjustified-bypass fixture fails |
| AUD-FUTURE-CONSTRAINTS | validate_future_constraints | OK_FUTURE_CONSTRAINTS | regressing-FC fixture fails |
| AUD-BROUTE-FROZEN | validate_b14_1_broute_compatibility_under_public_exposure | OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | router-schema-edit fixture fails |
| AUD-NO-IMPROVISATION | validate_no_banned_phrases | OK_NO_BANNED_PHRASES | banned-phrase fixture fails |

## 9. Communication rules

```yaml
planning_report_required_before_execution: true
execution_report_required_before_closure: true
phase_gate_report_required_before_phase_approval: true
supplemental_evidence_read_only: true
human_action_request_transport: CHANGE_SCOPE_with_human_action_request_id
plan_authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
plan_authoring_approval_request_recorded_in: reports/rp5/b14_1_plan_authoring_report.md
plan_authoring_orchestrator_decision_scope: plan_authoring
plan_authoring_orchestrator_decision_input_accepted_report_commit: 0bdaea89c665dd5cabd7904556dbf536ef409f9f
no_B14_1_implementation_task_starts_until: an APPROVE_FOR_EXECUTION decision for this plan package is recorded by the orchestrator, followed by an APPROVE_PLAN decision for the first B14.1 task (B14_1-00)
context_window_hygiene_required: true
context_window_hygiene_policy: after every two or three executed tasks within a phase, or at any phase boundary, the orchestrator should prefer a new Claude window to keep the working context narrow and evidence-focused
```

## 10. Cross-document conflict resolution

PLAN_CONFLICT activates when any predicate holds: marker mismatch across files, hard-stop marker without recovery packet, recovery-packet marker missing from registry, approval-packet fields disagree with schema, report-shape names missing from schema, phase-gate authority appearing inside a task body, tracker runtime values appearing inside schema, B14.0 future-constraint id missing from §3 preservation table. Resolution: CHANGE_SCOPE with all disagreeing files patched in one commit.
