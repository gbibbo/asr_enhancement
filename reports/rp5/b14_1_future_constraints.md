# B14.1 Future Constraint Preservation Records

This document records the future-phase constraints preserved across the B14.1
public-exposure seam (Tailscale Funnel layered on the B14.0 recruiter HTTPBasic
application-layer gate). Each entry is a `future_constraint_preservation_record`
per `docs/plans/b14_1/state_packet_schemas.yaml`. Authority for the constraint
table lives in `docs/plans/b14_1/orchestrator_plan.md` section 3. This file is
the B14_1-08 deliverable consumed by `scripts/rp5/validate_future_constraints.py`
under the b14_1 profile. No B14.1 phase work may enact any string listed under
`forbidden_current_plan_regression`.

## FC-B14-1-FUNNEL

- constraint_id: FC-B14-1-FUNNEL
- source_section: orchestrator_plan.md section 3
- current_scope_impact: B14.1 introduces the public-exposure flag plumbing and the tunnel configuration template, while keeping the recruiter HTTPBasic application-layer gate as the sole authority for public access; exposure is gated by recruiter auth, not by network trust
- must_preserve_in_current_plan: every B14.1 task keeps the application-layer gate as the sole authority for public access; exposure remains gated by recruiter auth and not by network trust; the exposure_state_record asserts a stable-named exposure or an explicit blocker
- forbidden_current_plan_regression: bypassing the recruiter gate via any network-trust assumption; claiming success from an ephemeral URL alone
- validator_or_review_check: validate_b14_1_application_layer_gate_invariants, validate_b14_1_exposure_state_record
- future_phase_owner: B14.1 active implementation; preservation owner for B15 and B-handoff
- out_of_scope_but_preserved: true

## FC-B15-MULTI-NETWORK

- constraint_id: FC-B15-MULTI-NETWORK
- source_section: orchestrator_plan.md section 3
- current_scope_impact: B14.1 verifies the recruiter-gated surface on loopback only; public-network smokeability of that surface remains intact for B15 without being exercised in B14.1
- must_preserve_in_current_plan: B15 starts after B14.1 PASS; B14.1 single-host loopback verification must not claim public-network or multi-network smoke coverage
- forbidden_current_plan_regression: claiming multi-network smoke coverage from a single-host B14.1 test
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B15
- out_of_scope_but_preserved: true

## FC-HANDOFF-DATAMOVE1

- constraint_id: FC-HANDOFF-DATAMOVE1
- source_section: orchestrator_plan.md section 3
- current_scope_impact: B14.1 leaves the router schema adapter-compatible; libs/asr/router_runtime.py is unmodified across all B14.1 tasks
- must_preserve_in_current_plan: the datamove1 router swap waits for the handoff gate; B14.1 introduces no router schema change and no cache-key schema change
- forbidden_current_plan_regression: changing the router schema; editing libs/asr/router_runtime.py
- validator_or_review_check: validate_future_constraints, validate_b14_1_broute_compatibility_under_public_exposure
- future_phase_owner: B-handoff
- out_of_scope_but_preserved: true

## FC-BROUTE-FROZEN

- constraint_id: FC-BROUTE-FROZEN
- source_section: orchestrator_plan.md section 3
- current_scope_impact: BR-01..BR-08 deliverables and schemas remain frozen under B14.1 public exposure; B14.1 re-verified B-route compatibility under the public-exposure flag at B14_1-07 with frozen fingerprints unchanged
- must_preserve_in_current_plan: BR-01..BR-08 task statuses remain PASS in the tracker; the B-route deliverables and schemas are not edited by any B14.1 task
- forbidden_current_plan_regression: edits to docs/plans/broute/, libs/asr/router_runtime.py, or the services/frontend/app/demo/types.ts router-field shape
- validator_or_review_check: validate_b14_1_broute_compatibility_under_public_exposure, validate_b14_1_path_locks
- future_phase_owner: B-route (frozen post-approval); preservation owner for B14.1 and every subsequent phase
- out_of_scope_but_preserved: true

## FC-B14-0-GATE-PRESERVED

- constraint_id: FC-B14-0-GATE-PRESERVED
- source_section: orchestrator_plan.md section 3 (FC-B14-0-PUBLIC-GATE preservation seam)
- current_scope_impact: B14.1 preserves the recruiter HTTPBasic gate, the BR-02 health invariant, and the admin/recruiter separation under public exposure; B14_1-02, B14_1-03, and B14_1-07 re-verified these under the public-exposure flag
- must_preserve_in_current_plan: the recruiter HTTPBasic gate remains intact under public exposure; the authenticated /demo/health payload remains canonical; admin and recruiter credentials remain separated
- forbidden_current_plan_regression: removing or bypassing the recruiter gate; returning a non-canonical /demo/health payload to an authenticated request; conflating admin and recruiter credentials
- validator_or_review_check: validate_b14_1_application_layer_gate_invariants, validate_b14_1_recruiter_gate_preserved_under_public_exposure, validate_b14_1_health_payload_preserved_under_public_exposure
- future_phase_owner: B14.1 active implementation; preservation owner for B15 and B-handoff
- out_of_scope_but_preserved: true
