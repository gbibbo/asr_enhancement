# BR-07 Future Constraint Preservation Records

This document records future-phase constraints preserved across the B-route
seam. Each entry is a `future_constraint_preservation_record` per
`docs/plans/broute/state_packet_schemas.yaml` with the eight required fields.
Authority for the constraint table lives in
`docs/plans/broute/orchestrator_plan.md` section 3. This file is the BR-07
deliverable consumed by `scripts/rp5/validate_future_constraints.py`.

The entries below cover the four future phases declared by the pre-plan:
B14.0 public gate, B14.1 Funnel, B15 multi-network smoke, and the
datamove1 handoff. The B-route phase must not enact any string listed under
`forbidden_current_plan_regression`.

## FC-B14-0-PUBLIC-GATE

- constraint_id: FC-B14-0-PUBLIC-GATE
- source_preplan_section: preplan §4
- current_scope_impact: B-route must not expose public routes
- must_preserve_in_current_plan: B14.0 starts after B-route PASS
- forbidden_current_plan_regression: adding recruiter auth or public tunnel work inside B-route
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B14.0
- out_of_scope_but_preserved: true

## FC-B14-1-FUNNEL

- constraint_id: FC-B14-1-FUNNEL
- source_preplan_section: preplan §5
- current_scope_impact: B-route must keep loopback binding compatible
- must_preserve_in_current_plan: B14.1 starts after B14.0 PASS
- forbidden_current_plan_regression: adding Funnel, serve, URL, or systemd work inside B-route
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B14.1
- out_of_scope_but_preserved: true

## FC-B15-MULTI-NETWORK

- constraint_id: FC-B15-MULTI-NETWORK
- source_preplan_section: preplan §6
- current_scope_impact: B-route response fields must remain smokeable
- must_preserve_in_current_plan: B15 starts after B14.1 PASS
- forbidden_current_plan_regression: claiming public smoke coverage from local B-route tests
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B15
- out_of_scope_but_preserved: true

## FC-HANDOFF-DATAMOVE1

- constraint_id: FC-HANDOFF-DATAMOVE1
- source_preplan_section: preplan §7
- current_scope_impact: B-route schema must be adapter-compatible
- must_preserve_in_current_plan: handoff swap waits for datamove1 tag
- forbidden_current_plan_regression: changing schema after handoff compatibility gate without diff report
- validator_or_review_check: validate_future_constraints
- future_phase_owner: B-handoff
- out_of_scope_but_preserved: true
