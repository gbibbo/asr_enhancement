# B14.0 Plan Revision Report — B14_0-00 Validator IDs

revision_scope: plan_authoring_revision (targeted)
preceded_by: B14.0 APPROVED_FOR_EXECUTION recording commit 385b11c6227644f8f73ef4e70b66dc704e141a15
revision_decision: APPROVE_TARGETED_REVISION
required_fix: explicitly declare B14.0-aware wrapper validators for B14_0-00 instead of reinterpreting inherited B-route validator ids at execution time
files_modified: docs/plans/b14_0/agent_plan.md (only)
files_unchanged: docs/plans/b14_0/orchestrator_plan.md, docs/plans/b14_0/state_packet_schemas.yaml (schema references did not need updating; both still carry APPROVED_FOR_EXECUTION)

## Revision Applied

| Section | Change |
|---|---|
| §0 validators list | Added two explicit wrapper validator ids at the top of the list: validate_b14_0_plan_compile (script scripts/rp5/validate_b14_0_plan_compile.py) and validate_b14_0_path_locks (script scripts/rp5/validate_b14_0_path_locks.py). Removed validate_plan_compiles and validate_changed_files_against_path_locks from the active validators list and moved them into a new `inherited_validators_context_only` annotation block so the historical lineage is preserved without implying direct execution by any B14.0 task |
| §1 path-lock table | Replaced the six per-row validator commands. Five rows previously named per-lock scripts that did not match the PL-B14_0-SCRIPTS pattern (validate_path_lock_pl_b14_0_*.py); two rows pointed at the inherited B-route umbrella. All six rows now invoke scripts/rp5/validate_b14_0_path_locks.py with the appropriate --lock <id> selector. The lock pattern and max_changed_files columns are unchanged |
| §7 final verification (FV-PLAN) | Changed `validate_plan_compiles --plan-dir docs/plans/b14_0` to `validate_b14_0_plan_compile --plan-dir docs/plans/b14_0`; sentinel OK_PLAN_COMPILES and deliverable reports/rp5/b14_0_plan_compile.md unchanged |
| §8 path lock contract closure command | Changed the closure command from `python scripts/rp5/validate_changed_files_against_path_locks.py ...` to `python scripts/rp5/validate_b14_0_path_locks.py ...`; sentinel OK_CHANGED_FILES_PATH_LOCKED and failure marker UNAUTHORIZED_FILE_TOUCHED unchanged; added a sentence stating that the inherited B-route umbrella is not invoked by any B14.0 task because its PATH_LOCKS list only enumerates PL-BR-* lock ids |
| §9 validator contracts narrative | Reworded the reuse paragraph so reusable B-route protocol validators (validate_report_shape, validate_approval_packet, print_tracker_state, validate_future_constraints, validate_no_banned_phrases, validate_public_security_invariants) are explicitly invoked directly (these read declarative schema/HAR/tracker inputs without B-route-hardcoded knowledge), while the two B14.0 wrappers replace the inherited scripts that did carry such hardcoded knowledge. Added a paragraph describing the wrappers' must_check parametric extension and the PATH_LOCKS list that validate_b14_0_path_locks populates |
| §10 B14_0-00 task contract | Rewrote the row so the action text explicitly enumerates the two wrapper scripts to be created, the deliverable commands `python3 scripts/rp5/validate_b14_0_plan_compile.py --plan-dir docs/plans/b14_0 --out reports/rp5/b14_0_plan_compile.md` and `python3 scripts/rp5/validate_b14_0_path_locks.py --diff HEAD~1..HEAD --out reports/rp5/path_lock_validation.md`, the validator ids validate_b14_0_plan_compile and validate_b14_0_path_locks with their sentinels and failure markers (PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP for the plan-compile wrapper; UNAUTHORIZED_FILE_TOUCHED for the path-locks wrapper). The Done-when condition (OK_PLAN_COMPILES + OK_CHANGED_FILES_PATH_LOCKED) and the stop_after column (execution_report) are unchanged |
| §11 recovery packets | Updated diagnosis commands in RP-PLAN-CONFLICT, RP-EXECUTION-RAIL-GAP, RP-PATH-LOCK-TOO-BROAD, RP-VALIDATOR-MATERIALIZATION-GAP, RP-RECOVERY-PACKET-GAP, and RP-UNAUTHORIZED-FILE-TOUCHED from inherited script paths to the wrapper paths (scripts/rp5/validate_b14_0_plan_compile.py and scripts/rp5/validate_b14_0_path_locks.py). The marker, retry_limit, allowed_inspect/modify columns, and next-state columns are unchanged |

Sections explicitly not changed in this revision:
- §0 entity registry (tasks, markers, artifacts, claims, phases) — unchanged
- §2 constants and decision rules — unchanged
- §2.1 threshold audit — unchanged
- §3 marker registry — unchanged
- §4 linear transition table — unchanged (B14_0-00 still PASS→B14_0-01 / FAIL→stop with PLAN_CONFLICT or VALIDATOR_MATERIALIZATION_GAP)
- §5 tracker schema and runtime state — unchanged
- §6 phase gate predicates reference — unchanged
- §9.1 fixture-generator table — unchanged (the wrappers do not need a paired fixture generator at this draft because they replicate inherited logic; if review requires fixture coverage for the wrappers, it can be added inside B14_0-00 execution under PL-B14_0-SCRIPTS)
- §12 security and forbidden scope — unchanged
- §13 report skeletons — unchanged
- §14 banned phrases scan — unchanged
- §15 HAR-B14_0-RECRUITER-CREDS-001 — unchanged
- §16 authoring status — unchanged (APPROVED_FOR_EXECUTION)
- §17 adversarial stress-replay — unchanged
- B14_0-01 through B14_0-08 task contract rows — unchanged

## Files Changed

| Path | Action |
|---|---|
| docs/plans/b14_0/agent_plan.md | modified (§0, §1, §7, §8, §9, §10, §11) |
| reports/rp5/b14_0_plan_revision_b140_00_validators.md | created |

## Validation Checks

| Check | Result |
|---|---|
| B14_0-00 task contract explicitly names both wrapper validator ids (validate_b14_0_plan_compile, validate_b14_0_path_locks) with scripts, commands, sentinels, and markers | PASS |
| No remaining B14_0-00 command requires running scripts/rp5/validate_plan_compiles.py directly | PASS (the only remaining mentions are inside the §0 inherited_validators_context_only block and the §8 explanatory sentence; neither is an execution command) |
| No remaining B14_0-00 command requires running scripts/rp5/validate_changed_files_against_path_locks.py directly | PASS (same context-only mentions; not executed by any task) |
| 22 references to the wrapper ids/paths across the agent_plan | PASS (greater than zero confirms wrappers are wired in §0, §1 six rows, §7 FV-PLAN, §8 closure, §9 narrative, §10 B14_0-00 row, §11 recovery packets) |
| Marker count agent_plan §0 == orchestrator_plan §6 == recovery packets §11 | PASS (21/21/21) |
| All three B14.0 plan files retain APPROVED_FOR_EXECUTION | PASS (orchestrator_plan 2, agent_plan 2, state_packet_schemas 1; zero DRAFT_NOT_APPROVED_FOR_EXECUTION hits across the three files) |
| Tracker docs/progress/rp5_progress.yaml unchanged | PASS (current_phase=B14.0, current_task=B14_0-00, markers=[]) |
| No B14.0 implementation files created | PASS (scripts/rp5/validate_b14_0_plan_compile.py and scripts/rp5/validate_b14_0_path_locks.py do not exist on disk; they remain B14_0-00 execution artifacts) |
| docs/plans/broute/ untouched | PASS (git diff --stat empty) |
| No real RECRUITER_USERNAME or RECRUITER_PASSWORD value committed | PASS |
| No literal non-loopback URL committed | PASS |
| B14_0 task sequence (B14_0-00 → B14_0-08) unchanged beyond validator-id clarification | PASS |

## Gate Reminder

B14_0-00 still cannot start until an APPROVE_PLAN decision is recorded for it. HAR-B14_0-RECRUITER-CREDS-001 remains pre_declared_unresolved and blocks B14_0-02 closure only.

## Result

OK_B14_0_PLAN_REVISION_B14_0_00_VALIDATORS_COMPLETE
