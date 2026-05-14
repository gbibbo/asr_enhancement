# B14_0-05 Manual End-to-End Smoke Under Recruiter Auth

generated_at_utc: 2026-05-14T04:59:02.151812+00:00
validator: validate_b14_0_e2e_manual_smoke_with_auth
schema_reference: docs/plans/b14_0/state_packet_schemas.yaml
agent_plan_section_reference: docs/plans/b14_0/agent_plan.md sections 2 and 10

## INV-E2E-001 unauthenticated probes

- [PASS] INV-E2E-001_unauth_GET_/demo/health: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-001_unauth_GET_/demo/examples: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-001_unauth_POST_/demo/run-cached: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-001_unauth_POST_/demo/jobs: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-001_unauth_GET_/demo/jobs/probe-no-such-job: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-001_unauth_GET_/demo/providers/assemblyai/status: status=401 realm_header_ok body_len=0

## INV-E2E-002..004 wrong-credentials probes

- [PASS] INV-E2E-002_wrong_user_only: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-003_wrong_pass_only: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-004_both_wrong: status=401 realm_header_ok body_len=0

## INV-E2E-005..006 authenticated probes (positive + byte-exact health)

- [PASS] INV-E2E-005_authenticated_GET_/demo/health: status=200 expected_in=[200]
- [PASS] INV-E2E-006_authenticated_health_byte_exact: status=200 body=b'{"status":"ok"}' (expected b'{"status":"ok"}')
- [PASS] INV-E2E-005_authenticated_GET_/demo/examples: status=200 expected_in=[200]
- [PASS] INV-E2E-005_authenticated_POST_/demo/run-cached: status=404 expected_in=[404]
- [PASS] INV-E2E-005_authenticated_POST_/demo/jobs: status=202 expected_in=[202, 503]
- [PASS] INV-E2E-005_authenticated_GET_/demo/jobs/probe-no-such-job: status=404 expected_in=[404]
- [PASS] INV-E2E-005_authenticated_GET_/demo/providers/assemblyai/status: status=200 expected_in=[200]

## INV-E2E-007 admin cross-realm rejection

- [PASS] INV-E2E-007_admin_creds_rejected_GET_/demo/health: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-007_admin_creds_rejected_GET_/demo/examples: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-007_admin_creds_rejected_POST_/demo/run-cached: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-007_admin_creds_rejected_POST_/demo/jobs: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-007_admin_creds_rejected_GET_/demo/jobs/probe-no-such-job: status=401 realm_header_ok body_len=0
- [PASS] INV-E2E-007_admin_creds_rejected_GET_/demo/providers/assemblyai/status: status=401 realm_header_ok body_len=0

## INV-E2E-008 uvicorn log credential-leak scan

- [PASS] INV-E2E-008_uvicorn_log_no_credential_leak: scanned /tmp/b14_0_05_uvicorn.log (13103 bytes); issues=[]

## Result

OK_B14_0_MANUAL_SMOKE_WITH_AUTH
