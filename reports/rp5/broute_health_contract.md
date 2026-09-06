# BR-02 B-route Health Public Payload Report

generated_at_utc: 2026-05-13T14:38:20.818623
transport: in-process app-module services.api.app.demo_main:app
checks: 6
failures: 0

## Check Results

- [PASS] health_returns_200: status_code=200
- [PASS] body_is_json_object: type=dict
- [PASS] body_key_set_is_status_only: keys=['status']
- [PASS] status_value_is_ok: status='ok'
- [PASS] no_forbidden_diagnostic_fields: none of the diagnostic fields present
- [PASS] no_privacy_fields: no privacy keys present

## Result: OK_BROUTE_HEALTH_PUBLIC_PAYLOAD

OK_BROUTE_HEALTH_PUBLIC_PAYLOAD
