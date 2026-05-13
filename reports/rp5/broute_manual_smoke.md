# BR-05 Manual End-to-End Smoke Report

generated_at_utc: 2026-05-13T22:03:50.466786
transport: base-url http://127.0.0.1:8002
manual_mode_default: true (no router decoration expected on public responses)
checks: 11
failures: 0

## Check Results

- [PASS] public_health_exact: status=200 body={'status': 'ok'}
- [PASS] public_examples_shape: status=200 keys=['examples', 'note', 'total']
- [PASS] public_assemblyai_state: status=200 body={'assemblyai': {'state': 'disabled', 'cap_state': 'below'}}
- [PASS] public_run_cached_unknown_example_404: status=404
- [PASS] public_create_job_202: status=202 body={'job_id': 'dc137bf6-6e3f-4b77-a988-ea718d65f5a6', 'status': 'queued'}
- [PASS] public_job_lookup_responds: status=200 keys=['created_at', 'degradation_id', 'degraded_artifact_path', 'enhanced_artifact_path', 'enhancer_version', 'error_message', 'expires_at', 'input_artifact_path', 'job_id', 'provider', 'result_json', 'status', 'updated_at']
- [PASS] public_admin_health_requires_auth: status=401 WWW-Authenticate='Basic'
- [PASS] public_admin_health_with_auth_ok: status=200 keys=['db_ok', 'mode', 'queue_depth']
- [PASS] public_admin_stats_requires_auth: status=401
- [PASS] manual_mode_no_router_fields: no router fields in public responses
- [PASS] public_no_privacy_leaks: no privacy/secret strings in /demo/health or /demo/providers/assemblyai/status (matches existing test_b12_1 precedent; /demo/examples excluded by design)

## Result: OK_BROUTE_MANUAL_SMOKE

All 11 checks passed in manual mode.

OK_BROUTE_MANUAL_SMOKE
