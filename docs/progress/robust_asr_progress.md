# Robust ASR LoRA Router — Progress

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Status: IN_PROGRESS

## Current state

- Phase: P1 (Schema, manifests, degradations)
- Current task: P1.3 (public manifests for LoRA / router / validation / locked test / OOD / demo reserved)
- Last completed: P1.2 (PASS — eval schema, normalization, metrics, leakage tests)
- Active markers: [BLOCKED_OOD_PUBLIC]
- Blocked: false
- claims_enabled.ood_real: false (no Section 1.1 OOD-real fallback resolves on host)
- normalization_version: normalization_v1 (frozen at P1.2)
- metrics_version: metrics_v1 (preserved; libs/audio/metrics.py unchanged)
- state_transport.last_accepted_report_commit: b049f9494f9acf163d6b5799f1f6450eaeee36c5 (advanced from 8185501 by APPROVE_EXECUTION(P1.2) at commit b049f94; CHANGE_SCOPE(P1.3) recorded at the same accepted commit)
- state_transport.expected_next_task: P1.3
- latest_approval_packet: CHANGE_SCOPE(P1.3) on `b049f94…` (next P1.3)
- prior_approval_packet: APPROVE_EXECUTION(P1.2) on `b049f94…` (next P1.3)

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
