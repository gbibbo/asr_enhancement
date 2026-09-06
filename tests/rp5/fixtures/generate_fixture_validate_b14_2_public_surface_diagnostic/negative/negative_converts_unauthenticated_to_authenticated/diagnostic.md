# B14.2 Public-Surface Recruiter-Gate Diagnostic (Fixture)
Task: B14_2-01 fixture
Phase: B14.2 (repair microphase)
Branch: feature/demo-runtime-rp5-v1
Record type: declarative diagnostic; read-only; no public-network commands

## Reference Sources (cited by reference only)

- reports/rp5/b15_multi_network_smoke_results.md
- reports/rp5/b15_smoke_adjudication.md
- reports/rp5/b15_phase_gate.md
- docs/progress/rp5_progress.yaml

## Freeze-Audit Pair

- plan_pinned_tracker_commit: bf8560a6c3493692ccd8a35926a5ddc647b627f6
- tracker_self_reference_spelling: this_tracker_commit_self_reference_per_b14_1_convention

## B15 Operator Evidence Preserved Verbatim by Reference

### Vantage point: windows_local

- recruiter_gate_observed_status: authenticated_access_only
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: fixture_operator_smoke_windows_local_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001

### Vantage point: mobile_cellular

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: fixture_operator_smoke_mobile_cellular_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001

### Vantage point: other_wifi

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: fixture_operator_smoke_other_wifi_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001

### Vantage point: vpn_or_external_tester

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: fixture_operator_smoke_vpn_or_external_tester_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001

### Anti-falsification statements

- No record converts unauthenticated_access_observed to authenticated_access_only.
- No record converts upload_with_manual_ground_truth FAIL to PASS without matching B14_2-04 evidence.

## Diagnostic Zones

### Zone A: B14.0 recruiter HTTPBasic middleware at loopback (frozen PASS)

- Hypothesis A1 (baseline; unconfirmed at the public surface): the middleware code is correct at loopback.

### Zone B: B14.1 public-exposure flag plumbing at loopback (frozen approved through explicit-blocker branch)

- Hypothesis B1 (baseline; unconfirmed at the public surface): the application-side plumbing is correct at loopback.

### Zone C: Funnel-terminated public surface (operator-owned)

- Hypothesis C1 (header-strip; unconfirmed): the Funnel terminator may strip the Authorization header.
- Hypothesis C2 (port-forward; unconfirmed): the Funnel terminator may forward to a FastAPI port with PUBLIC_DEMO_EXPOSURE false.
- Hypothesis C3 (route-mapping; unconfirmed): the Funnel serve configuration may map a route bypassing the recruiter middleware.
- Hypothesis C4 (interface-binding; unconfirmed): FastAPI may be bound to a non-loopback interface allowing direct bypass.
- Hypothesis C5 (flag-drift; unconfirmed): the FastAPI process behind the Funnel may have been started with PUBLIC_DEMO_EXPOSURE unset.

## Explicit Boundaries

- Upload-with-manual-ground-truth classification is deferred to B14_2-05.
- B14_2-01 does not resolve the carried marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE.
