# BR-08 Router Stub --base-url Compatibility Fix

marker: PLAN_CONFLICT
isolated_recovery_for: BR-08 phase-gate prerequisite (FV-ROUTER canonical command)
scope: isolated CLI compatibility fix to scripts/rp5/smoke_broute_router_stub.py only
not_in_scope:
  - BR-08 phase gate execution
  - tracker mutation
  - approval packet creation
  - any post-B-route work

## Issue

agent_plan.md §7 line 374 specifies the FV-ROUTER canonical command as:

    python scripts/rp5/smoke_broute_router_stub.py --base-url http://127.0.0.1:8001 --out reports/rp5/broute_router_stub_smoke.md

The BR-06 committed script (commit 1fd0e0d) defined argparse with only
`--app-module` and `--out`, so the canonical `--base-url` invocation was
rejected by argparse. agent_plan §9 line 402 for the same script omits
`--base-url`, creating an internal plan discrepancy that surfaced at BR-08
phase-gate planning.

## Stale Container Stopped

Port 127.0.0.1:8001 was occupied by a stale demo container returning a
pre-BR-02 health payload `{"status":"ok","mode":"demo","db_ok":true,"queue_depth":0}`.

    docker stop asr-demo-demo-api-1

After stop, ss -ltn confirmed port 8001 was free. No other containers were
modified, no docker rm, no compose down, no prune.

## Fix

scripts/rp5/smoke_broute_router_stub.py was extended to accept `--base-url`
alongside `--app-module`. The existing `--app-module` default and behaviour
were preserved. The HTTP-surface checks now route through a `_LiveClient`
(httpx) when `--base-url` is supplied or an `_InProcClient`
(fastapi.testclient.TestClient) when only `--app-module` is supplied, mirroring
the BR-05 manual-smoke transport split. The router-runtime in-process
assertions (stub constants, RouterDecision and AssembledResponse field sets,
build_cache_key router-field inclusion, two-call determinism,
routing_profile override) are unchanged and run identically in both modes.

When `--base-url` is supplied, the script does not touch DEMO_RUNTIME_ROOT,
ADMIN_STATS_USERNAME, ADMIN_STATS_PASSWORD, or DEMO_LOG_TO_FILE; the live
service owns runtime isolation. When only `--app-module` is supplied, the
script retains the BR-06 ephemeral DEMO_RUNTIME_ROOT and admin-env
isolation pattern.

## Validation Results

### --app-module mode (BR-06 backward compatibility)

    python3 scripts/rp5/smoke_broute_router_stub.py \
        --app-module services.api.app.demo_main:app \
        --out /tmp/br08_router_stub_appmodule_check.md

Result: OK_BROUTE_ROUTER_STUB_SMOKE — 18 checks, 0 failures.

### --base-url mode against live 127.0.0.1:8001

A temporary uvicorn was started on 127.0.0.1:8001 from the current repo head
with ephemeral runtime root and admin env vars under /tmp:

    DEMO_RUNTIME_ROOT=/tmp/br08_router_runtime_root
    ADMIN_STATS_USERNAME=admin
    ADMIN_STATS_PASSWORD=shh-smoke-only
    DEMO_LOG_TO_FILE=false
    python3 -m uvicorn services.api.app.demo_main:app --host 127.0.0.1 --port 8001

Readiness was confirmed when GET /demo/health returned exactly
`{"status":"ok"}` (BR-02 canonical payload).

    python3 scripts/rp5/smoke_broute_router_stub.py \
        --base-url http://127.0.0.1:8001 \
        --out /tmp/br08_router_stub_baseurl_check.md

Result: OK_BROUTE_ROUTER_STUB_SMOKE — 18 checks, 0 failures.

The temporary uvicorn process and its listening worker were terminated; ss -ltn
confirmed port 8001 was released afterward. The ephemeral DEMO_RUNTIME_ROOT
under /tmp was cleaned up alongside the other local-only evidence.

## Closure Constraints Respected

- no tracker mutation (docs/progress/rp5_progress.yaml untouched)
- no approval packet written
- no BR-08 phase gate invoked
- no scripts beyond scripts/rp5/smoke_broute_router_stub.py modified
- no compose, Dockerfile, config, dependency, lib, service, frontend, plan, or
  validator file modified
- no install or package mutation performed
- no port other than the canonical 127.0.0.1:8001 used
- only the named stale container (asr-demo-demo-api-1) was stopped

## Sentinels Observed

- OK_BROUTE_ROUTER_STUB_SMOKE (--app-module)
- OK_BROUTE_ROUTER_STUB_SMOKE (--base-url http://127.0.0.1:8001)
- OK_CHANGED_FILES_PATH_LOCKED (recorded after commit)
