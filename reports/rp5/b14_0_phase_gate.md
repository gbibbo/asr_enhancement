# B14.0 Phase Gate Report

phase_gate_report shape per `docs/plans/b14_0/state_packet_schemas.yaml`
`phase_gate_report.section_order = [STATE SNAPSHOT, PHASE, GATE PREDICATES,
VALIDATION RESULTS, CLAIM STATUS, FUTURE CONSTRAINTS, NEXT EXPECTED PHASE,
BLOCKERS]`. Authority for the gate predicates lives in
`docs/plans/b14_0/orchestrator_plan.md` section 3. This report is the
B14_0-08 deliverable; it does not record the orchestrator's phase decision,
which is a separate ORCHESTRATOR_DECISION packet.

## STATE SNAPSHOT

- repo_root: /home/gbibbo/code/asr_enhancement
- branch: feature/demo-runtime-rp5-v1
- parent_head_commit_at_report_authoring: 7c44afd9724b91a6f4ba181679718575b1f1792e
- working_tree_status_at_authoring: clean except the two B14_0-08 deliverables being authored
- current_phase: B14.0
- current_task: B14_0-08
- last_completed_task: B14_0-07
- last_completed_task_commit: 5a9b48402c208b9ba7bf895a1bbd723968897e78
- active_markers: none
- tracker_file: docs/progress/rp5_progress.yaml (untouched by this task)
- expected_next_task_per_tracker: B14_0-08
- requested_task_matches_tracker: true
- har_pending: none (HAR-B14_0-RECRUITER-CREDS-001 resolved at commit ca4730b8d3285d5f6abd1f25425f00fbce33e5f1)

## PHASE

- phase: B14.0
- phase_purpose: gate every public /demo/* route behind recruiter HTTPBasic, preserve the BR-02 health invariant and BR-05 manual_mode_no_router_fields invariant, without enabling any public-network exposure
- predecessor_phase: B-route (APPROVED at accepted_phase_gate_report_commit 4a4f8e4b20ff3ff5f19647e7ec1f723f6492df25)
- successor_phase: B14.1_PENDING_ORCHESTRATOR_INSTRUCTION

## GATE PREDICATES

Per `docs/plans/b14_0/orchestrator_plan.md` section 3 `phase_gate_pass_iff`:

| Predicate | Status | Evidence |
|---|---|---|
| B14_0-00 through B14_0-08 are PASS | PASS | tracker records B14_0-00..B14_0-07 PASS; B14_0-08 is this report and its companion future-constraints file |
| all final-verification sentinels emitted (agent_plan section 7) | PASS | see VALIDATION RESULTS below |
| BR-01 through BR-08 statuses remain PASS in tracker (no B-route rollback) | PASS | tracker records BR-00..BR-08 PASS unchanged since B-route APPROVED |
| no marker in marker registry active | PASS | every FV-* validator emitted only its OK sentinel; tracker `markers: []` |
| no literal public URL committed | PASS | path-lock validator + reports content invariants; only loopback 127.0.0.1:8001 appears in evidence |
| no recruiter credential committed | PASS | credentials supplied only via host environment per HAR-B14_0-RECRUITER-CREDS-001 resolution |
| BR-02 canonical /demo/health payload preserved under authenticated path | PASS | FV-HEALTH-UNDER-AUTH sentinel OK_B14_0_HEALTH_UNDER_AUTH |
| admin HTTPBasic semantics unchanged | PASS | FV-AUTH-SEPARATION sentinel OK_B14_0_AUTH_SEPARATION confirms admin realm, route prefix, and credentials remain distinct from recruiter |

## VALIDATION RESULTS

All nine final-verification validators emitted their OK sentinel. Each
output's sha256 below is from the local-only scratch path at
`/tmp/b14_0_08_FV-*.md`; those scratch files are not committed.

| Check id | Validator | Sentinel | Output sha256 |
|---|---|---|---|
| FV-PLAN | scripts/rp5/validate_b14_0_plan_compile.py --plan-dir docs/plans/b14_0 | OK_PLAN_COMPILES | 5e04a5fb2ef232a2b0a8e1afb33264f4b9d4e5dc4b6cc5353c791984c3d51df8 |
| FV-AUTH-CONTRACT | scripts/rp5/validate_b14_0_recruiter_auth_contract.py | OK_B14_0_RECRUITER_AUTH_CONTRACT | 65faf2e04c43c7119813598f4ef1677357bde38ee157c87428adf76d702f93d3 |
| FV-AUTH-SEPARATION | scripts/rp5/validate_b14_0_auth_separation_invariants.py --base-url http://127.0.0.1:8001 --component all | OK_B14_0_AUTH_SEPARATION | c68b21d41a9cc1aa4e98de0fdf3fcd1e216bdd05a37a772528dbc8e2bc5a7b1c |
| FV-HEALTH-UNDER-AUTH | scripts/rp5/validate_b14_0_health_payload_preserved_under_auth.py --base-url http://127.0.0.1:8001 | OK_B14_0_HEALTH_UNDER_AUTH | 79cd52f9a5f8930aec84dcd18840e9d93cfcf2777da92cffca8fd519270a2c80 |
| FV-FRONTEND-AUTH | scripts/rp5/validate_b14_0_frontend_auth_contract.py --types-file services/frontend/app/demo/types.ts | OK_B14_0_FRONTEND_AUTH | 1eb70c2476f19939ac2872bde2442d4a26a6cc4b450fa244bb16bbdfd05157fd |
| FV-MANUAL-WITH-AUTH | scripts/rp5/validate_b14_0_e2e_manual_smoke_with_auth.py --base-url http://127.0.0.1:8001 | OK_B14_0_MANUAL_SMOKE_WITH_AUTH | db457b8d2dcd090c0e63717c86c638868ac3a38fe61cc87f303837f548f345ce |
| FV-NO-CRED-LEAK | scripts/rp5/validate_b14_0_no_credential_leak.py --base-url http://127.0.0.1:8001 | OK_B14_0_NO_CRED_LEAK | c7ace894ba4fd9118813ab567bd0adf5500fffc129bbec91dd5d9203d9d04056 |
| FV-BROUTE-COMPAT | scripts/rp5/validate_b14_0_broute_compatibility_under_auth.py --base-url http://127.0.0.1:8001 | OK_B14_0_BROUTE_COMPATIBILITY | 785a410240a0cfc3773b1e2f239317fee8d97010b992cbbc0ef9f67ae5634d6b |
| FV-FUTURE | scripts/rp5/validate_future_constraints.py --constraints reports/rp5/b14_0_future_constraints.md | OK_FUTURE_CONSTRAINTS | b95ad936098d7e7d5b4463280f5d6410d002588f0bd03204780305a30d7f8e21 |

Frozen-fingerprint preservation (FC-BROUTE-FROZEN):

- libs/asr/router_runtime.py observed_sha256: dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- libs/asr/router_runtime.py expected_sha256 (baseline frozen at B14_0-07): dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc
- services/frontend/app/demo/types.ts RouterFields observed_sha256: b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c (recomputed by FV-BROUTE-COMPAT)
- services/frontend/app/demo/types.ts RouterFields expected_sha256 (baseline frozen at B14_0-04 and reconfirmed at B14_0-07): b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c

Live-evidence record:

- live_base_url: http://127.0.0.1:8001 (loopback only)
- uvicorn_log_path: /tmp/b14_0_08_uvicorn.log (local-only, removed before final status)
- uvicorn_log_sha256: 4b5a011346bfa9c68a4b004af8a0265c3b76048dc2b26858f8bea1cd0c9049ce
- uvicorn_log_size_bytes: 18782
- uvicorn_log_credential_needle_hits: 0 (scanned for RECRUITER_USERNAME, RECRUITER_PASSWORD, ADMIN_STATS_USERNAME, ADMIN_STATS_PASSWORD values and the four base64-encoded Basic-auth username:password combinations; zero hits across all eight needles)
- port_8001_released_after_smoke: true (deterministic rule: connect_ex returning a non-zero rc on re-check after uvicorn termination)
- synthetic_credentials_persisted: false (env vars unset; local-only env file removed)
- staged_diff_guard: PASS (see PATH LOCKS section in the Execution Report; the staged-diff guard is invoked separately on the two committed report paths before commit)

## CLAIM STATUS

Per `docs/plans/b14_0/agent_plan.md` section 0 `claims`:

| Claim | Status | Backing evidence |
|---|---|---|
| recruiter_public_gate_enforced_on_all_public_demo_routes | UPHELD | FV-AUTH-CONTRACT (6 protected routes), FV-AUTH-SEPARATION (route_prefix separation), FV-MANUAL-WITH-AUTH (23/23 checks), FV-BROUTE-COMPAT (25/25 checks) |
| admin_auth_unchanged_and_strictly_separate_from_recruiter | UPHELD | FV-AUTH-SEPARATION across separation dimensions realm, username, password, route_prefix, error_path, cred_separation |
| BR-02_health_payload_preserved_under_recruiter_auth | UPHELD | FV-HEALTH-UNDER-AUTH authenticated `{"status":"ok"}` byte-exact; FV-BROUTE-COMPAT BR02_health_public_payload re-emission |
| no_credential_leak_in_logs_or_error_pages | UPHELD | FV-NO-CRED-LEAK across INV-CL-001..INV-CL-010; uvicorn_log credential-needle-hit count = 0 |
| BR-01_through_BR-08_artifacts_remain_frozen | UPHELD | tracker BR-00..BR-08 PASS unchanged; FV-BROUTE-COMPAT frozen fingerprints match; FC-BROUTE-FROZEN preservation entry recorded |
| future_constraints_preserved | UPHELD | FV-FUTURE OK_FUTURE_CONSTRAINTS; five future_constraint_preservation_record entries authored under reports/rp5/b14_0_future_constraints.md |

## FUTURE CONSTRAINTS

Recorded in `reports/rp5/b14_0_future_constraints.md` and validated by FV-FUTURE:

- FC-B14-0-PUBLIC-GATE: implemented by B14.0; preserved against future-phase rollback
- FC-B14-1-FUNNEL: loopback-only binding preserved in B14.0; no Funnel/serve/systemd artefact introduced
- FC-B15-MULTI-NETWORK: no public-network smoke coverage claimed from local B14.0 tests
- FC-HANDOFF-DATAMOVE1: router schema and cache-key schema unchanged; libs/asr/router_runtime.py unmodified
- FC-BROUTE-FROZEN: BR-01..BR-08 deliverables, the libs/asr/router_runtime.py fingerprint, and the services/frontend/app/demo/types.ts router-field shape remain frozen under recruiter auth

## NEXT EXPECTED PHASE

- next_expected_phase: B14.1_PENDING_ORCHESTRATOR_INSTRUCTION
- next_expected_phase_status: awaiting orchestrator PHASE_APPROVE for B14.0 followed by APPROVE_PLAN for the first B14.1 task
- agent_action_until_phase_decision: stop after this report is committed and pushed; do not advance the tracker; do not record PHASE_APPROVE; do not start B14.1, B15, Funnel, public exposure, systemd, or datamove1 handoff work

## BLOCKERS

- none

Active markers: none. All recovery packets in `docs/plans/b14_0/agent_plan.md` section 11 are inactive. No human action request pending. No path-lock violation. No credential leak. No future-constraint regression. No B-route rollback. The gate predicates are fully satisfied; the phase decision itself is owned by the orchestrator.
