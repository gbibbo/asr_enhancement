# orchestrator_plan.md

Plan state: DRAFT_NOT_APPROVED_FOR_EXECUTION
Project scope: B14.2 is a repair microphase that addresses the B15-routed public-surface recruiter HTTPBasic gate regression `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`. The microphase restores the application-layer recruiter HTTPBasic gate as the sole authority for the public Funnel-exposed `/demo/*` surface and verifies the restoration through a fresh operator-supplied four-vantage-point public-surface re-smoke. B-route, B14.0, B14.1, and B15 canonical plan files and reports are frozen post-approval/post-rejection. B-handoff (datamove1 router swap) and downstream phases remain preserved as future constraints and are not executable here.
Authoritative predecessor: docs/plans/b15/ REJECTED. B15 phase rejection recorded with `accepted_phase_gate_report_commit 6bcfaee57df7a1e8f7026916b472559b3cadcbbc`, `accepted_tracker_closure_commit bf8560a6c3493692ccd8a35926a5ddc647b627f6`, `decision_rule_routing RETURN_TO_B14`, `claim_status FAILED_PENDING_PHASE_RETURN`. Predecessor B14.1 remains APPROVED through the explicit-blocker branch only. B14.0 and B-route remain APPROVED.
Legacy high-level scope source: docs/plans/demo_platform_plan.md section 37 Task B15.1 decision rule "If public tunnel fails, return to B14". That legacy text is the routing source; this triad is the deterministic authority for the B14.2 repair microphase.

## 0. Authority model

This file owns approvals, phase gate authority, hard stops, final closure, audits, communication rules, carried-marker and carried-HAR posture, and cross-document conflict resolution. Tasks, commands, validators, fixtures, markers, recovery packets, path locks, transitions, and tracker mutation rules live in agent_plan.md. Report shapes, entity types, enums, and approval wrappers live in state_packet_schemas.yaml.

Cross-document invariant:

```yaml
if_any_canonical_file_disagrees_with_another_on_marker_task_report_approval_or_schema:
  marker_to_emit: PLAN_CONFLICT
  resolution: CHANGE_SCOPE with all disagreeing files in the same patch
```

Predecessor posture invariant:

```yaml
b_route_phase_approval: APPROVED
b14_0_phase_approval: APPROVED
b14_1_phase_approval: APPROVED through the explicit-blocker branch only
b15_phase_decision: REJECTED via PHASE_REJECT with decision_rule_routing RETURN_TO_B14
b15_phase_decision_is_a_public_exposure_success_claim: false
b15_phase_outcome: B15_FAILED_PENDING_PHASE_RETURN
carried_forward_active:
  - B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
carried_forward_resolved_by_reference_only:
  - HAR-B14_1-STABLE-HOSTNAME-001
  - HAR-B14_1-FUNNEL-CAPABILITY-001
carried_forward_resolved_with_observation_set:
  - HAR-B15-MULTI-NETWORK-SMOKE-001
secondary_observation_preserved:
  - upload_with_manual_ground_truth FAIL on all four B15-05 vantage points (preserved verbatim; classified at B14_2-05; not silently absorbed)
public_exposure_success_state_entering_B14_2: BLOCKED_BY_OBSERVED_REGRESSION
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
task_level: [APPROVE_PLAN, REVISE_PLAN, STOP_SCOPE_CONFLICT, CLOSE_TASK, CLOSE_TASK_WITH_OBSERVED_REGRESSIONS, FIX_BEFORE_CLOSE]
phase_level: [PHASE_APPROVE, PHASE_REJECT, CHANGE_SCOPE]
plan_authoring_level: [REQUEST_PLAN_AUTHORING, APPROVE_FOR_EXECUTION, REVISE_PLAN, CHANGE_SCOPE]
human_action_marker_policy: HUMAN_ACTION_REQUIRED maps to CHANGE_SCOPE_with_human_action_request_id
```

## 2. Approval packet shape

Every approval packet is a single YAML mapping with exactly one top-level key ORCHESTRATOR_DECISION carrying the required fields. Schema reference: state_packet_schemas.yaml > approval_packet.

```yaml
ORCHESTRATOR_DECISION:
  scope: task | phase | scope_change | plan_authoring
  task_id: string_or_null
  phase: string_or_null
  decision: APPROVE_PLAN | REVISE_PLAN | STOP_SCOPE_CONFLICT | CLOSE_TASK | CLOSE_TASK_WITH_OBSERVED_REGRESSIONS | FIX_BEFORE_CLOSE | PHASE_APPROVE | PHASE_REJECT | CHANGE_SCOPE | REQUEST_PLAN_AUTHORING | APPROVE_FOR_EXECUTION
  observed_regression_markers: list_of_marker_ids_or_null   # required non-null and non-empty iff decision == CLOSE_TASK_WITH_OBSERVED_REGRESSIONS; absent or null otherwise
  accepted_report_commit: string_or_null
  next_expected_task: string_or_null
  required_fix: string_or_null
  rationale: one_sentence
```

`accepted_report_commit` semantics: the field is the 40-character commit at which the report that the orchestrator accepted was recorded. CLOSE_TASK and CLOSE_TASK_WITH_OBSERVED_REGRESSIONS set it to the commit of the accepted execution_report. PHASE_APPROVE and PHASE_REJECT set it to the commit of the accepted phase_gate_report. REQUEST_PLAN_AUTHORING and APPROVE_FOR_EXECUTION set it to the commit of the accepted plan-authoring report. The tracker closure that follows a CLOSE_TASK decision is recorded at a distinct accepted_tracker_closure_commit.

## 3. Phase gate authority

```yaml
phase: B14.2
purpose: restore the application-layer recruiter HTTPBasic gate as the sole authority for the public Funnel-exposed /demo/* surface, verified by a fresh operator-supplied four-vantage-point public-surface re-smoke recording authenticated_access_only on every vantage point, and classify the carried upload_with_manual_ground_truth=FAIL secondary observation as linked_to_gate or independent_defer based on the re-smoke evidence
preconditions:
  - last_completed_phase == B15
  - phase_approvals.B15.status == REJECTED
  - phase_approvals.B15.decision == PHASE_REJECT
  - phase_approvals.B15.accepted_phase_gate_report_commit == 6bcfaee57df7a1e8f7026916b472559b3cadcbbc
  - phase_approvals.B15.accepted_tracker_closure_commit == bf8560a6c3493692ccd8a35926a5ddc647b627f6
  - phase_approvals.B15.decision_rule_routing == RETURN_TO_B14
  - phase_approvals.B15.return_target_exact_phase_or_task_id == B14.2
  - phase_approvals.B14.1.status == APPROVED
  - phase_approvals.B14.0.status == APPROVED
  - phase_approvals.B-route.status == APPROVED
  - plan_authoring_approvals.B14.2.status == APPROVED_FOR_EXECUTION
  - tracker current_task is the next B14.2 task in the agent_plan transition table
  - markers contains B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE entering B14.2
phase_gate_pass_gate_restored_branch_iff:
  - B14_2-00 through B14_2-06 are PASS
  - all final-verification sentinels emitted (see agent_plan section 7)
  - HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 resolved with operator-supplied result records for all four network vantage points
  - every public_surface_recruiter_gate_resmoke_record reports recruiter_gate_observed_status authenticated_access_only
  - b14_2_public_surface_claim_record.claim_status == GATE_RESTORED_VERIFIED_BY_OPERATOR_RESMOKE
  - recovery packet RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE recorded PASS
  - upload_with_gt_secondary_observation_record.classification is one of {linked_to_gate, independent_defer}
  - BR-01 through BR-08, B14_0-00 through B14_0-08, B14_1-00 through B14_1-08, and B15-00 through B15-07 statuses remain unchanged in tracker
  - no marker active other than the carried marker scheduled for clearance at this approval recording
  - no literal public URL, stable hostname, Tailscale auth-key, Cloudflare token, recruiter password, admin password, or IP address committed
phase_gate_pass_blocked_branch_iff:
  - B14_2-00 through B14_2-03 are PASS
  - B14_2-04 is BLOCKED_BY_HUMAN_ACTION citing HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001
  - b14_2_public_surface_claim_record.claim_status == BLOCKED_PENDING_HUMAN_ACTION
  - all docs-only and validator-only final-verification sentinels for B14_2-00 through B14_2-03 emitted
  - no marker active other than the carried marker preserved-not-cleared at this approval recording
  - no literal public URL, stable hostname, Tailscale auth-key, Cloudflare token, recruiter password, admin password, or IP address committed
phase_gate_fail_iff:
  - any B14_2-00 through B14_2-03 task is FAIL or HALTED
  - or any non-carried marker remains active
  - or a public_surface_recruiter_gate_resmoke_record is fabricated, claimed without operator evidence, or claims a network vantage point not actually exercised
  - or B14_2-04 records any vantage point with recruiter_gate_observed_status unauthenticated_access_observed and B14_2-06 records claim_status anything other than FAILED_PENDING_PHASE_RETURN
  - or a public URL, stable hostname, or tunnel secret literal is committed
  - or upload_with_gt_secondary_observation_record records an upload-with-GT FAIL converted to PASS without matching B14_2-04 evidence
phase_gate_on_pass_gate_restored_branch:
  next_phase: PENDING_ORCHESTRATOR_INSTRUCTION
  requires_orchestrator_decision: PHASE_APPROVE
  carried_marker_cleared_at_this_recording: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
  upload_with_gt_secondary_observation_classification_recorded: true
phase_gate_on_pass_blocked_branch:
  next_phase: PENDING_ORCHESTRATOR_INSTRUCTION
  requires_orchestrator_decision: PHASE_APPROVE
  carried_marker_cleared_at_this_recording: none (preserved-not-cleared)
phase_gate_on_fail:
  next_state: return_to_first_failed_B14_2_task_or_FAILED_PENDING_PHASE_RETURN
  requires_orchestrator_decision: PHASE_REJECT_or_FIX_BEFORE_CLOSE
  carried_marker_state: preserved-not-cleared
```

Explicit non-claim rule: B14.2 cannot assert `SUCCESS_WITH_STABLE_NAMED_EXPOSURE`. That claim shape belongs to the B15 success-claim record and is not legal in a B14.2 closure. The B14.2 PHASE_APPROVE on the gate-restored branch clears only the carried gate-regression marker and the associated B15 recovery packet; it does not assert stable public exposure, host readiness, tunnel readiness, Funnel readiness, public URL availability, or full B15 coverage success.

Future constraint preservation:

| constraint_id | source | must_preserve_in_B14.2 | forbidden_in_B14.2 | validator | future_owner |
|---|---|---|---|---|---|
| FC-B15-MULTI-NETWORK | b15 orchestrator_plan section 3 | the multi-network coverage contract remains intact; the B14_2-04 re-smoke uses the same four vantage points; the B15-05 operator evidence is preserved verbatim | claiming multi-network coverage without operator-supplied result records for each vantage point; fabricating any vantage-point outcome | validate_b14_2_public_surface_recruiter_gate_resmoke, validate_future_constraints | B15 (frozen) and B14.2 active implementation |
| FC-B14-1-PUBLIC-GATE | b15 orchestrator_plan section 3 | the recruiter HTTPBasic application-layer gate is the sole authority for public access; the B14.2 repair restores end-to-end gate authority on the Funnel-exposed surface without introducing network-trust authority | bypassing the recruiter gate; introducing any network-trust authority decision; claiming success from an ephemeral URL alone | validate_b14_2_application_layer_gate_invariants, validate_b14_2_recruiter_gate_preserved_under_public_exposure | B14.2 active implementation |
| FC-HANDOFF-DATAMOVE1 | b15 orchestrator_plan section 3 | router schema remains adapter-compatible | changing router schema; editing libs/asr/router_runtime.py | validate_future_constraints | B-handoff |
| FC-BROUTE-FROZEN | b15 orchestrator_plan section 3 | BR-01..BR-08, B14_0-00..B14_0-08, and B14_1-00..B14_1-08 deliverables and schemas remain frozen | edits to docs/plans/broute/, docs/plans/b14_0/, docs/plans/b14_1/, libs/asr/router_runtime.py, services/frontend/app/demo/types.ts router-field shape | validate_b14_2_path_locks, validate_future_constraints | B-route, B14.0, B14.1 (frozen) |
| FC-B14-0-GATE-PRESERVED | b15 orchestrator_plan section 3 | recruiter HTTPBasic gate, BR-02 health invariant, and admin/recruiter separation remain intact under the repaired public surface | removing or bypassing the recruiter gate; returning a non-canonical /demo/health payload to an authenticated request; conflating admin and recruiter credentials | validate_b14_2_recruiter_gate_preserved_under_public_exposure, validate_b14_2_health_payload_preserved_under_public_exposure | B14.2 active implementation |
| FC-B15-FROZEN | b14_2 orchestrator_plan section 3 (this row) | B15-00..B15-07 deliverables, schemas, plan files, and reports remain frozen post-PHASE_REJECT; the B15 phase rejection itself and its `accepted_phase_gate_report_commit` and `accepted_tracker_closure_commit` are preserved verbatim; the carried marker is preserved-not-cleared until the B14.2 gate-restored branch fires | editing docs/plans/b15/, reports/rp5/b15_*.md, or any B15 task record; converting the B15 rejection to an approval; clearing the carried marker outside the gate-restored branch | validate_b14_2_path_locks, validate_future_constraints --constraint-profile b14_2 | B15 (frozen) and B14.2 active implementation |

## 4. Decision freeze rules

Decision freeze enters only when both reviewer turns produce STOP_PROPOSED with all axes EQUAL or STRONGER and cross-document audits pass. Decision freeze breaks if any canonical file changes after STOP_PROPOSED or any new counterexample is accepted.

## 5. Final closure rules

```yaml
final_closure_allowed_only_if:
  phase_gate_report: PASS through the gate-restored branch or the blocked branch
  all_task_reports_have_falseability_fields: true
  approval_packet_shape_matches_schema: true
  all_B14_2_markers_cleared: true
  carried_marker_state_consistent_with_phase_gate_branch: true
  future_constraints_report_exists: true
  no_public_url_literal_committed: true
  no_stable_hostname_literal_committed: true
  no_tailscale_auth_key_committed: true
  no_cloudflare_token_committed: true
  no_recruiter_credential_committed: true
  no_admin_credential_committed: true
  no_ip_address_literal_committed: true
  no_Authorization_header_value_committed: true
  recruiter_HTTPBasic_gate_preserved_under_public_exposure: true
  application_layer_authority_does_not_depend_on_network_trust: true
  every_public_surface_recruiter_gate_resmoke_record_traces_to_operator_supplied_evidence: true
  no_public_surface_recruiter_gate_resmoke_record_fabricated: true
  b14_2_public_surface_claim_is_gate_restored_or_blocked_pending_human_action_or_failed_pending_phase_return: true
  upload_with_gt_secondary_observation_classified_or_blocked: true
  changed_files_pass_path_locks: true
  no_predecessor_plan_or_report_file_modified: true
  router_runtime_sha256_unchanged: true
  router_fields_frontend_shape_sha256_unchanged: true
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
| B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED | FIX_BEFORE_CLOSE | RP-B14_2-APPLICATION-LAYER-GATE-BYPASS | blocks closure |
| B14_2_NETWORK_TRUST_AUTHORITY_DETECTED | FIX_BEFORE_CLOSE | RP-B14_2-NETWORK-TRUST-AUTHORITY-DETECTED | blocks closure |
| B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE | FIX_BEFORE_CLOSE | RP-B14_2-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-EXPOSURE | blocks closure |
| B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE | FIX_BEFORE_CLOSE | RP-B14_2-HEALTH-PAYLOAD-REGRESSION-UNDER-PUBLIC-EXPOSURE | blocks closure |
| B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED | FIX_BEFORE_CLOSE | RP-B14_2-OPENAPI-OR-DOCS-LEAK-DETECTED | blocks closure |
| B14_2_PUBLIC_URL_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | RP-B14_2-PUBLIC-URL-LITERAL-COMMITTED | blocks closure |
| B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | RP-B14_2-STABLE-HOSTNAME-LITERAL-COMMITTED | blocks closure |
| B14_2_TUNNEL_SECRET_COMMITTED | FIX_BEFORE_CLOSE | RP-B14_2-TUNNEL-SECRET-COMMITTED | blocks closure |
| B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE | FIX_BEFORE_CLOSE | RP-B14_2-BROUTE-REGRESSION-UNDER-PUBLIC-EXPOSURE | blocks closure |
| B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED | FIX_BEFORE_CLOSE | RP-B14_2-PUBLIC-SURFACE-RESMOKE-FABRICATED | blocks closure |
| B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP | FIX_BEFORE_CLOSE | RP-B14_2-PUBLIC-SURFACE-RESMOKE-COVERAGE-GAP | blocks closure |
| B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION | FIX_BEFORE_CLOSE | RP-B14_2-UPLOAD-WITH-GT-SILENT-ABSORPTION | blocks closure |
| B14_2_EPHEMERAL_URL_SUCCESS_CLAIM | FIX_BEFORE_CLOSE | RP-B14_2-EPHEMERAL-URL-SUCCESS-CLAIM | blocks closure |
| B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND | FIX_BEFORE_CLOSE | RP-B14_2-CARRIED-MARKER-CLEARED-OUT-OF-BAND | blocks closure |
| B14_2_PREDECESSOR_FILE_TOUCHED | STOP_SCOPE_CONFLICT | RP-B14_2-PREDECESSOR-FILE-TOUCHED | blocks closure |
| B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE | carried_from_B15; preserved active through B14_2-00..B14_2-05; eligible for clearance only at B14.2 PHASE_APPROVE on the gate-restored branch following RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE PASS | RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE (inherited from B15) | blocks full-success closure of B14.2 until cleared by the gate-restored branch |

## 7. Hard stop rules and forbidden public regressions

Every marker above is a hard stop until its recovery packet PASS is recorded. The carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` is preserved active through B14_2-00..B14_2-05 by design and is not treated as a B14.2-task hard stop during those tasks; it is the explicit phase-gate input that determines branch selection at B14_2-06.

```yaml
forbidden_public_regressions:
  runtime_owner: validate_b14_2_application_layer_gate_invariants and validate_b14_2_no_network_trust_authority and validate_b14_2_public_surface_recruiter_gate_resmoke and validate_b14_2_no_tunnel_secret_leak and validate_b14_2_no_public_url_or_hostname_literal
  patterns:
    - PUBLIC_DEMO_EXPOSURE_true_with_unauthenticated_demo_route_response_other_than_401_Basic_realm_asr_demo_recruiter
    - PUBLIC_DEMO_EXPOSURE_true_with_OpenAPI_or_docs_route_mounted_unprotected
    - PUBLIC_DEMO_EXPOSURE_true_with_application_layer_authority_decision_keyed_on_network_origin
    - PUBLIC_DEMO_EXPOSURE_true_with_authenticated_demo_health_payload_other_than_canonical_status_ok
    - public_surface_recruiter_gate_resmoke_record_authored_without_operator_evidence_reference
    - public_surface_recruiter_gate_resmoke_coverage_claimed_without_all_four_vantage_points
    - recruiter_password_logged_under_public_exposure
    - Tailscale_auth_key_logged
    - Tailscale_auth_key_committed_to_repository
    - Cloudflare_token_committed_to_repository
    - public_URL_literal_committed
    - stable_hostname_literal_committed
    - IP_address_literal_committed
    - claim_of_success_keyed_on_ephemeral_tunnel_URL_alone
    - SUCCESS_WITH_STABLE_NAMED_EXPOSURE_asserted_in_a_B14_2_record
    - carried_marker_B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE_cleared_outside_the_gate_restored_branch
    - upload_with_manual_ground_truth_FAIL_observation_converted_to_PASS_without_matching_B14_2_04_re_smoke_evidence
    - predecessor_plan_or_report_file_modified_by_a_B14_2_task
    - libs_asr_router_runtime_py_modified
    - services_frontend_app_demo_types_ts_router_field_shape_modified
```

## 8. Audit checklist

| Audit id | Source validator | PASS evidence | Negative case disproof |
|---|---|---|---|
| AUD-REPORT-SHAPE | validate_report_shape | OK_REPORT_SHAPE and schema hash | malformed report fixture fails |
| AUD-APPROVAL-PACKET | validate_approval_packet | OK_APPROVAL_PACKET and wrapper hash | missing wrapper fixture fails |
| AUD-PATH-LOCK | validate_b14_2_path_locks | OK_CHANGED_FILES_PATH_LOCKED and diff range | unauthorized file fixture fails (including predecessor-plan-touch fixture) |
| AUD-APP-LAYER-GATE | validate_b14_2_application_layer_gate_invariants | OK_B14_2_APPLICATION_LAYER_GATE | network-trust-bypass fixture fails |
| AUD-NO-NETWORK-TRUST | validate_b14_2_no_network_trust_authority | OK_B14_2_NO_NETWORK_TRUST_AUTHORITY | network-origin-decision fixture fails |
| AUD-RECRUITER-PRESERVED-LOOPBACK | validate_b14_2_recruiter_gate_preserved_under_public_exposure | OK_B14_2_RECRUITER_GATE_PRESERVED | unauthenticated-200 fixture fails |
| AUD-HEALTH-UNDER-PUBLIC-EXPOSURE | validate_b14_2_health_payload_preserved_under_public_exposure | OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE | non-canonical-payload fixture fails |
| AUD-OPENAPI-DOCS | validate_b14_2_openapi_docs_visibility | OK_B14_2_OPENAPI_DOCS_OFF | mounted-unprotected-openapi fixture fails |
| AUD-PUBLIC-SURFACE-RESMOKE | validate_b14_2_public_surface_recruiter_gate_resmoke | OK_B14_2_PUBLIC_SURFACE_RECRUITER_GATE_RESMOKE | fabricated-PASS resmoke fixture fails; partial-coverage resmoke fixture fails |
| AUD-UPLOAD-WITH-GT-CLASSIFIED | validate_b14_2_upload_with_gt_classification | OK_B14_2_UPLOAD_WITH_GT_CLASSIFIED | classification asserted without matching B14_2-04 evidence fails |
| AUD-NO-TUNNEL-SECRET | validate_b14_2_no_tunnel_secret_leak | OK_B14_2_NO_TUNNEL_SECRET_LEAK | committed-auth-key fixture fails |
| AUD-NO-PUBLIC-URL | validate_b14_2_no_public_url_or_hostname_literal | OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | committed-https-non-loopback fixture fails; committed-IP-address fixture fails |
| AUD-BROUTE-FROZEN | validate_b14_2_broute_compatibility_under_public_exposure | OK_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | router-schema-edit fixture fails; types.ts-router-field-shape-edit fixture fails |
| AUD-FUTURE-CONSTRAINTS | validate_future_constraints --constraint-profile b14_2 | OK_FUTURE_CONSTRAINTS | regressing-FC fixture fails; missing-FC-B15-FROZEN fixture fails |
| AUD-RP-B15-PASS | validate_b14_2_recovery_packet_b15_recruiter_gate | OK_RP_B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE | recovery-packet asserted without all-four authenticated_access_only re-smoke fixture fails |
| AUD-NO-IMPROVISATION | validate_no_banned_phrases | OK_NO_BANNED_PHRASES | banned-phrase fixture fails |

## 9. Communication rules

```yaml
planning_report_required_before_execution: true
execution_report_required_before_closure: true
phase_gate_report_required_before_phase_approval: true
supplemental_evidence_read_only: true
human_action_request_transport: CHANGE_SCOPE_with_human_action_request_id
plan_authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
plan_authoring_approval_request_recorded_in: reports/rp5/b14_2_plan_authoring_report.md
plan_authoring_orchestrator_decision_scope: plan_authoring
plan_authoring_orchestrator_decision_input_accepted_report_commit: null
no_B14_2_implementation_task_starts_until: an APPROVE_FOR_EXECUTION decision for this plan package is recorded by the orchestrator, followed by an APPROVE_PLAN decision for the first B14.2 task (B14_2-00)
context_window_hygiene_required: true
context_window_hygiene_policy: after every two or three executed tasks within a phase, or at any phase boundary, the orchestrator should prefer a new Claude window to keep the working context narrow and evidence-focused
```

## 10. Cross-document conflict resolution

PLAN_CONFLICT activates when any predicate holds: marker mismatch across files, hard-stop marker without recovery packet, recovery-packet marker missing from registry, approval-packet fields disagree with schema, report-shape names missing from schema, phase-gate authority appearing inside a task body, tracker runtime values appearing inside schema, B15 future-constraint id missing from section 3 preservation table, the carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` cleared by any task other than the gate-restored-branch phase-approval recording, an operator-observed `unauthenticated_access_observed` value converted to `authenticated_access_only` in any record, or an operator-observed `upload_with_manual_ground_truth=FAIL` value converted to `PASS` without matching B14_2-04 re-smoke evidence. Resolution: CHANGE_SCOPE with all disagreeing files patched in one commit.
