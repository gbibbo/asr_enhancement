# Robust ASR Orchestrator Plan v3.4.7

This file is the strategic spine. It is read by the human orchestrator and by ChatGPT web when approving or rejecting the agent's per-task execution plans. It does not contain executable commands. Execution lives in `docs/plans/robust_asr_agent_plan_v3_4_7.md`.

The literal shape of every report exchanged in chat (State Packet, Planning Report, Execution Report, Phase Gate Report, Approval Packet, Supplemental Evidence Report) is defined in `docs/plans/state_packet_schemas_v1.yaml`. This orchestrator plan and the agent plan both reference that file. If a plan and the schemas file disagree on any field, the agent records `PLAN_CONFLICT` and stops.

The live tracker is `docs/progress/robust_asr_progress.yaml`. Claude Code reads and updates it inside the repository. ChatGPT web does not assume live tracker access. ChatGPT makes decisions from the state packets and execution reports that Claude Code provides in chat.


## 0. Two consumers, one live tracker

This plan family has two readers, but only one reader has live repository state.

```text
Orchestrator:    ChatGPT web plus the human operator. Approves, rejects,
                 or corrects per-task plans and completion reports.
                 Uses the uploaded repository zip as structural context only.
                 Uses Claude's latest state packet as the current state.
                 Does not run commands and does not edit the tracker directly.

Agent:           Claude Code in VS Code on datamove1.surrey.ac.uk
                 (or local for non-Slurm work). Reads the agent plan
                 and the live tracker. Runs commands. Writes artifacts.
                 Updates the tracker last, before commit.
```

Boundaries:

```text
1. The live tracker lives in the repository and is the source of truth.
2. Claude Code owns live tracker access. ChatGPT does not assume that
   the uploaded zip contains the current tracker state.
3. ChatGPT approves or rejects using a self-contained State Packet,
   Planning Report, Execution Report, or Phase Gate Report produced by
   Claude Code.
4. ChatGPT returns an Approval Packet in chat. Claude Code records that
   packet in `docs/progress/robust_asr_progress.yaml` before advancing.
5. The agent never advances past a task approval point or phase gate
   without an approval signal recorded in the tracker, unless the
   tracker explicitly sets the corresponding continue override.
6. The orchestrator never edits source files, configs, scripts, reports,
   or tracker files directly. It sends decisions back to Claude Code.
7. If this file and the agent plan disagree on a task ID, marker,
   outcome label, report format, or approval protocol, the agent stops
   and records `PLAN_CONFLICT`.
```

Current-state rule:

```text
The uploaded zip is a snapshot, not live state. It may be used to inspect
structure, conventions, and prior implementation. It must not be used to
infer current task status after Claude has started editing the repo.
For current state, ChatGPT relies on Claude's latest State Packet and
Execution Report. If those are insufficient, ChatGPT requests a
Supplemental Evidence Report instead of inferring from the old zip.
```

Single-queue rule:

```text
There is exactly one execution queue. The queue is the ordered task list
in the agent plan plus the live tracker state. ChatGPT may request
planning for an expected task, but Claude Code must derive the
authoritative next task from the tracker.
```

Pre-bootstrap exception:

```text
Before docs/progress/robust_asr_progress.yaml exists, P0.0 is the only
legal task. Claude Code runs P0.0 in BOOTSTRAP_NO_TRACKER mode, performs
read-only source-branch and RP5-branch inventory, returns a
Pre-bootstrap Inventory Report, and stops. P0.1 creates the target
branch, materializes reports/robust_asr/repository_inventory.md, creates
the tracker, and records P0.0 PASS. ChatGPT must not ask Claude to run
any task other than P0.0 or P0.1 before the tracker exists.
```


## 0.1 Repository integration authority

The new plan family runs inside an existing repository. ChatGPT must not
allow Claude Code to decide what to reuse by intuition. The repository
integration policy is part of P0 and is binding for every later task.

Branch roles:

```text
Existing source branch:
  feature/training-datamove1-v1
  Role: structural and implementation base for the new datamove1 work.
  It is inspected, then used as the branch parent.

New datamove1 branch:
  feature/robust-asr-lora-router-datamove1-v1
  Role: only active branch for robust_asr training, evaluation, router,
  reports, handoff package, and robust_asr tracker.

RP5 runtime branch:
  feature/demo-runtime-rp5-v1
  Role: consumes the datamove1 handoff by tag. It does not consume
  floating HEAD from the robust_asr branch.
```

Repository-state rules:

```text
1. The correct repo root for this plan is
   /mnt/fast/nobackup/users/gb0048/asr_enhancement.
2. Any reference to /mnt/fast/nobackup/users/gb0048/asr_enhancement_platform
   is legacy context unless a later task explicitly proves otherwise.
3. Existing trackers such as docs/progress/training_datamove1_progress.*
   and docs/claude_task_progress.* are not robust_asr state.
4. Existing plans such as plan.md, demo_platform_plan.md, and
   training_datamove1_plan.md are templates or lineage references only.
5. Existing runtime code may be reused only if P0.2 classifies the path
   and the approved task cites the matching reuse_policy_v1.yaml row.
6. Existing outputs, caches, checkpoints, manifests, and reports are not
   robust_asr evidence until a robust_asr validator accepts them under
   the current plan.
7. CLAUDE.md must preserve existing repo-level rules. Claude may update
   only the delimited ROBUST_ASR_PROFILE block.
8. Unclassified paths are no-touch by default.
9. The RP5 runtime branch feature/demo-runtime-rp5-v1 must exist on
   origin before portfolio readiness, but it does not block datamove1 P0.
   P0.0 verifies the reference in read-only BOOTSTRAP_NO_TRACKER mode.
   P0.1 records the observed SHA or activates PENDING_RP5_INTEGRATION
   after creating the tracker. The orchestrator must treat
   PENDING_RP5_INTEGRATION as expected from P0 onward instead of from P9.
10. Legacy state paths (existing trackers and existing plans) must be
    classified in configs/robust_asr/reuse_policy_v1.yaml with
    permitted_use: read_only and commit_allowed: false. They must not be
    classified as forbidden, because P10.3 plan_tracker_consistency
    needs to read them.
```

Required P0 integration artifacts:

```text
reports/robust_asr/asset_inventory.md
reports/robust_asr/repo_integration_policy.md
reports/robust_asr/touch_policy.md
configs/robust_asr/reuse_policy_v1.yaml
scripts/robust_asr/validate_report_shape.py
artifacts/robust_asr/state_packets/report_shape_fixtures/
```

Orchestrator rule:

```text
Do not approve P0 unless those artifacts exist, the tracker references
all of them, and the P0 Phase Gate Report says no_unapproved_reuse=true.
Do not approve a task plan that edits outside robust_asr-owned paths
unless it cites the exact reuse_policy_v1.yaml row and that row allows
that task to edit the path.
```


## 1. Project goal

Build a portable ASR system that demonstrates honest engineering and ships even when experiments fail.

Final deployable architecture:

```text
remote browser client
  -> RP5 web runtime
  -> audio validation and transcoding
  -> Whisper base local backend
  -> optional Whisper LoRA local backend
  -> optional AssemblyAI backend
  -> ASR-aware router or deterministic selector
  -> transcript, confidence, latency, routing metadata, report links
```

Two independent technical claims:

```text
Claim 1 (LoRA experiment):
  Does Whisper base.en adapted with LoRA improve over the original
  local Whisper baseline under controlled ASR degradations?

Claim 2 (system experiment):
  Can a router-driven (or selector-driven) ASR system improve the
  quality, latency, cost, and third-party-exposure trade-off compared
  with always-local, always-LoRA, and always-cloud baselines?
```

LoRA is the Plan A hypothesis. The router is the deployment architecture and the LoRA-agnostic fallback.


## 2. Claim discipline

Four kinds of success. They are independent.

```text
Product success:
  The RP5 demo runs with at least one deployable ASR path, accepts
  browser input through the runtime contract, returns a transcript
  or a low-confidence warning, and links to the technical evidence.

Evidence success:
  The datamove1 branch produces canonical eval tables, manifests,
  checksums, leakage checks, reports, handoff artifacts, and
  reproducible commands for every backend that was actually evaluated.

Positive LoRA claim:
  Allowed only if the LoRA full gate reaches PASS_GLOBAL or PASS_SUBSET
  and the report contains the required paired confidence intervals.

Positive system claim:
  Allowed only if the router or deterministic selector passes the
  locked system gate against the declared baselines. Shipping a
  fallback path is not enough to claim system improvement.
```

Minimum shippable product path:

```text
The project is allowed to ship with Whisper base plus ask_repeat and a
deterministic selector if LoRA, AssemblyAI, or the ML router fail their
gates. In that case the final narrative must say that the product path
works, while positive_lora, cloud_tradeoff, ood_real, or positive_system
claims are disabled whenever their gates did not pass.
```

Decision rules:

```text
1. If product path works but LoRA fails: report product success and
   negative LoRA evidence.
2. If product path works but router/system metrics do not improve:
   report product success and negative or neutral system evidence.
3. If AssemblyAI is unavailable: remove cloud trade-off claims.
4. If Common Voice or any approved public OOD-real fallback is
   unavailable: remove OOD-real claims.
5. Never imply that a claim is positive because a fallback shipped.
6. The demo must remain shippable even if every experimental claim fails.
7. The demo not shipping does not mean a positive claim was impossible.
   Product success and positive claims are independent.
```


## 3. Outcome resolution table

This table is the single source of truth for crossed states. The agent plan re-encodes it as machine predicates; this file gives the narrative.

Notation:

```text
LoRA state:
  GLOBAL      = full LoRA PASS_GLOBAL and CT2 INT8 preservation PASS
  SUBSET      = full LoRA PASS_SUBSET and CT2 INT8 preservation PASS
  FAIL        = full LoRA FAIL_WITH_EVIDENCE or preservation FAIL/EXPORT_BLOCKED
  SMOKE_FAIL  = Decision A smoke FAIL and P4 skipped
  HALTED      = LoRA work halted with an active BLOCKED_* marker

OOD state:
  OK          = Common Voice or approved public OOD fallback prepared
  BLOCKED     = BLOCKED_OOD_PUBLIC active and claims_enabled.ood_real = false

API state:
  OK          = AssemblyAI cache exists and BLOCKED_API not active
  BLOCKED     = BLOCKED_API active and claims_enabled.cloud_tradeoff = false
```

| LoRA × OOD × API | Outcome | Demo scope | Handoff contents |
|---|---|---|---|
| GLOBAL × OK × OK | A | base + LoRA + AssemblyAI + ML router | base, LoRA, AssemblyAI config, ML router, OOD report |
| GLOBAL × OK × BLOCKED | A | base + LoRA + ML router | base, LoRA, local ML router |
| GLOBAL × BLOCKED × OK | A | base + LoRA + AssemblyAI + ML router (no OOD-real claim) | base, LoRA, AssemblyAI config, ML router, ID/OOD-param report |
| GLOBAL × BLOCKED × BLOCKED | A | base + LoRA + local ML router (no OOD-real claim) | base, LoRA, local ML router, ID/OOD-param report |
| SUBSET × OK × OK | B | base + conditional LoRA + AssemblyAI + ML router | base, LoRA, AssemblyAI config, ML router, OOD report |
| SUBSET × OK × BLOCKED | B | base + conditional LoRA + local ML router | base, LoRA, local ML router |
| SUBSET × BLOCKED × OK | B | base + conditional LoRA + AssemblyAI + ML router (no OOD-real claim) | base, LoRA, AssemblyAI config, ML router, ID/OOD-param report |
| SUBSET × BLOCKED × BLOCKED | B | base + conditional LoRA + local ML router (no OOD-real claim) | base, LoRA, local ML router, ID/OOD-param report |
| FAIL × OK × OK | C | base + AssemblyAI + ML router | base, AssemblyAI config, ML router, negative LoRA report |
| FAIL × OK × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector, negative LoRA report |
| FAIL × BLOCKED × OK | C | base + AssemblyAI + ML router (no OOD-real claim) | base, AssemblyAI config, ML router, ID/OOD-param report |
| FAIL × BLOCKED × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector |
| SMOKE_FAIL × OK × OK | D | base + AssemblyAI + ML router or selector | base, AssemblyAI config, router/selector, smoke negative report |
| SMOKE_FAIL × OK × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector, smoke negative report |
| SMOKE_FAIL × BLOCKED × OK | D | base + AssemblyAI + ML router or selector (no OOD-real claim) | base, AssemblyAI config, router/selector, smoke negative report |
| SMOKE_FAIL × BLOCKED × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector, smoke negative report |
| HALTED × OK × OK | C or D after orchestrator review | base + AssemblyAI if safe to proceed | blocker report plus available artifacts |
| HALTED × OK × BLOCKED | E after orchestrator review | base + ask_repeat + deterministic selector | blocker report plus deterministic selector |
| HALTED × BLOCKED × OK | C or D after orchestrator review | base + AssemblyAI (no OOD-real claim) | blocker report plus available artifacts |
| HALTED × BLOCKED × BLOCKED | E after orchestrator review | base + ask_repeat + deterministic selector | blocker report plus deterministic selector |

Hard rules:

```text
1. If fewer than two transcript-producing deployable backends remain,
   do not train a multi-backend ML router. Package the deterministic
   selector and record OUTCOME_E_DETERMINISTIC_SELECTOR.
2. If OOD state is BLOCKED, every final report must state that
   OOD-real claims are disabled.
3. If API state is BLOCKED, every final report must state that
   cloud trade-off claims are disabled.
4. If LoRA state is HALTED, present the LoRA result as blocked or
   early-stopped, not as a scientific negative result, unless
   FAIL_WITH_EVIDENCE artifacts exist.
5. positive_system stays `pending` until P8 evaluates the chosen
   router or selector. P8 sets it to true or false.
```


## 4. Phase narrative

Each phase is sized for orchestrator approval. The agent plan has the per-task detail.

### P0. Bootstrap and skeleton

What this phase produces:

```text
Repository inventory, target branch, tracker, preserved CLAUDE.md
ROBUST_ASR_PROFILE block, deterministic repo integration policy,
reuse policy, touch policy, runtime smoke (Slurm + Apptainer + imports),
minimal RP5 runtime contract skeleton (request/response JSON +
validator), model card and router card templates with
TODO_FILLED_IN markers.
```

Why this phase exists:

```text
Every later phase depends on the same runtime, the same JSON contract
shape, and the same documentation skeleton. Doing this last is what
made v3.3.5 prone to last-minute scrambles at P10.1.
```

Approval prompt for the orchestrator:

```text
Approve P0 to advance to P1 if:
  reports/robust_asr/repository_inventory.md exists,
  reports/robust_asr/asset_inventory.md exists,
  reports/robust_asr/repo_integration_policy.md exists,
  reports/robust_asr/touch_policy.md exists,
  configs/robust_asr/reuse_policy_v1.yaml exists,
  tracker.repo_integration.legacy_trackers_classified == true,
  tracker.repo_integration.legacy_plans_classified == true,
  tracker.repo_integration.unclassified_paths_default_no_touch == true,
  CLAUDE.md contains exactly one ROBUST_ASR_PROFILE block and preserves
    repository rules outside that block,
  .gitattributes does not contain "CLAUDE.md merge=ours",
  scripts/robust_asr/validate_report_shape.py exists and emits
    OK_REPORT_SHAPE on the report fixtures,
  reports/robust_asr/runtime_smoke.md shows exit_code=0,
  artifacts/robust_asr/runtime_contract/rp5_request_fixture.json and
    rp5_response_fixture.json validate with --strict-skeleton,
  docs/reports/robust_asr/model_card_lora.md and router_card.md exist
    with their TODO_FILLED_IN_<task_id> placeholders,
  no marker in {BLOCKED_SOURCE_BRANCH, BLOCKED_RUNTIME, PLAN_CONFLICT}.
```

Approximate cost: 1 to 2 sessions, no GPU.

### P1. Schema, manifests, degradations

What this phase produces:

```text
Canonical eval schema (28 columns), shared text normalization with
pinned NORMALIZATION_VERSION, public dataset manifests for LoRA train,
router train, validation, locked test, OOD-real (Common Voice or
approved public fallback), and degradation_v1 manifests for the five
condition families.
```

Why this phase exists:

```text
Every backend writes one row per audio_id to the same schema. Every
later evaluation is a JOIN on this schema. Locking it now prevents
silent definition drift across LoRA, AssemblyAI, router, and system reports.
```

Approval prompt:

```text
Approve P1 to advance to P2 if:
  tests/robust_asr/test_eval_schema.py PASS,
  tests/robust_asr/test_normalization_metrics.py PASS,
  tests/robust_asr/test_leakage.py PASS,
  tests/robust_asr/test_degradation_v1.py PASS,
  manifest checksums recorded in tracker,
  Common Voice OOD-real or approved fallback prepared OR
    BLOCKED_OOD_PUBLIC active and claims_enabled.ood_real=false.
```

Approximate cost: 2 to 3 sessions, mostly CPU.

### P2. Whisper base baseline

What this phase produces:

```text
Whisper base CT2 INT8 transcripts and metrics for ID, OOD-param, and
(if enabled) OOD-real eval sets, written into the canonical schema.
A baseline summary report. The LoRA smoke split config.
```

Why this phase exists:

```text
The LoRA experiment is paired against this baseline. Without it,
LoRA results have no comparator and bootstrap CIs cannot be paired.
```

Approval prompt:

```text
Approve P2 to advance to P3 if:
  artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet exists
    with checksum and validate_eval_table.py emits OK_EVAL_TABLE,
  reports/robust_asr/baseline_whisper_base.md exists,
  configs/robust_asr/lora_smoke.yaml references valid manifests.
```

Approximate cost: 1 session, GPU helpful for Whisper inference but optional.

### P3. LoRA smoke and Decision A

What this phase produces:

```text
A 200-step LoRA smoke training, smoke evaluation, an end-to-end
export smoke (LoRA merge + CT2 export + faster-whisper load +
transcribe one file), and Decision A.
```

Decision A:

```text
PASS or PARTIAL  -> proceed to P4 (full LoRA)
FAIL             -> skip P4 by setting tasks P4.1, P4.2, P4.3 to
                    SKIPPED_BY_DECISION_A; proceed to P5
HALTED           -> stop with active BLOCKED_* marker
```

Why this phase exists:

```text
Full LoRA can take 24 wall-clock hours per run. Smoke detects whether
LoRA has any signal in 4 hours, before committing the larger budget.
```

Approval prompt:

```text
Approve P3 to advance to P4 or P5 if:
  reports/robust_asr/lora/lora_smoke_report.md exists,
  reports/robust_asr/lora/decision_a_smoke.md exists,
  tracker.decisions.Decision_A_smoke.outcome in {PASS, PARTIAL, FAIL},
  no active marker in {BLOCKED_RUNTIME, MISSING_EVIDENCE, PLAN_CONFLICT}.
```

Approximate cost: 1 session, 1 GPU, 4 hours wall clock max.

### P4. Full LoRA, Decision B, and CT2 INT8 preservation

What this phase produces:

```text
Full LoRA training run, paired bootstrap evaluation against Whisper
base, deterministic checkpoint selection, LoRA merge to FP16,
CTranslate2 INT8 export, and preservation evaluation.
```

Decision B:

```text
include_lora_in_router = true  if full LoRA is PASS_GLOBAL or PASS_SUBSET
                                  AND CT2 INT8 preservation is PASS
include_lora_in_router = false otherwise
```

Why this phase exists:

```text
Whether or not LoRA helps, the experiment yields publishable evidence
in either direction. The CT2 INT8 preservation gate is what makes the
LoRA artifact actually deployable on RP5; FP16 LoRA is not deployable
on RP5 in the current runtime.
```

Approval prompt:

```text
Approve P4 to advance to P5 if any of these branches is true:
  Branch A: tasks P4.1, P4.2, P4.3 PASS;
            full LoRA outcome and preservation outcome recorded;
            Decision B and claims_enabled.positive_lora set.
  Branch B: tasks P4.1, P4.2, P4.3 SKIPPED_BY_DECISION_A;
            Decision B = exclude LoRA;
            claims_enabled.positive_lora = false.
  Branch C: P4.1 PASS, P4.2 PASS, P4.3 HALTED with EXPORT_BLOCKED or
            preservation FAIL; Decision B = exclude LoRA;
            FP LoRA evidence preserved.
```

Approximate cost: 1 to 2 sessions, 1 GPU, up to 24 hours wall clock per training run.

### P5. AssemblyAI cache or API block

What this phase produces:

```text
A populated AssemblyAI transcript cache for every audio_id in
ID, OOD-param, and OOD-real eval sets, written into the canonical
schema. OR a recorded BLOCKED_API marker.
```

Why this phase exists:

```text
The router treats AssemblyAI as a third backend. The cache makes
router training deterministic and removes runtime dependency on the
cloud during evaluation. If AssemblyAI is unavailable, the cloud
trade-off claim is disabled and the demo runs in local-only mode.
```

Approval prompt:

```text
Approve P5 to advance to P6 if:
  artifacts/robust_asr/eval_tables/assemblyai.parquet exists with
    checksum and validate_eval_table.py emits OK_EVAL_TABLE,
  OR BLOCKED_API active and claims_enabled.cloud_tradeoff = false.
  If fewer than two transcript-producing deployable backends remain,
    record OUTCOME_E_DETERMINISTIC_SELECTOR.
```

Approximate cost: 1 session, no GPU. AssemblyAI quota and dollar cost.

### P6. Oracle table, router matrices, or selector evidence

What this phase produces:

```text
Branch A, ML-router path:
  A per-audio_id oracle table that records, for every available backend,
  its WER, latency, cost, and the oracle-chosen action under the
  configured cost function. Router train, validation, and locked test
  matrices with acoustic features and Whisper base decode features.

Branch B, deterministic-selector path:
  A selector_evidence.parquet table for the minimum shippable path when
  fewer than two transcript-producing deployable backends remain or
  OUTCOME_E_DETERMINISTIC_SELECTOR is already active.
```

Why this phase exists:

```text
The ML router needs supervision per row. The oracle table provides it.
The deterministic selector does not need ML training matrices. Building
those matrices after Outcome E would create artificial work and would
invite the agent to train a router that should already be skipped.
```

Approval prompt:

```text
Approve P6 to advance to P7 if one branch is true:

Branch A:
  artifacts/robust_asr/oracle/oracle_table.parquet exists with checksum
    and validate_oracle_table.py emits OK_ORACLE_TABLE,
  artifacts/robust_asr/router/router_train.parquet, router_val.parquet,
    router_test_locked.parquet exist with checksums and
    validate_router_matrices.py emits OK_ROUTER_MATRICES,
  tests/robust_asr/test_leakage.py PASS after router matrix construction,
  next task is P7.1.

Branch B:
  OUTCOME_E_DETERMINISTIC_SELECTOR is active,
  artifacts/robust_asr/router/selector_evidence.parquet exists with
    checksum and validate_selector_evidence.py emits OK_SELECTOR_EVIDENCE,
  P6.2 is SKIPPED_BY_OUTCOME_E,
  next task is P7.3.
```

Approximate cost: 1 session, CPU only.

### P7. Router or deterministic selector

What this phase produces:

```text
If at least two transcript-producing deployable backends remain:
  Trained GBDT router candidates (LightGBM, XGBoost, or sklearn
  HistGradientBoostingRegressor), candidate selection, locked
  evaluation, and a packaged router.
Else:
  A deterministic selector packaged from Section 22A of the agent plan.
```

Decision C:

```text
Choose ML router if:
  >= 2 transcript-producing deployable backends are available
  AND OUTCOME_E_DETERMINISTIC_SELECTOR is not active
  AND at least one trained candidate beats always-Whisper-base on
  router validation by mean_regret with the configured tolerance.
Choose deterministic selector otherwise.

If OUTCOME_E_DETERMINISTIC_SELECTOR is active before P7.1, P7.1 and
P7.2 are not planning targets. The next valid task is P7.3.
```

Approval prompt:

```text
Approve P7 to advance to P8 if any of these branches is true:
  Branch A: ML router selected, packaged, and tests/robust_asr/
    test_router_runtime.py PASS.
  Branch B: deterministic selector selected, packaged, and
    tests/robust_asr/test_router_runtime.py PASS.
```

Approximate cost: 1 session, CPU only.

### P8. System evaluation and demo examples

What this phase produces:

```text
A locked system-level evaluation comparing the chosen router or
selector against always-base, always-LoRA (if applicable),
always-cloud (if applicable), and always-deterministic baselines.
A demo examples manifest with 8 public examples disjoint from
locked eval sets.
```

Decision D (positive_system):

```text
true  if mean_regret(router_or_selector) < mean_regret(every declared
       baseline), AND paired test p < 0.05 against at least one
       deployed baseline, AND no claim depends on a disabled
       claims_enabled flag.
false otherwise.
```

Approval prompt:

```text
Approve P8 to advance to P9 if:
  reports/robust_asr/system/system_eval.md exists with paired test
    results,
  tracker.claims_enabled.positive_system in {true, false},
  artifacts/robust_asr/demo/demo_examples_manifest.json exists with
    disjointness proof,
  tests/robust_asr/test_leakage.py PASS after demo example selection.
```

Approximate cost: 1 session, CPU only.

### P9. Final runtime contract, handoff, RP5 spec

What this phase produces:

```text
The final RP5 runtime contract (request/response schemas, finalized
from the P0.4 skeleton plus what backends and selectors actually exist).
A handoff package under artifacts/robust_asr/handoff/ with model
checksums, a smoke script, a rollback script, an RP5 runtime spec,
and an 8-section README.
A handoff/<date>-<short_sha> tag pushed to origin.
```

Why this phase exists:

```text
The RP5 branch is built independently and consumes this package.
The package is the contract.
```

Approval prompt:

```text
Approve P9 to advance to P10 if:
  artifacts/robust_asr/runtime_contract/final_request_schema.json
    and final_response_schema.json exist,
  artifacts/robust_asr/handoff/README.md exists with the 8-section
    template in order, verified by verify_handoff_package.py --strict,
  handoff/<date>-<short_sha> tag exists locally and on origin.
```

Approximate cost: 1 session, no GPU.

### P10. Final reports and audit

What this phase produces:

```text
Final LoRA report, final router/selector report, final system report,
final model card and router card, final asset audit (every checksum
recomputed, no residual TODO_FILLED_IN tokens for closed tasks),
and the plan-tracker consistency report.
```

Approval prompt:

```text
Approve P10 if:
  reports/robust_asr/final_verification.md exists,
  reports/robust_asr/final_asset_audit.md exists,
  reports/robust_asr/plan_tracker_consistency.md result: PASS,
  all leakage and schema tests pass,
  no secrets in repo,
  working tree clean and pushed,
  tracker.project_status = COMPLETE.
```

Approximate cost: 1 session, no GPU.


## 5. Approval protocol

The approval protocol has two levels: per-task approval and phase-gate approval. Both use chat as the transport and the tracker as the durable record.

Orchestrator review checklist for Planning Reports:

```text
Before returning APPROVE_PLAN:
1. Confirm task_id equals TRACKER-DERIVED NEXT TASK.
2. Confirm requested_task_matches_tracker == true.
3. Confirm Preconditions are explicit and satisfied.
4. Confirm in_scope and out_of_scope are narrow enough for one task.
5. Confirm expected_paths do not touch unrelated runtime, tracker,
   report, or large-artifact paths.
6. For every expected_path outside robust_asr-owned paths, confirm the
   Planning Report cites an exact reuse_policy_v1.yaml row and that the
   row permits the task and operation.
7. Confirm expected_no_touch_paths include legacy trackers, legacy plans,
   secrets, datasets, checkpoints, and caches unless the task explicitly
   names a permitted exception.
8. Confirm every command has an expected sentinel, artifact, or exit
   code.
9. Confirm Verification can fail deterministically.
10. Confirm STOP CONDITION prevents Claude from starting the next task.
11. Confirm RISKS_OR_BLOCKERS contain deterministic handling only.
12. If any item fails, return REVISE_PLAN or STOP_SCOPE_CONFLICT.
```

Orchestrator review checklist for Execution Reports:

```text
Before returning CLOSE_TASK:
1. Confirm task_id matches the approved task.
2. Confirm changed_paths match the approved scope and the approved
   reuse_policy_v1.yaml rows.
3. Confirm forbidden legacy paths and no-touch paths were not modified.
4. Confirm exact commands and exit codes are present.
5. Confirm required stdout sentinels are present.
6. Confirm required artifacts exist and have checksums when applicable.
7. Confirm tracker update matches the task result and next task.
8. Confirm state capsule was updated.
9. Confirm commit_hash exists and pushed_to_origin == true.
10. Confirm working_tree_status_after is clean.
11. If a phase gate was reached, return a phase-level decision instead
    of closing only the task.
12. If evidence is missing but likely obtainable with read-only commands,
    request SUPPLEMENTAL_EVIDENCE.
13. If any closure condition fails, return FIX_BEFORE_CLOSE.
```

Orchestrator review checklist for Phase Gate Reports:

```text
Before returning PHASE_APPROVE:
1. Confirm the phase predicate matches the active branch.
2. Confirm disabled claims are explicitly disabled in claims_enabled.
3. Confirm blockers are either cleared or intentionally carried forward.
4. Confirm the next phase's first task matches the agent plan Section 0.1.
5. If OUTCOME_E_DETERMINISTIC_SELECTOR is active before P7, confirm the
   next task is P7.3, not P7.1.
```


Default per-task loop:

```text
1. ChatGPT writes a prompt asking Claude Code to plan the next task.
2. Claude Code reads the live tracker and returns a Planning Report.
3. ChatGPT returns APPROVE_PLAN, REVISE_PLAN, or STOP_SCOPE_CONFLICT.
4. Claude Code records the accepted Approval Packet in the tracker.
5. Claude Code executes only the approved task.
6. Claude Code returns an Execution Report with evidence.
7. ChatGPT returns CLOSE_TASK, FIX_BEFORE_CLOSE, PHASE_APPROVE,
   PHASE_REJECT, or CHANGE_SCOPE.
8. Claude Code records the closure decision in the tracker before
   opening or executing any next task.
```

Planning Report required shape:

```text
Source of truth: docs/plans/state_packet_schemas_v1.yaml > planning_report

Section order (binding):
  STATE SNAPSHOT
  TRACKER-DERIVED NEXT TASK
  TASK SCOPE
  PRECONDITIONS
  PLANNED FILE CHANGES
  LEGACY_REUSE_AND_TOUCH_POLICY
  COMMANDS TO RUN
  VERIFICATION BLOCK
  EXPECTED TRACKER UPDATE
  STOP CONDITION
  RISKS_OR_BLOCKERS

Field names, field order, required/optional flags, and notes for each
section live in the schemas file. If the agent's report omits a required
field or reorders a section, return REVISE_PLAN with the specific section
name. If the schemas file and this plan disagree, the agent must have
recorded PLAN_CONFLICT before producing the report.
```

Execution Report required shape:

```text
Source of truth: docs/plans/state_packet_schemas_v1.yaml > execution_report

Section order (binding):
  STATE BEFORE
  TASK EXECUTED
  FILES CHANGED
  REUSE_AND_SCOPE RESULTS
  COMMANDS RUN
  VERIFICATION RESULTS
  ARTIFACTS CREATED
  TRACKER UPDATE
  COMMIT AND PUSH
  STATE AFTER
  GATE STATUS

Field names, field order, and required/optional flags for each section
live in the schemas file. If the report omits a required field, return
FIX_BEFORE_CLOSE naming the section. If forbidden_legacy_paths_touched
is non-empty, return FIX_BEFORE_CLOSE regardless of any other field.
```

Approval Packet required shape:

```text
Source of truth: docs/plans/state_packet_schemas_v1.yaml > approval_packet

The packet is a single YAML mapping with exactly one top-level key,
ORCHESTRATOR_DECISION. The fields below must appear inside that mapping:
  scope                  (task | phase | scope_change)
  task_id                (string or null)
  phase                  (string or null)
  decision               (APPROVE_PLAN | REVISE_PLAN | STOP_SCOPE_CONFLICT |
                          CLOSE_TASK | FIX_BEFORE_CLOSE | PHASE_APPROVE |
                          PHASE_REJECT | CHANGE_SCOPE)
  accepted_report_commit (string or null)
  next_expected_task     (string or null)
  required_fix           (string or null; non-null only when decision in
                          {FIX_BEFORE_CLOSE, REVISE_PLAN})
  rationale              (one sentence)

Required and optional flags per field live in the schemas file.
```

Task closure rule:

```text
A task is not closed for orchestration purposes until ChatGPT returns
CLOSE_TASK or a phase-level decision that explicitly accepts the task's
Execution Report. Claude Code must still update the live tracker with the
task result before commit. The orchestration closure decision is recorded
as state_transport.latest_approval_packet in the tracker.
```

Phase-gate protocol:

```text
After every phase gate the agent stops. The agent writes one of:

phase_summary.<P_n>: PASS, outcome=<short_outcome>, commit=<hash>
phase_summary.<P_n>: FAIL, failed_task=<task_id>, blocker=<marker_or_reason>

into `docs/progress/robust_asr_progress.yaml`, updates
`docs/progress/robust_asr_state_capsule.md`, commits, pushes, and returns
a Phase Gate Report in chat.

The orchestrator then decides one of: PHASE_APPROVE / PHASE_REJECT /
CHANGE_SCOPE.

PHASE_APPROVE  -> Claude records orchestrator_approvals.<P_n>: APPROVED
                  plus the Approval Packet, then advances to the next
                  phase's first tracker-valid task.
PHASE_REJECT   -> Claude records orchestrator_approvals.<P_n>: RE_EXECUTE
                  plus the reason, then plans only the required fix.
CHANGE_SCOPE   -> Claude records orchestrator_approvals.<P_n>: CHANGE_SCOPE
                  and edits this plan and the agent plan in the same
                  commit. Claude re-reads both before continuing.
```

Fast iteration override:

```text
For tight inner loops, the user may set one of these flags in the live
tracker session_log:

continue_without_per_task_plan_approval: true
continue_without_per_task_closure_approval: true
continue_through_gates: true

These flags are not default. Claude Code records the override in the
session log and still returns evidence reports. Any failed predicate,
PLAN_CONFLICT, or BLOCKED_* marker stops execution regardless of override.
```

Supplemental Evidence Report:

```text
If ChatGPT cannot decide from Claude's report, it requests a Supplemental
Evidence Report. Claude Code may then run read-only inspection commands
only. It must not modify files, update the tracker, commit, push, or
start a new task while producing supplemental evidence.
```


## 6. Strategic decision points

Four decisions are owned by the orchestrator and recorded in the tracker. The agent applies them mechanically once recorded.

```text
Decision A (after P3):
  Continue to full LoRA, or skip and go to P5?
  Source of truth: tracker.decisions.Decision_A_smoke.outcome
  Set by:          P3.2 in the agent plan
  Owned by:        agent (deterministic from smoke result),
                   orchestrator override allowed and must be logged.

Decision B (after P4):
  Include LoRA in the router?
  Source of truth: tracker.decisions.Decision_B_lora_full.include_lora_in_router
  Set by:          P4.2 (full eval) and P4.3 (preservation) jointly
  Owned by:        agent (deterministic from gates),
                   orchestrator may force exclude=true to ship faster.

Decision C (after P6 or P7.1):
  ML router or deterministic selector?
  Source of truth: tracker.decisions.Decision_C_router_choice.kind
  Set by:          P6 if fewer than two deployable backends remain;
                   otherwise P7.1 candidate evaluation
  Owned by:        agent (deterministic from candidate metrics + backend
                   count), orchestrator may force selector if confidence
                   in ML router is low.

Decision D (after P8):
  Is the positive system claim allowed?
  Source of truth: tracker.claims_enabled.positive_system
  Set by:          P8.1 paired test
  Owned by:        agent (deterministic from p-value and regret deltas),
                   orchestrator does not override; if the orchestrator
                   disagrees, change baselines or evaluation in
                   docs/plans/, not the claim flag.
```


## 7. Marker reference

The agent plan has machine predicates for each marker. The orchestrator reads this table to interpret tracker state.

| Marker | Owner phase | Effect on phase advance | Effect on claims |
|---|---|---|---|
| `BLOCKED_SOURCE_BRANCH` | P0.0 pre-bootstrap report or P0.1 bootstrap recovery | Halts P0 | Re-run P0.0 after source branch is reachable |
| `BLOCKED_BRANCH_LINEAGE` | P0.1 | Halts P0 | None until cleared |
| `PLAN_CONFLICT` | Any | Halts current phase | None until cleared |
| `BLOCKED_RUNTIME` | P0.3 | Halts at P0 to P1 boundary | None until cleared |
| `ENV_CONSTRAINT` | Any | None unless metric-affecting | Logged, may narrow claim scope |
| `BLOCKED_API` | P5.1 | Allows P6 only as local-only | Disables `cloud_tradeoff` |
| `BLOCKED_OOD_PUBLIC` | P1.3 | None on phase advance | Disables `ood_real` |
| `BLOCKED_RP5` | P9.x | None on datamove1 advance | Adds `PENDING_RP5_INTEGRATION` |
| `EXPORT_BLOCKED` | P4.3 | Allows P5 with LoRA excluded | LoRA ineligible for router |
| `FAIL_WITH_EVIDENCE` | P4.2 | Allows phase advance | LoRA negative experiment is publishable |
| `PASS_GLOBAL` | P4.2 | None on advance | Enables `positive_lora` if preservation also PASS |
| `PASS_SUBSET` | P4.2 | None on advance | Enables `positive_lora` if preservation also PASS |
| `PENDING_PRICING_VERIFICATION` | P5.1 / P10.1 | None | Limits cost claim language |
| `MISSING_EVIDENCE` | Any | Halts current phase | None until cleared |
| `ROUTER_IMPL_FALLBACK_SKLEARN` | P7.1 | None | Documented in router card |
| `DEGENERATE_ROUTER_RECOVERED` | P7.1 | None if recovered | Documented |
| `OUTCOME_E_DETERMINISTIC_SELECTOR` | P5 / P6 / P7 | Reroutes P6 to selector evidence and P7 to P7.3 | Narrows positive_system scope |
| `BUDGET_EXCEEDED` | P3.1 / P4.1 / P5.1 | Triggers fallback per Section 23 | May force HALTED |
| `PENDING_RP5_INTEGRATION` | P0 / P9 / P10 | None on datamove1 done | Portfolio not shipped until cleared |


## 8. Cross-branch dependency

Datamove1 owns dataset preparation, training, evaluation, router training, runtime contract, packaging, and the handoff package. RP5 owns the public web demo. The only active datamove1 branch for this work is feature/robust-asr-lora-router-datamove1-v1, created from feature/training-datamove1-v1.

Handoff loop:

```text
1. Datamove1 produces artifacts/robust_asr/handoff/ at P9.1 and tags
   handoff/<date>-<short_sha>.
2. The RP5 branch consumes the package by tag (not by floating HEAD).
3. The RP5 branch runs the smoke script and writes
   reports/robust_asr/handoff_validation_<tag>.md on its side.
4. Datamove1 records the handoff tag, validation report path, and
   public demo URL in the tracker.
5. Until step 4 completes, marker PENDING_RP5_INTEGRATION is active.
   Cleared when step 4 lands.
```

If RP5 is not available during datamove1 execution:

```text
Continue datamove1 work to P10. Mark PENDING_RP5_INTEGRATION as
active. Do not fabricate RP5 latency. The portfolio is shipped after
the RP5 acknowledgment lands.
```


## 9. Final portfolio readiness

Datamove1-side completion (40 items) is in the agent plan, Section 10. Cross-branch portfolio readiness adds 3 items:

```text
41. RP5 branch produced a handoff_validation_<tag>.md with PASS for
    at least one demo example.
42. Public demo URL is reachable.
43. Datamove1 tracker records handoff_tag, validation report path,
    and demo URL.
```


## 10. Final expected narrative

```text
Outcome A (Preferred):
  LoRA improves the local ASR baseline under relevant degradations,
  exports to CT2 INT8, and is integrated as a deployable local
  backend. The router uses it selectively when it improves the
  cost-quality-locality trade-off.

Outcome B (Acceptable strong):
  LoRA improves only specific degradation families. The router learns
  when to use LoRA, when to keep Whisper base, and when to escalate
  to AssemblyAI.

Outcome C (Acceptable fallback):
  LoRA does not justify deployment. The evidence is preserved as a
  rigorous negative adaptation experiment, and the final router-driven
  system excludes LoRA. A positive system claim is allowed only if
  the router improves the declared trade-off on locked evaluation.

Outcome D (Minimal viable):
  LoRA fails early or is not deployable. The demo remains functional
  with Whisper base, AssemblyAI when claims_enabled.cloud_tradeoff
  is true, and low-confidence handling. The report presents product
  success and honest limits.

Outcome E (Deterministic selector):
  The ML router is not deployable or not useful. The product ships
  with a deterministic selector. The report states whether the
  selector produced positive, neutral, or negative system results
  under locked evaluation.
```

All five are valid if evidence, reports, claim boundaries, runtime contract fixtures, and the RP5 handoff package are complete.


## 11. Pointers

```text
Agent plan:           docs/plans/robust_asr_agent_plan_v3_4_7.md
Tracker:              docs/progress/robust_asr_progress.yaml
Tracker prose:        docs/progress/robust_asr_progress.md
State capsule:        docs/progress/robust_asr_state_capsule.md
Report shapes:        docs/plans/state_packet_schemas_v1.yaml
Interaction protocol: embedded in this plan Section 5 and in the agent plan Section 0.
Profile:              docs/profiles/CLAUDE.robust_asr.md
Repo root:            /mnt/fast/nobackup/users/gb0048/asr_enhancement
Source branch:        feature/training-datamove1-v1
Target branch:        feature/robust-asr-lora-router-datamove1-v1
RP5 branch:           feature/demo-runtime-rp5-v1 (consumed by tag, not by HEAD)
```


## 12. Changelog

### v3.4.7 (this revision)

This revision aligns the orchestrator plan with the v3.4.7 agent and
schema fixes: explicit ORCHESTRATOR_DECISION schema wrapping,
branch-appropriate final verification for Outcome E, corrected
pre-bootstrap source-branch failure handling, and updated plan references.

### v3.4.6

This revision closes four cross-file consistency issues identified in
the v3.4.5 review. The four fixes apply to the agent plan and to the
schemas YAML; in this orchestrator file the only change is to extend
the "Required P0 integration artifacts" list in Section 0.1.

```text
1. Adds prebootstrap_inventory_report schema to
   docs/plans/state_packet_schemas_v1.yaml.
2. Agent plan: tracker.artifacts.repository_inventory.produced_by_task
   corrected from P0.0 to P0.1.
3. Agent plan: tracker.artifacts gains validate_report_shape_script
   and report_shape_fixtures entries.
4. Agent plan: Section 2 rule 5 rewritten so P0.0 stays read-only on
   missing source reference and never writes bootstrap_block.md.
5. This file: "Required P0 integration artifacts" extended with
   scripts/robust_asr/validate_report_shape.py and the fixtures
   directory, matching the P0 gate predicate.
```

### v3.4.5

This revision closes three operational drift risks identified in the
v3.4.3 review:

```text
1. Moves the literal shape of every report (State Packet, Planning
   Report, Execution Report, Phase Gate Report, Approval Packet,
   Supplemental Evidence Report) into a shared YAML at
   docs/plans/state_packet_schemas_v1.yaml. Both this plan Section 5
   and the agent plan Section 0 reference that file instead of
   duplicating the field lists, eliminating the v3.4.3 risk that the
   two plans drift on field names, field order, or required flags.
2. Adds rule 9 in Section 0.1: P0.0 verifies origin/feature/demo-runtime-rp5-v1
   exists. A missing reference is inventory only and does not block P0,
   but PENDING_RP5_INTEGRATION becomes expected from P0 instead of
   surfacing only at P9.
3. Adds rule 10 in Section 0.1: legacy state paths (existing trackers
   and plans) must be classified in reuse_policy_v1.yaml with
   permitted_use: read_only, not forbidden, so P10.3 plan_tracker_
   consistency can read them.
```

### v3.4.3

This revision closes the remaining repository-integration ambiguity:

```text
1. Adds Section 0.1 with branch roles, repo-root authority, legacy state
   rules, reuse policy requirements, and no-touch defaults.
2. Requires P0 to produce asset_inventory.md,
   repo_integration_policy.md, touch_policy.md, and reuse_policy_v1.yaml.
3. Requires CLAUDE.md preservation through a delimited
   ROBUST_ASR_PROFILE block instead of whole-file replacement.
4. Updates Planning and Execution Report shapes so ChatGPT can reject
   unapproved reuse or unrelated path edits.
```

### v3.4.2

This revision keeps the two-file split but adds the missing operational
discipline for ChatGPT web review and the minimum shippable route:

```text
1. Adds explicit Planning, Execution, and Phase Gate review checklists.
2. Makes product success independent from positive LoRA, cloud, OOD, or
   system claims.
3. Splits P6 into an ML-router branch and deterministic-selector evidence
   branch.
4. States that Outcome E routes directly to P7.3 and must not plan P7.1.
5. Adds BLOCKED_BRANCH_LINEAGE to the marker table.
```

### v3.4.1

This revision keeps the two-file split, but corrects the operational model for ChatGPT web. ChatGPT does not read or write the live tracker directly. Claude Code exports state through mandatory State Packets, Planning Reports, Execution Reports, and Phase Gate Reports; ChatGPT returns Approval Packets; Claude records those packets in the live tracker before advancing.

### v3.4.0

The plan was split into two files. This file is the orchestrator-facing strategy. The agent-facing execution lives in the matching agent plan. The split addresses the v3.3.6 problem of a single 4700-line document trying to serve two consumers with incompatible needs.

The v3.4.0 corrections relative to v3.3.6:

```text
1. Split into orchestrator and agent files; both used a shared tracker model. v3.4.1 refines this so Claude has live tracker access and ChatGPT receives tracker-derived state packets.
2. Section 1B + 1C + 17 + 18 of v3.3.6 collapsed into a single
   outcome resolution table here, and a single phase-gate predicate
   table in the agent plan, with one-way pointers between them.
3. Every "if available" / "if compute access allows" / "if a longer-
   running queue" replaced by a deterministic predicate or a marker.
   See agent plan Section 5 (Constants and thresholds) and Section 6
   (Marker definitions).
4. Section 5A of v3.3.6 (8 validator script contracts) extended in
   the agent plan Section 4 to all ~30 scripts referenced. Every
   script has Inputs, Outputs, Asserts, Stdout, Exit code.
5. Strategic decisions A, B, C, D explicitly named here with their
   tracker source of truth and ownership boundary.
6. Approval protocol formalized: phase_summary + orchestrator_approvals
   blocks in the tracker; continue_through_gates override.
```

### Lineage

```text
v3.4.3    Add Section 0.1 repository integration authority, P0 reuse
          policy / asset inventory / touch policy artifacts, CLAUDE.md
          ROBUST_ASR_PROFILE block preservation rule.
v3.4.2    Add orchestrator review checklists, minimum shippable route,
          and explicit selector-evidence path.
v3.4.1    Add ChatGPT-Claude state packet protocol and approval packet recording.
           Clarify that the uploaded zip is structural context only.

v3.4.0    Split into orchestrator + agent. Determinism, contracts, single
          decision tree.
v3.3.6    Execution-hardening pass on v3.3.5 (added P0.0, P0.5, Section
          5A, 19 contract assertions, P4-C branch, in_progress status,
          phase-gate stop-and-report, plan-tracker consistency check).
v3.3.5    Execution-form pass on v3.3.4.
v3.3.x    Earlier strategy iterations on the LoRA + router design.
v0        training_datamove1_plan.md (enhancement-based, MetricGAN+
          fallback). Preserved for reference; superseded by the LoRA
          + router family.
```
