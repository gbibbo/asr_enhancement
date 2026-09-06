# B15 Smoke Results Fixture

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-windows_local
  vantage_point: windows_local
  coverage_item_outcomes:
    five_curated_examples: COVERED
    five_degradations: COVERED
    whisper_provider: COVERED
    assemblyai_provider: COVERED
    upload_without_manual_ground_truth: COVERED
    upload_with_manual_ground_truth: COVERED
    upload_limit_enforced: COVERED
    provider_quota_state: COVERED
    mobile_layout: COVERED
  recruiter_gate_observed_status: authenticated_access_only
  quota_state_observed: AssemblyAI available
  upload_limit_observed: not_enforced
  mobile_layout_observed: no_horizontal_scroll
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: B15-OPERATOR-EVIDENCE-windows_local
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_upload_limit_enforced
  marker: B15_UPLOAD_LIMIT_REGRESSION
```

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-mobile_cellular
  vantage_point: mobile_cellular
  coverage_item_outcomes:
    five_curated_examples: COVERED
    five_degradations: COVERED
    whisper_provider: COVERED
    assemblyai_provider: COVERED
    upload_without_manual_ground_truth: COVERED
    upload_with_manual_ground_truth: COVERED
    upload_limit_enforced: COVERED
    provider_quota_state: COVERED
    mobile_layout: COVERED
  recruiter_gate_observed_status: authenticated_access_only
  quota_state_observed: AssemblyAI available
  upload_limit_observed: enforced
  mobile_layout_observed: no_horizontal_scroll
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: B15-OPERATOR-EVIDENCE-mobile_cellular
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_upload_limit_enforced
  marker: B15_UPLOAD_LIMIT_REGRESSION
```

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-other_wifi
  vantage_point: other_wifi
  coverage_item_outcomes:
    five_curated_examples: COVERED
    five_degradations: COVERED
    whisper_provider: COVERED
    assemblyai_provider: COVERED
    upload_without_manual_ground_truth: COVERED
    upload_with_manual_ground_truth: COVERED
    upload_limit_enforced: COVERED
    provider_quota_state: COVERED
    mobile_layout: COVERED
  recruiter_gate_observed_status: authenticated_access_only
  quota_state_observed: AssemblyAI available
  upload_limit_observed: enforced
  mobile_layout_observed: no_horizontal_scroll
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: B15-OPERATOR-EVIDENCE-other_wifi
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_upload_limit_enforced
  marker: B15_UPLOAD_LIMIT_REGRESSION
```

```yaml
multi_network_smoke_result_record:
  result_id: B15-SMOKE-RESULT-vpn_or_external_tester
  vantage_point: vpn_or_external_tester
  coverage_item_outcomes:
    five_curated_examples: COVERED
    five_degradations: COVERED
    whisper_provider: COVERED
    assemblyai_provider: COVERED
    upload_without_manual_ground_truth: COVERED
    upload_with_manual_ground_truth: COVERED
    upload_limit_enforced: COVERED
    provider_quota_state: COVERED
    mobile_layout: COVERED
  recruiter_gate_observed_status: authenticated_access_only
  quota_state_observed: AssemblyAI available
  upload_limit_observed: enforced
  mobile_layout_observed: no_horizontal_scroll
  cached_example_observed: all_curated_examples_resolved
  evidence_reference: B15-OPERATOR-EVIDENCE-vpn_or_external_tester
  har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_upload_limit_enforced
  marker: B15_UPLOAD_LIMIT_REGRESSION
```

