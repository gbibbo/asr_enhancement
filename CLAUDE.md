# ASR Enhancement Integration Branch: Claude Code Rules

This file is the active root `CLAUDE.md` on the `demo-rp5-v1` integration branch.

This branch receives changes from both implementation contexts:

1. demo, platform, Raspberry Pi, frontend, deployment, and GitHub narrative;
2. datamove1, Surrey Slurm, evaluation, training, export, and model-card training content.

Do not execute implementation tasks directly from this branch unless the user explicitly asks for integration-only work.

For demo/platform work, use branch `feature/demo-runtime-rp5-v1` and the active rules in root `CLAUDE.md` on that branch. The reference copy is `docs/profiles/CLAUDE.demo.md`.

For training/datamove1 work, use branch `feature/training-datamove1-v1` and the active rules in root `CLAUDE.md` on that branch. The reference copy is `docs/profiles/CLAUDE.training.md`.

Before merging any branch into this integration branch:

1. inspect `CLAUDE.md` explicitly;
2. keep this integration router as the root `CLAUDE.md` on `demo-rp5-v1`;
3. keep the branch-specific profiles under `docs/profiles/`;
4. keep `.gitattributes` containing `CLAUDE.md merge=ours`;
5. configure the local merge driver with `git config merge.ours.driver true`.

Read order for integration-only work:

1. `CLAUDE.md`;
2. `docs/plans/demo_platform_plan.md`;
3. `docs/plans/training_datamove1_plan.md`;
4. `docs/progress/demo_platform_progress.md`, if present;
5. `docs/progress/training_datamove1_progress.md`, if present;
6. repository status and branch graph.

Integration branch rules:

1. Do not run Slurm jobs from this branch.
2. Do not deploy to Raspberry Pi from this branch.
3. Do not start new implementation tasks from this branch.
4. Do not commit datasets, audio artifacts, checkpoints, caches, secrets, or runtime outputs.
5. Only merge reviewed, task-scoped changes from feature branches.
6. If `CLAUDE.md` conflicts, keep this router on `demo-rp5-v1`.
7. If plan or tracker conflicts occur, stop and report exact files.

Expected Git identity:

```text
user.name: Gabriel Bibbó
user.email: gabobibbo@gmail.com
```

Verification before any integration commit:

```bash
git branch --show-current
git status --short
git remote -v
git config user.name
git config user.email
git config merge.ours.driver
```
