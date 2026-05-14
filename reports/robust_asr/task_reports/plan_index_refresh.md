# Task Report — plan_index_refresh (CHANGE_SCOPE)

- Task: `plan_index_refresh`
- Type: `scope_change` (administrative pointer refresh; no project technical state altered)
- Phase: `P8`
- Branch: `feature/robust-asr-lora-router-datamove1-v1`
- Authorized at commit: `0073e7b4076ce76d36233bec2eacb4411ba28722`
- Decision packet: `CHANGE_SCOPE(plan_index_refresh)` recorded as `latest_approval_packet`

## Rationale

The live corrected State Packet established that `ROBUST_ASR_PROFILE`
(declared inside `CLAUDE.md` between the `BEGIN ROBUST_ASR_PROFILE` and
`END ROBUST_ASR_PROFILE` delimiters) is the active profile on this
branch; that `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` and
`docs/plans/robust_asr_agent_plan_v3_4_7.md` are the active plans; that
`docs/plans/state_packet_schemas_v1.yaml` is the active schema; and that
`docs/plans/training_datamove1_plan.md` is legacy/template-only. Stale
references in `plan.md` and in the upper Sections 1–23 of `CLAUDE.md`
(training/datamove1 profile body) caused a prior false `PLAN_CONFLICT`
diagnosis. This scope change refreshes the entry-point documentation
only; it does not alter any P8 evidence, the P8 gate predicate, or any
project technical state.

## Changes applied

1. `plan.md` — rewritten as the branch entry point. Declares the active
   profile, the two active plans, the active schemas, and the three
   active trackers; classifies the legacy training/datamove1 plan and
   trackers as read-only historical references; states explicitly that
   `docs/plans/training_datamove1_plan.md` must not be restored and
   names the read-only archived copy at
   `docs/plans/archive/legacy_reference_plans/20260507T223435Z/training_datamove1_plan.md`.
2. `CLAUDE.md` — a branch-specific warning was inserted above Section 1,
   outside the `BEGIN ROBUST_ASR_PROFILE` / `END ROBUST_ASR_PROFILE`
   delimiters. The warning names `ROBUST_ASR_PROFILE` as the normative
   block for this branch and frames Sections 1–23 as legacy
   training-template content superseded by `ROBUST_ASR_PROFILE`. The
   `ROBUST_ASR_PROFILE` block body is byte-unchanged.
3. `docs/progress/robust_asr_progress.yaml` — `latest_approval_packet`
   set to `CHANGE_SCOPE(plan_index_refresh)`; the prior
   `APPROVE_EXECUTION(P8.2)` packet on `2e1c46e…` demoted to
   `prior_approval_packet_p8_2_exec`;
   `state_transport.last_accepted_report_commit` advanced
   `2e1c46e8f1595fd1934ecb07743b713057652d29 ->
   0073e7b4076ce76d36233bec2eacb4411ba28722`; new
   `tasks.plan_index_refresh` row recorded with `status=PASS`,
   `type=scope_change`, `phase=P8`, `next_task=P8_GATE`.
4. `docs/progress/robust_asr_progress.md` — new section at the top of
   the chronological log documenting the scope change and listing the
   held invariants; existing "Current state" lines updated to reflect
   the new `latest_approval_packet` and the advanced
   `last_accepted_report_commit`.
5. `docs/progress/robust_asr_state_capsule.md` — top "Updated by:"
   header replaced with the `CHANGE_SCOPE(plan_index_refresh)` summary;
   prior `P8.2 APPROVE_EXECUTION` summary demoted to a "Prior update"
   section.

## State held (no changes)

- `current_task = P8_GATE` (held).
- `last_completed_task = P8.2` (held).
- `state_transport.expected_next_task = P8_GATE` (held).
- `tasks.P8_GATE.status = FAIL` (attempt 1; counter NOT advanced;
  no fresh attempt opened).
- `tasks.P8.2.status = PASS` (under enacted deviation
  `P8_2_demo_only_upstream_overlap`).
- `tasks.P8.1.status = PASS`.
- `phase_summary.P8 = null`; `orchestrator_approvals.P8 = null`.
- `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]` — none cleared, none added.
- `claims_enabled.{ood_real, cloud_tradeoff, positive_lora,
  positive_system} = false` — all held.
- `blocked = false`; `blocker = null`.
- `router_status = SELECTOR_PACKAGED`;
  `lora_status = SKIPPED_BY_DECISION_A`.
- `proposed_deviations.P8_2_demo_only_upstream_overlap.status = ENACTED`.

## Files explicitly not touched

- `docs/plans/training_datamove1_plan.md` — remains absent; not restored.
- `docs/plans/archive/**` — read-only legacy artifacts; byte-unchanged.
- `docs/progress/training_datamove1_progress.{yaml,md}` — read-only
  legacy trackers; byte-unchanged.
- `configs/robust_asr/reuse_policy_v1.yaml` — unchanged.
- `reports/robust_asr/touch_policy.md` — unchanged.
- The `BEGIN ROBUST_ASR_PROFILE` / `END ROBUST_ASR_PROFILE` block body
  inside `CLAUDE.md` — byte-unchanged.
- All P8 evidence files: `artifacts/robust_asr/demo/audio/*.wav`,
  `artifacts/robust_asr/demo/demo_examples_manifest.json`,
  `scripts/robust_asr/build_demo_examples.py`,
  `tests/robust_asr/test_leakage.py`,
  `reports/robust_asr/system/system_eval.md`,
  `reports/robust_asr/demo/provenance_audit.md`,
  `reports/robust_asr/task_reports/P8.1_system_eval.md`,
  `reports/robust_asr/task_reports/P8.2_demo_manifest.md`.

## Verification

- `test ! -f docs/plans/training_datamove1_plan.md` — passes (legacy
  canonical path remains absent).
- `git status` clean on authorized files only after commit; no
  unauthorized path appears in the diff.
- The new `latest_approval_packet` block parses as a single top-level
  `ORCHESTRATOR_DECISION` mapping per
  `docs/plans/state_packet_schemas_v1.yaml > approval_packet`.

## Next legal action

A PLAN_ONLY planning report for `P8_GATE` attempt 2, awaiting
orchestrator `APPROVE_PLAN(P8_GATE)` before any `phase_gate_report` is
emitted. On `APPROVE_PLAN`, EXECUTION evaluates the P8 gate predicate
(agent plan §2676–§2691) against the current tree and emits a
`phase_gate_report` with the tracker write of
`tasks.P8_GATE.attempt=2`, `tasks.P8_GATE.status` (PASS|FAIL), and
`phase_summary.P8` (PASS|FAIL). No P9 task may open without
`PHASE_APPROVE(P8)`.
