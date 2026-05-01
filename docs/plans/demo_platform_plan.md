# ASR Enhancement Demo, Platform Mode, and GitHub Narrative: Deterministic Implementation Plan

## 0. How to use this plan

This file is the execution plan for everything except datamove1 training. Read it after `CLAUDE.md` and before implementation work on the public demo, shared refactor, Raspberry Pi runtime, GitHub documentation, and final project narrative.

`CLAUDE.md` defines standing execution rules, repository policy, HPC rules, storage rules, Git identity policy, and scope guardrails. This file defines implementation order, task boundaries, decision rules, gates, verification criteria, parallel Git workflow, and progress tracker rules for the non-training branch.

Execution rule:

1. Read `CLAUDE.md`.
2. Read `docs/plans/demo_platform_plan.md`.
3. Read `docs/progress/demo_platform_progress.md` and `docs/progress/demo_platform_progress.yaml` if they exist.
4. Identify the first pending task.
5. Execute only that task.
6. Run the verification for that task.
7. Update the demo/platform progress trackers.
8. Stop at gates and report status.

If a task depends on an earlier task that is not complete, do the earlier task first and update the tracker.

## 1. Branch role

This branch builds the public demo and evolves the existing platform MVP into a two-mode portfolio project.

Working branch:

```text
feature/demo-runtime-rp5-v1
```

Integration branch:

```text
demo-rp5-v1
```

Preservation tag:

```text
platform-mvp-v0
```

Parallel training branch:

```text
feature/training-datamove1-v1
```

Rule:

```text
This branch owns the shared repository refactor and demo runtime. The training branch may not start shared evaluation or training until the required shared modules from this plan exist and are merged into demo-rp5-v1.
```

Recommended simple Git workflow:

```bash
git fetch origin
git checkout master
git pull --ff-only origin master
git tag -a platform-mvp-v0 -m "Preserve completed platform MVP" || true
git push origin platform-mvp-v0 || true
git checkout -b demo-rp5-v1
git push -u origin demo-rp5-v1
git checkout -b feature/demo-runtime-rp5-v1
git push -u origin feature/demo-runtime-rp5-v1
```

If `demo-rp5-v1` already exists:

```bash
git fetch origin
git checkout demo-rp5-v1 || git checkout -b demo-rp5-v1 origin/demo-rp5-v1
git pull --ff-only origin demo-rp5-v1
git checkout feature/demo-runtime-rp5-v1 || git checkout -b feature/demo-runtime-rp5-v1
git push -u origin feature/demo-runtime-rp5-v1
```

Decision rules:

1. If `platform-mvp-v0` already exists locally or remotely, do not recreate it with a different target.
2. If `demo-rp5-v1` already exists, use it as the integration branch.
3. If the repo has uncommitted changes, stop before creating tags or branches.
4. Do not merge directly into `master` while the parallel work is active.
5. Open pull requests from feature branches into `demo-rp5-v1`.
6. Merge `demo-rp5-v1` into `master` only after final public smoke test and documentation are complete.

## 2. Project goal

Convert the current `asr_enhancement` MVP into a public portfolio project that demonstrates three capabilities:

1. ML applied to audio:
   1. controlled speech degradation;
   2. enhancement before ASR;
   3. comparison between raw ASR and enhanced ASR;
   4. WER and Word Accuracy evaluation.
2. MLOps and platform engineering:
   1. interchangeable ASR providers;
   2. asynchronous jobs;
   3. versioned cache;
   4. usage ledger;
   5. tests;
   6. CI;
   7. rollback;
   8. model card;
   9. technical documentation.
3. Real deployment:
   1. public Raspberry Pi 5 demo;
   2. local Whisper on edge;
   3. AssemblyAI as cloud provider;
   4. Cloudflare Tunnel;
   5. cost control;
   6. lightweight observability.

The public demo must be understandable to a recruiter without reading the code. GitHub must remain deep enough for a technical reviewer to inspect the system design.

## 3. Relationship to the training branch

The training branch owns datamove1 training and evaluation. This branch owns all other work.

This branch owns:

1. `R0` to `R4`: safe refactor and shared code foundation;
2. `B0` to `B15`: Raspberry Pi public demo;
3. `C1` to `C3`: README, docs, assets, and portfolio narrative;
4. public demo cache and upload flows;
5. AssemblyAI cost controls;
6. frontend;
7. Cloudflare deployment;
8. platform mode preservation.

Training branch owns:

1. Slurm scripts;
2. datamove1 environment;
3. dataset manifests;
4. baseline evaluation on Surrey;
5. MetricGAN+ evaluation on Surrey;
6. training runs;
7. checkpoint selection;
8. model export;
9. training content for `docs/model_card.md`.

Shared files that must be handled carefully:

```text
libs/audio/metrics.py
libs/audio/degradations.py
libs/audio/enhancement.py
libs/common/versions.py
docs/model_card.md
README.md
```

Decision rules:

1. This branch creates initial shared modules.
2. This branch creates the enhancer interface, bypass enhancer, and an empty MetricGAN+ hook in B5.3.
3. The training branch fills the MetricGAN+ pretrained wrapper in T4.1 after syncing from `demo-rp5-v1`.
4. No branch should create a second MetricGAN+ implementation outside `libs/audio/enhancement.py`.
5. If the training branch changes shared modules, this branch must rerun demo tests after merging.
6. `docs/model_card.md` final training results come from the training branch.
7. README final narrative is owned by this branch after the training outcome is known.

## 4. Repository location and plan placement

The split plans live inside the repository.

Required plan files:

```text
docs/plans/demo_platform_plan.md
docs/plans/training_datamove1_plan.md
```

Required demo/platform trackers:

```text
docs/progress/demo_platform_progress.md
docs/progress/demo_platform_progress.yaml
```

Required training trackers, created by the training branch:

```text
docs/progress/training_datamove1_progress.md
docs/progress/training_datamove1_progress.yaml
```

Decision rules:

1. Do not replace the original root `plan.md` until the split workflow is committed.
2. If root `plan.md` remains useful as historical MVP implementation plan, keep it and add a note pointing to `docs/plans/`.
3. If root `plan.md` becomes misleading, replace it with a short router document only after both split plans exist.
4. The two detailed plans should live under `docs/plans/`, not at repo root.
5. Trackers should live under `docs/progress/` to avoid mixing branch-specific progress with legacy `docs/claude_task_progress.*`.

Recommended root `plan.md` router text after split:

```text
# ASR Enhancement Project Plans

The original platform MVP has been preserved under tag platform-mvp-v0.

Current implementation work is split into two deterministic plans:

1. docs/plans/demo_platform_plan.md
2. docs/plans/training_datamove1_plan.md

Use the demo/platform plan for repository refactor, public demo, Raspberry Pi deployment, and GitHub narrative.
Use the training plan for datamove1, Slurm, dataset preparation, evaluation, training, export, and model-card training content.
```

## 5. Fixed technical decisions

These decisions are closed for this branch:

1. Repo base: `gbibbo/asr_enhancement`.
2. Preservation tag: `platform-mvp-v0`.
3. Integration branch: `demo-rp5-v1`.
4. Demo branch: `feature/demo-runtime-rp5-v1`.
5. Training branch: `feature/training-datamove1-v1`.
6. Platform mode remains preserved.
7. Public demo mode is added without deleting platform mode.
8. Runtime RP5 uses Python 3.11, Docker, SQLite, filesystem local, local worker, `faster-whisper tiny.en`, AssemblyAI optional, and Cloudflare Tunnel.
9. Platform mode keeps FastAPI, Celery, Postgres, Redis, MinIO, Prometheus, Grafana, OpenTelemetry, AssemblyAI, and fake provider.
10. Public demo examples use cached results by default.
11. User uploads always use asynchronous jobs.
12. No long processing in request handlers.
13. Worker concurrency is 1 in public demo mode.
14. Queue max is 10 jobs in public demo mode.
15. If queue is full, return HTTP 503 with a clear English message.
16. Official demo language is English speech.
17. User-facing text must be in English.
18. Ground truth typed by users is used only in memory for current-session metrics and is not stored.
19. No spectrograms or waveforms in public demo v1.
20. No secrets in Git.

Decision rules:

1. If a task requires removing platform mode, stop and report the conflict.
2. If a task requires changing a fixed technical decision, stop and report before changing it.
3. If a later task can be implemented without touching platform mode, do that.
4. If shared code is needed by both modes, put it under `libs/`.
5. If demo-specific code is not reusable, put it under `libs/demo/` or demo service packages.

## 6. Product language policy

Everything user-facing must be in English.

This applies to:

1. public demo UI text;
2. button labels;
3. provider status messages;
4. quota messages;
5. validation messages;
6. API examples in docs;
7. code comments intended for shared project code;
8. screenshots used in documentation;
9. dashboard titles;
10. alert names;
11. printed messages in committed scripts.

If a note is private, not committed, not shown in screenshots, and not product-facing, it may be in Spanish.

## 7. Repository layout target

Use this layout:

```text
asr_enhancement/
  CLAUDE.md
  plan.md
  README.md
  docs/
    plans/
      demo_platform_plan.md
      training_datamove1_plan.md
    progress/
      demo_platform_progress.md
      demo_platform_progress.yaml
      training_datamove1_progress.md
      training_datamove1_progress.yaml
    architecture.md
    public_demo.md
    platform_mode.md
    training.md
    model_card.md
    deployment_raspberry_pi.md
    assemblyai_cost_controls.md
    privacy.md
    rollback.md
    release_checklist.md
  services/
    api/
    worker/
    frontend/
  libs/
    asr/
    audio/
    common/
    demo/
    observability/
  infra/
    compose/
    docker/
    grafana/
    prometheus/
    otel/
  scripts/
    prewarm_cache.py
    validate_cache.py
    invalidate_cache.py
    cleanup_uploads.py
  assets/
  tests/
```

Legacy paths during refactor:

```text
libs/asr_adapter/
libs/audio_pipeline/
```

Mapping fixed for the refactor:

```text
libs/asr_adapter/base.py          -> libs/asr/base.py
libs/asr_adapter/assemblyai.py    -> libs/asr/assemblyai_provider.py
libs/asr_adapter/fake.py          -> libs/asr/fake_provider.py
libs/audio_pipeline/pipeline.py   -> libs/audio/enhancement.py
libs/audio_pipeline/presets.py    -> baseline legacy presets
```

Decision rules:

1. First copy or adapt.
2. Then update imports.
3. Then update tests and CI.
4. Do not delete old code until replacement is validated.
5. If duplicate code remains after validation, remove it only in the cleanup task that owns that layer.
6. Do not create training-only directories in this branch unless they are shared plan or docs locations.

## 8. Demo API surface

Public demo endpoints:

```text
GET  /demo/health
GET  /demo/examples
GET  /demo/examples/{example_id}/audio/clean
GET  /demo/examples/{example_id}/audio/degraded
POST /demo/run-cached
POST /demo/upload
GET  /demo/jobs/{job_id}
GET  /demo/jobs/{job_id}/result
GET  /admin/stats
```

Platform endpoints must remain available:

```text
GET  /health
GET  /ready
POST /v1/transcribe
POST /v1/enhance-and-transcribe
GET  /v1/jobs/{job_id}
GET  /v1/jobs/{job_id}/result
GET  /metrics
```

Deferred endpoints:

```text
POST /v1/batch/submit
GET  /v1/experiments/{experiment_id}
POST /v1/stream/session
WS   /v1/stream/{session_id}
```

Decision rules:

1. If code generation suggests a deferred endpoint, reject it.
2. If a demo endpoint can reuse platform logic safely, reuse shared services.
3. If public demo mode needs lighter persistence, implement it without weakening platform mode.
4. If a new endpoint is needed, add it only after updating this plan and tracker.

## 9. Demo persistence and cache contract

Public demo mode uses SQLite plus filesystem local storage.

Platform mode keeps Postgres, Redis, and MinIO.

Demo examples:

```text
Preloaded examples return from cache when possible.
No API call is made for cached benchmark results.
```

Uploads:

```text
Uploads always create asynchronous jobs.
Temporary artifacts expire after 24 hours.
```

Cache key:

```text
example_id
degradation_id
DEGRADATION_VERSION
asr_provider
asr_model_version
ENHANCER_VERSION
METRICS_VERSION
```

Version source:

```text
libs/common/versions.py
```

Required constants:

```text
DEGRADATION_VERSION
METRICS_VERSION
DEFAULT_ENHANCER_VERSION
```

Decision rules:

1. Cache key must read `DEGRADATION_VERSION` and `METRICS_VERSION` from `libs.common.versions`.
2. No module may define local duplicate version constants for degradation, metrics, or enhancer.
3. `ENHANCER_VERSION` is read from `.env` at runtime.
4. If cache validation fails, do not serve stale cached results silently.
5. If cached result is served, UI must show: `Cached benchmark result. No API call was made for this example.`

## 10. ASR, enhancer, and metrics contracts

ASR providers:

1. fake provider for tests and CI;
2. AssemblyAI provider for cloud path;
3. Whisper local provider for Raspberry Pi demo.

Whisper decisions:

```text
RP5: faster-whisper tiny.en
Surrey: openai-whisper for reference evaluation
Official language: English
```

UI text:

```text
This demo is designed for English speech.
```

AssemblyAI states in UI:

```text
AssemblyAI available
AssemblyAI daily quota reached
AssemblyAI quota exhausted
AssemblyAI disabled
```

AssemblyAI failure policy:

```text
Timeout or 5xx:
1 retry
2 second backoff
then show:
AssemblyAI temporarily unavailable. Try again or use Whisper local.
```

Rule:

```text
Never silently switch from AssemblyAI to Whisper.
```

Metrics:

1. WER;
2. Word Accuracy;
3. text normalization;
4. implementation in `libs/audio/metrics.py`;
5. tests required.

Degradations:

1. `far_field_room`;
2. `cafe_background`;
3. `phone_call`;
4. `muffled`;
5. `broadband_hiss`.

Decision rules:

1. If ASR provider fails, surface provider-specific status and safe error message.
2. If metrics change, bump `METRICS_VERSION`.
3. If degradation parameters change, bump `DEGRADATION_VERSION`.
4. If enhancer changes, update `ENHANCER_VERSION` through runtime config and cache invalidation.
5. If no trained enhancer exists, use bypass honestly.

## 11. Testing strategy

Every task must run relevant tests or checks.

Required test classes:

1. import tests for new packages;
2. unit tests for metrics;
3. unit tests for degradations;
4. unit tests for version source and cache key;
5. ASR provider tests;
6. demo endpoint tests;
7. upload validation tests;
8. cache validation tests;
9. cleanup tests;
10. AssemblyAI cost-control tests;
11. frontend basic flow tests where feasible;
12. smoke tests for RP5 and public URL.

Rules:

1. CI must use fake provider.
2. CI must not require AssemblyAI credentials.
3. Tests must not write heavy artifacts inside tracked repo paths.
4. A task is not done until relevant tests or smoke checks have run.
5. If a test cannot run because a dependency is unavailable, stop, record the missing dependency, and do not mark the task complete.

## 12. Progress tracker format

Maintain both demo/platform trackers.

YAML shape:

```yaml
branch: feature/demo-runtime-rp5-v1
integration_branch: demo-rp5-v1
parallel_training_branch: feature/training-datamove1-v1
current_track: R
current_phase: 0
current_task: "S0.1"
last_completed_task: null
blocked: false
blocker: null
rp5_status: unknown
public_url_status: unknown
training_handoff_status: not_ready
tasks:
  "S0.1": pending
  "S0.2": pending
  "S0.3": pending
```

Markdown shape:

```markdown
# Demo and Platform Task Progress

Branch: feature/demo-runtime-rp5-v1
Integration branch: demo-rp5-v1
Parallel training branch: feature/training-datamove1-v1
Current track: Split bootstrap
Current phase: Phase 0
Current task: Task S0.1

## Completed

None yet.

## Current blocker

None.

## Training handoff status

Not ready.

## Next task

Task S0.1. Inspect repository state and preserve MVP.
```

After every task:

1. update completed task;
2. update next task;
3. record tests or checks run;
4. record failures or unverified parts;
5. record branch and commit status;
6. record whether training branch is blocked or unblocked by shared modules;
7. do not mark a gate complete without passing checks.

Decision rules:

1. If a task passes verification, mark it complete.
2. If a task fails verification, keep it current and record failure.
3. If a task cannot run because of a missing dependency, mark `blocked: true`.
4. If a gate passes, stop and report.
5. If a gate fails, do not advance.

## 13. Phase S0. Split bootstrap and Git safety

Goal: preserve the completed MVP, create the integration branch, place the two split plans in the repo, and prepare independent progress trackers.

### Task S0.1. Inspect repository state and preserve MVP

Actions:

1. inspect current files and directories;
2. confirm repository root;
3. verify Git remote;
4. inspect current branch;
5. inspect uncommitted changes;
6. run existing tests if practical;
7. create or verify tag `platform-mvp-v0`.

Suggested commands:

```bash
git rev-parse --show-toplevel
git status --short
git branch --show-current
git remote -v
git tag --list platform-mvp-v0
```

Done when:

1. repo root is known;
2. remote is correct;
3. dirty state is known;
4. MVP tag exists or is ready to create;
5. tracker records state.

Decision rules:

1. If the working tree is dirty, stop before tagging.
2. If tag already exists, do not recreate it.
3. If no tag exists, create it from the current completed MVP commit.
4. If remote is not `gbibbo/asr_enhancement`, stop and record mismatch.

### Task S0.2. Create integration and demo branches

Actions:

1. create `demo-rp5-v1` from the tagged or current MVP state;
2. push `demo-rp5-v1`;
3. create `feature/demo-runtime-rp5-v1` from `demo-rp5-v1`;
4. push the feature branch;
5. record branch names in tracker.

Done when:

1. integration branch exists locally and remotely;
2. demo feature branch exists locally and remotely;
3. current branch is `feature/demo-runtime-rp5-v1`.

Decision rules:

1. If `demo-rp5-v1` already exists, check it out and pull.
2. If `feature/demo-runtime-rp5-v1` already exists, check it out and merge `origin/demo-rp5-v1`.
3. If branch creation fails, stop and report exact Git state.

### Task S0.3. Add split plan files, plan router, and Claude profiles

Actions:

1. create `docs/plans/`;
2. add `docs/plans/demo_platform_plan.md`;
3. add `docs/plans/training_datamove1_plan.md`;
4. update root `plan.md` into a short router, or add a top note pointing to the new plans;
5. create `docs/profiles/`;
6. add `docs/profiles/CLAUDE.demo.md`;
7. add `docs/profiles/CLAUDE.training.md`;
8. replace root `CLAUDE.md` with the content of `docs/profiles/CLAUDE.demo.md` on `feature/demo-runtime-rp5-v1`;
9. create or update `.gitattributes` with `CLAUDE.md merge=ours`;
10. configure the local merge driver with `git config merge.ours.driver true`;
11. do not delete useful historical content unless router replacement is intentional;
12. commit the plan/profile split.

Done when:

1. both split plans exist;
2. root plan points to them;
3. both Claude profile reference files exist under `docs/profiles/`;
4. root `CLAUDE.md` is the demo/RP5 active profile on `feature/demo-runtime-rp5-v1`;
5. `.gitattributes` contains `CLAUDE.md merge=ours`;
6. Git commit contains only plan, profile, tracker, and documentation-routing changes;
7. branch is pushed.

Decision rules:

1. If root `plan.md` is still needed as historical implementation record, keep it and add a pointer near the top.
2. If root `plan.md` is now misleading, replace it with router text in this task only.
3. If the training plan is added here, the training branch can later inherit it from `demo-rp5-v1`.
4. Do not use `CLAUDE.datamove1.md` or `CLAUDE.demo_rp5.md` as active filenames in the repo root. Claude Code reads root `CLAUDE.md`.
5. If `CLAUDE.md` conflicts during branch sync, keep the version active for the current feature branch.
6. Do not rely on GitHub web merge to resolve `CLAUDE.md` conflicts. Sync branches locally when this file is involved.

### Task S0.4. Create demo/platform trackers

Actions:

1. create `docs/progress/` if missing;
2. create `docs/progress/demo_platform_progress.md`;
3. create `docs/progress/demo_platform_progress.yaml`;
4. initialize current task as `S0.1` or first incomplete task;
5. leave legacy `docs/claude_task_progress.*` untouched unless router note is needed.

Done when:

1. demo trackers exist;
2. tracker format is valid;
3. next task is visible;
4. tracker does not overwrite training tracker.

Decision rules:

1. If trackers already exist, update without deleting history.
2. If trackers disagree, Markdown is history and YAML is current state.
3. If old trackers exist, mark them as legacy only if doing so avoids confusion.

### Task S0.5. Push and open parallel workflow

Actions:

1. push `feature/demo-runtime-rp5-v1`;
2. ensure `demo-rp5-v1` is pushed;
3. record suggested creation of `feature/training-datamove1-v1` from `demo-rp5-v1`;
4. write a short tracker note explaining branch split.

Done when:

1. GitHub has the integration branch;
2. GitHub has the demo feature branch;
3. the training branch can be created from the integration branch;
4. split workflow is documented.

Decision rules:

1. If GitHub push fails, stop and record exact error.
2. If branch protection blocks push, follow PR workflow.
3. If training branch already exists, record it and do not recreate it.

Phase S0 gate: stop after split bootstrap and report branch status.

## 14. Phase R0. Preserve platform MVP and begin migration

Goal: preserve the existing MVP and start the public demo migration from a safe point.

### Task R0.1. Verify current platform mode before refactor

Actions:

1. run the existing test suite;
2. run existing smoke test if available;
3. verify platform endpoints still work locally;
4. record current passing or failing state;
5. do not refactor yet.

Done when:

1. current test status is recorded;
2. failures are known before refactor;
3. platform mode preservation risk is clear.

Decision rules:

1. If tests pass, proceed.
2. If tests fail because of missing environment, record and proceed only if failure is unrelated to code.
3. If tests fail because current code is broken, stop and fix or document before refactor.

### Task R0.2. Add README migration status note

Actions:

1. update `README.md` with a short migration note;
2. state that `platform-mvp-v0` preserves the completed platform MVP;
3. state that public demo mode is being developed on `demo-rp5-v1` and feature branches;
4. keep note concise.

Suggested text:

```text
Status: this repository is being migrated from a completed MLOps platform MVP into a public ASR enhancement demo with Raspberry Pi deployment. The original platform MVP is preserved under the platform-mvp-v0 tag while public demo mode is developed on the demo-rp5-v1 integration branch.
```

Done when:

1. README reflects migration state;
2. no false claim about completed public demo exists;
3. tracker records commit.

Decision rules:

1. If README already contains equivalent note, update it rather than duplicate it.
2. If live demo is not yet public, do not add a live demo link.
3. If branch names differ, update text to actual branch names.

## 15. Phase R1. Extract ASR adapters

Goal: move ASR providers to `libs/asr` without breaking platform endpoints.

### Task R1.1. Create ASR package and copy adapters

Actions:

1. create `libs/asr/`;
2. create `libs/asr/base.py`;
3. create `libs/asr/assemblyai_provider.py`;
4. create `libs/asr/fake_provider.py`;
5. copy or adapt from `libs/asr_adapter/`;
6. preserve old code until validation passes.

Done when:

1. new package imports;
2. adapter interfaces are coherent;
3. no endpoint imports have been changed yet unless tests are ready.

Decision rules:

1. If old adapter files are missing, inspect current active imports and adapt from actual code.
2. If old adapter names differ, preserve behavior and normalize names in new package.
3. If copying creates lint issues, fix only in copied files.

### Task R1.2. Update imports and tests for ASR package

Actions:

1. update application imports to `libs/asr`;
2. update tests;
3. update `.github/workflows/ci.yml` imports, paths, or test commands if they reference `libs/asr_adapter` or old module names;
4. run ASR adapter tests;
5. run platform endpoint tests;
6. keep legacy package only if still needed.

Done when:

1. endpoints `/v1` still work;
2. fake provider remains default;
3. AssemblyAI provider remains gated;
4. tests pass.

Decision rules:

1. If tests fail because old import paths are still used, update them.
2. If external public import paths exist, provide compatibility wrapper temporarily.
3. If platform mode breaks, revert import change and fix before proceeding.

### Task R1.3. Remove or quarantine legacy ASR package

Actions:

1. identify whether `libs/asr_adapter/` is still imported;
2. if unused, remove it or add compatibility wrappers;
3. update docs if path names are mentioned;
4. run tests.

Done when:

1. active ASR code lives under `libs/asr`;
2. no stale imports remain;
3. platform tests pass.

Decision rules:

1. If removing legacy package breaks imports, keep compatibility wrappers.
2. If code is duplicated but harmless, leave removal to cleanup task and record it.
3. Do not remove behavior not covered by tests.

## 16. Phase R2. Extract audio pipeline

Goal: move audio pipeline code to `libs/audio` without breaking platform mode.

### Task R2.1. Create audio package and migrate enhancement code

Actions:

1. create `libs/audio/`;
2. create `libs/audio/enhancement.py`;
3. migrate current pipeline from `libs/audio_pipeline/pipeline.py`;
4. preserve legacy presets;
5. keep old package until validation passes.

Done when:

1. new module imports;
2. existing enhancement behavior is preserved;
3. legacy presets are not lost.

Decision rules:

1. If current audio pipeline differs from expected path, migrate from active imports.
2. If old presets are needed by platform mode, keep compatibility.
3. If migration requires DSP dependency changes, stop and record before adding them.

### Task R2.2. Update imports and tests for audio package

Actions:

1. update imports to `libs/audio`;
2. update tests;
3. update `.github/workflows/ci.yml` imports, paths, or test commands if they reference `libs/audio_pipeline` or old module names;
4. run audio pipeline tests;
5. run platform smoke tests;
6. preserve platform mode.

Done when:

1. platform mode enhancement path still works;
2. tests pass;
3. `libs/audio` is the active shared audio package.

Decision rules:

1. If platform mode breaks, fix before continuing.
2. If old import paths are needed, add compatibility wrappers.
3. If enhancement behavior changes, document and test it.

## 17. Phase R2.5. Version source and cache key foundation

Goal: create a single source of version truth before cache and training depend on it.

### Task R2.5.1. Create `libs/common/versions.py`

Actions:

1. create `libs/common/versions.py`;
2. define `DEGRADATION_VERSION`;
3. define `METRICS_VERSION`;
4. define `DEFAULT_ENHANCER_VERSION`;
5. add import tests.

Done when:

1. constants import successfully;
2. no duplicate version constants are introduced;
3. tests pass.

Decision rules:

1. If `libs/common` already exists, extend it.
2. If version constants exist elsewhere, move them or import from this module.
3. If changing versions is needed later, bump only here.

### Task R2.5.2. Create central cache key function

Actions:

1. create `libs/demo/cache.py` or appropriate shared module;
2. implement `build_cache_key()`;
3. include `example_id`, `degradation_id`, `DEGRADATION_VERSION`, `asr_provider`, `asr_model_version`, `ENHANCER_VERSION`, and `METRICS_VERSION`;
4. read degradation and metrics versions from `libs.common.versions`;
5. add tests.

Done when:

1. cache key is deterministic;
2. tests verify version source;
3. test fails if versions are hardcoded locally.

Decision rules:

1. If demo package does not exist yet, create minimal `libs/demo/`.
2. If cache key belongs elsewhere, keep a single canonical function and document import path.
3. If `ENHANCER_VERSION` is not set, use `DEFAULT_ENHANCER_VERSION`.
4. Do not read degradation or metric versions from environment.

## 18. Phase R2b. Freeze dependencies

Goal: make installs reproducible across development, Surrey, and RP5.

### Task R2b.1. Generate x86_64 dependency lock

Actions:

1. inspect current dependency system;
2. generate `requirements.lock.x86_64`;
3. run tests after installing from the lock where practical;
4. commit lock.

Done when:

1. x86_64 lock exists;
2. generation command is documented;
3. tests still pass.

Decision rules:

1. If dependency management already has an equivalent lock, record it and do not duplicate unless needed.
2. If lock generation fails, stop and record exact failure.
3. If generated lock includes local paths or secrets, fix before commit.

### Task R2b.2. Attempt arm64 dependency lock

Actions:

1. attempt `requirements.lock.arm64` through Docker buildx;
2. if successful, commit it;
3. if unsuccessful, create B2.5 task note to generate it on RP5;
4. record outcome.

Done when:

1. arm64 lock exists or B2.5 is explicitly required;
2. failure reason is documented if missing.

Decision rules:

1. If Docker buildx works, generate arm64 lock before RP5 setup.
2. If buildx fails or delays the plan, defer to B2.5.
3. Do not block all demo work solely on arm64 lock if B2.5 is documented.

## 19. Phase R3. Metrics

Goal: implement shared ASR metrics for training, cache, and demo.

### Task R3.1. Implement metrics module

Actions:

1. create `libs/audio/metrics.py`;
2. implement text normalization;
3. implement WER with `jiwer`;
4. implement Word Accuracy;
5. define stable result schema;
6. add tests.

Done when:

1. metrics import;
2. tests cover normal cases;
3. tests cover empty or edge transcripts;
4. `METRICS_VERSION` is referenced from `libs/common/versions.py`.

Decision rules:

1. If `jiwer` is missing, add it to dependencies.
2. If reference text is absent, metrics return unavailable rather than fake values.
3. Word Accuracy should be bounded to a clear range.
4. If normalization changes later, bump `METRICS_VERSION`.

## 20. Phase R4. Degradations

Goal: implement shared official degradations before cache, RP5 validation, and training depend on them.

### Task R4.1. Implement degradation module

Actions:

1. create `libs/audio/degradations.py`;
2. implement `far_field_room`;
3. implement `cafe_background`;
4. implement `phone_call`;
5. implement `muffled`;
6. implement `broadband_hiss`;
7. expose versioned parameter metadata;
8. add tests.

Done when:

1. all five degradations exist;
2. each produces valid audio;
3. parameters are inspectable;
4. tests pass;
5. `DEGRADATION_VERSION` is referenced from `libs/common/versions.py`.

Decision rules:

1. If a degradation cannot be implemented exactly, implement deterministic approximation and document it.
2. If output audio validation fails, keep task incomplete.
3. If parameters change after cache exists, bump `DEGRADATION_VERSION` and invalidate cache.
4. Do not freeze degradation version until B7.

Phase R gate: R1, R2, R2.5, R2b, R3, and R4 must pass before training branch can run shared baseline evaluation.

## 21. Phase B0. Raspberry Pi, network, and account gate

Goal: confirm that hardware, network, and external accounts can support public demo deployment.

### Task B0.1. Hardware and LAN checklist

Actions:

1. verify SD card is at least 32 GB;
2. verify Ethernet cable;
3. verify adequate USB-C power supply;
4. verify UPS if available;
5. verify cooling;
6. verify Windows machine and RP5 will be on same LAN;
7. verify router allows SSH LAN.

Done when:

1. hardware status is recorded;
2. known blockers are listed;
3. RP5 setup can proceed.

Decision rules:

1. If cooling is missing, continue setup but do not run soak test until cooling is acceptable.
2. If Ethernet is unavailable, stop because public demo plan assumes Ethernet.
3. If SD card is too small, replace before installing.

### Task B0.2. Account and connectivity checklist

Actions:

1. verify Cloudflare account;
2. verify AssemblyAI account and credits;
3. verify RP5 can access internet when installed;
4. test AssemblyAI endpoint latency when network is available.

Latency probe:

```bash
curl -o /dev/null -s -w "%{time_total}\n" -X POST https://api.assemblyai.com/v2/transcript
```

Note:

```text
HTTP 401 is expected without API key. This measures connection and response latency, not functional success.
```

Done when:

1. account status is recorded;
2. network status is recorded;
3. AssemblyAI latency policy is evaluated.

Decision rules:

1. If latency exceeds 5 seconds consistently, AssemblyAI is limited to cache pre-warm and preloaded examples in v1.
2. If AssemblyAI account is unavailable, Whisper local remains the default path.
3. If Cloudflare account is unavailable, continue local LAN work and block public exposure.

## 22. Phase B1. RP5 headless image

Goal: boot and SSH into RP5 without HDMI.

### Task B1.1. Install Raspberry Pi OS headless

Actions:

1. flash Raspberry Pi OS from Windows;
2. enable SSH;
3. configure user;
4. configure hostname;
5. do not configure WiFi;
6. connect RP5 by Ethernet;
7. SSH from PowerShell.

Done when:

1. RP5 boots;
2. SSH from Windows works;
3. hostname and user are recorded.

Decision rules:

1. If SSH fails, troubleshoot LAN before installing project dependencies.
2. If hostname resolution fails, connect by IP and record it.
3. If WiFi was configured accidentally, keep Ethernet as runtime path.

## 23. Phase B2. RP5 base system

Goal: prepare RP5 for repository work and Docker runtime.

### Task B2.1. Install base system dependencies

Actions:

1. update system packages;
2. install Git;
3. install Docker;
4. install Docker Compose;
5. add user to Docker group;
6. test Docker without sudo after re-login.

Done when:

1. Docker works;
2. Compose works;
3. Git works;
4. tracker records versions.

Decision rules:

1. If Docker requires re-login, stop and instruct re-login before proceeding.
2. If Docker install fails, record exact package error.
3. If Compose is unavailable, install plugin or standalone equivalent and record command.

### Task B2.2. Configure Git and VS Code Remote SSH

Actions:

1. configure SSH keys if needed;
2. clone repo or fetch existing clone;
3. checkout `feature/demo-runtime-rp5-v1` or `demo-rp5-v1` as appropriate;
4. configure VS Code Remote SSH;
5. open repo remotely.

Done when:

1. repo opens from VS Code over SSH;
2. branch is correct;
3. Git remote works.

Decision rules:

1. If repo already exists, fetch and checkout instead of recloning.
2. If SSH key setup fails, use HTTPS temporarily only if credentials are safe.
3. Do not edit files in two unsynced copies without committing and pulling.

### Task B2.5. Generate arm64 lock on RP5 if missing

Actions:

1. check whether `requirements.lock.arm64` exists;
2. if missing, generate it on RP5;
3. install from it;
4. run import tests;
5. commit lock.

Done when:

1. arm64 lock exists;
2. install is reproducible on RP5;
3. tests or import checks pass.

Decision rules:

1. If arm64 lock already exists, verify install and skip generation.
2. If generation fails, record exact dependency blocker.
3. Do not proceed to public exposure without a working RP5 install path.

## 24. Phase B3. Lightweight demo runtime

Goal: run public demo mode without Postgres, MinIO, Grafana, Prometheus, or OTel on RP5.

### Task B3.1. Create demo Compose runtime

Actions:

1. create `docker-compose.demo.yml` or `infra/compose/docker-compose.demo.yml`;
2. define demo API service;
3. define demo worker service;
4. use SQLite;
5. use filesystem local storage;
6. keep platform Compose intact.

Done when:

1. demo Compose starts on development machine or RP5;
2. platform Compose remains available;
3. service names are clear.

Decision rules:

1. If existing Compose can support profiles cleanly, use profiles.
2. Else create a separate demo Compose file.
3. Do not remove platform services.
4. If demo mode starts platform dependencies, task is incomplete.

### Task B3.2. Implement demo persistence and queue limit

Actions:

1. create SQLite job state for demo mode;
2. create filesystem artifact root;
3. create the minimum SQLite tables listed below;
4. implement local worker concurrency 1;
5. implement queue max 10;
6. return HTTP 503 when queue is full.

Required SQLite schema contract, column names and types only:

```text
jobs:
  job_id TEXT PRIMARY KEY
  status TEXT
  created_at TIMESTAMP
  updated_at TIMESTAMP
  provider TEXT
  degradation_id TEXT
  enhancer_version TEXT
  input_artifact_path TEXT
  degraded_artifact_path TEXT
  enhanced_artifact_path TEXT NULL
  result_json TEXT NULL
  error_message TEXT NULL
  expires_at TIMESTAMP NULL

cache_entries:
  cache_key TEXT PRIMARY KEY
  example_id TEXT
  degradation_id TEXT
  degradation_version TEXT
  asr_provider TEXT
  asr_model_version TEXT
  enhancer_version TEXT
  metrics_version TEXT
  result_json TEXT
  artifact_root TEXT
  created_at TIMESTAMP
  validated_at TIMESTAMP NULL

usage_ledger:
  ledger_id TEXT PRIMARY KEY
  provider TEXT
  session_id_hash TEXT NULL
  job_id TEXT NULL
  audio_duration_seconds REAL
  estimated_cost_usd REAL
  status TEXT
  cap_state TEXT
  created_at TIMESTAMP

admin_state:
  key TEXT PRIMARY KEY
  value TEXT
  updated_at TIMESTAMP
```

Done when:

1. demo jobs persist locally;
2. required SQLite tables exist;
3. queue limit is enforced;
4. tests cover full queue behavior;
5. no long processing runs in request handler.

Decision rules:

1. If Celery is reused, configure it lightly for demo mode.
2. If simpler local queue is used, keep interface compatible with API expectations.
3. If queue length cannot be measured, do not claim max queue enforcement.

## 25. Phase B4. Demo endpoints

Goal: expose a public-demo API without breaking `/v1` platform endpoints.

### Task B4.1. Implement demo health and example listing

Actions:

1. implement `GET /demo/health`;
2. implement `GET /demo/examples`;
3. define demo example schema;
4. return empty or placeholder examples only if B6 has not run;
5. add tests.

Done when:

1. health endpoint works;
2. examples endpoint works;
3. tests pass;
4. `/v1` endpoints remain intact.

Decision rules:

1. `/demo/health` should check demo runtime health, not every external provider.
2. If examples are not curated yet, response must be explicit and not fake benchmark results.
3. If endpoint breaks platform mode, fix before continuing.

### Task B4.2. Implement demo audio endpoints

Actions:

1. implement clean audio endpoint;
2. implement degraded audio endpoint;
3. validate example IDs;
4. return correct media type;
5. add tests.

Done when:

1. valid example audio can be fetched;
2. invalid example returns 404;
3. audio endpoints do not expose arbitrary filesystem paths.

Decision rules:

1. If example audio is missing, return 404 or explicit unavailable state.
2. Do not allow path traversal.
3. If media type is unknown, use safe audio content type.

### Task B4.3. Implement cached run and job endpoints

Actions:

1. implement `POST /demo/run-cached`;
2. implement `POST /demo/upload` placeholder or full job creation if ready;
3. implement `GET /demo/jobs/{job_id}`;
4. implement `GET /demo/jobs/{job_id}/result`;
5. implement `GET /admin/stats` behind basic auth or configured protection.

Done when:

1. cached result path works for examples;
2. upload creates async job or returns not-ready status explicitly;
3. job status and result are stable;
4. admin stats are not public without protection.

Decision rules:

1. If cache miss occurs for preloaded example, enqueue recomputation only when safe.
2. If AssemblyAI cap blocks recomputation, return clear provider state.
3. If admin auth is missing, do not expose sensitive stats publicly.

## 26. Phase B5. Core demo processing

Goal: allow raw ASR and enhanced ASR through shared provider and enhancer interfaces.

### Task B5.1. Implement Whisper local provider

Actions:

1. create `libs/asr/whisper_provider.py`;
2. use `faster-whisper tiny.en` for RP5;
3. normalize provider result schema;
4. expose ASR model version;
5. add tests or import checks.

Done when:

1. provider imports;
2. one short audio file can be transcribed locally where dependencies exist;
3. normalized schema matches other providers.

Decision rules:

1. If `faster-whisper` is unavailable in CI, skip live import with clear marker and test normalization separately.
2. If model download is needed, cache outside repo.
3. If provider detects non-English language with probability above 0.5, surface warning in upload flow.

### Task B5.2. Adapt AssemblyAI provider for demo mode

Actions:

1. reuse `libs/asr/assemblyai_provider.py`;
2. add demo timeout and retry policy;
3. expose provider status;
4. ensure no silent fallback to Whisper;
5. add mocked tests.

Done when:

1. AssemblyAI provider obeys retry policy;
2. provider state is visible;
3. no silent fallback exists;
4. tests pass.

Decision rules:

1. Timeout or 5xx gets one retry after 2 seconds.
2. If retry fails, show the exact configured safe message.
3. If quota is exhausted, do not call AssemblyAI.
4. If key is missing, state is `AssemblyAI disabled`.

### Task B5.3. Implement enhancer interface, bypass, and MetricGAN+ hook

Actions:

1. define enhancer interface in `libs/audio/enhancement.py`;
2. implement bypass enhancer;
3. create an empty MetricGAN+ pretrained hook with the final function or class name expected by T4.1;
4. document in code that T4.1 owns the real MetricGAN+ implementation;
5. expose enhancer version;
6. add tests.

Done when:

1. raw ASR and enhanced ASR path can call the same interface;
2. bypass is honest and explicit;
3. MetricGAN+ hook exists but does not pretend to be implemented;
4. tests pass.

Decision rules:

1. If no trained enhancer exists, bypass remains default.
2. B5.3 must not implement the real MetricGAN+ wrapper.
3. T4.1 in the training branch fills the hook and opens or prepares a PR into `demo-rp5-v1`.
4. If pretrained or exported enhancer exists later, add it without breaking bypass.
5. If enhancer output is invalid, use fallback policy and record metadata.

## 27. Phase B6. Curated public examples

Goal: create ten public examples with verified ground truth and measurable degradation.

### Task B6.1. Select candidate examples

Actions:

1. choose examples from split not used in training;
2. choose duration 5 to 15 seconds;
3. include at least 5 speakers;
4. attempt reasonable gender balance if metadata allows;
5. avoid inappropriate public content;
6. write candidate manifest.

Done when:

1. 10 candidate examples exist;
2. source split and exclusion status are recorded;
3. ground truth source is available.

Decision rules:

1. If gender metadata is unavailable, document limitation.
2. If fewer than 5 speakers are available, select more candidates.
3. If an example may be unsuitable for public demo, exclude it.

### Task B6.2. Verify ground truth and ASR drop

Actions:

1. manually verify ground truth;
2. apply five degradations;
3. run Whisper local or available ASR;
4. confirm degradation produces visible ASR drop;
5. write `demo_examples.json`.

Done when:

1. 10 examples have verified GT;
2. examples have clean and degraded audio references;
3. ASR drop is measurable;
4. training branch can exclude them.

Decision rules:

1. If an example has no ASR drop under any degradation, replace it.
2. If GT is uncertain, replace or correct it.
3. If selected examples change, notify training branch to rerun exclusion.

## 28. Phase B7. Freeze degradations

Goal: freeze official demo and training degradation parameters.

### Task B7.1. Set `DEGRADATION_VERSION` to `degradation_v1`

Actions:

1. review degradation parameters;
2. confirm all five degradations produce valid audio;
3. confirm public examples show reasonable ASR drop;
4. set `DEGRADATION_VERSION = "degradation_v1"`;
5. run tests;
6. update tracker.

Done when:

1. degradation version is frozen;
2. tests pass;
3. training branch is unblocked for dry-run and full training.

Decision rules:

1. If parameters need to change after this point, bump version and invalidate cache.
2. If public examples do not show ASR drop, return to B6.
3. If training branch has already started with a previous version, coordinate before changing.

Phase B7 gate: training dry-run and full training cannot begin before this gate passes.

## 29. Phase B6.5. Cross-validation with RP5 and Surrey ASR

Goal: compare RP5 `faster-whisper` and Surrey `openai-whisper` on public examples and enhancer outputs.

Dependencies:

```text
B6 complete.
B7 complete.
Training branch T4 complete if evaluating MetricGAN+ pretrained.
```

### Task B6.5.1. Run public examples on RP5 and Surrey reference

Actions:

1. run 10 examples times 5 degradations with `faster-whisper tiny.en` on RP5;
2. run the same set with `openai-whisper` on development machine or Surrey;
3. compute WER and Word Accuracy with shared metrics;
4. compare results;
5. write report.

Done when:

1. both ASR implementations have results;
2. average difference is computed;
3. decision rule is applied;
4. report is committed if small.

Decision rules:

1. If average difference is within plus or minus 2 Word Accuracy points, treat as comparable.
2. If difference exceeds plus or minus 5 points, freeze exact dependency versions, document discrepancy in `docs/model_card.md`, use RP5 metrics for public demo, and use openai-whisper metrics for training reports.
3. If difference is between 2 and 5 points, document caution and use RP5 metrics for public demo.

### Task B6.5.2. Validate enhancer behavior on RP5

Actions:

1. install or load available enhancer wrapper;
2. run selected examples on RP5;
3. compare degraded versus enhanced ASR;
4. measure latency;
5. decide whether enhancer is enabled by default.

Done when:

1. RP5 enhancer path works or fails explicitly;
2. improvement or limitation is documented;
3. latency is recorded;
4. UI wording can be honest.

Decision rules:

1. If enhancer improves examples and latency is acceptable, enable it for cached examples.
2. If enhancer is weak but safe, show it as experimental.
3. If enhancer is too slow or broken, keep bypass default and document limitation.
4. Do not re-curate all examples solely because enhancer improvement is weak.

## 30. Phase B8. Reproducible cache

Goal: serve curated examples from versioned cache without unnecessary API calls or live inference.

### Task B8.1. Implement cache scripts

Actions:

1. create `scripts/prewarm_cache.py`;
2. create `scripts/validate_cache.py`;
3. create `scripts/invalidate_cache.py`;
4. use canonical cache key;
5. store cache metadata in `cache_entries` using the schema contract from B3.2;
6. add tests or dry-run checks.

Done when:

1. cache can be prewarmed;
2. cache can be validated;
3. cache can be invalidated by version;
4. `cache_entries` records all cache key components;
5. scripts do not require secrets for Whisper-only cache.

Decision rules:

1. Operational prewarm respects AssemblyAI caps.
2. `--bypass-budget-check` is allowed only for controlled handoff or release.
3. If cache key changes, validation must fail old entries.
4. If cache is missing for a public example, UI must not pretend it is cached.

## 31. Phase B9. User uploads

Goal: allow users to upload short audio and compare raw versus enhanced paths safely.

### Task B9.1. Implement upload validation

Actions:

1. enforce max duration 30 seconds;
2. enforce max size 5 MB;
3. validate on frontend and backend;
4. save temporarily;
5. create async job.

Done when:

1. valid uploads work;
2. oversized uploads fail clearly;
3. invalid audio fails clearly;
4. no long processing runs in request handler.

Decision rules:

1. Backend is authoritative.
2. If duration cannot be read safely, reject upload.
3. If file size exceeds 5 MB, return HTTP 413.
4. If audio format is unsupported, return HTTP 415.

### Task B9.2. Implement upload processing flow

Actions:

1. generate degraded audio;
2. allow playback of original;
3. allow playback of degraded;
4. run raw ASR;
5. run enhanced ASR;
6. compute Word Accuracy only if GT is provided;
7. keep manual GT in memory only.

Required UI text:

```text
Optional ground truth is used only to calculate accuracy for this session. It is not stored.
```

Done when:

1. upload works end to end with Whisper local;
2. manual GT is not persisted;
3. results show transcriptions and metrics when available.

Decision rules:

1. If GT is absent, show transcriptions only.
2. If GT is present, compute metrics in current session only.
3. If enhanced path fails, show raw result and safe enhanced error.
4. Do not log manual GT.

### Task B9.3. Add non-English warning

Actions:

1. read language detection result from `faster-whisper`;
2. if language is not English and probability is above 0.5, show warning;
3. allow user to continue explicitly;
4. keep warning visible with results.

Required UI text:

```text
Detected language is not English. This demo is designed for English speech, so results may be unreliable. Continue?
```

Done when:

1. warning appears for likely non-English speech;
2. user can continue;
3. results retain warning.

Decision rules:

1. Do not block non-English audio.
2. Do not hide warning after processing.
3. If language probability is unavailable, do not show false warning.

### Task B9.4. Implement cleanup job

Actions:

1. create `scripts/cleanup_uploads.py`;
2. delete uploads and derived artifacts older than 24 hours;
3. delete temporary transcriptions and expired jobs;
4. do not delete example cache, aggregated usage ledger, logs, or cost records;
5. configure cron on RP5 every hour;
6. make script idempotent.

Done when:

1. cleanup script works;
2. cron is configured;
3. last successful cleanup timestamp is available to `/admin/stats`;
4. tests or dry-run checks pass.

Decision rules:

1. If cleanup fails, log error and keep stats visible.
2. If artifact age cannot be determined, do not delete it.
3. If script deletes cache, task fails and must be fixed.

## 32. Phase B10. AssemblyAI cost controls

Goal: allow AssemblyAI demo use without uncontrolled spend.

### Task B10.1. Implement usage ledger

Actions:

1. use dedicated API key through `.env` only;
2. store usage ledger in SQLite using the `usage_ledger` schema contract from B3.2;
3. estimate cost by duration;
4. track daily spend;
5. track total spend;
6. expose provider state to UI.

Limits:

```text
Daily soft cap: 5 USD
Warning cap: 35 USD
Hard cap: 45 USD
Email warning: gabobibbo@gmail.com
Autopay: off at start
```

Done when:

1. usage ledger records calls;
2. caps are enforced;
3. UI state is accurate;
4. tests cover cap transitions.

Decision rules:

1. If daily soft cap is reached, block AssemblyAI for the day.
2. If warning cap is reached, email warning.
3. If hard cap is reached, disable AssemblyAI.
4. If ledger write fails, do not call AssemblyAI.

### Task B10.2. Enforce upload-specific AssemblyAI rules

Rules:

```text
Whisper local: available by default.
AssemblyAI: only if daily cap not exceeded.
AssemblyAI: only if audio duration <= 30 seconds.
AssemblyAI: only if session has not exceeded 3 AssemblyAI uses in 24 hours.
```

Actions:

1. implement session usage check;
2. implement duration check;
3. implement daily cap check;
4. surface clear UI states.

Done when:

1. uploads cannot exceed configured AssemblyAI access rules;
2. Whisper remains available;
3. no silent fallback occurs.

Decision rules:

1. If AssemblyAI is blocked, user may choose Whisper.
2. If AssemblyAI fails, do not automatically switch to Whisper.
3. If session tracking is unavailable, disable AssemblyAI rather than allowing unlimited use.

## 33. Phase B11. Frontend final mobile-first

Goal: build a public demo UI that a recruiter can understand without reading GitHub.

### Task B11.1a. Implement demo modes and selectors

Actions:

1. keep Next.js;
2. integrate `/demo` endpoints;
3. add curated example mode;
4. add upload mode;
5. add provider selector;
6. add degradation selector;
7. surface provider state;
8. surface cache state.

Done when:

1. curated example mode loads available examples;
2. upload mode creates or prepares jobs through the demo API;
3. provider selector reflects Whisper, AssemblyAI, disabled, quota, and unavailable states;
4. degradation selector uses the five frozen degradation IDs.

Decision rules:

1. If backend is unavailable, show clear English error.
2. If cache is used, show cache message.
3. If provider quota is exhausted, show the exact provider state.
4. Do not show fake benchmark results for examples that are not cached or computed.

### Task B11.1b. Implement audio playback and ground truth UI

Actions:

1. add original audio player;
2. add degraded audio player;
3. add GT display for curated examples;
4. add optional manual GT textarea for uploads;
5. show required manual-GT privacy text;
6. ensure manual GT is sent only for session metric computation if needed.

Required UI text:

```text
Optional ground truth is used only to calculate accuracy for this session. It is not stored.
```

Done when:

1. original audio can be played and paused;
2. degraded audio can be played and paused;
3. curated examples show verified GT;
4. upload GT textarea is optional and usable;
5. manual GT is not stored or logged.

Decision rules:

1. If audio is unavailable, show explicit unavailable state.
2. If manual GT is absent, show transcriptions without metrics.
3. If manual GT is present, compute metrics only for that session.
4. Do not add spectrograms.
5. Do not add waveforms.

### Task B11.1c. Implement comparison and pipeline details

Actions:

1. add raw ASR transcription panel;
2. add enhanced ASR transcription panel;
3. add Word Accuracy and WER when GT is available;
4. add Pipeline details;
5. show provider, ASR model version, degradation version, metrics version, enhancer version, job ID, latency, and cache status;
6. make layout mobile-first.

Done when:

1. a non-technical user can understand the raw versus enhanced comparison;
2. cached state is visible;
3. provider state is visible;
4. enhancer state is visible;
5. mobile layout is usable.

Decision rules:

1. If enhancer is bypass, label it honestly.
2. If enhanced path fails, show raw result and safe enhanced error.
3. If metrics are unavailable, do not display empty or misleading numbers.
4. If pipeline details are too large for mobile, collapse them behind a visible details section.

### Task B11.2. Validate mobile criteria

Criteria:

1. initial load completes in less than 5 seconds over 4G target conditions where practical;
2. play and pause work;
3. no horizontal scroll;
4. manual GT textarea is usable with virtual keyboard;
5. submit button is not covered.

Done when:

1. mobile checks pass;
2. screenshots can be taken for README;
3. known limitations are recorded.

Decision rules:

1. If performance misses target due to large assets, reduce assets.
2. If layout scrolls horizontally, fix before public smoke test.
3. If audio playback fails on mobile, keep task incomplete.

### Task B11.5. Add RP5 deployment photo

Actions:

1. take photo of the RP5 running;
2. save as `assets/rp5_deployment_photo.jpg`;
3. reference it from README or docs after the deployment section exists.

Done when:

1. photo exists;
2. file size is reasonable for GitHub;
3. image is referenced from documentation.

Decision rules:

1. If photo contains private information, retake or crop it.
2. If deployment is not running yet, postpone photo and keep tracker open.

## 34. Phase B12. Lightweight observability

Goal: operate the RP5 demo without Grafana on the device.

### Task B12.1. Implement logs and admin stats

Actions:

1. emit JSON logs;
2. configure log rotation;
3. implement protected `/admin/stats`;
4. include uptime;
5. include request count;
6. include jobs;
7. include queue length;
8. include cache hit rate;
9. include AssemblyAI spend estimate;
10. include disk usage;
11. include CPU temperature;
12. include last errors;
13. include Cloudflare tunnel status;
14. include last successful cleanup timestamp.

Done when:

1. admin stats are useful;
2. secrets are not exposed;
3. endpoint is protected;
4. logs rotate.

Decision rules:

1. If auth is not configured, do not expose admin stats publicly.
2. If CPU temperature cannot be read, show unavailable state.
3. If Cloudflare status cannot be read, show unavailable state.

### Task B12.2. Add email alerts

Actions:

1. email if disk usage exceeds 80 percent;
2. external health check every 5 minutes;
3. trigger email after 3 consecutive health-check failures;
4. document alert setup.

Health check command:

```bash
curl -fsS https://<demo-url>/demo/health
```

Done when:

1. alert scripts exist;
2. cron or systemd timer is configured;
3. tests or dry-run checks prove logic.

Decision rules:

1. If email is unavailable, log alert and record blocker.
2. If public URL is not configured yet, implement local health check and defer external check.
3. If health check produces false positives, adjust timeout before public smoke test.

## 35. Phase B13. Soak test local

Goal: prove the RP5 demo can run for 24 to 48 hours on LAN.

### Task B13.1. Run local soak test

Load:

```text
Duration: 24 to 48 hours.
Every 15 minutes: 1 random cached job.
Every 6 hours: 1 job forcing recomputation without cache.
Every 2 hours: 1 synthetic 10 second upload.
```

Artifacts:

```text
runs/soak_<timestamp>/
```

Done when:

1. zero crashes;
2. P95 latency is less than 2 times baseline;
3. RAM is not growing continuously;
4. sustained temperature is below 75 C;
5. disk use is stable;
6. cleanup works.

Decision rules:

1. If temperature exceeds 75 C, stop and improve cooling.
2. If RAM grows continuously, investigate leak before public exposure.
3. If cleanup fails, return to B9.4.
4. If recomputation fails only due to AssemblyAI cap, document and continue with Whisper path.

## 36. Phase B14. Public exposure

Goal: expose the demo outside the local network.

### Task B14.1. Configure Cloudflare Tunnel

Actions:

1. configure Cloudflare Tunnel;
2. use `trycloudflare.com` during development;
3. use own subdomain for CV if setup takes less than half a day;
4. configure HTTPS;
5. configure `cloudflared` as systemd service;
6. set restart policy;
7. add failure alert if practical.

Systemd requirements:

```text
Restart=always
RestartSec=10
```

Done when:

1. demo opens from outside LAN;
2. HTTPS works;
3. tunnel restarts automatically;
4. URL is recorded.

Decision rules:

1. If custom domain setup exceeds half a day, use `trycloudflare.com` for development and continue.
2. If tunnel fails repeatedly, keep public exposure incomplete.
3. If HTTPS is unavailable, do not publish URL in README.

## 37. Phase B15. Public smoke test

Goal: verify the public URL is safe to share.

### Task B15.1. Run smoke test from multiple networks

Test from:

1. Windows local;
2. mobile with cellular data;
3. another WiFi network;
4. VPN or external tester.

Cover:

1. 10 examples;
2. 5 degradations;
3. Whisper;
4. AssemblyAI if enabled;
5. upload without GT;
6. upload with manual GT;
7. upload limit;
8. provider quota state;
9. mobile layout.

Done when:

1. public URL works;
2. no critical UI path fails;
3. upload limits are enforced;
4. quota states are accurate;
5. URL can go into README, CV, and LinkedIn.

Decision rules:

1. If mobile fails, return to B11.
2. If public tunnel fails, return to B14.
3. If provider quota state is wrong, return to B10.
4. If cached examples fail, return to B8.

## 38. Phase H. Handoff from training to RP5

Goal: activate a trained or selected enhancer artifact from the training branch, or keep bypass honestly.

### Task H1. Receive training artifact or final fallback decision

Actions:

1. read training branch handoff note;
2. verify `ENHANCER_VERSION`;
3. verify checksum;
4. verify artifact location;
5. verify model card update;
6. decide whether to deploy artifact.

Done when:

1. artifact is available or fallback is explicit;
2. deployment decision is recorded;
3. tracker knows training handoff status.

Decision rules:

1. If no artifact exists, keep bypass or pretrained outcome.
2. If artifact exists but checksum fails, reject it.
3. If artifact exists but RP5 cannot load it, reject it and record reason.
4. If artifact works, proceed to H2.

### Task H2. Activate enhancer version on RP5

Actions:

1. set `ENHANCER_VERSION` in RP5 `.env`;
2. restart demo worker;
3. run cache prewarm with bypass budget flag for controlled release;
4. validate cache;
5. validate two examples manually;
6. run public smoke test.

Commands conceptually:

```bash
python scripts/prewarm_cache.py --bypass-budget-check --enhancer-version=<new>
python scripts/validate_cache.py
```

Done when:

1. new enhancer is active or rollback has succeeded;
2. cache validates;
3. public smoke test passes;
4. README can state the correct enhancer status.

Decision rules:

1. If activation fails, restore previous `ENHANCER_VERSION`.
2. If cache validation fails, do not publish new enhancer.
3. If public smoke test fails, rollback.
4. If the enhancer is bypass, label it as bypass and do not imply learned improvement.

## 39. Phase C. GitHub narrative and final documentation

Goal: make the repository clear and useful for recruiters and technical reviewers.

### Task C1. Final README

README must show:

1. live demo link;
2. short GIF;
3. problem statement;
4. architecture;
5. RP5 deployment;
6. Whisper local;
7. AssemblyAI cloud provider;
8. enhancement model or honest fallback;
9. platform mode;
10. public demo mode;
11. cost controls;
12. privacy;
13. how to run locally.

Done when:

1. README explains the project before code inspection;
2. claims match implemented behavior;
3. screenshots or GIFs exist;
4. no broken links remain.

Decision rules:

1. If live demo is not stable, do not present it as always available.
2. If enhancer is bypass or weak, state that clearly.
3. If AssemblyAI is disabled, describe it as optional or quota-limited.
4. If RP5 photo is unavailable, do not block README but leave asset task pending.

### Task C2. Documentation set

Create or update:

```text
docs/architecture.md
docs/public_demo.md
docs/platform_mode.md
docs/training.md
docs/model_card.md
docs/deployment_raspberry_pi.md
docs/assemblyai_cost_controls.md
docs/privacy.md
docs/rollback.md
docs/release_checklist.md
```

Done when:

1. docs explain demo, training, deployment, privacy, rollback, and costs;
2. model card matches training branch outcome;
3. docs do not expose secrets;
4. docs link to relevant scripts and commands.

Decision rules:

1. If training did not produce a model, training docs must say so.
2. If deployment is Cloudflare-based, document tunnel restart behavior.
3. If cost caps are estimates, label them as estimates.
4. If privacy behavior differs between examples and uploads, document both.

### Task C3. Assets

Create:

```text
assets/demo_short.gif
assets/comparison_screenshot.png
assets/pipeline_details_screenshot.png
assets/architecture_diagram.png
assets/rp5_deployment_photo.jpg
```

Done when:

1. assets exist;
2. files are reasonably sized;
3. README references key assets;
4. assets do not reveal secrets or private network details.

Decision rules:

1. If a GIF is too large, compress or replace with screenshot.
2. If architecture diagram becomes outdated, update it before final README.
3. If RP5 photo is unavailable, do not fake it.

## 40. Final demo/platform branch definition of done

This branch is done when:

1. platform MVP is preserved by tag;
2. split plans exist under `docs/plans/`;
3. demo/platform trackers are current;
4. ASR adapters live under `libs/asr`;
5. audio pipeline lives under `libs/audio`;
6. versions live under `libs/common/versions.py`;
7. metrics and degradations are shared and tested;
8. public examples are curated;
9. degradations are frozen;
10. RP5 demo mode runs with SQLite and filesystem storage;
11. cache is versioned and validated;
12. upload flow works with cleanup;
13. AssemblyAI is cost-controlled;
14. frontend is mobile-first;
15. observability is adequate for RP5 operation;
16. public URL passes smoke test;
17. training handoff is applied or bypass is honestly documented;
18. README, docs, and assets are final enough for CV and LinkedIn;
19. branch is pushed to GitHub;
20. pull request into `demo-rp5-v1` is ready or merged.

## 41. Estimated timeline and cut rules

These estimates are planning aids, not promises. Use them to decide whether to pursue full training before cluster access or personal availability becomes a blocker.

Estimated duration:

```text
S0 + R0-R4: 4 to 7 focused work sessions
B0-B5: 4 to 7 focused work sessions
B6-B8: 3 to 5 focused work sessions
B9-B12: 5 to 8 focused work sessions
B13-B15: 2 to 4 elapsed days because soak testing needs wall time
C1-C3: 2 to 4 focused work sessions
Training branch T0-T4: can run in parallel after S0 and after R1-R4 are merged
Training branch T5-T8: depends on B7, T2.5, cluster availability, and enhancer feasibility
Total realistic range: 5 to 7 weeks for a strong public version if work is steady
```

Cut rules:

1. If full training cannot finish before cluster access becomes unreliable, use the best of MetricGAN+ pretrained or bypass and document the limitation.
2. If RP5 deployment is ready before A6, publish with the honest current enhancer state and keep the training handoff as a later branch update.
3. If AssemblyAI cost controls are not complete, keep AssemblyAI disabled in public mode.
4. If frontend is not final but backend is strong, delay public exposure until B11.2 passes.

## 42. Practical control rules

1. Preserve platform mode before changing public demo mode.
2. Do not delete old code until replacement is validated.
3. Do not start RP5 public exposure before local demo works.
4. Do not make CI require real provider credentials.
5. Do not silently switch AssemblyAI to Whisper.
6. Do not store manual ground truth from uploads.
7. Do not serve stale cache silently.
8. Do not claim a trained enhancer exists unless training branch produced one.
9. Keep user-facing text in English.
10. Keep branch-specific trackers separate.
11. Stop at gates and report status.
12. If generated code conflicts with this plan, follow this plan.
13. If this plan conflicts with `CLAUDE.md`, follow `CLAUDE.md` and record the conflict.
