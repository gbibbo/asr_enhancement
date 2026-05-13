# Robust ASR — State Capsule

Updated by: P6.1 CHANGE_SCOPE recorded. ORCHESTRATOR_DECISION: scope=scope_change task_id=P6.1 phase=P6 decision=CHANGE_SCOPE accepted_report_commit=`9ffc885` next_expected_task=P6.1 required_fix="Authorize deterministic-selector config, selector evidence scripts, selector evidence table, and DETERMINISTIC_SELECTOR_VERSION." rationale: P6.1 Outcome E selector-evidence path requires `configs/robust_asr/router_v1.yaml` and `libs/common/versions.py` (append `DETERMINISTIC_SELECTOR_VERSION` only), but the current reuse/touch policy did not authorize these P6.1 writes. Scope-change applied to `configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md`. Reuse policy: `configs/robust_asr/**` `allowed_tasks` += `P6.1`; new row `configs/robust_asr/router_v1.yaml` (active_state, read_write, [P6.1, P6.2, P7.1, P7.3, P10.1], validator=`scripts/robust_asr/validate_selector_evidence.py`, checksum_required=true, large_artifact=false, commit_allowed=true); amend `libs/common/versions.py` row (existing_runtime_code, append_constants_only) allowed_tasks=[P1.2] -> [P1.2, P6.1], validator=`NORMALIZATION_VERSION_constant_present AND DETERMINISTIC_SELECTOR_VERSION_constant_present`, checksum_required=true, commit_allowed=true (NORMALIZATION_VERSION, METRICS_VERSION, DEGRADATION_VERSION, ENHANCER_VERSION must remain unchanged). Touch policy P6.1 row rewritten to authorize writes of `configs/robust_asr/router_v1.yaml`, `scripts/robust_asr/build_selector_evidence_table.py`, `scripts/robust_asr/validate_selector_evidence.py`, `artifacts/robust_asr/router/selector_evidence.parquet`, `reports/robust_asr/router/selector_evidence_summary.md`, `reports/robust_asr/task_reports/P6.1_selector_evidence.md`, `libs/common/versions.py` (append `DETERMINISTIC_SELECTOR_VERSION` only), `configs/robust_asr/reuse_policy_v1.yaml` (scope-change rows), `reports/robust_asr/touch_policy.md` (scope-change row), and the three live trackers; reads of plan files, `reuse_policy_v1.yaml`, `configs/robust_asr/{router_v1,data_v1,eval_manifests_v1,degradation_v1}.yaml`, `libs/common/{eval_schema.yaml,normalization.py,metrics.py,versions.py}`, `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`, `artifacts/robust_asr/manifests/*.parquet`, `artifacts/robust_asr/lora_smoke/**` (LoRA-train audio_id disjointness), `artifacts/robust_asr/demo/**` (trivial disjointness pre-P8.2), and `scripts/robust_asr/validate_report_shape.py`. Explicit P6.1 default_no_touch additions: `artifacts/robust_asr/oracle/**` (Branch A only; OUTCOME_E active), P6.2 router feature/matrix artifacts, P7.x candidate/selected_router artifacts, AssemblyAI runtime files, LoRA artifacts, `libs/audio/**` write, `libs/asr_adapter/**` write, `libs/common/**` write (except `libs/common/versions.py` append), `tests/robust_asr/**` write (P6.1 not in `tests/robust_asr/**` allowed_tasks), `slurm/**`, `configs/training/**`, `scripts/training/**`, `services/**`, `infra/**`, `configs/robust_asr/pricing_v1.yaml` write, `configs/robust_asr/eval_manifests_v1.yaml` write. External: none (no Slurm, no Apptainer GPU, no external API for P6.1). Artifact hashes: `artifacts.reuse_policy_config.sha256=9994a741d85fb9b4c2c6aa6ea5d5ce71f763cb551c4b0403964abd10cfdbdb7c`, `artifacts.reuse_policy_config.last_amended_by=P6.1_scope_change`; `artifacts.touch_policy.sha256=382f66de62a207472ee77a35d9af88585901e29394670043bf34198823f56a42`, `artifacts.touch_policy.last_amended_by=P6.1_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P6.1) on `9ffc885` (next P6.1); previous PHASE_APPROVE(P5) demoted to `prior_approval_packet_p5_phase` on `c71e0a0bb25a5d2749801d8fc7444869ff331d1b` (next P6.1). `state_transport.expected_next_task=P6.1` held; `state_transport.last_accepted_report_commit=c71e0a0bb25a5d2749801d8fc7444869ff331d1b` held (CHANGE_SCOPE does not advance `last_accepted_report_commit`). `tasks.P6.1.status=scope_change_recorded`, `tasks.P6.1.implementation_status=NOT_STARTED`; `tasks.P6.2` held null (`SKIPPED_BY_OUTCOME_E` is enacted at P6.1 closure per agent plan §3853-§3854). `validate_report_shape.py` -> `OK_REPORT_SHAPE`. Held: `current_phase=P6`, `current_task=P6.1`, `last_completed_task=P5.1`, `markers=[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=false`, `claims_enabled.positive_lora=false`, `claims_enabled.positive_system=pending`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS,P1:PASS,P2:PASS,P3:PASS,P5:PASS}`, `orchestrator_approvals={P0,P1,P2,P3,P5}=PHASE_APPROVE`. P6.1 implementation has not started: no `router_v1.yaml`, no selector scripts, no `selector_evidence.parquet`, no `selector_evidence_summary.md`, no `DETERMINISTIC_SELECTOR_VERSION` constant, no P6.2 skip mutation, no task report. Awaits `APPROVE_PLAN(P6.1)` and `APPROVE_EXECUTION(P6.1)`. No code, no test, no Slurm submission, no real-provider call for this update. Only policy and tracker files modified.

## Prior update — P5 PHASE_APPROVE recorded — OUTCOME_E activated. ORCHESTRATOR_DECISION: scope=phase task=null phase=P5 decision=PHASE_APPROVE accepted_report_commit=`c71e0a0bb25a5d2749801d8fc7444869ff331d1b` next_expected_task=P6.1 required_fix=null. Rationale: P5 phase gate PASS via the BLOCKED_API + `claims_enabled.cloud_tradeoff=false` branch of agent plan §2589-§2596 — `tasks.P5.1.status=HALTED` ∈ {PASS, PARTIAL, HALTED} AND marker `BLOCKED_API` active AND `claims_enabled.cloud_tradeoff=false` satisfies the one-of clause. Backend-count predicate (§2607-§2613): `{whisper_base_ct2_int8}` only (LoRA excluded by `Decision_B_lora_full.include_lora_in_router=false`/Decision_A_smoke=FAIL; AssemblyAI excluded by `BLOCKED_API`/`cloud_tradeoff=false`). Count = 1 < 2 → Section 8 routing activates `OUTCOME_E_DETERMINISTIC_SELECTOR` at the P5 gate. Routing advances to P6.1 selector-evidence path (§3848-§3853). Tracker mutations: `current_phase` advanced `P5 -> P6`; `current_task` advanced `P5_GATE -> P6.1`; `last_completed_task` held at `P5.1` (PHASE_APPROVE(P5) recorded on the P5.1 acceptance commit does not itself advance last_completed_task, matching the P0/P1/P2/P3 pattern); `phase_summary.P5=PASS`; `orchestrator_approvals.P5=PHASE_APPROVE`; `markers` -> `[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]`; `decisions.P5_routing.branch=B_blocked_api_outcome_e`; `decisions.P5_routing.deployable_backend_count=1`; `decisions.P5_routing.deployable_backends=[whisper_base_ct2_int8]`; `decisions.P5_routing.outcome_e_activated_at_task=P5_GATE`; `latest_approval_packet`=PHASE_APPROVE(P5) on `c71e0a0bb25a5d2749801d8fc7444869ff331d1b` (next P6.1); `prior_approval_packet_p5_1_exec`=APPROVE_EXECUTION(P5.1) on `c71e0a0` (next P5_GATE); `prior_approval_packet_p5_1_plan`=APPROVE_PLAN(P5.1) on `f7a845f3ff8f2bf51b8bcc8ff2342a4e4f817f64` (next P5_GATE); `prior_approval_packet_p5_1_scope_exec`=APPROVE_EXECUTION(P5.1-scope-change) on `f7a845f` (next P5.1); `prior_approval_packet_p5_1_change_scope`=CHANGE_SCOPE(P5.1) on `45b6cac93d1fe3eb54630a7511c331439715bb68` (next P5.1); `prior_approval_packet_p3_phase`=PHASE_APPROVE(P3) on `26db72df3215355a68029927980389216353526e` (next P5.1). `state_transport.expected_next_task=P6.1`; `state_transport.last_accepted_report_commit=c71e0a0bb25a5d2749801d8fc7444869ff331d1b` held (PHASE_APPROVE recorded against the P5.1 acceptance commit; not advanced by the phase-gate tracker commit itself). Held: `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=false`, `claims_enabled.positive_lora=false`, `claims_enabled.positive_system=pending`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS,P1:PASS,P2:PASS,P3:PASS,P5:PASS}`, `orchestrator_approvals={P0,P1,P2,P3,P5}=PHASE_APPROVE`. `tasks.P6.2.status=SKIPPED_BY_OUTCOME_E` is NOT enacted by the P5 gate — it is enacted by P6.1 per §3853. `tasks.P7.1` / `tasks.P7.2` skips are owned by the P6 gate (§312, §2664-§2665). BLOCKED_OOD_PUBLIC NOT cleared (held non-blocking); BLOCKED_API NOT cleared (held non-blocking). P6.1 not started. No code, no test, no Slurm submission, no real-provider call for this update. Only tracker files modified.

## Prior update — P5.1 APPROVE_EXECUTION recorded. ORCHESTRATOR_DECISION: scope=task task=P5.1 phase=P5 decision=APPROVE_EXECUTION accepted_report_commit=`c71e0a0bb25a5d2749801d8fc7444869ff331d1b` next_expected_task=P5_GATE required_fix=null. Rationale: P5.1 legally halted with `BLOCKED_API reason=key_unset`; ASSEMBLYAI_API_KEY was unset; no HTTP request or paid API call was made; pricing guard and tests passed; `claims_enabled.cloud_tradeoff=false` was set; BLOCKED_OOD_PUBLIC remains active and non-blocking. Tracker mutations: `current_task` advanced `P5.1 -> P5_GATE`; `last_completed_task` advanced `P3.2 -> P5.1`; `tasks.P5.1.status=HALTED` held; `tasks.P5.1.marker=BLOCKED_API` held; `tasks.P5.1.commit=c71e0a0bb25a5d2749801d8fc7444869ff331d1b`; `state_transport.last_accepted_report_commit` advanced `26db72df3215355a68029927980389216353526e -> c71e0a0bb25a5d2749801d8fc7444869ff331d1b`; `state_transport.expected_next_task=P5_GATE` held; `latest_approval_packet`=APPROVE_EXECUTION(P5.1) on `c71e0a0bb25a5d2749801d8fc7444869ff331d1b` (next P5_GATE); `prior_approval_packet_p5_1_plan`=APPROVE_PLAN(P5.1) on `f7a845f3ff8f2bf51b8bcc8ff2342a4e4f817f64` (next P5_GATE); `prior_approval_packet_p5_1_scope_exec`=APPROVE_EXECUTION(P5.1-scope-change) on `f7a845f` (next P5.1); `prior_approval_packet_p5_1_change_scope`=CHANGE_SCOPE(P5.1) on `45b6cac93d1fe3eb54630a7511c331439715bb68` (next P5.1); `prior_approval_packet_p3_phase`=PHASE_APPROVE(P3) on `26db72df3215355a68029927980389216353526e` (next P5.1). Held: `current_phase=P5`, `markers=[BLOCKED_OOD_PUBLIC, BLOCKED_API]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=false`, `claims_enabled.positive_lora=false`, `claims_enabled.positive_system=pending`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS,P1:PASS,P2:PASS,P3:PASS}`, `orchestrator_approvals={P0,P1,P2,P3}=PHASE_APPROVE`. P5_GATE not started. P6.1 not started. No code, no test, no Slurm submission, no real-provider call for this update. Only tracker files modified.

## Prior update — P5.1 HALTED — BLOCKED_API (key_unset). APPROVE_EXECUTION(P5.1-scope-change) and APPROVE_PLAN(P5.1) both recorded on commit `f7a845f3ff8f2bf51b8bcc8ff2342a4e4f817f64`. P5.1 implementation deliverables written this commit: `configs/robust_asr/pricing_v1.yaml` (sha256 `c1e61077ea4c025b147d0bbc9ce42e5b8cbca83a3cb360bc5724bdd99a61a815`), `configs/robust_asr/eval_manifests_v1.yaml` amended with `assemblyai` backend_endpoints entry (sha256 `ab7d16ec3998dd94a20eccf74d3cf2ba39800baef2851eb01d23ce5d1423cfc4`), `scripts/robust_asr/probe_assemblyai_runtime.py` (sha256 `6f1530db9769eae79cd5a013b9d4e7535667bd6e2d86e21201cc6b559d98657c`), `scripts/robust_asr/populate_assemblyai_cache.py` (sha256 `af21fb41a94c77431f7d9c948383c6a4c090dbb9329589291532372a9db89217`), `scripts/robust_asr/evaluate_assemblyai_from_cache.py` (sha256 `20c2e0b3a0df9b57cbc52951450d8cb38cef46ecf631dc16c58ea4756a78e20e`), `tests/robust_asr/test_assemblyai.py` (15 tests, sha256 `18a35a280baba0f3dab463c901b7132c6ade44e5ee51748789eafed02aba8348`), `reports/robust_asr/task_reports/P5.1_assemblyai.md`. Probe `python3 scripts/robust_asr/probe_assemblyai_runtime.py` → `ASSEMBLYAI_RUNTIME=false reason=key_unset` (exit 0); `ASSEMBLYAI_API_KEY` is unset on datamove1. No AssemblyAI request issued; no upload; no `assemblyai.parquet`; no `cache_summary.json`; no Slurm submission; ASSEMBLYAI_API_KEY never logged or persisted. Paid-API guard implemented in `populate_assemblyai_cache.py`: exit 8 ASSEMBLYAI_API_KEY_UNSET; exit 12 PENDING_PRICING_VERIFICATION (>90d old `assemblyai_pricing_checked_date`); exit 11 BUDGET_EXCEEDED (estimated total cost or running cost > `max_total_cost_usd`); exit 9 ASSEMBLYAI_AUTH_FAIL (HTTP 401/403); exit 10 ASSEMBLYAI_QUOTA (HTTP 429 after retries); pre-spend summary printed BEFORE any upload; per-row running-cost guard. Verification: `pytest tests/robust_asr/test_assemblyai.py -q` → 15 passed; full `pytest tests/robust_asr/` → 124/124 PASS (was 109; +15 new); `validate_report_shape.py` → `OK_REPORT_SHAPE`. Tracker mutations: `tasks.P5.1.status=HALTED`, `tasks.P5.1.blocked_marker=BLOCKED_API`, `tasks.P5.1.reason=key_unset`; `markers=[BLOCKED_OOD_PUBLIC, BLOCKED_API]`; `claims_enabled.cloud_tradeoff` flipped `true -> false`; `assemblyai_table.path=null`, `blocked_by=BLOCKED_API`, `blocked_reason=key_unset`, `expected_path=artifacts/robust_asr/eval_tables/assemblyai.parquet`; `latest_approval_packet`=APPROVE_PLAN(P5.1) on `f7a845f` (next P5_GATE); `prior_approval_packet_p5_1_scope_exec`=APPROVE_EXECUTION(P5.1-scope-change) on `f7a845f` (next P5.1); `prior_approval_packet_p5_1_change_scope`=CHANGE_SCOPE(P5.1) on `45b6cac` (next P5.1); `prior_approval_packet_p3_phase`=PHASE_APPROVE(P3) on `26db72d`. `state_transport.expected_next_task=P5_GATE`; `state_transport.last_accepted_report_commit=26db72df3215355a68029927980389216353526e` held per orchestrator instruction (NOT advanced to the P5.1 implementation commit). Held: `current_phase=P5`, `current_task=P5.1` (held until APPROVE_EXECUTION(P5.1) advances it to P5_GATE), `last_completed_task=P3.2`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=false`, `claims_enabled.positive_system=pending`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS,P1:PASS,P2:PASS,P3:PASS}`, `orchestrator_approvals={P0,P1,P2,P3}=PHASE_APPROVE`. `BLOCKED_OOD_PUBLIC` NOT cleared (held non-blocking). P5_GATE not started. AssemblyAI cloud-baseline awaits operator-supplied `ASSEMBLYAI_API_KEY` if Section 8 P5 gate Branch A is desired; otherwise the P5 gate will activate `OUTCOME_E_DETERMINISTIC_SELECTOR` per Section 8 (deployable transcript-producing backend count = 1).

## Prior update — P5.1 CHANGE_SCOPE recorded. ORCHESTRATOR_DECISION: scope=scope_change task=P5.1 phase=P5 decision=CHANGE_SCOPE accepted_report_commit=`45b6cac93d1fe3eb54630a7511c331439715bb68` next_expected_task=P5.1 required_fix="Authorize AssemblyAI pricing config, runtime scripts/tests, eval manifest extension, and scratch cache path." rationale: P5.1 requires `configs/robust_asr/pricing_v1.yaml`, `eval_manifests_v1.yaml` update, `tests/robust_asr/test_assemblyai.py`, and scratch AssemblyAI cache writes, but prior policy rows did not authorize these for P5.1. Scope-change applied at commit `e45903e76b5b42d3ceb2a89b77ec7675d9d239d4` to `configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md`. Reuse policy: `configs/robust_asr/**` allowed_tasks += P5.1; `tests/robust_asr/**` allowed_tasks += P5.1; new row `configs/robust_asr/pricing_v1.yaml` (active_state, read_write, [P5.1, P10.1], validator=load_yaml_and_check_required_fields, checksum_required=true, commit_allowed=true); new row `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/assemblyai_cache/**` (data_root, read_write, [P5.1], validator=cache_summary_json, large_artifact=true, commit_allowed=false). Touch policy P5.1 row rewritten to authorize writes of `configs/robust_asr/pricing_v1.yaml`, `configs/robust_asr/eval_manifests_v1.yaml` (append assemblyai backend_endpoints entry only), `configs/robust_asr/reuse_policy_v1.yaml` (scope-change rows), `scripts/robust_asr/probe_assemblyai_runtime.py`, `scripts/robust_asr/populate_assemblyai_cache.py`, `scripts/robust_asr/evaluate_assemblyai_from_cache.py`, `tests/robust_asr/test_assemblyai.py`, `artifacts/robust_asr/eval_tables/assemblyai.parquet`, `reports/robust_asr/assemblyai/cache_summary_summary.md`, `reports/robust_asr/task_reports/P5.1_assemblyai.md`, `reports/robust_asr/touch_policy.md` (scope-change row), and the three live trackers. Authorized external: `ASSEMBLYAI_API_KEY` from environment only (never logged or persisted); `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/assemblyai_cache/**` (read_write, large_artifact, never committed); robust_asr Apptainer image (exec only). Artifact hashes: `artifacts.reuse_policy_config.sha256=d72cc31f5ca46b7adb01cde7a8ffd3301c46fce58c8e8ff61c0c8bba8ed109ee`, `artifacts.reuse_policy_config.last_amended_by=P5.1_scope_change`; `artifacts.touch_policy.sha256=710a49f2e87c9755d7b00cf66c68bcdeaa9088b8eb5f44ccbcc347de4d58b4aa`, `artifacts.touch_policy.last_amended_by=P5.1_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P5.1) on `45b6cac93d1fe3eb54630a7511c331439715bb68` (next P5.1); previous PHASE_APPROVE(P3) demoted to `prior_approval_packet_p3_phase` on `26db72df3215355a68029927980389216353526e` (next P5.1). `state_transport.expected_next_task=P5.1` held; `state_transport.last_accepted_report_commit=26db72df3215355a68029927980389216353526e` held (CHANGE_SCOPE does not advance last_accepted_report_commit). `validate_report_shape.py` `OK_REPORT_SHAPE`. Held: `current_phase=P5`, `current_task=P5.1`, `last_completed_task=P3.2`, `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=false`, `claims_enabled.cloud_tradeoff=true`, `claims_enabled.positive_system=pending`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS, P3:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE, P3:PHASE_APPROVE}`. P5.1 implementation has not started: no `pricing_v1.yaml`, no probe/populate/evaluate scripts, no `test_assemblyai.py`, no `eval_manifests_v1.yaml` extension, no `assemblyai.parquet`, no AssemblyAI API call, no Slurm submission. Awaits `APPROVE_PLAN(P5.1)` and `APPROVE_EXECUTION(P5.1)`.

## Prior update — P3 PHASE_APPROVE — last_completed_task fix. `last_completed_task` corrected to `P3.2` (held; P3_GATE PHASE_APPROVE is recorded on the P3.2 acceptance commit and does not itself advance last_completed_task — matching the prior P0/P1/P2 phase-gate pattern). All other PHASE_APPROVE(P3) mutations from the prior commit are preserved: `current_phase` advanced `P3 -> P5`; `current_task` advanced `P3_GATE -> P5.1`; `phase_summary.P3=PASS`; `orchestrator_approvals.P3=PHASE_APPROVE`; `lora_status` transitioned `SMOKE_DONE -> SKIPPED_BY_DECISION_A`; `claims_enabled.positive_lora` transitioned `pending -> false`; `decisions.Decision_B_lora_full.include_lora_in_router=false` (decided_at_task=P3_GATE); `tasks.P4.1.status=tasks.P4.2.status=tasks.P4.3.status=SKIPPED_BY_DECISION_A`; `latest_approval_packet`=PHASE_APPROVE(P3) on `26db72df3215355a68029927980389216353526e` (next P5.1); `prior_approval_packet_p3_2_exec`=APPROVE_EXECUTION(P3.2) on `26db72d` (next P3_GATE); `prior_approval_packet_p3_2_plan`=APPROVE_PLAN(P3.2) on `1025a24` (next P3_GATE); `state_transport.expected_next_task=P5.1`; `state_transport.last_accepted_report_commit=26db72df3215355a68029927980389216353526e` held (PHASE_APPROVE recorded against the P3.2 acceptance commit; not advanced by the phase-gate tracker commit). Rationale: P3 phase gate PASS per Section 8 P3 predicate (tasks.P3.1=PASS, tasks.P3.2=PASS, lora_smoke_report.md first-line FAIL, decision_a_smoke.md present, Decision_A_smoke.outcome=FAIL ∈ {PASS,PARTIAL,FAIL,HALTED}, no BLOCKED_RUNTIME/MISSING_EVIDENCE/PLAN_CONFLICT). Section 8 Branch B routing for Decision_A_smoke=FAIL enacted: P4.1/P4.2/P4.3 skipped, lora excluded from router, no positive LoRA claims, next post-gate task = P5.1. BLOCKED_OOD_PUBLIC remains active and non-blocking; `claims_enabled.ood_real=false` held. Held: `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `claims_enabled.positive_system=pending`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS, P3:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE, P3:PHASE_APPROVE}`. P5.1 not started; AssemblyAI cloud baseline awaits APPROVE_PLAN(P5.1) and APPROVE_EXECUTION(P5.1). No code, no test, no Slurm submission, no real-provider call for this update. Only tracker files modified.

## Prior update — P3.2 APPROVE_EXECUTION recorded — `current_task` advanced `P3.2 -> P3_GATE`; `last_completed_task` advanced `P3.1 -> P3.2`; `tasks.P3.2.status=PASS` held; `tasks.P3.2.commit=26db72df3215355a68029927980389216353526e`; `decisions.Decision_A_smoke.outcome=FAIL` held (decided_at_task=P3.2); `state_transport.last_accepted_report_commit` advanced `096fe43 -> 26db72d`; `state_transport.expected_next_task=P3_GATE` held. `latest_approval_packet`=APPROVE_EXECUTION(P3.2) on `26db72df3215355a68029927980389216353526e` (next P3_GATE); `prior_approval_packet_p3_2_plan`=APPROVE_PLAN(P3.2) on `1025a2498d7ea416d475ab23ea80524025e302b7` (next P3_GATE); `prior_approval_packet_p3_2_scope_exec`=APPROVE_EXECUTION(P3.2-scope-change) on `1025a24` (next P3.2); `prior_approval_packet_p3_2_change_scope`=CHANGE_SCOPE(P3.2) on `ee92c8b` (next P3.2). Rationale: P3.2 passed. Decision_A_smoke was mechanically recorded as FAIL with sentinel `OK_LORA_SMOKE_DECISION:FAIL`. Tests passed (12/12 new in tests/robust_asr/test_decide_lora_smoke.py; 109/109 full robust_asr suite), and `OK_REPORT_SHAPE` passed. P3 gate will enact downstream routing: `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `claims_enabled.positive_lora=false`; next post-gate task = P5.1. Held: `current_phase=P3`, `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `claims_enabled.positive_lora=pending` (P3 gate enacts -> false), `lora_status=SMOKE_DONE` (P3 gate enacts -> SKIPPED_BY_DECISION_A), `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE}`. P4 task statuses (`P4.1`, `P4.2`, `P4.3`) are NOT modified by this update; the P3 gate enacts those transitions. P3_GATE not started. No code, no test, no Slurm submission for this update. Only tracker files modified.

## Prior update — P3.2 PASS — Decision_A_smoke recorded as FAIL (mechanical Section 5.1: `macro_wa_gain=-0.12843 < 0.005`, `max_family_wa_gain=-0.11345 < 0.010`, `clean_wa_regression=0.11345 > 0.010` and `> 0.020`, `per_family_wa_gain_variance=1.79e-4` non-degenerate, `export_smoke_result.outcome=PASS` so not HALTED). Sentinel `OK_LORA_SMOKE_DECISION:FAIL`. Deliverables: `scripts/robust_asr/decide_lora_smoke.py`, `tests/robust_asr/test_decide_lora_smoke.py` (12 tests), `reports/robust_asr/lora/lora_smoke_report.md` (first line `FAIL`), `reports/robust_asr/lora/decision_a_smoke.md`, `reports/robust_asr/task_reports/P3.2_decision_a.md`. Verification: `pytest tests/robust_asr/test_decide_lora_smoke.py` 12/12 PASS; CLI on real P3.1 inputs emits `OK_LORA_SMOKE_DECISION:FAIL` and writes `FAIL` first line; full `pytest tests/robust_asr/` 109/109 PASS (was 97 pre-P3.2; +12 new); `validate_report_shape.py` `OK_REPORT_SHAPE`. `tasks.P3.2.status=PASS`; `tasks.P3.2.sentinels=[OK_LORA_SMOKE_DECISION:FAIL]`; `decisions.Decision_A_smoke.outcome=FAIL` (decided_at_task=P3.2); `latest_approval_packet`=APPROVE_PLAN(P3.2) on `1025a2498d7ea416d475ab23ea80524025e302b7` (next P3_GATE); `prior_approval_packet_p3_2_scope_exec`=APPROVE_EXECUTION(P3.2-scope-change) on `1025a24` (next P3.2); `prior_approval_packet_p3_2_change_scope`=CHANGE_SCOPE(P3.2) on `ee92c8b` (next P3.2). `state_transport.expected_next_task=P3_GATE`. Held: `current_phase=P3`, `current_task=P3.2` (held until APPROVE_EXECUTION(P3.2)), `last_completed_task=P3.1`, `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=pending` (P3 gate enacts -> false), `claims_enabled.cloud_tradeoff=true`, `lora_status=SMOKE_DONE` (P3 gate enacts -> SKIPPED_BY_DECISION_A), `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE}`. `state_transport.last_accepted_report_commit=096fe43371f7357007ce41317ed758499d1ff131` STAYS per orchestrator instruction (NOT advanced to the P3.2 implementation commit). P3.2 does NOT enact P4 skips, does NOT transition `lora_status`, does NOT change `claims_enabled.positive_lora`, does NOT clear `BLOCKED_OOD_PUBLIC` — those mutations are enacted at the P3 gate (`PHASE_APPROVE(P3)`): `tasks.P4.1=P4.2=P4.3=SKIPPED_BY_DECISION_A`, `lora_status=SKIPPED_BY_DECISION_A`, `decisions.Decision_B_lora_full.include_lora_in_router=false`, `claims_enabled.positive_lora=false`; next post-gate task = P5.1.

## Prior update — P3.2 CHANGE_SCOPE recorded — touch_policy.md P3.2 row rewritten to authorize `scripts/robust_asr/decide_lora_smoke.py`, `tests/robust_asr/test_decide_lora_smoke.py`, `reports/robust_asr/lora/lora_smoke_report.md`, `reports/robust_asr/lora/decision_a_smoke.md`, `reports/robust_asr/task_reports/P3.2_decision_a.md`, `reports/robust_asr/touch_policy.md` (scope-change rows), and the three live trackers. Readable adds `configs/robust_asr/reuse_policy_v1.yaml`, `reports/robust_asr/lora/lora_smoke_result.json`, `artifacts/robust_asr/lora_smoke/export_smoke_result.json`, `libs/common/{versions,normalization,metrics}.py`, `scripts/robust_asr/validate_report_shape.py`. `latest_approval_packet`=CHANGE_SCOPE(P3.2) on `ee92c8b` (next P3.2); previous APPROVE_EXECUTION(P3.1) demoted to `prior_approval_packet_p3_1_exec` on `096fe43` (next P3.2). `current_task=P3.2` held; `last_completed_task=P3.1` held; `markers=[BLOCKED_OOD_PUBLIC]` held non-blocking; `blocked=false`; `claims_enabled.ood_real=false`; `lora_status=SMOKE_DONE` held; `state_transport.last_accepted_report_commit` STAYS at `096fe43371f7357007ce41317ed758499d1ff131` per orchestrator instruction (NOT advanced to the P3.2 scope-change implementation commit); `state_transport.expected_next_task=P3.2` held; `touch_policy.last_amended_by=P3.2_scope_change`; `artifacts.touch_policy.sha256=52c82b41624861f384c155ee44b6a40d8bc4d0b3a4473083952a6cb0f910d14a` (recorded post-commit `e8d5784`). No script implemented, no test created, no `lora_smoke_report.md` written, no Decision A recorded — this commit is the scope change only. `validate_report_shape.py` PASS. P3.2 implementation (Decision A) awaits orchestrator APPROVE_PLAN(P3.2) and APPROVE_EXECUTION(P3.2).

## Prior update — P3.1 APPROVE_EXECUTION recorded — `current_task` advanced `P3.1 -> P3.2`; `last_completed_task` advanced `P2.2 -> P3.1`; `tasks.P3.1.status=PASS` held; `tasks.P3.1.commit=096fe43371f7357007ce41317ed758499d1ff131`; `state_transport.last_accepted_report_commit` advanced `3ed96f5 -> 096fe43`; `state_transport.expected_next_task=P3.2`. `latest_approval_packet`=APPROVE_EXECUTION(P3.1) on `096fe43371f7357007ce41317ed758499d1ff131` (next P3.2); `prior_approval_packet_p3_1_plan`=APPROVE_PLAN(P3.1) on `3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91` (next P3.2); `prior_approval_packet_p3_1_scope_exec`=APPROVE_EXECUTION(P3.1-scope-change) on `3ed96f5` (next P3.1); `prior_approval_packet_p3_1_change_scope`=CHANGE_SCOPE(P3.1) on `ca98443d380f675eb45666af19d3686f3fbfa54f` (next P3.1). Rationale: P3.1 passed. `OK_LORA_SMOKE_TRAIN steps_completed=200 best_step=100 best_loss=0.5837`, `OK_LORA_SMOKE_EVAL macro_wa_gain=-0.1284 max_family_wa_gain=-0.1135 clean_regression=0.1135`, `OK_LORA_EXPORT_SMOKE`, `OK_REPORT_SHAPE`, and tests (97/97) passed. LoRA smoke completed via Slurm job `2131980` (COMPLETED 0:0, 9m48s on aisurrey03 / RTX 2080 Ti) without `BLOCKED_RUNTIME`, `BUDGET_EXCEEDED`, `DEGENERATE_SMOKE_RESULT`, or `EXPORT_BLOCKED`. P3.2 will make Decision A (mechanical Section 5.1 rule) from the recorded metrics; the predicted outcome is SMOKE_FAIL but P3.1 does NOT record this — P3.2 owns the decision and the Section 5.10 fallback side effects. BLOCKED_OOD_PUBLIC remains active and non-blocking; `claims_enabled.ood_real=false` held. Held: `current_phase=P3`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `lora_status=SMOKE_DONE`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE}`. P3 gate predicate (Section 8 P3) is now half-satisfied on the `tasks.P3.1=PASS` side; the remaining gate prerequisite is `tasks.P3.2` with `Decision_A_smoke.outcome` set. P3.2 not started; awaiting orchestrator `APPROVE_PLAN(P3.2)` before implementation. No code, no test, no Slurm submission for this update. Only tracker files modified.

## Prior update — P3.1 PASS

Updated by: P3.1 PASS — LoRA smoke train + eval + export smoke executed via Slurm job `2131980` (COMPLETED `0:0`, 9m48s on `aisurrey03.surrey.ac.uk`, RTX 2080 Ti, partition `2080ti`, MaxRSS 2,826,500 KiB, container sha256 `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`). All three Section 4.4 sentinels emitted: (1) `OK_LORA_SMOKE_TRAIN steps_completed=200 best_step=100 best_loss=0.5837` — 200 LoRA steps on the 600-row stratified `smoke_split` with on-the-fly degradation; LoRA trainable params 589,824 / 73,183,232 total (0.806%); fp16 + AdamW + warmup_steps=20 + lr=1e-4 + batch_size=8; zero CUDA OOM, zero non-finite loss; 4 checkpoints persisted (step_00050/00100/00150/00200) under `artifacts/robust_asr/lora_smoke/checkpoints/`. (2) `OK_LORA_SMOKE_EVAL macro_wa_gain=-0.1284 max_family_wa_gain=-0.1135 clean_wa_regression=0.1135` — 1000-row eval (200 base × 5 v3.4.7 families) over `degradation_v1_id_eval.parquet ∩ smoke_eval_split`; `per_family_wa_gain_variance=1.79e-4` ⇒ non-degenerate so `lora_smoke_degenerate.md` NOT written; per-family WA gain: clean −0.1135, cafe_noise −0.1455, phone_band −0.1213, far_field_room −0.1436, muffled_lowpass −0.1183. (3) `OK_LORA_EXPORT_SMOKE` — merge_lora_fp16 OK (15.8 s) → ct2_int8_export OK (1.34 s; patched `TransformersConverter.load_model` strips `dtype`/`torch_dtype` kwargs to bridge transformers/ctranslate2 4.7.1 incompatibility, same pattern as `build_whisper_base_ct2_int8.py` for P2.1-model-build) → faster_whisper_transcribe OK (0.76 s; one clean-fixture transcription on `librispeech/dev-clean/1272-128104-0000`, Section 3 decode defaults: `beam_size=1, temperature=0.0, language=en, task=transcribe, condition_on_previous_text=false, without_timestamps=true`). Predicted Decision A (Section 5.1 mechanical, written by P3.2 not P3.1) is **SMOKE_FAIL**: `macro_wa_gain (−0.1284) < 0.005` AND `clean_regression (0.1135) > 0.010` ⇒ NOT SMOKE_PASS; `max_family_wa_gain (−0.1135) < 0.010` ⇒ NOT SMOKE_PARTIAL. Negative gains are consistent with a deliberately tiny smoke recipe (200 steps; training-time families `cafe_background`/`phone_call`/`muffled`/`far_field_room` parameterised differently from the v3.4.7 eval-time families `cafe_noise`/`phone_band`/`muffled_lowpass`/`far_field_room`; fixed LR after warmup); the SMOKE_FAIL trajectory feeds the Section 5.10 fallback: P4 will be `SKIPPED_BY_DECISION_A`, `Decision_B_lora_full.include_lora_in_router=false`, `claims_enabled.positive_lora=false`. Deliverables committed (all small JSON/CSV/PNG/MD/scripts/tests): `artifacts/robust_asr/lora_smoke/checkpoint_manifest.json` (sha256 `21d519a5f24d5bc4a6e1b734966ef5b8eda0c41338ace3c58c6ee202b0201ce2`), `…/training_log.csv` (sha256 `d2fd4dca73e1948dbcdc4285262f921ce507aa0ea7289f24c48debd9f63faea8`), `…/loss_curve.png` (sha256 `3426869e965866c5974659476b9d318ec7e9710221dec4eda545051bd8dab69c`; rendered by the stdlib zlib+struct PNG fallback because the SIF has no matplotlib or PIL), `…/export_smoke_result.json` (sha256 `ca97450a1f901950b4a96ad3d53d97a6bee3b321c7b361a4c3bfe5b94cda33ad`), `reports/robust_asr/lora/lora_smoke_result.json` (sha256 `c5eac79f73d966548562119391837091c490e6d76c29627603563df786e721be`), `reports/robust_asr/task_reports/P3.1_lora_smoke.md`, plus the four new scripts (`scripts/robust_asr/{train_lora_smoke,evaluate_lora_smoke,smoke_export_lora_ct2}.py`), the new Slurm job (`slurm/jobs/p3_1_lora_smoke.sh`), the new test module (`tests/robust_asr/test_lora_smoke.py`), and the `.gitignore` extension for LoRA binary subtrees. Deliverables produced but NOT committed (gitignored per touch_policy): `artifacts/robust_asr/lora_smoke/checkpoints/` (4 adapter dirs, ~9.2 MiB total), `artifacts/robust_asr/lora_smoke/merged_fp16/` (~143 MiB), `artifacts/robust_asr/lora_smoke/ct2_int8/` (~77 MiB model.bin INT8). HF cache staging (no scope change; lives under the pre-authorised model-root cache path read-only): `model.safetensors` sha256 `d4dd5542fd6a1d35639e21384238f3bfe6c557c849d392b5905d33ee29e71db5` and `config.json` sha256 `160c1df40a60d4ef5a6014d536fd845c33aabfd1f318458ac7f87cfe91ebbe76` downloaded once on datamove1 and symlinked into `…/cache/huggingface/hub/models--openai--whisper-base.en/snapshots/911407f4214e0e1d82085af863093ec0b66f9cd6/` alongside the tokenizer/preprocessor files that were already present. Five Slurm iterations were required to reach PASS (jobs 2131879, 2131884, 2131889, 2131891, 2131897, 2131908, 2131980) with iterative fixes for HF offline cache lookup, missing `config.json`, PEFT `task_type` forwarding `input_ids`, `eval_audio_id` key mismatch with baseline parquet, `dtype` kwarg incompatibility, and missing `tokenizer.json` in the merged_fp16 dir; final PASS is on job 2131980. Verifications: `python3 scripts/robust_asr/validate_report_shape.py --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures artifacts/robust_asr/state_packets/report_shape_fixtures` → `OK_REPORT_SHAPE`, exit 0; `python3 -m pytest -q tests/robust_asr/` → **97 passed in 3.51 s** (was 85 pre-P3.1; +9 new `test_lora_smoke.py` tests + 3 conditional tests now active after artifact production). Approvals recorded against acceptance commit `3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91`: `APPROVE_EXECUTION(P3.1-scope-change)` (next P3.1) and `APPROVE_PLAN(P3.1)` (next P3.2). `latest_approval_packet=APPROVE_PLAN(P3.1)` on `3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91` (next P3.2); `prior_approval_packet_p3_1_scope_exec=APPROVE_EXECUTION(P3.1-scope-change)` on `3ed96f5`; `prior_approval_packet_p3_1_change_scope=CHANGE_SCOPE(P3.1)` on `ca98443`; `prior_approval_packet_p2_phase=PHASE_APPROVE(P2)` on `8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd`; `prior_approval_packet=APPROVE_EXECUTION(P2.2)` on `8c37ece`. Tracker mutations: `tasks.P3.1.status=PASS`, `tasks.P3.1.slurm_job_id=2131980`, `tasks.P3.1.next_task=P3.2`, `tasks.P3.1.marker=null`, `tasks.P3.1.artifacts_added.*` populated; `lora_status=NOT_STARTED → SMOKE_DONE`; `artifacts.lora_smoke_*` sha256s populated; `artifacts.lora_smoke_report.produced_by_task` corrected from `P3.1` to `P3.2`. Held: `current_phase=P3`, `current_task=P3.1` (orchestrator finalises via `APPROVE_EXECUTION(P3.1)` before P3.2 may start), `last_completed_task=P2.2`, `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking; NOT cleared), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE}`, `state_transport.last_accepted_report_commit=3ed96f5b8e559dcf9706c1fa6ae4279da56e0d91` (NOT advanced to the P3.1 implementation commit per orchestrator instruction), `state_transport.expected_next_task=P3.2`. P3 gate predicate (Section 8 P3) is now half-satisfied: `tasks.P3.1=PASS`; awaiting orchestrator `APPROVE_EXECUTION(P3.1)` and then P3.2 (Decision A) before `PHASE_APPROVE(P3)` and the P4 / P5 routing.

## Prior update — P3.1 CHANGE_SCOPE

Updated by: P3.1 CHANGE_SCOPE recorded — `reports/robust_asr/touch_policy.md` P3.1 row REWRITTEN to authorize the v3.4.7 P3.1 LoRA smoke train/eval/export task. The stale P3.2-style `reports/robust_asr/lora/lora_smoke_report.md` entry was REMOVED from `allowed_write_paths` and is now listed under `default_no_touch_paths` with the note "owned by P3.2; not written by P3.1". New `allowed_write_paths`: `scripts/robust_asr/train_lora_smoke.py`, `scripts/robust_asr/evaluate_lora_smoke.py`, `scripts/robust_asr/smoke_export_lora_ct2.py`, `slurm/jobs/p3_1_lora_smoke.sh`, `tests/robust_asr/test_lora_smoke.py`, `artifacts/robust_asr/lora_smoke/checkpoint_manifest.json`, `artifacts/robust_asr/lora_smoke/training_log.csv`, `artifacts/robust_asr/lora_smoke/loss_curve.png`, `artifacts/robust_asr/lora_smoke/export_smoke_result.json`, `reports/robust_asr/lora/lora_smoke_result.json`, `reports/robust_asr/lora/lora_smoke_degenerate.md`, `reports/robust_asr/task_reports/P3.1_lora_smoke.md`, `reports/robust_asr/touch_policy.md` (scope-change rows), `docs/progress/robust_asr_progress.yaml`, `docs/progress/robust_asr_progress.md`, `docs/progress/robust_asr_state_capsule.md`. New `allowed_read_paths`: plan files, `configs/robust_asr/{reuse_policy_v1.yaml, lora_smoke.yaml, data_v1.yaml, eval_manifests_v1.yaml, degradation_v1.yaml}`, `libs/common/{eval_schema.yaml, normalization.py, metrics.py, versions.py, runtime_contract.py}`, `libs/audio/**`, `libs/audio_pipeline/**`, `libs/asr_adapter/**`, `artifacts/robust_asr/manifests/{librispeech_lora_train.parquet, librispeech_validation.parquet, degradation_v1_*.parquet}`, `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`, `reports/robust_asr/{baseline_whisper_base.md, manifest_summary.md, degradation_v1_summary.md}`, `scripts/robust_asr/validate_report_shape.py`, `scripts/training/**`, `configs/training/**`. `default_no_touch`: legacy trackers, services/**, infra/**, configs/training/** (write), scripts/training/** (write), libs/audio/** (write), libs/asr_adapter/** (write), libs/audio_pipeline/** (write), libs/common/** (write), libs/observability/** (write), reports/robust_asr/lora/lora_smoke_report.md (P3.2-owned). `mandatory_no_touch`: all Section 2.2 patterns; LoRA adapter binary checkpoints (`*.pt`/`*.pth`/`*.bin`/`*.safetensors`) remain no-touch and never committed; the adapter subtree under `artifacts/robust_asr/lora_smoke/` is gitignored so only small JSON/CSV/PNG/MD metadata land in git. `external_resources`: Slurm submit via `slurm/tools/on_submit.sh` (GPU); robust_asr Apptainer image at `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif` (exec --nv); LibriSpeech and degradation_v1 audio (read-only) under `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/**` and `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**`; `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/whisper_models/whisper_base_en_ct2_int8/` (read-only for export smoke fixture); HF base.en source weights cache (read-only) for LoRA adapter injection. `configs/robust_asr/reuse_policy_v1.yaml` UNCHANGED — every P3.1 write path already lies under a robust_asr-owned reuse-policy row with P3.1 in `allowed_tasks` (scripts/robust_asr/**, artifacts/robust_asr/**, reports/robust_asr/**, tests/robust_asr/**, slurm/jobs/** with p<task>_*.sh basename rule, docs/progress/robust_asr_*); external host paths (SIF, datasets/**, datasets/degradation_v1/**, runtime/whisper_models/**) also list P3.1. New sha256s: `reports/robust_asr/touch_policy.md = 32ad92b1772ba180c7d1b96171c68e08ff81af694cdc2a93343c093ea27eeffc`; `artifacts.touch_policy.last_amended_by=P3.1_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P3.1) on `ca98443d380f675eb45666af19d3686f3fbfa54f` (next P3.1); `prior_approval_packet_p2_phase`=PHASE_APPROVE(P2) on `8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd` (next P3.1); `prior_approval_packet`=APPROVE_EXECUTION(P2.2) on `8c37ece` (next P2_GATE); `prior_approval_packet_p2_2_plan`=APPROVE_PLAN(P2.2) on `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2_GATE). `state_transport.last_accepted_report_commit` STAYS `ca98443d380f675eb45666af19d3686f3fbfa54f` (CHANGE_SCOPE does not advance). `state_transport.expected_next_task=P3.1` held. Required_fix from packet: "Rewrite stale touch_policy P3.1 row for LoRA smoke train/eval/export deliverables." Rationale: P3.1 requires `train_lora_smoke.py`, `evaluate_lora_smoke.py`, `smoke_export_lora_ct2.py`, Slurm job, smoke outputs, and reports, but the current touch_policy P3.1 row still referenced the stale P3.2-style `lora_smoke_report.md`. Held: `current_phase=P3`, `current_task=P3.1`, `last_completed_task=P2.2`, `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE}`. Verification: `python scripts/robust_asr/validate_report_shape.py --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures artifacts/robust_asr/state_packets/report_shape_fixtures` → `OK_REPORT_SHAPE` (exit 0). P3.1 implementation NOT executed: no `train_lora_smoke.py`, no `evaluate_lora_smoke.py`, no `smoke_export_lora_ct2.py`, no `slurm/jobs/p3_1_lora_smoke.sh`, no `tests/robust_asr/test_lora_smoke.py`, no `artifacts/robust_asr/lora_smoke/*` outputs, no `reports/robust_asr/lora/lora_smoke_*` outputs, no `P3.1_lora_smoke.md` task report, no Slurm submission, no Apptainer call, no GPU, no LoRA training, no LoRA inference, no LoRA export, no HuggingFace download, no model bytes written. Awaiting orchestrator `APPROVE_PLAN(P3.1)` before implementation.

## Prior update — P2 PHASE_APPROVE

Updated by: P2 PHASE_APPROVE recorded — `current_phase` advanced `P2 -> P3`; `current_task` advanced `P2_GATE -> P3.1`; `last_completed_task=P2.2` held; `phase_summary.P2=PASS`; `orchestrator_approvals.P2=PHASE_APPROVE`. `state_transport.last_accepted_report_commit` STAYS `8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd` (PHASE_APPROVE accepted on the same commit as the closing APPROVE_EXECUTION(P2.2); not advanced); `state_transport.expected_next_task=P3.1`. `latest_approval_packet`=PHASE_APPROVE(P2) on `8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd` (next P3.1); `prior_approval_packet`=APPROVE_EXECUTION(P2.2) on `8c37ece` (next P2_GATE); `prior_approval_packet_p2_2_plan`=APPROVE_PLAN(P2.2) on `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2_GATE); `prior_approval_packet_p2_2_scope_exec`=APPROVE_EXECUTION(P2.2-scope-change) on `d78678a` (next P2.2); `prior_approval_packet_p2_2_change_scope`=CHANGE_SCOPE(P2.2) on `821893c` (next P2.2). Rationale: P2 phase gate PASS. `tasks.P2.1=PASS`, `tasks.P2.2=PASS`; baseline parquet (`artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`, 53,230 rows, sha256 `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6`), baseline report (`reports/robust_asr/baseline_whisper_base.md`, sha256 `6e5e2f04…ca55e1`), and LoRA smoke config (`configs/robust_asr/lora_smoke.yaml`, sha256 `4d7ae448…e00cff`, 600 lora_train + 200 validation audio_ids verified against the canonical manifests) are present and validated. Sentinels recorded across P2.1/P2.2: `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`, `OK_LORA_SMOKE_CONFIG_PARSE`, `OK_LORA_SMOKE_MANIFEST_REFS`, `OK_LORA_SMOKE_HPARAMS`, `OK_LORA_SMOKE_DECODE_DEFAULTS`, `OK_LORA_SMOKE_TIMEOUTS`, `OK_REPORT_SHAPE`. No blocking markers active; no MISSING_EVIDENCE; no PLAN_CONFLICT. Held: `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking; claims_enabled.ood_real=false), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS, P2:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE, P2:PHASE_APPROVE}`. P3.1 (LoRA smoke train + eval + export smoke) is the next tracker-derived task; not started; awaiting orchestrator `APPROVE_PLAN(P3.1)`. P3.1 requires Slurm GPU submission via `slurm/tools/on_submit.sh` against `slurm/jobs/p3_1_lora_smoke.sh`, Apptainer `--nv` on the robust_asr SIF, and `configs/robust_asr/lora_smoke.yaml`. No code, no test, no Slurm submission for this update. Only tracker files modified.

## Prior update — P2.2 APPROVE_EXECUTION

Updated by: P2.2 APPROVE_EXECUTION recorded — `current_task` advanced `P2.2 -> P2_GATE`; `last_completed_task` advanced `P2.1 -> P2.2`; `tasks.P2.2.status=PASS` held; `tasks.P2.2.commit=8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd`; `state_transport.last_accepted_report_commit` advanced `83dd911 -> 8c37ece`; `state_transport.expected_next_task=P2_GATE`. `latest_approval_packet`=APPROVE_EXECUTION(P2.2) on `8c37ece193d8f24e8416cf7c3a2b59f4f8ef18bd` (next P2_GATE); `prior_approval_packet`=APPROVE_PLAN(P2.2) on `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2_GATE); `prior_approval_packet_p2_2_scope_exec`=APPROVE_EXECUTION(P2.2-scope-change) on `d78678a` (next P2.2); `prior_approval_packet_p2_2_change_scope`=CHANGE_SCOPE(P2.2) on `821893c69eb3e651a94e6bddde49ca5a22be7354` (next P2.2). Rationale: P2.2 passed. `lora_smoke.yaml` was created; `smoke_split` and `smoke_eval_split` reference valid manifest rows (600 audio_ids in `librispeech_lora_train.parquet` across 200 speakers; 200 audio_ids in `librispeech_validation.parquet` across 40 speakers); required hyperparameters (`steps_max=200`, `lora_rank=8`, `lora_alpha=16`, `target_modules=[q_proj,k_proj,v_proj,out_proj]`, `seed=42`), Section 3 eval decode defaults (`task=transcribe`, `language=en`, `condition_on_previous_text=false`, `without_timestamps=true`), and timeouts (`training_timeout_seconds=14400`, `eval_timeout_seconds=1800`) present; `OK_REPORT_SHAPE` passed; 85/85 non-regression tests passed. `BLOCKED_OOD_PUBLIC` remains active and non-blocking; `claims_enabled.ood_real=false` held. Held: `current_phase=P2`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`. P2 gate predicate (Section 8 P2) fully satisfiable: `tasks.P2.1=PASS`, `tasks.P2.2=PASS`, baseline eval table + report exist, `configs/robust_asr/lora_smoke.yaml` exists with valid manifest references, no MISSING_EVIDENCE / PLAN_CONFLICT. P2_GATE not started; awaiting orchestrator `PHASE_APPROVE(P2)` before P3.1 may begin. No code, no test, no Slurm submission for this update. Only tracker files modified.

## Prior update — P2.2 PASS

Updated by: P2.2 PASS — LoRA smoke split config built and committed. `configs/robust_asr/lora_smoke.yaml` written (43,252 bytes; sha256 `4d7ae4489587937e841df9ca172e9b9933e4647ddbe06edf3b00adc713e00cff`). Top-level keys: `version`, `seed`, `manifests`, `smoke_split`, `smoke_eval_split`, `hyperparameters`, `eval_decode_defaults`, `timeouts`. Sampling: deterministic stratified-by-speaker, RNG-free (group by `speaker_id`, sort speakers by integer ID, sort each speaker's utterances by `audio_id`, take the first `per_speaker`). `seed=42` is the canonical P3.1 training/eval seed. `smoke_split`: 600 audio_ids across 200 speakers (3 utt/speaker) from `librispeech_lora_train.parquet` (sha256 `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a`; 22,507 rows total / 200 speakers); total duration 7,647.93 s (2.1244 h). `smoke_eval_split`: 200 audio_ids across 40 speakers (5 utt/speaker) from `librispeech_validation.parquet` (sha256 `977a6f01d72171e9cfb9ce8aee71d4961a99d66397784225c71efbcf1d53733f`; 2,703 rows total / 40 speakers); total duration 1,730.07 s (0.4806 h). Hyperparameters: `steps_max=200`, `learning_rate=1.0e-4`, `batch_size=8`, `lora_rank=8`, `lora_alpha=16`, `lora_dropout=0.05`, `target_modules=[q_proj, k_proj, v_proj, out_proj]`, `seed=42`, `warmup_steps=20`, `optimizer=adamw`, `weight_decay=0.0`, `gradient_accumulation_steps=1`, `fp16=true`. Section 3 eval decode defaults exact: `task=transcribe`, `language=en`, `condition_on_previous_text=false`, `without_timestamps=true`, `beam_size=1`, `temperature=0.0`. Timeouts: `training_timeout_seconds=14400` (4 h), `eval_timeout_seconds=1800` (30 min). Verifications: `OK_LORA_SMOKE_CONFIG_PARSE`, `OK_LORA_SMOKE_MANIFEST_REFS`, `OK_LORA_SMOKE_HPARAMS`, `OK_LORA_SMOKE_DECODE_DEFAULTS`, `OK_LORA_SMOKE_TIMEOUTS`, `OK_REPORT_SHAPE` all exit 0; `python3 -m pytest -q tests/robust_asr/` 85/85 PASS in 2.94 s (non-regression). Approvals accepted: `APPROVE_EXECUTION(P2.2-scope-change)` on `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2.2); `APPROVE_PLAN(P2.2)` on `d78678aa9f7a18ddfd00743789bcf797fb191a98` (next P2_GATE). Tracker mutations: `tasks.P2.2.status=PASS`; `tasks.P2.2.next_task=P2_GATE`; `tasks.P2.2.marker=null`; `tasks.P2.2.artifacts_added.{lora_smoke_config, p2_2_task_report}` populated; `tasks.P2.2.slurm=null`. `latest_approval_packet`=APPROVE_PLAN(P2.2) on `d78678a` (next P2_GATE); `prior_approval_packet`=APPROVE_EXECUTION(P2.2-scope-change) on `d78678a` (next P2.2); `prior_approval_packet_p2_2_change_scope`=CHANGE_SCOPE(P2.2) on `821893c` (next P2.2); `prior_approval_packet_p2_1_exec`=APPROVE_EXECUTION(P2.1) on `83dd911` (next P2.2). Held: `current_phase=P2`, `current_task=P2.2` (orchestrator finalizes via APPROVE_EXECUTION(P2.2) before `P2_GATE` may start), `last_completed_task=P2.1`, `markers=[BLOCKED_OOD_PUBLIC]` (non-blocking; NOT cleared), `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`, `state_transport.last_accepted_report_commit=83dd911bc124a9f1dd53bab17cc4812dbf0cf932` (NOT advanced to the P2.2 commit per orchestrator instruction), `state_transport.expected_next_task=P2_GATE`. P2 gate predicate (Section 8 P2) now fully satisfiable on the artifact side; awaiting orchestrator `APPROVE_EXECUTION(P2.2)` and `PHASE_APPROVE(P2)` before P3.1. No Slurm submission, no Apptainer exec, no GPU, no external API, no model weights, no audio I/O, no `pip install`.

## Prior update — P2.2 CHANGE_SCOPE

Updated by: P2.2 CHANGE_SCOPE recorded — `reports/robust_asr/touch_policy.md` P2.2 row REWRITTEN to authorize the v3.4.7 P2.2 LoRA smoke split config task. New `allowed_write_paths`: `configs/robust_asr/lora_smoke.yaml`, `reports/robust_asr/task_reports/P2.2_lora_smoke_config.md`, `reports/robust_asr/touch_policy.md` (scope-change rows), `docs/progress/robust_asr_progress.yaml`, `docs/progress/robust_asr_progress.md`, `docs/progress/robust_asr_state_capsule.md`. New `allowed_read_paths`: plan files, `configs/robust_asr/data_v1.yaml`, `configs/robust_asr/reuse_policy_v1.yaml`, `libs/common/eval_schema.yaml`, `libs/common/normalization.py`, `libs/common/versions.py`, `artifacts/robust_asr/manifests/librispeech_lora_train.parquet`, `artifacts/robust_asr/manifests/librispeech_validation.parquet`, `reports/robust_asr/manifest_summary.md`, `reports/robust_asr/baseline_whisper_base.md`. `default_no_touch`: legacy trackers, services/**, infra/**, configs/training/**, scripts/training/**, libs/audio/** (write), libs/asr_adapter/** (write), libs/common/** (write), scripts/robust_asr/** (write), slurm/**. `mandatory_no_touch`: all Section 2.2 patterns; `*.wav`/`*.flac`/`*.mp3` under repo root. `external_resources`: none (no Slurm, no Apptainer, no GPU, no external API). `configs/robust_asr/reuse_policy_v1.yaml` UNCHANGED — P2.2 already in `allowed_tasks` for `configs/robust_asr/**` (line 80) and for the `artifacts/robust_asr/**` manifest rows (lines 33, 45, 57, 69); all P2.2 write paths are robust_asr-owned (§2.1). `latest_approval_packet`=CHANGE_SCOPE(P2.2) on `821893c69eb3e651a94e6bddde49ca5a22be7354` (next P2.2); `prior_approval_packet`=APPROVE_EXECUTION(P2.1) on `83dd911bc124a9f1dd53bab17cc4812dbf0cf932` (next P2.2); `prior_approval_packet_p2_1_rerun_plan`=APPROVE_PLAN(P2.1-rerun) on `28dddae0c503208f3042bb5989e2bf3f5798ef56` (next P2.2); `prior_approval_packet_p2_1_model_build_exec`=APPROVE_EXECUTION(P2.1-model-build) on `28dddae` (next P2.1). `state_transport.last_accepted_report_commit` STAYS `83dd911bc124a9f1dd53bab17cc4812dbf0cf932` (CHANGE_SCOPE does not advance). `state_transport.expected_next_task=P2.2` held. Held: `current_phase=P2`, `current_task=P2.2`, `last_completed_task=P2.1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`. Required_fix from packet: "Rewrite stale touch_policy P2.2 row to authorize the LoRA smoke config task." Rationale: P2.2 requires `configs/robust_asr/lora_smoke.yaml` and `P2.2_lora_smoke_config.md`, but the prior touch_policy P2.2 row referred to an old baseline-gate task. Verification: `validate_report_shape.py` -> `OK_REPORT_SHAPE` (exit 0). P2.2 implementation NOT executed: no `configs/robust_asr/lora_smoke.yaml`, no `P2.2_lora_smoke_config.md`, no pytest run, no Slurm submission, no Apptainer, no GPU, no external API. Awaiting orchestrator `APPROVE_PLAN(P2.2)` before implementation.

## Prior update — P2.1 APPROVE_EXECUTION

Updated by: P2.1 APPROVE_EXECUTION recorded — `current_task` advanced `P2.1 -> P2.2`; `last_completed_task` advanced `P1.4 -> P2.1`; `tasks.P2.1.status=PASS` held; `tasks.P2.1.commit=83dd911bc124a9f1dd53bab17cc4812dbf0cf932`; `state_transport.last_accepted_report_commit` advanced `28dddae -> 83dd911`; `state_transport.expected_next_task=P2.2`. `latest_approval_packet`=APPROVE_EXECUTION(P2.1) on `83dd911bc124a9f1dd53bab17cc4812dbf0cf932` (next P2.2); `prior_approval_packet`=APPROVE_PLAN(P2.1-rerun) on `28dddae` (next P2.2); `prior_approval_packet_p2_1_model_build_exec`=APPROVE_EXECUTION(P2.1-model-build) on `28dddae` (next P2.1). Rationale: P2.1 passed after model-build remediation and tracker fix. `whisper_base_ct2_int8` baseline produced 53,230 rows; `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`, `OK_REPORT_SHAPE` emitted; non-regression tests passed (85/85). MISSING_EVIDENCE cleared. BLOCKED_OOD_PUBLIC remains active and non-blocking. Held: `current_phase=P2`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`. P2 gate predicate satisfied on the `tasks.P2.1` side; the remaining gate prerequisite is `tasks.P2.2.status=PASS` plus the `configs/robust_asr/lora_smoke.yaml` deliverable. P2.2 not started; awaiting orchestrator APPROVE_PLAN(P2.2). No code, no test, no Slurm submission for this update.

## Prior update — P2.1 PASS

Updated by: P2.1 PASS — `whisper_base_ct2_int8` baseline evaluation complete on 53,230 rows (5 families × 2 tiers × 5323 source audios) using the CT2 INT8 model produced by P2.1-model-build. Slurm job `2129900` COMPLETED `0:0` in 2 h 40 m 00 s on `aisurrey04` (partition `2080ti`, GPU `--gres=gpu:1`, MaxRSS 811,860 KiB, container sha256 `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`, env-isolated). Sentinels `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE` all emitted. 0 row failures. §5.8 budget 3 h; actual 2 h 40 m (11.1 % margin). Per-family WER/WA (mean over n=10,646): clean 0.0709/0.9367, muffled_lowpass 0.1072/0.9027, cafe_noise 0.1241/0.8784, far_field_room 0.1410/0.8623, phone_band 0.6058/0.6034. `backend_version=faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8`; model.bin sha256 `4ed9e9b5ff94611603854e0abf79badb1d9f3ae3a4b1f3537d93a116e31db33f`; source openai-whisper base.en.pt sha256 `25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead` (canonical); ctranslate2 4.7.1; quantization int8; local_only=true; third_party_provider=null; cost_usd=null; normalization_version=normalization_v1. Deliverables: `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` (53,230 rows; 31 columns; 16,591,882 bytes; sha256 `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6`); `reports/robust_asr/baseline_whisper_base.md` (sha256 `6e5e2f04337c3a0655a37c408c223c6017f5d162adbd3f4eb03b2eb331ca55e1`); `scripts/robust_asr/run_backend_eval.py` (edited; sha256 `36ba31bb696441fb7d605c972358d217450bbbc8d6a1a97ad9eaaca8bb35f873`; prior `56ab650f...fa209d`) — added `eval_audio_id = source_audio_id + '::' + degradation_id` and a transcription cache keyed on audio_sha256. Verifications: `OK_REPORT_SHAPE`, exit 0; `validate_eval_table.py` rows=53230 unique_pk=53230 unique_audio_id=53230 `OK_EVAL_TABLE` exit 0; `pytest -q` 85/85 PASS in 6.88 s. Bug-fix history: attempt 1 (`2129649`) HALTED `13:0` in 14 s (MISSING_EVIDENCE; resolved by P2.1-model-build); attempt 2 (`2129652`) COMPLETED `0:0` in 18 m 32 s with 5,323 rows (clean tier only) due to PK collapse on source-only audio_id (detected post-run; no PASS declared on under-counted parquet); attempt 3 (`2129900`) COMPLETED `0:0` in 2 h 40 m 00 s with full 53,230-row coverage. Approvals recorded: `APPROVE_EXECUTION(P2.1-model-build)` on `28dddae0c503208f3042bb5989e2bf3f5798ef56` (next P2.1); `APPROVE_PLAN(P2.1-rerun)` on `28dddae0c503208f3042bb5989e2bf3f5798ef56` (next P2.2). Tracker mutations: `tasks.P2.1.status=PASS`; `tasks.P2.1.next_task=P2.2`; `tasks.P2.1.marker=null`; `tasks.P2.1.history.{attempt_1_halted_missing_evidence, attempt_2_under_counted}` blocks; `markers=[BLOCKED_OOD_PUBLIC]` (MISSING_EVIDENCE cleared; BLOCKED_OOD_PUBLIC held non-blocking, `claims_enabled.ood_real=false`); `blocked=false`; `blocker=null`. `artifacts.baseline_table.{path, sha256, rows}` and `artifacts.baseline_report.{path, sha256}` populated. New `tasks.P2.1.artifacts_added.{eval_table, baseline_report_full}` entries. `latest_approval_packet`=APPROVE_PLAN(P2.1-rerun) on `28dddae` (next P2.2); `prior_approval_packet`=APPROVE_EXECUTION(P2.1-model-build) on `28dddae` (next P2.1); `prior_approval_packet_p2_1_model_build_plan`=APPROVE_PLAN(P2.1-model-build) on `7253b87`; `prior_approval_packet_p2_1_model_scope_exec`=APPROVE_EXECUTION(P2.1-model-scope-change) on `7253b87`. Held: `current_phase=P2`, `current_task=P2.1` (orchestrator finalizes via APPROVE_EXECUTION before P2.2 may start), `last_completed_task=P1.4`, `claims_enabled.ood_real=false`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`, `state_transport.last_accepted_report_commit=28dddae0c503208f3042bb5989e2bf3f5798ef56` (advanced from `49b4bdc...` by APPROVE_EXECUTION(P2.1-model-build) at commit `28dddae`; the subsequent APPROVE_PLAN(P2.1-rerun) accepts the same commit and does not further advance; the P2.1-rerun implementation commit is NOT recorded as accepted per orchestrator instruction), `state_transport.expected_next_task=P2.1`. P2 gate predicate satisfiable on `tasks.P2.1` side; P2.2 (LoRA smoke split config) is next; P2.2 does not require Slurm.

## Tracker fix — state_transport.last_accepted_report_commit corrected (49b4bdc -> 28dddae)

The P2.1 PASS Execution Report recorded `state_transport.last_accepted_report_commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db` (PHASE_APPROVE(P1) acceptance), but `APPROVE_EXECUTION(P2.1-model-build)` had accepted commit `28dddae0c503208f3042bb5989e2bf3f5798ef56`, which should have advanced the accepted commit at P2.1-rerun acceptance time. `APPROVE_PLAN(P2.1-rerun)` accepts the same commit `28dddae` and does not further advance. Tracker corrected: `state_transport.last_accepted_report_commit` set to `28dddae0c503208f3042bb5989e2bf3f5798ef56`. No code, no test, no task-status change. Held: `current_task=P2.1`, `last_completed_task=P1.4`, `current_phase=P2`, `tasks.P2.1.status=PASS`, `tasks.P2.1.next_task=P2.2`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`, `state_transport.expected_next_task=P2.1`, `latest_approval_packet=APPROVE_PLAN(P2.1-rerun)` on `28dddae`, `prior_approval_packet=APPROVE_EXECUTION(P2.1-model-build)` on `28dddae`.

## Prior update — P2.1-model-build PASS

Updated by: P2.1-model-build PASS — CT2 INT8 weights for whisper_base_ct2_int8 produced under `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/whisper_models/whisper_base_en_ct2_int8/` (12 files; `model.bin` 76,396,161 bytes sha256 `4ed9e9b5ff94611603854e0abf79badb1d9f3ae3a4b1f3537d93a116e31db33f`). Source: `/mnt/.../cache/whisper/base.en.pt` sha256 `25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead` (matches canonical openai-whisper `_MODELS["base.en"]`). Slurm job `2129651` COMPLETED `0:0` in 32 s on `aisurrey04` (partition `2080ti`, MaxRSS 836,324 KiB, container sha256 `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`, env-isolated). Sentinel `OK_CT2_BUILD` emitted. Conversion path: ctranslate2 4.7.1 `TransformersConverter` Python API with a patched `load_model` that strips `dtype`/`torch_dtype` kwargs before `from_pretrained` (works around transformers/ctranslate2 API mismatch where strategies 1 — `OpenAIWhisperConverter` removed in ctranslate2 4.x — and 2 — `ct2-transformers-converter` CLI raising `TypeError: WhisperForConditionalGeneration.__init__() got an unexpected keyword argument 'dtype'` — both fail). Quantization `int8`. `provenance.json` records source path + sha256, output file sha256s, ctranslate2 version, quantization, container sha256, slurm job id, host, three conversion attempts, UTC timestamp. Files committed: `scripts/robust_asr/build_whisper_base_ct2_int8.py` (sha256 `79f29b5c18ba12f5230a31beb07dd58184f80b29b2e60e1b9183a4af5633835e`), `slurm/jobs/p2_1_build_ct2_model.sh` (sha256 `e575f8740d07248b0b8c4c47ac0f612e1281214d4e827537fc2c9ba6859d9e1e`), `reports/robust_asr/whisper_base_ct2_int8_build.md`. Prior attempt: Slurm `2129650` FAILED `1:0` in 31 s (strategies 1+2; strategy 3 not yet implemented at that commit; no partial outputs retained). Approvals recorded: `APPROVE_EXECUTION(P2.1-model-scope-change)` on `7253b878b61c4416f2e1164257e802ca7627a73b` (next P2.1) — model-scope-change rows now binding; `APPROVE_PLAN(P2.1-model-build)` on `7253b878b61c4416f2e1164257e802ca7627a73b` (next P2.1) — build accepted on the model-scope-change commit, `state_transport.last_accepted_report_commit` NOT advanced. Tracker mutations: new `tasks.P2.1.subtasks.P2.1-model-build` block with status PASS, Slurm metadata, history; new `tasks.P2.1.artifacts_added.{build_whisper_base_ct2_int8_script, p2_1_build_ct2_model_slurm_job, whisper_base_ct2_int8_build_report, whisper_base_ct2_int8_model}` entries; `latest_approval_packet`=APPROVE_PLAN(P2.1-model-build) on `7253b87`; `prior_approval_packet`=APPROVE_EXECUTION(P2.1-model-scope-change) on `7253b87`; `prior_approval_packet_p2_1_model_change_scope`=CHANGE_SCOPE(P2.1-model) on `268b8e9`; `prior_approval_packet_p2_1_plan`=APPROVE_PLAN(P2.1) on `def8458`. **Parent task `tasks.P2.1.status` stays `HALTED`** with `marker=MISSING_EVIDENCE` (the build does not by itself satisfy the parent's PASS criteria — the `slurm/jobs/p2_1_baseline.sh` rerun must emit `OK_BACKEND_EVAL`/`OK_BACKEND_SUMMARY`/`OK_EVAL_TABLE`). Held: `current_phase=P2`, `current_task=P2.1` (HALTED), `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` (MISSING_EVIDENCE NOT cleared), `blocked=true`, `claims_enabled.ood_real=false`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`, `state_transport.last_accepted_report_commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db`, `state_transport.expected_next_task=P2.1`. Unblock path for parent P2.1: rerun `slurm/jobs/p2_1_baseline.sh` (no code change required); the probe in `run_backend_eval.py` resolves the new model directory at the primary `candidate_local_paths` slot.

## Prior update — P2.1-model CHANGE_SCOPE

Updated by: P2.1-model CHANGE_SCOPE recorded — `configs/robust_asr/reuse_policy_v1.yaml`, `reports/robust_asr/touch_policy.md`, and `configs/robust_asr/eval_manifests_v1.yaml` amended to authorize offline CT2 INT8 conversion of the local openai-whisper `base.en.pt` checkpoint and a robust_asr-controlled CT2 model output root. Two new reuse_policy override rows: `/mnt/.../cache/whisper/base.en.pt` (`class=data_root`, `permitted_use=read_only`, `allowed_tasks=[P2.1]`, `validator=sha256==25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead`, `checksum_required=true`, `commit_allowed=false`) and `/mnt/.../runtime/whisper_models/**` (`class=model_root`, `permitted_use=read_write`, `allowed_tasks=[P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1]`, `validator=sha256_recorded_in_provenance_json`, `checksum_required=true`, `commit_allowed=false`). Cache root retains its no_touch default for all other paths. `touch_policy.md` P2.1 row extended (additive) with allowed_write_paths `scripts/robust_asr/build_whisper_base_ct2_int8.py`, `slurm/jobs/p2_1_build_ct2_model.sh`, `reports/robust_asr/whisper_base_ct2_int8_build.md`, and external resources (read-only `…/cache/whisper/base.en.pt`; read_write `…/runtime/whisper_models/**`). `eval_manifests_v1.yaml` `backend_endpoints.whisper_base_ct2_int8.candidate_local_paths` reordered: `/mnt/.../runtime/whisper_models/whisper_base_en_ct2_int8` placed first, prior four paths kept as fallbacks. New sha256s: `reuse_policy_v1.yaml=9766167cccd3d246a31adb488d89dcc6950b35c00e0eb5959b523c4c5fa8811b`, `touch_policy.md=e51dc99337cbd22e5f7f359f5ae154e79351b50d58b31d4259242a764dc03db3`, `eval_manifests_v1.yaml=1e371f369b7585099aa3eaaf24202371070eff61d6b7600ccb1158e1e9859130`; reuse_policy and touch_policy `last_amended_by=P2.1_model_scope_change`; `artifacts_added.eval_manifests_v1.last_amended_by=P2.1_model_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P2.1-model) on `268b8e9d0f999bce905a4f2f3652b821ff08a0c3` (next P2.1); `prior_approval_packet`=APPROVE_PLAN(P2.1) on `def8458` (next P2.2); `prior_approval_packet_p2_1_scope_exec`=APPROVE_EXECUTION(P2.1-scope-change) on `def8458` (next P2.1); `prior_approval_packet_p2_1_change_scope`=CHANGE_SCOPE(P2.1) on `22201db` (next P2.1); `prior_approval_packet_p1_phase`=PHASE_APPROVE(P1) on `49b4bdc` (next P2.1). `state_transport.last_accepted_report_commit` STAYS `49b4bdc122b9b9768b380ab9bb9c28bec49455db` (CHANGE_SCOPE does not advance). `state_transport.expected_next_task=P2.1` held. Held: `current_phase=P2`, `current_task=P2.1` (still HALTED), `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` (MISSING_EVIDENCE NOT cleared), `blocked=true`, `claims_enabled.ood_real=false`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`. Verification: `validate_report_shape.py` -> `OK_REPORT_SHAPE` (exit 0). Conversion NOT executed: no `build_whisper_base_ct2_int8.py`, no Slurm build job, no model bytes written, no rerun of `slurm/jobs/p2_1_baseline.sh`, no Apptainer call, no GPU, no external API.

## Prior update — P2.1 HALTED

Updated by: P2.1 HALTED — sentinel `MISSING_EVIDENCE`. CT2 INT8 weights for `whisper_base_ct2_int8` not present at any `candidate_local_paths` declared in `configs/robust_asr/eval_manifests_v1.yaml`; `scripts/robust_asr/run_backend_eval.py` exited 13 before any model load or row evaluation; provenance NOT invented. Slurm job `2129649` FAILED `13:0` in 14 s on `aisurrey04` (partition `2080ti`); container sha256 `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713` matches `tracker.artifacts.runtime_image_v1`. Probed paths: `${ASR_CACHE_ROOT}/whisper_ct2_int8_base_en`, `/mnt/fast/nobackup/scratch4weeks/.../runtime/whisper_models/Systran--faster-whisper-base.en`, `${HF_HOME}/hub/models--Systran--faster-whisper-base.en`, `${ASR_CACHE_ROOT}/huggingface/hub/models--Systran--faster-whisper-base.en`. Host has only openai-whisper `base.en.pt`/`tiny.en.pt` PyTorch checkpoints under `…/cache/whisper/` (not CT2 INT8); HF hub holds only `models--speechbrain--metricgan-plus-voicebank/`. Cache root classified `no_touch` in `reuse_policy_v1.yaml`, so unblock requires CHANGE_SCOPE that names destination host path and provenance source. Implementation deliverables produced and committed: `configs/robust_asr/eval_manifests_v1.yaml` (sha256 `4ed5c802…e86a3b9`), `scripts/robust_asr/run_backend_eval.py` (sha256 `56ab650f…fa209d`), `scripts/robust_asr/summarize_backend_eval.py` (sha256 `97407ff2…6cd3c1`), `scripts/robust_asr/validate_eval_table.py` (sha256 `3b2a6169…d576675`), `slurm/jobs/p2_1_baseline.sh` (sha256 `09f489ef…f36030`), `reports/robust_asr/task_reports/P2.1_baseline.md`. `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`: NOT EMITTED. `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` and `reports/robust_asr/baseline_whisper_base.md`: NOT WRITTEN. Verifications (host): `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0; `pytest -q test_runtime_contract_skeleton.py test_eval_schema.py test_normalization_metrics.py test_leakage.py test_degradation_v1.py` → 85/85 PASS in 2.87 s (non-regression). Approvals recorded: `APPROVE_EXECUTION(P2.1-scope-change)` on `def84589316237a7e2239967ae93448ecacd63a2` (next P2.1) — scope-change rows now binding; `APPROVE_PLAN(P2.1)` on `def84589316237a7e2239967ae93448ecacd63a2` (next P2.2) — implementation accepted on scope-change commit, `state_transport.last_accepted_report_commit` NOT advanced to P2.1 implementation commit per orchestrator instruction. Tracker mutations: `tasks.P2.1.status=HALTED`, `tasks.P2.1.marker=MISSING_EVIDENCE`, `tasks.P2.1.next_task=P2.1` (held); `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]`; `blocked=true`; `blocker` set; `current_task=P2.1` held; `last_completed_task=P1.4` held; `current_phase=P2` held; `state_transport.last_accepted_report_commit` STAYS `49b4bdc122b9b9768b380ab9bb9c28bec49455db`; `state_transport.expected_next_task=P2.1` held; `claims_enabled.ood_real=false` held; `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1` held; `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}` held. `latest_approval_packet`=APPROVE_PLAN(P2.1) on `def8458` (next P2.2); `prior_approval_packet`=APPROVE_EXECUTION(P2.1-scope-change) on `def8458` (next P2.1); `prior_approval_packet_p2_1_change_scope`=CHANGE_SCOPE(P2.1) on `22201db` (next P2.1); `prior_approval_packet_p1_phase`=PHASE_APPROVE(P1) on `49b4bdc` (next P2.1). Unblock path: provide CT2 INT8 weights at one of the declared candidate paths (Systran/faster-whisper-base.en snapshot; converted openai-whisper base.en.pt via ct2-converters; or a vetted internal mirror) under a CHANGE_SCOPE that records the host path and provenance; rerun `slurm/jobs/p2_1_baseline.sh`; no code change required in `run_backend_eval.py`.

## Prior update — P2.1 CHANGE_SCOPE

P2.1 CHANGE_SCOPE recorded — `configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md` amended to authorize P2.1 baseline-eval deliverables. `configs/robust_asr/**` row: P2.1 added to `allowed_tasks` (now `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.4, P2.1]`). `touch_policy.md` P2.1 row REWRITTEN to authorize `configs/robust_asr/eval_manifests_v1.yaml`, `scripts/robust_asr/run_backend_eval.py`, `scripts/robust_asr/summarize_backend_eval.py`, `scripts/robust_asr/validate_eval_table.py`, `slurm/jobs/p2_1_baseline.sh`, `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`, `reports/robust_asr/baseline_whisper_base.md`, `reports/robust_asr/task_reports/P2.1_baseline.md`, scope-change rows on the two policy files, and the three live trackers; reads include `configs/robust_asr/data_v1.yaml`, `configs/robust_asr/degradation_v1.yaml`, `libs/common/eval_schema.yaml`, `libs/common/normalization.py`, `libs/common/metrics.py`, `libs/common/versions.py`, `libs/audio/**`, `libs/asr_adapter/**`, `libs/audio_pipeline/**`, robust_asr public + degradation_v1 manifests; external resources: Slurm submit, Apptainer (exec) on the robust_asr SIF, LibriSpeech and degradation_v1 audio (read-only). New sha256s: `reuse_policy_v1.yaml=678d86a37ae471448736b08a68a9b34802ad6599ea12b08f3a0a33041d2aab6f`, `touch_policy.md=1b38914f1e814619d202a610ba98ca1cc18d404b9d507f5084d5871b2721c0e3`; both `last_amended_by=P2.1_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P2.1) on `22201db1a11586151811f814b14219e099e1a1ed` (next P2.1); `prior_approval_packet`=PHASE_APPROVE(P1) on `49b4bdc` (next P2.1); `prior_approval_packet_p1_gate`=APPROVE_EXECUTION(P1.4) on `49b4bdc` (next P1_GATE); `prior_approval_packet_p1_4_plan`=APPROVE_PLAN(P1.4) on `5c72769`. `state_transport.last_accepted_report_commit` STAYS `49b4bdc122b9b9768b380ab9bb9c28bec49455db` (PHASE_APPROVE(P1) acceptance; CHANGE_SCOPE does not advance). `state_transport.expected_next_task` STAYS `P2.1`. Held: `current_phase=P2`, `current_task=P2.1`, `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`. Verification: `validate_report_shape.py` -> `OK_REPORT_SHAPE` (exit 0). P2.1 implementation NOT executed: no `eval_manifests_v1.yaml`, no `run_backend_eval.py`, no `summarize_backend_eval.py`, no `validate_eval_table.py`, no Slurm job, no eval table, no baseline report, no pytest run, no Apptainer, no GPU, no external API.

## Prior update — P1 PHASE_APPROVE

P1 PHASE_APPROVE recorded — `current_phase` advanced P1 -> P2; `current_task` advanced P1_GATE -> P2.1; `last_completed_task=P1.4` held; `phase_summary.P1=PASS`; `orchestrator_approvals.P1=PHASE_APPROVE`. `state_transport.last_accepted_report_commit` STAYS `49b4bdc122b9b9768b380ab9bb9c28bec49455db` (PHASE_APPROVE accepted on the P1.4 PASS implementation commit; not advanced); `state_transport.expected_next_task=P2.1`. `latest_approval_packet`=PHASE_APPROVE(P1) on `49b4bdc` (next P2.1); `prior_approval_packet`=APPROVE_EXECUTION(P1.4) on `49b4bdc` (next P1_GATE); `prior_approval_packet_p1_4_plan`=APPROVE_PLAN(P1.4) on `5c72769`. P1 gate accepted as PASS_WITH_PREDICATE_NOTE: P1.1=PARTIAL and P1.3=PARTIAL only because OOD-real is unavailable; `BLOCKED_OOD_PUBLIC` active, non-blocking, `claims_enabled.ood_real=false`; P1.2=PASS, P1.4=PASS; required LibriSpeech manifests, eval schema, normalization, metrics, leakage tests, and degradation_v1 artifacts present; no MISSING_EVIDENCE, no PLAN_CONFLICT. Held: `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`. P2.1 not started; awaiting orchestrator APPROVE_PLAN(P2.1) before implementation.

## Prior update — P1.4 APPROVE_EXECUTION

P1.4 APPROVE_EXECUTION recorded — `current_task` advanced P1.4 -> P1_GATE; `last_completed_task` advanced P1.3 -> P1.4; `tasks.P1.4.next_task=P1_GATE`; `tasks.P1.4.commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db`. `state_transport.last_accepted_report_commit` advanced `d230971 -> 49b4bdc`; `state_transport.expected_next_task=P1_GATE`. `latest_approval_packet`=APPROVE_EXECUTION(P1.4) on `49b4bdc` (next P1_GATE); `prior_approval_packet`=APPROVE_PLAN(P1.4) on `5c72769` (next P1_GATE); `prior_approval_packet_p1_4_scope`=APPROVE_EXECUTION(P1.4-scope-change) on `5c72769`. `markers=[BLOCKED_OOD_PUBLIC]` held; `blocked=false` held; `claims_enabled.ood_real=false` held; `degradation_version=degradation_v1` held; `normalization_version=normalization_v1` held; `metrics_version=metrics_v1` held. P1 gate predicate (Section 8 P1) satisfiable: tasks[P1.1=PARTIAL accepted, P1.2=PASS, P1.4=PASS] and tasks[P1.3=PARTIAL accepted]; awaiting orchestrator PHASE_APPROVE(P1) before P2.1 may begin. P1_GATE not yet executed.

## Prior update — P1.4 PASS

P1.4 PASS — degradation_v1 generators and manifests built (5 families x 2 tiers x 5323 LibriSpeech eval rows = 53230 manifest rows; 42584 .wav under scratch). Sentinel `OK_DEGRADATION_V1` emitted by Slurm job `2129647` (COMPLETED 0:0 in 1m03s on aisurrey01, partition 2080ti, MaxRSS 11077812 KiB, container sha256 8db5364c..., env_isolation=PYTHONNOUSERSITE=1+cleared_PYTHONPATH/PYTHONUSERBASE+PIP_USER=0). 0 BAD_OUTPUT across all families/tiers; Section 9 P1.4 Decision rule 1 NOT FIRED. Source = `librispeech_validation` (2703) + `librispeech_locked_test` (2620), 5323 rows total; `lora_train`/`router_train` deliberately excluded. Manifests: `degradation_v1_id_eval.parquet` (26615 rows, sha256 cf0f0bce...) and `degradation_v1_ood_param_eval.parquet` (26615 rows, sha256 30684dc4...) plus 10 per-family per-tier parquets (5323 rows each). Audio under `/mnt/fast/nobackup/scratch4weeks/.../datasets/degradation_v1/<family>/<tier>/<audio_id>.wav` (never committed). Section 5.8 budget: 50 GB scratch / 6h/family; actual 10.297 GB / ~9s per family-tier (4.86x under budget). `libs/audio/degradations.py` extended additively (sample_clean, sample_cafe_noise, sample_phone_band, sample_far_field_room, sample_muffled_lowpass, SAMPLE_FUNCTIONS); existing `apply_degradation`, `DEGRADATION_FAMILIES`, `DEGRADATION_VERSION` value preserved. ID vs OOD-param ranges disjoint per family. Verifications: `OK_DEGRADATION_V1`, 85/85 pytest (test_degradation_v1 + P0.4 contract + P1.2 schema/normalization/leakage non-regression) in 2.59s, `OK_REPORT_SHAPE`. Prior attempt (Slurm 2129646) FAILED 1:0 in 10s on pyarrow OverflowError (uint64 seeds); fixed by masking to 63 bits (1<<63)-1; determinism preserved. `tasks.P1.4.status=PASS`, `tasks.P1.4.next_task=P1_GATE`, `tasks.P1.4.marker=BLOCKED_OOD_PUBLIC`. `degradation_version=degradation_v1`. `current_task=P1.4` (held); `last_completed_task=P1.3` (held); `markers=[BLOCKED_OOD_PUBLIC]` (held); `blocked=false`; `claims_enabled.ood_real=false`. `state_transport.last_accepted_report_commit` STAYS `d230971e8995484449095ae914b58c47c4d43b94` per orchestrator instruction (not advanced to P1.4 commit). `state_transport.expected_next_task=P1.4` (held). `latest_approval_packet`=APPROVE_PLAN(P1.4) on `5c72769d1cdf6f7aa7e789a02c2f05aa69284341` (next P1_GATE); `prior_approval_packet`=APPROVE_EXECUTION(P1.4-scope-change) on `5c72769`; `prior_approval_packet_p1_3`=CHANGE_SCOPE(P1.4) on `d230971`; `prior_approval_packet_p1_3a`=APPROVE_EXECUTION(P1.3) on `d230971`. P1 gate predicate (Section 8 P1) now satisfiable: tasks[P1.1=PARTIAL, P1.2=PASS, P1.4=PASS] and tasks[P1.3=PARTIAL]; awaiting orchestrator APPROVE_EXECUTION(P1.4) and PHASE_APPROVE(P1).

## Prior update — P1.4 scope-change

`configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md` amended to authorize additive P1.4 degradation_v1 work. NEW reuse_policy override row for `libs/audio/degradations.py` (class=existing_runtime_code, permitted_use=append_functions_only, allowed_tasks=[P1.4], validator=tests/robust_asr/test_degradation_v1.py, commit_allowed=true) authorizes the five Section 3 `sample_<family>` additions; preserves `apply_degradation`, `DEGRADATION_FAMILIES`, and the `DEGRADATION_VERSION` value. `slurm/jobs/**` and `/mnt/.../runtime/robust_asr_py311_cuda12.sif` rows: P1.4 added to allowed_tasks. `/mnt/.../asr_enhancement_training/datasets/**` row: P1.4 added (read_only for source LibriSpeech). NEW override row for `/mnt/.../asr_enhancement_training/datasets/degradation_v1/**` (read_write, [P1.4, P2.1, P3.1, P4.1, P4.2, P4.3, P8.1], large_artifact, never committed) for degraded audio outputs. `touch_policy.md` P1.4 row REWRITTEN to authorize the v3.4.7 deliverables (libs/audio/degradations.py append-only narrow patch, configs/robust_asr/degradation_v1.yaml, scripts/robust_asr/build_degradation_v1.py, slurm/jobs/p1_4_build_degradation_v1.sh, tests/robust_asr/test_degradation_v1.py, artifacts/robust_asr/manifests/degradation_v1_*.parquet, reports/robust_asr/degradation_v1_summary.md, reports/robust_asr/task_reports/P1.4_degradation_v1.md, scope-change rows on policy files, three live trackers). New sha256s: reuse_policy_v1.yaml=`f0528f7d4d14638b3cfdc4ede17c25c347cd3b838e844399fdfaf36464d81757`, touch_policy.md=`ede82ac0889628c87eab523d9fbd238995f2b041272004a835931ca5fb501f66`; both `last_amended_by=P1.4_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P1.4) on `d230971e8995484449095ae914b58c47c4d43b94` (next P1.4); `prior_approval_packet`=APPROVE_EXECUTION(P1.3) on `d230971e8995484449095ae914b58c47c4d43b94` (next P1.4); `prior_approval_packet_00`=APPROVE_PLAN(P1.3) on `7579602`; `prior_approval_packet_001`=APPROVE_EXECUTION(P1.3-scope-change) on `7579602`. `state_transport.last_accepted_report_commit` advanced `b049f94 -> d230971` per APPROVE_EXECUTION(P1.3); CHANGE_SCOPE does not further advance. `state_transport.expected_next_task=P1.4`. Held: `current_task=P1.4`, `last_completed_task=P1.3`, `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `claims_enabled.ood_real=false`. Verification: `validate_report_shape.py` -> `OK_REPORT_SHAPE` (exit 0). P1.4 implementation NOT executed: no degradations.py patch, no degradation_v1.yaml, no build_degradation_v1.py, no Slurm job, no manifests, no test file, no pytest run, no Apptainer, no GPU, no external API.
Date: 2026-05-08

## Branch

branch: feature/robust-asr-lora-router-datamove1-v1
HEAD: recorded_in_execution_report
pushed_to_origin: true

## Current state

current_phase: P2
current_task: P2.1
last_completed_task: P1.4
blocked: false
blocker: null
active_markers: [BLOCKED_OOD_PUBLIC]
claims_enabled.ood_real: false
normalization_version: normalization_v1
metrics_version: metrics_v1
degradation_version: degradation_v1

## Latest reports

latest_execution_report: reports/robust_asr/task_reports/P1.2_eval_schema.md
latest_planning_report: reports/robust_asr/task_reports/P1.2_eval_schema.md
latest_phase_gate_report: null
latest_approval_packet: ORCHESTRATOR_DECISION scope=task task=P1.2 phase=P1 decision=APPROVE_PLAN accepted_report_commit=8185501 next_expected_task=P1.3 (P1.2 plan accepted on the scope-change commit; implement eval schema, normalization, metrics, validator, three pytest files; do not advance last_accepted_report_commit)
prior_approval_packet: ORCHESTRATOR_DECISION scope=task task=P1.2-scope-change phase=P1 decision=APPROVE_EXECUTION accepted_report_commit=8185501 next_expected_task=P1.2 (P1.2 scope-change accepted; reuse_policy_v1.yaml libs/common/** override rows and rewritten touch_policy P1.2 row are now binding)
last_accepted_report_commit: 8185501955f5bb5ecf44c926fcabdc8f27ae2af9   # advanced from 587b7483 by APPROVE_EXECUTION(P1.2-scope-change) at commit 8185501; APPROVE_PLAN(P1.2) does not further advance the accepted commit

## Key artifacts created in P0.2

- reports/robust_asr/asset_inventory.md
- reports/robust_asr/repo_integration_policy.md
- reports/robust_asr/touch_policy.md
- configs/robust_asr/reuse_policy_v1.yaml (55 rows, 5 classes)
- scripts/robust_asr/validate_report_shape.py (emits OK_REPORT_SHAPE)
- artifacts/robust_asr/state_packets/report_shape_fixtures/ (6 fixtures)

## P0.3 scope change (no P0.3 execution)

- configs/robust_asr/reuse_policy_v1.yaml amended:
  - Apptainer image row: class=container_image, permitted_use=exec_only,
    allowed_tasks=[P0.3, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1],
    validator=sha256_recorded_in_runtime_smoke_job_metadata,
    checksum_required=true, large_artifact=true, commit_allowed=false.
  - slurm/jobs/** row: permitted_use=read_only_with_robust_asr_writes,
    allowed_tasks=[P0.3, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1],
    validator=file_basename_matches_p<task_id>_*.sh, commit_allowed=true.
- Tracker: latest_approval_packet replaced with the CHANGE_SCOPE packet.
- Tracker: last_accepted_report_commit set to 635a711... (P0.2 acceptance).
- Tracker: artifacts.reuse_policy_config.sha256 updated.
- current_task remains P0.3; last_completed_task remains P0.2;
  expected_next_task remains P0.3.
- P0.3 runtime smoke NOT executed; no Slurm submission.

## P0.3 PASS (closed via P0.3-rerun-2; BLOCKED_RUNTIME cleared)

- Slurm job 2129641 against new SIF with env-isolated apptainer exec:
  COMPLETED 0:0 in 15 s on aisurrey01.
- Container Python 3.11.15. All 11 imports OK at SIF-pinned versions:
  torch 2.5.1+cu121, transformers 4.49.0, peft 0.19.1, ctranslate2 4.7.1,
  faster_whisper 1.2.1, librosa 0.11.0, numpy 1.26.4, pandas 3.0.2,
  pyarrow 24.0.0, yaml 6.0.3, pytest 9.0.3.
- router_pick=lightgbm; ROUTER_IMPL_FALLBACK_SKLEARN not active.
- OK_RUNTIME_SMOKE emitted; env_isolation in metadata.
- Image sha256 8db5364c... matches tracker.artifacts.runtime_image_v1;
  SIF unmodified; legacy SIF mtime preserved.
- Tracker: tasks.P0.3.status=PASS; tasks['P0.3-rerun-2']=PASS;
  blocked=false; markers=[]; current_task=P0.4;
  last_completed_task=P0.3; expected_next_task=P0.4;
  last_accepted_report_commit STAYS efed06e (env-isolation
  scope-change acceptance; not advanced to rerun-2 commit).

## P0.3-rerun HALTED (historical — user-site shadowing)

- Slurm job 2129640 against new image: FAILED 1:0 in 10 s on aisurrey01.
- Container Python 3.11.15 OK; ctranslate2/faster_whisper/pytest/lightgbm OK.
- transformers/peft FAIL — shadowed transformers ≥4.50 + tokenizers 0.21.4 incompatibility.
- Root cause: auto-bound /mnt/fast/nobackup exposes user-site
  /mnt/fast/nobackup/users/gb0048/.local/lib/python3.11/site-packages
  and python_userbase/ shadow the SIF dist-packages. SIF itself is
  correct (build log 2129639 confirms torch 2.5.1+cu121, transformers
  4.49.0, tokenizers 0.21.4, numpy 1.26.4).
- Fix: --env PYTHONNOUSERSITE=1 (+ clear PYTHONUSERBASE/PYTHONPATH) on
  apptainer exec in slurm/jobs/p0_3_runtime_smoke.sh. CHANGE_SCOPE
  required.
- Tracker: tasks['P0.3-rerun']=HALTED added. tasks.P0.3.status STAYS HALTED.
  current_task STAYS P0.3, last_completed_task STAYS P0.2,
  blocked STAYS true, markers STAYS [BLOCKED_RUNTIME].
  state_transport.last_accepted_report_commit advanced to 805cddf...
  (P0.3-rebuild APPROVE_EXECUTION); NOT advanced to the rerun commit.
  expected_next_task rolled back to P0.3 (rerun-2 still parent of P0.3).

## P0.3-rebuild PASS (BLOCKED_RUNTIME still active; awaiting rerun)

- Slurm job 2129639 (attempt 2 after recipe quoting fix) COMPLETED 0:0
  in 8 min 39 s on aisurrey01 via `apptainer build --fakeroot`.
- New robust_asr Apptainer image at the authorized path:
  - path: /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif
  - sha256: 8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713
  - size_bytes: 5624180736
  - recipe: configs/robust_asr/runtime/apptainer_robust_asr_v1.def
    sha256 e6e7f79bae25e8f6bf3726ab8024a75f4769ad0825eddc15f8b1e50ae377f63e
  - base: docker://nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
  - inside-container Python 3.11.15; recipe %test PASS
    (torch 2.5.1+cu121, transformers 4.46+, peft, ctranslate2,
     faster_whisper, librosa 0.11.0, numpy 1.26.x, pandas, pyarrow,
     pyyaml 6.0.3, pytest 9.0.3, lightgbm, xgboost, scipy, scikit-learn,
     soundfile, jiwer)
- Legacy SIF /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
  untouched (mtime preserved).
- Tracker: tasks["P0.3-rebuild"]=PASS, artifacts.runtime_image_v1
  populated, tasks.P0.3.next_task=P0.3-rerun. BLOCKED_RUNTIME stays
  active. current_task stays P0.3, last_completed_task stays P0.2,
  state_transport.last_accepted_report_commit stays 635a711...

## P0.3 scope change Option A (no execution; HALTED state preserved)

- configs/robust_asr/reuse_policy_v1.yaml amended:
  - NEW data_root row: /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/**
    (permitted_use=read_write, allowed_tasks=[P0.3], commit_allowed=false).
  - NEW container_image row: /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif
    (permitted_use=exec_only, allowed_tasks=[P0.3, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1],
    validator=sha256_recorded_in_runtime_smoke_job_metadata,
    checksum_required=true, large_artifact=true, commit_allowed=false).
  - Legacy image row /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif: UNCHANGED.
- reports/robust_asr/touch_policy.md P0.3 row extended with runtime
  remediation write paths (recipe .def, build script, rebuild reports,
  optional build job script, slurm/jobs/p0_3_runtime_smoke.sh repoint).
- Tracker: artifact sha256s for reuse_policy_config and touch_policy
  updated to new values; latest_approval_packet replaced with this
  CHANGE_SCOPE packet.
- No image built. No P0.3 execution. tasks.P0.3.status remains HALTED,
  marker remains BLOCKED_RUNTIME, current_task remains P0.3,
  last_completed_task remains P0.2, last_accepted_report_commit remains
  635a711cd4fe44e919966a0e6bc3df99103fe6d3.

## P0.3 first attempt (HALTED, BLOCKED_RUNTIME)

- Slurm job 2129637 (partition 2080ti, host aisurrey01.surrey.ac.uk).
- Apptainer image sha256 dade8295... — exec authorized by amended
  reuse_policy_v1.yaml (class=container_image, exec_only).
- Container Python 3.10.13 (Decision rule 2 requires 3.11) — HALTED.
- Missing imports: ctranslate2, faster_whisper, pytest (Decision rule 4) — HALTED.
- Router fallback to sklearn HistGradientBoostingRegressor (informational
  only; superseded by HALTED).
- Evidence: reports/robust_asr/runtime_smoke.md,
  reports/robust_asr/task_reports/P0.3_runtime_smoke.md,
  artifacts/robust_asr/runtime_smoke/{runtime_smoke_job_metadata.json,stdout.txt,stderr.txt}.
- Tracker mutations: tasks.P0.3.status=HALTED, marker=BLOCKED_RUNTIME,
  blocked=true. current_task and last_completed_task UNCHANGED.
  state_transport.last_accepted_report_commit UNCHANGED at 635a711...
- Clear path: rebuild Apptainer image with Python 3.11 + missing
  packages; rerun slurm/jobs/p0_3_runtime_smoke.sh. If new image lives
  at a different host path, a CHANGE_SCOPE Approval Packet is required
  to amend the reuse_policy_v1.yaml row.

## P0.4 PASS (runtime contract skeleton)

- Slurm CPU job 2129642 on aisurrey01 (partition 2080ti) COMPLETED 0:0
  in 5 s, MaxRSS 3872 KiB. Env isolation: PYTHONNOUSERSITE=1, cleared
  PYTHONPATH/PYTHONUSERBASE, PIP_USER=0. Container sha256 8db5364c...
  matches tracker.artifacts.runtime_image_v1.
- Validator (`scripts/robust_asr/validate_runtime_contract.py`,
  `--strict-skeleton`) emitted `OK_CONTRACT_SKELETON`; all 19/19
  assertions PASS on `rp5_request_fixture.json` /
  `rp5_response_fixture.json`.
- Unit tests (`tests/robust_asr/test_runtime_contract_skeleton.py`):
  20/20 passing in 1.06 s inside the SIF (skeleton-fixtures-pass +
  per-assertion mutations A01..A19).
- Schema module `libs/common/runtime_contract.py` (JSON Schema 2020-12
  draft request/response schemas + pure-stdlib assertion runner; no
  jsonschema runtime dependency required).
- Scope-change at commit 22b685a authorized
  `libs/common/runtime_contract.py` (reuse_policy row,
  class=robust_asr_owned_extension, commit_allowed=true,
  allowed_tasks=[P0.4, P9.0]) and added validator/tests/Slurm-job paths
  to the touch_policy P0.4 row.
- Tracker: tasks.P0.4.status=PASS;
  artifacts.runtime_contract_fixture.path=
  reports/robust_asr/runtime_contract_smoke.md;
  contract_skeleton_validation_passed=true;
  contract_final_validation_passed=false (finalized in P9.0).
  current_task=P0.5; last_completed_task=P0.4; blocked=false; markers=[].
  state_transport.expected_next_task=P0.4 (held until orchestrator
  reviews P0.4 Execution Report);
  state_transport.last_accepted_report_commit STAYS 0b47b76e
  (P0.3-rerun-2 acceptance; NOT advanced to P0.4 commit per
  orchestrator instruction).

## P0.5 PASS (model card and router card templates)

- Template-only task. No Slurm, no Apptainer, no GPU, no external API,
  no scope change.
- `docs/reports/robust_asr/model_card_lora.md`: 9 sections
  (intended_use, training_data, hyperparameters, evaluation_data,
  metrics, fairness_and_limitations, risks, license, contact);
  30 `TODO_FILLED_IN_<task_id>` placeholders (≥ 10 required);
  sha256 `6f1a6ba8194149271d9091f96b17fe79e81c201613003f7e78842e0343585104`.
- `docs/reports/robust_asr/router_card.md`: 9 sections
  (intended_use, inputs, decision_rule, training_data, evaluation,
  fallbacks, risks, license, contact);
  24 `TODO_FILLED_IN_<task_id>` placeholders (≥ 8 required);
  sha256 `bc5dd87db91ac9371e05e838b56f32cb6dfa2a421ed0f3fbe91f99a7ff640bb4`.
- `scripts/robust_asr/validate_report_shape.py` still emits `OK_REPORT_SHAPE`.
- Tracker: `tasks.P0.5.status=PASS`; `current_task=P1.1`;
  `last_completed_task=P0.5`; `markers=[]`; `blocked=false`.
  `state_transport.last_accepted_report_commit` advanced from
  `0b47b76e` to `40406fc31ad167500bf8ce317286f5c2b5eeb96f`
  (P0.4 acceptance; not advanced to the P0.5 commit per orchestrator
  instruction). `state_transport.expected_next_task=P0.5` (held until
  orchestrator reviews the P0.5 Execution Report).

## P0 phase gate (PHASE_APPROVE)

- ORCHESTRATOR_DECISION: scope=phase phase=P0 decision=PHASE_APPROVE
  accepted_report_commit=`d0ba20c532477a94f359b55c03dc6c835529c1fa`
  next_expected_task=P1.1.
- Rationale: P0 phase gate PASS. P0.0..P0.5 PASS; required artifacts
  and sentinels present (OK_REPORT_SHAPE, BUILD_OK_8db5364c,
  OK_APPTAINER_INSPECT, OK_RUNTIME_SMOKE, OK_CONTRACT_SKELETON,
  OK_CARD_TEMPLATES); runtime smoke and contract skeleton passed;
  model/router card placeholder counts (30, 24) exceed minima
  (10, 8); no blockers or active markers.
- Tracker mutations: `phase_summary.P0=PASS`;
  `orchestrator_approvals.P0=PHASE_APPROVE`;
  `state_transport.last_accepted_report_commit` advanced
  `40406fc3` → `d0ba20c5`;
  `state_transport.expected_next_task=P1.1`.
- Held: `current_task=P1.1`, `last_completed_task=P0.5`,
  `blocked=false`, `markers=[]`.

## P1.1 scope change (no inventory; read-only authorization for dataset roots)

- configs/robust_asr/reuse_policy_v1.yaml amended:
  - Existing data_root row /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**:
    P1.1 added to allowed_tasks
    (now [P1.1, P1.2, P1.3, P2.1, P3.1, P4.1, P4.2, P4.3, P8.1]).
  - NEW data_root row /mnt/fast/nobackup/scratch4weeks/gb0048/sources/**:
    permitted_use=read_only, allowed_tasks=[P1.1, P1.2, P1.3, P2.1, P3.1, P4.1, P4.2, P4.3, P8.1],
    validator=none, checksum_required=false, large_artifact=true,
    commit_allowed=false. Authorizes inventory of LibriSpeech, Common
    Voice, TED-LIUM, CHiME public dataset source roots on host.
- reports/robust_asr/touch_policy.md P1.1 row rewritten to authorize:
  configs/robust_asr/data_v1.yaml, reports/robust_asr/data_inventory.md,
  reports/robust_asr/task_reports/P1.1_data_inventory.md,
  scripts/robust_asr/check_speaker_disjoint.py, scope-change rows on
  reuse_policy_v1.yaml/touch_policy.md, the three live trackers.
  Read-only inventory authorized on …/sources/** and
  …/asr_enhancement_training/datasets/**.
- Tracker mutations:
  - latest_approval_packet replaced with the P1.1 CHANGE_SCOPE packet
    (prior P0 PHASE_APPROVE packet shifted to prior_approval_packet).
  - artifacts.reuse_policy_config.sha256 →
    16f2b5f682055f6863e5e68a396dded32e6b8346af08efb2243d147b2664f406,
    last_amended_by=P1.1_scope_change.
  - artifacts.touch_policy.sha256 →
    7a0b85d6257d03d3ca322160c0080d2c6c91f5a90222114d3ad768af324ff16c,
    last_amended_by=P1.1_scope_change.
  - state_transport.last_accepted_report_commit STAYS
    3129c11edd5105d7c247b48eb1a170d7c1507cde (P0 phase-gate acceptance).
  - state_transport.expected_next_task STAYS P1.1.
- Held: current_task=P1.1, last_completed_task=P0.5, blocked=false,
  markers=[], project_status=IN_PROGRESS, phase_summary.P0=PASS,
  orchestrator_approvals.P0=PHASE_APPROVE.
- P1.1 inventory NOT executed; no data_v1.yaml authored; no
  data_inventory.md authored; no Slurm; no Apptainer; no GPU; no
  external API.

## P1.1 EXECUTION (rerun) — PARTIAL + BLOCKED_OOD_PUBLIC

- Operator restored LibriSpeech audio at the canonical root via `wget`
  + `tar -xzf` of `train-clean-100.tar.gz` and `test-clean.tar.gz` from
  `https://www.openslr.org/resources/12/` (gzip integrity OK; tar exit
  codes 0). `train-clean-360` not restored at this rerun (P1.1 does not
  require it).
- Post-restore inventory:
  - `train-clean-100`: 251 spk, 28 539 `.flac`, 585 `.trans.txt`,
    ~102.30 h, 6.3 GiB.
  - `dev-clean`: 40 spk, 2 703 `.flac`, 97 `.trans.txt`, 5.388 h,
    349 MiB.
  - `test-clean`: 40 spk, 2 620 `.flac`, 87 `.trans.txt`, ~5.47 h,
    356 MiB.
- Cross-split speaker overlap within LibriSpeech: zero
  (train∩dev=∅, train∩test=∅, dev∩test=∅).
- Deterministic split partition (recorded in `configs/robust_asr/data_v1.yaml`):
  - `lora_train`: 200 train-clean-100 speakers (the 200 not selected by every-5th).
  - `router_train`: 51 train-clean-100 speakers (every 5th in sorted ID order).
  - `validation`: 40 dev-clean speakers.
  - `locked_test`: 40 test-clean speakers.
  - `ood_real_locked`, `common_voice_demo_reserved`: empty (BLOCKED_OOD_PUBLIC).
- OOD-real probe unchanged: Common Voice EN `clips/` empty with no
  `.tsv` transcripts; TED-LIUM R3 and CHiME-6 absent.
- Verifications: `OK_DATA_V1_CONFIG`, `OK_SPEAKER_DISJOINT` (non-trivial,
  four non-empty splits), `OK_REPORT_SHAPE`. No Slurm, no Apptainer, no
  GPU, no external API.
- Decision rule 1 (LibriSpeech missing → HALTED) cleared. Decision
  rule 2 / Section 1.1 rule 4 (no OOD-real fallback → PARTIAL,
  `BLOCKED_OOD_PUBLIC`, `claims_enabled.ood_real=false`) operative.
- Tracker mutations: `tasks.P1.1.status=PARTIAL`,
  `tasks.P1.1.marker=BLOCKED_OOD_PUBLIC`,
  `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real` flipped `true → false`,
  `current_task=P1.1` (held), `last_completed_task=P0.5` (held),
  `state_transport.last_accepted_report_commit` STAYS
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the rerun commit per orchestrator instruction.
  Approval-packet chain unchanged.
- `tasks.P1.1.history.attempt_1` records the prior HALTED state at
  commit `1470ebc1da1a1cc70fdf9965480a070a0c248e4d`.

## P1.1 EXECUTION attempt 1 (HALTED — MISSING_EVIDENCE; cleared by operator restore)

- Inventoried dataset roots on host. Findings:
  - LibriSpeech `dev-clean`: 40 speakers, 2703 `.flac`, ~5.388 h, 349 MiB
    on disk — populated.
  - LibriSpeech `train-clean-100`: 251 speaker dirs, **0 `.flac`**, 0
    bytes — skeleton only.
  - LibriSpeech `train-clean-360`: subset directory **absent** on host.
  - LibriSpeech `test-clean`: 40 speaker dirs, **0 `.flac`**, 0 bytes
    — skeleton only.
  - Common Voice EN cv-corpus-24.0-2025-12-05: `clips/` empty, no `.tsv`
    transcripts.
  - TED-LIUM Release 3, CHiME-6: absent on `/mnt/fast/nobackup`.
- Files written:
  - `configs/robust_asr/data_v1.yaml` — six canonical splits, declared
    roots, OOD-real preference order, provisional dev-clean speaker
    partition (sourced from
    `datasets/splits/devclean_speaker_split_v1/{train,val}_speakers.txt`).
  - `reports/robust_asr/data_inventory.md` — per-dataset inventory and
    HALT rationale.
  - `scripts/robust_asr/check_speaker_disjoint.py` — pure-Python
    speaker-disjoint check; emits `OK_SPEAKER_DISJOINT`.
  - `reports/robust_asr/task_reports/P1.1_data_inventory.md` — execution
    report.
- Verifications: `OK_DATA_V1_CONFIG`, `OK_SPEAKER_DISJOINT` (trivial — 3
  of 4 splits empty), `OK_REPORT_SHAPE`. No Slurm, no Apptainer, no GPU,
  no external API.
- Decision rule 1 of P1.1 fires: LibriSpeech (partially) missing →
  HALTED + `MISSING_EVIDENCE`. Decision rule 2 / Section 1.1 rule 4 also
  triggers (no Section 1.1 OOD-real source resolves) but is superseded
  by the LibriSpeech HALT. `data_v1.yaml.ood_real.blocked=true` records
  the OOD-real status; `claims_enabled.ood_real` is NOT flipped at this
  report and awaits orchestrator instruction with HALT resolution.
- Tracker: `tasks.P1.1.status=HALTED`, `markers=[MISSING_EVIDENCE]`,
  `blocked=true`, `current_task=P1.1` (held), `last_completed_task=P0.5`
  (held), `state_transport.last_accepted_report_commit` STAYS
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the P1.1 commit per orchestrator instruction.
- Approval-packet chain on tracker:
  `latest_approval_packet`=APPROVE_PLAN(P1.1) on `e4a5677…` (next P1.2);
  `prior_approval_packet`=APPROVE_EXECUTION(P1.1-scope-change) on
  `e4a5677…` (next P1.1);
  `prior_approval_packet_2`=CHANGE_SCOPE(P1.1) on `3129c11e…` (next P1.1);
  `prior_approval_packet_3`=PHASE_APPROVE(P0) on `d0ba20c5…` (next P1.1).

## Unblock path

Restore LibriSpeech audio under
`/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech/`:
fetch `train-clean-100.tar.gz`, `test-clean.tar.gz` (and optionally
`train-clean-360.tar.gz`) from `openslr.org/12` and extract in place.
Then rerun P1.1 (no scope change required) — the inventory invariant is
rechecked and the HALT clears once `lora_train`, `router_train`,
`locked_test` resolve to non-empty file lists.

For OOD-real, separately populate Common Voice clips + transcripts
under the existing CV root or stage TED-LIUM R3 / CHiME-6 dev under a
new root; either path requires a new CHANGE_SCOPE if a new host root is
introduced.

## P1.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P1.1 phase=P1
  decision=APPROVE_EXECUTION
  accepted_report_commit=`587b7483a6d37a24e0cf31549d449427c4708234`
  next_expected_task=P1.2.
- Rationale: LibriSpeech inventory usable after operator restore;
  required splits non-empty and speaker-disjoint; OOD-real remains
  unavailable so PARTIAL with `BLOCKED_OOD_PUBLIC` and
  `claims_enabled.ood_real=false` accepted.
- Tracker: `current_phase=P1`, `current_task=P1.2`,
  `last_completed_task=P1.1`, `markers=[BLOCKED_OOD_PUBLIC]` held,
  `blocked=false` held, `claims_enabled.ood_real=false` held,
  `state_transport.last_accepted_report_commit` advanced
  `3129c11e -> 587b7483`,
  `state_transport.expected_next_task=P1.2`,
  `tasks.P1.1.next_task=P1.2`.

## P1.2 scope change (no P1.2 implementation; libs/common/** writes authorized)

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.2 phase=P1
  decision=CHANGE_SCOPE accepted_report_commit=`1ecbaa447e380d5ed3637e80b679bcc83ae77c17`
  next_expected_task=P1.2.
- Required fix: Authorize P1.2 writes under `libs/common/**` and
  update the stale touch_policy P1.2 row from the old manifests scope
  to eval schema / normalization / metrics / leakage tests.
- `configs/robust_asr/reuse_policy_v1.yaml` amended with four new
  rows (libs/common/eval_schema.yaml, libs/common/normalization.py,
  libs/common/metrics.py, libs/common/versions.py). New sha256:
  `c2999d597c1e35ecf1340e8dace4e3eaca0640a30fd2d802f1f26a34df853905`.
- `reports/robust_asr/touch_policy.md` P1.2 row rewritten to authorize
  the v3.4.7 P1.2 deliverables (eval_schema.yaml, normalization.py,
  metrics.py, versions.py append, validate_eval_schema.py, three test
  files, P1.2 task report) plus scope-change rows on policy files and
  the three live trackers. New sha256:
  `f09f4006ff0a6acfd2b296a974bd7ea49ab7e6288a77440a5a06d6e779204c01`.
- Tracker mutations: `latest_approval_packet` replaced with the P1.2
  CHANGE_SCOPE packet (prior P1.1 APPROVE_EXECUTION shifted to
  `prior_approval_packet`); `artifacts.reuse_policy_config.sha256` and
  `artifacts.touch_policy.sha256` updated; both `last_amended_by` set
  to `P1.2_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS `587b7483…`
  (P1.1 APPROVE_EXECUTION acceptance; CHANGE_SCOPE does not advance).
  Note: subsequently advanced to `8185501…` by
  APPROVE_EXECUTION(P1.2-scope-change); see "Tracker fix" section
  below.
- Held: `current_task=P1.2`, `last_completed_task=P1.1`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `phase_summary.P0=PASS`,
  `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.2 implementation NOT executed: no eval_schema.yaml, no
  normalization.py, no metrics.py, no versions.py mutation, no
  validator script, no tests, no pytest run, no Slurm, no Apptainer,
  no GPU, no external API.
- Non-regression: `validate_report_shape.py` against the canonical
  fixtures emitted `OK_REPORT_SHAPE`.

## P1.2 PASS — eval schema, normalization, metrics, leakage tests

- ORCHESTRATOR_DECISIONs: APPROVE_EXECUTION(P1.2-scope-change) and
  APPROVE_PLAN(P1.2), both on
  `accepted_report_commit=8185501955f5bb5ecf44c926fcabdc8f27ae2af9`.
  APPROVE_EXECUTION(P1.2-scope-change) sets `next_expected_task=P1.2`;
  APPROVE_PLAN(P1.2) sets `next_expected_task=P1.3`.
- Deliverables (sha256 in tracker yaml `artifacts.*`):
  - `libs/common/eval_schema.yaml` (31 columns; schema_version
    `eval_schema_v1`; backend_names + degradation_families + primary
    key + per-column type/required/description records + Section 3
    schema-tests rule register).
  - `libs/common/normalization.py` (`NORMALIZATION_VERSION` imported
    from versions.py; NFKC → lowercase → keep `[a-z0-9 ]` → collapse
    whitespace → strip; idempotent).
  - `libs/common/metrics.py` (`wer`, `cer`, `wa`,
    `paired_bootstrap_ci`, `paired_bootstrap_ci_delta`; pure stdlib;
    deterministic given seed).
  - `libs/common/versions.py` updated to append
    `NORMALIZATION_VERSION = "normalization_v1"`. Existing constants
    (`METRICS_VERSION`, `DEGRADATION_VERSION`, `ENHANCER_VERSION`)
    preserved.
  - `scripts/robust_asr/validate_eval_schema.py` (Section 4.1
    contract; emits `OK_EVAL_SCHEMA` or
    `FAIL_EVAL_SCHEMA: <reason>`; exit 0/1).
  - `tests/robust_asr/test_eval_schema.py` (positive + negative tests
    for Section 3 rules 1–7).
  - `tests/robust_asr/test_normalization_metrics.py` (idempotence,
    NFKC, WER/CER/WA correctness on hand-checked inputs, paired
    bootstrap CI determinism + bracket containment).
  - `tests/robust_asr/test_leakage.py` (5 named tests; speaker tests
    on real `data_v1.yaml` partition; audio_id / demo / OOD tests on
    placeholder fixtures with SKIP_OOD_PUBLIC_DEFERRED notes for
    empty splits).
  - `reports/robust_asr/task_reports/P1.2_eval_schema.md`.
- Verifications (all on host Python; no SIF, no Slurm, no GPU, no
  external API):
  - `pytest -q tests/robust_asr/test_eval_schema.py
    tests/robust_asr/test_normalization_metrics.py
    tests/robust_asr/test_leakage.py` → 41/41 PASS in 0.21 s.
  - `validate_eval_schema.py` → `OK_EVAL_SCHEMA`, exit 0.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `pytest -q tests/robust_asr/test_runtime_contract_skeleton.py` →
    20/20 PASS (P0.4 non-regression).
- Plan-text inconsistency (reported, not deviated): Section 3 header
  says "Columns (28):" but enumerates 31 column names. The 31 names
  are encoded verbatim; the validator checks set equality with the
  Section 3 list, not the header count.
- BLOCKED_OOD_PUBLIC handling: leakage tests 4 and 5 honor
  `claims_enabled.ood_real=false` by treating empty splits as
  trivially disjoint and writing `SKIP_OOD_PUBLIC_DEFERRED` notes
  under `reports/robust_asr/leakage/`. Notes must be removed by the
  unblocking task once Common Voice and OOD-real are populated.
- Tracker mutations: `tasks.P1.2.status=PASS`,
  `tasks.P1.2.next_task=P1.3`, `current_task=P1.3`,
  `last_completed_task=P1.2`, `markers=[BLOCKED_OOD_PUBLIC]` held,
  `blocked=false` held, `claims_enabled.ood_real=false` held,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1` held,
  `state_transport.last_accepted_report_commit` recorded as `587b7483…`
  at P1.2 PASS commit time, then corrected to
  `8185501955f5bb5ecf44c926fcabdc8f27ae2af9` by the subsequent tracker
  fix (APPROVE_EXECUTION(P1.2-scope-change) accepted commit). See
  "Tracker fix" section below.
  `state_transport.expected_next_task=P1.3`,
  `latest_approval_packet`=APPROVE_PLAN(P1.2) on `8185501…`,
  `prior_approval_packet`=APPROVE_EXECUTION(P1.2-scope-change) on
  `8185501…`.

## Tracker fix — state_transport.last_accepted_report_commit advanced

- The P1.2 PASS Execution Report wrote
  `state_transport.last_accepted_report_commit=587b7483…`,
  but `APPROVE_EXECUTION(P1.2-scope-change)` had accepted
  commit `8185501955f5bb5ecf44c926fcabdc8f27ae2af9`, which should
  have advanced the accepted commit at P1.2 commit time.
- Tracker corrected: `state_transport.last_accepted_report_commit`
  set to `8185501955f5bb5ecf44c926fcabdc8f27ae2af9`. No code, no
  test, no task-status change. P1.2 PASS state held.
- Held: `current_task=P1.3`, `last_completed_task=P1.2`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `tasks.P1.2.status=PASS`,
  `state_transport.expected_next_task=P1.3`,
  `latest_approval_packet`=APPROVE_PLAN(P1.2) on `8185501…`,
  `prior_approval_packet`=APPROVE_EXECUTION(P1.2-scope-change) on
  `8185501…`.

## Next expected Claude prompt

Task: P1.3 — Public manifests for LoRA / router / validation /
locked test / OOD / demo reserved.
Phase: P1
Preconditions: P0 PHASE_APPROVE; P1.1 PARTIAL APPROVE_EXECUTION;
P1.2 PASS APPROVE_PLAN recorded; libs/common eval schema /
normalization / metrics in place at `normalization_v1` /
`metrics_v1`; data_v1.yaml partition usable.
current_task == P1.3; last_completed_task == P1.2;
markers=[BLOCKED_OOD_PUBLIC]; blocked=false;
claims_enabled.ood_real=false.
Mode: await ORCHESTRATOR_DECISION APPROVE_EXECUTION(P1.2)
followed by APPROVE_PLAN(P1.3); do not start P1.3 implementation
until both packets are recorded.

Next session: read docs/progress/robust_asr_progress.yaml, confirm
current_task=P1.3, last_completed_task=P1.2, current_phase=P1,
markers=[BLOCKED_OOD_PUBLIC], blocked=false,
latest_approval_packet=APPROVE_PLAN(P1.2) on 8185501,
state_transport.last_accepted_report_commit=8185501 (advanced by
APPROVE_EXECUTION(P1.2-scope-change)),
then await APPROVE_EXECUTION(P1.2) followed by APPROVE_PLAN(P1.3).
