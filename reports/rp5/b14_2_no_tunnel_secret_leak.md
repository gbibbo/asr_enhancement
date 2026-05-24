# B14.2 No Tunnel Secret Leak

generated_at_utc: 2026-05-24T00:50:42.919250+00:00
root: /home/gbibbo/code/asr_enhancement
base_url: http://127.0.0.1:18001
files_scanned: 588
tailscale_authkey_hits: 0
cloudflare_token_hits: 0
checks: 4
failures: 0

## Invariant Results

- [PASS] no_tailscale_authkey_prefix_committed: no tskey- prefix observed
- [PASS] no_cloudflare_tunnel_token_shape_committed: no cloudflare tunnel token shape observed
- [PASS] loopback_response_does_not_echo_credentialed_request_headers: no credentialed request-header name echoed in the response
- [PASS] no_tunnel_secret_shape_in_response_headers: no tunnel-secret-shaped value in any response header

## Sentinel

OK_B14_2_NO_TUNNEL_SECRET_LEAK
