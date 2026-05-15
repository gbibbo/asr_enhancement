# Scope-Change Report — `reuse_policy_p10_3_script_allowance`

CHANGE_SCOPE applied

## scope_change_id

`reuse_policy_p10_3_script_allowance`

## Phase / Task

- phase: P10
- task_id: `reuse_policy_p10_3_script_allowance` (administrative policy fix; not a plan task)
- branch: `feature/robust-asr-lora-router-datamove1-v1`
- accepted_report_commit (planning_report anchor): `9f8e4c3687a8f449945e7e1f2d76fd19c082ce29`

## Issue

The active agent plan §4305 (P10.3 Action 1) requires P10.3 to run `verify_plan_tracker_consistency.py`, and §1057–§1103 defines its normative contract. However:

1. `scripts/robust_asr/verify_plan_tracker_consistency.py` does **not** exist on disk.
2. `configs/robust_asr/reuse_policy_v1.yaml` row `scripts/robust_asr/**` `allowed_tasks` did not include `P10.3` (last entry was `P10.2`).
3. `reports/robust_asr/touch_policy.md` P10.3 row `allowed_write_paths` did not list `scripts/robust_asr/verify_plan_tracker_consistency.py`.

Without this fix, the P10.3 implementation would write the script under an unauthorized task, in violation of the reuse policy and the touch policy. This is the direct analogue of the prior `CHANGE_SCOPE(reuse_policy_p10_2_script_allowance)` that authorized P10.2 to create `scripts/robust_asr/final_asset_audit.py`.

## Reason P10.3 needs this

P10.3 (Plan-tracker consistency, agent plan §4298–§4327) mandates running `verify_plan_tracker_consistency.py` per §4305 + §4316–§4320 verbatim:

```
python scripts/robust_asr/verify_plan_tracker_consistency.py \
  --plan-orchestrator docs/plans/robust_asr_orchestrator_plan_v3_4_7.md \
  --plan-agent        docs/plans/robust_asr_agent_plan_v3_4_7.md \
  --tracker           docs/progress/robust_asr_progress.yaml \
  --out               reports/robust_asr/plan_tracker_consistency.md
```

The script's contract (§1057–§1103) defines 17 binding assertions (A01–A17) and the `OK_PLAN_TRACKER_CONSISTENCY` stdout sentinel. P10.3 cannot proceed without the script. This scope-change is the minimum-necessary policy amendment that unblocks the implementation step without weakening any other rule.

## Exact reuse_policy row changed

- file: `configs/robust_asr/reuse_policy_v1.yaml`
- path: `scripts/robust_asr/**`
- row class: `active_state` (unchanged)
- permitted_use: `read_write` (unchanged)
- validator: `none` (unchanged)
- checksum_required: `false` (unchanged)
- large_artifact: `false` (unchanged)
- commit_allowed: `true` (unchanged)
- notes: annotated to record the `reuse_policy_p10_3_script_allowance` CHANGE_SCOPE id, the `9f8e4c36…` accepted_report_commit, and the §4305 + §1057–§1103 plan references; prior `reuse_policy_p10_2_script_allowance` annotation preserved verbatim.

### Before / after `allowed_tasks` for `scripts/robust_asr/**`

- allowed_tasks_before (20 entries):
  ```
  [P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1,
   P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2,
   P10.2]
  ```
- allowed_tasks_after (21 entries):
  ```
  [P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1,
   P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2,
   P10.2, P10.3]
  ```
- added: `P10.3`
- removed: none
- net: `+P10.3` only

### Reuse-policy file sha256

- before: `c9e187ecbdc24ba0503753934f32bf4bb08df0a4f5ca049b9200299fca851876`
- after:  `18905cd932a8a90199859e6f5cebc5f596177de5f5f2a2a5052e9972bc8e9037`
- `artifacts.reuse_policy_config.last_amended_by`: `model_router_card_completion → reuse_policy_p10_3_script_allowance`
- `artifacts.reuse_policy_config.prior_sha256`: `c9e187ec…`
- `artifacts.reuse_policy_config.sha256_history`: extended with the five-entry chain `[P0.2 (initial) → P8.2_scope_change → reuse_policy_p10_2_script_allowance → model_router_card_completion → reuse_policy_p10_3_script_allowance]`.

## Exact touch_policy row changed

- file: `reports/robust_asr/touch_policy.md`
- row: P10.3 (line 43)
- allowed_read_paths: unchanged (`All robust_asr artifacts (read), legacy trackers (read), legacy plans (read), plan files (read)`)
- default_no_touch_paths: unchanged (`none`)
- external_paths_requiring_approval: unchanged (`All mandatory no-touch patterns`)
- column 5 (notes): unchanged (`none`)

### Before / after P10.3 `allowed_write_paths`

- before (5 entries):
  ```
  reports/robust_asr/plan_tracker_consistency.md,
  reports/robust_asr/task_reports/P10.3_consistency.md,
  docs/progress/robust_asr_progress.yaml,
  docs/progress/robust_asr_progress.md,
  docs/progress/robust_asr_state_capsule.md
  ```
- after (6 entries):
  ```
  scripts/robust_asr/verify_plan_tracker_consistency.py,
  reports/robust_asr/plan_tracker_consistency.md,
  reports/robust_asr/task_reports/P10.3_consistency.md,
  docs/progress/robust_asr_progress.yaml,
  docs/progress/robust_asr_progress.md,
  docs/progress/robust_asr_state_capsule.md
  ```
- added: `scripts/robust_asr/verify_plan_tracker_consistency.py`
- removed: none
- renamed: none (`P10.3_consistency.md` filename preserved exactly)
- net: `+scripts/robust_asr/verify_plan_tracker_consistency.py` only

### Touch-policy file sha256

- before: `33243a494e3865dc7519008e75687bfcb232c27a5ec3dfd7cc6a8a00de0e80d7`
- after:  `c19c3e9c4256dc3645223a6affa5516da565ffdf1d7ccd62a961b22a2105702a`
- `artifacts.touch_policy.last_amended_by`: `P8.2_provenance_scope_change → reuse_policy_p10_3_script_allowance`
- `artifacts.touch_policy.prior_sha256`: `33243a49…`
- `artifacts.touch_policy.sha256_history`: initialized with the three-entry chain `[P0.2 (initial) → P8.2_provenance_scope_change → reuse_policy_p10_3_script_allowance]`.

## Tracker state preserved

Held (no changes by this scope-change commit):

- `project_status`: `IN_PROGRESS`
- `current_phase`: `P10`
- `current_task`: `P10.3`
- `last_completed_task`: `P10.2`
- `state_transport.expected_next_task`: `P10.3`
- `state_transport.last_accepted_report_commit`: `8ce525c896845ce79fc9bad96167448b77ab75f9`
- `state_transport.latest_approval_packet`: `APPROVE_EXECUTION(P10.2)` on `8ce525c896845ce79fc9bad96167448b77ab75f9` (held; **not** displaced by this scope-change packet, matching the FIX_BEFORE_CLOSE / scope-change precedent at `CHANGE_SCOPE(reuse_policy_p10_2_script_allowance)`, `CHANGE_SCOPE(model_router_card_completion)`, P9.2 strict-tag-validator-fix, and P8.2-deviation enactment)
- `state_transport.prior_approval_packet_p10_2_plan`: `APPROVE_PLAN(P10.2)` on `693b7498…` (held)
- `state_transport.prior_approval_packet_p10_1_exec`: `APPROVE_EXECUTION(P10.1)` on `37a588b6…` (held)
- `state_transport.prior_approval_packet_p10_1_plan`: `APPROVE_PLAN(P10.1)` on `d08dfa8…` (held)
- `state_transport.prior_approval_packet_p9_gate_phase_approve`: `PHASE_APPROVE(P9)` on `a3c7d37…` (held)
- All other prior approval packets held in their slots
- `phase_summary.{P0..P3, P5..P9}`: `PASS`
- `phase_summary.P4`: `null`
- `phase_summary.P10`: `null`
- `orchestrator_approvals.{P0..P3, P5..P9}`: `PHASE_APPROVE`
- `orchestrator_approvals.P4`: `null`
- `orchestrator_approvals.P10`: `null`
- `tasks.P10.1.status`: `PASS`
- `tasks.P10.2.status`: `PASS`
- `tasks.P10.3`: **not added** (deferred to P10.3 implementation under `APPROVE_PLAN(P10.3)`)
- `markers`: `[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]` (none cleared, none added)
- `OUTCOME_E_NARROWED_SCOPE`: held on `tasks.P8.1` / `decisions.Decision_D_positive_system`
- `claims_enabled.ood_real`: `false`
- `claims_enabled.cloud_tradeoff`: `false`
- `claims_enabled.positive_lora`: `false`
- `claims_enabled.positive_system`: `false`
- `proposed_deviations.P8_2_demo_only_upstream_overlap.status`: `ENACTED`
- `decisions.Decision_D_positive_system.outcome`: `false`
- `decisions.Decision_B_lora_full.include_lora_in_router`: `false`
- `lora_status`: `SKIPPED_BY_DECISION_A`
- `router_status`: `SELECTOR_PACKAGED`
- `system_status`: `NOT_STARTED`
- `blocked`: `false`
- `blocker`: `null`
- C4 disclosure status: `COMPLETED_IN_P9_1` (handoff README §6.4, byte-unchanged at sha256 `36f3c610…`)
- C5 exclusion verification status: `COMPLETED_AND_PASS` (P10.1 final_verification.md byte-unchanged at sha256 `82ad07ec…`; demo_examples_manifest.json sha256 `850c02db…` held)
- Handoff tag `handoff/20260514-64eba43`: unchanged on local and on origin (target `64eba4345f3207af38f0fba8ac2c43c6084e8852`); no retag, no new tag

Recorded by this scope-change commit:

- `state_transport.latest_scope_change_packet`: `CHANGE_SCOPE(reuse_policy_p10_3_script_allowance)` on `9f8e4c3687a8f449945e7e1f2d76fd19c082ce29`, with full ORCHESTRATOR_DECISION block + `reuse_policy_row_changed=scripts/robust_asr/**` + `allowed_tasks_before/after` + `reuse_policy_sha256_before/after` + `touch_policy_row_changed=P10.3` + `touch_policy_paths_before/after` + `touch_policy_sha256_before/after` + `latest_approval_packet_held` + `held_after_scope_change` block
- `state_transport.prior_scope_change_packet_model_router_card_completion`: previous `CHANGE_SCOPE(model_router_card_completion)` on `d714bac8…` (demoted; full record preserved including `cards_changed` block)
- `state_transport.prior_scope_change_packet_reuse_policy_p10_2_script_allowance`: held in its slot (unchanged from the previous demotion)

## Forbidden paths unchanged

Verified unchanged (no edits, no deletions, no rename):

- `docs/plans/**` (orchestrator plan, agent plan, schemas)
- `docs/plans/training_datamove1_plan.md` (still absent; not restored)
- `docs/progress/training_datamove1_progress.yaml`
- `docs/progress/training_datamove1_progress.md`
- `docs/claude_task_progress.md`
- `docs/claude_task_progress.yaml`
- `plan.md`
- `CLAUDE.md` (including the BEGIN/END ROBUST_ASR_PROFILE block body)
- `docs/profiles/CLAUDE.robust_asr.md`
- `.gitattributes`
- `artifacts/robust_asr/handoff/**` (README sha256 `36f3c610…`, rp5_runtime_spec.md sha256 `bbcf912d…`)
- `artifacts/robust_asr/runtime_contract/**`
- `artifacts/robust_asr/demo/**` (demo_examples_manifest.json sha256 `850c02db…` held; 8 WAVs byte-unchanged)
- `artifacts/robust_asr/eval_tables/**` (whisper_base_ct2_int8.parquet sha256 `0dc98736…`)
- `artifacts/robust_asr/router/**` (selector_evidence.parquet sha256 `c450a91a…`; selected_router/** byte-unchanged)
- `artifacts/robust_asr/oracle/**`
- `artifacts/robust_asr/manifests/**`
- `artifacts/robust_asr/lora_smoke/**`
- `artifacts/robust_asr/state_packets/report_shape_fixtures/**`
- `docs/reports/robust_asr/model_card_lora.md` (sha256 `01fec571…`)
- `docs/reports/robust_asr/router_card.md` (sha256 `2587f536…`)
- `reports/robust_asr/final_verification.md` (sha256 `82ad07ec…`)
- `reports/robust_asr/final_asset_audit.md` (sha256 `5ca0f4f7…`)
- `reports/robust_asr/task_reports/P10.1_final_verification.md`
- `reports/robust_asr/task_reports/P10.2_final_audit.md`
- `reports/robust_asr/task_reports/model_router_card_completion.md`
- `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md`
- All other prior task reports under `reports/robust_asr/task_reports/`
- `reports/robust_asr/baseline_whisper_base.md`, `asset_inventory.md`, `repo_integration_policy.md`, `data_inventory.md`, `manifest_summary.md`, `degradation_v1_summary.md`, `runtime_smoke.md`, `runtime_image_rebuild.md`, `runtime_contract_smoke.md`, `whisper_base_ct2_int8_build.md`, `repository_inventory.md`
- `reports/robust_asr/lora/**`, `reports/robust_asr/router/**`, `reports/robust_asr/system/**`, `reports/robust_asr/leakage/**`, `reports/robust_asr/demo/**`
- `scripts/robust_asr/**` (every script byte-unchanged; `scripts/robust_asr/final_asset_audit.py` sha256 `75538228…` held; `scripts/robust_asr/verify_plan_tracker_consistency.py` **still absent**)
- `tests/**`
- `libs/**`
- All `configs/robust_asr/*.yaml` other than `reuse_policy_v1.yaml`
- `refs/tags/handoff/20260514-64eba43` (still pointing at `64eba4345f3207af38f0fba8ac2c43c6084e8852` locally and on origin)

## Files modified on this commit

Only six files modified, all explicitly authorized by this scope-change:

1. `configs/robust_asr/reuse_policy_v1.yaml`
2. `reports/robust_asr/touch_policy.md`
3. `reports/robust_asr/task_reports/reuse_policy_p10_3_script_allowance.md` (new)
4. `docs/progress/robust_asr_progress.yaml`
5. `docs/progress/robust_asr_progress.md`
6. `docs/progress/robust_asr_state_capsule.md`

No code in `scripts/robust_asr/` (the script write is **deferred** to P10.3 implementation). No test, no plan file, no demo asset, no handoff asset, no runtime-contract asset, no eval/router/oracle parquet, no model card, no router card, no prior report touched.

## Validation observed at this commit

- `python3 -c "import yaml; yaml.safe_load(open('configs/robust_asr/reuse_policy_v1.yaml')); yaml.safe_load(open('docs/progress/robust_asr_progress.yaml')); print('OK_YAML_PARSE')"` → **`OK_YAML_PARSE`** (exit 0)
- P10.3 present in `scripts/robust_asr/**` `allowed_tasks`: **YES**
- `reports/robust_asr/touch_policy.md` P10.3 row includes `scripts/robust_asr/verify_plan_tracker_consistency.py`: **YES**
- `test -e scripts/robust_asr/verify_plan_tracker_consistency.py`: **absent** (still not created; deferred)
- `test -e reports/robust_asr/plan_tracker_consistency.md`: **absent** (still not created; deferred)

## Next legal action

Orchestrator returns `APPROVE_PLAN(P10.3)`. Under that approval, the P10.3 implementation may then:

1. Create `scripts/robust_asr/verify_plan_tracker_consistency.py` per agent plan §1057–§1103 contract verbatim.
2. Run the validator with the four `--plan-orchestrator` / `--plan-agent` / `--tracker` / `--out` arguments per §4316–§4320.
3. Write `reports/robust_asr/plan_tracker_consistency.md`.
4. Write `reports/robust_asr/task_reports/P10.3_consistency.md`.
5. Update `docs/progress/robust_asr_progress.{yaml,md}` and `docs/progress/robust_asr_state_capsule.md` per the established acceptance pattern (hold `current_task=P10.3`, `last_completed_task=P10.2`, `state_transport.expected_next_task=P10.3`, `project_status=IN_PROGRESS`, `phase_summary.P10=null`, `orchestrator_approvals.P10=null`; advance only on subsequent `APPROVE_EXECUTION(P10.3)`).
6. Commit (author Gabriel Bibbó <gabobibbo@gmail.com>; no AI-authorship trailers) and push to `origin feature/robust-asr-lora-router-datamove1-v1`.

Until `APPROVE_PLAN(P10.3)` is recorded, P10.3 must not start. `project_status = COMPLETE` and the P10 gate remain deferred until P10.3 PASS plus `APPROVE_EXECUTION(P10.3)` plus the subsequent P10_GATE PASS / `PHASE_APPROVE(P10)`.

## Author

Gabriel Bibbó <gabobibbo@gmail.com>. No `Co-Authored-By`, `Generated-By`, AI-authorship, or `Signed-off-by` trailer.
