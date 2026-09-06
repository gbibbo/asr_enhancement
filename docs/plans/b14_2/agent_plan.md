# agent_plan.md

Plan state: DRAFT_NOT_APPROVED_FOR_EXECUTION
Project scope: B14.2 repair microphase restoring the application-layer recruiter HTTPBasic gate as the sole authority for the public Funnel-exposed `/demo/*` surface; gate-restoration verified by an operator-supplied four-vantage-point public-surface re-smoke under a new HAR; the upload_with_manual_ground_truth=FAIL secondary observation preserved verbatim from B15-05 and classified at B14_2-05 from B14_2-04 evidence; predecessor canonical files (B-route, B14.0, B14.1, B15) frozen; carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` preserved active through B14_2-00..B14_2-05 and eligible for clearance only at B14.2 PHASE_APPROVE on the gate-restored branch. Future phase B-handoff (datamove1 router swap) preserved but not executable here.
Authority: executable task order, exact commands, validators, fixture generators, marker registry, recovery packets, transition table, tracker mutation rules, path locks, and report skeleton references.

## 0. Manifest and entity registry

```yaml
project: b14_2_repair_microphase_public_surface_recruiter_gate
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
starting_state:
  last_completed_phase: B15
  last_completed_task: B15-07
  current_phase: B14.2_PENDING_ORCHESTRATOR_INSTRUCTION
  current_task: B14.2_PENDING_ORCHESTRATOR_INSTRUCTION
  active_markers_entering_b14_2:
    - B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
canonical_output_files:
  - docs/plans/b14_2/orchestrator_plan.md
  - docs/plans/b14_2/agent_plan.md
  - docs/plans/b14_2/state_packet_schemas.yaml
phases:
  - B14.2
  - B-handoff_future_constraint
tasks:
  - B14_2-00
  - B14_2-01
  - B14_2-02
  - B14_2-03
  - B14_2-04
  - B14_2-05
  - B14_2-06
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
  - B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED
  - B14_2_NETWORK_TRUST_AUTHORITY_DETECTED
  - B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE
  - B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE
  - B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED
  - B14_2_PUBLIC_URL_LITERAL_COMMITTED
  - B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED
  - B14_2_TUNNEL_SECRET_COMMITTED
  - B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE
  - B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED
  - B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP
  - B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION
  - B14_2_EPHEMERAL_URL_SUCCESS_CLAIM
  - B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND
  - B14_2_PREDECESSOR_FILE_TOUCHED
  - B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE   # carried from B15; preserved active through B14_2-00..B14_2-05
validators:
  - validate_b14_2_plan_compile
  - validate_b14_2_path_locks
  - validate_b14_2_public_surface_diagnostic
  - validate_b14_2_application_layer_gate_invariants
  - validate_b14_2_no_network_trust_authority
  - validate_b14_2_recruiter_gate_preserved_under_public_exposure
  - validate_b14_2_health_payload_preserved_under_public_exposure
  - validate_b14_2_openapi_docs_visibility
  - validate_b14_2_no_public_url_or_hostname_literal
  - validate_b14_2_no_tunnel_secret_leak
  - validate_b14_2_broute_compatibility_under_public_exposure
  - validate_b14_2_public_surface_recruiter_gate_resmoke
  - validate_b14_2_upload_with_gt_classification
  - validate_b14_2_recovery_packet_b15_recruiter_gate
  - validate_future_constraints
  - validate_no_banned_phrases
  - validate_report_shape
  - validate_approval_packet
  - print_tracker_state
  - print_pending_human_action_requests
inherited_validators_context_only:
  - validate_b14_0_recruiter_auth_contract
  - validate_b14_0_auth_separation_invariants
  - validate_b14_0_no_credential_leak
  - validate_b14_1_application_layer_gate_invariants
  - validate_b14_1_recruiter_gate_preserved_under_public_exposure
  - validate_b15_recruiter_gate_preserved_under_public_smoke
  - validate_public_security_invariants
artifacts:
  - reports/rp5/b14_2_plan_compile.md
  - reports/rp5/b14_2_public_surface_diagnostic.md
  - reports/rp5/b14_2_application_layer_gate_invariants.md
  - reports/rp5/b14_2_no_network_trust_authority.md
  - reports/rp5/b14_2_recruiter_gate_preserved_under_public_exposure.md
  - reports/rp5/b14_2_health_payload_preserved_under_public_exposure.md
  - reports/rp5/b14_2_openapi_docs_visibility.md
  - reports/rp5/b14_2_no_public_url_or_hostname_literal.md
  - reports/rp5/b14_2_no_tunnel_secret_leak.md
  - reports/rp5/b14_2_broute_compatibility_under_public_exposure.md
  - reports/rp5/b14_2_local_verification.md
  - reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md
  - reports/rp5/b14_2_upload_with_gt_classification.md
  - reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md
  - reports/rp5/b14_2_future_constraints.md
  - reports/rp5/b14_2_phase_gate.md
claims:
  - public_surface_recruiter_gate_restored_by_application_layer_authority_only
  - no_application_layer_authority_decision_keyed_on_network_origin
  - BR-02_health_invariant_preserved_under_repaired_public_exposure
  - openapi_and_docs_unmounted_when_PUBLIC_DEMO_EXPOSURE_true_unless_admin_only_exception
  - public_surface_recruiter_gate_resmoke_records_authenticated_access_only_on_all_four_vantage_points_or_explicit_blocker_recorded
  - no_recruiter_credential_no_admin_credential_no_Tailscale_auth_key_no_Cloudflare_token_committed
  - no_public_URL_no_stable_hostname_literal_no_IP_address_literal_committed
  - BR-01_through_BR-08_B14_0-00_through_B14_0-08_B14_1-00_through_B14_1-08_and_B15-00_through_B15-07_records_remain_frozen
  - upload_with_manual_ground_truth_secondary_observation_classified_or_blocked
  - carried_marker_cleared_only_at_b14_2_phase_approve_on_gate_restored_branch
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
    - all B14.1 deliverables and validators (public-exposure flag plumbing on loopback, no-network-trust invariant, OpenAPI/docs visibility, tunnel template scaffold)
    - all B15 deliverables, reports, and the B15 phase rejection records
    - libs/asr/router_runtime.py (frozen schema)
    - services/frontend/app/demo/types.ts router-field shape (frozen at B14_0-04 and reconfirmed at B14_0-07 and B14_1)
    - structured JSON logs and log rotation policy
    - SQLite job and cache tables
```

| Lock id | Type | Allowed components | Validator command | Max files | Marker on violation |
|---|---|---|---|---:|---|
| PL-B14_2-API-DEMO | exact_directory_with_predicate | application-layer recruiter HTTPBasic gate plumbing and any application-side Funnel-aware wiring in services/api/app/ needed to preserve the gate end-to-end on the public surface; predicate excludes admin auth code (frozen) and any router_runtime adapter | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-API-DEMO --diff HEAD~1..HEAD` | 6 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_2-CONFIG | exact_file_or_create | .env.example placeholders only; real secrets forbidden; compose files (docker-compose*.yml, docker-compose.demo.yml) are forbidden in B14.2; if a future task needs a compose change, a CHANGE_SCOPE decision must update this lock row and the relevant section 10 task contract together in one patch before the compose file may be touched | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-CONFIG --diff HEAD~1..HEAD` | 2 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_2-TESTS | exact_directory_with_predicate | tests/demo/test_b14_2_*.py and tests/rp5/fixtures/ | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-TESTS --diff HEAD~1..HEAD` | 12 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_2-SCRIPTS | exact_directory_with_predicate | scripts/rp5/validate_b14_2_*.py and scripts/rp5/fixtures/generate_fixture_validate_b14_2_*.py and scripts/rp5/smoke_b14_2_*.py; the exact-filename allowlist of scripts/rp5/validate_future_constraints.py is added only via the section 11 scope-change repair recorded in section 22 | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-SCRIPTS --diff HEAD~1..HEAD` | 20 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_2-REPORTS | exact_directory_with_predicate | reports/rp5/b14_2_*.md; B-route, B14.0, B14.1, and B15 reports remain frozen | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-REPORTS --diff HEAD~1..HEAD` | 20 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_2-TUNNEL-TEMPLATE | exact_file_or_create | infra/tunnel/funnel_config.template.yaml or infra/tunnel/funnel_config.template.json placeholder template only; the template carries no real Tailscale auth-key, no Cloudflare token, no stable hostname literal, no public URL literal, no IP address literal | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-TUNNEL-TEMPLATE --diff HEAD~1..HEAD` | 1 | UNAUTHORIZED_FILE_TOUCHED |
| PL-B14_2-TRACKER | exact_file_or_create | docs/progress/rp5_progress.yaml; B14.2 tasks do not write this file; the only writes are orchestrator approval recordings and recovery-packet PASS records, governed by section 5 mutation rules | `python scripts/rp5/validate_b14_2_path_locks.py --lock PL-B14_2-TRACKER --diff HEAD~1..HEAD` | 1 | UNAUTHORIZED_FILE_TOUCHED |

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
ip_address_literal_policy: forbidden in any committed file (loopback 127.0.0.1 inside a script string literal for a local validator base-url is permitted; non-loopback IP literals are forbidden)
ephemeral_url_policy: never a success-claim source; ephemeral URLs may appear in local-only smoke evidence files that are removed before final commit
public_surface_resmoke_vantage_points: [windows_local, mobile_cellular, other_wifi, vpn_or_external_tester]
public_surface_resmoke_required_count: 4
loopback_binding_under_public_exposure_false: required
carried_marker_clearance_policy:
  marker: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
  clearance_allowed_only_at: B14.2 PHASE_APPROVE on the gate-restored branch following RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE PASS
  clearance_forbidden_during: plan_authoring, B14_2-00, B14_2-01, B14_2-02, B14_2-03, B14_2-04, B14_2-05, B14_2-06 task closure, B14.2 phase rejection, any scope-change repair
upload_with_gt_classification_rule:
  inputs: the four public_surface_recruiter_gate_resmoke_record entries authored at B14_2-04
  outputs:
    - linked_to_gate: iff every B14_2-04 record reports recruiter_gate_observed_status authenticated_access_only AND coverage_item_outcomes.upload_with_manual_ground_truth PASS
    - independent_defer: iff every B14_2-04 record reports recruiter_gate_observed_status authenticated_access_only AND any vantage point reports coverage_item_outcomes.upload_with_manual_ground_truth FAIL
    - re_smoke_evidence_pending: iff any B14_2-04 record reports recruiter_gate_observed_status unauthenticated_access_observed
  forbidden:
    - asserting linked_to_gate without the underlying PASS evidence on all four vantage points
    - asserting independent_defer while inventing a cause not directly evidenced by B14_2-04
    - asserting any classification without the four B14_2-04 records present
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
forbidden_in_B14_2:
  - any change to libs/asr/router_runtime.py
  - any change to services/frontend/app/demo/types.ts router-field shape
  - any literal public URL committed
  - any literal stable hostname committed
  - any literal non-loopback IP address committed
  - any Tailscale auth-key, Cloudflare token, recruiter password, or admin password committed
  - any logging of Authorization header values or password or auth-key material
  - any datamove1 router handoff swap
  - any assertion of SUCCESS_WITH_STABLE_NAMED_EXPOSURE in a B14.2 record
  - any clearance of the carried marker outside the gate-restored branch phase-approval recording
  - any conversion of an operator-observed unauthenticated_access_observed value to authenticated_access_only in any record
  - any conversion of an operator-observed upload_with_manual_ground_truth FAIL value to PASS without matching B14_2-04 evidence
  - any edit to docs/plans/broute/, docs/plans/b14_0/, docs/plans/b14_1/, docs/plans/b15/, or any reports/rp5/{broute,b14_0,b14_1,b15}_*.md
  - any systemd unit installation step inside B14.2 (the tunnel run-as-service surface is recorded as a carried HAR by reference; the unit file content can be authored as a template at PL-B14_2-TUNNEL-TEMPLATE but the install action is host-only, deferred to the operator, and not a B14.2 closure deliverable)
  - any claim of success keyed on an ephemeral URL alone
  - any public-network command (Funnel, Tailscale, Cloudflare, ngrok, systemd, Docker Compose, curl against a non-loopback URL, browser tests, or public endpoint checks)
```

### 2.1 Threshold audit

| Category | Status | Source or rationale |
|---|---|---|
| public_surface_recruiter_gate_resmoke_round_trip_latency_seconds | not_applicable_current_scope | B14.2 validates correctness of recruiter-gate authority on the public surface, not network timing |
| tunnel_restart_backoff_seconds_numeric | carried_resolved_by_reference (HAR-B14_1-FUNNEL-CAPABILITY-001) | host-side cloudflared or tailscale restart policy belongs to operator host configuration |
| tailscale_funnel_capability_grant_method | carried_resolved_by_reference (HAR-B14_1-FUNNEL-CAPABILITY-001) | enabling Funnel on the Tailscale account requires operator action outside the agent's authority |
| stable_hostname_string_value | carried_resolved_by_reference (HAR-B14_1-STABLE-HOSTNAME-001) | the literal hostname is operator-owned; agent records only the env-var name and a supplied-by-reference flag |
| recruiter_401_response_under_public_exposure_latency_sla_ms | not_applicable_current_scope | B14.2 validates correctness, not latency budgets |
| openapi_or_docs_admin_only_exception_decision | not_applicable_current_scope_unless_orchestrator_enacts_exception | B14.2 default is unmounted under PUBLIC_DEMO_EXPOSURE=true; the admin-only exception is opt-in and recorded in the b14_2_openapi_docs_visibility.md report |
| b14_2_phase_runtime_budget_minutes | not_applicable_current_scope | B14.2 closure is gated on correctness sentinels, not on wall-clock budget |
| public_surface_resmoke_evidence_freshness_window | HUMAN_ACTION_REQUIRED (HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001) | the operator supplies a non-secret evidence_reference and a non-secret resmoke_run_timestamp_utc; the agent does not invent timing values |

```yaml
threshold_audit_summary:
  numeric_thresholds_introduced_in_B14_2: 0
  HUMAN_ACTION_REQUIRED_entries_new_in_B14_2: 1 (HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001; HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001 is conditional and only fires if B14_2-04 leaves classification undecidable)
  carried_resolved_by_reference_entries: 2 (HAR-B14_1-STABLE-HOSTNAME-001 and HAR-B14_1-FUNNEL-CAPABILITY-001)
  carried_resolved_with_observation_set_entries: 1 (HAR-B15-MULTI-NETWORK-SMOKE-001)
  not_applicable_current_scope_entries: 5
```

## 3. Marker registry

Every marker from orchestrator_plan section 6 has a recovery packet in section 11 below. Markers fire from validators or from session-open detection. Active markers other than the carried `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` block phase gate closure. The carried marker is preserved active by design through B14_2-00..B14_2-05 and is the explicit phase-gate input at B14_2-06; its clearance is governed by the carried_marker_clearance_policy in section 2.

## 4. Linear transition table

| Current state | Condition | Marker on fail | Next on PASS | Next on FAIL | Report shape | Approval required |
|---|---|---|---|---|---|---|
| session-open | tracker readable; current_task is B14.2 entry; B15 PHASE_REJECT predicates hold; carried marker present in tracker.markers | TRACKER_MISSING or TRACKER_MISMATCH | B14_2-00 | stop | planning_report | yes |
| B14_2-00 | plan compiler passes for docs/plans/b14_2/ and B14.2 wrappers exist | PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP | B14_2-01 | stop | execution_report | yes |
| B14_2-01 | declarative diagnostic of the public-surface recruiter-gate regression authored; B15-05 evidence cited by reference only; no edit of B15 reports; no public-network commands run | EXECUTION_RAIL_GAP or B14_2_PREDECESSOR_FILE_TOUCHED | B14_2-02 | B14_2-01 fix | execution_report | yes |
| B14_2-02 | application/config repair authored under PL-B14_2-API-DEMO and optionally PL-B14_2-CONFIG and PL-B14_2-TUNNEL-TEMPLATE; loopback application-layer gate invariants and no-network-trust invariants hold under PUBLIC_DEMO_EXPOSURE=true | B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED or B14_2_NETWORK_TRUST_AUTHORITY_DETECTED | B14_2-03 | B14_2-02 fix | execution_report | yes |
| B14_2-03 | local verification re-emits recruiter-gate-preserved, health-payload-preserved, openapi-docs-visibility, no-public-URL, no-tunnel-secret, and broute-compatibility sentinels against loopback under PUBLIC_DEMO_EXPOSURE=true | B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE or B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE or B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED or B14_2_TUNNEL_SECRET_COMMITTED or B14_2_PUBLIC_URL_LITERAL_COMMITTED or B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE | B14_2-04 | B14_2-03 fix | execution_report | yes |
| B14_2-04 | HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 supplies four public_surface_recruiter_gate_resmoke_record entries; each record carries a non-null non-secret evidence_reference; the agent transcribes operator outcomes verbatim and fabricates nothing | HUMAN_ACTION_REQUIRED or B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED or B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP | B14_2-05 | B14_2-04 stays BLOCKED_BY_HUMAN_ACTION or FIX | execution_report | yes |
| B14_2-05 | upload_with_gt_secondary_observation_record authored; classification deterministically derived from B14_2-04 per the section 2 rule; FAIL observations never converted to PASS without matching B14_2-04 evidence | B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION or REPORT_SCHEMA_INVALID | B14_2-06 | B14_2-05 fix | execution_report | yes |
| B14_2-06 | phase-gate report authored; b14_2_public_surface_claim_record assigns claim_status per the gate-restored / blocked / failed branch selection; recovery-packet PASS for RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE recorded iff B14_2-04 records authenticated_access_only on all four vantage points; carried marker eligible for clearance only at the subsequent PHASE_APPROVE recording on the gate-restored branch | any active non-carried marker or B14_2_EPHEMERAL_URL_SUCCESS_CLAIM or B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND | phase gate | first failed task or FAILED_PENDING_PHASE_RETURN | phase_gate_report | yes |
| any | unauthorized path changed | UNAUTHORIZED_FILE_TOUCHED or B14_2_PREDECESSOR_FILE_TOUCHED | stop | stop | execution_report | yes |
| any | a B14.2 record asserts SUCCESS_WITH_STABLE_NAMED_EXPOSURE or clears the carried marker outside the gate-restored branch | B14_2_EPHEMERAL_URL_SUCCESS_CLAIM or B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND | stop | stop | execution_report | yes |

## 5. Tracker schema and runtime state

```yaml
tracker_file: docs/progress/rp5_progress.yaml
expected_initial_state_at_first_B14_2_task:
  current_phase: B14.2
  current_task: B14_2-00
  last_completed_phase: B15
  last_completed_task: B15-07
  markers:
    - B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
mutation_rules:
  - tracker_writes_only_in_recovery_or_closure: tasks do not write the tracker; closures and recovery do
  - task records appended in order with task_id, status, commit, files_changed, commands_run, key_outputs, marker, next_task per state_packet_schemas.yaml tracker_task_record
  - plan-authoring approval, once granted by the orchestrator, is recorded under tracker.plan_authoring_approvals.B14.2 with status APPROVED_FOR_EXECUTION, accepted_plan_revision_commit set, and approval_packet_path set
  - the carried marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE is removed from tracker.markers only by the PHASE_APPROVE recording on the gate-restored branch; CLOSE_TASK and CLOSE_TASK_WITH_OBSERVED_REGRESSIONS for any B14_2-NN task preserve it
  - predecessor records (phase_approvals.B-route, B14.0, B14.1, B15; tasks BR-*, B14_0-*, B14_1-*, B15-*; human_action_requests.HAR-B14_1-* and HAR-B15-MULTI-NETWORK-SMOKE-001) are not modified by B14.2 task closures
```

## 6. Phase gate predicates

Authority lives in orchestrator_plan.md section 3. Agent emits a phase_gate_report after B14_2-06 PASS; the orchestrator records PHASE_APPROVE separately and is the only writer that clears the carried marker.

## 7. Final verification checklist

| Check id | Command essence | PASS sentinel | Artifact |
|---|---|---|---|
| FV-PLAN | validate_b14_2_plan_compile --plan-dir docs/plans/b14_2 | OK_PLAN_COMPILES | reports/rp5/b14_2_plan_compile.md |
| FV-PUBLIC-SURFACE-DIAGNOSTIC | validate_b14_2_public_surface_diagnostic --record reports/rp5/b14_2_public_surface_diagnostic.md | OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC | reports/rp5/b14_2_public_surface_diagnostic.md |
| FV-APP-GATE | validate_b14_2_application_layer_gate_invariants --base-url http://127.0.0.1:8001 | OK_B14_2_APPLICATION_LAYER_GATE | reports/rp5/b14_2_application_layer_gate_invariants.md |
| FV-NO-NETWORK-TRUST | validate_b14_2_no_network_trust_authority --base-url http://127.0.0.1:8001 | OK_B14_2_NO_NETWORK_TRUST_AUTHORITY | reports/rp5/b14_2_no_network_trust_authority.md |
| FV-RECRUITER-PRESERVED-LOOPBACK | validate_b14_2_recruiter_gate_preserved_under_public_exposure --base-url http://127.0.0.1:8001 | OK_B14_2_RECRUITER_GATE_PRESERVED | reports/rp5/b14_2_recruiter_gate_preserved_under_public_exposure.md |
| FV-HEALTH-UNDER-PUBLIC | validate_b14_2_health_payload_preserved_under_public_exposure --base-url http://127.0.0.1:8001 | OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE | reports/rp5/b14_2_health_payload_preserved_under_public_exposure.md |
| FV-OPENAPI-DOCS | validate_b14_2_openapi_docs_visibility --base-url http://127.0.0.1:8001 | OK_B14_2_OPENAPI_DOCS_OFF | reports/rp5/b14_2_openapi_docs_visibility.md |
| FV-NO-PUBLIC-URL | validate_b14_2_no_public_url_or_hostname_literal --root . | OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | reports/rp5/b14_2_no_public_url_or_hostname_literal.md |
| FV-NO-TUNNEL-SECRET | validate_b14_2_no_tunnel_secret_leak --base-url http://127.0.0.1:8001 | OK_B14_2_NO_TUNNEL_SECRET_LEAK | reports/rp5/b14_2_no_tunnel_secret_leak.md |
| FV-BROUTE-COMPAT-UNDER-PUBLIC | validate_b14_2_broute_compatibility_under_public_exposure --base-url http://127.0.0.1:8001 | OK_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | reports/rp5/b14_2_broute_compatibility_under_public_exposure.md |
| FV-PUBLIC-SURFACE-RESMOKE | validate_b14_2_public_surface_recruiter_gate_resmoke --record reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md | OK_B14_2_PUBLIC_SURFACE_RECRUITER_GATE_RESMOKE | reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md |
| FV-UPLOAD-WITH-GT-CLASSIFIED | validate_b14_2_upload_with_gt_classification --record reports/rp5/b14_2_upload_with_gt_classification.md | OK_B14_2_UPLOAD_WITH_GT_CLASSIFIED | reports/rp5/b14_2_upload_with_gt_classification.md |
| FV-RP-B15-PASS | validate_b14_2_recovery_packet_b15_recruiter_gate --record reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md | OK_RP_B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE | reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md |
| FV-FUTURE | validate_future_constraints --constraint-profile b14_2 --constraints reports/rp5/b14_2_future_constraints.md | OK_FUTURE_CONSTRAINTS | reports/rp5/b14_2_future_constraints.md |
| FV-REPORT-SHAPE | validate_report_shape --schemas docs/plans/b14_2/state_packet_schemas.yaml --report-from-tracker latest_context | OK_REPORT_SHAPE | n/a (declarative) |
| FV-APPROVAL-PACKET | validate_approval_packet --packet-from-tracker latest | OK_APPROVAL_PACKET | n/a (declarative) |
| FV-NO-BANNED-PHRASES | validate_no_banned_phrases --root docs/plans/b14_2 | OK_NO_BANNED_PHRASES | n/a (declarative) |

## 8. Path lock contract

Closure command: `python scripts/rp5/validate_b14_2_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md`. Sentinel: OK_CHANGED_FILES_PATH_LOCKED. Failure markers: UNAUTHORIZED_FILE_TOUCHED, B14_2_PREDECESSOR_FILE_TOUCHED. Result on unauthorized file: STOP_SCOPE_CONFLICT. Predecessor path-lock validators (validate_b14_0_path_locks, validate_b14_1_path_locks, validate_b15_path_locks) are not invoked by any B14.2 task because each carries phase-hardcoded knowledge of its own lock ids; the B14.2 wrapper is independent and additive and additionally rejects any touch of docs/plans/{broute,b14_0,b14_1,b15}/ or reports/rp5/{broute,b14_0,b14_1,b15}_*.md with marker B14_2_PREDECESSOR_FILE_TOUCHED.

## 9. Validator contracts and fixtures

Each new validator has a paired fixture generator at scripts/rp5/fixtures/ named generate_fixture_validate_b14_2_ followed by the validator id (see the rows in section 9.1 for the exact generator-id-to-script-path mapping) producing positive_and_negative fixtures with sha256 manifests. Generator sentinel format: OK_FIXTURE_VALIDATE_B14_2_ followed by the validator id in UPPER_CASE (see the Sentinel column in section 9.1 for the exact value per validator). Failure marker matches the owning validator's marker per orchestrator_plan section 6. Reusable B-route protocol validators (validate_report_shape, validate_approval_packet, print_tracker_state, print_pending_human_action_requests, validate_no_banned_phrases) are invoked directly because they read declarative schema/HAR/tracker inputs without any phase-hardcoded lock or artifact-name knowledge. validate_future_constraints is profile-parameterized: it carries legacy broute, b14_1, and b15 profiles, and B14.2 introduces a new b14_2 profile through the section 22 scope-change repair; the validator is invoked directly without a separate B14.2 wrapper. The two B14.2 wrappers (validate_b14_2_plan_compile, validate_b14_2_path_locks) replace the inherited scripts that carry phase-hardcoded knowledge; they are created by B14_2-00 execution and live under scripts/rp5/.

validate_b14_2_plan_compile must_check contract is inherited from B14.1 section 9, with the additional checks `every_B14_2_task_next_state_exists`, `every_b14_2_marker_has_recovery_packet`, `every_b14_2_har_record_has_recovery_packet`, `carried_marker_clearance_policy_self_consistent`, and `upload_with_gt_classification_rule_self_consistent`.

validate_b14_2_path_locks reproduces the B-route umbrella classifier with PATH_LOCKS entries for PL-B14_2-API-DEMO, PL-B14_2-FRONTEND (omitted by default; B14.2 default introduces zero frontend changes; the lock is reserved and may be added by a CHANGE_SCOPE decision if a future task requires a UI surface for the operator re-smoke), PL-B14_2-CONFIG, PL-B14_2-TESTS, PL-B14_2-SCRIPTS, PL-B14_2-REPORTS, PL-B14_2-TUNNEL-TEMPLATE, PL-B14_2-TRACKER plus the protocol entries PROTOCOL-TRACKER and PROTOCOL-RP-REPORTS; the `--lock` selector restricts reporting to a single lock id. The umbrella additionally rejects any touch of predecessor canonical files with marker B14_2_PREDECESSOR_FILE_TOUCHED.

### 9.1 Fixture generator contracts for new B14.2 validators

| Generator id | Script path | Command | Output manifest | Sentinel | Owned marker |
|---|---|---|---|---|---|
| generate_fixture_validate_b14_2_public_surface_diagnostic | scripts/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_diagnostic.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_diagnostic.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_diagnostic_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_diagnostic_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_PUBLIC_SURFACE_DIAGNOSTIC | EXECUTION_RAIL_GAP |
| generate_fixture_validate_b14_2_application_layer_gate_invariants | scripts/rp5/fixtures/generate_fixture_validate_b14_2_application_layer_gate_invariants.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_application_layer_gate_invariants.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_application_layer_gate_invariants_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_application_layer_gate_invariants_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_APPLICATION_LAYER_GATE | B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED |
| generate_fixture_validate_b14_2_no_network_trust_authority | scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_network_trust_authority.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_network_trust_authority.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_no_network_trust_authority_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_no_network_trust_authority_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_NO_NETWORK_TRUST | B14_2_NETWORK_TRUST_AUTHORITY_DETECTED |
| generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure | scripts/rp5/fixtures/generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_RECRUITER_GATE_PRESERVED | B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE |
| generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure | scripts/rp5/fixtures/generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE | B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE |
| generate_fixture_validate_b14_2_openapi_docs_visibility | scripts/rp5/fixtures/generate_fixture_validate_b14_2_openapi_docs_visibility.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_openapi_docs_visibility.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_openapi_docs_visibility_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_openapi_docs_visibility_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_OPENAPI_DOCS | B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED |
| generate_fixture_validate_b14_2_no_public_url_or_hostname_literal | scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_public_url_or_hostname_literal.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_public_url_or_hostname_literal.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_no_public_url_or_hostname_literal_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_no_public_url_or_hostname_literal_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | B14_2_PUBLIC_URL_LITERAL_COMMITTED or B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED |
| generate_fixture_validate_b14_2_no_tunnel_secret_leak | scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_tunnel_secret_leak.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_no_tunnel_secret_leak.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_no_tunnel_secret_leak_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_no_tunnel_secret_leak_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_NO_TUNNEL_SECRET_LEAK | B14_2_TUNNEL_SECRET_COMMITTED |
| generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure | scripts/rp5/fixtures/generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE |
| generate_fixture_validate_b14_2_public_surface_recruiter_gate_resmoke | scripts/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_recruiter_gate_resmoke.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_recruiter_gate_resmoke.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_recruiter_gate_resmoke_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_public_surface_recruiter_gate_resmoke_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_PUBLIC_SURFACE_RECRUITER_GATE_RESMOKE | B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED or B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP |
| generate_fixture_validate_b14_2_upload_with_gt_classification | scripts/rp5/fixtures/generate_fixture_validate_b14_2_upload_with_gt_classification.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_upload_with_gt_classification.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_upload_with_gt_classification_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_upload_with_gt_classification_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_UPLOAD_WITH_GT_CLASSIFIED | B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION |
| generate_fixture_validate_b14_2_recovery_packet_b15_recruiter_gate | scripts/rp5/fixtures/generate_fixture_validate_b14_2_recovery_packet_b15_recruiter_gate.py | `python scripts/rp5/fixtures/generate_fixture_validate_b14_2_recovery_packet_b15_recruiter_gate.py --kind positive_and_negative --manifest tests/rp5/fixtures/generate_fixture_validate_b14_2_recovery_packet_b15_recruiter_gate_manifest.json` | tests/rp5/fixtures/generate_fixture_validate_b14_2_recovery_packet_b15_recruiter_gate_manifest.json with sha256 per file | OK_FIXTURE_VALIDATE_B14_2_RECOVERY_PACKET_B15_RECRUITER_GATE | B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND |

## 10. Task contracts

| Task | Preconditions | Action title | Deliverable | Validators | Done when | Stop |
|---|---|---|---|---|---|---|
| B14_2-00 | tracker readable; B15 PHASE_REJECTED; carried marker present in tracker.markers; plan-authoring APPROVE_FOR_EXECUTION recorded | create the two B14.2 wrapper validators (scripts/rp5/validate_b14_2_plan_compile.py and scripts/rp5/validate_b14_2_path_locks.py) and emit reports/rp5/b14_2_plan_compile.md; deliverable commands: `python3 scripts/rp5/validate_b14_2_plan_compile.py --plan-dir docs/plans/b14_2 --out reports/rp5/b14_2_plan_compile.md` and `python3 scripts/rp5/validate_b14_2_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md` | reports/rp5/b14_2_plan_compile.md | validate_b14_2_plan_compile (sentinel OK_PLAN_COMPILES, failure marker PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP); validate_b14_2_path_locks (sentinel OK_CHANGED_FILES_PATH_LOCKED, failure marker UNAUTHORIZED_FILE_TOUCHED or B14_2_PREDECESSOR_FILE_TOUCHED) | OK_PLAN_COMPILES + OK_CHANGED_FILES_PATH_LOCKED | execution_report |
| B14_2-01 | B14_2-00 PASS | declarative diagnostic of the public-surface recruiter-gate regression: read-only synthesis citing reports/rp5/b15_multi_network_smoke_results.md, reports/rp5/b15_smoke_adjudication.md, and reports/rp5/b15_phase_gate.md by reference; bound the regression locus between B14.0 recruiter middleware (loopback), the B14.1 public-exposure flag plumbing (loopback), and the Funnel terminator (host-only); pin the consumed tracker commit bf8560a6c3493692ccd8a35926a5ddc647b627f6 for auditable freezing; no public-network commands; no edits to predecessor reports | reports/rp5/b14_2_public_surface_diagnostic.md | validate_b14_2_public_surface_diagnostic, validate_b14_2_path_locks, validate_no_banned_phrases | OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC + OK_CHANGED_FILES_PATH_LOCKED | execution_report |
| B14_2-02 | B14_2-01 PASS | application/config repair restoring end-to-end recruiter HTTPBasic gate authority on the public Funnel-exposed surface; allowed surfaces: services/api/app/* (PL-B14_2-API-DEMO predicate), infra/tunnel/funnel_config.template.yaml placeholders only (PL-B14_2-TUNNEL-TEMPLATE), .env.example placeholders only (PL-B14_2-CONFIG); loopback verification of application-layer-gate and no-network-trust invariants under PUBLIC_DEMO_EXPOSURE=true | services/api/app/*, infra/tunnel/funnel_config.template.yaml, .env.example, reports/rp5/b14_2_application_layer_gate_invariants.md, reports/rp5/b14_2_no_network_trust_authority.md | validate_b14_2_application_layer_gate_invariants, validate_b14_2_no_network_trust_authority | OK_B14_2_APPLICATION_LAYER_GATE + OK_B14_2_NO_NETWORK_TRUST_AUTHORITY | execution_report |
| B14_2-03 | B14_2-02 PASS | local verification: re-emit BR-02 health, B14.0 auth-contract semantics, B14.1 OpenAPI/docs visibility, no-tunnel-secret, no-public-URL, and broute-compatibility-under-public-exposure sentinels against http://127.0.0.1:8001 under PUBLIC_DEMO_EXPOSURE=true; no mutation of predecessor reports; B14.2 wrappers emit fresh b14_2_*.md artifacts | reports/rp5/b14_2_recruiter_gate_preserved_under_public_exposure.md, reports/rp5/b14_2_health_payload_preserved_under_public_exposure.md, reports/rp5/b14_2_openapi_docs_visibility.md, reports/rp5/b14_2_no_public_url_or_hostname_literal.md, reports/rp5/b14_2_no_tunnel_secret_leak.md, reports/rp5/b14_2_broute_compatibility_under_public_exposure.md, reports/rp5/b14_2_local_verification.md | validate_b14_2_recruiter_gate_preserved_under_public_exposure, validate_b14_2_health_payload_preserved_under_public_exposure, validate_b14_2_openapi_docs_visibility, validate_b14_2_no_public_url_or_hostname_literal, validate_b14_2_no_tunnel_secret_leak, validate_b14_2_broute_compatibility_under_public_exposure | every loopback OK sentinel observed | execution_report |
| B14_2-04 | B14_2-03 PASS; HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 resolved by operator-supplied human_action_result carrying four public_surface_recruiter_gate_resmoke_record entries; agent transcribes operator outcomes verbatim and fabricates nothing | author reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md with one record per vantage point (windows_local, mobile_cellular, other_wifi, vpn_or_external_tester); each record carries non-null non-secret evidence_reference, har_reference HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001, and verbatim coverage_item_outcomes; if any vantage point reports unauthenticated_access_observed, the carried marker remains active and B14_2-04 closes BLOCKED_BY_HUMAN_ACTION or completes with the FAILED outcome propagated to B14_2-06 | reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md | validate_b14_2_public_surface_recruiter_gate_resmoke | OK_B14_2_PUBLIC_SURFACE_RECRUITER_GATE_RESMOKE (PASS only iff all four records record authenticated_access_only with non-null evidence_reference) | execution_report |
| B14_2-05 | B14_2-04 PASS or B14_2-04 BLOCKED_BY_HUMAN_ACTION or B14_2-04 closes with FAILED outcome propagated forward | author reports/rp5/b14_2_upload_with_gt_classification.md as one upload_with_gt_secondary_observation_record; classification derived deterministically from the four B14_2-04 records per the section 2 rule (linked_to_gate / independent_defer / re_smoke_evidence_pending); if classification is independent_defer, emit a secondary_observation_routing_request_record in the same report and explicitly state that B14.2 does not route the secondary observation; if classification is re_smoke_evidence_pending, declare the conditional HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001 unresolved | reports/rp5/b14_2_upload_with_gt_classification.md | validate_b14_2_upload_with_gt_classification | OK_B14_2_UPLOAD_WITH_GT_CLASSIFIED | execution_report |
| B14_2-06 | B14_2-05 PASS | B14.2 phase-gate report and B14.2 future-constraint records for FC-B15-MULTI-NETWORK, FC-B14-1-PUBLIC-GATE, FC-HANDOFF-DATAMOVE1, FC-BROUTE-FROZEN, FC-B14-0-GATE-PRESERVED, FC-B15-FROZEN; author the b14_2_public_surface_claim_record with claim_status per branch (GATE_RESTORED_VERIFIED_BY_OPERATOR_RESMOKE if FV-PUBLIC-SURFACE-RESMOKE PASS, BLOCKED_PENDING_HUMAN_ACTION if B14_2-04 stayed BLOCKED, FAILED_PENDING_PHASE_RETURN if any vantage point recorded unauthenticated_access_observed); author reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md with sentinel OK_RP_B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE only iff the gate-restored branch is selected | reports/rp5/b14_2_phase_gate.md, reports/rp5/b14_2_future_constraints.md, reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md | every validator from section 7 plus validate_future_constraints --constraint-profile b14_2 | every OK sentinel observed; carried marker preserved in this report (its clearance is performed by the subsequent orchestrator PHASE_APPROVE recording, never by this task) | phase_gate_report; stop for PHASE_APPROVE |

Implementation detail beyond the action-title and deliverable-set is owned by the per-task planning_report at execution time.

## 11. Recovery packets

Every marker in section 3 maps to exactly one recovery packet. Each packet defines: diagnosis_command, allowed_files_to_inspect, allowed_files_to_modify, retry_limit, next_state_on_recovered, next_state_on_retry_exhausted. Where the B14.1 plan defined an identical-named packet (PLAN_CONFLICT, TRACKER_*, REPORT_*, APPROVAL_*, EXECUTION_*, PATH_LOCK_*, VALIDATOR_*, RECOVERY_*, UNAUTHORIZED_*, HUMAN_*, FUTURE_*, PUBLIC_SECURITY_*), this plan inherits the packet semantics with the diagnosis_command rewritten to use docs/plans/b14_2/ and the B14.2 validators.

| Packet id | Marker | Diagnosis command | Allowed inspect | Allowed modify | Retry | Recovered next | Exhausted next |
|---|---|---|---|---|---:|---|---|
| RP-PLAN-CONFLICT | PLAN_CONFLICT | `python scripts/rp5/validate_b14_2_plan_compile.py --plan-dir docs/plans/b14_2 --out reports/rp5/b14_2_plan_conflict.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_2-00 | CHANGE_SCOPE |
| RP-TRACKER-MISSING | TRACKER_MISSING | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b14_2_tracker_missing.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_2-00 | CHANGE_SCOPE |
| RP-TRACKER-MISMATCH | TRACKER_MISMATCH | `python scripts/rp5/print_tracker_state.py --tracker-path docs/progress/rp5_progress.yaml --out reports/rp5/b14_2_tracker_mismatch.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task or B14_2-00 | CHANGE_SCOPE |
| RP-REPORT-SCHEMA-INVALID | REPORT_SCHEMA_INVALID | `python scripts/rp5/validate_report_shape.py --schemas docs/plans/b14_2/state_packet_schemas.yaml --report-from-tracker latest_context --out reports/rp5/b14_2_report_schema_invalid.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-APPROVAL-PACKET-MALFORMED | APPROVAL_PACKET_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_approval_packet --out reports/rp5/b14_2_approval_packet_malformed.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-HUMAN-ACTION-REQUEST-MALFORMED | HUMAN_ACTION_REQUEST_MALFORMED | `python scripts/rp5/validate_approval_packet.py --packet-from-tracker pending_human_action_request --out reports/rp5/b14_2_human_action_request_malformed.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-EXECUTION-RAIL-GAP | EXECUTION_RAIL_GAP | `python scripts/rp5/validate_b14_2_plan_compile.py --plan-dir docs/plans/b14_2 --out reports/rp5/b14_2_execution_rail_gap.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PATH-LOCK-TOO-BROAD | PATH_LOCK_TOO_BROAD | `python scripts/rp5/validate_b14_2_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b14_2_path_lock_too_broad.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-VALIDATOR-MATERIALIZATION-GAP | VALIDATOR_MATERIALIZATION_GAP | `python scripts/rp5/validate_b14_2_plan_compile.py --plan-dir docs/plans/b14_2 --out reports/rp5/b14_2_validator_materialization_gap.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-RECOVERY-PACKET-GAP | RECOVERY_PACKET_GAP | `python scripts/rp5/validate_b14_2_plan_compile.py --plan-dir docs/plans/b14_2 --out reports/rp5/b14_2_recovery_packet_gap.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-UNAUTHORIZED-FILE-TOUCHED | UNAUTHORIZED_FILE_TOUCHED | `python scripts/rp5/validate_b14_2_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/b14_2_unauthorized_file_touched.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | STOP_SCOPE_CONFLICT |
| RP-HUMAN-ACTION-REQUIRED | HUMAN_ACTION_REQUIRED | `python scripts/rp5/print_pending_human_action_requests.py --out reports/rp5/b14_2_pending_human_action.md` | docs/plans/b14_2, tracker, reports/rp5 | none until human_action_result is recorded | 0 | same task | CHANGE_SCOPE |
| RP-FUTURE-CONSTRAINT-REGRESSION | FUTURE_CONSTRAINT_REGRESSION | `python scripts/rp5/validate_future_constraints.py --constraint-profile b14_2 --constraints reports/rp5/b14_2_future_constraints.md --out reports/rp5/b14_2_future_constraint_regression.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-PUBLIC-SECURITY-REGRESSION | PUBLIC_SECURITY_REGRESSION | `python scripts/rp5/validate_public_security_invariants.py --base-url http://127.0.0.1:8001 --out reports/rp5/b14_2_public_security_regression.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-APPLICATION-LAYER-GATE-BYPASS | B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED | `python scripts/rp5/validate_b14_2_application_layer_gate_invariants.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_application_layer_gate_bypass.md` | docs/plans/b14_2, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-NETWORK-TRUST-AUTHORITY-DETECTED | B14_2_NETWORK_TRUST_AUTHORITY_DETECTED | `python scripts/rp5/validate_b14_2_no_network_trust_authority.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_network_trust_authority.md` | docs/plans/b14_2, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-EXPOSURE | B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE | `python scripts/rp5/validate_b14_2_recruiter_gate_preserved_under_public_exposure.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_recruiter_gate_regression.md` | docs/plans/b14_2, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-HEALTH-PAYLOAD-REGRESSION-UNDER-PUBLIC-EXPOSURE | B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE | `python scripts/rp5/validate_b14_2_health_payload_preserved_under_public_exposure.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_health_regression.md` | docs/plans/b14_2, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-OPENAPI-OR-DOCS-LEAK-DETECTED | B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED | `python scripts/rp5/validate_b14_2_openapi_docs_visibility.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_openapi_docs_leak.md` | docs/plans/b14_2, tracker, reports/rp5, services/api/app | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-PUBLIC-URL-LITERAL-COMMITTED | B14_2_PUBLIC_URL_LITERAL_COMMITTED | `python scripts/rp5/validate_b14_2_no_public_url_or_hostname_literal.py --root . --verbose --out reports/rp5/b14_2_public_url_literal_committed.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-STABLE-HOSTNAME-LITERAL-COMMITTED | B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED | `python scripts/rp5/validate_b14_2_no_public_url_or_hostname_literal.py --root . --component hostname_only --verbose --out reports/rp5/b14_2_stable_hostname_literal_committed.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-TUNNEL-SECRET-COMMITTED | B14_2_TUNNEL_SECRET_COMMITTED | `python scripts/rp5/validate_b14_2_no_tunnel_secret_leak.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_tunnel_secret_committed.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-BROUTE-REGRESSION-UNDER-PUBLIC-EXPOSURE | B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE | `python scripts/rp5/validate_b14_2_broute_compatibility_under_public_exposure.py --base-url http://127.0.0.1:8001 --verbose --out reports/rp5/b14_2_broute_regression.md` | docs/plans/b14_2, tracker, reports/rp5, services | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-PUBLIC-SURFACE-RESMOKE-FABRICATED | B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED | `python scripts/rp5/validate_b14_2_public_surface_recruiter_gate_resmoke.py --record reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md --verbose --out reports/rp5/b14_2_public_surface_resmoke_fabricated.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-PUBLIC-SURFACE-RESMOKE-COVERAGE-GAP | B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP | `python scripts/rp5/validate_b14_2_public_surface_recruiter_gate_resmoke.py --record reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md --component coverage --verbose --out reports/rp5/b14_2_public_surface_resmoke_coverage_gap.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-UPLOAD-WITH-GT-SILENT-ABSORPTION | B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION | `python scripts/rp5/validate_b14_2_upload_with_gt_classification.py --record reports/rp5/b14_2_upload_with_gt_classification.md --verbose --out reports/rp5/b14_2_upload_with_gt_silent_absorption.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-EPHEMERAL-URL-SUCCESS-CLAIM | B14_2_EPHEMERAL_URL_SUCCESS_CLAIM | `python scripts/rp5/validate_b14_2_recovery_packet_b15_recruiter_gate.py --record reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md --verbose --out reports/rp5/b14_2_ephemeral_url_success_claim.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | CHANGE_SCOPE |
| RP-B14_2-CARRIED-MARKER-CLEARED-OUT-OF-BAND | B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND | `python scripts/rp5/validate_b14_2_recovery_packet_b15_recruiter_gate.py --record reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md --component carried_marker_clearance_policy --verbose --out reports/rp5/b14_2_carried_marker_cleared_out_of_band.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 1 | same task | STOP_SCOPE_CONFLICT |
| RP-B14_2-PREDECESSOR-FILE-TOUCHED | B14_2_PREDECESSOR_FILE_TOUCHED | `python scripts/rp5/validate_b14_2_path_locks.py --diff HEAD~1..HEAD --verbose --out reports/rp5/b14_2_predecessor_file_touched.md` | docs/plans/b14_2, tracker, reports/rp5 | same task owned files only | 0 | n/a | STOP_SCOPE_CONFLICT |
| RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE | B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE (carried) | `python scripts/rp5/validate_b14_2_recovery_packet_b15_recruiter_gate.py --record reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md --out reports/rp5/b14_2_rp_b15_recruiter_gate.md` | docs/plans/b14_2, docs/plans/b15 (read-only), tracker, reports/rp5/b14_2_*, reports/rp5/b15_*.md (read-only) | reports/rp5/b14_2_recovery_packet_b15_recruiter_gate.md only | 1 | B14_2-06 phase gate emits OK_RP_B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE; the orchestrator PHASE_APPROVE on the gate-restored branch clears the marker | the marker remains active and B14.2 phase gate emits FAILED_PENDING_PHASE_RETURN or BLOCKED_PENDING_HUMAN_ACTION |

## 12. Security and forbidden scope

Forbidden in B14.2:

| Scope | Reason | Marker |
|---|---|---|
| any datamove1 router handoff swap | belongs to B-handoff | FUTURE_CONSTRAINT_REGRESSION |
| router schema or cache-key schema change | frozen by B-route | FUTURE_CONSTRAINT_REGRESSION |
| literal public URL commit | pre-plan forbids without explicit human approval | B14_2_PUBLIC_URL_LITERAL_COMMITTED |
| literal stable hostname commit | hostname is operator-owned and recorded by reference only | B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED |
| literal non-loopback IP address commit | IP literals expose host topology | B14_2_PUBLIC_URL_LITERAL_COMMITTED |
| committing real Tailscale auth-key, Cloudflare token, RECRUITER_PASSWORD, or ADMIN_STATS_PASSWORD | secret leak | B14_2_TUNNEL_SECRET_COMMITTED |
| application-layer authority decision keyed on network origin (client IP, source interface, Tailscale identity, X-Forwarded-For) | violates application-layer gate authority invariant | B14_2_NETWORK_TRUST_AUTHORITY_DETECTED |
| OpenAPI or interactive docs mounted unprotected under PUBLIC_DEMO_EXPOSURE=true | unauthenticated docs surface leak | B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED |
| claim of success keyed on an ephemeral URL alone | violates stable-named-exposure semantics | B14_2_EPHEMERAL_URL_SUCCESS_CLAIM |
| asserting SUCCESS_WITH_STABLE_NAMED_EXPOSURE in a B14.2 record | B14.2 cannot make a B15-shape full success claim | B14_2_EPHEMERAL_URL_SUCCESS_CLAIM |
| clearing carried marker outside the gate-restored branch | violates carried_marker_clearance_policy | B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND |
| converting an operator-observed unauthenticated_access_observed value to authenticated_access_only in any record | falsifies operator evidence | B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED |
| converting an operator-observed upload_with_manual_ground_truth FAIL value to PASS without matching B14_2-04 evidence | silently absorbs the secondary observation | B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION |
| editing docs/plans/broute/, docs/plans/b14_0/, docs/plans/b14_1/, or docs/plans/b15/ | predecessor plans frozen post-approval/post-rejection | B14_2_PREDECESSOR_FILE_TOUCHED |
| editing reports/rp5/broute_*.md, reports/rp5/b14_0_*.md, reports/rp5/b14_1_*.md, or reports/rp5/b15_*.md | predecessor reports frozen post-approval/post-rejection | B14_2_PREDECESSOR_FILE_TOUCHED |
| editing libs/asr/router_runtime.py | B-route schema frozen | UNAUTHORIZED_FILE_TOUCHED |
| editing services/frontend/app/demo/types.ts router-field shape | BR-04 contract frozen | UNAUTHORIZED_FILE_TOUCHED |
| installing a systemd unit inside a B14.2 task | systemd install action is host-only and operator-owned; the template file at PL-B14_2-TUNNEL-TEMPLATE may carry placeholders only | UNAUTHORIZED_FILE_TOUCHED |
| running Funnel, Tailscale, Cloudflare, ngrok, systemd, Docker Compose, curl against a non-loopback URL, browser tests, or public endpoint checks inside any B14.2 task | the agent has no public-network execution authority | PUBLIC_SECURITY_REGRESSION |

## 13. Report skeletons

Report shapes are defined in state_packet_schemas.yaml. The B14.2 plan reuses planning_report, execution_report, phase_gate_report, approval_packet, and supplemental_evidence_report unchanged from the B14.1 schema. New B14.2-specific records (public_surface_recruiter_gate_resmoke_record, upload_with_gt_secondary_observation_record, b14_2_public_surface_claim_record, b14_2_closure_report) are defined in state_packet_schemas.yaml.

Reports are compact and evidence-focused. Each execution_report must fit the eight-row schema; verbose narration is excluded by the validate_report_shape contract. The phase_gate_report at B14_2-06 cites every FV-* sentinel and one row per future-constraint preservation record, and no more.

## 14. Banned phrases and no-improvisation scan

Banned phrases registry is inherited from the B-route agent_plan section 14 verbatim. Scan command:

```bash
grep -nE '(as needed|as appropriate|as required|if already present|if present|where appropriate|best practices|obvious|TBD|TODO without a marker|discovered|discover |judgment|free-form|free form)' docs/plans/b14_2/agent_plan.md docs/plans/b14_2/orchestrator_plan.md | grep -v 'section_14\|banned_phrases\|forbidden_orchestrator_outputs'
```

Expected: zero rows.

## 15. Human action requests

The HAR transport (CHANGE_SCOPE_with_human_action_request_id) is inherited from B-route, B14.0, B14.1, and B15. Three carried HARs are recorded as resolved (by-reference for two of them; with the four-vantage-point observation set for HAR-B15-MULTI-NETWORK-SMOKE-001). One new HAR is pre-declared as the explicit input for B14_2-04. One conditional HAR is pre-declared and only fires if B14_2-04 leaves the upload-with-GT classification undecidable.

| HAR id | Trigger marker | Missing inputs | Blocking scope | Required human result shape |
|---|---|---|---|---|
| HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 | HUMAN_ACTION_REQUIRED | four public_surface_recruiter_gate_resmoke_record entries (one per vantage point: windows_local, mobile_cellular, other_wifi, vpn_or_external_tester); per record: recruiter_gate_observed_status enum value, coverage_item_outcomes mapping (including upload_with_manual_ground_truth), evidence_reference (non-secret), resmoke_run_timestamp_utc (non-secret), application_layer_only_no_network_trust_bypass_introduced (boolean) | resolved before B14_2-04 closure; unresolved leaves B14_2-04 BLOCKED_BY_HUMAN_ACTION and the carried marker preserved active | operator supplies the four records verbatim; the literal public URL, hostname, auth-key, token, password, or IP address is never recorded; the agent transcribes the operator outcomes without softening, converting, or fabricating any value |
| HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001 | HUMAN_ACTION_REQUIRED (conditional) | per-vantage-point classification token (linked_to_gate_confirmed_by_resmoke_pass / independent_observed_under_repaired_gate / re_smoke_evidence_pending); optional non-secret diagnostic note | resolved only when B14_2-04 leaves the upload-with-GT classification undecidable from the four resmoke records alone; otherwise the classification at B14_2-05 is derived deterministically without this HAR | operator supplies the classification token per vantage point; the agent does not infer a cause; no secret recorded |

```yaml
HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001:
  status: pre_declared_unresolved
  marker: HUMAN_ACTION_REQUIRED
  missing_inputs:
    - public_surface_recruiter_gate_resmoke_record_windows_local
    - public_surface_recruiter_gate_resmoke_record_mobile_cellular
    - public_surface_recruiter_gate_resmoke_record_other_wifi
    - public_surface_recruiter_gate_resmoke_record_vpn_or_external_tester
  why_human_only: the public-surface re-smoke requires real network access to the Funnel-terminated surface, which only the operator can perform; the agent must not run Funnel, Tailscale, Cloudflare, ngrok, systemd, Docker Compose, curl against a non-loopback URL, browser tests, or public endpoint checks
  allowed_values_or_schema:
    recruiter_gate_observed_status_per_record: [authenticated_access_only, unauthenticated_access_observed]
    coverage_item_outcomes_per_record:
      five_curated_examples: [PASS, FAIL]
      five_degradations: [PASS, FAIL]
      whisper_provider: [PASS, FAIL]
      assemblyai_provider: [PASS, FAIL, EXPLICIT_NA_PROVIDER_DISABLED]
      upload_without_manual_ground_truth: [PASS, FAIL]
      upload_with_manual_ground_truth: [PASS, FAIL]
      upload_limit_enforced: [PASS, FAIL]
      provider_quota_state: string_enum_value
      mobile_layout: [PASS, FAIL, NOT_APPLICABLE]
    evidence_reference_per_record: non-null non-secret token; literal URL, hostname, auth-key, token, password, or IP address never written
    resmoke_run_timestamp_utc_per_record: non-secret ISO-8601 UTC timestamp
    application_layer_only_no_network_trust_bypass_introduced_per_record: boolean
  blocks: B14_2-04 closure and any clearance of B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
  created_by_task: B14.2 plan authoring (this draft)
  next_state_until_result: agent waits at B14_2-04 (or records BLOCKED_BY_HUMAN_ACTION at B14_2-04 if the orchestrator advances the agent without supplying the result)
  forbidden_agent_action: inventing record values; softening unauthenticated_access_observed to authenticated_access_only; converting upload_with_manual_ground_truth FAIL to PASS; running any public-network command
  result_expected_at: before APPROVE_PLAN for B14_2-04, or recorded as the explicit blocker at B14_2-04
  result_recording_policy:
    - the human_action_result captures only enum values, boolean flags, and non-secret evidence_reference and timestamp tokens
    - literal URL, hostname, auth-key, token, password, or IP address values are NEVER written into tracker, approval packets, or any committed file
    - tracker records only the four-record set and an evidence_reference per record

HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001:
  status: pre_declared_conditional
  marker: HUMAN_ACTION_REQUIRED
  missing_inputs:
    - upload_with_gt_per_vantage_classification_token_windows_local
    - upload_with_gt_per_vantage_classification_token_mobile_cellular
    - upload_with_gt_per_vantage_classification_token_other_wifi
    - upload_with_gt_per_vantage_classification_token_vpn_or_external_tester
  why_human_only: classification depends on the same operator re-smoke that resolves the gate observation; the agent does not infer cause from absent evidence
  allowed_values_or_schema:
    per_vantage_classification_token: [linked_to_gate_confirmed_by_resmoke_pass, independent_observed_under_repaired_gate, re_smoke_evidence_pending]
    diagnostic_note: optional non-secret string; no PII, no secret
  blocks: B14_2-05 closure only when the classification cannot be derived deterministically from the four B14_2-04 records under the section 2 upload_with_gt_classification_rule
  created_by_task: B14.2 plan authoring (this draft)
  next_state_until_result: B14_2-05 records the classification as re_smoke_evidence_pending and the agent waits
  forbidden_agent_action: inferring a cause not directly evidenced by the resmoke; absorbing the FAIL observation into a B14.2 fix without a linked_to_gate_confirmed_by_resmoke_pass token; converting FAIL to PASS
  result_expected_at: before APPROVE_PLAN for B14_2-05 when the conditional trigger fires
  result_recording_policy:
    - the human_action_result captures only the per-vantage classification tokens and an optional non-secret diagnostic note
    - no operator outcome is softened or converted
```

Carried HARs (recorded as resolved at B14.2 plan-authoring time):

| Carried HAR id | Status entering B14.2 | Role |
|---|---|---|
| HAR-B14_1-STABLE-HOSTNAME-001 | resolved (by-reference) | preserved; B14.2 references the env-var name only; the literal hostname is never recorded |
| HAR-B14_1-FUNNEL-CAPABILITY-001 | resolved (by-reference) | preserved; B14.2 references the env-var name and restart-policy string only; the auth-key value is never recorded |
| HAR-B15-MULTI-NETWORK-SMOKE-001 | resolved (operator observation set preserved verbatim) | inputs to B14_2-01 diagnostic by reference; never edited from B14.2 |

## 16. Context-window hygiene

```yaml
context_window_hygiene_policy:
  trigger_kind_task_count_within_phase: prefer a new Claude window after every two or three executed B14.2 tasks
  trigger_kind_phase_boundary: prefer a new Claude window at the B15->B14.2 boundary and at the B14.2->next-phase boundary
  rationale: each task in B14.2 produces a compact execution_report; the orchestrator should keep the active context narrow and evidence-focused; the tracker is the durable transport between windows and is consulted at every session-open
  recommended_actions:
    - new Claude window at the B15->B14.2 boundary before B14_2-00 planning
    - new Claude window before B14_2-04 planning so the HAR-resolution exchange has its own context
    - new Claude window before B14_2-06 phase-gate authoring
```

## 17. Authoring status

```yaml
authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
plan_authoring_orchestrator_decision_scope: plan_authoring
plan_authoring_orchestrator_decision_input_accepted_report_commit: null
b15_accepted_phase_gate_report_commit: 6bcfaee57df7a1e8f7026916b472559b3cadcbbc
b15_accepted_tracker_closure_commit: bf8560a6c3493692ccd8a35926a5ddc647b627f6
b15_decision_rule_routing: RETURN_TO_B14
b15_return_target_exact_phase_or_task_id_resolved_by_orchestrator: B14.2
tracker_advance_policy: this draft does NOT advance the tracker; tracker.current_task remains B14_RETURN_PENDING_ORCHESTRATOR_PLAN_AUTHORING until an orchestrator APPROVE_FOR_EXECUTION decision for this plan package is recorded; tracker.plan_authoring_approvals.B14.2 is NOT created by this draft and will be created by the orchestrator's APPROVE_FOR_EXECUTION decision
no_B14_2_implementation_task_starts_until:
  - an APPROVE_FOR_EXECUTION decision for this plan package is recorded by the orchestrator
  - an APPROVE_PLAN decision for the first B14.2 task (B14_2-00) is recorded by the orchestrator after this plan-package approval
  - HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001 is resolved before B14_2-04 closure or is recorded as the explicit blocker at B14_2-04
```

## 18. Adversarial stress-replay

| Scenario | initial_state | triggering_event | expected_marker | expected_next_state | report_shape | plan_sections_used | result |
|---|---|---|---|---|---|---|---|
| network-trust bypass introduced | services/api/app/ adds a path that returns 200 from /demo/* when the client IP matches a private-range or a Tailscale identity header is present | B14_2-02 closure attempt | B14_2_NETWORK_TRUST_AUTHORITY_DETECTED | B14_2-02 fix | execution_report | section 2, section 3, section 4, section 10, section 11, section 12 | PASS evidence: validate_b14_2_no_network_trust_authority emits FAIL on the trust-by-IP and trust-by-header fixtures |
| recruiter gate still bypassed on public surface | B14_2-04 record reports recruiter_gate_observed_status unauthenticated_access_observed on at least one vantage point | B14_2-04 closure attempt | carried B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE remains active; no new marker fired by the record itself | B14_2-04 closes with FAILED outcome propagating to B14_2-06; B14_2-06 records claim_status FAILED_PENDING_PHASE_RETURN | execution_report | section 2, section 4, section 10, section 11 | PASS evidence: validate_b14_2_public_surface_recruiter_gate_resmoke records the observation verbatim; validate_b14_2_recovery_packet_b15_recruiter_gate emits FAIL on the not-all-authenticated fixture |
| fabricated PASS in B14_2-04 record | a public_surface_recruiter_gate_resmoke_record asserts authenticated_access_only with no operator evidence_reference | B14_2-04 closure attempt | B14_2_PUBLIC_SURFACE_RESMOKE_FABRICATED | B14_2-04 fix | execution_report | section 2, section 3, section 4, section 10, section 11, section 12 | PASS evidence: validate_b14_2_public_surface_recruiter_gate_resmoke emits FAIL on the fabricated-PASS fixture |
| only three vantage points supplied | three records authenticated, one missing | B14_2-04 closure attempt | B14_2_PUBLIC_SURFACE_RESMOKE_COVERAGE_GAP | B14_2-04 fix or BLOCKED_BY_HUMAN_ACTION | execution_report | section 2, section 4, section 11 | PASS evidence: validator emits FAIL on partial-coverage fixture |
| ephemeral URL success claim | a B14.2 record asserts SUCCESS_WITH_STABLE_NAMED_EXPOSURE | any B14_2-NN closure | B14_2_EPHEMERAL_URL_SUCCESS_CLAIM | first failing task fix | execution_report | section 2, section 7, section 12 | PASS evidence: validate_b14_2_recovery_packet_b15_recruiter_gate enforces "success claim shape SUCCESS_WITH_STABLE_NAMED_EXPOSURE is not legal in B14.2" |
| carried marker cleared by a task | a B14_2-NN execution_report removes B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE from tracker.markers | any B14_2-NN closure attempt | B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND | STOP_SCOPE_CONFLICT | execution_report | section 2, section 4, section 11 | PASS evidence: validate_b14_2_recovery_packet_b15_recruiter_gate emits FAIL on the marker-cleared-out-of-band fixture |
| upload-with-GT silent absorption | upload_with_gt_secondary_observation_record asserts linked_to_gate while B14_2-04 records any vantage point with upload_with_manual_ground_truth FAIL | B14_2-05 closure attempt | B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION | B14_2-05 fix | execution_report | section 2, section 4, section 11 | PASS evidence: validate_b14_2_upload_with_gt_classification emits FAIL on the silent-absorption fixture |
| OpenAPI mounted unprotected | services/api/app/ mounts /openapi.json unconditionally under PUBLIC_DEMO_EXPOSURE=true | B14_2-03 closure attempt | B14_2_OPENAPI_OR_DOCS_LEAK_DETECTED | B14_2-03 fix | execution_report | section 2, section 3, section 4, section 10, section 11, section 12 | PASS evidence: validate_b14_2_openapi_docs_visibility emits FAIL on the mounted-unprotected fixture |
| recruiter gate regressed under loopback public exposure | services/api/app/ flips PUBLIC_DEMO_EXPOSURE=true and a /demo/* response returns 200 without recruiter auth on loopback | B14_2-03 closure | B14_2_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_EXPOSURE | B14_2-03 fix | execution_report | section 2, section 3, section 4, section 10, section 11, section 12 | PASS evidence: validate_b14_2_recruiter_gate_preserved_under_public_exposure emits FAIL on the unauthenticated-200 fixture |
| /demo/health payload regressed | authenticated /demo/health body deviates from {"status":"ok"} under PUBLIC_DEMO_EXPOSURE=true | B14_2-03 closure | B14_2_HEALTH_PAYLOAD_REGRESSION_UNDER_PUBLIC_EXPOSURE | B14_2-03 fix | execution_report | section 2, section 3, section 4, section 10, section 11, section 12 | PASS evidence: validate_b14_2_health_payload_preserved_under_public_exposure enforces byte-exact equality |
| public URL or hostname literal committed | a committed file contains a non-loopback https URL or the operator's hostname string | any B14_2-NN closure | B14_2_PUBLIC_URL_LITERAL_COMMITTED or B14_2_STABLE_HOSTNAME_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | execution_report | section 3, section 4, section 11, section 12 | PASS evidence: validate_b14_2_no_public_url_or_hostname_literal scans the repo and emits FAIL on the committed-https-non-loopback and committed-hostname fixtures |
| non-loopback IP literal committed | a committed file contains a non-loopback IPv4/IPv6 address literal | any B14_2-NN closure | B14_2_PUBLIC_URL_LITERAL_COMMITTED | FIX_BEFORE_CLOSE | execution_report | section 3, section 4, section 11, section 12 | PASS evidence: validate_b14_2_no_public_url_or_hostname_literal scans for non-loopback IP literals |
| Tailscale auth-key committed | infra/tunnel/funnel_config.template.yaml or any committed file contains a string matching the Tailscale auth-key prefix | any B14_2-NN closure | B14_2_TUNNEL_SECRET_COMMITTED | FIX_BEFORE_CLOSE | execution_report | section 3, section 4, section 11, section 12 | PASS evidence: validate_b14_2_no_tunnel_secret_leak scans for auth-key prefixes and emits FAIL on the committed-auth-key fixture |
| router-runtime edit | libs/asr/router_runtime.py modified | any B14_2-NN commit | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | execution_report | section 1, section 3, section 8, section 11, section 12 | PASS evidence: path lock validator rejects file outside B14.2 lock set; FC-BROUTE-FROZEN preservation row in orchestrator_plan section 3 also fires |
| predecessor plan or report touched | a B14_2-NN commit modifies any file under docs/plans/{broute,b14_0,b14_1,b15}/ or reports/rp5/{broute,b14_0,b14_1,b15}_*.md | any B14_2-NN commit | B14_2_PREDECESSOR_FILE_TOUCHED | STOP_SCOPE_CONFLICT | execution_report | section 1, section 3, section 8, section 11, section 12 | PASS evidence: validate_b14_2_path_locks rejects predecessor-canonical-file touches with marker B14_2_PREDECESSOR_FILE_TOUCHED |
| systemd-unit install inside a task | a B14_2-NN task adds a /etc/systemd/system/*.service file or runs systemctl enable | any B14_2-NN closure | UNAUTHORIZED_FILE_TOUCHED | STOP_SCOPE_CONFLICT | execution_report | section 1, section 3, section 8, section 11, section 12 | PASS evidence: path lock validator rejects file outside B14.2 lock set; section 12 forbidden-scope row also fires |

```yaml
stress_replay_summary:
  scenarios_enumerated: 15
  every_scenario_maps_to_existing_marker: true
  every_scenario_maps_to_existing_recovery_packet: true
```

## 19. Carried-marker accounting

```yaml
carried_marker:
  id: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
  carried_from_phase: B15
  carried_from_task: B15-05 (admission); preserved by B15-06 CLOSE_TASK, B15-07 CLOSE_TASK, B15 PHASE_REJECT
  state_during_b14_2:
    plan_authoring: preserved active
    B14_2-00: preserved active
    B14_2-01: preserved active
    B14_2-02: preserved active
    B14_2-03: preserved active
    B14_2-04: preserved active; the four resmoke records determine whether the marker becomes eligible for clearance at B14_2-06
    B14_2-05: preserved active
    B14_2-06: preserved active; emits RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE PASS only iff all four B14_2-04 records record authenticated_access_only with non-null evidence_reference
    B14.2 PHASE_APPROVE on gate_restored_branch: cleared (removed from tracker.markers by the orchestrator approval recording)
    B14.2 PHASE_APPROVE on blocked_branch: preserved active (not cleared)
    B14.2 PHASE_REJECT: preserved active (not cleared)
  clearance_recording_owner: orchestrator approval recording (never a B14.2 task closure)
  audit_validator: validate_b14_2_recovery_packet_b15_recruiter_gate (component carried_marker_clearance_policy)
```

## 20. Validator-profile scope-change repair (deferred; not executed during plan authoring)

```yaml
scope_change_repair_id: RP-VALIDATOR-PROFILE-GAP-B14_2-06
scope: scope_change
task_id: B14_2-06 (or filed earlier if B14_2-00 surfaces the profile gap)
trigger: scripts/rp5/validate_future_constraints.py supports profiles {broute, b14_1, b15} only; the b14_2 profile is missing and FV-FUTURE is unreachable for B14_2-06
authorized_files_modified_in_repair:
  - scripts/rp5/validate_future_constraints.py
  - scripts/rp5/validate_b14_2_path_locks.py
  - docs/plans/b14_2/agent_plan.md
authorized_files_materialized_in_repair: []
predicate_to_self_test:
  - positive --constraint-profile b14_2 self-test against a six-FC-id b14_2 fixture: OK_FUTURE_CONSTRAINTS
  - positive filename-inference self-test against b14_2_*: OK_FUTURE_CONSTRAINTS
  - negative self-test missing one required B14.2 FC id: FUTURE_CONSTRAINT_REGRESSION
  - negative self-test one extra non-B14.2 FC id (reject_extra_ids=True): FUTURE_CONSTRAINT_REGRESSION
  - regression checks against reports/rp5/b14_1_future_constraints.md, broute_future_constraints.md, b14_0_future_constraints.md, b15_future_constraints.md all still emit OK_FUTURE_CONSTRAINTS (legacy unchanged)
required_b14_2_fc_id_set:
  - FC-B15-MULTI-NETWORK
  - FC-B14-1-PUBLIC-GATE
  - FC-HANDOFF-DATAMOVE1
  - FC-BROUTE-FROZEN
  - FC-B14-0-GATE-PRESERVED
  - FC-B15-FROZEN
reject_extra_ids: true
no_marker_cleared_by_repair: true
no_smoke_outcome_modified_by_repair: true
authorization_to_execute_the_repair: deferred to orchestrator APPROVE_SCOPE_CHANGE_EXECUTION decision; plan-authoring does not perform the repair
precedent: recovery_log.RP-VALIDATOR-PROFILE-GAP-B15-07
```

## 21. Predecessor freeze accounting

```yaml
predecessor_freeze:
  b_route:
    canonical_files_frozen: docs/plans/broute/**, reports/rp5/broute_*.md
    last_approved_phase_gate_report_commit: 4a4f8e4b20ff3ff5f19647e7ec1f723f6492df25
    last_approved_tracker_closure_commit: e6c5aec9139a436e75f783d1df2707d25b385346
  b14_0:
    canonical_files_frozen: docs/plans/b14_0/**, reports/rp5/b14_0_*.md
    last_approved_phase_gate_report_commit: 7e9ce1f7067f938d2b58a7a4e8615101b0012c58
    last_approved_tracker_closure_commit: 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8
  b14_1:
    canonical_files_frozen: docs/plans/b14_1/**, reports/rp5/b14_1_*.md
    last_approved_phase_gate_report_commit: f2a64d5619e34db99802595c0ce4ea9ae2e2d5f1
    last_approved_tracker_closure_commit: 360bc2bd8a3d7d42a1886d82cccd3f77b5de7d84
    approval_branch: explicit_blocker_branch_only
  b15:
    canonical_files_frozen: docs/plans/b15/**, reports/rp5/b15_*.md
    last_rejected_phase_gate_report_commit: 6bcfaee57df7a1e8f7026916b472559b3cadcbbc
    last_rejected_tracker_closure_commit: bf8560a6c3493692ccd8a35926a5ddc647b627f6
    decision: PHASE_REJECT
    decision_rule_routing: RETURN_TO_B14
    claim_status: FAILED_PENDING_PHASE_RETURN
  runtime_files_frozen:
    - libs/asr/router_runtime.py
    - services/frontend/app/demo/types.ts router-field shape
freeze_enforcement:
  primary_validator: validate_b14_2_path_locks (umbrella; marker B14_2_PREDECESSOR_FILE_TOUCHED)
  declarative_validator: validate_future_constraints --constraint-profile b14_2 (FC-BROUTE-FROZEN, FC-B15-FROZEN)
  phase_gate_predicate: orchestrator_plan section 5 final_closure_allowed_only_if.no_predecessor_plan_or_report_file_modified == true
```

## 22. Discipline log

```yaml
discipline_log:
  plan_authoring_decisions:
    - id: PA-B14_2-RETURN-TARGET-RESOLUTION
      decision: orchestrator selected B14.2 as the exact return target after PHASE_RETURN_TARGET_AMBIGUOUS_PENDING_ORCHESTRATOR_DECISION was recorded at B15-07 closure
      input_message: ORCHESTRATOR_DECISION{scope=plan_authoring, task_id=B14_2-PLAN-AUTHORING, phase=B14.2, decision=REQUEST_PLAN_AUTHORING, required_fix="Prepare a new B14.2 repair microphase plan package to address the public-surface recruiter HTTPBasic gate regression routed from B15, without reopening or editing frozen B-route, B14.0, B14.1, or B15 plan/report artifacts."}
      effect: this plan tree was authored
    - id: PA-B14_2-CARRIED-MARKER-CLEARANCE-POLICY
      decision: the carried marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE is clearable only at PHASE_APPROVE on the gate-restored branch
      effect: section 2 carried_marker_clearance_policy and section 19 carried-marker accounting
    - id: PA-B14_2-UPLOAD-WITH-GT-CLASSIFICATION
      decision: the upload_with_manual_ground_truth=FAIL secondary observation is preserved verbatim and classified at B14_2-05 based on B14_2-04 evidence; B14.2 does not route the secondary observation when classification is independent_defer
      effect: section 2 upload_with_gt_classification_rule and section 10 task contract for B14_2-05
    - id: PA-B14_2-VALIDATOR-PROFILE-SCOPE-CHANGE-DEFERRED
      decision: extending validate_future_constraints.py with a b14_2 profile is recorded as a scope-change repair (section 20) and is not executed by plan authoring
      precedent: recovery_log.RP-VALIDATOR-PROFILE-GAP-B15-07
      effect: section 20 scope-change repair documented; section 1 PL-B14_2-SCRIPTS allowlist widening deferred to the scope-change recording
  draft_approval_packet_authoring_convention:
    inspected_precedents:
      - reports/rp5/b15_plan_approval_packet.yaml authored at the orchestrator APPROVE_FOR_EXECUTION recording commit af52260 (not by the plan-authoring task itself)
      - reports/rp5/b14_1_plan_approval_packet.yaml authored after the plan-authoring report at commit 4bd54c2 (plan-authoring report) followed by a separate orchestrator approval recording
    conclusion: plan-authoring tasks do NOT author the *_plan_approval_packet.yaml file; the orchestrator approval recording is the sole writer
    action_in_this_plan_authoring: reports/rp5/b14_2_plan_approval_packet.yaml is NOT created by this plan-authoring task
```
