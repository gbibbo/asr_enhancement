#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_2_public_surface_diagnostic.

Materializes one positive sample and five negative samples of the B14.2
public-surface recruiter-gate diagnostic markdown record. Runs the
validator in-process against each sample and confirms that the positive
sample emits OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC and that each negative
sample emits EXECUTION_RAIL_GAP.

Negative cases:
  * negative_converts_unauthenticated_to_authenticated
  * negative_converts_upload_with_gt_fail_to_pass
  * negative_missing_b15_artifact_citation
  * negative_zone_c_hypothesis_confirmed
  * negative_missing_pinned_tracker_commit

The generator performs no public network call.

Emits OK_FIXTURE_VALIDATE_B14_2_PUBLIC_SURFACE_DIAGNOSTIC on success or
EXECUTION_RAIL_GAP if any adversarial expectation is violated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_PUBLIC_SURFACE_DIAGNOSTIC"
SENTINEL_FAIL = "EXECUTION_RAIL_GAP"
VALIDATOR_OK = "OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC"
VALIDATOR_FAIL = "EXECUTION_RAIL_GAP"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    REPO_ROOT / "scripts" / "rp5" / "validate_b14_2_public_surface_diagnostic.py"
)

VANTAGE_POINTS = [
    "windows_local",
    "mobile_cellular",
    "other_wifi",
    "vpn_or_external_tester",
]


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


def _vantage_block(vp: str,
                   recruiter_status: str = "unauthenticated_access_observed",
                   upload_gt: str = "FAIL") -> str:
    return (
        f"### Vantage point: {vp}\n\n"
        f"- recruiter_gate_observed_status: {recruiter_status}\n"
        f"- coverage_item_outcomes.upload_with_manual_ground_truth: {upload_gt}\n"
        f"- evidence_reference: fixture_operator_smoke_{vp}_no_literals\n"
        "- har_reference: HAR-B15-MULTI-NETWORK-SMOKE-001\n\n"
    )


def positive_body(include_b15_phase_gate_ref: bool = True,
                  include_pinned_commit: bool = True,
                  vantage_overrides: dict[str, dict] = None,
                  zone_c_unconfirmed: bool = True) -> str:
    if vantage_overrides is None:
        vantage_overrides = {}

    refs = [
        "reports/rp5/b15_multi_network_smoke_results.md",
        "reports/rp5/b15_smoke_adjudication.md",
        "reports/rp5/b15_phase_gate.md" if include_b15_phase_gate_ref else None,
        "docs/progress/rp5_progress.yaml",
    ]
    refs = [r for r in refs if r]

    parts = [
        "# B14.2 Public-Surface Recruiter-Gate Diagnostic (Fixture)\n",
        "Task: B14_2-01 fixture\n",
        "Phase: B14.2 (repair microphase)\n",
        "Branch: feature/demo-runtime-rp5-v1\n",
        "Record type: declarative diagnostic; read-only; no public-network commands\n",
        "\n## Reference Sources (cited by reference only)\n\n",
    ]
    for r in refs:
        parts.append(f"- {r}\n")
    parts.append("\n## Freeze-Audit Pair\n\n")
    if include_pinned_commit:
        parts.append("- plan_pinned_tracker_commit: bf8560a6c3493692ccd8a35926a5ddc647b627f6\n")
    parts.append("- tracker_self_reference_spelling: this_tracker_commit_self_reference_per_b14_1_convention\n")

    parts.append("\n## B15 Operator Evidence Preserved Verbatim by Reference\n\n")
    for vp in VANTAGE_POINTS:
        ov = vantage_overrides.get(vp, {})
        parts.append(_vantage_block(
            vp,
            recruiter_status=ov.get("recruiter", "unauthenticated_access_observed"),
            upload_gt=ov.get("upload_gt", "FAIL"),
        ))

    parts += [
        "### Anti-falsification statements\n\n",
        "- No record converts unauthenticated_access_observed to authenticated_access_only.\n",
        "- No record converts upload_with_manual_ground_truth FAIL to PASS without matching B14_2-04 evidence.\n",
        "\n## Diagnostic Zones\n\n",
        "### Zone A: B14.0 recruiter HTTPBasic middleware at loopback (frozen PASS)\n\n",
        "- Hypothesis A1 (baseline; unconfirmed at the public surface): the middleware code is correct at loopback.\n",
        "\n### Zone B: B14.1 public-exposure flag plumbing at loopback (frozen approved through explicit-blocker branch)\n\n",
        "- Hypothesis B1 (baseline; unconfirmed at the public surface): the application-side plumbing is correct at loopback.\n",
        "\n### Zone C: Funnel-terminated public surface (operator-owned)\n\n",
    ]
    c_marker = "unconfirmed" if zone_c_unconfirmed else "confirmed"
    parts += [
        f"- Hypothesis C1 (header-strip; {c_marker}): the Funnel terminator may strip the Authorization header.\n",
        f"- Hypothesis C2 (port-forward; {c_marker}): the Funnel terminator may forward to a FastAPI port with PUBLIC_DEMO_EXPOSURE false.\n",
        f"- Hypothesis C3 (route-mapping; {c_marker}): the Funnel serve configuration may map a route bypassing the recruiter middleware.\n",
        f"- Hypothesis C4 (interface-binding; {c_marker}): FastAPI may be bound to a non-loopback interface allowing direct bypass.\n",
        f"- Hypothesis C5 (flag-drift; {c_marker}): the FastAPI process behind the Funnel may have been started with PUBLIC_DEMO_EXPOSURE unset.\n",
        "\n## Explicit Boundaries\n\n",
        "- Upload-with-manual-ground-truth classification is deferred to B14_2-05.\n",
        "- B14_2-01 does not resolve the carried marker B15_RECRUITER_GATE_REGRESSION_UNDER_PUBLIC_SMOKE.\n",
    ]
    return "".join(parts)


def positive_body_default() -> str:
    return positive_body()


def negative_bodies() -> dict[str, str]:
    # 1) Convert unauthenticated_access_observed to authenticated_access_only
    #    on one vantage point (without a negative-assertion qualifier).
    convert_unauth = positive_body(vantage_overrides={
        "windows_local": {"recruiter": "authenticated_access_only", "upload_gt": "FAIL"},
    })

    # 2) Convert upload_with_manual_ground_truth FAIL to PASS on one vantage
    #    point (without a negative-assertion qualifier).
    convert_pass = positive_body(vantage_overrides={
        "mobile_cellular": {"recruiter": "unauthenticated_access_observed", "upload_gt": "PASS"},
    })

    # 3) Drop the b15_phase_gate.md citation (missing required reference).
    missing_ref = positive_body(include_b15_phase_gate_ref=False)

    # 4) Mark a Zone C hypothesis as confirmed cause.
    zone_c_confirmed = positive_body(zone_c_unconfirmed=False)

    # 5) Drop the plan-pinned tracker commit (missing freeze-audit pin).
    missing_commit = positive_body(include_pinned_commit=False)

    return {
        "negative_converts_unauthenticated_to_authenticated": convert_unauth,
        "negative_converts_upload_with_gt_fail_to_pass": convert_pass,
        "negative_missing_b15_artifact_citation": missing_ref,
        "negative_zone_c_hypothesis_confirmed": zone_c_confirmed,
        "negative_missing_pinned_tracker_commit": missing_commit,
    }


def run_validator(record_path: pathlib.Path) -> str:
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as tmp:
        transcript = pathlib.Path(tmp.name)
    try:
        proc = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                "--record", str(record_path),
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
        / "generate_fixture_validate_b14_2_public_surface_diagnostic"
    )
    fixtures_root.mkdir(parents=True, exist_ok=True)

    adversarial_failures: list[str] = []

    pos_root = fixtures_root / "positive"
    pos_root.mkdir(parents=True, exist_ok=True)
    pos_file = pos_root / "diagnostic.md"
    pos_file.write_text(positive_body_default(), encoding="utf-8")
    pos_sentinel = run_validator(pos_file)
    if pos_sentinel != VALIDATOR_OK:
        adversarial_failures.append(
            f"positive: expected {VALIDATOR_OK} got {pos_sentinel!r}"
        )
    positive_entry = {
        "case_name": "positive",
        "root": "positive",
        "expected_sentinel": VALIDATOR_OK,
        "observed_sentinel": pos_sentinel,
        "tree_files": hash_tree(pos_root),
    }

    neg_root = fixtures_root / "negative"
    neg_root.mkdir(parents=True, exist_ok=True)
    neg_entries: list[dict] = []
    for case_name, body in sorted(negative_bodies().items()):
        case_root = neg_root / case_name
        case_root.mkdir(parents=True, exist_ok=True)
        case_file = case_root / "diagnostic.md"
        case_file.write_text(body, encoding="utf-8")
        sentinel = run_validator(case_file)
        if sentinel != VALIDATOR_FAIL:
            adversarial_failures.append(
                f"{case_name}: expected {VALIDATOR_FAIL} got {sentinel!r}"
            )
        neg_entries.append({
            "case_name": case_name,
            "root": str(case_root.relative_to(fixtures_root)),
            "expected_marker": VALIDATOR_FAIL,
            "observed_sentinel": sentinel,
            "tree_files": hash_tree(case_root),
        })

    manifest = {
        "validator": "validate_b14_2_public_surface_diagnostic",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
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
