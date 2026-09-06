# B14_1-02 Application-Layer Gate Invariants

generated_at_utc: 2026-05-14T19:52:34.634460+00:00
base_url: http://127.0.0.1:8001
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD
protected_routes_probed: 6

## application_layer_gate_invariant_record

```yaml
invariant_id: ALGI-B14_1-02
protected_route_glob: /demo/*
required_status_when_unauthenticated: 401
required_www_authenticate_value: 'Basic realm="asr-demo-recruiter"'
required_authenticated_health_payload: '{"status":"ok"}'
forbidden_bypass_paths: []
validator: validate_b14_1_application_layer_gate_invariants
marker: B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED
```

## Checks

- [PASS] unauth_GET_/demo/health: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_GET_/demo/examples: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_POST_/demo/run-cached: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_POST_/demo/jobs: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_GET_/demo/jobs/probe-no-such-job: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_GET_/demo/providers/assemblyai/status: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] wrong_creds_health_401: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] authenticated_health_byte_exact: status=200 body_matches_canonical=True

## Result

All checks passed.

OK_B14_1_APPLICATION_LAYER_GATE
