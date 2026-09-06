#!/usr/bin/env python3
"""
Fixture generator for validate_public_security_invariants.
Positive: real services.api.app.demo_main:app.
Negative: stub FastAPI app whose /admin/health is unauthenticated.
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
VALIDATOR = REPO_ROOT / "scripts/rp5/validate_public_security_invariants.py"


STUB_INSECURE_APP = textwrap.dedent('''\
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/demo/health")
    async def h():
        return {"status": "ok"}

    @app.get("/admin/health")
    async def ah():
        return {"db_ok": True, "queue_depth": 0, "mode": "demo"}

    @app.get("/admin/stats")
    async def s():
        return {"unauthenticated": True}

    @app.get("/demo/providers/assemblyai/status")
    async def p():
        return {"assemblyai": {"state": "disabled", "cap_state": "below"}}
''')


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_validator(app_module, out_path, extra_syspath=None):
    env = None
    if extra_syspath:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extra_syspath) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--app-module", app_module, "--out", str(out_path)],
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

    pos_out = fixture_dir / "validate_public_security_invariants_positive.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_security_") as tmp:
        prev_root = os.environ.get("DEMO_RUNTIME_ROOT")
        prev_user = os.environ.get("ADMIN_STATS_USERNAME")
        prev_pass = os.environ.get("ADMIN_STATS_PASSWORD")
        os.environ["DEMO_RUNTIME_ROOT"] = tmp
        os.environ["ADMIN_STATS_USERNAME"] = "admin"
        os.environ["ADMIN_STATS_PASSWORD"] = "shh-test-only"
        try:
            rc_pos, stdout_pos, content_pos = run_validator(
                "services.api.app.demo_main:app", pos_out,
            )
        finally:
            for k, v in (("DEMO_RUNTIME_ROOT", prev_root), ("ADMIN_STATS_USERNAME", prev_user), ("ADMIN_STATS_PASSWORD", prev_pass)):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    pos_sentinel = stdout_pos if stdout_pos in ("OK_PUBLIC_SECURITY_INVARIANTS", "PUBLIC_SECURITY_REGRESSION") else (
        "OK_PUBLIC_SECURITY_INVARIANTS" if "OK_PUBLIC_SECURITY_INVARIANTS" in content_pos else "PUBLIC_SECURITY_REGRESSION"
    )
    pos_pass = pos_sentinel == "OK_PUBLIC_SECURITY_INVARIANTS"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "app_module": "services.api.app.demo_main:app",
    }

    neg_out = fixture_dir / "validate_public_security_invariants_negative.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_security_neg_") as tmpdir:
        stub_pkg = pathlib.Path(tmpdir) / "broute_neg_security"
        stub_pkg.mkdir()
        (stub_pkg / "__init__.py").write_text("")
        (stub_pkg / "insecure.py").write_text(STUB_INSECURE_APP)
        rc_neg, stdout_neg, content_neg = run_validator(
            "broute_neg_security.insecure:app", neg_out, extra_syspath=tmpdir,
        )
    neg_sentinel = stdout_neg if stdout_neg in ("OK_PUBLIC_SECURITY_INVARIANTS", "PUBLIC_SECURITY_REGRESSION") else (
        "PUBLIC_SECURITY_REGRESSION" if "PUBLIC_SECURITY_REGRESSION" in content_neg else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "PUBLIC_SECURITY_REGRESSION"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "app_module": "temp_stub_insecure_admin_health",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = "OK_FIXTURE_VALIDATE_PUBLIC_SECURITY_INVARIANTS" if all_pass else "PUBLIC_SECURITY_REGRESSION"
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
