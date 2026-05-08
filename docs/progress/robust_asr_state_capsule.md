# Robust ASR — State Capsule

Updated by: P0.2
Date: 2026-05-08

## Branch

branch: feature/robust-asr-lora-router-datamove1-v1
HEAD: recorded_in_execution_report
pushed_to_origin: true

## Current state

current_phase: P0
current_task: P0.3
last_completed_task: P0.2
blocked: false
active_markers: []

## Latest reports

latest_execution_report: reports/robust_asr/task_reports/P0.2_asset_inventory.md
latest_planning_report: null
latest_phase_gate_report: null
latest_approval_packet: ORCHESTRATOR_DECISION task=P0.1 decision=APPROVE_EXECUTION

## Key artifacts created in P0.2

- reports/robust_asr/asset_inventory.md
- reports/robust_asr/repo_integration_policy.md
- reports/robust_asr/touch_policy.md
- configs/robust_asr/reuse_policy_v1.yaml (55 rows, 5 classes)
- scripts/robust_asr/validate_report_shape.py (emits OK_REPORT_SHAPE)
- artifacts/robust_asr/state_packets/report_shape_fixtures/ (6 fixtures)

## Next expected Claude prompt

Task: P0.3
Phase: P0
Preconditions: P0.2 PASS (tracker current_task == P0.3)
Mode: PLANNING then EXECUTION

The next session must start with the session-open ritual:
read docs/progress/robust_asr_progress.yaml, confirm current_task=P0.3,
select PLANNING mode, return a P0.3 Planning Report, and stop.
