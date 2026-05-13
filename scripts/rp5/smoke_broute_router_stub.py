#!/usr/bin/env python3
"""
B-route router-stub end-to-end smoke.

Exercises the router-ready seam in libs/asr/router_runtime.py with the
deterministic stub values declared in docs/plans/broute/agent_plan.md
section 2 (router_decision_fields, assembled_response_fields, router_stub).

Also confirms in-process that the BR-02 public health contract and the
BR-05 manual_mode_no_router_fields invariant still hold on HTTP surfaces
served by services.api.app.demo_main.

Emits OK_BROUTE_ROUTER_STUB_SMOKE on success or B_ROUTE_ROUTER_SMOKE_FAILED
on failure.
"""
import argparse
import dataclasses
import datetime
import importlib
import os
import pathlib
import sys
import tempfile


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


ROUTER_DECISION_FIELDS = [
    "selected_backend",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "third_party_provider",
    "cost_policy",
    "estimated_cost_usd",
    "predicted_confidence",
    "predicted_ask_repeat",
    "routing_explanation",
    "router_latency_ms",
]

ASSEMBLED_RESPONSE_FIELDS = [
    "transcript_text",
    "selected_backend",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "third_party_provider",
    "estimated_cost_usd",
    "cost_usd",
    "backend_confidence",
    "ask_repeat",
    "routing_explanation",
]

LATENCY_MS_SUBFIELDS = ["backend", "server", "end_to_end"]

ROUTER_HTTP_LEAK_FIELDS = [
    "router_kind",
    "router_version",
    "routing_profile",
    "selected_backend",
    "allow_third_party",
]

ALLOWED_ASSEMBLYAI_STATES = {
    "available",
    "daily_quota_reached",
    "quota_exhausted",
    "disabled",
}

EXPECTED_STUB_ROUTER_KIND = "deterministic_selector"
EXPECTED_STUB_ROUTER_VERSION = "stub-v0"
EXPECTED_STUB_SELECTED_BACKEND = "whisper_base_ct2_int8"
EXPECTED_STUB_ROUTING_EXPLANATION = "stub: awaiting datamove1 handoff"
DEFAULT_ROUTING_PROFILE = "balanced"


def _check(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


def _import_app(spec):
    module_name, _, attr = spec.partition(":")
    if not attr:
        raise ValueError(f"Invalid --app-module spec: {spec!r}")
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


def _json_or_empty(resp):
    ctype = (resp.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        try:
            return resp.json()
        except Exception:
            return None
    return None


def run_checks(app_module_spec):
    results = []

    # Router-runtime in-process checks ---------------------------------------
    try:
        from libs.asr.router_runtime import (
            AssembledResponse,
            LatencyMs,
            RouterDecision,
            RouterRuntime,
            STUB_ROUTER_KIND,
            STUB_ROUTER_VERSION,
            STUB_SELECTED_BACKEND,
            build_cache_key,
        )
    except Exception as exc:
        results.append(_check(
            "import_router_runtime",
            False,
            f"{type(exc).__name__}: {exc}",
        ))
        return results

    results.append(_check(
        "stub_router_kind_constant",
        STUB_ROUTER_KIND == EXPECTED_STUB_ROUTER_KIND,
        f"STUB_ROUTER_KIND={STUB_ROUTER_KIND!r} expected={EXPECTED_STUB_ROUTER_KIND!r}",
    ))
    results.append(_check(
        "stub_router_version_constant",
        STUB_ROUTER_VERSION == EXPECTED_STUB_ROUTER_VERSION,
        f"STUB_ROUTER_VERSION={STUB_ROUTER_VERSION!r} expected={EXPECTED_STUB_ROUTER_VERSION!r}",
    ))
    results.append(_check(
        "stub_selected_backend_constant",
        STUB_SELECTED_BACKEND == EXPECTED_STUB_SELECTED_BACKEND,
        f"STUB_SELECTED_BACKEND={STUB_SELECTED_BACKEND!r} expected={EXPECTED_STUB_SELECTED_BACKEND!r}",
    ))

    try:
        decision_default = RouterRuntime().route()
    except Exception as exc:
        results.append(_check(
            "router_runtime_route_call",
            False,
            f"{type(exc).__name__}: {exc}",
        ))
        return results

    decision_fields_actual = sorted(f.name for f in dataclasses.fields(RouterDecision))
    decision_fields_expected = sorted(ROUTER_DECISION_FIELDS)
    results.append(_check(
        "router_decision_field_set",
        decision_fields_actual == decision_fields_expected,
        f"actual={decision_fields_actual} expected={decision_fields_expected}",
    ))

    results.append(_check(
        "router_decision_selected_backend",
        decision_default.selected_backend == EXPECTED_STUB_SELECTED_BACKEND,
        f"selected_backend={decision_default.selected_backend!r}",
    ))
    results.append(_check(
        "router_decision_router_kind",
        decision_default.router_kind == EXPECTED_STUB_ROUTER_KIND,
        f"router_kind={decision_default.router_kind!r}",
    ))
    results.append(_check(
        "router_decision_router_version",
        decision_default.router_version == EXPECTED_STUB_ROUTER_VERSION,
        f"router_version={decision_default.router_version!r}",
    ))
    results.append(_check(
        "router_decision_default_routing_profile",
        decision_default.routing_profile == DEFAULT_ROUTING_PROFILE,
        f"routing_profile={decision_default.routing_profile!r}",
    ))
    results.append(_check(
        "router_decision_routing_explanation",
        decision_default.routing_explanation == EXPECTED_STUB_ROUTING_EXPLANATION,
        f"routing_explanation={decision_default.routing_explanation!r}",
    ))

    # Two-call determinism
    try:
        decision_second = RouterRuntime().route()
        deterministic = dataclasses.asdict(decision_default) == dataclasses.asdict(decision_second)
    except Exception as exc:
        deterministic = False
        decision_second = None
        det_detail = f"{type(exc).__name__}: {exc}"
    else:
        det_detail = "identical RouterDecision across two route() calls"
    results.append(_check(
        "router_decision_deterministic_two_calls",
        deterministic,
        det_detail,
    ))

    # routing_profile override preserves stub identifiers
    try:
        decision_override = RouterRuntime().route(routing_profile="latency")
        override_ok = (
            decision_override.routing_profile == "latency"
            and decision_override.router_kind == EXPECTED_STUB_ROUTER_KIND
            and decision_override.router_version == EXPECTED_STUB_ROUTER_VERSION
            and decision_override.selected_backend == EXPECTED_STUB_SELECTED_BACKEND
        )
        override_detail = (
            f"routing_profile={decision_override.routing_profile!r} "
            f"router_kind={decision_override.router_kind!r} "
            f"router_version={decision_override.router_version!r} "
            f"selected_backend={decision_override.selected_backend!r}"
        )
    except Exception as exc:
        override_ok = False
        override_detail = f"{type(exc).__name__}: {exc}"
    results.append(_check(
        "router_decision_routing_profile_override_preserves_stub",
        override_ok,
        override_detail,
    ))

    # AssembledResponse field set
    assembled_fields_actual = sorted(f.name for f in dataclasses.fields(AssembledResponse))
    expected_assembled = sorted(ASSEMBLED_RESPONSE_FIELDS + ["latency_ms"])
    results.append(_check(
        "assembled_response_field_set",
        assembled_fields_actual == expected_assembled,
        f"actual={assembled_fields_actual} expected={expected_assembled}",
    ))

    latency_fields_actual = sorted(f.name for f in dataclasses.fields(LatencyMs))
    latency_fields_expected = sorted(LATENCY_MS_SUBFIELDS)
    results.append(_check(
        "assembled_response_latency_ms_subfields",
        latency_fields_actual == latency_fields_expected,
        f"actual={latency_fields_actual} expected={latency_fields_expected}",
    ))

    try:
        assembled = AssembledResponse(
            transcript_text="",
            selected_backend=decision_default.selected_backend,
            router_kind=decision_default.router_kind,
            router_version=decision_default.router_version,
            routing_profile=decision_default.routing_profile,
            allow_third_party=decision_default.allow_third_party,
            third_party_provider=decision_default.third_party_provider,
            estimated_cost_usd=decision_default.estimated_cost_usd,
            cost_usd=0.0,
            backend_confidence=0.0,
            ask_repeat=0.0,
            latency_ms=LatencyMs(backend=0.0, server=0.0, end_to_end=0.0),
            routing_explanation=decision_default.routing_explanation,
        )
        assembled_ok = (
            assembled.router_kind == EXPECTED_STUB_ROUTER_KIND
            and assembled.router_version == EXPECTED_STUB_ROUTER_VERSION
            and assembled.selected_backend == EXPECTED_STUB_SELECTED_BACKEND
            and assembled.latency_ms.backend == 0.0
            and assembled.latency_ms.server == 0.0
            and assembled.latency_ms.end_to_end == 0.0
        )
        assembled_detail = (
            f"router_kind={assembled.router_kind!r} "
            f"router_version={assembled.router_version!r} "
            f"selected_backend={assembled.selected_backend!r}"
        )
    except Exception as exc:
        assembled_ok = False
        assembled_detail = f"{type(exc).__name__}: {exc}"
    results.append(_check(
        "assembled_response_composition_from_stub_decision",
        assembled_ok,
        assembled_detail,
    ))

    # build_cache_key router-field inclusion
    try:
        key = build_cache_key(
            audio_hash="stub-audio-hash",
            selected_backend=decision_default.selected_backend,
            asr_model_and_version="whisper_base_ct2_int8@v1",
            router_kind=decision_default.router_kind,
            router_version=decision_default.router_version,
            routing_profile=decision_default.routing_profile,
            allow_third_party=decision_default.allow_third_party,
            degradation_version="dv-stub",
            metrics_or_features_version="mv-stub",
        )
        required_segments = [
            "stub-audio-hash",
            EXPECTED_STUB_SELECTED_BACKEND,
            "whisper_base_ct2_int8@v1",
            EXPECTED_STUB_ROUTER_KIND,
            EXPECTED_STUB_ROUTER_VERSION,
            DEFAULT_ROUTING_PROFILE,
            "dv-stub",
            "mv-stub",
        ]
        missing = [seg for seg in required_segments if seg not in key]
        # allow_third_party=False must be encoded somewhere in the key
        allow_third_party_encoded = ("0" in key) or ("False" in key) or ("false" in key)
        cache_key_ok = isinstance(key, str) and len(missing) == 0 and allow_third_party_encoded
        cache_key_detail = (
            f"key_len={len(key) if isinstance(key, str) else None} "
            f"missing={missing} allow_third_party_encoded={allow_third_party_encoded}"
        )
    except Exception as exc:
        cache_key_ok = False
        cache_key_detail = f"{type(exc).__name__}: {exc}"
    results.append(_check(
        "build_cache_key_router_fields_present",
        cache_key_ok,
        cache_key_detail,
    ))

    # HTTP surface checks via in-process TestClient ---------------------------
    try:
        from fastapi.testclient import TestClient
        app = _import_app(app_module_spec)
        cm = TestClient(app)
    except Exception as exc:
        results.append(_check(
            "open_in_process_client",
            False,
            f"{type(exc).__name__}: {exc}",
        ))
        return results

    try:
        with cm as c:
            r = c.get("/demo/health")
            body = _json_or_empty(r)
            results.append(_check(
                "public_health_exact_status_ok",
                r.status_code == 200 and body == {"status": "ok"},
                f"status={r.status_code} body={body!r}",
            ))
            text_health = r.text

            r = c.get("/demo/providers/assemblyai/status")
            body = _json_or_empty(r)
            state_ok = False
            if r.status_code == 200 and isinstance(body, dict):
                aa = body.get("assemblyai")
                if isinstance(aa, dict) and aa.get("state") in ALLOWED_ASSEMBLYAI_STATES:
                    state_ok = True
            results.append(_check(
                "public_assemblyai_state_allowed",
                state_ok,
                f"status={r.status_code} body={body!r}",
            ))
            text_providers = r.text

            combined = text_health + "\n" + text_providers
            leaked = [f for f in ROUTER_HTTP_LEAK_FIELDS if f in combined]
            results.append(_check(
                "public_http_surface_no_router_fields",
                len(leaked) == 0,
                f"leaked={leaked}" if leaked else "no router fields leaked to /demo/health or /demo/providers/assemblyai/status",
            ))
    except Exception as exc:
        results.append(_check(
            "in_process_http_checks",
            False,
            f"{type(exc).__name__}: {exc}",
        ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--app-module",
        default="services.api.app.demo_main:app",
        help="MODULE:VAR for in-process TestClient mode",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # In-process runtime isolation: point the demo app at an ephemeral
    # runtime root so it does not require a writable system DB path.
    # Mirrors the env-setup precedent in the BR-05 manual-smoke fixture
    # generator (scripts/rp5/fixtures/generate_fixture_validate_broute_e2e_manual_smoke.py).
    with tempfile.TemporaryDirectory(prefix="broute_router_stub_smoke_") as tmp:
        prev = {
            k: os.environ.get(k)
            for k in (
                "DEMO_RUNTIME_ROOT",
                "ADMIN_STATS_USERNAME",
                "ADMIN_STATS_PASSWORD",
                "DEMO_LOG_TO_FILE",
            )
        }
        os.environ["DEMO_RUNTIME_ROOT"] = tmp
        os.environ.setdefault("ADMIN_STATS_USERNAME", "admin")
        os.environ.setdefault("ADMIN_STATS_PASSWORD", "shh-smoke-only")
        os.environ["DEMO_LOG_TO_FILE"] = "false"
        try:
            results = run_checks(args.app_module)
        finally:
            for k, v in prev.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    failures = [r for r in results if not r["passed"]]

    lines = [
        "# BR-06 Router Stub End-to-End Smoke Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"transport: in-process app-module {args.app_module}",
        "router_mode: deterministic_stub (stub-v0)",
        f"checks: {len(results)}",
        f"failures: {len(failures)}",
        "",
        "## Check Results",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")

    if failures:
        lines += [
            "",
            "## Result: B_ROUTE_ROUTER_SMOKE_FAILED",
            "",
            "B_ROUTE_ROUTER_SMOKE_FAILED",
        ]
        sentinel = "B_ROUTE_ROUTER_SMOKE_FAILED"
    else:
        lines += [
            "",
            "## Result: OK_BROUTE_ROUTER_STUB_SMOKE",
            "",
            f"All {len(results)} checks passed for router stub mode.",
            "",
            "OK_BROUTE_ROUTER_STUB_SMOKE",
        ]
        sentinel = "OK_BROUTE_ROUTER_STUB_SMOKE"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_BROUTE_ROUTER_STUB_SMOKE" else 1


if __name__ == "__main__":
    sys.exit(main())
