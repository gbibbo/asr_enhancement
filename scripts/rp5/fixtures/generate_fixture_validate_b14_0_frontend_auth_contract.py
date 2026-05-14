#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_frontend_auth_contract.

Produces positive and negative synthetic frontend source fixtures for the
B14_0-04 frontend recruiter-auth UX contract, plus a manifest carrying
sha256 / size for each fixture. Each negative fixture violates exactly
one invariant from the validator's INV-FE-AUTH-001..007 list; the
positive fixture set passes every invariant.

The fixtures are isolated synthetic source trees under
<manifest_parent>/validate_b14_0_frontend_auth_contract/<case>/ ; they
are never staged for commit and are removed before final status.

The generator re-runs the validator against each fixture tree to prove
that positive fixtures pass and negative fixtures fail with the expected
marker — without this adversarial smoke step the negative set is not
actually negative.

Emits OK_FIXTURE_VALIDATE_B14_0_FRONTEND_AUTH on PASS or
B14_0_FRONTEND_AUTH_UX_DRIFT on FAIL.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_FRONTEND_AUTH"
SENTINEL_FAIL = "B14_0_FRONTEND_AUTH_UX_DRIFT"
SENTINEL_FAIL_BROUTE = "B14_0_BROUTE_REGRESSION_UNDER_AUTH"
# Sentinels emitted by the paired validator (distinct from this
# generator's own SENTINEL_PASS / SENTINEL_FAIL).
VALIDATOR_SENTINEL_PASS = "OK_B14_0_FRONTEND_AUTH"
VALIDATOR_SENTINEL_FAIL_UX = "B14_0_FRONTEND_AUTH_UX_DRIFT"
VALIDATOR_SENTINEL_FAIL_BROUTE = "B14_0_BROUTE_REGRESSION_UNDER_AUTH"
KINDS_ALLOWED = ["positive_and_negative"]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
VALIDATOR_SCRIPT = REPO_ROOT / "scripts" / "rp5" / "validate_b14_0_frontend_auth_contract.py"


# Canonical types.ts content used by positive fixtures. Mirrors the
# BR-04 RouterFields shape currently committed at
# services/frontend/app/demo/types.ts; computed at run time from the
# real file to avoid drift between this fixture generator and the
# committed types.ts. The validator's frozen fingerprint is built from
# the same canonical extraction, so the positive fixture matches.
def load_canonical_types_text():
    real_types = REPO_ROOT / "services" / "frontend" / "app" / "demo" / "types.ts"
    return real_types.read_text(encoding="utf-8")


POSITIVE_PAGE_TSX = """\
'use client';
import { useEffect, useState } from 'react';

export default function DemoPage() {
  const [examples, setExamples] = useState<unknown[]>([]);
  useEffect(() => {
    fetch('/api/demo/examples', { cache: 'no-store' })
      .then((r) => r.json())
      .then((d) => setExamples(d.examples ?? []));
  }, []);
  return <main>{examples.length} examples</main>;
}
"""

POSITIVE_SESSION_TS = """\
const STORAGE_KEY = 'demo_session_id';
export function getOrCreateDemoSessionId(): string {
  const existing = window.localStorage.getItem(STORAGE_KEY);
  if (existing) return existing;
  const fresh = window.crypto.randomUUID();
  window.localStorage.setItem(STORAGE_KEY, fresh);
  return fresh;
}
"""


def write_tree(root: pathlib.Path, files: dict):
    root.mkdir(parents=True, exist_ok=True)
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def hash_tree(root: pathlib.Path):
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


def run_validator(types_file: pathlib.Path, demo_dir: pathlib.Path,
                  out_file: pathlib.Path):
    result = subprocess.run(
        [
            sys.executable, str(VALIDATOR_SCRIPT),
            "--types-file", str(types_file),
            "--frontend-demo-dir", str(demo_dir),
            "--out", str(out_file),
        ],
        capture_output=True, text=True,
    )
    stdout_last = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return result.returncode, stdout_last, result.stderr.strip()


def build_positive_fixtures(fixtures_root: pathlib.Path, canonical_types: str):
    cases = []

    pos_root = fixtures_root / "positive_clean"
    write_tree(pos_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": POSITIVE_PAGE_TSX,
        "demo/session.ts": POSITIVE_SESSION_TS,
    })
    cases.append({
        "case_name": "positive_clean",
        "kind": "positive",
        "root": pos_root,
        "types_file": pos_root / "demo" / "types.ts",
        "demo_dir": pos_root / "demo",
        "expected_validator_sentinel": VALIDATOR_SENTINEL_PASS,
        "expected_exit_code": 0,
        "violated_invariant": None,
    })

    return cases


def build_negative_fixtures(fixtures_root: pathlib.Path, canonical_types: str):
    cases = []

    # Negative 1: INV-FE-AUTH-001 credential-shaped localStorage write.
    n1_root = fixtures_root / "negative_inv001_localstorage_password"
    write_tree(n1_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": (
            "'use client';\n"
            "export default function P() {\n"
            "  window.localStorage.setItem('recruiterPassword', 'x');\n"
            "  return null;\n"
            "}\n"
        ),
    })
    cases.append({
        "case_name": "negative_inv001_localstorage_password",
        "kind": "negative",
        "root": n1_root,
        "types_file": n1_root / "demo" / "types.ts",
        "demo_dir": n1_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-001",
    })

    # Negative 2: INV-FE-AUTH-002 manual Authorization: Basic header.
    n2_root = fixtures_root / "negative_inv002_authorization_basic"
    write_tree(n2_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": (
            "'use client';\n"
            "export default function P() {\n"
            "  fetch('/api/demo/health', {\n"
            "    headers: { 'Authorization': 'Basic ' + btoa(`${u}:${p}`) }\n"
            "  });\n"
            "  return null;\n"
            "}\n"
        ),
    })
    cases.append({
        "case_name": "negative_inv002_authorization_basic",
        "kind": "negative",
        "root": n2_root,
        "types_file": n2_root / "demo" / "types.ts",
        "demo_dir": n2_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-002",
    })

    # Negative 3: INV-FE-AUTH-003 in-page password input.
    n3_root = fixtures_root / "negative_inv003_password_input"
    write_tree(n3_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": (
            "'use client';\n"
            "export default function P() {\n"
            "  return <input type=\"password\" name=\"password\" />;\n"
            "}\n"
        ),
    })
    cases.append({
        "case_name": "negative_inv003_password_input",
        "kind": "negative",
        "root": n3_root,
        "types_file": n3_root / "demo" / "types.ts",
        "demo_dir": n3_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-003",
    })

    # Negative 4: INV-FE-AUTH-004 client-side 401 interception with custom UI.
    n4_root = fixtures_root / "negative_inv004_custom_401_modal"
    write_tree(n4_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": (
            "'use client';\n"
            "import { useState } from 'react';\n"
            "export default function P() {\n"
            "  const [showLogin, setLogin] = useState(false);\n"
            "  fetch('/api/demo/health').then((r) => {\n"
            "    if (r.status === 401) { setLogin(true); }\n"
            "  });\n"
            "  return null;\n"
            "}\n"
        ),
    })
    cases.append({
        "case_name": "negative_inv004_custom_401_modal",
        "kind": "negative",
        "root": n4_root,
        "types_file": n4_root / "demo" / "types.ts",
        "demo_dir": n4_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-004",
    })

    # Negative 5: INV-FE-AUTH-005 credential placeholder echo.
    n5_root = fixtures_root / "negative_inv005_placeholder_echo"
    write_tree(n5_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": (
            "'use client';\n"
            "// debug token: <env:RECRUITER_PASSWORD-value>\n"
            "export default function P() { return null; }\n"
        ),
    })
    cases.append({
        "case_name": "negative_inv005_placeholder_echo",
        "kind": "negative",
        "root": n5_root,
        "types_file": n5_root / "demo" / "types.ts",
        "demo_dir": n5_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-005",
    })

    # Negative 6: INV-FE-AUTH-006 non-loopback URL literal.
    n6_root = fixtures_root / "negative_inv006_non_loopback_url"
    write_tree(n6_root, {
        "demo/types.ts": canonical_types,
        "demo/page.tsx": (
            "'use client';\n"
            "const ENDPOINT = 'https://demo.example.com/api';\n"
            "export default function P() { return ENDPOINT; }\n"
        ),
    })
    cases.append({
        "case_name": "negative_inv006_non_loopback_url",
        "kind": "negative",
        "root": n6_root,
        "types_file": n6_root / "demo" / "types.ts",
        "demo_dir": n6_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-006",
    })

    # Negative 7: INV-FE-AUTH-007 RouterFields shape drift (extra field).
    drifted_types = canonical_types.replace(
        "export type RouterDecisionView = {\n  selected_backend: string;",
        "export type RouterDecisionView = {\n  selected_backend: string;\n  rogue_router_field: string;",
    )
    n7_root = fixtures_root / "negative_inv007_router_shape_drift"
    write_tree(n7_root, {
        "demo/types.ts": drifted_types,
        "demo/page.tsx": "'use client';\nexport default function P() { return null; }\n",
    })
    cases.append({
        "case_name": "negative_inv007_router_shape_drift",
        "kind": "negative",
        "root": n7_root,
        "types_file": n7_root / "demo" / "types.ts",
        "demo_dir": n7_root / "demo",
        "expected_validator_sentinel": SENTINEL_FAIL_BROUTE,
        "expected_exit_code": 1,
        "violated_invariant": "INV-FE-AUTH-007",
    })

    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_root = manifest_path.parent / "validate_b14_0_frontend_auth_contract"
    fixtures_root.mkdir(parents=True, exist_ok=True)

    canonical_types = load_canonical_types_text()

    positives = build_positive_fixtures(fixtures_root, canonical_types)
    negatives = build_negative_fixtures(fixtures_root, canonical_types)

    manifest = {
        "validator": "validate_b14_0_frontend_auth_contract",
        "kind": args.kind,
        "owned_marker": SENTINEL_FAIL,
        "sentinel_pass": SENTINEL_PASS,
        "fixtures_root": str(fixtures_root),
        "positive": [],
        "negative": [],
    }

    adversarial_failures = []
    transcripts_dir = fixtures_root / "_transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    for case in positives + negatives:
        out_file = transcripts_dir / (case["case_name"] + ".md")
        rc, sentinel, stderr = run_validator(
            case["types_file"], case["demo_dir"], out_file,
        )
        entry = {
            "case_name": case["case_name"],
            "root": str(case["root"]),
            "violated_invariant": case["violated_invariant"],
            "expected_validator_sentinel": case["expected_validator_sentinel"],
            "expected_exit_code": case["expected_exit_code"],
            "observed_validator_sentinel": sentinel,
            "observed_exit_code": rc,
            "stderr": stderr,
            "tree_files": hash_tree(case["root"]),
        }
        if (sentinel != case["expected_validator_sentinel"]
                or rc != case["expected_exit_code"]):
            adversarial_failures.append(case["case_name"])
        if case["kind"] == "positive":
            manifest["positive"].append(entry)
        else:
            manifest["negative"].append(entry)

    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_body)

    print(f"manifest_sha256: {sha256_bytes(manifest_body)}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_failures:
        print(f"adversarial_failures: {adversarial_failures}")
        print(SENTINEL_FAIL)
        return 1

    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
