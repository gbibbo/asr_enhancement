# B14.0 Future Constraint Preservation Records

This document records future-phase constraints preserved across the B14.0
seam (recruiter HTTPBasic public-access gate). Each entry is a
`future_constraint_preservation_record` per
`docs/plans/b14_0/state_packet_schemas.yaml` (the schema is inherited
verbatim from the B-route state_packet_schemas.yaml). Authority for the
constraint table lives in `docs/plans/b14_0/orchestrator_plan.md` section 3.
This file is the B14_0-08 deliverable consumed by
`scripts/rp5/validate_future_constraints.py`.

The entries below cover the four future-phase constraints that the validator
requires (FC-B14-0-PUBLIC-GATE, FC-B14-1-FUNNEL, FC-B15-MULTI-NETWORK,
FC-HANDOFF-DATAMOVE1) plus the B14.0-introduced constraint FC-BROUTE-FROZEN
that pins the B-route deliverables against in-scope regression under
recruiter auth. No B14.0 phase work may enact any string listed under
`forbidden_current_plan_regression`.

## FC-B14-0-PUBLIC-GATE

- constraint_id: FC-B14-0-PUBLIC-GATE
- source_preplan_section: preplan section 4
- current_scope_impact: B14.0 has implemented the recruiter HTTPBasic public-access gate on every public /demo/* route; the constraint is preserved going forward against any future-phase rollback of the gate
- must_preserve_in_current_plan: each B14.0 task PASS through B14_0-08 has verified the gate is in place and the canonical health invariant is preserved on the authenticated path
- forbidden_current_plan_regression: removing the recruiter gate, routing any public /demo/* request to an unauthenticated handler, or returning a non-canonical /demo/health payload to an authenticated request
- validator_or_review_check: validate_b14_0_recruiter_auth_contract, validate_b14_0_health_payload_preserved_under_auth, validate_b14_0_e2e_manual_smoke_with_auth, validate_b14_0_no_credential_leak, validate_b14_0_auth_separation_invariants
- future_phase_owner: B14.0 active implementation; preservation owner for B14.1, B15, and B-handoff
- out_of_scope_but_preserved: true

## FC-B14-1-FUNNEL

- constraint_id: FC-B14-1-FUNNEL
- source_preplan_section: preplan section 5
- current_scope_impact: B14.0 keeps the recruiter-gated app loopback-bound only; no public-network exposure artefact is introduced
- must_preserve_in_current_plan: B14.1 starts after B14.0 PASS; the Funnel layer must compose on top of the recruiter gate without bypassing it
- forbidden_current_plan_regression: adding Tailscale-Funnel exposure, the funnel-serve command, a systemd unit installation for Funnel, or any public URL artefact inside B14.0
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B14.1
- out_of_scope_but_preserved: true

## FC-B15-MULTI-NETWORK

- constraint_id: FC-B15-MULTI-NETWORK
- source_preplan_section: preplan section 6
- current_scope_impact: B14.0 response fields and the recruiter-auth surface remain smokeable from a multi-network harness when B15 introduces one
- must_preserve_in_current_plan: B15 starts after B14.1 PASS; B14.0 local-loopback tests must not claim public-network smoke coverage
- forbidden_current_plan_regression: claiming public-network smoke coverage from local B14.0 tests; introducing public-network test fixtures inside B14.0
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B15
- out_of_scope_but_preserved: true

## FC-HANDOFF-DATAMOVE1

- constraint_id: FC-HANDOFF-DATAMOVE1
- source_preplan_section: preplan section 7
- current_scope_impact: B14.0 leaves the router schema adapter-compatible; libs/asr/router_runtime.py is unmodified across all B14.0 tasks
- must_preserve_in_current_plan: handoff swap waits for the datamove1 tag; B14.0 introduces no router schema change and no cache-key schema change
- forbidden_current_plan_regression: changing the router schema or cache-key schema in B14.0; modifying libs/asr/router_runtime.py; changing the services/frontend/app/demo/types.ts router-field shape
- validator_or_review_check: validate_future_constraints, validate_b14_0_broute_compatibility_under_auth
- future_phase_owner: B-handoff
- out_of_scope_but_preserved: true

## FC-BROUTE-FROZEN

- constraint_id: FC-BROUTE-FROZEN
- source_preplan_section: B14.0 orchestrator_plan section 3 (future constraint preservation row added by B14.0)
- current_scope_impact: BR-01..BR-08 deliverables, the libs/asr/router_runtime.py byte-content fingerprint, and the services/frontend/app/demo/types.ts router-field shape remain frozen under B14.0 recruiter auth
- must_preserve_in_current_plan: every B14.0 task has left router_runtime.py sha256 dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc and the frontend RouterFields-shape sha256 b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c unchanged; BR-01..BR-08 task statuses remain PASS in the tracker
- forbidden_current_plan_regression: edits to docs/plans/broute/; edits to libs/asr/router_runtime.py; changes to the services/frontend/app/demo/types.ts router-field shape; rollback of any BR-01..BR-08 PASS status in the tracker
- validator_or_review_check: validate_b14_0_broute_compatibility_under_auth, validate_b14_0_path_locks
- future_phase_owner: B-route (frozen post-approval); preservation owner for B14.0 and every subsequent phase
- out_of_scope_but_preserved: true
