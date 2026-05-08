# Robust ASR — Repository Integration Policy

Produced by: P0.2
Date: 2026-05-08

This document is the binding integration policy for all robust_asr tasks
(P0.0 through P10.3). Every table below is enforced by
`configs/robust_asr/reuse_policy_v1.yaml`. Any path not listed in Table A,
B, or C defaults to no_touch (Table D rule applies).

---

## A. Active robust_asr state paths

These paths are owned by this plan. Approved robust_asr tasks may create or
modify them. They are tracked in `docs/progress/robust_asr_progress.yaml`.

| Path | Permitted use | Write tasks |
|------|---------------|-------------|
| docs/progress/robust_asr_progress.yaml | read + write | All tasks (tracker update) |
| docs/progress/robust_asr_progress.md | read + write | All tasks (prose tracker update) |
| docs/progress/robust_asr_state_capsule.md | read + write | All tasks (capsule update) |
| reports/robust_asr/** | read + write | Designated task per plan |
| artifacts/robust_asr/** | read + write | Designated task per plan |
| configs/robust_asr/** | read + write | Designated task per plan |
| scripts/robust_asr/** | read + write | Designated task per plan |
| tests/robust_asr/** | read + write | Designated task per plan |
| docs/reports/robust_asr/** | read + write | Designated task per plan |
| docs/profiles/CLAUDE.robust_asr.md | read + write | Profile update tasks only |
| CLAUDE.md (ROBUST_ASR_PROFILE block only) | read + write | Profile update tasks only |

---

## B. Legacy state paths and their read-only status

These paths are git-tracked artifacts from prior branches. They must NOT be
modified by any robust_asr task except P10.3 (which reads them for
consistency checks).

| Path | Class | Permitted use | Commit allowed | Notes |
|------|-------|---------------|----------------|-------|
| docs/progress/training_datamove1_progress.md | legacy_state | read_only | false | Prior training tracker |
| docs/progress/training_datamove1_progress.yaml | legacy_state | read_only | false | Prior training tracker |
| docs/progress/demo_platform_progress.md | legacy_state | read_only | false | Demo branch tracker |
| docs/progress/demo_platform_progress.yaml | legacy_state | read_only | false | Demo branch tracker |
| plan.md | legacy_state | read_only | false | Legacy root plan placeholder |
| docs/plans/archive/** | legacy_state | read_only | false | Archived demo and training plans |
| docs/claude_task_progress.* | legacy_state | read_only | false | ABSENT — if created, treat as legacy_state |

---

## C. Reusable implementation paths and required approval mode

These paths contain existing code that robust_asr tasks may read and import
but must not modify without an explicit CHANGE_SCOPE Approval Packet naming
the exact file. The default approval mode is read_only.

| Path | Default permitted use | Required approval for writes |
|------|-----------------------|------------------------------|
| services/api/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| services/worker/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| services/frontend/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| libs/asr_adapter/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| libs/audio_pipeline/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| libs/audio/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| libs/common/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| libs/observability/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| infra/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| scripts/training/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| slurm/tools/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| slurm/jobs/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| tests/** (excl. tests/robust_asr/**) | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |
| configs/training/** | read_only | CHANGE_SCOPE + row in reuse_policy_v1.yaml |

---

## D. Mandatory no-touch paths

These paths must never be read-from-cache, modified, created, or deleted by
any robust_asr task regardless of phase or approval.

| Pattern | Reason |
|---------|--------|
| .git/** | Git internals |
| .env | Secrets |
| .env.* | Secrets |
| *.key | Secrets |
| *.pem | Secrets |
| *.token | Secrets |
| runs/** | Legacy training run directories (in-repo) |
| .cache/** | Cache directories |
| .hf_cache/** | HuggingFace cache |
| **/__pycache__/** | Python bytecode |
| *.wav | Audio files |
| *.flac | Audio files |
| *.mp3 | Audio files |
| *.m4a | Audio files |
| *.pt | PyTorch model weights |
| *.pth | PyTorch model weights |
| *.ckpt | Checkpoint files |
| *.bin | Binary model files |
| *.safetensors | Safetensors model files |

### D.1 External host no-touch assets

| Path | Reason |
|------|--------|
| /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif | Apptainer binary; read-execute only |
| /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/** | Prior training runs |
| /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache/** | Model and dataset caches |

### D.2 Default rule

Any path not explicitly classified in Tables A, B, or C above is treated as
**no_touch** with **permitted_use: forbidden** and **commit_allowed: false**.
This is the default policy for every unclassified path.
