# B14.2 BR-02 Health Payload Preserved Under Public Exposure

generated_at_utc: 2026-05-24T00:50:35.316819+00:00
mode: live
base_url: http://127.0.0.1:18001
public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true
expected_health_body_sha256: a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288
observed_health_body_sha256: a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288
checks: 2
failures: 0

## Invariant Results

- [PASS] authenticated_demo_health_status_200: observed_status=200
- [PASS] authenticated_demo_health_body_byte_exact_canonical: observed_len=15 observed_sha256=a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288 expected_sha256=a29ee2b15c494311c52521766e44af56a3ad2248e7a8ab465e5206463c13d288

## Sentinel

OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE
