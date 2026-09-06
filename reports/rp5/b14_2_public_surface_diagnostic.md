# B14.2 Public-Surface Recruiter-Gate Diagnostic

Task: B14_2-01
Phase: B14.2 (repair microphase)
Branch: feature/demo-runtime-rp5-v1
Record type: declarative diagnostic; read-only; no public-network commands

## Purpose

Bound the locus of the B15-routed public-surface recruiter HTTPBasic gate regression `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` into three diagnostic zones (A, B, C). Cite all B15 evidence by reference only. Enumerate Zone-C (Funnel-terminator) hypotheses as unconfirmed candidates for the repair work at B14_2-02 and operator verification at B14_2-04. Defer upload-with-GT classification to B14_2-05. Do not assert any cause as confirmed. Do not clear the carried marker. Do not resolve either B14.2 HAR. Do not record any literal public URL, hostname, non-loopback IP address, auth-key, token, password, or secret.

## Reference Sources (cited by reference only)

The following B15 artifacts are consumed as read-only inputs. None is modified by this diagnostic.

- reports/rp5/b15_multi_network_smoke_results.md (B15-05 multi-network smoke results, four `multi_network_smoke_result_record` entries)
- reports/rp5/b15_smoke_adjudication.md (B15-06 adjudication, `public_exposure_smoke_claim_record` and `b15_decision_rule_routing_record`)
- reports/rp5/b15_phase_gate.md (B15-07 phase gate, outcome `B15_FAILED_PENDING_PHASE_RETURN`, routing `RETURN_TO_B14`)
- docs/progress/rp5_progress.yaml at pinned tracker commit bf8560a6c3493692ccd8a35926a5ddc647b627f6 (the B15 PHASE_REJECT recording commit; consumed as a freeze pin for the B15 evidence read by this diagnostic)

## Freeze-Audit Pair

- plan_pinned_tracker_commit: bf8560a6c3493692ccd8a35926a5ddc647b627f6
- tracker_self_reference_spelling: this_tracker_commit_self_reference_per_b14_1_convention

Both spellings reference the same B15 PHASE_REJECT closure recording. The plan literally pins the 40-character hash; the tracker today writes the closure self-reference as the named sentinel per the B14.1 convention. Recording both makes the freeze-audit deterministic across spellings.

## B15 Operator Evidence Preserved Verbatim by Reference

The following four-vantage-point observation set is recorded verbatim from `human_action_requests.HAR-B15-MULTI-NETWORK-SMOKE-001.supplied_values` at the pinned tracker commit. No value is converted, softened, or reinterpreted.

### Vantage point: windows_local

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: operator_smoke_windows_local_via_mobile_hotspot_2026-05-22_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
- five_curated_examples: PASS
- five_degradations: PASS
- whisper_provider: PASS
- assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
- upload_without_manual_ground_truth: PASS
- upload_limit_observed: enforced
- mobile_layout_observed: not_applicable
- cached_example_observed: all_curated_examples_resolved

### Vantage point: mobile_cellular

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: operator_smoke_mobile_cellular_2026-05-22_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
- five_curated_examples: PASS
- five_degradations: PASS
- whisper_provider: PASS
- assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
- upload_without_manual_ground_truth: PASS
- upload_limit_observed: enforced
- mobile_layout_observed: no_horizontal_scroll
- cached_example_observed: all_curated_examples_resolved

### Vantage point: other_wifi

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: operator_smoke_other_wifi_via_second_mobile_hotspot_2026-05-22_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
- five_curated_examples: PASS
- five_degradations: PASS
- whisper_provider: PASS
- assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
- upload_without_manual_ground_truth: PASS
- upload_limit_observed: enforced
- mobile_layout_observed: not_applicable
- cached_example_observed: all_curated_examples_resolved

### Vantage point: vpn_or_external_tester

- recruiter_gate_observed_status: unauthenticated_access_observed
- coverage_item_outcomes.upload_with_manual_ground_truth: FAIL
- evidence_reference: operator_smoke_vpn_or_external_tester_2026-05-22_no_literals
- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
- five_curated_examples: PASS
- five_degradations: PASS
- whisper_provider: PASS
- assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
- upload_without_manual_ground_truth: PASS
- upload_limit_observed: enforced
- mobile_layout_observed: not_applicable
- cached_example_observed: all_curated_examples_resolved

### Anti-falsification statements

- No record in this diagnostic converts unauthenticated_access_observed to authenticated_access_only; the B15-05 observation must not be converted to authenticated_access_only by any B14.2 task.
- No record in this diagnostic converts upload_with_manual_ground_truth FAIL to PASS; the B15-05 observation must not be converted to PASS by any B14.2 task without matching B14_2-04 re-smoke evidence.
- AssemblyAI provider remains EXPLICIT_NA_PROVIDER_DISABLED on all four vantage points (provider intentionally disabled in the demo; not a regression).
- cached_example_observed remains all_curated_examples_resolved on all four vantage points (no curated-example regression).
- upload_limit_observed remains enforced on all four vantage points (no upload-limit regression).
- mobile_layout_observed remains no_horizontal_scroll on mobile_cellular and not_applicable on the three non-mobile vantage points (no mobile-layout regression).
- All anti-falsification statements are inherited from the docs/plans/b14_2/agent_plan.md section 2 carried_marker_clearance_policy and the section 2 forbidden-in-B14.2 list.

## Diagnostic Zones

### Zone A: B14.0 recruiter HTTPBasic middleware at loopback (frozen PASS)

The B14.0 recruiter HTTPBasic middleware, when invoked through FastAPI at the loopback base-url http://127.0.0.1:8001, enforces the recruiter HTTPBasic challenge per `validate_b14_0_recruiter_auth_contract` emitting `OK_B14_0_RECRUITER_AUTH_CONTRACT` at the B14.0 PHASE_APPROVE recording (`phase_approvals.B14.0.accepted_phase_gate_report_commit 7e9ce1f7067f938d2b58a7a4e8615101b0012c58`). B14.2 does not touch any B14.0 file.

- Hypothesis A1 (baseline statement, not a regression candidate; unconfirmed at the public surface): the B14.0 middleware code is correct at loopback and the regression is unlikely to originate inside the middleware itself. This hypothesis is consistent with the B14.0 PASS evidence but cannot be independently verified at the public surface without operator action.

### Zone B: B14.1 public-exposure flag plumbing at loopback (frozen approved through explicit-blocker branch only)

The B14.1 application-side public-exposure flag plumbing, when invoked at the loopback base-url http://127.0.0.1:8001 with PUBLIC_DEMO_EXPOSURE=true, enforces the recruiter HTTPBasic challenge end-to-end per `validate_b14_1_recruiter_gate_preserved_under_public_exposure` emitting `OK_B14_1_RECRUITER_GATE_PRESERVED` in the frozen B14.1 execution evidence. B14.1 was approved through the explicit-blocker branch only (`plan_authoring_approvals.B15.predecessor_phase_approval.approval_branch: explicit_blocker_branch_only`); the gate-preservation-under-Funnel predicate was admitted via the carried-HAR blocker route at B14.1 phase-gate time, not satisfied by exercise against the actual Funnel-terminated public surface. B14.2 does not touch any B14.1 file.

- Hypothesis B1 (baseline statement, not a regression candidate; unconfirmed at the public surface): the B14.1 application-side plumbing is correct at loopback and the regression is unlikely to originate inside the application-side flag plumbing. This hypothesis is consistent with the loopback-only validator evidence but cannot be independently verified at the Funnel-terminated public surface without operator action.

### Zone C: Funnel-terminated public surface (operator-owned; not directly inspectable by the agent)

This is the locus most consistent with the B15-05 operator-observed regression. The following hypotheses are unconfirmed candidates only; none is asserted as a confirmed cause. Confirmation belongs to the application/config repair work at B14_2-02 (services/api/app/ scope and infra/tunnel/funnel_config.template.yaml placeholder scope) and the operator-supplied four-vantage-point public-surface re-smoke at B14_2-04 under HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001.

- Hypothesis C1 (header-strip; unconfirmed): the Funnel terminator may forward the request to FastAPI without preserving the Authorization header (or without preserving the 401 WWW-Authenticate reply on the return path), suppressing the recruiter HTTPBasic challenge from reaching the client.
- Hypothesis C2 (port-forward; unconfirmed): the Funnel terminator may forward to a FastAPI port or instance whose PUBLIC_DEMO_EXPOSURE value is false, returning the unauthenticated path that is legal under loopback dev mode.
- Hypothesis C3 (route-mapping; unconfirmed): the Funnel serve configuration may map one or more public routes (for example health or openapi probes) without the recruiter middleware in front of them, and the operator's smoke walk may have surfaced one of those unprotected routes as the unauthenticated response.
- Hypothesis C4 (interface-binding; unconfirmed): FastAPI may be bound to a non-loopback interface accessible directly through the host network, allowing direct bypass of the Funnel terminator and the gate enforcement that depends on the application-side flag.
- Hypothesis C5 (flag-drift; unconfirmed): the FastAPI process running behind the Funnel exposure may have been started with PUBLIC_DEMO_EXPOSURE unset or false, leaving the application in the loopback-dev posture where the recruiter middleware path differs from the public-exposure-true posture.

## Explicit Boundaries

- B14_2-01 does not prove the repair. B14_2-02 owns the application/config repair scope; B14_2-04 owns the operator-supplied public-surface re-smoke verification.
- B14_2-01 does not perform public-network verification. The agent runs no Funnel, Tailscale, Cloudflare, ngrok, systemd, Docker Compose, curl-against-non-loopback, browser, or public endpoint check during B14_2-01.
- B14_2-01 does not resolve the carried marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE. Clearance is reserved for the B14.2 PHASE_APPROVE recording on the gate-restored branch per docs/plans/b14_2/agent_plan.md section 2 carried_marker_clearance_policy.
- B14_2-01 does not resolve HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001. The HAR remains pre_declared_unresolved; its inputs are consumed at B14_2-04 closure.
- B14_2-01 does not resolve HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001. The HAR remains pre_declared_conditional; its trigger fires only at B14_2-05 if the deterministic classification rule cannot decide from the four B14_2-04 records alone.
- Upload-with-manual-ground-truth classification is deferred to B14_2-05 per docs/plans/b14_2/agent_plan.md section 2 upload_with_gt_classification_rule; B14_2-01 does not assert linked_to_gate, independent_defer, or re_smoke_evidence_pending.
- B14_2-01 records no literal public URL, hostname, non-loopback IP address, Tailscale auth-key, Cloudflare token, recruiter password, admin password, or secret. References to the loopback address 127.0.0.1 appear only in the context of validator base-url defaults inherited from the B14.0/B14.1 frozen validators.

## Next Steps

- B14_2-02 authors the application/config repair restoring the recruiter HTTPBasic gate at the Funnel-exposed public surface (services/api/app/ under PL-B14_2-API-DEMO; placeholder template under PL-B14_2-TUNNEL-TEMPLATE; .env.example placeholders under PL-B14_2-CONFIG; loopback verification of application-layer gate and no-network-trust invariants under PUBLIC_DEMO_EXPOSURE=true).
- B14_2-03 re-emits loopback recruiter-gate-preserved, health-payload-preserved, OpenAPI-docs-visibility, no-public-URL, no-tunnel-secret, and broute-compatibility sentinels under PUBLIC_DEMO_EXPOSURE=true.
- B14_2-04 collects operator-supplied four-vantage-point public-surface re-smoke evidence under HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 (one record per vantage_point in the required set {windows_local, mobile_cellular, other_wifi, vpn_or_external_tester}).
- B14_2-05 classifies the upload-with-GT secondary observation per the section 2 deterministic rule (linked_to_gate / independent_defer / re_smoke_evidence_pending).
- B14_2-06 emits the B14.2 phase-gate report and the RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE recovery-packet record. The carried marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE becomes eligible for clearance only at the subsequent orchestrator PHASE_APPROVE recording on the gate-restored branch following the recovery-packet PASS.
