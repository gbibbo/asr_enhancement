#!/usr/bin/env python3
"""
Fixture generator paired with
scripts/rp5/validate_b14_2_broute_compatibility_under_public_exposure.py.

Materializes:
  * positive observations.json (head_router_runtime_sha256 and
    head_types_router_shape_sha256 match the FROZEN_ANCHOR_COMMIT
    fingerprints derived at runtime; loopback BR-02 health probe shows
    canonical 401/200 behaviour);
  * one negative observations.json with a mutated head_router_runtime_sha256
    (frozen fingerprint drift).

The generator derives the frozen-fingerprint anchors at runtime via
`git cat-file` against FROZEN_ANCHOR_COMMIT (same anchor as the
validator) so positive observations are self-consistent with the current
repository state.

Emits OK_FIXTURE_VALIDATE_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE
on success or B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE on failure.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys


SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE"
VALIDATOR_OK = "OK_B14_2_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE"
VALIDATOR_FAIL = "B14_2_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_PATH = (REPO_ROOT / "scripts" / "rp5" /
                  "validate_b14_2_broute_compatibility_under_public_exposure.py")
FROZEN_ANCHOR_COMMIT = "7730a4f53744eeb99d118f6f5b283c2f1c35dfc8"
ROUTER_RUNTIME_PATH = "libs/asr/router_runtime.py"
FRONTEND_TYPES_PATH = "services/frontend/app/demo/types.ts"
ROUTER_TYPE_BLOCK_NAMES = ["RouterDecisionView", "AssembledResponseView"]
RECRUITER_REALM = "asr-demo-recruiter"
CANONICAL_WWW = f'Basic realm="{RECRUITER_REALM}"'
CANONICAL_HEALTH_BODY = b'{"status":"ok"}'


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hash_tree(root: pathlib.Path) -> list[dict]:
    return [{"path": str(p.relative_to(root)),
             "sha256": sha256_bytes(p.read_bytes()),
             "size_bytes": p.stat().st_size}
            for p in sorted(root.rglob("*")) if p.is_file()]


def _git_blob(commit: str, path: str) -> bytes | None:
    res = subprocess.run(
        ["git", "cat-file", "-p", f"{commit}:{path}"],
        capture_output=True, cwd=str(REPO_ROOT),
    )
    if res.returncode != 0:
        return None
    return res.stdout


def _router_shape_fingerprint(types_ts_bytes: bytes) -> str:
    text = types_ts_bytes.decode("utf-8")
    parts = []
    rx_tmpl = r"export\s+type\s+{name}\s*=\s*\{{(?P<body>[^}}]*)\}}\s*;"
    for name in ROUTER_TYPE_BLOCK_NAMES:
        rx = re.compile(rx_tmpl.format(name=name), re.DOTALL)
        m = rx.search(text)
        if not m:
            parts.append(f"{name}:MISSING")
        else:
            canonical = [ln.strip() for ln in m.group("body").splitlines() if ln.strip()]
            parts.append(f"{name}:" + "\n".join(canonical))
    blob = ("\n----\n".join(parts)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def derive_anchors() -> tuple[str, str]:
    router_blob = _git_blob(FROZEN_ANCHOR_COMMIT, ROUTER_RUNTIME_PATH)
    types_blob = _git_blob(FROZEN_ANCHOR_COMMIT, FRONTEND_TYPES_PATH)
    if router_blob is None or types_blob is None:
        raise SystemExit(
            f"{SENTINEL_FAIL}: git cat-file failed at {FROZEN_ANCHOR_COMMIT}"
        )
    return hashlib.sha256(router_blob).hexdigest(), _router_shape_fingerprint(types_blob)


def positive_record(router_anchor: str, types_anchor: str) -> dict:
    return {
        "case_name": "positive",
        "head_router_runtime_sha256": router_anchor,
        "head_types_router_shape_sha256": types_anchor,
        "health_probe": {
            "unauth_status": 401,
            "unauth_www_authenticate": CANONICAL_WWW,
            "auth_status": 200,
            "auth_body_b64": base64.b64encode(CANONICAL_HEALTH_BODY).decode("ascii"),
        },
    }


def negative_record(router_anchor: str, types_anchor: str) -> dict:
    rec = positive_record(router_anchor, types_anchor)
    rec["case_name"] = "negative_router_runtime_sha256_drift"
    rec["head_router_runtime_sha256"] = "0" * 64  # fingerprint drift
    return rec


def _write(case_root: pathlib.Path, record: dict) -> None:
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / "observations.json").write_bytes(
        json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    )


def _wipe(p: pathlib.Path) -> None:
    if not p.exists():
        return
    for child in sorted(p.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    p.rmdir()


def run_selftest(fixtures_root: pathlib.Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--selftest",
         "--fixtures", str(fixtures_root)],
        capture_output=True, text=True,
    )
    out = proc.stdout.strip().splitlines()
    return out[-1] if out else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=["positive_and_negative"])
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    router_anchor, types_anchor = derive_anchors()

    manifest_path = pathlib.Path(args.manifest).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = (manifest_path.parent /
                     "generate_fixture_validate_b14_2_broute_compatibility_under_public_exposure")
    _wipe(fixtures_root)
    fixtures_root.mkdir(parents=True, exist_ok=True)

    _write(fixtures_root / "positive" / "positive",
           positive_record(router_anchor, types_anchor))
    neg = negative_record(router_anchor, types_anchor)
    _write(fixtures_root / "negative" / neg["case_name"], neg)

    aggregate = run_selftest(fixtures_root)

    per_case_root = fixtures_root / "_per_case" / neg["case_name"]
    _write(per_case_root / "positive" / neg["case_name"], neg)
    decoy = positive_record(router_anchor, types_anchor)
    decoy["case_name"] = "decoy_negative"
    decoy["head_types_router_shape_sha256"] = "0" * 64
    _write(per_case_root / "negative" / "decoy_negative", decoy)
    per_case_sentinel = run_selftest(per_case_root)
    _wipe(fixtures_root / "_per_case")

    failures = []
    if aggregate != VALIDATOR_OK:
        failures.append(f"aggregate: expected {VALIDATOR_OK} got {aggregate!r}")
    if per_case_sentinel != VALIDATOR_FAIL:
        failures.append(
            f"per_case_{neg['case_name']}: expected {VALIDATOR_FAIL} got {per_case_sentinel!r}"
        )

    manifest = {
        "validator": "validate_b14_2_broute_compatibility_under_public_exposure",
        "kind": args.kind,
        "owned_markers": [VALIDATOR_FAIL],
        "sentinel_pass": SENTINEL_PASS,
        "validator_sentinel_pass": VALIDATOR_OK,
        "fixtures_root": str(fixtures_root.relative_to(REPO_ROOT)),
        "frozen_anchor_commit": FROZEN_ANCHOR_COMMIT,
        "router_runtime_anchor_sha256": router_anchor,
        "router_fields_shape_anchor_sha256": types_anchor,
        "aggregate_selftest_sentinel": aggregate,
        "positive": [{"case_name": "positive", "root": "positive/positive",
                      "expected_sentinel_under_aggregate_selftest": VALIDATOR_OK}],
        "negative": [{"case_name": neg["case_name"],
                      "root": f"negative/{neg['case_name']}",
                      "expected_sentinel_when_treated_as_positive_only_input": VALIDATOR_FAIL,
                      "observed_sentinel": per_case_sentinel}],
        "tree_files": hash_tree(fixtures_root),
    }
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(body)
    print(f"manifest_sha256: {sha256_bytes(body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if failures:
        for f in failures:
            print(f"adversarial_failure: {f}")
        print(SENTINEL_FAIL)
        return 1
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
