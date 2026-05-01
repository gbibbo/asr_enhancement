# ASR Enhancement Demo and Raspberry Pi: Claude Code Rules

This file is the active root `CLAUDE.md` on the `feature/demo-runtime-rp5-v1` branch. The reference copy lives at `docs/profiles/CLAUDE.demo.md`. To prevent merge conflicts when syncing between branches, ensure `.gitattributes` declares `CLAUDE.md merge=ours` on this branch and the local merge driver is configured with `git config merge.ours.driver true`.

## 1. Project identity

Repository:

```text
https://github.com/gbibbo/asr_enhancement
```

GitHub owner:

```text
gbibbo
```

Demo working branch:

```text
feature/demo-runtime-rp5-v1
```

Integration branch:

```text
demo-rp5-v1
```

Parallel training branch:

```text
feature/training-datamove1-v1
```

Preservation tag:

```text
platform-mvp-v0
```

This file is for the public demo, shared refactor, Raspberry Pi runtime, frontend, deployment, and GitHub narrative branch. It must not be used as the root `CLAUDE.md` for datamove1 training.

If this file is inside an existing checkout with a different path, treat the directory containing this file as the repository root. Do not create a duplicate checkout unless explicitly instructed.

## 2. Read order before any change

Before editing code, configs, docs, scripts, or trackers, read:

1. `CLAUDE.md`
2. `docs/plans/demo_platform_plan.md`
3. `docs/progress/demo_platform_progress.md`, if present
4. `docs/progress/demo_platform_progress.yaml`, if present
5. `docs/plans/training_datamove1_plan.md`, only when the current task depends on training branch outputs
6. the existing repository structure

Then:

1. identify the first pending demo/platform task;
2. execute only that task;
3. run the verification required by that task;
4. update the demo/platform trackers;
5. stop at gates and report status.

Do not skip gates. Do not continue into the next task unless explicitly asked.

## 3. Scope of this Claude profile

This profile covers:

1. split bootstrap and Git safety;
2. platform MVP preservation;
3. shared repository refactor;
4. ASR provider abstraction;
5. audio pipeline extraction;
6. versions, metrics, and degradations;
7. public demo runtime;
8. Raspberry Pi setup;
9. SQLite and filesystem demo mode;
10. demo endpoints;
11. local Whisper provider for the demo;
12. AssemblyAI demo provider and cost controls;
13. frontend UI;
14. upload handling;
15. cache prewarming and validation;
16. lightweight observability;
17. Cloudflare Tunnel deployment;
18. README, docs, screenshots, and GitHub narrative.

This profile does not cover datamove1 training execution.

Do not add Slurm scripts, datamove1 environment logic, HPC dataset processing, or training jobs from this branch unless the demo plan explicitly asks for a small shared-code interface.

## 4. No HPC or Slurm work in this profile

Do not use Slurm.

Do not add datamove1-specific execution rules.

Do not run or create HPC training jobs.

Do not create training datasets.

Do not run full training.

Do not process large datasets on the Raspberry Pi.

The Raspberry Pi is a public demo host, not a training machine.

Allowed Raspberry Pi work:

1. Docker installation and verification;
2. repo checkout;
3. demo runtime setup;
4. SQLite setup;
5. filesystem artifact storage for demo use;
6. faster-whisper tiny.en for short demo audio;
7. cached curated examples;
8. small uploads up to the plan limits;
9. health checks;
10. logs and lightweight stats;
11. Cloudflare Tunnel.

## 5. Branch discipline

Expected branch for demo work:

```text
feature/demo-runtime-rp5-v1
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

1. If the branch is not `feature/demo-runtime-rp5-v1`, stop unless the current task is explicitly branch setup.
2. If there are unrelated uncommitted changes, stop and report them.
3. Do not force push.
4. Do not change remotes without explicit instruction.
5. Open pull requests into `demo-rp5-v1`, not into `master`.
6. Merge `demo-rp5-v1` into `master` only after final smoke test and documentation are complete.

Sync pattern:

```bash
git fetch origin
git checkout feature/demo-runtime-rp5-v1
git pull --ff-only origin feature/demo-runtime-rp5-v1
```

After training branch outputs are merged into `demo-rp5-v1`, sync explicitly:

```bash
git fetch origin
git checkout feature/demo-runtime-rp5-v1
git merge origin/demo-rp5-v1
git status
```

If conflicts touch shared files, stop and report before resolving.

## 6. Current split plan files

The split plan files must live inside the repo:

```text
docs/plans/demo_platform_plan.md
docs/plans/training_datamove1_plan.md
```

Demo/platform trackers:

```text
docs/progress/demo_platform_progress.md
docs/progress/demo_platform_progress.yaml
```

Training trackers are owned by the training branch:

```text
docs/progress/training_datamove1_progress.md
docs/progress/training_datamove1_progress.yaml
```

Rules:

1. Update the demo/platform trackers after each completed or blocked task.
2. Do not mark a task as done until its verification has passed.
3. If blocked, keep `current_task` on the blocked task, keep `last_completed_task` unchanged, set `blocked: true`, and write the blocker clearly.
4. Do not overwrite training trackers from the demo branch except during a deliberate merge conflict resolution.

## 7. Repository locations

Local development checkout may be on Windows, WSL, macOS, or Linux. Use the actual repo root from:

```bash
git rev-parse --show-toplevel
```

Recommended Raspberry Pi checkout:

```text
/home/$USER/code/asr_enhancement
```

Recommended Raspberry Pi runtime root:

```text
/home/$USER/asr_enhancement_runtime
```

Recommended Raspberry Pi subdirectories:

```text
/home/$USER/asr_enhancement_runtime/db
/home/$USER/asr_enhancement_runtime/cache
/home/$USER/asr_enhancement_runtime/uploads
/home/$USER/asr_enhancement_runtime/artifacts
/home/$USER/asr_enhancement_runtime/logs
/home/$USER/asr_enhancement_runtime/tmp
```

Rules:

1. Keep the repo for source, configs, tests, docs, and small metadata.
2. Keep runtime audio, uploads, cache, SQLite files, and logs outside the repo or under ignored runtime paths.
3. Do not commit runtime artifacts.
4. Do not commit `.env` files with real values.

## 8. Runtime modes

The project must preserve two modes.

Platform mode:

```text
FastAPI
Celery
Postgres
Redis
MinIO
Prometheus
Grafana
OpenTelemetry
AssemblyAI
Fake provider
```

Public demo mode:

```text
Raspberry Pi 5
Docker
SQLite
local filesystem
local worker
faster-whisper tiny.en
AssemblyAI with cost controls
Cloudflare Tunnel
Next.js frontend
```

Rules:

1. Do not break existing `/v1` platform endpoints while adding `/demo` endpoints.
2. Keep existing platform Docker Compose intact unless the current task explicitly modifies it.
3. Add demo-specific runtime in separate files, for example `docker-compose.demo.yml`, when the plan asks for it.
4. Do not remove legacy modules until their replacements are validated and tests pass.
5. Public demo mode must not require Postgres, Redis, MinIO, Grafana, Prometheus, or OpenTelemetry collector.

## 9. Shared refactor rules

The planned refactor uses these mappings:

```text
libs/audio_pipeline/pipeline.py   -> libs/audio/enhancement.py
libs/audio_pipeline/presets.py    -> baseline legacy presets
```

Rules:

1. Copy or adapt first.
2. Update imports second.
3. Update tests third.
4. Update CI if affected.
5. Keep platform endpoints working.
6. Do not delete old code until replacement behavior is validated.
7. Avoid broad renames outside the current task.

## 10. Shared module rules

Shared modules:

```text
libs/audio/metrics.py
libs/audio/degradations.py
libs/audio/enhancement.py
libs/common/versions.py
```

Rules:

1. The demo branch creates the initial shared modules.
2. The demo branch creates the enhancer interface, bypass enhancer, and an empty MetricGAN+ hook.
3. The training branch fills or reuses the MetricGAN+ pretrained wrapper after syncing from `demo-rp5-v1`.
4. Do not create a second MetricGAN+ implementation outside `libs/audio/enhancement.py`.
5. If `degradations.py` changes, bump `DEGRADATION_VERSION`.
6. If `metrics.py` changes, bump `METRICS_VERSION`.
7. Do not define local version constants for metrics, degradations, or enhancer behavior outside `libs/common/versions.py` and runtime `ENHANCER_VERSION`.

## 11. Cache version contract

Cache keys must include:

```text
example_id
degradation_id
DEGRADATION_VERSION
asr_provider
asr_model_version
ENHANCER_VERSION
METRICS_VERSION
```

Rules:

1. `DEGRADATION_VERSION` comes from `libs/common/versions.py`.
2. `METRICS_VERSION` comes from `libs/common/versions.py`.
3. `DEFAULT_ENHANCER_VERSION` comes from `libs/common/versions.py`.
4. Runtime `ENHANCER_VERSION` may override the default through environment configuration.
5. Do not hardcode metric or degradation versions in cache modules.
6. Add tests that fail if cache key logic stops reading from `libs.common.versions`.

## 12. Raspberry Pi runtime policy

Target runtime:

```text
Python 3.11
Docker
SQLite
filesystem local storage
worker concurrency = 1
queue max = 10 jobs
faster-whisper tiny.en
AssemblyAI with explicit quota state
Cloudflare Tunnel
```

Rules:

1. Do not process long jobs inside request handlers.
2. Cached curated examples may return immediately.
3. User uploads must go through asynchronous job flow.
4. If queue length exceeds the plan limit, return HTTP 503 with a clear user-facing message.
5. Keep worker concurrency at 1 unless the plan changes it.
6. Keep upload limits at 30 seconds and 5 MB.
7. Do not silently fall back from AssemblyAI to Whisper.
8. Do not add spectrograms or waveforms to the frontend unless the plan changes scope.

## 13. Raspberry Pi command policy

Common Raspberry Pi commands:

```bash
cd /home/$USER/code/asr_enhancement
git status --short
git branch --show-current
git pull --ff-only origin feature/demo-runtime-rp5-v1
```

Docker Compose demo commands should use the demo compose file when it exists:

```bash
docker compose -f docker-compose.demo.yml config
docker compose -f docker-compose.demo.yml up -d
docker compose -f docker-compose.demo.yml ps
docker compose -f docker-compose.demo.yml logs --tail=100 demo-api
docker compose -f docker-compose.demo.yml logs --tail=100 demo-worker
docker compose -f docker-compose.demo.yml down
```

If the compose file lives under `infra/compose/`, use the exact path defined by the current task.

Rules:

1. Do not run platform Compose when the task asks for demo mode.
2. Do not run demo Compose when verifying preserved platform mode unless the task asks for it.
3. Keep `.env` and secrets local.
4. Do not put secrets in compose files.
5. Do not run destructive cleanup commands without checking target paths.

## 14. SQLite schema policy

Demo SQLite tables are owned by the demo branch.

Minimum tables expected by the plan:

```text
jobs
cache_entries
usage_ledger
```

Minimum `jobs` columns:

```text
job_id TEXT PRIMARY KEY
status TEXT NOT NULL
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
completed_at TEXT NULL
source_type TEXT NOT NULL
provider TEXT NOT NULL
degradation_id TEXT NULL
enhancer_version TEXT NULL
error_message TEXT NULL
result_path TEXT NULL
```

Minimum `cache_entries` columns:

```text
cache_key TEXT PRIMARY KEY
example_id TEXT NOT NULL
degradation_id TEXT NOT NULL
asr_provider TEXT NOT NULL
asr_model_version TEXT NOT NULL
degradation_version TEXT NOT NULL
metrics_version TEXT NOT NULL
enhancer_version TEXT NOT NULL
created_at TEXT NOT NULL
result_json_path TEXT NOT NULL
audio_artifact_dir TEXT NULL
```

Minimum `usage_ledger` columns:

```text
ledger_id TEXT PRIMARY KEY
provider TEXT NOT NULL
created_at TEXT NOT NULL
duration_seconds REAL NOT NULL
estimated_cost_usd REAL NOT NULL
session_id TEXT NULL
job_id TEXT NULL
status TEXT NOT NULL
```

Rules:

1. Migrations or initialization scripts must be rerunnable.
2. SQLite files must not be committed.
3. Tests may use temporary SQLite files.
4. Production demo SQLite files live under the runtime root.

## 15. AssemblyAI policy

AssemblyAI is optional and controlled.

Required states in UI:

```text
AssemblyAI available
AssemblyAI daily quota reached
AssemblyAI quota exhausted
AssemblyAI disabled
```

Rules:

1. Use a dedicated demo API key.
2. Do not commit the key.
3. Autopay is assumed disabled unless Gabriel states otherwise.
4. Daily soft cap is 5 USD.
5. Warning cap is 35 USD.
6. Hard cap is 45 USD.
7. Estimate cost from audio duration.
8. Record usage in SQLite before or during provider execution as defined by the task.
9. On timeout or 5xx, retry once with 2 second backoff.
10. If it fails, show the exact planned message.
11. Never silently switch from AssemblyAI to Whisper.

Required temporary failure text:

```text
AssemblyAI temporarily unavailable. Try again or use Whisper local.
```

## 16. Upload and privacy policy

Upload limits:

```text
max duration: 30 seconds
max size: 5 MB
language target: English speech
```

Ground truth policy:

```text
Optional ground truth is used only to calculate accuracy for this session. It is not stored.
```

Rules:

1. Validate upload size and duration in frontend and backend.
2. Do not store manual ground truth.
3. Do not log manual ground truth.
4. Do not use manual ground truth for training.
5. Do not keep uploaded audio longer than the cleanup policy allows.
6. Cleanup must not delete curated example cache, usage ledger, aggregate stats, or operational logs.
7. If faster-whisper detects non-English language with probability above the plan threshold, show the warning and let the user explicitly continue.

Required non-English warning:

```text
Detected language is not English. This demo is designed for English speech, so results may be unreliable. Continue?
```

## 17. Frontend policy

The frontend must be understandable without reading GitHub.

Required public demo concepts:

1. curated examples;
2. upload mode;
3. provider selector;
4. degradation selector;
5. original audio playback;
6. degraded audio playback;
7. ground truth for curated examples;
8. optional manual ground truth for uploads;
9. raw ASR transcript;
10. enhanced ASR transcript or honest baseline;
11. Word Accuracy when ground truth is available;
12. pipeline details;
13. provider status;
14. enhancer version;
15. cache status;
16. job ID;
17. latency;
18. AssemblyAI quota state.

Rules:

1. Use mobile-first layout.
2. No horizontal scroll.
3. Do not add spectrograms.
4. Do not add waveforms.
5. Keep UI copy in English.
6. Avoid frontend polish that is not required by the current task.
7. Split large frontend work according to the plan subdivisions.

## 18. Observability policy for RP5

Use lightweight observability only.

Required concepts:

1. JSON logs;
2. log rotation;
3. `/admin/stats` with basic auth;
4. uptime;
5. requests;
6. jobs;
7. queue length;
8. cache hit rate;
9. AssemblyAI spend estimate;
10. disk usage;
11. CPU temperature;
12. last errors;
13. Cloudflare tunnel status;
14. cleanup timestamp;
15. email alert for disk above threshold;
16. email alert for repeated health check failure.

Do not add Grafana, Prometheus, or OpenTelemetry collector to public demo mode unless the plan explicitly changes.

## 19. Secrets and local environment policy

Never commit:

```text
ASSEMBLYAI_API_KEY
Cloudflare tokens
SSH private keys
.env files with real values
SQLite runtime databases
uploaded audio
cached generated audio
logs with sensitive content
```

Allowed examples:

```text
.env.example
services/frontend/.env.example
```

Rules:

1. Keep secrets in local `.env` files or host-level service configuration.
2. Use clear placeholder names in examples.
3. Do not print secrets in logs.
4. Do not include secrets in screenshots.
5. Do not commit Cloudflare tunnel credentials.

## 20. Git identity and commit policy

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

Push only to the current branch:

```bash
git push origin feature/demo-runtime-rp5-v1
```

## 21. Blocked verification policy

If a task is implemented locally but cannot be fully verified because Raspberry Pi hardware, Docker, Cloudflare, AssemblyAI credentials, mobile testing, or another external dependency is unavailable:

1. Keep the task blocked, not done.
2. Update trackers with `blocked: true`.
3. Keep `current_task` on the blocked task.
4. Keep `last_completed_task` on the previous completed task.
5. Commit implementation plus blocked tracker state only if the plan requires preserving the work.
6. Report the exact external verification commands Gabriel must run.
7. After Gabriel reports verification passed, update trackers to done.
8. Do not start the next task unless explicitly asked.

## 22. Implementation discipline

For each task:

1. inspect existing files first;
2. read the current task text in the plan;
3. change one layer only;
4. prefer extending existing modules over creating duplicates;
5. keep scripts rerunnable;
6. make scripts resume-safe where practical;
7. use `pathlib` for Python paths;
8. write tests for new behavior;
9. update CI if imports or command paths change;
10. avoid broad refactors outside the task scope;
11. update trackers after completion or blockage;
12. report changed files, commands run, results, remaining failures, and next pending task.

Do not add services, endpoints, provider calls, frontend features, or deployment logic unless the current plan task requires them.

## 23. Documentation and language

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

Keep documentation minimal. Update docs only when behavior, setup, execution, testing, or demo use changes.

## 24. Final report format

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

If Raspberry Pi or Docker was used, include:

```text
Host:
Compose file:
Services touched:
Health check result:
Relevant log path or command:
```

If public exposure was touched, include:

```text
Cloudflare status:
Public URL status:
External smoke test status:
Rollback command:
```


<!-- BEGIN GABRIEL GIT POLICY -->
## Git policy for Claude

For this demo/RP5 profile:

- At the end of every successfully completed and verified task, commit and push automatically to the current branch.
- Use Git identity exactly: Gabriel Bibbó <gabobibbo@gmail.com>.
- Do not add Co-Authored-By, Generated-By, AI-authorship, Signed-off-by, or similar authorship trailers.
- Do not invent commits, branches, remotes, or verification results.
<!-- END GABRIEL GIT POLICY -->
