# B15 Multi-Network Smoke Coverage Matrix

Task: B15-01
Phase: B15
Branch: feature/demo-runtime-rp5-v1
Record type: multi_network_smoke_coverage_record
(schema: docs/plans/b15/state_packet_schemas.yaml)

## Purpose

This is the declarative B15-01 deliverable. It enumerates the four network
vantage points and the nine coverage items that the B15 multi-network public
smoke test must exercise. It records only a *planned* status per coverage
item; runtime smoke outcomes are owned by the multi_network_smoke_result_record
deliverables authored at B15-05 against operator-supplied evidence.

Every coverage item carries planned-status `PENDING_OPERATOR_EVIDENCE`: no
smoke result is asserted here, and no operator evidence has been supplied yet.
Resolution of the four vantage points into observed outcomes is gated on
`HAR-B15-MULTI-NETWORK-SMOKE-001`.

## Coverage matrix (planned status)

Each cell is `PENDING_OPERATOR_EVIDENCE`: the item is planned for coverage from
that vantage point and awaits operator-supplied smoke evidence.

| Coverage item | windows_local | mobile_cellular | other_wifi | vpn_or_external_tester |
|---|---|---|---|---|
| five_curated_examples | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| five_degradations | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| whisper_provider | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| assemblyai_provider | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| upload_without_manual_ground_truth | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| upload_with_manual_ground_truth | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| upload_limit_enforced | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| provider_quota_state | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |
| mobile_layout | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE | PENDING_OPERATOR_EVIDENCE |

## Declarative record

```yaml
multi_network_smoke_coverage_record:
  coverage_id: B15-COVERAGE-MATRIX-001
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
    whisper_provider: PENDING_OPERATOR_EVIDENCE
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

## Notes

- The curated-example coverage item identifier is `five_curated_examples`, aligned with the live public demo which intentionally exposes 5 curated examples. The prior identifier `ten_curated_examples` was retired via recovery packet `RP-B15-CURATED-EXAMPLE-COUNT-SCOPE-CHANGE-B15-05`.
- No smoke evidence is fabricated. Every coverage item is `PENDING_OPERATOR_EVIDENCE`.
- `EXPLICIT_NA_PROVIDER_DISABLED` is not used here; it is schema-legal only for
  the `assemblyai_provider` coverage item, and would be recorded only if the
  AssemblyAI provider were operator-disabled for the smoke run.
- No public URL, public hostname, Tailscale auth-key, Cloudflare token,
  recruiter password, or admin password is recorded in this deliverable.
- This record does not start, request, or imply public exposure. Public
  exposure bring-up is the HAR-gated B15-04 task.
