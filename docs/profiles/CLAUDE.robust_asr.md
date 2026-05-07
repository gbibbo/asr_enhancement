# Robust ASR LoRA Router — Claude Profile (v3.4.7)

audience: robust_asr_lora_router
repo_root: /mnt/fast/nobackup/users/gb0048/asr_enhancement
target_branch: feature/robust-asr-lora-router-datamove1-v1
source_branch: feature/training-datamove1-v1

## Pointers

- Agent plan:          docs/plans/robust_asr_agent_plan_v3_4_7.md
- Orchestrator plan:   docs/plans/robust_asr_orchestrator_plan_v3_4_7.md
- Live tracker:        docs/progress/robust_asr_progress.yaml
- State capsule:       docs/progress/robust_asr_state_capsule.md
- Report schemas:      docs/plans/state_packet_schemas_v1.yaml

## Session-open ritual (Section 0)

Run at the start of every session before any planning or execution:

1. Read docs/progress/robust_asr_progress.yaml. Extract: current_phase,
   current_task, blocked, active markers, session_log overrides, and
   state_transport.latest_approval_packet.
2. Read docs/progress/robust_asr_state_capsule.md if it exists.
3. Read docs/progress/robust_asr_progress.md.
4. Read the agent plan Sections 0 through 7.
5. Identify the first task with status not in
   {PASS, FAIL, HALTED, SKIPPED_BY_DECISION_A, SKIPPED_BY_OUTCOME_E}
   and all preconditions satisfied.
6. Compare user-requested task with tracker-derived next task.
7. If they differ, return TRACKER_MISMATCH in a State Packet and stop.
8. Select exactly one mode:
   PLANNING | EXECUTION | CLOSURE_FIX |
   PHASE_APPROVAL_RECORDING | SUPPLEMENTAL_EVIDENCE

Pre-tracker exception: if robust_asr_progress.yaml is absent, only
BOOTSTRAP_NO_TRACKER mode is legal and P0.0 is the only legal task.
P0.1 requires an explicit P0.0 PASS report plus APPROVE_PLAN packet.

Stop after returning each report. Do not auto-advance to the next task.
The tracker is the only source of truth for current_task; do not infer
it from prose, legacy trackers, or uploaded zips.

## Phase routing (Section 0.1)

Follow the Section 0.1 transition table exactly:
- P0.0 PASS → P0.1
- P0 gate PASS + PHASE_APPROVE → P1.1
- P3.2 Decision A FAIL → P5.1 (P4.x = SKIPPED_BY_DECISION_A)
- OUTCOME_E active before P7.1 → skip P7.1, P7.2; next task P7.3
- P10.3 PASS → project_status = COMPLETE

Never infer next task from narrative. Never open a task with unsatisfied
preconditions. Never skip a task unless the tracker records an explicit
skip status.

## Active robust_asr state paths (Section 2.1)

Paths owned by this plan — may be modified by approved tasks:

  docs/progress/robust_asr_progress.yaml
  docs/progress/robust_asr_progress.md
  docs/progress/robust_asr_state_capsule.md
  reports/robust_asr/**
  artifacts/robust_asr/**
  configs/robust_asr/**
  scripts/robust_asr/**
  tests/robust_asr/**
  docs/reports/robust_asr/**
  docs/profiles/CLAUDE.robust_asr.md

Legacy state paths — read-only unless an approved task explicitly names
the path and the orchestrator approves:

  plan.md
  docs/plans/demo_platform_plan.md
  docs/plans/training_datamove1_plan.md
  docs/progress/training_datamove1_progress.md
  docs/progress/training_datamove1_progress.yaml
  docs/claude_task_progress.md
  docs/claude_task_progress.yaml
  reports/training/**
  artifacts/training/**

Path classification rules:
1. robust_asr_progress.yaml is the only live robust_asr tracker.
2. Legacy trackers never determine current_task, markers, or claims.
3. plan.md and training_datamove1_plan.md are templates only.
4. Existing runtime code may be reused only via adapter, import, or
   narrow patch. Rewrites require an approved task naming exact files.
5. Existing evaluation outputs are not robust_asr evidence until a
   robust_asr validator accepts them under the current plan.
6. Existing AssemblyAI caches are not valid until P0.2 records their
   provenance and P5.1 validates them.
7. Existing LoRA checkpoints are never directly selected; P4 must
   produce new ones unless skipped by Decision A.
8. Existing dataset roots may be reused as storage locations only;
   P1 must build new robust_asr manifests.
9. Existing tests must not be deleted or weakened.
10. Any unclassified path is default no-touch. Reading is allowed for
    inventory; editing requires an Approval Packet naming the path.

## Reuse policy (Section 2.2)

After P0.2, every use of a path outside robust_asr-owned directories
requires a row in configs/robust_asr/reuse_policy_v1.yaml:

  path, class, permitted_use, allowed_tasks, validator,
  checksum_required, large_artifact, commit_allowed, notes

Default for unclassified paths:
  class=no_touch | permitted_use=forbidden | commit_allowed=false

Every Planning Report must list expected_paths and expected_no_touch_paths.
For each path outside robust_asr-owned directories, cite the exact
reuse_policy_v1.yaml row. Return REQUIRES_SCOPE_CHANGE if no row exists.

Mandatory no-touch paths for every task (no exceptions unless explicitly
named by an approved task):
  .git/**  .env  .env.*  *.key  *.pem  *.token
  runs/**  .cache/**  .hf_cache/**  **/__pycache__/**
  *.wav  *.flac  *.mp3  *.m4a  *.pt  *.pth  *.ckpt  *.bin  *.safetensors

## CLAUDE.md rule

Preserve all content outside the delimited ROBUST_ASR_PROFILE block
in CLAUDE.md exactly. Replace only the block body on updates. Do not
add CLAUDE.md merge=ours to .gitattributes. If a merge conflict touches
outside the block, halt with PLAN_CONFLICT.
