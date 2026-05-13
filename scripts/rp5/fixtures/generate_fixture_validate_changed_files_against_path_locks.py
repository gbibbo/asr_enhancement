#!/usr/bin/env python3
"""
Fixture generator for validate_changed_files_against_path_locks.
Positive fixture: classify_file returns a valid lock for each approved BR-00 file.
Negative fixture: classify_file returns None for unauthorized paths.
Uses direct unit-test of classify_file to avoid git diff timing issues during pre-commit fixture generation.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "scripts/rp5/validate_changed_files_against_path_locks.py"


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load_classify_file():
    spec = importlib.util.spec_from_file_location("vcp", str(VALIDATOR_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.classify_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", default="positive_and_negative")
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_dir = manifest_path.parent

    classify_file = load_classify_file()

    manifest = {
        "generated_at_utc": datetime.datetime.utcnow().isoformat(),
        "generator": str(pathlib.Path(__file__).relative_to(REPO_ROOT)),
        "fixtures": {},
    }

    # Positive fixture: BR-00 approved committed files — all must classify to a valid lock
    approved_files = [
        "scripts/rp5/validate_plan_compiles.py",
        "scripts/rp5/fixtures/generate_fixture_validate_plan_compiles.py",
        "scripts/rp5/validate_changed_files_against_path_locks.py",
        "scripts/rp5/fixtures/generate_fixture_validate_changed_files_against_path_locks.py",
        "reports/rp5/broute_plan_compile.md",
    ]
    pos_results = {f: classify_file(f) for f in approved_files}
    pos_pass = all(lock is not None for lock in pos_results.values())
    pos_content_lines = ["# Positive fixture: BR-00 approved files"]
    for f, lock in pos_results.items():
        status = "PASS" if lock else "FAIL"
        pos_content_lines.append(f"- [{status}] {f} -> {lock}")
    pos_sentinel = "OK_FIXTURE_VALIDATE_CHANGED_FILES_AGAINST_PATH_LOCKS" if pos_pass else "UNAUTHORIZED_FILE_TOUCHED"
    pos_content_lines.append("")
    pos_content_lines.append(pos_sentinel)

    pos_out = fixture_dir / "validate_changed_files_against_path_locks_positive.yaml"
    pos_out.write_text("\n".join(pos_content_lines) + "\n")

    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "method": "direct_classify_file_unit_test",
        "files_tested": approved_files,
        "classifications": pos_results,
    }

    # Negative fixture: unauthorized paths — all must return None (not classified to any lock)
    unauthorized_paths = [
        "docs/CLAUDE.md",
        "services/api/main.py",
        ".env",
        "tests/rp5/fixtures/validate_plan_compiles_positive.yaml",
        "reports/rp5/path_lock_validation.md",
        "setup.py",
    ]
    neg_results = {f: classify_file(f) for f in unauthorized_paths}
    neg_pass = all(lock is None for lock in neg_results.values())
    neg_content_lines = ["# Negative fixture: unauthorized paths must return None"]
    for f, lock in neg_results.items():
        status = "PASS" if lock is None else "FAIL"
        neg_content_lines.append(f"- [{status}] {f} -> {lock} (expected None)")
    neg_sentinel = "UNAUTHORIZED_FILE_TOUCHED" if neg_pass else "UNEXPECTED_PASS"
    neg_content_lines.append("")
    neg_content_lines.append(neg_sentinel)

    neg_out = fixture_dir / "validate_changed_files_against_path_locks_negative.yaml"
    neg_out.write_text("\n".join(neg_content_lines) + "\n")

    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "method": "direct_classify_file_unit_test",
        "paths_tested": unauthorized_paths,
        "classifications": neg_results,
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = "OK_FIXTURE_VALIDATE_CHANGED_FILES_AGAINST_PATH_LOCKS" if all_pass else "UNAUTHORIZED_FILE_TOUCHED"
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
