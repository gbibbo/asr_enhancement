#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_application_layer_gate_invariants.py.

Materializes:

  * one positive observations.json (every committed /demo/* route
    returns a canonical 401 challenge to an unauthenticated request
    and a non-401 status to a credentialed request);
  * two negative observations.json fixtures (unprotected /demo/upload
    and unprotected /demo/jobs/{job_id}/result), each carrying one
    route whose unauthenticated probe returned a non-401 status,
    simulating a missing recruiter dependency on that route.

The generator drives the paired validator in --selftest mode against
the assembled fixture tree (positive + negatives) and additionally
re-exercises each negative case in isolation (treated as a single
positive case) to confirm that the validator emits
B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED on each adversarial
defect.

No public-network call. No literal public URL, hostname, auth-key,
token, password, or non-loopback IP address is written.

Emits OK_FIXTURE_VALIDATE_B14_2_APPLICATION_LAYER_GATE on success or
B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED if any adversarial
expectation is violated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_APPLICATION_LAYER_GATE"
SENTINEL_FAIL = "B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED"
VALIDATOR_OK = "OK_B14_2_APPLICATION_LAYER_GATE"
VALIDATOR_FAIL = "B14_2_APPLICATION_LAYER_GATE_BYPASS_DETECTED"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (
    REPO_ROOT / "scripts" / "rp5" /
    "validate_b14_2_application_layer_gate_invariants.py"
)
RECRUITER_REALM = "asr-demo-recruiter"
CANONICAL_WWW_AUTHENTICATE = f'Basic realm="{RECRUITER_REALM}"'

# Mirror of DEMO_ROUTES in the paired validator. Kept in step with that
# list (selftest mode rejects fixtures that omit any committed route).
DEMO_ROUTES: list[tuple[str, str]] = [
    ("GET", "/demo/health"),
    ("GET", "/demo/examples"),
    ("GET", "/demo/examples/b14_2_fixture/audio/clean"),
    ("GET", "/demo/examples/b14_2_fixture/audio/degraded/b14_2_fixture_degradation"),
    ("POST", "/demo/jobs"),
    ("POST", "/demo/run-cached"),
    ("POST", "/demo/upload"),
    ("GET", "/demo/providers/assemblyai/status"),
    ("GET", "/demo/jobs/b14_2_fixture_job"),
    ("GET", "/demo/jobs/b14_2_fixture_job/result"),
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


def _canonical_unauth_401() -> dict:
    return {
        "status": 401,
        "www_authenticate": CANONICAL_WWW_AUTHENTICATE,
        "body_len": 0,
        "error": None,
    }


def _credentialed_non_401(status: int = 200) -> dict:
    return {
        "status": status,
        "www_authenticate": "",
        "body_len": 0,
        "error": None,
    }


def positive_observations() -> dict:
    observations = []
    for method, path in DEMO_ROUTES:
        observations.append({
            "method": method,
            "path": path,
            "unauth": _canonical_unauth_401(),
            "creds": _credentialed_non_401(status=200 if method == "GET" else 202),
        })
    return {
        "case_name": "positive",
        "credentialed_probe_attempted": True,
        "observations": observations,
    }


def _negative_unprotected(target_method: str, target_path: str,
                          leaked_status: int, case_name: str) -> dict:
    record = positive_observations()
    record["case_name"] = case_name
    for obs in record["observations"]:
        if obs["method"] == target_method and obs["path"] == target_path:
            # Simulate the recruiter dependency being absent on this
            # route: unauthenticated request reaches the route handler
            # and returns a non-401 (e.g. 202 queued / 200 ok). The
            # validator must flag this as a bypass.
            obs["unauth"] = {
                "status": leaked_status,
                "www_authenticate": "",
                "body_len": 0,
                "error": None,
            }
            break
    return record


def negative_observations() -> dict[str, dict]:
    return {
        "negative_unprotected_demo_upload": _negative_unprotected(
            "POST", "/demo/upload", leaked_status=202,
            case_name="negative_unprotected_demo_upload",
        ),
        "negative_unprotected_demo_jobs_result": _negative_unprotected(
            "GET", "/demo/jobs/b14_2_fixture_job/result", leaked_status=200,
            case_name="negative_unprotected_demo_jobs_result",
        ),
    }


def _write_case(case_root: pathlib.Path, record: dict) -> None:
    case_root.mkdir(parents=True, exist_ok=True)
    body = json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    (case_root / "observations.json").write_bytes(body)


def _wipe(p: pathlib.Path) -> None:
    if not p.exists():
        return
    for child in sorted(p.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    p.rmdir()


def run_validator_selftest(fixtures_root: pathlib.Path) -> str:
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATOR_PATH),
            "--selftest",
            "--fixtures", str(fixtures_root),
        ],
        capture_output=True, text=True,
    )
    out = proc.stdout.strip().splitlines()
    return out[-1] if out else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = (
        manifest_path.parent /
        "generate_fixture_validate_b14_2_application_layer_gate_invariants"
    )
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    # Aggregate fixture tree: one positive subdir and two negative subdirs.
    _write_case(fixtures_root / "positive" / "positive", positive_observations())
    neg_records = negative_observations()
    for case_name, record in sorted(neg_records.items()):
        _write_case(fixtures_root / "negative" / case_name, record)

    aggregate_sentinel = run_validator_selftest(fixtures_root)

    # Adversarial per-case checks: re-write each negative observation
    # under a temporary positive-only tree and confirm the validator
    # emits the failure sentinel because the "positive" case actually
    # violates an invariant.
    adversarial_failures: list[str] = []
    per_case_observations: list[dict] = []
    for case_name, record in sorted(neg_records.items()):
        per_case_root = fixtures_root / "_per_case" / case_name
        _write_case(per_case_root / "positive" / case_name, record)
        # Also include one passing negative so neg_ok is satisfied for the
        # validator's two-sided gate; we use a fresh canonical positive
        # observation cast as a "negative" expected to fail, mirrored by
        # injecting a single bypass observation.
        decoy = positive_observations()
        decoy["case_name"] = f"decoy_negative_for_{case_name}"
        # Inject a deterministic bypass so the decoy negative case
        # legitimately fails its invariants (otherwise neg_ok would be
        # False from len==0 and we could not isolate the cause to the
        # per-case positive defect).
        decoy["observations"][0]["unauth"] = {
            "status": 200,
            "www_authenticate": "",
            "body_len": 0,
            "error": None,
        }
        _write_case(per_case_root / "negative" / f"decoy_for_{case_name}", decoy)
        observed = run_validator_selftest(per_case_root)
        per_case_observations.append({
            "case_name": case_name,
            "observed_sentinel": observed,
        })
        if observed != VALIDATOR_FAIL:
            adversarial_failures.append(
                f"{case_name}: per-case adversarial expected {VALIDATOR_FAIL}, "
                f"got {observed!r}"
            )

    # Aggregate must also be VALIDATOR_OK (positives pass invariants;
    # negatives fail invariants).
    if aggregate_sentinel != VALIDATOR_OK:
        adversarial_failures.append(
            f"aggregate: expected {VALIDATOR_OK} got {aggregate_sentinel!r}"
        )

    # Remove the helper subtree so the manifest stays deterministic and
    # the on-disk fixture tree is compact.
    _wipe(fixtures_root / "_per_case")

    manifest = {
        "validator": "validate_b14_2_application_layer_gate_invariants",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "aggregate_selftest_sentinel": aggregate_sentinel,
        "positive": [{
            "case_name": "positive",
            "root": "positive/positive",
            "expected_sentinel_under_aggregate_selftest": VALIDATOR_OK,
        }],
        "negative": [
            {
                "case_name": name,
                "root": f"negative/{name}",
                "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
                "observed_sentinel": next(
                    (o["observed_sentinel"] for o in per_case_observations
                     if o["case_name"] == name), None
                ),
            }
            for name in sorted(neg_records)
        ],
        "tree_files": hash_tree(fixtures_root),
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
