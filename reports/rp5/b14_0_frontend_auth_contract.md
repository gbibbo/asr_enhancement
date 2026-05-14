# B14_0-04 Frontend Recruiter-Auth UX Contract

generated_at_utc: 2026-05-14T04:36:34.527126+00:00
validator: validate_b14_0_frontend_auth_contract
schema_reference: docs/plans/b14_0/state_packet_schemas.yaml
agent_plan_section_reference: docs/plans/b14_0/agent_plan.md sections 2 and 12
types_file: services/frontend/app/demo/types.ts
frontend_demo_dir: services/frontend/app/demo
frontend_files_scanned: 6

## Frozen RouterFields Shape

- expected_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c
- observed_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c
- type_blocks_covered:
    - RouterDecisionView
    - AssembledResponseView

## Static Scan Checks

- [PASS] INV-FE-AUTH-007_router_fields_shape_frozen: observed_sha256=b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c expected_sha256=b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c
- [PASS] INV-FE-AUTH-001_no_client_side_credential_persistence: PASS (0 hits)
- [PASS] INV-FE-AUTH-002_no_custom_authorization_basic_header: PASS (0 hits)
- [PASS] INV-FE-AUTH-003_no_inpage_credential_capture_form: PASS (0 hits)
- [PASS] INV-FE-AUTH-004_no_client_side_401_interception: PASS (0 hits)
- [PASS] INV-FE-AUTH-005_no_credential_placeholder_echo: PASS (0 hits)
- [PASS] INV-FE-AUTH-006_no_banned_phrase_or_nonloopback_url: PASS (0 hits)

## Files Scanned

- services/frontend/app/demo/degradations.ts
- services/frontend/app/demo/page.tsx
- services/frontend/app/demo/scoring.ts
- services/frontend/app/demo/session.ts
- services/frontend/app/demo/types.ts
- services/frontend/app/demo/versions.ts

## Result

All 7 static-scan checks passed.

frontend_files_modified: false
types_ts_modified: false
router_fields_shape_unchanged: true

OK_B14_0_FRONTEND_AUTH
