# agent_plan.md

Plan state: DRAFT_NOT_APPROVED_FOR_EXECUTION
Project scope: B15 multi-network public smoke test of the recruiter-gated public-demo surface. B15 is verification-only: it produces declarative coverage records, multi-network smoke-result records, and adjudication records, and it does not modify application, library, infrastructure, compose, runtime, or test-target code. Public-exposure and multi-network execution tasks are HAR-gated. Future phases (B-handoff datamove1 router swap, H, C) are preserved but not executable in this plan. B-route, B14.0, and B14.1 deliverables are frozen.
Authority: executable task order, exact commands, validators, fixture generators, marker registry, recovery packets, transition table, tracker mutation rules, path locks, HAR table, and report skeleton references.

## 0. Manifest and entity registry

```yaml
project: b15_public_smoke_multi_network
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
starting_state:
  last_completed_phase: B14.1
  last_completed_task: B14_1-08
  current_phase: B15
  current_task: B15_PENDING_ORCHESTRATOR_INSTRUCTION
canonical_output_files:
  - docs/plans/b15/orchestrator_plan.md
  - docs/plans/b15/agent_plan.md
  - docs/plans/b15/state_packet_schemas.yaml
phases:
  - B15
  - B-handoff_future_constraint
tasks:
  - B15-00
  - B15-01
  - B15-02
  - B15-03
  - B15-04
  - B15-05
  - B15-06
  - B15-07
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
  - B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED
  - B15_SMOKE_RESULT_FABRICATED
  - B15_MULTI_NETWORK_COVERAGE_GAP
  - B15_EPHEMERAL_URL_SUCCESS_CLAIM
  - B15_PUBLIC_URL_LITERAL_COMMITTED
  - B15_STABLE_HOSTNAME_LITERAL_COMMITTED
  - B15_TUNNEL_SECRET_COMMITTED
  - B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
  - B15_QUOTA_STATE_MISREPRESENTED
  - B15_UPLOAD_LIMIT_REGRESSION
  - B15_MOBILE_LAYOUT_REGRESSION
  - B15_CACHED_EXAMPLE_REGRESSION
  - B15_BROUTE_REGRESSION_UNDER_PUBLIC_SMOKE
validators:
  - validate_b15_plan_compile
  - validate_b15_path_locks
  - validate_b15_coverage_matrix
  - validate_b15_multi_network_smoke
  - validate_b15_smoke_result_evidence
  - validate_b15_recruiter_gate_preserved_under_public_smoke
  - validate_b15_quota_state_accuracy
  - validate_b15_upload_limit_enforced
  - validate_b15_mobile_layout
  - validate_b15_cached_example_integrity
  - validate_b15_public_exposure_smoke_claim
  - validate_b15_no_public_url_or_hostname_literal
  - validate_future_constraints
  - validate_no_banned_phrases
  - validate_report_shape
  - validate_approval_packet
  - print_tracker_state
  - print_pending_human_action_requests
artifacts:
  - reports/rp5/b15_plan_compile.md
  - reports/rp5/b15_coverage_matrix.md
  - reports/rp5/b15_smoke_harness.md
  - reports/rp5/b15_human_action_packet.md
  - reports/rp5/b15_public_exposure_bringup.md
  - reports/rp5/b15_multi_network_smoke_results.md
  - reports/rp5/b15_smoke_adjudication.md
  - reports/rp5/b15_future_constraints.md
  - reports/rp5/b15_phase_gate.md
claims:
  - recruiter_HTTPBasic_gate_remains_sole_authority_for_public_access_under_public_smoke
  - multi_network_coverage_verified_for_four_vantage_points_or_explicit_blocker_recorded
  - every_smoke_result_record_traces_to_operator_supplied_evidence
  - provider_quota_states_accurately_represented
  - upload_limit_enforced_in_smoke
  - mobile_layout_has_no_horizontal_scroll_in_smoke
  - cached_curated_examples_resolve_in_smoke
  - public_exposure_smoke_claim_is_stable_named_or_explicit_blocker_recorded
  - no_public_URL_no_stable_hostname_no_tunnel_secret_literal_committed
  - no_application_library_infra_runtime_file_modified_by_B15
  - BR-01..BR-08_B14_0-00..B14_0-08_B14_1-00..B14_1-08_remain_frozen
  - future_constraints_preserved
```

## 1. Branch, repository layout, and path locks

```yaml
repository:
  root: /home/gbibbo/code/asr_enhancement
  branch: feature/demo-runtime-rp5-v1
  runtime_preserved:
    - all B-route deliverables and validators
    - all B14.0 deliverables and validators
    - all B14.1 deliverables and validators (PUBLIC_DEMO_EXPOSURE flag plumbing, exposure-state record, tunnel template)
    - libs/asr/router_runtime.py (frozen schema)
    - services/api/app/* (no B15 task modifies application code)
    - services/frontend/app/demo/* (no B15 task modifies frontend code)
    - infra/tunnel/* (B14.1 template frozen; no B15 task modifies it)
    - structured JSON logs and log rotation policy
    - SQLite job, cache, and usage tables
```

B15 modifies no application, library, infrastructure, compose, or runtime code. B15 creates and modifies only: the B15 plan triad (during plan authoring and revision), B15 reports, B15 validator/harness scripts and their fixtures, and B15 declarative-record tests.

| Lock id | Type | Allowed components | Validator command | Max files | Marker on violation |
|---|---|---|---|---:|---|
| PL-B15-PLANS | exact_directory | docs/plans/b15/orchestrator_plan.md, docs/plans/b15/agent_plan.md, docs/plans/b15/state_packet_schemas.yaml; editable only during plan authoring or an orchestrator-approved plan revision | `python scripts/rp5/validate_b15_path_locks.py --lock PL-B15-PLANS --diff HEAD~1..HEAD` | 3 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B15-REPORTS | exact_directory_with_predicate | reports/rp5/b15_*.md; B-route, B14.0, and B14.1 reports remain frozen | `python scripts/rp5/validate_b15_path_locks.py --lock PL-B15-REPORTS --diff HEAD~1..HEAD` | 14 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B15-SCRIPTS | exact_directory_with_predicate | scripts/rp5/validate_b15_*.py and scripts/rp5/fixtures/generate_fixture_validate_b15_*.py and scripts/rp5/smoke_b15_*.py, plus the exact-filename allowlist scripts/rp5/validate_report_shape.py and scripts/rp5/validate_approval_packet.py (the two reusable protocol validators materialized by the B15-03 scope-change repair) and scripts/rp5/print_pending_human_action_requests.py (the reusable protocol diagnostic helper materialized by the B15-04 scope-change repair); allowlisted by exact name only, the glob is not broadened | `python scripts/rp5/validate_b15_path_locks.py --lock PL-B15-SCRIPTS --diff HEAD~1..HEAD` | 20 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B15-TESTS | exact_directory_with_predicate | tests/demo/test_b15_*.py and tests/rp5/fixtures/ | `python scripts/rp5/validate_b15_path_locks.py --lock PL-B15-TESTS --diff HEAD~1..HEAD` | 14 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B15-CONFIG | exact_file_or_create | .env.example placeholders only; real secrets forbidden; compose files (docker-compose*.yml, docker-compose.demo.yml) and infra/compose/* are forbidden in B15; application, library, infrastructure, and runtime files are forbidden in B15 | `python scripts/rp5/validate_b15_path_locks.py --lock PL-B15-CONFIG --diff HEAD~1..HEAD` | 1 | UNAUTHORIZED_FILE_TOUCHED |

Forbidden paths in B15 (any change triggers UNAUTHORIZED_FILE_TOUCHED and STOP_SCOPE_CONFLICT):

```yaml
forbidden_paths_b15:
  - services/**
  - libs/**
  - infra/**
  - docker-compose*.yml
  - infra/compose/**
  - docs/plans/broute/**
  - docs/plans/b14_0/**
  - docs/plans/b14_1/**
  - .env (with real values)
  - any runtime database, uploaded audio, cached generated audio, or log file
  - reports/rp5/broute_*.md, reports/rp5/b14_0_*.md, reports/rp5/b14_1_*.md, reports/rp5/*_approval_packet.yaml
```

## 2. Constants and decision rules

```yaml
public_exposure_flag_env: PUBLIC_DEMO_EXPOSURE
recruiter_realm: "asr-demo-recruiter"
stable_hostname_env_reference: PUBLIC_DEMO_STABLE_HOSTNAME
tailscale_auth_key_env_reference: TAILSCALE_AUTHKEY
network_vantage_points_required:
  - windows_local
  - mobile_cellular
  - other_wifi
  - vpn_or_external_tester
coverage_items_required:
  - five_curated_examples
  - five_degradations
  - whisper_provider
  - assemblyai_provider
  - upload_without_manual_ground_truth
  - upload_with_manual_ground_truth
  - upload_limit_enforced
  - provider_quota_state
  - mobile_layout
assemblyai_coverage_rule: if AssemblyAI is disabled or quota-exhausted at smoke time, the assemblyai_provider coverage item is recorded as explicit_NA_provider_disabled with the disabled or quota state captured in the smoke-result record; explicit_NA is legal only for the assemblyai_provider item and never for the other eight items
quota_states_recognised: [AssemblyAI available, AssemblyAI daily quota reached, AssemblyAI quota exhausted, AssemblyAI disabled]
public_url_literal_policy: forbidden in any committed file
stable_hostname_literal_policy: forbidden in any committed file; referenced by env-var name only
tunnel_secret_literal_policy: Tailscale auth-key and Cloudflare token forbidden in any committed file
ephemeral_url_policy: never a success-claim source; ephemeral URLs may appear only in local-only smoke evidence files that are removed before final commit
smoke_result_evidence_rule: every multi_network_smoke_result_record cites an operator-supplied evidence reference recorded via a human_action_result; a B15 task never authors a smoke-result record without that evidence reference
b14_1_approval_posture: B14.1 is APPROVED through the explicit-blocker branch only; B14.1 approval is not a public-exposure success claim
forbidden_in_B15:
  - any modification of services/**, libs/**, infra/**, or compose files
  - any modification of docs/plans/broute/, docs/plans/b14_0/, or docs/plans/b14_1/
  - any change to libs/asr/router_runtime.py
  - any literal public URL committed
  - any literal stable hostname committed
  - any Tailscale auth-key, Cloudflare token, recruiter password, or admin password committed
  - any logging of Authorization header values, password, or auth-key material
  - any datamove1 router handoff swap
  - starting public exposure, Funnel, Tailscale, Cloudflare, or systemd without operator-supplied human-action evidence
  - authoring or accepting a smoke-result record without an operator-supplied evidence reference
  - claiming multi-network coverage from fewer than four operator-supplied vantage-point records
  - any claim of public-exposure success keyed on an ephemeral URL alone
```

### 2.1 Threshold audit

| Category | Status | Source or rationale |
|---|---|---|
| public_smoke_request_latency_sla_ms | not_applicable_current_scope | B15 verifies correctness of the smoke surface, not latency budgets |
| multi_network_vantage_point_count | fixed_at_4 | the four vantage points are enumerated in section 2 network_vantage_points_required and are not a tunable threshold |
| curated_example_count | fixed_at_5 | the public demo is intentionally scoped to 5 curated examples; supersedes the legacy demo_platform_plan section 37 ten-example expectation; recorded via recovery packet RP-B15-CURATED-EXAMPLE-COUNT-SCOPE-CHANGE-B15-05 |
| degradation_count | fixed_at_5 | legacy demo_platform_plan section 37 fixes 5 degradations |
| tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY | HUMAN_ACTION_REQUIRED (HAR-B14_1-FUNNEL-CAPABILITY-001 residual) | carried unresolved from B14.1; the auth-key is operator-owned host env |
| stable_hostname_string_value | HUMAN_ACTION_REQUIRED (HAR-B14_1-STABLE-HOSTNAME-001) | carried unresolved from B14.1; the literal hostname is operator-owned |
| multi_network_smoke_result_records | HUMAN_ACTION_REQUIRED (HAR-B15-MULTI-NETWORK-SMOKE-001) | the four-vantage-point smoke results require operator runs on networks outside the agent's authority |
| b15_phase_runtime_budget_minutes | not_applicable_current_scope | B15 closure is gated on correctness sentinels and operator evidence, not on wall-clock budget |

```yaml
threshold_audit_summary:
  numeric_thresholds_introduced_in_B15: 0
  HUMAN_ACTION_REQUIRED_entries: 3 (HAR-B14_1-STABLE-HOSTNAME-001 and HAR-B14_1-FUNNEL-CAPABILITY-001 carried; HAR-B15-MULTI-NETWORK-SMOKE-001 new)
  fixed_value_entries: 3 (vantage points, curated examples, degradations)
  not_applicable_current_scope_entries: 2
```

## 3. Marker registry

Every marker from orchestrator_plan section 6 has a recovery packet in section 11 below. Markers fire from validators or from session-open detection. Active markers block phase gate closure.

## 4. Linear transition table

| Current state | Condition | Marker on fail | Next on PASS | Next on FAIL | Report shape | Approval required |
|---|---|---|---|---|---|---|
| session-open | tracker readable; current_task is the B15 entry; B14.1 PHASE_APPROVED predicates hold; plan_authoring_approvals.B15 == APPROVED_FOR_EXECUTION | TRACKER_MISSING or TRACKER_MISMATCH | B15-00 | stop | planning_report | yes |
| B15-00 | plan compiler passes for docs/plans/b15/ and the two B15 wrapper validators exist | PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP | B15-01 | stop | execution_report | yes |
| B15-01 | scripts/rp5/validate_b15_coverage_matrix.py and scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py materialized with their two paired fixture generators; b15_coverage_matrix.md authored as a multi_network_smoke_coverage_record enumerating all four vantage points and all nine coverage items; no public URL, hostname, or secret literal committed | B15_MULTI_NETWORK_COVERAGE_GAP or PLAN_CONFLICT | B15-02 | B15-01 fix | execution_report | yes |
| B15-02 | multi-network smoke harness validators materialized; harness consumes declarative records and performs no public network call during validation; fixtures present | VALIDATOR_MATERIALIZATION_GAP or EXECUTION_RAIL_GAP | B15-03 | B15-02 fix | execution_report | yes |
| B15-03 | b15_human_action_packet.md authored declaring HAR-B14_1-STABLE-HOSTNAME-001, HAR-B14_1-FUNNEL-CAPABILITY-001 residual, and HAR-B15-MULTI-NETWORK-SMOKE-001 with required evidence shapes | HUMAN_ACTION_REQUEST_MALFORMED | B15-04 | B15-03 fix | execution_report | yes |
| B15-04 | HAR-gated: operator-supplied human-action evidence resolves HAR-B14_1-STABLE-HOSTNAME-001 and HAR-B14_1-FUNNEL-CAPABILITY-001 residual; public-exposure bring-up evidence record authored | HUMAN_ACTION_REQUIRED or B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED | B15-05 | B15-04 BLOCKED_BY_HUMAN_ACTION | execution_report | yes |
| B15-05 | HAR-gated: operator-supplied multi-network smoke-result records for all four vantage points and all nine coverage items; every record cites operator evidence; structural validators (smoke_result_evidence, multi_network_smoke) and the no-public-URL/hostname-literal sweep emit OK; closure status is PASS when every per-marker validator emits OK, or PASS_WITH_OBSERVED_REGRESSION when one or more regression-class markers fire honestly without fabrication or coverage gap (firing markers carried forward as observed_regression_markers; see §10 Done-when and the state-transition map below) | HUMAN_ACTION_REQUIRED or B15_SMOKE_RESULT_FABRICATED or B15_MULTI_NETWORK_COVERAGE_GAP | B15-06 | B15-05 BLOCKED_BY_HUMAN_ACTION or B15-05 fix | execution_report | yes |
| B15-06 | HAR-gated: smoke adjudication authored; public_exposure_smoke_claim_record asserts SUCCESS_WITH_STABLE_NAMED_EXPOSURE or an explicit blocker; decision-rule routing record present | B15_EPHEMERAL_URL_SUCCESS_CLAIM or B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE or B15_QUOTA_STATE_MISREPRESENTED or B15_UPLOAD_LIMIT_REGRESSION or B15_MOBILE_LAYOUT_REGRESSION or B15_CACHED_EXAMPLE_REGRESSION or B15_BROUTE_REGRESSION_UNDER_PUBLIC_SMOKE | B15-07 | B15-06 fix or B15-06 BLOCKED_BY_HUMAN_ACTION | execution_report | yes |
| B15-07 | all gate predicates pass through the full-success branch or the explicit-blocker branch | any active B15_* marker | phase gate | first failed task | phase_gate_report | yes |
| any | unauthorized path changed | UNAUTHORIZED_FILE_TOUCHED | stop | stop | execution_report | yes |

State transition map (every terminal state maps to exactly one next legal state):

| State on a task | Next legal state |
|---|---|
| PASS on B15-00..B15-03 | next task in the table; orchestrator records CLOSE_TASK |
| PASS on B15-04..B15-06 (full-success branch) | next task in the table; orchestrator records CLOSE_TASK |
| PASS_WITH_OBSERVED_REGRESSION on B15-05 | next task in the table (B15-06); orchestrator records CLOSE_TASK_WITH_OBSERVED_REGRESSIONS; observed_regression_markers carried forward to B15-06 adjudication; firing regression markers remain active in tracker.markers and are NOT cleared by this closure; the full-success branch at B15-07 is foreclosed by these markers and B15-06 must record claim_status FAILED_PENDING_PHASE_RETURN or BLOCKED_PENDING_HUMAN_ACTION with the corresponding decision-rule routing (RETURN_TO_B14 / RETURN_TO_B11 / RETURN_TO_B10 / RETURN_TO_B8) |
| FAIL on B15-00 | stop; orchestrator records STOP_SCOPE_CONFLICT or REVISE_PLAN |
| FAIL on B15-01..B15-03 | same task fix; orchestrator records FIX_BEFORE_CLOSE |
| FAIL on B15-05 (fabrication or coverage gap only) | same task fix; orchestrator records FIX_BEFORE_CLOSE; regression-class markers raised under honest evidence DO NOT route here -- they route through PASS_WITH_OBSERVED_REGRESSION above |
| FAIL on B15-06 | B15-06 fix; orchestrator records FIX_BEFORE_CLOSE |
| HALTED on any B15 task | same task; orchestrator records FIX_BEFORE_CLOSE after the owning recovery packet PASS |
| HUMAN_ACTION_REQUIRED on B15-04..B15-06 | same task held; orchestrator records CHANGE_SCOPE_with_human_action_request_id; task status set to BLOCKED_BY_HUMAN_ACTION until a human_action_result is recorded |
| BLOCKED_BY_HUMAN_ACTION on B15-04..B15-06 unresolved at B15-07 | B15-07 phase gate passes through the explicit-blocker branch only; orchestrator records PHASE_APPROVE through the explicit-blocker branch or PHASE_REJECT |
| PLAN_CONFLICT on any B15 task | CHANGE_SCOPE; all disagreeing canonical files patched in one commit |
| any marker active at B15-07 | phase gate FAIL on the full-success branch; the explicit-blocker branch may still pass if predicates hold and the active markers are carried-HAR or observed_regression_markers; otherwise orchestrator records PHASE_REJECT |

## 5. Tracker schema and runtime state

```yaml
tracker_file: docs/progress/rp5_progress.yaml
expected_initial_state_at_first_B15_task:
  current_phase: B15
  current_task: B15-00
  last_completed_phase: B14.1
  last_completed_task: B14_1-08
  markers: []
mutation_rules:
  - tracker_writes_only_in_recovery_or_closure: tasks do not write the tracker; closures and recovery do
  - task records appended in order with task_id, status, commit, files_changed, commands_run, key_outputs, marker, next_task per state_packet_schemas.yaml tracker_task_record
  - plan-authoring approval, once granted by the orchestrator, is recorded under tracker.plan_authoring_approvals.B15 with status APPROVED_FOR_EXECUTION, accepted_plan_revision_commit set, and approval_packet_path set
  - phase approval, once granted, is recorded under tracker.phase_approvals.B15 per state_packet_schemas.yaml phase_approval_record
plan_authoring_tracker_advance_policy: during plan authoring this draft advances tracker.current_task and tracker.state_transport.expected_next_task from B15_PENDING_ORCHESTRATOR_INSTRUCTION to B15_PLAN_AUTHORING per the orchestrator-issued REQUEST_PLAN_AUTHORING decision; tracker.plan_authoring_approvals.B15 is NOT created by this draft
```

## 6. Phase gate predicates

Authority lives in orchestrator_plan.md section 3. The agent emits a phase_gate_report after B15-07; the orchestrator records PHASE_APPROVE separately. The phase gate has two pass branches: the full-success branch (public_exposure_smoke_claim_record.claim_status == SUCCESS_WITH_STABLE_NAMED_EXPOSURE) and the explicit-blocker branch (claim_status == BLOCKED_PENDING_HUMAN_ACTION with a carried-HAR citation).

## 7. Final verification checklist

| Check id | Command essence | PASS sentinel | Artifact | Branch |
|---|---|---|---|---|
| FV-PLAN | validate_b15_plan_compile --plan-dir docs/plans/b15 | OK_PLAN_COMPILES | reports/rp5/b15_plan_compile.md | both |
| FV-COVERAGE | validate_b15_coverage_matrix --record reports/rp5/b15_coverage_matrix.md | OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED | reports/rp5/b15_coverage_matrix.md | both |
| FV-SMOKE-EVIDENCE | validate_b15_smoke_result_evidence --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_SMOKE_RESULT_EVIDENCE_TRACED | reports/rp5/b15_multi_network_smoke_results.md | full-success only |
| FV-MULTI-NETWORK | validate_b15_multi_network_smoke --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_MULTI_NETWORK_SMOKE_OR_BLOCKED | reports/rp5/b15_multi_network_smoke_results.md | both |
| FV-RECRUITER | validate_b15_recruiter_gate_preserved_under_public_smoke --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_RECRUITER_GATE_PRESERVED | reports/rp5/b15_multi_network_smoke_results.md | full-success only |
| FV-QUOTA | validate_b15_quota_state_accuracy --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_QUOTA_STATE_ACCURATE | reports/rp5/b15_multi_network_smoke_results.md | full-success only |
| FV-UPLOAD-LIMIT | validate_b15_upload_limit_enforced --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_UPLOAD_LIMIT_ENFORCED | reports/rp5/b15_multi_network_smoke_results.md | full-success only |
| FV-MOBILE | validate_b15_mobile_layout --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_MOBILE_LAYOUT_OK | reports/rp5/b15_multi_network_smoke_results.md | full-success only |
| FV-CACHED | validate_b15_cached_example_integrity --results reports/rp5/b15_multi_network_smoke_results.md | OK_B15_CACHED_EXAMPLE_OK | reports/rp5/b15_multi_network_smoke_results.md | full-success only |
| FV-SMOKE-CLAIM | validate_b15_public_exposure_smoke_claim --adjudication reports/rp5/b15_smoke_adjudication.md | OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED | reports/rp5/b15_smoke_adjudication.md | both |
| FV-NO-PUBLIC-URL | validate_b15_no_public_url_or_hostname_literal --root . | OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | reports/rp5/b15_phase_gate.md | both |
| FV-FUTURE | validate_future_constraints --constraints reports/rp5/b15_future_constraints.md | OK_FUTURE_CONSTRAINTS | reports/rp5/b15_future_constraints.md | both |
| FV-PATH-LOCK | validate_b15_path_locks --diff HEAD~1..HEAD | OK_CHANGED_FILES_PATH_LOCKED | reports/rp5/path_lock_validation.md | both |

Branch column: checks marked "both" are required on the full-success branch and the explicit-blocker branch; checks marked "full-success only" are required when public_exposure_smoke_claim_record.claim_status == SUCCESS_WITH_STABLE_NAMED_EXPOSURE, and on the explicit-blocker branch they are recorded as BLOCKED_PENDING_HUMAN_ACTION with a carried-HAR citation rather than executed.

## 8. Path lock contract

Closure command: `python scripts/rp5/validate_b15_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md`. Sentinel: OK_CHANGED_FILES_PATH_LOCKED. Failure marker: UNAUTHORIZED_FILE_TOUCHED. Result on unauthorized file: STOP_SCOPE_CONFLICT. The B14.1 path-lock validator is not invoked by any B15 task because its PATH_LOCKS list enumerates PL-B14_1-* lock ids only; B15 introduces its own five lock ids plus the protocol entries PROTOCOL-TRACKER and PROTOCOL-RP-REPORTS.

## 9. Validator contracts and fixtures

Each new B15 validator has a paired fixture generator at scripts/rp5/fixtures/ named generate_fixture_validate_b15_ followed by the validator id, producing positive_and_negative fixtures with sha256 manifests. Generator sentinel format: OK_FIXTURE_VALIDATE_B15_ followed by the validator id in UPPER_CASE. Failure marker matches the owning validator's marker per orchestrator_plan section 6. Reusable protocol validators (validate_report_shape, validate_approval_packet, print_tracker_state, print_pending_human_action_requests, validate_no_banned_phrases) are invoked directly. The two report/packet protocol validators scripts/rp5/validate_report_shape.py and scripts/rp5/validate_approval_packet.py were materialized by the B15-03 scope-change repair (orchestrator decision APPROVE_SCOPE_CHANGE_EXECUTION, scope=scope_change, task_id=B15-03) after they were found absent from reachable HEAD; they remain reusable protocol validators with no paired fixture generator and are admitted under PL-B15-SCRIPTS by exact-filename allowlist. The protocol diagnostic helper scripts/rp5/print_pending_human_action_requests.py was materialized by the B15-04 scope-change repair (orchestrator decision APPROVE_SCOPE_CHANGE_EXECUTION, scope=scope_change, task_id=B15-04) after it was found absent from reachable HEAD; it is a pure read-only diagnostic helper that summarizes human-action requests by request_id and status, carries no paired fixture generator, emits no PASS sentinel, and is admitted under PL-B15-SCRIPTS by exact-filename allowlist. validate_future_constraints is profile-parameterized and gains a b15 profile selected from the --constraints filename or an explicit --constraint-profile value, so it is invoked directly without a separate B15 wrapper. The two B15 wrapper validators (validate_b15_plan_compile, validate_b15_path_locks) are created by B15-00 execution; B15-01 creates validate_b15_coverage_matrix and validate_b15_no_public_url_or_hostname_literal together with their two paired fixture generators, because B15-01 must run both validators against its own b15_coverage_matrix.md deliverable; the remaining eight smoke harness validators and their paired fixture generators are created by B15-02 execution. All B15 validators are pure: they read declarative records and fixtures and perform no public network call.

validate_b15_plan_compile must_check contract is inherited from B14.1 section 9 with the additional checks `every_B15_task_next_state_exists`, `every_b15_marker_has_recovery_packet`, and `every_b15_har_record_has_recovery_packet`.

validate_b15_path_locks reproduces the umbrella classifier with PATH_LOCKS entries for PL-B15-PLANS, PL-B15-REPORTS, PL-B15-SCRIPTS, PL-B15-TESTS, PL-B15-CONFIG plus the protocol entries PROTOCOL-TRACKER and PROTOCOL-RP-REPORTS; the `--lock` selector restricts reporting to a single lock id.

### 9.1 Fixture generator contracts for new B15 validators

Ten fixture generators back the ten new B15 smoke harness validators. Two are owned and created by B15-01; the remaining eight are owned and created by B15-02.

B15-01-owned fixture generators (created by B15-01 alongside its two validators):

| Generator id | Script path | Output manifest | Sentinel | Owned marker |
|---|---|---|---|---|
| generate_fixture_validate_b15_coverage_matrix | scripts/rp5/fixtures/generate_fixture_validate_b15_coverage_matrix.py | tests/rp5/fixtures/generate_fixture_validate_b15_coverage_matrix_manifest.json | OK_FIXTURE_VALIDATE_B15_COVERAGE_MATRIX | B15_MULTI_NETWORK_COVERAGE_GAP |
| generate_fixture_validate_b15_no_public_url_or_hostname_literal | scripts/rp5/fixtures/generate_fixture_validate_b15_no_public_url_or_hostname_literal.py | tests/rp5/fixtures/generate_fixture_validate_b15_no_public_url_or_hostname_literal_manifest.json | OK_FIXTURE_VALIDATE_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | B15_PUBLIC_URL_LITERAL_COMMITTED or B15_STABLE_HOSTNAME_LITERAL_COMMITTED |

B15-02-owned fixture generators (created by B15-02):

| Generator id | Script path | Output manifest | Sentinel | Owned marker |
|---|---|---|---|---|
| generate_fixture_validate_b15_multi_network_smoke | scripts/rp5/fixtures/generate_fixture_validate_b15_multi_network_smoke.py | tests/rp5/fixtures/generate_fixture_validate_b15_multi_network_smoke_manifest.json | OK_FIXTURE_VALIDATE_B15_MULTI_NETWORK_SMOKE | B15_MULTI_NETWORK_COVERAGE_GAP |
| generate_fixture_validate_b15_smoke_result_evidence | scripts/rp5/fixtures/generate_fixture_validate_b15_smoke_result_evidence.py | tests/rp5/fixtures/generate_fixture_validate_b15_smoke_result_evidence_manifest.json | OK_FIXTURE_VALIDATE_B15_SMOKE_RESULT_EVIDENCE | B15_SMOKE_RESULT_FABRICATED |
| generate_fixture_validate_b15_recruiter_gate_preserved_under_public_smoke | scripts/rp5/fixtures/generate_fixture_validate_b15_recruiter_gate_preserved_under_public_smoke.py | tests/rp5/fixtures/generate_fixture_validate_b15_recruiter_gate_preserved_under_public_smoke_manifest.json | OK_FIXTURE_VALIDATE_B15_RECRUITER_GATE_PRESERVED | B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE |
| generate_fixture_validate_b15_quota_state_accuracy | scripts/rp5/fixtures/generate_fixture_validate_b15_quota_state_accuracy.py | tests/rp5/fixtures/generate_fixture_validate_b15_quota_state_accuracy_manifest.json | OK_FIXTURE_VALIDATE_B15_QUOTA_STATE_ACCURACY | B15_QUOTA_STATE_MISREPRESENTED |
| generate_fixture_validate_b15_upload_limit_enforced | scripts/rp5/fixtures/generate_fixture_validate_b15_upload_limit_enforced.py | tests/rp5/fixtures/generate_fixture_validate_b15_upload_limit_enforced_manifest.json | OK_FIXTURE_VALIDATE_B15_UPLOAD_LIMIT_ENFORCED | B15_UPLOAD_LIMIT_REGRESSION |
| generate_fixture_validate_b15_mobile_layout | scripts/rp5/fixtures/generate_fixture_validate_b15_mobile_layout.py | tests/rp5/fixtures/generate_fixture_validate_b15_mobile_layout_manifest.json | OK_FIXTURE_VALIDATE_B15_MOBILE_LAYOUT | B15_MOBILE_LAYOUT_REGRESSION |
| generate_fixture_validate_b15_cached_example_integrity | scripts/rp5/fixtures/generate_fixture_validate_b15_cached_example_integrity.py | tests/rp5/fixtures/generate_fixture_validate_b15_cached_example_integrity_manifest.json | OK_FIXTURE_VALIDATE_B15_CACHED_EXAMPLE_INTEGRITY | B15_CACHED_EXAMPLE_REGRESSION |
| generate_fixture_validate_b15_public_exposure_smoke_claim | scripts/rp5/fixtures/generate_fixture_validate_b15_public_exposure_smoke_claim.py | tests/rp5/fixtures/generate_fixture_validate_b15_public_exposure_smoke_claim_manifest.json | OK_FIXTURE_VALIDATE_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM | B15_EPHEMERAL_URL_SUCCESS_CLAIM |

Each generator command takes `--kind positive_and_negative --manifest <output manifest path>` and emits the sentinel in the table. validate_b15_plan_compile and validate_b15_path_locks are wrapper validators and carry no separate fixture generator; their fixtures are the B15 plan triad and the diff range.

## 10. Task contracts

| Task | Preconditions | Action title | Deliverable | Validators | Done when | HAR-gated | Stop |
|---|---|---|---|---|---|---|---|
| B15-00 | tracker readable; B14.1 PHASE_APPROVED; plan-authoring APPROVE_FOR_EXECUTION recorded | create the two B15 wrapper validators (scripts/rp5/validate_b15_plan_compile.py and scripts/rp5/validate_b15_path_locks.py) and emit reports/rp5/b15_plan_compile.md | reports/rp5/b15_plan_compile.md + the two wrapper scripts | validate_b15_plan_compile, validate_b15_path_locks | OK_PLAN_COMPILES + OK_CHANGED_FILES_PATH_LOCKED | no | execution_report |
| B15-01 | B15-00 PASS | materialize scripts/rp5/validate_b15_coverage_matrix.py and scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py with their two paired fixture generators and manifests, then author the multi-network smoke coverage matrix: a multi_network_smoke_coverage_record enumerating the four network vantage points and the nine coverage items, each with planned-status PENDING_OPERATOR_EVIDENCE | reports/rp5/b15_coverage_matrix.md + scripts/rp5/validate_b15_coverage_matrix.py + scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py + scripts/rp5/fixtures/generate_fixture_validate_b15_coverage_matrix.py + scripts/rp5/fixtures/generate_fixture_validate_b15_no_public_url_or_hostname_literal.py + the two paired tests/rp5/fixtures/ manifests | validate_b15_coverage_matrix, validate_b15_no_public_url_or_hostname_literal, both paired generators (positive_and_negative) | OK_B15_COVERAGE_MATRIX_COMPLETE_OR_BLOCKED + OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL + OK_FIXTURE_VALIDATE_B15_COVERAGE_MATRIX + OK_FIXTURE_VALIDATE_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | no | execution_report |
| B15-02 | B15-01 PASS | materialize the remaining eight smoke harness validators and fixtures (validate_b15_multi_network_smoke, validate_b15_smoke_result_evidence, validate_b15_recruiter_gate_preserved_under_public_smoke, validate_b15_quota_state_accuracy, validate_b15_upload_limit_enforced, validate_b15_mobile_layout, validate_b15_cached_example_integrity, validate_b15_public_exposure_smoke_claim) plus paired fixture generators; validate_b15_coverage_matrix and validate_b15_no_public_url_or_hostname_literal are already materialized by B15-01 and are reused as validators by downstream B15 tasks; harness performs no public network call | the eight scripts/rp5/validate_b15_*.py + eight fixture generators + manifests + reports/rp5/b15_smoke_harness.md | validate_b15_plan_compile, all eight generators (positive_and_negative) | OK_PLAN_COMPILES + every OK_FIXTURE_VALIDATE_B15_* sentinel | no | execution_report |
| B15-03 | B15-02 PASS | author reports/rp5/b15_human_action_packet.md declaring HAR-B14_1-STABLE-HOSTNAME-001 (carried, unresolved), HAR-B14_1-FUNNEL-CAPABILITY-001 (carried, residual auth-key blocker), and HAR-B15-MULTI-NETWORK-SMOKE-001 (new) with required human-evidence shapes | reports/rp5/b15_human_action_packet.md | validate_approval_packet, validate_report_shape | OK_APPROVAL_PACKET + OK_REPORT_SHAPE | no | execution_report |
| B15-04 | B15-03 PASS; operator-supplied human_action_result resolving HAR-B14_1-STABLE-HOSTNAME-001 and HAR-B14_1-FUNNEL-CAPABILITY-001 residual | author reports/rp5/b15_public_exposure_bringup.md as a public_exposure_bringup_record citing the operator-supplied evidence by reference; if no human_action_result exists, emit HUMAN_ACTION_REQUIRED and set task status BLOCKED_BY_HUMAN_ACTION | reports/rp5/b15_public_exposure_bringup.md | validate_b15_no_public_url_or_hostname_literal, print_pending_human_action_requests | OK_B15_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL and bring-up evidence referenced, or BLOCKED_BY_HUMAN_ACTION | yes | execution_report |
| B15-05 | B15-04 PASS; operator-supplied multi-network smoke-result evidence resolving HAR-B15-MULTI-NETWORK-SMOKE-001 | author reports/rp5/b15_multi_network_smoke_results.md as multi_network_smoke_result_records (one per vantage point, each covering the nine items) each citing operator evidence; if no evidence exists, emit HUMAN_ACTION_REQUIRED and set status BLOCKED_BY_HUMAN_ACTION | reports/rp5/b15_multi_network_smoke_results.md | validate_b15_smoke_result_evidence, validate_b15_multi_network_smoke, validate_b15_recruiter_gate_preserved_under_public_smoke, validate_b15_quota_state_accuracy, validate_b15_upload_limit_enforced, validate_b15_mobile_layout, validate_b15_cached_example_integrity | structural validators (smoke_result_evidence, multi_network_smoke) AND the no-public-URL/hostname-literal sweep emit OK AND no fabrication-class marker (B15_SMOKE_RESULT_FABRICATED, B15_MULTI_NETWORK_COVERAGE_GAP) is raised AND either (every per-marker validator emits OK -> status PASS) OR (one or more of the regression-class markers fires honestly -> status PASS_WITH_OBSERVED_REGRESSION with observed_regression_markers recorded for B15-06 carry-forward), or BLOCKED_BY_HUMAN_ACTION on unresolved HAR | yes | execution_report |
| B15-06 | B15-05 PASS | author reports/rp5/b15_smoke_adjudication.md with a public_exposure_smoke_claim_record and a b15_decision_rule_routing_record; the claim asserts SUCCESS_WITH_STABLE_NAMED_EXPOSURE or an explicit blocker; legacy decision-rule routing recorded | reports/rp5/b15_smoke_adjudication.md | validate_b15_public_exposure_smoke_claim | OK_B15_PUBLIC_EXPOSURE_SMOKE_CLAIM_STABLE_OR_BLOCKED, or BLOCKED_BY_HUMAN_ACTION | yes | execution_report |
| B15-07 | B15-06 PASS or B15-04..B15-06 BLOCKED_BY_HUMAN_ACTION with explicit carried-HAR citation | B15 phase gate final-verification checklist + B15 future-constraint records for FC-B15-MULTI-NETWORK, FC-B14-1-PUBLIC-GATE, FC-HANDOFF-DATAMOVE1, FC-BROUTE-FROZEN, FC-B14-0-GATE-PRESERVED | reports/rp5/b15_phase_gate.md and reports/rp5/b15_future_constraints.md | every applicable validator from section 7 plus validate_future_constraints | full-success branch or explicit-blocker branch predicates pass and no marker active | no | phase_gate_report; stop for PHASE_APPROVE |

Implementation detail beyond the action-title and deliverable-set is owned by the per-task planning_report at execution time.

### 10.1 Legacy B15.1 success and failure behavior

The legacy demo_platform_plan section 37 Task B15.1 success conditions and decision rules are encoded deterministically below. The b15_decision_rule_routing_record authored at B15-06 records the routing outcome.

```yaml
legacy_b15_1_success_conditions:
  public_url_works: recorded PASS only when a stable-named exposure is operator-supplied by reference and reached from at least one vantage point
  no_critical_ui_path_fails: recorded PASS only when every smoke-result record reports no critical UI path failure
  upload_limits_enforced: recorded PASS only when validate_b15_upload_limit_enforced emits OK_B15_UPLOAD_LIMIT_ENFORCED
  quota_states_accurate: recorded PASS only when validate_b15_quota_state_accuracy emits OK_B15_QUOTA_STATE_ACCURATE
  url_shareable: recorded SUCCESS_WITH_STABLE_NAMED_EXPOSURE only when all of the above PASS and the hostname is supplied by reference
legacy_b15_1_decision_rules:
  - if a mobile_cellular or mobile_layout smoke-result record reports failure: b15_decision_rule_routing_record.routing = RETURN_TO_B11; B15 phase gate FAIL
  - if the public tunnel fails to expose the surface from any vantage point: routing = RETURN_TO_B14; B15 phase gate FAIL
  - if a provider quota state is misrepresented: routing = RETURN_TO_B10; marker B15_QUOTA_STATE_MISREPRESENTED; B15 phase gate FAIL
  - if a cached curated example fails to resolve: routing = RETURN_TO_B8; marker B15_CACHED_EXAMPLE_REGRESSION; B15 phase gate FAIL
  - if no failure routing fires and all success conditions PASS: routing = PROCEED_TO_B_HANDOFF
  - if operator evidence is absent: routing = BLOCKED_PENDING_HUMAN_ACTION; B15 phase gate passes only through the explicit-blocker branch
```

## 11. Recovery packets

Every marker in section 3 maps to exactly one recovery packet. Each packet defines diagnosis_command, allowed_files_to_inspect, allowed_files_to_modify, retry_limit, next_state_on_recovered, next_state_on_retry_exhausted. Packets that share a name with a B14.1 packet inherit its semantics with the diagnosis_command rewritten to docs/plans/b15/ and the B15 validators.

| Packet id | Marker | Diagnosis command | Allowed inspect | Allowed modify | Retry | Recovered next | Exhausted next |
|---|---|---|---|---|---:|---|---|
| RP-PLAN-CONFLICT | PLAN_CONFLICT | `python scripts/rp5/validate_b15_plan_compile.py --plan-dir docs/plans/b15 --out reports/rp5/b15_plan_conflict.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task or B15-00 | CHANGE_SCOPE |
| RP-TRACKER-MISSING | TRACKER_MISSING | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b15_tracker_missing.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task or B15-00 | CHANGE_SCOPE |
| RP-TRACKER-MISMATCH | TRACKER_MISMATCH | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b15_tracker_mismatch.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task or B15-00 | CHANGE_SCOPE |
| RP-REPORT-SCHEMA-INVALID | REPORT_SCHEMA_INVALID | `python scripts/rp5/validate_report_shape.py --schemas docs/plans/b15/state_packet_schemas.yaml --report-from-tracker latest_context --out reports/rp5/b15_report_schema_invalid.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-APPROVAL-PACKET-MALFORMED | APPROVAL_PACKET_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_approval_packet --out reports/rp5/b15_approval_packet_malformed.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-HUMAN-ACTION-REQUEST-MALFORMED | HUMAN_ACTION_REQUEST_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_human_action_request --out reports/rp5/b15_human_action_request_malformed.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-EXECUTION-RAIL-GAP | EXECUTION_RAIL_GAP | `python scripts/rp5/validate_b15_plan_compile.py --plan-dir docs/plans/b15 --out reports/rp5/b15_execution_rail_gap.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PATH-LOCK-TOO-BROAD | PATH_LOCK_TOO_BROAD | `python scripts/rp5/validate_b15_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b15_path_lock_too_broad.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-VALIDATOR-MATERIALIZATION-GAP | VALIDATOR_MATERIALIZATION_GAP | `python scripts/rp5/validate_b15_plan_compile.py --plan-dir docs/plans/b15 --out reports/rp5/b15_validator_materialization_gap.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-RECOVERY-PACKET-GAP | RECOVERY_PACKET_GAP | `python scripts/rp5/validate_b15_plan_compile.py --plan-dir docs/plans/b15 --out reports/rp5/b15_recovery_packet_gap.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-UNAUTHORIZED-FILE-TOUCHED | UNAUTHORIZED_FILE_TOUCHED | `python scripts/rp5/validate_b15_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b15_unauthorized_file_touched.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | STOP_SCOPE_CONFLICT |
| RP-HUMAN-ACTION-REQUIRED | HUMAN_ACTION_REQUIRED | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/b15_pending_human_action.md` | docs/plans/b15, tracker, reports/rp5 | none until a human_action_result is recorded | 0 | same task | CHANGE_SCOPE |
| RP-FUTURE-CONSTRAINT-REGRESSION | FUTURE_CONSTRAINT_REGRESSION | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/b15_future_constraints.md --constraint-profile b15 --out reports/rp5/b15_future_constraint_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PUBLIC-SECURITY-REGRESSION | PUBLIC_SECURITY_REGRESSION | `python scripts/rp5/validate_b15_recruiter_gate_preserved_under_public_smoke.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_public_security_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-PUBLIC-EXPOSURE-NOT-HUMAN-GATED | B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/b15_public_exposure_not_human_gated.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-SMOKE-RESULT-FABRICATED | B15_SMOKE_RESULT_FABRICATED | `python scripts/rp5/validate_b15_smoke_result_evidence.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_smoke_result_fabricated.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-MULTI-NETWORK-COVERAGE-GAP | B15_MULTI_NETWORK_COVERAGE_GAP | `python scripts/rp5/validate_b15_multi_network_smoke.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_multi_network_coverage_gap.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-EPHEMERAL-URL-SUCCESS-CLAIM | B15_EPHEMERAL_URL_SUCCESS_CLAIM | `python scripts/rp5/validate_b15_public_exposure_smoke_claim.py --adjudication reports/rp5/b15_smoke_adjudication.md --verbose --out reports/rp5/b15_ephemeral_url_success_claim.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-PUBLIC-URL-LITERAL-COMMITTED | B15_PUBLIC_URL_LITERAL_COMMITTED | `python scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py --root . --verbose --out reports/rp5/b15_public_url_literal_committed.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-STABLE-HOSTNAME-LITERAL-COMMITTED | B15_STABLE_HOSTNAME_LITERAL_COMMITTED | `python scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py --root . --component hostname_only --verbose --out reports/rp5/b15_stable_hostname_literal_committed.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-TUNNEL-SECRET-COMMITTED | B15_TUNNEL_SECRET_COMMITTED | `python scripts/rp5/validate_b15_no_public_url_or_hostname_literal.py --root . --component tunnel_secret --verbose --out reports/rp5/b15_tunnel_secret_committed.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE | B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE | `python scripts/rp5/validate_b15_recruiter_gate_preserved_under_public_smoke.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_recruiter_gate_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-QUOTA-STATE-MISREPRESENTED | B15_QUOTA_STATE_MISREPRESENTED | `python scripts/rp5/validate_b15_quota_state_accuracy.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_quota_state_misrepresented.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-UPLOAD-LIMIT-REGRESSION | B15_UPLOAD_LIMIT_REGRESSION | `python scripts/rp5/validate_b15_upload_limit_enforced.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_upload_limit_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-MOBILE-LAYOUT-REGRESSION | B15_MOBILE_LAYOUT_REGRESSION | `python scripts/rp5/validate_b15_mobile_layout.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_mobile_layout_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-CACHED-EXAMPLE-REGRESSION | B15_CACHED_EXAMPLE_REGRESSION | `python scripts/rp5/validate_b15_cached_example_integrity.py --results reports/rp5/b15_multi_network_smoke_results.md --verbose --out reports/rp5/b15_cached_example_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B15-BROUTE-REGRESSION-UNDER-PUBLIC-SMOKE | B15_BROUTE_REGRESSION_UNDER_PUBLIC_SMOKE | `python scripts/rp5/validate_future_constraints.py --constraints reports/rp5/b15_future_constraints.md --constraint-profile b15 --verbose --out reports/rp5/b15_broute_regression.md` | docs/plans/b15, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |

## 12. Security and forbidden scope

| Scope | Reason | Marker |
|---|---|---|
| starting public exposure, Funnel, Tailscale, Cloudflare, or systemd without operator-supplied human-action evidence | public-exposure execution must be human-gated | B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED |
| authoring a smoke-result record without an operator-supplied evidence reference | smoke results must trace to operator evidence | B15_SMOKE_RESULT_FABRICATED |
| claiming multi-network coverage from fewer than four operator-supplied vantage-point records | coverage is verified per vantage point | B15_MULTI_NETWORK_COVERAGE_GAP |
| claim of public-exposure success keyed on an ephemeral URL alone | violates stable-named-exposure semantics | B15_EPHEMERAL_URL_SUCCESS_CLAIM |
| literal public URL commit | forbidden without explicit human approval | B15_PUBLIC_URL_LITERAL_COMMITTED |
| literal stable hostname commit | hostname is operator-owned and recorded by reference only | B15_STABLE_HOSTNAME_LITERAL_COMMITTED |
| committing a real Tailscale auth-key, Cloudflare token, recruiter password, or admin password | secret leak | B15_TUNNEL_SECRET_COMMITTED |
| recruiter gate bypassed during public smoke | violates application-layer gate authority | B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE |
| editing services/**, libs/**, infra/**, or compose files | B15 is verification-only | UNAUTHORIZED_FILE_TOUCHED |
| editing docs/plans/broute/, docs/plans/b14_0/, or docs/plans/b14_1/ | predecessor plans frozen post-approval | UNAUTHORIZED_FILE_TOUCHED |
| editing libs/asr/router_runtime.py | B-route schema frozen | UNAUTHORIZED_FILE_TOUCHED |
| any datamove1 router handoff swap | belongs to B-handoff | FUTURE_CONSTRAINT_REGRESSION |

## 13. Report skeletons

Report shapes are defined in state_packet_schemas.yaml. The B15 plan reuses planning_report, execution_report, phase_gate_report, approval_packet, human_action_request, human_action_result, and supplemental_evidence_report unchanged from the B14.1 schema lineage. New B15-specific records (multi_network_smoke_coverage_record, multi_network_smoke_result_record, public_exposure_bringup_record, public_exposure_smoke_claim_record, b15_decision_rule_routing_record, b15_closure_report) are defined in state_packet_schemas.yaml. Reports are compact and evidence-focused; the phase_gate_report at B15-07 cites every applicable FV-* sentinel and one row per future-constraint preservation record, and no more.

## 14. Banned phrases and no-improvisation scan

Banned phrases registry is inherited from the B14.1 agent_plan section 14 verbatim. Scan command:

```bash
grep -nE '(as needed|as appropriate|as required|if already present|where appropriate|best practices|TBD|free-form|free form)' docs/plans/b15/agent_plan.md docs/plans/b15/orchestrator_plan.md | grep -v 'section_14\|banned_phrases\|forbidden_orchestrator_outputs'
```

Expected: zero rows.

## 15. Human action requests

The HAR transport (CHANGE_SCOPE_with_human_action_request_id) is inherited from B14.1. Two HARs are carried forward from B14.1 and one is new for the multi-network smoke run.

| HAR id | Status entering B15 | Trigger marker | Missing inputs | Blocking scope | Required human result shape |
|---|---|---|---|---|---|
| HAR-B14_1-STABLE-HOSTNAME-001 | pre_declared_unresolved (carried) | HUMAN_ACTION_REQUIRED | stable_hostname_supplied_as_host_env_PUBLIC_DEMO_STABLE_HOSTNAME, stable_hostname_owned_by_operator_account, dns_or_tailnet_funnel_record_active | blocks B15-04 closure and any B15 public-exposure success claim | operator supplies the hostname only by reference (env-var name and "supplied: true"); the literal hostname is never recorded in tracker, approval packets, or any committed file |
| HAR-B14_1-FUNNEL-CAPABILITY-001 | partially_resolved_at_B14_1-04_threshold (carried) | HUMAN_ACTION_REQUIRED | tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY (residual; the other inputs were supplied at B14_1-04) | blocks B15-04 closure (the tunnel must actually run for a multi-network smoke) | operator declares the auth-key supplied as host env "supplied: true"; the auth-key value is never read, echoed, or committed |
| HAR-B15-MULTI-NETWORK-SMOKE-001 | new (pre_declared_unresolved) | HUMAN_ACTION_REQUIRED | smoke_result_windows_local, smoke_result_mobile_cellular, smoke_result_other_wifi, smoke_result_vpn_or_external_tester | blocks B15-05 closure and the B15 phase-gate full-success branch | operator runs the smoke from each of the four vantage points and supplies one declarative result record per vantage point with an evidence reference; no literal public URL, hostname, or secret is recorded |

```yaml
HAR-B15-MULTI-NETWORK-SMOKE-001:
  status: pre_declared_unresolved
  marker: HUMAN_ACTION_REQUIRED
  missing_inputs:
    - smoke_result_windows_local
    - smoke_result_mobile_cellular
    - smoke_result_other_wifi
    - smoke_result_vpn_or_external_tester
  why_human_only: a multi-network public smoke requires the operator to reach the public surface from four distinct networks outside the agent's host and authority; the agent must not fabricate network results
  allowed_values_or_schema:
    each_smoke_result: a multi_network_smoke_result_record per state_packet_schemas.yaml, covering the nine coverage items, with an operator evidence_reference and no literal public URL, hostname, or secret
  blocks: B15-05 closure and the B15 phase-gate full-success branch
  created_by_task: B15.1 plan authoring (this draft) and re-declared by B15-03
  next_state_until_result: agent waits at B15-05 with task status BLOCKED_BY_HUMAN_ACTION; the phase gate may pass only through the explicit-blocker branch until results are supplied
  forbidden_agent_action: fabricating smoke results; inventing network vantage-point outcomes; recording literal public URLs, hostnames, or secrets
  result_expected_at: before APPROVE_PLAN for B15-05, or recorded as an explicit blocker at B15-07
  result_recording_policy:
    - the human_action_result captures coverage-item PASS/FAIL flags and an evidence_reference per vantage point only
    - literal public URLs, hostnames, auth-keys, and tokens are never written into tracker, approval packets, or any committed file
```

## 16. Context-window hygiene

```yaml
context_window_hygiene_policy:
  trigger_kind_task_count_within_phase: prefer a new Claude window after every two or three executed B15 tasks
  trigger_kind_phase_boundary: prefer a new Claude window at the B14.1->B15 boundary and at the B15->B-handoff boundary
  recommended_actions:
    - after B15-02 closure, prefer a new Claude window before B15-03 planning
    - after B15-05 closure, prefer a new Claude window before B15-06 planning
    - at the B15-07 phase gate boundary, prefer a new Claude window before any B-handoff plan-authoring step
```

## 17. Authoring status

```yaml
authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
plan_authoring_orchestrator_decision_scope: plan_authoring
plan_authoring_orchestrator_decision_input_accepted_report_commit: 63fefd061ee56873c51fb72f4baab333aa86740c
b14_1_accepted_phase_gate_report_commit: f2a64d5619e34db99802595c0ce4ea9ae2e2d5f1
b14_1_accepted_tracker_closure_commit: 360bc2bd8a3d7d42a1886d82cccd3f77b5de7d84
tracker_advance_policy: this draft advances tracker.current_task and tracker.state_transport.expected_next_task from B15_PENDING_ORCHESTRATOR_INSTRUCTION to B15_PLAN_AUTHORING per the orchestrator-issued REQUEST_PLAN_AUTHORING decision; tracker.plan_authoring_approvals.B15 is NOT created by this draft and will be created by the orchestrator's APPROVE_FOR_EXECUTION decision
no_B15_implementation_task_starts_until:
  - an APPROVE_FOR_EXECUTION decision for this plan package is recorded by the orchestrator
  - an APPROVE_PLAN decision for the first B15 task (B15-00) is recorded after this plan-package approval
  - HAR-B14_1-STABLE-HOSTNAME-001 and HAR-B14_1-FUNNEL-CAPABILITY-001 residual are resolved before B15-04 closure, or B15-04 is recorded BLOCKED_BY_HUMAN_ACTION
  - HAR-B15-MULTI-NETWORK-SMOKE-001 is resolved before B15-05 closure, or B15-05 is recorded BLOCKED_BY_HUMAN_ACTION
```

## 18. Adversarial stress-replay

| Scenario | triggering_event | expected_marker | expected_next_state | result |
|---|---|---|---|---|
| public smoke started without human evidence | B15-04 closure attempt with no human_action_result for HAR-B14_1-STABLE-HOSTNAME-001 | B15_PUBLIC_EXPOSURE_NOT_HUMAN_GATED or HUMAN_ACTION_REQUIRED | B15-04 BLOCKED_BY_HUMAN_ACTION | PASS evidence: print_pending_human_action_requests reports the unresolved HAR; B15-04 cannot close |
| fabricated smoke result | a multi_network_smoke_result_record authored without an operator evidence_reference | B15_SMOKE_RESULT_FABRICATED | B15-05 fix | PASS evidence: validate_b15_smoke_result_evidence emits FAIL on the no-evidence fixture |
| missing vantage point | only three of four vantage-point records present | B15_MULTI_NETWORK_COVERAGE_GAP | B15-05 fix | PASS evidence: validate_b15_multi_network_smoke emits FAIL on the missing-vantage-point fixture |
| ephemeral URL success claim | b15_smoke_adjudication.md records SUCCESS_WITH_STABLE_NAMED_EXPOSURE while stable hostname supplied-by-reference is false | B15_EPHEMERAL_URL_SUCCESS_CLAIM | B15-06 fix or BLOCKED_BY_HUMAN_ACTION | PASS evidence: validate_b15_public_exposure_smoke_claim enforces the stable-named-exposure rule |
| quota state misrepresented | a smoke-result record reports "AssemblyAI available" while the operator evidence shows quota exhausted | B15_QUOTA_STATE_MISREPRESENTED | B15-05 closes PASS_WITH_OBSERVED_REGRESSION; marker carried forward; B15-06 adjudication records routing RETURN_TO_B10 | PASS evidence: validate_b15_quota_state_accuracy emits FAIL on the mismatch fixture |
| upload limit not enforced | a smoke-result record reports an oversize upload accepted | B15_UPLOAD_LIMIT_REGRESSION | B15-05 closes PASS_WITH_OBSERVED_REGRESSION; marker carried forward; B15-06 adjudication records the corresponding decision-rule routing | PASS evidence: validate_b15_upload_limit_enforced emits FAIL on the oversize-accepted fixture |
| mobile layout regression | a mobile-layout smoke-result record reports horizontal scroll, or reports not_applicable on the mobile_cellular vantage point | B15_MOBILE_LAYOUT_REGRESSION | B15-05 closes PASS_WITH_OBSERVED_REGRESSION; marker carried forward; B15-06 adjudication records routing RETURN_TO_B11 | PASS evidence: validate_b15_mobile_layout emits FAIL on the horizontal-scroll fixture and on the not_applicable-on-mobile_cellular fixture |
| cached example regression | a curated example fails to resolve from cache | B15_CACHED_EXAMPLE_REGRESSION | B15-05 closes PASS_WITH_OBSERVED_REGRESSION; marker carried forward; B15-06 adjudication records routing RETURN_TO_B8 | PASS evidence: validate_b15_cached_example_integrity emits FAIL on the cache-miss fixture |
| recruiter gate bypassed | a smoke-result record reports an unauthenticated 200 on /demo/* | B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE | B15-05 closes PASS_WITH_OBSERVED_REGRESSION; marker carried forward; B15-06 adjudication records routing RETURN_TO_B14 | PASS evidence: validate_b15_recruiter_gate_preserved_under_public_smoke emits FAIL on the unauthenticated-200 fixture |
| public URL literal committed | a committed file contains a non-loopback https URL | B15_PUBLIC_URL_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | PASS evidence: validate_b15_no_public_url_or_hostname_literal emits FAIL on the committed-https fixture |
| application file edited | a B15 task modifies services/api/app/ | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | PASS evidence: validate_b15_path_locks rejects the file outside the B15 lock set |
| router-runtime edit | libs/asr/router_runtime.py modified | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | PASS evidence: path lock validator rejects the file; FC-BROUTE-FROZEN preservation row also fires |

```yaml
stress_replay_summary:
  scenarios_enumerated: 12
  every_scenario_maps_to_existing_marker: true
  every_scenario_maps_to_existing_recovery_packet: true
```
