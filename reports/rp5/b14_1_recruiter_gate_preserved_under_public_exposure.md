# B14_1-03 Recruiter Gate Preserved Under Public Exposure

generated_at_utc: 2026-05-14T20:42:49.081826+00:00
base_url: http://127.0.0.1:8001
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD
protected_routes_probed: 6

## application_layer_gate_invariant_record

```yaml
invariant_id: RGP-B14_1-03
protected_route_glob: /demo/*
required_status_when_unauthenticated: 401
required_www_authenticate_value: 'Basic realm="asr-demo-recruiter"'
required_authenticated_health_payload: '{"status":"ok"}'
forbidden_bypass_paths: []
validator: validate_b14_1_recruiter_gate_preserved_under_public_exposure
marker: B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE
```

## Checks

- [PASS] unauth_GET_/demo/health_returns_401_with_canonical_realm: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_GET_/demo/examples_returns_401_with_canonical_realm: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_POST_/demo/run-cached_returns_401_with_canonical_realm: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_POST_/demo/jobs_returns_401_with_canonical_realm: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_GET_/demo/jobs/probe-no-such-job_returns_401_with_canonical_realm: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_GET_/demo/providers/assemblyai/status_returns_401_with_canonical_realm: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] authenticated_demo_health_returns_200: status=200
- [PASS] admin_health_with_recruiter_credentials_does_not_authorize: status=401 (must not be 200)

## Result

All checks passed.

OK_B14_1_RECRUITER_GATE_PRESERVED
