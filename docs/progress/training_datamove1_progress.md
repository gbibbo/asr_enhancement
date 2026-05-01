# Training Task Progress

Branch: feature/training-datamove1-v1
Integration branch: demo-rp5-v1
Current cut: T1 (T0 gate complete; T1.1 complete)
Current phase: Phase 1
Current task: Task T1.2

## Completed

- T0.1: inspected datamove1 repository state. Repo root `/mnt/fast/nobackup/users/gb0048/asr_enhancement`, remote `git@github.com:gbibbo/asr_enhancement.git`, working tree clean, branch on `feature/training-datamove1-v1`.
- T0.2: training Claude profile activated on `feature/training-datamove1-v1` (commit `243ed48`). Root `CLAUDE.md` mirrors `docs/profiles/CLAUDE.training.md`; `.gitattributes` declares `CLAUDE.md merge=ours`; local `merge.ours.driver` configured to `true`.
- T0.3: created independent training trackers `docs/progress/training_datamove1_progress.{md,yaml}` per training plan §8 format. Legacy `docs/claude_task_progress.*` left untouched as historical.
- T0.4: added training runtime ignore patterns to `.gitignore` (`runs/`, `artifacts/`, `checkpoints/`, `data/`, `.cache/`, `*.wav`, `*.flac`, `*.mp3`, `*.m4a`, `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`). No duplicates of existing rules; source, configs, docs, plans, and trackers remain trackable.
- T0.5: minimal Slurm gate job submitted through the committed wrapper and completed cleanly. Job `2125754` ran on `aisurrey01.surrey.ac.uk`, sacct state `COMPLETED`, exit code `0:0`. Output `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.out` reports Python `3.10.13` and platform `Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31` from inside the Apptainer container; stderr `…2125754.err` carries the expected `WARNING: Not mounting current directory: user bind control is disabled by system administrator` (already encoded in CLAUDE.md §8 constraint 8). The Cut T0 gate is complete.
- T1.1: Apptainer environment configured. Image `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` (~3.22 GiB) confirmed readable from datamove1 and from the Slurm execution context (re-using T0.5 job `2125754` evidence on `aisurrey01.surrey.ac.uk`). Python `3.10.13` inside the container (mismatch with plan §5 nominal 3.11 recorded; acceptance gated on T1.2 dependency imports). `slurm/templates/apptainer_job_template.job` already encodes the required absolute-path, `--env`-only, no-`--bind`, no-`--pwd`, no-`--nv` pattern; no new T1.1 probe job submitted; no venv-based training execution path introduced. YAML drift on `current_cut`/`current_phase` (T0/0 → T1/1) corrected as part of this closure.

## Current blocker

None. Cut T0 (datamove1 bootstrap) is complete; T1.1 (Apptainer environment) is complete.

## T0.5 closure evidence (2026-05-01)

Submitted through the committed wrapper from datamove1:

```bash
./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t0_minimal_job.sh
```

| Field | Value |
|---|---|
| Job ID | `2125754` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Execution node | `aisurrey01.surrey.ac.uk` |
| Output log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.out` |
| Error log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.err` |
| Python (in Apptainer) | `3.10.13` |
| Platform (in Apptainer) | `Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31` |
| Apptainer warning (stderr) | `WARNING: Not mounting current directory: user bind control is disabled by system administrator` |

The expected cwd-bind warning is already encoded as a hard constraint in CLAUDE.md §8 (item 8) and reflected in `slurm/jobs/t0_minimal_job.sh` and `slurm/templates/apptainer_job_template.job`, so all training jobs must continue to use absolute paths.

## T1.1 closure evidence (2026-05-01)

T1.1 closes by recording the Apptainer environment already exercised by T0.5 job `2125754`; no new Slurm job was submitted. Raw logs from that job were re-read end-to-end before this closure; all claims below come from the on-disk log content, not from prior tracker text.

| Field | Value |
|---|---|
| Apptainer image | `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` |
| Image size | `3459866624` bytes (~3.22 GiB) |
| Image host mtime | `2026-01-15T21:22:00` |
| Readable from datamove1 | yes (`ls -la` on the login node) |
| Readable from Slurm execution context | yes (T0.5 job `2125754` ran `apptainer exec` against this exact path on `aisurrey01.surrey.ac.uk`) |
| Apptainer required for Slurm Python jobs | yes (single execution mode; no venv-based training path introduced) |
| Python inside container | `3.10.13 (main, Sep 11 2023, 13:44:35) [GCC 11.2.0]` |
| Platform inside container | `Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31` |
| Python version nominal (plan §5) | `3.11` |
| Python version mismatch | recorded; conditionally accepted, gated on T1.2 dependency import success inside the same container (plan §11 T1.1 decision rule 4) |
| Reusable Slurm template | `slurm/templates/apptainer_job_template.job` — already sufficient (absolute paths, `--env` exports, no `--bind`/`--pwd`/`--nv`); not modified |
| New T1.1 probe job | not required; T0.5 evidence covers all T1.1 “done when” criteria |
| Source evidence (stdout) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.out` |
| Source evidence (stderr) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.err` |

Raw T0.5 log excerpts re-confirmed in this closure:

- stdout line 5: `Container: /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`
- stdout lines 14–16: `--- Python version (inside Apptainer) ---` / `Python: 3.10.13 (main, Sep 11 2023, 13:44:35) [GCC 11.2.0]` / `Platform: Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31`
- stdout line 18: `=== T0.5 minimal job complete ===` (clean exit; matches sacct `COMPLETED 0:0`)
- stderr lines 1–3: `INFO: Setting 'NVIDIA_VISIBLE_DEVICES=all' …`, `INFO: Setting --writable-tmpfs …`, `WARNING: Not mounting current directory: user bind control is disabled by system administrator`

## Sync status

Last synced from demo-rp5-v1: 2026-05-01 (T0.2 commit `243ed48`, 1 ahead / 0 behind).

## Next task

Task T1.2. Install training dependencies.
