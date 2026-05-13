# BR-01 B-route Schema Contract Report

generated_at_utc: 2026-05-13T14:05:56.700647
source_file: libs/asr/router_runtime.py
checks: 10
failures: 0

## Check Results

- [PASS] module_importable: loaded libs/asr/router_runtime.py
- [PASS] RouterRuntime_present: found
- [PASS] RouterDecision_present: found
- [PASS] AssembledResponse_present: found
- [PASS] build_cache_key_present: found
- [PASS] RouterRuntime_has_route: route method present
- [PASS] RouterDecision_fields_complete: all 12 fields present
- [PASS] AssembledResponse_fields_complete: all 13 fields present
- [PASS] latency_ms_subfields: all 3 latency subfields present
- [PASS] build_cache_key_callable: callable

## Required Field Sets

RouterDecision required fields: ['selected_backend', 'router_kind', 'router_version', 'routing_profile', 'allow_third_party', 'third_party_provider', 'cost_policy', 'estimated_cost_usd', 'predicted_confidence', 'predicted_ask_repeat', 'routing_explanation', 'router_latency_ms']
AssembledResponse required fields: ['transcript_text', 'selected_backend', 'router_kind', 'router_version', 'routing_profile', 'allow_third_party', 'third_party_provider', 'estimated_cost_usd', 'cost_usd', 'backend_confidence', 'ask_repeat', 'latency_ms', 'routing_explanation']
latency_ms required subfields: ['backend', 'server', 'end_to_end']

## Result: OK_BROUTE_SCHEMA_CONTRACT

All 10 checks passed.

OK_BROUTE_SCHEMA_CONTRACT
