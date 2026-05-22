# B15 Coverage Matrix Fixture

```yaml
multi_network_smoke_coverage_record:
  coverage_id: B15-COVERAGE-MATRIX-FIXTURE
  vantage_points:
    - windows_local
    - mobile_cellular
    - other_wifi
    - vpn_or_external_tester
  coverage_items:
    - five_curated_examples
    - five_degradations
    - whisper_provider
    - assemblyai_provider
    - upload_without_manual_ground_truth
    - upload_with_manual_ground_truth
    - upload_limit_enforced
    - provider_quota_state
    - mobile_layout
  planned_status_per_item:
    five_curated_examples: PENDING_OPERATOR_EVIDENCE
    five_degradations: PENDING_OPERATOR_EVIDENCE
    whisper_provider: EXPLICIT_NA_PROVIDER_DISABLED
    assemblyai_provider: PENDING_OPERATOR_EVIDENCE
    upload_without_manual_ground_truth: PENDING_OPERATOR_EVIDENCE
    upload_with_manual_ground_truth: PENDING_OPERATOR_EVIDENCE
    upload_limit_enforced: PENDING_OPERATOR_EVIDENCE
    provider_quota_state: PENDING_OPERATOR_EVIDENCE
    mobile_layout: PENDING_OPERATOR_EVIDENCE
  blocker_if_unsupplied: HAR-B15-MULTI-NETWORK-SMOKE-001
  validator: validate_b15_coverage_matrix
  marker: B15_MULTI_NETWORK_COVERAGE_GAP
```
