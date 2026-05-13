#!/usr/bin/env python3
"""
Public security invariants validator.
Confirms:
- /demo/health body is exactly {"status": "ok"}
- /admin/health requires HTTPBasic auth (401 without/with bad creds; 200 with correct)
- /admin/stats requires HTTPBasic auth (regression check)
- Public response text contains no privacy/secret-leak strings
Emits OK_PUBLIC_SECURITY_INVARIANTS on success or PUBLIC_SECURITY_REGRESSION on failure.
"""
import argparse
import datetime
import importlib
import os
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


PRIVACY_LEAK_NEEDLES = [
    "transcript", "hypothesis", "ground_truth", "reference_text",
    "session_id_hash", "ledger_id", "raw_payload", "ASSEMBLYAI_API_KEY",
]

_ADMIN_USER_DEFAULT = "admin"
_ADMIN_PASS_DEFAULT = "shh-test-only"


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def _import_app(spec):
    module_name, _, attr = spec.partition(":")
    if not attr:
        raise ValueError(f"Invalid --app-module spec: {spec!r} (expected MODULE:VAR)")
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


def _setup_admin_env(monkeypatch_env):
    if not os.environ.get("ADMIN_STATS_USERNAME"):
        os.environ["ADMIN_STATS_USERNAME"] = _ADMIN_USER_DEFAULT
        monkeypatch_env.append("ADMIN_STATS_USERNAME")
    if not os.environ.get("ADMIN_STATS_PASSWORD"):
        os.environ["ADMIN_STATS_PASSWORD"] = _ADMIN_PASS_DEFAULT
        monkeypatch_env.append("ADMIN_STATS_PASSWORD")
    if not os.environ.get("DEMO_RUNTIME_ROOT"):
        import tempfile
        tmp = tempfile.mkdtemp(prefix="validate_security_")
        os.environ["DEMO_RUNTIME_ROOT"] = tmp
        monkeypatch_env.append("DEMO_RUNTIME_ROOT")


def _teardown_admin_env(monkeypatch_env):
    for var in monkeypatch_env:
        os.environ.pop(var, None)


def run_checks(args):
    results = []
    user = os.environ.get("ADMIN_STATS_USERNAME", _ADMIN_USER_DEFAULT)
    password = os.environ.get("ADMIN_STATS_PASSWORD", _ADMIN_PASS_DEFAULT)

    if args.base_url:
        import httpx
        base = args.base_url.rstrip("/")
        def get(path, auth=None):
            r = httpx.get(base + path, auth=auth, timeout=10.0)
            return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else {}, r.headers, r.text
        try:
            health_status, health_body, _, health_text = get("/demo/health")
            admin_no_status, _, admin_no_headers, _ = get("/admin/health")
            admin_bad_status, _, _, _ = get("/admin/health", auth=("wrong", "wrong"))
            admin_ok_status, admin_ok_body, _, _ = get("/admin/health", auth=(user, password))
            stats_no_status, _, _, _ = get("/admin/stats")
            providers_status, _, _, providers_text = get("/demo/providers/assemblyai/status")
        except Exception as exc:
            results.append(_check("requests_succeed", False, f"{type(exc).__name__}: {exc}"))
            return results
    else:
        from fastapi.testclient import TestClient
        app = _import_app(args.app_module)
        try:
            with TestClient(app) as client:
                r = client.get("/demo/health")
                health_status, health_body, health_text = r.status_code, r.json(), r.text
                r = client.get("/admin/health")
                admin_no_status, admin_no_headers = r.status_code, r.headers
                r = client.get("/admin/health", auth=("wrong", "wrong"))
                admin_bad_status = r.status_code
                r = client.get("/admin/health", auth=(user, password))
                admin_ok_status, admin_ok_body = r.status_code, r.json()
                r = client.get("/admin/stats")
                stats_no_status = r.status_code
                r = client.get("/demo/providers/assemblyai/status")
                providers_status, providers_text = r.status_code, r.text
        except Exception as exc:
            results.append(_check("requests_succeed", False, f"{type(exc).__name__}: {exc}"))
            return results

    results.append(_check("public_health_exact_status_ok",
                          health_status == 200 and health_body == {"status": "ok"},
                          f"status={health_status} body={health_body}"))
    results.append(_check("admin_health_no_creds_401",
                          admin_no_status == 401,
                          f"status={admin_no_status}"))
    results.append(_check("admin_health_www_authenticate_basic",
                          admin_no_headers.get("WWW-Authenticate") == "Basic",
                          f"WWW-Authenticate={admin_no_headers.get('WWW-Authenticate')!r}"))
    results.append(_check("admin_health_bad_creds_401",
                          admin_bad_status == 401,
                          f"status={admin_bad_status}"))
    results.append(_check("admin_health_correct_creds_200",
                          admin_ok_status == 200,
                          f"status={admin_ok_status}"))
    if admin_ok_status == 200:
        diagnostic_keys_present = all(k in admin_ok_body for k in ("db_ok", "queue_depth", "mode"))
        results.append(_check("admin_health_has_diagnostic_keys",
                              diagnostic_keys_present,
                              f"keys={sorted(admin_ok_body.keys())}"))
    results.append(_check("admin_stats_no_creds_401",
                          stats_no_status == 401,
                          f"status={stats_no_status}"))

    public_blobs = [("demo/health", health_text), ("demo/providers/assemblyai/status", providers_text)]
    for label, blob in public_blobs:
        leaks = [n for n in PRIVACY_LEAK_NEEDLES if n in blob]
        results.append(_check(
            f"no_privacy_leaks_in_{label.replace('/', '_')}",
            len(leaks) == 0,
            f"leaks={leaks}" if leaks else "no privacy/secret strings present",
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

    monkeypatch_env = []
    if not args.base_url:
        _setup_admin_env(monkeypatch_env)
    try:
        results = run_checks(args)
    finally:
        _teardown_admin_env(monkeypatch_env)

    failures = [r for r in results if not r["passed"]]

    lines = [
        "# BR-02 Public Security Invariants Report",
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
        lines += ["", "## Result: PUBLIC_SECURITY_REGRESSION", "", "PUBLIC_SECURITY_REGRESSION"]
        sentinel = "PUBLIC_SECURITY_REGRESSION"
    else:
        lines += ["", "## Result: OK_PUBLIC_SECURITY_INVARIANTS", "", "OK_PUBLIC_SECURITY_INVARIANTS"]
        sentinel = "OK_PUBLIC_SECURITY_INVARIANTS"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_PUBLIC_SECURITY_INVARIANTS" else 1


if __name__ == "__main__":
    sys.exit(main())
