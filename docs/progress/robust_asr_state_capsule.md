# Robust ASR — State Capsule

Updated by: P1.1 CHANGE_SCOPE (scope-change only; no inventory; current_task stays P1.1, last_completed_task stays P0.5)
Date: 2026-05-08

## Branch

branch: feature/robust-asr-lora-router-datamove1-v1
HEAD: recorded_in_execution_report
pushed_to_origin: true

## Current state

current_phase: P0
current_task: P1.1
last_completed_task: P0.5
blocked: false
blocker: null
active_markers: []

## Latest reports

latest_execution_report: reports/robust_asr/task_reports/P0.5_card_templates.md
latest_planning_report: reports/robust_asr/task_reports/P0.5_card_templates.md
latest_phase_gate_report: null
latest_approval_packet: ORCHESTRATOR_DECISION scope=scope_change task=P1.1 phase=P1 decision=CHANGE_SCOPE accepted_report_commit=3129c11e next_expected_task=P1.1 (authorize read-only dataset root inventory for P1.1 and P1 downstream tasks plus P1.1 write paths)
prior_approval_packet: ORCHESTRATOR_DECISION scope=phase phase=P0 decision=PHASE_APPROVE accepted_report_commit=d0ba20c5 next_expected_task=P1.1 (P0 gate PASS; P0.0..P0.5 PASS; sentinels and artifacts present; no blockers/markers)
last_accepted_report_commit: 3129c11edd5105d7c247b48eb1a170d7c1507cde

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

## Next expected Claude prompt

Task: P1.1 Data root inventory and dataset configs
Phase: P1
Preconditions: P0 PHASE_APPROVE recorded; P1.1 CHANGE_SCOPE recorded;
current_task == P1.1; last_completed_task == P0.5; markers=[]; blocked=false.
Mode: await ORCHESTRATOR_DECISION APPROVE_PLAN for P1.1, then return
a P1.1 Planning Report (already produced once before scope-change) or
proceed to P1.1 execution per orchestrator instruction.

Next session: read docs/progress/robust_asr_progress.yaml, confirm
current_task=P1.1, last_completed_task=P0.5, phase_summary.P0=PASS,
orchestrator_approvals.P0=PHASE_APPROVE, latest_approval_packet =
CHANGE_SCOPE(P1.1), then await APPROVE_PLAN(P1.1) or APPROVE_EXECUTION(P1.1).
