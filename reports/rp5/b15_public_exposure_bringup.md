# B15-04 Public Exposure Bring-up Record

Task: B15-04. Branch: feature/demo-runtime-rp5-v1.

This report is the B15-04 deliverable: a `public_exposure_bringup_record`
(schema `docs/plans/b15/state_packet_schemas.yaml > public_exposure_bringup_record`)
recording that the operator-side public-exposure bring-up evidence has been
supplied by reference. The agent records only references and boolean flags.

This is a bring-up evidence record, not a public-exposure success claim. It
does not assert `SUCCESS_WITH_STABLE_NAMED_EXPOSURE`, does not claim public
smoke success, and records no smoke result. The public-exposure success
claim is the separate `public_exposure_smoke_claim_record` at B15-06, which
depends on the B15-05 multi-network smoke results. The agent started,
modified, restarted, and verified no public-exposure mechanism, and ran no
network or runtime command.

```yaml
public_exposure_bringup_record:
  bringup_id: B15-BRINGUP-001
  public_exposure_flag: PUBLIC_DEMO_EXPOSURE_true
  stable_hostname_supplied_by_reference: true
  tailscale_authkey_supplied_by_reference: true
  tunnel_run_as_service_restart_policy_string: on-failure
  har_references:
    - HAR-B14_1-STABLE-HOSTNAME-001
    - HAR-B14_1-FUNNEL-CAPABILITY-001
  evidence_reference: operator_chat_confirmation_B15_04_carried_HARs_all_flags_true_no_literals_2026-05-15
  validator: validate_b15_no_public_url_or_hostname_literal
  marker: null
```

## Evidence basis

- `stable_hostname_supplied_by_reference: true` and
  `tailscale_authkey_supplied_by_reference: true` are taken from the
  operator-supplied `human_action_result` records accepted by the
  orchestrator (`ACCEPT_HUMAN_ACTION_RESULT`) for HAR-B14_1-STABLE-HOSTNAME-001
  and HAR-B14_1-FUNNEL-CAPABILITY-001. Both carried B14.1 HARs are recorded
  `resolved` in the tracker `human_action_requests` section.
- `public_exposure_flag: PUBLIC_DEMO_EXPOSURE_true` is recorded only as the
  operator-declared, by-reference exposure state derived from those resolved
  HARs. The agent toggles no exposure flag and performs no exposure action.
- `tunnel_run_as_service_restart_policy_string: on-failure` is the non-secret
  restart-policy string already recorded in the tracker for the
  HAR-B14_1-FUNNEL-CAPABILITY-001 lineage.
- `evidence_reference` is the non-secret operator confirmation reference. No
  literal public URL, hostname, Tailscale auth-key, Cloudflare token, tunnel
  secret, recruiter password, or admin password appears in this record.

## Scope boundary

- HAR-B15-MULTI-NETWORK-SMOKE-001 is not resolved by this record. It remains
  unresolved and gates B15-05 and the B15 phase-gate full-success branch.
- No public smoke result is recorded or implied here.
