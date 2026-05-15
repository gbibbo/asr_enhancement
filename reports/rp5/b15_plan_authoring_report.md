# B15 Plan Authoring Report

Scope: plan_authoring (B15). This report records the authoring of the deterministic
B15 plan triad and requests a separate orchestrator plan-authoring approval. It
does not approve the plan, does not start any B15 task, and does not resolve any
carried human-action request.

## 1. STATE BEFORE

```yaml
branch: feature/demo-runtime-rp5-v1
head_before_authoring: 63fefd061ee56873c51fb72f4baab333aa86740c
current_phase: B15
current_task_before: B15_PENDING_ORCHESTRATOR_INSTRUCTION
last_completed_phase: B14.1
last_completed_task: B14_1-08
markers: []
phase_approvals.B14.1.status: APPROVED
plan_authoring_approvals.B15: absent
b15_deterministic_plan_triad: absent
orchestrator_decision_input_accepted_report_commit: 63fefd061ee56873c51fb72f4baab333aa86740c
orchestrator_decision: REQUEST_PLAN_AUTHORING (scope plan_authoring, phase B15)
```

## 2. PLAN FILES AUTHORED

```yaml
authored:
  - docs/plans/b15/orchestrator_plan.md
  - docs/plans/b15/agent_plan.md
  - docs/plans/b15/state_packet_schemas.yaml
authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
companion_report:
  - reports/rp5/b15_plan_authoring_report.md
```

## 3. B15 PLAN SUMMARY

B15 is the public smoke-test phase. The legacy demo_platform_plan section 37
Task B15.1 was converted into a deterministic B14-style triad with linear task
sequencing and no discretionary branching.

Deterministic task table (8 tasks):

| Task | Action | HAR-gated | Public exposure |
|---|---|---|---|
| B15-00 | create B15 wrapper validators; emit plan compile | no | no |
| B15-01 | author multi-network smoke coverage matrix record | no | no |
| B15-02 | materialize smoke harness validators and fixtures | no | no |
| B15-03 | author B15 human-action packet (carried + new HARs) | no | no |
| B15-04 | public-exposure bring-up evidence record | yes | yes |
| B15-05 | multi-network smoke-result records (4 vantage points) | yes | yes |
| B15-06 | smoke adjudication, claim record, decision-rule routing | yes | yes |
| B15-07 | B15 phase gate | no | no |

Key properties encoded:

- B15-00 through B15-03 are docs-only and validator-only tasks, safe without
  public exposure. B15-04 through B15-06 are HAR-gated and cannot start without
  operator-supplied human-action evidence.
- B15 is verification-only: no application, library, infrastructure, compose, or
  runtime file may be modified. File locks PL-B15-PLANS, PL-B15-REPORTS,
  PL-B15-SCRIPTS, PL-B15-TESTS, PL-B15-CONFIG plus the protocol locks bound the
  authorized surface; services/**, libs/**, infra/**, compose, and the frozen
  predecessor plan directories are forbidden paths.
- The transition table maps every PASS, FAIL, HALTED, HUMAN_ACTION_REQUIRED,
  BLOCKED_BY_HUMAN_ACTION, PLAN_CONFLICT, and active-marker state to exactly one
  next legal state.
- The phase gate has two pass branches: a full-success branch
  (claim_status SUCCESS_WITH_STABLE_NAMED_EXPOSURE) and an explicit-blocker
  branch (claim_status BLOCKED_PENDING_HUMAN_ACTION citing a carried HAR).
- The legacy B15.1 scope is encoded exactly: four network vantage points
  (Windows local, mobile cellular, other WiFi, VPN/external tester) and nine
  coverage items (10 curated examples, 5 degradations, Whisper, AssemblyAI,
  upload without GT, upload with manual GT, upload limit, provider quota state,
  mobile layout). The legacy decision rules (mobile failure -> B11, tunnel
  failure -> B14, quota error -> B10, cached-example failure -> B8) are encoded
  in the b15_decision_rule_routing_record schema and agent_plan section 10.1.
- 27 markers, each with exactly one recovery packet; 14 audits; 12 stress-replay
  scenarios; 13 final-verification checks.
- Report schemas authored: planning report and execution report (reused),
  b15_closure_report (new), b15_human_action_packet (new), b15_phase_gate_report
  (alias of phase_gate_report), and phase_approval_record with an explicit note
  that an explicit-blocker-branch B15 approval is not a public-exposure success
  claim.
- accepted_report_commit semantics, marker rules, recovery packets, path locks,
  and phase-gate semantics are encoded across orchestrator_plan sections 1-3, 5-7
  and agent_plan sections 4-5, 8, 11.
- A plan-authoring gate rule (orchestrator_plan section 11) states explicitly
  that B15 implementation cannot begin until this plan package is approved by a
  separate orchestrator decision.

## 4. CARRIED HAR POSTURE

```yaml
HAR-B14_1-STABLE-HOSTNAME-001:
  status: pre_declared_unresolved
  carried_into_b15: true
  resolved_by_b14_1_approval: false
  role_in_b15: primary explicit blocker for any B15 public-exposure success claim; blocks B15-04 closure
HAR-B14_1-FUNNEL-CAPABILITY-001:
  status: partially_resolved_at_B14_1-04_threshold
  residual_blocker: tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY=false
  carried_into_b15: true
  resolved_by_b14_1_approval: false
  role_in_b15: residual blocker for B15-04 closure (the tunnel must run for a multi-network smoke)
HAR-B15-MULTI-NETWORK-SMOKE-001:
  status: pre_declared_unresolved
  new_in_b15: true
  role_in_b15: blocks B15-05 closure and the phase-gate full-success branch until the operator supplies four vantage-point smoke-result records
public_exposure_success_state: BLOCKED_PENDING_HUMAN_ACTION
note: B14.1 approval is preserved only through the explicit-blocker branch and is not a public-exposure success claim. This authoring step resolves no HAR.
```

## 5. TRACKER UPDATE

```yaml
file: docs/progress/rp5_progress.yaml
change:
  current_task: B15_PENDING_ORCHESTRATOR_INSTRUCTION -> B15_PLAN_AUTHORING
  state_transport.expected_next_task: B15_PENDING_ORCHESTRATOR_INSTRUCTION -> B15_PLAN_AUTHORING
unchanged:
  current_phase: B15
  last_completed_phase: B14.1
  last_completed_task: B14_1-08
  markers: []
  phase_approvals: unchanged
  plan_authoring_approvals.B15: not created (orchestrator-owned)
rationale: tracker schema reflects the B15_PLAN_AUTHORING state during plan authoring per the orchestrator REQUEST_PLAN_AUTHORING decision; plan_authoring_approvals.B15 and phase_approvals.B15 are not created by this draft.
```

## 6. FILES CHANGED

```text
docs/plans/b15/orchestrator_plan.md        (new)
docs/plans/b15/agent_plan.md               (new)
docs/plans/b15/state_packet_schemas.yaml   (new)
reports/rp5/b15_plan_authoring_report.md   (new)
docs/progress/rp5_progress.yaml            (modified: B15_PLAN_AUTHORING state)
```

## 7. COMMIT AND PUSH

Recorded in the final report section after commit and push.

## 8. NEXT LEGAL ORCHESTRATOR ACTION

The next step is a B15 plan audit and a separate orchestrator plan-authoring
approval decision (scope plan_authoring, decision APPROVE_FOR_EXECUTION or
REVISE_PLAN). It is not B15 task execution. No B15 task may start until an
APPROVE_FOR_EXECUTION decision creates plan_authoring_approvals.B15 and an
APPROVE_PLAN decision for B15-00 is recorded thereafter.

## 9. BLOCKERS_OR_MARKERS

```yaml
markers: []
carried_blockers:
  - HAR-B14_1-STABLE-HOSTNAME-001: pre_declared_unresolved
  - HAR-B14_1-FUNNEL-CAPABILITY-001: residual tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY=false
public_exposure_success: BLOCKED_PENDING_HUMAN_ACTION
plan_authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
```
