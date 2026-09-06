# B14.1 Plan Authoring Report

authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
preceded_by: B14.0 phase approval commit 0bdaea89c665dd5cabd7904556dbf536ef409f9f (accepted_phase_gate_report_commit 7e9ce1f7067f938d2b58a7a4e8615101b0012c58; accepted_tracker_closure_commit 7730a4f53744eeb99d118f6f5b283c2f1c35dfc8)
plan_authoring_decision_input: ORCHESTRATOR_DECISION scope=plan_authoring, phase=B14.1, decision=REQUEST_PLAN_AUTHORING, accepted_report_commit=0bdaea89c665dd5cabd7904556dbf536ef409f9f, next_expected_task=B14.1_PLAN_AUTHORING, required_fix=null
blocker_addressed: NEXT_PHASE_PLAN_MISSING (docs/plans/b14_1/ absent)

## Files Created

| Path | Authority surface |
|---|---|
| docs/plans/b14_1/orchestrator_plan.md | approval protocol, phase gate authority, hard stops, final closure, marker registry, forbidden public regressions extended for application-layer-gated public exposure, audit checklist, communication rules, cross-document conflict resolution |
| docs/plans/b14_1/agent_plan.md | manifest and entity registry, branch layout and seven B14.1 path locks (incl. PL-B14_1-TUNNEL-TEMPLATE), constants and decision rules (PUBLIC_DEMO_EXPOSURE flag, application-layer authority invariants, openapi/docs visibility, local-bypass justification), marker registry, linear transition table, tracker schema and mutation rules, phase gate predicates reference, final verification checklist (FV-PLAN through FV-FUTURE), validator and fixture-generator contracts, B14_1-00 through B14_1-08 task contracts, recovery packets per marker, security and forbidden scope, report skeletons, banned-phrase scan, HAR-B14_1-FUNNEL-CAPABILITY-001 and HAR-B14_1-STABLE-HOSTNAME-001, context-window hygiene policy, authoring-status gate, adversarial stress-replay |
| docs/plans/b14_1/state_packet_schemas.yaml | schema_version, drift handling, schema constraints, inherited shapes (state_packet, planning_report, execution_report, phase_gate_report, approval_packet, supplemental_evidence_report, human_action_*, path_lock_record, security_invariant_record, blocking_marker_recovery_record, tracker_task_record, artifact_record, orchestrator_approval_record, future_constraint_preservation_record, phase_approval_record), B14.1-specific records (public_exposure_artifact_record, application_layer_gate_invariant_record, exposure_state_record, openapi_docs_visibility_record, local_bypass_justification_record, public_exposure_claim_record, context_window_hygiene_record) |

## Plan Status

- All three plan files carry the DRAFT_NOT_APPROVED_FOR_EXECUTION marker.
- Authority split mirrors the B-route and B14.0 plan packages.
- B14.0 future-constraint preservation seam (FC-B14-1-FUNNEL) is converted into executable task contracts B14_1-01 (exposure state and HAR declarations), B14_1-02 (application-layer gate invariants under public exposure), B14_1-03 (recruiter gate / health / openapi-docs preserved), B14_1-04 (tunnel template, placeholders only), B14_1-05 (local-bypass justification), B14_1-06 (no-tunnel-secret-leak), B14_1-07 (B-route and B14.0 compatibility under public exposure), and B14_1-08 (phase gate with deterministic stable-named exposure or explicit blocker).
- FC-B14-1-FUNNEL, FC-B15-MULTI-NETWORK, FC-HANDOFF-DATAMOVE1, FC-BROUTE-FROZEN, and FC-B14-0-GATE-PRESERVED are preserved as future-constraint preservation records in orchestrator_plan §3 and explicitly forbidden in agent_plan §12 where regression would occur.
- Linear task sequence B14_1-00 through B14_1-08 with explicit preconditions, deliverables, validators, and stop conditions.
- The phase gate cannot pass on an ephemeral URL alone: public_exposure_claim_record requires claim_status=SUCCESS_WITH_STABLE_NAMED_EXPOSURE with stable_named_exposure_supplied_by_reference=true and explicit_blocker_id=null, or claim_status starting with BLOCKED_ with a non-null explicit_blocker_id pointing to HAR-B14_1-FUNNEL-CAPABILITY-001 or HAR-B14_1-STABLE-HOSTNAME-001.
- Funnel/public-exposure work is gated by application-layer recruiter HTTPBasic authority, not by network trust: invariant validate_b14_1_no_network_trust_authority forbids any application-layer authority decision keyed on client IP, source interface, Tailscale identity, X-Forwarded-For, or any header the public surface cannot independently authenticate.
- PUBLIC_DEMO_EXPOSURE=false may allow local/dev bypass only when paired with a test that asserts the bypass is disabled when PUBLIC_DEMO_EXPOSURE=true; PUBLIC_DEMO_EXPOSURE=true forbids bypass.
- OpenAPI and interactive docs are unmounted by default under PUBLIC_DEMO_EXPOSURE=true; a narrow admin-only exception is opt-in and recorded inside reports/rp5/b14_1_openapi_docs_visibility.md, mounted behind the existing admin HTTPBasic realm.
- No B15 multi-network smoke claim is made from B14.1; no datamove1 handoff implementation occurs; no router schema change occurs; no B-route rollback occurs.
- No real Tailscale auth-key, Cloudflare token, recruiter password, admin password, public URL, or stable hostname literal is committed; .env.example placeholders and PL-B14_1-TUNNEL-TEMPLATE placeholders only.
- The tunnel run-as-service action (systemd unit install) is host-only and operator-owned: the unit template content may be authored at PL-B14_1-TUNNEL-TEMPLATE with placeholders, but the install action is not a B14.1 closure deliverable; the operator action is captured by HAR-B14_1-FUNNEL-CAPABILITY-001.
- No B14.1 implementation files were created in this authoring step (no scripts/rp5/validate_b14_1_*.py, no services/api/app changes, no services/frontend changes, no infra/tunnel/ file content).
- Context-window hygiene policy is encoded in agent_plan §16: prefer a new Claude window after every two or three executed tasks and at every phase boundary.

## Validation Checks

| Check | Result |
|---|---|
| three plan files exist under docs/plans/b14_1/ | PASS |
| every plan file contains DRAFT_NOT_APPROVED_FOR_EXECUTION | PASS |
| no B14.1 implementation files created (no scripts/rp5/validate_b14_1_*.py, no services/, no libs/, no infra/) | PASS |
| no real RECRUITER_PASSWORD, ADMIN_STATS_PASSWORD, TAILSCALE_AUTHKEY, or Cloudflare token value committed | PASS (env-var-name references and placeholder policy only) |
| no literal non-loopback URL committed | PASS (grep for https?:// excluding 127.0.0.1, localhost, and protocol-only mention returned zero) |
| no literal stable hostname committed | PASS (no hostname literal appears in any committed file; the env-var name PUBLIC_DEMO_STABLE_HOSTNAME and a supplied-by-reference flag are the only references) |
| banned-phrase scan against B-route agent_plan §14 list (inherited) | PASS (zero rows after exclusions) |
| approval_packet wrapper and field set match the B14.0 schema (with scope `plan_authoring` and decision `REQUEST_PLAN_AUTHORING`/`APPROVE_FOR_EXECUTION` additions) | PASS |
| every marker in orchestrator_plan §6 has a recovery packet in agent_plan §11 | PASS |
| every B14.1 task next_state appears in the transition table | PASS |
| every HAR id appears both in agent_plan §15 and in agent_plan §11 recovery rows (via RP-HUMAN-ACTION-REQUIRED) | PASS |
| B14.0 boundary commits referenced in canonical files | PASS (phase approval 0bdaea89..., phase gate report 7e9ce1f7..., tracker closure 7730a4f5...) |
| no angle-bracket placeholders (single `<` or `>` literals other than in HTTPBasic Authorization-header technical phrasing) in canonical plan files | PASS (grep -n '<[a-zA-Z_]\+>' returned zero rows in orchestrator_plan.md, agent_plan.md, state_packet_schemas.yaml) |
| state_packet_schemas.yaml parses as YAML | PASS (python yaml.safe_load) |
| canonical files contain no Tailscale auth-key, Cloudflare token, or hostname literal substring patterns | PASS |

## Gate Before Implementation

No B14.1 implementation task may execute until:

1. This draft passes the same Dual-Agent Adversarial Plan Convergence Protocol used for B-route and B14.0 (or an orchestrator-named equivalent).
2. The orchestrator records ORCHESTRATOR_DECISION(scope=plan_authoring, phase=B14.1, decision=APPROVE_FOR_EXECUTION, accepted_report_commit=this-commit-or-its-convergent-successor).
3. The orchestrator advances the tracker by appending tracker.plan_authoring_approvals.B14.1 with status=APPROVED_FOR_EXECUTION, accepted_plan_revision_commit set, and approval_packet_path set, and by advancing tracker.current_task and tracker.state_transport.expected_next_task to B14_1-00.
4. An APPROVE_PLAN decision is recorded for the first B14.1 task (B14_1-00).
5. HAR-B14_1-FUNNEL-CAPABILITY-001 is resolved before B14_1-04 closure; HAR-B14_1-STABLE-HOSTNAME-001 is resolved before B14_1-08 success-claim or is recorded as the explicit blocker at B14_1-08.

## Result

OK_B14_1_PLAN_AUTHORING_DRAFT_COMPLETE
