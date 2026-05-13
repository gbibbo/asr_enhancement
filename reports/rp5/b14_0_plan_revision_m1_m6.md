# B14.0 Plan Revision Report — M1..M6

authoring_status: DRAFT_NOT_APPROVED_FOR_EXECUTION
preceded_by: B14.0 plan authoring commit 1d09855e627ca0ed3729d8774c0b349bab6a5251
audit_accepted: APPROVE_FOR_EXTERNAL_REVIEW (from compact draft-plan audit)
revision_decision: APPROVE_TARGETED_REVISION (scope=plan_authoring_revision)

## Revisions Applied

| Issue | Section touched | Change summary |
|---|---|---|
| M1 | agent_plan §0 validators | Added `validate_public_security_invariants` to the validators list with an "inherited from B-route; reused by RP-PUBLIC-SECURITY-REGRESSION diagnosis command in §11" comment so the reference in §11 resolves against the §0 manifest |
| M2 | agent_plan §9.1 (new sub-section) | Added a fixture-generator contract table with one row per new B14.0 validator (7 rows): generator id, script path, exact command, output manifest path, OK sentinel format, owned marker. The narrative paragraph at the top of §9 still declares the convention; §9.1 enumerates each generator explicitly |
| M3 | agent_plan §1 PL-B14_0-CONFIG row | Rewrote the allowed_symbols_or_components clause to explicitly forbid compose files (docker-compose*.yml, docker-compose.demo.yml) inside B14.0 and to require that any future compose change be authorized by a CHANGE_SCOPE decision that updates the lock row and the relevant §10 task contract together in one patch |
| M4 | agent_plan §2.1 (new sub-section) | Added a threshold-audit table with seven rows (recruiter_credential_rotation_interval_numeric → HUMAN_ACTION_REQUIRED, recruiter_initial_credential_values → HUMAN_ACTION_REQUIRED, plus five not_applicable_current_scope rows). Summary block at the end: 0 numeric thresholds introduced, 2 HUMAN_ACTION_REQUIRED entries (both routed through HAR-B14_0-RECRUITER-CREDS-001), 5 not_applicable_current_scope entries |
| M5 | agent_plan §17 (new section) | Added an adversarial stress-replay table with 8 scenarios: shared-credential conflation, 401 leaks router field, password logged, admin-realm collision, Funnel string introduced, public URL literal, router-runtime edit, frontend types router-field shape edit. Each row identifies expected_marker, expected_next_state, report_shape, plan sections used, and PASS-evidence reference |
| M6 | agent_plan §15 | Replaced the "no HAR pre-declared" sentence with a pre-declared HAR table row for HAR-B14_0-RECRUITER-CREDS-001 plus a YAML block enumerating missing_inputs (recruiter_initial_username, recruiter_initial_password, recruiter_credential_rotation_cadence), allowed_values_or_schema (length, ASCII, entropy ≥ 96 bits, must differ from admin creds), blocks=B14_0-02 closure, result_recording_policy that records only field-supplied flags and the rotation policy string (never values) in tracker or approval packets |

Files actually modified by this revision:
- docs/plans/b14_0/agent_plan.md (M1, M2, M3, M4, M5, M6 — all six revisions land here)

Files intentionally untouched:
- docs/plans/b14_0/orchestrator_plan.md (no orchestrator-level change required by M1..M6)
- docs/plans/b14_0/state_packet_schemas.yaml (no schema-shape change required by M1..M6)

## Files Changed

| Path | Action | Notes |
|---|---|---|
| docs/plans/b14_0/agent_plan.md | modified | M1..M6 |
| reports/rp5/b14_0_plan_revision_m1_m6.md | created | this report |

## Validation Checks

| Check | Result |
|---|---|
| DRAFT_NOT_APPROVED_FOR_EXECUTION still present in all three plan files | PASS (orchestrator_plan: 2 hits, agent_plan: 2 hits, state_packet_schemas: 1 hit) |
| No tracker mutation (docs/progress/rp5_progress.yaml unchanged) | PASS (git diff --stat returns empty) |
| No B14.0 implementation file created | PASS |
| No real secrets committed | PASS (HAR result recording policy explicitly forbids credential values in tracker, approval packets, or committed files) |
| No literal non-loopback URL committed | PASS (grep https?:// excluding 127.0.0.1 and localhost returns zero) |
| docs/plans/broute/ unchanged | PASS (git diff --stat returns empty) |
| Marker count agent_plan §0 == orchestrator_plan §6 | PASS (21 markers each) |
| Recovery-packet count agent_plan §11 == orchestrator_plan §6 references | PASS (21 each) |
| Every new B14.0 validator from §0 has a fixture-generator row in §9.1 | PASS (7 new B14.0 validators → 7 generator rows) |
| Every generator row maps to an existing marker in §3 | PASS |
| HAR-B14_0-RECRUITER-CREDS-001 marker (HUMAN_ACTION_REQUIRED) is in the marker registry | PASS (HUMAN_ACTION_REQUIRED present in §0 and orchestrator §6) |
| HAR result-recording policy declares value-free recording | PASS (only field-supplied flags and policy string are recorded; never credential values) |
| Threshold-audit subsection lists 0 numeric thresholds introduced | PASS |
| Adversarial stress-replay table maps every scenario to existing marker and recovery packet | PASS (8/8 scenarios → markers and packets that exist in §3 and §11) |
| Banned-phrase scan on agent_plan §14 list against the three plan files | PASS (zero rows after section_14/banned_phrases/forbidden_orchestrator_outputs exclusions) |
| PL-B14_0-CONFIG now forbids compose files in B14.0 absent a CHANGE_SCOPE that updates lock and task contract together | PASS |
| RP-PUBLIC-SECURITY-REGRESSION diagnosis command resolves against §0 manifest | PASS (validate_public_security_invariants now in §0 with inherited annotation) |
| Working tree contains only the two allowed files in this commit (agent_plan.md and this report) | PASS |

## Gate Reminder

No B14.0 implementation task may execute until:

1. This revised draft passes the same Dual-Agent Adversarial Plan Convergence Protocol used for B-route (or an orchestrator-named equivalent)
2. ORCHESTRATOR_DECISION(scope=plan_authoring_approval, decision=APPROVE_FOR_EXECUTION, accepted_report_commit=<commit of this revision or its convergent successor>) is recorded
3. A separate ORCHESTRATOR_DECISION advances the tracker from B14.0_PENDING_ORCHESTRATOR_INSTRUCTION to a B14.0-active state
4. APPROVE_PLAN is recorded for the first B14.0 task (B14_0-00)
5. HAR-B14_0-RECRUITER-CREDS-001 is resolved (operator-supplied recruiter credentials and rotation policy recorded by reference) before B14_0-02 closure

## Result

OK_B14_0_PLAN_REVISION_M1_M6_COMPLETE
