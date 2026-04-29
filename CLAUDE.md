# ASR Enhancement Platform: Claude Code Rules

## 1. Project identity

Repository: `https://github.com/gbibbo/asr_enhancement`

Default HPC checkout:

```text
/mnt/fast/nobackup/users/gb0048/asr_enhancement
```

If this file is inside an existing checkout with a different path, treat the directory containing this file as the repository root. Do not create a duplicate checkout unless explicitly instructed.

The implementation plan controls task order. This file only contains persistent execution rules.

## 2. Read order

Before changing code, read:

1. `CLAUDE.md`
2. `plan.md`
3. `docs/claude_task_progress.md`, if present
4. `docs/claude_task_progress.yaml`, if present
5. the existing project structure

If progress trackers are missing, create them before implementation. Detect the last completed task and execute only the next pending task. Do not skip gates or broaden scope.

## 3. MVP boundaries

The MVP is pre-recorded only.

Allowed core components:

- FastAPI API
- Celery worker
- PostgreSQL
- Redis
- MinIO or S3-compatible object storage
- fake ASR adapter for local tests and CI
- AssemblyAI pre-recorded adapter only when explicitly required
- small frontend only after the backend path works
- basic logs, metrics, traces, and CI when required by the plan

Do not implement before MVP completion:

- streaming, WebSockets, or live sessions
- batch experiment APIs
- hyperparameter sweeps
- preset ranking or promotion workflows
- dedicated scheduler, experiment-runner, or streaming services
- heavy neural enhancement models
- Kubernetes
- enterprise auth, multi-tenant features, or advanced dashboards

Use fake ASR by default. Real provider calls must be explicit, credential-gated, and absent from CI.

## 4. Surrey HPC rules

Heavy work must not run directly on a login node. Slurm commands must go through:

```bash
./slurm/tools/on_submit.sh <squeue|sbatch|scancel|sacct|scontrol> <args...>
```

Python jobs submitted to Slurm must run inside Apptainer. Do not call bare compute-node `python`, `python3`, `~/.local`, or `PYTHONUSERBASE` for scientific dependencies.

Container:

```text
/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
```

Required pattern:

```bash
REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
REPO_PARENT="/mnt/fast/nobackup/users/gb0048"
CONTAINER="$REPO_PARENT/opro2/pytorch_2.1_cuda12.sif"

cd "$REPO" || exit 1

apptainer exec \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_RUNTIME_ROOT="$ASR_RUNTIME_ROOT" \
  --env ASR_ARTIFACTS_ROOT="$ASR_ARTIFACTS_ROOT" \
  --env ASR_CACHE_ROOT="$ASR_CACHE_ROOT" \
  "$CONTAINER" \
  python3 "$REPO/scripts/my_script.py" [args...]
```

Surrey constraints:

- `--bind` is disabled. `/mnt/fast/nobackup` is auto-bound.
- `--pwd` is disabled. Use `cd` before `apptainer exec`.
- pass variables via `--env`
- use `--nv` only when a job needs GPU
- use `python3` inside the container

For new Slurm Python jobs, copy `slurm/templates/apptainer_job.sh` to `slurm/jobs/<task_name>.sh`, replace `CHANGEME`, then run a micro-validation job before any full run.

Docker Compose is for local/demo orchestration. Do not run heavy Compose workloads on an HPC login node.

## 5. Storage rules

Do not write heavy runtime artifacts inside the repository.

Repository root:

```text
/mnt/fast/nobackup/users/gb0048/asr_enhancement
```

Runtime root:

```text
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_runtime
```

Artifact root:

```text
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_artifacts
```

Default environment variables:

```bash
ASR_REPO_ROOT=/mnt/fast/nobackup/users/gb0048/asr_enhancement
ASR_RUNTIME_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_runtime
ASR_ARTIFACTS_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_artifacts
ASR_CACHE_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/cache
ASR_PROVIDER=fake
```

Use runtime/artifact roots for audio, object-store data, transcripts, logs, reports, caches, and test outputs. Keep only code, configs, migrations, tests, docs, lightweight metadata, and trackers in git. Do not rely on `scratch4weeks` for long-term storage.

## 6. Implementation discipline

For each task:

- inspect the existing structure first
- locate the current task in `plan.md`
- prefer extending existing modules over creating duplicates
- keep scripts rerunnable and resume-safe
- use `pathlib` for Python paths
- update progress trackers after completion
- report changed files, verification run, remaining failures, and next pending task

Do not add services, endpoints, dashboards, frontend polish, provider calls, or enhancement complexity unless the current plan task requires them.

## 7. Public API boundary

Do not expand the API early.

MVP public endpoints:

```text
GET  /health
GET  /ready
POST /v1/transcribe
POST /v1/enhance-and-transcribe
GET  /v1/jobs/{job_id}
GET  /v1/jobs/{job_id}/result
GET  /metrics
```

Do not implement batch, experiment, streaming, or WebSocket endpoints before the MVP backend is stable.

## 8. Git and GitHub identity

The repository belongs to Gabriel Bibbó, GitHub username `gbibbo`. Commits must be authored as Gabriel, not as an assistant, AI vendor, or bot.

Before the first commit in a checkout:

```bash
git config user.name "Gabriel Bibbó"

if [ -z "$(git config user.email)" ]; then
  echo "Missing git user.email. Stop and ask Gabriel for the correct Git email before committing."
  exit 1
fi
```

Do not invent an email. Stop if uncertain.

Never add AI authorship banners, assistant co-author trailers, assistant sign-off trailers, bot authorship metadata, or comments saying code was written by an AI assistant to commits, PRs, source files, docs, generated artifacts, or release notes.

Commit messages must be plain and project-focused. Do not push unless explicitly requested or required by the current plan task. Before pushing, verify:

```bash
git remote -v
```

Expected remote:

```text
git@github.com:gbibbo/asr_enhancement.git
https://github.com/gbibbo/asr_enhancement.git
```

Do not change remotes or force push without explicit instruction.

## 9. Language and docs

User-facing product material must be in English: UI text, status messages, validation messages, API examples, shared code comments, dashboard titles, alerts, screenshots, and demo output.

Internal personal notes may be in Spanish. Keep docs minimal and update them only when they help setup, execution, testing, or demo use.

## 10. Done criteria

A task is done only when:

- changes match the task boundary
- relevant tests or smoke checks ran
- failures or unverified parts are documented
- progress trackers are updated
- no heavy artifacts were added to git
- no out-of-scope service or endpoint was introduced
- Git identity and no-signature rules were respected if a commit was created
