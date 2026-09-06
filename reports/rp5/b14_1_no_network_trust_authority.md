# B14_1-02 No Network-Trust Authority

generated_at_utc: 2026-05-14T19:52:34.739044+00:00
base_url: http://127.0.0.1:8001
spoofed_headers_tested: 7
static_files_scanned: 3

## Checks

- [PASS] unauth_trust_header_X-Forwarded-For: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_trust_header_X-Forwarded-For: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_trust_header_X-Real-IP: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_trust_header_X-Forwarded-Proto: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_trust_header_Tailscale-User-Login: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_trust_header_Tailscale-User-Name: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] unauth_trust_header_X-Tailscale-Identity: status=401 realm_header='Basic realm="asr-demo-recruiter"'
- [PASS] static_inspect_services/api/app/recruiter_auth.py: forbidden_token_hits=none
- [PASS] static_inspect_services/api/app/public_exposure.py: forbidden_token_hits=none
- [PASS] static_inspect_services/api/app/demo_main.py: forbidden_token_hits=none

## Result

All checks passed.

OK_B14_1_NO_NETWORK_TRUST_AUTHORITY
