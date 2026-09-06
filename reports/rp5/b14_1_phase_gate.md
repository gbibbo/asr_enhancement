# B14.1 Phase Gate Report

## STATE SNAPSHOT

- repo_root: /home/gbibbo/code/asr_enhancement
- branch: feature/demo-runtime-rp5-v1
- head_commit_before_b14_1_08: d662acd0b2177f92a021ea619e47f3d0736868f2
- current_phase: B14.1
- current_task: B14_1-08
- last_completed_task: B14_1-07
- active_markers: none
- latest_planning_report: B14_1-08 Revised Planning Report (resumed after FV-FUTURE scope-change fix)
- latest_execution_report: B14_1-08 execution report (this task)
- latest_phase_gate_report: reports/rp5/b14_1_phase_gate.md (this file)

## PHASE

B14.1 — layer Tailscale Funnel public exposure on top of the B14.0 recruiter
HTTPBasic application-layer gate, with deterministic stable-named exposure
semantics, without introducing any application-layer authority that depends on
network trust.

B14.1 task PASS records, each referenced by its accepted execution commit:

| Task | Status | Accepted execution commit |
|---|---|---|
| B14_1-00 | PASS | 8e40543bfdd22206559f5509f60504e61a7bd5c6 |
| B14_1-01 | PASS | 5fab1b7a6fbab33cbd0e7cf76e216df5d13b4b11 |
| B14_1-02 | PASS | bc250b443e44b8f9012a64db807f44aaac088f80 |
| B14_1-03 | PASS | e43c1447887aaa489e135a941dc732acddde9a90 |
| B14_1-04 | PASS | 1b15c41fdb5f20cedf18bfe48bf85b6ff658d01f |
| B14_1-05 | PASS | 4c5c52d7fdab877db99dca6116b82ad79703f316 |
| B14_1-06 | PASS | 831bab969c4de96d150abf7f6a93966af34e4ce8 |
| B14_1-07 | PASS | c116dfd8206796455db067fb77b1c3eef0ccecd2 |

B14_1-08 is the phase-gate final-verification task. The FV-FUTURE PLAN_CONFLICT
was resolved by scope-change commit d662acd0b2177f92a021ea619e47f3d0736868f2,
which made scripts/rp5/validate_future_constraints.py profile-aware while
preserving legacy B-route/B14.0 behavior.

## GATE PREDICATES

- B14_1-00 through B14_1-07 are PASS; B14_1-08 final verification is PASS.
- BR-01..BR-08 statuses remain PASS in the tracker; no B-route rollback.
- B14_0-00..B14_0-08 statuses remain PASS in the tracker; no B14.0 rollback.
- No marker in the marker registry is active.
- No literal public URL committed; no literal stable hostname committed.
- No recruiter, admin, Tailscale auth-key, or Cloudflare token value committed.
- The recruiter HTTPBasic application-layer gate remains the sole authority for
  public /demo/* access under PUBLIC_DEMO_EXPOSURE=true; no network-trust bypass.
- OpenAPI and interactive docs routes are unmounted under PUBLIC_DEMO_EXPOSURE=true.
- The exposure_state_record asserts an explicit blocker (HAR-B14_1-STABLE-HOSTNAME-001);
  the explicit-blocker branch of the phase-gate predicate is the branch satisfied.

## VALIDATION RESULTS

B14_1-08 final-verification checklist — every §7 FV check observed PASS:

| Check id | Sentinel observed | Transcript path |
|---|---|---|
| FV-PLAN | OK_PLAN_COMPILES | /tmp/b14_1_08_plan_compile.md |
| FV-EXPOSURE-STATE | OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED | /tmp/b14_1_08_exposure_state.md |
| FV-APP-GATE | OK_B14_1_APPLICATION_LAYER_GATE | /tmp/b14_1_08_application_layer_gate.md |
| FV-NO-NETWORK-TRUST | OK_B14_1_NO_NETWORK_TRUST_AUTHORITY | /tmp/b14_1_08_no_network_trust.md |
| FV-RECRUITER-PRESERVED | OK_B14_1_RECRUITER_GATE_PRESERVED | /tmp/b14_1_08_recruiter_gate.md |
| FV-HEALTH-UNDER-PUBLIC | OK_B14_1_HEALTH_UNDER_PUBLIC_EXPOSURE | /tmp/b14_1_08_health_payload.md |
| FV-OPENAPI-DOCS | OK_B14_1_OPENAPI_DOCS_OFF | /tmp/b14_1_08_openapi_docs.md |
| FV-NO-PUBLIC-URL | OK_B14_1_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL | /tmp/b14_1_08_no_public_url.md |
| FV-NO-TUNNEL-SECRET | OK_B14_1_NO_TUNNEL_SECRET_LEAK | /tmp/b14_1_08_no_tunnel_secret.md |
| FV-LOCAL-BYPASS | OK_B14_1_LOCAL_BYPASS_JUSTIFIED | /tmp/b14_1_08_local_bypass.md |
| FV-BROUTE-COMPAT-UNDER-PUBLIC | OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE | /tmp/b14_1_08_broute_compatibility.md |
| FV-FUTURE | OK_FUTURE_CONSTRAINTS | /tmp/b14_1_08_future_constraints_validation.md |

Runtime FV checks ran loopback-only against http://127.0.0.1:8001 with
PUBLIC_DEMO_EXPOSURE=true and synthetic env-only recruiter credentials; the
runtime was stopped and DEMO_RUNTIME_ROOT removed before staging.

Path-lock checks for the B14_1-08 deliverable commit:

| Path-lock check | Diff spec | Sentinel |
|---|---|---|
| pre-commit | --diff HEAD | OK_CHANGED_FILES_PATH_LOCKED |
| post-commit | --diff HEAD~1..HEAD | OK_CHANGED_FILES_PATH_LOCKED (confirmed in the B14_1-08 execution report) |

## CLAIM STATUS

claim_status: BLOCKED_PENDING_HUMAN_ACTION

The B14.1 public-exposure claim is blocked. No public-exposure success claim is
asserted. No stable-named-exposure success enum value is asserted. The phase
gate passes on the explicit-blocker branch of its predicate set, not on a
public-exposure success claim.

## FUTURE CONSTRAINTS

Recorded in reports/rp5/b14_1_future_constraints.md, validated FV-FUTURE =
OK_FUTURE_CONSTRAINTS:

| Constraint | out_of_scope_but_preserved | Future phase owner |
|---|---|---|
| FC-B14-1-FUNNEL | true | B14.1 active implementation; preservation owner for B15 and B-handoff |
| FC-B15-MULTI-NETWORK | true | B15 |
| FC-HANDOFF-DATAMOVE1 | true | B-handoff |
| FC-BROUTE-FROZEN | true | B-route (frozen post-approval) |
| FC-B14-0-GATE-PRESERVED | true | B14.1 active implementation; preservation owner for B15 and B-handoff |

## NEXT EXPECTED PHASE

next_expected_phase: B15_PENDING_ORCHESTRATOR_INSTRUCTION

## BLOCKERS

- Primary explicit blocker: HAR-B14_1-STABLE-HOSTNAME-001 (pre_declared_unresolved).
  The stable hostname is operator-owned and was not supplied by reference; this
  blocks the B14.1 public-exposure success claim. Recovery packet:
  RP-HUMAN-ACTION-REQUIRED.
- Residual blocker: HAR-B14_1-FUNNEL-CAPABILITY-001
  (partially_resolved_at_B14_1-04_threshold) with
  tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY=false. This residual
  auth-key host-env input is not supplied; it blocks the B14.1 success claim and
  any future host-execution surface. Recovery packet: RP-HUMAN-ACTION-REQUIRED.
- The agent did not record PHASE_APPROVE and did not record phase_approvals.B14.1.
  The agent is awaiting orchestrator audit, which decides PHASE_APPROVE,
  PHASE_REJECT, FIX_BEFORE_CLOSE, or another legal decision after the B14_1-08
  execution report.
