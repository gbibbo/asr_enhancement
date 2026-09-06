# B15-07 Phase Gate Report

Task: B15-07. Branch: feature/demo-runtime-rp5-v1.

This file is the B15-07 deliverable and serves as both a `phase_gate_report`
(schema `docs/plans/b15/state_packet_schemas.yaml > phase_gate_report`) and
a `b15_closure_report` (schema `> b15_closure_report`). The phase outcome is
`B15_FAILED_PENDING_PHASE_RETURN`. The B15 phase-gate full-success branch is
foreclosed; the explicit-blocker branch is not reached; the
failed-pending-phase-return branch is reached. The active carried marker
`B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` is preserved and is not
cleared by this report. No public-exposure success claim is asserted, and
`SUCCESS_WITH_STABLE_NAMED_EXPOSURE` is not asserted.

## STATE SNAPSHOT

- current_phase: B15
- current_task: B15-07
- last_completed_task: B15-06
- expected_next_task: B15-07
- active_markers:
  - B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
- repo_root: /home/gbibbo/code/asr_enhancement
- branch: feature/demo-runtime-rp5-v1
- working_tree_status: clean before B15-07 authoring

## PHASE

- phase: B15
- predecessor_phase: B14.1 (APPROVED via the explicit-blocker branch)
- scope_change_repairs_applied_to_b15:
  - B15-03: materialized validate_report_shape and validate_approval_packet
  - B15-04: materialized print_pending_human_action_requests
  - B15-05: execution-rail repair admitting honest observed regressions and
    vantage-point-conditional mobile_layout
  - B15-07: materialized the b15 profile in validate_future_constraints
    (accepted_report_commit 218c9c0)

## PHASE OUTCOME

- phase_outcome: B15_FAILED_PENDING_PHASE_RETURN
- reason: the B15-05 multi-network smoke evidence observed
  `recruiter_gate_observed_status: unauthenticated_access_observed` on all
  four vantage points and `upload_with_manual_ground_truth: FAIL` on all
  four vantage points. The recruiter HTTPBasic application-layer gate is
  the sole authority for public access (FC-B14-1-PUBLIC-GATE); operator
  smoke evidence shows that authority was not honoured at the public
  surface during the smoke window. The B15-06 adjudication recorded
  `claim_status: FAILED_PENDING_PHASE_RETURN`,
  `all_coverage_items_passed: false`, and decision-rule routing
  `RETURN_TO_B14`.

## GATE PREDICATES

- full_success_branch: FORECLOSED
  - SUCCESS_WITH_STABLE_NAMED_EXPOSURE is not asserted.
  - public_exposure_smoke_claim_record.claim_status is
    FAILED_PENDING_PHASE_RETURN, not SUCCESS_WITH_STABLE_NAMED_EXPOSURE.
  - At least one coverage-item outcome did not pass and at least one
    forbidden public regression pattern fired
    (B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE).
- explicit_blocker_branch: NOT_REACHED
  - Operator smoke evidence was supplied for all four vantage points, so
    B15-05 did not stop at BLOCKED_BY_HUMAN_ACTION; the phase did not
    rest on a carried-HAR explicit blocker.
- failed_pending_phase_return_branch: REACHED
  - The B15-06 adjudication recorded FAILED_PENDING_PHASE_RETURN with
    decision-rule routing RETURN_TO_B14 and a non-null
    explicit_blocker_id citation.

## VALIDATION RESULTS

The B15-07 final-verification checklist sentinels, run against the
materialized declarative records, are:

- OK_PLAN_COMPILES
- OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED
- OK_B15_SMOKE_RESULT_EVIDENCE_TRACED
- OK_B15_MULTI_NETWORK_SMOKE_OR_BLOCKED
- B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
  (preserved active carried marker; not cleared; not converted to PASS;
  fires deterministically against the B15-05 smoke-result records that
  recorded `unauthenticated_access_observed` on all four vantage points)
- OK_B15_QUOTA_STATE_ACCURATE
- OK_B15_UPLOAD_LIMIT_ENFORCED
- OK_B15_MOBILE_LAYOUT_OK
- OK_B15_CACHED_EXAMPLE_OK
- OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED
- OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL
- OK_FUTURE_CONSTRAINTS
- OK_REPORT_SHAPE
- OK_CHANGED_FILES_PATH_LOCKED

## FINAL-VERIFICATION SENTINELS

Identical to the VALIDATION RESULTS section above (the `b15_closure_report`
shape requires a `FINAL-VERIFICATION SENTINELS` section; the
`phase_gate_report` shape requires `VALIDATION RESULTS`; both list the
same sentinel set, recorded once in each section for shape conformance).

## CLAIM STATUS

- claim_status: FAILED_PENDING_PHASE_RETURN
- stable_named_exposure_supplied_by_reference: true (recorded at B15-04
  by reference only; never as a literal hostname)
- all_coverage_items_passed: false
- explicit_blocker_id: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
- blocker_recovery_packet: RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE
- success_with_stable_named_exposure_asserted: false
- no_public_url_or_hostname_literal_committed: true
- no_tunnel_secret_committed: true
- recruiter_credential_committed: false
- admin_credential_committed: false

## DECISION-RULE ROUTING

- routing: RETURN_TO_B14
- triggering_condition: the recruiter HTTPBasic gate authority was not
  honoured at the public surface across all four vantage points; the
  failure pattern matches the legacy demo_platform_plan section 37 Task
  B15.1 decision rule "if the public tunnel fails to expose the surface
  from any vantage point with the recruiter gate authority preserved,
  routing RETURN_TO_B14 fires".
- return_phase_if_any: B14 (specifically the B14.1 public-exposure seam
  for re-verification of the recruiter gate under public exposure; the
  exact next phase or task selection is reserved for the orchestrator
  after PHASE_REJECT)
- proceed_to_b_handoff_fires: false
- blocked_pending_human_action_fires: false

## CARRIED HAR POSTURE

- HAR-B14_1-STABLE-HOSTNAME-001: resolved (operator
  human_action_result accepted at the B15-04 boundary; by-reference only)
- HAR-B14_1-FUNNEL-CAPABILITY-001: resolved (residual auth-key flag
  declared supplied as host env; by-reference only)
- HAR-B15-MULTI-NETWORK-SMOKE-001: resolved with operator smoke evidence
  for all four vantage points and all nine coverage items; the operator
  evidence recorded unauthenticated_access_observed on all four vantage
  points and upload_with_manual_ground_truth FAIL on all four vantage
  points; the agent transcribed those operator outcomes verbatim and
  fabricated nothing.
- no_carried_har_remains_unresolved_blocking_b15_07: true
- public_exposure_success_state_at_phase_boundary: BLOCKED_BY_OBSERVED_REGRESSION

## FUTURE CONSTRAINTS

Five future-constraint preservation records are recorded in
`reports/rp5/b15_future_constraints.md` using the `b15` profile of
`scripts/rp5/validate_future_constraints.py`:

- FC-B15-MULTI-NETWORK (preserves the multi-network coverage contract;
  evidence exists for all four vantage points)
- FC-B14-1-PUBLIC-GATE (preserves recruiter HTTPBasic gate authority;
  operator-observed regression preserved-and-routed RETURN_TO_B14)
- FC-HANDOFF-DATAMOVE1 (router schema adapter compatibility preserved;
  no runtime code modified by B15)
- FC-BROUTE-FROZEN (predecessor plans and reports frozen post-approval;
  no B-route/B14.0/B14.1 deliverables modified by B15)
- FC-B14-0-GATE-PRESERVED (recruiter HTTPBasic gate, BR-02 health
  invariant, and admin/recruiter separation preserved; the observed
  public-surface regression is preserved as operator evidence and routed
  RETURN_TO_B14)

All five records carry `out_of_scope_but_preserved: true`. No active-plan
file enacts any forbidden_current_plan_regression string for any of the
five constraints.

## NEXT EXPECTED PHASE

- next_expected_phase: PHASE_REJECT_or_RETURN_TO_B14
- next_expected_orchestrator_decision: PHASE_REJECT (or an equivalent
  closure decision routing per the RETURN_TO_B14 outcome). Selection of
  the exact follow-on task or phase is reserved for the orchestrator and
  is not made by this report. B15-07 itself does not start any follow-on
  phase, return task, or B14 work.
- requires_orchestrator_decision: true

## BLOCKERS

- B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE (active carried marker;
  preserved; not cleared; not converted to PASS)
- recruiter HTTPBasic gate authority was not honoured at the public
  surface in the B15-05 operator smoke evidence on all four vantage
  points; preserved-and-routed RETURN_TO_B14.
- upload_with_manual_ground_truth was FAIL on all four vantage points in
  the B15-05 operator smoke evidence; preserved as operator evidence and
  contributes to the FAILED_PENDING_PHASE_RETURN outcome.
- HAR-B15-MULTI-NETWORK-SMOKE-001 itself is resolved (evidence supplied);
  the blocker is the content of that evidence, not a missing input.
- No literal public URL, public hostname, Tailscale auth-key, Cloudflare
  token, tunnel secret, recruiter password, admin password, or IP address
  was recorded by B15-07.
