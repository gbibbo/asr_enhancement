# B15 Multi-Network Smoke Harness

Task: B15-02
Phase: B15
Branch: feature/demo-runtime-rp5-v1

## Purpose

This is the declarative B15-02 deliverable. It records the materialized
B15 smoke harness: the validators and paired fixture generators that the
later B15 tasks use to adjudicate the multi-network public smoke test.

The harness is pure and declarative. Every validator reads a declarative
record file (markdown carrying fenced `yaml` blocks) and writes only its
`--out` report. No validator or generator performs a public network call,
starts public exposure, or invokes Funnel, Tailscale, Cloudflare, ngrok,
systemd, Docker Compose, or any runtime service.

## Harness composition

The ten new B15 smoke harness validators are materialized across two
tasks. B15-01 materialized two (`validate_b15_coverage_matrix`,
`validate_b15_no_public_url_or_hostname_literal`). B15-02 materializes the
remaining eight, listed below. Each B15-02 validator has a paired fixture
generator under `scripts/rp5/fixtures/` and a manifest plus
positive/negative fixture tree under `tests/rp5/fixtures/`.

| Validator | Consumes | Pass sentinel | Failure marker |
|---|---|---|---|
| validate_b15_multi_network_smoke | B15-05 smoke-results (`--results`) | OK_B15_MULTI_NETWORK_SMOKE_OR_BLOCKED | B15_MULTI_NETWORK_COVERAGE_GAP |
| validate_b15_smoke_result_evidence | B15-05 smoke-results (`--results`) | OK_B15_SMOKE_RESULT_EVIDENCE_TRACED | B15_SMOKE_RESULT_FABRICATED |
| validate_b15_recruiter_gate_preserved_under_public_smoke | B15-05 smoke-results (`--results`) | OK_B15_RECRUITER_GATE_PRESERVED | B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE |
| validate_b15_quota_state_accuracy | B15-05 smoke-results (`--results`) | OK_B15_QUOTA_STATE_ACCURATE | B15_QUOTA_STATE_MISREPRESENTED |
| validate_b15_upload_limit_enforced | B15-05 smoke-results (`--results`) | OK_B15_UPLOAD_LIMIT_ENFORCED | B15_UPLOAD_LIMIT_REGRESSION |
| validate_b15_mobile_layout | B15-05 smoke-results (`--results`) | OK_B15_MOBILE_LAYOUT_OK | B15_MOBILE_LAYOUT_REGRESSION |
| validate_b15_cached_example_integrity | B15-05 smoke-results (`--results`) | OK_B15_CACHED_EXAMPLE_OK | B15_CACHED_EXAMPLE_REGRESSION |
| validate_b15_public_exposure_smoke_claim | B15-06 smoke-adjudication (`--adjudication`) | OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED | B15_EPHEMERAL_URL_SUCCESS_CLAIM |

## Record shapes consumed

- Validators 1–7 read `multi_network_smoke_result_record` blocks (one per
  network vantage point) per `docs/plans/b15/state_packet_schemas.yaml`.
- `validate_b15_public_exposure_smoke_claim` reads a
  `public_exposure_smoke_claim_record` and, when the claim status is
  `FAILED_PENDING_PHASE_RETURN`, a `b15_decision_rule_routing_record`.

At B15-02 the live B15-05/B15-06 record instances do not yet exist; each
validator is exercised only against the synthetic positive and negative
fixtures emitted by its paired generator.

## Fixture generators

Each generator runs as
`generate_fixture_validate_b15_<name>.py --kind positive_and_negative
--manifest tests/rp5/fixtures/generate_fixture_validate_b15_<name>_manifest.json`.
It writes a positive fixture and two negative fixtures, runs the paired
validator in-process against each, asserts the positive fixture passes and
each negative fixture is flagged with the owning marker, and emits its
`OK_FIXTURE_VALIDATE_B15_*` sentinel:

- OK_FIXTURE_VALIDATE_B15_MULTI_NETWORK_SMOKE
- OK_FIXTURE_VALIDATE_B15_SMOKE_RESULT_EVIDENCE
- OK_FIXTURE_VALIDATE_B15_RECRUITER_GATE_PRESERVED
- OK_FIXTURE_VALIDATE_B15_QUOTA_STATE_ACCURACY
- OK_FIXTURE_VALIDATE_B15_UPLOAD_LIMIT_ENFORCED
- OK_FIXTURE_VALIDATE_B15_MOBILE_LAYOUT
- OK_FIXTURE_VALIDATE_B15_CACHED_EXAMPLE_INTEGRITY
- OK_FIXTURE_VALIDATE_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM

## Notes

- No public smoke result, human evidence, HAR evidence, public URL,
  public hostname, provider quota state, or mobile test evidence is
  fabricated by this harness. The harness only validates the shape and
  rules of declarative records supplied later by operator evidence.
- `validate_b15_coverage_matrix` and `validate_b15_no_public_url_or_hostname_literal`
  were materialized in B15-01 and are reused, not redefined, by B15-02.
- No public URL, public hostname, Tailscale auth-key, Cloudflare token,
  recruiter password, or admin password is recorded in this deliverable.
