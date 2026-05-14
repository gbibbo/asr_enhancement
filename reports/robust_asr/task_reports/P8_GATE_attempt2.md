# Phase Gate Report — P8_GATE attempt 2

PASS

## STATE SNAPSHOT

- project: `robust_asr_lora_router`
- branch: `feature/robust-asr-lora-router-datamove1-v1`
- head_commit_full (pre-gate): `643efe520904caeff84e29b11cb764ad07bbe3d9`
- git_status_short: (clean before this gate execution)
- current_phase: `P8`
- current_task at entry: `P8_GATE`
- last_completed_task at entry: `P8.2`
- state_transport.expected_next_task at entry: `P8_GATE`
- state_transport.last_accepted_report_commit at entry: `0073e7b4076ce76d36233bec2eacb4411ba28722`
- state_transport.latest_approval_packet at entry: `APPROVE_PLAN(P8_GATE)` (this report's authorizing packet), `accepted_report_commit=643efe520904caeff84e29b11cb764ad07bbe3d9`, `next_expected_task=P8_GATE`, with Reading A pre-ruling on the disjointness-proof conjunct
- markers at entry: `[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]`
- claims_enabled at entry: `{ood_real: false, cloud_tradeoff: false, positive_lora: false, positive_system: false}`
- router_status: `SELECTOR_PACKAGED`
- lora_status: `SKIPPED_BY_DECISION_A`
- proposed_deviations.P8_2_demo_only_upstream_overlap.status: `ENACTED`
- decisions.Decision_D_positive_system.outcome: `false`

## PHASE GATE EVIDENCE

- phase: `P8`
- task_id: `P8_GATE`
- attempt: `2`
- predicate_source: agent plan §2676–§2691 (P8 gate predicate)
- active_branch_in_outcome_table: OUTCOME_E (Branch B deterministic-selector, single-deployable-baseline `whisper_base_ct2_int8`)
- decisions_set_during_phase: `Decision_D_positive_system.outcome = false` (recorded at P8.1; not changed here)
- predicate_result: **PASS**

### Predicate conjuncts and observed values

1. **`tracker.tasks[P8.1].status == PASS`** — result: **PASS**.
   - observed_value: `PASS`.
   - evidence: `docs/progress/robust_asr_progress.yaml` → `tasks.P8.1.status: PASS` (approved_at_commit `1b9f33e6…`, OUTCOME_E_NARROWED_SCOPE marker recorded on this task and on `decisions.Decision_D_positive_system`).
2. **`tracker.tasks[P8.2].status == PASS`** — result: **PASS**.
   - observed_value: `PASS` under enacted deviation `P8_2_demo_only_upstream_overlap` (`deviation_status: ENACTED`).
   - evidence: `docs/progress/robust_asr_progress.yaml` → `tasks.P8.2.status: PASS`, `tasks.P8.2.deviation: P8_2_demo_only_upstream_overlap`, `tasks.P8.2.deviation_status: ENACTED`, `tasks.P8.2.approved_by: APPROVE_EXECUTION_P8.2`, `tasks.P8.2.approved_at_commit: 2e1c46e8…` (the `APPROVE_EXECUTION(P8.2)` packet has been demoted to `prior_approval_packet_p8_2_exec` by `plan_index_refresh` and is unchanged).
   - notes_on_pass (carried verbatim from the tracker): "PASS recorded as demo-only UI asset delivery under enacted deviation P8_2_demo_only_upstream_overlap with binding constraints C1-C5. NOT evaluation evidence; NOT support for any claims_enabled.* flag."
3. **`reports/robust_asr/system/system_eval.md` exists with paired test results AND `positive_system` on first line** — result: **PASS**.
   - observed_value: file exists; `head -n 1` is the literal line `positive_system: false`; body contains paired BCa bootstrap (10000 iter, seed 20250514) and Wilcoxon signed-rank against declared baseline `whisper_base_ct2_int8` per the P8.1 task report and `tasks.P8.1.notes`.
   - evidence: live `head -n 1` of the file (returned `positive_system: false`); cross-reference `reports/robust_asr/task_reports/P8.1_system_eval.md` and `tasks.P8.1.notes` recording Slurm job `2132279` COMPLETED 0:0 producing the file.
4. **`tracker.claims_enabled.positive_system in {true, false}`** — result: **PASS**.
   - observed_value: `false`.
   - evidence: `docs/progress/robust_asr_progress.yaml` → `claims_enabled.positive_system: false` (parsed via `yaml.safe_load`). Under OUTCOME_E single-deployable-baseline scope, Section 5.6 predicate (i)+(ii) cannot hold; predicate (iii) holds; outcome `false` is the recorded decision.
5. **`artifacts/robust_asr/demo/demo_examples_manifest.json` exists with disjointness proof** — result: **PASS** (under orchestrator pre-ruling, Reading A — see "Demo-only deviation pre-ruling" below).
   - observed_value: file exists; parsed:
     - `len(examples) == 8`,
     - `manifest_version == "v1.2-deviation-enacted"`,
     - top-level `deviation` block present with `deviation_id == "P8_2_demo_only_upstream_overlap"`, `upstream_disjointness == false`, and `binding_constraints` listing exactly `C1, C2, C3, C4, C5`.
     - `manifest_sha256 == 850c02db…` (per tracker `artifacts.demo_examples_manifest.sha256`); WAV bytes byte-unchanged at every prior verification gate.
   - demo-side disjointness proof: `tests/robust_asr/test_leakage.py::test_demo_examples_disjoint_from_eval_sets` PASSED (live run; see conjunct 6).
   - cross-reference: `reports/robust_asr/demo/provenance_audit.md` records `PASS_WITH_DEMO_ONLY_DEVIATION (final)` on its first non-blank lines (after `PASS (provenance fields)` and `FAIL (upstream disjointness)`), narrating both the upstream-level overlap and the demo-side disjointness preservation.
6. **`pytest tests/robust_asr/test_leakage.py` PASS** — result: **PASS**.
   - observed_value: `5 passed in 7.56s` (Python 3.9.13, pytest 8.4.2, configfile `pyproject.toml`).
     - `test_speaker_disjoint_lora_vs_router_train PASSED`
     - `test_audio_id_disjoint_lora_train_vs_router_targets PASSED`
     - `test_locked_test_sets_disjoint_from_train PASSED`
     - `test_demo_examples_disjoint_from_eval_sets PASSED`
     - `test_common_voice_demo_disjoint_from_ood_locked PASSED`
   - cross-check (full robust_asr suite, not in predicate but recorded for evidence): `pytest tests/robust_asr/` → `137 passed in 15.85s`.

## Demo-only deviation pre-ruling (Reading A applied)

Per the authorizing `APPROVE_PLAN(P8_GATE)` packet (`accepted_report_commit=643efe520904caeff84e29b11cb764ad07bbe3d9`), the disjointness-proof conjunct (conjunct 5 above) is satisfied by **demo-side `audio_id` / `speaker_id` / `audio_sha256` disjointness** under the enacted `P8_2_demo_only_upstream_overlap` deviation. The upstream-level overlap with the locked LibriSpeech `dev-clean`–derived validation and `degradation_v1` eval manifests is real, is disclosed in the manifest's top-level `deviation` block, is narrated in `reports/robust_asr/demo/provenance_audit.md`, and is carried forward to the next phase under the binding constraints C1–C5. The pre-ruling does not convert the deviation into positive evidence and does not relax any binding constraint.

### Upstream overlap carried forward (disclosure)

- Upstream utterances: `librispeech/dev-clean/{1272-128104-0000, 1673-143396-0002, 174-168635-0000, 1993-147149-0000, 2086-149214-0000}`.
- Upstream speakers: `{1272, 1673, 174, 1993, 2086}`.
- Overlap scope: 13 of 16 locked manifests (validation + `degradation_v1_id_eval` + `degradation_v1_ood_param_eval` + all 10 per-family subsets) under schema-normalized comparison.
- Disclosure ownership: P9.1 (C4) and P10.1 (C5) per `proposed_deviations.P8_2_demo_only_upstream_overlap.required_disclosure_tasks`.

### Demo artifacts are not evaluation evidence and do not support `claims_enabled.*` flags

- Demo bundle scope: UI/demo only (P9.1 handoff bundle, P10 handoff package, asr-rp5 demo runtime).
- Forbidden uses (binding constraints, restated): WER, CER, robustness metrics, `claims_enabled.positive_system`, `claims_enabled.cloud_tradeoff`, `claims_enabled.positive_lora`, `claims_enabled.ood_real`, P8.1 system evaluation, P10.1 final verification metrics, `artifacts/robust_asr/eval_tables/**.parquet`, `selector_evidence.parquet`, `oracle/**.parquet`, and any system_eval input set.
- This gate report does not change any `claims_enabled.*` flag. All four flags remain `false`.

## COMMIT REFERENCE

- commit_hash for this gate report and tracker write: recorded in `Tracker mutations` below (the gate-evidence commit).
- `state_transport.last_accepted_report_commit` is **held** at the `plan_index_refresh` anchor `0073e7b4076ce76d36233bec2eacb4411ba28722` per the P5.1 / P6.1 / P7.3 / P8.1 / P8.2 acceptance pattern; the orchestrator advances it on `PHASE_APPROVE(P8)` in a subsequent `PHASE_APPROVAL_RECORDING` step.
- pushed_to_origin: true.

## Tracker mutations on this commit

- `tasks.P8_GATE.attempt`: `1` → **`2`** (new attempt opened by this evaluation; the `attempt=1` FAIL record is preserved under `prior_attempts`).
- `tasks.P8_GATE.status`: `FAIL` → **`PASS`** (attempt 2).
- `tasks.P8_GATE.predicate_inputs`: recorded with the six observed values above.
- `phase_summary.P8`: `null` → **`PASS`**.
- `state_transport.latest_phase_gate_report`: `null` → **`reports/robust_asr/task_reports/P8_GATE_attempt2.md`**.
- `state_transport.latest_approval_packet`: recorded as `APPROVE_PLAN(P8_GATE)` on `643efe520904caeff84e29b11cb764ad07bbe3d9` with Reading A pre-ruling; the prior `CHANGE_SCOPE(plan_index_refresh)` packet demoted to `prior_approval_packet_plan_index_refresh`.
- `state_transport.last_accepted_report_commit`: **HELD** at `0073e7b4076ce76d36233bec2eacb4411ba28722` (NOT advanced by the gate-evidence commit; advanced only on `PHASE_APPROVE(P8)`).

## State held (no changes)

- `current_task = P8_GATE` (held; **NOT advanced to P9.0**).
- `last_completed_task = P8.2` (held; the gate report does not itself advance `last_completed_task`; that advancement is owned by the subsequent `PHASE_APPROVAL_RECORDING` step on `PHASE_APPROVE(P8)`).
- `state_transport.expected_next_task = P8_GATE` (held; orchestrator pivots to P9.0 on `PHASE_APPROVE(P8)`).
- `orchestrator_approvals.P8 = null` (held; gate-evidence emission does not record orchestrator approval).
- `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]` (held; OUTCOME_E_NARROWED_SCOPE held on `tasks.P8.1` and `decisions.Decision_D_positive_system`).
- `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system} = false` (all held).
- `blocked = false`; `blocker = null` (held).
- `router_status = SELECTOR_PACKAGED`; `lora_status = SKIPPED_BY_DECISION_A` (held).
- `proposed_deviations.P8_2_demo_only_upstream_overlap.status = ENACTED` (held).
- `decisions.Decision_D_positive_system.outcome = false` (held).
- `tasks.P8.1.status = PASS` (held). `tasks.P8.2.status = PASS` (held). All `tasks.P8.2-*` sub-tasks held in their accepted states.
- `tasks.P4.{1,2,3} = SKIPPED_BY_DECISION_A` (held). `tasks.P6.2 = SKIPPED_BY_OUTCOME_E` (held). `tasks.P7.{1,2} = SKIPPED_BY_OUTCOME_E` (held). `tasks.P7.3 = PASS` (held).

## NEXT EXPECTED PHASE

- next_phase_first_task (per agent plan Section 0.1 transition table, conditional on `PHASE_APPROVE(P8)`): **`P9.0`** — Final runtime contract.
- markers_carried_forward: `[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]` plus `OUTCOME_E_NARROWED_SCOPE` on `tasks.P8.1` / `decisions.Decision_D_positive_system`.
- claims_enabled_state at gate time: `{ood_real: false, cloud_tradeoff: false, positive_lora: false, positive_system: false}`.
- deviation_carried_forward: `P8_2_demo_only_upstream_overlap` (`ENACTED`); P9.1 must enforce C4 (disclosure); P10.1 must enforce C5 (exclusion).
- handoff/contract obligations entering P9: finalize `artifacts/robust_asr/runtime_contract/{final_request_schema,final_response_schema}.json` reflecting deployable backends (only `whisper_base_ct2_int8` under OUTCOME_E; LoRA absent per Decision B; AssemblyAI absent per BLOCKED_API/`claims_enabled.cloud_tradeoff=false`) and the deterministic-selector router; produce the handoff package with C4 disclosure.

## Next legal action

**Stop after this report. Request `PHASE_APPROVE(P8)`.** Do not open `P9.0` until the orchestrator returns `PHASE_APPROVE(P8)` (or `PHASE_REJECT(P8)` or `CHANGE_SCOPE`). On `PHASE_APPROVE(P8)`, a subsequent `PHASE_APPROVAL_RECORDING` step will:

- set `orchestrator_approvals.P8 = PHASE_APPROVE`,
- advance `current_task` `P8_GATE → P9.0`,
- advance `last_completed_task` `P8.2 → P8_GATE`,
- advance `state_transport.last_accepted_report_commit` from `0073e7b…` to the `PHASE_APPROVE`-accepted commit,
- set `state_transport.expected_next_task = P9.0`,
- demote the current `APPROVE_PLAN(P8_GATE)` packet to `prior_approval_packet_p8_gate_plan`,
- record `PHASE_APPROVE(P8)` as the new `latest_approval_packet`.
