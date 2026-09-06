# BR-03 B-route Cache-Key Contract Report

generated_at_utc: 2026-05-13T14:51:34.417173
source_file: libs/asr/router_runtime.py
checks: 8
failures: 0

## Required Cache-Key Fields

- audio_hash
- selected_backend
- asr_model_and_version
- router_kind
- router_version
- routing_profile
- allow_third_party
- degradation_version
- metrics_or_features_version

## Check Results

- [PASS] module_importable: loaded libs/asr/router_runtime.py
- [PASS] build_cache_key_present: callable
- [PASS] signature_has_all_9_fields: all 9 fields present
- [PASS] baseline_call_succeeds: non-empty str returned
- [PASS] determinism: two calls with identical kwargs returned equal strings
- [PASS] sensitivity_per_field: all 9 fields cause key change when modified
- [PASS] allow_third_party_boolean_encoding: True vs False produce distinct deterministic encodings
- [PASS] no_forbidden_content_in_baseline_key: none of the forbidden substrings present

## Result: OK_BROUTE_CACHE_KEY_CONTRACT

All 8 checks passed.

OK_BROUTE_CACHE_KEY_CONTRACT
