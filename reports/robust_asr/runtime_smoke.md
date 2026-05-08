# P0.3 Runtime Smoke Report (PASS — rerun-2 against env-isolated apptainer exec)

Date: 2026-05-08
Outcome: **PASS**
Marker: null
Branch: feature/robust-asr-lora-router-datamove1-v1
Plan section: agent plan v3.4.7 — "P0.3 Environment and Slurm smoke" (rerun-2 sub-task P0.3-rerun-2)

## Summary

`slurm/jobs/p0_3_runtime_smoke.sh` (env-isolated at commit `efed06e`) ran on Surrey Slurm (job `2129641`, partition `2080ti`, host `aisurrey01.surrey.ac.uk`), exec'd inside the robust_asr Apptainer image with `--env PYTHONNOUSERSITE=1 --env PYTHONPATH= --env PYTHONUSERBASE= --env PIP_USER=0`. Python is **3.11.15** (Decision rule 2 OK), all 11 required imports succeed at the SIF's correctly-pinned versions, the `OK_RUNTIME_SMOKE` sentinel was emitted, and `exit_code == 0`. **`BLOCKED_RUNTIME` is cleared.**

The env-isolation eliminated the user-site shadowing that HALTED rerun-1: instead of seeing the `~/.local`/`python_userbase` versions (torch 2.9.1+cu128, transformers 4.50+, numpy 2.3.5), Python now sees only the SIF dist-packages (torch 2.5.1+cu121, transformers 4.49.0, numpy 1.26.4) — exactly what the build log of `2129639` recorded.

## Slurm submission

| field | value |
|---|---|
| job_name | robust_asr_p0_3_runtime_smoke |
| job_id | 2129641 |
| partition | 2080ti |
| state | COMPLETED |
| exit_code | 0:0 |
| submitted_at_utc | 2026-05-08T02:30:57Z |
| started_at_utc   | 2026-05-08T03:31:13Z |
| completed_at_utc | 2026-05-08T03:31:28Z |
| elapsed_s | 15 |
| host | aisurrey01.surrey.ac.uk |
| MaxRSS (batch) | 5020 KiB |

## Image

| field | value |
|---|---|
| image_path  | /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif |
| image_sha256 | 8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713 |
| image_size_bytes | 5624180736 |

The reuse_policy validator `sha256_recorded_in_runtime_smoke_job_metadata` is satisfied: `image_sha256` matches `tracker.artifacts.runtime_image_v1.sha256` and is recorded as 64-hex in `runtime_smoke_job_metadata.json`. Legacy SIF at `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` is untouched (mtime preserved at `2026-01-15 21:22:43 UTC`).

## Apptainer env isolation (the change that fixed rerun-1)

Added flags to `apptainer exec` in `slurm/jobs/p0_3_runtime_smoke.sh` at scope-change commit `efed06e`:

```
--env PYTHONNOUSERSITE=1
--env PYTHONPATH=
--env PYTHONUSERBASE=
--env PIP_USER=0
```

These prevent Python's user-site mechanism (and any inherited PYTHONPATH) from importing packages off the auto-bound `/mnt/fast/nobackup` mount.

## Inside-container probe (now SIF-only)

```
PYTHON_VERSION=3.11.15
HOST=aisurrey01.surrey.ac.uk
TORCH_CUDA_AVAILABLE=False
ROUTER_PICK=lightgbm FALLBACK_SKLEARN=False
RUNTIME_SMOKE_RESULTS_BEGIN
{ ... smoke_ok: true, all_required_imports_ok: true ... }
RUNTIME_SMOKE_RESULTS_END
OK_RUNTIME_SMOKE
```

| module          | result | version       | matches SIF build log? |
|-----------------|--------|---------------|------------------------|
| torch           | OK     | 2.5.1+cu121   | YES |
| transformers    | OK     | 4.49.0        | YES |
| peft            | OK     | 0.19.1        | YES |
| ctranslate2     | OK     | 4.7.1         | YES |
| faster_whisper  | OK     | 1.2.1         | YES |
| librosa         | OK     | 0.11.0        | YES |
| numpy           | OK     | 1.26.4        | YES |
| pandas          | OK     | 3.0.2         | YES |
| pyarrow         | OK     | 24.0.0        | YES |
| yaml            | OK     | 6.0.3         | YES |
| pytest          | OK     | 9.0.3         | YES |

Router pick: `lightgbm` (no fallback). `ROUTER_IMPL_FALLBACK_SKLEARN` not active.

## Decision rule mapping

| Decision rule | Triggered? | Outcome |
|---|---|---|
| 1. Apptainer image missing | No | image present (sha256 8db5364c…) |
| 2. Python != 3.11 | No | 3.11.15 OK |
| 3. lightgbm + xgboost missing, sklearn ok | No | lightgbm OK |
| 4. Other required import fails | No | all 11 OK |
| 5. exit_code != 0 for non-import reasons | No | exit 0 |

Final: **PASS**, no marker.

## P0.3 attempt history (closure)

| attempt | sub-task | job_id | image | Python | result |
|---|---|---|---|---|---|
| 1 | P0.3 (initial) | 2129637 | legacy `pytorch_2.1_cuda12.sif` | 3.10.13 | HALTED — Python ≠ 3.11; ctranslate2/faster_whisper/pytest missing |
| 2 | P0.3-rebuild #1 | 2129638 | n/a (build) | n/a | FAILED — recipe quoting bug |
| 3 | P0.3-rebuild #2 | 2129639 | n/a (build → new SIF) | n/a | COMPLETED — SIF built, sha256 8db5364c… |
| 4 | P0.3-rerun | 2129640 | new SIF, no env isolation | 3.11.15 | HALTED — user-site shadowing (transformers/peft fail) |
| 5 | P0.3-rerun-2 | 2129641 | new SIF, env-isolated apptainer exec | 3.11.15 | **PASS** — all 11 imports OK, OK_RUNTIME_SMOKE |

## Tracker mutations (PASS closure)

```yaml
current_task: P0.4                                                          # ADVANCED
last_completed_task: P0.3                                                   # ADVANCED
blocked: false                                                              # CLEARED
blocker: null                                                               # CLEARED
markers: []                                                                 # CLEARED — BLOCKED_RUNTIME removed

tasks.P0.3.status: PASS                                                     # CLOSED
tasks.P0.3.marker: null                                                     # CLEARED
tasks.P0.3.next_task: P0.4
tasks['P0.3-rebuild'].status: PASS                                          # UNCHANGED
tasks['P0.3-rerun'].status: HALTED                                          # UNCHANGED (historical)
tasks['P0.3-rerun-2'].status: PASS                                          # NEW

artifacts.runtime_smoke_report:
  outcome: PASS
  marker: null
  produced_by_task: P0.3-rerun-2

state_transport:
  latest_execution_report: reports/robust_asr/task_reports/P0.3_runtime_smoke.md
  expected_next_task: P0.4
  last_accepted_report_commit: efed06e690255a1838741acc5ebd8ffb4f2c4599   # UNCHANGED (advanced from APPROVE_EXECUTION on the env-isolation scope-change; NOT advanced to the rerun-2 commit)
  latest_approval_packet:
    ORCHESTRATOR_DECISION:
      scope: task
      task_id: P0.3-rerun-2
      decision: APPROVE_PLAN
      accepted_report_commit: efed06e690255a1838741acc5ebd8ffb4f2c4599
      next_expected_task: P0.4
```
