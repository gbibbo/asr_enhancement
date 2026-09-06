# B14_0-01 Recruiter Auth Contract

generated_at_utc: 2026-05-14T02:54:01.496638+00:00
validator: validate_b14_0_recruiter_auth_contract
schema_reference: docs/plans/b14_0/state_packet_schemas.yaml
agent_plan_section_reference: docs/plans/b14_0/agent_plan.md section 2

## Schema Conformance Checks

- [PASS] recruiter_auth_invariant_record_schema_conformance: PASS
- [PASS] credential_storage_policy_records_schema_conformance: PASS (2 records)
- [PASS] auth_separation_invariant_records_schema_conformance: PASS (5 records)
- [PASS] no_real_credential_value_in_records: all credential records use deferred-HAR token; no operator values present
- [PASS] authenticated_health_payload_excludes_router_field_names: authenticated /demo/health payload {"status":"ok"} carries no router-field names

## recruiter_auth_invariant_record

```yaml
invariant_id: RECRUITER-AUTH-INVARIANT-001
protected_route_glob:
  - GET /demo/health
  - GET /demo/examples
  - POST /demo/run-cached
  - POST /demo/jobs
  - GET /demo/jobs/{job_id}
  - GET /demo/providers/assemblyai/status
expected_unauthenticated_status: 401
expected_www_authenticate_value: Basic realm="asr-demo-recruiter"
expected_authenticated_health_payload: {"status":"ok"}
forbidden_response_body_substrings:
  - router_kind
  - router_version
  - routing_profile
  - selected_backend
  - allow_third_party
  - <env:Authorization-header-value>
  - <env:RECRUITER_PASSWORD-value>
  - <env:ADMIN_STATS_PASSWORD-value>
validator: validate_b14_0_recruiter_auth_contract
marker: B14_0_RECRUITER_AUTH_CONTRACT_FAILED
```

Note: items 1..5 of forbidden_response_body_substrings are literal scan needles.
Items 6..8 are placeholder tokens for runtime value categories whose actual
operator values are resolved at smoke time by the runtime validators
(validate_b14_0_no_credential_leak, validate_b14_0_auth_separation_invariants).
No operator credential value is ever inlined into this contract document.

## credential_storage_policy_records

```yaml
- policy_id: RECRUITER-CRED-STORAGE-001
  credential_name: RECRUITER_USERNAME
  source: environment_variable
  allowed_storage:
    - environment_variable
    - host_systemd_service_env
  forbidden_storage:
    - git_committed_file
    - dockerfile_literal
    - compose_file_literal
    - plan_file_literal
    - log_output
    - error_response_body
  rotation_policy: deferred_to_HAR-B14_0-RECRUITER-CREDS-001
  validator: validate_b14_0_recruiter_auth_contract
  marker: B14_0_RECRUITER_AUTH_CONTRACT_FAILED
- policy_id: RECRUITER-CRED-STORAGE-002
  credential_name: RECRUITER_PASSWORD
  source: environment_variable
  allowed_storage:
    - environment_variable
    - host_systemd_service_env
  forbidden_storage:
    - git_committed_file
    - dockerfile_literal
    - compose_file_literal
    - plan_file_literal
    - log_output
    - error_response_body
  rotation_policy: deferred_to_HAR-B14_0-RECRUITER-CREDS-001
  validator: validate_b14_0_recruiter_auth_contract
  marker: B14_0_RECRUITER_AUTH_CONTRACT_FAILED
```

rotation_policy uses the literal token 'deferred_to_HAR-B14_0-RECRUITER-CREDS-001'
because HAR-B14_0-RECRUITER-CREDS-001 is pre_declared_unresolved and blocks
B14_0-02 closure only. The operator-supplied rotation cadence will be
recorded in the HAR result block when the human action resolves; this
contract carries the deferred token in the meantime so the schema's
required rotation_policy field stays non-empty without inventing policy.

## auth_separation_invariant_records (preserved for B14_0-03)

```yaml
- invariant_id: AUTH-SEP-001
  surface_a: admin
  surface_b: recruiter
  separation_dimension: realm
  validator: validate_b14_0_auth_separation_invariants
  marker: B14_0_ADMIN_RECRUITER_CRED_CONFLATION
- invariant_id: AUTH-SEP-002
  surface_a: admin
  surface_b: recruiter
  separation_dimension: username
  validator: validate_b14_0_auth_separation_invariants
  marker: B14_0_ADMIN_RECRUITER_CRED_CONFLATION
- invariant_id: AUTH-SEP-003
  surface_a: admin
  surface_b: recruiter
  separation_dimension: password
  validator: validate_b14_0_auth_separation_invariants
  marker: B14_0_ADMIN_RECRUITER_CRED_CONFLATION
- invariant_id: AUTH-SEP-004
  surface_a: admin
  surface_b: recruiter
  separation_dimension: route_prefix
  validator: validate_b14_0_auth_separation_invariants
  marker: B14_0_ADMIN_RECRUITER_CRED_CONFLATION
- invariant_id: AUTH-SEP-005
  surface_a: admin
  surface_b: recruiter
  separation_dimension: error_path
  validator: validate_b14_0_auth_separation_invariants
  marker: B14_0_ADMIN_RECRUITER_CRED_CONFLATION
```

These records are declared in this contract for downstream consumption by
validate_b14_0_auth_separation_invariants during B14_0-03 execution.
B14_0-01 does not bind a runtime separation validator.

## Result

All 5 schema-conformance checks passed.

OK_B14_0_RECRUITER_AUTH_CONTRACT
