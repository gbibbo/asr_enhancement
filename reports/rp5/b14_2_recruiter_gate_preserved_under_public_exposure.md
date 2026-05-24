# B14.2 Recruiter Gate Preserved Under Public Exposure

generated_at_utc: 2026-05-24T00:50:35.222728+00:00
mode: live
base_url: http://127.0.0.1:18001
recruiter_realm: asr-demo-recruiter
public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true
checks: 5
failures: 0

## Routes Probed

- GET /demo/health
- GET /demo/examples
- GET /demo/examples/b14_2_fixture/audio/clean
- GET /demo/examples/b14_2_fixture/audio/degraded/b14_2_fixture_degradation
- POST /demo/jobs
- POST /demo/run-cached
- POST /demo/upload
- GET /demo/providers/assemblyai/status
- GET /demo/jobs/b14_2_fixture_job
- GET /demo/jobs/b14_2_fixture_job/result

## Invariant Results

- [PASS] every_committed_demo_route_observed: all 10 committed /demo/* routes present
- [PASS] every_demo_route_returns_401_to_unauthenticated_request: every /demo/* unauthenticated probe returned 401
- [PASS] every_demo_401_carries_canonical_recruiter_www_authenticate: every 401 carried WWW-Authenticate=='Basic realm="asr-demo-recruiter"'
- [PASS] every_demo_401_body_is_empty: every 401 carried an empty body
- [PASS] credentialed_requests_reach_route_handler_non_401: every credentialed probe returned non-401 (auth boundary passed)

## Sentinel

OK_B14_2_RECRUITER_GATE_PRESERVED
