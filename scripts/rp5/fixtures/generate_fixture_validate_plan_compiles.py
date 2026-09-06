#!/usr/bin/env python3
"""
Fixture generator for validate_plan_compiles.
Positive fixture: runs validator against the real plan docs (expects OK_PLAN_COMPILES).
Negative fixture: runs validator against an empty directory (expects PLAN_CONFLICT).
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/rp5/validate_plan_compiles.py"


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_validator(plan_dir, out_path):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--plan-dir", str(plan_dir), "--out", str(out_path)],
        capture_output=True, text=True,
    )
    content = out_path.read_text() if out_path.exists() else ""
    stdout = result.stdout.strip()
    return result.returncode, stdout, content


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

    # Positive fixture: real plan directory
    pos_out = fixture_dir / "validate_plan_compiles_positive.yaml"
    rc, stdout, content = run_validator(REPO_ROOT / "docs/plans/broute", pos_out)
    pos_sentinel = stdout if stdout in ("OK_PLAN_COMPILES", "PLAN_CONFLICT") else (
        "OK_PLAN_COMPILES" if "OK_PLAN_COMPILES" in content else "PLAN_CONFLICT"
    )
    pos_pass = pos_sentinel == "OK_PLAN_COMPILES"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "plan_dir": "docs/plans/broute",
    }

    # Negative fixture: empty temporary directory (missing plan files)
    neg_out = fixture_dir / "validate_plan_compiles_negative.yaml"
    with tempfile.TemporaryDirectory() as tmpdir:
        rc_neg, stdout_neg, content_neg = run_validator(pathlib.Path(tmpdir), neg_out)
    neg_sentinel = stdout_neg if stdout_neg in ("OK_PLAN_COMPILES", "PLAN_CONFLICT") else (
        "PLAN_CONFLICT" if "PLAN_CONFLICT" in content_neg else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "PLAN_CONFLICT"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "plan_dir": "empty_temp_dir",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = "OK_FIXTURE_VALIDATE_PLAN_COMPILES" if all_pass else "PLAN_CONFLICT"
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
