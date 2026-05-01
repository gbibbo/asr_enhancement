# CLAUDE.md — integration router

This root `CLAUDE.md` is active only on the `demo-rp5-v1` integration branch.

This branch is a controlled integration branch. It is not the daily working branch for either implementation line.

Daily work branches:

- Demo/Raspberry Pi work belongs on `feature/demo-runtime-rp5-v1`.
- Training/datamove1 work belongs on `feature/training-datamove1-v1`.

Reference profiles:

- Demo/Raspberry Pi profile: `docs/profiles/CLAUDE.demo.md`
- Training/datamove1 profile: `docs/profiles/CLAUDE.training.md`

Plans:

- Demo/Raspberry Pi plan: `docs/plans/demo_platform_plan.md`
- Training/datamove1 plan: `docs/plans/training_datamove1_plan.md`

Progress trackers:

- Demo/Raspberry Pi trackers:
  - `docs/progress/demo_platform_progress.md`
  - `docs/progress/demo_platform_progress.yaml`
- Training/datamove1 trackers:
  - `docs/progress/training_datamove1_progress.md`
  - `docs/progress/training_datamove1_progress.yaml`

Branch rules:

1. Do not implement feature work directly on `demo-rp5-v1`.
2. Use `feature/demo-runtime-rp5-v1` for demo/Raspberry Pi tasks.
3. Use `feature/training-datamove1-v1` for training/datamove1 tasks.
4. Use `demo-rp5-v1` only to integrate verified work from both feature branches.
5. Preserve both plans, both profile files, both progress tracker pairs, and `slurm/`.
6. Keep `.gitattributes` with `CLAUDE.md merge=ours`.
7. Configure the local merge driver before integration work:
   `git config merge.ours.driver true`

Git policy:

- At the end of every successfully completed and verified task, commit and push automatically to the current branch.
- Use Git identity exactly: Gabriel Bibbó <gabobibbo@gmail.com>.
- Do not add Co-Authored-By, Generated-By, AI-authorship, Signed-off-by, or similar authorship trailers.
- Do not invent commits, branches, remotes, or verification results.

Slurm policy:

- Slurm work belongs to `feature/training-datamove1-v1`.
- From datamove1, do not call `sbatch`, `squeue`, `sacct`, or `scancel` directly.
- Use `./slurm/tools/on_submit.sh <squeue|sbatch|scancel|sacct> <args...>`.
- Jobs must use absolute paths.
- Jobs must not depend on Apptainer mounting the current working directory.
- Expected container: `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`.