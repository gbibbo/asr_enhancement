# ASR Enhancement Training: Claude Code Rules for datamove1

This file is the active root `CLAUDE.md` on the `feature/training-datamove1-v1` branch. The reference copy lives at `docs/profiles/CLAUDE.training.md`. To prevent merge conflicts when syncing between branches, ensure `.gitattributes` declares `CLAUDE.md merge=ours` on this branch and the local merge driver is configured with `git config merge.ours.driver true`.

## 1. Project identity

Repository:

```text
https://github.com/gbibbo/asr_enhancement
```

GitHub owner:

```text
gbibbo
```

Training branch:

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

Default datamove1 checkout:

```text
/mnt/fast/nobackup/users/gb0048/asr_enhancement
```

If this file is inside an existing checkout with a different path, treat the directory containing this file as the repository root. Do not create a duplicate checkout unless the plan explicitly requires it or the current checkout is unusable.

This file is for the datamove1 and Surrey Slurm training branch only. It must not be used as the root `CLAUDE.md` for the Raspberry Pi demo branch.

## 2. Read order before any change

Before editing code, configs, docs, scripts, or trackers, read:

1. `CLAUDE.md`
2. `docs/plans/training_datamove1_plan.md`
3. `docs/progress/training_datamove1_progress.md`, if present
4. `docs/progress/training_datamove1_progress.yaml`, if present
5. `docs/plans/demo_platform_plan.md`, only when the current training task depends on shared demo branch work
6. the existing repository structure

Then:

1. identify the first pending task in the training plan;
2. execute only that task;
3. run the verification required by that task;
4. update the training trackers;
5. stop at gates and report status.

Do not skip gates. Do not continue into the next task unless explicitly asked.

## 3. Bootstrap dependency

The training branch depends on the split bootstrap from the demo/platform plan.

Before starting training work, verify:

```bash
git fetch origin
git ls-remote --heads origin demo-rp5-v1
git ls-remote --tags origin platform-mvp-v0
```

Rules:

1. If `origin/demo-rp5-v1` does not exist, stop and report that Phase S0 of `docs/plans/demo_platform_plan.md` must be completed first.
2. If `platform-mvp-v0` does not exist locally or remotely, stop before modifying the repository.
3. The training branch must be created from `demo-rp5-v1`, not from `master`.
4. Open pull requests into `demo-rp5-v1`, not into `master`.
5. Do not merge directly into `master`.

## 4. Branch discipline

Expected branch:

```text
feature/training-datamove1-v1
```

Check before work:

```bash
git status --short
git branch --show-current
git remote -v
git log --oneline -5
```

Expected remote:

```text
https://github.com/gbibbo/asr_enhancement.git
```

or:

```text
git@github.com:gbibbo/asr_enhancement.git
```

Rules:

1. If the branch is not `feature/training-datamove1-v1`, stop unless the current task is explicitly branch setup.
2. If there are unrelated uncommitted changes, stop and report them.
3. Sync from `demo-rp5-v1` before tasks that depend on shared modules.
4. If conflicts touch `libs/audio/`, `libs/common/versions.py`, or `docs/model_card.md`, stop and report before resolving.
5. Do not force push.
6. Do not change remotes without explicit instruction.

Sync pattern:

```bash
git fetch origin
git checkout feature/training-datamove1-v1
git merge origin/demo-rp5-v1
git status
```

## 5. Scope of this Claude profile

This profile covers only:

1. datamove1 repository setup;
2. Surrey Slurm verification;
3. Apptainer execution;
4. dependency and environment checks for training;
5. dataset manifests and exclusions;
6. baseline evaluation with `openai-whisper`;
7. MetricGAN+ pretrained evaluation;
8. dry-run training;
9. full training if compute access allows;
10. checkpoint selection;
11. export of an enhancer artifact;
12. training content for `docs/model_card.md`;
13. handoff information for the Raspberry Pi demo branch.

Do not implement public demo endpoints, Raspberry Pi Docker Compose, frontend UI, Cloudflare Tunnel, public upload handling, or AssemblyAI cost-control UI from this branch unless the training plan explicitly requires a small shared-code change.

## 6. Current split plan files

The split plan files must live inside the repo:

```text
docs/plans/training_datamove1_plan.md
docs/plans/demo_platform_plan.md
```

Training trackers:

```text
docs/progress/training_datamove1_progress.md
docs/progress/training_datamove1_progress.yaml
```

Demo trackers are not owned by this branch:

```text
docs/progress/demo_platform_progress.md
docs/progress/demo_platform_progress.yaml
```

Rules:

1. Update the training trackers after each completed or blocked task.
2. Do not mark a task as done until its verification has passed.
3. If blocked, keep `current_task` on the blocked task, keep `last_completed_task` unchanged, set `blocked: true`, and write the blocker clearly.
4. Do not overwrite demo trackers from the training branch except during a deliberate merge conflict resolution.

## 7. Surrey and datamove1 execution rules

Heavy work must not run directly on a login node.

Allowed on login node:

1. `git` operations;
2. reading files;
3. editing small files;
4. checking disk usage;
5. checking Slurm availability;
6. submitting jobs;
7. inspecting short logs;
8. creating small config or tracker files.

Not allowed on login node:

1. training;
2. full dataset preparation;
3. large audio processing;
4. ASR evaluation over many files;
5. Whisper inference over datasets;
6. enhancement over datasets;
7. long Python jobs;
8. memory-heavy imports for real workloads.

Use Slurm for compute work.

## 8. Apptainer is required for Slurm Python jobs

On datamove1 and Surrey Slurm, Python jobs submitted through Slurm must run inside Apptainer.

Default Apptainer image:

```text
/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
```

If this image is missing or unsuitable, stop and record the blocker in the training tracker before choosing another image.

Do not call bare compute-node `python`, `python3`, `~/.local`, or `PYTHONUSERBASE` for scientific dependencies in Slurm jobs.

Surrey constraints:

1. `/mnt/fast/nobackup` is auto-bound.
2. `--bind` may be disabled.
3. `--pwd` may be disabled.
4. Use `cd` before `apptainer exec`.
5. Pass variables through `--env`.
6. Use `python3` inside the container.
7. Use `--nv` only for GPU jobs.
8. The current working directory may not be auto-mounted into the container ("WARNING: Not mounting current directory: user bind control is disabled by system administrator"). Use absolute paths inside the container; never rely on `$PWD` or relative paths from inside Apptainer.

Required Apptainer pattern:

```bash
REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
REPO_PARENT="/mnt/fast/nobackup/users/gb0048"
CONTAINER="$REPO_PARENT/opro2/pytorch_2.1_cuda12.sif"

export ASR_REPO_ROOT="$REPO"
export ASR_RUNTIME_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime"
export ASR_ARTIFACTS_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts"
export ASR_CACHE_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache"
export ASR_PROVIDER="fake"

cd "$REPO" || exit 1

apptainer exec \
  --env ASR_REPO_ROOT="$ASR_REPO_ROOT" \
  --env ASR_RUNTIME_ROOT="$ASR_RUNTIME_ROOT" \
  --env ASR_ARTIFACTS_ROOT="$ASR_ARTIFACTS_ROOT" \
  --env ASR_CACHE_ROOT="$ASR_CACHE_ROOT" \
  --env ASR_PROVIDER="$ASR_PROVIDER" \
  "$CONTAINER" \
  python3 "$REPO/scripts/my_script.py" [args...]
```

## 9. Slurm command policy

The Surrey Slurm scheduler is not directly callable from `datamove1.surrey.ac.uk`: `sbatch`, `squeue`, `sacct`, and `scancel` are not in PATH on that host. Never call them directly from datamove1. All Slurm commands must go through the repository wrapper:

```bash
./slurm/tools/on_submit.sh <squeue|sbatch|scancel|sacct|scontrol> <args...>
```

The wrapper forwards each command to the Surrey submit host:

```bash
ssh -o BatchMode=yes aisurrey-submit01.surrey.ac.uk "$@"
```

Slurm jobs execute on `aisurrey` compute nodes (e.g. `aisurrey01.surrey.ac.uk`) where Apptainer (`/usr/bin/apptainer`) and Singularity (`/usr/bin/singularity`) are installed. The shared `/mnt/fast/nobackup` mount is visible from datamove1, the submit host, and the compute nodes, so absolute paths under `/mnt/fast/nobackup` are valid everywhere.

Examples (run from datamove1; absolute paths recommended):

```bash
./slurm/tools/on_submit.sh squeue -u "$USER"
./slurm/tools/on_submit.sh sinfo || true
./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/<job_name>.sh
./slurm/tools/on_submit.sh sacct -j <job_id> --format=JobID,JobName,State,Elapsed,MaxRSS,ExitCode
./slurm/tools/on_submit.sh scancel <job_id>
```

Rules:

1. Never call `sbatch`, `squeue`, `sacct`, or `scancel` directly from `datamove1`. They are not in PATH; the wrapper is the only path.
2. SSH key-based auth to `aisurrey-submit01.surrey.ac.uk` must be configured in advance (the wrapper uses `BatchMode=yes` and will not prompt).
3. Do not submit long jobs before the minimal Slurm gate (Task T0.5) succeeds.
4. Do not submit GPU jobs before a CPU micro-validation job succeeds.
5. Do not start full training from an interactive shell.
6. Do not submit jobs with output paths inside the repo unless those paths are ignored and lightweight.
7. Every reusable Slurm job must write logs outside the repo or under an ignored path (e.g. `$ASR_TRAINING_ROOT/logs/`).

## 10. Slurm job template

Reusable templates go here:

```text
slurm/templates/
```

Concrete job scripts go here:

```text
slurm/jobs/
```

Minimal Apptainer Slurm template:

```bash
#!/usr/bin/env bash
#SBATCH --job-name=asr_<task_name>
#SBATCH --output=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.out
#SBATCH --error=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/%x_%j.err
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"
TRAIN_ROOT="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"

mkdir -p "$TRAIN_ROOT/logs" "$TRAIN_ROOT/runtime" "$TRAIN_ROOT/artifacts" "$TRAIN_ROOT/cache"

cd "$REPO"

apptainer exec \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$TRAIN_ROOT/runtime" \
  --env ASR_ARTIFACTS_ROOT="$TRAIN_ROOT/artifacts" \
  --env ASR_CACHE_ROOT="$TRAIN_ROOT/cache" \
  "$CONTAINER" \
  python3 scripts/<script_name>.py <args>
```

For GPU jobs, add:

```bash
#SBATCH --gres=gpu:1
```

and use:

```bash
apptainer exec --nv ...
```

Only add GPU resources when the current task explicitly requires them.

## 11. Storage rules for datamove1

Do not write heavy runtime artifacts inside the repository.

Repository root:

```text
/mnt/fast/nobackup/users/gb0048/asr_enhancement
```

Training root:

```text
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
```

Recommended subdirectories:

```text
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/exports
```

Default environment variables:

```bash
ASR_REPO_ROOT=/mnt/fast/nobackup/users/gb0048/asr_enhancement
ASR_TRAINING_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training
ASR_RUNTIME_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime
ASR_ARTIFACTS_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts
ASR_CACHE_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache
ASR_PROVIDER=fake
```

Keep in Git:

1. source code;
2. tests;
3. small configs;
4. Slurm templates;
5. small metadata schemas;
6. small reports;
7. docs;
8. trackers.

Never commit:

1. datasets;
2. full audio files;
3. generated degraded audio;
4. generated enhanced audio;
5. checkpoints;
6. full run directories;
7. caches;
8. local secrets;
9. API keys;
10. `.env` files with real credentials;
11. large logs.

Do not rely on `scratch4weeks` for long-term preservation. Export final selected artifacts through the release or handoff process defined by the plan.

## 12. Required ignored runtime paths

The training branch must ensure these paths are ignored if created under the repo:

```text
runs/
artifacts/
cache/
datasets/
outputs/
exports/
*.ckpt
*.pt
*.pth
*.onnx
*.wav
*.flac
*.mp3
.env
.env.*
```

Exception:

```text
.env.example
services/frontend/.env.example
```

Do not add broad ignore rules that hide source files, configs, tests, or docs.

## 13. Shared module rules

Shared modules are owned carefully across branches:

```text
libs/audio/metrics.py
libs/audio/degradations.py
libs/audio/enhancement.py
libs/common/versions.py
```

Rules:

1. Do not create duplicate metrics modules in training scripts.
2. Do not create duplicate degradation definitions in training scripts.
3. Do not define local metric, degradation, or enhancer version constants outside `libs/common/versions.py` and runtime `ENHANCER_VERSION`.
4. If `metrics.py` changes, bump `METRICS_VERSION`.
5. If `degradations.py` changes, bump `DEGRADATION_VERSION`.
6. If enhancer behavior changes, update `ENHANCER_VERSION` through the plan-defined mechanism.
7. If a shared change is required, verify that demo-facing tests are not broken before the change is merged into `demo-rp5-v1`.

MetricGAN+ ownership:

1. The demo branch creates the enhancer interface, bypass enhancer, and an empty MetricGAN+ hook.
2. The training branch fills or reuses the MetricGAN+ pretrained wrapper in `libs/audio/enhancement.py`.
3. Do not create a second MetricGAN+ implementation outside `libs/audio/enhancement.py`.
4. If the wrapper does not exist when T4.1 starts, stop and sync from `demo-rp5-v1` before implementing it.

## 14. Public example exclusion rule

Public demo examples must not leak into training.

Expected exclusion file:

```text
configs/training/public_examples_excluded.yaml
```

Rules:

1. If B6 has not produced `demo_examples.json`, create a placeholder exclusion file with a clear `filled_after_b6` marker.
2. Baseline or training tasks must fail safely if the exclusion file is still a placeholder when real data processing starts.
3. Once B6 closes, fill the exclusion file with the public example IDs or source references.
4. Do not train, validate, or select checkpoints on the 10 public demo examples.

## 15. Dataset and run reproducibility

Every dataset or run task must record enough information to reproduce it.

For datasets, record:

1. dataset version;
2. source datasets;
3. split rules;
4. exclusion rules;
5. manifest path;
6. creation command;
7. checksum or row count where practical.

For runs, record:

1. run ID;
2. git commit;
3. branch;
4. config path;
5. dataset version;
6. degradation version;
7. metrics version;
8. enhancer version;
9. Slurm job ID;
10. output path;
11. summary metrics;
12. known failures.

Dry-run and full training outputs must go under:

```text
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/<run_id>/
```

Only small summary files may be copied into Git if the plan asks for them.

## 16. Reference ASR policy

Training branch reference ASR:

```text
openai-whisper
```

Demo branch ASR:

```text
faster-whisper tiny.en
```

Rules:

1. Use `openai-whisper` for Surrey baseline and training evaluation.
2. Do not substitute `faster-whisper` for training results unless the plan explicitly asks for cross-validation.
3. Cross-validation against RP5 metrics is owned by B6.5 in the demo plan but may require training branch artifacts.
4. Record exact model and package versions used for ASR evaluation.

## 17. Metrics policy

Primary metrics:

```text
WER
Word Accuracy
```

Metric implementation:

```text
libs/audio/metrics.py
```

Rules:

1. Use the shared metric implementation for training, baseline evaluation, model card, and cache validation.
2. Do not define ad hoc WER or Word Accuracy calculations in notebooks or scripts.
3. Normalize text through the shared normalization function.
4. If a result table includes WER, include Word Accuracy unless the task explicitly says otherwise.
5. Record per-degradation results, not only averages.

## 18. Secrets and provider calls

Do not commit secrets.

Never commit:

```text
ASSEMBLYAI_API_KEY
Cloudflare tokens
SSH private keys
.env files with real values
```

Training branch provider policy:

1. Use fake providers for local or CI tests unless the task explicitly requires real ASR.
2. Real AssemblyAI calls are not part of datamove1 training unless the plan explicitly says so.
3. Reference ASR is `openai-whisper`, running locally through the controlled environment.
4. If a real provider call is needed, require explicit credentials, avoid CI, and record cost or quota implications.

## 19. Git identity and commit policy

Commits must be authored as Gabriel Bibbó, not as an assistant, AI vendor, or bot.

Before committing:

```bash
git config user.name "Gabriel Bibbó"

if [ -z "$(git config user.email)" ]; then
  echo "Missing git user.email. Stop and ask Gabriel for the correct Git email before committing."
  exit 1
fi
```

Do not invent an email.

Never add:

1. AI authorship banners;
2. assistant co-author trailers;
3. assistant sign-off trailers;
4. bot authorship metadata;
5. comments saying code was written by an AI assistant.

Before every commit, run:

```bash
git status
git remote -v
git branch --show-current
git config user.name
git config user.email
git diff --stat
```

Commit messages must be plain and project-focused.

Do not push unless the current plan task requires it or Gabriel explicitly asks.

Push only to the current branch:

```bash
git push origin feature/training-datamove1-v1
```

## 20. Blocked verification policy

If a task is implemented on datamove1 but cannot be fully verified there because Docker, Docker Compose, Raspberry Pi hardware, local browser testing, or another external dependency is unavailable:

1. Keep the task blocked, not done.
2. Update trackers with `blocked: true`.
3. Keep `current_task` on the blocked task.
4. Keep `last_completed_task` on the previous completed task.
5. Commit implementation plus blocked tracker state only if the plan requires preserving the work.
6. Report the exact external verification commands Gabriel must run.
7. After Gabriel reports verification passed, update trackers to done.
8. Do not start the next task unless explicitly asked.

## 21. Implementation discipline

For each task:

1. inspect existing files first;
2. read the current task text in the plan;
3. change one layer only;
4. prefer extending existing modules over creating duplicates;
5. keep scripts rerunnable;
6. make scripts resume-safe where practical;
7. use `pathlib` for Python paths;
8. write small tests for new behavior;
9. avoid broad refactors outside the task scope;
10. update trackers after completion or blockage;
11. report changed files, commands run, results, remaining failures, and next pending task.

Do not add services, endpoints, dashboards, frontend polish, provider calls, or Raspberry Pi deployment logic from the training branch.

## 22. Documentation and language

User-facing product material must be in English:

1. UI text;
2. API examples;
3. validation messages;
4. status messages;
5. shared code comments;
6. dashboard titles;
7. alerts;
8. README text;
9. model card;
10. public docs.

Internal task notes may be in Spanish if Gabriel asks for them.

Keep documentation minimal. Update docs only when behavior, setup, execution, testing, or handoff changes.

## 23. Final report format

After each task, report:

```text
Task:
Branch:
Commit, if any:
Files changed:
Commands run:
Verification result:
Tracker state:
Blocked status:
Next pending task:
Notes for Gabriel:
```

If a Slurm job was run, include:

```text
Slurm job ID:
Job script:
Log path:
Exit state:
Elapsed time:
MaxRSS, if available:
```

