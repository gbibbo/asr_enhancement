# BR-04 Frontend/Backend Contract Report

generated_at_utc: 2026-05-13T21:40:46.416499
types_file: services/frontend/app/demo/types.ts
checks: 9
failures: 0

## Check Results

- [PASS] types_file_present: services/frontend/app/demo/types.ts
- [PASS] DemoHealthResponse_block_parseable: type body isolated
- [PASS] DemoHealthResponse_only_has_status_field: fields=['status']
- [PASS] DemoHealthResponse_status_value_is_ok: status literal is "ok"
- [PASS] DemoHealthResponse_no_forbidden_diagnostic_fields: no forbidden diagnostic fields in block
- [PASS] RouterDecisionView_fields_complete: all 12 fields present
- [PASS] AssembledResponseView_top_fields_complete: all 13 top fields present
- [PASS] LatencyMs_subfields_complete: all 3 subfields present
- [PASS] file_omits_secrets_urls_diagnostics_outside_comments: no forbidden substrings in code (comments scanned separately and ignored)

## Result: OK_FRONTEND_BACKEND_CONTRACT

All 9 checks passed.

OK_FRONTEND_BACKEND_CONTRACT
