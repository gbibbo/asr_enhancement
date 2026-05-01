# Training Task Progress

Branch: feature/training-datamove1-v1
Integration branch: demo-rp5-v1
Current cut: T0
Current phase: Phase 0
Current task: Task T0.5 (in progress; ready to retry through committed wrapper)

## Completed

- T0.1: inspected datamove1 repository state. Repo root `/mnt/fast/nobackup/users/gb0048/asr_enhancement`, remote `git@github.com:gbibbo/asr_enhancement.git`, working tree clean, branch on `feature/training-datamove1-v1`.
- T0.2: training Claude profile activated on `feature/training-datamove1-v1` (commit `243ed48`). Root `CLAUDE.md` mirrors `docs/profiles/CLAUDE.training.md`; `.gitattributes` declares `CLAUDE.md merge=ours`; local `merge.ours.driver` configured to `true`.
- T0.3: created independent training trackers `docs/progress/training_datamove1_progress.{md,yaml}` per training plan §8 format. Legacy `docs/claude_task_progress.*` left untouched as historical.
- T0.4: added training runtime ignore patterns to `.gitignore` (`runs/`, `artifacts/`, `checkpoints/`, `data/`, `.cache/`, `*.wav`, `*.flac`, `*.mp3`, `*.m4a`, `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`). No duplicates of existing rules; source, configs, docs, plans, and trackers remain trackable.

## Current blocker

None. The earlier blocker (Slurm/Apptainer absent from the datamove1 shell) was resolved by encoding the validated submission path into the repository.

## Manual external validation (2026-05-01)

Gabriel manually validated the live Surrey Slurm workflow before the corrective commit:

- `./slurm/tools/on_submit.sh squeue -u gb0048` (run from `/mnt/fast/nobackup/users/gb0048/opro3_final`) returned a normal queue listing — the wrapper's `ssh -o BatchMode=yes aisurrey-submit01.surrey.ac.uk "$@"` path works.
- `sbatch` through the same wrapper produced job `2125750`, which ran on `aisurrey01.surrey.ac.uk`.
- Inside the job, `/usr/bin/apptainer` and `/usr/bin/singularity` were both available.
- The container `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` loaded; `python3 --version` inside it reported `3.10.13`.
- Apptainer emitted: *"WARNING: Not mounting current directory: user bind control is disabled by system administrator"* — captured in CLAUDE.md §8 constraint 8 and reflected in the job script and template (absolute paths only).

This validates the workflow as a procedure, but T0.5 is not closed yet because the test was run from `opro3_final`, not from the now-committed `slurm/tools/on_submit.sh` and `slurm/jobs/t0_minimal_job.sh` in this repo. T0.5 closes after the same submission is repeated through this repo's wrapper.

## T0.5 retry commands (run from datamove1 in the repo root)

```bash
cd /mnt/fast/nobackup/users/gb0048/asr_enhancement
./slurm/tools/on_submit.sh squeue -u "$USER"
./slurm/tools/on_submit.sh sinfo || true
./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t0_minimal_job.sh
# capture <job_id> from sbatch output, then:
./slurm/tools/on_submit.sh sacct -j <job_id> --format=JobID,JobName,State,Elapsed,MaxRSS,ExitCode
cat /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_<job_id>.out
```

Once that succeeds, this tracker should be flipped to: `tasks."T0.5": done`, `last_completed_task: "T0.5"`, `current_task: "T1.1"`, `slurm_status: ok`, `datamove1_status: ready`. The T0 gate is then complete.

## Sync status

Last synced from demo-rp5-v1: 2026-05-01 (T0.2 commit `243ed48`, 1 ahead / 0 behind).

## Next task

Task T0.5 — retry the minimal Slurm gate job through the now-committed `slurm/tools/on_submit.sh` and `slurm/jobs/t0_minimal_job.sh`. Once it succeeds, advance to Task T1.1 (Configure required Apptainer environment).
