# B15 Multi-Network Smoke Results

Task: B15-05
Phase: B15
Branch: feature/demo-runtime-rp5-v1
Record type: multi_network_smoke_result_record
(schema: docs/plans/b15/state_packet_schemas.yaml)

## Purpose

This is the declarative B15-05 deliverable. It carries one
`multi_network_smoke_result_record` per required vantage point, faithfully
transcribed from the operator-supplied human_action_result resolving
`HAR-B15-MULTI-NETWORK-SMOKE-001` (recorded in
`docs/progress/rp5_progress.yaml` > `human_action_requests.
HAR-B15-MULTI-NETWORK-SMOKE-001.supplied_values`). The records preserve
every observed outcome verbatim. No `FAIL` is softened. No
`unauthenticated_access_observed` is converted to `authenticated_access_only`.
No `not_applicable` is converted to `no_horizontal_scroll` on non-mobile
vantage points. No public URL, hostname, auth-key, token, password, or IP
address is recorded.

The aggregate operator `evidence_reference` is
`operator_multi_network_smoke_2026-05-22_no_literals`. Per-vantage-point
evidence_reference strings are the non-secret opaque tags supplied by the
operator.

## Vantage point: windows_local

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-WINDOWS-LOCAL-001
  vantage_point: windows_local
  coverage_item_outcomes:
    five_curated_examples: PASS
    five_degradations: PASS
    whisper_provider: PASS
    assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
    upload_without_manual_ground_truth: PASS
    upload_with_manual_ground_truth: FAIL
    upload_limit_enforced: PASS
    provider_quota_state: AssemblyAI disabled
    mobile_layout: NOT_APPLICABLE
  recruiter_gate_observed_status: unauthenticated_access_observed
  quota_state_observed: AssemblyAI disabled
  upload_limit_observed: enforced
  mobile_layout_observed: not_applicable
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: operator_smoke_windows_local_via_mobile_hotspot_2026-05-22_no_literals
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_multi_network_smoke
  marker: B15_MULTI_NETWORK_COVERAGE_GAP
```

## Vantage point: mobile_cellular

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-MOBILE-CELLULAR-001
  vantage_point: mobile_cellular
  coverage_item_outcomes:
    five_curated_examples: PASS
    five_degradations: PASS
    whisper_provider: PASS
    assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
    upload_without_manual_ground_truth: PASS
    upload_with_manual_ground_truth: FAIL
    upload_limit_enforced: PASS
    provider_quota_state: AssemblyAI disabled
    mobile_layout: PASS
  recruiter_gate_observed_status: unauthenticated_access_observed
  quota_state_observed: AssemblyAI disabled
  upload_limit_observed: enforced
  mobile_layout_observed: no_horizontal_scroll
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: operator_smoke_mobile_cellular_2026-05-22_no_literals
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_multi_network_smoke
  marker: B15_MULTI_NETWORK_COVERAGE_GAP
```

## Vantage point: other_wifi

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-OTHER-WIFI-001
  vantage_point: other_wifi
  coverage_item_outcomes:
    five_curated_examples: PASS
    five_degradations: PASS
    whisper_provider: PASS
    assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
    upload_without_manual_ground_truth: PASS
    upload_with_manual_ground_truth: FAIL
    upload_limit_enforced: PASS
    provider_quota_state: AssemblyAI disabled
    mobile_layout: NOT_APPLICABLE
  recruiter_gate_observed_status: unauthenticated_access_observed
  quota_state_observed: AssemblyAI disabled
  upload_limit_observed: enforced
  mobile_layout_observed: not_applicable
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: operator_smoke_other_wifi_via_second_mobile_hotspot_2026-05-22_no_literals
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_multi_network_smoke
  marker: B15_MULTI_NETWORK_COVERAGE_GAP
```

## Vantage point: vpn_or_external_tester

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-VPN-OR-EXTERNAL-TESTER-001
  vantage_point: vpn_or_external_tester
  coverage_item_outcomes:
    five_curated_examples: PASS
    five_degradations: PASS
    whisper_provider: PASS
    assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED
    upload_without_manual_ground_truth: PASS
    upload_with_manual_ground_truth: FAIL
    upload_limit_enforced: PASS
    provider_quota_state: AssemblyAI disabled
    mobile_layout: NOT_APPLICABLE
  recruiter_gate_observed_status: unauthenticated_access_observed
  quota_state_observed: AssemblyAI disabled
  upload_limit_observed: enforced
  mobile_layout_observed: not_applicable
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: operator_smoke_vpn_or_external_tester_2026-05-22_no_literals
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_multi_network_smoke
  marker: B15_MULTI_NETWORK_COVERAGE_GAP
```

## Notes

- All four records carry a non-null operator-supplied `evidence_reference` and
  cite `HAR-B15-MULTI-NETWORK-SMOKE-001`.
- The `recruiter_gate_observed_status: unauthenticated_access_observed`
  value on all four vantage points is an honest upstream observation. It is
  expected to fire `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` at
  validation time. The marker is carried forward as an
  `observed_regression_marker` at B15-05 closure per the active rail
  (`PASS_WITH_OBSERVED_REGRESSION` / `CLOSE_TASK_WITH_OBSERVED_REGRESSIONS`)
  and routed at B15-06 adjudication per the legacy decision rule
  (`RETURN_TO_B14`).
- `upload_with_manual_ground_truth: FAIL` on all four vantage points is
  preserved verbatim as a coverage-item outcome. No B15-05 validator owns a
  dedicated marker for this single item; the value propagates to B15-06's
  `public_exposure_smoke_claim_record.all_coverage_items_passed: false`
  predicate, which forecloses `SUCCESS_WITH_STABLE_NAMED_EXPOSURE` and
  forces `claim_status: FAILED_PENDING_PHASE_RETURN` at B15-06.
- `mobile_layout_observed: not_applicable` on the three non-mobile vantage
  points is legal under the repaired schema rule (`not_applicable` is legal
  only when `vantage_point` is one of `{windows_local, other_wifi,
  vpn_or_external_tester}`). The mobile_cellular record carries
  `no_horizontal_scroll` as observed.
- `assemblyai_provider: EXPLICIT_NA_PROVIDER_DISABLED` is legal only on the
  `assemblyai_provider` coverage item; the eight other items carry their
  own legal values.
- No literal public URL, public hostname, Tailscale auth-key, Cloudflare
  token, recruiter password, admin password, or IP address is recorded in
  this deliverable.
- This record does not author a `public_exposure_smoke_claim_record` or a
  `b15_decision_rule_routing_record`; those are B15-06 deliverables.
- No `SUCCESS_WITH_STABLE_NAMED_EXPOSURE` claim is asserted.
