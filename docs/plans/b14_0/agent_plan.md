# agent_plan.md

Plan state: APPROVED_FOR_EXECUTION (accepted_plan_revision_commit 8a049d00bdfec5b97c416f3135644ecd78f14bd8)
Project scope: B14.0 recruiter HTTPBasic public-access gate only. Future phases (B14.1, B15, B-handoff) are preserved but not executable in this plan. B-route deliverables are frozen.
Authority: executable task order, exact commands, validators, fixture generators, marker registry, recovery packets, transition table, tracker mutation rules, path locks, and report skeleton references.

## 0. Manifest and entity registry

```yaml
project: b14_0_recruiter_http_basic_public_gate
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
starting_state:
  last_completed_phase: B-route
  current_phase: B14.0_PENDING_ORCHESTRATOR_INSTRUCTION
  current_task: B14.0_PENDING_ORCHESTRATOR_INSTRUCTION
canonical_output_files:
  - docs/plans/b14_0/orchestrator_plan.md
  - docs/plans/b14_0/agent_plan.md
  - docs/plans/b14_0/state_packet_schemas.yaml
phases:
  - B14.0
  - B14.1_future_constraint
  - B15_future_constraint
  - B-handoff_future_constraint
tasks:
  - B14_0-00
  - B14_0-01
  - B14_0-02
  - B14_0-03
  - B14_0-04
  - B14_0-05
  - B14_0-06
  - B14_0-07
  - B14_0-08
markers:
  - PLAN_CONFLICT
  - TRACKER_MISSING
  - TRACKER_MISMATCH
  - REPORT_SCHEMA_INVALID
  - APPROVAL_PACKET_MALFORMED
  - EXECUTION_RAIL_GAP
  - PATH_LOCK_TOO_BROAD
  - VALIDATOR_MATERIALIZATION_GAP
  - RECOVERY_PACKET_GAP
  - UNAUTHORIZED_FILE_TOUCHED
  - HUMAN_ACTION_REQUIRED
  - FUTURE_CONSTRAINT_REGRESSION
  - PUBLIC_SECURITY_REGRESSION
  - B14_0_RECRUITER_AUTH_CONTRACT_FAILED
  - B14_0_AUTH_BYPASS_DETECTED
  - B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH
  - B14_0_ADMIN_RECRUITER_CRED_CONFLATION
  - B14_0_FRONTEND_AUTH_UX_DRIFT
  - B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED
  - B14_0_CRED_LEAK_DETECTED
  - B14_0_BROUTE_REGRESSION_UNDER_AUTH
validators:
  - validate_plan_compiles
  - validate_b14_0_recruiter_auth_contract
  - validate_b14_0_auth_separation_invariants
  - validate_b14_0_health_payload_preserved_under_auth
  - validate_b14_0_frontend_auth_contract
  - validate_b14_0_e2e_manual_smoke_with_auth
  - validate_b14_0_no_credential_leak
  - validate_b14_0_broute_compatibility_under_auth
  - validate_future_constraints
  - validate_no_banned_phrases
  - validate_changed_files_against_path_locks
  - validate_report_shape
  - validate_approval_packet
  - print_tracker_state
  - validate_public_security_invariants  # inherited from B-route; reused by RP-PUBLIC-SECURITY-REGRESSION diagnosis command in §11
artifacts:
  - reports/rp5/b14_0_plan_compile.md
  - reports/rp5/b14_0_recruiter_auth_contract.md
  - reports/rp5/b14_0_auth_separation_invariants.md
  - reports/rp5/b14_0_health_payload_under_auth.md
  - reports/rp5/b14_0_frontend_auth_contract.md
  - reports/rp5/b14_0_manual_smoke_with_auth.md
  - reports/rp5/b14_0_no_credential_leak.md
  - reports/rp5/b14_0_broute_compatibility_under_auth.md
  - reports/rp5/b14_0_future_constraints.md
  - reports/rp5/b14_0_phase_gate.md
claims:
  - recruiter_public_gate_enforced_on_all_public_demo_routes
  - admin_auth_unchanged_and_strictly_separate_from_recruiter
  - BR-02_health_payload_preserved_under_recruiter_auth
  - no_credential_leak_in_logs_or_error_pages
  - BR-01_through_BR-08_artifacts_remain_frozen
  - future_constraints_preserved
```

## 1. Branch, repository layout, and path locks

```yaml
repository:
  root: /home/gbibbo/code/asr_enhancement
  branch: feature/demo-runtime-rp5-v1
  runtime_preserved:
    - all B-route deliverables and validators
    - libs/asr/router_runtime.py (frozen schema)
    - admin HTTPBasic and existing /admin/* routes
    - structured JSON logs and log rotation policy
    - SQLite job and cache tables
```

| Lock id | Type | Allowed components | Validator command | Max files | Marker on violation |
|---|---|---|---|---:|---|
| PL-B14_0-API-DEMO | exact_directory_with_predicate | recruiter middleware and dependency wiring in services/api/app/; admin auth code in services/api/app/ may be inspected but not modified except where the predicate explicitly allows | `python scripts/rp5/validate_path_lock_pl_b14_0_api_demo.py --diff HEAD~1..HEAD` | 6 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_0-FRONTEND | exact_directory_with_predicate | recruiter-auth UX under services/frontend/app/demo/; unrelated style-only files excluded | `python scripts/rp5/validate_path_lock_pl_b14_0_frontend.py --diff HEAD~1..HEAD` | 8 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_0-CONFIG | exact_file_or_create | .env.example placeholders only; real secrets forbidden; compose files (docker-compose*.yml, docker-compose.demo.yml) are forbidden in B14.0; if a future task requires a compose change, a CHANGE_SCOPE decision must update this lock row and the relevant §10 task contract together in one patch before the compose file may be touched | `python scripts/rp5/validate_changed_files_against_path_locks.py --lock PL-B14_0-CONFIG --diff HEAD~1..HEAD` | 2 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_0-TESTS | exact_directory_with_predicate | tests/demo/test_b14_0_*.py and tests/rp5/fixtures/ | `python scripts/rp5/validate_path_lock_pl_b14_0_tests.py --diff HEAD~1..HEAD` | 12 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_0-SCRIPTS | exact_directory_with_predicate | scripts/rp5/validate_b14_0_*.py and scripts/rp5/fixtures/generate_fixture_validate_b14_0_*.py and scripts/rp5/smoke_b14_0_*.py | `python scripts/rp5/validate_path_lock_pl_b14_0_scripts.py --diff HEAD~1..HEAD` | 18 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_0-REPORTS | exact_directory_with_predicate | reports/rp5/b14_0_*.md; B-route reports remain frozen | `python scripts/rp5/validate_changed_files_against_path_locks.py --lock PL-B14_0-REPORTS --diff HEAD~1..HEAD` | 20 | UNAUTHORIZED_FILE_TOUCHED |

## 2. Constants and decision rules

```yaml
recruiter_realm: "asr-demo-recruiter"
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD
recruiter_credential_storage_policy: env-var only; no .env with real values committed; .env.example placeholders only
admin_realm_unchanged: true (admin HTTPBasic semantics frozen from B-route)
recruiter_protected_routes:
  - GET /demo/health
  - GET /demo/examples
  - POST /demo/run-cached
  - POST /demo/jobs
  - GET /demo/jobs/{job_id}
  - GET /demo/providers/assemblyai/status
recruiter_unauthenticated_response:
  status: 401
  www_authenticate: 'Basic realm="asr-demo-recruiter"'
  body_must_not_contain:
    - router_kind
    - router_version
    - routing_profile
    - selected_backend
    - allow_third_party
    - any value of Authorization header
    - any value of RECRUITER_PASSWORD
    - any value of ADMIN_STATS_PASSWORD
authenticated_health_payload_canonical: {"status":"ok"}
admin_and_recruiter_separation_rule:
  - RECRUITER_USERNAME must differ from ADMIN_STATS_USERNAME OR realm must differ AND route prefix must differ; realm differs by definition above
  - RECRUITER_PASSWORD value must not equal ADMIN_STATS_PASSWORD value at startup
  - admin routes (/admin/*) must continue to challenge with their own realm and accept only admin credentials
default_behavior_when_env_vars_unset:
  policy: refuse to start the demo public surface; emit B14_0_RECRUITER_AUTH_CONTRACT_FAILED at startup probe
forbidden_in_B14_0:
  - any change to libs/asr/router_runtime.py
  - any change to services/frontend/app/demo/types.ts router-field shape
  - any literal public URL
  - any Tailscale Funnel, serve, systemd, or public-network artifact
  - any datamove1 router handoff swap
  - any logging of Authorization header values or password material
```

### 2.1 Threshold audit

| Category | Status | Source or rationale |
|---|---|---|
| recruiter_credential_rotation_interval_numeric | HUMAN_ACTION_REQUIRED (HAR-B14_0-RECRUITER-CREDS-001) | rotation cadence is operator policy; agent has no authority to pick a numeric default |
| recruiter_initial_credential_values | HUMAN_ACTION_REQUIRED (HAR-B14_0-RECRUITER-CREDS-001) | secrets must originate outside the agent; supplied via host environment at deploy time |
| recruiter_401_response_timing_sla_ms | not_applicable_current_scope | B14.0 validates correctness of challenge response, not a latency SLA; latency budgets belong to a later soak phase |
| recruiter_failed_attempt_lockout_counter | not_applicable_current_scope | B14.0 does not introduce rate-limiting or lockout; lockout policy belongs to B14.1 public exposure layer |
| credential_leak_max_bytes_in_logs | not_applicable_current_scope_per_zero_tolerance | qualitative invariant: zero credential bytes in logs, error pages, structured-log fields, or challenge bodies; no numeric tolerance authorized |
| BR-02_health_payload_byte_tolerance | not_applicable_current_scope_per_exact_match | authenticated /demo/health body must equal {"status":"ok"} byte-for-byte; no tolerance |
| broute_validator_re_emission_runtime_budget_ms | not_applicable_current_scope | B14_0-07 re-runs BR-02..BR-07 validators for correctness, not for performance |

```yaml
threshold_audit_summary:
  numeric_thresholds_introduced_in_B14_0: 0
  HUMAN_ACTION_REQUIRED_entries: 2 (both routed through HAR-B14_0-RECRUITER-CREDS-001)
  not_applicable_current_scope_entries: 5
```

## 3. Marker registry

Every marker from orchestrator_plan §6 has a recovery packet in §11 below. Markers fire from validators or from session-open detection. Active markers block phase gate closure.

## 4. Linear transition table

| Current state | Condition | Marker on fail | Next on PASS | Next on FAIL | Report shape | Approval required |
|---|---|---|---|---|---|---|
| session-open | tracker readable and task matches B14.0 | TRACKER_MISSING or TRACKER_MISMATCH | B14_0-00 | stop | planning_report | yes |
| B14_0-00 | plan compiler passes for docs/plans/b14_0/ and path-lock validators exist | PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP | B14_0-01 | stop | execution_report | yes |
| B14_0-01 | recruiter auth contract recorded | B14_0_RECRUITER_AUTH_CONTRACT_FAILED | B14_0-02 | B14_0-01 fix | execution_report | yes |
| B14_0-02 | recruiter middleware enforces gate on public /demo/* | B14_0_AUTH_BYPASS_DETECTED | B14_0-03 | B14_0-02 fix | execution_report | yes |
| B14_0-03 | admin-recruiter separation invariants pass | B14_0_ADMIN_RECRUITER_CRED_CONFLATION | B14_0-04 | B14_0-03 fix | execution_report | yes |
| B14_0-04 | frontend recruiter-auth UX contract pass | B14_0_FRONTEND_AUTH_UX_DRIFT | B14_0-05 | B14_0-04 fix | execution_report | yes |
| B14_0-05 | manual end-to-end smoke under recruiter auth pass | B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED | B14_0-06 | B14_0-05 fix | execution_report | yes |
| B14_0-06 | no-credential-leak invariants pass | B14_0_CRED_LEAK_DETECTED | B14_0-07 | B14_0-06 fix | execution_report | yes |
| B14_0-07 | B-route compatibility under auth (BR-02..BR-07 sentinels re-emitted, BR-02 health payload preserved on authenticated path) | B14_0_BROUTE_REGRESSION_UNDER_AUTH or B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH | B14_0-08 | B14_0-07 fix | execution_report | yes |
| B14_0-08 | all gate predicates pass | any active B14_0_* marker | phase gate | first failed task | phase_gate_report | yes |
| any | unauthorized path changed | UNAUTHORIZED_FILE_TOUCHED | stop | stop | execution_report | yes |

## 5. Tracker schema and runtime state

```yaml
tracker_file: docs/progress/rp5_progress.yaml
expected_initial_state_at_first_B14_0_task:
  current_phase: B14.0
  current_task: B14_0-00
  last_completed_phase: B-route
  last_completed_task: BR-08
  markers: []
mutation_rules:
  - tracker_writes_only_in_recovery_or_closure: tasks do not write the tracker; closures and recovery do
  - task records appended in order with task_id, status, commit, files_changed, commands_run, key_outputs, marker, next_task per state_packet_schemas.yaml tracker_task_record
```

## 6. Phase gate predicates

Authority lives in orchestrator_plan.md §3. Agent emits a phase_gate_report after B14_0-08 PASS; the orchestrator records PHASE_APPROVE separately.

## 7. Final verification checklist

| Check id | Command essence | PASS sentinel | Artifact |
|---|---|---|---|
| FV-PLAN | validate_plan_compiles --plan-dir docs/plans/b14_0 | OK_PLAN_COMPILES | reports/rp5/b14_0_plan_compile.md |
| FV-AUTH-CONTRACT | validate_b14_0_recruiter_auth_contract | OK_B14_0_RECRUITER_AUTH_CONTRACT | reports/rp5/b14_0_recruiter_auth_contract.md |
| FV-AUTH-SEPARATION | validate_b14_0_auth_separation_invariants --base-url http://127.0.0.1:8001 | OK_B14_0_AUTH_SEPARATION | reports/rp5/b14_0_auth_separation_invariants.md |
| FV-HEALTH-UNDER-AUTH | validate_b14_0_health_payload_preserved_under_auth --base-url http://127.0.0.1:8001 | OK_B14_0_HEALTH_UNDER_AUTH | reports/rp5/b14_0_health_payload_under_auth.md |
| FV-FRONTEND-AUTH | validate_b14_0_frontend_auth_contract --types-file services/frontend/app/demo/types.ts | OK_B14_0_FRONTEND_AUTH | reports/rp5/b14_0_frontend_auth_contract.md |
| FV-MANUAL-WITH-AUTH | validate_b14_0_e2e_manual_smoke_with_auth --base-url http://127.0.0.1:8001 | OK_B14_0_MANUAL_SMOKE_WITH_AUTH | reports/rp5/b14_0_manual_smoke_with_auth.md |
| FV-NO-CRED-LEAK | validate_b14_0_no_credential_leak --base-url http://127.0.0.1:8001 | OK_B14_0_NO_CRED_LEAK | reports/rp5/b14_0_no_credential_leak.md |
| FV-BROUTE-COMPAT | validate_b14_0_broute_compatibility_under_auth --base-url http://127.0.0.1:8001 | OK_B14_0_BROUTE_COMPATIBILITY | reports/rp5/b14_0_broute_compatibility_under_auth.md |
| FV-FUTURE | validate_future_constraints --constraints reports/rp5/b14_0_future_constraints.md | OK_FUTURE_CONSTRAINTS | reports/rp5/b14_0_future_constraints.md |

## 8. Path lock contract

Closure command: `python scripts/rp5/validate_changed_files_against_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md`. Sentinel: OK_CHANGED_FILES_PATH_LOCKED. Failure marker: UNAUTHORIZED_FILE_TOUCHED. Result on unauthorized file: STOP_SCOPE_CONFLICT.

## 9. Validator contracts and fixtures

Each new validator has a paired fixture generator at scripts/rp5/fixtures/generate_fixture_validate_b14_0_<id>.py producing positive_and_negative fixtures with sha256 manifests. Generator sentinel format: OK_FIXTURE_VALIDATE_B14_0_<ID>. Failure marker matches the owning validator's marker per orchestrator_plan §6. Inherited validators (validate_plan_compiles, validate_changed_files_against_path_locks, validate_report_shape, validate_approval_packet, print_tracker_state, validate_future_constraints, validate_no_banned_phrases, validate_public_security_invariants) reuse the B-route scripts and fixture generators with --plan-dir docs/plans/b14_0/ where applicable.

validate_plan_compiles must_check contract is inherited from B-route §9, with the additional check `every_B14_0_task_next_state_exists`.

### 9.1 Fixture generator contracts for new B14.0 validators

| Generator id | Script path | Command | Output manifest | Sentinel | Owned marker |
|---|---|---|---|---|---|
| generate_fixture_validate_b14_0_recruiter_auth_contract | scripts/rp5/fixtures/generate_fixture_validate_b14_0_recruiter_auth_contract.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_recruiter_auth_contract.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_recruiter_auth_contract_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_recruiter_auth_contract_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_RECRUITER_AUTH_CONTRACT | B14_0_RECRUITER_AUTH_CONTRACT_FAILED |
| generate_fixture_validate_b14_0_auth_separation_invariants | scripts/rp5/fixtures/generate_fixture_validate_b14_0_auth_separation_invariants.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_auth_separation_invariants.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_auth_separation_invariants_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_auth_separation_invariants_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_AUTH_SEPARATION | B14_0_AUTH_BYPASS_DETECTED or B14_0_ADMIN_RECRUITER_CRED_CONFLATION |
| generate_fixture_validate_b14_0_health_payload_preserved_under_auth | scripts/rp5/fixtures/generate_fixture_validate_b14_0_health_payload_preserved_under_auth.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_health_payload_preserved_under_auth.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_health_payload_preserved_under_auth_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_health_payload_preserved_under_auth_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_HEALTH_UNDER_AUTH | B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH |
| generate_fixture_validate_b14_0_frontend_auth_contract | scripts/rp5/fixtures/generate_fixture_validate_b14_0_frontend_auth_contract.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_frontend_auth_contract.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_frontend_auth_contract_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_frontend_auth_contract_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_FRONTEND_AUTH | B14_0_FRONTEND_AUTH_UX_DRIFT |
| generate_fixture_validate_b14_0_e2e_manual_smoke_with_auth | scripts/rp5/fixtures/generate_fixture_validate_b14_0_e2e_manual_smoke_with_auth.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_e2e_manual_smoke_with_auth.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_e2e_manual_smoke_with_auth_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_e2e_manual_smoke_with_auth_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_MANUAL_SMOKE_WITH_AUTH | B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED |
| generate_fixture_validate_b14_0_no_credential_leak | scripts/rp5/fixtures/generate_fixture_validate_b14_0_no_credential_leak.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_no_credential_leak.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_no_credential_leak_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_no_credential_leak_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_NO_CRED_LEAK | B14_0_CRED_LEAK_DETECTED |
| generate_fixture_validate_b14_0_broute_compatibility_under_auth | scripts/rp5/fixtures/generate_fixture_validate_b14_0_broute_compatibility_under_auth.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_0_broute_compatibility_under_auth.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_0_broute_compatibility_under_auth_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_0_broute_compatibility_under_auth_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_0_BROUTE_COMPATIBILITY | B14_0_BROUTE_REGRESSION_UNDER_AUTH |

## 10. Task contracts

| Task | Preconditions | Action title | Deliverable | Validators | Done when | Stop |
|---|---|---|---|---|---|---|
| B14_0-00 | tracker readable; B-route APPROVED | plan compiler bootstrap and path-lock validator coverage for B14.0 locks | reports/rp5/b14_0_plan_compile.md | validate_plan_compiles, validate_changed_files_against_path_locks | OK_PLAN_COMPILES + OK_CHANGED_FILES_PATH_LOCKED | execution_report |
| B14_0-01 | B14_0-00 PASS | recruiter auth contract and credential-bootstrap policy (env-var only) | reports/rp5/b14_0_recruiter_auth_contract.md | validate_b14_0_recruiter_auth_contract | OK_B14_0_RECRUITER_AUTH_CONTRACT | execution_report |
| B14_0-02 | B14_0-01 PASS | recruiter HTTPBasic middleware on public /demo/* (preserving BR-02 health invariant on authenticated path) | services/api/app/* + reports/rp5/b14_0_*.md | validate_b14_0_recruiter_auth_contract (re-run), validate_b14_0_health_payload_preserved_under_auth | both OK sentinels | execution_report |
| B14_0-03 | B14_0-02 PASS | admin vs recruiter separation invariants (distinct realm, distinct cred values, distinct error paths) | reports/rp5/b14_0_auth_separation_invariants.md | validate_b14_0_auth_separation_invariants | OK_B14_0_AUTH_SEPARATION | execution_report |
| B14_0-04 | B14_0-03 PASS | frontend recruiter-auth UX and accessibility (no client-side credential persistence beyond session) | services/frontend/app/demo/* + reports/rp5/b14_0_frontend_auth_contract.md | validate_b14_0_frontend_auth_contract | OK_B14_0_FRONTEND_AUTH | execution_report |
| B14_0-05 | B14_0-04 PASS | manual end-to-end smoke under recruiter auth (positive and negative credentials) | reports/rp5/b14_0_manual_smoke_with_auth.md | validate_b14_0_e2e_manual_smoke_with_auth | OK_B14_0_MANUAL_SMOKE_WITH_AUTH | execution_report |
| B14_0-06 | B14_0-05 PASS | no-credential-leak invariants (logs, error pages, structured logs, challenge responses, header echo) | reports/rp5/b14_0_no_credential_leak.md | validate_b14_0_no_credential_leak | OK_B14_0_NO_CRED_LEAK | execution_report |
| B14_0-07 | B14_0-06 PASS | B-route compatibility re-verification under recruiter auth (BR-02..BR-07 sentinels re-emitted) | reports/rp5/b14_0_broute_compatibility_under_auth.md | validate_b14_0_broute_compatibility_under_auth | OK_B14_0_BROUTE_COMPATIBILITY | execution_report |
| B14_0-08 | B14_0-07 PASS | B14.0 phase gate final-verification checklist + B14.0 future-constraint records for FC-B14-1-FUNNEL, FC-B15-MULTI-NETWORK, FC-HANDOFF-DATAMOVE1, FC-BROUTE-FROZEN | reports/rp5/b14_0_phase_gate.md and reports/rp5/b14_0_future_constraints.md | every validator from §7 plus validate_future_constraints | every OK sentinel observed and no marker active | phase_gate_report; stop for PHASE_APPROVE |

Implementation detail beyond the action-title and deliverable-set is owned by the per-task planning_report at execution time.

## 11. Recovery packets

Every marker in §3 maps to exactly one recovery packet. Each packet defines: diagnosis_command, allowed_files_to_inspect, allowed_files_to_modify, retry_limit, next_state_on_recovered, next_state_on_retry_exhausted. Where the B-route plan defined an identical-named packet (PLAN_CONFLICT, TRACKER_*, REPORT_*, APPROVAL_*, EXECUTION_*, PATH_LOCK_*, VALIDATOR_*, RECOVERY_*, UNAUTHORIZED_*, HUMAN_*, FUTURE_*, PUBLIC_SECURITY_*), this plan inherits the B-route packet semantics with the diagnosis_command rewritten to use docs/plans/b14_0/ and the B14.0 validators where applicable.

| Packet id | Marker | Diagnosis command | Allowed inspect | Allowed modify | Retry | Recovered next | Exhausted next |
|---|---|---|---|---|---:|---|---|
| RP-PLAN-CONFLICT | PLAN_CONFLICT | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/b14_0 --out reports/rp5/b14_0_plan_conflict.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_0-00 | CHANGE_SCOPE |
| RP-TRACKER-MISSING | TRACKER_MISSING | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b14_0_tracker_missing.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_0-00 | CHANGE_SCOPE |
| RP-TRACKER-MISMATCH | TRACKER_MISMATCH | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b14_0_tracker_mismatch.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_0-00 | CHANGE_SCOPE |
| RP-REPORT-SCHEMA-INVALID | REPORT_SCHEMA_INVALID | `python scripts/rp5/validate_report_shape.py --schemas docs/plans/b14_0/state_packet_schemas.yaml --report-from-tracker latest_context --out reports/rp5/b14_0_report_schema_invalid.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-APPROVAL-PACKET-MALFORMED | APPROVAL_PACKET_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_approval_packet --out reports/rp5/b14_0_approval_packet_malformed.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-EXECUTION-RAIL-GAP | EXECUTION_RAIL_GAP | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/b14_0 --out reports/rp5/b14_0_execution_rail_gap.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PATH-LOCK-TOO-BROAD | PATH_LOCK_TOO_BROAD | `python scripts/rp5/validate_changed_files_against_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b14_0_path_lock_too_broad.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-VALIDATOR-MATERIALIZATION-GAP | VALIDATOR_MATERIALIZATION_GAP | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/b14_0 --out reports/rp5/b14_0_validator_materialization_gap.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-RECOVERY-PACKET-GAP | RECOVERY_PACKET_GAP | `python scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/b14_0 --out reports/rp5/b14_0_recovery_packet_gap.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-UNAUTHORIZED-FILE-TOUCHED | UNAUTHORIZED_FILE_TOUCHED | `python scripts/rp5/validate_changed_files_against_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b14_0_unauthorized_file_touched.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | STOP_SCOPE_CONFLICT |
| RP-HUMAN-ACTION-REQUIRED | HUMAN_ACTION_REQUIRED | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/b14_0_pending_human_action.md` | docs/plans/b14_0, tracker, reports/rp5 | none until human_action_result is recorded | 0 | same task | CHANGE_SCOPE |
| RP-FUTURE-CONSTRAINT-REGRESSION | FUTURE_CONSTRAINT_REGRESSION | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/b14_0_future_constraints.md --out reports/rp5/b14_0_future_constraint_regression.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PUBLIC-SECURITY-REGRESSION | PUBLIC_SECURITY_REGRESSION | `python scripts/rp5/validate_public_security_invariants.py --base-url http://127.0.0.1:8001 --out reports/rp5/b14_0_public_security_regression.md` | docs/plans/b14_0, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-RECRUITER-AUTH-CONTRACT-FAILED | B14_0_RECRUITER_AUTH_CONTRACT_FAILED | `python scripts/rp5/validate_b14_0_recruiter_auth_contract.py --verbose --out reports/rp5/b14_0_recruiter_auth_failure.md` | docs/plans/b14_0, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-AUTH-BYPASS-DETECTED | B14_0_AUTH_BYPASS_DETECTED | `python scripts/rp5/validate_b14_0_auth_separation_invariants.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_0_auth_bypass.md` | docs/plans/b14_0, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-HEALTH-PAYLOAD-REGRESSION | B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH | `python scripts/rp5/validate_b14_0_health_payload_preserved_under_auth.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_0_health_regression.md` | docs/plans/b14_0, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-ADMIN-RECRUITER-CRED-CONFLATION | B14_0_ADMIN_RECRUITER_CRED_CONFLATION | `python scripts/rp5/validate_b14_0_auth_separation_invariants.py --component cred_separation --verbose --out reports/rp5/b14_0_cred_conflation.md` | docs/plans/b14_0, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-FRONTEND-AUTH-UX-DRIFT | B14_0_FRONTEND_AUTH_UX_DRIFT | `python scripts/rp5/validate_b14_0_frontend_auth_contract.py --types-file services/frontend/app/demo/types.ts --verbose --out reports/rp5/b14_0_frontend_auth_drift.md` | docs/plans/b14_0, tracker, reports/rp5, services/frontend | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-MANUAL-SMOKE-WITH-AUTH-FAILED | B14_0_MANUAL_SMOKE_WITH_AUTH_FAILED | `python scripts/rp5/validate_b14_0_e2e_manual_smoke_with_auth.py --base-url http://127.0.0.1:8001 --debug --out reports/rp5/b14_0_manual_smoke_failure.md` | docs/plans/b14_0, tracker, reports/rp5, services | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-CRED-LEAK-DETECTED | B14_0_CRED_LEAK_DETECTED | `python scripts/rp5/validate_b14_0_no_credential_leak.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_0_cred_leak.md` | docs/plans/b14_0, tracker, reports/rp5, services/api/app, runtime logs under /tmp | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_0-BROUTE-REGRESSION-UNDER-AUTH | B14_0_BROUTE_REGRESSION_UNDER_AUTH | `python scripts/rp5/validate_b14_0_broute_compatibility_under_auth.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_0_broute_regression.md` | docs/plans/b14_0, tracker, reports/rp5, services | same task owned files only | 1 | same task | CHANGE_SCOPE |

## 12. Security and forbidden scope

Forbidden in B14.0:

| Scope | Reason | Marker |
|---|---|---|
| Tailscale Funnel, serve, public URL, systemd, public-network artifact | belongs to B14.1 | FUTURE_CONSTRAINT_REGRESSION |
| public-network smoke claim from local B14.0 tests | belongs to B15 | FUTURE_CONSTRAINT_REGRESSION |
| router schema or cache-key schema change | belongs to B-handoff or frozen by B-route | FUTURE_CONSTRAINT_REGRESSION |
| literal public URL commit | pre-plan forbids without explicit human approval | PUBLIC_SECURITY_REGRESSION |
| committing real RECRUITER_PASSWORD or RECRUITER_USERNAME | secret leak | PUBLIC_SECURITY_REGRESSION |
| logging Authorization header value or password | secret leak | B14_0_CRED_LEAK_DETECTED |
| editing docs/plans/broute/ | B-route frozen post-approval | UNAUTHORIZED_FILE_TOUCHED |
| editing libs/asr/router_runtime.py | B-route schema frozen | UNAUTHORIZED_FILE_TOUCHED |
| editing services/frontend/app/demo/types.ts router-field shape | BR-04 contract frozen | UNAUTHORIZED_FILE_TOUCHED |

## 13. Report skeletons

Report shapes are defined in state_packet_schemas.yaml. The B14.0 plan reuses planning_report, execution_report, phase_gate_report, approval_packet, and supplemental_evidence_report unchanged from the B-route schema. New B14.0-specific records (recruiter_auth_invariant_record, credential_storage_policy_record) are defined in state_packet_schemas.yaml.

## 14. Banned phrases and no-improvisation scan

Banned phrases registry is inherited from the B-route agent_plan §14 verbatim. Scan command:

```bash
grep -nE '(as needed|as appropriate|as required|if already present|if present|where appropriate|best practices|obvious|TBD|TODO without a marker|discovered|discover |judgment|free-form|free form)' docs/plans/b14_0/agent_plan.md docs/plans/b14_0/orchestrator_plan.md | grep -v 'section_14\|banned_phrases\|forbidden_orchestrator_outputs'
```

Expected: zero rows.

## 15. Human action requests

The HAR transport (CHANGE_SCOPE_with_human_action_request_id) is inherited from B-route. One HAR is pre-declared because recruiter credentials must originate outside the agent's authority.

| HAR id | Trigger marker | Missing inputs | Blocking scope | Required human result shape |
|---|---|---|---|---|
| HAR-B14_0-RECRUITER-CREDS-001 | HUMAN_ACTION_REQUIRED | recruiter_initial_username, recruiter_initial_password, recruiter_credential_rotation_cadence | resolved before B14_0-02 closure | operator provides values via host environment (or host systemd service env); values are recorded only by reference (env-var-name and rotation-cadence string), never by value, in tracker supplemental_evidence and in the HAR result block; explicit_NA is accepted only for the rotation_cadence field if the operator declares a manual-rotation-on-incident policy |

```yaml
HAR-B14_0-RECRUITER-CREDS-001:
  status: pre_declared_unresolved
  marker: HUMAN_ACTION_REQUIRED
  missing_inputs:
    - recruiter_initial_username
    - recruiter_initial_password
    - recruiter_credential_rotation_cadence
  why_human_only: secrets must originate outside the agent; the agent has no authority to invent recruiter credentials or pick a rotation policy
  allowed_values_or_schema:
    recruiter_initial_username: ASCII string of length 1..64, not equal to ADMIN_STATS_USERNAME value
    recruiter_initial_password: ASCII string of length 16..128, entropy ≥ 96 bits per operator policy, not equal to ADMIN_STATS_PASSWORD value
    recruiter_credential_rotation_cadence: ISO-8601 duration or the literal "manual-rotation-on-incident"
  blocks: B14_0-02 closure
  created_by_task: B14.0 plan authoring (this draft)
  next_state_until_result: agent waits; no B14.0-02 execution begins
  forbidden_agent_action: inventing credential values, committing real credentials, logging credentials, storing credentials in committed files
  result_expected_at: before APPROVE_PLAN for B14_0-02
  result_recording_policy:
    - the human_action_result captures field names and the rotation-policy string only
    - actual credential values are NEVER written into tracker, approval packets, or any committed file
    - tracker records only "supplied: true" per field and the rotation policy string
```

## 16. Authoring status

```yaml
authoring_status: APPROVED_FOR_EXECUTION
accepted_plan_revision_commit: 8a049d00bdfec5b97c416f3135644ecd78f14bd8
plan_approval_packet_path: reports/rp5/b14_0_plan_approval_packet.yaml
tracker_advanced_to: current_phase=B14.0, current_task=B14_0-00, expected_next_task=B14_0-00
no_B14_0_implementation_task_starts_until:
  - an APPROVE_PLAN decision for the first B14.0 task (B14_0-00) is recorded by the orchestrator after this plan-package approval
  - HAR-B14_0-RECRUITER-CREDS-001 is resolved before B14_0-02 closure (does not block B14_0-00 or B14_0-01)
```

## 17. Adversarial stress-replay

| Scenario | initial_state | triggering_event | expected_marker | expected_next_state | report_shape | plan_sections_used | result |
|---|---|---|---|---|---|---|---|
| shared-credential conflation | RECRUITER_USERNAME == ADMIN_STATS_USERNAME or RECRUITER_PASSWORD == ADMIN_STATS_PASSWORD at startup | B14_0-03 closure attempt | B14_0_ADMIN_RECRUITER_CRED_CONFLATION | B14_0-03 fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_0_auth_separation_invariants emits FAIL on shared-credential fixture |
| 401 leaks router field | recruiter 401 challenge body contains router_kind | B14_0-02 or B14_0-06 closure | B14_0_AUTH_BYPASS_DETECTED or B14_0_CRED_LEAK_DETECTED depending on origin | first failing task fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_0_recruiter_auth_contract forbidden_response_body_substrings list rejects the fixture; validate_b14_0_no_credential_leak supplements detection |
| password logged | structured log line includes RECRUITER_PASSWORD value | B14_0-06 closure | B14_0_CRED_LEAK_DETECTED | B14_0-06 fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_0_no_credential_leak scans log scratch with credential needles and emits FAIL |
| admin-realm collision | /demo/* recruiter route challenges with realm="Restricted" (admin realm) | B14_0-02 or B14_0-03 closure | B14_0_AUTH_BYPASS_DETECTED | first failing task fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_0_recruiter_auth_contract pins WWW-Authenticate to Basic realm="asr-demo-recruiter"; mismatch fails |
| Funnel string introduced | services/ or scripts/ contains "tailscale funnel" or "funnel serve" literal | any B14_0-NN closure | FUTURE_CONSTRAINT_REGRESSION | CHANGE_SCOPE | execution_report | §3, §4, §11, §12, orchestrator_plan §3 | PASS evidence: validate_future_constraints scans active plan and committed sources for forbidden Funnel substrings |
| public URL literal | committed file contains a non-loopback http URL | any B14_0-NN closure | PUBLIC_SECURITY_REGRESSION | FIX_BEFORE_CLOSE | execution_report | §3, §4, §11, §12, orchestrator_plan §7 | PASS evidence: validate_public_security_invariants and validate_no_banned_phrases scan-based detection |
| router-runtime edit | libs/asr/router_runtime.py modified | any B14_0-NN commit | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | execution_report | §1, §3, §8, §11, §12 | PASS evidence: path lock validator rejects file outside B14.0 lock set; FC-BROUTE-FROZEN preservation row in orchestrator_plan §3 also fires |
| frontend types router-field shape edit | services/frontend/app/demo/types.ts RouterFields shape changed | B14_0-04 closure | B14_0_BROUTE_REGRESSION_UNDER_AUTH or UNAUTHORIZED_FILE_TOUCHED | B14_0-04 fix or STOP_SCOPE_CONFLICT | execution_report | §1, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_0_broute_compatibility_under_auth compares BR-04 frontend-backend contract output; mismatch fails |

```yaml
stress_replay_summary:
  scenarios_enumerated: 8
  every_scenario_maps_to_existing_marker: true
  every_scenario_maps_to_existing_recovery_packet: true (markers above all appear in §3 and §11)
```
