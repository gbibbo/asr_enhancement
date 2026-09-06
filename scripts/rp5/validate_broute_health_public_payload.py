#!/usr/bin/env python3
"""
B-route health public payload validator.
Checks that GET /demo/health returns exactly {"status": "ok"} and no diagnostic fields.
Emits OK_BROUTE_HEALTH_PUBLIC_PAYLOAD on success or B_ROUTE_HEALTH_PAYLOAD_REGRESSION on failure.
Supports --app-module (in-process TestClient) or --base-url (live HTTP).
"""
import argparse
import datetime
import importlib
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


FORBIDDEN_FIELDS = [
    "version", "build", "commit", "uptime", "queue_depth",
    "cache_stats", "worker_count", "model_name", "provider_state",
    "env_flags", "hostname",
]

PRIVACY_FIELDS = [
    "transcript", "hypothesis", "ground_truth", "reference_text",
    "session_id_hash", "ledger_id", "raw_payload",
]


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def _import_app(spec):
    module_name, _, attr = spec.partition(":")
    if not attr:
        raise ValueError(f"Invalid --app-module spec: {spec!r} (expected MODULE:VAR)")
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


def _get_health(args):
    if args.base_url:
        import httpx
        url = args.base_url.rstrip("/") + "/demo/health"
        r = httpx.get(url, timeout=10.0)
        return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    from fastapi.testclient import TestClient
    app = _import_app(args.app_module)
    with TestClient(app) as client:
        r = client.get("/demo/health")
        return r.status_code, r.json()


def run_checks(args):
    results = []
    try:
        status_code, body = _get_health(args)
    except Exception as exc:
        results.append(_check("health_request_succeeds", False, f"{type(exc).__name__}: {exc}"))
        return results

    results.append(_check("health_returns_200", status_code == 200, f"status_code={status_code}"))
    results.append(_check("body_is_json_object", isinstance(body, dict), f"type={type(body).__name__}"))
    if not isinstance(body, dict):
        return results

    keys = set(body.keys())
    results.append(_check("body_key_set_is_status_only", keys == {"status"}, f"keys={sorted(keys)}"))
    results.append(_check("status_value_is_ok", body.get("status") == "ok", f"status={body.get('status')!r}"))

    leaked_forbidden = [f for f in FORBIDDEN_FIELDS if f in body]
    results.append(_check(
        "no_forbidden_diagnostic_fields",
        len(leaked_forbidden) == 0,
        f"leaked: {leaked_forbidden}" if leaked_forbidden else "none of the diagnostic fields present",
    ))

    leaked_privacy = [f for f in PRIVACY_FIELDS if f in body]
    results.append(_check(
        "no_privacy_fields",
        len(leaked_privacy) == 0,
        f"leaked: {leaked_privacy}" if leaked_privacy else "no privacy keys present",
    ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-module", default="services.api.app.demo_main:app")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = run_checks(args)
    failures = [r for r in results if not r["passed"]]

    lines = [
        "# BR-02 B-route Health Public Payload Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"transport: {'base-url ' + args.base_url if args.base_url else 'in-process app-module ' + args.app_module}",
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
        lines += ["", "## Result: B_ROUTE_HEALTH_PAYLOAD_REGRESSION", "", "B_ROUTE_HEALTH_PAYLOAD_REGRESSION"]
        sentinel = "B_ROUTE_HEALTH_PAYLOAD_REGRESSION"
    else:
        lines += ["", "## Result: OK_BROUTE_HEALTH_PUBLIC_PAYLOAD", "", "OK_BROUTE_HEALTH_PUBLIC_PAYLOAD"]
        sentinel = "OK_BROUTE_HEALTH_PUBLIC_PAYLOAD"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_BROUTE_HEALTH_PUBLIC_PAYLOAD" else 1


if __name__ == "__main__":
    sys.exit(main())
