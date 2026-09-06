# B14_0-07 B-route Compatibility Under Recruiter Auth

generated_at_utc: 2026-05-14T05:24:57.729839+00:00
validator: validate_b14_0_broute_compatibility_under_auth
schema_reference: docs/plans/b14_0/state_packet_schemas.yaml
agent_plan_section_reference: docs/plans/b14_0/agent_plan.md section 10 row B14_0-07
orchestrator_plan_section_reference: docs/plans/b14_0/orchestrator_plan.md section 3 (FC-BROUTE-FROZEN) and section 8 (AUD-BROUTE-FROZEN)

## Frozen-Schema Fingerprints

- libs/asr/router_runtime.py observed_sha256: dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- libs/asr/router_runtime.py expected_sha256: dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- services/frontend/app/demo/types.ts RouterFields observed_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c
- services/frontend/app/demo/types.ts RouterFields expected_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c

## Re-emitted B-route Sentinels

- BR02_health: OK_BROUTE_HEALTH_PUBLIC_PAYLOAD
- BR02_public_security: OK_PUBLIC_SECURITY_INVARIANTS
- BR03: OK_BROUTE_CACHE_KEY_CONTRACT
- BR04: OK_FRONTEND_BACKEND_CONTRACT
- BR05: OK_BROUTE_MANUAL_SMOKE
- BR06: OK_BROUTE_ROUTER_STUB_SMOKE
- BR07: OK_FUTURE_CONSTRAINTS

## Frozen-Schema Guard

- [PASS] FROZEN_router_runtime_sha256_matches_baseline: observed=dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc expected=dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- [PASS] FROZEN_frontend_types_router_shape_sha256_matches_baseline: observed=b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c expected=b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c

## BR-02 health_public_payload re-emission (inlined under auth)

- [PASS] BR02_health_unauthenticated_401_challenge: status=401 realm='Basic realm="asr-demo-recruiter"' body_len=0
- [PASS] BR02_health_authenticated_byte_exact: status=200 body=b'{"status":"ok"}' expected=b'{"status":"ok"}'
- [PASS] BR02_health_authenticated_body_no_credential_or_router_leak: cred_hits=[] router_hits=[]

## BR-02 public_security_invariants re-emission (inlined under auth)

- [PASS] BR02_admin_health_no_creds_401: status=401
- [PASS] BR02_admin_health_www_authenticate_basic_distinct_realm: www_authenticate='Basic'
- [PASS] BR02_admin_health_correct_admin_creds_200: status=200
- [PASS] BR02_admin_stats_no_creds_401: status=401
- [PASS] BR02_authenticated_demo_health_no_privacy_leak: status=200 router_hits=[] cred_hits=[]
- [PASS] BR02_authenticated_providers_status_no_privacy_leak: status=200 router_hits=[] cred_hits=[]

## BR-03 cache_key_contract re-emission (subprocess)

- [PASS] BR03_cache_key_contract_via_subprocess: rc=0 observed_sentinel='OK_BROUTE_CACHE_KEY_CONTRACT' expected='OK_BROUTE_CACHE_KEY_CONTRACT' stderr='/home/gbibbo/code/asr_enhancement/scripts/rp5/validate_broute_cache_key_contract.py:178: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use' report_sha256=b3a67feb9008475aa98a70a15f83906c7f523478e54b039eeba34aefe9890ee4

## BR-04 frontend_backend_contract re-emission (subprocess)

- [PASS] BR04_frontend_backend_contract_via_subprocess: rc=0 observed_sentinel='OK_FRONTEND_BACKEND_CONTRACT' expected='OK_FRONTEND_BACKEND_CONTRACT' stderr='/home/gbibbo/code/asr_enhancement/scripts/rp5/validate_frontend_backend_contract.py:169: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use' report_sha256=eca516075e58a295f4aec0e4219b53ac8c0d94f32da668460736296735c80e25

## BR-05 manual_smoke re-emission (inlined under auth)

- [PASS] BR05_manual_smoke_authenticated_GET_/demo/health: status=200 expected_in=[200]
- [PASS] BR05_manual_smoke_authenticated_GET_/demo/examples: status=200 expected_in=[200]
- [PASS] BR05_manual_smoke_authenticated_POST_/demo/run-cached: status=404 expected_in=[404]
- [PASS] BR05_manual_smoke_authenticated_POST_/demo/jobs: status=202 expected_in=[202, 503]
- [PASS] BR05_manual_smoke_authenticated_GET_/demo/jobs/probe-no-such-job: status=404 expected_in=[404]
- [PASS] BR05_manual_smoke_authenticated_GET_/demo/providers/assemblyai/status: status=200 expected_in=[200]

## BR-06 router_stub_smoke re-emission (inlined TestClient under auth)

- [PASS] BR06_testclient_health_byte_exact_under_auth: status=200 body=b'{"status":"ok"}'
- [PASS] BR06_testclient_examples_shape_under_auth: status=200 keys=['examples', 'note', 'total'] router_hits=[]
- [PASS] BR06_testclient_providers_status_shape_under_auth: status=200 payload_top_keys=['assemblyai'] router_hits=[]
- [PASS] BR06_testclient_health_unauth_401_canonical_realm: status=401 realm='Basic realm="asr-demo-recruiter"'

## BR-07 future_constraints re-emission (subprocess)

- [PASS] BR07_future_constraints_via_subprocess: rc=0 observed_sentinel='OK_FUTURE_CONSTRAINTS' expected='OK_FUTURE_CONSTRAINTS' stderr='/home/gbibbo/code/asr_enhancement/scripts/rp5/validate_future_constraints.py:182: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezo' report_sha256=7c5ce64f59cab0fb2d5b7c35d2bc905d111659f5f284bf1da52e3c09b9e63e3d

## uvicorn log credential-leak scan

- [PASS] uvicorn_log_no_credential_leak: scanned /tmp/b14_0_07_uvicorn.log (4110 bytes); issues=[]

## Result

OK_B14_0_BROUTE_COMPATIBILITY
