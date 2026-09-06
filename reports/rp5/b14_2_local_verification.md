# B14.2 Local Verification (Aggregate)

Task: B14_2-03
Phase: B14.2 (repair microphase)
Branch: feature/demo-runtime-rp5-v1
Record type: aggregate execution report (loopback-only verification)
Schema reference: docs/plans/b14_2/state_packet_schemas.yaml
Plan reference: docs/plans/b14_2/agent_plan.md section 10 row B14_2-03

## Purpose

Re-emit on loopback, under `PUBLIC_DEMO_EXPOSURE=true`, the six B14.2
invariant sentinels required by the agent_plan §10 B14_2-03 task
contract and §7 FV-* table. Verifies that the B14_2-02 application
repair (recruiter dependency on every committed `/demo/*` route) holds
under public-exposure mode at loopback, that the BR-02 health invariant
is preserved, that the OpenAPI/docs surfaces are unmounted, that no
public URL / tunnel-hostname literal or tunnel secret is committed, and
that the B-route freeze (router_runtime SHA-256 + types.ts RouterFields
canonical fingerprint) is unchanged.

## Non-claim clause (explicit)

- This report is a **loopback-only** verification. It does **not**
  assert that the Funnel-terminated public surface is fixed.
- The carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`
  remains active and is preserved by this task; clearance is reserved
  for the B14.2 PHASE_APPROVE recording on the gate-restored branch
  following the operator-supplied B14_2-04 re-smoke evidence per
  HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001.
- `HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001` remains
  `pre_declared_unresolved`. `HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001`
  remains `pre_declared_conditional`. B14_2-03 does **not** transition
  either HAR.
- No Zone-C hypothesis (header-strip / port-forward / route-mapping /
  interface-binding / flag-drift) is recorded as confirmed. Confirmation
  belongs to the B14_2-04 operator re-smoke.

## Loopback verification (port deviation accepted)

Pre-existing `asr-demo-demo-api-1` Docker container occupies host port
`8001` (carrying the pre-fix code). Docker Compose mutation is
forbidden by the active B14.2 plan; loopback verification therefore
uses port `127.0.0.1:18001`, supplied as `--base-url` to each B14.2
wrapper. Still strictly loopback. Same port deviation accepted at
B14_2-02 (recorded in `tasks.B14_2-02.port_deviation_accepted`).

Uvicorn was started with:

```
PUBLIC_DEMO_EXPOSURE=true \
RECRUITER_USERNAME=<local-only ephemeral> \
RECRUITER_PASSWORD=<local-only ephemeral> \
DEMO_RUNTIME_ROOT=/tmp/b14_2_03_runtime \
python -m uvicorn services.api.app.demo_main:app --host 127.0.0.1 --port 18001
```

Credential values were supplied only in the validator subprocess env
and were never written to disk, the tracker, or any committed file.
After verification, the uvicorn process was stopped, the loopback port
was released, and `/tmp/b14_2_03_runtime/` plus `/tmp/b14_2_03_uvicorn*`
were removed.

## Aggregate sentinel inventory

| Validator | Sentinel observed | Report |
|---|---|---|
| `validate_b14_2_recruiter_gate_preserved_under_public_exposure` | `OK_B14_2_RECRUITER_GATE_PRESERVED` | [reports/rp5/b14_2_recruiter_gate_preserved_under_public_exposure.md](b14_2_recruiter_gate_preserved_under_public_exposure.md) |
| `validate_b14_2_health_payload_preserved_under_public_exposure` | `OK_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE` | [reports/rp5/b14_2_health_payload_preserved_under_public_exposure.md](b14_2_health_payload_preserved_under_public_exposure.md) |
| `validate_b14_2_openapi_docs_visibility` | `OK_B14_2_OPENAPI_DOCS_OFF` | [reports/rp5/b14_2_openapi_docs_visibility.md](b14_2_openapi_docs_visibility.md) |
| `validate_b14_2_no_public_url_or_hostname_literal` | `OK_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL` | [reports/rp5/b14_2_no_public_url_or_hostname_literal.md](b14_2_no_public_url_or_hostname_literal.md) |
| `validate_b14_2_no_tunnel_secret_leak` | `OK_B14_2_NO_TUNNEL_SECRET_LEAK` | [reports/rp5/b14_2_no_tunnel_secret_leak.md](b14_2_no_tunnel_secret_leak.md) |
| `validate_b14_2_broute_compatibility_under_public_exposure` | `OK_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE` | [reports/rp5/b14_2_broute_compatibility_under_public_exposure.md](b14_2_broute_compatibility_under_public_exposure.md) |

Six PASS sentinels observed. All six were emitted in live HTTP mode
against `http://127.0.0.1:18001` under `PUBLIC_DEMO_EXPOSURE=true`.

## Fixture-generator inventory

Each B14_2-03 validator has a paired fixture generator under
`scripts/rp5/fixtures/generate_fixture_validate_b14_2_*.py`. Each
generator was re-run twice with byte-identical manifest sha256
output (determinism confirmed).

| Generator | Manifest sha256 | Sentinel |
|---|---|---|
| `generate_fixture_validate_b14_2_recruiter_gate_preserved_under_public_exposure` | `0eeae9495b993624cde31eebb3187050ed7288ceca8263dc36f7c30767e6685d` | `OK_FIXTURE_VALIDATE_B14_2_RECRUITER_GATE_PRESERVED` |
| `generate_fixture_validate_b14_2_health_payload_preserved_under_public_exposure` | `d3f3908184e399b8a9c1389626eda890debc05424457fe957c485c13e91c920c` | `OK_FIXTURE_VALIDATE_B14_2_HEALTH_UNDER_PUBLIC_EXPOSURE` |
| `generate_fixture_validate_b14_2_openapi_docs_visibility` | `f73ca5827b269514c35b2e72283efdfbda40a93c16a5daabbe36e12f79518402` | `OK_FIXTURE_VALIDATE_B14_2_OPENAPI_DOCS` |
| `generate_fixture_validate_b14_2_no_public_url_or_hostname_literal` | `5f8a6b58e06db077be6c8e7c490a8d352a7a1f5ec2c9ee976925d9a179810655` | `OK_FIXTURE_VALIDATE_B14_2_NO_PUBLIC_URL_OR_HOSTNAME_LITERAL` |
| `generate_fixture_validate_b14_2_no_tunnel_secret_leak` | `3230ecf3a043c44b3db9a045393b8415b80bc31b94af39293c4a2d76ec3c8220` | `OK_FIXTURE_VALIDATE_B14_2_NO_TUNNEL_SECRET_LEAK` |
| `generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure` | `d58e2358e415f53d3e497c535ae574b71d66c7ac4a508413680a76cca4b27cd0` | `OK_FIXTURE_VALIDATE_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE` |

## Carried marker, HAR, and predecessor freeze

- Carried marker `B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE`:
  **preserved active**. No B14_2-03 file clears it; the only writer
  authorised to clear it is the orchestrator PHASE_APPROVE recording on
  the gate-restored branch per
  `docs/plans/b14_2/agent_plan.md` section 2 carried_marker_clearance_policy.
- `HAR-B14_2-PUBLIC-SURFACE-RECRUITER-GATE-RESMOKE-001`:
  `pre_declared_unresolved` (unchanged; consumed at B14_2-04).
- `HAR-B14_2-UPLOAD-WITH-GT-DIAGNOSTIC-001`:
  `pre_declared_conditional` (unchanged; conditional fire at B14_2-05).
- Carried predecessor HARs (`HAR-B14_1-STABLE-HOSTNAME-001`,
  `HAR-B14_1-FUNNEL-CAPABILITY-001`, `HAR-B15-MULTI-NETWORK-SMOKE-001`,
  `HAR-BR-THRESHOLDS-001`): referenced read-only; not modified.
- Predecessor freeze: no edit to `docs/plans/{broute,b14_0,b14_1,b15,b14_2}/`,
  `reports/rp5/{broute,b14_0,b14_1,b15}_*.md`,
  `libs/asr/router_runtime.py`,
  `services/frontend/app/demo/types.ts`, or any compose file.
- No services / libs / infra runtime change in B14_2-03 (the B14_2-02
  surface is frozen for this verification task).

## Local-only evidence removed

- Loopback uvicorn process: stopped (PID released).
- `/tmp/b14_2_03_uvicorn.log`: removed.
- `/tmp/b14_2_03_uvicorn.pid`: removed.
- `/tmp/b14_2_03_runtime/`: removed.
- No ephemeral URL, no recruiter credential, and no operator-owned
  literal recorded in any committed file.

## Result

`B14_2_LOCAL_VERIFICATION_PASS` (aggregate of the six PASS sentinels above).
This report does not claim public-surface success. The B14_2-04
HAR-gated operator re-smoke is still required before the carried marker
becomes eligible for clearance.
