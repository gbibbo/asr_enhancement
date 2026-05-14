# B14_0-06 No-Credential-Leak Invariants

generated_at_utc: 2026-05-14T05:11:27.191237+00:00
validator: validate_b14_0_no_credential_leak
schema_reference: docs/plans/b14_0/state_packet_schemas.yaml
agent_plan_section_reference: docs/plans/b14_0/agent_plan.md sections 2 and 12
orchestrator_plan_section_reference: docs/plans/b14_0/orchestrator_plan.md section 7

## INV-CL-001..004 unauthenticated probes (body + headers + router substrings)

- [PASS] INV-CL-001..004_unauth_body_no_credentials_GET_/demo/health: status=401 body_len=0 cred_hits=[]
- [PASS] INV-CL-008_unauth_body_no_router_substrings_GET_/demo/health: status=401 router_hits=[]
- [PASS] INV-CL-006_unauth_headers_no_credentials_GET_/demo/health: header_hits=[]
- [PASS] INV-CL-001..004_unauth_body_no_credentials_GET_/demo/examples: status=401 body_len=0 cred_hits=[]
- [PASS] INV-CL-008_unauth_body_no_router_substrings_GET_/demo/examples: status=401 router_hits=[]
- [PASS] INV-CL-006_unauth_headers_no_credentials_GET_/demo/examples: header_hits=[]
- [PASS] INV-CL-001..004_unauth_body_no_credentials_POST_/demo/run-cached: status=401 body_len=0 cred_hits=[]
- [PASS] INV-CL-008_unauth_body_no_router_substrings_POST_/demo/run-cached: status=401 router_hits=[]
- [PASS] INV-CL-006_unauth_headers_no_credentials_POST_/demo/run-cached: header_hits=[]
- [PASS] INV-CL-001..004_unauth_body_no_credentials_POST_/demo/jobs: status=401 body_len=0 cred_hits=[]
- [PASS] INV-CL-008_unauth_body_no_router_substrings_POST_/demo/jobs: status=401 router_hits=[]
- [PASS] INV-CL-006_unauth_headers_no_credentials_POST_/demo/jobs: header_hits=[]
- [PASS] INV-CL-001..004_unauth_body_no_credentials_GET_/demo/jobs/probe-no-such-job: status=401 body_len=0 cred_hits=[]
- [PASS] INV-CL-008_unauth_body_no_router_substrings_GET_/demo/jobs/probe-no-such-job: status=401 router_hits=[]
- [PASS] INV-CL-006_unauth_headers_no_credentials_GET_/demo/jobs/probe-no-such-job: header_hits=[]
- [PASS] INV-CL-001..004_unauth_body_no_credentials_GET_/demo/providers/assemblyai/status: status=401 body_len=0 cred_hits=[]
- [PASS] INV-CL-008_unauth_body_no_router_substrings_GET_/demo/providers/assemblyai/status: status=401 router_hits=[]
- [PASS] INV-CL-006_unauth_headers_no_credentials_GET_/demo/providers/assemblyai/status: header_hits=[]

## INV-CL-005..006 wrong-credentials echo probe

- [PASS] INV-CL-005_wrong_auth_body_no_echo: status=401 body_len=0 body_echoes_auth=False cred_hits=[]
- [PASS] INV-CL-006_wrong_auth_headers_no_echo: header_hits=[]

## INV-CL-007 + INV-CL-010 error-path probes

- [PASS] INV-CL-007_run_cached_empty_body_no_credential_echo: status=422 body_len=178 cred_hits=[]
- [PASS] INV-CL-010_run_cached_malformed_pydantic_422_no_credential_echo: status=422 body_len=192 cred_hits=[]
- [PASS] INV-CL-007_jobs_empty_body_no_credential_echo: status=202 body_len=67 cred_hits=[]

## INV-CL-009 uvicorn log credential-leak scan

- [PASS] INV-CL-009_uvicorn_log_no_credential_leak: scanned /tmp/b14_0_06_uvicorn.log (3286 bytes); issues=[]

## Result

OK_B14_0_NO_CRED_LEAK
