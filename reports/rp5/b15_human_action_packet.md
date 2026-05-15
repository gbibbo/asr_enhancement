# B15-03 Human Action Packet

Task: B15-03. Branch: feature/demo-runtime-rp5-v1.

This report is the B15-03 deliverable: a `b15_human_action_packet` record
(schema `docs/plans/b15/state_packet_schemas.yaml > b15_human_action_packet`)
that declares the three unresolved human-action requests gating the B15
public smoke test. It declares the requests and their required human-evidence
shapes only. It resolves no human-action request, consumes no operator
evidence, and records no literal public URL, public hostname, Tailscale
auth-key, Cloudflare token, tunnel secret, recruiter password, admin
password, HAR evidence, smoke evidence, or provider evidence.

```yaml
b15_human_action_packet:
  packet_id: B15-HAP-001
  carried_from_b14_1:
    - HAR-B14_1-STABLE-HOSTNAME-001
    - HAR-B14_1-FUNNEL-CAPABILITY-001
  new_in_b15:
    - HAR-B15-MULTI-NETWORK-SMOKE-001
  validator:
    - validate_report_shape
    - validate_approval_packet
  marker: null
  human_action_requests:
    - request_id: HAR-B14_1-STABLE-HOSTNAME-001
      status: pre_declared_unresolved
      carried_from_phase: B14.1
      marker: HUMAN_ACTION_REQUIRED
      missing_inputs:
        - stable_hostname_supplied_as_host_env_PUBLIC_DEMO_STABLE_HOSTNAME
        - stable_hostname_owned_by_operator_account
        - dns_or_tailnet_funnel_record_active
      why_human_only: >-
        A stable public hostname is owned and provisioned through the
        operator's external account. The agent cannot create, own, or verify
        operator-account DNS or tailnet records, so the hostname can only be
        confirmed by the operator.
      allowed_values_or_schema: >-
        The operator supplies the hostname only by reference: the env-var name
        PUBLIC_DEMO_STABLE_HOSTNAME and a boolean "supplied: true". The literal
        hostname is never recorded in the tracker, approval packets, or any
        committed file.
      blocks: B15-04 closure and any B15 public-exposure success claim
      created_by_task: B15.1 plan authoring; re-declared by B15-03
      next_state_until_result: >-
        The agent waits at B15-04 with task status BLOCKED_BY_HUMAN_ACTION.
        The B15 phase gate may pass only through the explicit-blocker branch
        until the hostname is supplied by reference.
      forbidden_agent_action: >-
        Inventing or guessing a hostname; recording a literal hostname;
        claiming public-exposure success without the operator-supplied
        reference.
      result_expected_at: >-
        Before APPROVE_PLAN for B15-04, or recorded as an explicit blocker at
        B15-07.
    - request_id: HAR-B14_1-FUNNEL-CAPABILITY-001
      status: partially_resolved_at_B14_1-04_threshold
      carried_from_phase: B14.1
      marker: HUMAN_ACTION_REQUIRED
      missing_inputs:
        - tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY
      why_human_only: >-
        The Tailscale auth-key is an operator-account secret. The agent must
        never read, echo, or commit it, so only the operator can declare it
        supplied. The other Funnel-capability inputs were supplied at the
        B14_1-04 threshold; this is the residual auth-key blocker.
      allowed_values_or_schema: >-
        The operator declares the auth-key supplied as host env with a boolean
        "supplied: true". The auth-key value is never read, echoed, or
        committed.
      blocks: >-
        B15-04 closure; the tunnel must actually run for a multi-network
        smoke.
      created_by_task: B14.1 (carried); re-declared by B15-03
      next_state_until_result: >-
        The agent waits at B15-04 with task status BLOCKED_BY_HUMAN_ACTION
        until the residual auth-key is declared supplied.
      forbidden_agent_action: >-
        Reading, echoing, or committing the auth-key value; starting Tailscale
        or Funnel without the operator-supplied declaration.
      result_expected_at: >-
        Before APPROVE_PLAN for B15-04, or recorded as an explicit blocker at
        B15-07.
    - request_id: HAR-B15-MULTI-NETWORK-SMOKE-001
      status: pre_declared_unresolved
      carried_from_phase: B15
      marker: HUMAN_ACTION_REQUIRED
      missing_inputs:
        - smoke_result_windows_local
        - smoke_result_mobile_cellular
        - smoke_result_other_wifi
        - smoke_result_vpn_or_external_tester
      why_human_only: >-
        A multi-network public smoke requires the operator to reach the public
        surface from four distinct networks outside the agent's host and
        authority. The agent must not fabricate network results.
      allowed_values_or_schema: >-
        Each smoke result is a multi_network_smoke_result_record per
        state_packet_schemas.yaml, covering the nine coverage items, with an
        operator evidence_reference and no literal public URL, hostname, or
        secret.
      blocks: B15-05 closure and the B15 phase-gate full-success branch
      created_by_task: B15.1 plan authoring; re-declared by B15-03
      next_state_until_result: >-
        The agent waits at B15-05 with task status BLOCKED_BY_HUMAN_ACTION.
        The B15 phase gate may pass only through the explicit-blocker branch
        until results are supplied.
      forbidden_agent_action: >-
        Fabricating smoke results; inventing network vantage-point outcomes;
        recording literal public URLs, hostnames, or secrets.
      result_expected_at: >-
        Before APPROVE_PLAN for B15-05, or recorded as an explicit blocker at
        B15-07.
```

## Declaration scope

- No human-action request is resolved by this packet. Each entry remains
  unresolved: HAR-B14_1-STABLE-HOSTNAME-001 pre_declared_unresolved,
  HAR-B14_1-FUNNEL-CAPABILITY-001 with a residual auth-key blocker, and
  HAR-B15-MULTI-NETWORK-SMOKE-001 pre_declared_unresolved.
- No operator evidence is consumed or fabricated.
- No literal public URL, public hostname, Tailscale auth-key, Cloudflare
  token, tunnel secret, recruiter password, or admin password appears in this
  report. Env-var names (PUBLIC_DEMO_STABLE_HOSTNAME, TAILSCALE_AUTHKEY) are
  names only, not values.
