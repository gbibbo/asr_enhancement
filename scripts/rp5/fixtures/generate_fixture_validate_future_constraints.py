#!/usr/bin/env python3
"""
Fixture generator for validate_future_constraints.

Positive: validate the real reports/rp5/broute_future_constraints.md and
capture the validator output as the positive fixture.

Negative: validate a synthetic constraints file missing FC-B14-1-FUNNEL and
capture the validator output as the negative fixture (expected sentinel:
FUTURE_CONSTRAINT_REGRESSION).

Emits OK_FIXTURE_VALIDATE_FUTURE_CONSTRAINTS on success.
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
VALIDATOR = REPO_ROOT / "scripts/rp5/validate_future_constraints.py"
REAL_CONSTRAINTS = REPO_ROOT / "reports/rp5/broute_future_constraints.md"

SYNTHETIC_NEGATIVE_CONSTRAINTS = textwrap.dedent("""\
    # Synthetic negative fixture for validate_future_constraints

    Only three of the four required FC ids are present here. FC-B14-1-FUNNEL is
    deliberately omitted so the validator must emit FUTURE_CONSTRAINT_REGRESSION.

    ## FC-B14-0-PUBLIC-GATE

    - constraint_id: FC-B14-0-PUBLIC-GATE
    - source_preplan_section: preplan §4
    - current_scope_impact: B-route must not expose public routes
    - must_preserve_in_current_plan: B14.0 starts after B-route PASS
    - forbidden_current_plan_regression: adding recruiter auth or public tunnel work inside B-route
    - validator_or_review_check: validate_future_constraints
    - future_phase_owner: B14.0
    - out_of_scope_but_preserved: true

    ## FC-B15-MULTI-NETWORK

    - constraint_id: FC-B15-MULTI-NETWORK
    - source_preplan_section: preplan §6
    - current_scope_impact: B-route response fields must remain smokeable
    - must_preserve_in_current_plan: B15 starts after B14.1 PASS
    - forbidden_current_plan_regression: claiming public smoke coverage from local B-route tests
    - validator_or_review_check: validate_future_constraints
    - future_phase_owner: B15
    - out_of_scope_but_preserved: true

    ## FC-HANDOFF-DATAMOVE1

    - constraint_id: FC-HANDOFF-DATAMOVE1
    - source_preplan_section: preplan §7
    - current_scope_impact: B-route schema must be adapter-compatible
    - must_preserve_in_current_plan: handoff swap waits for datamove1 tag
    - forbidden_current_plan_regression: changing schema after handoff compatibility gate without diff report
    - validator_or_review_check: validate_future_constraints
    - future_phase_owner: B-handoff
    - out_of_scope_but_preserved: true
""")


def sha256_path(path):
    p = pathlib.Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run_validator(constraints_path, out_path):
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--constraints",
            str(constraints_path),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
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
    pos_out = fixture_dir / "validate_future_constraints_positive.yaml"
    rc_pos, stdout_pos, content_pos = run_validator(REAL_CONSTRAINTS, pos_out)
    pos_sentinel = stdout_pos if stdout_pos in (
        "OK_FUTURE_CONSTRAINTS",
        "FUTURE_CONSTRAINT_REGRESSION",
    ) else (
        "OK_FUTURE_CONSTRAINTS"
        if "OK_FUTURE_CONSTRAINTS" in content_pos
        else "FUTURE_CONSTRAINT_REGRESSION"
    )
    pos_pass = pos_sentinel == "OK_FUTURE_CONSTRAINTS"
    manifest["fixtures"]["positive"] = {
        "path": str(pos_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(pos_out),
        "sentinel": pos_sentinel,
        "pass": pos_pass,
        "constraints_source": str(REAL_CONSTRAINTS.relative_to(REPO_ROOT)),
    }

    # Negative ---------------------------------------------------------------
    neg_out = fixture_dir / "validate_future_constraints_negative.yaml"
    with tempfile.TemporaryDirectory(prefix="fixture_future_constraints_neg_") as tmpdir:
        neg_constraints = pathlib.Path(tmpdir) / "broute_future_constraints_missing_funnel.md"
        neg_constraints.write_text(SYNTHETIC_NEGATIVE_CONSTRAINTS)
        rc_neg, stdout_neg, content_neg = run_validator(neg_constraints, neg_out)
    neg_sentinel = stdout_neg if stdout_neg in (
        "OK_FUTURE_CONSTRAINTS",
        "FUTURE_CONSTRAINT_REGRESSION",
    ) else (
        "FUTURE_CONSTRAINT_REGRESSION"
        if "FUTURE_CONSTRAINT_REGRESSION" in content_neg
        else "UNEXPECTED"
    )
    neg_pass = neg_sentinel == "FUTURE_CONSTRAINT_REGRESSION"
    manifest["fixtures"]["negative"] = {
        "path": str(neg_out.resolve().relative_to(REPO_ROOT)),
        "sha256": sha256_path(neg_out),
        "sentinel": neg_sentinel,
        "pass": neg_pass,
        "constraints_source": "synthetic_missing_FC-B14-1-FUNNEL",
    }

    all_pass = pos_pass and neg_pass
    manifest["sentinel"] = (
        "OK_FIXTURE_VALIDATE_FUTURE_CONSTRAINTS"
        if all_pass
        else "FUTURE_CONSTRAINT_REGRESSION"
    )
    manifest["positive_pass"] = pos_pass
    manifest["negative_pass"] = neg_pass

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(manifest["sentinel"])
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
