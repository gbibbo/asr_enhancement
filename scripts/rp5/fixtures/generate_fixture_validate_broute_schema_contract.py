#!/usr/bin/env python3
"""
Fixture generator for validate_broute_schema_contract.
Positive: run validator against the real libs/asr/router_runtime.py.
Negative: run validator against a temp stub module missing required fields.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/rp5/validate_broute_schema_contract.py"
REAL_SOURCE = REPO_ROOT / "libs/asr/router_runtime.py"

STUB_BROKEN_MODULE = '''from __future__ import annotations
import dataclasses


@dataclasses.dataclass
class RouterDecision:
    selected_backend: str
    router_kind: str


@dataclasses.dataclass
class AssembledResponse:
    transcript_text: str


class RouterRuntime:
    pass


def build_cache_key():
    return ""
'''


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_validator(source_file, out_path):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--source-file", str(source_file), "--out", str(out_path)],
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

    pos_out = fixture_dir / "validate_broute_schema_contract_positive.yaml"
    rc_pos, stdout_pos, content_pos = run_validator(REAL_SOURCE, pos_out)
    pos_sentinel = stdout_pos if stdout_pos in ("OK_BROUTE_SCHEMA_CONTRACT", "ROUTER_SCHEMA_DRIFT") else (
        "OK_BROUTE_SCHEMA_CONTRACT" if "OK_BROUTE_SCHEMA_CONTRACT" in content_pos else "ROUTER_SCHEMA_DRIFT"
    )
    pos_pass = pos_sentinel == "OK_BROUTE_SCHEMA_CONTRACT"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "source_file": str(REAL_SOURCE.relative_to(REPO_ROOT)),
    }

    neg_out = fixture_dir / "validate_broute_schema_contract_negative.yaml"
    with tempfile.TemporaryDirectory() as tmpdir:
        stub_path = pathlib.Path(tmpdir) / "router_runtime_broken.py"
        stub_path.write_text(STUB_BROKEN_MODULE)
        rc_neg, stdout_neg, content_neg = run_validator(stub_path, neg_out)
    neg_sentinel = stdout_neg if stdout_neg in ("OK_BROUTE_SCHEMA_CONTRACT", "ROUTER_SCHEMA_DRIFT") else (
        "ROUTER_SCHEMA_DRIFT" if "ROUTER_SCHEMA_DRIFT" in content_neg else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "ROUTER_SCHEMA_DRIFT"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "source_file": "temp_stub_broken_module",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = "OK_FIXTURE_VALIDATE_BROUTE_SCHEMA_CONTRACT" if all_pass else "ROUTER_SCHEMA_DRIFT"
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
