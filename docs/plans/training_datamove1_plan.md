# ASR Enhancement Training on datamove1: Deterministic Implementation Plan

## 0. How to use this plan

This file is the execution plan for the datamove1 training branch. Read it after `CLAUDE.md` and before implementation work on Surrey infrastructure.

`CLAUDE.md` defines standing execution rules, repository policy, HPC rules, storage rules, Git identity policy, and scope guardrails. This file defines the training branch order, task boundaries, decision rules, gates, verification criteria, and progress tracker rules.

This plan covers only the training and evaluation work that runs on datamove1 or Surrey compute.

Execution rule:

1. Read `CLAUDE.md`.
2. Read `docs/plans/training_datamove1_plan.md`.
3. Read `docs/progress/training_datamove1_progress.md` and `docs/progress/training_datamove1_progress.yaml` if they exist.
4. Identify the first pending task.
5. Execute only that task.
6. Run the verification for that task.
7. Update the training progress trackers.
8. Commit only source code, configs, documentation, small reports, and tracker updates.
9. Do not commit datasets, checkpoints, cache folders, local secrets, large run artifacts, or generated audio.
10. Stop at gates and report status.

If a task depends on an earlier task that is not complete, do the earlier task first and update the tracker.

Bootstrap ordering note:

```text
If origin/demo-rp5-v1 does not exist, do not start this training plan.
Run Phase S0 of docs/plans/demo_platform_plan.md first, push demo-rp5-v1, then return to T0.
```

## 1. Branch role

This branch exists to build and evaluate the enhancement model or enhancement baseline on datamove1 while the public demo and repository refactor continue in a separate branch.

Working branch:

```text
feature/training-datamove1-v1
```

Integration branch:

```text
demo-rp5-v1
```

Preservation tag:

```text
platform-mvp-v0
```

Parallel branch for non-training work:

```text
feature/demo-runtime-rp5-v1
```

Rule:

```text
The training branch must merge or rebase from demo-rp5-v1 before any task that depends on shared audio code, shared metrics, shared degradation definitions, or cache version contracts.
```

Recommended simple Git workflow:

```bash
git fetch origin
git checkout demo-rp5-v1
git pull --ff-only origin demo-rp5-v1
git checkout -b feature/training-datamove1-v1
git push -u origin feature/training-datamove1-v1
```

To sync later from the integration branch:

```bash
git fetch origin
git checkout feature/training-datamove1-v1
git merge origin/demo-rp5-v1
git status
git push
```

Decision rules:

1. If the branch does not exist, create it from `demo-rp5-v1`.
2. If the branch already exists locally, fetch and merge `origin/demo-rp5-v1` before continuing.
3. If merge conflicts touch shared files under `libs/audio/`, stop and report the conflict before editing.
4. If merge conflicts only touch training trackers, preserve both histories and update current state manually.
5. Do not merge directly into `master`.
6. Open pull requests into `demo-rp5-v1`, not into `master`.

## 2. Project goal

Train, evaluate, or validate an enhancement stage for English speech degraded by controlled acoustic transformations, with the explicit goal of improving ASR robustness or documenting when improvement is limited.

The training branch must produce:

1. a reproducible datamove1 environment;
2. a versioned dataset manifest;
3. clean versus degraded ASR baselines;
4. MetricGAN+ pretrained evaluation;
5. dry-run training artifacts;
6. full training artifacts if compute access allows;
7. checkpoint selection logic;
8. an exported enhancer artifact usable by the Raspberry Pi demo;
9. a completed model card section for the selected enhancer;
10. a clear handoff procedure back to the demo branch.

The branch must support three possible outcomes:

1. fine-tuned enhancer with average Word Accuracy improvement of at least 5 points;
2. pretrained enhancer with partial but honest improvements;
3. bypass or framework-only result, clearly documented as evaluation and deployment infrastructure rather than a claimed ASR improvement.

## 3. Relationship to the public demo branch

The public demo branch owns:

1. repository refactor;
2. ASR provider abstraction;
3. demo endpoints;
4. Raspberry Pi runtime;
5. frontend;
6. cache;
7. upload handling;
8. AssemblyAI cost controls;
9. public deployment;
10. README and demo assets.

The training branch owns:

1. datamove1 environment;
2. Slurm scripts;
3. training configs;
4. dataset preparation scripts;
5. evaluation scripts that run on Surrey compute;
6. training runs;
7. checkpoint selection;
8. export package;
9. model card training content.

Shared code ownership:

```text
libs/audio/metrics.py
libs/audio/degradations.py
libs/audio/enhancement.py
libs/common/versions.py
```

Rules:

1. The public demo branch creates the first stable versions of shared audio modules.
2. The training branch may import those modules after syncing from `demo-rp5-v1`.
3. The training branch may extend shared modules only when needed for training or evaluation.
4. Any change to shared modules must keep demo tests passing.
5. Any change to `degradations.py` must bump `DEGRADATION_VERSION` in `libs/common/versions.py`.
6. Any change to `metrics.py` must bump `METRICS_VERSION` in `libs/common/versions.py`.
7. The training branch must not define local duplicate metric or degradation versions.

## 4. Repository location and plan placement

The split plans must live inside the repository, not beside it.

Required plan files:

```text
docs/plans/training_datamove1_plan.md
docs/plans/demo_platform_plan.md
```

Required training trackers:

```text
docs/progress/training_datamove1_progress.md
docs/progress/training_datamove1_progress.yaml
```

Recommended heavy runtime roots on Surrey:

```text
/mnt/fast/nobackup/users/gb0048/asr_enhancement
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
```

Decision rules:

1. If the repo root is unknown, run `git rev-parse --show-toplevel` and use that path.
2. If the checked-out repo already exists on datamove1, reuse it.
3. If both local Windows and datamove1 copies exist, GitHub is the source of synchronization.
4. Do not manually copy edited source files between machines unless Git is unavailable.
5. Large artifacts live outside the repo and are referenced by path, checksum, run ID, or release tag.

## 5. Fixed technical decisions

These decisions are closed for the training branch:

1. Training host: datamove1 plus Surrey compute through Slurm where available.
2. Python version: Python 3.11.
3. Reference ASR for Surrey evaluation: `openai-whisper`.
4. Public demo ASR for Raspberry Pi: `faster-whisper tiny.en`, validated separately in the demo branch.
5. Official language: English speech.
6. Degradation families: `far_field_room`, `cafe_background`, `phone_call`, `muffled`, `broadband_hiss`.
7. Primary metrics: WER and Word Accuracy.
8. Metric implementation: `libs/audio/metrics.py`.
9. Degradation implementation: `libs/audio/degradations.py`.
10. Cache and model version source: `libs/common/versions.py` plus runtime `ENHANCER_VERSION`.
11. Scheduler: Slurm.
12. Environment isolation on datamove1 / Surrey Slurm: Apptainer is required.
13. Default Apptainer image: `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`, unless a newer valid image is recorded in the tracker before T1.2.
14. No secrets in Git.
15. No large audio, datasets, checkpoints, cache, or full run directories in Git.

Decision rules:

1. On datamove1 / Surrey Slurm, use Apptainer for Python jobs submitted through Slurm.
2. Use a Python 3.11 venv only for local non-Slurm helper commands, and only if it does not replace the required Slurm Apptainer path.
3. If the default Apptainer image is unavailable, stop T1.1 and record the exact missing path or permission issue.
4. If a dependency cannot be installed on login nodes, move installation into an Apptainer build step, a Slurm build job, or an external lock-generation step.
5. If GPU access is unavailable, complete baseline, pretrained evaluation, and CPU dry-runs before attempting full training.
6. If Slurm is unavailable, stop before training tasks and record the blocker.
7. If datamove1 storage is insufficient, move runtime data to scratch and keep manifests in a stable project path.

## 6. Training repository layout target

Use this layout for training-specific files:

```text
asr_enhancement/
  docs/
    plans/
      training_datamove1_plan.md
      demo_platform_plan.md
    progress/
      training_datamove1_progress.md
      training_datamove1_progress.yaml
    model_card.md
  configs/
    training/
      baseline.yaml
      metricgan_pretrained.yaml
      dry_run.yaml
      full_training.yaml
  scripts/
    training/
      prepare_librispeech_manifest.py
      exclude_public_examples.py
      run_whisper_baseline.py
      run_metricgan_eval.py
      train_enhancer.py
      select_checkpoint.py
      export_enhancer.py
      summarize_run.py
  slurm/
    jobs/
    templates/
    tools/
  reports/
    training/
  libs/
    audio/
    common/
```

Runtime-only paths, ignored by Git:

```text
runs/
artifacts/
checkpoints/
.cache/
data/
outputs/
*.wav
*.flac
*.mp3
```

Decision rules:

1. If a directory already exists and is compatible, reuse it.
2. If a training script belongs under `scripts/training/`, do not place it at repo root.
3. If a Slurm script is a reusable template, put it under `slurm/templates/`.
4. If a Slurm script is a concrete job submission script, put it under `slurm/jobs/`.
5. If a report is small and useful for GitHub, put it under `reports/training/`.
6. If a report contains audio, checkpoints, or large CSVs, keep it outside Git and reference it from a summary.

## 7. Training cuts

Implementation is split into four cuts. A later cut must not start before the previous cut gate passes, except where explicitly marked as parallel setup.

### Cut T0. Branch, tracker, and datamove1 gate

Immediate target: prove that the branch is safe, the repo root is correct, Slurm is available, and progress can be tracked independently from the demo branch.

### Cut T1. Environment and dataset foundation

Target: create a reproducible training environment and a dataset manifest that excludes public demo examples.

### Cut T2. Evaluation baseline and pretrained enhancer

Target: measure clean, degraded, and pretrained enhanced ASR behavior before any fine-tuning.

### Cut T3. Training, checkpoint selection, export, and handoff

Target: run a dry-run, run full training if available, select a checkpoint, export it, update the model card, and hand off the enhancer to the Raspberry Pi demo.

## 8. Progress tracker format

Maintain both training trackers.

YAML shape:

```yaml
branch: feature/training-datamove1-v1
integration_branch: demo-rp5-v1
current_cut: T0
current_phase: 0
current_task: "T0.1"
last_completed_task: null
blocked: false
blocker: null
synced_from_demo_rp5_v1: null
datamove1_status: unknown
slurm_status: unknown
artifact_root: null
tasks:
  "T0.1": pending
  "T0.2": pending
  "T0.3": pending
```

Markdown shape:

```markdown
# Training Task Progress

Branch: feature/training-datamove1-v1
Integration branch: demo-rp5-v1
Current cut: T0
Current phase: Phase 0
Current task: Task T0.1

## Completed

None yet.

## Current blocker

None.

## Sync status

Last synced from demo-rp5-v1: not recorded.

## Next task

Task T0.1. Inspect datamove1 repository state.
```

After every task:

1. update completed task;
2. update next task;
3. record commands run;
4. record tests or checks run;
5. record output artifact paths;
6. record failures or unverified parts;
7. record whether the branch was synced from `demo-rp5-v1`;
8. do not mark a gate complete without passing checks.

Decision rules:

1. If a task passes verification, mark it complete.
2. If a task fails verification, keep it current and record failure.
3. If a task cannot run because of a missing dependency, mark `blocked: true`.
4. If a gate passes, stop and report.
5. If a gate fails, do not advance.

## 9. Phase 0. Branch and datamove1 bootstrap

Goal: make training work safe to run in parallel.

### Task T0.1. Inspect datamove1 repository state

Actions:

1. connect to datamove1;
2. locate the repository root;
3. run `git rev-parse --show-toplevel`;
4. inspect current branch;
5. inspect Git remote;
6. inspect uncommitted changes;
7. inspect whether `docs/plans/` and `docs/progress/` already exist;
8. do not delete existing code.

Suggested commands:

```bash
pwd
git rev-parse --show-toplevel
git status --short
git branch --show-current
git remote -v
ls -la
ls -la docs || true
```

Done when:

1. repo root is recorded;
2. active branch is recorded;
3. remote is recorded;
4. dirty working tree status is recorded;
5. next task can be applied to the actual checkout.

Decision rules:

1. If the remote is not `gbibbo/asr_enhancement`, record the mismatch and stop.
2. If the repo has uncommitted user changes, stop and report before changing files.
3. If this is not a Git repo, stop and report the exact path.
4. If the repo is already on `feature/training-datamove1-v1`, continue after fetching.

### Task T0.2. Create or sync the training branch and activate training Claude profile

Actions:

1. fetch GitHub state;
2. confirm `demo-rp5-v1` exists locally or remotely;
3. create `feature/training-datamove1-v1` from `demo-rp5-v1` if missing;
4. otherwise sync the existing training branch with `origin/demo-rp5-v1`;
5. push the branch if it is new;
6. confirm `docs/profiles/CLAUDE.training.md` exists;
7. replace root `CLAUDE.md` with the content of `docs/profiles/CLAUDE.training.md`;
8. create or update `.gitattributes` with `CLAUDE.md merge=ours`;
9. configure the local merge driver with `git config merge.ours.driver true`;
10. commit the training profile activation.

Suggested commands:

```bash
git fetch origin
git checkout demo-rp5-v1 || git checkout -b demo-rp5-v1 origin/demo-rp5-v1
git pull --ff-only origin demo-rp5-v1
git checkout feature/training-datamove1-v1 || git checkout -b feature/training-datamove1-v1 origin/feature/training-datamove1-v1 || git checkout -b feature/training-datamove1-v1
git push -u origin feature/training-datamove1-v1
cp docs/profiles/CLAUDE.training.md CLAUDE.md
printf "CLAUDE.md merge=ours\n" > .gitattributes
git config merge.ours.driver true
git add CLAUDE.md .gitattributes
git commit -m "chore: activate training Claude profile"
git push origin feature/training-datamove1-v1
```

Done when:

1. training branch exists;
2. branch tracks `origin/feature/training-datamove1-v1`;
3. current branch is `feature/training-datamove1-v1`;
4. root `CLAUDE.md` is the datamove1/training active profile;
5. `.gitattributes` contains `CLAUDE.md merge=ours`;
6. tracker records branch state.

Decision rules:

1. If `demo-rp5-v1` does not exist, stop and request completion of the split bootstrap in the demo plan.
2. If `docs/profiles/CLAUDE.training.md` does not exist, stop and request completion of S0.3 in the demo plan.
3. If branch creation fails because the branch exists remotely, check it out from origin.
4. If branch is behind `demo-rp5-v1`, merge `origin/demo-rp5-v1`.
5. If `CLAUDE.md` conflicts during branch sync, keep the training version on `feature/training-datamove1-v1`.
6. Do not rely on GitHub web merge to resolve `CLAUDE.md` conflicts. Sync branches locally when this file is involved.
7. If merge conflicts occur outside `CLAUDE.md`, stop and report.

### Task T0.3. Create independent training trackers

Actions:

1. create `docs/progress/` if missing;
2. create `docs/progress/training_datamove1_progress.md` if missing;
3. create `docs/progress/training_datamove1_progress.yaml` if missing;
4. initialize current cut as `T0`;
5. initialize current task as `T0.1` or the first incomplete task;
6. keep existing root trackers untouched unless explicitly required.

Done when:

1. both training trackers exist;
2. tracker format is valid;
3. next pending task is visible;
4. tracker does not conflict with demo branch trackers.

Decision rules:

1. If trackers already exist, update them without deleting history.
2. If trackers disagree, use Markdown for history and YAML for current state.
3. If tracker current task is earlier than completed history, correct YAML and record the correction.
4. If `docs/claude_task_progress.*` exists, leave it as legacy or root tracker and do not reuse it for the training branch.

### Task T0.4. Configure ignored runtime artifact paths

Actions:

1. inspect `.gitignore`;
2. ensure training runtime artifacts are ignored;
3. add ignore rules for `runs/`, `artifacts/`, `checkpoints/`, local datasets, cache folders, and generated audio;
4. do not ignore source configs or small reports.

Required ignore patterns:

```text
runs/
artifacts/
checkpoints/
data/
.cache/
*.wav
*.flac
*.mp3
*.m4a
*.pt
*.pth
*.ckpt
*.onnx
```

Done when:

1. heavy training outputs are ignored;
2. configs and scripts remain trackable;
3. `.gitignore` contains no secrets;
4. tracker records the change.

Decision rules:

1. If `.gitignore` already contains equivalent rules, do not duplicate them.
2. If a small report directory is ignored accidentally, narrow the rule.
3. If a required artifact is too large for GitHub, keep it ignored and document external location.

### Task T0.5. Verify Slurm and minimal job execution

`sbatch`/`squeue`/`sacct` are not in PATH on `datamove1.surrey.ac.uk`. All Slurm commands must go through the repo wrapper `slurm/tools/on_submit.sh`, which forwards via `ssh -o BatchMode=yes aisurrey-submit01.surrey.ac.uk "$@"`. Jobs execute on `aisurrey` compute nodes (e.g. `aisurrey01`) where `/usr/bin/apptainer` is available. See CLAUDE.md §9.

Actions:

1. confirm the wrapper exists at `slurm/tools/on_submit.sh` and is executable;
2. probe the scheduler from datamove1 via the wrapper;
3. ensure a minimal Slurm job exists at `slurm/jobs/t0_minimal_job.sh` that prints hostname, date, working directory, available disk, and the Python version reported from inside Apptainer;
4. submit the job through the wrapper;
5. collect output from the absolute log path under `$ASR_TRAINING_ROOT/logs/`;
6. record job ID, execution node, and output path.

Suggested checks (run from datamove1):

```bash
./slurm/tools/on_submit.sh squeue -u "$USER"
./slurm/tools/on_submit.sh sinfo || true
./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t0_minimal_job.sh
./slurm/tools/on_submit.sh sacct -j <job_id> --format=JobID,JobName,State,Elapsed,MaxRSS,ExitCode
cat /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_<job_id>.out
```

Done when:

1. wrapper-based scheduler probe succeeds (or its blocker is recorded);
2. a minimal job submitted through the wrapper either succeeds or its failure is recorded;
3. output path is recorded;
4. datamove1 gate status is clear.

Decision rules:

1. If the wrapper-based probe and minimal job both succeed, mark the datamove1 gate complete.
2. If the wrapper or SSH access to `aisurrey-submit01.surrey.ac.uk` is unavailable, mark blocked.
3. If submission via the wrapper fails on the submit host or compute node, record the exact scheduler or Apptainer error.
4. If the job remains pending too long, record queue state via `./slurm/tools/on_submit.sh squeue` and stop.

Cut T0 gate: stop after this task and report datamove1 readiness.

## 10. Phase 1. Environment

Goal: create a reproducible environment that can run one audio processing job.

### Task T1.1. Configure required Apptainer environment

Actions:

1. verify that Apptainer is available on datamove1 / Surrey Slurm;
2. verify that `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` exists and is readable;
3. verify Python 3.11 inside the container, or record the exact Python version if the image differs;
4. create a minimal Slurm command template that runs Python through Apptainer;
5. record the selected container path in `docs/progress/training_datamove1_progress.yaml`.

Done when:

1. Apptainer is confirmed as the Slurm execution mode;
2. container path is recorded;
3. Python inside the container is known;
4. no duplicate venv-based Slurm strategy is started.

Decision rules:

1. If the default Apptainer image exists and runs Python, use it.
2. If the default image is missing, stop and record the blocker before attempting training.
3. If a local venv is useful for editing or non-Slurm helper commands, it may be created, but it must not become the training execution path.
4. If Python inside the image is not 3.11, record the mismatch and continue only if project dependencies and tests still pass inside the container.

### Task T1.2. Install training dependencies

Actions:

1. install project dependencies;
2. install `openai-whisper` for Surrey reference evaluation;
3. install PyTorch only if needed by the selected enhancer or training path;
4. install audio IO dependencies;
5. freeze x86_64 dependency versions if the main branch has not already done so;
6. record exact install command.

Done when:

1. Python imports project modules;
2. `openai-whisper` imports;
3. PyTorch import status is known;
4. dependency versions are recorded;
5. no secrets are printed.

Decision rules:

1. If `requirements.lock.x86_64` exists, install from it.
2. Else install from project dependencies and generate or update `requirements.lock.x86_64` only if this branch owns that task.
3. If PyTorch install fails and the current task does not need training, continue with baseline-only dependencies and record limitation.
4. If Whisper model download is needed, use cache outside the repo.

### Task T1.3. Run one audio processing job through Slurm

Actions:

1. create or reuse a tiny test WAV outside Git;
2. submit a Slurm job that imports the project and reads the audio;
3. run a minimal metrics or audio duration check;
4. write output to ignored runtime path;
5. record the result.

Done when:

1. Slurm can run Python project code;
2. one audio file can be read;
3. output is created outside Git;
4. no training has started yet.

Decision rules:

1. If import fails, fix environment before continuing.
2. If audio IO fails, fix dependencies before continuing.
3. If Slurm output path is inside the repo, move it outside or ensure it is ignored.
4. If the job succeeds, close Phase 1.

## 11. Phase 2. Dataset and manifests

Goal: prepare the training and evaluation data without contaminating public demo examples.

### Task T2.1. Prepare LibriSpeech source configuration

Actions:

1. define source paths for LibriSpeech;
2. verify files exist;
3. define allowed splits;
4. define output manifest path;
5. record dataset root outside Git;
6. do not download large datasets into the repository.

Done when:

1. source paths are validated;
2. split list is explicit;
3. output manifest path is defined;
4. missing data status is clear.

Decision rules:

1. If LibriSpeech already exists on Surrey storage, use existing copy.
2. If it does not exist, create a documented download or staging step outside the repo.
3. If storage is insufficient, stop and record required space.
4. If split names are ambiguous, use standard LibriSpeech split names and record them.

### Task T2.2. Create dataset manifest

Actions:

1. implement `scripts/training/prepare_librispeech_manifest.py`;
2. collect audio paths, durations, speaker IDs, split names, and transcript text;
3. assign stable example IDs;
4. save manifest outside heavy data folders but in a trackable or referenced location;
5. write a small manifest summary to `reports/training/`.

Done when:

1. manifest exists;
2. row count is recorded;
3. duration statistics are recorded;
4. speaker count is recorded;
5. transcript availability is verified.

Decision rules:

1. If the full manifest is small enough, it may be committed.
2. If the full manifest is large, keep it outside Git and commit only a summary plus generation script.
3. If transcript text is missing for a row, exclude the row or mark it unusable.
4. If audio duration cannot be read, exclude the row and record count.

### Task T2.3. Exclude public demo examples

Actions:

1. read `demo_examples.json` if it exists;
2. otherwise read the public-example manifest path declared by the demo branch;
3. if public examples are not yet selected, create `configs/training/public_examples_excluded.yaml` as an explicit placeholder;
4. remove public examples from training and validation manifests by ID and by audio hash where available;
5. write exclusion report;
6. fail if any public example remains in training data.

Required placeholder format if B6 is not closed yet:

```yaml
status: pending_public_examples
source_manifest: null
filled_after_demo_task: B6.2
excluded_ids: []
excluded_audio_sha256: []
notes: "Filled after B6 closes. T3 baseline tasks must not run while this file remains pending."
```

Done when:

1. `configs/training/public_examples_excluded.yaml` exists;
2. status is `complete`, not `pending_public_examples`;
3. public examples are excluded;
4. exclusion count is recorded;
5. no public example ID or audio hash remains in training or validation manifests;
6. report is committed if small.

Decision rules:

1. If public examples are not yet selected, create the placeholder YAML and stop before T3.
2. T3.1 must fail fast if `configs/training/public_examples_excluded.yaml` has `status: pending_public_examples`.
3. If public examples are selected by audio hash rather than ID, exclude by hash.
4. If IDs and hashes disagree, stop and report.
5. If the demo branch changes public examples later, rerun this task and bump the dataset version.

### Task T2.4. Define dataset version

Actions:

1. create a dataset version string;
2. include source, split policy, exclusion policy, and manifest checksum;
3. write version metadata to config or report;
4. include dataset version in all later run summaries.

Example:

```text
dataset_version: librispeech_asr_demo_v1_excluding_public_examples
```

Done when:

1. dataset version is recorded;
2. manifest checksum is recorded;
3. later scripts can read the version.

Decision rules:

1. If manifest changes, bump or revise dataset version.
2. If public example exclusions change, bump or revise dataset version.
3. If only comments or docs change, do not bump dataset version.

### Task T2.5. Create model card template

Actions:

1. create `docs/model_card.md` if missing;
2. use a Hugging Face compatible structure;
3. include intended use;
4. include not intended use;
5. include training data;
6. include degradation bank;
7. include training procedure;
8. include evaluation setup;
9. include eval results table placeholders;
10. include limitations;
11. include ethical considerations;
12. include deployment target;
13. define placeholders that can be completed from `runs/<run_id>/run_summary.md`.

Done when:

1. model card template exists;
2. it names the deployment target;
3. it can be completed from later run artifacts;
4. T5 dry-run is unblocked with respect to documentation.

Decision rules:

1. If `docs/model_card.md` already exists, update it without deleting useful content.
2. If no training has run yet, use placeholders and mark them clearly.
3. If the final result is bypass-only, model card must not claim a trained enhancer.
4. If the final result is pretrained-only, model card must name the pretrained model and limitation.

Cut T1 gate: environment, dataset, exclusion policy, dataset version, and model card template must be complete before baseline evaluation.

## 12. Sync gate before shared evaluation

The following tasks require shared code from the demo branch:

```text
libs/audio/metrics.py
libs/audio/degradations.py
libs/audio/enhancement.py
libs/common/versions.py
```

Before Task T3.1, run:

```bash
git fetch origin
git checkout feature/training-datamove1-v1
git merge origin/demo-rp5-v1
git status
```

Done when:

1. required shared modules exist;
2. import tests pass;
3. tracker records the sync commit or merge base;
4. no local duplicate metric or degradation module exists.

Decision rules:

1. If shared modules do not exist, block Task T3.1 and continue only with environment or dataset tasks.
2. If `DEGRADATION_VERSION` is not defined, block Task T3.1.
3. If `METRICS_VERSION` is not defined, block Task T3.1.
4. If `B7` has not frozen degradation parameters, do not start dry-run or full training.

## 13. Phase 3. Baseline evaluation

Goal: measure how much the official degradations reduce ASR performance.

### Task T3.1. Run clean-audio Whisper baseline

Actions:

1. implement or update `scripts/training/run_whisper_baseline.py`;
2. run `openai-whisper` on clean validation audio;
3. compute WER and Word Accuracy using `libs/audio/metrics.py`;
4. save results to ignored run path;
5. save summary CSV or Markdown to `reports/training/`.

Done when:

1. clean baseline exists;
2. WER and Word Accuracy are computed by shared metrics;
3. model and dependency versions are recorded;
4. run summary includes dataset version.

Decision rules:

1. If Whisper fails on a file, record the file and continue unless failure rate is high.
2. If failure rate exceeds 2 percent, stop and investigate.
3. If metrics import fails, return to the sync gate.
4. If results are too large for Git, commit only a summary.

### Task T3.2. Run degraded-audio Whisper baseline

Actions:

1. apply the five official degradations using `libs/audio/degradations.py`;
2. run `openai-whisper` on degraded audio;
3. compute WER and Word Accuracy;
4. aggregate by degradation;
5. save run summary.

Done when:

1. all five degradations have results;
2. degradation parameters and `DEGRADATION_VERSION` are recorded;
3. metrics version is recorded;
4. ASR drop is measurable or documented as weak.

Decision rules:

1. If a degradation does not reduce ASR performance, keep it but flag it in the summary.
2. If multiple degradations produce no measurable effect, stop and report before training.
3. If degradation output validation fails, fix `degradations.py` or parameters before continuing.
4. If results differ from demo expectations, record the difference and continue with Surrey reference metrics.

### Task T3.3. Produce baseline report

Actions:

1. create `reports/training/baseline_summary.md`;
2. include clean WER and Word Accuracy;
3. include degraded WER and Word Accuracy by degradation;
4. include dataset version;
5. include ASR model version;
6. include degradation version;
7. include metrics version;
8. include limitations.

Done when:

1. baseline report is committed;
2. heavy artifacts remain outside Git;
3. tracker links to run artifact root;
4. next task can compare pretrained enhancement.

Decision rules:

1. If the report exposes absolute private storage paths, replace them with relative run IDs or sanitized paths.
2. If the report includes tables from large CSVs, include only aggregated tables.
3. If baseline is incomplete, mark the report as partial and keep task incomplete.

Cut T2 gate: clean and degraded baselines must be completed before pretrained enhancer evaluation.

## 14. Phase 4. MetricGAN+ pretrained evaluation

Goal: determine whether a pretrained enhancer provides enough benefit to use as the first public demo enhancer.

### Task T4.1. Integrate MetricGAN+ pretrained wrapper for Surrey evaluation

Ownership rule:

```text
B5.3 in the demo/platform branch creates the enhancer interface, bypass enhancer, and empty MetricGAN+ hook.
T4.1 in the training branch fills the MetricGAN+ pretrained wrapper.
No other task should independently implement MetricGAN+ in libs/audio/enhancement.py.
```

Actions:

1. sync from `origin/demo-rp5-v1` before editing `libs/audio/enhancement.py`;
2. confirm `libs/audio/enhancement.py` exposes the enhancer interface and MetricGAN+ hook created by B5.3;
3. implement the MetricGAN+ pretrained wrapper by filling that hook;
4. make wrapper callable from a script and from the demo runtime interface;
5. add a small import or smoke test;
6. record dependency requirements;
7. open or prepare a pull request from `feature/training-datamove1-v1` into `demo-rp5-v1` before T4.2 proceeds.

Done when:

1. wrapper imports;
2. one degraded audio file can be enhanced;
3. output audio validates;
4. interface is compatible with demo runtime;
5. merge path into `demo-rp5-v1` is explicit.

Decision rules:

1. If the B5.3 hook does not exist, stop and ask the demo branch to complete B5.3 before implementing MetricGAN+.
2. If a MetricGAN+ wrapper already exists from the demo branch, reuse it and do not create a second implementation.
3. If adding the wrapper requires heavy dependencies, isolate them to training or optional extras where possible.
4. If the wrapper cannot run on RP5, document that and keep it out of default demo runtime until export or replacement is available.
5. If editing `libs/audio/enhancement.py` causes merge conflicts with the demo branch, stop and resolve through the pull request, not by duplicating code.
6. If output audio is invalid, keep task incomplete.

### Task T4.2. Evaluate degraded versus pretrained-enhanced ASR

Actions:

1. enhance degraded validation audio with MetricGAN+ pretrained;
2. run `openai-whisper` on enhanced audio;
3. compute WER and Word Accuracy;
4. aggregate by degradation;
5. compare with degraded baseline.

Done when:

1. pretrained-enhanced results exist;
2. average improvement is computed;
3. worst-case degradation is computed;
4. limitations are recorded.

Decision rules:

1. If average Word Accuracy improves by at least 5 points, mark pretrained enhancer as strong enough for publicable baseline.
2. If improvement is positive but below 5 points, mark as partial.
3. If improvement is zero or negative, keep it as a comparison and do not sell it as improvement.
4. If only some degradations improve, report per-degradation behavior.

### Task T4.3. Update model card and activate RP5 validation request

Actions:

1. add pretrained evaluation summary to `docs/model_card.md`;
2. update `reports/training/metricgan_pretrained_summary.md`;
3. record whether B6.5 should validate this enhancer on RP5;
4. notify the demo branch through tracker notes or PR description.

Done when:

1. summary is committed;
2. model card contains pretrained evaluation status;
3. demo branch has a clear B6.5 input.

Decision rules:

1. If pretrained evaluation is incomplete, do not activate B6.5.
2. If pretrained evaluation is complete but weak, B6.5 may still run to document demo behavior.
3. If wrapper is not RP5-compatible, B6.5 must use exported or bypass-compatible path.

Cut T2 gate: pretrained evaluation must be complete before deciding whether to fine-tune.

## 15. Phase 5. Dry-run training

Goal: prove the training pipeline produces all expected artifacts before full training.

Dependencies:

```text
B7 complete in the demo branch.
docs/model_card.md exists.
DEGRADATION_VERSION is frozen as degradation_v1.
METRICS_VERSION is defined.
Dataset version is defined.
```

### Task T5.1. Create dry-run training config

Actions:

1. create `configs/training/dry_run.yaml`;
2. specify dataset version;
3. specify degradation version;
4. specify metrics version;
5. set steps to 100;
6. define artifact output root outside Git;
7. define run summary output.

Done when:

1. config exists;
2. config is deterministic;
3. output paths are outside Git or ignored;
4. config can be parsed by training script.

Decision rules:

1. If B7 is not complete, do not create a final dry-run config with frozen parameters.
2. If output root points inside tracked repo files, fix it before running.
3. If random seeds are supported, set them.
4. If hardware target is unknown, use the smallest safe dry-run settings.

### Task T5.2. Implement dry-run training script

Actions:

1. implement or update `scripts/training/train_enhancer.py`;
2. support dry-run config;
3. generate run ID;
4. create `runs/<run_id>/` outside Git or under ignored path;
5. save `config.yaml`;
6. save `metrics.csv`;
7. save `wer_by_degradation.csv`;
8. save sample audio references or tiny allowed samples only if policy permits;
9. save `loss_curve.png`;
10. save `val_wer_curve.png`;
11. save `run_summary.md`.

Done when:

1. script can run without full training;
2. output artifact contract is satisfied;
3. run summary is generated;
4. no heavy artifacts are staged in Git.

Decision rules:

1. If a requested artifact cannot be generated in dry-run, create an explicit placeholder and mark it incomplete in the summary.
2. If sample audio cannot be committed, keep it in run artifacts and reference it by path or checksum.
3. If validation WER cannot be computed within dry-run, record why and keep task incomplete unless explicitly accepted.
4. If dry-run fails before writing summary, fix script before proceeding.

### Task T5.3. Run 100-step dry-run on Slurm

Actions:

1. create Slurm job for dry-run;
2. submit job;
3. monitor completion;
4. collect output;
5. inspect run artifacts;
6. update tracker.

Done when:

1. dry-run completes;
2. required artifacts exist;
3. summary is readable;
4. tracker records run ID and output root.

Decision rules:

1. If Slurm job fails due to environment, return to Phase 1.
2. If it fails due to data, return to Phase 2.
3. If it fails due to model code, fix script and rerun.
4. If it times out, reduce dry-run workload but keep artifact requirements.

Cut T3 gate: dry-run must generate all required artifact types before full training.

## 16. Phase 6. Full training

Goal: produce at least one candidate checkpoint, if compute access allows.

### Task T6.1. Create full training config

Actions:

1. create `configs/training/full_training.yaml`;
2. use frozen degradation version;
3. use dataset version;
4. set validation schedule;
5. set checkpoint schedule;
6. set output artifact root;
7. include random seed;
8. include expected hardware assumptions.

Done when:

1. config exists;
2. config is explicit enough to reproduce;
3. checkpoint policy is clear;
4. validation policy is clear.

Decision rules:

1. If compute time is uncertain, use a conservative first full-training config.
2. If GPU is unavailable, create CPU-feasible reduced training config and mark result as limited.
3. If dry-run config and full config diverge in incompatible ways, update dry-run or document the difference.

### Task T6.2. Run full training

Actions:

1. submit full training job;
2. monitor Slurm status;
3. save checkpoints outside Git;
4. save metrics periodically;
5. save validation results;
6. save run summary;
7. preserve logs.

Done when:

1. at least one candidate checkpoint exists;
2. metrics and validation files exist;
3. run summary exists;
4. failure or completion is recorded.

Decision rules:

1. If full training completes, proceed to checkpoint selection.
2. If full training is interrupted but has usable checkpoints, proceed to checkpoint selection with limitation noted.
3. If no usable checkpoint exists, return to config or environment task.
4. If compute access expires, document partial result and use pretrained or bypass outcome.

### Task T6.3. Generate full training summary

Actions:

1. create or update `reports/training/full_training_summary.md`;
2. include run ID;
3. include dataset version;
4. include checkpoint list;
5. include validation metrics;
6. include known limitations;
7. include whether full training is complete or partial.

Done when:

1. summary is committed;
2. heavy artifacts remain outside Git;
3. tracker points to external run root;
4. checkpoint selection can run.

Decision rules:

1. If full training was not possible, write a partial summary rather than hiding it.
2. If no checkpoint exists, do not proceed to export.
3. If a checkpoint exists but metrics are incomplete, run evaluation before selection.

## 17. Phase 7. Checkpoint selection

Goal: select a checkpoint using a deterministic rule.

Selection rule:

```text
Primary metric:
average Word Accuracy over the five official degradations.

Tiebreaker 1:
best worst-case degradation.

Tiebreaker 2:
most recent checkpoint.
```

### Task T7.1. Implement checkpoint selection script

Actions:

1. implement `scripts/training/select_checkpoint.py`;
2. read candidate checkpoint metrics;
3. compute average Word Accuracy;
4. compute worst-case degradation;
5. apply tiebreakers;
6. write `checkpoint_selection.md`;
7. write machine-readable selected checkpoint metadata.

Done when:

1. script selects a checkpoint deterministically;
2. selection rationale is written;
3. selected checkpoint path or artifact ID is recorded;
4. no manual preference overrides selection without documentation.

Decision rules:

1. If no checkpoint metrics exist, stop.
2. If metrics are tied, apply tiebreaker 1.
3. If still tied, apply tiebreaker 2.
4. If selected checkpoint is missing on disk, fail selection.

### Task T7.2. Evaluate selected checkpoint against baselines

Actions:

1. run selected checkpoint on degraded validation audio;
2. run ASR on enhanced audio;
3. compute WER and Word Accuracy;
4. compare to degraded baseline and pretrained baseline;
5. write final evaluation summary.

Done when:

1. selected checkpoint has final metrics;
2. comparison to baselines exists;
3. publishability tier is assigned;
4. limitations are recorded.

Decision rules:

1. If improvement is at least 5 average Word Accuracy points, classify as publicable strong.
2. If improvement is partial, classify as publicable acceptable with limitations.
3. If improvement is weak or negative, classify as framework-only unless there is a defensible reason.
4. Do not claim improvement not supported by metrics.

## 18. Phase 8. Export and model card

Goal: create a deployable enhancer artifact and complete documentation.

### Task T8.1. Export selected enhancer

Actions:

1. implement or update `scripts/training/export_enhancer.py`;
2. load selected checkpoint;
3. export a CPU-compatible artifact;
4. test inference on CPU;
5. compute artifact checksum;
6. assign `ENHANCER_VERSION`;
7. write export metadata.

Done when:

1. exported artifact exists;
2. CPU inference test passes;
3. checksum is recorded;
4. `ENHANCER_VERSION` is recorded;
5. artifact location is ready for handoff.

Decision rules:

1. If export fails, do not hand off checkpoint directly unless the demo branch supports checkpoint loading.
2. If CPU inference is too slow, document latency and consider fallback.
3. If artifact is too large for GitHub, publish through release, external storage, or documented transfer path.
4. If export succeeds but metrics are weak, artifact can still be handed off as experimental.

### Task T8.2. Complete model card

Actions:

1. update `docs/model_card.md` from selected run summary;
2. fill training data;
3. fill training procedure;
4. fill evaluation results;
5. fill limitations;
6. fill ethical considerations;
7. fill deployment target;
8. state whether result is fine-tuned, pretrained, or bypass.

Done when:

1. model card no longer contains unresolved placeholders for selected result;
2. claims match metrics;
3. deployment limitations are clear;
4. file is committed.

Decision rules:

1. If no trained model exists, model card must say so.
2. If pretrained model is used, do not describe it as trained by this project.
3. If bypass is used, model card becomes an evaluation framework card, not a model card claiming enhancement.
4. If metrics are from Surrey openai-whisper, label them as such.

### Task T8.3. Handoff artifact to demo branch

Actions:

1. publish artifact using a release, documented external path, or agreed transfer path;
2. provide checksum;
3. provide `ENHANCER_VERSION`;
4. provide expected runtime dependencies;
5. provide smoke-test command;
6. update tracker with handoff status;
7. open PR into `demo-rp5-v1` if source changes are required.

Handoff procedure expected by the demo branch:

```text
1. Set ENHANCER_VERSION in RP5 .env.
2. Restart demo worker.
3. Run prewarm_cache.py --bypass-budget-check --enhancer-version=<new>.
4. Run validate_cache.py.
5. Validate 2 examples manually.
6. Run public smoke test.
7. Roll back to previous ENHANCER_VERSION if validation fails.
```

Done when:

1. demo branch has enough information to load or reject the artifact;
2. checksum is available;
3. model card is updated;
4. training branch can be merged or archived.

Decision rules:

1. If artifact handoff fails, keep training branch complete but mark deployment handoff blocked.
2. If demo branch rejects artifact due to latency or compatibility, record limitation and keep previous enhancer.
3. If artifact works, update final README and docs through the demo branch, not this branch.

Cut T3 gate: export and handoff must pass before training branch is considered complete.

## 19. Final training branch definition of done

The training branch is done when:

1. datamove1 environment is documented;
2. dataset manifest or manifest summary exists;
3. public examples are excluded;
4. clean and degraded baselines exist;
5. pretrained enhancer evaluation exists;
6. dry-run training produced required artifacts;
7. full training either produced a selected checkpoint or is honestly documented as unavailable;
8. model card is complete for the selected outcome;
9. exported artifact or fallback decision is documented;
10. handoff to demo branch is complete or the blocker is explicit;
11. progress trackers are current;
12. branch is pushed to GitHub.

## 20. Practical control rules

1. Do not start this plan until `origin/demo-rp5-v1` exists.
2. Do not start training before dataset exclusion is done.
3. Do not start dry-run before degradations are frozen.
4. Do not define metrics locally in training scripts.
5. Do not commit datasets or checkpoints.
6. Do not commit secrets or API keys.
7. Do not claim ASR improvement without WER or Word Accuracy evidence.
8. Do not hide failed or weak enhancement results.
9. Keep Slurm jobs rerunnable.
10. Keep run summaries small enough to inspect.
11. Stop at gates and report status.
12. If generated code conflicts with this plan, follow this plan.
13. If this plan conflicts with `CLAUDE.md`, follow `CLAUDE.md` and record the conflict.
