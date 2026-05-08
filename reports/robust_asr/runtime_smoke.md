# P0.3 Runtime Smoke Report

Date: 2026-05-08
Outcome: **HALTED**
Marker: **BLOCKED_RUNTIME**
Branch: feature/robust-asr-lora-router-datamove1-v1
Plan section: agent plan v3.4.7 — "P0.3 Environment and Slurm smoke"

## Summary

The P0.3 runtime smoke job ran on Surrey Slurm
(`aisurrey-submit01.surrey.ac.uk`, partition `2080ti`, compute node
`aisurrey01.surrey.ac.uk`), executed inside the Apptainer image
`/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`
(sha256 `dade82953b391d41c064b1c45c98a7438ab3eabdbbd84877ecdde4c8b7e80443`,
size 3459866624 bytes). The container ran for 12 s and exited with code 1.

Two independent failure conditions per the agent plan's Decision rules
fired:

1. **Decision rule 2 (BLOCKED_RUNTIME).** Python inside the image is
   `3.10.13`, not `3.11.x`. The plan fixes Python 3.11 inside the
   Apptainer image (Section "Fixed technical decisions", item 2).
2. **Decision rule 4 (BLOCKED_RUNTIME).** Three required imports
   failed: `ctranslate2`, `faster_whisper`, `pytest`. These are not
   installed in the current image.

A non-blocking observation also fired: `lightgbm` and `xgboost` are
both missing from the image, while `sklearn.HistGradientBoostingRegressor`
imports successfully. Per Decision rule 3 this would map to the
informational marker `ROUTER_IMPL_FALLBACK_SKLEARN`. It is reported here
for completeness; it is not the blocker — the blocker is the Python
version and the three missing imports.

## Slurm submission

| field | value |
|---|---|
| job_name | robust_asr_p0_3_runtime_smoke |
| job_id | 2129637 |
| partition | 2080ti |
| cpus_per_task | 1 |
| mem_request | 2G |
| time_limit | 00:05:00 |
| state | FAILED |
| exit_code | 1:0 |
| submitted_at_utc | 2026-05-08T00:57:01Z |
| started_at_utc | 2026-05-08T01:57:12Z |
| completed_at_utc | 2026-05-08T01:57:24Z |
| elapsed_s | 12 |
| host | aisurrey01.surrey.ac.uk |

Submission command:
```
./slurm/tools/on_submit.sh sbatch \
  /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/p0_3_runtime_smoke.sh
```

## Apptainer image probe (datamove1 side)

| field | value |
|---|---|
| path | /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif |
| size_bytes | 3459866624 |
| sha256 | dade82953b391d41c064b1c45c98a7438ab3eabdbbd84877ecdde4c8b7e80443 |

Reuse policy row: `class=container_image`, `permitted_use=exec_only`,
`allowed_tasks` includes P0.3, `validator=sha256_recorded_in_runtime_smoke_job_metadata`,
`checksum_required=true`, `large_artifact=true`, `commit_allowed=false`.
The validator is satisfied: `image_sha256` is recorded as 64-hex in
`artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json`.

## Inside-container probe

```
PYTHON_VERSION=3.10.13     ← fails Decision rule 2 (must be 3.11)
HOST=aisurrey01.surrey.ac.uk
TORCH_CUDA_AVAILABLE=False
ROUTER_PICK=sklearn.HistGradientBoostingRegressor FALLBACK_SKLEARN=True
```

| module          | status      | version            |
|-----------------|-------------|--------------------|
| torch           | OK          | 2.5.1+cu121        |
| transformers    | OK          | 5.0.0.dev0         |
| peft            | OK          | 0.18.1             |
| ctranslate2     | **MISSING** | n/a                |
| faster_whisper  | **MISSING** | n/a                |
| librosa         | OK          | 0.11.0             |
| numpy           | OK          | 1.26.0             |
| pandas          | OK          | 2.3.3              |
| pyarrow         | OK          | 23.0.0             |
| yaml            | OK          | 6.0                |
| pytest          | **MISSING** | n/a                |
| lightgbm        | MISSING     | router fallback ok |
| xgboost         | MISSING     | router fallback ok |
| sklearn (HistGB)| OK          | (fallback chain)   |

## Decision rule mapping

| Decision rule | Triggered? | Outcome |
|---|---|---|
| 1. Apptainer image missing | No | image present |
| 2. Python != 3.11 | **Yes** | HALTED, marker=BLOCKED_RUNTIME |
| 3. lightgbm + xgboost missing, sklearn ok | Yes (informational) | would be ROUTER_IMPL_FALLBACK_SKLEARN — superseded by HALTED |
| 4. Other required import fails | **Yes** (ctranslate2, faster_whisper, pytest) | HALTED, marker=BLOCKED_RUNTIME |
| 5. exit_code != 0 for non-import reasons (submit fail) | No | submit and execution both succeeded; failure is import/version |

Final: `HALTED` with marker `BLOCKED_RUNTIME`.
The marker definition (agent plan Section 6) states
`BLOCKED_RUNTIME` is cleared when "runtime smoke job exits 0; rerun P0.3".

## Required follow-up to clear BLOCKED_RUNTIME

Either (a) replace the Apptainer image with one that ships Python 3.11
plus the three missing modules, or (b) extend the existing image (or
build a new layered image) to satisfy both conditions. Specifically,
the image must provide:

- Python 3.11.x as the default `python3` interpreter inside the container.
- `ctranslate2` (any compatible version).
- `faster_whisper` (any compatible version).
- `pytest` (any compatible version).
- Optionally, `lightgbm` or `xgboost` (otherwise this report records the
  non-blocking marker `ROUTER_IMPL_FALLBACK_SKLEARN` on rerun).

After the image is updated, rerun by submitting
`slurm/jobs/p0_3_runtime_smoke.sh` again via the wrapper.

## Artifacts

- `artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json`
- `artifacts/robust_asr/runtime_smoke/stdout.txt`
- `artifacts/robust_asr/runtime_smoke/stderr.txt`
- `slurm/jobs/p0_3_runtime_smoke.sh`
