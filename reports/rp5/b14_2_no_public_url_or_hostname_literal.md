# B14.2 No Public URL or Hostname Literal

generated_at_utc: 2026-05-24T00:56:57.381414+00:00
root: /home/gbibbo/code/asr_enhancement
component: all
files_scanned: 442
url_hits: 0
host_hits: 0
scope_note: only tunnel-hostname-pattern hosts (*.ts.net, *.trycloudflare.com, *.cfargotunnel.com) are flagged; the scope mirrors the B15 precedent validator.

## Invariant Results

- [PASS] no_tunnel_hostname_pattern_in_url_literal_committed: no tunnel-hostname-pattern URL literal observed
- [PASS] no_tunnel_hostname_pattern_committed: no tunnel-hostname-pattern bare-hostname literal observed

## Sentinel

OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL
