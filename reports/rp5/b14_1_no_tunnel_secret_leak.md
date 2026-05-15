# B14.1 No Tunnel Secret Leak — Scan Report

generated_at_utc: 2026-05-15T00:41:09.544250
scope: template
root: /home/gbibbo/code/asr_enhancement
files_scanned: 357
files_skipped: 0
hits: 0

## Hits (redacted)

- none

## HAR Result (B14_1-04, HAR-B14_1-FUNNEL-CAPABILITY-001)

- tailscale_account_funnel_capability_enabled: true
- tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY: false
- cloudflare_tunnel_alternative_token_supplied_as_host_env: explicit_NA
- tunnel_run_as_service_restart_policy_string: on-failure
- restart_policy_classification: operator-supplied service policy (non-runtime documentation field)
- template_readiness_claim: NOT_READY_TO_RUN
- residual_blocker_for_B14_1-08: tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY=false

## HAR Result (B14_1-04, HAR-B14_1-STABLE-HOSTNAME-001)

- status: pre_declared_unresolved
- effect_on_B14_1-04: does_not_block
- effect_on_B14_1-08: blocks success-claim unless resolved or recorded as explicit blocker

## Result

No tunnel-secret literal was found in the requested scope.

OK_B14_1_NO_TUNNEL_SECRET_LEAK
