# agent_plan.md

Plan state: DRAFT_NOT_APPROVED_FOR_EXECUTION
Project scope: B14.1 public exposure via Tailscale Funnel layered on top of the B14.0 recruiter HTTPBasic application-layer gate, with deterministic stable-named exposure semantics. Future phases (B15 multi-network smoke, B-handoff datamove1 router swap) are preserved but not executable in this plan. B-route and B14.0 deliverables are frozen.
Authority: executable task order, exact commands, validators, fixture generators, marker registry, recovery packets, transition table, tracker mutation rules, path locks, and report skeleton references.

## 0. Manifest and entity registry

```yaml
project: b14_1_public_exposure_application_gated
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
starting_state:
  last_completed_phase: B14.0
  current_phase: B14.1_PENDING_ORCHESTRATOR_INSTRUCTION
  current_task: B14.1_PENDING_ORCHESTRATOR_INSTRUCTION
canonical_output_files:
  - docs/plans/b14_1/orchestrator_plan.md
  - docs/plans/b14_1/agent_plan.md
  - docs/plans/b14_1/state_packet_schemas.yaml
phases:
  - B14.1
  - B15_future_constraint
  - B-handoff_future_constraint
tasks:
  - B14_1-00
  - B14_1-01
  - B14_1-02
  - B14_1-03
  - B14_1-04
  - B14_1-05
  - B14_1-06
  - B14_1-07
  - B14_1-08
markers:
  - PLAN_CONFLICT
  - TRACKER_MISSING
  - TRACKER_MISMATCH
  - REPORT_SCHEMA_INVALID
  - APPROVAL_PACKET_MALFORMED
  - HUMAN_ACTION_REQUEST_MALFORMED
  - EXECUTION_RAIL_GAP
  - PATH_LOCK_TOO_BROAD
  - VALIDATOR_MATERIALIZATION_GAP
  - RECOVERY_PACKET_GAP
  - UNAUTHORIZED_FILE_TOUCHED
  - HUMAN_ACTION_REQUIRED
  - FUTURE_CONSTRAINT_REGRESSION
  - PUBLIC_SECURITY_REGRESSION
  - B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED
  - B14_1_NETWORK_TRUST_AUTHORITY_DETECTED
  - B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE
  - B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE
  - B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED
  - B14_1_EPHEMERAL_URL_SUCCESS_CLAIM
  - B14_1_PUBLIC_URL_LITERAL_COMMITTED
  - B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED
  - B14_1_TUNNEL_SECRET_COMMITTED
  - B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE
  - B14_1_LOCAL_BYPASS_UNJUSTIFIED
validators:
  - validate_b14_1_plan_compile
  - validate_b14_1_path_locks
  - validate_b14_1_exposure_state_record
  - validate_b14_1_application_layer_gate_invariants
  - validate_b14_1_no_network_trust_authority
  - validate_b14_1_recruiter_gate_preserved_under_public_exposure
  - validate_b14_1_health_payload_preserved_under_public_exposure
  - validate_b14_1_openapi_docs_visibility
  - validate_b14_1_no_public_url_or_hostname_literal
  - validate_b14_1_no_tunnel_secret_leak
  - validate_b14_1_local_bypass_justification
  - validate_b14_1_broute_compatibility_under_public_exposure
  - validate_future_constraints
  - validate_no_banned_phrases
  - validate_report_shape
  - validate_approval_packet
  - print_tracker_state
inherited_validators_context_only:
  - validate_b14_0_recruiter_auth_contract
  - validate_b14_0_auth_separation_invariants
  - validate_b14_0_no_credential_leak
  - validate_public_security_invariants
artifacts:
  - reports/rp5/b14_1_plan_compile.md
  - reports/rp5/b14_1_exposure_state_record.md
  - reports/rp5/b14_1_application_layer_gate_invariants.md
  - reports/rp5/b14_1_no_network_trust_authority.md
  - reports/rp5/b14_1_recruiter_gate_preserved_under_public_exposure.md
  - reports/rp5/b14_1_health_payload_preserved_under_public_exposure.md
  - reports/rp5/b14_1_openapi_docs_visibility.md
  - reports/rp5/b14_1_no_public_url_or_hostname_literal.md
  - reports/rp5/b14_1_no_tunnel_secret_leak.md
  - reports/rp5/b14_1_local_bypass_justification.md
  - reports/rp5/b14_1_broute_compatibility_under_public_exposure.md
  - reports/rp5/b14_1_future_constraints.md
  - reports/rp5/b14_1_phase_gate.md
claims:
  - application_layer_recruiter_gate_is_sole_authority_under_public_exposure
  - no_application_layer_authority_decision_keyed_on_network_origin
  - BR-02_health_invariant_preserved_under_public_exposure
  - openapi_and_docs_unmounted_when_PUBLIC_DEMO_EXPOSURE_true_unless_admin_only_exception
  - exposure_state_is_stable_named_or_explicit_blocker_recorded
  - no_recruiter_credential_no_admin_credential_no_Tailscale_auth_key_no_Cloudflare_token_committed
  - no_public_URL_no_stable_hostname_literal_committed
  - BR-01_through_BR-08_and_B14_0-00_through_B14_0-08_remain_frozen
  - future_constraints_preserved
```

## 1. Branch, repository layout, and path locks

```yaml
repository:
  root: /home/gbibbo/code/asr_enhancement
  branch: feature/demo-runtime-rp5-v1
  runtime_preserved:
    - all B-route deliverables and validators
    - all B14.0 deliverables and validators (recruiter HTTPBasic gate, BR-02 health invariant under auth, admin/recruiter separation)
    - libs/asr/router_runtime.py (frozen schema)
    - services/frontend/app/demo/types.ts router-field shape (frozen at B14_0-04 and reconfirmed at B14_0-07)
    - structured JSON logs and log rotation policy
    - SQLite job and cache tables
```

| Lock id | Type | Allowed components | Validator command | Max files | Marker on violation |
|---|---|---|---|---:|---|
| PL-B14_1-API-DEMO | exact_directory_with_predicate | application-layer exposure-flag plumbing and OpenAPI/docs visibility wiring in services/api/app/; recruiter middleware (B14.0) may be inspected but not modified except where the predicate explicitly allows | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-API-DEMO --diff HEAD~1..HEAD` | 6 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_1-FRONTEND | exact_directory_with_predicate | exposure-state UI surface under services/frontend/app/demo/ (visibility only, no router-field shape edits); unrelated style-only files excluded | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-FRONTEND --diff HEAD~1..HEAD` | 4 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_1-CONFIG | exact_file_or_create | .env.example placeholders only; real secrets forbidden; compose files (docker-compose*.yml, docker-compose.demo.yml) are forbidden in B14.1; if a future task requires a compose change, a CHANGE_SCOPE decision must update this lock row and the relevant §10 task contract together in one patch before the compose file may be touched | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-CONFIG --diff HEAD~1..HEAD` | 2 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_1-TESTS | exact_directory_with_predicate | tests/demo/test_b14_1_*.py and tests/rp5/fixtures/ | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-TESTS --diff HEAD~1..HEAD` | 12 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_1-SCRIPTS | exact_directory_with_predicate | scripts/rp5/validate_b14_1_*.py and scripts/rp5/fixtures/generate_fixture_validate_b14_1_*.py and scripts/rp5/smoke_b14_1_*.py | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-SCRIPTS --diff HEAD~1..HEAD` | 18 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_1-REPORTS | exact_directory_with_predicate | reports/rp5/b14_1_*.md; B-route and B14.0 reports remain frozen | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-REPORTS --diff HEAD~1..HEAD` | 20 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_1-TUNNEL-TEMPLATE | exact_file_or_create | infra/tunnel/funnel_config.template.yaml or infra/tunnel/funnel_config.template.json placeholder template only; the template carries no real Tailscale auth-key, no Cloudflare token, no stable hostname literal, no public URL literal; the real tunnel configuration lives host-only and is referenced by env-var name only | `python scripts/rp5/validate_b14_1_path_locks.py --lock PL-B14_1-TUNNEL-TEMPLATE --diff HEAD~1..HEAD` | 1 | UNAUTHORIZED_FILE_TOUCHED |

## 2. Constants and decision rules

```yaml
public_exposure_flag_env: PUBLIC_DEMO_EXPOSURE
public_exposure_flag_allowed_values: [false, true]
recruiter_realm: "asr-demo-recruiter"
recruiter_username_env: RECRUITER_USERNAME
recruiter_password_env: RECRUITER_PASSWORD
recruiter_credential_storage_policy: env-var only; no .env with real values committed; .env.example placeholders only
admin_realm_unchanged: true (admin HTTPBasic semantics frozen from B-route and B14.0)
tailscale_auth_key_env_reference: TAILSCALE_AUTHKEY
tailscale_auth_key_storage_policy: host-only env or systemd service env; never committed; never logged; never echoed by any validator
stable_hostname_env_reference: PUBLIC_DEMO_STABLE_HOSTNAME
stable_hostname_storage_policy: host env or HAR result by reference; never committed as a literal; never echoed by any validator
public_url_literal_policy: forbidden in any committed file
ephemeral_url_policy: never a success-claim source; ephemeral URLs may appear in local-only smoke evidence files that are removed before final commit
loopback_binding_under_public_exposure_false: required
application_layer_authority_under_public_exposure_true:
  - recruiter HTTPBasic gate is the sole authority for public /demo/* access
  - no application-layer authority decision may be keyed on network origin, client IP, source interface, Tailscale identity, X-Forwarded-For, or any header that the public surface cannot independently authenticate
  - the funnel layer terminates TLS upstream of FastAPI; FastAPI must still see and enforce the same recruiter HTTPBasic challenge end-to-end
openapi_docs_visibility:
  PUBLIC_DEMO_EXPOSURE_false:
    openapi: mounted_unprotected_allowed
    docs: mounted_unprotected_allowed
    redoc: mounted_unprotected_allowed
  PUBLIC_DEMO_EXPOSURE_true:
    openapi: unmounted_required_unless_admin_only_exception
    docs: unmounted_required_unless_admin_only_exception
    redoc: unmounted_required_unless_admin_only_exception
  narrow_admin_only_exception_definition: the exception, if planned, must mount /admin/openapi behind the existing admin HTTPBasic realm with no recruiter access; its planning record must appear in the b14_1_openapi_docs_visibility.md report and reference the same admin HTTPBasic plumbing already validated by B14_0-03
local_bypass_under_public_exposure_false:
  allowed_only_if: paired with an automated test that asserts the bypass is disabled when PUBLIC_DEMO_EXPOSURE=true
  forbidden_otherwise: B14_1_LOCAL_BYPASS_UNJUSTIFIED
forbidden_in_B14_1:
  - any change to libs/asr/router_runtime.py
  - any change to services/frontend/app/demo/types.ts router-field shape
  - any literal public URL committed
  - any literal stable hostname committed
  - any Tailscale auth-key, Cloudflare token, recruiter password, or admin password committed
  - any logging of Authorization header values or password or auth-key material
  - any datamove1 router handoff swap
  - any multi-network public smoke claim made from a single B14.1 host run
  - any systemd unit installation step inside B14.1 (the tunnel run-as-service surface is recorded as a HAR; the unit file content can be authored as a template at PL-B14_1-TUNNEL-TEMPLATE but the install action is host-only, deferred to the operator, and not a B14.1 closure deliverable)
  - any claim of success keyed on an ephemeral URL alone
```

### 2.1 Threshold audit

| Category | Status | Source or rationale |
|---|---|---|
| stable_hostname_resolution_timeout_seconds | not_applicable_current_scope | B14.1 validates correctness of stable-named exposure semantics, not network timing |
| tunnel_restart_backoff_seconds_numeric | HUMAN_ACTION_REQUIRED (HAR-B14_1-FUNNEL-CAPABILITY-001) | host-side cloudflared or tailscale restart policy belongs to operator host configuration |
| tailscale_funnel_capability_grant_method | HUMAN_ACTION_REQUIRED (HAR-B14_1-FUNNEL-CAPABILITY-001) | enabling Funnel on the Tailscale account requires operator action outside the agent's authority |
| stable_hostname_string_value | HUMAN_ACTION_REQUIRED (HAR-B14_1-STABLE-HOSTNAME-001) | the literal hostname is operator-owned; agent records only the env-var name and a supplied-by-reference flag |
| recruiter_401_response_under_public_exposure_latency_sla_ms | not_applicable_current_scope | B14.1 validates correctness, not latency budgets |
| openapi_or_docs_admin_only_exception_decision | not_applicable_current_scope_unless_orchestrator_enacts_exception | B14.1 default is unmounted under PUBLIC_DEMO_EXPOSURE=true; the admin-only exception is opt-in and recorded in the b14_1_openapi_docs_visibility.md report |
| local_bypass_count | not_applicable_current_scope_unless_any_bypass_is_introduced | the default plan introduces zero local bypasses; if any is introduced, validate_b14_1_local_bypass_justification enforces the paired-test rule |
| b14_1_phase_runtime_budget_minutes | not_applicable_current_scope | B14.1 closure is gated on correctness sentinels, not on wall-clock budget |

```yaml
threshold_audit_summary:
  numeric_thresholds_introduced_in_B14_1: 0
  HUMAN_ACTION_REQUIRED_entries: 3 (HAR-B14_1-FUNNEL-CAPABILITY-001 covers two; HAR-B14_1-STABLE-HOSTNAME-001 covers one)
  not_applicable_current_scope_entries: 5
```

## 3. Marker registry

Every marker from orchestrator_plan §6 has a recovery packet in §11 below. Markers fire from validators or from session-open detection. Active markers block phase gate closure.

## 4. Linear transition table

| Current state | Condition | Marker on fail | Next on PASS | Next on FAIL | Report shape | Approval required |
|---|---|---|---|---|---|---|
| session-open | tracker readable; current_task is B14.1 entry; B14.0 PHASE_APPROVED predicates hold | TRACKER_MISSING or TRACKER_MISMATCH | B14_1-00 | stop | planning_report | yes |
| B14_1-00 | plan compiler passes for docs/plans/b14_1/ and B14.1 wrappers exist | PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP | B14_1-01 | stop | execution_report | yes |
| B14_1-01 | exposure_state_record recorded with PUBLIC_DEMO_EXPOSURE flag plumbing wired application-side; flag default is PUBLIC_DEMO_EXPOSURE=false; no public URL or stable hostname committed; HAR-B14_1-STABLE-HOSTNAME-001 and HAR-B14_1-FUNNEL-CAPABILITY-001 declared | B14_1_PUBLIC_URL_LITERAL_COMMITTED or B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED or HUMAN_ACTION_REQUIRED | B14_1-02 | B14_1-01 fix | execution_report | yes |
| B14_1-02 | application-layer gate invariants hold under PUBLIC_DEMO_EXPOSURE=true (recruiter HTTPBasic remains sole authority; no network-trust decision) | B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED or B14_1_NETWORK_TRUST_AUTHORITY_DETECTED | B14_1-03 | B14_1-02 fix | execution_report | yes |
| B14_1-03 | recruiter gate preserved end-to-end under public exposure (BR-02 health canonical; auth separation preserved; no openapi/docs leak) | B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE or B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE or B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED | B14_1-04 | B14_1-03 fix | execution_report | yes |
| B14_1-04 | tunnel configuration template authored at PL-B14_1-TUNNEL-TEMPLATE with placeholders only; no real Tailscale auth-key, no Cloudflare token, no stable hostname literal, no public URL literal | B14_1_TUNNEL_SECRET_COMMITTED or B14_1_PUBLIC_URL_LITERAL_COMMITTED or B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED | B14_1-05 | B14_1-04 fix | execution_report | yes |
| B14_1-05 | local bypass justification recorded; either zero bypasses, or every bypass is paired with a test that asserts the bypass is disabled when PUBLIC_DEMO_EXPOSURE=true | B14_1_LOCAL_BYPASS_UNJUSTIFIED | B14_1-06 | B14_1-05 fix | execution_report | yes |
| B14_1-06 | no-tunnel-secret-leak invariants pass (logs, error pages, structured logs, openapi/docs scratch); committed scan finds no auth-key, no token, no hostname literal | B14_1_TUNNEL_SECRET_COMMITTED or PUBLIC_SECURITY_REGRESSION | B14_1-07 | B14_1-06 fix | execution_report | yes |
| B14_1-07 | B-route and B14.0 compatibility under public exposure (BR-02..BR-07 sentinels re-emitted under public-exposure flag; B14_0-02..B14_0-07 sentinels re-emitted under public-exposure flag; frozen fingerprints unchanged) | B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE | B14_1-08 | B14_1-07 fix | execution_report | yes |
| B14_1-08 | all gate predicates pass; exposure_state_record asserts application_gated_stable_hostname or an explicit blocker is active | any active B14_1_* marker or B14_1_EPHEMERAL_URL_SUCCESS_CLAIM | phase gate | first failed task | phase_gate_report | yes |
| any | unauthorized path changed | UNAUTHORIZED_FILE_TOUCHED | stop | stop | execution_report | yes |

## 5. Tracker schema and runtime state

```yaml
tracker_file: docs/progress/rp5_progress.yaml
expected_initial_state_at_first_B14_1_task:
  current_phase: B14.1
  current_task: B14_1-00
  last_completed_phase: B14.0
  last_completed_task: B14_0-08
  markers: []
mutation_rules:
  - tracker_writes_only_in_recovery_or_closure: tasks do not write the tracker; closures and recovery do
  - task records appended in order with task_id, status, commit, files_changed, commands_run, key_outputs, marker, next_task per state_packet_schemas.yaml tracker_task_record
  - plan-authoring approval, once granted by the orchestrator, is recorded under tracker.plan_authoring_approvals.B14.1 with status APPROVED_FOR_EXECUTION, accepted_plan_revision_commit set, and approval_packet_path set
```

## 6. Phase gate predicates

Authority lives in orchestrator_plan.md §3. Agent emits a phase_gate_report after B14_1-08 PASS; the orchestrator records PHASE_APPROVE separately.

## 7. Final verification checklist

| Check id | Command essence | PASS sentinel | Artifact |
|---|---|---|---|
| FV-PLAN | validate_b14_1_plan_compile --plan-dir docs/plans/b14_1 | OK_PLAN_COMPILES | reports/rp5/b14_1_plan_compile.md |
| FV-EXPOSURE-STATE | validate_b14_1_exposure_state_record --record reports/rp5/b14_1_exposure_state_record.md | OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED | reports/rp5/b14_1_exposure_state_record.md |
| FV-APP-GATE | validate_b14_1_application_layer_gate_invariants --base-url http://127.0.0.1:8001 | OK_B14_1_APPLICATION_LAYER_GATE | reports/rp5/b14_1_application_layer_gate_invariants.md |
| FV-NO-NETWORK-TRUST | validate_b14_1_no_network_trust_authority --base-url http://127.0.0.1:8001 | OK_B14_1_NO_NETWORK_TRUST_AUTHORITY | reports/rp5/b14_1_no_network_trust_authority.md |
| FV-RECRUITER-PRESERVED | validate_b14_1_recruiter_gate_preserved_under_public_exposure --base-url http://127.0.0.1:8001 | OK_B14_1_RECRUITER_GATE_PRESERVED | reports/rp5/b14_1_recruiter_gate_preserved_under_public_exposure.md |
| FV-HEALTH-UNDER-PUBLIC | validate_b14_1_health_payload_preserved_under_public_exposure --base-url http://127.0.0.1:8001 | OK_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE | reports/rp5/b14_1_health_payload_preserved_under_public_exposure.md |
| FV-OPENAPI-DOCS | validate_b14_1_openapi_docs_visibility --base-url http://127.0.0.1:8001 | OK_B14_1_OPENAPI_DOCS_OFF | reports/rp5/b14_1_openapi_docs_visibility.md |
| FV-NO-PUBLIC-URL | validate_b14_1_no_public_url_or_hostname_literal --root . | OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | reports/rp5/b14_1_no_public_url_or_hostname_literal.md |
| FV-NO-TUNNEL-SECRET | validate_b14_1_no_tunnel_secret_leak --base-url http://127.0.0.1:8001 | OK_B14_1_NO_TUNNEL_SECRET_LEAK | reports/rp5/b14_1_no_tunnel_secret_leak.md |
| FV-LOCAL-BYPASS | validate_b14_1_local_bypass_justification --root . | OK_B14_1_LOCAL_BYPASS_JUSTIFIED | reports/rp5/b14_1_local_bypass_justification.md |
| FV-BROUTE-COMPAT-UNDER-PUBLIC | validate_b14_1_broute_compatibility_under_public_exposure --base-url http://127.0.0.1:8001 | OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | reports/rp5/b14_1_broute_compatibility_under_public_exposure.md |
| FV-FUTURE | validate_future_constraints --constraints reports/rp5/b14_1_future_constraints.md | OK_FUTURE_CONSTRAINTS | reports/rp5/b14_1_future_constraints.md |

## 8. Path lock contract

Closure command: `python scripts/rp5/validate_b14_1_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md`. Sentinel: OK_CHANGED_FILES_PATH_LOCKED. Failure marker: UNAUTHORIZED_FILE_TOUCHED. Result on unauthorized file: STOP_SCOPE_CONFLICT. The B14.0 path-lock validator `scripts/rp5/validate_b14_0_path_locks.py` is not invoked by any B14.1 task because its PATH_LOCKS list only enumerates PL-B14_0-* lock ids; B14.1 introduces its own seven lock ids.

## 9. Validator contracts and fixtures

Each new validator has a paired fixture generator at scripts/rp5/fixtures/ named generate_fixture_validate_b14_1_ followed by the validator id (see the rows in §9.1 for the exact generator-id-to-script-path mapping) producing positive_and_negative fixtures with sha256 manifests. Generator sentinel format: OK_FIXTURE_VALIDATE_B14_1_ followed by the validator id in UPPER_CASE (see the Sentinel column in §9.1 for the exact value per validator). Failure marker matches the owning validator's marker per orchestrator_plan §6. Reusable B-route protocol validators (validate_report_shape, validate_approval_packet, print_tracker_state, validate_future_constraints, validate_no_banned_phrases) are invoked directly because they read declarative schema/HAR/tracker inputs without any phase-hardcoded lock or artifact-name knowledge. The two B14.1 wrappers (validate_b14_1_plan_compile, validate_b14_1_path_locks) replace the inherited scripts that carry phase-hardcoded knowledge; they are created by B14_1-00 execution and live under scripts/rp5/.

validate_b14_1_plan_compile must_check contract is inherited from B-route §9, with the additional checks `every_B14_1_task_next_state_exists`, `every_b14_1_marker_has_recovery_packet`, and `every_b14_1_har_record_has_recovery_packet`.

validate_b14_1_path_locks reproduces the B-route umbrella classifier with PATH_LOCKS entries for PL-B14_1-API-DEMO, PL-B14_1-FRONTEND, PL-B14_1-CONFIG, PL-B14_1-TESTS, PL-B14_1-SCRIPTS, PL-B14_1-REPORTS, PL-B14_1-TUNNEL-TEMPLATE plus the protocol entries PROTOCOL-TRACKER and PROTOCOL-RP-REPORTS; the `--lock` selector restricts reporting to a single lock id.

### 9.1 Fixture generator contracts for new B14.1 validators

| Generator id | Script path | Command | Output manifest | Sentinel | Owned marker |
|---|---|---|---|---|---|
| generate_fixture_validate_b14_1_exposure_state_record | scripts/rp5/fixtures/generate_fixture_validate_b14_1_exposure_state_record.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_exposure_state_record.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_exposure_state_record_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_exposure_state_record_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_EXPOSURE_STATE | B14_1_EPHEMERAL_URL_SUCCESS_CLAIM |
| generate_fixture_validate_b14_1_application_layer_gate_invariants | scripts/rp5/fixtures/generate_fixture_validate_b14_1_application_layer_gate_invariants.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_application_layer_gate_invariants.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_application_layer_gate_invariants_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_application_layer_gate_invariants_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_APPLICATION_LAYER_GATE | B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED |
| generate_fixture_validate_b14_1_no_network_trust_authority | scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_network_trust_authority.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_network_trust_authority.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_no_network_trust_authority_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_no_network_trust_authority_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_NO_NETWORK_TRUST | B14_1_NETWORK_TRUST_AUTHORITY_DETECTED |
| generate_fixture_validate_b14_1_recruiter_gate_preserved_under_public_exposure | scripts/rp5/fixtures/generate_fixture_validate_b14_1_recruiter_gate_preserved_under_public_exposure.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_recruiter_gate_preserved_under_public_exposure.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_recruiter_gate_preserved_under_public_exposure_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_recruiter_gate_preserved_under_public_exposure_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_RECRUITER_GATE_PRESERVED | B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE |
| generate_fixture_validate_b14_1_health_payload_preserved_under_public_exposure | scripts/rp5/fixtures/generate_fixture_validate_b14_1_health_payload_preserved_under_public_exposure.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_health_payload_preserved_under_public_exposure.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_health_payload_preserved_under_public_exposure_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_health_payload_preserved_under_public_exposure_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE | B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE |
| generate_fixture_validate_b14_1_openapi_docs_visibility | scripts/rp5/fixtures/generate_fixture_validate_b14_1_openapi_docs_visibility.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_openapi_docs_visibility.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_openapi_docs_visibility_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_openapi_docs_visibility_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_OPENAPI_DOCS | B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED |
| generate_fixture_validate_b14_1_no_public_url_or_hostname_literal | scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_no_public_url_or_hostname_literal_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | B14_1_PUBLIC_URL_LITERAL_COMMITTED or B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED |
| generate_fixture_validate_b14_1_no_tunnel_secret_leak | scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_no_tunnel_secret_leak_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_NO_TUNNEL_SECRET_LEAK | B14_1_TUNNEL_SECRET_COMMITTED |
| generate_fixture_validate_b14_1_local_bypass_justification | scripts/rp5/fixtures/generate_fixture_validate_b14_1_local_bypass_justification.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_local_bypass_justification.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_local_bypass_justification_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_local_bypass_justification_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_LOCAL_BYPASS_JUSTIFIED | B14_1_LOCAL_BYPASS_UNJUSTIFIED |
| generate_fixture_validate_b14_1_broute_compatibility_under_public_exposure | scripts/rp5/fixtures/generate_fixture_validate_b14_1_broute_compatibility_under_public_exposure.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_1_broute_compatibility_under_public_exposure.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_1_broute_compatibility_under_public_exposure_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_1_broute_compatibility_under_public_exposure_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE |

## 10. Task contracts

| Task | Preconditions | Action title | Deliverable | Validators | Done when | Stop |
|---|---|---|---|---|---|---|
| B14_1-00 | tracker readable; B14.0 PHASE_APPROVED; plan-authoring APPROVE_FOR_EXECUTION recorded | create the two B14.1 wrapper validators (scripts/rp5/validate_b14_1_plan_compile.py and scripts/rp5/validate_b14_1_path_locks.py) and emit reports/rp5/b14_1_plan_compile.md; deliverable commands: `python3 scripts/rp5/validate_b14_1_plan_compile.py --plan-dir docs/plans/b14_1 --out reports/rp5/b14_1_plan_compile.md` and `python3 scripts/rp5/validate_b14_1_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md` | reports/rp5/b14_1_plan_compile.md | validate_b14_1_plan_compile (sentinel OK_PLAN_COMPILES, failure marker PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP); validate_b14_1_path_locks (sentinel OK_CHANGED_FILES_PATH_LOCKED, failure marker UNAUTHORIZED_FILE_TOUCHED) | OK_PLAN_COMPILES + OK_CHANGED_FILES_PATH_LOCKED | execution_report |
| B14_1-01 | B14_1-00 PASS | exposure-state plumbing: introduce PUBLIC_DEMO_EXPOSURE flag wiring in services/api/app/ (default false), author reports/rp5/b14_1_exposure_state_record.md as a public_exposure_claim_record citing HAR-B14_1-FUNNEL-CAPABILITY-001 and HAR-B14_1-STABLE-HOSTNAME-001 by reference, .env.example placeholders only | services/api/app/* + .env.example + reports/rp5/b14_1_exposure_state_record.md | validate_b14_1_exposure_state_record, validate_b14_1_no_public_url_or_hostname_literal | OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED + OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | execution_report |
| B14_1-02 | B14_1-01 PASS | application-layer gate invariants under PUBLIC_DEMO_EXPOSURE=true (recruiter HTTPBasic remains sole authority; no decision keyed on network origin) | reports/rp5/b14_1_application_layer_gate_invariants.md + reports/rp5/b14_1_no_network_trust_authority.md + minimal services/api/app/ edits if needed | validate_b14_1_application_layer_gate_invariants, validate_b14_1_no_network_trust_authority | OK_B14_1_APPLICATION_LAYER_GATE + OK_B14_1_NO_NETWORK_TRUST_AUTHORITY | execution_report |
| B14_1-03 | B14_1-02 PASS | recruiter-gate and BR-02 health preservation under public exposure, plus OpenAPI/docs visibility | reports/rp5/b14_1_recruiter_gate_preserved_under_public_exposure.md + reports/rp5/b14_1_health_payload_preserved_under_public_exposure.md + reports/rp5/b14_1_openapi_docs_visibility.md | validate_b14_1_recruiter_gate_preserved_under_public_exposure, validate_b14_1_health_payload_preserved_under_public_exposure, validate_b14_1_openapi_docs_visibility | all three OK sentinels | execution_report |
| B14_1-04 | B14_1-03 PASS | tunnel configuration template at PL-B14_1-TUNNEL-TEMPLATE with placeholders only (env-var-name references for auth-key and hostname; no real secrets; no public URL); README pointer in the same task is allowed only as a host-only operator note inside the template file itself, never as a literal hostname | infra/tunnel/funnel_config.template.yaml or .json + reports/rp5/b14_1_no_public_url_or_hostname_literal.md re-emission | validate_b14_1_no_public_url_or_hostname_literal, validate_b14_1_no_tunnel_secret_leak (template-scope) | OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL + OK_B14_1_NO_TUNNEL_SECRET_LEAK | execution_report |
| B14_1-05 | B14_1-04 PASS | local bypass justification: enumerate every bypass under PUBLIC_DEMO_EXPOSURE=false and pair each with a test that asserts it is disabled when PUBLIC_DEMO_EXPOSURE=true; if zero bypasses are introduced, record explicit_NA_zero_bypasses | reports/rp5/b14_1_local_bypass_justification.md + tests/demo/test_b14_1_local_bypass_disabled_under_public_exposure.py (only if any bypass is introduced) | validate_b14_1_local_bypass_justification | OK_B14_1_LOCAL_BYPASS_JUSTIFIED | execution_report |
| B14_1-06 | B14_1-05 PASS | no-tunnel-secret-leak invariants (logs, error pages, structured logs, openapi/docs scratch); committed scan finds no auth-key, no token, no hostname literal, no public URL | reports/rp5/b14_1_no_tunnel_secret_leak.md | validate_b14_1_no_tunnel_secret_leak | OK_B14_1_NO_TUNNEL_SECRET_LEAK | execution_report |
| B14_1-07 | B14_1-06 PASS | B-route and B14.0 compatibility re-verification under public exposure (BR-02..BR-07 sentinels re-emitted; B14_0-02..B14_0-07 sentinels re-emitted; frozen fingerprints unchanged) | reports/rp5/b14_1_broute_compatibility_under_public_exposure.md | validate_b14_1_broute_compatibility_under_public_exposure | OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | execution_report |
| B14_1-08 | B14_1-07 PASS | B14.1 phase gate final-verification checklist + B14.1 future-constraint records for FC-B14-1-FUNNEL, FC-B15-MULTI-NETWORK, FC-HANDOFF-DATAMOVE1, FC-BROUTE-FROZEN, FC-B14-0-GATE-PRESERVED | reports/rp5/b14_1_phase_gate.md and reports/rp5/b14_1_future_constraints.md | every validator from §7 plus validate_future_constraints | every OK sentinel observed and no marker active; exposure_state_record asserts application_gated_stable_hostname or an explicit blocker is active | phase_gate_report; stop for PHASE_APPROVE |

Implementation detail beyond the action-title and deliverable-set is owned by the per-task planning_report at execution time.

## 11. Recovery packets

Every marker in §3 maps to exactly one recovery packet. Each packet defines: diagnosis_command, allowed_files_to_inspect, allowed_files_to_modify, retry_limit, next_state_on_recovered, next_state_on_retry_exhausted. Where the B14.0 plan defined an identical-named packet (PLAN_CONFLICT, TRACKER_*, REPORT_*, APPROVAL_*, EXECUTION_*, PATH_LOCK_*, VALIDATOR_*, RECOVERY_*, UNAUTHORIZED_*, HUMAN_*, FUTURE_*, PUBLIC_SECURITY_*), this plan inherits the packet semantics with the diagnosis_command rewritten to use docs/plans/b14_1/ and the B14.1 validators where applicable.

| Packet id | Marker | Diagnosis command | Allowed inspect | Allowed modify | Retry | Recovered next | Exhausted next |
|---|---|---|---|---|---:|---|---|
| RP-PLAN-CONFLICT | PLAN_CONFLICT | `python scripts/rp5/validate_b14_1_plan_compile.py --plan-dir docs/plans/b14_1 --out reports/rp5/b14_1_plan_conflict.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_1-00 | CHANGE_SCOPE |
| RP-TRACKER-MISSING | TRACKER_MISSING | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b14_1_tracker_missing.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_1-00 | CHANGE_SCOPE |
| RP-TRACKER-MISMATCH | TRACKER_MISMATCH | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b14_1_tracker_mismatch.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_1-00 | CHANGE_SCOPE |
| RP-REPORT-SCHEMA-INVALID | REPORT_SCHEMA_INVALID | `python scripts/rp5/validate_report_shape.py --schemas docs/plans/b14_1/state_packet_schemas.yaml --report-from-tracker latest_context --out reports/rp5/b14_1_report_schema_invalid.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-APPROVAL-PACKET-MALFORMED | APPROVAL_PACKET_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_approval_packet --out reports/rp5/b14_1_approval_packet_malformed.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-HUMAN-ACTION-REQUEST-MALFORMED | HUMAN_ACTION_REQUEST_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_human_action_request --out reports/rp5/b14_1_human_action_request_malformed.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-EXECUTION-RAIL-GAP | EXECUTION_RAIL_GAP | `python scripts/rp5/validate_b14_1_plan_compile.py --plan-dir docs/plans/b14_1 --out reports/rp5/b14_1_execution_rail_gap.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PATH-LOCK-TOO-BROAD | PATH_LOCK_TOO_BROAD | `python scripts/rp5/validate_b14_1_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b14_1_path_lock_too_broad.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-VALIDATOR-MATERIALIZATION-GAP | VALIDATOR_MATERIALIZATION_GAP | `python scripts/rp5/validate_b14_1_plan_compile.py --plan-dir docs/plans/b14_1 --out reports/rp5/b14_1_validator_materialization_gap.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-RECOVERY-PACKET-GAP | RECOVERY_PACKET_GAP | `python scripts/rp5/validate_b14_1_plan_compile.py --plan-dir docs/plans/b14_1 --out reports/rp5/b14_1_recovery_packet_gap.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-UNAUTHORIZED-FILE-TOUCHED | UNAUTHORIZED_FILE_TOUCHED | `python scripts/rp5/validate_b14_1_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b14_1_unauthorized_file_touched.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | STOP_SCOPE_CONFLICT |
| RP-HUMAN-ACTION-REQUIRED | HUMAN_ACTION_REQUIRED | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/b14_1_pending_human_action.md` | docs/plans/b14_1, tracker, reports/rp5 | none until human_action_result is recorded | 0 | same task | CHANGE_SCOPE |
| RP-FUTURE-CONSTRAINT-REGRESSION | FUTURE_CONSTRAINT_REGRESSION | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/b14_1_future_constraints.md --out reports/rp5/b14_1_future_constraint_regression.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PUBLIC-SECURITY-REGRESSION | PUBLIC_SECURITY_REGRESSION | `python scripts/rp5/validate_public_security_invariants.py --base-url http://127.0.0.1:8001 --out reports/rp5/b14_1_public_security_regression.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-APPLICATION-LAYER-GATE-BYPASS | B14_1_APPLICATION_LAYER_GATE_BYPASS_DETECTED | `python scripts/rp5/validate_b14_1_application_layer_gate_invariants.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_application_layer_gate_bypass.md` | docs/plans/b14_1, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-NETWORK-TRUST-AUTHORITY-DETECTED | B14_1_NETWORK_TRUST_AUTHORITY_DETECTED | `python scripts/rp5/validate_b14_1_no_network_trust_authority.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_network_trust_authority.md` | docs/plans/b14_1, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-EXPOSURE | B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE | `python scripts/rp5/validate_b14_1_recruiter_gate_preserved_under_public_exposure.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_recruiter_gate_regression.md` | docs/plans/b14_1, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-HEALTH-PAYLOAD-REGRESSION-UNDER-PUBLIC-EXPOSURE | B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE | `python scripts/rp5/validate_b14_1_health_payload_preserved_under_public_exposure.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_health_regression.md` | docs/plans/b14_1, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-OPENAPI-OR-DOCS-LEAK-DETECTED | B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED | `python scripts/rp5/validate_b14_1_openapi_docs_visibility.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_openapi_docs_leak.md` | docs/plans/b14_1, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-EPHEMERAL-URL-SUCCESS-CLAIM | B14_1_EPHEMERAL_URL_SUCCESS_CLAIM | `python scripts/rp5/validate_b14_1_exposure_state_record.py --record reports/rp5/b14_1_exposure_state_record.md --verbose --out reports/rp5/b14_1_ephemeral_url_success_claim.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-PUBLIC-URL-LITERAL-COMMITTED | B14_1_PUBLIC_URL_LITERAL_COMMITTED | `python scripts/rp5/validate_b14_1_no_public_url_or_hostname_literal.py --root . --verbose --out reports/rp5/b14_1_public_url_literal_committed.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-STABLE-HOSTNAME-LITERAL-COMMITTED | B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED | `python scripts/rp5/validate_b14_1_no_public_url_or_hostname_literal.py --root . --component hostname_only --verbose --out reports/rp5/b14_1_stable_hostname_literal_committed.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-TUNNEL-SECRET-COMMITTED | B14_1_TUNNEL_SECRET_COMMITTED | `python scripts/rp5/validate_b14_1_no_tunnel_secret_leak.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_tunnel_secret_committed.md` | docs/plans/b14_1, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-BROUTE-REGRESSION-UNDER-PUBLIC-EXPOSURE | B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE | `python scripts/rp5/validate_b14_1_broute_compatibility_under_public_exposure.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_1_broute_regression.md` | docs/plans/b14_1, tracker, reports/rp5, services | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_1-LOCAL-BYPASS-UNJUSTIFIED | B14_1_LOCAL_BYPASS_UNJUSTIFIED | `python scripts/rp5/validate_b14_1_local_bypass_justification.py --root . --verbose --out reports/rp5/b14_1_local_bypass_unjustified.md` | docs/plans/b14_1, tracker, reports/rp5, tests/demo | same task owned files only | 1 | same task | CHANGE_SCOPE |

## 12. Security and forbidden scope

Forbidden in B14.1:

| Scope | Reason | Marker |
|---|---|---|
| public-network multi-network smoke claim from a single B14.1 host run | belongs to B15 | FUTURE_CONSTRAINT_REGRESSION |
| router schema or cache-key schema change | belongs to B-handoff or frozen by B-route | FUTURE_CONSTRAINT_REGRESSION |
| literal public URL commit | pre-plan forbids without explicit human approval | B14_1_PUBLIC_URL_LITERAL_COMMITTED |
| literal stable hostname commit | hostname is operator-owned and recorded by reference only | B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED |
| committing real Tailscale auth-key, Cloudflare token, RECRUITER_PASSWORD, or ADMIN_STATS_PASSWORD | secret leak | B14_1_TUNNEL_SECRET_COMMITTED |
| application-layer authority decision keyed on network origin (client IP, source interface, Tailscale identity, X-Forwarded-For) | violates application-layer gate authority invariant | B14_1_NETWORK_TRUST_AUTHORITY_DETECTED |
| OpenAPI or interactive docs mounted unprotected under PUBLIC_DEMO_EXPOSURE=true | unauthenticated docs surface leak | B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED |
| claim of success keyed on an ephemeral URL alone | violates stable-named-exposure semantics | B14_1_EPHEMERAL_URL_SUCCESS_CLAIM |
| local bypass active under PUBLIC_DEMO_EXPOSURE=true | bypass surface leaks public surface | B14_1_LOCAL_BYPASS_UNJUSTIFIED |
| editing docs/plans/broute/ or docs/plans/b14_0/ | predecessor plans frozen post-approval | UNAUTHORIZED_FILE_TOUCHED |
| editing libs/asr/router_runtime.py | B-route schema frozen | UNAUTHORIZED_FILE_TOUCHED |
| editing services/frontend/app/demo/types.ts router-field shape | BR-04 contract frozen | UNAUTHORIZED_FILE_TOUCHED |
| installing a systemd unit inside a B14.1 task | systemd install action is host-only and operator-owned; the template file at PL-B14_1-TUNNEL-TEMPLATE may carry placeholders only | UNAUTHORIZED_FILE_TOUCHED |
| processing user uploads via the Funnel surface inside B14.1 | upload behavior is preserved from B14.0; no upload-pipeline changes occur in B14.1 | UNAUTHORIZED_FILE_TOUCHED |

## 13. Report skeletons

Report shapes are defined in state_packet_schemas.yaml. The B14.1 plan reuses planning_report, execution_report, phase_gate_report, approval_packet, and supplemental_evidence_report unchanged from the B14.0 schema. New B14.1-specific records (public_exposure_artifact_record, application_layer_gate_invariant_record, exposure_state_record, openapi_docs_visibility_record, local_bypass_justification_record, public_exposure_claim_record, context_window_hygiene_record) are defined in state_packet_schemas.yaml.

Reports are compact and evidence-focused. Each execution_report must fit the seven-row schema; verbose narration is excluded by the validate_report_shape contract. The phase_gate_report at B14_1-08 cites every FV-* sentinel and one row per future-constraint preservation record, and no more.

## 14. Banned phrases and no-improvisation scan

Banned phrases registry is inherited from the B-route agent_plan §14 verbatim. Scan command:

```bash
grep -nE '(as needed|as appropriate|as required|if already present|if present|where appropriate|best practices|obvious|TBD|TODO without a marker|discovered|discover |judgment|free-form|free form)' docs/plans/b14_1/agent_plan.md docs/plans/b14_1/orchestrator_plan.md | grep -v 'section_14\|banned_phrases\|forbidden_orchestrator_outputs'
```

Expected: zero rows.

## 15. Human action requests

The HAR transport (CHANGE_SCOPE_with_human_action_request_id) is inherited from B-route and B14.0. Two HARs are pre-declared because Funnel capability and the stable hostname must originate outside the agent's authority.

| HAR id | Trigger marker | Missing inputs | Blocking scope | Required human result shape |
|---|---|---|---|---|
| HAR-B14_1-FUNNEL-CAPABILITY-001 | HUMAN_ACTION_REQUIRED | tailscale_account_funnel_capability_enabled, tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY, cloudflare_tunnel_alternative_token_supplied_as_host_env (only if the operator selects Cloudflare instead of Tailscale Funnel), tunnel_run_as_service_restart_policy_string | resolved before B14_1-04 closure (template authoring); fully resolved before B14_1-08 closure (success-claim) | operator declares Funnel capability state and tunnel restart policy; secrets stored only as host env or systemd service env; tracker records only "supplied: true" per field and the restart-policy string, never the secret values; explicit_NA is accepted for the cloudflare_tunnel_alternative_token field if the operator selects Tailscale Funnel exclusively |
| HAR-B14_1-STABLE-HOSTNAME-001 | HUMAN_ACTION_REQUIRED | stable_hostname_supplied_as_host_env_PUBLIC_DEMO_STABLE_HOSTNAME, stable_hostname_owned_by_operator_account, dns_or_tailnet_funnel_record_active | resolved before B14_1-08 closure (success-claim); unresolved at B14_1-08 forces public_exposure_claim_record.claim_status to BLOCKED_PENDING_HUMAN_ACTION and the phase gate report cites the HAR id as the explicit blocker | operator supplies the hostname only by reference (env-var name and "supplied: true" flag); the literal hostname string is never recorded in tracker, approval packets, or any committed file; explicit_NA is not accepted (the phase gate cannot pass without either a supplied-by-reference hostname or an explicit BLOCKED claim citing this HAR) |

```yaml
HAR-B14_1-FUNNEL-CAPABILITY-001:
  status: pre_declared_unresolved
  marker: HUMAN_ACTION_REQUIRED
  missing_inputs:
    - tailscale_account_funnel_capability_enabled
    - tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY
    - cloudflare_tunnel_alternative_token_supplied_as_host_env
    - tunnel_run_as_service_restart_policy_string
  why_human_only: enabling Funnel on a Tailscale account or provisioning a Cloudflare tunnel token requires operator authority outside the agent; the agent must not invent auth-key values
  allowed_values_or_schema:
    tailscale_account_funnel_capability_enabled: boolean
    tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY: boolean (the agent never reads or echoes the value)
    cloudflare_tunnel_alternative_token_supplied_as_host_env: boolean or explicit_NA
    tunnel_run_as_service_restart_policy_string: ISO-8601 duration or one of the strings "always" or "on-failure" or "manual-restart-on-incident"
  blocks: B14_1-04 closure (template authoring) and B14_1-08 closure (success-claim)
  created_by_task: B14.1 plan authoring (this draft)
  next_state_until_result: agent waits at B14_1-04 (or accepts a BLOCKED_PENDING_HUMAN_ACTION claim at B14_1-08)
  forbidden_agent_action: inventing auth-key or token values; committing auth-key or token values; logging auth-key or token values; storing auth-key or token values in committed files
  result_expected_at: before APPROVE_PLAN for B14_1-04 (capability flag and restart-policy string); fully resolved before B14_1-08 success-claim
  result_recording_policy:
    - the human_action_result captures field names, boolean flags, and the restart-policy string only
    - actual auth-key or token values are NEVER written into tracker, approval packets, or any committed file
    - tracker records only "supplied: true" per field and the restart-policy string

HAR-B14_1-STABLE-HOSTNAME-001:
  status: pre_declared_unresolved
  marker: HUMAN_ACTION_REQUIRED
  missing_inputs:
    - stable_hostname_supplied_as_host_env_PUBLIC_DEMO_STABLE_HOSTNAME
    - stable_hostname_owned_by_operator_account
    - dns_or_tailnet_funnel_record_active
  why_human_only: the stable hostname is operator-owned; the agent must not invent or commit hostname literals
  allowed_values_or_schema:
    stable_hostname_supplied_as_host_env_PUBLIC_DEMO_STABLE_HOSTNAME: boolean (the agent never reads or echoes the literal hostname)
    stable_hostname_owned_by_operator_account: boolean
    dns_or_tailnet_funnel_record_active: boolean
  blocks: B14_1-08 closure (success-claim); does not block B14_1-00..B14_1-07
  created_by_task: B14.1 plan authoring (this draft)
  next_state_until_result: agent reaches B14_1-08 and emits public_exposure_claim_record.claim_status = BLOCKED_PENDING_HUMAN_ACTION citing this HAR id; phase gate cannot pass without either a supplied-by-reference hostname or a BLOCKED claim
  forbidden_agent_action: inventing or committing hostname literals; recording hostname literal in tracker, approval packets, or any committed file; reading the literal hostname value from any source
  result_expected_at: before APPROVE_PLAN for B14_1-08 success-claim, or recorded as the explicit blocker at B14_1-08
  result_recording_policy:
    - the human_action_result captures only "supplied: true" or "supplied: false" per field
    - the literal hostname string is NEVER written into tracker, approval packets, or any committed file
```

## 16. Context-window hygiene

```yaml
context_window_hygiene_policy:
  trigger_kind_task_count_within_phase: prefer a new Claude window after every two or three executed B14.1 tasks
  trigger_kind_phase_boundary: prefer a new Claude window at the B14.0->B14.1 boundary and at the B14.1->B15 boundary
  rationale: each task in B14.1 produces a compact execution_report; the orchestrator should keep the active context narrow and evidence-focused; the tracker is the durable transport between windows and is consulted at every session-open
  recommended_actions:
    - after B14_1-02 closure, prefer a new Claude window before B14_1-03 planning
    - after B14_1-05 closure, prefer a new Claude window before B14_1-06 planning
    - at the B14_1-08 phase gate boundary, prefer a new Claude window before any B15 plan-authoring step
```

## 17. Authoring status

```yaml
authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
plan_authoring_orchestrator_decision_scope: plan_authoring
plan_authoring_orchestrator_decision_input_accepted_report_commit: 0bdaea89c665dd5cabd7904556dbf536ef409f9f
b14_0_accepted_phase_gate_report_commit: 7e9ce1f7067f938d2b58a7a4e8615101b0012c58
b14_0_accepted_tracker_closure_commit: 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8
tracker_advance_policy: this draft advances tracker.current_task and tracker.state_transport.expected_next_task from B14.1_PENDING_ORCHESTRATOR_INSTRUCTION to B14.1_PLAN_AUTHORING per the orchestrator-issued REQUEST_PLAN_AUTHORING decision; tracker.plan_authoring_approvals.B14.1 is NOT created by this draft and will be created by the orchestrator's APPROVE_FOR_EXECUTION decision
no_B14_1_implementation_task_starts_until:
  - an APPROVE_FOR_EXECUTION decision for this plan package is recorded by the orchestrator
  - an APPROVE_PLAN decision for the first B14.1 task (B14_1-00) is recorded by the orchestrator after this plan-package approval
  - HAR-B14_1-FUNNEL-CAPABILITY-001 is resolved before B14_1-04 closure (does not block B14_1-00..B14_1-03)
  - HAR-B14_1-STABLE-HOSTNAME-001 is resolved before B14_1-08 success-claim or is recorded as the explicit blocker at B14_1-08
```

## 18. Adversarial stress-replay

| Scenario | initial_state | triggering_event | expected_marker | expected_next_state | report_shape | plan_sections_used | result |
|---|---|---|---|---|---|---|---|
| network-trust bypass introduced | services/api/app/ adds a path that returns 200 from /demo/* when the client IP matches a private-range or a Tailscale identity header is present | B14_1-02 closure attempt | B14_1_NETWORK_TRUST_AUTHORITY_DETECTED | B14_1-02 fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_no_network_trust_authority emits FAIL on the trust-by-IP and trust-by-header fixtures |
| ephemeral URL success claim | reports/rp5/b14_1_exposure_state_record.md records claim_status=SUCCESS_WITH_STABLE_NAMED_EXPOSURE while stable_hostname_supplied_by_reference=false | B14_1-08 closure attempt | B14_1_EPHEMERAL_URL_SUCCESS_CLAIM | B14_1-08 fix or BLOCKED_PENDING_HUMAN_ACTION recording | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_exposure_state_record enforces the rule "success requires stable_named_exposure_supplied_by_reference=true and explicit_blocker_id=null" |
| OpenAPI mounted unprotected | services/api/app/ mounts /openapi.json unconditionally under PUBLIC_DEMO_EXPOSURE=true | B14_1-03 closure attempt | B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED | B14_1-03 fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_openapi_docs_visibility emits FAIL on the mounted-unprotected fixture |
| recruiter gate regressed under public exposure | services/api/app/ flips PUBLIC_DEMO_EXPOSURE=true and a /demo/* response returns 200 without recruiter auth | B14_1-03 or B14_1-07 closure | B14_1_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE | first failing task fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_recruiter_gate_preserved_under_public_exposure emits FAIL on the unauthenticated-200 fixture |
| /demo/health payload regressed | authenticated /demo/health body deviates from {"status":"ok"} under PUBLIC_DEMO_EXPOSURE=true | B14_1-03 closure | B14_1_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE | B14_1-03 fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_health_payload_preserved_under_public_exposure enforces byte-exact equality |
| public URL literal committed | a committed file contains a non-loopback https URL | any B14_1-NN closure | B14_1_PUBLIC_URL_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | execution_report | §3, §4, §11, §12 | PASS evidence: validate_b14_1_no_public_url_or_hostname_literal scans the repo and emits FAIL on the committed-https-non-loopback fixture |
| stable hostname literal committed | a committed file contains the operator's hostname string | any B14_1-NN closure | B14_1_STABLE_HOSTNAME_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | execution_report | §3, §4, §11, §12 | PASS evidence: validate_b14_1_no_public_url_or_hostname_literal --component hostname_only emits FAIL on the committed-hostname fixture |
| Tailscale auth-key committed | infra/tunnel/funnel_config.template.yaml or any committed file contains a string matching the Tailscale auth-key prefix | any B14_1-NN closure | B14_1_TUNNEL_SECRET_COMMITTED | FIX_BEFORE_CLOSE | execution_report | §3, §4, §11, §12 | PASS evidence: validate_b14_1_no_tunnel_secret_leak scans for auth-key prefixes and emits FAIL on the committed-auth-key fixture |
| unjustified local bypass under PUBLIC_DEMO_EXPOSURE=true | a bypass is introduced under PUBLIC_DEMO_EXPOSURE=false without a paired test asserting disabled-when-true | B14_1-05 closure | B14_1_LOCAL_BYPASS_UNJUSTIFIED | B14_1-05 fix | execution_report | §2, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_local_bypass_justification emits FAIL on the unjustified-bypass fixture |
| router-runtime edit | libs/asr/router_runtime.py modified | any B14_1-NN commit | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | execution_report | §1, §3, §8, §11, §12 | PASS evidence: path lock validator rejects file outside B14.1 lock set; FC-BROUTE-FROZEN preservation row in orchestrator_plan §3 also fires |
| frontend types router-field shape edit | services/frontend/app/demo/types.ts RouterFields shape changed | B14_1-03 closure | B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE or UNAUTHORIZED_FILE_TOUCHED | B14_1-03 fix or STOP_SCOPE_CONFLICT | execution_report | §1, §3, §4, §10, §11, §12 | PASS evidence: validate_b14_1_broute_compatibility_under_public_exposure compares the frozen RouterFields shape sha256 and emits FAIL on mismatch |
| systemd-unit install inside a task | a B14_1-NN task adds a /etc/systemd/system/*.service file or runs systemctl enable | any B14_1-NN closure | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | execution_report | §1, §3, §8, §11, §12 | PASS evidence: path lock validator rejects file outside B14.1 lock set; §12 forbidden-scope row also fires |

```yaml
stress_replay_summary:
  scenarios_enumerated: 12
  every_scenario_maps_to_existing_marker: true
  every_scenario_maps_to_existing_recovery_packet: true (markers above all appear in §3 and §11)
```
