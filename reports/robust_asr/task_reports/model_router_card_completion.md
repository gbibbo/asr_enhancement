# Scope-change report — `model_router_card_completion`

PASS

## Scope-change identity

- `scope_change_id`: `model_router_card_completion`
- `phase`: `P10`
- `decision`: `CHANGE_SCOPE`
- `accepted_report_commit` (orchestrator packet): `d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d`
- `next_expected_task`: `P10.2`
- `branch`: `feature/robust-asr-lora-router-datamove1-v1`
- `head_before` (this commit): `d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d`
- `git_status_before`: clean (0 lines)
- `author`: Gabriel Bibbó <gabobibbo@gmail.com>; no `Co-Authored-By`, `Generated-By`, AI-authorship, or `Signed-off-by` trailer.

## Issue

The active agent plan (`docs/plans/robust_asr_agent_plan_v3_4_7.md`) Section 10 final-verification checklist items 11–12 (§4355–§4358) require:

- "docs/reports/robust_asr/model_card_lora.md exists; no residual TODO_FILLED_IN_<task_id> for closed tasks."
- "docs/reports/robust_asr/router_card.md exists; no residual TODO_FILLED_IN_<task_id> for closed tasks."

Section 4.1 §1105–§1119 defines `final_asset_audit.py` Assertion 3: "No residual TODO_FILLED_IN_<task_id> tokens for tasks whose tracker.tasks[<task_id>].status == PASS." Decision Rule 1 (§4288): "Residual TODO_FILLED_IN_<task_id> for closed task: status = FAIL, return to that task to fill the placeholder."

Both cards are active final assets (NOT template-only references): they are referenced by `artifacts/robust_asr/runtime_contract/final_response_fixture.json` lines 24–25 (`report_links.model_card` / `report_links.router_card`), validated by `validate_runtime_contract.py --strict-final` A19 (already PASS in P10.1), and named in handoff README §4 (lines 109–110) and §8 (lines 268–270). The reuse-policy row `docs/reports/robust_asr/**` (line 168–176) classifies them as `class=active_state`.

Pre-amendment, the cards contained 30 (model card) + 24 (router card) = 54 `TODO_FILLED_IN_<task_id>` tokens, of which a strict count of ≥ 18 occurrences targeted PASS-status tasks (P1.2, P1.4, P2.1, P3.1, P3.2, P6.1, P7.3, P8.1, P8.2, P9.1) and would trigger Decision Rule 1 FAIL when P10.2 final_asset_audit.py runs.

## Why the cards are active final assets

Five independent evidence trails confirm the cards are active final assets, not templates:

1. `artifacts/robust_asr/runtime_contract/final_response_fixture.json` lines 24–25: `report_links.model_card = "docs/reports/robust_asr/model_card_lora.md"`, `report_links.router_card = "docs/reports/robust_asr/router_card.md"`.
2. `artifacts/robust_asr/runtime_contract/final_response_schema.json` line 105 declares `required: ["model_card", "router_card"]` under `report_links`; line 5 description: "report_links.model_card and report_links.router_card must be non-empty strings in --strict-final".
3. `validate_runtime_contract.py --strict-final` A19 PASS (per P10.1 final_verification.md and tasks.P9_GATE evidence): "A19 PASS: strict_final: model_card='docs/reports/robust_asr/model_card_lora.md' router_card='docs/reports/robust_asr/router_card.md'".
4. `artifacts/robust_asr/handoff/README.md` §4 lines 109–110 and §8 lines 268–270 reference both card paths as live final assets.
5. Agent plan Section 10 items 11–12 §4355–§4358 normatively require absence of residual `TODO_FILLED_IN_<task_id>` for closed tasks in BOTH cards as a pre-COMPLETE condition.

The reuse-policy row line 168–176 already classifies `docs/reports/robust_asr/**` as `class=active_state, permitted_use=read_write`; the historical "templates" wording in the notes line refers to P0.5 seeding, not to operational classification.

## Reuse policy row changed

File: `configs/robust_asr/reuse_policy_v1.yaml`

Row: `docs/reports/robust_asr/**` (lines 168–177 post-amendment).

### Before

```yaml
- path: docs/reports/robust_asr/**
  class: active_state
  permitted_use: read_write
  allowed_tasks: [P0.5, P9.1, P10.1]
  validator: none
  checksum_required: false
  large_artifact: false
  commit_allowed: true
  notes: Model card and router card templates
```

### After

```yaml
- path: docs/reports/robust_asr/**
  class: active_state
  permitted_use: read_write
  allowed_tasks: [P0.5, P9.1, P10.1, model_router_card_completion]
  validator: none
  checksum_required: false
  large_artifact: false
  commit_allowed: true
  notes: Model card and router card templates (P0.5 seeded; finalized progressively). model_router_card_completion added under CHANGE_SCOPE on accepted_report_commit d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d to fill or N/A-rewrite every TODO_FILLED_IN_<task_id> placeholder in docs/reports/robust_asr/{model_card_lora.md,router_card.md} per agent plan Section 10 items 11-12, before P10.2 final_asset_audit.py runs. Minimum-necessary amendment; no other tasks added; no class/permitted_use/no-touch change.
```

### Allowed-tasks delta

- `allowed_tasks_before`: `[P0.5, P9.1, P10.1]` (length 3).
- `allowed_tasks_after`: `[P0.5, P9.1, P10.1, model_router_card_completion]` (length 4).
- Added: `model_router_card_completion` only.
- Removed: none.
- `class`, `permitted_use`, `validator`, `checksum_required`, `large_artifact`, `commit_allowed`: all unchanged.
- No-touch patterns elsewhere in `reuse_policy_v1.yaml`: unchanged. The `scripts/robust_asr/**` row (lines 138–148) is byte-unchanged from its prior CHANGE_SCOPE state at sha256 `e72eb5d2…`; the new amendment only touches the `docs/reports/robust_asr/**` row.
- P10.2 was NOT added to this row, so P10.2 cannot edit the cards (audit-only role for P10.2).
- `configs/robust_asr/reuse_policy_v1.yaml` sha256 advanced from `e72eb5d2dfab5843212d3bef71f9eed956475d2f23b8f141662061f2d39ad958` to `c9e187ecbdc24ba0503753934f32bf4bb08df0a4f5ca049b9200299fca851876`.

## Files changed on this commit

- `configs/robust_asr/reuse_policy_v1.yaml` (single-row amendment to `docs/reports/robust_asr/**`)
- `docs/reports/robust_asr/model_card_lora.md` (full rewrite; sha256 → `01fec571aea1d3f915ae635c1522d75b5254ffe4537c2d86ce9fae8cb66bc463`)
- `docs/reports/robust_asr/router_card.md` (full rewrite; sha256 → `2587f5364a761bf8cef7bf4de111b9fe6af1bb3f51e0dc0aa8f0f07bd7882624`)
- `reports/robust_asr/task_reports/model_router_card_completion.md` (this report; new)
- `docs/progress/robust_asr_progress.yaml` (record CHANGE_SCOPE under `state_transport.latest_scope_change_packet`; update `artifacts.reuse_policy_config.sha256` and `last_amended_by`/`prior_sha256`/`sha256_history`; update `artifacts.model_card_template.sha256` and `artifacts.router_card_template.sha256` for the first time)
- `docs/progress/robust_asr_progress.md` (compact top bullet)
- `docs/progress/robust_asr_state_capsule.md` (compact top capsule entry)

## TODO inventory before and after

### Before

- `docs/reports/robust_asr/model_card_lora.md`: 30 `TODO_FILLED_IN_<task_id>` tokens covering task ids `[P1.1, P1.2, P1.3, P1.4, P2.1, P3.1, P3.2, P4.1, P4.2, P4.3, P5.1, P8.1, P8.2, P9.1]`.
- `docs/reports/robust_asr/router_card.md`: 24 `TODO_FILLED_IN_<task_id>` tokens covering task ids `[P1.3, P5.1, P6.1, P6.2, P7.1, P7.2, P7.3, P8.1, P8.2, P9.1]`.
- Total residual TODOs: 54.
- Strict blocking (PASS-status tasks): ≥ 18 occurrences (P1.2, P1.4, P2.1, P3.1, P3.2, P6.1, P7.3, P8.1, P8.2, P9.1).
- Pessimistic blocking incl. PARTIAL/HALTED: ≥ 24 occurrences (also P1.1, P1.3, P5.1).
- Non-blocking (SKIPPED_BY_DECISION_A / SKIPPED_BY_OUTCOME_E): ≥ 10 occurrences (P4.1, P4.2, P4.3, P6.2, P7.1, P7.2).

### After

- `docs/reports/robust_asr/model_card_lora.md`: 0 residual `TODO_FILLED_IN` tokens (verified by `grep -nE TODO_FILLED_IN docs/reports/robust_asr/model_card_lora.md` returning empty).
- `docs/reports/robust_asr/router_card.md`: 0 residual `TODO_FILLED_IN` tokens (same).
- Total residual TODOs: 0.
- Blocking TODOs remaining: false.

## Treatment of placeholders by tracker status

For each `<task_id>` whose placeholder appeared in the cards, the following replacement rule was applied (per the orchestrator-issued source mappings):

- `P0.5` (PASS — template seeding): N/A — the seeding task itself; not a fill target.
- `P1.1` (PARTIAL — `BLOCKED_OOD_PUBLIC`): replaced with concise PARTIAL statement citing `reports/robust_asr/data_inventory.md` and `reports/robust_asr/manifest_summary.md`; named the LibriSpeech subsets in scope and the OOD-real fallbacks that did not resolve; recorded that `claims_enabled.ood_real = false` and `BLOCKED_OOD_PUBLIC` is held.
- `P1.2` (PASS): replaced with concise PASS statement citing `artifacts/robust_asr/manifests/librispeech_lora_train.parquet` (sha256 `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a`, 22 507 rows, 200 speakers, ~79.58 h, full column list) and the manifest_summary.md.
- `P1.3` (PARTIAL): replaced with concise PARTIAL statement citing `reports/robust_asr/manifest_summary.md` (4-manifest disjointness table) and `tests/robust_asr/test_leakage.py` (5/5 PASS); recorded that the OOD-real disjointness conjunct is out of scope under `BLOCKED_OOD_PUBLIC`.
- `P1.4` (PASS): replaced with concise PASS statement citing `configs/robust_asr/degradation_v1.yaml` (degradation_version, master_seed, source manifests, families) and `reports/robust_asr/degradation_v1_summary.md` (sentinel `OK_DEGRADATION_V1`).
- `P2.1` (PASS): replaced with concise PASS statement citing `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` (sha256 `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6`, 53 230 rows) and `reports/robust_asr/baseline_whisper_base.md` (per-family WER/WA table verbatim, backend version `faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8`, `total_cost_usd = 0.0000`).
- `P3.1` (PASS): replaced with concise PASS statement citing `reports/robust_asr/lora/lora_smoke_report.md` and the smoke metrics (macro_wa_gain, max_family_wa_gain, clean_wa_regression, per-family WA gain table) verbatim.
- `P3.2` (PASS): replaced with concise PASS statement citing `reports/robust_asr/lora/decision_a_smoke.md` (Decision_A_smoke = FAIL, sentinel `OK_LORA_SMOKE_DECISION:FAIL`, mechanical per agent plan §5.1) and the routed consequences (`tasks.P4.{1,2,3}.status = SKIPPED_BY_DECISION_A`; `lora_status = SKIPPED_BY_DECISION_A`).
- `P4.1`, `P4.2`, `P4.3` (`SKIPPED_BY_DECISION_A`): replaced with "**N/A — skipped by Decision A**" plus marker citation, citing `reports/robust_asr/lora/decision_a_smoke.md`. Confirmed that no `artifacts/robust_asr/lora_full/`, `artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet`, `artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet`, `artifacts/robust_asr/lora_ct2_int8/`, or `reports/robust_asr/lora/full_lora_eval.md` / `lora_ct2_int8_preservation.md` exist. Confirmed: LoRA is NOT a deployed backend; `claims_enabled.positive_lora = false`.
- `P5.1` (HALTED — `BLOCKED_API`): replaced with "**N/A — HALTED under BLOCKED_API**" plus marker citation, citing handoff README §6.3 and `verify_handoff_package.py --strict` A6 secret-scan PASS. Confirmed: AssemblyAI is NOT an enabled backend; `claims_enabled.cloud_tradeoff = false`. Confirmed: no `artifacts/robust_asr/eval_tables/assemblyai.parquet`; no `ASSEMBLYAI_API_KEY` / `sk_*` / `Bearer` token in handoff.
- `P6.1` (PASS): replaced with concise PASS statement citing `artifacts/robust_asr/router/selector_evidence.parquet` (sha256 `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7`, 53 230 rows) and `reports/robust_asr/router/selector_evidence_summary.md` (Section 5.5 constants, decode-feature proxy policy, selector-outcome distribution).
- `P6.2` (`SKIPPED_BY_OUTCOME_E`): replaced with "**N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**" plus marker citation. Confirmed: `extract_router_features.py` was not run; no `router_features.parquet` / `router_train.parquet` / `router_val.parquet` / `router_test_locked.parquet` exist; the deterministic selector consumes `selector_evidence.parquet` columns directly.
- `P7.1`, `P7.2` (`SKIPPED_BY_OUTCOME_E`): replaced with "**N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**". Confirmed: no learned ML-router was trained; no held-out top-1 / regret-vs-oracle evaluation; no `ROUTER_IMPL_FALLBACK_*` lineage at runtime.
- `P7.3` (PASS): replaced with concise PASS statement citing `artifacts/robust_asr/router/selected_router/{deterministic_selector.json, metadata.json, rp5_inference.py, test_vectors.json}` with all four file sha256s verbatim, the §5.5 constants verbatim, the deployable action set verbatim, the build metadata, and `reports/robust_asr/router/selector_final_eval.md` (NEUTRAL_EVIDENCE first line; selection rates over 53 230 rows).
- `P8.1` (PASS): replaced with concise PASS statement citing `reports/robust_asr/system/system_eval.md` (first line `positive_system: false`; primary-result table verbatim including mean WER selector / baseline / regret CI / Wilcoxon) and `Decision_D_positive_system.outcome = false` under `OUTCOME_E_NARROWED_SCOPE` held on `tasks.P8.1` and `decisions.Decision_D_positive_system`.
- `P8.2` (PASS): replaced with concise PASS statement citing `artifacts/robust_asr/demo/demo_examples_manifest.json` (manifest_version `v1.2-deviation-enacted`, sha256 `850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba`, 8 entries) and `reports/robust_asr/final_verification.md` "C5 EXCLUSION VERIFICATION" section (`C5_EXCLUSION_PASS`).
- `P9.1` (PASS): replaced with concise PASS statement citing `artifacts/robust_asr/handoff/README.md` and the canonical handoff tag `handoff/20260514-64eba43` → `64eba4345f3207af38f0fba8ac2c43c6084e8852` (present locally and on `origin`); referenced handoff_validation_template.md.

## Claims consistency check

- `grep -nE "TODO_FILLED_IN" docs/reports/robust_asr/{model_card_lora.md,router_card.md}` → no matches (verified).
- `grep -nE "AssemblyAI.*enabled|LoRA.*deployed|positive system.*enabled|OOD.*enabled" docs/reports/robust_asr/{model_card_lora.md,router_card.md}` → matches present, ALL of which are LEGITIMATE NEGATIONS (per the orchestrator's allowance "If matches are legitimate negations, record them"):
  - `model_card_lora.md` line 8: header note explicitly listing the closed states (`SKIPPED_BY_DECISION_A`, `SKIPPED_BY_OUTCOME_E`, `HALTED`) and stating `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system} = false`.
  - `model_card_lora.md` line 14: "the deployed-backend set excludes any LoRA adapter (see §6.2 of the handoff README and `lora_status = SKIPPED_BY_DECISION_A`)".
  - `model_card_lora.md` lines 21, 40, 50, 51, 58, 60, 66, 68, 76: all explicit disclaimers ("N/A — HALTED under BLOCKED_API", "LoRA is NOT a deployed backend", "AssemblyAI is NOT an enabled backend", "claims_enabled.ood_real = false", etc.).
  - `router_card.md` line 14: "`assemblyai` and `whisper_lora_ct2_int8` are present in the action vocabulary but unreachable at runtime: `assemblyai_available = false` (BLOCKED_API), `lora_available = false` (SKIPPED_BY_DECISION_A). See handoff README §6.2 (LoRA not deployed) and §6.3 (AssemblyAI not enabled)."
  - `router_card.md` line 39: PARTIAL speaker-disjoint note explicitly recording `claims_enabled.ood_real = false` and `BLOCKED_OOD_PUBLIC` as the disabling marker.
  - `router_card.md` line 55: "AssemblyAI is not an enabled backend".
  - `router_card.md` line 63: "no positive system claim is enabled by these neutral results".
- No card statement asserts `LoRA is deployed`, `AssemblyAI is enabled`, `positive system is enabled`, or `OOD is enabled`. No claim depends on a disabled `claims_enabled` flag.
- Cross-walk against handoff README §6.1 (all four flags `false`), §6.2 (LoRA not deployed), §6.3 (AssemblyAI not enabled), §6.4 (C4 disclosure), §6.5 (OOD-real), §6.6 (System-level positive claim) — fully consistent.

## C4/C5 preservation

- C4 disclosure (P9.1): handoff README §6.4 byte-unchanged at sha256 `36f3c610571402851213bc0c7eb73384512caf2f24c3ed3a4c9a179160cf3b18`. Both cards explicitly cite handoff README §6.4 / the C4 disclosure (model card §evaluation_data and §risks; router card §risks "Public-example leakage through router features").
- C5 exclusion verification (P10.1): `reports/robust_asr/final_verification.md` byte-unchanged at sha256 `82ad07ecebbb33511b6712fb4a74ffb904995582d9a7fabc2d9b7196b1fc1378`; both cards explicitly cite the C5 EXCLUSION VERIFICATION section and the `C5_EXCLUSION_PASS` sentinel. The demo_examples_manifest.json sha256 `850c02db…` is held byte-unchanged.

## Forbidden paths unchanged

Verified by `git diff --stat` against `d714bac` post-commit:

- `docs/plans/**` — byte-unchanged (orchestrator plan, agent plan, schemas).
- `plan.md` — byte-unchanged.
- `CLAUDE.md` (incl. ROBUST_ASR_PROFILE block body) — byte-unchanged.
- `docs/progress/training_datamove1_progress.{yaml,md}` — byte-unchanged.
- `docs/plans/training_datamove1_plan.md` — still absent (not restored).
- `artifacts/robust_asr/**` — byte-unchanged. Specifically: `demo/demo_examples_manifest.json` sha256 `850c02db…` held; `handoff/README.md` sha256 `36f3c610…` held; `handoff/rp5_runtime_spec.md` sha256 `bbcf912d…` held; `eval_tables/whisper_base_ct2_int8.parquet` sha256 `0dc98736…` held; `router/selector_evidence.parquet` sha256 `c450a91a…` held; `runtime_contract/**` byte-unchanged; `oracle/**` byte-unchanged; `manifests/**` byte-unchanged.
- `reports/robust_asr/final_verification.md` sha256 `82ad07ec…` held.
- `reports/robust_asr/task_reports/P10.1_final_verification.md` sha256 `ed7b149b…` held.
- All other prior task reports under `reports/robust_asr/task_reports/` — byte-unchanged.
- `reports/robust_asr/touch_policy.md` — byte-unchanged.
- `reports/robust_asr/data_inventory.md`, `reports/robust_asr/manifest_summary.md`, `reports/robust_asr/baseline_whisper_base.md`, `reports/robust_asr/lora/decision_a_smoke.md`, `reports/robust_asr/lora/lora_smoke_report.md`, `reports/robust_asr/degradation_v1_summary.md`, `reports/robust_asr/system/system_eval.md`, `reports/robust_asr/router/selector_final_eval.md`, `reports/robust_asr/router/selector_evidence_summary.md` — byte-unchanged (read-only sources for the card content).
- `scripts/**` — byte-unchanged (incl. all of `scripts/robust_asr/**`; `scripts/robust_asr/final_asset_audit.py` still absent).
- `tests/**` — byte-unchanged.
- `libs/**` — byte-unchanged.
- All other `configs/robust_asr/*.yaml` — byte-unchanged (only `reuse_policy_v1.yaml` modified, by the single `[..., model_router_card_completion]` allowed_tasks extension and a notes annotation; sha256 advanced as recorded above).
- `refs/tags/handoff/20260514-64eba43` — still pointing at `64eba4345f3207af38f0fba8ac2c43c6084e8852` locally and on `origin`; no retag, no new tag.

## Tracker state preserved

- `current_task = P10.2` (held)
- `last_completed_task = P10.1` (held)
- `current_phase = P10` (held)
- `state_transport.expected_next_task = P10.2` (held)
- `state_transport.last_accepted_report_commit = 37a588b6aa4ee3116c32778092990b8dc9d023b0` (held; the APPROVE_EXECUTION(P10.1) anchor)
- `state_transport.latest_approval_packet = APPROVE_EXECUTION(P10.1)` on `37a588b6…` (held; not displaced; matches the FIX_BEFORE_CLOSE / scope-change precedent at P9.2 strict-tag-validator-fix and P8.2-deviation enactment)
- `state_transport.latest_scope_change_packet` advanced from `CHANGE_SCOPE(reuse_policy_p10_2_script_allowance)` on `9452afc…` to `CHANGE_SCOPE(model_router_card_completion)` on `d714bac…`; prior packet held under `state_transport.prior_scope_change_packet_reuse_policy_p10_2_script_allowance`.
- `phase_summary.P10 = null` (held)
- `orchestrator_approvals.P10 = null` (held)
- `tasks.P10.1.status = PASS` (held with sentinels)
- `tasks.P10.2` not added (P10.2 implementation not started)
- `tasks.P10.3` not added
- `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system} = false` (all held)
- `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]` (held)
- `OUTCOME_E_NARROWED_SCOPE` held on `tasks.P8.1` / `decisions.Decision_D_positive_system`
- `lora_status = SKIPPED_BY_DECISION_A`, `router_status = SELECTOR_PACKAGED`, `system_status = NOT_STARTED`
- `proposed_deviations.P8_2_demo_only_upstream_overlap.status = ENACTED`
- `blocked = false`, `blocker = null`
- `project_status = IN_PROGRESS`
- `artifacts.reuse_policy_config.sha256` advanced `e72eb5d2dfab5843212d3bef71f9eed956475d2f23b8f141662061f2d39ad958` → `c9e187ecbdc24ba0503753934f32bf4bb08df0a4f5ca049b9200299fca851876`; `last_amended_by` advanced `reuse_policy_p10_2_script_allowance` → `model_router_card_completion`; `prior_sha256` advanced to `e72eb5d2…`; `sha256_history` extended.
- `artifacts.model_card_template.sha256` advanced `null` → `01fec571aea1d3f915ae635c1522d75b5254ffe4537c2d86ce9fae8cb66bc463`; `last_amended_by` set to `model_router_card_completion`.
- `artifacts.router_card_template.sha256` advanced `null` → `2587f5364a761bf8cef7bf4de111b9fe6af1bb3f51e0dc0aa8f0f07bd7882624`; `last_amended_by` set to `model_router_card_completion`.

## Next legal action

Orchestrator returns `APPROVE_PLAN(P10.2)`. The P10.2 implementation may then:

1. Create `scripts/robust_asr/final_asset_audit.py` per agent plan §1105–§1119 (under `task_id=P10.2`, authorized by the prior `reuse_policy_p10_2_script_allowance` CHANGE_SCOPE on `9452afc…`).
2. Run it. With cards now fully filled, Assertion 3 ("No residual TODO_FILLED_IN_<task_id> tokens for tasks whose tracker.tasks[<task_id>].status == PASS") is expected to PASS regardless of `--report-root` scope (whether `reports/robust_asr/` only or extended to `docs/reports/robust_asr/`).
3. Write `reports/robust_asr/final_asset_audit.md` and `reports/robust_asr/task_reports/P10.2_final_audit.md`.
4. Update trackers and commit.

**P10.2 must NOT be started until orchestrator returns `APPROVE_PLAN(P10.2)`. P10.3 must NOT be started until orchestrator returns `APPROVE_EXECUTION(P10.2)`.**
