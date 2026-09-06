# BR-02 Public Security Invariants Report

generated_at_utc: 2026-05-13T14:38:31.296982
transport: in-process app-module services.api.app.demo_main:app
checks: 9
failures: 0

## Check Results

- [PASS] public_health_exact_status_ok: status=200 body={'status': 'ok'}
- [PASS] admin_health_no_creds_401: status=401
- [PASS] admin_health_www_authenticate_basic: WWW-Authenticate='Basic'
- [PASS] admin_health_bad_creds_401: status=401
- [PASS] admin_health_correct_creds_200: status=200
- [PASS] admin_health_has_diagnostic_keys: keys=['db_ok', 'mode', 'queue_depth']
- [PASS] admin_stats_no_creds_401: status=401
- [PASS] no_privacy_leaks_in_demo_health: no privacy/secret strings present
- [PASS] no_privacy_leaks_in_demo_providers_assemblyai_status: no privacy/secret strings present

## Result: OK_PUBLIC_SECURITY_INVARIANTS

OK_PUBLIC_SECURITY_INVARIANTS
