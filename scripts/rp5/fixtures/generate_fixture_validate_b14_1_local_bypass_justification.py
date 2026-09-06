#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_1_local_bypass_justification.

Materialises one positive and four negative fixture trees that exercise
the validator's two failure modes (a flag-keyed authority-bypass surface
detected by the scanner; and a malformed local_bypass_justification_record
report) and asserts that the validator emits the expected sentinel/marker
in each case.

The generator never writes any real secret, hostname, public URL, or
Authorization value into any fixture. The "bypass-shaped" code body in
the negative fixture is a synthetic skeleton that references the flag
identifier and authority-context vocabulary; it is not a working FastAPI
module and is not executable.

Emits OK_FIXTURE_VALIDATE_B14_1_LOCAL_BYPASS_JUSTIFIED on PASS or
B14_1_LOCAL_BYPASS_UNJUSTIFIED on FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_1_LOCAL_BYPASS_JUSTIFIED"
SENTINEL_FAIL = "B14_1_LOCAL_BYPASS_UNJUSTIFIED"
VALIDATOR_PASS = "OK_B14_1_LOCAL_BYPASS_JUSTIFIED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    REPO_ROOT / "scripts" / "rp5"
    / "validate_b14_1_local_bypass_justification.py"
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hash_tree(root: pathlib.Path) -> list[dict]:
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            files.append({
                "path": str(p.relative_to(root)),
                "sha256": sha256_bytes(data),
                "size_bytes": len(data),
            })
    return files


GOOD_REPORT_BODY = """# Local Bypass Justification (fixture)

```yaml
record_kind: local_bypass_justification_record
classification: explicit_NA_zero_bypasses
bypass_count: 0
applies_when_flag_is: PUBLIC_DEMO_EXPOSURE_false
must_be_disabled_when_flag_is: PUBLIC_DEMO_EXPOSURE_true
validator: validate_b14_1_local_bypass_justification
marker: B14_1_LOCAL_BYPASS_UNJUSTIFIED
bypasses: []
```
"""


WRONG_MARKER_REPORT_BODY = """# Local Bypass Justification (fixture, wrong marker)

```yaml
record_kind: local_bypass_justification_record
classification: explicit_NA_zero_bypasses
bypass_count: 0
applies_when_flag_is: PUBLIC_DEMO_EXPOSURE_false
must_be_disabled_when_flag_is: PUBLIC_DEMO_EXPOSURE_true
validator: validate_b14_1_local_bypass_justification
marker: NOT_THE_RIGHT_MARKER
bypasses: []
```
"""


ENUMERATES_REPORT_BODY = """# Local Bypass Justification (fixture, enumerates bypass under NA)

```yaml
record_kind: local_bypass_justification_record
classification: explicit_NA_zero_bypasses
bypass_count: 0
applies_when_flag_is: PUBLIC_DEMO_EXPOSURE_false
must_be_disabled_when_flag_is: PUBLIC_DEMO_EXPOSURE_true
validator: validate_b14_1_local_bypass_justification
marker: B14_1_LOCAL_BYPASS_UNJUSTIFIED
bypasses:
  - bypass_id: BYPASS-FIXTURE-1
    bypass_surface: synthetic
```
"""


# Synthetic skeleton — references the flag identifier and the authority
# vocabulary token Depends( on a following line, forcing the validator
# to classify the hit as BYPASS_CANDIDATE. This is not executable code.
BYPASS_SHAPED_BODY = """from synthetic.fixture import get_public_demo_exposure_flag, recruiter_auth_dependency
from fastapi import Depends


def attach_routes(app):
    if not get_public_demo_exposure_flag():
        # Synthetic local/dev bypass: skip recruiter dependency when flag is false.
        app.add_api_route(
            \"/demo/health\",
            lambda: {\"status\": \"ok\"},
        )
    else:
        app.add_api_route(
            \"/demo/health\",
            lambda: {\"status\": \"ok\"},
            dependencies=[Depends(recruiter_auth_dependency)],
        )
"""


# Visibility-only synthetic block: references the flag, but only in
# proximity to openapi_url/docs_url/redoc_url tokens. The classifier must
# allow this as CLASS C and the scanner must produce zero BYPASS_CANDIDATE.
VISIBILITY_ONLY_BODY = """from synthetic.fixture import get_public_demo_exposure_flag


def build_app():
    if get_public_demo_exposure_flag():
        return FastAPI(
            title=\"synthetic\",
            openapi_url=None,
            docs_url=None,
            redoc_url=None,
        )
    return FastAPI(title=\"synthetic\")
"""


def _materialise_empty_tree(root: pathlib.Path) -> None:
    (root / "services" / "api" / "app").mkdir(parents=True, exist_ok=True)
    (root / "reports" / "rp5").mkdir(parents=True, exist_ok=True)


def _materialise_visibility_tree(root: pathlib.Path) -> None:
    _materialise_empty_tree(root)
    (root / "services" / "api" / "app" / "visibility_only.py").write_text(
        VISIBILITY_ONLY_BODY, encoding="utf-8"
    )


def _materialise_bypass_tree(root: pathlib.Path) -> None:
    _materialise_empty_tree(root)
    (root / "services" / "api" / "app" / "bypass_shaped.py").write_text(
        BYPASS_SHAPED_BODY, encoding="utf-8"
    )


def run_validator(root: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(
        suffix=".md", delete=False, mode="w"
    ) as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--root", str(root),
                "--out", str(transcript),
            ],
            capture_output=True, text=True,
        )
        out = proc.stdout.strip().splitlines()
        return out[-1] if out else ""
    finally:
        transcript.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = (
        manifest_path.parent
        / "validate_b14_1_local_bypass_justification"
    )
    fixtures_root.mkdir(parents=True, exist_ok=True)

    pos_root = fixtures_root / "positive"
    neg_root = fixtures_root / "negative"
    pos_root.mkdir(parents=True, exist_ok=True)
    neg_root.mkdir(parents=True, exist_ok=True)

    # Materialise positive fixture tree (committed for audit).
    _materialise_visibility_tree(pos_root)
    (pos_root / "reports" / "rp5" / "b14_1_local_bypass_justification.md").write_text(
        GOOD_REPORT_BODY, encoding="utf-8"
    )

    # Materialise negative fixture trees (committed for audit). Each
    # negative case carries only the files needed to exercise its single
    # failure mode, to keep the committed footprint within the
    # PL-B14_1-TESTS cap declared in agent_plan §1.
    cases = {
        "negative_bypass_candidate_with_clean_report": {
            "factory": _materialise_bypass_tree,
            "report_body": GOOD_REPORT_BODY,
            "expected_sentinel": SENTINEL_FAIL,
        },
        "negative_report_missing": {
            "factory": _materialise_empty_tree,
            "report_body": None,
            "expected_sentinel": SENTINEL_FAIL,
        },
        "negative_report_wrong_marker": {
            "factory": _materialise_empty_tree,
            "report_body": WRONG_MARKER_REPORT_BODY,
            "expected_sentinel": SENTINEL_FAIL,
        },
        "negative_report_enumerates_bypass_under_NA": {
            "factory": _materialise_empty_tree,
            "report_body": ENUMERATES_REPORT_BODY,
            "expected_sentinel": SENTINEL_FAIL,
        },
    }
    for case_name, spec in cases.items():
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        spec["factory"](case_root)
        report_dir = case_root / "reports" / "rp5"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "b14_1_local_bypass_justification.md"
        if spec["report_body"] is not None:
            report_file.write_text(spec["report_body"], encoding="utf-8")

    adversarial_failures: list[str] = []
    neg_entries: list[dict] = []
    for case_name, spec in cases.items():
        case_root = neg_root / case_name
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            spec["factory"](tmp_path)
            tmp_report_dir = tmp_path / "reports" / "rp5"
            tmp_report_dir.mkdir(parents=True, exist_ok=True)
            if spec["report_body"] is not None:
                (tmp_report_dir / "b14_1_local_bypass_justification.md").write_text(
                    spec["report_body"], encoding="utf-8"
                )
            observed = run_validator(tmp_path)
        if observed != spec["expected_sentinel"]:
            adversarial_failures.append(
                f"{case_name}: expected {spec['expected_sentinel']} got {observed!r}"
            )
        neg_entries.append({
            "case_name": case_name,
            "root": str(case_root.relative_to(fixtures_root)),
            "expected_sentinel": spec["expected_sentinel"],
            "observed_sentinel": observed,
            "tree_files": hash_tree(case_root),
        })

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        _materialise_visibility_tree(tmp_path)
        (tmp_path / "reports" / "rp5" / "b14_1_local_bypass_justification.md").write_text(
            GOOD_REPORT_BODY, encoding="utf-8"
        )
        pos_observed = run_validator(tmp_path)
    if pos_observed != VALIDATOR_PASS:
        adversarial_failures.append(
            f"positive: expected {VALIDATOR_PASS} got {pos_observed!r}"
        )

    positive_entry = {
        "case_name": "positive",
        "root": "positive",
        "expected_sentinel": VALIDATOR_PASS,
        "observed_sentinel": pos_observed,
        "tree_files": hash_tree(pos_root),
    }

    manifest = {
        "validator": "validate_b14_1_local_bypass_justification",
        "kind": args.kind,
        "owned_markers": [SENTINEL_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_pass_sentinel": VALIDATOR_PASS,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "positive": [positive_entry],
        "negative": neg_entries,
    }
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(body)
    print(f"manifest_sha256: {sha256_bytes(body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_failures:
        for f in adversarial_failures:
            print(f"adversarial_failure: {f}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
