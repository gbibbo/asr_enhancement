# BR-04 B-route Frontend Detection Report

generated_at_utc: 2026-05-13T21:39:13.672385
demo_root_scanned: services/frontend/app/demo
br_relevant_tokens: ['DemoHealthResponse', '/api/demo/health', '/api/demo/upload', '/api/demo/results', 'selected_backend', 'router_kind', 'router_version', 'routing_profile', 'allow_third_party', 'RouterFieldsPanel', 'UploadForm', 'ResultView']
candidates_scanned: 6
eligible_files: 2
misclassified_files: 0

## Eligible Files (PL-BR-FRONTEND)

- services/frontend/app/demo/page.tsx (lock=PL-BR-FRONTEND, tokens=['DemoHealthResponse', '/api/demo/health', '/api/demo/upload'])
- services/frontend/app/demo/types.ts (lock=PL-BR-FRONTEND, tokens=['DemoHealthResponse'])

## Result: OK_BROUTE_FRONTEND_DETECTION

OK_BROUTE_FRONTEND_DETECTION
