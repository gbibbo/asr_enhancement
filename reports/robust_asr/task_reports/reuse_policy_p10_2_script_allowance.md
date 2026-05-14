# Scope-change report — `reuse_policy_p10_2_script_allowance`

PASS

## Scope-change identity

- `scope_change_id`: `reuse_policy_p10_2_script_allowance`
- `phase`: `P10`
- `decision`: `CHANGE_SCOPE`
- `accepted_report_commit` (orchestrator packet): `9452afcf3c3f6b1874d86650724606d8e902b286`
- `next_expected_task`: `P10.2`
- `branch`: `feature/robust-asr-lora-router-datamove1-v1`
- `head_before` (this commit): `9452afcf3c3f6b1874d86650724606d8e902b286`
- `git_status_before`: clean (0 lines)
- `author`: Gabriel Bibbó <gabobibbo@gmail.com>; no `Co-Authored-By`, `Generated-By`, AI-authorship, or `Signed-off-by` trailer.

## Issue

The active agent plan (`docs/plans/robust_asr_agent_plan_v3_4_7.md`) specifies:

- §4275 (P10.2 Action 1): "Run `final_asset_audit.py` per Section 4.1."
- §1105–§1119 (Section 4.1 — `scripts/robust_asr/final_asset_audit.py`): defines the script's normative contract (inputs, asserts, sentinel `OK_FINAL_ASSET_AUDIT`, exit codes).
- §915: "Every script referenced anywhere in this plan must satisfy its contract here. Inputs, outputs, asserts, exit codes, and stdout sentinels are normative. If a task implementation drifts from the contract, stop and record `PLAN_CONFLICT`."

`scripts/robust_asr/final_asset_audit.py` does **not** exist on disk (verified via `test -f` returning non-zero). For P10.2 to satisfy its Action 1, the script must be created in P10.2's implementation commit.

`configs/robust_asr/reuse_policy_v1.yaml` row for `scripts/robust_asr/**` (lines 138–147 pre-amendment) listed `allowed_tasks` as `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2]`. **`P10.2` was absent.** Without this scope change, the P10.2 implementation commit would write to `scripts/robust_asr/**` under a task not authorized by the reuse policy, violating CLAUDE.md `ROBUST_ASR_PROFILE` Section 2.2 ("Reuse policy") and orchestrator review checklist item 6 ("for every expected_path outside robust_asr-owned paths, confirm the Planning Report cites an exact `reuse_policy_v1.yaml` row and that the row permits the task and operation").

## Exact reuse-policy row changed

File: `configs/robust_asr/reuse_policy_v1.yaml`

Row: `scripts/robust_asr/**` (lines 138–148 post-amendment).

### Before

```yaml
- path: scripts/robust_asr/**
  class: active_state
  permitted_use: read_write
  allowed_tasks: [P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1,
                  P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2]
  validator: none
  checksum_required: false
  large_artifact: false
  commit_allowed: true
  notes: Robust ASR scripts
```

### After

```yaml
- path: scripts/robust_asr/**
  class: active_state
  permitted_use: read_write
  allowed_tasks: [P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1,
                  P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2,
                  P10.2]
  validator: none
  checksum_required: false
  large_artifact: false
  commit_allowed: true
  notes: Robust ASR scripts. P10.2 added under CHANGE_SCOPE(reuse_policy_p10_2_script_allowance) on accepted_report_commit 9452afcf3c3f6b1874d86650724606d8e902b286 to authorize creation of scripts/robust_asr/final_asset_audit.py per agent plan §4275 (P10.2 Action 1) and §1105–§1119 (final_asset_audit.py contract). Minimum-necessary amendment; no other tasks added; no class/permitted_use/no-touch change.
```

### Allowed-tasks delta

- `allowed_tasks_before`: `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2]` (length 19).
- `allowed_tasks_after`: `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.3, P1.4, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P6.1, P6.2, P7.2, P7.3, P8.1, P8.2, P10.2]` (length 20).
- Added: `P10.2` only.
- Removed: none.
- `class` unchanged: `active_state`.
- `permitted_use` unchanged: `read_write`.
- `validator` unchanged: `none`.
- `checksum_required` unchanged: `false`.
- `large_artifact` unchanged: `false`.
- `commit_allowed` unchanged: `true`.
- No-touch patterns elsewhere in `reuse_policy_v1.yaml`: unchanged.

## Reason P10.2 needs this

Agent plan §4275 (P10.2 Action 1) requires running `final_asset_audit.py`, which does not yet exist on disk. Per agent plan §915, scripts referenced by the plan must satisfy their Section-4.1 contract. The implementation commit of `scripts/robust_asr/final_asset_audit.py` will land under `task_id=P10.2`. Without `P10.2` in the `scripts/robust_asr/**` row's `allowed_tasks`, that write would violate the reuse policy. This scope change is the minimum-necessary administrative fix to authorize that single write.

## Tracker state preserved

The following tracker fields are **held** (no advance) by this scope-change commit:

- `current_task = P10.2`
- `last_completed_task = P10.1`
- `current_phase = P10`
- `state_transport.expected_next_task = P10.2`
- `state_transport.last_accepted_report_commit = 37a588b6aa4ee3116c32778092990b8dc9d023b0` (the APPROVE_EXECUTION(P10.1) anchor)
- `state_transport.latest_approval_packet = APPROVE_EXECUTION(P10.1)` on `37a588b6aa4ee3116c32778092990b8dc9d023b0` (held; this CHANGE_SCOPE packet is recorded under `state_transport.latest_scope_change_packet` instead, per the FIX_BEFORE_CLOSE/CHANGE_SCOPE precedent applied at P9.2 strict-tag-validator-fix and at P8.2-deviation enactment, where in-task scope changes do not displace `latest_approval_packet`)
- `phase_summary.P10 = null`
- `orchestrator_approvals.P10 = null`
- `tasks.P10.1.status = PASS` (held with sentinels `[pytest_tests_robust_asr_137_of_137, OK_EVAL_TABLE, OK_SELECTOR_EVIDENCE, OK_HANDOFF_PACKAGE, OK_CONTRACT_FINAL, C5_EXCLUSION_PASS]`)
- `tasks.P10.2` **not added** (P10.2 implementation has not started)
- `tasks.P10.3` **not added**
- `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system} = false` (all held)
- `markers = [BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]` (held; none cleared, none added)
- `OUTCOME_E_NARROWED_SCOPE` held on `tasks.P8.1` / `decisions.Decision_D_positive_system`
- `lora_status = SKIPPED_BY_DECISION_A`, `router_status = SELECTOR_PACKAGED`, `system_status = NOT_STARTED`
- `proposed_deviations.P8_2_demo_only_upstream_overlap.status = ENACTED`
- `blocked = false`, `blocker = null`
- `project_status = IN_PROGRESS`
- `artifacts.reuse_policy_config.sha256` advanced from `33bcc25cc8b4a925ec9762d3812df9eb0297112edb6591c7d01345edee81f1ae` to `e72eb5d2dfab5843212d3bef71f9eed956475d2f23b8f141662061f2d39ad958`; `prior_sha256` updated to record the chain (`33bcc25c...` becomes the latest prior); `last_amended_by` advanced to `reuse_policy_p10_2_script_allowance` (prior `last_amended_by` was `P8.2_scope_change`).

## Forbidden paths unchanged

Verified by `git diff --stat` against `9452afc` post-commit:

- `docs/plans/**` (orchestrator plan, agent plan, schemas) — byte-unchanged.
- `plan.md` — byte-unchanged.
- `CLAUDE.md` (incl. `ROBUST_ASR_PROFILE` block body) — byte-unchanged.
- `docs/progress/training_datamove1_progress.{yaml,md}` — byte-unchanged.
- `docs/plans/training_datamove1_plan.md` — still absent (not restored).
- `artifacts/robust_asr/**` — byte-unchanged. Specifically: `demo/demo_examples_manifest.json` sha256 `850c02db…` held; `handoff/README.md` sha256 `36f3c610…` held; `handoff/rp5_runtime_spec.md` sha256 `bbcf912d…` held; `eval_tables/whisper_base_ct2_int8.parquet` sha256 `0dc98736…` held; `router/selector_evidence.parquet` sha256 `c450a91a…` held; `runtime_contract/**` byte-unchanged; `oracle/**` byte-unchanged.
- `reports/robust_asr/final_verification.md` sha256 `82ad07ec…` held.
- `reports/robust_asr/task_reports/P10.1_final_verification.md` sha256 `ed7b149b…` held.
- All prior task reports under `reports/robust_asr/task_reports/` (P0.x, P1.x, P2.1, P3.x, P5.1, P6.1, P7.3, P8.1, P8.2, P8_GATE_attempt2, P9.0, P9.1, P9.2, P9.2_strict_tag_validator_fix, P9_GATE_attempt1, plan_index_refresh, P10.1) — byte-unchanged.
- `scripts/**` — byte-unchanged (incl. `scripts/robust_asr/**`; `scripts/robust_asr/final_asset_audit.py` still absent).
- `tests/**` — byte-unchanged.
- `libs/**` — byte-unchanged.
- All other `configs/robust_asr/*.yaml` — byte-unchanged (only `reuse_policy_v1.yaml` modified, by the single 19→20-element `allowed_tasks` extension and a notes-line annotation).
- `reports/robust_asr/touch_policy.md` — byte-unchanged (touch_policy P10.2 row line 42 already authorizes the report and tracker writes for this commit).
- `refs/tags/handoff/20260514-64eba43` — still pointing at `64eba4345f3207af38f0fba8ac2c43c6084e8852` locally and on `origin`; no retag, no new tag.

## Files modified on this commit

- `configs/robust_asr/reuse_policy_v1.yaml` (single-row amendment + notes line)
- `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` (this report; new)
- `docs/progress/robust_asr_progress.yaml` (record CHANGE_SCOPE packet under `state_transport.latest_scope_change_packet`; update `artifacts.reuse_policy_config.sha256` and `last_amended_by`/`prior_sha256`)
- `docs/progress/robust_asr_progress.md` (compact top bullet)
- `docs/progress/robust_asr_state_capsule.md` (compact top capsule entry)

## Next legal action

Orchestrator returns `APPROVE_PLAN(P10.2)` against the planning report. P10.2 implementation may then proceed with creation of `scripts/robust_asr/final_asset_audit.py` (per agent plan §1105–§1119), running it (default `--report-root=reports/robust_asr`), writing `reports/robust_asr/final_asset_audit.md`, writing `reports/robust_asr/task_reports/P10.2_final_audit.md`, and updating trackers under `task_id=P10.2`. **P10.2 must NOT be started until orchestrator returns `APPROVE_PLAN(P10.2)`. P10.3 must NOT be started until orchestrator returns `APPROVE_EXECUTION(P10.2)`.**
