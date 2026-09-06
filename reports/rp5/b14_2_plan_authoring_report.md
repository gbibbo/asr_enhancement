# B14.2 Plan-Authoring Report

Task: B14_2-PLAN-AUTHORING
Phase: B14.2 (repair microphase)
Branch: feature/demo-runtime-rp5-v1
Record type: plan-authoring report
Plan state authored: DRAFT_NOT_APPROVED_FOR_EXECUTION

## Purpose

This file is the B14.2 plan-authoring deliverable. It records the authoring of a new self-contained B14.2 repair-microphase plan package addressing the public-surface recruiter HTTPBasic gate regression `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` routed from B15 under `decision_rule_routing=RETURN_TO_B14`. It accompanies, but does not by itself approve, the three plan files. No implementation has started; no tracker mutation has been performed; no public-network command has been run; the carried marker remains active; predecessor canonical files and reports are frozen; no public-exposure success claim is asserted; the secondary observation `upload_with_manual_ground_truth=FAIL` carried from B15-05 is preserved verbatim and routed to B14_2-05 classification rather than absorbed.

## Plan package authored (sha256 per file)

| Path | Line count | sha256 |
|---|---:|---|
| docs/plans/b14_2/orchestrator_plan.md | 294 | 58408413b6a79f51f8d8d3e75d3cfd46aab01651415f20a820b6202d541f5233 |
| docs/plans/b14_2/agent_plan.md | 672 | b70b5254c15c1e355dbfba2423cfea86f08e850c24c34ef9e5950ce7122e01d6 |
| docs/plans/b14_2/state_packet_schemas.yaml | 295 | 31fd1df0a6cd0e0ff5bbbf8918483e2c837faba4199774c103554c95e85d29ca |

Plan-authoring deliverable: this file, `reports/rp5/b14_2_plan_authoring_report.md`. The approval-packet wrapper `reports/rp5/b14_2_plan_approval_packet.yaml` is NOT authored by this task; per the established repository convention (verified against `reports/rp5/b15_plan_approval_packet.yaml` authored at commit `af52260` by the orchestrator APPROVE_FOR_EXECUTION recording, and `reports/rp5/b14_1_plan_approval_packet.yaml` authored similarly), plan-authoring tasks do not write the approval-packet file; the orchestrator approval recording is the sole writer.

## Predecessor state recorded in the plan

- B-route: APPROVED (`accepted_phase_gate_report_commit 4a4f8e4b20ff3ff5f19647e7ec1f723f6492df25`, `accepted_tracker_closure_commit e6c5aec9139a436e75f783d1df2707d25b385346`).
- B14.0: APPROVED (`accepted_phase_gate_report_commit 7e9ce1f7067f938d2b58a7a4e8615101b0012c58`, `accepted_tracker_closure_commit 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8`).
- B14.1: APPROVED through the explicit-blocker branch only (`accepted_phase_gate_report_commit f2a64d5619e34db99802595c0ce4ea9ae2e2d5f1`, `accepted_tracker_closure_commit 360bc2bd8a3d7d42a1886d82cccd3f77b5de7d84`).
- B15: REJECTED via PHASE_REJECT (`accepted_phase_gate_report_commit 6bcfaee57df7a1e8f7026916b472559b3cadcbbc`, `accepted_tracker_closure_commit bf8560a6c3493692ccd8a35926a5ddc647b627f6`); `decision_rule_routing RETURN_TO_B14`; `claim_status FAILED_PENDING_PHASE_RETURN`; `full_success_branch FORECLOSED`; `explicit_blocker_branch NOT_REACHED`; `failed_pending_phase_return_branch REACHED`.
- Active carried marker: `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`.
- B15-05 operator observations (preserved verbatim by reference): `recruiter_gate_observed_status: unauthenticated_access_observed` on all four vantage points; `upload_with_manual_ground_truth: FAIL` on all four vantage points.

## B14.2 scope recorded in the plan

- Primary objective: restore the application-layer recruiter HTTPBasic gate as the sole authority for the public Funnel-exposed `/demo/*` surface.
- Verification mechanism: a fresh operator-supplied four-vantage-point public-surface re-smoke under the new HAR `HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001`.
- Secondary observation handling: `upload_with_manual_ground_truth=FAIL` carried from B15-05 is preserved verbatim and classified at `B14_2-05` from `B14_2-04` evidence per the deterministic rule encoded in `docs/plans/b14_2/agent_plan.md` section 2 `upload_with_gt_classification_rule`. Possible classifications: `linked_to_gate`, `independent_defer`, `re_smoke_evidence_pending`. `independent_defer` emits a `secondary_observation_routing_request_record` requesting orchestrator routing; B14.2 does not route the secondary observation.
- Phase-gate predicates: PHASE_APPROVE only on the gate-restored branch (all four re-smoke records `authenticated_access_only` with non-null `evidence_reference` and `RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE` PASS) or on the blocked branch (B14_2-04 BLOCKED_BY_HUMAN_ACTION citing the new HAR). FAILED_PENDING_PHASE_RETURN otherwise.
- Carried-marker clearance policy: clearable only by the orchestrator PHASE_APPROVE recording on the gate-restored branch. Never by plan authoring, never by B14_2-00..B14_2-06 task closures, never by a scope-change repair, never by a PHASE_REJECT recording.
- B14.2 cannot assert `SUCCESS_WITH_STABLE_NAMED_EXPOSURE`; that claim shape is reserved for the B15 success-claim record shape and is not legal in any B14.2 record.

## Task sequence summary

| Task | Action title | Stop condition |
|---|---|---|
| B14_2-00 | Bootstrap the two B14.2 wrapper validators (`validate_b14_2_plan_compile`, `validate_b14_2_path_locks`) and emit `reports/rp5/b14_2_plan_compile.md` | OK_PLAN_COMPILES + OK_CHANGED_FILES_PATH_LOCKED |
| B14_2-01 | Declarative diagnostic of the public-surface recruiter-gate regression; cites B15-05 evidence by reference; no public-network commands; no edits to predecessor reports | OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC + OK_CHANGED_FILES_PATH_LOCKED |
| B14_2-02 | Application/config repair restoring end-to-end recruiter HTTPBasic gate authority on the public Funnel-exposed surface; allowed surfaces are PL-B14_2-API-DEMO, PL-B14_2-TUNNEL-TEMPLATE (placeholders only), PL-B14_2-CONFIG (placeholders only); loopback verification of application-layer-gate and no-network-trust invariants under PUBLIC_DEMO_EXPOSURE=true | OK_B14_2_APPLICATION_LAYER_GATE + OK_B14_2_NO_NETWORK_TRUST_AUTHORITY |
| B14_2-03 | Local verification re-emitting recruiter-gate-preserved, health-payload-preserved, OpenAPI-docs-visibility, no-public-URL, no-tunnel-secret, and broute-compatibility sentinels against loopback under PUBLIC_DEMO_EXPOSURE=true | every loopback OK sentinel |
| B14_2-04 | HAR-gated four-vantage-point operator public-surface recruiter-gate re-smoke; records four `public_surface_recruiter_gate_resmoke_record` entries verbatim from operator-supplied HAR result; literal URL, hostname, secret, IP never recorded | OK_B14_2_PUBLIC_SURFACE_RECRUITER_GATE_RESMOKE iff all four records report `authenticated_access_only` with non-null `evidence_reference` |
| B14_2-05 | Upload-with-GT secondary-observation classification deterministically derived from the four B14_2-04 records | OK_B14_2_UPLOAD_WITH_GT_CLASSIFIED |
| B14_2-06 | B14.2 phase-gate report, future-constraint records (six FCs including the new FC-B15-FROZEN), `b14_2_public_surface_claim_record`, and `RP-B15-RECRUITER-GATE-REGRESSION-UNDER-PUBLIC-SMOKE` recovery-packet record | every FV-* OK sentinel; carried marker preserved in this report; clearance deferred to the subsequent orchestrator PHASE_APPROVE recording on the gate-restored branch |

## HARs and marker-clearance policy

Carried (recorded as resolved at B14.2 plan-authoring time):

- `HAR-B14_1-STABLE-HOSTNAME-001`: resolved by-reference; the literal hostname is never recorded.
- `HAR-B14_1-FUNNEL-CAPABILITY-001`: resolved by-reference; the auth-key value is never recorded; restart-policy string and env-var name are the only recorded fields.
- `HAR-B15-MULTI-NETWORK-SMOKE-001`: resolved with the operator observation set preserved verbatim; consumed by reference at B14_2-01 and B14_2-05.

New, pre-declared:

- `HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001` (`pre_declared_unresolved`): supplies the four `public_surface_recruiter_gate_resmoke_record` entries at B14_2-04. Blocks B14_2-04 closure and blocks any clearance of the carried marker until resolved. The operator supplies enum values, boolean flags, and non-secret `evidence_reference` and `resmoke_run_timestamp_utc` tokens only; the agent transcribes outcomes verbatim and runs no public-network command.

Conditional:

- `HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001` (`pre_declared_conditional`): fires only when B14_2-04 leaves the upload-with-GT classification undecidable from the four resmoke records alone (i.e. only under the `re_smoke_evidence_pending` classification path or when the operator must supply per-vantage classification tokens to disambiguate between `linked_to_gate` and `independent_defer`).

Marker clearance:

- The carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` is preserved active through plan authoring, B14_2-00 through B14_2-06 task closures, every scope-change repair, and a B14.2 PHASE_REJECT recording.
- The marker becomes eligible for clearance only when the B14_2-06 `b14_2_recovery_packet_b15_recruiter_gate_record` records `carried_marker_eligible_for_clearance_at_phase_approval: true` (which requires `all_four_authenticated_access_only` and `all_four_evidence_reference_non_null` both true).
- The marker is removed from `tracker.markers` only by the orchestrator PHASE_APPROVE recording on the gate-restored branch. No B14.2 task closure performs the clearance.
- Out-of-band clearance attempts fire `B14_2_CARRIED_MARKER_CLEARED_OUT_OF_BAND` and stop with `STOP_SCOPE_CONFLICT`.

## upload_with_manual_ground_truth handling

The B15-05 operator observation `upload_with_manual_ground_truth: FAIL` on all four vantage points is preserved verbatim in `human_action_requests.HAR-B15-MULTI-NETWORK-SMOKE-001` (frozen). B14.2 does not edit that record. The repair pipeline handles it as follows:

1. B14_2-01 cites the B15-05 observations by reference in the declarative diagnostic.
2. B14_2-04 requires the operator re-smoke records to include `coverage_item_outcomes.upload_with_manual_ground_truth` per vantage point.
3. B14_2-05 derives the classification deterministically from the four B14_2-04 records under the section 2 `upload_with_gt_classification_rule`:
   - `linked_to_gate`: every B14_2-04 record reports `recruiter_gate_observed_status: authenticated_access_only` AND `upload_with_manual_ground_truth: PASS` on every vantage point; the gate fix is sufficient; the secondary observation is cleared inside B14.2 as a downstream effect.
   - `independent_defer`: every B14_2-04 record reports `recruiter_gate_observed_status: authenticated_access_only` AND any vantage point reports `upload_with_manual_ground_truth: FAIL`; the observation is independent of the gate fix; a `secondary_observation_routing_request_record` is emitted requesting orchestrator routing; B14.2 does not route it.
   - `re_smoke_evidence_pending`: any B14_2-04 record reports `recruiter_gate_observed_status: unauthenticated_access_observed`; classification deferred; the carried marker remains active and the conditional HAR may fire.
4. Asserting `linked_to_gate` while any vantage point reports `upload_with_manual_ground_truth: FAIL` fires `B14_2_UPLOAD_WITH_GT_SILENT_ABSORPTION` and blocks closure.

No `FAIL` is converted to `PASS` without matching B14_2-04 evidence. No cause is inferred from absent evidence.

## Validation results

Local consistency scan and parse:

| Check | Command | Result |
|---|---|---|
| YAML parse for state_packet_schemas.yaml | `python3 -c "import yaml; yaml.safe_load(open('docs/plans/b14_2/state_packet_schemas.yaml'))"` | OK_YAML_PARSE |
| Every task B14_2-00..B14_2-06 appears in task table and transition table | grep both tables | OK_TASK_TABLE_AND_TRANSITION_TABLE_COMPLETE |
| Every HAR has marker, missing_inputs, why_human_only, allowed_values_or_schema, blocks, created_by_task, next_state_until_result, forbidden_agent_action, result_expected_at | inspection of agent_plan section 15 YAML blocks for both HARs | OK_EVERY_HAR_HAS_REQUIRED_FIELDS |
| Every marker used in transitions appears in marker registry | cross-reference agent_plan section 0 markers list, section 4 transition table, orchestrator_plan section 6 marker registry | OK_EVERY_TRANSITION_MARKER_IN_REGISTRY |
| Every validator named in task contracts appears in validator contract section | cross-reference agent_plan section 0 validators list, section 7 FV table, section 9.1 fixture generator table, section 10 task contracts | OK_EVERY_TASK_CONTRACT_VALIDATOR_IN_REGISTRY |
| Every future constraint named in the phase gate appears in the future-constraint section | cross-reference orchestrator_plan section 3 phase_gate_pass_*_iff predicates and section 3 FC table | OK_EVERY_PHASE_GATE_FC_IN_FC_TABLE |
| Banned-phrase scan over the three plan files and this report | the scan command specified by the task description, piped through `grep -v 'section_14\|banned_phrases\|forbidden_orchestrator_outputs'` per the documented filter inherited from B-route agent_plan section 14 and applied in the B14.1 and B15 plan-authoring reports | zero substantive matches; the only raw hit is `docs/plans/b14_2/agent_plan.md` section 14 which carries the scan-command definition itself and is filtered by the documented-filter convention |
| Secret/literal scan over the same files | scan for public URL, non-loopback IP literal, Tailscale auth-key prefix, Cloudflare token shape, recruiter or admin password literal, stable hostname literal | zero matches; only allowed loopback `http://127.0.0.1:8001` references in validator-command strings |
| git diff --name-only authorized-files audit | `git diff --name-only` against the staged set | only four authorized files: docs/plans/b14_2/orchestrator_plan.md, docs/plans/b14_2/agent_plan.md, docs/plans/b14_2/state_packet_schemas.yaml, reports/rp5/b14_2_plan_authoring_report.md |

The B14.2 implementation validators (`validate_b14_2_*.py`) are not invoked here because they do not yet exist; they are authored by B14_2-00 implementation, which is forbidden by this plan-authoring task. No public-network commands were run.

## Freeze and forbidden-path audit

- `docs/plans/broute/**`: untouched.
- `docs/plans/b14_0/**`: untouched.
- `docs/plans/b14_1/**`: untouched.
- `docs/plans/b15/**`: untouched.
- `reports/rp5/broute_*.md`, `reports/rp5/b14_0_*.md`, `reports/rp5/b14_1_*.md`, `reports/rp5/b15_*.md`: untouched.
- `libs/asr/router_runtime.py`: untouched.
- `services/frontend/app/demo/types.ts`: untouched.
- `services/**`, `libs/**`, `infra/**`, compose files, runtime code: untouched.
- `scripts/**`, `tests/**`: untouched (no implementation in this task).
- `docs/progress/rp5_progress.yaml`: untouched.

The plan declares two protection layers for the freeze: the umbrella path-lock validator `validate_b14_2_path_locks` (to be materialized at B14_2-00) which rejects any predecessor-canonical-file touch with marker `B14_2_PREDECESSOR_FILE_TOUCHED`, and the declarative future-constraint set including `FC-BROUTE-FROZEN` (covers B-route, B14.0, B14.1) and the new `FC-B15-FROZEN` (added in this plan; validated by `validate_future_constraints --constraint-profile b14_2` after the deferred scope-change repair recorded in agent_plan section 20).

## Tracker mutation status

No tracker mutation performed by this plan-authoring task. `docs/progress/rp5_progress.yaml` remains at its current values:

- `current_phase: B15`
- `current_task: B14_RETURN_PENDING_ORCHESTRATOR_PLAN_AUTHORING`
- `last_completed_task: B15-07`
- `last_completed_phase: B15`
- `markers: [B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE]`
- `phase_approvals.B15.status: REJECTED`
- `phase_approvals.B15.return_target_exact_phase_or_task_id: PHASE_RETURN_TARGET_AMBIGUOUS_PENDING_ORCHESTRATOR_DECISION`

Per the established convention (B14.1 plan-authoring at commit `4bd54c2` recorded the authored plan files and the plan-authoring report without mutating the tracker; the subsequent orchestrator `APPROVE_FOR_EXECUTION` decision then advanced the tracker), tracker mutation is deferred to a future orchestrator decision recording. The expected mutation shape after an `APPROVE_FOR_EXECUTION` decision is documented in `docs/plans/b14_2/agent_plan.md` section 5 and section 17 (`tracker_advance_policy`).

## Explicit assertions

- No tracker mutation performed by this task.
- No implementation started; no B14_2-NN task deliverable created.
- No validator script, fixture generator, test, service-code change, tunnel-config change, or runtime change authored.
- The carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` remains active and is not cleared by this task.
- The B15 operator observation `recruiter_gate_observed_status: unauthenticated_access_observed` is preserved verbatim by reference; no record in this plan package converts it to `authenticated_access_only`.
- The B15 operator observation `upload_with_manual_ground_truth: FAIL` is preserved verbatim by reference and routed to deterministic classification at B14_2-05; no record in this plan package converts it to `PASS`.
- No public-exposure success claim is asserted. `SUCCESS_WITH_STABLE_NAMED_EXPOSURE` is explicitly omitted from the `b14_2_public_surface_claim_record` schema enum.
- No public-network commands were run (no Funnel, Tailscale, Cloudflare, ngrok, systemd, Docker Compose, curl against a non-loopback URL, browser test, or public endpoint check).
- No literal public URL, hostname, IP address, auth-key, Cloudflare token, recruiter password, admin password, or other secret was written into any authored file. Only loopback `http://127.0.0.1:8001` references appear inside validator-command strings.
- Predecessor canonical files and reports remain frozen verbatim.
- `reports/rp5/b14_2_plan_approval_packet.yaml` is NOT authored by this task; the file is reserved for the orchestrator `APPROVE_FOR_EXECUTION` recording per the established convention. This is the only ambiguity-resolution decision recorded by this report.

## Notes for the orchestrator

- The user-provided orchestrator decision string for the plan-authoring authorization used the enum value `APPROVE_PLAN_AUTHORING_EXECUTION`, which is not present in the inherited `approval_packet.decision` enum set in `docs/plans/b14_2/state_packet_schemas.yaml` (which mirrors the B15 enum: `[APPROVE_PLAN, REVISE_PLAN, STOP_SCOPE_CONFLICT, CLOSE_TASK, CLOSE_TASK_WITH_OBSERVED_REGRESSIONS, FIX_BEFORE_CLOSE, PHASE_APPROVE, PHASE_REJECT, CHANGE_SCOPE, REQUEST_PLAN_AUTHORING, APPROVE_FOR_EXECUTION]`). The closest canonical values are `REQUEST_PLAN_AUTHORING` (request to author the plan package) and `APPROVE_FOR_EXECUTION` (acceptance of the authored package). This plan package was authored against the intent of `REQUEST_PLAN_AUTHORING`; the subsequent orchestrator decision that accepts this package should use the canonical `APPROVE_FOR_EXECUTION` value, or extend the schema enum via `CHANGE_SCOPE`.
- The deferred validator-profile scope-change repair `RP-VALIDATOR-PROFILE-GAP-B14_2-06` (documented in `docs/plans/b14_2/agent_plan.md` section 20) follows the precedent of `recovery_log.RP-VALIDATOR-PROFILE-GAP-B15-07`. It must be recorded before `B14_2-06` executes `validate_future_constraints --constraint-profile b14_2`, otherwise `FV-FUTURE` is unreachable.
- The B14.2 phase-gate `next_phase` after a gate-restored-branch PHASE_APPROVE is intentionally left at `PENDING_ORCHESTRATOR_INSTRUCTION`. After clearance of the carried marker, the orchestrator decides whether the next phase is a B15 re-execution, a continuation, or a brand-new phase.
- Risks and PLAN_CONFLICT candidates: none detected in this authoring step. The plan does not edit any predecessor canonical file. The only authorized edit outside the plan tree (in a future task) is the `validate_future_constraints.py` profile extension, which is governed by the section 20 scope-change repair.
