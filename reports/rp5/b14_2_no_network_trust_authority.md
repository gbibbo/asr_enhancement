# B14.2 No-Network-Trust-Authority Invariants

generated_at_utc: 2026-05-24T00:17:39.738330
mode: live
base_url: http://127.0.0.1:18001
recruiter_realm: asr-demo-recruiter
checks: 4
failures: 0

## Surrogate Headers Exercised

- CF-Connecting-IP
- Tailscale-User-Login
- Tailscale-User-Name
- Tailscale-User-Profile-Pic
- X-Forwarded-For
- X-Forwarded-Host
- X-Forwarded-Proto
- X-Real-IP

## Probe Routes

- GET /demo/health
- GET /demo/examples
- POST /demo/upload
- GET /demo/jobs/b14_2_fixture_job/result

## Invariant Results

- [PASS] every_required_surrogate_header_exercised: all 8 surrogate headers exercised
- [PASS] surrogate_header_alone_does_not_satisfy_recruiter_gate: every surrogate-header-only probe returned 401
- [PASS] every_surrogate_header_401_carries_canonical_recruiter_www_authenticate: every surrogate-header 401 carried WWW-Authenticate=='Basic realm="asr-demo-recruiter"'
- [PASS] every_surrogate_header_401_body_is_empty: every surrogate-header 401 carried an empty body

## Sentinel

OK_B14_2_NO_NETWORK_TRUST_AUTHORITY
