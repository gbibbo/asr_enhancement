# B15 Smoke Adjudication

Task: B15-06
Phase: B15
Branch: feature/demo-runtime-rp5-v1
Record types: public_exposure_smoke_claim_record, b15_decision_rule_routing_record
(schema: docs/plans/b15/state_packet_schemas.yaml)

## Purpose

This is the declarative B15-06 deliverable. It carries exactly one
`public_exposure_smoke_claim_record` and exactly one
`b15_decision_rule_routing_record`, each shape-conformant to the active
B15 schema. The adjudication consumes the B15-04 and B15-05 deliverables
as declarative inputs only and computes the legacy demo_platform_plan
section 37 Task B15.1 decision rule (encoded by agent_plan.md section
10.1) against the regression marker carried forward from B15-05 closure
(`CLOSE_TASK_WITH_OBSERVED_REGRESSIONS`, observed_regression_markers
includes `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`).

The adjudication preserves every observed outcome verbatim. No `FAIL` is
softened, no `unauthenticated_access_observed` is converted to
`authenticated_access_only`, no `upload_with_manual_ground_truth=FAIL`
is converted to `PASS`, and no `SUCCESS_WITH_STABLE_NAMED_EXPOSURE` is
asserted. No literal public URL, public hostname, Tailscale auth-key,
Cloudflare token, recruiter password, admin password, or IP address is
recorded.

## Declarative inputs (consumed read-only)

- `reports/rp5/b15_public_exposure_bringup.md` (B15-04 deliverable,
  commit `e1a444d`): `public_exposure_bringup_record` `B15-BRINGUP-001`
  with `stable_hostname_supplied_by_reference: true` and
  `tailscale_authkey_supplied_by_reference: true`, both supplied by
  reference via resolved `HAR-B14_1-STABLE-HOSTNAME-001` and
  `HAR-B14_1-FUNNEL-CAPABILITY-001`. The bring-up record is explicitly
  not a public-exposure success claim.
- `reports/rp5/b15_multi_network_smoke_results.md` (B15-05 deliverable,
  commit `58a7cb2`): four `multi_network_smoke_result_record` entries,
  one per vantage point (`windows_local`, `mobile_cellular`,
  `other_wifi`, `vpn_or_external_tester`). Across all four records:
  `recruiter_gate_observed_status: unauthenticated_access_observed` and
  `coverage_item_outcomes.upload_with_manual_ground_truth: FAIL`. These
  observations are preserved verbatim and propagate into this
  adjudication.
- Carried marker (preserved, not cleared by B15-06):
  `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`. Per
  `orchestrator_plan.md` section 6 marker registry, this regression-class
  marker is carried forward to B15-06 adjudication with routing
  `RETURN_TO_B14`.

## public_exposure_smoke_claim_record

```yaml
public_exposure_smoke_claim_record:
  claim_id: B15-CLAIM-001
  claim_status: FAILED_PENDING_PHASE_RETURN
  stable_named_exposure_supplied_by_reference: true
  all_coverage_items_passed: false
  explicit_blocker_id: null
  blocker_recovery_packet: null
  validator: validate_b15_public_exposure_smoke_claim
  marker: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
```

Rationale (per schema rules in
`docs/plans/b15/state_packet_schemas.yaml` >
`public_exposure_smoke_claim_record`):

- `claim_status: FAILED_PENDING_PHASE_RETURN` is the deterministic value
  forced by the carried `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`
  marker per the state-transition map in `agent_plan.md` section 4
  ("PASS_WITH_OBSERVED_REGRESSION on B15-05 ... B15-06 must record
  claim_status FAILED_PENDING_PHASE_RETURN or BLOCKED_PENDING_HUMAN_ACTION
  with the corresponding decision-rule routing"). The schema permits a
  null `explicit_blocker_id` and a null `blocker_recovery_packet` when
  `claim_status` does not start with `BLOCKED`; the
  `FAILED_PENDING_PHASE_RETURN` branch requires only that a
  `b15_decision_rule_routing_record` whose routing is not
  `PROCEED_TO_B_HANDOFF` is recorded in the same file (satisfied below).
- `stable_named_exposure_supplied_by_reference: true` reflects the
  B15-04 `public_exposure_bringup_record` flags
  (`stable_hostname_supplied_by_reference: true`,
  `tailscale_authkey_supplied_by_reference: true`). The literal hostname
  is never recorded; it is referenced by env-var name only via the
  resolved B14.1 HARs.
- `all_coverage_items_passed: false` is set because the four B15-05
  multi-network smoke-result records preserve two coverage-relevant
  failures verbatim: (a) `recruiter_gate_observed_status:
  unauthenticated_access_observed` on all four vantage points, and (b)
  `coverage_item_outcomes.upload_with_manual_ground_truth: FAIL` on all
  four vantage points. Either observation alone foreclosed the
  `SUCCESS_WITH_STABLE_NAMED_EXPOSURE` branch; both observations
  together are propagated.
- `marker: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` cites the
  carried regression marker. The marker is preserved in
  `docs/progress/rp5_progress.yaml` > `markers` and is not cleared by
  this adjudication.

`SUCCESS_WITH_STABLE_NAMED_EXPOSURE` is foreclosed and is not asserted.

## b15_decision_rule_routing_record

```yaml
b15_decision_rule_routing_record:
  routing_id: B15-ROUTING-001
  routing: RETURN_TO_B14
  triggering_condition: >-
    Carried regression marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
    from B15-05 (CLOSE_TASK_WITH_OBSERVED_REGRESSIONS); the four B15-05
    multi_network_smoke_result_record entries (windows_local,
    mobile_cellular, other_wifi, vpn_or_external_tester) all observed
    recruiter_gate_observed_status=unauthenticated_access_observed,
    i.e. the recruiter HTTPBasic application-layer gate was bypassed
    under public smoke from every vantage point. The
    upload_with_manual_ground_truth=FAIL observation on all four vantage
    points is preserved as an additional contributor to the
    all_coverage_items_passed=false predicate that forecloses
    SUCCESS_WITH_STABLE_NAMED_EXPOSURE. Per the legacy
    demo_platform_plan section 37 Task B15.1 decision rules encoded in
    agent_plan.md section 10.1 and per orchestrator_plan.md section 6
    marker registry, this carried marker routes to RETURN_TO_B14.
  return_phase_if_any: B14
  validator: validate_b15_public_exposure_smoke_claim
  marker: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE
```

Rationale (per schema rules in
`docs/plans/b15/state_packet_schemas.yaml` >
`b15_decision_rule_routing_record`):

- `routing: RETURN_TO_B14` is the deterministic legacy decision-rule
  outcome for a recruiter-gate regression under public smoke. The
  orchestrator marker registry in `orchestrator_plan.md` section 6
  pins `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` to the
  `RETURN_TO_B14` carry-forward branch at B15-06 adjudication. The
  `agent_plan.md` section 18 adversarial stress-replay row for the
  "recruiter gate bypassed" scenario likewise maps to
  `routing RETURN_TO_B14`.
- `return_phase_if_any: B14` names the deterministic return phase.
- `marker: B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE` cites the
  carried regression marker. The marker is not cleared by this routing
  record.

`PROCEED_TO_B_HANDOFF` is foreclosed and is not recorded.

## Notes

- The carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`
  is preserved in `docs/progress/rp5_progress.yaml` > `markers` and is
  not cleared by B15-06. Per `orchestrator_plan.md` section 6 dual-effect
  policy, this marker remains active and is consumed by B15-07 phase-gate
  evaluation (full-success branch foreclosed; explicit-blocker branch
  admits the carried marker as an explicit blocker).
- The B15-05 observation
  `coverage_item_outcomes.upload_with_manual_ground_truth: FAIL` on all
  four vantage points is preserved verbatim and is propagated as a
  contributor to `all_coverage_items_passed: false`. It is not
  converted to `PASS` and it is not removed from the inputs.
- No B15-06 task action read, echoed, or recorded any literal public
  URL, public hostname, Tailscale auth-key, Cloudflare token, recruiter
  password, admin password, or IP address. The bring-up flags are
  consumed by reference only.
- No public-network command was run by B15-06 (no Tailscale, Funnel,
  Cloudflare, ngrok, systemd, Docker Compose, curl, browser, or public
  endpoint check). All validators are local and read declarative
  records.
- This deliverable does not author a `b15_closure_report` or a
  `b15_phase_gate_report`; B15-07 is not started.
- No `SUCCESS_WITH_STABLE_NAMED_EXPOSURE` claim is asserted.
- Tracker mutation for B15-06 closure is reserved for the orchestrator
  closure decision (`CLOSE_TASK`); this task does not write the tracker.
