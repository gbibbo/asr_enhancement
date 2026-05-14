# B14_0-02 Health Payload Preserved Under Auth

generated_at_utc: 2026-05-14T03:15:05.491475+00:00
base_url: http://127.0.0.1:8001
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD
protected_routes_probed: 6
check_count: 11

## Checks

- [PASS] unauth_GET_/demo/health: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0 leaks=[]
- [PASS] unauth_GET_/demo/examples: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0 leaks=[]
- [PASS] unauth_POST_/demo/run-cached: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0 leaks=[]
- [PASS] unauth_POST_/demo/jobs: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0 leaks=[]
- [PASS] unauth_GET_/demo/jobs/probe-no-such-job: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0 leaks=[]
- [PASS] unauth_GET_/demo/providers/assemblyai/status: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0 leaks=[]
- [PASS] wrong_creds_health_401: status=401 realm_header='Basic realm="asr-demo-recruiter"' body_len=0
- [PASS] malformed_auth_health_401: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] authenticated_health_byte_exact: status=200 body=b'{"status":"ok"}' (expected b'{"status":"ok"}')
- [PASS] env_unset_dependency_raises: RecruiterAuthChallenge raised as expected with env unset
- [PASS] uvicorn_log_no_credential_leak: scanned /tmp/b14_0_02_uvicorn.log (6283 bytes); issues=[]

## Result

All checks passed.

OK_B14_0_HEALTH_UNDER_AUTH
