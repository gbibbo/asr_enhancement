# B15-07 Future Constraint Preservation Records

This file is the B15-07 future-constraint deliverable. It contains exactly
five `future_constraint_preservation_record`s (schema
`docs/plans/b15/state_packet_schemas.yaml > future_constraint_preservation_record`)
covering the constraint ids required by the `b15` profile of
`scripts/rp5/validate_future_constraints.py`. Each record uses the eight
required fields of that profile, every record carries
`out_of_scope_but_preserved: true`, and no literal public URL, public
hostname, or secret appears in the document.

The records describe observed regressions as preserved-and-routed
(RETURN_TO_B14 via the B15-06 adjudication), not as B15 enacting any
forbidden current-plan regression.

## FC-B15-MULTI-NETWORK

- constraint_id: FC-B15-MULTI-NETWORK
- source_section: docs/plans/b15/orchestrator_plan.md section 3 (Future constraint preservation)
- current_scope_impact: B15-05 collected operator smoke evidence for all four required vantage points (windows_local, mobile_cellular, other_wifi, vpn_or_external_tester) and all nine coverage items; coverage matrix (B15-01) and smoke-evidence tracing (B15-05 validators) confirm multi-network coverage exists and is not claimed from fewer than four operator vantage points
- must_preserve_in_current_plan: every multi-network coverage claim must trace to an operator-supplied multi_network_smoke_result_record per vantage point with a non-null evidence_reference; the four required vantage points are enumerated in the schema
- forbidden_current_plan_regression: claiming multi-network coverage from fewer than four operator-supplied vantage-point records; fabricating any vantage-point outcome; recording smoke results without an operator evidence_reference
- validator_or_review_check: scripts/rp5/validate_b15_multi_network_smoke.py, scripts/rp5/validate_b15_smoke_result_evidence.py, scripts/rp5/validate_b15_coverage_matrix.py, scripts/rp5/validate_future_constraints.py --constraint-profile b15
- future_phase_owner: B15 active implementation (coverage preserved into RETURN_TO_B14 follow-on)
- out_of_scope_but_preserved: true

## FC-B14-1-PUBLIC-GATE

- constraint_id: FC-B14-1-PUBLIC-GATE
- source_section: docs/plans/b15/orchestrator_plan.md section 3 (Future constraint preservation)
- current_scope_impact: the recruiter HTTPBasic application-layer gate is the sole authority for public access; B15 did not modify any application, library, infrastructure, or runtime code; the B15-05 operator smoke evidence observed recruiter_gate_observed_status unauthenticated_access_observed on all four vantage points; that observed regression is preserved verbatim, the active marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE is preserved-not-cleared, and the B15-06 adjudication routed RETURN_TO_B14 with claim_status FAILED_PENDING_PHASE_RETURN; B15 did not assert SUCCESS_WITH_STABLE_NAMED_EXPOSURE and did not accept any ephemeral tunnel url as success evidence
- must_preserve_in_current_plan: application-layer authority of the recruiter HTTPBasic gate; no public-exposure success claim keyed on an ephemeral url alone; no literal hostname/url/secret committed; observed regressions are surfaced honestly, never softened
- forbidden_current_plan_regression: removing or bypassing the recruiter HTTPBasic gate from active-plan code; treating an ephemeral tunnel url as public-exposure success evidence; softening an observed regression to a PASS in B15 reports
- validator_or_review_check: scripts/rp5/validate_b15_recruiter_gate_preserved_under_public_smoke.py, scripts/rp5/validate_b15_public_exposure_smoke_claim.py, scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py, scripts/rp5/validate_future_constraints.py --constraint-profile b15
- future_phase_owner: B15 active implementation now routing RETURN_TO_B14 for re-verification of the recruiter gate under public exposure
- out_of_scope_but_preserved: true

## FC-HANDOFF-DATAMOVE1

- constraint_id: FC-HANDOFF-DATAMOVE1
- source_section: docs/plans/b15/orchestrator_plan.md section 3 (Future constraint preservation)
- current_scope_impact: the router_runtime adapter schema remains unchanged; B15 modified no application, library, infrastructure, compose, or runtime file; the datamove1 handoff target remains adapter-compatible after B15-00 through B15-07
- must_preserve_in_current_plan: router schema adapter compatibility for the future datamove1 router swap; verification-only posture of B15
- forbidden_current_plan_regression: modifying the runtime router file in B15 scope; performing any datamove1 router swap from B15
- validator_or_review_check: scripts/rp5/validate_future_constraints.py --constraint-profile b15, scripts/rp5/validate_b15_path_locks.py (PL-B15-SCRIPTS, PL-B15-PLANS, PL-B15-REPORTS, PL-B15-TESTS, PL-B15-CONFIG)
- future_phase_owner: B-handoff (datamove1 router swap; out of B15 scope)
- out_of_scope_but_preserved: true

## FC-BROUTE-FROZEN

- constraint_id: FC-BROUTE-FROZEN
- source_section: docs/plans/b15/orchestrator_plan.md section 3 (Future constraint preservation)
- current_scope_impact: BR-01 through BR-08, B14_0-00 through B14_0-08, and B14_1-00 through B14_1-08 deliverables, schemas, plans, and reports remain frozen; B15 did not edit docs/plans/broute/, docs/plans/b14_0/, docs/plans/b14_1/, or the router_runtime file; predecessor phase approvals stand
- must_preserve_in_current_plan: B-route, B14.0, and B14.1 deliverables and schemas frozen post-approval; predecessor approval commits unchanged
- forbidden_current_plan_regression: editing predecessor plan or report files in B15 scope; reopening B-route, B14.0, or B14.1 task records from B15
- validator_or_review_check: scripts/rp5/validate_b15_path_locks.py, scripts/rp5/validate_future_constraints.py --constraint-profile b15
- future_phase_owner: B-route, B14.0, B14.1 (all frozen post-approval)
- out_of_scope_but_preserved: true

## FC-B14-0-GATE-PRESERVED

- constraint_id: FC-B14-0-GATE-PRESERVED
- source_section: docs/plans/b15/orchestrator_plan.md section 3 (Future constraint preservation)
- current_scope_impact: the recruiter HTTPBasic gate, the BR-02 health-payload invariant, and admin/recruiter separation remain intact in active-plan code; B15 did not return any non-canonical demo health payload to authenticated requests and modified no application, library, infrastructure, or runtime code; the operator-observed unauthenticated_access_observed pattern is preserved in B15-05 smoke evidence and routed RETURN_TO_B14 via the B15-06 adjudication, not absorbed into a B15 PASS
- must_preserve_in_current_plan: recruiter HTTPBasic gate authority, BR-02 health-payload invariant, admin/recruiter separation, canonical demo health payload to authenticated requests
- forbidden_current_plan_regression: returning a non-canonical demo health payload to authenticated requests; collapsing admin and recruiter roles; removing the recruiter gate from active-plan code
- validator_or_review_check: scripts/rp5/validate_b15_recruiter_gate_preserved_under_public_smoke.py, scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py, scripts/rp5/validate_future_constraints.py --constraint-profile b15
- future_phase_owner: B15 active implementation now routing RETURN_TO_B14 for re-verification
- out_of_scope_but_preserved: true
