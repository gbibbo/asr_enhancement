# P0.3 Runtime Image Rebuild Report

Sub-task: P0.3-rebuild (parent: P0.3)
Outcome: **PASS**
Marker: null (informational; `BLOCKED_RUNTIME` on parent P0.3 remains active until rerun PASS)
Date: 2026-05-08
Branch: feature/robust-asr-lora-router-datamove1-v1

## Image identification

```yaml
image_path:        /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif
image_sha256:      8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713
image_size_bytes:  5624180736          # 5.24 GB (5.3 GiB)
recipe_path:       configs/robust_asr/runtime/apptainer_robust_asr_v1.def
recipe_sha256:     e6e7f79bae25e8f6bf3726ab8024a75f4769ad0825eddc15f8b1e50ae377f63e
```

The reuse_policy validator `sha256_recorded_in_runtime_smoke_job_metadata` is satisfied at parent-task level by the value `8db5364c…` recorded above and pinned in `tracker.artifacts.runtime_image_v1.sha256`. The SIF itself is **not** committed to git (`commit_allowed: false`).

## Reuse policy authorization

```yaml
- path: /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif
  class: container_image
  permitted_use: exec_only
  allowed_tasks: [P0.3, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1]
  validator: sha256_recorded_in_runtime_smoke_job_metadata
  checksum_required: true
  large_artifact: true
  commit_allowed: false

- path: /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/**
  class: data_root
  permitted_use: read_write
  allowed_tasks: [P0.3]
```

Both rows are commit `5ca1885` (Option A scope-change). The legacy image at `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` was **not** read, exec'd, modified, or copied by this rebuild.

## Build provenance

```yaml
build_host:                 aisurrey01.surrey.ac.uk
builder:                    apptainer version 1.4.1-1.el9
slurm_job_id:               2129639
slurm_partition:            2080ti
slurm_state:                COMPLETED
slurm_exit_code:            0:0
build_method:               fakeroot         # apptainer build --fakeroot succeeded on first attempt of retry
build_command:              "apptainer build --fakeroot ${OUT_SIF} ${RECIPE}"
base_image:                 docker://nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
base_image_labels:          # from `apptainer inspect`
  org.label-schema.usage.singularity.deffile.bootstrap: docker
  org.label-schema.usage.singularity.deffile.from:      nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
  org.opencontainers.image.ref.name:                    ubuntu
  org.opencontainers.image.version:                     22.04
  com.nvidia.cudnn.version:                             8.9.0.131
  org.label-schema.build-arch:                          amd64
  org.label-schema.build-date:                          Friday_8_May_2026_2:49:48_BST
  org.label-schema.usage.apptainer.version:             1.4.1-1.el9
build_submitted_at_utc:     2026-05-08T01:46:21Z
build_started_at_utc:       2026-05-08T01:46:23Z
build_completed_at_utc:     2026-05-08T01:54:57Z
build_elapsed_s:            514                # 8 min 34 s of wall-clock under the recipe
slurm_elapsed:              00:08:39           # ~5 s allocator overhead
slurm_max_rss_kib:          25162696           # ~24 GB (matches --mem=24G request)
```

Build was performed inside a Slurm job submitted from datamove1 via `./slurm/tools/on_submit.sh sbatch slurm/jobs/p0_3_build_runtime_image.sh`. No build step ran on the datamove1 login node.

## Build attempt history

| attempt | job_id  | wall-clock | result | reason |
|---------|---------|-----------:|--------|--------|
| 1       | 2129638 | 00:12:00   | FAILED | dash interpreted unquoted `<X` in pip pinned-version specifiers as input redirection; recipe error `/.post.script: 39: cannot open 4.50.0: No such file`. Recipe was patched to single-quote every `>=…,<…` pip spec. |
| 2       | 2129639 | 00:08:39   | COMPLETED | `apptainer build --fakeroot` succeeded (`User not listed in /etc/subuid, trying root-mapped namespace` then `BUILD_ATTEMPT_END fakeroot rc=0`); `%test` block emitted `robust_asr runtime image v1 test PASS`. |

The recipe-patch retry path is the deterministic remediation contemplated in the rebuild Planning Report (RISKS_OR_BLOCKERS: "If `apptainer build` exits non-zero for non-root reasons … fix the recipe or scale up resources, retry."). No CHANGE_SCOPE was needed for the retry — the recipe lives under the `configs/robust_asr/runtime/` write-allowed path and the same `slurm/jobs/p0_3_build_runtime_image.sh` is reused.

## Apptainer inspect excerpt (verbatim from build job stdout)

```
Description: Python 3.11 + ctranslate2 + faster_whisper + pytest + LightGBM + XGBoost
Owner: Gabriel Bibbo
Plan: docs/plans/robust_asr_agent_plan_v3_4_7.md
Project: robust_asr_lora_router
Version: v1
com.nvidia.cudnn.version: 8.9.0.131
maintainer: NVIDIA CORPORATION <cudatools@nvidia.com>
org.label-schema.build-arch: amd64
org.label-schema.build-date: Friday_8_May_2026_2:49:48_BST
org.label-schema.schema-version: 1.0
org.label-schema.usage: /.singularity.d/runscript.help
org.label-schema.usage.apptainer.runscript.help: /.singularity.d/runscript.help
org.label-schema.usage.apptainer.version: 1.4.1-1.el9
org.label-schema.usage.singularity.deffile.bootstrap: docker
org.label-schema.usage.singularity.deffile.from: nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
org.opencontainers.image.ref.name: ubuntu
org.opencontainers.image.version: 22.04
```

Sentinels emitted by the build wrapper, all observed:
- `BUILD_METHOD=fakeroot`
- `OUT_SHA256=8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`
- `OUT_SIZE_BYTES=5624180736`
- `OK_APPTAINER_INSPECT`
- `BUILD_OK_8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`

## Recipe %test result (informational, not the parent-task validator)

The recipe's `%test` block ran inside the new image at the end of the build:

```
Python 3.11.15
robust_asr runtime image v1 test PASS
```

This confirms inside-container Python is 3.11.15 and that all required imports succeed:

- `torch` (>=2.) → torch 2.5.1+cu121
- `ctranslate2` → OK
- `faster_whisper` → OK
- `peft` → OK
- `transformers` → OK
- `librosa` → OK (0.11.0)
- `numpy` → OK (1.26.x)
- `pandas` → OK
- `pyarrow` → OK
- `yaml` (pyyaml 6.0.3) → OK
- `pytest` → OK (9.0.3)
- `lightgbm` → OK
- `xgboost` → OK

This `%test` outcome is **not** the parent task's PASS criterion. The agent plan requires the official P0.3 runtime smoke (`slurm/jobs/p0_3_runtime_smoke.sh`) to exit 0 against the new image with `image_sha256` recorded in `runtime_smoke_job_metadata.json` to clear `BLOCKED_RUNTIME`. That validation belongs to the next sub-task (`P0.3-rerun`).

## Files committed by this sub-task

- `configs/robust_asr/runtime/apptainer_robust_asr_v1.def`
- `scripts/robust_asr/build_runtime_image.sh`
- `slurm/jobs/p0_3_build_runtime_image.sh`
- `reports/robust_asr/runtime_image_rebuild.md` (this file)
- `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md`
- `docs/progress/robust_asr_progress.yaml` (APPROVE_PLAN packet + tasks["P0.3-rebuild"]=PASS + artifacts.runtime_image_v1 + state_transport.latest_execution_report)
- `docs/progress/robust_asr_progress.md`
- `docs/progress/robust_asr_state_capsule.md`

Files **not** committed (per reuse_policy):
- `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif` (5.3 GB; large_artifact, commit_allowed=false)
- `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/build_logs/p0_3_build_*.{out,err}` (build logs; under runtime/** read_write data_root, not committed by policy)
- `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/build_cache/**` (apptainer build cache; same)

## Tracker invariants preserved

```yaml
current_task: P0.3                        # UNCHANGED (sub-task PASS does not advance)
last_completed_task: P0.2                 # UNCHANGED
tasks.P0.3.status: HALTED                 # UNCHANGED (only rerun PASS may set PASS)
markers: [BLOCKED_RUNTIME]                # UNCHANGED
blocked: true                             # UNCHANGED
state_transport.last_accepted_report_commit: 635a711cd4fe44e919966a0e6bc3df99103fe6d3   # UNCHANGED
state_transport.expected_next_task: P0.3  # UNCHANGED
```

The legacy SIF was not modified:

```
$ stat /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
   modify time unchanged from 2026-01-15 (last touched at image build); not opened by P0.3-rebuild.
```

## Next sub-task

`P0.3-rerun` — repoint `slurm/jobs/p0_3_runtime_smoke.sh`'s `CONTAINER` variable to the new SIF path, resubmit via the wrapper, parse `runtime_smoke_job_metadata.json` for `exit_code==0` and `python_version` starting `3.11.`, then advance the tracker (clear `BLOCKED_RUNTIME`, set `current_task=P0.4`, `last_completed_task=P0.3`). Awaiting orchestrator APPROVE_PLAN.
