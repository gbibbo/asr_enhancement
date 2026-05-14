# B14.1 Exposure State Record

Produced by: B14_1-01 (exposure-state plumbing).
Schemas: docs/plans/b14_1/state_packet_schemas.yaml — exposure_state_record and public_exposure_claim_record.
No literal public URL, stable hostname, Tailscale auth-key, Cloudflare token, recruiter password, or admin password appears in this file. Hostname material is referenced only by env-var name.

## STATE SNAPSHOT

```yaml
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
current_phase: B14.1
current_task: B14_1-01
last_completed_phase: B14.0
last_completed_task: B14_1-00
active_markers: []
expected_next_task: B14_1-01
requested_task_matches_tracker: true
```

## exposure_state_record

```yaml
exposure_state_id: ESR-B14_1-01
exposure_mode: loopback_only
public_exposure_flag: PUBLIC_DEMO_EXPOSURE_false
stable_hostname_source_reference: env_var_name_PUBLIC_DEMO_STABLE_HOSTNAME
stable_hostname_supplied_by_reference: false
blocker_if_unsupplied: HAR-B14_1-STABLE-HOSTNAME-001
validator: validate_b14_1_exposure_state_record
marker: B14_1_EPHEMERAL_URL_SUCCESS_CLAIM
```

Notes:

- exposure_mode is loopback_only at B14_1-01; the forbidden value ephemeral_only is not used.
- public_exposure_flag default is false (PUBLIC_DEMO_EXPOSURE=false), wired application-side via services/api/app/public_exposure.py.
- The stable hostname is operator-owned and referenced only by env-var name (PUBLIC_DEMO_STABLE_HOSTNAME); no literal value is recorded.
- The application-layer recruiter HTTPBasic gate (B14.0) remains the sole authority for public /demo/* access at PUBLIC_DEMO_EXPOSURE=true; this record neither alters nor depends on network-trust.

## public_exposure_claim_record

```yaml
claim_id: PECR-B14_1-01
claim_status: BLOCKED_PENDING_HUMAN_ACTION
stable_named_exposure_supplied_by_reference: false
explicit_blocker_id: HAR-B14_1-STABLE-HOSTNAME-001
blocker_recovery_packet: RP-HUMAN-ACTION-REQUIRED
validator: validate_b14_1_exposure_state_record
marker: B14_1_EPHEMERAL_URL_SUCCESS_CLAIM
```

Rule check (state_packet_schemas.yaml public_exposure_claim_record.rules):

- claim_status starts with BLOCKED ⇒ explicit_blocker_id non-null AND blocker_recovery_packet exists.
  - explicit_blocker_id: HAR-B14_1-STABLE-HOSTNAME-001 (non-null) — PASS.
  - blocker_recovery_packet: RP-HUMAN-ACTION-REQUIRED (exists in agent_plan §11) — PASS.

## Non-blocking HAR references (id-only)

```yaml
HAR-B14_1-FUNNEL-CAPABILITY-001:
  status: pre_declared_unresolved
  blocks: B14_1-04 closure and B14_1-08 closure
  blocks_B14_1-01: false
  reference_kind: id_only_no_value_material
HAR-B14_1-STABLE-HOSTNAME-001:
  status: pre_declared_unresolved
  blocks: B14_1-08 success-claim
  blocks_B14_1-01: false
  reference_kind: id_only_no_value_material
  cited_as_explicit_blocker_in_this_record: true
```

## Future constraints preserved by B14_1-01

```yaml
FC-B14-0-GATE-PRESERVED: untouched (no auth-layer file edited; no /demo/health behavior changed)
FC-BROUTE-FROZEN: untouched (libs/asr/router_runtime.py and frontend RouterFields not edited)
FC-B14-1-FUNNEL: flag plumbed only; authority remains the recruiter gate
FC-B15-MULTI-NETWORK: out-of-scope; preserved by exclusion
FC-HANDOFF-DATAMOVE1: out-of-scope; preserved by exclusion
```

## Result

OK_B14_1_EXPOSURE_STATE_STABLE_OR_BLOCKED
