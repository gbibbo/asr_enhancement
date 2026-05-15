# B14_1-07 B-route and B14.0 Compatibility Under Public Exposure

generated_at_utc: 2026-05-15T03:28:30.369219+00:00
validator: validate_b14_1_broute_compatibility_under_public_exposure
mode: live
schema_reference: docs/plans/b14_1/state_packet_schemas.yaml
agent_plan_section_reference: docs/plans/b14_1/agent_plan.md section 10 row B14_1-07
orchestrator_plan_section_reference: docs/plans/b14_1/orchestrator_plan.md section 3 (FC-BROUTE-FROZEN, FC-B14-0-GATE-PRESERVED) and section 8 (AUD-BROUTE-FROZEN)
public_exposure_flag: PUBLIC_DEMO_EXPOSURE_true

## Frozen-Fingerprint Anchors

- anchor_commit: 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8
- libs/asr/router_runtime.py anchor_sha256: dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- libs/asr/router_runtime.py head_sha256: dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- services/frontend/app/demo/types.ts RouterFields-shape anchor_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c
- services/frontend/app/demo/types.ts RouterFields-shape head_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c

## Committed-Report Re-emission Inventory

| Task | Report | SHA-256 | Sentinel |
|---|---|---|---|
| BR-02 | reports/rp5/broute_health_contract.md | dda73472bad08a523a3e0503b17cbad728159906659efae1f5c1e510f084c33c | OK_BROUTE_HEALTH_PUBLIC_PAYLOAD |
| BR-02 | reports/rp5/broute_public_security_invariants.md | db05731bae3796b3dd2eb3fc30be51bb6ed12bad1c59e8a39d8b305da96bfce6 | OK_PUBLIC_SECURITY_INVARIANTS |
| BR-03 | reports/rp5/broute_cache_key_contract.md | ba28bebe92679dde2e1aa574bbc241d9fd5a456310bbbe33d999baaf41672b99 | OK_BROUTE_CACHE_KEY_CONTRACT |
| BR-04 | reports/rp5/broute_frontend_backend_contract.md | b224bf406efa6ba87d184b98c7bd8b8f51dc3d0cb2bc4a4133a0563a983e9284 | OK_FRONTEND_BACKEND_CONTRACT |
| BR-05 | reports/rp5/broute_manual_smoke.md | 087116e37b5bf903c10be2d6119c765239df9d54568012e8deb122bc97abf867 | OK_BROUTE_MANUAL_SMOKE |
| BR-06 | reports/rp5/broute_router_stub_smoke.md | bc1eab4a389c4ec3703e7f9c103655856a7bfa4cb730024ff7c75a2974a12c28 | OK_BROUTE_ROUTER_STUB_SMOKE |
| BR-07 | reports/rp5/broute_future_constraints.md | 1a02aa6f255c661a0ecad6b0007af3067f4e97c5fc1070a041694736e00c21a7 | declarative_input |
| B14_0-02 | reports/rp5/b14_0_recruiter_auth_contract.md | 2a73615b5dbc4ae726f0a5f201dea687cf9ee47845e42ba90b4aa28b2b4bbb8a | OK_B14_0_RECRUITER_AUTH_CONTRACT |
| B14_0-02 | reports/rp5/b14_0_health_payload_under_auth.md | 829c76d28eae880300b5cfc8279eefd8ea10f89711e41abe38d7e7f6ffee695e | OK_B14_0_HEALTH_UNDER_AUTH |
| B14_0-03 | reports/rp5/b14_0_auth_separation_invariants.md | 6a5e1a3d9422b27691ea72f7574fe5553e0789105aac13df59706ea6e1158bf0 | OK_B14_0_AUTH_SEPARATION |
| B14_0-04 | reports/rp5/b14_0_frontend_auth_contract.md | 0491101add088c0ecc52891f2c5b7b736edef8a250a3b431d68abff9d4d01d98 | OK_B14_0_FRONTEND_AUTH |
| B14_0-05 | reports/rp5/b14_0_manual_smoke_with_auth.md | 5ed64368c790d79475d8d79a75ba76fb20509dc2bbd4d303576d48f17069cf0e | OK_B14_0_MANUAL_SMOKE_WITH_AUTH |
| B14_0-06 | reports/rp5/b14_0_no_credential_leak.md | 1f158857962a946e8e4d663cbf4e775dc2e8fac2e87183b8ba3edbe7dc4dcff4 | OK_B14_0_NO_CRED_LEAK |
| B14_0-07 | reports/rp5/b14_0_broute_compatibility_under_auth.md | d77879a8718d22c5c9c911204a5a929b6e6ae7dc0e18cea5811c201c940470f9 | OK_B14_0_BROUTE_COMPATIBILITY |

## Frozen-Fingerprint Guard + Loopback BR-02 Health Re-emission

- [PASS] FROZEN_router_runtime_sha256_matches_anchor: observed=dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc anchor=dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- [PASS] FROZEN_router_fields_shape_sha256_matches_anchor: observed=b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c anchor=b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c
- [PASS] BR02_demo_health_unauthenticated_401_canonical_realm: status=401 realm='Basic realm="asr-demo-recruiter"'
- [PASS] BR02_demo_health_authenticated_byte_exact_under_public_exposure: status=200 body=b'{"status":"ok"}' expected=b'{"status":"ok"}'

## Committed-Report Re-emission (BR-02..BR-07, B14_0-02..B14_0-07)

- [PASS] committed_report_sentinel_BR-02_reports/rp5/broute_health_contract.md: sha256=dda73472bad08a523a3e0503b17cbad728159906659efae1f5c1e510f084c33c expected_sentinel=OK_BROUTE_HEALTH_PUBLIC_PAYLOAD observed=present
- [PASS] committed_report_sentinel_BR-02_reports/rp5/broute_public_security_invariants.md: sha256=db05731bae3796b3dd2eb3fc30be51bb6ed12bad1c59e8a39d8b305da96bfce6 expected_sentinel=OK_PUBLIC_SECURITY_INVARIANTS observed=present
- [PASS] committed_report_sentinel_BR-03_reports/rp5/broute_cache_key_contract.md: sha256=ba28bebe92679dde2e1aa574bbc241d9fd5a456310bbbe33d999baaf41672b99 expected_sentinel=OK_BROUTE_CACHE_KEY_CONTRACT observed=present
- [PASS] committed_report_sentinel_BR-04_reports/rp5/broute_frontend_backend_contract.md: sha256=b224bf406efa6ba87d184b98c7bd8b8f51dc3d0cb2bc4a4133a0563a983e9284 expected_sentinel=OK_FRONTEND_BACKEND_CONTRACT observed=present
- [PASS] committed_report_sentinel_BR-05_reports/rp5/broute_manual_smoke.md: sha256=087116e37b5bf903c10be2d6119c765239df9d54568012e8deb122bc97abf867 expected_sentinel=OK_BROUTE_MANUAL_SMOKE observed=present
- [PASS] committed_report_sentinel_BR-06_reports/rp5/broute_router_stub_smoke.md: sha256=bc1eab4a389c4ec3703e7f9c103655856a7bfa4cb730024ff7c75a2974a12c28 expected_sentinel=OK_BROUTE_ROUTER_STUB_SMOKE observed=present
- [PASS] committed_report_present_BR-07_reports/rp5/broute_future_constraints.md: present sha256=1a02aa6f255c661a0ecad6b0007af3067f4e97c5fc1070a041694736e00c21a7 (declarative input; no sentinel scan)
- [PASS] committed_report_sentinel_B14_0-02_reports/rp5/b14_0_recruiter_auth_contract.md: sha256=2a73615b5dbc4ae726f0a5f201dea687cf9ee47845e42ba90b4aa28b2b4bbb8a expected_sentinel=OK_B14_0_RECRUITER_AUTH_CONTRACT observed=present
- [PASS] committed_report_sentinel_B14_0-02_reports/rp5/b14_0_health_payload_under_auth.md: sha256=829c76d28eae880300b5cfc8279eefd8ea10f89711e41abe38d7e7f6ffee695e expected_sentinel=OK_B14_0_HEALTH_UNDER_AUTH observed=present
- [PASS] committed_report_sentinel_B14_0-03_reports/rp5/b14_0_auth_separation_invariants.md: sha256=6a5e1a3d9422b27691ea72f7574fe5553e0789105aac13df59706ea6e1158bf0 expected_sentinel=OK_B14_0_AUTH_SEPARATION observed=present
- [PASS] committed_report_sentinel_B14_0-04_reports/rp5/b14_0_frontend_auth_contract.md: sha256=0491101add088c0ecc52891f2c5b7b736edef8a250a3b431d68abff9d4d01d98 expected_sentinel=OK_B14_0_FRONTEND_AUTH observed=present
- [PASS] committed_report_sentinel_B14_0-05_reports/rp5/b14_0_manual_smoke_with_auth.md: sha256=5ed64368c790d79475d8d79a75ba76fb20509dc2bbd4d303576d48f17069cf0e expected_sentinel=OK_B14_0_MANUAL_SMOKE_WITH_AUTH observed=present
- [PASS] committed_report_sentinel_B14_0-06_reports/rp5/b14_0_no_credential_leak.md: sha256=1f158857962a946e8e4d663cbf4e775dc2e8fac2e87183b8ba3edbe7dc4dcff4 expected_sentinel=OK_B14_0_NO_CRED_LEAK observed=present
- [PASS] committed_report_sentinel_B14_0-07_reports/rp5/b14_0_broute_compatibility_under_auth.md: sha256=d77879a8718d22c5c9c911204a5a929b6e6ae7dc0e18cea5811c201c940470f9 expected_sentinel=OK_B14_0_BROUTE_COMPATIBILITY observed=present

## Result

OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE
