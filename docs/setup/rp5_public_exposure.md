# RP5 Public Exposure Runbook (B14.1 tunnel + B14_2-04 re-smoke)

Operator runbook for bringing the demo up behind the public tunnel and running
the four-vantage-point recruiter-gate re-smoke that closes the B14.2 repair.

No secret, public URL, stable hostname, auth-key, or IP literal belongs in this
file or in any committed file. Everything sensitive lives in the host `.env.demo`
and in host environment variables only.

## 0. What this fixes

The B15 public smoke found the recruiter HTTPBasic gate was bypassable on the
public `/demo/*` surface and that upload-with-manual-ground-truth failed on every
network. The gate was restored in code (B14_2-02: every `/demo/*` route now
depends on `recruiter_auth_dependency`) and verified on loopback (B14_2-03). This
runbook drives the live re-verification (B14_2-04) that only the operator can do.

## 1. Host prerequisites

On the RP5, in the host `.env.demo` (never committed), set at least:

```text
RECRUITER_USERNAME=<choose>
RECRUITER_PASSWORD=<choose a strong value>
ADMIN_STATS_PASSWORD=<choose a strong value>
PUBLIC_DEMO_EXPOSURE=true
```

As host environment variables for the tunnel (not in the repo):

```text
TAILSCALE_AUTHKEY=<from Tailscale admin>
PUBLIC_DEMO_STABLE_HOSTNAME=<your funnel hostname, if using a stable name>
```

With `RECRUITER_USERNAME` or `RECRUITER_PASSWORD` empty the gate is fail-closed:
every request gets `401`. That is safe but the demo is unusable until both are set.

## 2. Bring up the demo runtime

```bash
cd /home/$USER/code/asr_enhancement
git pull --ff-only origin feature/demo-runtime-rp5-v1
docker compose -f infra/compose/docker-compose.demo.yml --env-file .env.demo up -d --build
docker compose -f infra/compose/docker-compose.demo.yml ps   # demo-api must be healthy
```

The container healthcheck now authenticates with the recruiter credentials, so
`healthy` also confirms the credentials are wired correctly.

## 3. Loopback gate sanity check (before exposing)

```bash
# No credentials -> 401 with the recruiter realm
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8001/demo/health
# Expect: 401

curl -s -D - -o /dev/null http://localhost:8001/demo/health | grep -i www-authenticate
# Expect: WWW-Authenticate: Basic realm="asr-demo-recruiter"

# With credentials -> 200 {"status":"ok"}
curl -s -u "$RECRUITER_USERNAME:$RECRUITER_PASSWORD" http://localhost:8001/demo/health
# Expect: {"status":"ok"}

# OpenAPI / docs must be off
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8001/openapi.json   # expect 404
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8001/docs            # expect 404
```

If any of these deviate, stop and fix before exposing publicly.

## 4. Start the tunnel (Tailscale Funnel)

Funnel terminates TLS upstream and forwards to the loopback app on
`127.0.0.1:8001`; the app still enforces the recruiter gate end-to-end. Provision
`TAILSCALE_AUTHKEY` on the host first, then run Funnel against port `8001`.
Install the tunnel as a host service with `Restart=always` / `RestartSec=10`
(or the Tailscale service equivalent). The unit file is host-only; do not commit it.

Record the resulting HTTPS URL **out of band** (not in the repo).

## 5. B14_2-04 four-vantage-point re-smoke

Run the same checks from four independent network vantage points:

1. `windows_local`
2. `mobile_cellular`
3. `other_wifi`
4. `vpn_or_external_tester`

From each vantage point, against the public HTTPS URL, record:

| Check | Expected | Record as |
|---|---|---|
| `GET /demo/health` with no credentials | `401`, `WWW-Authenticate: Basic realm="asr-demo-recruiter"` | recruiter_gate_observed_status |
| `GET /demo/health` with recruiter credentials | `200 {"status":"ok"}` | recruiter_gate_observed_status = `authenticated_access_only` |
| `GET /openapi.json` and `/docs` | `404` | openapi_docs_off |
| Load the UI, run one cached example (Whisper) | transcript renders | coverage_item_outcomes.cached_example |
| Upload a short clip WITHOUT ground truth | job completes, transcript renders | coverage_item_outcomes.upload_without_gt |
| Upload a short clip WITH manual ground truth | job completes, Word Accuracy shown | coverage_item_outcomes.upload_with_manual_ground_truth |
| Upload over 30 s / over 5 MB | rejected with the limit message | coverage_item_outcomes.upload_limit |
| Mobile layout (on the phone) | no horizontal scroll, usable | coverage_item_outcomes.mobile_layout |

`recruiter_gate_observed_status` is `authenticated_access_only` only if the
unauthenticated request got `401` AND the authenticated request got in. If any
vantage point can reach a `/demo/*` route without credentials, that is
`unauthenticated_access_observed` and the gate is still broken.

## 6. What to send back

For each of the four vantage points, send me:

- `recruiter_gate_observed_status`: `authenticated_access_only` or `unauthenticated_access_observed`
- `upload_with_manual_ground_truth`: `PASS` or `FAIL`
- the other coverage outcomes (PASS/FAIL)
- a non-secret evidence reference (e.g. "curl transcript saved locally", a screenshot filename) — do NOT paste the public URL, hostname, or credentials

I transcribe those verbatim into `reports/rp5/b14_2_public_surface_recruiter_gate_resmoke.md`
and derive the classification:

- all four `authenticated_access_only` + upload-with-GT PASS -> gate restored, upload issue was `linked_to_gate`
- all four `authenticated_access_only` + any upload-with-GT FAIL -> gate restored, upload issue is `independent_defer` (a real UI bug to fix separately)
- any `unauthenticated_access_observed` -> gate still broken, back to B14.2 repair

## 7. Rollback

To take the demo offline immediately: stop the tunnel service, then

```bash
docker compose -f infra/compose/docker-compose.demo.yml down
```

Setting `PUBLIC_DEMO_EXPOSURE=false` and restarting does not open the gate (the
gate is independent of the flag); stopping the tunnel is what removes public reach.
