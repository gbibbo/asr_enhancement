# B14_0-03 Admin vs Recruiter Auth Separation Invariants

generated_at_utc: 2026-05-14T04:18:28.508333+00:00
base_url: http://127.0.0.1:8001
component: all
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD
admin_username_env: ADMIN_STATS_USERNAME
admin_password_env: ADMIN_STATS_PASSWORD
check_count: 11

## Checks

- [PASS] realm: realm.demo_health_recruiter_realm: status=401 www_authenticate='Basic realm="asr-demo-recruiter"'
- [PASS] realm: realm.admin_health_distinct_realm: status=401 www_authenticate_present=True distinct_from_recruiter=True
- [PASS] username: username.admin_creds_rejected_at_demo: status=401 realm='Basic realm="asr-demo-recruiter"'
- [PASS] username: username.recruiter_creds_rejected_at_admin: status=401 realm='Basic'
- [PASS] password: password.recruiter_user_admin_pass_rejected: status=401 realm='Basic realm="asr-demo-recruiter"'
- [PASS] password: password.admin_user_recruiter_pass_rejected: status=401 realm='Basic'
- [PASS] route_prefix: route_prefix.disjoint_under_correct_prefixes: recruiter_routes_under_demo=True admin_routes_under_admin=True disjoint=True recruiter_count=6 admin_count=2
- [PASS] error_path: error_path.401_bodies_distinct: demo_body_len=0 admin_body_len=25 distinct=True
- [PASS] cred_separation: cred_separation.usernames_distinct: admin_username_equals_recruiter_username=False
- [PASS] cred_separation: cred_separation.passwords_distinct: admin_password_equals_recruiter_password=False
- [PASS] log_scan: log.no_credential_leak: scanned /tmp/b14_0_03_uvicorn.log (2872 bytes); issues=[]

## Result

All 11 checks passed.

OK_B14_0_AUTH_SEPARATION
