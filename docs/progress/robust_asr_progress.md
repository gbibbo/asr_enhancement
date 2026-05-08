# Robust ASR LoRA Router — Progress

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Status: IN_PROGRESS

## Current state

- Phase: P0 (Bootstrap and skeleton)
- Current task: P0.3 (HALTED — must be rerun after image fix)
- Last completed: P0.2 (asset inventory, reuse policy, touch policy, report shape validator)
- Active markers: BLOCKED_RUNTIME
- Blocked: true
- Blocker: Apptainer image provides Python 3.10.13 (Decision rule 2 requires 3.11) and ctranslate2/faster_whisper/pytest are not installed (Decision rule 4). Clear by rebuilding the image and rerunning P0.3.

## Completed tasks

- P0.0 PASS: Pre-bootstrap inventory (read-only, no commit)
- P0.1 PASS: Branch created, profile installed, tracker initialized
- P0.2 PASS: Asset inventory, reuse policy, touch policy, validate_report_shape.py

## Scope changes

- P0.3 CHANGE_SCOPE applied: amended `configs/robust_asr/reuse_policy_v1.yaml`
  to authorize exec-only use of the Apptainer image (class=container_image,
  permitted_use=exec_only) and to make `slurm/jobs/**` writable for
  robust_asr `p<task_id>_*.sh` scripts (permitted_use=read_only_with_robust_asr_writes).
  current_task remains P0.3; last_completed_task remains P0.2.

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

## Pending

- P0.3 (rerun): Runtime smoke after image fix clears BLOCKED_RUNTIME
- P0.4: Runtime contract skeleton
- P0.5: Model card and router card templates
- P0 gate → P1 (schema, manifests, degradations)
- P1 → P2 (Whisper base baseline)
- P3 (LoRA smoke, Decision A)
- P4 (Full LoRA if Decision A PASS)
- P5 (AssemblyAI cache or BLOCKED_API)
- P6 (Oracle / selector evidence)
- P7 (Router or deterministic selector)
- P8 (System evaluation)
- P9 (Handoff package)
- P10 (Final reports and audit)
