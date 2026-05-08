# Robust ASR — State Capsule

Updated by: P0.3-rebuild (PASS — BLOCKED_RUNTIME persists pending rerun)
Date: 2026-05-08

## Branch

branch: feature/robust-asr-lora-router-datamove1-v1
HEAD: recorded_in_execution_report
pushed_to_origin: true

## Current state

current_phase: P0
current_task: P0.3            # HALTED, must be rerun after image fix
last_completed_task: P0.2
blocked: true
blocker: BLOCKED_RUNTIME (Python 3.10.13 inside Apptainer image; ctranslate2/faster_whisper/pytest missing)
active_markers: [BLOCKED_RUNTIME]

## Latest reports

latest_execution_report: reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md
latest_planning_report: null
latest_phase_gate_report: null
latest_approval_packet: ORCHESTRATOR_DECISION scope=task task=P0.3-rebuild decision=APPROVE_PLAN accepted_report_commit=5ca1885 (Option A scope-change accepted; rebuild approved)
last_accepted_report_commit: 635a711cd4fe44e919966a0e6bc3df99103fe6d3

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

Task: P0.3-rerun
Phase: P0
Preconditions: tasks["P0.3-rebuild"].status == PASS;
artifacts.runtime_image_v1 populated; BLOCKED_RUNTIME still active.
Mode: PLANNING then EXECUTION

The next session must start with the session-open ritual:
read docs/progress/robust_asr_progress.yaml, confirm current_task=P0.3
with BLOCKED_RUNTIME and the new image SHA in
artifacts.runtime_image_v1, await orchestrator APPROVE_PLAN for the
P0.3-rerun sub-task, then return a P0.3-rerun Planning Report and stop.
