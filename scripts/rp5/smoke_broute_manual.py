#!/usr/bin/env python3
"""
B-route manual end-to-end smoke.
Runs HTTP probes against a running demo API to verify the BR-02 public health
contract, admin-auth invariants, and the BR-05 manual-mode-no-router-fields
invariant. Supports --base-url (live HTTP via httpx) and --app-module
(in-process TestClient) for fixture generation.
Emits OK_BROUTE_MANUAL_SMOKE on success or B_ROUTE_MANUAL_SMOKE_FAILED on failure.
"""
import argparse
import contextlib
import datetime
import importlib
import os
import pathlib
import sys


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


ROUTER_FIELDS = [
    "router_kind",
    "router_version",
    "routing_profile",
    "selected_backend",
    "allow_third_party",
]

PRIVACY_LEAK_NEEDLES = [
    "transcript",
    "hypothesis",
    "ground_truth",
    "reference_text",
    "session_id_hash",
    "ledger_id",
    "raw_payload",
    "ASSEMBLYAI_API_KEY",
]

ALLOWED_ASSEMBLYAI_STATES = {"available", "daily_quota_reached", "quota_exhausted", "disabled"}


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def _import_app(spec):
    module_name, _, attr = spec.partition(":")
    if not attr:
        raise ValueError(f"Invalid --app-module spec: {spec!r}")
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


class _LiveClient:
    def __init__(self, base_url):
        import httpx
        self._base = base_url.rstrip("/")
        self._httpx = httpx
        self._cm = None
        self._client = None

    def __enter__(self):
        self._client = self._httpx.Client(timeout=10.0)
        return self

    def __exit__(self, *a):
        if self._client is not None:
            self._client.close()

    def get(self, path, auth=None):
        return self._client.get(self._base + path, auth=auth)

    def post(self, path, json=None, auth=None):
        return self._client.post(self._base + path, json=json, auth=auth)


class _InProcClient:
    def __init__(self, app_module):
        self._app_module = app_module
        self._cm = None
        self._client = None

    def __enter__(self):
        from fastapi.testclient import TestClient
        app = _import_app(self._app_module)
        self._cm = TestClient(app)
        self._client = self._cm.__enter__()
        return self

    def __exit__(self, *a):
        if self._cm is not None:
            self._cm.__exit__(*a)

    def get(self, path, auth=None):
        return self._client.get(path, auth=auth)

    def post(self, path, json=None, auth=None):
        return self._client.post(path, json=json, auth=auth)


def _open_client(args):
    if args.base_url:
        return _LiveClient(args.base_url)
    return _InProcClient(args.app_module)


def _json_or_empty(resp):
    ctype = (resp.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        try:
            return resp.json()
        except Exception:
            return None
    return None


def run_checks(args):
    results = []
    user = args.admin_user or os.environ.get("ADMIN_STATS_USERNAME", "admin")
    password = args.admin_pass or os.environ.get("ADMIN_STATS_PASSWORD", "shh-smoke-only")

    try:
        client_cm = _open_client(args)
    except Exception as exc:
        results.append(_check("open_client", False, f"{type(exc).__name__}: {exc}"))
        return results

    try:
        with client_cm as c:
            # 1. public_health_exact
            r = c.get("/demo/health")
            body = _json_or_empty(r)
            ok = r.status_code == 200 and body == {"status": "ok"}
            results.append(_check("public_health_exact", ok, f"status={r.status_code} body={body!r}"))
            text_demo_health = r.text

            # 2. public_examples_shape
            r = c.get("/demo/examples")
            body = _json_or_empty(r)
            ok = (
                r.status_code == 200
                and isinstance(body, dict)
                and set(body.keys()) >= {"examples", "total", "note"}
                and isinstance(body.get("total"), int)
            )
            results.append(_check("public_examples_shape", ok, f"status={r.status_code} keys={sorted(body.keys()) if isinstance(body, dict) else None}"))
            text_examples = r.text

            # 3. public_assemblyai_state
            r = c.get("/demo/providers/assemblyai/status")
            body = _json_or_empty(r)
            state_ok = False
            if r.status_code == 200 and isinstance(body, dict):
                aa = body.get("assemblyai")
                if isinstance(aa, dict) and aa.get("state") in ALLOWED_ASSEMBLYAI_STATES:
                    state_ok = True
            results.append(_check("public_assemblyai_state", state_ok, f"status={r.status_code} body={body!r}"))
            text_providers = r.text

            # 4. public_run_cached_unknown_example_404
            r = c.post(
                "/demo/run-cached",
                json={
                    "example_id": "br05-synthetic-unknown",
                    "degradation_id": "far_field_room",
                    "provider": "whisper",
                },
            )
            results.append(_check(
                "public_run_cached_unknown_example_404",
                r.status_code == 404,
                f"status={r.status_code}",
            ))

            # 5. public_create_job_202
            r = c.post("/demo/jobs")
            body = _json_or_empty(r)
            job_id = None
            ok = (
                r.status_code == 202
                and isinstance(body, dict)
                and "job_id" in body
                and body.get("status") == "queued"
            )
            if ok:
                job_id = body["job_id"]
            results.append(_check("public_create_job_202", ok, f"status={r.status_code} body={body!r}"))

            # 6. public_job_lookup_responds
            if job_id is not None:
                r = c.get(f"/demo/jobs/{job_id}")
                body = _json_or_empty(r)
                lookup_ok = r.status_code in (200, 202) and isinstance(body, dict) and "status" in body
                results.append(_check("public_job_lookup_responds", lookup_ok, f"status={r.status_code} keys={sorted(body.keys()) if isinstance(body, dict) else None}"))
            else:
                results.append(_check("public_job_lookup_responds", False, "no job_id from create_job"))

            # 7. public_admin_health_requires_auth
            r = c.get("/admin/health", auth=None)
            results.append(_check(
                "public_admin_health_requires_auth",
                r.status_code == 401 and r.headers.get("WWW-Authenticate") == "Basic",
                f"status={r.status_code} WWW-Authenticate={r.headers.get('WWW-Authenticate')!r}",
            ))

            # 8. public_admin_health_with_auth_ok
            r = c.get("/admin/health", auth=(user, password))
            body = _json_or_empty(r)
            ok = (
                r.status_code == 200
                and isinstance(body, dict)
                and "db_ok" in body and "queue_depth" in body and "mode" in body
            )
            results.append(_check("public_admin_health_with_auth_ok", ok, f"status={r.status_code} keys={sorted(body.keys()) if isinstance(body, dict) else None}"))

            # 9. public_admin_stats_requires_auth
            r = c.get("/admin/stats", auth=None)
            results.append(_check(
                "public_admin_stats_requires_auth",
                r.status_code == 401,
                f"status={r.status_code}",
            ))

            # 10. manual_mode_no_router_fields
            # Router fields must be absent from ALL public responses (including
            # /demo/examples — DemoExample type does not include router fields).
            combined_router_scan_text = text_demo_health + "\n" + text_examples + "\n" + text_providers
            leaked_router = [f for f in ROUTER_FIELDS if f in combined_router_scan_text]
            results.append(_check(
                "manual_mode_no_router_fields",
                len(leaked_router) == 0,
                f"leaked: {leaked_router}" if leaked_router else "no router fields in public responses",
            ))

            # 11. public_no_privacy_leaks
            # Matches the existing precedent in
            # tests/demo/test_b12_1_admin_stats_fields.py::test_public_endpoints_full_string_scan_no_privacy_leakage:
            # scan /demo/health and /demo/providers/assemblyai/status only.
            # /demo/examples is intentionally excluded because DemoExample carries
            # the curated `ground_truth` field by design (needed by the frontend WER
            # calculation for curated examples; not a privacy leak).
            combined_privacy_scan_text = text_demo_health + "\n" + text_providers
            extra_needles = list(PRIVACY_LEAK_NEEDLES)
            if password:
                extra_needles.append(password)
            privacy_hits = [n for n in extra_needles if n in combined_privacy_scan_text]
            results.append(_check(
                "public_no_privacy_leaks",
                len(privacy_hits) == 0,
                f"leaks: {privacy_hits}" if privacy_hits else "no privacy/secret strings in /demo/health or /demo/providers/assemblyai/status (matches existing test_b12_1 precedent; /demo/examples excluded by design)",
            ))

    except Exception as exc:
        results.append(_check("smoke_runtime", False, f"{type(exc).__name__}: {exc}"))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None, help="Live HTTP base URL, e.g. http://127.0.0.1:8002")
    parser.add_argument("--app-module", default="services.api.app.demo_main:app", help="MODULE:VAR for in-process TestClient mode")
    parser.add_argument("--admin-user", default=None)
    parser.add_argument("--admin-pass", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = run_checks(args)
    failures = [r for r in results if not r["passed"]]

    transport = "base-url " + args.base_url if args.base_url else "in-process app-module " + args.app_module

    lines = [
        "# BR-05 Manual End-to-End Smoke Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"transport: {transport}",
        f"manual_mode_default: true (no router decoration expected on public responses)",
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
        lines += ["", "## Result: B_ROUTE_MANUAL_SMOKE_FAILED", "", "B_ROUTE_MANUAL_SMOKE_FAILED"]
        sentinel = "B_ROUTE_MANUAL_SMOKE_FAILED"
    else:
        lines += ["", "## Result: OK_BROUTE_MANUAL_SMOKE", "", f"All {len(results)} checks passed in manual mode.", "", "OK_BROUTE_MANUAL_SMOKE"]
        sentinel = "OK_BROUTE_MANUAL_SMOKE"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_BROUTE_MANUAL_SMOKE" else 1


if __name__ == "__main__":
    sys.exit(main())
