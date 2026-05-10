# agent_plan.md

Plan state: APPROVED_FOR_EXECUTION
Project scope: RP5 B-route router-ready seam only. Future phases are preserved but not executable in this plan.
Authority: executable task order, exact commands, validators, fixture generators, marker registry, recovery packets, transition table, tracker mutation rules, path locks, and report skeleton references.

## 0. Manifest and entity registry

```yaml
project: rp5_b_route_router_ready_seam
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
starting_state:
  last_completed_task: B13.1
  current_phase: B14
  preplan_next_detailed_work: B-route
canonical_output_files:
  - orchestrator_plan.md
  - agent_plan.md
  - state_packet_schemas.yaml
phases:
  - B-route
  - B14.0_future_constraint
  - B14.1_future_constraint
  - B15_future_constraint
  - B-handoff_future_constraint
tasks:
  - BR-00
  - BR-01
  - BR-02
  - BR-03
  - BR-04
  - BR-05
  - BR-06
  - BR-07
  - BR-08
markers:
  - PLAN_CONFLICT
  - PREPLAN_THRESHOLD_GAP
  - TRACKER_MISSING
  - TRACKER_MISMATCH
  - REPORT_SCHEMA_INVALID
  - APPROVAL_PACKET_MALFORMED
  - EXECUTION_RAIL_GAP
  - PATH_LOCK_TOO_BROAD
  - VALIDATOR_MATERIALIZATION_GAP
  - RECOVERY_PACKET_GAP
  - PUBLIC_SECURITY_REGRESSION
  - ROUTER_SCHEMA_DRIFT
  - FRONTEND_BACKEND_DRIFT
  - FUTURE_CONSTRAINT_REGRESSION
  - UNAUTHORIZED_FILE_TOUCHED
  - HUMAN_ACTION_REQUIRED
  - B_ROUTE_BACKEND_TEST_FAILED
  - B_ROUTE_FRONTEND_TEST_FAILED
  - B_ROUTE_MANUAL_SMOKE_FAILED
  - B_ROUTE_ROUTER_SMOKE_FAILED
  - B_ROUTE_HEALTH_PAYLOAD_REGRESSION
  - B_ROUTE_CACHE_KEY_INCOMPLETE
  - B_ROUTE_STUB_DRIFT
validators:
  - validate_plan_compiles
  - validate_broute_schema_contract
  - validate_broute_cache_key_contract
  - validate_broute_health_public_payload
  - validate_public_security_invariants
  - validate_frontend_backend_contract
  - validate_broute_e2e_manual_smoke
  - validate_broute_e2e_router_stub_smoke
  - validate_no_banned_phrases
  - validate_changed_files_against_path_locks
  - validate_report_shape
  - validate_approval_packet
  - print_tracker_state
  - validate_future_constraints
  - validate_path_lock_pl_br_asr
  - validate_path_lock_pl_br_api_demo
  - validate_path_lock_pl_br_frontend
  - validate_path_lock_pl_br_tests
  - validate_path_lock_pl_br_scripts
  - generate_fixture_validate_plan_compiles
  - generate_fixture_validate_broute_schema_contract
  - generate_fixture_validate_broute_cache_key_contract
  - generate_fixture_validate_broute_health_public_payload
  - generate_fixture_validate_public_security_invariants
  - generate_fixture_validate_frontend_backend_contract
  - generate_fixture_validate_broute_e2e_manual_smoke
  - generate_fixture_validate_broute_e2e_router_stub_smoke
  - generate_fixture_validate_no_banned_phrases
  - generate_fixture_validate_changed_files_against_path_locks
  - generate_fixture_validate_report_shape
  - generate_fixture_validate_approval_packet
  - generate_fixture_print_tracker_state
  - generate_fixture_validate_future_constraints
artifacts:
  - reports/rp5/broute_discovery.md
  - reports/rp5/broute_frontend_detection.md
  - reports/rp5/broute_plan_compile.md
  - reports/rp5/broute_schema_contract.md
  - reports/rp5/broute_cache_key_contract.md
  - reports/rp5/broute_health_contract.md
  - reports/rp5/broute_public_security_invariants.md
  - reports/rp5/broute_frontend_backend_contract.md
  - reports/rp5/broute_manual_smoke.md
  - reports/rp5/broute_router_stub_smoke.md
  - reports/rp5/broute_future_constraints.md
  - reports/rp5/broute_phase_gate.md
  - scripts/rp5/fixtures/generate_fixture_validate_plan_compiles.py
  - scripts/rp5/fixtures/generate_fixture_validate_broute_schema_contract.py
  - scripts/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract.py
  - scripts/rp5/fixtures/generate_fixture_validate_broute_health_public_payload.py
  - scripts/rp5/fixtures/generate_fixture_validate_public_security_invariants.py
  - scripts/rp5/fixtures/generate_fixture_validate_frontend_backend_contract.py
  - scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke.py
  - scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke.py
  - scripts/rp5/fixtures/generate_fixture_validate_no_banned_phrases.py
  - scripts/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks.py
  - scripts/rp5/fixtures/generate_fixture_validate_report_shape.py
  - scripts/rp5/fixtures/generate_fixture_validate_approval_packet.py
  - scripts/rp5/fixtures/generate_fixture_print_tracker_state.py
  - scripts/rp5/fixtures/generate_fixture_validate_future_constraints.py
claims:
  - router_ready_seam_implemented
  - manual_mode_regression_free
  - router_stub_mode_available
  - public_security_invariants_preserved
  - future_constraints_preserved
```

## 1. Branch and repository layout

```yaml
repository:
  root: /home/gbibbo/code/asr_enhancement
  branch: feature/demo-runtime-rp5-v1
  runtime_preserved:
    - Docker Compose RP5 runtime
    - FastAPI bound to 8001 through local loopback in future public phase
    - upload and examples endpoints
    - job queue and cache
    - Whisper local fallback
    - optional AssemblyAI provider
    - admin HTTPBasic
    - structured JSON logs
    - soak evidence from B13.1
```

Path locks:

| Lock id | Type | Detection command | Include predicate | Exclude predicate | allowed_symbols_or_components | validator_command | Max changed files | Unauthorized marker |
|---|---|---|---|---|---|---|---:|---|
| PL-BR-CONFIG | exact_file_or_create | `test -f config/demo_examples.json || true` | demo config only | secrets and literal public URL | config/demo_examples.json | `python scripts/rp5/validate_changed_files_against_path_locks.py --lock PL-BR-CONFIG --diff HEAD~1..HEAD` | 1 | UNAUTHORIZED_FILE_TOUCHED |
| PL-BR-API-DEMO | exact_directory_with_predicate | `python scripts/rp5/write_broute_api_detection.py --out reports/rp5/broute_discovery.md` | demo route, upload route, result route, response assembly | admin auth secrets and unrelated modules | /demo/health, /demo/upload, /demo/results, assemble_demo_response | `python scripts/rp5/validate_path_lock_pl_br_api_demo.py --diff HEAD~1..HEAD` | 6 | UNAUTHORIZED_FILE_TOUCHED |
| PL-BR-ASR | exact_directory_with_predicate | `python scripts/rp5/write_broute_asr_detection.py --out reports/rp5/broute_discovery.md` | router runtime seam and cache helper | training code and provider secrets | RouterRuntime, RouterDecision, AssembledResponse, build_cache_key | `python scripts/rp5/validate_path_lock_pl_br_asr.py --diff HEAD~1..HEAD` | 8 | UNAUTHORIZED_FILE_TOUCHED |
| PL-BR-FRONTEND | exact_directory_with_predicate | `python scripts/rp5/write_broute_frontend_detection.py --out reports/rp5/broute_frontend_detection.md` | upload component and result component fields | unrelated style-only files | RouterFieldsPanel, UploadForm, ResultView | `python scripts/rp5/validate_path_lock_pl_br_frontend.py --diff HEAD~1..HEAD` | 8 | UNAUTHORIZED_FILE_TOUCHED |
| PL-BR-TESTS | exact_directory_with_predicate | `find tests -type f \( -path '*demo*' -o -path '*router*' -o -path '*api*' \)` | B-route schema, cache, mode, security, smoke tests | deleting or weakening existing tests | test_broute_backend.py, test_broute_frontend.py, test_broute_security.py | `python scripts/rp5/validate_path_lock_pl_br_tests.py --diff HEAD~1..HEAD` | 12 | UNAUTHORIZED_FILE_TOUCHED |
| PL-BR-SCRIPTS | exact_directory_with_predicate | `find scripts/rp5 scripts/demo -type f 2>/dev/null || true` | smoke validators and fixture generators | public tunnel control scripts outside current phase | scripts/rp5 validators and fixture generators | `python scripts/rp5/validate_path_lock_pl_br_scripts.py --diff HEAD~1..HEAD` | 18 | UNAUTHORIZED_FILE_TOUCHED |
| PL-BR-REPORTS | exact_directory_with_predicate | `mkdir -p reports/rp5 && find reports/rp5 -maxdepth 1 -type f` | B-route reports | literal public URL | broute_*.md | `python scripts/rp5/validate_changed_files_against_path_locks.py --lock PL-BR-REPORTS --diff HEAD~1..HEAD` | 20 | UNAUTHORIZED_FILE_TOUCHED |

## 2. Constants and decision rules

```yaml
router_mode_values: [manual, router]
manual_default: true
router_stub:
  router_kind: deterministic_selector
  router_version: stub-v0
  selected_backend: whisper_base_ct2_int8
  routing_explanation: "stub: awaiting datamove1 handoff"
routing_profile_default: balanced
health_payload_public:
  status: ok
health_payload_forbidden_fields:
  - version
  - build
  - commit
  - uptime
  - queue_depth
  - cache_stats
  - worker_count
  - model_name
  - provider_state
  - env_flags
  - hostname
cache_key_required_fields:
  - audio_hash
  - selected_backend
  - asr_model_and_version
  - router_kind
  - router_version
  - routing_profile
  - allow_third_party
  - degradation_version
  - metrics_or_features_version
router_decision_fields:
  - selected_backend
  - router_kind
  - router_version
  - routing_profile
  - allow_third_party
  - third_party_provider
  - cost_policy
  - estimated_cost_usd
  - predicted_confidence
  - predicted_ask_repeat
  - routing_explanation
  - router_latency_ms
assembled_response_fields:
  - transcript_text
  - selected_backend
  - router_kind
  - router_version
  - routing_profile
  - allow_third_party
  - third_party_provider
  - estimated_cost_usd
  - cost_usd
  - backend_confidence
  - ask_repeat
  - latency_ms.backend
  - latency_ms.server
  - latency_ms.end_to_end
  - routing_explanation
```

Pre-plan threshold audit:

| Category | Status | Source or issue |
|---|---|---|
| smoke_pass_threshold_numeric | not_applicable_current_scope | B-route is not LoRA smoke |
| full_training_pass_threshold_numeric | not_applicable_current_scope | B-route is not datamove1 training |
| family_collapse_threshold_numeric | not_applicable_current_scope | B-route has no degradation-family evaluation |
| baseline_reproduction_tolerance_numeric | not_applicable_current_scope_per_explicit_NA_from_human | HAR-BR-THRESHOLDS-001 resolved by human_action_result: B-route validates routing, schema, cache key, health payload, manual smoke, and router stub smoke. It does not introduce a formal metric regression benchmark. |
| clean_regression_tolerance_numeric | not_applicable_current_scope | no clean WER regression in B-route |
| quantization_preservation_factor_numeric | not_applicable_current_scope | no CT2 preservation in B-route |
| checkpoint_tie_break_tolerance_numeric | not_applicable_current_scope | no checkpoint selection in B-route |
| bootstrap_ci_threshold_if_applicable | not_applicable_current_scope | no statistical claim in B-route |
| degradation_macro_metric_target_numeric | not_applicable_current_scope | no degradation macro metric in B-route |
| latency_runtime_target_numeric | not_applicable_current_scope_per_explicit_NA_from_human | HAR-BR-THRESHOLDS-001 resolved by human_action_result: B-route does not set a new latency SLA. Latency thresholds belong to later public exposure or soak runtime validation. |
| memory_peak_target_numeric | not_applicable_current_scope_per_explicit_NA_from_human | HAR-BR-THRESHOLDS-001 resolved by human_action_result: B-route does not introduce a memory budget benchmark. Memory peak validation belongs to later soak runtime validation. |

Decision rules:

```yaml
manual_mode:
  router_decision_effect: none
  response_fields: assembled_response_fields with existing backend result
router_mode:
  router_decision_effect: deterministic_stub_until_datamove1_handoff
  selected_backend: whisper_base_ct2_int8
  required_response_fields: assembled_response_fields
health_payload_rule:
  public_payload_exact: {status: ok}
  forbidden_fields_trigger: B_ROUTE_HEALTH_PAYLOAD_REGRESSION
cache_key_rule:
  missing_required_field_triggers: B_ROUTE_CACHE_KEY_INCOMPLETE
```

## 3. Marker registry

| Marker | Owner | Active iff | Emits from | Recovery packet |
|---|---|---|---|---|
| PLAN_CONFLICT | agent | PLAN_CONFLICT predicate is true | validator or session-open | RP-PLAN-CONFLICT |
| PREPLAN_THRESHOLD_GAP | agent | PREPLAN_THRESHOLD_GAP predicate is true | validator or session-open | RP-PREPLAN-THRESHOLD-GAP |
| TRACKER_MISSING | agent | TRACKER_MISSING predicate is true | validator or session-open | RP-TRACKER-MISSING |
| TRACKER_MISMATCH | agent | TRACKER_MISMATCH predicate is true | validator or session-open | RP-TRACKER-MISMATCH |
| REPORT_SCHEMA_INVALID | agent | REPORT_SCHEMA_INVALID predicate is true | validator or session-open | RP-REPORT-SCHEMA-INVALID |
| APPROVAL_PACKET_MALFORMED | agent | APPROVAL_PACKET_MALFORMED predicate is true | validator or session-open | RP-APPROVAL-PACKET-MALFORMED |
| EXECUTION_RAIL_GAP | agent | EXECUTION_RAIL_GAP predicate is true | validator or session-open | RP-EXECUTION-RAIL-GAP |
| PATH_LOCK_TOO_BROAD | agent | PATH_LOCK_TOO_BROAD predicate is true | validator or session-open | RP-PATH-LOCK-TOO-BROAD |
| VALIDATOR_MATERIALIZATION_GAP | agent | VALIDATOR_MATERIALIZATION_GAP predicate is true | validator or session-open | RP-VALIDATOR-MATERIALIZATION-GAP |
| RECOVERY_PACKET_GAP | agent | RECOVERY_PACKET_GAP predicate is true | validator or session-open | RP-RECOVERY-PACKET-GAP |
| PUBLIC_SECURITY_REGRESSION | agent | PUBLIC_SECURITY_REGRESSION predicate is true | validator or session-open | RP-PUBLIC-SECURITY-REGRESSION |
| ROUTER_SCHEMA_DRIFT | agent | ROUTER_SCHEMA_DRIFT predicate is true | validator or session-open | RP-ROUTER-SCHEMA-DRIFT |
| FRONTEND_BACKEND_DRIFT | agent | FRONTEND_BACKEND_DRIFT predicate is true | validator or session-open | RP-FRONTEND-BACKEND-DRIFT |
| FUTURE_CONSTRAINT_REGRESSION | agent | FUTURE_CONSTRAINT_REGRESSION predicate is true | validator or session-open | RP-FUTURE-CONSTRAINT-REGRESSION |
| UNAUTHORIZED_FILE_TOUCHED | agent | UNAUTHORIZED_FILE_TOUCHED predicate is true | validator or session-open | RP-UNAUTHORIZED-FILE-TOUCHED |
| HUMAN_ACTION_REQUIRED | agent | HUMAN_ACTION_REQUIRED predicate is true | validator or session-open | RP-HUMAN-ACTION-REQUIRED |
| B_ROUTE_BACKEND_TEST_FAILED | agent | B_ROUTE_BACKEND_TEST_FAILED predicate is true | B-route validator | RP-BROUTE-BACKEND-TEST-FAILED |
| B_ROUTE_FRONTEND_TEST_FAILED | agent | B_ROUTE_FRONTEND_TEST_FAILED predicate is true | B-route validator | RP-BROUTE-FRONTEND-TEST-FAILED |
| B_ROUTE_MANUAL_SMOKE_FAILED | agent | B_ROUTE_MANUAL_SMOKE_FAILED predicate is true | B-route validator | RP-BROUTE-MANUAL-SMOKE-FAILED |
| B_ROUTE_ROUTER_SMOKE_FAILED | agent | B_ROUTE_ROUTER_SMOKE_FAILED predicate is true | B-route validator | RP-BROUTE-ROUTER-SMOKE-FAILED |
| B_ROUTE_HEALTH_PAYLOAD_REGRESSION | agent | B_ROUTE_HEALTH_PAYLOAD_REGRESSION predicate is true | B-route validator | RP-BROUTE-HEALTH-PAYLOAD-REGRESSION |
| B_ROUTE_CACHE_KEY_INCOMPLETE | agent | B_ROUTE_CACHE_KEY_INCOMPLETE predicate is true | B-route validator | RP-BROUTE-CACHE-KEY-INCOMPLETE |
| B_ROUTE_STUB_DRIFT | agent | B_ROUTE_STUB_DRIFT predicate is true | B-route validator | RP-BROUTE-STUB-DRIFT |


## 4. Linear transition table

| Current state | Condition | Marker if fail | Next state on PASS | Next state on FAIL | Report shape | Approval required |
|---|---|---|---|---|---|---|
| session-open | tracker readable and task matches B-route | TRACKER_MISSING or TRACKER_MISMATCH | BR-00 | stop | planning_report | yes |
| BR-00 | plan compiler passes | PLAN_CONFLICT | BR-01 | stop | execution_report | yes |
| BR-01 | schema seam and router runtime contracts pass | ROUTER_SCHEMA_DRIFT | BR-02 | BR-01 fix | execution_report | yes |
| BR-02 | health payload and security invariants pass | B_ROUTE_HEALTH_PAYLOAD_REGRESSION | BR-03 | BR-02 fix | execution_report | yes |
| BR-03 | cache key contract passes | B_ROUTE_CACHE_KEY_INCOMPLETE | BR-04 | BR-03 fix | execution_report | yes |
| BR-04 | frontend and backend contract pass | FRONTEND_BACKEND_DRIFT | BR-05 | BR-04 fix | execution_report | yes |
| BR-05 | manual smoke passes | B_ROUTE_MANUAL_SMOKE_FAILED | BR-06 | BR-05 fix | execution_report | yes |
| BR-06 | router stub smoke passes | B_ROUTE_ROUTER_SMOKE_FAILED | BR-07 | BR-06 fix | execution_report | yes |
| BR-07 | future constraints report validates | FUTURE_CONSTRAINT_REGRESSION | BR-08 | BR-07 fix | execution_report | yes |
| BR-08 | all gate predicates pass | any active B_ROUTE marker | phase gate | first failed task | phase_gate_report | yes |
| any | unauthorized path changed | UNAUTHORIZED_FILE_TOUCHED | stop | stop | execution_report | yes |

## 5. Tracker schema and runtime state

```yaml
tracker_file: docs/progress/rp5_progress.yaml
current_phase: B-route
current_task: BR-00
last_completed_task: B13.1
markers: []
human_action_requests:
  HAR-BR-THRESHOLDS-001:
    status: resolved
    result_kind: explicit_NA_all_three_categories
    evidence_reference: "Gabriel message: Ok, encárgate de implementar las mejoras entonces"
    accepted_by_orchestrator_decision: true
    resolved_fields:
      baseline_reproduction_tolerance_numeric: not_applicable_current_scope
      latency_runtime_target_numeric: not_applicable_current_scope
      memory_peak_target_numeric: not_applicable_current_scope
state_transport:
  latest_planning_report_path: null
  latest_execution_report_path: null
  latest_phase_gate_report_path: null
  latest_approval_packet_path: null
  expected_next_task: BR-00
decisions:
  broute_mode_default: manual
  human_action_policy: CHANGE_SCOPE_with_human_action_request_id
```

Runtime values are tracker-owned. This plan owns only schema and mutation rules.

## 6. Phase gate predicates

The B-route phase gate is evaluated after BR-08. Authority lives in orchestrator_plan.md section 3.

```yaml
B_route_gate_PASS_iff:
  task_statuses:
    BR-01: PASS
    BR-02: PASS
    BR-03: PASS
    BR-04: PASS
    BR-05: PASS
    BR-06: PASS
    BR-07: PASS
    BR-08: PASS
  validators:
    - validate_plan_compiles emits OK_PLAN_COMPILES
    - validate_broute_schema_contract emits OK_BROUTE_SCHEMA_CONTRACT
    - validate_broute_cache_key_contract emits OK_BROUTE_CACHE_KEY_CONTRACT
    - validate_broute_health_public_payload emits OK_BROUTE_HEALTH_PUBLIC_PAYLOAD
    - validate_public_security_invariants emits OK_PUBLIC_SECURITY_INVARIANTS
    - validate_frontend_backend_contract emits OK_FRONTEND_BACKEND_CONTRACT
    - validate_broute_e2e_manual_smoke emits OK_BROUTE_MANUAL_SMOKE
    - validate_broute_e2e_router_stub_smoke emits OK_BROUTE_ROUTER_STUB_SMOKE
    - validate_future_constraints emits OK_FUTURE_CONSTRAINTS
  forbidden_active_markers: all markers except HUMAN_ACTION_REQUIRED when scoped to thresholds only
```

## 7. Final verification checklist

| Check id | Command | PASS sentinel | Artifact |
|---|---|---|---|
| FV-PLAN | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out reports/rp5/broute_plan_compile.md` | OK_PLAN_COMPILES | reports/rp5/broute_plan_compile.md |
| FV-SCHEMA | `python scripts/rp5/validate_broute_schema_contract.py --out reports/rp5/broute_schema_contract.md` | OK_BROUTE_SCHEMA_CONTRACT | reports/rp5/broute_schema_contract.md |
| FV-CACHE | `python scripts/rp5/validate_broute_cache_key_contract.py --out reports/rp5/broute_cache_key_contract.md` | OK_BROUTE_CACHE_KEY_CONTRACT | reports/rp5/broute_cache_key_contract.md |
| FV-HEALTH | `python scripts/rp5/validate_broute_health_public_payload.py --base-url http://127.0.0.1:8001 --out reports/rp5/broute_health_contract.md` | OK_BROUTE_HEALTH_PUBLIC_PAYLOAD | reports/rp5/broute_health_contract.md |
| FV-SECURITY | `python scripts/rp5/validate_public_security_invariants.py --base-url http://127.0.0.1:8001 --out reports/rp5/broute_public_security_invariants.md` | OK_PUBLIC_SECURITY_INVARIANTS | reports/rp5/broute_public_security_invariants.md |
| FV-FRONTEND | `python scripts/rp5/validate_frontend_backend_contract.py --out reports/rp5/broute_frontend_backend_contract.md` | OK_FRONTEND_BACKEND_CONTRACT | reports/rp5/broute_frontend_backend_contract.md |
| FV-MANUAL | `python scripts/rp5/smoke_broute_manual.py --base-url http://127.0.0.1:8001 --out reports/rp5/broute_manual_smoke.md` | OK_BROUTE_MANUAL_SMOKE | reports/rp5/broute_manual_smoke.md |
| FV-ROUTER | `python scripts/rp5/smoke_broute_router_stub.py --base-url http://127.0.0.1:8001 --out reports/rp5/broute_router_stub_smoke.md` | OK_BROUTE_ROUTER_STUB_SMOKE | reports/rp5/broute_router_stub_smoke.md |
| FV-FUTURE | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/broute_future_constraints.md --out reports/rp5/future_constraint_validation.md` | OK_FUTURE_CONSTRAINTS | reports/rp5/future_constraint_validation.md |

## 8. Path lock contract

Each lock from section 1 has a validator command. At execution close, every changed file must match at least one lock and every matched lock must list the modified symbol or artifact path.

```yaml
path_lock_closure:
  command: python scripts/rp5/validate_changed_files_against_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md
  sentinel: OK_CHANGED_FILES_PATH_LOCKED
  failure_marker: UNAUTHORIZED_FILE_TOUCHED
  unauthorized_file_result: STOP_SCOPE_CONFLICT
```

## 9. Validator contracts and fixtures

Every validator has a deterministic generator for its positive and negative fixture. Generator scripts are plan artifacts in section 0.

| Validator id | Script path | Invocation command | Positive fixture generator | Positive fixture sha256 mode | Negative fixture generator | Negative fixture sha256 mode | Expected stdout | Owned failure marker |
|---|---|---|---|---|---|---|---|---|
| validate_plan_compiles | scripts/rp5/validate_plan_compiles.py | `python scripts/rp5/validate_plan_compiles.py --out reports/rp5/validate_plan_compiles.md` | `scripts/rp5/fixtures/generate_fixture_validate_plan_compiles.py --kind positive --out tests/rp5/fixtures/validate_plan_compiles_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_plan_compiles.py --kind negative --out tests/rp5/fixtures/validate_plan_compiles_negative.yaml` | computed_by_generator_manifest | OK_PLAN_COMPILES | PLAN_CONFLICT |
| validate_broute_schema_contract | scripts/rp5/validate_broute_schema_contract.py | `python scripts/rp5/validate_broute_schema_contract.py --out reports/rp5/validate_broute_schema_contract.md` | `scripts/rp5/fixtures/generate_fixture_validate_broute_schema_contract.py --kind positive --out tests/rp5/fixtures/validate_broute_schema_contract_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_broute_schema_contract.py --kind negative --out tests/rp5/fixtures/validate_broute_schema_contract_negative.yaml` | computed_by_generator_manifest | OK_BROUTE_SCHEMA_CONTRACT | ROUTER_SCHEMA_DRIFT |
| validate_broute_cache_key_contract | scripts/rp5/validate_broute_cache_key_contract.py | `python scripts/rp5/validate_broute_cache_key_contract.py --out reports/rp5/validate_broute_cache_key_contract.md` | `scripts/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract.py --kind positive --out tests/rp5/fixtures/validate_broute_cache_key_contract_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract.py --kind negative --out tests/rp5/fixtures/validate_broute_cache_key_contract_negative.yaml` | computed_by_generator_manifest | OK_BROUTE_CACHE_KEY_CONTRACT | B_ROUTE_CACHE_KEY_INCOMPLETE |
| validate_broute_health_public_payload | scripts/rp5/validate_broute_health_public_payload.py | `python scripts/rp5/validate_broute_health_public_payload.py --out reports/rp5/validate_broute_health_public_payload.md` | `scripts/rp5/fixtures/generate_fixture_validate_broute_health_public_payload.py --kind positive --out tests/rp5/fixtures/validate_broute_health_public_payload_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_broute_health_public_payload.py --kind negative --out tests/rp5/fixtures/validate_broute_health_public_payload_negative.yaml` | computed_by_generator_manifest | OK_BROUTE_HEALTH_PUBLIC_PAYLOAD | B_ROUTE_HEALTH_PAYLOAD_REGRESSION |
| validate_public_security_invariants | scripts/rp5/validate_public_security_invariants.py | `python scripts/rp5/validate_public_security_invariants.py --out reports/rp5/validate_public_security_invariants.md` | `scripts/rp5/fixtures/generate_fixture_validate_public_security_invariants.py --kind positive --out tests/rp5/fixtures/validate_public_security_invariants_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_public_security_invariants.py --kind negative --out tests/rp5/fixtures/validate_public_security_invariants_negative.yaml` | computed_by_generator_manifest | OK_PUBLIC_SECURITY_INVARIANTS | PUBLIC_SECURITY_REGRESSION |
| validate_frontend_backend_contract | scripts/rp5/validate_frontend_backend_contract.py | `python scripts/rp5/validate_frontend_backend_contract.py --out reports/rp5/validate_frontend_backend_contract.md` | `scripts/rp5/fixtures/generate_fixture_validate_frontend_backend_contract.py --kind positive --out tests/rp5/fixtures/validate_frontend_backend_contract_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_frontend_backend_contract.py --kind negative --out tests/rp5/fixtures/validate_frontend_backend_contract_negative.yaml` | computed_by_generator_manifest | OK_FRONTEND_BACKEND_CONTRACT | FRONTEND_BACKEND_DRIFT |
| validate_broute_e2e_manual_smoke | scripts/rp5/smoke_broute_manual.py | `python scripts/rp5/smoke_broute_manual.py --out reports/rp5/validate_broute_e2e_manual_smoke.md` | `scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke.py --kind positive --out tests/rp5/fixtures/validate_broute_e2e_manual_smoke_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke.py --kind negative --out tests/rp5/fixtures/validate_broute_e2e_manual_smoke_negative.yaml` | computed_by_generator_manifest | OK_BROUTE_MANUAL_SMOKE | B_ROUTE_MANUAL_SMOKE_FAILED |
| validate_broute_e2e_router_stub_smoke | scripts/rp5/smoke_broute_router_stub.py | `python scripts/rp5/smoke_broute_router_stub.py --out reports/rp5/validate_broute_e2e_router_stub_smoke.md` | `scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke.py --kind positive --out tests/rp5/fixtures/validate_broute_e2e_router_stub_smoke_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke.py --kind negative --out tests/rp5/fixtures/validate_broute_e2e_router_stub_smoke_negative.yaml` | computed_by_generator_manifest | OK_BROUTE_ROUTER_STUB_SMOKE | B_ROUTE_ROUTER_SMOKE_FAILED |
| validate_no_banned_phrases | scripts/rp5/validate_no_banned_phrases.py | `python scripts/rp5/validate_no_banned_phrases.py --out reports/rp5/validate_no_banned_phrases.md` | `scripts/rp5/fixtures/generate_fixture_validate_no_banned_phrases.py --kind positive --out tests/rp5/fixtures/validate_no_banned_phrases_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_no_banned_phrases.py --kind negative --out tests/rp5/fixtures/validate_no_banned_phrases_negative.yaml` | computed_by_generator_manifest | OK_NO_BANNED_PHRASES | EXECUTION_RAIL_GAP |
| validate_changed_files_against_path_locks | scripts/rp5/validate_changed_files_against_path_locks.py | `python scripts/rp5/validate_changed_files_against_path_locks.py --out reports/rp5/validate_changed_files_against_path_locks.md` | `scripts/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks.py --kind positive --out tests/rp5/fixtures/validate_changed_files_against_path_locks_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks.py --kind negative --out tests/rp5/fixtures/validate_changed_files_against_path_locks_negative.yaml` | computed_by_generator_manifest | OK_CHANGED_FILES_PATH_LOCKED | UNAUTHORIZED_FILE_TOUCHED |
| validate_report_shape | scripts/rp5/validate_report_shape.py | `python scripts/rp5/validate_report_shape.py --schemas docs/plans/broute/state_packet_schemas.yaml --report-from-tracker latest_context --out reports/rp5/report_shape_validation.md` | `scripts/rp5/fixtures/generate_fixture_validate_report_shape.py --kind positive --out tests/rp5/fixtures/validate_report_shape_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_report_shape.py --kind negative --out tests/rp5/fixtures/validate_report_shape_negative.yaml` | computed_by_generator_manifest | OK_REPORT_SHAPE | REPORT_SCHEMA_INVALID |
| validate_approval_packet | scripts/rp5/validate_approval_packet.py | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_approval_packet --out reports/rp5/approval_packet_validation.md` | `scripts/rp5/fixtures/generate_fixture_validate_approval_packet.py --kind positive --out tests/rp5/fixtures/validate_approval_packet_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_approval_packet.py --kind negative --out tests/rp5/fixtures/validate_approval_packet_negative.yaml` | computed_by_generator_manifest | OK_APPROVAL_PACKET | APPROVAL_PACKET_MALFORMED |
| print_tracker_state | scripts/rp5/print_tracker_state.py | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/tracker_state.md` | `scripts/rp5/fixtures/generate_fixture_print_tracker_state.py --kind positive --out tests/rp5/fixtures/print_tracker_state_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_print_tracker_state.py --kind negative --out tests/rp5/fixtures/print_tracker_state_negative.yaml` | computed_by_generator_manifest | OK_TRACKER_STATE | TRACKER_MISMATCH |
| validate_future_constraints | scripts/rp5/validate_future_constraints.py | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/broute_future_constraints.md --out reports/rp5/future_constraint_validation.md` | `scripts/rp5/fixtures/generate_fixture_validate_future_constraints.py --kind positive --out tests/rp5/fixtures/validate_future_constraints_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_future_constraints.py --kind negative --out tests/rp5/fixtures/validate_future_constraints_negative.yaml` | computed_by_generator_manifest | OK_FUTURE_CONSTRAINTS | FUTURE_CONSTRAINT_REGRESSION |
| validate_path_lock_pl_br_asr | scripts/rp5/validate_path_lock_pl_br_asr.py | `python scripts/rp5/validate_path_lock_pl_br_asr.py --out reports/rp5/validate_path_lock_pl_br_asr.md` | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_asr.py --kind positive --out tests/rp5/fixtures/validate_path_lock_pl_br_asr_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_asr.py --kind negative --out tests/rp5/fixtures/validate_path_lock_pl_br_asr_negative.yaml` | computed_by_generator_manifest | OK_PATH_LOCK_PL_BR_ASR | UNAUTHORIZED_FILE_TOUCHED |
| validate_path_lock_pl_br_api_demo | scripts/rp5/validate_path_lock_pl_br_api_demo.py | `python scripts/rp5/validate_path_lock_pl_br_api_demo.py --out reports/rp5/validate_path_lock_pl_br_api_demo.md` | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_api_demo.py --kind positive --out tests/rp5/fixtures/validate_path_lock_pl_br_api_demo_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_api_demo.py --kind negative --out tests/rp5/fixtures/validate_path_lock_pl_br_api_demo_negative.yaml` | computed_by_generator_manifest | OK_PATH_LOCK_PL_BR_API_DEMO | UNAUTHORIZED_FILE_TOUCHED |
| validate_path_lock_pl_br_frontend | scripts/rp5/validate_path_lock_pl_br_frontend.py | `python scripts/rp5/validate_path_lock_pl_br_frontend.py --out reports/rp5/validate_path_lock_pl_br_frontend.md` | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_frontend.py --kind positive --out tests/rp5/fixtures/validate_path_lock_pl_br_frontend_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_frontend.py --kind negative --out tests/rp5/fixtures/validate_path_lock_pl_br_frontend_negative.yaml` | computed_by_generator_manifest | OK_PATH_LOCK_PL_BR_FRONTEND | UNAUTHORIZED_FILE_TOUCHED |
| validate_path_lock_pl_br_tests | scripts/rp5/validate_path_lock_pl_br_tests.py | `python scripts/rp5/validate_path_lock_pl_br_tests.py --out reports/rp5/validate_path_lock_pl_br_tests.md` | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_tests.py --kind positive --out tests/rp5/fixtures/validate_path_lock_pl_br_tests_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_tests.py --kind negative --out tests/rp5/fixtures/validate_path_lock_pl_br_tests_negative.yaml` | computed_by_generator_manifest | OK_PATH_LOCK_PL_BR_TESTS | UNAUTHORIZED_FILE_TOUCHED |
| validate_path_lock_pl_br_scripts | scripts/rp5/validate_path_lock_pl_br_scripts.py | `python scripts/rp5/validate_path_lock_pl_br_scripts.py --out reports/rp5/validate_path_lock_pl_br_scripts.md` | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_scripts.py --kind positive --out tests/rp5/fixtures/validate_path_lock_pl_br_scripts_positive.yaml` | computed_by_generator_manifest | `scripts/rp5/fixtures/generate_fixture_validate_path_lock_pl_br_scripts.py --kind negative --out tests/rp5/fixtures/validate_path_lock_pl_br_scripts_negative.yaml` | computed_by_generator_manifest | OK_PATH_LOCK_PL_BR_SCRIPTS | UNAUTHORIZED_FILE_TOUCHED |

Fixture generator contracts:

| Generator id | Script path | Command | Output manifest | Sentinel | Owned marker |
|---|---|---|---|---|---|
| generate_fixture_validate_plan_compiles | scripts/rp5/fixtures/generate_fixture_validate_plan_compiles.py | `python scripts/rp5/fixtures/generate_fixture_validate_plan_compiles.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_plan_compiles_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_plan_compiles_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_PLAN_COMPILES | PLAN_CONFLICT |
| generate_fixture_validate_broute_schema_contract | scripts/rp5/fixtures/generate_fixture_validate_broute_schema_contract.py | `python scripts/rp5/fixtures/generate_fixture_validate_broute_schema_contract.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_broute_schema_contract_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_broute_schema_contract_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_BROUTE_SCHEMA_CONTRACT | ROUTER_SCHEMA_DRIFT |
| generate_fixture_validate_broute_cache_key_contract | scripts/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract.py | `python scripts/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_broute_cache_key_contract_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_BROUTE_CACHE_KEY_CONTRACT | B_ROUTE_CACHE_KEY_INCOMPLETE |
| generate_fixture_validate_broute_health_public_payload | scripts/rp5/fixtures/generate_fixture_validate_broute_health_public_payload.py | `python scripts/rp5/fixtures/generate_fixture_validate_broute_health_public_payload.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_broute_health_public_payload_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_broute_health_public_payload_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_BROUTE_HEALTH_PUBLIC_PAYLOAD | B_ROUTE_HEALTH_PAYLOAD_REGRESSION |
| generate_fixture_validate_public_security_invariants | scripts/rp5/fixtures/generate_fixture_validate_public_security_invariants.py | `python scripts/rp5/fixtures/generate_fixture_validate_public_security_invariants.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_public_security_invariants_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_public_security_invariants_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_PUBLIC_SECURITY_INVARIANTS | PUBLIC_SECURITY_REGRESSION |
| generate_fixture_validate_frontend_backend_contract | scripts/rp5/fixtures/generate_fixture_validate_frontend_backend_contract.py | `python scripts/rp5/fixtures/generate_fixture_validate_frontend_backend_contract.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_frontend_backend_contract_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_frontend_backend_contract_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_FRONTEND_BACKEND_CONTRACT | FRONTEND_BACKEND_DRIFT |
| generate_fixture_validate_broute_e2e_manual_smoke | scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke.py | `python scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_BROUTE_E2E_MANUAL_SMOKE | B_ROUTE_MANUAL_SMOKE_FAILED |
| generate_fixture_validate_broute_e2e_router_stub_smoke | scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke.py | `python scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_broute_e2e_router_stub_smoke_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_BROUTE_E2E_ROUTER_STUB_SMOKE | B_ROUTE_ROUTER_SMOKE_FAILED |
| generate_fixture_validate_no_banned_phrases | scripts/rp5/fixtures/generate_fixture_validate_no_banned_phrases.py | `python scripts/rp5/fixtures/generate_fixture_validate_no_banned_phrases.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_no_banned_phrases_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_no_banned_phrases_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_NO_BANNED_PHRASES | EXECUTION_RAIL_GAP |
| generate_fixture_validate_changed_files_against_path_locks | scripts/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks.py | `python scripts/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_CHANGED_FILES_AGAINST_PATH_LOCKS | UNAUTHORIZED_FILE_TOUCHED |
| generate_fixture_validate_report_shape | scripts/rp5/fixtures/generate_fixture_validate_report_shape.py | `python scripts/rp5/fixtures/generate_fixture_validate_report_shape.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_report_shape_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_report_shape_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_REPORT_SHAPE | REPORT_SCHEMA_INVALID |
| generate_fixture_validate_approval_packet | scripts/rp5/fixtures/generate_fixture_validate_approval_packet.py | `python scripts/rp5/fixtures/generate_fixture_validate_approval_packet.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_approval_packet_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_approval_packet_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_APPROVAL_PACKET | APPROVAL_PACKET_MALFORMED |
| generate_fixture_print_tracker_state | scripts/rp5/fixtures/generate_fixture_print_tracker_state.py | `python scripts/rp5/fixtures/generate_fixture_print_tracker_state.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_print_tracker_state_manifest.json` | tests/rp5/fixtures/generate_fixture_print_tracker_state_manifest.json with sha256 per file | OK_FIXTURE_PRINT_TRACKER_STATE | TRACKER_MISMATCH |
| generate_fixture_validate_future_constraints | scripts/rp5/fixtures/generate_fixture_validate_future_constraints.py | `python scripts/rp5/fixtures/generate_fixture_validate_future_constraints.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_future_constraints_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_future_constraints_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_FUTURE_CONSTRAINTS | FUTURE_CONSTRAINT_REGRESSION |


validate_plan_compiles must_check contract:

```yaml
must_check:
  - every_marker_in_registry_has_transition_row
  - every_marker_has_recovery_packet
  - every_validator_owned_failure_marker_exists
  - every_task_next_state_exists
  - every_report_referenced_by_agent_has_schema
  - every_approval_rule_has_schema_record
  - every_path_lock_reference_resolves_to_file_or_directory_policy
  - every_action_has_matching_deliverable
  - every_deliverable_has_producing_action
  - every_future_constraint_from_preplan_has_preservation_rule_or_explicit_out_of_scope_record
  - every_patch_with_N_locations_modified_has_acceptance_check_per_location
  - every_new_entity_has_full_registration_set_for_its_type
  - every_new_consumer_audited_pre_existing_data_or_explicit_NA
```

## 10. Task contracts

| Task | Preconditions | Actions | Deliverables | Validators | Done when | Stop condition |
|---|---|---|---|---|---|---|
| BR-00 | tracker readable | run plan compiler, report path locks, report missing thresholds | reports/rp5/broute_plan_compile.md | validate_plan_compiles | OK_PLAN_COMPILES | stop after planning report |
| BR-01 | BR-00 PASS | create or update `libs/asr/router_runtime.py`; selection rule: use that exact file for RouterRuntime, RouterDecision, AssembledResponse, and build_cache_key | reports/rp5/broute_schema_contract.md | validate_broute_schema_contract | OK_BROUTE_SCHEMA_CONTRACT | stop after execution_report |
| BR-02 | BR-01 PASS | redefine public `GET /demo/health` to return only `{"status":"ok"}`; route detailed diagnostics to `/admin/health` under admin auth | reports/rp5/broute_health_contract.md | validate_broute_health_public_payload, validate_public_security_invariants | both sentinels observed | stop after execution_report |
| BR-03 | BR-02 PASS | extend cache key using every cache_key_required_field from section 2 | reports/rp5/broute_cache_key_contract.md | validate_broute_cache_key_contract | OK_BROUTE_CACHE_KEY_CONTRACT | stop after execution_report |
| BR-04 | BR-03 PASS | run `python scripts/rp5/write_broute_frontend_detection.py --out reports/rp5/broute_frontend_detection.md`; update only files named by that report and path lock PL-BR-FRONTEND | reports/rp5/broute_frontend_backend_contract.md | validate_frontend_backend_contract | OK_FRONTEND_BACKEND_CONTRACT | stop after execution_report |
| BR-05 | BR-04 PASS | run manual end-to-end smoke with router disabled | reports/rp5/broute_manual_smoke.md | validate_broute_e2e_manual_smoke | OK_BROUTE_MANUAL_SMOKE | stop after execution_report |
| BR-06 | BR-05 PASS | run router end-to-end smoke with deterministic stub values | reports/rp5/broute_router_stub_smoke.md | validate_broute_e2e_router_stub_smoke | OK_BROUTE_ROUTER_STUB_SMOKE | stop after execution_report |
| BR-07 | BR-06 PASS | write future constraint records for B14.0, B14.1, B15, B-handoff | reports/rp5/broute_future_constraints.md | validate_future_constraints | OK_FUTURE_CONSTRAINTS | stop after execution_report |
| BR-08 | BR-07 PASS | run final B-route gate checklist | reports/rp5/broute_phase_gate.md | all validators from section 7 | all sentinels observed and no blocking marker active | stop for PHASE_APPROVE |

## 11. Recovery packets

Commands in this table are literal. `--report-from-tracker latest_context` means the validator reads the tracker field that matches the marker origin: latest_planning_report_path, latest_execution_report_path, or latest_phase_gate_report_path. No shell placeholder is used.

| Packet id | Marker | Diagnosis command | Allowed inspect | Allowed modify | Retry limit | Next state recovered | Next state exhausted |
|---|---|---|---|---|---:|---|---|
| RP-PLAN-CONFLICT | PLAN_CONFLICT | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out reports/rp5/plan_conflict.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-PREPLAN-THRESHOLD-GAP | PREPLAN_THRESHOLD_GAP | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/pending_har.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | none until human_action_result is recorded | 0 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-TRACKER-MISSING | TRACKER_MISSING | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/tracker_missing.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-TRACKER-MISMATCH | TRACKER_MISMATCH | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/tracker_mismatch.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-REPORT-SCHEMA-INVALID | REPORT_SCHEMA_INVALID | `python scripts/rp5/validate_report_shape.py --schemas docs/plans/broute/state_packet_schemas.yaml --report-from-tracker latest_context --out reports/rp5/report_schema_invalid.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-APPROVAL-PACKET-MALFORMED | APPROVAL_PACKET_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_approval_packet --out reports/rp5/approval_packet_malformed.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-EXECUTION-RAIL-GAP | EXECUTION_RAIL_GAP | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out reports/rp5/execution_rail_gap.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-PATH-LOCK-TOO-BROAD | PATH_LOCK_TOO_BROAD | `python scripts/rp5/validate_changed_files_against_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_too_broad.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-VALIDATOR-MATERIALIZATION-GAP | VALIDATOR_MATERIALIZATION_GAP | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out reports/rp5/validator_materialization_gap.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-RECOVERY-PACKET-GAP | RECOVERY_PACKET_GAP | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out reports/rp5/recovery_packet_gap.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-PUBLIC-SECURITY-REGRESSION | PUBLIC_SECURITY_REGRESSION | `python scripts/rp5/validate_public_security_invariants.py --base-url http://127.0.0.1:8001 --out reports/rp5/public_security_regression.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-ROUTER-SCHEMA-DRIFT | ROUTER_SCHEMA_DRIFT | `python scripts/rp5/validate_broute_schema_contract.py --out reports/rp5/router_schema_drift.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-FRONTEND-BACKEND-DRIFT | FRONTEND_BACKEND_DRIFT | `python scripts/rp5/validate_frontend_backend_contract.py --out reports/rp5/frontend_backend_drift.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-FUTURE-CONSTRAINT-REGRESSION | FUTURE_CONSTRAINT_REGRESSION | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/broute_future_constraints.md --out reports/rp5/future_constraint_regression.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-UNAUTHORIZED-FILE-TOUCHED | UNAUTHORIZED_FILE_TOUCHED | `python scripts/rp5/validate_changed_files_against_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/unauthorized_file_touched.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-HUMAN-ACTION-REQUIRED | HUMAN_ACTION_REQUIRED | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/pending_human_action.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | none until human_action_result is recorded | 0 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-BACKEND-TEST-FAILED | B_ROUTE_BACKEND_TEST_FAILED | `python -m pytest tests/rp5/test_broute_backend.py -v --tb=short > reports/rp5/broute_backend_test_failure.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-FRONTEND-TEST-FAILED | B_ROUTE_FRONTEND_TEST_FAILED | `python -m pytest tests/rp5/test_broute_frontend.py -v --tb=short > reports/rp5/broute_frontend_test_failure.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-MANUAL-SMOKE-FAILED | B_ROUTE_MANUAL_SMOKE_FAILED | `python scripts/rp5/smoke_broute_manual.py --base-url http://127.0.0.1:8001 --debug --out reports/rp5/broute_manual_smoke_failure.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-ROUTER-SMOKE-FAILED | B_ROUTE_ROUTER_SMOKE_FAILED | `python scripts/rp5/smoke_broute_router_stub.py --base-url http://127.0.0.1:8001 --debug --out reports/rp5/broute_router_smoke_failure.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-HEALTH-PAYLOAD-REGRESSION | B_ROUTE_HEALTH_PAYLOAD_REGRESSION | `python scripts/rp5/validate_broute_health_public_payload.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/broute_health_regression.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-CACHE-KEY-INCOMPLETE | B_ROUTE_CACHE_KEY_INCOMPLETE | `python scripts/rp5/validate_broute_cache_key_contract.py --verbose --out reports/rp5/broute_cache_key_incomplete.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |
| RP-BROUTE-STUB-DRIFT | B_ROUTE_STUB_DRIFT | `python scripts/rp5/validate_broute_schema_contract.py --component router_stub --verbose --out reports/rp5/broute_stub_drift.md` | docs/plans/broute, docs/progress/rp5_progress.yaml, reports/rp5 | same task owned files only | 1 | same task or BR-00 after recovery | CHANGE_SCOPE |


The table above is exhaustive for every marker in section 3.

## 12. Security and forbidden scope

Forbidden in B-route:

| Scope | Reason | Marker |
|---|---|---|
| Tailscale Funnel service work | belongs to B14.1 | FUTURE_CONSTRAINT_REGRESSION |
| recruiter HTTPBasic implementation | belongs to B14.0 | FUTURE_CONSTRAINT_REGRESSION |
| public URL commit | pre-plan forbids literal URL commit without explicit Gabriel approval | PUBLIC_SECURITY_REGRESSION |
| port binding changes for public exposure | belongs to B14.1 | FUTURE_CONSTRAINT_REGRESSION |
| datamove1 handoff swap | belongs to B-handoff | FUTURE_CONSTRAINT_REGRESSION |
| changing admin auth semantics | unrelated to B-route | UNAUTHORIZED_FILE_TOUCHED |

## 13. Report skeletons

Report shapes are defined in state_packet_schemas.yaml.

```yaml
planning_report: state_packet_schemas.yaml planning_report
execution_report: state_packet_schemas.yaml execution_report
phase_gate_report: state_packet_schemas.yaml phase_gate_report
approval_packet: state_packet_schemas.yaml approval_packet
supplemental_evidence_report: state_packet_schemas.yaml supplemental_evidence_report
future_constraint_preservation_report: state_packet_schemas.yaml future_constraint_preservation_record
```

## 14. Banned phrases and no-improvisation scan

The validator scans all canonical files and ignores only this YAML list plus orchestrator forbidden-output examples.

```yaml
banned_phrases_item_01: "as needed"
banned_phrases_item_02: "as appropriate"
banned_phrases_item_03: "as required"
banned_phrases_item_04: "if already present"
banned_phrases_item_05: "if present"
banned_phrases_item_06: "where appropriate"
banned_phrases_item_07: "best practices"
banned_phrases_item_08: "obvious"
banned_phrases_item_09: "TBD"
banned_phrases_item_10: "TODO without a marker"
banned_phrases_item_11: "discovered"
banned_phrases_item_12: "discover "
banned_phrases_item_13: "judgment"
banned_phrases_item_14: "free-form"
banned_phrases_item_15: "free form"
```

Scan command:

```bash
grep -nE '(as needed|as appropriate|as required|if already present|if present|where appropriate|best practices|obvious|TBD|TODO without a marker|discovered|discover |judgment|free-form|free form)' agent_plan.md orchestrator_plan.md | grep -v 'section_14\|banned_phrases\|forbidden_orchestrator_outputs'
```

Expected result: zero rows.

## 15. Human action requests and results

| HAR id | Trigger marker | Missing input | Blocking scope | Required human result shape |
|---|---|---|---|---|
| HAR-BR-THRESHOLDS-001 | PREPLAN_THRESHOLD_GAP | baseline reproduction tolerance, runtime latency target, memory peak target | resolved before STOP_PROPOSED | explicit_NA accepted for all three categories |

HUMAN_ACTION_REQUIRED maps to CHANGE_SCOPE with `required_fix` containing the HAR id. No new approval decision enum is introduced.

Resolved human action result:

```yaml
human_action_result:
  request_id: HAR-BR-THRESHOLDS-001
  supplied_values: null
  explicit_NA:
    baseline_reproduction_tolerance_numeric:
      status: not_applicable_current_scope
      rationale: B-route does not introduce a formal metric regression benchmark. It validates routing, manual runtime behavior, schema contracts, cache-key behavior, health payload safety, and end-to-end smoke.
    latency_runtime_target_numeric:
      status: not_applicable_current_scope
      rationale: B-route does not set a new latency SLA. Latency targets belong to later public exposure or soak runtime validation.
    memory_peak_target_numeric:
      status: not_applicable_current_scope
      rationale: B-route does not introduce a memory-budget benchmark. Memory peak validation belongs to later soak runtime validation.
  evidence_reference: Gabriel message authorizing implementation of the remaining improvements before WRITER turn 9
  accepted_by_orchestrator_decision: true
  next_state: STOP_PROPOSED preparation allowed after mechanical checks pass
```

## 16. Issue and patch ledger

| Turn | Patch ids | Issues addressed | Status |
|---|---|---|---|
| WRITER turn 3 | WRI2_P01..WRI2_P04 | first canonical drafts | superseded by this patch set |
| REVIEWER turn 4 | REV4_P01..REV4_P13 | orphan recovery packets, marker mismatch, hard stops, approval shape, validators, placeholders, plan compiler, phrase scan, path locks, fixtures, future constraints, stress replay, mature inventory | applied in WRITER turn 5 |
| WRITER turn 5 | WRI5_P01..WRI5_P13 | implements REV4_P01..REV4_P13 | reviewed by REVIEWER turn 6 |
| REVIEWER turn 6 | REV6_P01..REV6_P05 | residual stress pack, forbidden public regressions, MMI enums, validator IDs, cleanliness directive | applied in WRITER turn 7 except cleanliness deferred |
| WRITER turn 7 | WRI7_P01..WRI7_P04, WRI7_P05 deferred | implements REV6_P01..REV6_P04 | reviewed by REVIEWER turn 8 |
| REVIEWER turn 8 | REV8_P01 | conditional HAR and cleanliness directive | applied in WRITER turn 9 |
| WRITER turn 9 | WRI9_P01..WRI9_P03 | HAR resolved by explicit_NA, canonical cleanliness applied, final mechanical checks re-run | STOP_PROPOSED |

## 17. Adversarial stress-test results

| Scenario | initial_state | triggering_event | expected_marker | expected_next_state | expected_report_shape | generated_plan_sections_used | result |
|---|---|---|---|---|---|---|---|
| tracker missing | tracker file absent | session-open | TRACKER_MISSING | stop | supplemental_evidence_report | sections 3,4,11,13 | PASS evidence: RP-TRACKER-MISSING maps to exact command |
| task mismatch | tracker current_task differs from request | planning request | TRACKER_MISMATCH | stop | planning_report | sections 3,4,11,13 | PASS evidence: section 4 row and RP-TRACKER-MISMATCH |
| malformed approval | approval lacks wrapper | approval intake | APPROVAL_PACKET_MALFORMED | stop | supplemental_evidence_report | sections 3,11,13 and schema approval_packet | PASS evidence: validate_approval_packet contract |
| report schema invalid | report lacks required section | report validation | REPORT_SCHEMA_INVALID | stop | supplemental_evidence_report | sections 9,11,13 | PASS evidence: validate_report_shape contract |
| backend schema drift | RouterDecision missing field | BR-01 closure | ROUTER_SCHEMA_DRIFT | BR-01 fix | execution_report | sections 2,3,4,9,10,11 | PASS evidence: schema validator contract |
| health regression | /demo/health emits version | BR-02 closure | B_ROUTE_HEALTH_PAYLOAD_REGRESSION | BR-02 fix | execution_report | sections 2,3,4,9,10,11 | PASS evidence: exact health payload validator |
| cache key incomplete | router_version missing from cache key | BR-03 closure | B_ROUTE_CACHE_KEY_INCOMPLETE | BR-03 fix | execution_report | sections 2,3,4,9,10,11 | PASS evidence: cache key validator |
| frontend mismatch | UI hides router_kind | BR-04 closure | FRONTEND_BACKEND_DRIFT | BR-04 fix | execution_report | sections 3,4,9,10,11 | PASS evidence: frontend-backend validator |
| future phase regression | B14.1 Funnel work starts in B-route | BR-07 closure | FUTURE_CONSTRAINT_REGRESSION | CHANGE_SCOPE | execution_report | sections 3,4,11,12 | PASS evidence: future constraint validator |
| unauthorized path | secret file modified | any closure | UNAUTHORIZED_FILE_TOUCHED | stop | execution_report | sections 1,3,8,11 | PASS evidence: path lock validator |

## 18. Mature mechanism inventory and operational stress pack snapshot

| mechanism_id | mature_source_file | mature_source_section | mature_behavior_summary | applies_to_current_preplan_scope | generated_plan_target_file | generated_plan_target_section | generated_plan_equivalent_behavior | equivalence_direction | concrete_counterexample_attempted | counterexample_result | required_patch_if_WEAKER |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MMI-001 | mature orchestrator | authority split | separate orchestrator, agent, schema authority | true | all three | orchestrator 0, agent 0, schema root | same partition | EQUAL | checked phase authority not in task body | no gap | none |
| MMI-002 | mature schema | ORCHESTRATOR_DECISION wrapper | wrapper with all 8 keys present | true | schema | approval_packet | all 8 keys required | EQUAL | tried 3-key packet | rejected by schema | none |
| MMI-003 | mature agent | marker recovery | every marker has recovery packet | true | agent | sections 3 and 11 | 23 markers, 23 packets | EQUAL | B_ROUTE marker lookup | packet exists | none |
| MMI-004 | mature agent | validator contracts | every script has contract and fixtures | true | agent | section 9 | validator plus generator contracts | EQUAL | validate_report_shape lookup | contract exists | none |
| MMI-005 | mature agent | path locks | closed path policy with validators | true | agent | sections 1 and 8 | locks have symbols and validators | EQUAL | frontend lock broadness | validator row added | none |
| MMI-006 | mature agent | transition closure | closed transition table | true | agent | section 4 | every task and marker maps to next state | EQUAL | HUMAN_ACTION marker | maps to CHANGE_SCOPE | none |
| MMI-007 | mature schema | schema not runtime owner | schema defines shape only | true | schema | whole file | no runtime values or commands | EQUAL | grep for python command in schema | zero hits | none |
| MMI-008 | mature agent | no phrase improvisation | scanner rejects forbidden phrases | true | agent | section 14 | scan command and no body hits | EQUAL | grep command run | zero hits after exclusions | none |
| MMI-009 | mature agent | final verification outside final task | final gate separate from task PASS | true | orchestrator | section 5 | closure independent from BR-08 | EQUAL | BR-08 PASS without PHASE_APPROVE | not closed | none |
| MMI-010 | mature schema | falseability fields | every PASS cites evidence | true | schema and agent | schema reports, agent 17 | stress rows include sections and report shape | EQUAL | summary-only stress row | rewritten | none |
| MMI-011 | mature orchestrator | pre-bootstrap exception | tracker absent is a special mode | true_partial | agent | sections 3,4,11 | existing repo expected, TRACKER_MISSING stops with recovery | EQUAL | tracker absent | stop path exists | none |
| MMI-012 | mature orchestrator | repository integration authority | path reuse and no-touch policy | true | agent | sections 1 and 8 | path locks and unauthorized marker | EQUAL | unauthorized file | blocked | none |
| MMI-013 | mature orchestrator | outcome resolution table | crossed states drive routing | false | agent | section 2 | B-route has no LoRA/OOD/API outcome matrix | NOT_APPLICABLE_LEGITIMATE_SCOPE_DIFFERENCE | current pre-plan excludes training outcomes | out_of_scope_legitimate | none |
| MMI-014 | mature orchestrator | strategic decisions A/B/C/D | tracker-owned experimental decisions | false | agent | section 2 | B-route has mode rule, not datamove1 decisions | NOT_APPLICABLE_LEGITIMATE_SCOPE_DIFFERENCE | current pre-plan excludes LoRA and router training decisions | out_of_scope_legitimate | none |
| MMI-015 | mature orchestrator | cross-branch handoff loop | handoff by tag after P9.1 | true_preserved | orchestrator and agent | orchestrator 3, agent 12 | B-handoff preserved as future constraint | EQUAL | swap attempted in B-route | blocked | none |
| MMI-016 | mature schema | prebootstrap_inventory_report schema | structured no-tracker report | true_partial | schema | prebootstrap_inventory_report | present for tracker-absent diagnostics | EQUAL | tracker missing report | schema exists | none |

Operational stress pack:

```yaml
no_summary_only_audits: PASS
validate_plan_compiles_contract_present: PASS
action_deliverable_validator_bijection_complete: PASS
path_lock_granularity_pass: PASS
future_constraint_preservation_pass: PASS
adversarial_trajectory_replay_pass: PASS
last_patch_regression_attack_pass_if_applicable: PASS
canonical_final_cleanliness_pass: PASS
```
