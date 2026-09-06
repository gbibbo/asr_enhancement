#!/usr/bin/env python3
"""
Fixture generator for validate_broute_e2e_manual_smoke.
Positive: smoke against real services.api.app.demo_main:app (in-process).
Negative: smoke against a stub FastAPI app whose /demo/health leaks router_kind
(violates the BR-05 manual-mode-no-router-fields invariant).
Both runs use --app-module (in-process TestClient) to avoid background uvicorn at fixture time.
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
SMOKE = REPO_ROOT / "scripts/rp5/smoke_broute_manual.py"

STUB_LEAKY_APP = textwrap.dedent('''\
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/demo/health")
    async def h():
        # Deliberate manual-mode-invariant violation: router_kind must not appear in manual mode
        return {"status": "ok", "router_kind": "leaked-stub"}

    @app.get("/demo/examples")
    async def ex():
        return {"examples": [], "total": 0, "note": None}

    @app.get("/demo/providers/assemblyai/status")
    async def p():
        return {"assemblyai": {"state": "disabled", "cap_state": "below"}}

    @app.post("/demo/run-cached")
    async def rc():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Example not found")

    @app.post("/demo/jobs", status_code=202)
    async def j():
        return {"job_id": "stub-job", "status": "queued"}

    @app.get("/demo/jobs/{job_id}")
    async def jl(job_id: str):
        return {"job_id": job_id, "status": "queued"}

    @app.get("/admin/health")
    async def ah():
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})

    @app.get("/admin/stats")
    async def s():
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
''')


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_smoke(app_module, out_path, extra_syspath=None):
    env = os.environ.copy()
    if extra_syspath:
        env["PYTHONPATH"] = str(extra_syspath) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
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

    pos_out = fixture_dir / "validate_broute_e2e_manual_smoke_positive.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_manual_smoke_pos_") as tmp:
        prev_root = os.environ.get("DEMO_RUNTIME_ROOT")
        prev_user = os.environ.get("ADMIN_STATS_USERNAME")
        prev_pass = os.environ.get("ADMIN_STATS_PASSWORD")
        prev_log = os.environ.get("DEMO_LOG_TO_FILE")
        os.environ["DEMO_RUNTIME_ROOT"] = tmp
        os.environ["ADMIN_STATS_USERNAME"] = "admin"
        os.environ["ADMIN_STATS_PASSWORD"] = "shh-smoke-only"
        os.environ["DEMO_LOG_TO_FILE"] = "false"
        try:
            rc_pos, stdout_pos, content_pos = run_smoke(
                "services.api.app.demo_main:app", pos_out,
            )
        finally:
            for k, v in (
                ("DEMO_RUNTIME_ROOT", prev_root),
                ("ADMIN_STATS_USERNAME", prev_user),
                ("ADMIN_STATS_PASSWORD", prev_pass),
                ("DEMO_LOG_TO_FILE", prev_log),
            ):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    pos_sentinel = stdout_pos if stdout_pos in ("OK_BROUTE_MANUAL_SMOKE", "B_ROUTE_MANUAL_SMOKE_FAILED") else (
        "OK_BROUTE_MANUAL_SMOKE" if "OK_BROUTE_MANUAL_SMOKE" in content_pos else "B_ROUTE_MANUAL_SMOKE_FAILED"
    )
    pos_pass = pos_sentinel == "OK_BROUTE_MANUAL_SMOKE"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "app_module": "services.api.app.demo_main:app",
    }

    neg_out = fixture_dir / "validate_broute_e2e_manual_smoke_negative.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_manual_smoke_neg_") as tmpdir:
        stub_pkg = pathlib.Path(tmpdir) / "broute_neg_manual_smoke"
        stub_pkg.mkdir()
        (stub_pkg / "__init__.py").write_text("")
        (stub_pkg / "leaky.py").write_text(STUB_LEAKY_APP)
        rc_neg, stdout_neg, content_neg = run_smoke(
            "broute_neg_manual_smoke.leaky:app", neg_out, extra_syspath=tmpdir,
        )
    neg_sentinel = stdout_neg if stdout_neg in ("OK_BROUTE_MANUAL_SMOKE", "B_ROUTE_MANUAL_SMOKE_FAILED") else (
        "B_ROUTE_MANUAL_SMOKE_FAILED" if "B_ROUTE_MANUAL_SMOKE_FAILED" in content_neg else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "B_ROUTE_MANUAL_SMOKE_FAILED"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "app_module": "temp_stub_leaky_router_kind",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = "OK_FIXTURE_VALIDATE_BROUTE_E2E_MANUAL_SMOKE" if all_pass else "B_ROUTE_MANUAL_SMOKE_FAILED"
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
