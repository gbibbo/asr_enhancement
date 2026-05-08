# P0.3 Runtime Smoke Report (rerun against new image)

Date: 2026-05-08
Outcome: **HALTED**
Marker: **BLOCKED_RUNTIME**
Branch: feature/robust-asr-lora-router-datamove1-v1
Plan section: agent plan v3.4.7 — "P0.3 Environment and Slurm smoke" (rerun sub-task P0.3-rerun)

## Summary

The repointed `slurm/jobs/p0_3_runtime_smoke.sh` ran on Surrey Slurm (job `2129640`, partition `2080ti`, host `aisurrey01.surrey.ac.uk`) inside the **new** robust_asr Apptainer image at the authorized path. Python is **3.11.15** (Decision rule 2 cleared) and `ctranslate2`, `faster_whisper`, `pytest`, `lightgbm` (and others) all import — the gaps that HALTED attempt 1 are gone.

However, the smoke job exited with code 1: `transformers` and `peft` failed to import with `tokenizers>=0.22.0,<=0.23.0 is required ... but found tokenizers==0.21.4`. Decision rule 4 fires → **HALTED, BLOCKED_RUNTIME**.

Root cause is **not** the SIF. The SIF was built with correctly pinned packages (`torch-2.5.1+cu121`, `transformers-4.49.0`, `tokenizers-0.21.4` — compatible with 4.49 — and `numpy-1.26.4`; verified via build log `p0_3_build_2129639.out`). The runtime smoke instead saw `torch 2.9.1+cu128`, `numpy 2.3.5`, and a transformers ≥4.50 that demands a newer tokenizers. These versions come from outside the container.

The `/mnt/fast/nobackup` filesystem is auto-bound by Apptainer (per Surrey policy and CLAUDE.md §8). User-site Python packages exist on that mount:

- `/mnt/fast/nobackup/users/gb0048/.local/lib/python3.11/site-packages/` (transformers, numpy, …)
- `/mnt/fast/nobackup/scratch4weeks/gb0048/python_userbase/lib/python3.11/site-packages/` (transformers, …)

Inside the container, Python's user-site mechanism finds these and imports them in preference to the SIF's `/usr/local/lib/python3.11/dist-packages`. The shadowed `transformers` (≥4.50) is incompatible with the shadowed `tokenizers` (0.21.4), producing the `ImportError`.

## Slurm submission

| field | value |
|---|---|
| job_name | robust_asr_p0_3_runtime_smoke |
| job_id | 2129640 |
| partition | 2080ti |
| state | FAILED |
| exit_code | 1:0 |
| submitted_at_utc | 2026-05-08T02:12:43Z |
| started_at_utc   | 2026-05-08T03:12:45Z |
| completed_at_utc | 2026-05-08T03:12:55Z |
| elapsed_s | 10 |
| host | aisurrey01.surrey.ac.uk |

## Image

| field | value |
|---|---|
| image_path  | /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif |
| image_sha256 | 8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713 |
| image_size_bytes | 5624180736 |

The reuse_policy validator `sha256_recorded_in_runtime_smoke_job_metadata` is satisfied: `image_sha256` is recorded as 64-hex in `artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json` and matches `tracker.artifacts.runtime_image_v1.sha256`.

The legacy SIF at `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` was not opened, exec'd, modified, or copied (mtime preserved at `2026-01-15 21:22:43 UTC`).

## Inside-container probe (observed via auto-bound user-site)

```
PYTHON_VERSION=3.11.15
HOST=aisurrey01.surrey.ac.uk
TORCH_CUDA_AVAILABLE=False
ROUTER_PICK=lightgbm FALLBACK_SKLEARN=False
```

| module          | observed result | observed version | notes |
|-----------------|-----------------|------------------|-------|
| torch           | OK              | 2.9.1+cu128      | **MISMATCH**: SIF holds 2.5.1+cu121 |
| transformers    | **FAIL**        | n/a              | shadowed transformers ≥4.50 + shadowed tokenizers 0.21.4 → ImportError |
| peft            | **FAIL**        | n/a              | propagates the transformers import error |
| ctranslate2     | OK              | 4.7.1            | matches SIF |
| faster_whisper  | OK              | 1.2.1            | matches SIF |
| librosa         | OK              | 0.11.0           | matches SIF |
| numpy           | OK              | 2.3.5            | **MISMATCH**: SIF holds 1.26.4 |
| pandas          | OK              | 3.0.0            | close to SIF (3.0.2) |
| pyarrow         | OK              | 24.0.0           | matches SIF |
| yaml            | OK              | 6.0.3            | matches SIF |
| pytest          | OK              | 9.0.3            | matches SIF |

Router fallback: did not fire (`lightgbm` resolved successfully). `ROUTER_IMPL_FALLBACK_SKLEARN` not active.

## Decision rule mapping (rerun)

| Decision rule | Triggered? | Outcome |
|---|---|---|
| 1. Apptainer image missing | No | image present (sha256 8db5364c…) |
| 2. Python != 3.11 | No | 3.11.15 OK |
| 3. lightgbm + xgboost missing, sklearn ok | No | lightgbm OK |
| 4. Other required import fails | **Yes** (transformers, peft) | HALTED, marker=BLOCKED_RUNTIME |
| 5. exit_code != 0 for non-import reasons | No | failure is import-side; submit and exec succeeded |

## Required follow-up to clear BLOCKED_RUNTIME

The SIF is correct. The remediation is at the apptainer-exec boundary. Add to the `apptainer exec` invocation in `slurm/jobs/p0_3_runtime_smoke.sh` (and to all future Slurm jobs that use this image):

```
--env PYTHONNOUSERSITE=1
--env PYTHONUSERBASE=
--env PYTHONPATH=
```

`PYTHONNOUSERSITE=1` disables Python's user-site search (the most direct fix). Clearing `PYTHONUSERBASE` and `PYTHONPATH` defends against host-side environment leakage. Optionally also add `--cleanenv` to apptainer exec to scrub all host environment variables (may have side effects on CUDA/HF caches; preferred to set the three vars explicitly).

This edit goes beyond the P0.3-rerun plan's stated single-line CONTAINER repoint scope (the plan's `RISKS_OR_BLOCKERS` listed accidentally adding lines as a violation). Therefore a CHANGE_SCOPE Approval Packet is required before applying it. Possible scopes:

- (A) Edit only `slurm/jobs/p0_3_runtime_smoke.sh` to add the three `--env` flags. Smallest blast radius; affects only P0.3.
- (B) Add a thin wrapper helper (e.g. `slurm/jobs/_robust_asr_apptainer_exec.sh.inc`) sourced by all robust_asr Slurm jobs. Better long-term hygiene since every later sub-task (P2.1, P3.1, P4.x, P5.1, P7.2, P8.1) will hit the same shadowing.
- (C) Rebuild the image with `%environment` setting `PYTHONNOUSERSITE=1`. Most robust but most expensive and least surgical.

Option B is recommended (the shadowing affects every Slurm task that uses this image; fixing it once at the apptainer-exec entry point prevents repeated remediation), but Option A is the smallest deviation and acceptable for clearing P0.3.

## Artifacts

- `artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json` (HALTED, exit_code=1)
- `artifacts/robust_asr/runtime_smoke/stdout.txt` (rewritten from p0_3_runtime_smoke_2129640.out)
- `artifacts/robust_asr/runtime_smoke/stderr.txt` (rewritten from p0_3_runtime_smoke_2129640.err)
- `slurm/jobs/p0_3_runtime_smoke.sh` (CONTAINER var repointed; build log `p0_3_build_2129639.out` confirms SIF contents)

## Tracker invariants preserved (rerun HALTED)

```yaml
current_task: P0.3                                                          # UNCHANGED
last_completed_task: P0.2                                                   # UNCHANGED
tasks.P0.3.status: HALTED                                                   # UNCHANGED
tasks['P0.3-rebuild'].status: PASS                                          # UNCHANGED (commit 805cddf)
tasks['P0.3-rerun'].status: HALTED                                          # NEW
markers: [BLOCKED_RUNTIME]                                                  # UNCHANGED
blocked: true                                                               # UNCHANGED
state_transport.last_accepted_report_commit: 805cddf7cab78d0ad4560dcf73092d3f8747e05e
                                                                             # UNCHANGED (advanced this turn from APPROVE_EXECUTION(P0.3-rebuild); not advanced to the rerun commit)
state_transport.expected_next_task: P0.3
```
