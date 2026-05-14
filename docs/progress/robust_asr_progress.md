# Robust ASR LoRA Router — Progress

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Status: IN_PROGRESS

## Current state

- Phase: P8 (system evaluation and demo examples)
- Current task: P8_GATE (P8.1 PASS — system evaluation, Decision D = false under OUTCOME_E_NARROWED_SCOPE)
- Last completed: P8.1 (PASS — system_eval.md first line `positive_system: false`; OK_SYSTEM_EVAL:false on stdout; pytest 137/137; full BCa bootstrap 10000 iter seed 20250514; Slurm job 2132279 COMPLETED 0:0)
- Prior completed: P7.3 (PASS — deterministic selector packaged under OUTCOME_E Branch B; PHASE_APPROVE(P7) recorded against the same P7.3 acceptance commit and does not itself advance last_completed_task)
- Prior completed: P6.1 (PASS — selector-evidence path)
- Prior completed: P5.1 (HALTED — BLOCKED_API reason=key_unset)
- Prior completed: P3.2 (PASS — Decision_A_smoke.outcome=FAIL)
- Phase summary: P0=PASS, P1=PASS, P2=PASS, P3=PASS, P5=PASS, P6=PASS, P7=PASS
- tasks.P7.1.status: SKIPPED_BY_OUTCOME_E (decided_at_task=P6_GATE, next_task=P7.3)
- tasks.P7.2.status: SKIPPED_BY_OUTCOME_E (decided_at_task=P6_GATE, next_task=P7.3)
- Active markers: [BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]
- Blocked: false
- Blocker: null
- claims_enabled.ood_real: false (no Section 1.1 OOD-real fallback resolves on host)
- claims_enabled.cloud_tradeoff: false (set by P5.1 BLOCKED_API; ASSEMBLYAI_API_KEY unset)
- claims_enabled.positive_lora: false (transitioned from pending by P3 gate Branch B)
- claims_enabled.positive_system: false (set by P8.1; Section 5.6 predicate fails under OUTCOME_E single-deployable-baseline scope; OUTCOME_E_NARROWED_SCOPE marker)
- decisions.Decision_D_positive_system.outcome: false (decided at P8.1)
- lora_status: SKIPPED_BY_DECISION_A (transitioned from SMOKE_DONE by P3 gate Branch B)
- decisions.Decision_B_lora_full.include_lora_in_router: false (set by P3 gate Branch B)
- tasks.P4.1 / P4.2 / P4.3: SKIPPED_BY_DECISION_A (set by P3 gate Branch B)
- normalization_version: normalization_v1 (frozen at P1.2)
- metrics_version: metrics_v1 (preserved; libs/audio/metrics.py unchanged)
- state_transport.last_accepted_report_commit: d009c318acd99041de3175af26b91df2adddffa6 (held at the P7.3 acceptance commit; PHASE_APPROVE(P7) was recorded against this commit and does not itself advance it, matching the P0/P1/P2/P3/P5/P6 pattern)
- state_transport.expected_next_task: P8_GATE
- deterministic_selector_version: deterministic_selector_v1 (frozen at P6.1)
- router_status: SELECTOR_PACKAGED
- tasks.P6.1.status: PASS (branch B selector-evidence)
- tasks.P6.2.status: SKIPPED_BY_OUTCOME_E (next_task P7.3)
- tasks.P7.3.status: PASS (branch B_deterministic_selector; commit `d009c31`; approved_by APPROVE_EXECUTION_P7.3; next_task P7_GATE)
- decisions.P7_routing.branch: B_deterministic_selector (decided at P7_GATE; outcome_e_carried_forward=true; routes to P8.1)
- latest_approval_packet: APPROVE_PLAN(P8.1) on `f23a270` (next P8_GATE) — system evaluator implementation approved; Decision D evaluates to false under OUTCOME_E
- prior_approval_packet_p8_1_scope_exec: APPROVE_EXECUTION(P8.1-scope-change) on `f23a270` (next P8.1) — touch_policy P8.1 row + progress.yaml parse-fix accepted
- prior_approval_packet_p8_1_change_scope: CHANGE_SCOPE(P8.1) on `440f2fa` (next P8.1) — authorizes scripts/robust_asr/evaluate_system.py in the P8.1 touch-policy row
- prior_approval_packet_p7_phase: PHASE_APPROVE(P7) on `d009c31` (next P8.1)
- prior_approval_packet_p7_3_exec: APPROVE_EXECUTION(P7.3) on `d009c31` (next P7_GATE)
- prior_approval_packet_p7_3_plan: APPROVE_PLAN(P7.3) on `394df2d` (next P7_GATE)
- prior_approval_packet_p7_3_scope_exec: APPROVE_EXECUTION(P7.3-scope-change) on `394df2d` (next P7.3)
- prior_approval_packet_p7_3_change_scope: CHANGE_SCOPE(P7.3) on `e9ebbfe` (next P7.3)
- prior_approval_packet_p6_phase: PHASE_APPROVE(P6) on `6441350` (next P7.3)
- prior_approval_packet_p6_1_exec: APPROVE_EXECUTION(P6.1) on `6441350` (next P6_GATE)
- prior_approval_packet_p6_1_plan: APPROVE_PLAN(P6.1) on `4a9f929` (next P6_GATE)
- prior_approval_packet_p6_1_scope_exec: APPROVE_EXECUTION(P6.1-scope-change) on `4a9f929` (next P6.1)
- prior_approval_packet_p6_1_change_scope: CHANGE_SCOPE(P6.1) on `9ffc885` (next P6.1)
- prior_approval_packet_p5_phase: PHASE_APPROVE(P5) on `c71e0a0` (next P6.1)
- prior_approval_packet_p5_1_exec: APPROVE_EXECUTION(P5.1) on `c71e0a0` (next P5_GATE)
- prior_approval_packet_p5_1_plan: APPROVE_PLAN(P5.1) on `f7a845f` (next P5_GATE)
- prior_approval_packet_p5_1_scope_exec: APPROVE_EXECUTION(P5.1-scope-change) on `f7a845f` (next P5.1)
- prior_approval_packet_p5_1_change_scope: CHANGE_SCOPE(P5.1) on `45b6cac` (next P5.1)
- prior_approval_packet_p3_phase: PHASE_APPROVE(P3) on `26db72d` (next P5.1)
- prior_approval_packet_p3_2_exec: APPROVE_EXECUTION(P3.2) on `26db72d` (next P3_GATE)
- prior_approval_packet_p3_2_plan: APPROVE_PLAN(P3.2) on `1025a24` (next P3_GATE)
- prior_approval_packet_p3_2_scope_exec: APPROVE_EXECUTION(P3.2-scope-change) on `1025a24` (next P3.2)
- prior_approval_packet_p3_2_change_scope: CHANGE_SCOPE(P3.2) on `ee92c8b` (next P3.2)
- prior_approval_packet_p3_1_exec: APPROVE_EXECUTION(P3.1) on `096fe43` (next P3.2)
- prior_approval_packet_p3_1_plan: APPROVE_PLAN(P3.1) on `3ed96f5` (next P3.2)
- prior_approval_packet_p3_1_scope_exec: APPROVE_EXECUTION(P3.1-scope-change) on `3ed96f5` (next P3.1)
- prior_approval_packet_p3_1_change_scope: CHANGE_SCOPE(P3.1) on `ca98443` (next P3.1)
- prior_approval_packet_p2_phase: PHASE_APPROVE(P2) on `8c37ece` (next P3.1)
- prior_approval_packet: APPROVE_EXECUTION(P2.2) on `8c37ece` (next P2_GATE)
- prior_approval_packet_p2_2_plan: APPROVE_PLAN(P2.2) on `d78678a` (next P2_GATE)
- prior_approval_packet_p2_2_scope_exec: APPROVE_EXECUTION(P2.2-scope-change) on `d78678a` (next P2.2)
- prior_approval_packet_p2_2_change_scope: CHANGE_SCOPE(P2.2) on `821893c` (next P2.2)
- prior_approval_packet_p2_1_exec: APPROVE_EXECUTION(P2.1) on `83dd911` (next P2.2)
- prior_approval_packet_p2_1_rerun_plan: APPROVE_PLAN(P2.1-rerun) on `28dddae` (next P2.2)
- prior_approval_packet_p2_1_model_build_exec: APPROVE_EXECUTION(P2.1-model-build) on `28dddae` (next P2.1)
- prior_approval_packet_p2_1_model_build_plan: APPROVE_PLAN(P2.1-model-build) on `7253b87` (next P2.1)
- prior_approval_packet_p2_1_model_scope_exec: APPROVE_EXECUTION(P2.1-model-scope-change) on `7253b87` (next P2.1)
- prior_approval_packet_p2_1_model_change_scope: CHANGE_SCOPE(P2.1-model) on `268b8e9` (next P2.1)

## P7 PHASE_APPROVE recorded — Branch B deterministic selector

- ORCHESTRATOR_DECISION: scope=phase task=null phase=P7
  decision=PHASE_APPROVE
- accepted_report_commit:
  `d009c318acd99041de3175af26b91df2adddffa6` (the P7.3 acceptance
  commit; PHASE_APPROVE(P7) is recorded against this commit and does
  not itself advance `last_accepted_report_commit`).
- next_expected_task: `P8.1`
- required_fix: null
- rationale: P7 phase gate PASS on Branch B deterministic selector
  packaging (agent plan §2661-§2669).
  `OUTCOME_E_DETERMINISTIC_SELECTOR` is active; `tasks.P7.3 = PASS`;
  `tasks.P7.1` and `tasks.P7.2` are `SKIPPED_BY_OUTCOME_E`;
  `artifacts/robust_asr/router/selected_router/deterministic_selector.json`
  and `…/rp5_inference.py` exist; `pytest
  tests/robust_asr/test_router_runtime.py` PASS (13/13);
  `selector_final_eval.md` declares **NEUTRAL_EVIDENCE** and
  `claims_enabled.positive_system` remains `pending`. Routing
  advances to `P8.1` per §2672.

### Predicate inputs (P7 gate Branch B, §2661-§2669)

| clause | observed | satisfied |
|---|---|---|
| marker `OUTCOME_E_DETERMINISTIC_SELECTOR` active | true | ✓ |
| `tasks.P7.3.status == PASS` | `PASS` | ✓ |
| `tasks.P7.1.status ∈ {SKIPPED_BY_OUTCOME_E, PASS, FAIL, HALTED, null}` | `SKIPPED_BY_OUTCOME_E` | ✓ |
| `tasks.P7.2.status ∈ {SKIPPED_BY_OUTCOME_E, PASS, null}` | `SKIPPED_BY_OUTCOME_E` | ✓ |
| `selected_router/deterministic_selector.json` exists | sha256 `41d19421…` | ✓ |
| `selected_router/rp5_inference.py` exists | sha256 `62f0caab…` | ✓ |
| `pytest tests/robust_asr/test_router_runtime.py` PASS | 13/13 | ✓ |

### Tracker mutations

- `current_phase` advanced `P7 -> P8`.
- `current_task` advanced `P7_GATE -> P8.1`.
- `last_completed_task` held at `P7.3` (PHASE_APPROVE recorded
  against the P7.3 acceptance commit does not advance
  `last_completed_task`; matches P0/P1/P2/P3/P5/P6 pattern).
- `phase_summary.P7 = PASS`;
  `orchestrator_approvals.P7 = PHASE_APPROVE`.
- `decisions.P7_routing.branch = B_deterministic_selector`;
  `decisions.P7_routing.outcome_e_carried_forward = true`;
  `decisions.P7_routing.enacted_at = P7_GATE`;
  `decisions.P7_routing.decided_at_task = P7_GATE`.
- New `tasks.P7_GATE` entry with the seven satisfied predicate
  inputs.
- `latest_approval_packet` = `PHASE_APPROVE(P7)` on
  `d009c318acd99041de3175af26b91df2adddffa6` (next `P8.1`); prior
  `APPROVE_EXECUTION(P7.3)` demoted to
  `prior_approval_packet_p7_3_exec` on `d009c318…` (next
  `P7_GATE`); `APPROVE_PLAN(P7.3)` held as
  `prior_approval_packet_p7_3_plan` on `394df2d` (next `P7_GATE`);
  `APPROVE_EXECUTION(P7.3-scope-change)` held as
  `prior_approval_packet_p7_3_scope_exec` on `394df2d` (next
  `P7.3`); `CHANGE_SCOPE(P7.3)` held as
  `prior_approval_packet_p7_3_change_scope` on `e9ebbfe` (next
  `P7.3`); `PHASE_APPROVE(P6)` held as
  `prior_approval_packet_p6_phase` on `6441350` (next `P7.3`).
- `state_transport.last_accepted_report_commit` held at
  `d009c318acd99041de3175af26b91df2adddffa6` per orchestrator
  instruction (PHASE_APPROVE recorded against the P7.3 acceptance
  commit; not advanced by the phase-gate tracker commit itself).
- `state_transport.expected_next_task` = `P8.1`.

### Routing state (held)

- Markers `[BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]` held (none cleared; OUTCOME_E
  remains the active outcome routing P7 → P10).
- `blocked = false`; `blocker = null`.
- `claims_enabled.ood_real = false`,
  `claims_enabled.cloud_tradeoff = false`,
  `claims_enabled.positive_lora = false`,
  `claims_enabled.positive_system = pending` — all held. **NOT
  enabled by this approval**; `positive_system` is set only by P8.1
  per §5.6.
- `router_status = SELECTOR_PACKAGED` held.
- `deterministic_selector_version = deterministic_selector_v1`
  held.
- `lora_status = SKIPPED_BY_DECISION_A` held;
  `decisions.Decision_B_lora_full.include_lora_in_router = false`
  held; `tasks.P4.1 = P4.2 = P4.3 = SKIPPED_BY_DECISION_A` held;
  `tasks.P6.2 = SKIPPED_BY_OUTCOME_E` held;
  `tasks.P7.1 = tasks.P7.2 = SKIPPED_BY_OUTCOME_E` held.

### Notes

- No code, no test, no Slurm submission, no real-provider call for
  this update. Only tracker files modified.
- P8.1 not started. The P8 phase will:
  - run `evaluate_system.py` (Section 4.7) on the deterministic
    selector and the backend tables;
  - set `claims_enabled.positive_system` from the first line of
    `reports/robust_asr/system/system_eval.md`;
  - record `decisions.Decision_D_positive_system.outcome`.

## P7.3 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P7.3 phase=P7
  decision=APPROVE_EXECUTION
- accepted_report_commit:
  `d009c318acd99041de3175af26b91df2adddffa6`
- next_expected_task: `P7_GATE`
- required_fix: null
- rationale: P7.3 passed on the OUTCOME_E deterministic-selector
  packaging path. `OK_DETERMINISTIC_SELECTOR_PACKAGE`,
  `OK_SELECTOR_FINAL_EVAL`, `OK_REPORT_SHAPE`, `test_router_runtime`,
  and the full robust_asr suite passed. The `selected_router`
  package contains no forbidden audio/model/secret files.
  `selector_final_eval.md` correctly frames the result as
  **NEUTRAL_EVIDENCE** and leaves
  `claims_enabled.positive_system=pending`.

### Tracker mutations

- `tasks.P7.3.commit` = `d009c318acd99041de3175af26b91df2adddffa6`;
  `tasks.P7.3.approved_by` = `APPROVE_EXECUTION_P7.3`;
  `tasks.P7.3.approved_at_commit` =
  `d009c318acd99041de3175af26b91df2adddffa6`.
- `state_transport.last_accepted_report_commit` advanced
  `64413500094b79a160fbcb179b432fd6ccdaf80f -> d009c318acd99041de3175af26b91df2adddffa6`.
- `state_transport.expected_next_task` = `P7_GATE` (held).
- `latest_approval_packet` = `APPROVE_EXECUTION(P7.3)` on
  `d009c31` (next P7_GATE); prior `APPROVE_PLAN(P7.3)` demoted to
  `prior_approval_packet_p7_3_plan` on `394df2d` (next P7_GATE);
  `APPROVE_EXECUTION(P7.3-scope-change)` held as
  `prior_approval_packet_p7_3_scope_exec` on `394df2d` (next P7.3);
  `CHANGE_SCOPE(P7.3)` held as
  `prior_approval_packet_p7_3_change_scope` on `e9ebbfe`
  (next P7.3); `PHASE_APPROVE(P6)` held as
  `prior_approval_packet_p6_phase` on `6441350` (next P7.3).
- Held: `current_phase = P7`, `current_task = P7_GATE`,
  `last_completed_task = P7.3`, `tasks.P7.3.status = PASS`
  (branch `B_deterministic_selector`; next_task `P7_GATE`),
  `tasks.P7.1.status = SKIPPED_BY_OUTCOME_E`,
  `tasks.P7.2.status = SKIPPED_BY_OUTCOME_E`,
  `router_status = SELECTOR_PACKAGED`,
  `deterministic_selector_version = deterministic_selector_v1`,
  `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]`,
  `blocked = false`, `blocker = null`,
  `claims_enabled.ood_real = false`,
  `claims_enabled.cloud_tradeoff = false`,
  `claims_enabled.positive_lora = false`,
  `claims_enabled.positive_system = pending`,
  `lora_status = SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router = false`,
  `tasks.P4.1 = P4.2 = P4.3 = SKIPPED_BY_DECISION_A`,
  `tasks.P6.1 = PASS`, `tasks.P6.2 = SKIPPED_BY_OUTCOME_E`.

### Notes

- No code, no test, no Slurm submission, no real-provider call for
  this update. Only tracker files modified.
- `claims_enabled.positive_system` is NOT enabled by this approval;
  the deterministic selector under OUTCOME_E is still NEUTRAL
  EVIDENCE per agent plan §1664-§1665. `positive_system` will be
  set by P8.1 only.
- P7_GATE not started. P8.1 not started.

## P7.3 PASS — deterministic selector packaged (Outcome E, Branch B)

- ORCHESTRATOR_DECISION (current `latest_approval_packet`):
  scope=task task=P7.3 phase=P7 decision=APPROVE_PLAN
  accepted_report_commit=`394df2d2778e0f7204aba8155fa66e2eea8cb1a9`
  next_expected_task=`P7_GATE` required_fix=null.
- Sentinels emitted: `OK_DETERMINISTIC_SELECTOR_PACKAGE`,
  `OK_SELECTOR_FINAL_EVAL`, `OK_REPORT_SHAPE`,
  `pytest tests/robust_asr` 137 passed (incl. the 13 new
  `test_router_runtime.py` cases).
- Files created:
  - `scripts/robust_asr/package_deterministic_selector.py`
    (sha256 `969c3af202407bbb686e6de83869173a8e8b06958afb2eae7f63c3a58c86ddf1`).
  - `scripts/robust_asr/evaluate_deterministic_selector.py`
    (sha256 `fa6e2623815c9e47b279aeaceb577fd24ed9b7e1da668945fc92bc735a4a10d2`).
  - `tests/robust_asr/test_router_runtime.py`
    (sha256 `fffed034964fecaeb3519ef65f8f963eeed4828c9ca311d712c985c710784514`;
    13 tests PASS).
  - `artifacts/robust_asr/router/selected_router/deterministic_selector.json`
    (sha256 `41d194218b52c13b795d782eb92c381ac3eaa696f56fd217cab43e6a059df3fd`;
    845 B).
  - `artifacts/robust_asr/router/selected_router/metadata.json`
    (sha256 `93dfd0cc2b385d4859cb6c723664fbf1cb4876e27c513590d3f8842d915ff924`;
    1751 B).
  - `artifacts/robust_asr/router/selected_router/rp5_inference.py`
    (sha256 `62f0caab558dbd26dd63e9cdf3c931831b527a0ec9f520811d145e7408378427`;
    2820 B; stdlib-only).
  - `artifacts/robust_asr/router/selected_router/test_vectors.json`
    (sha256 `e57fc83e8e19763389a02e9aa6798e3e70026f7a2c041162fa33a3dec732739d`;
    5794 B; 20 tuples covering every Section 5.5 branch).
  - `reports/robust_asr/router/selector_final_eval.md`
    (sha256 `8a67872b64b28430576a719d4d7d9189aebda57ce88bb8e62ed625094c654ecf`;
    first line declares **NEUTRAL_EVIDENCE**).
  - `reports/robust_asr/task_reports/P7.3_router_package.md`.
- Forbidden files asserted absent under
  `artifacts/robust_asr/router/selected_router/`: no
  `*.wav/*.flac/*.mp3/*.m4a`, no `*.pt/*.pth/*.ckpt/*.bin/*.safetensors`,
  no `.env/.env.*/*.key/*.pem/*.token`.

### Selector final evaluation (n = 53 230)

- Predicate parity vs the parquet-recorded `selected_action`:
  **0 / 53 230 mismatches**.
- `selected_action` distribution: `whisper_base_ct2_int8` 53 202
  (99.9474 %), `ask_repeat` 28 (0.0526 %), `assemblyai` 0,
  `whisper_lora_ct2_int8` 0.
- `cloud_call_rate` = 0.00 %; `local_only_rate` = 100.00 %; total
  cost = $0.00.
- Mean WER (selector) = mean WER (always-`whisper_base_ct2_int8`) =
  0.209797; mean WA = 0.836701.
- `mean_regret_wer` = 0; paired BCa 95 % CI = [0, 0] (10 000
  iterations, seed 20260514, percentile_fallback because all 28
  `ask_repeat` rows already have `baseline_wer = 1.0`); Wilcoxon
  undefined (n = 0 nonzero deltas).
- Per agent plan §1664-§1665 and §5.6, this is **NEUTRAL EVIDENCE**;
  `claims_enabled.positive_system` stays `pending`. The selector
  under OUTCOME_E is not making a positive system claim.

### Tracker mutations

- `tasks.P7.3.status` = `PASS`;
  `tasks.P7.3.branch` = `B_deterministic_selector`;
  `tasks.P7.3.next_task` = `P7_GATE`;
  `tasks.P7.3.sentinels` =
  `[OK_DETERMINISTIC_SELECTOR_PACKAGE, OK_SELECTOR_FINAL_EVAL,
   OK_REPORT_SHAPE, pytest_tests/robust_asr_137/137]`.
- `current_task` advanced `P7.3 -> P7_GATE`;
  `last_completed_task` advanced `P6.1 -> P7.3`.
- `router_status` = `SELECTOR_EVIDENCE_BUILT -> SELECTOR_PACKAGED`.
- `artifacts.router_package` = `{kind: deterministic_selector,
  sha256 (selector json): 41d19421…}` plus per-file sha256s; new
  artifact entries for the two scripts, the runtime test, and the
  final eval report.
- `state_transport.latest_approval_packet` = `APPROVE_PLAN(P7.3)` on
  `394df2d`; prior `APPROVE_EXECUTION(P7.3-scope-change)` demoted to
  `prior_approval_packet_p7_3_scope_exec` on `394df2d`; prior
  `CHANGE_SCOPE(P7.3)` demoted to
  `prior_approval_packet_p7_3_change_scope` on `e9ebbfe`;
  `PHASE_APPROVE(P6)` held as `prior_approval_packet_p6_phase`.
- `state_transport.last_accepted_report_commit` held at
  `64413500094b79a160fbcb179b432fd6ccdaf80f` per orchestrator
  instruction (NOT advanced to this P7.3 implementation commit,
  matching the P5.1 / P6.1 pattern).
- `state_transport.expected_next_task` = `P7_GATE`.
- Markers `[BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]` held; `blocked = false`;
  `claims_enabled.ood_real = false`, `.cloud_tradeoff = false`,
  `.positive_lora = false`, `.positive_system = pending` (all held);
  `deterministic_selector_version = deterministic_selector_v1` held;
  `lora_status = SKIPPED_BY_DECISION_A` held.

### Notes

- No Slurm submission, no Apptainer GPU, no AssemblyAI call, no
  LoRA call. CPU-only login-node task under CLAUDE.md §7.
- `rp5_inference.py` is stdlib-only and loads its constants from
  the sibling `deterministic_selector.json` at runtime, so the
  packaged metadata is the single source of truth. Drift between
  `router_v1.yaml` and the packaged constants would be caught by
  `test_metadata_file_sha256s_match_on_disk`.
- P7_GATE not started. P8.1 not started.

## P7.3 CHANGE_SCOPE recorded — deterministic selector packaging

- ORCHESTRATOR_DECISION: scope=scope_change task=P7.3 phase=P7
  decision=CHANGE_SCOPE
- accepted_report_commit: `e9ebbfe` (P6 phase gate approval commit; current
  HEAD prior to this scope-change commit)
- next_expected_task: `P7.3`
- required_fix: "Authorize deterministic selector packaging scripts,
  runtime test, final eval report, and P7.3 touch-policy paths."
- rationale: P7.3 requires `scripts/robust_asr/package_deterministic_selector.py`,
  `scripts/robust_asr/evaluate_deterministic_selector.py`,
  `tests/robust_asr/test_router_runtime.py`,
  `reports/robust_asr/router/selector_final_eval.md`, and the
  `artifacts/robust_asr/router/selected_router/**` package, but the prior
  policy (committed at `6441350`) did not authorize all P7.3 writes — in
  particular, the `tests/robust_asr/**` row excluded P7.3 and the P7.3
  touch-policy row did not list the scripts, the runtime test, or
  `selector_final_eval.md`.

### Reuse-policy amendments

- `configs/robust_asr/reuse_policy_v1.yaml`:
  - `tests/robust_asr/**` `allowed_tasks`:
    `[P1.1, P1.2, P1.4, P3.1, P4.1, P5.1, P8.1]` →
    `[P1.1, P1.2, P1.4, P3.1, P4.1, P5.1, P7.3, P8.1]`.
    Authorizes `tests/robust_asr/test_router_runtime.py` for the
    deterministic-selector runtime regression required by P7 gate
    Branch B (agent plan §2669).

### Touch-policy amendments

- `reports/robust_asr/touch_policy.md` P7.3 row rewritten to authorize
  writes:
  - `scripts/robust_asr/package_deterministic_selector.py`
  - `scripts/robust_asr/evaluate_deterministic_selector.py`
  - `tests/robust_asr/test_router_runtime.py`
  - `artifacts/robust_asr/router/selected_router/**`
  - `reports/robust_asr/router/selector_final_eval.md`
  - `reports/robust_asr/task_reports/P7.3_router_package.md`
  - `configs/robust_asr/reuse_policy_v1.yaml` (scope-change rows)
  - `reports/robust_asr/touch_policy.md` (scope-change row)
  - `docs/progress/robust_asr_progress.yaml`,
    `docs/progress/robust_asr_progress.md`,
    `docs/progress/robust_asr_state_capsule.md`
- Authorized reads added: `configs/robust_asr/reuse_policy_v1.yaml`,
  `configs/robust_asr/router_v1.yaml`,
  `artifacts/robust_asr/router/selector_evidence.parquet`,
  `reports/robust_asr/router/selector_evidence_summary.md`,
  `libs/common/versions.py`, `libs/common/normalization.py`,
  `libs/common/metrics.py`, `libs/common/eval_schema.yaml`,
  `scripts/robust_asr/validate_report_shape.py`,
  `scripts/robust_asr/validate_selector_evidence.py`.
- Explicit P7.3 `default_no_touch` additions: legacy trackers,
  `services/**`, `infra/**`, `configs/training/**`,
  `scripts/training/**`, `slurm/**`, `libs/audio/** (write)`,
  `libs/asr_adapter/** (write)`, `libs/common/** (write)`,
  `libs/audio_pipeline/** (write)`, `libs/observability/** (write)`,
  `artifacts/robust_asr/oracle/**` (Branch A only; OUTCOME_E active),
  P6.2 router feature/matrix artifacts, P7.2 router candidates,
  `artifacts/robust_asr/router/selector_evidence.parquet` (write — owned
  by P6.1), `configs/robust_asr/pricing_v1.yaml` (write — owned by P5.1),
  `configs/robust_asr/eval_manifests_v1.yaml` (write),
  `configs/robust_asr/router_v1.yaml` (write — owned by P6.1),
  `configs/robust_asr/data_v1.yaml` (write),
  `configs/robust_asr/degradation_v1.yaml` (write), AssemblyAI / API
  runtime files, `*.wav/*.flac/*.mp3/*.m4a` under repo root,
  `*.pt/*.pth/*.ckpt/*.bin/*.safetensors` under `selected_router/`.

### Tracker artifact sha256 updates

- `artifacts.reuse_policy_config.sha256` =
  `3e84490f50d5a4c46e962a482decfef74d36064afa00871923728ae08c916dcf`;
  `last_amended_by` = `P7.3_scope_change`.
- `artifacts.touch_policy.sha256` =
  `f236467af7776f5243439a69baeffe50ec5193135e231bbfa5bdbd063d310ddc`;
  `last_amended_by` = `P7.3_scope_change`.

### Routing state (held)

- `current_phase` = `P7` (held).
- `current_task` = `P7.3` (held; not advanced — this commit records the
  scope-change only).
- `last_completed_task` = `P6.1` (held).
- `tasks.P7.1.status` = `SKIPPED_BY_OUTCOME_E` (held; decided at
  `P6_GATE`).
- `tasks.P7.2.status` = `SKIPPED_BY_OUTCOME_E` (held; decided at
  `P6_GATE`).
- `tasks.P7.3.status` = `IN_PROGRESS` / `implementation_status` =
  `NOT_STARTED` (scope-change committed; APPROVE_PLAN and
  APPROVE_EXECUTION still required before P7.3 implementation).
- Markers `[BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]` held.
- `blocked` = `false`; `blocker` = `null` (held).
- `claims_enabled.ood_real` = `false`,
  `claims_enabled.cloud_tradeoff` = `false`,
  `claims_enabled.positive_lora` = `false`,
  `claims_enabled.positive_system` = `pending` (all held).
- `router_status` = `SELECTOR_EVIDENCE_BUILT` (held).
- `deterministic_selector_version` = `deterministic_selector_v1` (held).
- `state_transport.last_accepted_report_commit` =
  `64413500094b79a160fbcb179b432fd6ccdaf80f` (held per orchestrator
  instruction — NOT advanced to this scope-change commit, matching
  P5.1 / P6.1 pattern).
- `state_transport.expected_next_task` = `P7.3` (held).
- `state_transport.latest_approval_packet` = `CHANGE_SCOPE(P7.3)` on
  `e9ebbfe`; the prior `PHASE_APPROVE(P6)` packet demoted to
  `prior_approval_packet_p6_phase`.

### Validation

- `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml
  --fixtures artifacts/robust_asr/state_packets/report_shape_fixtures`
  → `OK_REPORT_SHAPE`.

### Notes

- No code, no test, no Slurm submission, no real-provider call. Only
  the policy files (`configs/robust_asr/reuse_policy_v1.yaml`,
  `reports/robust_asr/touch_policy.md`) and the tracker files
  (`docs/progress/robust_asr_progress.{yaml,md}`,
  `docs/progress/robust_asr_state_capsule.md`) were modified.
- P7.3 implementation (deterministic selector packaging, runtime test,
  selector final eval, P7.3 task report) is the next scoped task once
  `APPROVE_PLAN(P7.3)` is recorded.

## P6 PHASE_APPROVE recorded — Branch B selector-evidence

- ORCHESTRATOR_DECISION: scope=phase task=null phase=P6
  decision=PHASE_APPROVE
  accepted_report_commit=`64413500094b79a160fbcb179b432fd6ccdaf80f`
  next_expected_task=P7.3 required_fix=null.
- Rationale: P6 phase gate PASS on Branch B (selector-evidence). All five
  agent-plan §2631-§2636 predicates hold: `OUTCOME_E_DETERMINISTIC_SELECTOR`
  active; `tasks.P6.1.status=PASS`;
  `tasks.P6.2.status=SKIPPED_BY_OUTCOME_E`;
  `artifacts/robust_asr/router/selector_evidence.parquet` exists with
  sha256 `c450a91a…` (53 230 rows); `validate_selector_evidence.py`
  emitted `OK_SELECTOR_EVIDENCE`. `OUTCOME_E_DETERMINISTIC_SELECTOR`
  remains active, so P7.1 and P7.2 are skipped at the P6 gate and
  routing advances to P7.3 (§308, §2642).
- Tracker mutations:
  `current_phase` advanced `P6 -> P7`;
  `current_task` advanced `P6_GATE -> P7.3`;
  `last_completed_task` held at `P6.1` (PHASE_APPROVE(P6) recorded
  against the P6.1 acceptance commit does not itself advance
  `last_completed_task`, matching the P0/P1/P2/P3/P5 pattern);
  `phase_summary.P6 = PASS`;
  `orchestrator_approvals.P6 = PHASE_APPROVE`;
  `decisions.P6_routing.branch = B_selector_evidence`;
  `decisions.P6_routing.outcome_e_carried_forward = true`;
  `decisions.P6_routing.enacted_at = P6_GATE`;
  `decisions.P6_routing.p7_skips_enacted = [P7.1, P7.2]`;
  `tasks.P7.1.status = SKIPPED_BY_OUTCOME_E`
    (`decided_at_task=P6_GATE`, `next_task=P7.3`);
  `tasks.P7.2.status = SKIPPED_BY_OUTCOME_E`
    (`decided_at_task=P6_GATE`, `next_task=P7.3`);
  new `tasks.P6_GATE` entry with the five satisfied predicate inputs
  and the two enacted P7 skips;
  `latest_approval_packet` = PHASE_APPROVE(P6) on
  `64413500094b79a160fbcb179b432fd6ccdaf80f` (next P7.3);
  prior APPROVE_EXECUTION(P6.1) demoted to
  `prior_approval_packet_p6_1_exec` on
  `64413500094b79a160fbcb179b432fd6ccdaf80f` (next P6_GATE);
  APPROVE_PLAN(P6.1) held as `prior_approval_packet_p6_1_plan` on
  `4a9f9291f0a1e90d21f0d771885d9eaf273aa37b` (next P6_GATE);
  APPROVE_EXECUTION(P6.1-scope-change) held as
  `prior_approval_packet_p6_1_scope_exec` on
  `4a9f9291f0a1e90d21f0d771885d9eaf273aa37b` (next P6.1);
  CHANGE_SCOPE(P6.1) held as
  `prior_approval_packet_p6_1_change_scope` on `9ffc885` (next P6.1);
  PHASE_APPROVE(P5) held as `prior_approval_packet_p5_phase` on
  `c71e0a0bb25a5d2749801d8fc7444869ff331d1b` (next P6.1);
  `state_transport.expected_next_task = P7.3`;
  `state_transport.last_accepted_report_commit =
  64413500094b79a160fbcb179b432fd6ccdaf80f` held (PHASE_APPROVE
  recorded against the P6.1 acceptance commit; not advanced by the
  phase-gate tracker commit itself).
  Held: `blocked = false`, `blocker = null`,
  `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]` (none cleared; OUTCOME_E remains
  the active outcome routing P7 → P10),
  `claims_enabled.ood_real = false`, `.cloud_tradeoff = false`,
  `.positive_lora = false`, `.positive_system = pending`,
  `lora_status = SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router = false`,
  `tasks.P4.1 = P4.2 = P4.3 = SKIPPED_BY_DECISION_A`,
  `tasks.P6.1 = PASS`, `tasks.P6.2 = SKIPPED_BY_OUTCOME_E`,
  `deterministic_selector_version = deterministic_selector_v1`,
  `router_status = SELECTOR_EVIDENCE_BUILT`,
  `normalization_version = normalization_v1`,
  `metrics_version = metrics_v1`,
  `degradation_version = degradation_v1`,
  `phase_summary = {P0,P1,P2,P3,P5,P6} = PASS`,
  `orchestrator_approvals = {P0,P1,P2,P3,P5,P6} = PHASE_APPROVE`.
- P7.3 not started. P7 gate Branch B predicate (§2661-§2669) now has
  `tasks.P7.1.status = SKIPPED_BY_OUTCOME_E ∈ {SKIPPED_BY_OUTCOME_E, PASS,
  FAIL, HALTED, null}` and `tasks.P7.2.status = SKIPPED_BY_OUTCOME_E
  ∈ {SKIPPED_BY_OUTCOME_E, PASS, null}`, so it will hold once
  `tasks.P7.3.status = PASS`. No code, no test, no Slurm submission, no
  real-provider call for this update. Only tracker files modified.

## P6.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P6.1 phase=P6
  decision=APPROVE_EXECUTION
  accepted_report_commit=`64413500094b79a160fbcb179b432fd6ccdaf80f`
  next_expected_task=P6_GATE required_fix=null.
- Rationale: P6.1 passed on the OUTCOME_E selector-evidence path.
  `selector_evidence.parquet` has 53 230 rows;
  `OK_SELECTOR_EVIDENCE_BUILD` and `OK_SELECTOR_EVIDENCE` were emitted;
  full `robust_asr` pytest passed (124/124); `OK_REPORT_SHAPE` passed;
  `deterministic_selector_version = deterministic_selector_v1` was
  recorded; `tasks.P6.2` was correctly marked `SKIPPED_BY_OUTCOME_E`
  with `next_task = P7.3`.
- Tracker mutations:
  `tasks.P6.1.commit = 64413500094b79a160fbcb179b432fd6ccdaf80f`;
  `tasks.P6.1.approved_by = APPROVE_EXECUTION_P6.1`;
  `tasks.P6.1.approved_at_commit =
  64413500094b79a160fbcb179b432fd6ccdaf80f`;
  `state_transport.last_accepted_report_commit` advanced
  `c71e0a0bb25a5d2749801d8fc7444869ff331d1b ->
  64413500094b79a160fbcb179b432fd6ccdaf80f`;
  `state_transport.expected_next_task = P6_GATE` held;
  `latest_approval_packet` = APPROVE_EXECUTION(P6.1) on
  `64413500094b79a160fbcb179b432fd6ccdaf80f` (next P6_GATE);
  prior APPROVE_PLAN(P6.1) demoted to
  `prior_approval_packet_p6_1_plan` on
  `4a9f9291f0a1e90d21f0d771885d9eaf273aa37b` (next P6_GATE);
  APPROVE_EXECUTION(P6.1-scope-change) held as
  `prior_approval_packet_p6_1_scope_exec` on
  `4a9f9291f0a1e90d21f0d771885d9eaf273aa37b` (next P6.1);
  CHANGE_SCOPE(P6.1) held as
  `prior_approval_packet_p6_1_change_scope` on `9ffc885` (next P6.1);
  PHASE_APPROVE(P5) held as `prior_approval_packet_p5_phase` on
  `c71e0a0bb25a5d2749801d8fc7444869ff331d1b` (next P6.1).
  Held: `current_phase = P6`, `current_task = P6_GATE`,
  `last_completed_task = P6.1`,
  `tasks.P6.1.status = PASS`,
  `tasks.P6.2.status = SKIPPED_BY_OUTCOME_E`,
  `deterministic_selector_version = deterministic_selector_v1`,
  `router_status = SELECTOR_EVIDENCE_BUILT`,
  `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]`, `blocked = false`,
  `claims_enabled.ood_real = false`, `.cloud_tradeoff = false`,
  `.positive_lora = false`, `.positive_system = pending`,
  `lora_status = SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router = false`,
  `tasks.P4.1 = P4.2 = P4.3 = SKIPPED_BY_DECISION_A`,
  `degradation_version = degradation_v1`,
  `normalization_version = normalization_v1`,
  `metrics_version = metrics_v1`,
  `phase_summary = {P0,P1,P2,P3,P5} = PASS`,
  `orchestrator_approvals = {P0,P1,P2,P3,P5} = PHASE_APPROVE`.
- P6_GATE not started. P7.1 / P7.2 skips remain owned by the P6
  gate (§312, §2664-§2665); P6.1 owns only the P6.2 skip. P7.3 not
  started. No code, no test, no Slurm submission, no real-provider
  call for this update. Only tracker files modified.

## P6.1 PASS — selector-evidence path (Outcome E)

- ORCHESTRATOR_DECISION: scope=task task=P6.1 phase=P6
  decision=APPROVE_PLAN accepted_report_commit=`4a9f9291f0a1e90d21f0d771885d9eaf273aa37b`
  next_expected_task=P6_GATE required_fix=null.
- Prior: APPROVE_EXECUTION(P6.1-scope-change) on `4a9f9291…` (next P6.1).
- Branch: B (selector-evidence). Reason: `OUTCOME_E_DETERMINISTIC_SELECTOR`
  active; deployable transcript-producing backend count = 1
  (`whisper_base_ct2_int8` only).
- Deliverables produced this commit:
  - `configs/robust_asr/router_v1.yaml` (sha256
    `ef9586c8e589436ae074d472d38bc12b417d2043d142d5f74d8d5d75f7de2f98`) —
    schema_version `router_v1`, `deterministic_selector_version =
    deterministic_selector_v1`, Section 5.5 thresholds, Section 5.4
    cost coefficients, profile defaults, eligible action set,
    selector_evidence build options (`assemblyai_available=False`,
    `lora_available=False`, no_speech_prob proxy from empty
    `normalized_transcript`, `avg_logprob_default=0.0`).
  - `libs/common/versions.py` (sha256
    `be0b136d4f910dd12481554405a5a0ec53091f8222b15ab622cedea0af0161f6`) —
    appended `DETERMINISTIC_SELECTOR_VERSION = "deterministic_selector_v1"`;
    `NORMALIZATION_VERSION`, `METRICS_VERSION`, `DEGRADATION_VERSION`,
    `ENHANCER_VERSION` preserved.
  - `scripts/robust_asr/build_selector_evidence_table.py` (sha256
    `226e428e84e1c0646922893d23456c64eef02511424d1c5e2dfef2f1b557735a`)
    — Section 5.5 reference selector applied per row; emits
    `OK_SELECTOR_EVIDENCE_BUILD rows=<N>`.
  - `scripts/robust_asr/validate_selector_evidence.py` (sha256
    `68c39ca111b3ee8eaada8a13fd9b51ab9e282a35efefbb122d24925febe2c1d2`)
    — enforces six §982-§1001 assertions; emits `OK_SELECTOR_EVIDENCE`.
  - `artifacts/robust_asr/router/selector_evidence.parquet` (sha256
    `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7`,
    53 230 rows).
  - `reports/robust_asr/router/selector_evidence_summary.md` (sha256
    `fab05394feb361bb0c1e24b15f32e53b651ea33a4f0e0e3c42affd3914c47d89`).
  - `reports/robust_asr/task_reports/P6.1_selector_evidence.md` (sha256
    `28f1f7d6716f4ca190272544e96352f86607a9d00f062f66b3522e57fea423c0`).
- Verification:
  - `python3 scripts/robust_asr/build_selector_evidence_table.py …` →
    `OK_SELECTOR_EVIDENCE_BUILD rows=53230`.
  - `python3 scripts/robust_asr/validate_selector_evidence.py …` →
    `OK_SELECTOR_EVIDENCE`.
  - `python3 -m pytest tests/robust_asr -q` → 124 passed (unchanged
    from the P5.1 baseline; no new tests authorized for P6.1).
  - `python3 scripts/robust_asr/validate_report_shape.py …` →
    `OK_REPORT_SHAPE`.
- Result (Outcome E, single deployable backend):
  - `selected_action`: 53 202 `whisper_base_ct2_int8`
    (`selector_reason=baseline`) + 28 `ask_repeat`
    (`selector_reason=no_speech`, derived from empty
    `normalized_transcript`).
  - Zero `assemblyai` or `whisper_lora_ct2_int8` selections;
    `assemblyai_available=False`, `lora_available=False`,
    `ask_repeat_allowed=True` on every row.
  - Disjointness: LoRA-train overlap = 0 (eval is `dev-clean` /
    `test-clean`, LoRA train is `train-clean-100`; checked at both
    full-id and base-stem granularity); demo overlap = 0 (manifest
    absent pre-P8.2).
- Tracker mutations:
  `current_task` advanced `P6.1 -> P6_GATE`;
  `last_completed_task` advanced `P5.1 -> P6.1`;
  `tasks.P6.1.status = PASS` (branch B);
  `tasks.P6.1.sentinels = [OK_SELECTOR_EVIDENCE_BUILD,
  OK_SELECTOR_EVIDENCE, OK_REPORT_SHAPE]`;
  `tasks.P6.2.status = SKIPPED_BY_OUTCOME_E`, `next_task = P7.3`
  (agent plan §3853-§3854);
  `deterministic_selector_version = deterministic_selector_v1`;
  `router_status = SELECTOR_EVIDENCE_BUILT`;
  artifacts `router_v1_config`, `versions_module`,
  `build_selector_evidence_script`, `validate_selector_evidence_script`,
  `selector_evidence_table`, `selector_evidence_summary`,
  `P6_1_task_report` recorded with sha256s;
  `oracle_table.path` held null (`blocked_by =
  OUTCOME_E_DETERMINISTIC_SELECTOR`,
  `blocked_reason = branch_B_selector_evidence_taken`);
  `latest_approval_packet` = APPROVE_PLAN(P6.1) on `4a9f929` (next P6_GATE);
  prior CHANGE_SCOPE(P6.1) demoted to
  `prior_approval_packet_p6_1_change_scope`;
  APPROVE_EXECUTION(P6.1-scope-change) recorded as
  `prior_approval_packet_p6_1_scope_exec`;
  `state_transport.expected_next_task = P6_GATE`;
  `state_transport.last_accepted_report_commit =
  c71e0a0bb25a5d2749801d8fc7444869ff331d1b` held per orchestrator
  instruction (NOT advanced to the P6.1 implementation commit).
  Held: `current_phase=P6`,
  `markers=[BLOCKED_OOD_PUBLIC, BLOCKED_API,
  OUTCOME_E_DETERMINISTIC_SELECTOR]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `.cloud_tradeoff=false`,
  `.positive_lora=false`, `.positive_system=pending`,
  `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`,
  `phase_summary={P0,P1,P2,P3,P5}=PASS`,
  `orchestrator_approvals={P0,P1,P2,P3,P5}=PHASE_APPROVE`.
- P6_GATE not started. `P7.1` / `P7.2` skips remain owned by the P6
  gate (§312, §2664-§2665); P6.1 owns only the P6.2 skip. No Slurm
  submission, no AssemblyAI call, no LoRA call.

## P6.1 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P6.1 phase=P6
  decision=CHANGE_SCOPE accepted_report_commit=`9ffc885`
  next_expected_task=P6.1
  required_fix="Authorize deterministic-selector config, selector evidence
  scripts, selector evidence table, and DETERMINISTIC_SELECTOR_VERSION."
- Rationale: P6.1 Outcome E selector-evidence path requires
  `configs/robust_asr/router_v1.yaml` and `libs/common/versions.py`
  (append `DETERMINISTIC_SELECTOR_VERSION` only), but current reuse/touch
  policy did not authorize these P6.1 writes.
- Reuse policy amendments (`configs/robust_asr/reuse_policy_v1.yaml`):
  - `configs/robust_asr/**` `allowed_tasks` += `P6.1`.
  - New row `configs/robust_asr/router_v1.yaml`: class=`active_state`,
    permitted_use=`read_write`, allowed_tasks=`[P6.1, P6.2, P7.1, P7.3,
    P10.1]`, validator=`scripts/robust_asr/validate_selector_evidence.py`,
    checksum_required=`true`, large_artifact=`false`, commit_allowed=`true`.
  - Amend `libs/common/versions.py` row: allowed_tasks=`[P1.2]` →
    `[P1.2, P6.1]`; permitted_use=`append_constants_only` (held);
    validator=`NORMALIZATION_VERSION_constant_present AND
    DETERMINISTIC_SELECTOR_VERSION_constant_present`; checksum_required=
    `true`; large_artifact=`false`; commit_allowed=`true`. Existing
    constants (NORMALIZATION_VERSION, METRICS_VERSION, DEGRADATION_VERSION,
    ENHANCER_VERSION) must remain unchanged.
- Touch-policy amendments (`reports/robust_asr/touch_policy.md`, P6.1 row
  rewritten): authorize writes of `configs/robust_asr/router_v1.yaml`,
  `scripts/robust_asr/build_selector_evidence_table.py`,
  `scripts/robust_asr/validate_selector_evidence.py`,
  `artifacts/robust_asr/router/selector_evidence.parquet`,
  `reports/robust_asr/router/selector_evidence_summary.md`,
  `reports/robust_asr/task_reports/P6.1_selector_evidence.md`,
  `libs/common/versions.py` (append `DETERMINISTIC_SELECTOR_VERSION`
  only), `configs/robust_asr/reuse_policy_v1.yaml` (scope-change rows),
  `reports/robust_asr/touch_policy.md` (scope-change row), and the three
  live trackers. Authorize reads of plan files, `reuse_policy_v1.yaml`,
  `configs/robust_asr/{router_v1,data_v1,eval_manifests_v1,degradation_v1}.yaml`,
  `libs/common/{eval_schema.yaml,normalization.py,metrics.py,versions.py}`,
  `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
  `artifacts/robust_asr/manifests/*.parquet`,
  `artifacts/robust_asr/lora_smoke/**` (LoRA-train audio_id disjointness),
  `artifacts/robust_asr/demo/**` (trivial disjointness pre-P8.2), and
  `scripts/robust_asr/validate_report_shape.py`. Explicit P6.1
  default_no_touch additions: `artifacts/robust_asr/oracle/**` (Branch A
  only; OUTCOME_E active), P6.2 router feature/matrix artifacts, P7.x
  candidate/selected_router artifacts, AssemblyAI runtime files, LoRA
  artifacts, `libs/audio/**` (write), `libs/asr_adapter/**` (write),
  `libs/common/**` (write except `libs/common/versions.py` append),
  `tests/robust_asr/**` (write — P6.1 not in tests/robust_asr/**
  allowed_tasks), `slurm/**`, `configs/training/**`,
  `scripts/training/**`, `services/**`, `infra/**`,
  `configs/robust_asr/pricing_v1.yaml` (write),
  `configs/robust_asr/eval_manifests_v1.yaml` (write). External:
  none (no Slurm, no Apptainer GPU, no external API for P6.1).
- Artifact sha256 updates:
  - `artifacts.reuse_policy_config.sha256` =
    `9994a741d85fb9b4c2c6aa6ea5d5ce71f763cb551c4b0403964abd10cfdbdb7c`;
    `last_amended_by` = `P6.1_scope_change`.
  - `artifacts.touch_policy.sha256` =
    `382f66de62a207472ee77a35d9af88585901e29394670043bf34198823f56a42`;
    `last_amended_by` = `P6.1_scope_change`.
- Tracker mutations:
  `latest_approval_packet` = CHANGE_SCOPE(P6.1) on `9ffc885` (next P6.1);
  previous PHASE_APPROVE(P5) demoted to `prior_approval_packet_p5_phase`
  on `c71e0a0` (next P6.1);
  `state_transport.expected_next_task = P6.1` held;
  `state_transport.last_accepted_report_commit =
  c71e0a0bb25a5d2749801d8fc7444869ff331d1b` held (CHANGE_SCOPE does not
  advance `last_accepted_report_commit`);
  `tasks.P6.1.status = scope_change_recorded` with `implementation_status =
  NOT_STARTED`; `tasks.P6.2` held `null` (`SKIPPED_BY_OUTCOME_E` is
  enacted by P6.1 closure, per agent plan §3853-§3854).
  Held: `current_phase=P6`, `current_task=P6.1`, `last_completed_task=P5.1`,
  `markers=[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]`,
  `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`,
  `claims_enabled.cloud_tradeoff=false`,
  `claims_enabled.positive_lora=false`,
  `claims_enabled.positive_system=pending`,
  `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`,
  `phase_summary={P0,P1,P2,P3,P5}=PASS`,
  `orchestrator_approvals={P0,P1,P2,P3,P5}=PHASE_APPROVE`.
- `validate_report_shape.py` → `OK_REPORT_SHAPE`.
- P6.1 implementation has not started: no `router_v1.yaml`, no
  `build_selector_evidence_table.py`, no `validate_selector_evidence.py`,
  no `selector_evidence.parquet`, no `selector_evidence_summary.md`, no
  `DETERMINISTIC_SELECTOR_VERSION` constant, no `P6.2` skip mutation,
  no task report. Awaits `APPROVE_PLAN(P6.1)` and
  `APPROVE_EXECUTION(P6.1)`. No code, no test, no Slurm submission,
  no real-provider call for this update. Only policy and tracker files
  modified.

## P5 PHASE_APPROVE recorded — OUTCOME_E activated

- ORCHESTRATOR_DECISION: scope=phase task=null phase=P5
  decision=PHASE_APPROVE
  accepted_report_commit=`c71e0a0bb25a5d2749801d8fc7444869ff331d1b`
  next_expected_task=P6.1 required_fix=null.
- Rationale: P5 phase gate PASS via the BLOCKED_API + `cloud_tradeoff=false`
  branch of §2589–§2596. `tasks.P5.1.status=HALTED` ∈ {PASS, PARTIAL, HALTED}
  AND marker `BLOCKED_API` active AND `claims_enabled.cloud_tradeoff=false`
  satisfies the predicate one-of clause. Backend-count predicate (§2607–2613):
  start with `{whisper_base_ct2_int8}`; LoRA excluded by
  `Decision_B_lora_full.include_lora_in_router=false` (Decision_A_smoke=FAIL);
  AssemblyAI excluded by `BLOCKED_API` active. Count = 1 < 2 →
  `OUTCOME_E_DETERMINISTIC_SELECTOR` activated at the P5 gate. Routing
  advances to P6.1 selector-evidence path (§3848–§3853). BLOCKED_OOD_PUBLIC
  and BLOCKED_API remain active and non-blocking.
- Tracker mutations:
  `current_phase` advanced `P5 -> P6`;
  `current_task` advanced `P5_GATE -> P6.1`;
  `last_completed_task` held at `P5.1` (PHASE_APPROVE recorded against the
  P5.1 acceptance commit does not itself advance last_completed_task,
  matching the P0/P1/P2/P3 pattern);
  `phase_summary.P5 = PASS`;
  `orchestrator_approvals.P5 = PHASE_APPROVE`;
  `markers` → `[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]`;
  `decisions.P5_routing.branch = B_blocked_api_outcome_e`;
  `decisions.P5_routing.deployable_backend_count = 1`;
  `decisions.P5_routing.deployable_backends = [whisper_base_ct2_int8]`;
  `decisions.P5_routing.outcome_e_activated_at_task = P5_GATE`;
  `state_transport.latest_approval_packet` = PHASE_APPROVE(P5) on `c71e0a0`;
  `prior_approval_packet_p5_1_exec` = APPROVE_EXECUTION(P5.1) on `c71e0a0`;
  `state_transport.expected_next_task = P6.1`;
  `state_transport.last_accepted_report_commit = c71e0a0…` held
  (PHASE_APPROVE recorded against the P5.1 acceptance commit; not advanced
  by the phase-gate tracker commit itself).
  Held: `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`,
  `claims_enabled.cloud_tradeoff=false`, `claims_enabled.positive_lora=false`,
  `claims_enabled.positive_system=pending`,
  `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`, `metrics_version=metrics_v1`,
  `phase_summary={P0,P1,P2,P3}=PASS`,
  `orchestrator_approvals={P0,P1,P2,P3}=PHASE_APPROVE`.
- P6.1 selector-evidence path is the next task. `tasks.P6.2.status =
  SKIPPED_BY_OUTCOME_E` is NOT enacted by the P5 gate — it is enacted by
  P6.1 per §3853. `tasks.P7.1`/`tasks.P7.2` skips are owned by the P6
  gate (§312, §2664–§2665). BLOCKED_OOD_PUBLIC NOT cleared. BLOCKED_API
  NOT cleared. P6.1 not started. No code, no test, no Slurm submission,
  no real-provider call for this update. Only tracker files modified.

## P5.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P5.1 phase=P5
  decision=APPROVE_EXECUTION
  accepted_report_commit=`c71e0a0bb25a5d2749801d8fc7444869ff331d1b`
  next_expected_task=P5_GATE required_fix=null.
- Rationale: P5.1 legally halted with `BLOCKED_API reason=key_unset`.
  `ASSEMBLYAI_API_KEY` was unset, no HTTP request or paid API call was
  made, pricing guard and tests passed, `claims_enabled.cloud_tradeoff=false`
  was set, and `BLOCKED_OOD_PUBLIC` remains active and non-blocking.
- Tracker mutations:
  `current_task` advanced `P5.1 -> P5_GATE`;
  `last_completed_task` advanced `P3.2 -> P5.1`;
  `tasks.P5.1.status=HALTED` held;
  `tasks.P5.1.marker=BLOCKED_API` held;
  `tasks.P5.1.commit=c71e0a0bb25a5d2749801d8fc7444869ff331d1b`;
  `state_transport.last_accepted_report_commit` advanced
  `26db72d… -> c71e0a0bb25a5d2749801d8fc7444869ff331d1b`;
  `state_transport.expected_next_task=P5_GATE` held;
  `latest_approval_packet` = APPROVE_EXECUTION(P5.1) on `c71e0a0`;
  prior `APPROVE_PLAN(P5.1)` demoted to `prior_approval_packet_p5_1_plan` on `f7a845f`.
  Held: `current_phase=P5`, `markers=[BLOCKED_OOD_PUBLIC, BLOCKED_API]`,
  `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`,
  `claims_enabled.cloud_tradeoff=false`, `claims_enabled.positive_lora=false`,
  `claims_enabled.positive_system=pending`,
  `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`, `metrics_version=metrics_v1`,
  `phase_summary={P0,P1,P2,P3}=PASS`,
  `orchestrator_approvals={P0,P1,P2,P3}=PHASE_APPROVE`.
- P5_GATE not started. P6.1 not started. No code, no test, no Slurm
  submission, no real-provider call for this update. Only tracker files
  modified.

## P5.1 HALTED — BLOCKED_API (key_unset)

- APPROVE_EXECUTION(P5.1-scope-change) recorded on `f7a845f` (next P5.1);
  APPROVE_PLAN(P5.1) recorded on `f7a845f` (next P5_GATE).
- Probe `python3 scripts/robust_asr/probe_assemblyai_runtime.py` →
  `ASSEMBLYAI_RUNTIME=false reason=key_unset`. `ASSEMBLYAI_API_KEY` is
  unset on datamove1. Per agent plan §3786–3805, cache populate and
  evaluate are skipped; `BLOCKED_API` is the legal Section 5 closure.
- Deliverables written: `configs/robust_asr/pricing_v1.yaml`,
  `configs/robust_asr/eval_manifests_v1.yaml` (append assemblyai
  `backend_endpoints` entry only),
  `scripts/robust_asr/probe_assemblyai_runtime.py`,
  `scripts/robust_asr/populate_assemblyai_cache.py`,
  `scripts/robust_asr/evaluate_assemblyai_from_cache.py`,
  `tests/robust_asr/test_assemblyai.py` (15 tests),
  `reports/robust_asr/task_reports/P5.1_assemblyai.md`. No
  `assemblyai.parquet`, no `cache_summary.json`, no Slurm submission, no
  AssemblyAI request.
- Paid-API guard (`populate_assemblyai_cache.py`):
  exit 8 = `ASSEMBLYAI_API_KEY_UNSET`;
  exit 12 = `PENDING_PRICING_VERIFICATION` (>90 day old `assemblyai_pricing_checked_date`);
  exit 11 = `BUDGET_EXCEEDED` (estimated total cost > `max_total_cost_usd`,
  or per-row running-cost check would exceed the cap mid-run);
  exit 9 = `ASSEMBLYAI_AUTH_FAIL` on HTTP 401/403;
  exit 10 = `ASSEMBLYAI_QUOTA` on HTTP 429 after retries.
  Pre-spend summary printed BEFORE any upload.
  `ASSEMBLYAI_API_KEY` is read from the environment only and is never
  logged or written to disk. Tests exercise all five guards without
  network calls.
- Verification: `python3 -m pytest tests/robust_asr/test_assemblyai.py -q`
  → `15 passed`; full `pytest tests/robust_asr/` → `124/124 PASS`
  (was 109; +15 new); `validate_report_shape.py` → `OK_REPORT_SHAPE`.
- Tracker mutations:
  `tasks.P5.1.status = HALTED`;
  `tasks.P5.1.blocked_marker = BLOCKED_API` (`reason=key_unset`);
  `markers` → `[BLOCKED_OOD_PUBLIC, BLOCKED_API]`;
  `claims_enabled.cloud_tradeoff = false` (was `true`);
  `assemblyai_table.path = null`, `blocked_by = BLOCKED_API`,
  `expected_path = artifacts/robust_asr/eval_tables/assemblyai.parquet`;
  `latest_approval_packet` = APPROVE_PLAN(P5.1) on `f7a845f`;
  prior `APPROVE_EXECUTION(P5.1-scope-change)` recorded as
  `prior_approval_packet_p5_1_scope_exec`;
  prior `CHANGE_SCOPE(P5.1)` demoted to `prior_approval_packet_p5_1_change_scope`;
  `state_transport.expected_next_task = P5_GATE`;
  `state_transport.last_accepted_report_commit = 26db72d…` held
  (CHANGE_SCOPE + APPROVE_PLAN do not advance `last_accepted_report_commit`
  to the P5.1 implementation commit).
- Held: `current_phase=P5`, `current_task=P5.1` (held until
  APPROVE_EXECUTION(P5.1) advances it to `P5_GATE`),
  `last_completed_task=P3.2`, `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=false`,
  `claims_enabled.positive_system=pending`,
  `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`, `metrics_version=metrics_v1`,
  `phase_summary={P0,P1,P2,P3}=PASS`,
  `orchestrator_approvals={P0,P1,P2,P3}=PHASE_APPROVE`.
- `BLOCKED_OOD_PUBLIC` NOT cleared; held non-blocking.
- P5_GATE not started. Awaits orchestrator `APPROVE_EXECUTION(P5.1)`.

## P5.1 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P5.1 phase=P5
  decision=CHANGE_SCOPE
  accepted_report_commit=`45b6cac93d1fe3eb54630a7511c331439715bb68`
  next_expected_task=P5.1
  required_fix="Authorize AssemblyAI pricing config, runtime scripts/tests, eval manifest extension, and scratch cache path."
  rationale: "P5.1 requires `configs/robust_asr/pricing_v1.yaml`,
  `eval_manifests_v1.yaml` update, `tests/robust_asr/test_assemblyai.py`,
  and scratch AssemblyAI cache writes, but prior policy rows did not
  authorize these for P5.1."
- Scope-change applied at commit `e45903e76b5b42d3ceb2a89b77ec7675d9d239d4`
  (files: `configs/robust_asr/reuse_policy_v1.yaml`, `reports/robust_asr/touch_policy.md`).
- Reuse policy mutations:
  `configs/robust_asr/**` allowed_tasks `+= P5.1`;
  `tests/robust_asr/**` allowed_tasks `+= P5.1`;
  new row `configs/robust_asr/pricing_v1.yaml` (`active_state`, `read_write`,
  allowed_tasks=`[P5.1, P10.1]`, validator=`load_yaml_and_check_required_fields`,
  `checksum_required=true`, `commit_allowed=true`);
  new row `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/assemblyai_cache/**`
  (`data_root`, `read_write`, allowed_tasks=`[P5.1]`, validator=`cache_summary_json`,
  `large_artifact=true`, `commit_allowed=false`).
- Touch policy P5.1 row rewritten. New `allowed_write_paths` now include:
  `configs/robust_asr/pricing_v1.yaml`, `configs/robust_asr/eval_manifests_v1.yaml`
  (append `assemblyai` `backend_endpoints` entry only),
  `configs/robust_asr/reuse_policy_v1.yaml` (scope-change rows),
  `scripts/robust_asr/probe_assemblyai_runtime.py`,
  `scripts/robust_asr/populate_assemblyai_cache.py`,
  `scripts/robust_asr/evaluate_assemblyai_from_cache.py`,
  `tests/robust_asr/test_assemblyai.py`,
  `artifacts/robust_asr/eval_tables/assemblyai.parquet`,
  `reports/robust_asr/assemblyai/cache_summary_summary.md`,
  `reports/robust_asr/task_reports/P5.1_assemblyai.md`,
  `reports/robust_asr/touch_policy.md` (scope-change row),
  `docs/progress/robust_asr_progress.yaml`,
  `docs/progress/robust_asr_progress.md`,
  `docs/progress/robust_asr_state_capsule.md`.
- Authorized external read/write:
  `ASSEMBLYAI_API_KEY` from environment only (never logged or persisted);
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/assemblyai_cache/**`
  (`read_write`, large_artifact, never committed);
  robust_asr Apptainer image `/mnt/fast/.../robust_asr_py311_cuda12.sif` (exec only).
- New `configs/robust_asr/reuse_policy_v1.yaml` sha256 =
  `d72cc31f5ca46b7adb01cde7a8ffd3301c46fce58c8e8ff61c0c8bba8ed109ee`
  (`artifacts.reuse_policy_config.sha256`,
  `artifacts.reuse_policy_config.last_amended_by=P5.1_scope_change`).
- New `reports/robust_asr/touch_policy.md` sha256 =
  `710a49f2e87c9755d7b00cf66c68bcdeaa9088b8eb5f44ccbcc347de4d58b4aa`
  (`artifacts.touch_policy.sha256`,
  `artifacts.touch_policy.last_amended_by=P5.1_scope_change`).
- Validation: `python scripts/robust_asr/validate_report_shape.py --schemas
  docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` → `OK_REPORT_SHAPE`.
- `state_transport.latest_approval_packet` = CHANGE_SCOPE(P5.1) on `45b6cac`;
  prior `PHASE_APPROVE(P3)` packet demoted to `prior_approval_packet_p3_phase`;
  `state_transport.expected_next_task = P5.1`;
  `state_transport.last_accepted_report_commit = 26db72d…` (held; CHANGE_SCOPE
  does not advance `last_accepted_report_commit`).
- Held: `current_phase=P5`, `current_task=P5.1`, `last_completed_task=P3.2`,
  `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=false`,
  `claims_enabled.cloud_tradeoff=true`, `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`,
  `phase_summary={P0,P1,P2,P3}=PASS`,
  `orchestrator_approvals={P0,P1,P2,P3}=PHASE_APPROVE`.
- P5.1 implementation has not started: no `pricing_v1.yaml`, no probe/populate/
  evaluate scripts, no `test_assemblyai.py`, no `eval_manifests_v1.yaml`
  extension, no `assemblyai.parquet`, no AssemblyAI API call, no Slurm
  submission. Awaits `APPROVE_PLAN(P5.1)` and `APPROVE_EXECUTION(P5.1)`.

## P3 PHASE_APPROVE recorded — Branch B skip P4

- ORCHESTRATOR_DECISION: scope=phase task=null phase=P3
  decision=PHASE_APPROVE
  accepted_report_commit=`26db72df3215355a68029927980389216353526e`
  next_expected_task=P5.1.
- Rationale: P3 phase gate PASS per Section 8 P3 predicate. `tasks.P3.1=PASS`,
  `tasks.P3.2=PASS`, `lora_smoke_report.md` first line = `FAIL`,
  `decision_a_smoke.md` present, `Decision_A_smoke.outcome=FAIL` ∈
  {PASS, PARTIAL, FAIL, HALTED}, no `BLOCKED_RUNTIME` / `MISSING_EVIDENCE` /
  `PLAN_CONFLICT`. Decision_A_smoke=FAIL routes to Branch B of the P3 gate:
  P4.1/P4.2/P4.3 skipped, LoRA excluded from router, no positive LoRA claims,
  next task P5.1. `BLOCKED_OOD_PUBLIC` remains active and non-blocking.
- Tracker mutations:
  `current_phase` advanced `P3 -> P5`;
  `current_task` advanced `P3_GATE -> P5.1`;
  `last_completed_task` held at `P3.2` (P3_GATE PHASE_APPROVE is recorded on
  the P3.2 acceptance commit and does not itself advance last_completed_task);
  `phase_summary.P3 = PASS`;
  `orchestrator_approvals.P3 = PHASE_APPROVE`;
  `lora_status` transitioned `SMOKE_DONE -> SKIPPED_BY_DECISION_A`;
  `claims_enabled.positive_lora` transitioned `pending -> false`;
  `decisions.Decision_B_lora_full.include_lora_in_router` set `false`
  (`decided_at_task=P3_GATE`);
  `tasks.P4.1.status = SKIPPED_BY_DECISION_A`;
  `tasks.P4.2.status = SKIPPED_BY_DECISION_A`;
  `tasks.P4.3.status = SKIPPED_BY_DECISION_A`;
  `state_transport.latest_approval_packet` = PHASE_APPROVE(P3) on `26db72d`;
  `prior_approval_packet_p3_2_exec` = APPROVE_EXECUTION(P3.2) on `26db72d`;
  `state_transport.expected_next_task = P5.1`;
  `state_transport.last_accepted_report_commit = 26db72d…` (held; PHASE_APPROVE
  recorded against the P3.2 acceptance commit and not itself advanced by the
  phase-gate tracker commit).
  Held: `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`,
  `blocker=null`, `claims_enabled.ood_real=false`,
  `claims_enabled.cloud_tradeoff=true`,
  `claims_enabled.positive_system=pending`, `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`, `metrics_version=metrics_v1`,
  `phase_summary={P0:PASS, P1:PASS, P2:PASS, P3:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE,
  P2:PHASE_APPROVE, P3:PHASE_APPROVE}`.
- P5.1 not started. AssemblyAI cloud baseline awaits its own
  `APPROVE_PLAN(P5.1)` and `APPROVE_EXECUTION(P5.1)`. No code, no test, no
  Slurm submission, no real-provider call for this update. Only tracker
  files modified.

## P3.2 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P3.2 phase=P3
  decision=APPROVE_EXECUTION
  accepted_report_commit=`26db72df3215355a68029927980389216353526e`
  next_expected_task=P3_GATE.
- Rationale: P3.2 passed. Decision_A_smoke was mechanically recorded as FAIL
  with sentinel `OK_LORA_SMOKE_DECISION:FAIL`. Tests passed
  (12/12 new + 109/109 full robust_asr suite), and
  `validate_report_shape.py` emitted `OK_REPORT_SHAPE`. P3 gate will enact
  downstream routing and P4 skips.
- Tracker mutations:
  `current_task` advanced `P3.2 -> P3_GATE`;
  `last_completed_task` advanced `P3.1 -> P3.2`;
  `tasks.P3.2.status=PASS` (held);
  `tasks.P3.2.commit=26db72df3215355a68029927980389216353526e`;
  `state_transport.last_accepted_report_commit` advanced
  `096fe43 -> 26db72d`;
  `state_transport.expected_next_task=P3_GATE` (held).
  `latest_approval_packet`=APPROVE_EXECUTION(P3.2) on `26db72d`;
  `prior_approval_packet_p3_2_plan`=APPROVE_PLAN(P3.2) on `1025a24`.
  Held: `current_phase=P3`, `markers=[BLOCKED_OOD_PUBLIC]`
  (non-blocking), `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`,
  `claims_enabled.positive_lora=pending` (P3 gate enacts → false),
  `lora_status=SMOKE_DONE` (P3 gate enacts → `SKIPPED_BY_DECISION_A`),
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`,
  `phase_summary={P0:PASS, P1:PASS, P2:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE,
  P2:PHASE_APPROVE}`.
- P3_GATE not started. P4 task statuses (`P4.1`, `P4.2`, `P4.3`) remain
  unchanged; they transition to `SKIPPED_BY_DECISION_A` only when the
  orchestrator runs the P3 gate. No script, no test, no Slurm submission
  for this update. Only tracker files modified.

## P3.2 PASS — Decision A = FAIL

- Decision_A_smoke.outcome = **FAIL** (mechanical Section 5.1).
- Sentinel: `OK_LORA_SMOKE_DECISION:FAIL`.
- Mechanical reasons:
  - `macro_wa_gain = -0.12843 < 0.005` (PASS branch A fails)
  - `max_family_wa_gain = -0.11345 < 0.010` (PASS branch B / PARTIAL fail)
  - `clean_wa_regression = 0.11345 > 0.010` and `> 0.020` (clean reg above both ceilings)
  - `per_family_wa_gain_variance = 1.79e-4 ≠ 0` (degenerate guard not active)
  - `export_smoke_result.outcome = PASS` (not HALTED, not EXPORT_BLOCKED)
- Deliverables written:
  - `scripts/robust_asr/decide_lora_smoke.py` (Section 5.1 CLI per §1263–§1285)
  - `tests/robust_asr/test_decide_lora_smoke.py` (12 unit tests; CLI end-to-end)
  - `reports/robust_asr/lora/lora_smoke_report.md` (first line: `FAIL`)
  - `reports/robust_asr/lora/decision_a_smoke.md` (narrative + expected
    P3-gate side effects per Section 0.1 / Section 5.10)
  - `reports/robust_asr/task_reports/P3.2_decision_a.md`
- Verification:
  - `python3 -m pytest -q tests/robust_asr/test_decide_lora_smoke.py` → 12 passed
  - `python3 scripts/robust_asr/decide_lora_smoke.py …` → `OK_LORA_SMOKE_DECISION:FAIL`
  - `python3 -m pytest -q tests/robust_asr/` → 109 passed (was 97 pre-P3.2; +12 new)
  - `python3 scripts/robust_asr/validate_report_shape.py …` → `OK_REPORT_SHAPE`
- Tracker mutations:
  `tasks.P3.2.status=PASS`;
  `tasks.P3.2.sentinels=[OK_LORA_SMOKE_DECISION:FAIL]`;
  `decisions.Decision_A_smoke.outcome=FAIL`;
  `decisions.Decision_A_smoke.decided_at_task=P3.2`;
  `state_transport.latest_approval_packet`=APPROVE_PLAN(P3.2) on `1025a24`
  (next P3_GATE);
  `prior_approval_packet_p3_2_scope_exec`=APPROVE_EXECUTION(P3.2-scope-change)
  on `1025a24`;
  `prior_approval_packet_p3_2_change_scope`=CHANGE_SCOPE(P3.2) on `ee92c8b`;
  `state_transport.expected_next_task=P3_GATE`.
  Held: `current_task=P3.2`, `last_completed_task=P3.1`,
  `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`,
  `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=pending`
  (P3 gate enacts the transition to false), `lora_status=SMOKE_DONE`
  (P3 gate enacts the transition to `SKIPPED_BY_DECISION_A`),
  `state_transport.last_accepted_report_commit=096fe43...` (STAYS per
  orchestrator instruction; NOT advanced to the P3.2 implementation commit).
- P4 task statuses are NOT modified by P3.2. The P3 gate enacts
  `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `lora_status=SKIPPED_BY_DECISION_A`,
  `decisions.Decision_B_lora_full.include_lora_in_router=false`,
  `claims_enabled.positive_lora=false`. Next post-gate task = P5.1.

## P3.2 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P3.2 phase=P3
  decision=CHANGE_SCOPE
  accepted_report_commit=`ee92c8b`
  next_expected_task=P3.2
  required_fix="Rewrite touch_policy P3.2 row to authorize Decision A
  script, test, and lora smoke report."
- Rationale: P3.2 requires `scripts/robust_asr/decide_lora_smoke.py`,
  `tests/robust_asr/test_decide_lora_smoke.py`, and
  `reports/robust_asr/lora/lora_smoke_report.md`, but the prior
  `touch_policy.md` P3.2 row omitted them.
- Touch_policy P3.2 row rewritten (allowed writes):
  `scripts/robust_asr/decide_lora_smoke.py`,
  `tests/robust_asr/test_decide_lora_smoke.py`,
  `reports/robust_asr/lora/lora_smoke_report.md`,
  `reports/robust_asr/lora/decision_a_smoke.md`,
  `reports/robust_asr/task_reports/P3.2_decision_a.md`,
  `reports/robust_asr/touch_policy.md` (scope-change rows),
  `docs/progress/robust_asr_progress.yaml`,
  `docs/progress/robust_asr_progress.md`,
  `docs/progress/robust_asr_state_capsule.md`.
  Reads add `configs/robust_asr/reuse_policy_v1.yaml`,
  `reports/robust_asr/lora/lora_smoke_result.json`,
  `artifacts/robust_asr/lora_smoke/export_smoke_result.json`,
  `libs/common/{versions,normalization,metrics}.py`,
  `scripts/robust_asr/validate_report_shape.py`. No external paths.
- No script implemented, no test created, no Decision A made, no
  `lora_smoke_report.md` written. This commit is the scope change only.
- Tracker mutations:
  `current_task=P3.2` held; `last_completed_task=P3.1` held;
  `markers=[BLOCKED_OOD_PUBLIC]` held; `blocked=false`;
  `claims_enabled.ood_real=false`; `lora_status=SMOKE_DONE` held;
  `state_transport.latest_approval_packet`=CHANGE_SCOPE(P3.2) on
  `ee92c8b`; previous APPROVE_EXECUTION(P3.1) demoted to
  `prior_approval_packet_p3_1_exec`;
  `state_transport.last_accepted_report_commit` STAYS at `096fe43`
  per orchestrator instruction (NOT advanced to the P3.2 scope-change
  implementation commit);
  `state_transport.expected_next_task=P3.2` held;
  `touch_policy.last_amended_by=P3.2_scope_change`;
  `artifacts.touch_policy.sha256=52c82b41624861f384c155ee44b6a40d8bc4d0b3a4473083952a6cb0f910d14a`
  (recorded post-commit `e8d5784`).
- Verification: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` → PASS.
- Next: orchestrator APPROVE_PLAN(P3.2) and APPROVE_EXECUTION(P3.2)
  required before `decide_lora_smoke.py` is implemented and Decision A
  is recorded.

## P3.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P3.1 phase=P3
  decision=APPROVE_EXECUTION
  accepted_report_commit=`096fe43371f7357007ce41317ed758499d1ff131`
  next_expected_task=P3.2.
- Rationale: P3.1 passed. `OK_LORA_SMOKE_TRAIN`, `OK_LORA_SMOKE_EVAL`,
  `OK_LORA_EXPORT_SMOKE`, `OK_REPORT_SHAPE`, and tests passed. LoRA
  smoke completed without `BLOCKED_RUNTIME`, `BUDGET_EXCEEDED`,
  `DEGENERATE_SMOKE_RESULT`, or `EXPORT_BLOCKED`. P3.2 will make
  Decision A from the recorded metrics.
- Tracker mutations:
  `current_task` advanced `P3.1 -> P3.2`;
  `last_completed_task` advanced `P2.2 -> P3.1`;
  `tasks.P3.1.commit=096fe43371f7357007ce41317ed758499d1ff131`;
  `state_transport.last_accepted_report_commit` advanced
  `3ed96f5 -> 096fe43`;
  `state_transport.expected_next_task=P3.2`.
  `latest_approval_packet`=APPROVE_EXECUTION(P3.1) on `096fe43`;
  `prior_approval_packet_p3_1_plan`=APPROVE_PLAN(P3.1) on `3ed96f5`;
  `prior_approval_packet_p3_1_scope_exec`=APPROVE_EXECUTION(P3.1-scope-change)
  on `3ed96f5`; `prior_approval_packet_p3_1_change_scope`=CHANGE_SCOPE(P3.1)
  on `ca98443`.
  Held: `current_phase=P3`, `markers=[BLOCKED_OOD_PUBLIC]`
  (non-blocking), `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`,
  `lora_status=SMOKE_DONE`, `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`,
  `phase_summary={P0:PASS, P1:PASS, P2:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE,
  P2:PHASE_APPROVE}`.
- P3.2 not started; awaiting orchestrator `APPROVE_PLAN(P3.2)` before
  implementation. P3.2 deliverables (per agent plan §3601-§3637):
  `reports/robust_asr/lora/lora_smoke_report.md` (PASS|PARTIAL|FAIL|HALTED
  outcome on first line) and `reports/robust_asr/lora/decision_a_smoke.md`
  (decision narrative). No code, no test, no Slurm submission for this
  update. Only tracker files modified.

## P3.1 PASS — LoRA smoke train, eval, export smoke (Slurm job 2131980)

- ORCHESTRATOR_DECISION: scope=task task=P3.1-scope-change phase=P3
  decision=APPROVE_EXECUTION
  accepted_report_commit=`3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91`
  next_expected_task=P3.1. Then immediately:
  scope=task task=P3.1 phase=P3 decision=APPROVE_PLAN
  accepted_report_commit=`3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91`
  next_expected_task=P3.2.
- Slurm job `2131980` COMPLETED `0:0` in `00:09:48` on
  `aisurrey03.surrey.ac.uk` (RTX 2080 Ti, partition `2080ti`,
  MaxRSS 2,826,500 KiB, container sha256 `8db5364c…ce8713`).
  All three sentinels emitted in order:
  - `OK_LORA_SMOKE_TRAIN steps_completed=200 best_step=100
    best_loss=0.5837` — 200 LoRA steps over the 600-row smoke_split
    with on-the-fly degradation; no OOM, no non-finite loss
    (`nonfinite_count=0`); LoRA trainable params 589,824 /
    73,183,232 total (0.806%); fp16 + AdamW + warmup_steps=20 +
    lr=1e-4; per-step duration ≈ 1.5–2 s on RTX 2080 Ti.
  - `OK_LORA_SMOKE_EVAL macro_wa_gain=-0.1284
    max_family_wa_gain=-0.1135 clean_wa_regression=0.1135` —
    1000 rows over the 200-base × 5-family
    `degradation_v1_id_eval.parquet` slice for the smoke_eval_split;
    `per_family_wa_gain_variance=1.79e-4` (non-degenerate so no
    `lora_smoke_degenerate.md` written); per-family WA gain:
    clean −0.1135, cafe_noise −0.1455, phone_band −0.1213,
    far_field_room −0.1436, muffled_lowpass −0.1183.
  - `OK_LORA_EXPORT_SMOKE` — merge_lora_fp16 OK (15.8 s) →
    ct2_int8_export OK (1.34 s, model.bin 77 MB INT8) →
    faster_whisper_transcribe OK (0.76 s on
    `librispeech/dev-clean/1272-128104-0000` clean fixture from the
    smoke_eval_split). Workaround applied: patched
    `TransformersConverter.load_model` strips `dtype`/`torch_dtype`
    kwargs to bridge transformers/ctranslate2 4.7.1 API mismatch
    (same pattern used by `build_whisper_base_ct2_int8.py` in
    P2.1-model-build).
- Predicted Decision A (Section 5.1, mechanical) is **SMOKE_FAIL**:
  `macro_wa_gain` (−0.1284) `< 0.005` AND `clean_regression` (0.1135)
  `> 0.010` ⇒ not SMOKE_PASS; `max_family_wa_gain` (−0.1135) `< 0.010`
  ⇒ not SMOKE_PARTIAL. P3.1 does NOT record this; P3.2 owns the
  decision and the side effects (Section 5.10 fallback: P4
  `SKIPPED_BY_DECISION_A`, `Decision_B_lora_full.include_lora_in_router
  = false`, `claims_enabled.positive_lora = false`).
- Run history (single PASS plus four iterative fixes, full
  reproducibility): see `reports/robust_asr/task_reports/P3.1_lora_smoke.md`
  for the per-attempt table (jobs 2131879, 2131884, 2131889, 2131891,
  2131897, 2131908, 2131980).
- Verifications:
  `python3 scripts/robust_asr/validate_report_shape.py …` →
  `OK_REPORT_SHAPE` exit 0;
  `python3 -m pytest -q tests/robust_asr/` → **97 passed in 3.51 s**
  (was 85 pre-P3.1; +9 new tests + 3 conditional tests now active
  after artifact production).
- Deliverables committed (all small JSON/CSV/PNG/MD/scripts/tests):
  `artifacts/robust_asr/lora_smoke/checkpoint_manifest.json` (sha256
  `21d519a5…01ce2`), `…/training_log.csv` (sha256 `d2fd4dca…faea8`),
  `…/loss_curve.png` (sha256 `3426869e…ab69c`, generated by the
  stdlib zlib+struct PNG fallback since the SIF has no matplotlib
  or PIL), `…/export_smoke_result.json` (sha256 `ca97450a…cda33ad`),
  `reports/robust_asr/lora/lora_smoke_result.json` (sha256
  `c5eac79f…721be`), `reports/robust_asr/task_reports/P3.1_lora_smoke.md`,
  plus the four new scripts/tests
  (`scripts/robust_asr/{train_lora_smoke,evaluate_lora_smoke,smoke_export_lora_ct2}.py`,
  `slurm/jobs/p3_1_lora_smoke.sh`, `tests/robust_asr/test_lora_smoke.py`)
  and the `.gitignore` extension for LoRA binary subtrees.
- Deliverables produced but NOT committed (gitignored per touch_policy):
  `artifacts/robust_asr/lora_smoke/checkpoints/step_{00050,00100,00150,00200}/`
  (4 LoRA adapter dirs, ~9.2 MiB total),
  `artifacts/robust_asr/lora_smoke/merged_fp16/` (FP16 base + LoRA,
  ~143 MiB), `artifacts/robust_asr/lora_smoke/ct2_int8/` (CT2 INT8
  export with model.bin ~77 MiB).
- HF cache staging (no scope change; lives under the
  pre-authorized model-root cache path read-only): `model.safetensors`
  (sha256 `d4dd5542…71db5`) and `config.json` (sha256 `160c1df4…be76`)
  were downloaded from `huggingface.co/openai/whisper-base.en/resolve/main`
  on datamove1 and symlinked into
  `…/cache/huggingface/hub/models--openai--whisper-base.en/snapshots/911407f4…/`
  alongside the tokenizer/preprocessor files that were already present.
  This is read-only data, never committed to git.
- Tracker mutations:
  `tasks.P3.1.status=PASS`,
  `tasks.P3.1.slurm_job_id=2131980`,
  `tasks.P3.1.next_task=P3.2`,
  `tasks.P3.1.marker=null`,
  `tasks.P3.1.artifacts_added.{checkpoint_manifest, training_log,
  loss_curve, lora_smoke_result, export_smoke_result, scripts,
  Slurm job, tests, task report}` populated;
  `lora_status=SMOKE_DONE`;
  `artifacts.lora_smoke_*` sha256s populated;
  `artifacts.lora_smoke_report.produced_by_task=P3.2` corrected
  (was incorrectly recorded as `P3.1` at tracker-init).
  `latest_approval_packet=APPROVE_PLAN(P3.1)` on `3ed96f5`;
  `prior_approval_packet_p3_1_scope_exec=APPROVE_EXECUTION(P3.1-scope-change)`
  on `3ed96f5`;
  `prior_approval_packet_p3_1_change_scope=CHANGE_SCOPE(P3.1)` on
  `ca98443`.
  Held: `current_phase=P3`, `current_task=P3.1` (orchestrator
  finalizes via `APPROVE_EXECUTION(P3.1)` before P3.2 may start),
  `last_completed_task=P2.2`, `markers=[BLOCKED_OOD_PUBLIC]`
  (non-blocking; NOT cleared), `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`,
  `phase_summary={P0:PASS, P1:PASS, P2:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE,
  P2:PHASE_APPROVE}`,
  `state_transport.last_accepted_report_commit=3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91`
  (NOT advanced to the P3.1 implementation commit per orchestrator
  instruction),
  `state_transport.expected_next_task=P3.2`.
- P3 gate predicate (Section 8 P3) is now half-satisfied:
  `tasks.P3.1` is PASS; awaiting orchestrator
  `APPROVE_EXECUTION(P3.1)` and then P3.2 (Decision A) before
  `PHASE_APPROVE(P3)` and the P4 / P5 routing.

## P3.1 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P3.1 phase=P3
  decision=CHANGE_SCOPE
  accepted_report_commit=`ca98443d380f675eb45666af19d3686f3fbfa54f`
  next_expected_task=P3.1.
  required_fix="Rewrite stale touch_policy P3.1 row for LoRA smoke
  train/eval/export deliverables."
- Rationale: P3.1 requires `scripts/robust_asr/train_lora_smoke.py`,
  `scripts/robust_asr/evaluate_lora_smoke.py`,
  `scripts/robust_asr/smoke_export_lora_ct2.py`,
  `slurm/jobs/p3_1_lora_smoke.sh`, smoke outputs
  (`artifacts/robust_asr/lora_smoke/{checkpoint_manifest.json,
  training_log.csv, loss_curve.png, export_smoke_result.json}`), and
  smoke reports (`reports/robust_asr/lora/{lora_smoke_result.json,
  lora_smoke_degenerate.md}`), but the current touch_policy P3.1 row
  still referenced the stale P3.2-style `lora_smoke_report.md` and
  omitted the three new scripts, the test file, and the JSON/degenerate
  deliverables.
- `reports/robust_asr/touch_policy.md` P3.1 row REWRITTEN. New
  `allowed_write_paths`:
  `scripts/robust_asr/train_lora_smoke.py`,
  `scripts/robust_asr/evaluate_lora_smoke.py`,
  `scripts/robust_asr/smoke_export_lora_ct2.py`,
  `slurm/jobs/p3_1_lora_smoke.sh`,
  `tests/robust_asr/test_lora_smoke.py`,
  `artifacts/robust_asr/lora_smoke/checkpoint_manifest.json`,
  `artifacts/robust_asr/lora_smoke/training_log.csv`,
  `artifacts/robust_asr/lora_smoke/loss_curve.png`,
  `artifacts/robust_asr/lora_smoke/export_smoke_result.json`,
  `reports/robust_asr/lora/lora_smoke_result.json`,
  `reports/robust_asr/lora/lora_smoke_degenerate.md`,
  `reports/robust_asr/task_reports/P3.1_lora_smoke.md`,
  `reports/robust_asr/touch_policy.md` (scope-change rows),
  `docs/progress/robust_asr_progress.yaml`,
  `docs/progress/robust_asr_progress.md`,
  `docs/progress/robust_asr_state_capsule.md`.
  New `allowed_read_paths`: plan files,
  `configs/robust_asr/{reuse_policy_v1.yaml, lora_smoke.yaml,
  data_v1.yaml, eval_manifests_v1.yaml, degradation_v1.yaml}`,
  `libs/common/{eval_schema.yaml, normalization.py, metrics.py,
  versions.py, runtime_contract.py}`,
  `libs/audio/**`, `libs/audio_pipeline/**`, `libs/asr_adapter/**`,
  `artifacts/robust_asr/manifests/{librispeech_lora_train.parquet,
  librispeech_validation.parquet, degradation_v1_*.parquet}`,
  `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
  `reports/robust_asr/{baseline_whisper_base.md, manifest_summary.md,
  degradation_v1_summary.md}`,
  `scripts/robust_asr/validate_report_shape.py`,
  `scripts/training/**`, `configs/training/**`.
  `default_no_touch_paths`: legacy trackers, `services/**`, `infra/**`,
  `configs/training/**` (write), `scripts/training/**` (write),
  `libs/audio/**` (write), `libs/asr_adapter/**` (write),
  `libs/audio_pipeline/**` (write), `libs/common/**` (write),
  `libs/observability/**` (write),
  `reports/robust_asr/lora/lora_smoke_report.md` (P3.2-owned;
  EXPLICITLY REMOVED from P3.1 writes).
  `mandatory_no_touch`: all Section 2.2 patterns; LoRA adapter binary
  checkpoints (`*.pt`/`*.pth`/`*.bin`/`*.safetensors`) remain
  no-touch and never committed; the adapter subtree under
  `artifacts/robust_asr/lora_smoke/` is gitignored so only small
  JSON/CSV/PNG/MD metadata land in git.
  `external_resources`: Slurm submit via `slurm/tools/on_submit.sh`
  (GPU); robust_asr Apptainer image at
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif`
  (exec `--nv`); LibriSpeech source audio under
  `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/**` and
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**`
  (read-only); degradation_v1 audio under
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degradation_v1/**`
  (read-only at P3.1);
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/whisper_models/whisper_base_en_ct2_int8/`
  (read-only for export smoke fixture); HF base.en source weights
  cache (read-only) for LoRA adapter injection.
- New `reports/robust_asr/touch_policy.md` sha256 =
  `32ad92b1772ba180c7d1b96171c68e08ff81af694cdc2a93343c093ea27eeffc`;
  `artifacts.touch_policy.last_amended_by=P3.1_scope_change`.
- `configs/robust_asr/reuse_policy_v1.yaml` UNCHANGED — every P3.1 write
  path already sits under a robust_asr-owned reuse-policy row that lists
  P3.1 in `allowed_tasks` (`scripts/robust_asr/**`,
  `artifacts/robust_asr/**`, `reports/robust_asr/**`,
  `tests/robust_asr/**`, `slurm/jobs/**` with `p<task>_*.sh` basename
  rule, `docs/progress/robust_asr_*`); external host paths
  (`…/runtime/robust_asr_py311_cuda12.sif`, `…/datasets/**`,
  `…/datasets/degradation_v1/**`, `…/runtime/whisper_models/**`) also
  already list P3.1 in `allowed_tasks`.
- `latest_approval_packet`=CHANGE_SCOPE(P3.1) on
  `ca98443d380f675eb45666af19d3686f3fbfa54f` (next P3.1);
  `prior_approval_packet_p2_phase`=PHASE_APPROVE(P2) on `8c37ece`
  (next P3.1); `prior_approval_packet`=APPROVE_EXECUTION(P2.2) on
  `8c37ece` (next P2_GATE);
  `prior_approval_packet_p2_2_plan`=APPROVE_PLAN(P2.2) on `d78678a`
  (next P2_GATE).
- `state_transport.last_accepted_report_commit` STAYS
  `ca98443d380f675eb45666af19d3686f3fbfa54f` (CHANGE_SCOPE does not
  advance). `state_transport.expected_next_task=P3.1` held.
- Held: `current_phase=P3`, `current_task=P3.1`,
  `last_completed_task=P2.2`, `markers=[BLOCKED_OOD_PUBLIC]`
  (non-blocking), `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false`,
  `claims_enabled.cloud_tradeoff=true`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`,
  `phase_summary={P0:PASS, P1:PASS, P2:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE,
  P2:PHASE_APPROVE}`.
- Verification: `python scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE` (exit 0).
- P3.1 implementation NOT executed: no `train_lora_smoke.py`, no
  `evaluate_lora_smoke.py`, no `smoke_export_lora_ct2.py`, no
  `slurm/jobs/p3_1_lora_smoke.sh`, no `tests/robust_asr/test_lora_smoke.py`,
  no `artifacts/robust_asr/lora_smoke/*` outputs, no
  `reports/robust_asr/lora/lora_smoke_*` outputs, no
  `P3.1_lora_smoke.md` task report, no Slurm submission, no Apptainer,
  no GPU, no LoRA training, no LoRA inference, no LoRA export, no
  HuggingFace download, no model bytes written. Awaiting orchestrator
  `APPROVE_PLAN(P3.1)` before implementation.

## P2 PHASE_APPROVE recorded

- ORCHESTRATOR_DECISION: scope=phase task=null phase=P2
  decision=PHASE_APPROVE
  accepted_report_commit=`8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd`
  next_expected_task=P3.1.
- Rationale: P2 phase gate PASS. `tasks.P2.1` and `tasks.P2.2` are
  PASS; baseline parquet
  (`artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
  53,230 rows; sha256
  `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6`),
  baseline report (`reports/robust_asr/baseline_whisper_base.md`,
  sha256 `6e5e2f04…ca55e1`), and LoRA smoke config
  (`configs/robust_asr/lora_smoke.yaml`, sha256
  `4d7ae448…e00cff`, 600 + 200 audio_ids referencing valid manifest
  rows) are present and validated. Sentinels recorded across
  P2.1/P2.2: `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`,
  `OK_LORA_SMOKE_CONFIG_PARSE`, `OK_LORA_SMOKE_MANIFEST_REFS`,
  `OK_LORA_SMOKE_HPARAMS`, `OK_LORA_SMOKE_DECODE_DEFAULTS`,
  `OK_LORA_SMOKE_TIMEOUTS`, `OK_REPORT_SHAPE`. No blocking markers
  active. `BLOCKED_OOD_PUBLIC` remains active and non-blocking with
  `claims_enabled.ood_real=false`.
- Tracker mutations: `current_phase` advanced `P2 -> P3`;
  `current_task` advanced `P2_GATE -> P3.1`;
  `last_completed_task=P2.2` held;
  `phase_summary.P2=PASS`;
  `orchestrator_approvals.P2=PHASE_APPROVE`;
  `markers=[BLOCKED_OOD_PUBLIC]` held;
  `blocked=false` held; `claims_enabled.ood_real=false` held;
  `state_transport.last_accepted_report_commit` STAYS
  `8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd` (PHASE_APPROVE accepted
  on the same commit as the closing APPROVE_EXECUTION(P2.2); not
  advanced);
  `state_transport.expected_next_task=P3.1`.
  `latest_approval_packet=PHASE_APPROVE(P2)` on `8c37ece`;
  `prior_approval_packet=APPROVE_EXECUTION(P2.2)` on `8c37ece`;
  `prior_approval_packet_p2_2_plan=APPROVE_PLAN(P2.2)` on `d78678a`.
- P3.1 not started; awaiting orchestrator `APPROVE_PLAN(P3.1)` before
  implementation (P3.1 requires Slurm GPU submission, Apptainer `--nv`,
  the robust_asr SIF, and `configs/robust_asr/lora_smoke.yaml`).
- No code, no test, no Slurm submission for this update. Only tracker
  files modified.

## P2.2 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P2.2 phase=P2
  decision=APPROVE_EXECUTION
  accepted_report_commit=`8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd`
  next_expected_task=P2_GATE.
- Rationale: P2.2 passed. `configs/robust_asr/lora_smoke.yaml` was
  created; `smoke_split` and `smoke_eval_split` reference valid
  manifest rows (600 / 200 audio_ids); required hyperparameters,
  Section 3 decode defaults, and timeouts are present; `OK_REPORT_SHAPE`
  passed; 85/85 non-regression tests passed. `BLOCKED_OOD_PUBLIC`
  remains active and non-blocking.
- Tracker mutations: `current_phase=P2` held;
  `current_task` advanced `P2.2 -> P2_GATE`;
  `last_completed_task` advanced `P2.1 -> P2.2`;
  `tasks.P2.2.status=PASS` held;
  `tasks.P2.2.commit=8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd`;
  `markers=[BLOCKED_OOD_PUBLIC]` held;
  `blocked=false` held; `claims_enabled.ood_real=false` held;
  `state_transport.last_accepted_report_commit` advanced
  `83dd911 -> 8c37ece`;
  `state_transport.expected_next_task=P2_GATE`.
  `latest_approval_packet=APPROVE_EXECUTION(P2.2)` on `8c37ece`;
  `prior_approval_packet=APPROVE_PLAN(P2.2)` on `d78678a`;
  `prior_approval_packet_p2_2_scope_exec=APPROVE_EXECUTION(P2.2-scope-change)`
  on `d78678a`;
  `prior_approval_packet_p2_2_change_scope=CHANGE_SCOPE(P2.2)`
  on `821893c`.
- P2 gate predicate (Section 8 P2) fully satisfiable: `tasks.P2.1=PASS`,
  `tasks.P2.2=PASS`, baseline eval table + report exist,
  `configs/robust_asr/lora_smoke.yaml` exists with valid manifest
  references, no MISSING_EVIDENCE / PLAN_CONFLICT. P2_GATE not started;
  awaiting orchestrator `PHASE_APPROVE(P2)` before P3.1 may begin.
- No code, no test, no Slurm submission for this update. Only tracker
  files modified.

## P2.2 PASS

- LoRA smoke split config built and committed.
  `configs/robust_asr/lora_smoke.yaml` written
  (43,252 bytes; sha256
  `4d7ae4489587937e841df9ca172e9b9933e4647ddbe06edf3b00adc713e00cff`).
  Top-level keys: `version`, `seed`, `manifests`, `smoke_split`,
  `smoke_eval_split`, `hyperparameters`, `eval_decode_defaults`,
  `timeouts`.
- Approvals accepted: `APPROVE_EXECUTION(P2.2-scope-change)` on
  `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2.2);
  `APPROVE_PLAN(P2.2)` on
  `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2_GATE).
- Sampling: deterministic stratified-by-speaker, RNG-free. For each
  manifest the rule is: group rows by `speaker_id`, sort speakers by
  integer ID, sort each speaker's utterances by `audio_id`
  lexicographically, take the first `per_speaker` utterances per
  speaker. Seed `42` is the canonical training/eval seed (P3.1-binding);
  the smoke sampler itself is RNG-free.
- `smoke_split` (from `librispeech_lora_train.parquet`, source sha256
  `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a`,
  22,507 rows / 200 speakers): **600 audio_ids across 200 speakers
  (3 utt/speaker)**; total duration 7,647.93 s (2.1244 h).
- `smoke_eval_split` (from `librispeech_validation.parquet`, source
  sha256
  `977a6f01d72171e9cfb9ce8aee71d4961a99d66397784225c71efbcf1d53733f`,
  2,703 rows / 40 speakers): **200 audio_ids across 40 speakers
  (5 utt/speaker)**; total duration 1,730.07 s (0.4806 h).
- Hyperparameters: `steps_max=200`, `learning_rate=1.0e-4`,
  `batch_size=8`, `lora_rank=8`, `lora_alpha=16`, `lora_dropout=0.05`,
  `target_modules=[q_proj, k_proj, v_proj, out_proj]`, `seed=42`,
  `warmup_steps=20`, `optimizer=adamw`, `weight_decay=0.0`,
  `gradient_accumulation_steps=1`, `fp16=true`.
- Section 3 eval decode defaults exact: `task=transcribe`,
  `language=en`, `condition_on_previous_text=false`,
  `without_timestamps=true`, `beam_size=1`, `temperature=0.0`.
- Timeouts: `training_timeout_seconds=14400` (4 h),
  `eval_timeout_seconds=1800` (30 min).
- Verifications: `OK_LORA_SMOKE_CONFIG_PARSE`,
  `OK_LORA_SMOKE_MANIFEST_REFS`, `OK_LORA_SMOKE_HPARAMS`,
  `OK_LORA_SMOKE_DECODE_DEFAULTS`, `OK_LORA_SMOKE_TIMEOUTS`,
  `OK_REPORT_SHAPE` (all exit 0). `python3 -m pytest -q
  tests/robust_asr/` → **85/85 PASS in 2.94 s** (non-regression).
- Tracker mutations: `tasks.P2.2.status=PASS`,
  `tasks.P2.2.next_task=P2_GATE`, `tasks.P2.2.marker=null`,
  `tasks.P2.2.artifacts_added.{lora_smoke_config, p2_2_task_report}`
  populated. `current_phase=P2` held; `current_task=P2.2` held until
  orchestrator `APPROVE_EXECUTION(P2.2)` advances to `P2_GATE`;
  `last_completed_task=P2.1` held. `markers=[BLOCKED_OOD_PUBLIC]`
  held (non-blocking; `claims_enabled.ood_real=false` held).
  `blocked=false`; `blocker=null`.
  `state_transport.last_accepted_report_commit` STAYS
  `83dd911bc124a9f1dd53bab17cc4812dbf0cf932` (the P2.2 commit is NOT
  accepted per orchestrator instruction).
  `state_transport.expected_next_task=P2_GATE`.
  `latest_approval_packet=APPROVE_PLAN(P2.2)` on `d78678a` (next
  P2_GATE); `prior_approval_packet=APPROVE_EXECUTION(P2.2-scope-change)`
  on `d78678a` (next P2.2);
  `prior_approval_packet_p2_2_change_scope=CHANGE_SCOPE(P2.2)` on
  `821893c` (next P2.2); `prior_approval_packet_p2_1_exec=
  APPROVE_EXECUTION(P2.1)` on `83dd911` (next P2.2).
- P2 gate predicate (Section 8 P2) now fully satisfiable: `tasks.P2.1
  =PASS`, `tasks.P2.2=PASS`, baseline eval table + report exist,
  `configs/robust_asr/lora_smoke.yaml` exists with valid manifest
  references, no MISSING_EVIDENCE/PLAN_CONFLICT. Awaiting orchestrator
  `APPROVE_EXECUTION(P2.2)` and `PHASE_APPROVE(P2)` before P3.1.
- No Slurm submission, no Apptainer exec, no GPU, no external API,
  no model weights, no audio I/O, no `pip install`.

## P2.2 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P2.2 phase=P2
  decision=CHANGE_SCOPE
  accepted_report_commit=`821893c69eb3e651a94e6bddde49ca5a22be7354`
  next_expected_task=P2.2.
  required_fix="Rewrite stale touch_policy P2.2 row to authorize the
  LoRA smoke config task."
- Rationale: P2.2 requires `configs/robust_asr/lora_smoke.yaml` and
  `reports/robust_asr/task_reports/P2.2_lora_smoke_config.md`, but the
  prior touch_policy P2.2 row still referred to an old baseline-gate
  task. Row rewritten (additive) to authorize the v3.4.7 P2.2 LoRA
  smoke split config deliverables and the read paths needed for
  manifest-membership validation.
- `reports/robust_asr/touch_policy.md` P2.2 row REWRITTEN.
  allowed_write_paths: `configs/robust_asr/lora_smoke.yaml`,
  `reports/robust_asr/task_reports/P2.2_lora_smoke_config.md`,
  `reports/robust_asr/touch_policy.md` (scope-change rows),
  `docs/progress/robust_asr_progress.yaml`,
  `docs/progress/robust_asr_progress.md`,
  `docs/progress/robust_asr_state_capsule.md`.
  allowed_read_paths: plan files, `configs/robust_asr/data_v1.yaml`,
  `configs/robust_asr/reuse_policy_v1.yaml`,
  `libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/versions.py`,
  `artifacts/robust_asr/manifests/librispeech_lora_train.parquet`,
  `artifacts/robust_asr/manifests/librispeech_validation.parquet`,
  `reports/robust_asr/manifest_summary.md`,
  `reports/robust_asr/baseline_whisper_base.md`.
  default_no_touch: legacy trackers, services/**, infra/**,
  configs/training/**, scripts/training/**, libs/audio/** (write),
  libs/asr_adapter/** (write), libs/common/** (write),
  scripts/robust_asr/** (write), slurm/**.
  mandatory_no_touch: all Section 2.2 patterns; `*.wav`/`*.flac`/`*.mp3`
  under repo root. external_resources: none (no Slurm, no Apptainer,
  no GPU, no external API).
- `configs/robust_asr/reuse_policy_v1.yaml` UNCHANGED. P2.2 is already
  listed in `allowed_tasks` for `configs/robust_asr/**` (line 80) and
  for the `artifacts/robust_asr/**` manifest rows (lines 33, 45, 57,
  69) used by P2.2 reads; all P2.2 paths are robust_asr-owned.
- `latest_approval_packet`=CHANGE_SCOPE(P2.2) on
  `821893c69eb3e651a94e6bddde49ca5a22be7354` (next P2.2);
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1) on `83dd911` (next
  P2.2); `prior_approval_packet_p2_1_rerun_plan`=APPROVE_PLAN(P2.1-rerun)
  on `28dddae` (next P2.2).
- `state_transport.last_accepted_report_commit` STAYS
  `83dd911bc124a9f1dd53bab17cc4812dbf0cf932` (CHANGE_SCOPE does not
  advance). `state_transport.expected_next_task=P2.2` held.
- Held: `current_phase=P2`, `current_task=P2.2`,
  `last_completed_task=P2.1`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `claims_enabled.ood_real=false`,
  `claims_enabled.cloud_tradeoff=true`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`,
  `phase_summary={P0:PASS, P1:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`.
- Verification: `validate_report_shape.py` -> `OK_REPORT_SHAPE` (exit
  0).
- P2.2 implementation NOT executed: no `configs/robust_asr/lora_smoke.yaml`,
  no `P2.2_lora_smoke_config.md`, no manifest-membership check run, no
  pytest run, no Slurm, no Apptainer, no GPU, no external API. Awaiting
  orchestrator `APPROVE_PLAN(P2.2)` before implementation.

## P2.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P2.1 phase=P2
  decision=APPROVE_EXECUTION
  accepted_report_commit=`83dd911bc124a9f1dd53bab17cc4812dbf0cf932`
  next_expected_task=P2.2.
- Rationale: P2.1 passed after model-build remediation and tracker fix.
  `whisper_base_ct2_int8` baseline produced 53,230 rows; sentinels
  `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`,
  `OK_REPORT_SHAPE` emitted; non-regression tests passed (85/85).
  MISSING_EVIDENCE cleared. BLOCKED_OOD_PUBLIC remains active and
  non-blocking; `claims_enabled.ood_real=false`.
- Tracker mutations: `current_phase=P2` held; `current_task=P2.2`;
  `last_completed_task=P2.1`; `tasks.P2.1.status=PASS` held;
  `tasks.P2.1.commit=83dd911…`; `markers=[BLOCKED_OOD_PUBLIC]` held;
  `blocked=false`; `claims_enabled.ood_real=false` held;
  `state_transport.last_accepted_report_commit` advanced
  `28dddae -> 83dd911`; `state_transport.expected_next_task=P2.2`.
  `latest_approval_packet=APPROVE_EXECUTION(P2.1)` on `83dd911`;
  `prior_approval_packet=APPROVE_PLAN(P2.1-rerun)` on `28dddae`;
  `prior_approval_packet_p2_1_model_build_exec=APPROVE_EXECUTION(P2.1-model-build)`
  on `28dddae`.
- P2.2 not started; awaiting orchestrator APPROVE_PLAN(P2.2) before
  implementation.

## Tracker fix — last_accepted_report_commit advanced 49b4bdc -> 28dddae

- The P2.1 PASS update recorded
  `state_transport.last_accepted_report_commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db`
  (PHASE_APPROVE(P1) acceptance), but
  `APPROVE_EXECUTION(P2.1-model-build)` had accepted commit
  `28dddae0c503208f3042bb5989e2bf3f5798ef56`, which should have
  advanced the accepted commit at P2.1-rerun acceptance time.
  `APPROVE_PLAN(P2.1-rerun)` accepts the same commit and does not
  further advance.
- Tracker corrected:
  `state_transport.last_accepted_report_commit` set to
  `28dddae0c503208f3042bb5989e2bf3f5798ef56`. No code, no test, no
  task-status change. P2.1 PASS state held.
- Held: `current_task=P2.1`, `last_completed_task=P1.4`,
  `current_phase=P2`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`,
  `tasks.P2.1.status=PASS`, `tasks.P2.1.next_task=P2.2`,
  `state_transport.expected_next_task=P2.1`,
  `latest_approval_packet`=APPROVE_PLAN(P2.1-rerun) on `28dddae`,
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1-model-build) on
  `28dddae`.

## P2.1 PASS — whisper_base_ct2_int8 baseline evaluation (53,230 rows; MISSING_EVIDENCE cleared)

- ORCHESTRATOR_DECISIONs recorded:
  - `APPROVE_EXECUTION(P2.1-model-build)` on
    `accepted_report_commit=28dddae0c503208f3042bb5989e2bf3f5798ef56`,
    `next_expected_task=P2.1`. CT2 INT8 model at
    `…/runtime/whisper_models/whisper_base_en_ct2_int8/` is the binding
    baseline backend.
  - `APPROVE_PLAN(P2.1-rerun)` on
    `accepted_report_commit=28dddae0c503208f3042bb5989e2bf3f5798ef56`,
    `next_expected_task=P2.2`. Rerun accepted on the model-build
    commit; `state_transport.last_accepted_report_commit` NOT advanced.
- Deliverables (sha256 in tracker yaml `artifacts.*` / `tasks.P2.1.artifacts_added.*`):
  - `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`
    (53,230 rows; 31 columns; 16,591,882 bytes; sha256
    `0dc98736…f4a6`).
  - `reports/robust_asr/baseline_whisper_base.md`
    (sha256 `6e5e2f04…55e1`).
  - `scripts/robust_asr/run_backend_eval.py` (edited; sha256
    `36ba31bb…55e1`; prior `56ab650f…fa209d`). Added
    `eval_audio_id = source_audio_id + '::' + degradation_id` and a
    transcription cache keyed on `audio_sha256` so each
    `(source × condition_family × tier)` row is a distinct eval-table
    row and identical audio decodes once.
- Slurm execution (final PASS run):
  - Wrapper: `./slurm/tools/on_submit.sh sbatch /…/slurm/jobs/p2_1_baseline.sh`.
  - Job: `2129900`, name `asr_p2_1_baseline`, partition `2080ti`, host
    `aisurrey04`, GPU job.
  - State / ExitCode: `COMPLETED 0:0` in 2 h 40 m 00 s. MaxRSS
    811,860 KiB. Container sha256 `8db5364c…ce8713`.
  - 53,230 successful inferences; 0 row failures.
  - §5.8 budget: 10800 s (3 h); actual 9600 s (11.1 % margin).
- Per-family metrics (mean over successful rows; n=10,646 per family =
  2 tiers × 5323):
  - clean: WER 0.0709, WA 0.9367
  - muffled_lowpass: WER 0.1072, WA 0.9027
  - cafe_noise: WER 0.1241, WA 0.8784
  - far_field_room: WER 0.1410, WA 0.8623
  - phone_band: WER 0.6058, WA 0.6034
- Backend / model provenance:
  `backend_version=faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8`;
  model.bin sha256 `4ed9e9b5…db33f`; source openai-whisper base.en.pt
  sha256 `25a8566e…ad` (canonical); ctranslate2 4.7.1; quantization
  int8; local_only=true; third_party_provider=null; cost_usd=null;
  normalization_version=normalization_v1.
- Verifications:
  - `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE` all emitted.
  - `validate_eval_table.py` → `rows=53230 unique_pk=53230
    unique_audio_id=53230`, `OK_EVAL_TABLE`, exit 0.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `pytest -q test_runtime_contract_skeleton.py test_eval_schema.py
    test_normalization_metrics.py test_leakage.py test_degradation_v1.py`
    → 85/85 PASS in 6.88 s.
- Bug-fix history:
  - Attempt 1 (Slurm `2129649`): HALTED `13:0` in 14 s,
    `MISSING_EVIDENCE` — CT2 weights absent. Resolved by
    CHANGE_SCOPE(P2.1-model) + P2.1-model-build (`2129651`).
  - Attempt 2 (Slurm `2129652`): COMPLETED `0:0` in 18 m 32 s; all
    sentinels emitted but only 5,323 rows (clean tier only) due to
    PK collapse on source-only audio_id. Detected post-run; no PASS
    declared on under-counted parquet.
  - Attempt 3 (Slurm `2129900`, this PASS): COMPLETED `0:0` in
    2 h 40 m 00 s; 53,230 rows; full coverage.
- Tracker mutations: `tasks.P2.1.status=PASS`;
  `tasks.P2.1.next_task=P2.2`; `tasks.P2.1.marker=null`;
  `tasks.P2.1.slurm.job_id=2129900`, `state=COMPLETED`, `exit_code=0:0`,
  `sentinel=OK_BACKEND_EVAL`; history block records attempts 1 and 2.
  `markers=[BLOCKED_OOD_PUBLIC]` (MISSING_EVIDENCE cleared;
  BLOCKED_OOD_PUBLIC held — non-blocking, `claims_enabled.ood_real=false`).
  `blocked=false`; `blocker=null`. `current_task=P2.1` held (orchestrator
  finalizes via APPROVE_EXECUTION before P2.2 may start);
  `last_completed_task=P1.4` held. `state_transport.last_accepted_report_commit`
  STAYS `49b4bdc…` per orchestrator instruction;
  `state_transport.expected_next_task=P2.1` held.
  `latest_approval_packet`=APPROVE_PLAN(P2.1-rerun) on `28dddae`;
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1-model-build) on
  `28dddae`. `artifacts.baseline_table.{sha256,rows}` and
  `artifacts.baseline_report.sha256` populated. New
  `tasks.P2.1.artifacts_added.{eval_table, baseline_report_full}` entries.

## P2.1-model-build PASS — CT2 INT8 weights produced (parent P2.1 still HALTED)

- ORCHESTRATOR_DECISIONs recorded:
  - `APPROVE_EXECUTION(P2.1-model-scope-change)` on
    `accepted_report_commit=7253b878b61c4416f2e1164257e802ca7627a73b`,
    `next_expected_task=P2.1`. Two new reuse_policy override rows
    (`…/cache/whisper/base.en.pt` read-only sha256-pinned;
    `…/runtime/whisper_models/**` read_write) and the touch_policy P2.1
    row extension are now binding.
  - `APPROVE_PLAN(P2.1-model-build)` on
    `accepted_report_commit=7253b878b61c4416f2e1164257e802ca7627a73b`,
    `next_expected_task=P2.1`. Build accepted on the model-scope-change
    commit; `state_transport.last_accepted_report_commit` is NOT
    advanced.
- Implementation deliverables:
  - `scripts/robust_asr/build_whisper_base_ct2_int8.py`
    (sha256 `79f29b5c…835e`). Source-sha256 verification, three
    conversion strategies in order, idempotent provenance write.
  - `slurm/jobs/p2_1_build_ct2_model.sh`
    (sha256 `e575f874…9e1e`). Apptainer SIF exec, env-isolated,
    CPU-only, `--time=00:30:00`, `--mem=8G`, `--cpus-per-task=2`.
  - `reports/robust_asr/whisper_base_ct2_int8_build.md`.
- Slurm job 2129651 COMPLETED 0:0 in 32 s on aisurrey04 (partition
  `2080ti`); MaxRSS 836,324 KiB; container sha256 `8db5364c…ce8713`
  matches tracker; sentinel `OK_CT2_BUILD` printed.
- Conversion outcome: strategy 1 (`OpenAIWhisperConverter`) — class
  removed from ctranslate2 4.x; strategy 2 (`ct2-transformers-converter`
  CLI) — failed with `TypeError: WhisperForConditionalGeneration.__init__()
  got an unexpected keyword argument 'dtype'` (transformers/ctranslate2
  API mismatch); strategy 3 (`TransformersConverter` Python API with
  patched `load_model` that strips `dtype`/`torch_dtype` before
  `from_pretrained`) — PASS.
- Model directory:
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/whisper_models/whisper_base_en_ct2_int8/`
  - `model.bin` (76,396,161 bytes; sha256 `4ed9e9b5…db33f`).
  - 11 ancillary files (config, tokenizer, vocab, normalizer, generation
    config, etc.); per-file sha256s in `provenance.json`.
  - `provenance.json` records: source path + sha256 +
    `source_canonical_sha256=25a8566e…ad`,
    `ctranslate2_version=4.7.1`, `quantization=int8`, three conversion
    attempts, `container_sha256`, `slurm_job_id=2129651`, host, UTC
    timestamp.
- Source: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache/whisper/base.en.pt`,
  sha256 `25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead`,
  matches the canonical openai-whisper `_MODELS["base.en"]` hash.
  HF mirror `openai/whisper-base.en` was used for model-class load only;
  conversion outputs derive from those (canonically identical) bytes.
- Prior attempt: Slurm job `2129650` FAILED `1:0` in 31 s
  (strategies 1+2; strategy 3 not yet present at that commit). No
  partial output retained because the build script wipes the output
  directory between strategies and writes provenance.json only on
  full success.
- Verifications: `OK_CT2_BUILD` emitted; model.bin present; 12 output
  files written; provenance.json records all required fields. P2.1
  baseline rerun NOT executed; non-regression checks not re-run on this
  build (no robust_asr code under test changed).
- Tracker mutations: new `tasks.P2.1.subtasks.P2.1-model-build` block
  with status PASS and Slurm metadata; new
  `tasks.P2.1.artifacts_added.{build_whisper_base_ct2_int8_script,
  p2_1_build_ct2_model_slurm_job, whisper_base_ct2_int8_build_report,
  whisper_base_ct2_int8_model}` entries; `latest_approval_packet`
  replaced with APPROVE_PLAN(P2.1-model-build) and
  APPROVE_EXECUTION(P2.1-model-scope-change) shifted to
  `prior_approval_packet`. **`tasks.P2.1.status` stays `HALTED`** (the
  build does not by itself satisfy the parent task's PASS criteria).
  `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` held; `blocked=true`
  held; `current_task=P2.1` held; `last_completed_task=P1.4` held;
  `state_transport.last_accepted_report_commit=49b4bdc…` held.

## P2.1 model-remediation scope change (no conversion; CT2 source/output paths authorized)

- ORCHESTRATOR_DECISION: scope=scope_change task=P2.1-model phase=P2
  decision=CHANGE_SCOPE accepted_report_commit=`268b8e9d0f999bce905a4f2f3652b821ff08a0c3`
  next_expected_task=P2.1.
- Required fix: Authorize read-only use of the local OpenAI Whisper
  `base.en.pt` checkpoint and read-write robust_asr CT2 INT8 model
  output path.
- `configs/robust_asr/reuse_policy_v1.yaml` amended with two new override
  rows under the `…/cache/**` no_touch and `…/runtime/**` data_root blocks:
  - `/mnt/.../cache/whisper/base.en.pt` — `class=data_root`,
    `permitted_use=read_only`, `allowed_tasks=[P2.1]`,
    `validator=sha256==25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead`,
    `checksum_required=true`, `large_artifact=true`,
    `commit_allowed=false`. Cache root retains its no_touch posture for
    every other path.
  - `/mnt/.../runtime/whisper_models/**` — `class=model_root`,
    `permitted_use=read_write`,
    `allowed_tasks=[P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1]`,
    `validator=sha256_recorded_in_provenance_json`,
    `checksum_required=true`, `large_artifact=true`,
    `commit_allowed=false`. P2.1 writes
    `whisper_base_en_ct2_int8/{model.bin,config.json,tokenizer*,vocabulary*,provenance.json}`;
    downstream tasks read the same root.
  - New sha256: `9766167cccd3d246a31adb488d89dcc6950b35c00e0eb5959b523c4c5fa8811b`,
    `last_amended_by=P2.1_model_scope_change`.
- `reports/robust_asr/touch_policy.md` P2.1 row extended (additive) with:
  - allowed_write_paths: `scripts/robust_asr/build_whisper_base_ct2_int8.py`,
    `slurm/jobs/p2_1_build_ct2_model.sh`,
    `reports/robust_asr/whisper_base_ct2_int8_build.md`.
  - external_paths_requiring_approval: read-only access to
    `/mnt/.../cache/whisper/base.en.pt` (sha256-pinned 25a8566e…ad);
    read_write access to `/mnt/.../runtime/whisper_models/**`.
  - New sha256: `e51dc99337cbd22e5f7f359f5ae154e79351b50d58b31d4259242a764dc03db3`,
    `last_amended_by=P2.1_model_scope_change`.
- `configs/robust_asr/eval_manifests_v1.yaml` updated to put the new
  robust_asr-controlled path
  `/mnt/.../runtime/whisper_models/whisper_base_en_ct2_int8` first in
  `backend_endpoints.whisper_base_ct2_int8.candidate_local_paths`; the
  prior four paths are kept as fallbacks. New sha256:
  `1e371f369b7585099aa3eaaf24202371070eff61d6b7600ccb1158e1e9859130`.
- Tracker mutations: `latest_approval_packet` replaced with the
  CHANGE_SCOPE(P2.1-model) packet (prior APPROVE_PLAN(P2.1) shifted to
  `prior_approval_packet`; APPROVE_EXECUTION(P2.1-scope-change) shifted
  to `prior_approval_packet_p2_1_scope_exec`);
  `artifacts.reuse_policy_config.sha256` and
  `artifacts.touch_policy.sha256` updated; both `last_amended_by` set to
  `P2.1_model_scope_change`. `artifacts_added.eval_manifests_v1.sha256`
  updated; `last_amended_by=P2.1_model_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS `49b4bdc…`
  (PHASE_APPROVE(P1) acceptance; CHANGE_SCOPE does not advance).
  `state_transport.expected_next_task` STAYS `P2.1`.
- Held: `current_phase=P2`, `current_task=P2.1` (still HALTED),
  `last_completed_task=P1.4`,
  `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` (MISSING_EVIDENCE NOT
  cleared), `blocked=true`, `claims_enabled.ood_real=false`,
  `phase_summary={P0:PASS, P1:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`.
- Conversion NOT executed: no `build_whisper_base_ct2_int8.py`, no
  Slurm build job, no model bytes written under `runtime/whisper_models/`,
  no rerun of `slurm/jobs/p2_1_baseline.sh`, no Apptainer call, no GPU,
  no external API.
- Non-regression: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE`.

## P2.1 HALTED — MISSING_EVIDENCE (CT2 INT8 weights absent)

- ORCHESTRATOR_DECISIONs recorded by P2.1:
  - `APPROVE_EXECUTION(P2.1-scope-change)` on
    `accepted_report_commit=def84589316237a7e2239967ae93448ecacd63a2`,
    `next_expected_task=P2.1`. Scope-change rows from CHANGE_SCOPE(P2.1)
    (configs/robust_asr/** P2.1 allowed_tasks; rewritten touch_policy
    P2.1 row) are now binding.
  - `APPROVE_PLAN(P2.1)` on
    `accepted_report_commit=def84589316237a7e2239967ae93448ecacd63a2`,
    `next_expected_task=P2.2`. Implementation accepted on the
    scope-change commit; `state_transport.last_accepted_report_commit`
    is NOT advanced to the P2.1 implementation commit per orchestrator
    instruction.
- Implementation deliverables (sha256 in `tasks.P2.1.artifacts_added`):
  - `configs/robust_asr/eval_manifests_v1.yaml`
  - `scripts/robust_asr/run_backend_eval.py`
    (Section 4.2 contract; CT2 weight probe; clean MISSING_EVIDENCE halt)
  - `scripts/robust_asr/summarize_backend_eval.py`
    (Section 4.2 contract; per-family WER/WA aggregation)
  - `scripts/robust_asr/validate_eval_table.py`
    (Section 4.1 contract; Section 3 schema tests 1..7)
  - `slurm/jobs/p2_1_baseline.sh`
    (apptainer --nv; --gres=gpu:1; cpus=4; mem=24G; time=03:00:00;
    partition=2080ti; env-isolation matching P0.3-rerun-2 pattern)
  - `reports/robust_asr/task_reports/P2.1_baseline.md`
- Slurm job 2129649 FAILED 13:0 in 14 s on aisurrey04 (partition
  2080ti). Container sha256 `8db5364c…` matches tracker. Sentinel
  `MISSING_EVIDENCE` printed to stdout; the script exited 13 BEFORE
  attempting any model load, network access, or row evaluation.
- candidate_local_paths probed (none resolved):
  `${ASR_CACHE_ROOT}/whisper_ct2_int8_base_en`,
  `/mnt/.../scratch4weeks/.../runtime/whisper_models/Systran--faster-whisper-base.en`,
  `${HF_HOME}/hub/models--Systran--faster-whisper-base.en`,
  `${ASR_CACHE_ROOT}/huggingface/hub/models--Systran--faster-whisper-base.en`.
- On host: `…/cache/whisper/` holds only `base.en.pt` + `tiny.en.pt`
  (openai-whisper PyTorch checkpoints, not CT2 INT8); HF hub holds
  only `models--speechbrain--metricgan-plus-voicebank/`. The cache
  root is classified `no_touch` in `reuse_policy_v1.yaml`, so
  populating CT2 INT8 weights requires a CHANGE_SCOPE that names the
  destination host path and the provenance source.
- Verifications (host Python):
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `pytest -q tests/robust_asr/test_runtime_contract_skeleton.py
    test_eval_schema.py test_normalization_metrics.py test_leakage.py
    test_degradation_v1.py` → 85/85 PASS in 2.87 s (non-regression).
  - `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`: NOT
    EMITTED (intended HALT).
  - `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
    `reports/robust_asr/baseline_whisper_base.md`: NOT WRITTEN.
- Tracker mutations: `tasks.P2.1.status=HALTED`,
  `tasks.P2.1.marker=MISSING_EVIDENCE`,
  `tasks.P2.1.next_task=P2.1` (held); `markers` extended to
  `[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]`; `blocked=true`;
  `blocker` set; `current_task=P2.1` held; `last_completed_task=P1.4`
  held; `state_transport.last_accepted_report_commit` STAYS `49b4bdc`
  per orchestrator instruction; `state_transport.expected_next_task=P2.1`
  held. `latest_approval_packet`=APPROVE_PLAN(P2.1) on `def8458`;
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1-scope-change) on
  `def8458`.
- Unblock path: provide CT2 INT8 weights at one of the declared
  candidate paths (Systran/faster-whisper-base.en snapshot; converted
  openai-whisper base.en.pt via ct2-converters; or a vetted internal
  mirror) under a CHANGE_SCOPE packet that records the host path and
  provenance. After weights resolve, rerun `slurm/jobs/p2_1_baseline.sh`;
  no code change needed in `run_backend_eval.py`.

## P2.1 scope change (no P2.1 implementation; baseline eval paths authorized)

- ORCHESTRATOR_DECISION: scope=scope_change task=P2.1 phase=P2
  decision=CHANGE_SCOPE accepted_report_commit=`22201db1a11586151811f814b14219e099e1a1ed`
  next_expected_task=P2.1.
- Required fix: Authorize P2.1 eval config and backend-eval scripts;
  update stale touch_policy P2.1 row.
- `configs/robust_asr/reuse_policy_v1.yaml` amended:
  - `configs/robust_asr/**` row: P2.1 added to `allowed_tasks`
    (now `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.4, P2.1]`). Authorizes
    P2.1 to author `configs/robust_asr/eval_manifests_v1.yaml`.
  - New sha256: `678d86a37ae471448736b08a68a9b34802ad6599ea12b08f3a0a33041d2aab6f`,
    `last_amended_by=P2.1_scope_change`.
- `reports/robust_asr/touch_policy.md` P2.1 row REWRITTEN to authorize
  the v3.4.7 P2.1 deliverables: `configs/robust_asr/eval_manifests_v1.yaml`,
  `scripts/robust_asr/run_backend_eval.py`,
  `scripts/robust_asr/summarize_backend_eval.py`,
  `scripts/robust_asr/validate_eval_table.py`,
  `slurm/jobs/p2_1_baseline.sh`,
  `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
  `reports/robust_asr/baseline_whisper_base.md`,
  `reports/robust_asr/task_reports/P2.1_baseline.md`,
  scope-change rows on `reuse_policy_v1.yaml`/`touch_policy.md`,
  three live trackers. Reads include `configs/robust_asr/data_v1.yaml`,
  `configs/robust_asr/degradation_v1.yaml`, `libs/common/eval_schema.yaml`,
  `libs/common/normalization.py`, `libs/common/metrics.py`,
  `libs/common/versions.py`, `libs/audio/**`, `libs/asr_adapter/**`,
  `libs/audio_pipeline/**`, robust_asr public manifests, and
  degradation_v1 manifests. External: Slurm submit; Apptainer (exec)
  on the robust_asr SIF; LibriSpeech and degradation_v1 audio
  (read-only).
  New sha256: `1b38914f1e814619d202a610ba98ca1cc18d404b9d507f5084d5871b2721c0e3`,
  `last_amended_by=P2.1_scope_change`.
- Tracker mutations: `latest_approval_packet` replaced with the P2.1
  CHANGE_SCOPE packet (prior PHASE_APPROVE(P1) shifted to
  `prior_approval_packet`; APPROVE_EXECUTION(P1.4) shifted to
  `prior_approval_packet_p1_gate`); `artifacts.reuse_policy_config.sha256`
  and `artifacts.touch_policy.sha256` updated; both `last_amended_by`
  set to `P2.1_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS `49b4bdc…`
  (PHASE_APPROVE(P1) acceptance; CHANGE_SCOPE does not advance).
  `state_transport.expected_next_task` STAYS `P2.1`.
- Held: `current_phase=P2`, `current_task=P2.1`,
  `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `claims_enabled.ood_real=false`,
  `phase_summary={P0:PASS, P1:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`.
- P2.1 implementation NOT executed: no `eval_manifests_v1.yaml`, no
  `run_backend_eval.py`, no `summarize_backend_eval.py`, no
  `validate_eval_table.py`, no Slurm job, no eval table, no baseline
  report, no Slurm, no Apptainer, no GPU, no external API.
- Non-regression: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE`.

## P1 phase gate (PHASE_APPROVE)

- ORCHESTRATOR_DECISION: scope=phase phase=P1 decision=PHASE_APPROVE
  accepted_report_commit=`49b4bdc122b9b9768b380ab9bb9c28bec49455db`
  next_expected_task=P2.1.
- Rationale: P1 phase gate accepted as PASS_WITH_PREDICATE_NOTE.
  P1.1 and P1.3 are PARTIAL only because OOD-real is unavailable;
  `BLOCKED_OOD_PUBLIC` is active, non-blocking, and
  `claims_enabled.ood_real=false`. P1.2 and P1.4 are PASS. Required
  LibriSpeech manifests, eval schema, normalization, metrics, leakage
  tests, and degradation_v1 artifacts are present. No active blocking
  markers (no MISSING_EVIDENCE, no PLAN_CONFLICT).
- Tracker mutations: `phase_summary.P1=PASS`,
  `orchestrator_approvals.P1=PHASE_APPROVE`,
  `current_phase=P2`, `current_task=P2.1`,
  `last_completed_task=P1.4` (held),
  `state_transport.last_accepted_report_commit` STAYS `49b4bdc`
  (PHASE_APPROVE accepted on the P1.4 PASS implementation commit;
  not advanced),
  `state_transport.expected_next_task=P2.1`.
- Held: `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`,
  `claims_enabled.positive_lora=pending`,
  `claims_enabled.positive_system=pending`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`.

## P1.4 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P1.4 phase=P1
  decision=APPROVE_EXECUTION
  accepted_report_commit=`49b4bdc122b9b9768b380ab9bb9c28bec49455db`
  next_expected_task=P1_GATE.
- Rationale: P1.4 passed. `OK_DEGRADATION_V1` emitted, 0 BAD_OUTPUT,
  degradation_v1 manifests built for ID and OOD-param eval, scratch
  usage stayed under budget, tests and report-shape validation passed.
  `BLOCKED_OOD_PUBLIC` remains active and non-blocking.
- Tracker: `current_phase=P1`, `current_task=P1_GATE`,
  `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC]` held,
  `blocked=false` held, `claims_enabled.ood_real=false` held,
  `degradation_version=degradation_v1` held,
  `state_transport.last_accepted_report_commit` advanced
  `d230971 -> 49b4bdc`,
  `state_transport.expected_next_task=P1_GATE`,
  `tasks.P1.4.next_task=P1_GATE`,
  `tasks.P1.4.commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db`.
- P1 gate predicate (Section 8 P1) satisfiable: tasks[P1.1=PARTIAL accepted,
  P1.2=PASS, P1.4=PASS] and tasks[P1.3=PARTIAL accepted]. Awaiting orchestrator
  PHASE_APPROVE(P1) before P2.1 may begin.

## P1.4 PASS — degradation_v1 generators and manifests

- ORCHESTRATOR_DECISIONs: APPROVE_EXECUTION(P1.4-scope-change) and
  APPROVE_PLAN(P1.4), both on `accepted_report_commit=5c72769d1cdf6f7aa7e789a02c2f05aa69284341`.
  APPROVE_EXECUTION(P1.4-scope-change) sets `next_expected_task=P1.4`;
  APPROVE_PLAN(P1.4) sets `next_expected_task=P1_GATE`.
- Deliverables (sha256 in tracker yaml `artifacts.*`):
  - `libs/audio/degradations.py` — additive narrow patch: appended
    `sample_clean`, `sample_cafe_noise`, `sample_phone_band`,
    `sample_far_field_room`, `sample_muffled_lowpass` and a
    `SAMPLE_FUNCTIONS` registry. Existing `apply_degradation`,
    `DEGRADATION_FAMILIES`, `DEGRADATION_PARAMS`, and
    `DEGRADATION_VERSION` value `"degradation_v1"` preserved.
  - `configs/robust_asr/degradation_v1.yaml` — eval-only sources
    (`librispeech_validation`, `librispeech_locked_test`); per-family
    ID and OOD-param ranges (disjoint per family); master_seed=20260508;
    50 GB scratch budget recorded.
  - `scripts/robust_asr/build_degradation_v1.py` — §4.3 contract;
    emits `OK_DEGRADATION_V1`; per-family success/skip/BAD_OUTPUT counts;
    `INSUFFICIENT_SCRATCH` halt; idempotent resume per-row.
  - `slurm/jobs/p1_4_build_degradation_v1.sh` — Apptainer SIF exec;
    cpus=16 mem=16G time=06:00:00 partition=2080ti.
  - `tests/robust_asr/test_degradation_v1.py` — 24 tests covering
    metadata fields, RMS ≥ 1e-6, clipping_ratio < 0.5, source sha256
    match, determinism, ID/OOD parameter disjointness, phone_band
    bit_depth.
  - `artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet`
    (26 615 rows; sha256 `cf0f0bce…`).
  - `artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet`
    (26 615 rows; sha256 `30684dc4…`).
  - 10 per-family parquets (5 families × 2 tiers; 5 323 rows each;
    sha256s in `degradation_v1_build_summary.json`).
  - `artifacts/robust_asr/manifests/degradation_v1_build_summary.json`.
  - `reports/robust_asr/degradation_v1_summary.md`.
  - `reports/robust_asr/task_reports/P1.4_degradation_v1.md`.
- Source data: 5 323 LibriSpeech eval rows (validation 2 703 +
  locked_test 2 620). `lora_train` and `router_train` deliberately
  excluded — training-time degradation is owned by P3.1 / P4.1.
- Audio output: 42 584 `.wav` (8 wavs/source; clean is identity, no
  audio rewritten) under
  `/mnt/fast/nobackup/scratch4weeks/.../datasets/degradation_v1/<family>/<tier>/<audio_id>.wav`.
  Never committed.
- Verifications (Slurm + non-regression + report shape):
  - Slurm job `2129647` COMPLETED `0:0` in 1 min 3 s on aisurrey01
    (partition `2080ti`, MaxRSS 11 077 812 KiB). Sentinel
    `OK_DEGRADATION_V1` with per-family/tier counts `5323/0`.
  - `pytest -q tests/robust_asr/test_degradation_v1.py
    tests/robust_asr/test_eval_schema.py
    tests/robust_asr/test_normalization_metrics.py
    tests/robust_asr/test_leakage.py
    tests/robust_asr/test_runtime_contract_skeleton.py` →
    85/85 PASS in 2.59 s.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
- Section 5.8 budget: 50 GB scratch, 6 h/family wall-clock; actual
  10.297 GB scratch used and ~9 s/family/tier. Safety margin ≥ 4×.
- Section 9 P1.4 Decision rule 1 (BAD_OUTPUT > 1 % per family):
  NOT FIRED. 0 / 53 230 BAD_OUTPUT across all 5 families × 2 tiers.
- ID vs OOD-param disjointness verified (cafe_noise snr, far_field_room
  rt60 + mic_distance, muffled_lowpass lowpass + attenuation,
  phone_band bit_depth).
- Prior attempt: Slurm job `2129646` FAILED `1:0` in 10 s due to
  `pyarrow OverflowError: Python int too large to convert to C long`
  on uint64 seeds. Fixed by masking the per-row seed to 63 bits
  (`(1<<63)-1`) so it fits pyarrow `int64`. Determinism preserved
  (SHA-256-derived 63-bit unsigned space, 9.2e18 distinct seeds).
  No partial parquets were committed.
- Tracker mutations: `tasks.P1.4.status=PASS`,
  `tasks.P1.4.next_task=P1_GATE`, `tasks.P1.4.marker=BLOCKED_OOD_PUBLIC`;
  `degradation_version=degradation_v1`; `current_task=P1.4` held;
  `last_completed_task=P1.3` held;
  `markers=[BLOCKED_OOD_PUBLIC]` held; `blocked=false` held;
  `claims_enabled.ood_real=false` held;
  `state_transport.last_accepted_report_commit` STAYS
  `d230971e8995484449095ae914b58c47c4d43b94` per orchestrator
  instruction (not advanced to the P1.4 implementation commit);
  `state_transport.expected_next_task=P1.4` (held until orchestrator
  reviews the P1.4 Execution Report).
  `latest_approval_packet`=APPROVE_PLAN(P1.4) on `5c72769`;
  `prior_approval_packet`=APPROVE_EXECUTION(P1.4-scope-change) on `5c72769`.

## P1.4 scope change (no implementation; reuse_policy + touch_policy amended)

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.4 phase=P1
  decision=CHANGE_SCOPE
  accepted_report_commit=`d230971e8995484449095ae914b58c47c4d43b94`
  next_expected_task=P1.4.
- Required fix: Authorize additive P1.4 degradation_v1 implementation,
  Slurm job, runtime SIF exec, and scratch dataset writes.
- `configs/robust_asr/reuse_policy_v1.yaml` amended:
  - NEW override row for `libs/audio/degradations.py`
    (class=existing_runtime_code, permitted_use=append_functions_only,
    allowed_tasks=[P1.4], validator=tests/robust_asr/test_degradation_v1.py,
    checksum_required=true, commit_allowed=true). Authorizes the five
    Section 3 `sample_<family>` additions; preserves `apply_degradation`,
    `DEGRADATION_FAMILIES`, and the `DEGRADATION_VERSION` value.
  - `slurm/jobs/**` row: P1.4 added to `allowed_tasks`.
  - `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif`
    row: P1.4 added to `allowed_tasks` (exec_only).
  - `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**`
    row: P1.4 added to `allowed_tasks` (read_only for source LibriSpeech audio).
  - NEW override row for
    `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degradation_v1/**`
    (class=data_root, permitted_use=read_write, allowed_tasks=[P1.4, P2.1, P3.1,
    P4.1, P4.2, P4.3, P8.1], large_artifact, never committed). P1.4 audio outputs
    land here under Section 5.8 budget (max 50 GB scratch).
  - New sha256: `f0528f7d4d14638b3cfdc4ede17c25c347cd3b838e844399fdfaf36464d81757`,
    last_amended_by=`P1.4_scope_change`.
- `reports/robust_asr/touch_policy.md` P1.4 row REWRITTEN to authorize the
  v3.4.7 P1.4 deliverables (`libs/audio/degradations.py` append-only narrow
  patch, `configs/robust_asr/degradation_v1.yaml`,
  `scripts/robust_asr/build_degradation_v1.py`,
  `slurm/jobs/p1_4_build_degradation_v1.sh`,
  `tests/robust_asr/test_degradation_v1.py`,
  `artifacts/robust_asr/manifests/degradation_v1_*.parquet`,
  `reports/robust_asr/degradation_v1_summary.md`,
  `reports/robust_asr/task_reports/P1.4_degradation_v1.md`,
  scope-change rows on policy files, three live trackers). External resources:
  Slurm submit; Apptainer (exec) on the robust_asr SIF; LibriSpeech sources
  (read-only); degradation_v1 scratch subtree (read_write).
  New sha256: `ede82ac0889628c87eab523d9fbd238995f2b041272004a835931ca5fb501f66`,
  last_amended_by=`P1.4_scope_change`.
- Tracker mutations: `latest_approval_packet` replaced with the P1.4
  CHANGE_SCOPE packet (prior P1.3 APPROVE_EXECUTION shifted to
  `prior_approval_packet`; previous APPROVE_PLAN(P1.3) and
  APPROVE_EXECUTION(P1.3-scope-change) shifted to `prior_approval_packet_00`
  and `prior_approval_packet_001`); `artifacts.reuse_policy_config.sha256`
  and `artifacts.touch_policy.sha256` updated; both `last_amended_by` set
  to `P1.4_scope_change`.
  `state_transport.last_accepted_report_commit` advanced
  `b049f94 -> d230971` per the APPROVE_EXECUTION(P1.3) packet; CHANGE_SCOPE
  does not further advance.
- Held: `current_task=P1.4`, `last_completed_task=P1.3`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `phase_summary.P0=PASS`,
  `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.4 implementation NOT executed: no `degradations.py` patch, no
  `degradation_v1.yaml`, no `build_degradation_v1.py`, no Slurm job, no
  manifests, no test file, no pytest run, no Apptainer, no GPU, no external API.
- Non-regression: `validate_report_shape.py` against the canonical
  fixtures emitted `OK_REPORT_SHAPE`.

## P1.3 PARTIAL — public LibriSpeech manifests; OOD-real splits skipped

- ORCHESTRATOR_DECISIONs recorded by P1.3:
  - `APPROVE_EXECUTION(P1.3-scope-change)` on `accepted_report_commit=7579602`,
    `next_expected_task=P1.3`. Rewritten touch_policy P1.3 row authorizing
    `build_public_manifests.py`, `summarize_manifests.py`, manifest parquets,
    summary, and task report is now binding.
  - `APPROVE_PLAN(P1.3)` on `accepted_report_commit=7579602`,
    `next_expected_task=P1.4`.
- Deliverables (sha256 in tracker yaml `artifacts.*`):
  - `scripts/robust_asr/build_public_manifests.py` — reads `data_v1.yaml`,
    walks LibriSpeech subsets, hashes each `.flac`, probes duration with
    `soundfile.info`, writes one parquet per `<dataset>_<split>` with
    columns `{audio_id, source_dataset, source_subset, speaker_id,
    chapter_id, utterance_id, audio_path_or_uri, audio_sha256,
    duration_s, sample_rate, num_frames, split_label}`. Halts (exit 1)
    only when a required LibriSpeech split has no resolvable rows.
  - `scripts/robust_asr/summarize_manifests.py` — emits markdown summary
    with per-manifest row count, duration, distinct speaker count,
    parquet byte sha256, and OOD-real claim status.
  - `artifacts/robust_asr/manifests/librispeech_{lora_train,router_train,validation,locked_test}.parquet`
  - `reports/robust_asr/manifest_summary.md`
  - `reports/robust_asr/task_reports/P1.3_manifest_summary.md`.
- Manifest counts:
  - `librispeech_lora_train.parquet`: 22 507 rows, 200 spk, 286 505.07 s
    (79.5848 h), sha256 `7896175e…`.
  - `librispeech_router_train.parquet`: 6 032 rows, 51 spk, 75 622.10 s
    (21.0061 h), sha256 `c3d281ab…`.
  - `librispeech_validation.parquet`: 2 703 rows, 40 spk, 19 396.12 s
    (5.3878 h), sha256 `977a6f01…`.
  - `librispeech_locked_test.parquet`: 2 620 rows, 40 spk, 19 452.48 s
    (5.4035 h), sha256 `ad4f401e…`.
  - Totals: 33 862 rows, 331 distinct speakers, 400 975.77 s (111.3822 h).
  - Cross-check: lora_train + router_train = 28 539 = train-clean-100;
    validation = 2 703 = dev-clean; locked_test = 2 620 = test-clean.
- OOD-real / demo splits skipped (Decision rule 1 fired):
  - `ood_real_locked`: `SKIPPED_OOD_PUBLIC_DEFERRED`
    (`no_source_dataset_selected`).
  - `common_voice_demo_reserved`: `SKIPPED_OOD_PUBLIC_DEFERRED`
    (`root_absent_or_empty`; `present_on_host=false`,
    `declared_speakers=0`).
  - `marker=BLOCKED_OOD_PUBLIC` and `claims_enabled.ood_real=false`
    held; no fallback admitted in P1.3 (plan §1 rule 5).
- Verifications (host Python; no Slurm, no SIF, no GPU, no external API):
  - `build_public_manifests.py` → `OK_PUBLIC_MANIFESTS`, exit 0,
    wall-clock 10.151 s for 33 862 files (~7 GiB).
  - `summarize_manifests.py` → `OK_MANIFEST_SUMMARY`, exit 0.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `check_speaker_disjoint.py --splits lora_train router_train
    validation locked_test` → `OK_SPEAKER_DISJOINT` (non-trivial).
  - `pytest -q test_runtime_contract_skeleton.py test_eval_schema.py
    test_normalization_metrics.py test_leakage.py` → 61/61 PASS in 1.42 s.
- Tracker mutations: `tasks.P1.3.status=PARTIAL`,
  `tasks.P1.3.marker=BLOCKED_OOD_PUBLIC`, `tasks.P1.3.next_task=P1.4`,
  `current_task=P1.4`, `last_completed_task=P1.3`,
  `markers=[BLOCKED_OOD_PUBLIC]` held, `blocked=false` held,
  `claims_enabled.ood_real=false` held,
  `state_transport.last_accepted_report_commit` STAYS `b049f9494f9acf163d6b5799f1f6450eaeee36c5`
  (per orchestrator instruction; NOT advanced to the P1.3
  implementation commit), `state_transport.expected_next_task=P1.4`,
  `latest_approval_packet=APPROVE_PLAN(P1.3)` on `7579602`,
  `prior_approval_packet=APPROVE_EXECUTION(P1.3-scope-change)` on `7579602`.
  `artifacts.manifest_summary`, `artifacts.build_public_manifests_script`,
  `artifacts.summarize_manifests_script`, and a new
  `artifacts.public_manifests` block populated.

## P1.3 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.3 phase=P1
  decision=CHANGE_SCOPE accepted_report_commit=`b049f9494f9acf163d6b5799f1f6450eaeee36c5`
  next_expected_task=P1.3.
- Required fix: Amend touch_policy P1.3 row to authorize
  `build_public_manifests.py` and `summarize_manifests.py`.
- Rationale: P1.3 requires new manifest build and summary scripts under
  `scripts/robust_asr/**`, but the current touch_policy P1.3 row omits
  those write paths.
- `reports/robust_asr/touch_policy.md` P1.3 row rewritten to authorize:
  `scripts/robust_asr/build_public_manifests.py`,
  `scripts/robust_asr/summarize_manifests.py`,
  `artifacts/robust_asr/manifests/*.parquet`,
  `reports/robust_asr/manifest_summary.md`,
  `reports/robust_asr/task_reports/P1.3_manifest_summary.md`,
  `reports/robust_asr/touch_policy.md` (scope-change row),
  the three live trackers. Reads include `configs/robust_asr/data_v1.yaml`,
  `libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/versions.py`. External reads:
  `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/**` and
  `…/asr_enhancement_training/datasets/**` (read-only ls/stat/open).
- Tracker mutations: `latest_approval_packet` set to the P1.3
  CHANGE_SCOPE packet (prior `APPROVE_EXECUTION(P1.2)` shifted to
  `prior_approval_packet`; older P1.2 packets shifted to
  `prior_approval_packet_0a`/`prior_approval_packet_0b`).
  `artifacts.touch_policy.sha256` →
  `f0ec8dcbf4b3dd09cb76794150745e0f2ec5b6bd701d94c6a623f4dd8b21d4a5`,
  `last_amended_by=P1.3_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS
  `b049f9494f9acf163d6b5799f1f6450eaeee36c5`
  (P1.2 APPROVE_EXECUTION acceptance; CHANGE_SCOPE does not advance).
- Held: `current_task=P1.3`, `last_completed_task=P1.2`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `phase_summary.P0=PASS`,
  `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.3 implementation NOT executed: no `build_public_manifests.py`, no
  `summarize_manifests.py`, no parquet manifests, no manifest summary,
  no Slurm, no Apptainer, no GPU, no external API.
- Non-regression: `validate_report_shape.py` against canonical fixtures
  emitted `OK_REPORT_SHAPE`.

## Tracker fix — last_accepted_report_commit advanced 587b7483 -> 8185501

- The P1.2 PASS Execution Report recorded
  `state_transport.last_accepted_report_commit=587b7483…`,
  but `APPROVE_EXECUTION(P1.2-scope-change)` had accepted commit
  `8185501955f5bb5ecf44c926fcabdc8f27ae2af9`, which should have
  advanced the accepted commit at P1.2 commit time.
- Corrected: `state_transport.last_accepted_report_commit` set to
  `8185501955f5bb5ecf44c926fcabdc8f27ae2af9`. No code, no test, no
  task-status change. P1.2 PASS state held.
- Held: `current_task=P1.3`, `last_completed_task=P1.2`,
  `tasks.P1.2.status=PASS`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `claims_enabled.ood_real=false`,
  `state_transport.expected_next_task=P1.3`,
  `latest_approval_packet`=APPROVE_PLAN(P1.2) on `8185501…`,
  `prior_approval_packet`=APPROVE_EXECUTION(P1.2-scope-change) on
  `8185501…`.

## P1.2 PASS — eval schema, normalization, metrics, leakage tests

- ORCHESTRATOR_DECISIONs recorded by P1.2:
  - `APPROVE_EXECUTION(P1.2-scope-change)` on
    `accepted_report_commit=8185501955f5bb5ecf44c926fcabdc8f27ae2af9`,
    `next_expected_task=P1.2`. Scope-change rows in
    `configs/robust_asr/reuse_policy_v1.yaml` and the rewritten P1.2
    row in `reports/robust_asr/touch_policy.md` are now binding.
  - `APPROVE_PLAN(P1.2)` on
    `accepted_report_commit=8185501955f5bb5ecf44c926fcabdc8f27ae2af9`,
    `next_expected_task=P1.3`.
- Implementation deliverables (sha256 in tracker yaml `artifacts.*`):
  `libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/metrics.py`, `libs/common/versions.py` (NORMALIZATION_VERSION
  appended; existing constants preserved),
  `scripts/robust_asr/validate_eval_schema.py`,
  `tests/robust_asr/test_eval_schema.py`,
  `tests/robust_asr/test_normalization_metrics.py`,
  `tests/robust_asr/test_leakage.py`,
  `reports/robust_asr/task_reports/P1.2_eval_schema.md`.
- Verifications:
  - `python3 -m pytest -q tests/robust_asr/test_eval_schema.py
    tests/robust_asr/test_normalization_metrics.py
    tests/robust_asr/test_leakage.py` → **41/41 PASS in 0.21 s**.
  - `python3 scripts/robust_asr/validate_eval_schema.py --schema
    libs/common/eval_schema.yaml` → `OK_EVAL_SCHEMA`, exit 0.
  - `python3 scripts/robust_asr/validate_report_shape.py …` →
    `OK_REPORT_SHAPE`, exit 0 (non-regression).
  - `python3 -m pytest -q tests/robust_asr/test_runtime_contract_skeleton.py`
    → **20/20 PASS** (P0.4 non-regression).
- `NORMALIZATION_VERSION = "normalization_v1"` appended to
  `libs/common/versions.py`. Existing `METRICS_VERSION="metrics_v1"`,
  `DEGRADATION_VERSION="degradation_v1"`, `ENHANCER_VERSION=None`
  preserved. New `libs/common/metrics.py` is the canonical robust_asr
  metrics module (distinct from training-profile
  `libs/audio/metrics.py`, which remains unmodified).
- Plan-text inconsistency: Section 3 header reads "Columns (28):" but
  enumerates 31 column names. The 31 names are encoded verbatim in the
  schema YAML; the validator checks set equality with the Section 3
  list, not the header count. Reported as a plan-text inconsistency,
  not a P1.2 deviation.
- Leakage tests 4 and 5 honor `BLOCKED_OOD_PUBLIC` /
  `claims_enabled.ood_real=false`: empty Common Voice / OOD-real /
  demo-reserved splits are treated as trivially disjoint and a
  `SKIP_OOD_PUBLIC_DEFERRED` note is written under
  `reports/robust_asr/leakage/`.
- Tracker mutations: `tasks.P1.2.status=PASS`,
  `current_task=P1.3`, `last_completed_task=P1.2`,
  `markers=[BLOCKED_OOD_PUBLIC]` held, `blocked=false` held,
  `claims_enabled.ood_real=false` held,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1` held,
  `state_transport.last_accepted_report_commit` STAYS `587b7483…`
  (per orchestrator instruction; not advanced to the P1.2 commit),
  `state_transport.expected_next_task=P1.3`,
  `latest_approval_packet`=APPROVE_PLAN(P1.2) on `8185501…`,
  `prior_approval_packet`=APPROVE_EXECUTION(P1.2-scope-change) on
  `8185501…`.

## P1.2 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.2 phase=P1
  decision=CHANGE_SCOPE
  accepted_report_commit=`1ecbaa447e380d5ed3637e80b679bcc83ae77c17`
  next_expected_task=P1.2.
- Rationale: P1.2 requires `libs/common/eval_schema.yaml`,
  `libs/common/normalization.py`, `libs/common/metrics.py`, and
  `libs/common/versions.py` update, but the current reuse_policy only
  allows read-only access under `libs/common/**` except
  `libs/common/runtime_contract.py`.
- Required fix: Authorize P1.2 writes under `libs/common/**` and
  update the stale touch_policy P1.2 row from the old manifests scope
  to eval schema / normalization / metrics / leakage tests.
- `configs/robust_asr/reuse_policy_v1.yaml` amended with four new
  rows under the libs/common/** override block:
  - `libs/common/eval_schema.yaml`: class=robust_asr_owned_extension,
    permitted_use=read_write, allowed_tasks=[P1.2, P9.0],
    validator=`scripts/robust_asr/validate_eval_schema.py`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
  - `libs/common/normalization.py`: class=robust_asr_owned_extension,
    permitted_use=read_write,
    allowed_tasks=[P1.2, P2.1, P3.1, P4.2, P4.3, P5.1, P6.1, P7.3, P8.1, P9.0],
    validator=`tests/robust_asr/test_normalization_metrics.py`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
  - `libs/common/metrics.py`: class=robust_asr_owned_extension,
    permitted_use=read_write,
    allowed_tasks=[P1.2, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P6.1, P7.3, P8.1],
    validator=`tests/robust_asr/test_normalization_metrics.py`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
  - `libs/common/versions.py`: class=existing_runtime_code,
    permitted_use=append_constants_only, allowed_tasks=[P1.2],
    validator=`NORMALIZATION_VERSION_constant_present`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
- `reports/robust_asr/touch_policy.md` P1.2 row rewritten to
  authorize the v3.4.7 P1.2 write paths
  (`libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/metrics.py`, `libs/common/versions.py` (append-only),
  `scripts/robust_asr/validate_eval_schema.py`,
  `tests/robust_asr/test_eval_schema.py`,
  `tests/robust_asr/test_normalization_metrics.py`,
  `tests/robust_asr/test_leakage.py`,
  `reports/robust_asr/task_reports/P1.2_eval_schema.md`, scope-change
  rows on `reuse_policy_v1.yaml`/`touch_policy.md`, the three live
  trackers). Reads include `configs/robust_asr/data_v1.yaml`,
  `libs/audio/metrics.py`, `libs/common/runtime_contract.py`. No Slurm,
  no Apptainer, no GPU, no external API.
- Tracker mutations:
  - `latest_approval_packet` set to the P1.2 CHANGE_SCOPE packet
    (prior P1.1 APPROVE_EXECUTION shifted to `prior_approval_packet`;
    the older P1.1 APPROVE_PLAN shifted to `prior_approval_packet_1b`).
  - `artifacts.reuse_policy_config.sha256` →
    `c2999d597c1e35ecf1340e8dace4e3eaca0640a30fd2d802f1f26a34df853905`,
    `last_amended_by=P1.2_scope_change`.
  - `artifacts.touch_policy.sha256` →
    `f09f4006ff0a6acfd2b296a974bd7ea49ab7e6288a77440a5a06d6e779204c01`,
    `last_amended_by=P1.2_scope_change`.
  - `state_transport.last_accepted_report_commit` STAYS
    `587b7483a6d37a24e0cf31549d449427c4708234`
    (P1.1 APPROVE_EXECUTION acceptance).
  - `state_transport.expected_next_task` STAYS `P1.2`.
- Held: `current_task=P1.2`, `last_completed_task=P1.1`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`,
  `phase_summary.P0=PASS`, `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.2 implementation NOT executed: no `eval_schema.yaml`, no
  `normalization.py`, no `metrics.py`, no `versions.py` mutation, no
  validator script, no tests, no pytest run, no Slurm, no Apptainer,
  no GPU, no external API.
- Non-regression: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE`.

## P1.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P1.1 phase=P1 decision=APPROVE_EXECUTION
  accepted_report_commit=`587b7483a6d37a24e0cf31549d449427c4708234`
  next_expected_task=P1.2.
- Rationale: LibriSpeech inventory usable after operator restore;
  required splits non-empty and speaker-disjoint; OOD-real remains
  unavailable so PARTIAL with `BLOCKED_OOD_PUBLIC` and
  `claims_enabled.ood_real=false` is accepted.
- Tracker: `current_phase=P1`, `current_task=P1.2`,
  `last_completed_task=P1.1`, `markers=[BLOCKED_OOD_PUBLIC]` held,
  `blocked=false` held, `claims_enabled.ood_real=false` held,
  `state_transport.last_accepted_report_commit` advanced
  `3129c11e -> 587b7483`, `state_transport.expected_next_task=P1.2`.
- `tasks.P1.1.next_task` set to `P1.2`. P1.2 not started.

## P0 phase gate

- ORCHESTRATOR_DECISION: scope=phase phase=P0 decision=PHASE_APPROVE
  accepted_report_commit=`d0ba20c532477a94f359b55c03dc6c835529c1fa`
  next_expected_task=P1.1.
- Rationale: P0.0 through P0.5 PASS; required artifacts and sentinels
  present (OK_REPORT_SHAPE, BUILD_OK_8db5364c, OK_APPTAINER_INSPECT,
  OK_RUNTIME_SMOKE, OK_CONTRACT_SKELETON, OK_CARD_TEMPLATES); runtime
  smoke and contract skeleton passed; model/router card placeholder
  counts exceed minima; no blockers or active markers.
- Tracker: `phase_summary.P0=PASS`; `orchestrator_approvals.P0=PHASE_APPROVE`;
  `state_transport.last_accepted_report_commit` advanced
  `40406fc3` → `d0ba20c5`; `state_transport.expected_next_task=P1.1`.
- `current_task=P1.1`, `last_completed_task=P0.5`, `blocked=false`,
  `markers=[]` unchanged.

## Completed tasks

- P0.0 PASS: Pre-bootstrap inventory (read-only, no commit)
- P0.1 PASS: Branch created, profile installed, tracker initialized
- P0.2 PASS: Asset inventory, reuse policy, touch policy, validate_report_shape.py
- P0.3 PASS: Runtime smoke (Slurm + Apptainer + 11 imports). Closed via P0.3-rerun-2 (job 2129641) against new SIF (sha256 8db5364c...) with env-isolated apptainer exec. Sub-tasks: P0.3-rebuild PASS (image build), P0.3-rerun HALTED (user-site shadowing), P0.3-rerun-2 PASS (env-isolation cleared shadowing).
- P0.4 PASS: RP5 runtime contract skeleton — request/response fixtures + `libs/common/runtime_contract.py` schema + `scripts/robust_asr/validate_runtime_contract.py` (19 assertions) + 20 unit tests. Slurm CPU job 2129642 COMPLETED 0:0 in 5 s on aisurrey01 (env-isolated apptainer exec). `OK_CONTRACT_SKELETON` emitted; pytest 20/20 passing. `tracker.artifacts.runtime_contract_fixture.contract_skeleton_validation_passed = true`. P0.4 acceptance commit: `40406fc31ad167500bf8ce317286f5c2b5eeb96f`.
- P0.5 PASS: Model card and router card templates. `docs/reports/robust_asr/model_card_lora.md` (9 sections; 30 `TODO_FILLED_IN_<task_id>` placeholders, ≥ 10 required; sha256 `6f1a6ba8...`) and `docs/reports/robust_asr/router_card.md` (9 sections; 24 placeholders, ≥ 8 required; sha256 `bc5dd87d...`). No scope change, no compute. `validate_report_shape.py` still emits `OK_REPORT_SHAPE`. `current_task` advanced P0.5 → P1.1; `last_completed_task` P0.4 → P0.5. `state_transport.last_accepted_report_commit` advanced `0b47b76e` → `40406fc3` (P0.4 acceptance, per orchestrator instruction; not advanced to the P0.5 commit).

## Scope changes

- P1.1 CHANGE_SCOPE applied: amended `configs/robust_asr/reuse_policy_v1.yaml`
  to (a) add `P1.1` to `allowed_tasks` of the existing `data_root` row
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**`
  and (b) add a new `data_root` row
  `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/**`
  (`permitted_use=read_only`, `allowed_tasks=[P1.1, P1.2, P1.3, P2.1, P3.1, P4.1, P4.2, P4.3, P8.1]`,
  `validator=none`, `checksum_required=false`, `large_artifact=true`,
  `commit_allowed=false`). `reports/robust_asr/touch_policy.md` P1.1 row
  rewritten to authorize the actual P1.1 write paths
  (`configs/robust_asr/data_v1.yaml`, `reports/robust_asr/data_inventory.md`,
  `reports/robust_asr/task_reports/P1.1_data_inventory.md`,
  `scripts/robust_asr/check_speaker_disjoint.py`, scope-change rows on
  `reuse_policy_v1.yaml`/`touch_policy.md`, the three live trackers) and
  to record the read-only inventory authorization on
  `…/sources/**` and `…/asr_enhancement_training/datasets/**`. Tracker:
  `latest_approval_packet` set to the P1.1 CHANGE_SCOPE packet (prior
  P0 PHASE_APPROVE shifted to `prior_approval_packet`);
  `artifacts.reuse_policy_config.sha256` →
  `16f2b5f682055f6863e5e68a396dded32e6b8346af08efb2243d147b2664f406`,
  `last_amended_by=P1.1_scope_change`;
  `artifacts.touch_policy.sha256` →
  `7a0b85d6257d03d3ca322160c0080d2c6c91f5a90222114d3ad768af324ff16c`,
  `last_amended_by=P1.1_scope_change`. `current_task` stays `P1.1`,
  `last_completed_task` stays `P0.5`, `blocked=false`, `markers=[]`,
  `state_transport.last_accepted_report_commit` stays
  `3129c11edd5105d7c247b48eb1a170d7c1507cde`. P1.1 inventory not
  executed; no Slurm; no Apptainer; no GPU.

- P0.3 CHANGE_SCOPE applied: amended `configs/robust_asr/reuse_policy_v1.yaml`
  to authorize exec-only use of the Apptainer image (class=container_image,
  permitted_use=exec_only) and to make `slurm/jobs/**` writable for
  robust_asr `p<task_id>_*.sh` scripts (permitted_use=read_only_with_robust_asr_writes).
  current_task remains P0.3; last_completed_task remains P0.2.
- P0.3 CHANGE_SCOPE (Option A) applied: added a new robust_asr-specific
  Apptainer image path under `scratch4weeks/.../asr_enhancement_training/runtime/`
  to `configs/robust_asr/reuse_policy_v1.yaml`
  (class=container_image, permitted_use=exec_only, same allowed_tasks
  as `slurm/tools/**`) and a `data_root` parent row
  (`runtime/**`, permitted_use=read_write, allowed_tasks=[P0.3]) for
  the build outputs. The legacy image at `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`
  is preserved untouched. `reports/robust_asr/touch_policy.md` extended
  with the P0.3 runtime remediation write paths. current_task remains
  P0.3, last_completed_task remains P0.2, BLOCKED_RUNTIME stays active,
  last_accepted_report_commit stays at 635a711.

## P0.3 first attempt (HALTED)

- Slurm job 2129637 ran in container; exit_code=1.
- Container Python 3.10.13 (must be 3.11) and missing imports
  ctranslate2/faster_whisper/pytest. Lightgbm and xgboost also missing
  (would have triggered ROUTER_IMPL_FALLBACK_SKLEARN, superseded by HALTED).
- Evidence committed at `reports/robust_asr/runtime_smoke.md`,
  `reports/robust_asr/task_reports/P0.3_runtime_smoke.md`,
  `artifacts/robust_asr/runtime_smoke/` (metadata + stdout + stderr).
- Awaiting orchestrator decision: rebuild image (likely a CHANGE_SCOPE
  if the new image lives at a different host path) and rerun P0.3.

## P0.3-rerun sub-task (HALTED — BLOCKED_RUNTIME persists; CHANGE_SCOPE needed)

- Slurm job 2129640 against new image: FAILED 1:0 in 10 s on aisurrey01.
- Container Python 3.11.15 OK; lightgbm OK; ctranslate2/faster_whisper/pytest OK
  (Decision rules 2/3 cleared; previous attempt 1 gaps gone).
- transformers and peft FAIL — shadowed user-site transformers ≥4.50
  needs tokenizers ≥0.22 but only tokenizers 0.21.4 is on the path.
- Root cause: auto-bound `/mnt/fast/nobackup` exposes user-site packages
  that shadow the SIF's correctly-pinned packages. SIF itself is correct
  (build log 2129639: torch 2.5.1+cu121, transformers 4.49.0,
  tokenizers 0.21.4 [compatible w/ 4.49], numpy 1.26.4).
- Fix: add `--env PYTHONNOUSERSITE=1` (+ clear `PYTHONUSERBASE`/`PYTHONPATH`)
  to the apptainer exec in `slurm/jobs/p0_3_runtime_smoke.sh`. CHANGE_SCOPE
  required — the P0.3-rerun plan only authorized a single-line CONTAINER
  repoint.

## P0.3-rebuild sub-task (PASS — BLOCKED_RUNTIME still active)

- Slurm job 2129638 (attempt 1): FAILED 1:0 in 12 min — recipe quoting
  bug (`<X` interpreted as input redirect by dash inside `%post`).
  Fixed by single-quoting every `'>=…,<…'` pip spec in the recipe.
- Slurm job 2129639 (attempt 2): COMPLETED 0:0 in 8 min 39 s via
  `apptainer build --fakeroot` on aisurrey01. Image size 5.24 GB.
  Recipe `%test` block ran `Python 3.11.15` and
  `robust_asr runtime image v1 test PASS`.
- Image at the authorized path:
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif`
  sha256 `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`
  recipe sha256 `e6e7f79bae25e8f6bf3726ab8024a75f4769ad0825eddc15f8b1e50ae377f63e`
- Legacy SIF at `/mnt/.../opro2/pytorch_2.1_cuda12.sif` untouched.
- Tracker: `tasks["P0.3-rebuild"]=PASS`,
  `artifacts.runtime_image_v1` populated,
  `tasks.P0.3.next_task=P0.3-rerun`. **BLOCKED_RUNTIME stays active**;
  `current_task` stays `P0.3`; `last_completed_task` stays `P0.2`;
  `state_transport.last_accepted_report_commit` stays `635a711...`

## P0.4 (PASS)

- Files added: fixtures (`rp5_request_fixture.json`, `rp5_response_fixture.json`),
  schema (`libs/common/runtime_contract.py` — JSON Schema 2020-12 draft +
  pure-stdlib assertion runner), validator
  (`scripts/robust_asr/validate_runtime_contract.py` with `--strict-skeleton`
  and `--strict-final`), tests
  (`tests/robust_asr/test_runtime_contract_skeleton.py` — 20 tests covering
  fixtures-pass + per-assertion mutations A01..A19), and Slurm job
  (`slurm/jobs/p0_4_contract_smoke.sh`).
- Scope-change at commit `22b685a` authorized `libs/common/runtime_contract.py`
  (reuse_policy row, `class=robust_asr_owned_extension`, `commit_allowed=true`,
  `allowed_tasks=[P0.4, P9.0]`) and added the validator/tests/Slurm-job paths
  to the touch_policy P0.4 row.
- Slurm CPU job 2129642 on aisurrey01 (partition 2080ti) COMPLETED 0:0 in 5 s,
  MaxRSS 3872 KiB. Env isolation: `PYTHONNOUSERSITE=1`, cleared
  `PYTHONPATH`/`PYTHONUSERBASE`, `PIP_USER=0`. Container sha256
  `8db5364c...` matches `tracker.artifacts.runtime_image_v1`.
- 19/19 assertions PASS in `--strict-skeleton`; sentinel `OK_CONTRACT_SKELETON`.
- 20/20 unit tests passing in 1.06 s inside the SIF.
- `tracker.artifacts.runtime_contract_fixture.contract_skeleton_validation_passed = true`;
  `contract_final_validation_passed` stays `false` (final validation finalized in P9.0).
- `current_task` advanced from P0.4 → P0.5; `last_completed_task` P0.3 → P0.4;
  `state_transport.last_accepted_report_commit` UNCHANGED at `0b47b76e` per
  orchestrator instruction; `state_transport.expected_next_task` stays
  `P0.4` until orchestrator reviews the P0.4 Execution Report.

## P1.1 (PARTIAL — BLOCKED_OOD_PUBLIC; rerun after operator restore)

- Operator restored LibriSpeech audio at the canonical root via
  `wget` + `tar -xzf` of `train-clean-100.tar.gz` and
  `test-clean.tar.gz` from `https://www.openslr.org/resources/12/`
  (gzip integrity OK; tar exit codes 0). `train-clean-360` not
  restored (P1.1 does not require it).
- Post-restore counts:
  - `train-clean-100`: 251 spk, 28 539 `.flac`, 585 `.trans.txt`,
    ~102.30 h, 6.3 GiB.
  - `dev-clean`: 40 spk, 2 703 `.flac`, 97 `.trans.txt`, 5.388 h,
    349 MiB.
  - `test-clean`: 40 spk, 2 620 `.flac`, 87 `.trans.txt`, ~5.47 h,
    356 MiB.
- Cross-split speaker overlap within LibriSpeech: zero.
- Deterministic split partition (recorded in `data_v1.yaml`):
  `lora_train` = 200 train-clean-100 speakers; `router_train` = 51
  train-clean-100 speakers (every 5th sorted ID); `validation` = 40
  dev-clean speakers; `locked_test` = 40 test-clean speakers.
- OOD-real candidates unchanged: Common Voice EN `clips/` empty with no
  `.tsv` transcripts; TED-LIUM R3 and CHiME-6 absent.
- Decision rule 1 (LibriSpeech missing → HALTED + MISSING_EVIDENCE) is
  cleared. Decision rule 2 / Section 1.1 rule 4 (no OOD-real fallback →
  PARTIAL + BLOCKED_OOD_PUBLIC + `claims_enabled.ood_real=false`) is
  the operative outcome.
- Verifications: `OK_DATA_V1_CONFIG`, `OK_SPEAKER_DISJOINT`
  (non-trivial — 4 non-empty splits), `OK_REPORT_SHAPE`. No Slurm,
  no Apptainer, no GPU, no external API.
- Tracker mutations: `tasks.P1.1.status=PARTIAL`,
  `tasks.P1.1.marker=BLOCKED_OOD_PUBLIC`,
  `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false` (was `true`),
  `current_task=P1.1` (held — orchestrator finalizes via APPROVE_EXECUTION),
  `last_completed_task=P0.5` (held),
  `state_transport.last_accepted_report_commit` STAYS
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the rerun commit per orchestrator instruction.
  Approval-packet chain unchanged from prior P1.1.
- Prior attempt history: `tasks.P1.1.history.attempt_1` records the
  HALTED state at commit `1470ebc1da1a1cc70fdf9965480a070a0c248e4d`.

## P1.1 attempt 1 (HALTED — MISSING_EVIDENCE; cleared by operator restore)

- Inventory of dataset roots completed and recorded in
  `reports/robust_asr/data_inventory.md` and `configs/robust_asr/data_v1.yaml`.
- Findings:
  - LibriSpeech `dev-clean`: 40 speakers, 2703 `.flac`, ~5.388 h, 349 MiB on disk — populated.
  - LibriSpeech `train-clean-100`: 251 speaker dirs, **0 `.flac`**, 0 bytes — skeleton only.
  - LibriSpeech `train-clean-360`: subset directory **absent** on host.
  - LibriSpeech `test-clean`: 40 speaker dirs, **0 `.flac`**, 0 bytes — skeleton only.
  - Common Voice EN cv-corpus-24.0-2025-12-05: `clips/` empty, no `.tsv` transcripts.
  - TED-LIUM Release 3: absent.
  - CHiME-6: absent.
- Decision rule 1 of P1.1 fires: LibriSpeech (partially) missing →
  HALTED + `MISSING_EVIDENCE`. Three of four required split labels
  (`lora_train`, `router_train`, `locked_test`) cannot resolve to
  non-empty file lists.
- Decision rule 2 / Section 1.1 rule 4 (BLOCKED_OOD_PUBLIC) is also
  triggered (no Section 1.1 OOD-real source resolves) but is superseded
  by the LibriSpeech HALT. `data_v1.yaml.ood_real.blocked=true` records
  the OOD-real status; `claims_enabled.ood_real` flag is not flipped at
  this report and awaits orchestrator instruction.
- Verifications: `OK_DATA_V1_CONFIG`, `OK_SPEAKER_DISJOINT` (trivial — 3
  of 4 splits empty), `OK_REPORT_SHAPE`. No Slurm, no Apptainer, no GPU,
  no external API.
- Tracker mutations: `tasks.P1.1.status=HALTED`,
  `markers=[MISSING_EVIDENCE]`, `blocked=true`,
  `current_task=P1.1` (held), `last_completed_task=P0.5` (held),
  `state_transport.last_accepted_report_commit` STAYS
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the P1.1 commit per orchestrator instruction.
  Approval-packet chain on tracker:
  `latest_approval_packet`=APPROVE_PLAN(P1.1) on `e4a5677…` (next P1.2);
  `prior_approval_packet`=APPROVE_EXECUTION(P1.1-scope-change) on
  `e4a5677…` (next P1.1);
  `prior_approval_packet_2`=CHANGE_SCOPE(P1.1) on `3129c11e…` (next P1.1);
  `prior_approval_packet_3`=PHASE_APPROVE(P0) on `d0ba20c5…` (next P1.1).

## Pending

- P0 gate → P1 (schema, manifests, degradations) — blocked at P1.1 by MISSING_EVIDENCE
- P1 → P2 (Whisper base baseline)
- P3 (LoRA smoke, Decision A)
- P4 (Full LoRA if Decision A PASS)
- P5 (AssemblyAI cache or BLOCKED_API)
- P6 (Oracle / selector evidence)
- P7 (Router or deterministic selector)
- P8 (System evaluation)
- P9 (Handoff package)
- P10 (Final reports and audit)
