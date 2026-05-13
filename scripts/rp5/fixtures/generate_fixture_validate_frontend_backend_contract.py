#!/usr/bin/env python3
"""
Fixture generator for validate_frontend_backend_contract.
Positive: validator against real services/frontend/app/demo/types.ts (post-edit).
Negative: validator against a temp TS file that re-introduces db_ok inside DemoHealthResponse.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/rp5/validate_frontend_backend_contract.py"
REAL_TYPES = REPO_ROOT / "services/frontend/app/demo/types.ts"

STUB_DRIFTING_TYPES = textwrap.dedent('''\
    export type DemoHealthResponse = {
      status: "ok";
      db_ok: boolean;
      queue_depth: number;
    };
''')


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_validator(types_file, out_path):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--types-file", str(types_file), "--out", str(out_path)],
        capture_output=True, text=True,
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

    pos_out = fixture_dir / "validate_frontend_backend_contract_positive.yaml"
    rc_pos, stdout_pos, content_pos = run_validator(REAL_TYPES, pos_out)
    pos_sentinel = stdout_pos if stdout_pos in ("OK_FRONTEND_BACKEND_CONTRACT", "FRONTEND_BACKEND_DRIFT") else (
        "OK_FRONTEND_BACKEND_CONTRACT" if "OK_FRONTEND_BACKEND_CONTRACT" in content_pos else "FRONTEND_BACKEND_DRIFT"
    )
    pos_pass = pos_sentinel == "OK_FRONTEND_BACKEND_CONTRACT"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "types_file": str(REAL_TYPES.relative_to(REPO_ROOT)),
    }

    neg_out = fixture_dir / "validate_frontend_backend_contract_negative.yaml"
    with tempfile.TemporaryDirectory() as tmpdir:
        stub_path = pathlib.Path(tmpdir) / "drifting_types.ts"
        stub_path.write_text(STUB_DRIFTING_TYPES)
        rc_neg, stdout_neg, content_neg = run_validator(stub_path, neg_out)
    neg_sentinel = stdout_neg if stdout_neg in ("OK_FRONTEND_BACKEND_CONTRACT", "FRONTEND_BACKEND_DRIFT") else (
        "FRONTEND_BACKEND_DRIFT" if "FRONTEND_BACKEND_DRIFT" in content_neg else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "FRONTEND_BACKEND_DRIFT"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "types_file": "temp_stub_drifting_types_ts",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = "OK_FIXTURE_VALIDATE_FRONTEND_BACKEND_CONTRACT" if all_pass else "FRONTEND_BACKEND_DRIFT"
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
