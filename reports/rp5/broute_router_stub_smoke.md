# BR-06 Router Stub End-to-End Smoke Report

generated_at_utc: 2026-05-13T22:23:58.633292
transport: in-process app-module services.api.app.demo_main:app
router_mode: deterministic_stub (stub-v0)
checks: 18
failures: 0

## Check Results

- [PASS] stub_router_kind_constant: STUB_ROUTER_KIND='deterministic_selector' expected='deterministic_selector'
- [PASS] stub_router_version_constant: STUB_ROUTER_VERSION='stub-v0' expected='stub-v0'
- [PASS] stub_selected_backend_constant: STUB_SELECTED_BACKEND='whisper_base_ct2_int8' expected='whisper_base_ct2_int8'
- [PASS] router_decision_field_set: actual=['allow_third_party', 'cost_policy', 'estimated_cost_usd', 'predicted_ask_repeat', 'predicted_confidence', 'router_kind', 'router_latency_ms', 'router_version', 'routing_explanation', 'routing_profile', 'selected_backend', 'third_party_provider'] expected=['allow_third_party', 'cost_policy', 'estimated_cost_usd', 'predicted_ask_repeat', 'predicted_confidence', 'router_kind', 'router_latency_ms', 'router_version', 'routing_explanation', 'routing_profile', 'selected_backend', 'third_party_provider']
- [PASS] router_decision_selected_backend: selected_backend='whisper_base_ct2_int8'
- [PASS] router_decision_router_kind: router_kind='deterministic_selector'
- [PASS] router_decision_router_version: router_version='stub-v0'
- [PASS] router_decision_default_routing_profile: routing_profile='balanced'
- [PASS] router_decision_routing_explanation: routing_explanation='stub: awaiting datamove1 handoff'
- [PASS] router_decision_deterministic_two_calls: identical RouterDecision across two route() calls
- [PASS] router_decision_routing_profile_override_preserves_stub: routing_profile='latency' router_kind='deterministic_selector' router_version='stub-v0' selected_backend='whisper_base_ct2_int8'
- [PASS] assembled_response_field_set: actual=['allow_third_party', 'ask_repeat', 'backend_confidence', 'cost_usd', 'estimated_cost_usd', 'latency_ms', 'router_kind', 'router_version', 'routing_explanation', 'routing_profile', 'selected_backend', 'third_party_provider', 'transcript_text'] expected=['allow_third_party', 'ask_repeat', 'backend_confidence', 'cost_usd', 'estimated_cost_usd', 'latency_ms', 'router_kind', 'router_version', 'routing_explanation', 'routing_profile', 'selected_backend', 'third_party_provider', 'transcript_text']
- [PASS] assembled_response_latency_ms_subfields: actual=['backend', 'end_to_end', 'server'] expected=['backend', 'end_to_end', 'server']
- [PASS] assembled_response_composition_from_stub_decision: router_kind='deterministic_selector' router_version='stub-v0' selected_backend='whisper_base_ct2_int8'
- [PASS] build_cache_key_router_fields_present: key_len=120 missing=[] allow_third_party_encoded=True
- [PASS] public_health_exact_status_ok: status=200 body={'status': 'ok'}
- [PASS] public_assemblyai_state_allowed: status=200 body={'assemblyai': {'state': 'disabled', 'cap_state': 'below'}}
- [PASS] public_http_surface_no_router_fields: no router fields leaked to /demo/health or /demo/providers/assemblyai/status

## Result: OK_BROUTE_ROUTER_STUB_SMOKE

All 18 checks passed for router stub mode.

OK_BROUTE_ROUTER_STUB_SMOKE
