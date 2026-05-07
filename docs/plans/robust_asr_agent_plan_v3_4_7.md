# Robust ASR Agent Plan v3.4.7

This file is the execution spine. It is read by the coding agent in VS Code on `datamove1.surrey.ac.uk`. Strategy, narrative, and approval gates live in `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md`. The live tracker is `docs/progress/robust_asr_progress.yaml`. Claude Code reads and updates it. ChatGPT web receives tracker-derived state only through required reports and sends decisions back as Approval Packets.

The literal shape of every report exchanged in chat (State Packet, Planning Report, Execution Report, Phase Gate Report, Approval Packet, Supplemental Evidence Report) is defined in `docs/plans/state_packet_schemas_v1.yaml`. This file and the orchestrator plan both reference that file. If this plan and the schemas file disagree on field names, field order, section names, or required values, the agent records `PLAN_CONFLICT` and stops.

The agent does not write claim narratives. The agent runs commands, writes artifacts, updates the tracker, and stops at gates.


## 0. Session-open ritual and interaction modes

Run this at the start of every Claude Code session, even short ones. Do not plan or execute a task before completing the ritual.

```text
1. Read docs/progress/robust_asr_progress.yaml. Identify
   current_phase, current_task, last_completed_task, active markers,
   session_log overrides, and latest approval packet.
2. Read docs/progress/robust_asr_state_capsule.md if it exists.
3. Read docs/progress/robust_asr_progress.md for narrative state.
4. Read this file from Section 0 through Section 7. Then re-read the
   section that owns the current task and Section 9 entry for the task.
5. Identify the first pending task whose Preconditions are satisfied.
   If a prerequisite is incomplete, the prerequisite is the next task.
6. Compare the user-requested task, if any, with the tracker-derived
   next task.
7. If the requested task differs from tracker.current_task or from the
   first pending task with satisfied Preconditions, do not plan
   execution. Return TRACKER_MISMATCH with the tracker-derived task.
8. Select exactly one mode: BOOTSTRAP_NO_TRACKER, PLANNING, EXECUTION,
   CLOSURE_FIX, PHASE_APPROVAL_RECORDING, or SUPPLEMENTAL_EVIDENCE.
```

Pre-tracker exception:

```text
If docs/progress/robust_asr_progress.yaml is missing, the only legal
mode is BOOTSTRAP_NO_TRACKER and the only legal task is P0.0. In this
mode, steps 1 through 3 of the session-open ritual are replaced by a
read-only check that the repository root exists and that this plan plus
the orchestrator plan are readable. Any request other than P0.0 returns
TRACKER_MISSING_BOOTSTRAP_REQUIRED and stops.
```

Mode selection:

```text
BOOTSTRAP_NO_TRACKER:
  Use only when docs/progress/robust_asr_progress.yaml does not exist
  and the requested work is P0.0. Run only the P0.0 read-only
  pre-bootstrap inventory. Do not edit files inside the repository, do
  not create the target branch, do not create the tracker, do not
  commit, and do not push. Return a Pre-bootstrap Inventory Report and
  stop. P0.1 materializes the official repository_inventory.md and
  records P0.0 PASS in the newly created tracker.

PLANNING:
  Use when ChatGPT asks for a plan for the next task. Produce a
  Planning Report and stop. Do not edit files, run implementation
  commands, update the tracker, commit, or push.

EXECUTION:
  Use only when the prompt includes an Approval Packet with
  decision: APPROVE_PLAN for the tracker-derived task, or when
  session_log.continue_without_per_task_plan_approval == true.
  Execute only the approved task. Run Verification. Update tracker,
  state capsule, task report, commit, push, and return an Execution
  Report. Stop after the report.

CLOSURE_FIX:
  Use when ChatGPT returns FIX_BEFORE_CLOSE. Execute only the requested
  fix for the same task. Do not start the next task.

PHASE_APPROVAL_RECORDING:
  Use when ChatGPT returns PHASE_APPROVE, PHASE_REJECT, or CHANGE_SCOPE.
  Record the Approval Packet in the tracker, commit, push, then either
  stop or produce the next Planning Report, depending on the prompt.

SUPPLEMENTAL_EVIDENCE:
  Use when ChatGPT requests more evidence. Run read-only inspection
  commands only. Do not edit files, update tracker, commit, push, or
  start a task.
```

Default stop rules:

```text
1. In BOOTSTRAP_NO_TRACKER mode, stop after the Pre-bootstrap Inventory
   Report.
2. In PLANNING mode, stop after the Planning Report.
3. In EXECUTION mode, stop after the Execution Report.
4. In CLOSURE_FIX mode, stop after the fix report.
5. At a phase gate, stop after the Phase Gate Report unless
   session_log.continue_through_gates == true.
6. Do not start the next task merely because the tracker says it is
   available. A new task requires a new ChatGPT prompt or an explicit
   continue override in the tracker.
```

Decision rules for state authority:

```text
0. Before P0.1, there is no live robust_asr tracker. P0.0 is a
   read-only pre-bootstrap task and its result is carried into P0.1 by
   the Pre-bootstrap Inventory Report.
1. The live tracker in the repo is the source of truth.
2. ChatGPT web may have an old zip. Treat that zip as structural context
   only, not as live state.
3. Every Planning Report and Execution Report must include a
   self-contained State Snapshot.
4. If ChatGPT's requested task and the tracker-derived task disagree,
   return TRACKER_MISMATCH and stop. Do not infer that ChatGPT intended
   to skip tasks.
5. If this plan and the orchestrator plan disagree on task IDs, marker
   names, approval packet fields, report shapes, or outcome labels,
   record PLAN_CONFLICT and stop.
```

State packet minimum fields:

```text
Source of truth: docs/plans/state_packet_schemas_v1.yaml > state_packet

The state packet is reused as the content of STATE SNAPSHOT, STATE BEFORE,
and STATE AFTER sections in every report below. All listed fields are
required and must be non-null unless the schemas file marks them optional.
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

Field names, field order, and required/optional flags for each section
live in the schemas file. Missing a required field or reordering sections
is a malformed report.
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

Field names, field order, and required/optional flags live in the
schemas file. forbidden_legacy_paths_touched must be an empty list;
non-empty triggers FIX_BEFORE_CLOSE.
```

Approval Packet required shape:

```text
Source of truth: docs/plans/state_packet_schemas_v1.yaml > approval_packet

The packet must be a single ORCHESTRATOR_DECISION mapping with these
fields inside it:
  scope                  (task | phase | scope_change)
  task_id                (string or null)
  phase                  (string or null)
  decision               (APPROVE_PLAN | REVISE_PLAN | STOP_SCOPE_CONFLICT |
                          CLOSE_TASK | FIX_BEFORE_CLOSE | PHASE_APPROVE |
                          PHASE_REJECT | CHANGE_SCOPE)
  accepted_report_commit (string or null)
  next_expected_task     (string or null)
  required_fix           (string or null)
  rationale              (one sentence)

Required and optional flags per field live in the schemas file. Claude
records the received packet under tracker.state_transport.latest_approval_packet
before any further action.
```

Phase-gate stop-and-report protocol:

```text
After each P0/P1/.../P10 gate predicate evaluates to PASS:
1. Write phase_summary.<P_n>: "PASS, outcome=<short_outcome>,
   commit=<hash>" in the tracker.
2. Update docs/progress/robust_asr_state_capsule.md.
3. Commit and push tracker, reports, and small artifacts.
4. Return a Phase Gate Report with the State Snapshot, gate predicate
   evidence, commit hash, and next expected phase.
5. Stop. Wait for a ChatGPT Approval Packet unless
   session_log.continue_through_gates == true.

After each P0/P1/.../P10 gate predicate evaluates to FAIL:
1. Write phase_summary.<P_n>: "FAIL, failed_task=<task_id>,
   blocker=<marker_or_reason>".
2. Update the state capsule and task report.
3. Commit and push if safe.
4. Return a Phase Gate Report and stop. Do not retry without an
   Approval Packet.
```

Closure rule:

```text
A task can be marked PASS, PARTIAL, FAIL, HALTED, or SKIPPED in the live
tracker after Verification. However, orchestration closure is separate:
ChatGPT must return CLOSE_TASK, FIX_BEFORE_CLOSE, or a phase-level
decision after reading the Execution Report. Claude records that decision
under state_transport.latest_approval_packet before opening the next task.
```


## 0.1 Linear routing table and minimum shippable path

This section prevents branch drift across the two-plan split. The agent
must use this table after every terminal task state before selecting the
next task. If the table, Section 8, Section 9, and the tracker disagree,
record `PLAN_CONFLICT` and stop.

Minimum shippable path:

```text
P0 runtime contract skeleton PASS.
P1 schema, manifests, leakage tests, and degradation manifests PASS.
P2 Whisper base baseline PASS.
P3 LoRA smoke produces Decision A.
If Decision A is FAIL or HALTED with usable evidence:
  skip or halt P4 exactly as Section 5.10 defines.
P5 AssemblyAI is optional. BLOCKED_API disables cloud_tradeoff.
If fewer than two transcript-producing deployable backends remain:
  activate OUTCOME_E_DETERMINISTIC_SELECTOR.
  build selector evidence in P6.
  skip P7.1 and P7.2.
  package deterministic selector in P7.3.
P8 evaluates the shipped router or selector and may set
  positive_system = true or false.
P9 produces the handoff package.
P10 runs final verification and audit.
```

Transition table:

```text
Terminal state or marker                                      Next tracker-valid task

P0.0 PASS                                                     P0.1
P0.1 PASS                                                     P0.2
P0.2 PASS                                                     P0.3
P0.3 PASS                                                     P0.4
P0.4 PASS                                                     P0.5
P0 gate PASS + PHASE_APPROVE                                  P1.1

P1.1 PASS                                                     P1.2
P1.2 PASS                                                     P1.3
P1.3 PASS or BLOCKED_OOD_PUBLIC handled                       P1.4
P1.4 PASS                                                     P2.1 after P1 gate approval

P2.1 PASS                                                     P2.2
P2.2 PASS                                                     P3.1 after P2 gate approval

P3.1 PASS or FAIL with evidence                               P3.2
P3.1 HALTED                                                   stop, approval required
P3.2 Decision A PASS                                          P4.1 after P3 gate approval
P3.2 Decision A PARTIAL                                       P4.1 after P3 gate approval
P3.2 Decision A FAIL                                          P5.1 after P3 gate approval,
                                                              with P4.1, P4.2, P4.3 =
                                                              SKIPPED_BY_DECISION_A
P3.2 Decision A HALTED                                        stop, approval required

P4.1 PASS                                                     P4.2
P4.1 HALTED with BUDGET_EXCEEDED and usable checkpoint         P4.2 for usable checkpoint only
P4.1 HALTED without usable checkpoint                          P5.1 after approval,
                                                              include_lora_in_router=false
P4.2 PASS_GLOBAL or PASS_SUBSET                               P4.3
P4.2 FAIL_WITH_EVIDENCE                                       P5.1 after P4 gate approval,
                                                              include_lora_in_router=false
P4.3 PASS preservation                                        P5.1 after P4 gate approval
P4.3 FAIL or EXPORT_BLOCKED                                   P5.1 after P4 gate approval,
                                                              include_lora_in_router=false

P5.1 PASS with >= 2 deployable backends                        P6.1 oracle path
P5.1 PASS or HALTED with BLOCKED_API and >= 2 deployable backends
                                                              P6.1 oracle path
P5.1 PASS or HALTED with BLOCKED_API and < 2 deployable backends
                                                              P6.1 selector evidence path,
                                                              OUTCOME_E_DETERMINISTIC_SELECTOR active

P6.1 oracle path PASS                                         P6.2 router matrix path
P6.1 selector evidence path PASS                              P6.2 SKIPPED_BY_OUTCOME_E
P6.2 router matrix path PASS                                  P7.1 after P6 gate approval
P6.2 SKIPPED_BY_OUTCOME_E                                     P7.3 after P6 gate approval

P7.1 OK_ROUTER_SELECT                                         P7.2
P7.1 ALL_CANDIDATES_DEGENERATE or NO_CANDIDATE_BEATS_BASELINE P7.3 selector path,
                                                              OUTCOME_E_DETERMINISTIC_SELECTOR active
P7.2 PASS                                                     P7.3 ML router path
P7.3 PASS                                                     P8.1 after P7 gate approval

P8.1 PASS                                                     P8.2
P8.2 PASS                                                     P9.0 after P8 gate approval
P9.0 PASS                                                     P9.1
P9.1 PASS                                                     P9.2
P9.2 PASS                                                     P10.1 after P9 gate approval
P10.1 PASS                                                    P10.2
P10.2 PASS                                                    P10.3
P10.3 PASS                                                    project_status = COMPLETE
```

Hard transition rules:

```text
1. Do not infer the next task from narrative prose.
2. Do not open a task whose Preconditions are false.
3. Do not skip a task unless the status value is one of the explicit
   skip statuses in Section 7.
4. Do not train an ML router when OUTCOME_E_DETERMINISTIC_SELECTOR is
   active before P7.1.
5. If a route reaches a task that cannot produce meaningful evidence
   for the active branch, set the task to the explicit skip status and
   record the route in the tracker.
```

## 1. Hard constraints

```text
1. Public datasets only for training and evaluation.
2. Browser microphone audio is demo-only runtime input. Never used
   for training or evaluation claims.
3. Local files uploaded by recruiters are demo-only runtime input.
   Never used for training or evaluation claims.
4. Evaluation claims must come from locked public evaluation sets.
5. Demo examples and evaluation sets must be separate.
6. LoRA must be evaluated independently before the router claim is
   reported.
7. All backend outputs must be persisted in the canonical schema
   (Section 3).
8. Router training must not leak LoRA fine-tuning examples into router
   train, validation, or locked test targets.
9. AssemblyAI must never be used as ground truth for any set where
   AssemblyAI is also evaluated as a backend.
10. The remote demo is served from the RP5. The recruiter interacts
    through a browser, not by speaking directly to the RP5.
11. No task may be marked complete only because expected files exist.
    Verification commands must run and pass.
12. No checkpoint may be selected manually. Use the deterministic
    selection rules in Section 5.
13. No temporary tolerance markers may be introduced to force a pass.
14. No refactor outside the task scope unless required to make the
    task pass and documented in the tracker.
15. ChatGPT web approval is never inferred from memory. It must be
    provided as an Approval Packet in chat and recorded in the tracker.
16. The uploaded zip seen by ChatGPT is never treated as live state.
    Claude must export current state through the mandatory reports.
17. The agent must not execute a task from an outdated ChatGPT request
    when the tracker-derived next task differs.
18. The agent must not decide reuse by judgment. Existing code, caches,
    configs, reports, plans, trackers, or scripts may be reused only when
    Section 2.2 or configs/robust_asr/reuse_policy_v1.yaml explicitly
    permits the exact path and task.
19. Existing repository trackers and legacy plans are not live state for
    robust_asr. They may be cited as legacy references only after P0.2
    classifies them.
20. CLAUDE.md must not be overwritten wholesale. The robust_asr profile
    is inserted or updated only inside the ROBUST_ASR_PROFILE block,
    preserving all pre-existing repository rules outside that block.
```

Fixed technical decisions:

```text
1. Training host:    datamove1.surrey.ac.uk + Slurm via
                     aisurrey-submit01.surrey.ac.uk through
                     slurm/tools/on_submit.sh
2. Python (Slurm):   Python 3.11 inside Apptainer
3. Apptainer image:  /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
                     If unavailable: record BLOCKED_RUNTIME and stop.
4. Reference ASR:    openai-whisper (Surrey-side evaluation)
5. RP5 runtime ASR:  faster-whisper tiny.en for Whisper base, plus
                     LoRA-adapted CT2 INT8 export when LoRA passes
                     inclusion + preservation gates.
6. Base model:       whisper-base.en
7. Quantized export: CTranslate2 INT8
8. Router priority:  LightGBM > XGBoost > sklearn HistGradientBoostingRegressor
9. Bootstrap:        paired BCa, 10000 iterations.
                     Fallback to paired percentile only if BCa is
                     unavailable in the environment; record the choice.
10. Datasets:        LibriSpeech (ID + synthetic degradation)
                     Common Voice (OOD-real, with approved fallbacks
                     in Section 1.1)
11. Optional:        CHiME, TED-LIUM (not required for v1)
12. Language:        English speech only.
13. No secrets in Git or in committed reports.
14. No large audio, datasets, checkpoints, or full run directories
    in Git.
15. Browser microphone audio is demo-only runtime input.
```

Any deviation must be recorded as `PLAN_CONFLICT` in the tracker and the agent must stop, except where this plan defines a specific non-blocking marker (`ROUTER_IMPL_FALLBACK_SKLEARN`, `BLOCKED_API`, `PENDING_PRICING_VERIFICATION`).

### 1.1 Approved public OOD fallback datasets

In priority order:

```text
1. Common Voice English subset with official transcripts.
2. TED-LIUM Release 3 held-out talks.
3. CHiME-6 dev set.
```

Approval predicate (all four must hold):

```text
1. Has official public transcripts.
2. License allows evaluation use and redistribution of derived manifests.
3. Was preregistered in configs/robust_asr/data_v1.yaml before P1.3
   ran.
4. Selected examples are disjoint from training, validation, locked
   test, and demo examples by audio_id and audio_sha256.
```

Decision rules:

```text
1. If Common Voice satisfies the predicate, use Common Voice.
2. Else if TED-LIUM Release 3 satisfies the predicate, use it and
   name it explicitly in every report.
3. Else if CHiME-6 dev satisfies the predicate, use it and name it
   explicitly in every report.
4. Else: set claims_enabled.ood_real = false, record BLOCKED_OOD_PUBLIC,
   continue ID and OOD-param work, do not make OOD-real claims.
5. Do not approve a new fallback inside P1.3 after seeing results.
```


## 2. Branch and repository layout

Repository root: `/mnt/fast/nobackup/users/gb0048/asr_enhancement`

Source branch: `feature/training-datamove1-v1`
Target branch: `feature/robust-asr-lora-router-datamove1-v1`

Hard branch rules:

```text
1. Do not start any task unless feature/training-datamove1-v1 exists
   locally and can be inspected.
2. Do not start any implementation task unless
   origin/feature/training-datamove1-v1 is reachable through
   git fetch origin.
3. Create the target branch only from feature/training-datamove1-v1.
4. Do not create the target branch from master, main, or any other
   branch.
5. If either source reference is missing during P0.0, return
   prebootstrap_status = HALTED in the Pre-bootstrap Inventory Report
   (chat only) with marker_to_record_in_p0_1 = null and stop. Do not
   write any files. P0.0 is read-only and cannot create
   reports/robust_asr/bootstrap_block.md or any other on-disk artifact.
   P0.1 will not run while prebootstrap_status == HALTED. A later
   successful P0.0 supersedes the halted report and P0.1 must not record
   BLOCKED_SOURCE_BRANCH from the earlier halted report.
```

Deterministic target branch resolution:

```text
Let source = feature/training-datamove1-v1.
Let target = feature/robust-asr-lora-router-datamove1-v1.

Before P0.1:
  run git fetch origin.

If target does not exist locally and origin/target does not exist:
  checkout source.
  pull --ff-only origin source.
  create target from source.
  push -u origin target.

If target exists on origin but not locally:
  checkout -b target origin/target.
  verify target contains source as an ancestor or contains the P0.1
    bootstrap commit recorded in the tracker.

If target exists locally:
  checkout target.
  pull --ff-only origin target if origin/target exists.
  verify target contains source as an ancestor or contains the P0.1
    bootstrap commit recorded in the tracker.

If target exists but neither ancestry condition holds:
  status = HALTED.
  marker = BLOCKED_BRANCH_LINEAGE.
  write reports/robust_asr/branch_lineage_block.md.
  stop before editing files.

If target branch is checked out and the working tree is dirty before
P0.1:
  status = HALTED.
  marker = PLAN_CONFLICT.
  write the dirty paths to reports/robust_asr/branch_lineage_block.md.
  stop before editing files.
```

Required directories (create at P0.1, then never delete):

```text
configs/robust_asr/
docs/plans/
docs/progress/
docs/profiles/
docs/reports/robust_asr/
reports/robust_asr/
reports/robust_asr/lora/
reports/robust_asr/router/
reports/robust_asr/system/
reports/robust_asr/demo/
reports/robust_asr/leakage/
reports/robust_asr/task_reports/
artifacts/robust_asr/
artifacts/robust_asr/manifests/
artifacts/robust_asr/eval_tables/
artifacts/robust_asr/oracle/
artifacts/robust_asr/router/
artifacts/robust_asr/router/candidates/
artifacts/robust_asr/router/selected_router/
artifacts/robust_asr/lora_smoke/
artifacts/robust_asr/lora_full/
artifacts/robust_asr/lora_merged_fp16/
artifacts/robust_asr/lora_ct2_int8/
artifacts/robust_asr/runtime_smoke/
artifacts/robust_asr/runtime_contract/
artifacts/robust_asr/demo/
artifacts/robust_asr/handoff/
artifacts/robust_asr/state_packets/
scripts/robust_asr/
tests/robust_asr/
slurm/jobs/
slurm/templates/
slurm/tools/
libs/audio/
libs/common/
```

Ignored runtime paths (managed in `.gitignore`):

```text
runs/
*.wav
*.flac
*.mp3
*.m4a
*.pt
*.pth
*.ckpt
*.bin
*.safetensors
.cache/
.hf_cache/
```

Demo example audio under `artifacts/robust_asr/demo/` is the only audio that may be tracked, and only if licensed for redistribution and small enough for Git.

Document-priority for conflicts:

```text
1. orchestrator plan (strategy, claim boundaries, approval protocol)
2. this file (execution rules, contracts, gates)
3. existing repository contracts and test suites
4. existing training_datamove1_plan.md conventions (legacy)
5. existing progress tracker state
6. existing README or loose notes

Do not silently resolve conflicts. If a conflict changes data splits,
evaluation definitions, model selection, or deployment behavior,
record PLAN_CONFLICT and stop.
```


### 2.1 Existing repository integration policy

These rules close every discretionary integration point with the existing
repository. They are active from P0.0 onward.

Active robust_asr state paths:

```text
docs/progress/robust_asr_progress.yaml
docs/progress/robust_asr_progress.md
docs/progress/robust_asr_state_capsule.md
reports/robust_asr/**
artifacts/robust_asr/**
configs/robust_asr/**
scripts/robust_asr/**
tests/robust_asr/**
docs/reports/robust_asr/**
docs/profiles/CLAUDE.robust_asr.md
```

Legacy state paths. These are read-only unless a later task names the
exact path in its Planned File Changes and the orchestrator approves it:

```text
plan.md
docs/plans/demo_platform_plan.md
docs/plans/training_datamove1_plan.md
docs/progress/training_datamove1_progress.md
docs/progress/training_datamove1_progress.yaml
docs/claude_task_progress.md
docs/claude_task_progress.yaml
reports/training/**
artifacts/training/**
```

Reusable implementation paths. These may be read in P0.2 and used later
only through an explicit task scope and a reuse_policy_v1.yaml row:

```text
services/api/**
services/worker/**
libs/asr_adapter/**
libs/audio_pipeline/**
libs/audio/**
libs/common/**
infra/**
scripts/demo/**
scripts/training/**
slurm/tools/**
slurm/jobs/**
tests/**
configs/**
```

Path classification rules:

```text
1. robust_asr_progress.yaml is the only live robust_asr tracker.
2. Existing training or demo trackers are legacy references. They never
   determine current_task, last_completed_task, markers, or claims.
3. Existing plan.md and docs/plans/training_datamove1_plan.md are
   templates and lineage references only. They never override this plan.
4. Existing runtime code may be reused only by adapter, import, wrapper,
   or narrow patch. Rewrites of services/api, services/worker, or infra
   require a task that names the exact file set.
5. Existing evaluation outputs are not valid robust_asr evidence unless
   a robust_asr adapter converts them into the Section 3 schema and a
   validator records OK_EVAL_TABLE under the current task.
6. Existing AssemblyAI caches are not valid robust_asr evidence unless
   P0.2 records their path, checksum policy, dataset coverage, backend
   version, and transcript provenance, and P5.1 validates them.
7. Existing LoRA checkpoints are never selected directly. They may only
   be inspected as prior evidence. Full LoRA selection must be produced
   by P4 under this plan unless P4 is skipped by Decision A.
8. Existing dataset roots may be reused as storage locations, not as
   manifests. P1 must build new robust_asr manifests.
9. Existing tests remain part of repository health. A robust_asr task may
   add tests or fix regressions inside approved scope, but must not
   delete or weaken existing tests.
10. Any path not classified above is default no-touch. Reading is allowed
    for inventory. Editing requires an Approval Packet that names the
    path and rationale.
```

### 2.2 Deterministic reuse policy and touch authority

P0.2 creates `configs/robust_asr/reuse_policy_v1.yaml`. After P0.2,
no task may reuse a repository asset unless the policy has a row with
all required fields:

```yaml
- path: <exact_path_or_glob>
  class: legacy_state|template_reference|implementation_reuse|data_root|cache_candidate|no_touch
  permitted_use: read_only|adapter_input|extend_in_place|generated_output|forbidden
  allowed_tasks: [P0.2]
  validator: <script_or_command_or_none>
  checksum_required: true|false
  large_artifact: true|false
  commit_allowed: true|false
  notes: <short deterministic note>
```

Default policy values when a path has no row:

```text
class = no_touch
permitted_use = forbidden
allowed_tasks = []
validator = none
checksum_required = false
large_artifact = unknown
commit_allowed = false
```

Task planning rule:

```text
1. Every Planning Report must list expected_paths and
   expected_no_touch_paths.
2. For every expected_path outside robust_asr-owned paths, the Planning
   Report must name the matching reuse_policy_v1.yaml row.
3. If no matching row exists, Claude must return REQUIRES_SCOPE_CHANGE
   in the Planning Report and stop. It must not edit the path.
4. If a row says permitted_use = read_only, Claude may inspect the path
   but must not modify it.
5. If a row says permitted_use = adapter_input, Claude may read it and
   write new robust_asr adapter outputs, but must not modify the source
   path.
6. If a row says permitted_use = extend_in_place, Claude may modify only
   the files named by the approved task.
7. If a row says permitted_use = generated_output, Claude may create or
   overwrite files only under the output path named by that row.
8. If a row says permitted_use = forbidden, Claude must not read large
   binary contents, modify, copy, commit, or derive evidence from it.
```

Mandatory no-touch paths for every task unless the task explicitly names
an exception:

```text
.git/**
.env
.env.*
*.key
*.pem
*.token
runs/**
.cache/**
.hf_cache/**
**/__pycache__/**
*.wav
*.flac
*.mp3
*.m4a
*.pt
*.pth
*.ckpt
*.bin
*.safetensors
```

CLAUDE.md update rule:

```text
P0.1 must preserve the existing CLAUDE.md outside this exact block:

BEGIN ROBUST_ASR_PROFILE
...
END ROBUST_ASR_PROFILE

If the block exists, replace only the block body. If it does not exist,
append the block at the end of CLAUDE.md. No other CLAUDE.md lines may
be deleted, reordered, or rewritten. Do not add CLAUDE.md merge=ours to
.gitattributes. If a future merge conflict touches CLAUDE.md outside the
ROBUST_ASR_PROFILE block, halt with PLAN_CONFLICT instead of resolving
it automatically.
```


## 3. Canonical evaluation schema

Every backend writes one row per `audio_id` to the same schema. No backend may use a private result format without an adapter into this schema.

Columns (28):

```text
audio_id
source_dataset
source_split
speaker_id
utterance_id
condition_family
degradation_id
degradation_params_json
audio_path_or_uri
audio_sha256
reference_text
reference_normalized
backend_name
backend_version
backend_kind
decode_config_json
raw_transcript
normalized_transcript
normalization_version
wer
cer
wa
backend_latency_ms
server_processing_latency_ms
end_to_end_latency_ms
ram_peak_mb
cost_usd
local_only
third_party_provider
error_or_null
created_at_utc
```

Backend names:

```text
whisper_base_ct2_int8
whisper_lora_fp16
whisper_lora_ct2_int8
assemblyai
router_driven
deterministic_selector_driven
```

`local_only` means the audio did not leave the RP5 to a third-party ASR provider. It does not mean the audio stayed on the recruiter device.

Required schema tests (in `tests/robust_asr/test_eval_schema.py`):

```text
1. All required columns exist.
2. One row per (audio_id, backend_name, decode_config_hash).
3. audio_id is stable across backends.
4. reference_normalized is identical across backends for the same
   audio_id.
5. normalization_version is recorded on every row.
6. error_or_null is non-null whenever any latency field is null.
7. cost_usd is numeric or null; null only when local_only == true.
```

Required degradation families:

```text
clean
cafe_noise
phone_band
far_field_room
muffled_lowpass
```

Degradation function interface (every family must implement):

```python
def sample_<family>(input_wav: str, output_wav: str, seed: int, params: dict) -> dict:
    """Write degraded audio and return metadata with all parameter values."""
```

Required metadata returned:

```text
condition_family
random_seed
snr_db
rir_id_or_null
filter_params_json
source_audio_sha256
output_audio_sha256
```

ID eval uses parameter ranges seen during training. OOD-param eval uses the same families with held-out parameter ranges.

Leakage guard (enforced by `tests/robust_asr/test_leakage.py`):

```text
1. No speaker_id in both LoRA train and router train.
2. No audio_id used for LoRA fine-tuning may appear in router train,
   router validation, router locked test, or OOD-real eval.
3. LoRA checkpoint selection may not use router locked test or
   OOD-real locked eval.
4. Router training targets may use LoRA predictions only on audio
   not used for LoRA fine-tuning.
5. Demo examples may not be drawn from locked evaluation sets.
6. Common Voice demo examples must be drawn from a dedicated public
   demo subset disjoint from the Common Voice OOD-real locked eval.
```

Required leakage tests:

```text
test_speaker_disjoint_lora_vs_router_train
test_audio_id_disjoint_lora_train_vs_router_targets
test_locked_test_sets_disjoint_from_train
test_demo_examples_disjoint_from_eval_sets
test_common_voice_demo_disjoint_from_ood_locked
```

Each test must fail with intersecting IDs printed or written to a failure artifact under `reports/robust_asr/leakage/`.

Normalization and metrics:

```text
1. One shared text normalization function for all backends.
2. WER, CER, WA = 1 - WER. All comparisons use normalized reference
   and normalized transcript.
3. Raw transcripts are also preserved.
4. NORMALIZATION_VERSION is a string constant in libs/common/versions.py.
5. Decode config disables timestamps for WER eval unless a task
   records ENV_CONSTRAINT.
6. Whisper decode defaults for evaluation: task=transcribe, language=en,
   condition_on_previous_text=false (deviations require ENV_CONSTRAINT).
```


## 4. Script contracts

Every script referenced anywhere in this plan must satisfy its contract here. Inputs, outputs, asserts, exit codes, and stdout sentinels are normative. If a task implementation drifts from the contract, stop and record `PLAN_CONFLICT`.

Conventions:

```text
- Every script accepts --help and exits 0.
- Every script writes a single OK_<NAME> line on stdout when its
  primary assertion passes.
- Every script exits 0 on success, 1 on the first failing assertion.
- Every script reads paths from CLI args, not env vars (except
  ASSEMBLYAI_API_KEY and HF_TOKEN where explicitly noted).
- All output paths are relative to the repository root unless prefixed
  with a scratch root configured in the relevant YAML.
```

### 4.1 Validators

`scripts/robust_asr/validate_eval_schema.py`:

```text
Inputs:  --schema <yaml>                optional; defaults to libs/common/eval_schema.yaml
Asserts: 1. Schema YAML loads.
         2. Listed columns equal Section 3 columns.
         3. Required column types are recorded.
Stdout:  OK_EVAL_SCHEMA on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/validate_eval_table.py`:

```text
Inputs:  --input <parquet>
Asserts: Section 3 schema tests 1 through 7.
Stdout:  OK_EVAL_TABLE on PASS.
Exit:    0 PASS, 1 FAIL with first failing assertion.
```

`scripts/robust_asr/validate_oracle_table.py`:

```text
Inputs:  --input <parquet>
Asserts: 1. Section 3 columns plus per-backend WER/latency/cost.
         2. oracle_action is in the available action set.
         3. For every row, oracle_action selects the backend with the
            lowest predicted total_cost under Section 5 epsilon_wer
            plus priority order.
         4. No row has oracle_action == 'whisper_lora_ct2_int8' and
            backend_available_lora == false.
Stdout:  OK_ORACLE_TABLE on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/validate_router_matrices.py`:

```text
Inputs:  --router-dir <dir>
Asserts: 1. router_train.parquet, router_val.parquet,
            router_test_locked.parquet exist with non-zero rows.
         2. Feature columns identical across the three matrices.
         3. No audio_id in both router_train and (router_val or
            router_test_locked).
         4. No speaker_id in both router_train and router_test_locked.
         5. Target columns include predicted_wer per available backend.
Stdout:  OK_ROUTER_MATRICES on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/validate_selector_evidence.py`:

```text
Inputs:  --input <artifacts/robust_asr/router/selector_evidence.parquet>
Asserts: 1. File exists and has non-zero rows.
         2. Columns include audio_id, reference_normalized,
            whisper_base_ct2_int8_wer, whisper_base_ct2_int8_latency_ms,
            selected_action, selector_reason, ask_repeat_allowed,
            assemblyai_available, lora_available.
         3. selected_action is in {whisper_base_ct2_int8, assemblyai,
            whisper_lora_ct2_int8, ask_repeat}.
         4. If assemblyai_available == false, selected_action is never
            assemblyai.
         5. If lora_available == false, selected_action is never
            whisper_lora_ct2_int8.
         6. Every audio_id is disjoint from demo examples and from any
            LoRA fine-tuning audio_id.
Stdout:  OK_SELECTOR_EVIDENCE on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/validate_runtime_contract.py`:

```text
Inputs:  --strict-skeleton | --strict-final (mutually exclusive)
         --request <json>
         --response <json>
         [--request-schema <json-schema>]
         [--response-schema <json-schema>]
         [--out <md>]
Asserts: The 19 assertions specified in Task P0.4.
Stdout:  OK_CONTRACT_SKELETON or OK_CONTRACT_FINAL on PASS.
Exit:    0 PASS, 1 FAIL with the failing assertion key.
```

`scripts/robust_asr/validate_report_shape.py`:

```text
Inputs:  --schemas <docs/plans/state_packet_schemas_v1.yaml>
         --fixtures <artifacts/robust_asr/state_packets/report_shape_fixtures>
Asserts: 1. The schemas YAML loads.
         2. Required schema keys exist: prebootstrap_inventory_report,
            state_packet, planning_report, execution_report,
            phase_gate_report, approval_packet, and
            supplemental_evidence_report.
         3. Every fixture file exists and uses the exact section order
            required by the corresponding schema.
         4. Every required field appears.
         5. approval_packet is wrapped in exactly one
            ORCHESTRATOR_DECISION mapping.
         6. No fixture contains unknown top-level report sections.
Stdout:  OK_REPORT_SHAPE on PASS.
Exit:    0 PASS, 1 FAIL with first inconsistency.
```

`scripts/robust_asr/verify_handoff_package.py`:

```text
Inputs:  --handoff <dir>
         [--strict]   if set, requires all 8 README sections in order
                      and a handoff/<date>-<short_sha> tag.
Asserts: 1. README.md has the 8 numbered sections from P9.1 in order.
         2. Every artifact in README Section 2 exists at the listed
            path with matching SHA-256.
         3. handoff_smoke.py is executable.
         4. rollback_to_previous_handoff.py is executable.
         5. handoff_validation_template.md exists.
         6. Backend configs do not contain literal secrets (grep for
            ASSEMBLYAI_API_KEY, sk_, Bearer ).
         7. If --strict, a tag of the form handoff/<date>-<short_sha>
            exists locally and on origin.
Stdout:  OK_HANDOFF_PACKAGE on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/verify_plan_tracker_consistency.py`:

```text
Inputs:  --plan-orchestrator <md>   docs/plans/robust_asr_orchestrator_plan_v3_4_7.md
         --plan-agent <md>          this file
         --tracker <yaml>           docs/progress/robust_asr_progress.yaml
         --out <md>                 reports/robust_asr/plan_tracker_consistency.md
Asserts: 1. Every task ID P[0-9]+\.[0-9]+ defined in the agent plan
            Section 9 has a tracker entry.
         2. Every tracker task entry references a task ID in the
            agent plan.
         3. Every phase gate field referenced in Section 8 exists in
            the tracker YAML schema.
         4. Every marker referenced in either plan is in Section 6.
         5. Every claims_enabled key referenced in either plan is set
            to true or false (not 'pending') in the tracker by P10.
         6. Every script referenced in either plan is in this Section 4
            or exists at its referenced path.
         7. Every approval prompt requirement listed in the
            orchestrator plan Section 4 phase narrative is satisfied
            by tracker state when phase_summary.<P_n> = PASS.
         8. The tracker schema contains state_transport fields required
            by Section 0.
         9. The state capsule path exists in tracker artifacts after P0.1.
        10. Every completed task after P0.1 has a task report path under
            reports/robust_asr/task_reports/.
        11. Every transition in Section 0.1 has a valid source task,
            terminal state or marker, and destination task.
        12. Every skip status referenced in Section 0.1 is allowed by
            the tracker status enum.
        13. If OUTCOME_E_DETERMINISTIC_SELECTOR is active, P6/P7 gate
            predicates route to selector evidence and P7.3, not to
            router candidate training.
        14. tracker.repo_integration exists and points to
            configs/robust_asr/reuse_policy_v1.yaml,
            reports/robust_asr/repo_integration_policy.md, and
            reports/robust_asr/touch_policy.md.
        15. CLAUDE.md contains exactly one BEGIN ROBUST_ASR_PROFILE block
            and one END ROBUST_ASR_PROFILE block, and the text inside
            the block matches docs/profiles/CLAUDE.robust_asr.md.
        16. Every completed task report contains reuse_policy_rows_used
            and no_unapproved_reuse.
        17. scripts/robust_asr/validate_report_shape.py exists and the
            latest report shape fixtures emit OK_REPORT_SHAPE.
Stdout:  OK_PLAN_TRACKER_CONSISTENCY on PASS.
Exit:    0 PASS, 1 FAIL with first inconsistency.
```

`scripts/robust_asr/final_asset_audit.py`:

```text
Inputs:  --artifact-root <dir>   default artifacts/robust_asr
         --report-root <dir>     default reports/robust_asr
         --out <md>              reports/robust_asr/final_asset_audit.md
Asserts: 1. Every committed artifact has a SHA-256 matching the tracker.
         2. Every referenced large artifact has a SHA-256 in the tracker.
         3. No residual TODO_FILLED_IN_<task_id> tokens for tasks whose
            tracker.tasks[<task_id>].status == PASS.
         4. No secret-like tokens (ASSEMBLYAI_API_KEY, sk_, Bearer )
            anywhere outside .git.
Stdout:  OK_FINAL_ASSET_AUDIT on PASS.
Exit:    0 PASS, 1 FAIL.
```

### 4.2 Backend evaluation

`scripts/robust_asr/run_backend_eval.py`:

```text
Inputs:  --backend <whisper_base_ct2_int8 | whisper_lora_fp16 |
                     whisper_lora_ct2_int8 | assemblyai>
         --manifests <eval_manifests_v1.yaml>
         [--model <path>]   required for whisper_lora_fp16,
                            whisper_lora_ct2_int8, and (when no cache)
                            whisper_base_ct2_int8.
         [--cache <dir>]    required for assemblyai (read AssemblyAI
                            transcripts from cache).
         --out <parquet>
Behavior: Writes one row per audio_id with all 28 Section 3 columns.
          Computes WER, CER, WA against reference_normalized using
          NORMALIZATION_VERSION from libs/common/versions.py.
          Records backend_version, decode_config_json, normalization_version.
Stdout:  OK_BACKEND_EVAL on PASS.
Exit:    0 PASS, 1 FAIL on missing or malformed input.
```

`scripts/robust_asr/summarize_backend_eval.py`:

```text
Inputs:  --input <parquet>
         --out <md>
Behavior: Writes per-family WER/WA, total latency, total cost, count
          of failed rows. Records dataset version, backend version,
          and normalization version.
Stdout:  OK_BACKEND_SUMMARY on PASS.
Exit:    0 PASS, 1 FAIL.
```

### 4.3 Manifests and degradations

`scripts/robust_asr/build_public_manifests.py`:

```text
Inputs:  --config <configs/robust_asr/data_v1.yaml>
Behavior: Reads dataset roots from config. Builds parquet manifests
          for: LoRA train, router train, validation, locked test,
          OOD-real locked (only if a Section 1.1 dataset's root
          resolves), and Common Voice demo reservation (only if the
          Common Voice root resolves).
          Writes audio_sha256, audio_path_or_uri, speaker_id (or
          proxy_speaker_id_v1 if dataset lacks stable speaker IDs),
          duration_s, and split_label.
          Skips a dataset when os.path.isdir(<root>) is false; records
          the absence in stdout. Halts (exit 1) if data_v1.yaml has
          unresolvable required fields (no fallback configured for the
          OOD slot).
Outputs: artifacts/robust_asr/manifests/<dataset>_<split>.parquet
Stdout:  OK_PUBLIC_MANIFESTS on PASS, with per-dataset row counts.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/summarize_manifests.py`:

```text
Inputs:  --manifest-root <dir>
         --out <md>
Behavior: Writes per-manifest row count, duration sum, speaker count,
          checksum, and OOD-real claim status (`enabled` if Common
          Voice or fallback is present, `disabled` if BLOCKED_OOD_PUBLIC).
Stdout:  OK_MANIFEST_SUMMARY on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/build_degradation_v1.py`:

```text
Inputs:  --config <configs/robust_asr/degradation_v1.yaml>
Behavior: Generates ID and OOD-param degraded audio for the five
          required families using libs/audio/degradations.py
          functions. Writes manifests with per-row params, source
          and output checksums, seed, and family.
Outputs: artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet
         artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet
         (and per-family individual files under the same root)
Stdout:  OK_DEGRADATION_V1 on PASS, with per-family success/skip counts.
Exit:    0 PASS, 1 FAIL.
```

### 4.4 LoRA pipeline

`scripts/robust_asr/train_lora_smoke.py`:

```text
Inputs:  --config <configs/robust_asr/lora_smoke.yaml>
Behavior: Trains Whisper base.en with LoRA on the smoke split for at
          most steps_max steps. Saves checkpoints, training logs,
          loss curve to artifacts/robust_asr/lora_smoke/.
          Reads degraded inputs and clean transcript targets.
          Uses fixed eval decode defaults from Section 3.
          On CUDA OOM at batch_size = b, retries once with
          batch_size = max(1, b // 2). If OOM persists at batch_size = 1,
          exits 2 with stderr line "CUDA_OOM_AT_BATCH_SIZE_1".
          On non-finite loss for >= 5% of completed steps,
          exits 3 with stderr line "NON_FINITE_LOSS_THRESHOLD_EXCEEDED".
Outputs: artifacts/robust_asr/lora_smoke/checkpoint_manifest.json
         artifacts/robust_asr/lora_smoke/training_log.csv
         artifacts/robust_asr/lora_smoke/loss_curve.png
Stdout:  OK_LORA_SMOKE_TRAIN on PASS, with steps_completed and
         best_step recorded.
Exit:    0 PASS, 1 generic FAIL, 2 OOM_AT_BATCH_1, 3 NON_FINITE_LOSS.
```

`scripts/robust_asr/evaluate_lora_smoke.py`:

```text
Inputs:  --config <configs/robust_asr/lora_smoke.yaml>
         --checkpoint-manifest <artifacts/robust_asr/lora_smoke/checkpoint_manifest.json>
         --out <reports/robust_asr/lora/lora_smoke_result.json>
Behavior: Evaluates the best-loss smoke checkpoint on the smoke eval
          split. Writes per-family WA, macro WA gain over Whisper base
          on the same split, max family WA gain, clean WA regression.
          Uses NORMALIZATION_VERSION and reference_normalized.
          Asserts variance > 0 across families (no degenerate result).
          On variance == 0, writes
          reports/robust_asr/lora/lora_smoke_degenerate.md and exits 4
          with stderr "DEGENERATE_SMOKE_RESULT".
Stdout:  OK_LORA_SMOKE_EVAL on PASS.
Exit:    0 PASS, 1 generic FAIL, 4 DEGENERATE.
```

`scripts/robust_asr/smoke_export_lora_ct2.py`:

```text
Inputs:  --config <configs/robust_asr/lora_smoke.yaml>
         --checkpoint <path>
         --out <artifacts/robust_asr/lora_smoke/export_smoke_result.json>
Behavior: Merges LoRA into FP16, exports to CTranslate2 INT8, loads
          with faster-whisper, transcribes one fixture audio file.
          Records each step's success/failure and elapsed time.
Stdout:  OK_LORA_EXPORT_SMOKE on PASS.
Exit:    0 PASS, 1 FAIL with the offending step name in stderr.
         If CTranslate2 reports an unsupported model version or
         operator, exit 5 with stderr
         "CT2_UNSUPPORTED_VERSION_OR_OP: <version_or_op>".
```

`scripts/robust_asr/decide_lora_smoke.py`:

```text
Inputs:  --input <reports/robust_asr/lora/lora_smoke_result.json>
         --export-input <artifacts/robust_asr/lora_smoke/export_smoke_result.json>
         --out <reports/robust_asr/lora/lora_smoke_report.md>
Behavior: Applies the Section 5 strict smoke booleans:
            SMOKE_PASS    = (macro_wa_gain >= 0.005
                              AND clean_regression <= 0.010)
                            OR (max_family_wa_gain >= 0.010
                                AND clean_regression <= 0.010)
            SMOKE_PARTIAL = (NOT SMOKE_PASS
                             AND max_family_wa_gain >= 0.010
                             AND clean_regression <= 0.020)
            SMOKE_FAIL    = otherwise
          On export-input failure, outcome = HALTED, marker = EXPORT_BLOCKED.
          On evaluate input file missing, exit 1.
          On degenerate evaluate file, outcome = FAIL.
Outputs: lora_smoke_report.md with one of {PASS, PARTIAL, FAIL, HALTED}
         on its first line.
Stdout:  OK_LORA_SMOKE_DECISION:<outcome> on PASS.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/train_lora_full.py`:

```text
Inputs:  --config <configs/robust_asr/lora_full.yaml>
Behavior: Trains Whisper base.en with LoRA on the full LoRA train split.
          Saves checkpoints at config.checkpoint_every_steps. Persists
          training_log.csv, loss_curve.png. Same OOM and non-finite
          loss exit codes as train_lora_smoke.py.
          On Slurm preemption signal (SIGTERM), persist current
          checkpoint and write
          artifacts/robust_asr/lora_full/preemption_log.json with the
          step number, then exit 6 with stderr "PREEMPTED_AT_STEP_<n>".
Outputs: artifacts/robust_asr/lora_full/checkpoint_manifest.json
         artifacts/robust_asr/lora_full/training_log.csv
         artifacts/robust_asr/lora_full/loss_curve.png
Stdout:  OK_LORA_FULL_TRAIN on PASS.
Exit:    0 PASS, 1 generic FAIL, 2 OOM_AT_BATCH_1,
         3 NON_FINITE_LOSS, 6 PREEMPTED_AT_STEP.
```

`scripts/robust_asr/evaluate_lora_checkpoints.py`:

```text
Inputs:  --config <configs/robust_asr/lora_full.yaml>
         --checkpoint-manifest <artifacts/robust_asr/lora_full/checkpoint_manifest.json>
         --out <reports/robust_asr/lora/full_lora_selection.json>
Behavior: For each candidate checkpoint:
          - Loads weights. If torch.load raises OR any tensor in the
            state dict satisfies torch.isfinite(...).all() == False,
            mark checkpoint as CORRUPT and skip.
          - Runs evaluation on lora_validation manifest with the
            global wall-clock timeout config.eval_timeout_seconds.
            On timeout, retries once with batch_size = max(1, b // 2).
            On second timeout, mark checkpoint as TIMED_OUT and skip.
          - Records macro_wa, per_family_wa, worst_family_wa, paired
            bootstrap WA gain CI vs whisper_base on the same audio_ids.
          If all checkpoints are CORRUPT or TIMED_OUT, exit 7 with
          stderr "ALL_CHECKPOINTS_UNUSABLE".
Stdout:  OK_LORA_CHECKPOINT_EVAL with usable_count and unusable_count.
Exit:    0 PASS, 1 FAIL, 7 ALL_UNUSABLE.
```

`scripts/robust_asr/select_lora_checkpoint.py`:

```text
Inputs:  --input <reports/robust_asr/lora/full_lora_selection.json>
         --out <reports/robust_asr/lora/full_lora_training.md>
         --tolerance-macro-wa <float>     default 0.002
Behavior: Applies Section 5 deterministic checkpoint priority:
            (1) highest macro WA on lora_validation;
            (2) tie within tolerance-macro-wa: highest worst-family WA;
            (3) tie within tolerance-macro-wa AND tie on worst-family:
                lowest val/train WA gap (anti-overfit);
            (4) tie on all above: most recent training step.
          Records the rule that fired in the report.
          If macro_wa is non-monotonic across checkpoints (defined as:
          there exists step i < j with macro_wa[i] > macro_wa[j] for
          some j, i.e. the running max is reached before the last
          checkpoint), still apply the priority strictly. Record the
          monotonicity diagnostic in the report.
Stdout:  OK_LORA_CHECKPOINT_SELECT:<step>
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/evaluate_full_lora.py`:

```text
Inputs:  --selected <reports/robust_asr/lora/full_lora_training.md>
         --eval-manifests <eval_manifests_v1.yaml>
         --out-table <artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet>
         --out-report <reports/robust_asr/lora/full_lora_eval.md>
Behavior: Runs full LoRA inference on ID, OOD-param, and (if enabled)
          OOD-real eval sets. Writes canonical schema rows. Computes
          paired bootstrap BCa CIs (10000 iterations) of WA gain over
          Whisper base on every shared audio_id.
          Applies Section 5 full LoRA outcome rules:
            PASS_GLOBAL:
              macro WA gain > 0,
              paired BCa 95% CI lower bound > 0.010,
              clean regression <= 0.015 WA loss,
              no family WA drop > 0.030.
            PASS_SUBSET:
              not PASS_GLOBAL,
              at least one family with paired BCa 95% CI lower bound
              > 0.010,
              clean regression <= 0.015 WA loss,
              at most one family with WA drop > 0.030.
            FAIL_WITH_EVIDENCE:
              not PASS_GLOBAL, not PASS_SUBSET; all artifacts present.
            HALTED:
              required artifacts missing (raise; do not write a fake
              outcome).
Outputs: full_lora_eval.md with the outcome on its first line.
         whisper_lora_fp16.parquet in canonical schema.
Stdout:  OK_LORA_FULL_EVAL:<outcome>
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/merge_lora_to_fp16.py`:

```text
Inputs:  --selected-checkpoint <path>
         --base-model <whisper-base.en handle or path>
         --out-dir <artifacts/robust_asr/lora_merged_fp16>
Behavior: Merges LoRA weights into the FP16 base model. Saves the
          merged model and its config. Computes SHA-256 of merged
          model files.
Stdout:  OK_LORA_MERGE_FP16
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/export_lora_ct2_int8.py`:

```text
Inputs:  --merged-fp16-dir <artifacts/robust_asr/lora_merged_fp16>
         --out-dir <artifacts/robust_asr/lora_ct2_int8>
Behavior: Exports the merged FP16 model to CTranslate2 with
          quantization INT8. On unsupported version or op, exit 5
          with stderr "CT2_UNSUPPORTED_VERSION_OR_OP: <version_or_op>".
Stdout:  OK_LORA_CT2_INT8_EXPORT
Exit:    0 PASS, 1 FAIL, 5 UNSUPPORTED.
```

`scripts/robust_asr/evaluate_lora_int8_preservation.py`:

```text
Inputs:  --base-eval-table <artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet>
         --fp-eval-table <artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet>
         --int8-eval-table <artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet>
         --out <reports/robust_asr/lora/lora_ct2_int8_preservation.md>
Behavior: For each shared audio_id across the three tables, computes
          baseline_wer, fp_wer, int8_wer.
          Aggregates: fp_improvement = baseline_wer - fp_wer
                       int8_improvement = baseline_wer - int8_wer
          Outcome:
            PASS if fp_improvement > 0 AND
                    int8_improvement >= 0.8 * fp_improvement;
            PASS if fp_improvement <= 0 AND
                    int8_wer <= fp_wer + 0.005;
            FAIL otherwise.
            EXPORT_BLOCKED if int8_eval_table missing.
Outputs: lora_ct2_int8_preservation.md with outcome on first line.
Stdout:  OK_LORA_PRESERVATION:<outcome>
Exit:    0 PASS, 1 FAIL.
```

### 4.5 AssemblyAI

`scripts/robust_asr/populate_assemblyai_cache.py`:

```text
Inputs:  --manifests <eval_manifests_v1.yaml>
         --cache-dir <scratch path or artifacts/robust_asr/cache/assemblyai>
         --pricing-config <configs/robust_asr/pricing_v1.yaml>
Reads:   ASSEMBLYAI_API_KEY from env. If unset, exit 8 with stderr
         "ASSEMBLYAI_API_KEY_UNSET".
Behavior: For every audio_id in the eval manifests not yet cached,
          submits AssemblyAI request, stores response JSON keyed by
          audio_sha256. On HTTP 401/403, exit 9 with stderr
          "ASSEMBLYAI_AUTH_FAIL". On HTTP 429, exponential backoff up
          to 5 retries, then exit 10 with stderr "ASSEMBLYAI_QUOTA".
          On HTTP 5xx, retry once with 60s backoff, then move on and
          record the failure for that audio_id.
          Computes estimated total cost using pricing_v1.yaml fields
          and writes it to cache_summary.json.
Outputs: <cache-dir>/<audio_sha256>.json (one per audio_id)
         <cache-dir>/cache_summary.json
Stdout:  OK_ASSEMBLYAI_CACHE with <cached_count>/<requested_count>.
Exit:    0 PASS, 1 generic FAIL, 8 KEY_UNSET, 9 AUTH, 10 QUOTA.
```

`scripts/robust_asr/evaluate_assemblyai_from_cache.py`:

```text
Inputs:  --manifests <eval_manifests_v1.yaml>
         --cache-dir <path>
         --pricing-config <configs/robust_asr/pricing_v1.yaml>
         --out <artifacts/robust_asr/eval_tables/assemblyai.parquet>
Behavior: Reads cached transcripts. Builds canonical schema rows.
          Records cost_usd from cache and pricing.
          local_only = false; third_party_provider = "assemblyai".
          For audio_ids without a cache entry, writes one row with
          error_or_null = "no_cache_entry" and all latency fields null.
Stdout:  OK_ASSEMBLYAI_EVAL with <rows> and <missing_audio_ids> count.
Exit:    0 PASS, 1 FAIL.
```

### 4.6 Oracle and router

`scripts/robust_asr/build_oracle_table.py`:

```text
Inputs:  --backend-tables <list of parquets>
         --cost-config <configs/robust_asr/router_v1.yaml>
         --out <artifacts/robust_asr/oracle/oracle_table.parquet>
Behavior: JOINs all backend eval tables on audio_id. For every audio_id,
          computes total_cost per available action under
          alpha * predicted_WER + beta * normalized_latency
          + gamma * monetary_cost + delta * third_party_penalty.
          Selects oracle_action: the eligible action with the lowest
          total_cost, ties broken by Section 5 priority order
          (whisper_base_ct2_int8 > whisper_lora_ct2_int8 > assemblyai),
          ask_repeat applied if min predicted_wer > ask_repeat_wer_threshold.
          Asserts JOIN coverage: row count of oracle_table equals the
          number of distinct audio_ids in the largest backend table.
          On coverage < 100%, exits 1 with stderr listing missing
          audio_ids.
Stdout:  OK_ORACLE_BUILD with <rows>.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/build_selector_evidence_table.py`:

```text
Inputs:  --backend-tables <list of parquets>
         --selector-config <configs/robust_asr/router_v1.yaml>
         --out <artifacts/robust_asr/router/selector_evidence.parquet>
Behavior: Builds the locked evaluation table for the deterministic
          selector path when OUTCOME_E_DETERMINISTIC_SELECTOR is active
          before P7.1. Uses only deployable backends and the Section 5.5
          predicate. If only whisper_base_ct2_int8 remains, selected_action
          is either whisper_base_ct2_int8 or ask_repeat. Records one row
          per audio_id with selector_reason, selected_action, latency,
          WER, WA, and backend availability booleans.
Stdout:  OK_SELECTOR_EVIDENCE_BUILD with <rows>.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/extract_router_features.py`:

```text
Inputs:  --manifests <eval_manifests_v1.yaml>
         --whisper-base-eval-table <parquet>
         --out <artifacts/robust_asr/router/router_features.parquet>
Behavior: For every audio_id in the eval manifests, computes:
          - acoustic_features:
              rms_mean, rms_std, clipping_ratio,
              spectral_centroid_mean, spectral_flatness_mean,
              zero_crossing_rate, duration_s, silence_ratio,
              snr_proxy
          - decode_features_from_whisper_base (read from whisper-base
            eval table where exposed):
              avg_logprob, no_speech_prob, compression_ratio,
              token_count, decode_latency_ms, repetition_score,
              language_confidence_or_null
          Records FEATURES_VERSION from libs/common/versions.py.
Stdout:  OK_ROUTER_FEATURES with <rows>.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/build_router_matrices.py`:

```text
Inputs:  --features <artifacts/robust_asr/router/router_features.parquet>
         --oracle <artifacts/robust_asr/oracle/oracle_table.parquet>
         --splits-config <configs/robust_asr/data_v1.yaml>
         --out-dir <artifacts/robust_asr/router>
Behavior: Joins features and oracle. Splits into router_train,
          router_val, router_test_locked according to splits-config
          (speaker-disjoint per Section 3 leakage rules). Writes
          predicted_wer per available backend as target columns.
Outputs: router_train.parquet, router_val.parquet, router_test_locked.parquet
Stdout:  OK_ROUTER_MATRICES_BUILD with per-split row counts.
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/train_router_candidates.py`:

```text
Inputs:  --router-dir <artifacts/robust_asr/router>
         --config <configs/robust_asr/router_v1.yaml>
         --out <artifacts/robust_asr/router/candidates>
Behavior: Trains GBDT regressors per available backend WER target.
          Uses LightGBM if importable; else XGBoost; else sklearn
          HistGradientBoostingRegressor (record ROUTER_IMPL_FALLBACK_SKLEARN).
          For each candidate, records validation per-target MAE and
          system regret on router_val.
          Detects degeneracy:
            For every pair of available_backends (a, b),
            Pearson correlation r between predicted_wer[a] and
            predicted_wer[b] over router_val. If
            min over pairs of (1 - r) < 0.10 (i.e. predictions are
            nearly identical across backends), mark candidate as
            DEGENERATE.
          On any DEGENERATE candidate, retry training once with
          stronger regularization (config.regularization_strong block).
          If still DEGENERATE, mark candidate as DEGENERATE and record
          DEGENERATE_ROUTER_RECOVERED if at least one non-degenerate
          candidate exists.
          If no non-degenerate candidate exists, exit 11 with stderr
          "ALL_CANDIDATES_DEGENERATE".
Outputs: candidates/<impl>__<config_id>/model.{txt|json|joblib}
         candidates/<impl>__<config_id>/val_metrics.json
Stdout:  OK_ROUTER_CANDIDATES with <candidate_count>.
Exit:    0 PASS, 1 FAIL, 11 ALL_DEGENERATE.
```

`scripts/robust_asr/select_router.py`:

```text
Inputs:  --candidates-dir <artifacts/robust_asr/router/candidates>
         --router-val <artifacts/robust_asr/router/router_val.parquet>
         --baseline-action <whisper_base_ct2_int8>
         --tolerance-mean-regret <float>   default 0.001
         --out <artifacts/robust_asr/router/selected_router>
Behavior: Applies Section 5 router selection priority:
            (1) lowest mean_regret on router_val vs always-baseline;
            (2) tie within tolerance-mean-regret: lowest p95_regret;
            (3) tie: lowest cloud_call_rate;
            (4) tie: lowest predicted RP5 latency proxy
                (sum of decode_latency_ms over selected actions);
            (5) tie: most-interpretable model (LightGBM > XGBoost
                > sklearn).
          If best candidate's mean_regret >= mean_regret(always-baseline)
          on router_val (no improvement at all), exit 12 with stderr
          "NO_CANDIDATE_BEATS_BASELINE".
Outputs: selected_router/model.<ext>, selected_router/metadata.json
Stdout:  OK_ROUTER_SELECT:<impl>__<config_id>
Exit:    0 PASS, 1 FAIL, 12 NO_BEAT.
```

`scripts/robust_asr/evaluate_router.py`:

```text
Inputs:  --selected-router <artifacts/robust_asr/router/selected_router>
         --router-test-locked <parquet>
         --out <reports/robust_asr/router/router_final_eval.md>
Behavior: Applies the Section 5 router decision rule to predict
          chosen_action per row. Computes router-driven WER, WA,
          regret, mean_regret, p95_regret, local_only_rate,
          cloud_call_rate, latency, cost.
          Computes paired bootstrap BCa CIs (10000 iterations) for
          mean_regret, WER, local_only_rate, cloud_call_rate, latency.
Stdout:  OK_ROUTER_FINAL_EVAL
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/package_router.py`:

```text
Inputs:  --selected-router <artifacts/robust_asr/router/selected_router>
         --router-config <configs/robust_asr/router_v1.yaml>
         --out <artifacts/robust_asr/router/selected_router>
Behavior: Adds rp5_inference.py with a deterministic predict()
          function that the RP5 runtime can import. Writes
          metadata.json with FEATURES_VERSION, ROUTER_VERSION,
          training data checksum, decision rule constants
          (epsilon_wer, ask_repeat_wer_threshold,
          router_confidence_min). Writes test_vectors.json with at
          least 16 (features, expected predicted_wer per backend,
          expected chosen_action) tuples for runtime regression.
Stdout:  OK_ROUTER_PACKAGE
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/package_deterministic_selector.py`:

```text
Inputs:  --selector-config <configs/robust_asr/router_v1.yaml>
         --out <artifacts/robust_asr/router/selected_router>
Behavior: Writes deterministic_selector.json with the constants and
          predicate from Section 5.5 (Outcome E selector). Adds
          rp5_inference.py wrapping the deterministic predicate.
          Writes test_vectors.json with at least 16 tuples.
Stdout:  OK_DETERMINISTIC_SELECTOR_PACKAGE
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/evaluate_deterministic_selector.py`:

```text
Inputs:  --selector <artifacts/robust_asr/router/selected_router/deterministic_selector.json>
         --selector-test <artifacts/robust_asr/router/selector_evidence.parquet>
         --out <reports/robust_asr/router/selector_final_eval.md>
Behavior: Computes deterministic-selector WER, WA, ask_repeat_rate,
          local_only_rate, cloud_call_rate, latency, cost, and regret
          against always-whisper-base on the selector evidence table.
          If only one transcript-producing backend exists, regret is
          reported as neutral evidence, not as a positive system claim.
Stdout:  OK_SELECTOR_FINAL_EVAL
Exit:    0 PASS, 1 FAIL.
```

### 4.7 System and demo

`scripts/robust_asr/evaluate_system.py`:

```text
Inputs:  --selected-router <artifacts/robust_asr/router/selected_router>
         --backend-tables <list of parquets>
         --baselines <list of action names>
         --profile <balanced | quality_first | local_first>
         --out <reports/robust_asr/system/system_eval.md>
Behavior: Computes paired per-audio_id deltas
          (regret_router_or_selector_i - regret_baseline_i)
          for each declared baseline.
          Runs paired BCa bootstrap (10000 iterations) and Wilcoxon
          signed-rank.
          Sets claims_enabled.positive_system = true if AND ONLY IF:
            mean_regret(router_or_selector) < mean_regret(every
              declared baseline) on router_test_locked or selector_evidence,
            paired BCa 95% CI lower bound for the delta against at
              least one deployed baseline excludes 0,
            no claim depends on a claims_enabled flag that is false
              (cloud_tradeoff or ood_real).
          Else sets positive_system = false.
Outputs: system_eval.md with positive_system on first line.
Stdout:  OK_SYSTEM_EVAL:<true|false>
Exit:    0 PASS, 1 FAIL.
```

`scripts/robust_asr/build_demo_examples.py`:

```text
Inputs:  --eval-manifests <eval_manifests_v1.yaml>
         --reserved-demo <artifacts/robust_asr/manifests/common_voice_demo_reserved.parquet>
                         optional; required only if claims_enabled.ood_real
                         == true.
         --out-manifest <artifacts/robust_asr/demo/demo_examples_manifest.json>
         --out-audio-dir <artifacts/robust_asr/demo/audio>
Behavior: Selects exactly 8 examples:
            1 clean (LibriSpeech-derived public)
            1 cafe_noise (LibriSpeech-derived public)
            1 phone_band (LibriSpeech-derived public)
            1 far_field_room (LibriSpeech-derived public)
            1 muffled_lowpass (LibriSpeech-derived public)
            3 OOD examples:
              if claims_enabled.ood_real == true:
                  3 from common_voice_demo_reserved
              else:
                  3 from public LibriSpeech-derived material disjoint
                  from locked eval; label as ID/OOD-param illustrative.
          Verifies disjointness from all locked eval sets by audio_id
          and audio_sha256.
          Writes manifest entries: audio_id, source, license, family,
          duration_s, audio_sha256, file_path.
Stdout:  OK_DEMO_EXAMPLES with 8 selected.
Exit:    0 PASS, 1 FAIL.
```


### 4.8 Resource resolution helpers

`scripts/robust_asr/resolve_long_running_queue.py`:

```text
Used by the agent when a "longer-running queue" is needed.
Behavior: Calls slurm/tools/on_submit.sh sinfo --noheader \
                  --format='%P %l %a' and parses each row.
          A queue qualifies if:
            availability column == 'up',
            time-limit column parses as >= 48:00:00 OR is 'infinite',
            partition is in the user's allowed_partitions list (read
            from configs/robust_asr/runtime_v1.yaml).
          Prints the first qualifying partition name on stdout.
          If none qualify, exits 13 with stderr
          "NO_LONG_RUNNING_QUEUE_AVAILABLE".
Stdout:  <partition_name> on PASS.
Exit:    0 PASS, 13 NONE.
```

`scripts/robust_asr/probe_assemblyai_runtime.py`:

```text
Used at runtime by the deterministic selector and at P5.1 by the
agent.
Behavior: If ASSEMBLYAI_API_KEY env var is unset, prints
          "ASSEMBLYAI_RUNTIME=false reason=key_unset" and exits 0.
          Else issues an HTTP HEAD or trivial transcript request to
          AssemblyAI with timeout = 5 seconds. If HTTP 200, prints
          "ASSEMBLYAI_RUNTIME=true reason=health_ok". Else prints
          "ASSEMBLYAI_RUNTIME=false reason=<http_status_or_error>".
          Always exits 0 (this script is informational; callers
          decide).
```


## 5. Constants, thresholds, and decision rules

This section consolidates every numeric threshold and decision used elsewhere in the plan. If a task seems to require a threshold that is not here, stop and record `PLAN_CONFLICT`.

### 5.1 Smoke gate thresholds

```text
smoke_global_wa_gain_min        = 0.005
smoke_family_wa_gain_min        = 0.010
smoke_clean_regression_max_pass = 0.010   (WA loss; allowed for SMOKE_PASS)
smoke_clean_regression_max_partial = 0.020 (WA loss; allowed for SMOKE_PARTIAL)
```

Smoke booleans (decide_lora_smoke.py):

```text
SMOKE_PASS = (macro_wa_gain >= 0.005 AND clean_regression <= 0.010)
             OR (max_family_wa_gain >= 0.010 AND clean_regression <= 0.010)

SMOKE_PARTIAL = (NOT SMOKE_PASS
                 AND max_family_wa_gain >= 0.010
                 AND clean_regression <= 0.020)

SMOKE_FAIL = otherwise

HALTED = export smoke failed (EXPORT_BLOCKED) OR data/runtime blocker.
```

### 5.2 Full LoRA outcome thresholds

```text
PASS_GLOBAL:
  macro_WA_gain > 0
  paired BCa 95% CI lower bound > 0.010
  clean_regression <= 0.015 WA loss
  no degradation family WA drop > 0.030 absolute

PASS_SUBSET:
  not PASS_GLOBAL
  at least one family with paired BCa 95% CI lower bound > 0.010
  clean_regression <= 0.015 WA loss
  at most one family with WA drop > 0.030

FAIL_WITH_EVIDENCE:
  not PASS_GLOBAL, not PASS_SUBSET; all artifacts present.

HALTED:
  required artifacts missing; an active BLOCKED_* marker.
```

LoRA router inclusion gate:

```text
include_lora_in_router = true  if Full LoRA in {PASS_GLOBAL, PASS_SUBSET}
                                 AND CT2 INT8 preservation == PASS
                              = false otherwise
```

### 5.3 CT2 INT8 LoRA preservation thresholds

```text
fp_improvement   = baseline_wer - fp_wer
int8_improvement = baseline_wer - int8_wer

Preservation PASS:
  if fp_improvement > 0:
    int8_improvement >= 0.8 * fp_improvement
  if fp_improvement <= 0:
    int8_wer <= fp_wer + 0.005 absolute WER
```

Preservation FAIL does not delete the LoRA result. It blocks LoRA from RP5 router inclusion unless a deployable runtime alternative exists.

### 5.4 Router decision rule and selection

Eligibility plus priority (applied at decision time per audio_id):

```python
best_predicted_wer = min(predicted_wer[a]
                         for a in available_actions_without_ask_repeat)

eligible = {a for a in available_actions_without_ask_repeat
              if predicted_wer[a] <= best_predicted_wer + epsilon_wer}

priority_order = [
    "whisper_base_ct2_int8",
    "whisper_lora_ct2_int8",
    "assemblyai",
]

chosen = first(a for a in priority_order if a in eligible)

if min_predicted_wer > ask_repeat_wer_threshold:
    chosen = "ask_repeat"

if router_confidence < router_confidence_min:
    chosen = "ask_repeat"
```

Constants:

```text
epsilon_wer            = 0.020
ask_repeat_wer_threshold = 0.350
router_confidence_min   = 0.550
```

Cost function:

```text
total_cost = alpha * predicted_WER
           + beta  * normalized_latency
           + gamma * monetary_cost
           + delta * third_party_penalty
```

Profiles (alpha, beta, gamma, delta):

```text
balanced       = (1.0, 0.3, 0.3, 0.3)
quality_first  = (1.0, 0.1, 0.1, 0.1)
local_first    = (1.0, 0.3, 0.3, 0.7)
```

Default demo profile: `balanced`.

Router candidate selection priority:

```text
1. lowest mean_regret on router_val vs always-baseline
2. tie within tolerance_mean_regret = 0.001: lowest p95_regret
3. tie: lowest cloud_call_rate
4. tie: lowest sum decode_latency_ms (RP5 latency proxy)
5. tie: most-interpretable model (LightGBM > XGBoost > sklearn)
```

Degeneracy detection:

```text
For every pair (a, b) of available_backends, compute Pearson r
between predicted_wer[a] and predicted_wer[b] over router_val.
If min over pairs of (1 - r) < 0.10:
  candidate is DEGENERATE.
```

Recovery rule:

```text
1. Retry training once with config.regularization_strong block.
2. If still DEGENERATE and at least one non-degenerate candidate
   exists: record DEGENERATE_ROUTER_RECOVERED, continue with the
   non-degenerate candidate.
3. If all candidates DEGENERATE: train_router_candidates.py exits 11
   ALL_CANDIDATES_DEGENERATE; agent records OUTCOME_E_DETERMINISTIC_SELECTOR.
```

### 5.5 Deterministic selector (Outcome E)

Reference implementation:

```python
def deterministic_select(
    decode_features,
    assemblyai_available=True,
    ask_repeat_threshold=-1.0,
    escalate_threshold=-0.5,
    no_speech_threshold=0.6,
):
    """
    Returns one of: 'whisper_base_ct2_int8', 'assemblyai', 'ask_repeat'.
    If AssemblyAI is unavailable, never returns 'assemblyai'.
    """
    if decode_features.get('no_speech_prob', 0.0) > no_speech_threshold:
        return 'ask_repeat'
    if decode_features.get('avg_logprob', 0.0) < ask_repeat_threshold:
        return 'ask_repeat'
    if assemblyai_available and decode_features.get('avg_logprob', 0.0) < escalate_threshold:
        return 'assemblyai'
    return 'whisper_base_ct2_int8'
```

Constants:

```text
ask_repeat_threshold  = -1.0
escalate_threshold    = -0.5
no_speech_threshold   =  0.6
```

`assemblyai_available` is computed at runtime, never hardcoded:

```text
assemblyai_available = true iff:
  marker BLOCKED_API not active in runtime tracker copy
  AND ASSEMBLYAI_API_KEY env var set
  AND a recent AssemblyAI health check (within
       health_check_ttl_seconds = 300) returned HTTP 200.

Default false on any check failure.
```

Use `scripts/robust_asr/probe_assemblyai_runtime.py` to compute this at training time and at serving time.

Selector parameters and thresholds are tracked under `DETERMINISTIC_SELECTOR_VERSION` in `libs/common/versions.py`.

### 5.6 System evaluation thresholds

```text
positive_system = true iff ALL of:
  mean_regret(chosen) < mean_regret(b) for every declared baseline b
    on router_test_locked,
  paired BCa 95% CI lower bound for at least one
    (regret_chosen - regret_b) excludes 0,
  no claim depends on a disabled claims_enabled flag.

positive_system = false otherwise.
```

Wilcoxon signed-rank is also computed and reported, but does not gate the flag.

### 5.7 Bootstrap policy

```text
bootstrap_iterations = 10000
bootstrap_confidence = 0.95
bootstrap_method     = BCa (default), percentile (fallback)
paired_bootstrap_required_for = full_lora, system_regret, system_wer

LoRA smoke: no strict CI required.
Full LoRA: paired bootstrap CI required.
Router final: bootstrap CI required for WER, regret, cloud_call_rate,
              local_only_rate, latency.
```

If BCa is unavailable in the environment, use paired percentile bootstrap with `bootstrap_method = percentile` recorded in the report and tracker. Do not silently switch methods.

### 5.8 Runtime budgets and OOM/timeout behavior

OOM (CUDA out-of-memory) policy across all training and evaluation scripts:

```text
On first OOM at batch_size = b:
  retry once with batch_size = max(1, b // 2).
On second OOM at the same task:
  if reduced batch_size > 1: retry once with batch_size //= 2 again.
  if reduced batch_size == 1: exit 2 OOM_AT_BATCH_SIZE_1.
On OOM_AT_BATCH_SIZE_1:
  task records HALTED with marker BLOCKED_RUNTIME and stops.
```

Timeout policy:

```text
Per-task wall_clock_seconds is read from the task's config YAML
(eval_timeout_seconds or training_timeout_seconds).
Default eval_timeout_seconds: 1800 (30 minutes per checkpoint eval).
Default training_timeout_seconds: 86400 (24 hours per training run).
On first timeout: retry once with batch_size = max(1, b // 2).
On second timeout: mark unit (checkpoint or run) as TIMED_OUT and skip.
```

Slurm preemption policy:

```text
On SIGTERM (preemption signal):
  before exiting, if a checkpoint save is not already in progress,
  attempt to call torch.save() of the current adapter weights into
  artifacts/robust_asr/lora_full/checkpoint_at_preemption.pt with a
  10-second wall-clock guard. Whether the save lands is best-effort
  (the OS may issue SIGKILL before completion). After the attempt,
  exit 6 PREEMPTED_AT_STEP_<n>.

Agent re-action:
  Requeue once.
  If preempted twice in a row at the same step or earlier:
    call scripts/robust_asr/resolve_long_running_queue.py
    if it returns a partition: switch and retry once.
    if it exits 13 NO_LONG_RUNNING_QUEUE_AVAILABLE:
      record BUDGET_EXCEEDED and trigger Section 5.10 fallback.
```

Per-task wall-clock budgets:

```text
P1.4 build_degradation_v1:        max 21600s/family (6h), max 50 GB scratch
P2.1 baseline whisper:            max 10800s (3h)
P3.1 LoRA smoke train+eval:       max 14400s (4h), max 1 GPU, max 200 steps
P4.1 LoRA full train:             max 86400s (24h), max 1 GPU, max 3 retries
P4.2 LoRA full eval:              max 21600s (6h), max 1 GPU
P4.3 LoRA CT2 INT8 export+eval:   max 7200s (2h)
P5.1 AssemblyAI cache populate:   max 43200s (12h), max API budget per pricing_v1.yaml
P6.1 build_oracle_table:          max 1800s (30min), CPU only
P6.2 extract_router_features:     max 7200s (2h), CPU only
P7.1 train_router_candidates:     max 7200s (2h), CPU only
P7.2 evaluate_router:             max 1800s (30min), CPU only
P8.1 evaluate_system:             max 1800s (30min), CPU only
```

If a budget is exceeded without a usable result, the task records `BUDGET_EXCEEDED` and triggers Section 5.10 fallback.

### 5.9 Corruption and degeneracy detection

Checkpoint corruption:

```text
A checkpoint is CORRUPT iff:
  torch.load(<path>, map_location='cpu') raises any exception
  OR for any tensor t in the loaded state dict:
       not torch.isfinite(t).all()
```

Smoke result degeneracy:

```text
A smoke result is DEGENERATE iff:
  variance over families of (per-family WA gain) == 0.
```

Audio degradation degeneracy:

```text
A degraded audio file is BAD_OUTPUT iff:
  rms_mean of output < 1e-6 (effectively silence)
  OR any sample is NaN
  OR clipping_ratio > 0.5 (> 50% samples at +/- max).
```

Router prediction degeneracy: see Section 5.4.

Macro WA non-monotonicity (informational, not a hard failure):

```text
A training trajectory is NON_MONOTONIC iff:
  there exist checkpoint indices i < j such that
  macro_wa[j] < running_max(macro_wa[0:j+1]) - 0.005.
```

The selection rule (Section 5.4 / Section 5.2) still applies; non-monotonicity is recorded as a diagnostic in the selection report.

### 5.10 Fallback rules

If LoRA smoke FAIL:

```text
Decision_A_smoke.outcome = FAIL.
Skip P4 by setting tasks P4.1, P4.2, P4.3 to SKIPPED_BY_DECISION_A.
Decision_B_lora_full.include_lora_in_router = false.
claims_enabled.positive_lora = false.
Continue to P5. If P5 sets BLOCKED_API:
  claims_enabled.cloud_tradeoff = false; the deployable backend set
  is {whisper_base_ct2_int8} only and Section 5.10 OUTCOME_E rule
  applies.
Else:
  the deployable backend set is {whisper_base_ct2_int8, assemblyai};
  proceed to P6 with router or selector per Section 8 P5 routing.
```

If full LoRA FAIL_WITH_EVIDENCE:

```text
Decision_B_lora_full.include_lora_in_router = false.
Keep LoRA reports as adaptation experiment evidence.
Continue with router if >= 2 transcript-producing deployable backends.
Else record OUTCOME_E_DETERMINISTIC_SELECTOR.
```

If LoRA export EXPORT_BLOCKED but FP LoRA evaluation succeeded:

```text
Decision_B_lora_full.include_lora_in_router = false.
Keep FP LoRA results in experimental report (positive_lora may still
be true if FP gates pass).
Continue with deployable backends.
```

If AssemblyAI BLOCKED_API:

```text
claims_enabled.cloud_tradeoff = false.
If LoRA deployable: train local-only router (Whisper base + LoRA).
If LoRA not deployable AND AssemblyAI blocked: package deterministic
selector in local-only mode, record OUTCOME_E_DETERMINISTIC_SELECTOR.
```

If Common Voice OOD BLOCKED_OOD_PUBLIC:

```text
claims_enabled.ood_real = false.
Try TED-LIUM Release 3 then CHiME-6 dev per Section 1.1.
If none available: continue ID and OOD-param work, disable OOD-real claims.
Do not substitute private recordings.
```

If RP5 unavailable during datamove1:

```text
Record PENDING_RP5_INTEGRATION.
Continue datamove1 reports, runtime contract fixtures, and handoff.
Do not fabricate RP5 latency.
```

If BUDGET_EXCEEDED on P3.1, P4.1, or P5.1:

```text
P3.1: treat as SMOKE_FAIL with reason=BUDGET; trigger Decision_A_smoke=FAIL fallback.
P4.1: treat as HALTED with marker BUDGET_EXCEEDED; if a usable
      checkpoint exists meeting smoke gate, evaluate it; else fall back
      per the LoRA SMOKE_FAIL path.
P5.1: treat as BLOCKED_API; record and continue with cloud_tradeoff=false.
```

Claim rule (orchestrator-owned, not overridden by fallback):

```text
A fallback can preserve product success.
A fallback cannot create a positive experimental claim unless the
locked evaluation gate passes.
```


## 6. Marker definitions (computable predicates)

Every marker referenced anywhere in the plans is defined here with a precise predicate.

| Marker | Active iff | Cleared when | Blocks phase advance |
|---|---|---|---|
| `BLOCKED_SOURCE_BRANCH` | `git rev-parse --verify feature/training-datamove1-v1` fails locally OR on origin | local + origin source branch reachable; rerun P0.0 | yes (blocks P0) |
| `BLOCKED_BRANCH_LINEAGE` | target branch exists but is not a valid descendant or continuation of the approved source branch lineage | target recreated or rebased by explicit orchestrator approval | yes (blocks P0) |
| `PLAN_CONFLICT` | this plan or orchestrator plan disagrees with repository contracts, tests, or each other | orchestrator edits plans and tests pass | yes (current phase) |
| `BLOCKED_RUNTIME` | Apptainer image missing OR Python != 3.11 OR slurm wrapper missing OR required imports missing OR Slurm submit fails | runtime smoke job exits 0; rerun P0.3 | yes (blocks P0 to P1) |
| `ENV_CONSTRAINT` | a documented deviation forced (e.g. timestamps required by a backend) | tracker records the deviation and impacted claims | no, unless metric-affecting |
| `BLOCKED_API` | populate_assemblyai_cache.py exits 8/9/10 OR pricing config missing | API access restored AND cache populated | blocks AssemblyAI backend only |
| `BLOCKED_OOD_PUBLIC` | no Common Voice OR fallback satisfies Section 1.1 predicate | a satisfying public OOD set prepared | blocks final OOD-real claim only |
| `BLOCKED_RP5` | RP5 unavailable for runtime validation during P9 acknowledgment | RP5 reachable AND handoff_validation_<tag>.md exists | blocks portfolio readiness only |
| `EXPORT_BLOCKED` | export_lora_ct2_int8.py exits 5 OR preservation FAIL | a usable CT2 INT8 export AND preservation PASS | blocks LoRA from RP5 router inclusion only |
| `FAIL_WITH_EVIDENCE` | full LoRA neither PASS_GLOBAL nor PASS_SUBSET, all artifacts exist | (informational only; not cleared, used as outcome) | no |
| `PASS_GLOBAL` | full LoRA passes Section 5.2 PASS_GLOBAL predicate | (informational only) | no |
| `PASS_SUBSET` | full LoRA passes Section 5.2 PASS_SUBSET predicate | (informational only) | no |
| `PENDING_PRICING_VERIFICATION` | pricing_v1.yaml lacks `assemblyai_pricing_checked_date` within last 90 days | pricing source URL + checked_date updated within 90 days | no, but limits cost claims |
| `MISSING_EVIDENCE` | a phase gate predicate references an artifact that does not exist | the missing artifact is produced | yes (current phase) |
| `ROUTER_IMPL_FALLBACK_SKLEARN` | LightGBM and XGBoost imports both fail; sklearn HistGradientBoostingRegressor used | (informational only) | no |
| `DEGENERATE_ROUTER_RECOVERED` | at least one router candidate was DEGENERATE per Section 5.4 and was recovered with regularization or sklearn fallback | (informational only) | no |
| `OUTCOME_E_DETERMINISTIC_SELECTOR` | < 2 transcript-producing deployable backends OR train_router_candidates.py exits 11 OR select_router.py exits 12 | (kept active as the outcome) | no, narrows positive_system scope |
| `BUDGET_EXCEEDED` | a Section 5.8 wall-clock or retry budget exceeded without success | (informational only; triggers Section 5.10 fallback) | no, triggers fallback |
| `PENDING_RP5_INTEGRATION` | (P0.1) P0.0 Pre-bootstrap Inventory Report recorded origin/feature/demo-runtime-rp5-v1 missing OR (P10) datamove1 P10 done AND RP5 handoff_validation_<tag>.md missing | RP5 branch reachable AND handoff_validation_<tag>.md exists AND demo URL reachable | no on datamove1; blocks portfolio readiness |


## 7. Tracker schema

Two files, one source of truth.

```text
docs/progress/robust_asr_progress.md             narrative state
docs/progress/robust_asr_progress.yaml           machine state
docs/progress/robust_asr_state_capsule.md        compact state exported for ChatGPT review
```

Minimum YAML shape:

```yaml
project: robust_asr_lora_router
branch: feature/robust-asr-lora-router-datamove1-v1
source_branch: feature/training-datamove1-v1
project_status: IN_PROGRESS   # IN_PROGRESS | COMPLETE
current_phase: P0
current_task: P0.0
last_completed_task: null

blocked: false
blocker: null

lora_status: NOT_STARTED       # NOT_STARTED | IN_PROGRESS | DONE
router_status: NOT_STARTED
system_status: NOT_STARTED

normalization_version: null
features_version: null
router_version: null
lora_version: null
deterministic_selector_version: null
degradation_version: null
metrics_version: null

training_selection_baseline: whisper_base_ct2_int8
product_baseline: whisper_base_ct2_int8

artifact_root: artifacts/robust_asr
handoff_root: artifacts/robust_asr/handoff

markers: []

claims_enabled:
  ood_real: true            # set to false when BLOCKED_OOD_PUBLIC
  cloud_tradeoff: true      # set to false when BLOCKED_API
  positive_lora: pending    # true | false | pending until P4.2
  positive_system: pending  # true | false | pending until P8.1

session_log:
  current_session_id: null
  continue_without_per_task_plan_approval: false
  continue_without_per_task_closure_approval: false
  continue_through_gates: false
  parallel_sessions_active: []

state_transport:
  latest_state_capsule: docs/progress/robust_asr_state_capsule.md
  latest_planning_report: null
  latest_execution_report: null
  latest_phase_gate_report: null
  latest_supplemental_evidence_report: null
  latest_approval_packet: null
  last_accepted_report_commit: null
  expected_next_task: P0.0
  last_tracker_mismatch: null

phase_summary:
  P0: null   # one-line summary written by agent at gate
  P1: null
  P2: null
  P3: null
  P4: null
  P5: null
  P6: null
  P7: null
  P8: null
  P9: null
  P10: null

orchestrator_approvals:
  P0: null   # APPROVED | RE_EXECUTE | CHANGE_SCOPE plus reason
  P1: null
  P2: null
  P3: null
  P4: null
  P5: null
  P6: null
  P7: null
  P8: null
  P9: null
  P10: null

profile:
  active_profile_path: docs/profiles/CLAUDE.robust_asr.md
  active_profile_sha256: null
  claude_md_block_sha256: null
  claude_md_block_installed: false
  gitattributes_merge_ours_set: false

repo_integration:
  source_branch_lineage_verified: false
  legacy_trackers_classified: false
  legacy_plans_classified: false
  claude_md_preserved_outside_block: false
  reuse_policy_path: configs/robust_asr/reuse_policy_v1.yaml
  repo_integration_policy_path: reports/robust_asr/repo_integration_policy.md
  touch_policy_path: reports/robust_asr/touch_policy.md
  unclassified_paths_default_no_touch: true
  existing_repo_root_confirmed: /mnt/fast/nobackup/users/gb0048/asr_enhancement

evidence:
  P0.0: { base_commit: null, branch_state: null, marker: null, unblock_condition: null }

artifacts:
  state_capsule:          { path: docs/progress/robust_asr_state_capsule.md, sha256: null, produced_by_task: P0.1 }
  task_reports_root:      { path: reports/robust_asr/task_reports, sha256: null, produced_by_task: P0.1 }
  repository_inventory:    { path: reports/robust_asr/repository_inventory.md, sha256: null, produced_by_task: P0.1 }
  asset_inventory:         { path: reports/robust_asr/asset_inventory.md, sha256: null, produced_by_task: P0.2 }
  repo_integration_policy: { path: reports/robust_asr/repo_integration_policy.md, sha256: null, produced_by_task: P0.2 }
  touch_policy:            { path: reports/robust_asr/touch_policy.md, sha256: null, produced_by_task: P0.2 }
  reuse_policy_config:     { path: configs/robust_asr/reuse_policy_v1.yaml, sha256: null, produced_by_task: P0.2 }
  validate_report_shape_script:
                           { path: scripts/robust_asr/validate_report_shape.py, sha256: null, produced_by_task: P0.2,
                             last_emit: null }
  report_shape_fixtures:   { path: artifacts/robust_asr/state_packets/report_shape_fixtures, sha256: null, produced_by_task: P0.2,
                             schemas_covered: [prebootstrap_inventory_report, planning_report, execution_report, phase_gate_report, approval_packet, supplemental_evidence_report] }
  runtime_smoke_report:    { path: reports/robust_asr/runtime_smoke.md, sha256: null, produced_by_task: P0.3 }
  runtime_contract_fixture:
                           { path: reports/robust_asr/runtime_contract_smoke.md, sha256: null, produced_by_task: P0.4,
                             contract_skeleton_validation_passed: false,
                             contract_final_validation_passed: false }
  model_card_template:     { path: docs/reports/robust_asr/model_card_lora.md, sha256: null, produced_by_task: P0.5 }
  router_card_template:    { path: docs/reports/robust_asr/router_card.md, sha256: null, produced_by_task: P0.5 }
  manifest_summary:        { path: reports/robust_asr/manifest_summary.md, sha256: null, produced_by_task: P1.3 }
  baseline_table:          { path: artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet, sha256: null, rows: null, produced_by_task: P2.1 }
  baseline_report:         { path: reports/robust_asr/baseline_whisper_base.md, sha256: null, produced_by_task: P2.1 }
  lora_smoke_report:       { path: reports/robust_asr/lora/lora_smoke_report.md, sha256: null, produced_by_task: P3.1 }
  decision_a_report:       { path: reports/robust_asr/lora/decision_a_smoke.md, sha256: null, produced_by_task: P3.2 }
  full_lora_table:         { path: artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet, sha256: null, rows: null, produced_by_task: P4.2 }
  full_lora_report:        { path: reports/robust_asr/lora/full_lora_eval.md, sha256: null, produced_by_task: P4.2 }
  lora_int8_table:         { path: artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet, sha256: null, rows: null, produced_by_task: P4.3 }
  preservation_report:     { path: reports/robust_asr/lora/lora_ct2_int8_preservation.md, sha256: null, produced_by_task: P4.3 }
  assemblyai_table:        { path: artifacts/robust_asr/eval_tables/assemblyai.parquet, sha256: null, rows: null, produced_by_task: P5.1 }
  oracle_table:            { path: artifacts/robust_asr/oracle/oracle_table.parquet, sha256: null, rows: null, produced_by_task: P6.1 }
  selector_evidence_table: { path: artifacts/robust_asr/router/selector_evidence.parquet, sha256: null, rows: null, produced_by_task: P6.1 }
  router_features:         { path: artifacts/robust_asr/router/router_features.parquet, sha256: null, produced_by_task: P6.2 }
  router_matrices:         { train: null, val: null, test_locked: null, produced_by_task: P6.2 }
  router_package:          { path: artifacts/robust_asr/router/selected_router, sha256: null, kind: null, produced_by_task: P7.3 }
  system_eval_report:      { path: reports/robust_asr/system/system_eval.md, sha256: null, produced_by_task: P8.1 }
  demo_examples_manifest:  { path: artifacts/robust_asr/demo/demo_examples_manifest.json, sha256: null, produced_by_task: P8.2 }
  final_runtime_contract:  { path: artifacts/robust_asr/runtime_contract/final_response_schema.json, sha256: null, produced_by_task: P9.0 }
  handoff_package:         { path: artifacts/robust_asr/handoff, sha256: null, tag: null, produced_by_task: P9.1 }
  rp5_runtime_spec:        { path: artifacts/robust_asr/handoff/rp5_runtime_spec.md, sha256: null, produced_by_task: P9.2 }
  final_verification:      { path: reports/robust_asr/final_verification.md, sha256: null, produced_by_task: P10.1 }
  final_asset_audit:       { path: reports/robust_asr/final_asset_audit.md, sha256: null, produced_by_task: P10.2 }
  plan_tracker_consistency: { path: reports/robust_asr/plan_tracker_consistency.md, sha256: null, produced_by_task: P10.3 }

decisions:
  Decision_A_smoke:
    outcome: null              # PASS | PARTIAL | FAIL | HALTED
    decided_at_task: P3.2
  Decision_B_lora_full:
    outcome: null              # PASS_GLOBAL | PASS_SUBSET | FAIL_WITH_EVIDENCE | HALTED
    preservation_outcome: null # PASS | FAIL | EXPORT_BLOCKED
    include_lora_in_router: null  # true | false
    decided_at_task: P4.2
  Decision_C_router_choice:
    kind: null                 # ml_router | deterministic_selector
    selected_impl: null        # lightgbm | xgboost | sklearn | deterministic
    decided_at_task: P7.1
  Decision_D_positive_system:
    outcome: null              # true | false
    decided_at_task: P8.1
```

Per-task entry shape:

```yaml
task_id:
  status: PASS | PARTIAL | FAIL | HALTED | SKIPPED_BY_DECISION_A | SKIPPED_BY_OUTCOME_E | in_progress
  commit: <sha_or_null>
  files_changed: []
  commands_run: []
  key_outputs: []
  marker: null
  next_task: <task_id>
```

Status semantics:

```text
PASS                  task ran, Verification block passed.
PARTIAL               task ran with documented limitation; next task
                       may proceed if its Preconditions allow it.
FAIL                  task ran, experimental result failed an evidence
                       threshold; result preserved as evidence.
HALTED                task could not run (env, runtime, data, branch
                       blocker); active BLOCKED_* marker required.
SKIPPED_BY_DECISION_A reserved for P4 tasks deliberately skipped after
                       Decision A == FAIL.
SKIPPED_BY_OUTCOME_E  reserved for router-only tasks deliberately skipped
                       because OUTCOME_E_DETERMINISTIC_SELECTOR is active.
in_progress           task running asynchronously (Slurm or API).
                       Must transition to terminal status before the
                       task is treated as complete.
```

Tracker rules:

```text
1. Read the tracker first at the start of every session.
2. Update the tracker last before commit.
3. If a numbered task ID is added, removed, renamed, or split, update
   Section 9 task list, Section 8 phase gates, the orchestrator plan
   Section 4, and the tracker YAML in the same commit. Tracker
   narrative substeps `<task_id>a`, `<task_id>b` do not count.
4. Do not leave plans and tracker inconsistent.
```


## 8. Phase gate predicates

Each phase gate is a binary predicate. The agent evaluates it after the last task in the phase. On PASS, the agent writes `phase_summary.<P_n>: PASS, ...` and stops for orchestrator approval. On FAIL, the agent writes `phase_summary.<P_n>: FAIL, ...` and stops.

This section is the single source of truth for advance/return routing. The orchestrator plan Section 4 has the narrative version.

### P0 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P0.0, P0.1, P0.2, P0.3, P0.4, P0.5].status == PASS
  reports/robust_asr/repository_inventory.md exists
  reports/robust_asr/asset_inventory.md exists
  reports/robust_asr/repo_integration_policy.md exists
  reports/robust_asr/touch_policy.md exists
  configs/robust_asr/reuse_policy_v1.yaml exists
  tracker.repo_integration.legacy_trackers_classified == true
  tracker.repo_integration.legacy_plans_classified == true
  tracker.repo_integration.unclassified_paths_default_no_touch == true
  scripts/robust_asr/validate_report_shape.py exists
  validate_report_shape.py emits OK_REPORT_SHAPE on the report fixtures
  reports/robust_asr/runtime_smoke.md exists
  artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json
    parses and meta.exit_code == 0
  artifacts/robust_asr/runtime_contract/rp5_request_fixture.json exists
  artifacts/robust_asr/runtime_contract/rp5_response_fixture.json exists
  reports/robust_asr/runtime_contract_smoke.md exists
  docs/reports/robust_asr/model_card_lora.md exists with at least 10
    TODO_FILLED_IN_<task_id> placeholders
  docs/reports/robust_asr/router_card.md exists with at least 8
    TODO_FILLED_IN_<task_id> placeholders
  CLAUDE.md contains exactly one ROBUST_ASR_PROFILE block
  CLAUDE.md robust block body equals docs/profiles/CLAUDE.robust_asr.md
  tracker.profile.claude_md_block_installed == true
  .gitattributes does not contain "CLAUDE.md merge=ours"
  tracker.profile.gitattributes_merge_ours_set == false
  tracker.artifacts.runtime_contract_fixture.contract_skeleton_validation_passed == true
  no active marker in {BLOCKED_SOURCE_BRANCH, BLOCKED_RUNTIME, PLAN_CONFLICT}

ROUTING:
  on PASS: phase_summary.P0 = PASS; stop, request orchestrator approval.
           on APPROVED: advance to P1.1.
  on FAIL: phase_summary.P0 = FAIL; return to the failed P0 task.
```

### P1 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P1.1, P1.2, P1.4].status == PASS
  tracker.tasks[P1.3].status in {PASS, PARTIAL}
  pytest tests/robust_asr/test_eval_schema.py PASS
  pytest tests/robust_asr/test_normalization_metrics.py PASS
  pytest tests/robust_asr/test_leakage.py PASS
  pytest tests/robust_asr/test_degradation_v1.py PASS
  artifacts/robust_asr/manifests/librispeech_lora_train.parquet,
    librispeech_router_train.parquet, and the validation/locked-test
    parquets exist with checksums recorded
  one of:
    artifacts/robust_asr/manifests/common_voice_ood_locked.parquet
      exists with checksum (claims_enabled.ood_real = true)
    OR an approved fallback (TED-LIUM, CHiME-6) per Section 1.1 with
      checksum (claims_enabled.ood_real = true)
    OR marker BLOCKED_OOD_PUBLIC active AND claims_enabled.ood_real == false
  no active marker in {MISSING_EVIDENCE, PLAN_CONFLICT}

ROUTING:
  on PASS: stop, request orchestrator approval; on APPROVED, advance to P2.1.
  on FAIL: return to the failed P1 task.
```

### P2 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P2.1, P2.2].status == PASS
  artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet exists
    with checksum AND validate_eval_table.py emits OK_EVAL_TABLE
  reports/robust_asr/baseline_whisper_base.md exists
  configs/robust_asr/lora_smoke.yaml exists and references valid
    manifests
  no active marker in {MISSING_EVIDENCE, PLAN_CONFLICT}

ROUTING:
  on PASS: stop, request approval; on APPROVED, advance to P3.1.
  on FAIL: return to the failed P2 task.
```

### P3 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P3.1].status in {PASS, PARTIAL, FAIL}
  tracker.tasks[P3.2].status == PASS
  reports/robust_asr/lora/lora_smoke_report.md exists with first line
    in {PASS, PARTIAL, FAIL, HALTED}
  reports/robust_asr/lora/decision_a_smoke.md exists
  tracker.decisions.Decision_A_smoke.outcome in {PASS, PARTIAL, FAIL, HALTED}
  no active marker in {BLOCKED_RUNTIME, MISSING_EVIDENCE, PLAN_CONFLICT}

ROUTING:
  if Decision_A_smoke.outcome in {PASS, PARTIAL}:
    stop, request approval; on APPROVED, advance to P4.1.
  if Decision_A_smoke.outcome == FAIL:
    set tracker.tasks[P4.1, P4.2, P4.3].status = SKIPPED_BY_DECISION_A
    set Decision_B_lora_full.include_lora_in_router = false
    set claims_enabled.positive_lora = false
    stop, request approval; on APPROVED, advance to P5.1.
  if P3.1.status == HALTED OR Decision_A_smoke.outcome == HALTED:
    gate FAIL; stop with active BLOCKED_* or EXPORT_BLOCKED marker.
```

### P4 gate

```text
PREDICATE PASS iff exactly one of:

Branch A (LoRA executed and exported):
  tracker.tasks[P4.1, P4.2, P4.3].status == PASS
  reports/robust_asr/lora/full_lora_eval.md outcome in
    {PASS_GLOBAL, PASS_SUBSET, FAIL_WITH_EVIDENCE, HALTED}
  reports/robust_asr/lora/lora_ct2_int8_preservation.md outcome in
    {PASS, FAIL, EXPORT_BLOCKED}
  Decision_B_lora_full.include_lora_in_router in {true, false}
  claims_enabled.positive_lora in {true, false}

Branch B (LoRA skipped by Decision A):
  tracker.tasks[P4.1, P4.2, P4.3].status == SKIPPED_BY_DECISION_A
  Decision_B_lora_full.include_lora_in_router == false
  claims_enabled.positive_lora == false

Branch C (full LoRA executed but export or preservation blocked):
  tracker.tasks[P4.1, P4.2].status == PASS
  tracker.tasks[P4.3].status == HALTED
  marker EXPORT_BLOCKED active OR preservation outcome == FAIL
  Decision_B_lora_full.include_lora_in_router == false
  claims_enabled.positive_lora may be true or false (FP evidence preserved)

ROUTING:
  on Branch A or B PASS AND tracker.tasks[P5.1].status NOT IN
      {PASS, PARTIAL, HALTED, in_progress} AND marker BLOCKED_API NOT active:
    stop, request approval; on APPROVED, advance to P5.1.
  on Branch A or B PASS AND tracker.tasks[P5.1].status IN
      {PASS, PARTIAL, HALTED} OR marker BLOCKED_API active:
    stop, request approval; on APPROVED, advance to P6.1.
  on Branch A or B PASS AND tracker.tasks[P5.1].status == in_progress:
    stop, do not advance; wait for P5.1 to terminate, next session re-reads
    tracker and routes accordingly.
  on Branch C PASS:
    stop, request approval; on APPROVED, advance to P5.1 if not yet
    attempted, else P6.1.
  on FAIL: return to the failed P4 task.
```

### P5 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P5.1].status in {PASS, PARTIAL, HALTED}
  one of:
    artifacts/robust_asr/eval_tables/assemblyai.parquet exists with
      checksum AND validate_eval_table.py emits OK_EVAL_TABLE
    OR marker BLOCKED_API active AND claims_enabled.cloud_tradeoff == false

ROUTING:
  on PASS AND fewer than 2 transcript-producing deployable backends remain:
    record OUTCOME_E_DETERMINISTIC_SELECTOR.
    stop, request approval.
    on APPROVED, advance to P6.1 selector evidence path.
  on PASS AND >= 2 transcript-producing deployable backends remain:
    stop, request approval.
    on APPROVED, advance to P6.1 oracle path.
  on FAIL: return to P5.1.

Backend count predicate:
  transcript_producing_deployable = {whisper_base_ct2_int8}
  if Decision_B_lora_full.include_lora_in_router == true:
    + whisper_lora_ct2_int8
  if claims_enabled.cloud_tradeoff == true AND BLOCKED_API not active:
    + assemblyai
  count == |transcript_producing_deployable|
```

### P6 gate

```text
PREDICATE PASS iff one of:

Branch A (router matrix path):
  tracker.tasks[P6.1, P6.2].status == PASS
  marker OUTCOME_E_DETERMINISTIC_SELECTOR not active
  artifacts/robust_asr/oracle/oracle_table.parquet exists with checksum
    AND validate_oracle_table.py emits OK_ORACLE_TABLE
  artifacts/robust_asr/router/router_train.parquet,
    router_val.parquet, router_test_locked.parquet exist with checksums
    AND validate_router_matrices.py emits OK_ROUTER_MATRICES
  pytest tests/robust_asr/test_leakage.py PASS

Branch B (selector evidence path):
  marker OUTCOME_E_DETERMINISTIC_SELECTOR active
  tracker.tasks[P6.1].status == PASS
  tracker.tasks[P6.2].status == SKIPPED_BY_OUTCOME_E
  artifacts/robust_asr/router/selector_evidence.parquet exists with checksum
    AND validate_selector_evidence.py emits OK_SELECTOR_EVIDENCE

ROUTING:
  Branch A PASS:
    stop, request approval; on APPROVED, advance to P7.1.
  Branch B PASS:
    stop, request approval; on APPROVED, advance to P7.3.
  on FAIL:
    return to the failed P6 task, except do not unskip P6.2 while
    OUTCOME_E_DETERMINISTIC_SELECTOR is active.
```

### P7 gate

```text
PREDICATE PASS iff one of:

Branch A (ML router selected):
  tracker.tasks[P7.1, P7.2, P7.3].status == PASS
  artifacts/robust_asr/router/selected_router/ contains
    model artifact, metadata.json, test_vectors.json, rp5_inference.py
  reports/robust_asr/router/router_final_eval.md exists with regret
    confidence intervals
  pytest tests/robust_asr/test_router_runtime.py PASS

Branch B (deterministic selector selected):
  marker OUTCOME_E_DETERMINISTIC_SELECTOR active
  tracker.tasks[P7.3].status == PASS
  tracker.tasks[P7.1].status in {SKIPPED_BY_OUTCOME_E, PASS, FAIL, HALTED, null}
  tracker.tasks[P7.2].status in {SKIPPED_BY_OUTCOME_E, PASS, null}
  artifacts/robust_asr/router/selected_router/deterministic_selector.json
    exists
  artifacts/robust_asr/router/selected_router/rp5_inference.py exists
  pytest tests/robust_asr/test_router_runtime.py PASS

ROUTING:
  on PASS: stop, request approval; on APPROVED, advance to P8.1.
  on FAIL: return to the failed P7 task.
```

### P8 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P8.1, P8.2].status == PASS
  reports/robust_asr/system/system_eval.md exists with paired test
    results AND positive_system on first line
  tracker.claims_enabled.positive_system in {true, false}
  artifacts/robust_asr/demo/demo_examples_manifest.json exists with
    disjointness proof
  pytest tests/robust_asr/test_leakage.py PASS

ROUTING:
  on PASS: stop, request approval; on APPROVED, advance to P9.0.
  on FAIL: return to the failed P8 task.
```

### P9 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P9.0, P9.1, P9.2].status == PASS
  artifacts/robust_asr/runtime_contract/final_request_schema.json exists
  artifacts/robust_asr/runtime_contract/final_response_schema.json exists
  validate_runtime_contract.py --strict-final emits OK_CONTRACT_FINAL
  artifacts/robust_asr/handoff/README.md exists with the 8 numbered
    sections from P9.1 in order
  verify_handoff_package.py --strict emits OK_HANDOFF_PACKAGE
  artifacts/robust_asr/handoff/handoff_smoke.py and
    rollback_to_previous_handoff.py exist and are executable
  artifacts/robust_asr/handoff/rp5_runtime_spec.md exists
  a tag of the form handoff/<date>-<short_sha> exists locally and on
    origin

ROUTING:
  on PASS: stop, request approval; on APPROVED, advance to P10.1.
  on FAIL: return to the failed P9 task.
```

### P10 gate

```text
PREDICATE PASS iff:
  tracker.tasks[P10.1, P10.2, P10.3].status == PASS
  reports/robust_asr/final_verification.md exists
  reports/robust_asr/final_asset_audit.md exists
  reports/robust_asr/plan_tracker_consistency.md result: PASS
  pytest tests/robust_asr/ PASS
  no secret tokens in repo:
    grep -rE 'ASSEMBLYAI_API_KEY|sk_|Bearer ' --exclude-dir=.git
      returns no matches in tracked files
  git status --short returns 0 lines
  git rev-parse HEAD == git rev-parse origin/feature/robust-asr-lora-router-datamove1-v1

ROUTING:
  on PASS: tracker.project_status = COMPLETE; stop, request final
           orchestrator confirmation. Section 9 (final definition of
           done) is satisfied.
  on FAIL: return to the failed final verification step.
```



## 9. Tasks (P0.0 through P10.3)

Every task entry has the same shape: Preconditions, Actions, Required deliverables, Done when, Verification, Decision rules (where applicable), Stop condition.

A task's "Done when" predicate is the only binary check the agent uses to mark `status: PASS` for that task.

### P0. Bootstrap and skeleton

#### P0.0 Pre-bootstrap inventory and source-branch validation

```text
Mode:
  BOOTSTRAP_NO_TRACKER only. This is the only task allowed before
  docs/progress/robust_asr_progress.yaml exists.

Preconditions:
  - Repository accessible at /mnt/fast/nobackup/users/gb0048/asr_enhancement.
  - docs/progress/robust_asr_progress.yaml does not exist OR the user
    explicitly requests a pre-bootstrap recheck before P0.1.

Actions:
  1. Do not edit files inside the repository. Do not create branches. Do
     not create the tracker. Do not commit or push.
  2. Run: git fetch origin
  3. Run: git rev-parse --verify feature/training-datamove1-v1
  4. Run: git rev-parse --verify origin/feature/training-datamove1-v1
  5. Run (inventory only, non-blocking):
       git rev-parse --verify origin/feature/demo-runtime-rp5-v1
     Capture the SHA on success or the exact error on failure.
  6. Capture: HEAD SHA of feature/training-datamove1-v1, git status,
     remote URL, present top-level directories, and whether any
     robust_asr tracker already exists.
  7. Return a Pre-bootstrap Inventory Report in chat using
     docs/plans/state_packet_schemas_v1.yaml > prebootstrap_inventory_report.
     The report must include a "RP5 runtime branch" field with either
     the observed SHA or the exact error from step 5.

Required deliverables:
  - No committed repository deliverables in P0.0.
  - Pre-bootstrap Inventory Report in chat.

Done when:
  Steps 3 and 4 both exit 0 AND the Pre-bootstrap Inventory Report
  contains the RP5 branch SHA or recorded absence. Step 5 success is not
  required for PASS.

Verification:
  git rev-parse --verify feature/training-datamove1-v1
  git rev-parse --verify origin/feature/training-datamove1-v1

Decision rules:
  1. If step 3 fails: prebootstrap_status = HALTED,
     marker_to_record_in_p0_1 = null. Return the exact missing local
     branch error and stop. P0.1 is not legal from this report.
  2. If step 4 fails: prebootstrap_status = HALTED,
     marker_to_record_in_p0_1 = null. Return the exact missing origin
     reference error and stop. P0.1 is not legal from this report.
  3. If steps 3 and 4 succeed and step 5 succeeds: prebootstrap_status =
     PASS, next_task = P0.1, rp5_branch_state = present, record the SHA
     in the report.
  4. If steps 3 and 4 succeed and step 5 fails: prebootstrap_status =
     PASS, next_task = P0.1, rp5_branch_state = missing, record the
     exact error in the report. P0.1 will activate
     PENDING_RP5_INTEGRATION in the tracker after creating it.

Stop condition:
  After returning the Pre-bootstrap Inventory Report. Do not create the
  target branch in this task.
```

#### P0.1 Create target branch and tracker, install profile

```text
Preconditions:
  - P0.0 Pre-bootstrap Inventory Report has prebootstrap_status = PASS.
  - The P0.0 report shows feature/training-datamove1-v1 and
    origin/feature/training-datamove1-v1 are reachable.
  - No robust_asr tracker exists yet, or the user explicitly approved
    P0.1 bootstrap recovery.

Actions:
  1. Run git fetch origin.
  2. Resolve source and target branch exactly as Section 2
     "Deterministic target branch resolution" defines.
  3. If resolution halts with BLOCKED_BRANCH_LINEAGE or PLAN_CONFLICT,
     write the block report and stop before editing files.
  4. Create the directory tree from Section 2.
  5. Write docs/profiles/CLAUDE.robust_asr.md with the project profile
     (audience: robust_asr_lora_router; pointers to both plan files
     and tracker; rules from this file Section 0, Section 0.1,
     Section 2.1, and Section 2.2).
  6. Update CLAUDE.md using only the Section 2.2 ROBUST_ASR_PROFILE
     block rule:
       - if CLAUDE.md does not exist, create it with repository-level
         preface plus the robust_asr block;
       - if the block exists, replace only the block body;
       - if the block does not exist, append the block;
       - preserve every line outside the block exactly.
  7. Do not add CLAUDE.md merge=ours to .gitattributes. If
     .gitattributes already contains a CLAUDE.md merge=ours rule, remove
     that rule unless removing it would touch unrelated lines; in that
     case halt with PLAN_CONFLICT and write
     reports/robust_asr/claude_md_merge_policy_block.md.
  8. Write reports/robust_asr/repository_inventory.md from the P0.0
     Pre-bootstrap Inventory Report and the current branch resolution
     observations. Include a "RP5 runtime branch" subsection with the
     SHA or recorded absence from P0.0.
  9. Compute SHA-256 of docs/profiles/CLAUDE.robust_asr.md and write it
     to tracker.profile.active_profile_sha256.
 10. Compute SHA-256 of the installed ROBUST_ASR_PROFILE block body in
     CLAUDE.md and write it to tracker.profile.claude_md_block_sha256.
 11. Initialize docs/progress/robust_asr_progress.yaml with the
     Section 7 schema (project_status: IN_PROGRESS, current_phase: P0,
     current_task: P0.2, claims_enabled defaults, repo_integration
     defaults).
 12. Initialize docs/progress/robust_asr_progress.md with a one-page
     project state stub.
 13. Initialize docs/progress/robust_asr_state_capsule.md with branch,
     HEAD, current_phase, current_task, active markers, latest reports,
     and next expected Claude prompt.
 14. Create reports/robust_asr/task_reports/.
 15. If the P0.0 report recorded RP5 branch absence, activate
     PENDING_RP5_INTEGRATION in the newly created tracker. If P0.0
     recorded a SHA, record that SHA under tracker.evidence.P0.0.
 16. Record tracker.tasks[P0.0].status = PASS and
     tracker.tasks[P0.1].status = PASS only after this task's
     Verification block passes.
 17. Commit: "robust_asr P0.1: branch, profile, tracker bootstrap".
 18. Push target branch to origin.

Required deliverables:
  - feature/robust-asr-lora-router-datamove1-v1 branch on origin
  - docs/profiles/CLAUDE.robust_asr.md
  - CLAUDE.md containing exactly one BEGIN ROBUST_ASR_PROFILE block
    and exactly one END ROBUST_ASR_PROFILE block
  - reports/robust_asr/repository_inventory.md
  - docs/progress/robust_asr_progress.yaml (Section 7 schema)
  - docs/progress/robust_asr_progress.md
  - docs/progress/robust_asr_state_capsule.md
  - reports/robust_asr/task_reports/
  - All directories from Section 2
  - reports/robust_asr/branch_lineage_block.md only if halted

Done when:
  - git rev-parse --verify feature/robust-asr-lora-router-datamove1-v1
    AND git rev-parse --verify origin/feature/robust-asr-lora-router-datamove1-v1
  - current branch is feature/robust-asr-lora-router-datamove1-v1
  - target branch satisfies the Section 2 lineage predicate
  - docs/progress/robust_asr_progress.yaml parses and current_task == P0.2
  - docs/progress/robust_asr_state_capsule.md exists and contains current_task: P0.2
  - CLAUDE.md has exactly one BEGIN ROBUST_ASR_PROFILE line and one
    END ROBUST_ASR_PROFILE line
  - the installed CLAUDE.md robust block body equals
    docs/profiles/CLAUDE.robust_asr.md byte-for-byte
  - tracker.profile.active_profile_sha256 equals sha256 of
    docs/profiles/CLAUDE.robust_asr.md
  - tracker.profile.claude_md_block_installed == true
  - reports/robust_asr/repository_inventory.md exists and contains
    "RP5 runtime branch"
  - .gitattributes does not contain "CLAUDE.md merge=ours"

Verification:
  git fetch origin
  git branch --show-current
  git rev-parse --verify feature/robust-asr-lora-router-datamove1-v1
  git rev-parse --verify origin/feature/robust-asr-lora-router-datamove1-v1
  git merge-base --is-ancestor feature/training-datamove1-v1 feature/robust-asr-lora-router-datamove1-v1     || grep -q "P0.1" docs/progress/robust_asr_progress.yaml
  python -c "import yaml; yaml.safe_load(open('docs/progress/robust_asr_progress.yaml'))"
  test -f docs/progress/robust_asr_state_capsule.md
  grep -q "current_task: P0.2" docs/progress/robust_asr_state_capsule.md
  test "$(grep -c '^BEGIN ROBUST_ASR_PROFILE$' CLAUDE.md)" = "1"
  test "$(grep -c '^END ROBUST_ASR_PROFILE$' CLAUDE.md)" = "1"
  python - <<'PYCODE'
from pathlib import Path
claude = Path('CLAUDE.md').read_text()
profile = Path('docs/profiles/CLAUDE.robust_asr.md').read_text()
body = claude.split('BEGIN ROBUST_ASR_PROFILE\n', 1)[1].split('\nEND ROBUST_ASR_PROFILE', 1)[0]
assert body == profile
PYCODE
  ! grep -q "CLAUDE.md merge=ours" .gitattributes

Decision rules:
  1. If preserving CLAUDE.md outside the robust block cannot be verified,
     status = HALTED, marker = PLAN_CONFLICT, write
     reports/robust_asr/profile_install_block.md, and stop.
  2. If lineage verification fails, status = HALTED,
     marker = BLOCKED_BRANCH_LINEAGE, and stop.

Stop condition:
  After commit and push of the bootstrap commit, or immediately after
  writing a branch-lineage or profile-install block report.
```

#### P0.2 Inventory existing assets and lock reuse policy

```text
Preconditions:
  - P0.1 PASS.
  - docs/progress/robust_asr_progress.yaml exists.
  - CLAUDE.md robust block installed and verified.

Actions:
  1. Inventory existing repo state without editing it:
       - plan.md
       - docs/plans/*.md
       - docs/progress/*progress*.md
       - docs/progress/*progress*.yaml
       - docs/claude_task_progress.*
       - CLAUDE.md outside the ROBUST_ASR_PROFILE block
       - services/api/**
       - services/worker/**
       - libs/asr_adapter/**
       - libs/audio_pipeline/**
       - libs/audio/**
       - libs/common/**
       - infra/**
       - scripts/demo/**
       - scripts/training/**
       - slurm/tools/**
       - slurm/jobs/**
       - tests/**
       - configs/**
  2. Inventory candidate runtime and data assets without validating them
     as robust_asr evidence:
       - dataset roots reachable on the host;
       - prior AssemblyAI cache directories;
       - prior LoRA checkpoints or run directories;
       - prior pricing configs;
       - prior demo fixtures;
       - Apptainer image candidate;
       - Slurm submit wrapper candidate.
  3. For every candidate, record path, class, size, modification time,
     git-tracked status, large-artifact status, and whether committing
     is allowed.
  4. Write reports/robust_asr/asset_inventory.md with observation only.
     The report must not grant reuse permission.
  5. Write reports/robust_asr/repo_integration_policy.md with four
     tables in this order:
       A. Active robust_asr state paths.
       B. Legacy state paths and their read-only status.
       C. Reusable implementation paths and required approval mode.
       D. Mandatory no-touch paths.
  6. Write configs/robust_asr/reuse_policy_v1.yaml with one row per
     classified path group using Section 2.2 fields. Apply these
     binding classification rules:
       - Existing trackers (docs/progress/training_datamove1_progress.*,
         docs/claude_task_progress.*) and existing plans (plan.md,
         docs/plans/demo_platform_plan.md, docs/plans/training_datamove1_plan.md)
         must be classified with class: legacy_state, permitted_use:
         read_only, commit_allowed: false. They must not be classified
         as forbidden, because P10.3 plan_tracker_consistency must read
         them.
       - Mandatory no-touch paths from Section 2.2 (.git/**, .env,
         .env.*, *.key, *.pem, *.token, runs/**, .cache/**, .hf_cache/**,
         **/__pycache__/**, *.wav, *.flac, *.mp3, *.m4a, *.pt, *.pth,
         *.ckpt, *.bin, *.safetensors) must be classified as class:
         no_touch, permitted_use: forbidden.
       - Existing runtime code paths under services/api, services/worker,
         libs/asr_adapter, libs/audio_pipeline, libs/audio, libs/common,
         infra, scripts/demo, scripts/training, slurm/tools, slurm/jobs,
         tests, configs must be classified as class: implementation_reuse,
         permitted_use: read_only by default. Tasks that need to extend
         them must request CHANGE_SCOPE and add a permitted_use:
         extend_in_place row for the specific files.
  7. Write reports/robust_asr/touch_policy.md with one row per P0 to
     P10 task:
       task_id | allowed_write_paths | allowed_read_paths |
       default_no_touch_paths | external_paths_requiring_approval.
  8. Implement scripts/robust_asr/validate_report_shape.py. It must
     read docs/plans/state_packet_schemas_v1.yaml and validate report
     fixtures for: prebootstrap_inventory_report, planning_report,
     execution_report, phase_gate_report, approval_packet, and
     supplemental_evidence_report. It must emit OK_REPORT_SHAPE on PASS.
  9. Write minimal valid fixtures under
     artifacts/robust_asr/state_packets/report_shape_fixtures/ for every
     schema named in Action 8, then run validate_report_shape.py against
     that directory.
 10. Update tracker.repo_integration:
       legacy_trackers_classified = true;
       legacy_plans_classified = true;
       claude_md_preserved_outside_block = true;
       reuse_policy_path = configs/robust_asr/reuse_policy_v1.yaml;
       repo_integration_policy_path = reports/robust_asr/repo_integration_policy.md;
       touch_policy_path = reports/robust_asr/touch_policy.md;
       unclassified_paths_default_no_touch = true.
 11. Update tracker.artifacts for asset_inventory,
     repo_integration_policy, touch_policy, reuse_policy_config, and
     report_shape_fixtures.
 12. Update tracker.tasks[P0.2] with status PASS only after the
     Verification block passes.

Required deliverables:
  - reports/robust_asr/asset_inventory.md
  - reports/robust_asr/repo_integration_policy.md
  - reports/robust_asr/touch_policy.md
  - configs/robust_asr/reuse_policy_v1.yaml
  - scripts/robust_asr/validate_report_shape.py
  - artifacts/robust_asr/state_packets/report_shape_fixtures/

Done when:
  - asset_inventory.md exists and contains observed candidate assets.
  - repo_integration_policy.md contains the four required tables in
    order.
  - touch_policy.md has rows for every task P0.0 through P10.3.
  - reuse_policy_v1.yaml parses and contains explicit rows for active
    robust_asr paths, legacy state paths, reusable implementation paths,
    and mandatory no-touch paths.
  - Every unclassified path defaults to no-touch by policy.
  - validate_report_shape.py validates all report fixtures and emits
    OK_REPORT_SHAPE.
  - tracker.repo_integration fields are set exactly as Action 10.

Verification:
  test -f reports/robust_asr/asset_inventory.md
  test -f reports/robust_asr/repo_integration_policy.md
  test -f reports/robust_asr/touch_policy.md
  test -f configs/robust_asr/reuse_policy_v1.yaml
  test -f scripts/robust_asr/validate_report_shape.py
  grep -q "A. Active robust_asr state paths" reports/robust_asr/repo_integration_policy.md
  grep -q "B. Legacy state paths" reports/robust_asr/repo_integration_policy.md
  grep -q "C. Reusable implementation paths" reports/robust_asr/repo_integration_policy.md
  grep -q "D. Mandatory no-touch paths" reports/robust_asr/repo_integration_policy.md
  grep -q "P10.3" reports/robust_asr/touch_policy.md
  python - <<'PYCODE'
import yaml
p = yaml.safe_load(open('configs/robust_asr/reuse_policy_v1.yaml'))
assert isinstance(p, list) and p
required = {'path','class','permitted_use','allowed_tasks','validator','checksum_required','large_artifact','commit_allowed','notes'}
for row in p:
    assert required <= set(row), row
assert any(row['class'] == 'legacy_state' for row in p)
assert any(row['class'] == 'implementation_reuse' for row in p)
assert any(row['class'] == 'no_touch' for row in p)
# Every legacy_state row must be read_only and not commit_allowed.
# Forbidden classification would block P10.3 plan_tracker_consistency.
for row in p:
    if row['class'] == 'legacy_state':
        assert row['permitted_use'] == 'read_only', \
            f"legacy_state row {row['path']} must be read_only, got {row['permitted_use']}"
        assert row['commit_allowed'] is False, \
            f"legacy_state row {row['path']} must have commit_allowed: false"
# Every no_touch row must be forbidden.
for row in p:
    if row['class'] == 'no_touch':
        assert row['permitted_use'] == 'forbidden', \
            f"no_touch row {row['path']} must be forbidden, got {row['permitted_use']}"
PYCODE
  python - <<'PYCODE'
import yaml
tr = yaml.safe_load(open('docs/progress/robust_asr_progress.yaml'))
ri = tr['repo_integration']
assert ri['legacy_trackers_classified'] is True
assert ri['legacy_plans_classified'] is True
assert ri['claude_md_preserved_outside_block'] is True
assert ri['unclassified_paths_default_no_touch'] is True
assert ri['reuse_policy_path'] == 'configs/robust_asr/reuse_policy_v1.yaml'
PYCODE
  python scripts/robust_asr/validate_report_shape.py \
    --schemas docs/plans/state_packet_schemas_v1.yaml \
    --fixtures artifacts/robust_asr/state_packets/report_shape_fixtures

Decision rules:
  1. No existing asset becomes reusable merely by being listed in
     asset_inventory.md.
  2. If a legacy tracker or legacy plan cannot be classified, status =
     HALTED, marker = PLAN_CONFLICT, write
     reports/robust_asr/repo_integration_block.md, and stop.
  3. If a path needed by a future task is not classifiable, classify it
     as no_touch and require a later CHANGE_SCOPE Approval Packet before
     any edit.
  4. After this task, all subsequent tasks must cite reuse_policy_v1.yaml
     rows for any read or write outside active robust_asr state paths.

Stop condition:
  After commit of asset_inventory.md, repo_integration_policy.md,
  touch_policy.md, reuse_policy_v1.yaml, and tracker updates.
```

#### P0.3 Environment and Slurm smoke

```text
Preconditions:
  - P0.2 PASS.

Actions:
  1. Confirm Apptainer image at
     /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif.
  2. Confirm slurm/tools/on_submit.sh exists and is executable.
  3. Submit a 1-CPU 5-minute Slurm job that:
     - exec into the Apptainer image,
     - prints python version, torch version, CUDA available, host,
     - imports: torch, transformers, peft, ctranslate2, faster_whisper,
       lightgbm OR xgboost OR sklearn, librosa, numpy, pandas, pyarrow,
       yaml, pytest.
  4. Capture exit code, stdout, stderr to
     artifacts/robust_asr/runtime_smoke/.
  5. Write artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json
     with: job_id, partition, exit_code, host, python_version,
     image_sha256, submitted_at_utc, completed_at_utc.
  6. Write reports/robust_asr/runtime_smoke.md.

Required deliverables:
  - artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json
  - artifacts/robust_asr/runtime_smoke/stdout.txt and stderr.txt
  - reports/robust_asr/runtime_smoke.md

Done when:
  - runtime_smoke_job_metadata.json parses and exit_code == 0.
  - All required imports succeeded (or sklearn fallback recorded).

Verification:
  python -c "import json; m=json.load(open('artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json')); assert m['exit_code'] == 0, m"

Decision rules:
  1. If Apptainer image missing: status = HALTED, marker = BLOCKED_RUNTIME.
  2. If python != 3.11 inside the image: status = HALTED, marker = BLOCKED_RUNTIME.
  3. If lightgbm and xgboost both missing AND sklearn HistGradientBoostingRegressor
     succeeds: record ROUTER_IMPL_FALLBACK_SKLEARN, do not block.
  4. If any other required import fails: status = HALTED, marker = BLOCKED_RUNTIME.
  5. If exit_code != 0 for non-import reasons (e.g. submit failed):
     status = HALTED, marker = BLOCKED_RUNTIME.

Stop condition:
  After commit of runtime_smoke.md and job metadata.
```

#### P0.4 RP5 runtime contract skeleton (request/response JSON + 19 assertions)

```text
Preconditions:
  - P0.3 PASS.

Actions:
  1. Write artifacts/robust_asr/runtime_contract/rp5_request_fixture.json:
       {
         "request_id": "<uuid>",
         "audio": {
           "encoding": "wav | flac | webm_opus",
           "sample_rate_hz": 16000,
           "channels": 1,
           "duration_s": <float>,
           "sha256": "<hex>",
           "uri_or_inline": "<base64 or storage uri>"
         },
         "client": { "browser_user_agent": "<string>",
                     "client_version": "<semver>" },
         "constraints": { "max_latency_ms": <int>,
                          "allow_third_party": <bool>,
                          "profile": "<balanced | quality_first | local_first>" }
       }
  2. Write artifacts/robust_asr/runtime_contract/rp5_response_fixture.json:
       {
         "request_id": "<uuid>",
         "transcript": "<normalized text or null>",
         "raw_transcript": "<raw text or null>",
         "confidence": <float in [0,1] or null>,
         "ask_repeat": <bool>,
         "selected_backend": "<backend_name or null>",
         "router_kind": "<ml_router | deterministic_selector>",
         "routing_features": { ... },
         "latency_ms": { "backend": <int>, "server": <int>, "end_to_end": <int> },
         "cost_usd": <float or null>,
         "third_party_provider": "<provider or null>",
         "report_links": { "model_card": "<url>", "router_card": "<url>" },
         "errors": [ ... ]
       }
  3. Write libs/common/runtime_contract.py with request/response
     schemas (jsonschema 2020-12 draft).
  4. Implement scripts/robust_asr/validate_runtime_contract.py with
     19 assertions:
       1. JSON parses.
       2. Request and response have non-empty request_id and they match.
       3. Audio encoding in {"wav","flac","webm_opus"}.
       4. sample_rate_hz == 16000.
       5. channels == 1.
       6. duration_s > 0.
       7. audio.sha256 is 64-hex.
       8. constraints.profile in {"balanced","quality_first","local_first"}.
       9. constraints.allow_third_party is bool.
      10. constraints.max_latency_ms is positive int.
      11. response.ask_repeat is bool.
      12. (response.transcript is null) iff (response.ask_repeat == true OR errors non-empty).
      13. response.selected_backend is null iff response.ask_repeat == true.
      14. response.router_kind in {"ml_router","deterministic_selector"}.
      15. response.cost_usd is null OR >= 0.0.
      16. response.third_party_provider is null OR matches selected_backend
          when selected_backend == "assemblyai".
      17. latency_ms.end_to_end >= latency_ms.server >= latency_ms.backend.
      18. response.confidence is null OR in [0.0, 1.0].
      19. report_links.model_card and report_links.router_card are
          strings (may be empty in skeleton; non-empty enforced at
          --strict-final).
  5. Run validate_runtime_contract.py --strict-skeleton on the two
     fixtures.
  6. Write reports/robust_asr/runtime_contract_smoke.md with the
     19 assertions and pass/fail per assertion.
  7. Update tracker.artifacts.runtime_contract_fixture
     .contract_skeleton_validation_passed = true.

Required deliverables:
  - rp5_request_fixture.json
  - rp5_response_fixture.json
  - libs/common/runtime_contract.py
  - scripts/robust_asr/validate_runtime_contract.py (with --help)
  - reports/robust_asr/runtime_contract_smoke.md

Done when:
  - validate_runtime_contract.py --strict-skeleton emits
    OK_CONTRACT_SKELETON.
  - tracker.artifacts.runtime_contract_fixture
    .contract_skeleton_validation_passed == true.

Verification:
  python scripts/robust_asr/validate_runtime_contract.py \
    --strict-skeleton \
    --request artifacts/robust_asr/runtime_contract/rp5_request_fixture.json \
    --response artifacts/robust_asr/runtime_contract/rp5_response_fixture.json

Decision rules:
  1. If any assertion fails: status = FAIL on first run; fix the
     fixture or the schema, do not weaken assertions.
  2. If audio encoding cannot be webm_opus through the RP5 web runtime
     (validated later in P9.0): record ENV_CONSTRAINT and update
     final schema; do not change skeleton.

Stop condition:
  After OK_CONTRACT_SKELETON and commit.
```

#### P0.5 Model card and router card templates

```text
Preconditions:
  - P0.4 PASS.

Actions:
  1. Write docs/reports/robust_asr/model_card_lora.md with sections:
     intended_use, training_data, hyperparameters, evaluation_data,
     metrics, fairness_and_limitations, risks, license, contact.
     Use TODO_FILLED_IN_<task_id> placeholders linked to the task that
     will fill the field (e.g. TODO_FILLED_IN_P4.2 for evaluation
     metrics).
     Include at least 10 placeholders across the sections.
  2. Write docs/reports/robust_asr/router_card.md with sections:
     intended_use, inputs, decision_rule, training_data, evaluation,
     fallbacks, risks, license, contact.
     Include at least 8 TODO_FILLED_IN_<task_id> placeholders.

Required deliverables:
  - docs/reports/robust_asr/model_card_lora.md
  - docs/reports/robust_asr/router_card.md

Done when:
  - Both files exist and grep -c TODO_FILLED_IN model_card_lora.md >= 10
    AND grep -c TODO_FILLED_IN router_card.md >= 8.

Verification:
  test $(grep -c TODO_FILLED_IN docs/reports/robust_asr/model_card_lora.md) -ge 10
  test $(grep -c TODO_FILLED_IN docs/reports/robust_asr/router_card.md) -ge 8

Stop condition:
  After commit of both templates.
```

(End of P0. Evaluate the P0 gate predicate from Section 8. On PASS, write phase_summary.P0 and stop.)

### P1. Schema, manifests, degradations

#### P1.1 Data root inventory and dataset configs

```text
Preconditions:
  - P0 gate PASS or fast iteration through gates.

Actions:
  1. Inventory dataset roots:
     - LibriSpeech (train-clean-100, train-clean-360, dev-clean, test-clean)
     - Common Voice English release locked to a specific version
     - TED-LIUM Release 3 (fallback)
     - CHiME-6 (fallback)
  2. For each dataset present, record root path, version label,
     speaker count, hour count, file count, license URL, and
     access_method ("local" or "via_dataset_loader").
  3. Write configs/robust_asr/data_v1.yaml with declared roots,
     selected splits, OOD-real preference order (Common Voice ->
     TED-LIUM -> CHiME-6), and split definitions
     (lora_train, router_train, validation, locked_test, ood_real_locked,
     common_voice_demo_reserved).
  4. Validate that lora_train / router_train / validation / locked_test
     are speaker-disjoint.
  5. Write reports/robust_asr/data_inventory.md.

Required deliverables:
  - configs/robust_asr/data_v1.yaml
  - reports/robust_asr/data_inventory.md

Done when:
  - data_v1.yaml parses.
  - At least LibriSpeech is available; all four split labels resolve
    to non-empty file lists; speaker-disjoint check passes for
    LibriSpeech splits.
  - Either Common Voice resolves OR a Section 1.1 fallback is
    declared OR BLOCKED_OOD_PUBLIC is recorded.

Verification:
  python -c "import yaml; c=yaml.safe_load(open('configs/robust_asr/data_v1.yaml')); assert 'splits' in c and 'lora_train' in c['splits']"

Decision rules:
  1. If LibriSpeech missing: status = HALTED, marker = MISSING_EVIDENCE.
  2. If no Section 1.1 OOD-real source resolves: status = PARTIAL,
     marker = BLOCKED_OOD_PUBLIC, claims_enabled.ood_real = false.

Stop condition:
  After commit of data_v1.yaml and data_inventory.md.
```

#### P1.2 Canonical eval schema, normalization, leakage tests

```text
Preconditions:
  - P1.1 PASS.

Actions:
  1. Write libs/common/eval_schema.yaml with the 28 columns from
     Section 3.
  2. Write libs/common/normalization.py with one shared normalization
     function. Set NORMALIZATION_VERSION in libs/common/versions.py.
  3. Write libs/common/metrics.py exposing wer, cer, wa, paired
     bootstrap CI helpers.
  4. Write tests:
     tests/robust_asr/test_eval_schema.py
     tests/robust_asr/test_normalization_metrics.py
     tests/robust_asr/test_leakage.py
  5. Write scripts/robust_asr/validate_eval_schema.py per Section 4.1.

Required deliverables:
  - libs/common/eval_schema.yaml
  - libs/common/normalization.py
  - libs/common/metrics.py
  - libs/common/versions.py with NORMALIZATION_VERSION
  - scripts/robust_asr/validate_eval_schema.py
  - tests above.

Done when:
  - pytest tests/robust_asr/test_eval_schema.py PASS
  - pytest tests/robust_asr/test_normalization_metrics.py PASS
  - pytest tests/robust_asr/test_leakage.py PASS (placeholder data
    OK at this point)
  - validate_eval_schema.py emits OK_EVAL_SCHEMA.

Verification:
  pytest tests/robust_asr/test_eval_schema.py tests/robust_asr/test_normalization_metrics.py tests/robust_asr/test_leakage.py
  python scripts/robust_asr/validate_eval_schema.py

Stop condition:
  After all three pytest files PASS and OK_EVAL_SCHEMA, commit.
```

#### P1.3 Public manifests (LoRA/router/validation/locked test/OOD/demo reserved)

```text
Preconditions:
  - P1.1 PASS, P1.2 PASS.

Actions:
  1. Run scripts/robust_asr/build_public_manifests.py per Section 4.3.
  2. Run scripts/robust_asr/summarize_manifests.py per Section 4.3.
  3. Update tracker.artifacts.manifest_summary.

Required deliverables:
  - artifacts/robust_asr/manifests/<dataset>_<split>.parquet for every
    split listed in Section 9 P1.1
  - reports/robust_asr/manifest_summary.md

Done when:
  - build_public_manifests.py emits OK_PUBLIC_MANIFESTS.
  - summarize_manifests.py emits OK_MANIFEST_SUMMARY.
  - At least the LibriSpeech manifests exist with non-zero rows.

Verification:
  python scripts/robust_asr/build_public_manifests.py --config configs/robust_asr/data_v1.yaml
  python scripts/robust_asr/summarize_manifests.py --manifest-root artifacts/robust_asr/manifests --out reports/robust_asr/manifest_summary.md
  ls artifacts/robust_asr/manifests/librispeech_lora_train.parquet

Decision rules:
  1. If Common Voice and all fallbacks fail: status = PARTIAL, marker
     = BLOCKED_OOD_PUBLIC, claims_enabled.ood_real = false.
  2. If LibriSpeech manifests fail: status = HALTED, marker = MISSING_EVIDENCE.

Stop condition:
  After OK_PUBLIC_MANIFESTS and OK_MANIFEST_SUMMARY and commit.
```

#### P1.4 Degradation v1 generators and manifests

```text
Preconditions:
  - P1.3 PASS.

Actions:
  1. Implement libs/audio/degradations.py with the five family
     functions (clean is identity; cafe_noise, phone_band,
     far_field_room, muffled_lowpass) per Section 3.
  2. Write configs/robust_asr/degradation_v1.yaml with parameter
     ranges for ID and OOD-param.
  3. Run scripts/robust_asr/build_degradation_v1.py per Section 4.3.
  4. Write tests/robust_asr/test_degradation_v1.py asserting:
     - Each function writes audio with rms_mean >= 1e-6.
     - Each function returns the metadata fields from Section 3.
     - clipping_ratio < 0.5 on a sample of fixtures.
     - source_audio_sha256 matches the input hash.

Required deliverables:
  - libs/audio/degradations.py
  - configs/robust_asr/degradation_v1.yaml
  - artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet
  - artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet
  - tests/robust_asr/test_degradation_v1.py

Done when:
  - build_degradation_v1.py emits OK_DEGRADATION_V1.
  - pytest tests/robust_asr/test_degradation_v1.py PASS.

Verification:
  python scripts/robust_asr/build_degradation_v1.py --config configs/robust_asr/degradation_v1.yaml
  pytest tests/robust_asr/test_degradation_v1.py

Decision rules:
  1. If a family produces BAD_OUTPUT (Section 5.9) on > 1% of files:
     status = FAIL, marker = MISSING_EVIDENCE; investigate before
     advancing.

Stop condition:
  After OK_DEGRADATION_V1 and tests PASS and commit.
```

(End of P1. Evaluate P1 gate from Section 8.)

### P2. Whisper base baseline

#### P2.1 Whisper base CT2 INT8 evaluation

```text
Preconditions:
  - P1 gate PASS.

Actions:
  1. Run scripts/robust_asr/run_backend_eval.py per Section 4.2 with
     --backend whisper_base_ct2_int8.
  2. Run scripts/robust_asr/summarize_backend_eval.py.
  3. Run scripts/robust_asr/validate_eval_table.py on the produced
     parquet.
  4. Update tracker.artifacts.baseline_table and baseline_report with
     SHA-256 and row counts.

Required deliverables:
  - artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet
  - reports/robust_asr/baseline_whisper_base.md

Done when:
  - validate_eval_table.py emits OK_EVAL_TABLE on the parquet.
  - summarize_backend_eval.py emits OK_BACKEND_SUMMARY.

Verification:
  python scripts/robust_asr/validate_eval_table.py --input artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet
  test -f reports/robust_asr/baseline_whisper_base.md

Stop condition:
  After OK_EVAL_TABLE and commit.
```

#### P2.2 LoRA smoke split config

```text
Preconditions:
  - P1.3 PASS, P1.4 PASS, P2.1 PASS.

Actions:
  1. Write configs/robust_asr/lora_smoke.yaml with:
     - smoke split (subset of lora_train per data_v1.yaml)
     - smoke eval split (subset of validation)
     - hyperparameters: steps_max=200, learning_rate, batch_size,
       lora_rank, lora_alpha, lora_dropout, target_modules, seed
     - eval_decode_defaults: see Section 3
     - timeouts: training_timeout_seconds=14400 (4h), eval_timeout_seconds=1800
  2. Validate that the smoke splits reference rows present in the
     manifests.

Required deliverables:
  - configs/robust_asr/lora_smoke.yaml

Done when:
  - lora_smoke.yaml parses and references manifest rows that exist.

Verification:
  python -c "import yaml; c=yaml.safe_load(open('configs/robust_asr/lora_smoke.yaml')); print(list(c.keys()))"

Stop condition:
  After commit of lora_smoke.yaml.
```

(End of P2. Evaluate P2 gate.)

### P3. LoRA smoke and Decision A

#### P3.1 LoRA smoke train, eval, export smoke

```text
Preconditions:
  - P2 gate PASS.

Actions:
  1. Submit train_lora_smoke.py via Slurm using configs/robust_asr/lora_smoke.yaml.
  2. On train exit 0, run evaluate_lora_smoke.py with the produced
     checkpoint manifest.
  3. On evaluate exit 0, run smoke_export_lora_ct2.py with the best
     smoke checkpoint.
  4. Update tracker.tasks[P3.1] with commit, files, and outcomes from
     each step.

Required deliverables:
  - artifacts/robust_asr/lora_smoke/checkpoint_manifest.json
  - artifacts/robust_asr/lora_smoke/training_log.csv
  - artifacts/robust_asr/lora_smoke/loss_curve.png
  - reports/robust_asr/lora/lora_smoke_result.json
  - artifacts/robust_asr/lora_smoke/export_smoke_result.json if export ran
  - reports/robust_asr/lora/lora_smoke_degenerate.md if evaluate exits 4

Done when:
  - train_lora_smoke.py exits 0 after any internal batch-size retry.
  - evaluate_lora_smoke.py exits 0, OR exits 4 with
    DEGENERATE_SMOKE_RESULT and the degenerate report exists.
  - smoke_export_lora_ct2.py exits 0, OR exits 5 with EXPORT_BLOCKED
    recorded.
  - No PARTIAL state is allowed for CUDA OOM. OOM is PASS only if the
    script recovered internally and exited 0; otherwise it is HALTED.

Verification:
  test -f artifacts/robust_asr/lora_smoke/checkpoint_manifest.json
  test -f reports/robust_asr/lora/lora_smoke_result.json \
    || test -f reports/robust_asr/lora/lora_smoke_degenerate.md
  if test -f artifacts/robust_asr/lora_smoke/export_smoke_result.json; then \
    test -s artifacts/robust_asr/lora_smoke/export_smoke_result.json; fi

Decision rules (machine, applied by the agent):
  1. Train exits 0 after internal retry: continue.
  2. Train exits 2 (OOM_AT_BATCH_1): status = HALTED, marker =
     BLOCKED_RUNTIME, do not run subsequent steps.
  3. Train exits 3 (NON_FINITE_LOSS): status = FAIL, no marker;
     P3.2 will set Decision_A_smoke = FAIL.
  4. Evaluate exits 4 (DEGENERATE): status = FAIL.
  5. Export exits 5 (CT2_UNSUPPORTED): record EXPORT_BLOCKED. Do not
     fail the smoke for this; P3.2 decides from the smoke metrics and
     records export risk separately.
  6. Wall-clock budget exceeded (> 14400s elapsed without success):
     status = HALTED, marker = BUDGET_EXCEEDED.

Stop condition:
  After all applicable steps complete with PASS, FAIL, or HALTED and
  the task report, tracker, commit, and push are complete.
```

#### P3.2 Decision A

```text
Preconditions:
  - P3.1 status in {PASS, PARTIAL, FAIL, HALTED}.

Actions:
  1. Run scripts/robust_asr/decide_lora_smoke.py per Section 4.4.
  2. Set tracker.decisions.Decision_A_smoke.outcome from the report
     first line.
  3. Write reports/robust_asr/lora/decision_a_smoke.md narrating the
     decision and the tracker side effects expected at the P3 gate
     (Section 8).

Required deliverables:
  - reports/robust_asr/lora/lora_smoke_report.md (PASS|PARTIAL|FAIL|HALTED)
  - reports/robust_asr/lora/decision_a_smoke.md

Done when:
  - decide_lora_smoke.py emits OK_LORA_SMOKE_DECISION.
  - tracker.decisions.Decision_A_smoke.outcome set.

Verification:
  python scripts/robust_asr/decide_lora_smoke.py \
    --input reports/robust_asr/lora/lora_smoke_result.json \
    --export-input artifacts/robust_asr/lora_smoke/export_smoke_result.json \
    --out reports/robust_asr/lora/lora_smoke_report.md
  test -f reports/robust_asr/lora/decision_a_smoke.md

Decision rules:
  Outcome is mechanical from the smoke report (Section 5.1).
  The orchestrator may override in tracker.orchestrator_approvals
  before P4 begins, but the override must be logged with reason.

Stop condition:
  After commit. Evaluate P3 gate.
```

(End of P3. Evaluate P3 gate.)

### P4. Full LoRA, Decision B, CT2 INT8 preservation

#### P4.1 Full LoRA training

```text
Preconditions:
  - P3 gate PASS.
  - tracker.decisions.Decision_A_smoke.outcome in {PASS, PARTIAL}.

Actions:
  1. Write configs/robust_asr/lora_full.yaml with:
     full lora_train split, validation split, hyperparameters,
     checkpoint_every_steps, training_timeout_seconds=86400 (24h),
     eval_timeout_seconds=1800, allowed_partitions list, seed.
  2. Submit train_lora_full.py via Slurm.
  3. Persist checkpoints, training_log.csv, loss_curve.png.

Required deliverables:
  - configs/robust_asr/lora_full.yaml
  - artifacts/robust_asr/lora_full/checkpoint_manifest.json
  - artifacts/robust_asr/lora_full/training_log.csv
  - artifacts/robust_asr/lora_full/loss_curve.png

Done when:
  - train_lora_full.py exit 0 with at least 2 saved checkpoints.

Verification:
  python -c "import json; m=json.load(open('artifacts/robust_asr/lora_full/checkpoint_manifest.json')); assert len(m['checkpoints']) >= 2"

Decision rules:
  1. exit 2 (OOM_AT_BATCH_1): status = HALTED, marker = BLOCKED_RUNTIME.
  2. exit 3 (NON_FINITE_LOSS): status = HALTED, marker = MISSING_EVIDENCE.
  3. exit 6 (PREEMPTED_AT_STEP): requeue once. If preempted twice,
     run resolve_long_running_queue.py:
       on exit 0 (partition returned): switch and retry once.
       on exit 13 (NO_LONG_RUNNING_QUEUE_AVAILABLE): status = HALTED,
         marker = BUDGET_EXCEEDED.
  4. wall_clock elapsed > training_timeout_seconds without success:
     status = HALTED, marker = BUDGET_EXCEEDED.

Stop condition:
  After exit 0 with checkpoints, or HALTED with the appropriate marker.
```

#### P4.2 Full LoRA evaluation, paired bootstrap, Decision B

```text
Preconditions:
  - P4.1 PASS.

Actions:
  1. Run evaluate_lora_checkpoints.py per Section 4.4.
  2. Run select_lora_checkpoint.py with tolerance_macro_wa=0.002.
  3. Run evaluate_full_lora.py to produce whisper_lora_fp16.parquet
     and full_lora_eval.md.
  4. Run validate_eval_table.py on whisper_lora_fp16.parquet.
  5. Update tracker.decisions.Decision_B_lora_full.outcome from the
     full_lora_eval.md outcome line.

Required deliverables:
  - reports/robust_asr/lora/full_lora_selection.json
  - reports/robust_asr/lora/full_lora_training.md
  - reports/robust_asr/lora/full_lora_eval.md
  - artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet

Done when:
  - evaluate_full_lora.py emits OK_LORA_FULL_EVAL with one of
    {PASS_GLOBAL, PASS_SUBSET, FAIL_WITH_EVIDENCE, HALTED}.
  - validate_eval_table.py emits OK_EVAL_TABLE on the parquet.

Verification:
  python scripts/robust_asr/validate_eval_table.py --input artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet

Decision rules:
  1. evaluate_lora_checkpoints.py exit 7 (ALL_CHECKPOINTS_UNUSABLE):
     status = HALTED, marker = MISSING_EVIDENCE.
  2. PASS_GLOBAL or PASS_SUBSET: status = PASS,
     claims_enabled.positive_lora = true (subject to preservation outcome).
  3. FAIL_WITH_EVIDENCE: status = FAIL,
     claims_enabled.positive_lora = false. Continue to P4.3 only if
     orchestrator wants to verify CT2 INT8 export anyway. By default,
     skip P4.3 by setting it SKIPPED_BY_DECISION_A; mark
     Decision_B_lora_full.include_lora_in_router = false; advance.
  4. HALTED: same as FAIL above with respect to inclusion.

Stop condition:
  After OK_LORA_FULL_EVAL and Decision_B partial recording (preservation
  may flip include_lora_in_router to false in P4.3).
```

#### P4.3 LoRA merge to FP16, CT2 INT8 export, preservation eval

```text
Preconditions:
  - P4.2 PASS with PASS_GLOBAL or PASS_SUBSET, OR orchestrator approval
    to run preservation under FAIL_WITH_EVIDENCE.

Actions:
  1. Run merge_lora_to_fp16.py.
  2. Run export_lora_ct2_int8.py.
  3. Run run_backend_eval.py --backend whisper_lora_ct2_int8 to
     produce whisper_lora_ct2_int8.parquet.
  4. Run validate_eval_table.py on whisper_lora_ct2_int8.parquet.
  5. Run evaluate_lora_int8_preservation.py per Section 4.4.
  6. Update tracker.decisions.Decision_B_lora_full
     .preservation_outcome and .include_lora_in_router.

Required deliverables:
  - artifacts/robust_asr/lora_merged_fp16/
  - artifacts/robust_asr/lora_ct2_int8/
  - artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet
  - reports/robust_asr/lora/lora_ct2_int8_preservation.md (outcome on first line)

Done when:
  - evaluate_lora_int8_preservation.py emits OK_LORA_PRESERVATION
    with one of {PASS, FAIL, EXPORT_BLOCKED}.

Verification:
  python scripts/robust_asr/validate_eval_table.py --input artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet
  head -n 1 reports/robust_asr/lora/lora_ct2_int8_preservation.md

Decision rules:
  1. export_lora_ct2_int8.py exit 5 (CT2_UNSUPPORTED): status = HALTED,
     marker = EXPORT_BLOCKED, set Decision_B.include_lora_in_router = false.
  2. preservation outcome = PASS: keep include_lora_in_router consistent
     with P4.2 (true if P4.2 was PASS_*).
  3. preservation outcome = FAIL: status = PASS for P4.3 (the eval ran),
     set include_lora_in_router = false; FP LoRA experimental result
     remains.

Stop condition:
  After commit of preservation report and tracker update.
```

(End of P4. Evaluate P4 gate.)

### P5. AssemblyAI cache or API block

#### P5.1 AssemblyAI cache populate and evaluate

```text
Preconditions:
  - P4 gate PASS (any branch).

Actions:
  1. Confirm pricing_v1.yaml. If assemblyai_pricing_checked_date is
     older than 90 days: record PENDING_PRICING_VERIFICATION.
  2. Run probe_assemblyai_runtime.py.
     If "ASSEMBLYAI_RUNTIME=false reason=key_unset": skip cache
       populate; record BLOCKED_API.
  3. Else run populate_assemblyai_cache.py.
  4. On success, run evaluate_assemblyai_from_cache.py.
  5. Run validate_eval_table.py on assemblyai.parquet.

Required deliverables:
  - <cache-dir>/cache_summary.json (if API available)
  - artifacts/robust_asr/eval_tables/assemblyai.parquet (if API
    available)

Done when:
  - One of:
    OK_ASSEMBLYAI_CACHE + OK_ASSEMBLYAI_EVAL + OK_EVAL_TABLE on
      assemblyai.parquet.
    OR BLOCKED_API recorded with reason in {key_unset, auth, quota,
      health_check_failed} and claims_enabled.cloud_tradeoff = false.

Verification:
  if API available:
    python scripts/robust_asr/validate_eval_table.py --input artifacts/robust_asr/eval_tables/assemblyai.parquet
  else:
    grep -q BLOCKED_API docs/progress/robust_asr_progress.yaml

Decision rules:
  1. populate_assemblyai_cache.py exit 8/9/10: status = HALTED, marker
     = BLOCKED_API, set claims_enabled.cloud_tradeoff = false.
  2. exit 1 with HTTP 5xx for > 1% of audio_ids: status = PARTIAL;
     evaluate from cache for the remaining audio_ids; record the
     missing list in cache_summary.json.
  3. cost > pricing_config.max_total_cost_usd: status = HALTED, marker
     = BUDGET_EXCEEDED.

Stop condition:
  After OK_EVAL_TABLE on the produced parquet OR BLOCKED_API recorded.
```

(End of P5. Evaluate P5 gate.)

### P6. Oracle table and router matrices

#### P6.1 Oracle table or selector evidence table

```text
Preconditions:
  - P5 gate PASS.

Actions:
  1. Write configs/robust_asr/router_v1.yaml with: cost coefficients
     (alpha, beta, gamma, delta), profile defaults, eligible action
     set under each profile, ask_repeat_wer_threshold,
     router_confidence_min, epsilon_wer, and deterministic selector
     constants from Section 5.5.
  2. Count transcript-producing deployable backends using the P5 gate
     Backend count predicate.
  3. If count >= 2 and OUTCOME_E_DETERMINISTIC_SELECTOR is not active:
       Branch A, oracle path:
         a. Run build_oracle_table.py per Section 4.6.
         b. Run validate_oracle_table.py.
  4. If count < 2 or OUTCOME_E_DETERMINISTIC_SELECTOR is active:
       Branch B, selector evidence path:
         a. Ensure OUTCOME_E_DETERMINISTIC_SELECTOR is active.
         b. Run build_selector_evidence_table.py per Section 4.6.
         c. Run validate_selector_evidence.py.
         d. Set tracker.tasks[P6.2].status = SKIPPED_BY_OUTCOME_E
            with next_task = P7.3.

Required deliverables:
  Branch A:
    - configs/robust_asr/router_v1.yaml
    - artifacts/robust_asr/oracle/oracle_table.parquet
  Branch B:
    - configs/robust_asr/router_v1.yaml
    - artifacts/robust_asr/router/selector_evidence.parquet
    - reports/robust_asr/router/selector_evidence_summary.md

Done when:
  Branch A:
    - validate_oracle_table.py emits OK_ORACLE_TABLE.
  Branch B:
    - validate_selector_evidence.py emits OK_SELECTOR_EVIDENCE.
    - tracker marker OUTCOME_E_DETERMINISTIC_SELECTOR is active.
    - tracker.tasks[P6.2].status == SKIPPED_BY_OUTCOME_E.

Verification:
  Branch A:
    python scripts/robust_asr/validate_oracle_table.py --input artifacts/robust_asr/oracle/oracle_table.parquet
  Branch B:
    python scripts/robust_asr/validate_selector_evidence.py --input artifacts/robust_asr/router/selector_evidence.parquet
    grep -q OUTCOME_E_DETERMINISTIC_SELECTOR docs/progress/robust_asr_progress.yaml
    grep -q SKIPPED_BY_OUTCOME_E docs/progress/robust_asr_progress.yaml

Decision rules:
  1. JOIN coverage < 100% on Branch A: status = HALTED, marker =
     MISSING_EVIDENCE.
  2. Selector evidence with zero rows on Branch B: status = HALTED,
     marker = MISSING_EVIDENCE.
  3. Do not build router_train/router_val/router_test_locked on Branch B.

Stop condition:
  After Branch A OK_ORACLE_TABLE or Branch B OK_SELECTOR_EVIDENCE and
  commit.
```

#### P6.2 Router features and matrices

```text
Preconditions:
  - P6.1 PASS.
  - Marker OUTCOME_E_DETERMINISTIC_SELECTOR not active.

Actions:
  1. Run extract_router_features.py per Section 4.6.
  2. Run build_router_matrices.py per Section 4.6.
  3. Run validate_router_matrices.py.
  4. Run pytest tests/robust_asr/test_leakage.py.

Required deliverables:
  - artifacts/robust_asr/router/router_features.parquet
  - artifacts/robust_asr/router/router_train.parquet
  - artifacts/robust_asr/router/router_val.parquet
  - artifacts/robust_asr/router/router_test_locked.parquet

Done when:
  - validate_router_matrices.py emits OK_ROUTER_MATRICES.
  - test_leakage.py PASS.

Verification:
  python scripts/robust_asr/validate_router_matrices.py --router-dir artifacts/robust_asr/router
  pytest tests/robust_asr/test_leakage.py

Skip rule:
  If OUTCOME_E_DETERMINISTIC_SELECTOR is active before P6.2 starts:
    - Do not run feature extraction or matrix construction.
    - Set tracker.tasks[P6.2].status = SKIPPED_BY_OUTCOME_E.
    - next_task = P7.3.
    - Commit the tracker update with the P6.1 selector evidence commit
      if possible; otherwise commit it as the P6.2 skip commit.

Stop condition:
  After OK_ROUTER_MATRICES + leakage tests PASS and commit, or after
  SKIPPED_BY_OUTCOME_E is recorded.
```

(End of P6. Evaluate P6 gate.)

### P7. Router or deterministic selector

#### P7.1 Train router candidates and select

```text
Preconditions:
  - P6 gate PASS.
  - Marker OUTCOME_E_DETERMINISTIC_SELECTOR not active.
  - tracker.tasks[P6.2].status == PASS.
  - artifacts/robust_asr/router/router_train.parquet,
    router_val.parquet, router_test_locked.parquet exist.

Actions:
  1. Run train_router_candidates.py per Section 4.6.
  2. Run select_router.py per Section 4.6.

Required deliverables:
  - artifacts/robust_asr/router/candidates/<impl>__<config_id>/
  - artifacts/robust_asr/router/selected_router/

Done when:
  - select_router.py emits OK_ROUTER_SELECT.

Verification:
  test -f artifacts/robust_asr/router/selected_router/metadata.json

Decision rules:
  1. If OUTCOME_E_DETERMINISTIC_SELECTOR is active before P7.1 starts:
     status = SKIPPED_BY_OUTCOME_E; next_task = P7.3; do not train.
  2. train_router_candidates.py exit 11 (ALL_CANDIDATES_DEGENERATE):
     record OUTCOME_E_DETERMINISTIC_SELECTOR; set P7.2 =
     SKIPPED_BY_OUTCOME_E; advance to P7.3 deterministic-selector path.
  3. select_router.py exit 12 (NO_CANDIDATE_BEATS_BASELINE):
     record OUTCOME_E_DETERMINISTIC_SELECTOR; set P7.2 =
     SKIPPED_BY_OUTCOME_E; advance to P7.3 deterministic-selector path.
  4. DEGENERATE_ROUTER_RECOVERED is non-blocking; record and continue.

Stop condition:
  After OK_ROUTER_SELECT or after OUTCOME_E_DETERMINISTIC_SELECTOR is
  recorded with P7.2 skipped.
```

#### P7.2 Evaluate router on locked test

```text
Preconditions:
  - P7.1 PASS without OUTCOME_E_DETERMINISTIC_SELECTOR.

Actions:
  1. Run evaluate_router.py per Section 4.6.
  2. Update tracker.artifacts with the report SHA-256.

Required deliverables:
  - reports/robust_asr/router/router_final_eval.md (with paired BCa
    intervals)

Done when:
  - evaluate_router.py emits OK_ROUTER_FINAL_EVAL.

Verification:
  test -f reports/robust_asr/router/router_final_eval.md

Stop condition:
  After OK_ROUTER_FINAL_EVAL and commit.
```

#### P7.3 Package router or deterministic selector

```text
Preconditions:
  - P7.2 PASS, OR marker OUTCOME_E_DETERMINISTIC_SELECTOR active.
  - If OUTCOME_E_DETERMINISTIC_SELECTOR is active:
      artifacts/robust_asr/router/selector_evidence.parquet exists
      OR router_test_locked.parquet exists from a previous valid P6.2 run.

Actions:
  Branch A (ML router):
    1. Run package_router.py per Section 4.6.
    2. Run pytest tests/robust_asr/test_router_runtime.py.
  Branch B (deterministic selector):
    1. Run package_deterministic_selector.py per Section 4.6.
    2. Run evaluate_deterministic_selector.py with:
       --selector artifacts/robust_asr/router/selected_router/deterministic_selector.json
       --selector-test artifacts/robust_asr/router/selector_evidence.parquet
       unless router_test_locked.parquet is the active valid evidence table.
    3. Run pytest tests/robust_asr/test_router_runtime.py.

Required deliverables:
  - artifacts/robust_asr/router/selected_router/
      model.<ext> (Branch A) OR deterministic_selector.json (Branch B)
      metadata.json
      rp5_inference.py
      test_vectors.json
  - reports/robust_asr/router/router_final_eval.md (Branch A)
    OR reports/robust_asr/router/selector_final_eval.md (Branch B)

Done when:
  Branch A: OK_ROUTER_PACKAGE + tests PASS.
  Branch B: OK_DETERMINISTIC_SELECTOR_PACKAGE + OK_SELECTOR_FINAL_EVAL
            + tests PASS.

Verification:
  pytest tests/robust_asr/test_router_runtime.py
  if test -f artifacts/robust_asr/router/selected_router/deterministic_selector.json; then \
    test -f reports/robust_asr/router/selector_final_eval.md; fi
  if test -f artifacts/robust_asr/router/selected_router/model.txt \
       || test -f artifacts/robust_asr/router/selected_router/model.json \
       || test -f artifacts/robust_asr/router/selected_router/model.joblib; then \
    test -f reports/robust_asr/router/router_final_eval.md; fi

Stop condition:
  After tests PASS and commit.
```

(End of P7. Evaluate P7 gate.)

### P8. System evaluation and demo examples

#### P8.1 System evaluation and Decision D

```text
Preconditions:
  - P7 gate PASS.

Actions:
  1. Run evaluate_system.py per Section 4.7.
  2. Update tracker.claims_enabled.positive_system from system_eval.md
     first line.
  3. Update tracker.decisions.Decision_D_positive_system.outcome.

Required deliverables:
  - reports/robust_asr/system/system_eval.md

Done when:
  - evaluate_system.py emits OK_SYSTEM_EVAL with true or false on the
    first line.

Verification:
  head -n 1 reports/robust_asr/system/system_eval.md

Stop condition:
  After OK_SYSTEM_EVAL and tracker updated.
```

#### P8.2 Demo examples

```text
Preconditions:
  - P8.1 PASS.

Actions:
  1. Run build_demo_examples.py per Section 4.7.
  2. Run pytest tests/robust_asr/test_leakage.py.

Required deliverables:
  - artifacts/robust_asr/demo/demo_examples_manifest.json
  - artifacts/robust_asr/demo/audio/ with 8 example audio files (or
    references to public files where allowed)

Done when:
  - OK_DEMO_EXAMPLES with 8 selected.
  - test_leakage.py PASS after demo example selection.

Verification:
  python -c "import json; m=json.load(open('artifacts/robust_asr/demo/demo_examples_manifest.json')); assert len(m['examples']) == 8"
  pytest tests/robust_asr/test_leakage.py

Stop condition:
  After OK_DEMO_EXAMPLES + leakage PASS and commit.
```

(End of P8. Evaluate P8 gate.)

### P9. Final runtime contract, handoff, RP5 spec

#### P9.0 Final runtime contract

```text
Preconditions:
  - P8 gate PASS.

Actions:
  1. Update artifacts/robust_asr/runtime_contract/ with finalized
     request and response schemas reflecting:
     - Whether LoRA backend exists (Decision B).
     - Whether AssemblyAI backend exists (claims_enabled.cloud_tradeoff).
     - Whether router_kind is ml_router or deterministic_selector.
  2. Write final_request_schema.json and final_response_schema.json.
  3. Run validate_runtime_contract.py --strict-final on representative
     fixtures from each backend pathway.

Required deliverables:
  - artifacts/robust_asr/runtime_contract/final_request_schema.json
  - artifacts/robust_asr/runtime_contract/final_response_schema.json

Done when:
  - validate_runtime_contract.py --strict-final emits OK_CONTRACT_FINAL
    on at least one fixture per supported backend.

Verification:
  python scripts/robust_asr/validate_runtime_contract.py --strict-final \
    --request artifacts/robust_asr/runtime_contract/final_request_fixture.json \
    --response artifacts/robust_asr/runtime_contract/final_response_fixture.json

Stop condition:
  After OK_CONTRACT_FINAL and commit.
```

#### P9.1 Handoff package

```text
Preconditions:
  - P9.0 PASS.

Actions:
  1. Populate artifacts/robust_asr/handoff/ with:
     - README.md with the 8 numbered sections in order:
         1. Purpose and scope
         2. Artifacts and checksums
         3. Reproduction commands
         4. Runtime contract (link to final schemas)
         5. Smoke and rollback scripts
         6. Risks, limits, disabled claims
         7. Provenance (commit, branch, tag)
         8. Contact and license
     - Backend configs (no secrets).
     - selected_router/ (model + metadata + test_vectors + rp5_inference.py).
     - lora_ct2_int8/ (only if include_lora_in_router == true).
     - handoff_smoke.py: loads selected_router and one backend config,
       transcribes one demo audio file, exits 0 on success.
     - rollback_to_previous_handoff.py: takes a previous tag, restores
       the package directory from that tag.
     - handoff_validation_template.md: the template the RP5 branch fills in.
  2. Compute SHA-256 for every artifact and record in tracker.
  3. Run verify_handoff_package.py --strict.
  4. Tag handoff/<YYYYMMDD>-<short_sha> locally and push to origin.

Required deliverables:
  - artifacts/robust_asr/handoff/README.md
  - artifacts/robust_asr/handoff/handoff_smoke.py (executable)
  - artifacts/robust_asr/handoff/rollback_to_previous_handoff.py (executable)
  - artifacts/robust_asr/handoff/handoff_validation_template.md
  - handoff/<date>-<short_sha> tag local and on origin

Done when:
  - verify_handoff_package.py --strict emits OK_HANDOFF_PACKAGE.
  - Tag exists on origin.

Verification:
  python scripts/robust_asr/verify_handoff_package.py --strict --handoff artifacts/robust_asr/handoff
  git rev-parse --verify origin/handoff/$(date -u +%Y%m%d)-$(git rev-parse --short HEAD)

Stop condition:
  After OK_HANDOFF_PACKAGE and tag pushed.
```

#### P9.2 RP5 runtime spec

```text
Preconditions:
  - P9.1 PASS.

Actions:
  1. Write artifacts/robust_asr/handoff/rp5_runtime_spec.md with:
     - input contract (browser audio formats, sample_rate, duration limits)
     - server-side validation steps
     - inference steps (decode features, route, run backend)
     - response shape mapping to final_response_schema.json
     - latency budgets and the deterministic selector fallback path
     - failure modes and the matching response.errors entries
  2. Validate that every backend referenced in rp5_inference.py is
     present in the handoff package.

Required deliverables:
  - artifacts/robust_asr/handoff/rp5_runtime_spec.md

Done when:
  - rp5_runtime_spec.md exists with the 6 sections above and references
    only artifacts present in the handoff directory.

Verification:
  test -f artifacts/robust_asr/handoff/rp5_runtime_spec.md
  grep -q "input contract" artifacts/robust_asr/handoff/rp5_runtime_spec.md

Stop condition:
  After commit and tracker update.
```

(End of P9. Evaluate P9 gate.)

### P10. Final reports and audit

#### P10.1 Final verification

```text
Preconditions:
  - P9 gate PASS.

Actions:
  1. Run full pytest suite: pytest tests/robust_asr/.
  2. Re-run validate_eval_table.py on every committed eval parquet.
  3. If ML-router path is active:
       a. Re-run validate_oracle_table.py on the oracle.
       b. Re-run validate_router_matrices.py on the router dir.
     If OUTCOME_E_DETERMINISTIC_SELECTOR is active:
       a. Re-run validate_selector_evidence.py on
          artifacts/robust_asr/router/selector_evidence.parquet.
       b. Confirm tracker.tasks[P6.2].status == SKIPPED_BY_OUTCOME_E.
     Exactly one of these branches must be active.
  4. Re-run verify_handoff_package.py --strict.
  5. Confirm tracker.claims_enabled.positive_lora and .positive_system
     are true or false (not 'pending').
  6. Confirm no claim depends on a disabled claims_enabled flag.
  7. Write reports/robust_asr/final_verification.md summarizing all
     branch-appropriate checks and pointing to each artifact.

Required deliverables:
  - reports/robust_asr/final_verification.md

Done when:
  - All branch-appropriate checks above PASS and final_verification.md
    exists.

Verification:
  pytest tests/robust_asr/
  python scripts/robust_asr/verify_handoff_package.py --strict --handoff artifacts/robust_asr/handoff
  test -f reports/robust_asr/final_verification.md
  The branch-appropriate validator from Action 3 must be run and
  recorded in reports/robust_asr/final_verification.md.

Stop condition:
  After commit.
```

#### P10.2 Final asset audit

```text
Preconditions:
  - P10.1 PASS.

Actions:
  1. Run final_asset_audit.py per Section 4.1.

Required deliverables:
  - reports/robust_asr/final_asset_audit.md

Done when:
  - final_asset_audit.py emits OK_FINAL_ASSET_AUDIT.

Verification:
  python scripts/robust_asr/final_asset_audit.py

Decision rules:
  1. Residual TODO_FILLED_IN_<task_id> for closed task: status = FAIL,
     return to that task to fill the placeholder.
  2. Mismatched SHA-256: status = FAIL, recompute and update tracker.
  3. Secret-like token detected: status = FAIL, remove and rewrite
     history if needed.

Stop condition:
  After OK_FINAL_ASSET_AUDIT and commit.
```

#### P10.3 Plan-tracker consistency

```text
Preconditions:
  - P10.2 PASS.

Actions:
  1. Run verify_plan_tracker_consistency.py per Section 4.1 against
     the orchestrator plan, this file, and the tracker.
  2. Set tracker.project_status = COMPLETE only after this passes.

Required deliverables:
  - reports/robust_asr/plan_tracker_consistency.md

Done when:
  - verify_plan_tracker_consistency.py emits OK_PLAN_TRACKER_CONSISTENCY.

Verification:
  python scripts/robust_asr/verify_plan_tracker_consistency.py \
    --plan-orchestrator docs/plans/robust_asr_orchestrator_plan_v3_4_7.md \
    --plan-agent docs/plans/robust_asr_agent_plan_v3_4_7.md \
    --tracker docs/progress/robust_asr_progress.yaml \
    --out reports/robust_asr/plan_tracker_consistency.md

Stop condition:
  After OK_PLAN_TRACKER_CONSISTENCY, tracker.project_status = COMPLETE,
  and commit. Evaluate P10 gate (Section 8). On PASS, write
  phase_summary.P10 = PASS and stop for the final orchestrator
  confirmation.
```


## 10. Final verification checklist

Datamove1-side completion (40 items). The remaining 3 items (41 to 43) are in the orchestrator plan Section 9 and require RP5-branch acknowledgment.

```text
1.  Branch feature/robust-asr-lora-router-datamove1-v1 pushed to origin.
2.  CLAUDE.md contains exactly one ROBUST_ASR_PROFILE block; the block
    body equals docs/profiles/CLAUDE.robust_asr.md; content outside the
    block was preserved; .gitattributes does not contain
    "CLAUDE.md merge=ours".
3.  docs/progress/robust_asr_progress.yaml parses; project_status == COMPLETE.
4.  reports/robust_asr/repository_inventory.md exists.
5.  reports/robust_asr/asset_inventory.md exists.
6.  reports/robust_asr/repo_integration_policy.md,
    reports/robust_asr/touch_policy.md, configs/robust_asr/
    reuse_policy_v1.yaml, and scripts/robust_asr/
    validate_report_shape.py exist; validate_report_shape.py emits
    OK_REPORT_SHAPE on the report fixtures; the policy files are
    referenced by tracker.repo_integration.
7.  reports/robust_asr/runtime_smoke.md exists; metadata exit_code == 0.
8.  reports/robust_asr/runtime_contract_smoke.md exists.
9.  artifacts/robust_asr/runtime_contract/rp5_request_fixture.json
    and rp5_response_fixture.json exist; pass --strict-skeleton.
10.  artifacts/robust_asr/runtime_contract/final_request_schema.json
    and final_response_schema.json exist; pass --strict-final.
11. docs/reports/robust_asr/model_card_lora.md exists; no residual
    TODO_FILLED_IN_<task_id> for closed tasks.
12. docs/reports/robust_asr/router_card.md exists; no residual
    TODO_FILLED_IN_<task_id> for closed tasks.
13. configs/robust_asr/data_v1.yaml, degradation_v1.yaml,
    lora_smoke.yaml, lora_full.yaml, router_v1.yaml, pricing_v1.yaml,
    runtime_v1.yaml, eval_manifests_v1.yaml exist.
14. tests/robust_asr/test_eval_schema.py PASS.
15. tests/robust_asr/test_normalization_metrics.py PASS.
16. tests/robust_asr/test_leakage.py PASS.
17. tests/robust_asr/test_degradation_v1.py PASS.
18. tests/robust_asr/test_router_runtime.py PASS.
19. artifacts/robust_asr/manifests/ contains LoRA train, router train,
    validation, locked test, OOD-real (or BLOCKED_OOD_PUBLIC marker
    with claims_enabled.ood_real == false).
20. artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet and
    degradation_v1_ood_param_eval.parquet exist.
21. artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet
    exists; validate_eval_table.py PASS.
22. artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet exists
    OR P4 SKIPPED_BY_DECISION_A or HALTED with documented reason.
23. artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet
    exists OR EXPORT_BLOCKED or skipped with documented reason.
24. artifacts/robust_asr/eval_tables/assemblyai.parquet exists OR
    BLOCKED_API with claims_enabled.cloud_tradeoff == false.
25. reports/robust_asr/baseline_whisper_base.md exists.
26. reports/robust_asr/lora/lora_smoke_report.md exists with
    PASS|PARTIAL|FAIL|HALTED on first line.
27. reports/robust_asr/lora/decision_a_smoke.md exists.
28. reports/robust_asr/lora/full_lora_eval.md exists with outcome on
    first line OR P4 skipped.
29. reports/robust_asr/lora/lora_ct2_int8_preservation.md exists with
    outcome on first line OR P4.3 skipped.
30. If ML-router path is active: artifacts/robust_asr/oracle/
    oracle_table.parquet exists and validate_oracle_table.py PASS.
    If OUTCOME_E_DETERMINISTIC_SELECTOR is active: artifacts/robust_asr/
    router/selector_evidence.parquet exists and
    validate_selector_evidence.py PASS.
31. If ML-router path is active: artifacts/robust_asr/router/
    router_train.parquet, router_val.parquet, router_test_locked.parquet
    exist and validate_router_matrices.py PASS. If
    OUTCOME_E_DETERMINISTIC_SELECTOR is active: P6.2 ==
    SKIPPED_BY_OUTCOME_E and router matrices are not required.
32. artifacts/robust_asr/router/selected_router/ contains the model
    artifact (Branch A) or deterministic_selector.json (Branch B)
    plus rp5_inference.py, metadata.json, test_vectors.json.
33. reports/robust_asr/router/router_final_eval.md OR
    reports/robust_asr/router/selector_final_eval.md exists with
    paired bootstrap CIs.
34. reports/robust_asr/system/system_eval.md exists with
    positive_system on first line.
35. artifacts/robust_asr/demo/demo_examples_manifest.json exists with
    8 examples.
36. artifacts/robust_asr/handoff/README.md exists with the 8 numbered
    sections in order; verify_handoff_package.py --strict PASS.
37. handoff/<date>-<short_sha> tag exists locally and on origin.
38. reports/robust_asr/final_verification.md exists.
39. reports/robust_asr/final_asset_audit.md exists; OK_FINAL_ASSET_AUDIT.
40. reports/robust_asr/plan_tracker_consistency.md exists;
    OK_PLAN_TRACKER_CONSISTENCY.
```

Once items 1 to 40 pass, the datamove1 side is complete. Cross-branch portfolio readiness (items 41 to 43) is the orchestrator's responsibility per the orchestrator plan Section 9.


## 11. Pointers

```text
Orchestrator plan: docs/plans/robust_asr_orchestrator_plan_v3_4_7.md
Tracker:           docs/progress/robust_asr_progress.yaml
Tracker prose:     docs/progress/robust_asr_progress.md
State capsule:     docs/progress/robust_asr_state_capsule.md
Report shapes:     docs/plans/state_packet_schemas_v1.yaml
Interaction protocol: embedded in this plan Section 0 and in the orchestrator plan Section 5.
Profile:           docs/profiles/CLAUDE.robust_asr.md
Repo root:         /mnt/fast/nobackup/users/gb0048/asr_enhancement
Source branch:     feature/training-datamove1-v1
Target branch:     feature/robust-asr-lora-router-datamove1-v1
RP5 branch:        feature/demo-runtime-rp5-v1 (consumed by tag, not by HEAD)
Slurm wrapper:     slurm/tools/on_submit.sh
Apptainer image:   /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif
```


## 12. Changelog

### v3.4.7 (this revision)

This revision closes four residual consistency issues identified in the
v3.4.6 review:

1. Makes the approval_packet schema explicitly require the single
   ORCHESTRATOR_DECISION wrapper expected by both plans.
2. Makes P10.1 branch-appropriate for ML-router versus
   OUTCOME_E_DETERMINISTIC_SELECTOR, so Outcome E no longer requires
   oracle or router matrices.
3. Corrects source-branch bootstrap failure handling: a halted P0.0
   report is superseded by a later successful P0.0 and does not cause
   P0.1 to record BLOCKED_SOURCE_BRANCH.
4. Updates stale schema header references from v3_4_4/v3_4_6 to
   v3_4_7.

### v3.4.6

This revision closes four cross-file consistency issues identified in
the v3.4.5 review:

```text
1. Adds the prebootstrap_inventory_report schema to
   docs/plans/state_packet_schemas_v1.yaml so that P0.0 can return a
   conformant report and validate_report_shape.py can pass its
   "Required schema keys exist" assertion.
2. Corrects tracker.artifacts.repository_inventory.produced_by_task
   from P0.0 to P0.1, since v3.4.5 made P0.0 strictly read-only and
   P0.1 materializes the on-disk inventory.
3. Adds tracker.artifacts entries for validate_report_shape_script
   and report_shape_fixtures so that P0.2 Action 11 can update them
   without writing to undefined keys.
4. Rewrites Section 2 rule 5 so that a missing source reference at
   P0.0 returns prebootstrap_status = HALTED in chat with no on-disk
   side effects, instead of writing reports/robust_asr/bootstrap_block.md.
   The bootstrap_block.md path is no longer used.
```

### v3.4.5

This revision closes three operational drift risks identified in the
v3.4.3 review:

```text
1. Moves the literal shape of every report (State Packet, Planning
   Report, Execution Report, Phase Gate Report, Approval Packet,
   Supplemental Evidence Report) into a shared YAML at
   docs/plans/state_packet_schemas_v1.yaml. Section 0 of this plan
   and Section 5 of the orchestrator plan reference that file instead
   of duplicating field lists.
2. Extends P0.0 with an inventory-only verification of
   origin/feature/demo-runtime-rp5-v1. A missing reference activates
   PENDING_RP5_INTEGRATION at P0 instead of waiting until P9.
3. Adds binding classification rules in P0.2 Action 6: legacy_state
   paths must be permitted_use: read_only with commit_allowed: false,
   not forbidden, so P10.3 plan_tracker_consistency can read them.
   Verification now enforces this at P0.2 close.
4. Updates the PENDING_RP5_INTEGRATION marker definition in Section 6
   to reflect activation at P0 or P10.
```

### v3.4.3

This revision closes the remaining discretionary integration points:

```text
1. Adds deterministic repository integration policy for existing plans,
   trackers, runtime code, tests, configs, data roots, caches, and
   checkpoints.
2. Replaces whole-file CLAUDE.md overwrite with a preserved
   ROBUST_ASR_PROFILE block update.
3. Makes P0.2 produce asset_inventory.md, repo_integration_policy.md,
   touch_policy.md, and reuse_policy_v1.yaml.
4. Requires all later tasks to cite reuse_policy_v1.yaml rows before
   reading or writing outside robust_asr-owned paths.
5. Adds tracker.repo_integration fields and plan-tracker consistency
   checks for reuse policy, CLAUDE.md block integrity, and unapproved
   reuse.
```

### v3.4.2

This revision keeps the two-plan split and adds a stricter execution
spine for the web-orchestrated workflow:

```text
1. Adds Section 0.1 with a single transition table and minimum
   shippable path.
2. Makes target-branch creation and recovery deterministic in P0.1.
3. Removes ambiguous OOM PARTIAL handling from P3.1.
4. Splits P6 into an oracle path for ML-router evidence and a selector
   evidence path for OUTCOME_E_DETERMINISTIC_SELECTOR.
5. Makes P7.1/P7.2 skippable only through SKIPPED_BY_OUTCOME_E.
6. Adds selector evidence validation and transition consistency checks.
```

### v3.4.1

This revision preserves the linear task queue and adds the real ChatGPT web workflow: Claude Code exports tracker-derived state through mandatory reports; ChatGPT returns Approval Packets in chat; Claude records them in the live tracker before continuing. It adds state_transport tracker fields, a state capsule, task reports, and explicit PLANNING/EXECUTION/CLOSURE_FIX/PHASE_APPROVAL_RECORDING/SUPPLEMENTAL_EVIDENCE modes.

### v3.4.0

```text
1. Split into orchestrator + agent. This file is the agent-facing spine.
2. Section 1B + 1C + 17 + 18 of v3.3.6 collapsed into Section 8
   (phase gate predicates) here, with one routing per gate.
3. Every "if available" / "if compute access allows" / "if a longer-
   running queue" replaced by deterministic predicates: see Section
   1.1 (OOD fallback predicate), 5.4 (router decision), 5.5
   (deterministic selector with assemblyai_available probe), 5.8
   (OOM/timeout/preemption with explicit retry counts and exit codes),
   5.9 (corruption/degeneracy/non-monotonicity), 5.10 (fallback
   triggers), 4.8 (resolve_long_running_queue.py).
4. Section 5A of v3.3.6 (8 validator contracts) extended in Section 4
   to ~30 scripts. Every script has Inputs, Outputs, Asserts, Stdout,
   Exit code. Standardized exit codes:
       0  PASS
       1  generic FAIL
       2  CUDA_OOM_AT_BATCH_SIZE_1
       3  NON_FINITE_LOSS_THRESHOLD_EXCEEDED
       4  DEGENERATE_SMOKE_RESULT
       5  CT2_UNSUPPORTED_VERSION_OR_OP
       6  PREEMPTED_AT_STEP_<n>
       7  ALL_CHECKPOINTS_UNUSABLE
       8  ASSEMBLYAI_API_KEY_UNSET
       9  ASSEMBLYAI_AUTH_FAIL
      10  ASSEMBLYAI_QUOTA
      11  ALL_CANDIDATES_DEGENERATE
      12  NO_CANDIDATE_BEATS_BASELINE
      13  NO_LONG_RUNNING_QUEUE_AVAILABLE
5. Stop condition added to every Section 9 task: "what makes the agent
   stop and return control to the orchestrator (or to the next task,
   under continue_through_gates)".
6. Marker definitions table (Section 6) made computable:
   active iff <predicate>, cleared when <predicate>.

Lineage: same as the orchestrator plan Section 12.
```
