#!/usr/bin/env python3
"""
Fixture generator for validate_broute_e2e_router_stub_smoke.

Positive: router-stub smoke against services.api.app.demo_main:app (in-process).
Negative: router-stub smoke against a stub FastAPI app whose /demo/health leaks
router_kind and a forbidden health field (violates BR-02 health payload and
BR-05 manual_mode_no_router_fields invariants), forcing the smoke to emit
B_ROUTE_ROUTER_SMOKE_FAILED.

Both runs use --app-module (in-process TestClient) to avoid background uvicorn
at fixture time.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SMOKE = REPO_ROOT / "scripts/rp5/smoke_broute_router_stub.py"

STUB_LEAKY_APP = textwrap.dedent('''\
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/demo/health")
    async def h():
        # Deliberate violations: extra forbidden health field AND router_kind leak.
        return {"status": "ok", "router_kind": "leaked-stub"}

    @app.get("/demo/providers/assemblyai/status")
    async def p():
        return {"assemblyai": {"state": "disabled", "cap_state": "below"}}
''')


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_smoke(app_module, out_path, extra_syspath=None):
    env = os.environ.copy()
    if extra_syspath:
        env["PYTHONPATH"] = str(extra_syspath) + (
            ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
    result = subprocess.run(
        [sys.executable, str(SMOKE), "--app-module", app_module, "--out", str(out_path)],
        capture_output=True, text=True, env=env,
    )
    content = out_path.read_text() if out_path.exists() else ""
    return result.returncode, result.stdout.strip(), content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", default="positive_and_negative")
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_dir = manifest_path.parent

    manifest = {
        "generated_at_utc": datetime.datetime.utcnow().isoformat(),
        "generator": str(pathlib.Path(__file__).relative_to(REPO_ROOT)),
        "fixtures": {},
    }

    # Positive ---------------------------------------------------------------
    pos_out = fixture_dir / "validate_broute_e2e_router_stub_smoke_positive.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_router_stub_smoke_pos_") as tmp:
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
        os.environ["ADMIN_STATS_USERNAME"] = "admin"
        os.environ["ADMIN_STATS_PASSWORD"] = "shh-smoke-only"
        os.environ["DEMO_LOG_TO_FILE"] = "false"
        try:
            rc_pos, stdout_pos, content_pos = run_smoke(
                "services.api.app.demo_main:app", pos_out,
            )
        finally:
            for k, v in prev.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    pos_sentinel = stdout_pos if stdout_pos in (
        "OK_BROUTE_ROUTER_STUB_SMOKE",
        "B_ROUTE_ROUTER_SMOKE_FAILED",
    ) else (
        "OK_BROUTE_ROUTER_STUB_SMOKE"
        if "OK_BROUTE_ROUTER_STUB_SMOKE" in content_pos
        else "B_ROUTE_ROUTER_SMOKE_FAILED"
    )
    pos_pass = pos_sentinel == "OK_BROUTE_ROUTER_STUB_SMOKE"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "app_module": "services.api.app.demo_main:app",
    }

    # Negative ---------------------------------------------------------------
    neg_out = fixture_dir / "validate_broute_e2e_router_stub_smoke_negative.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_router_stub_smoke_neg_") as tmpdir:
        stub_pkg = pathlib.Path(tmpdir) / "broute_neg_router_stub_smoke"
        stub_pkg.mkdir()
        (stub_pkg / "__init__.py").write_text("")
        (stub_pkg / "leaky.py").write_text(STUB_LEAKY_APP)
        rc_neg, stdout_neg, content_neg = run_smoke(
            "broute_neg_router_stub_smoke.leaky:app", neg_out, extra_syspath=tmpdir,
        )

    neg_sentinel = stdout_neg if stdout_neg in (
        "OK_BROUTE_ROUTER_STUB_SMOKE",
        "B_ROUTE_ROUTER_SMOKE_FAILED",
    ) else (
        "B_ROUTE_ROUTER_SMOKE_FAILED"
        if "B_ROUTE_ROUTER_SMOKE_FAILED" in content_neg
        else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "B_ROUTE_ROUTER_SMOKE_FAILED"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "app_module": "temp_stub_leaky_router_kind",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = (
        "OK_FIXTURE_VALIDATE_BROUTE_E2E_ROUTER_STUB_SMOKE"
        if all_pass
        else "B_ROUTE_ROUTER_SMOKE_FAILED"
    )
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
