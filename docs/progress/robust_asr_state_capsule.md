# Robust ASR — State Capsule

Updated by: P0.3-rerun-2 (PASS — BLOCKED_RUNTIME cleared; current_task -> P0.4)
Date: 2026-05-08

## Branch

branch: feature/robust-asr-lora-router-datamove1-v1
HEAD: recorded_in_execution_report
pushed_to_origin: true

## Current state

current_phase: P0
current_task: P0.4
last_completed_task: P0.3
blocked: false
blocker: null
active_markers: []

## Latest reports

latest_execution_report: reports/robust_asr/task_reports/P0.3_runtime_smoke.md
latest_planning_report: null
latest_phase_gate_report: null
latest_approval_packet: ORCHESTRATOR_DECISION scope=task task=P0.3-rerun-2 decision=APPROVE_PLAN accepted_report_commit=efed06e (env-isolation scope-change accepted; rerun-2 plan approved; outcome PASS, BLOCKED_RUNTIME cleared)
prior_approval_packet: ORCHESTRATOR_DECISION scope=scope_change task=P0.3-rerun-2-scope-change decision=APPROVE_EXECUTION accepted_report_commit=efed06e (env-isolation edit accepted)
last_accepted_report_commit: efed06e690255a1838741acc5ebd8ffb4f2c4599

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

## Next expected Claude prompt

Task: P0.4 Runtime contract skeleton
Phase: P0
Preconditions: P0.3 PASS (current_task == P0.4); BLOCKED_RUNTIME cleared.
Mode: PLANNING then EXECUTION

Next session: read docs/progress/robust_asr_progress.yaml, confirm
current_task=P0.4 and last_completed_task=P0.3, await orchestrator
APPROVE_PLAN for P0.4, then return a P0.4 Planning Report and stop.
