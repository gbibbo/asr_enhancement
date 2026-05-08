# Robust ASR — State Capsule

Updated by: P2.1 CHANGE_SCOPE recorded — `configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md` amended to authorize P2.1 baseline-eval deliverables. `configs/robust_asr/**` row: P2.1 added to `allowed_tasks` (now `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.4, P2.1]`). `touch_policy.md` P2.1 row REWRITTEN to authorize `configs/robust_asr/eval_manifests_v1.yaml`, `scripts/robust_asr/run_backend_eval.py`, `scripts/robust_asr/summarize_backend_eval.py`, `scripts/robust_asr/validate_eval_table.py`, `slurm/jobs/p2_1_baseline.sh`, `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`, `reports/robust_asr/baseline_whisper_base.md`, `reports/robust_asr/task_reports/P2.1_baseline.md`, scope-change rows on the two policy files, and the three live trackers; reads include `configs/robust_asr/data_v1.yaml`, `configs/robust_asr/degradation_v1.yaml`, `libs/common/eval_schema.yaml`, `libs/common/normalization.py`, `libs/common/metrics.py`, `libs/common/versions.py`, `libs/audio/**`, `libs/asr_adapter/**`, `libs/audio_pipeline/**`, robust_asr public + degradation_v1 manifests; external resources: Slurm submit, Apptainer (exec) on the robust_asr SIF, LibriSpeech and degradation_v1 audio (read-only). New sha256s: `reuse_policy_v1.yaml=678d86a37ae471448736b08a68a9b34802ad6599ea12b08f3a0a33041d2aab6f`, `touch_policy.md=1b38914f1e814619d202a610ba98ca1cc18d404b9d507f5084d5871b2721c0e3`; both `last_amended_by=P2.1_scope_change`. `latest_approval_packet`=CHANGE_SCOPE(P2.1) on `22201db1a11586151811f814b14219e099e1a1ed` (next P2.1); `prior_approval_packet`=PHASE_APPROVE(P1) on `49b4bdc` (next P2.1); `prior_approval_packet_p1_gate`=APPROVE_EXECUTION(P1.4) on `49b4bdc` (next P1_GATE); `prior_approval_packet_p1_4_plan`=APPROVE_PLAN(P1.4) on `5c72769`. `state_transport.last_accepted_report_commit` STAYS `49b4bdc122b9b9768b380ab9bb9c28bec49455db` (PHASE_APPROVE(P1) acceptance; CHANGE_SCOPE does not advance). `state_transport.expected_next_task` STAYS `P2.1`. Held: `current_phase=P2`, `current_task=P2.1`, `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`, `degradation_version=degradation_v1`, `normalization_version=normalization_v1`, `metrics_version=metrics_v1`, `phase_summary={P0:PASS, P1:PASS}`, `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`. Verification: `validate_report_shape.py` -> `OK_REPORT_SHAPE` (exit 0). P2.1 implementation NOT executed: no `eval_manifests_v1.yaml`, no `run_backend_eval.py`, no `summarize_backend_eval.py`, no `validate_eval_table.py`, no Slurm job, no eval table, no baseline report, no pytest run, no Apptainer, no GPU, no external API.

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
