# Training Task Progress

Branch: feature/training-datamove1-v1
Integration branch: demo-rp5-v1
Current cut: T0
Current phase: Phase 0
Current task: Task T0.5 (blocked)

## Completed

- T0.1: inspected datamove1 repository state. Repo root `/mnt/fast/nobackup/users/gb0048/asr_enhancement`, remote `git@github.com:gbibbo/asr_enhancement.git`, working tree clean, branch on `feature/training-datamove1-v1`.
- T0.2: training Claude profile activated on `feature/training-datamove1-v1` (commit `243ed48`). Root `CLAUDE.md` mirrors `docs/profiles/CLAUDE.training.md`; `.gitattributes` declares `CLAUDE.md merge=ours`; local `merge.ours.driver` configured to `true`.
- T0.3: created independent training trackers `docs/progress/training_datamove1_progress.{md,yaml}` per training plan §8 format. Legacy `docs/claude_task_progress.*` left untouched as historical.
- T0.4: added training runtime ignore patterns to `.gitignore` (`runs/`, `artifacts/`, `checkpoints/`, `data/`, `.cache/`, `*.wav`, `*.flac`, `*.mp3`, `*.m4a`, `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`). No duplicates of existing rules; source, configs, docs, plans, and trackers remain trackable.

## Current blocker

T0.5 is blocked. The minimal Slurm gate job cannot be submitted from this datamove1 shell:

- `sbatch`, `squeue`, `sacct` are not in PATH and are absent from `/opt`, `/usr`, `/cm`, `/shared`, `/apps`.
- `apptainer` and `singularity` are also absent.
- No `module` system is available on this shell to load them.
- Host confirmed: `datamove1.surrey.ac.uk`.
- Container `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` exists (3.3 GB) and is readable.

What is ready:

- The minimal job script is committed at `slurm/jobs/t0_minimal_job.sh`. It prints hostname, date, working directory, `df -h` head, and the Python version reported from inside the Apptainer container, per CLAUDE.md §10 / §8.
- Output and error logs are routed to `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.{out,err}` (created by the script's `mkdir -p`).

External verification commands Gabriel must run from a Surrey host that has both Slurm and Apptainer (e.g. condor1 / aisurrey1 / wherever he submits Slurm):

```bash
which sbatch squeue sacct
which apptainer
sinfo
cd /mnt/fast/nobackup/users/gb0048/asr_enhancement
sbatch slurm/jobs/t0_minimal_job.sh
# wait for completion, then
sacct -j <job_id> --format=JobID,JobName,State,Elapsed,MaxRSS,ExitCode
cat /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_<job_id>.out
```

Once Gabriel reports the job exited cleanly, this tracker should be flipped to: `tasks."T0.5": done`, `last_completed_task: "T0.5"`, `current_task: "T1.1"`, `blocked: false`, `blocker: null`, `datamove1_status: ready` (or the equivalent label for the host he used), `slurm_status: ok`. The T0 gate is then complete.

## Sync status

Last synced from demo-rp5-v1: 2026-05-01 (T0.2 commit `243ed48`, 1 ahead / 0 behind).

## Next task

Task T0.5 (currently blocked — see Current blocker). Once cleared, Task T1.1. Configure required Apptainer environment.
