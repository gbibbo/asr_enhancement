# Robust ASR LoRA Router — Progress

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Status: IN_PROGRESS

## Current state

- Phase: P0 (Bootstrap and skeleton) — PHASE_APPROVED; P1 not yet entered
- Current task: P1.1 (HALTED — MISSING_EVIDENCE)
- Last completed: P0.5 (model_card and router_card templates PASS; 30 and 24 TODO_FILLED_IN placeholders respectively)
- Active markers: [MISSING_EVIDENCE]
- Blocked: true — LibriSpeech train-clean-100, train-clean-360, and test-clean audio missing on host; only dev-clean populated. Three of four required split labels (lora_train, router_train, locked_test) cannot resolve to non-empty file lists. Restore audio under `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech/` and rerun P1.1.

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

## P1.1 (HALTED — MISSING_EVIDENCE; awaiting audio restore)

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
