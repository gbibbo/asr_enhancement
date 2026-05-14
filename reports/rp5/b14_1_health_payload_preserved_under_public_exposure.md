# B14_1-03 BR-02 Health Payload Preserved Under Public Exposure

generated_at_utc: 2026-05-14T20:42:49.169283+00:00
base_url: http://127.0.0.1:8001
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD

## canonical_payload_record

```yaml
invariant_id: HPP-B14_1-03
route: /demo/health
required_status_when_authenticated: 200
required_authenticated_health_payload: '{"status":"ok"}'
required_authenticated_health_payload_sha256: a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288
validator: validate_b14_1_health_payload_preserved_under_public_exposure
marker: B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE
```

## Checks

- [PASS] authenticated_demo_health_status_200: status=200
- [PASS] authenticated_demo_health_body_byte_exact_canonical: observed_len=15 observed_sha256=a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288 expected_sha256=a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288

## Result

Body byte-exact equality holds.

OK_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE
