#!/usr/bin/env python3
"""
B14_1-07 B-route and B14.0 compatibility validator under public exposure.

Re-verifies that the B-route (BR-02..BR-07) and B14.0 (B14_0-02..B14_0-07)
deliverables remain compatible once PUBLIC_DEMO_EXPOSURE=true is layered on
top of the B14.0 recruiter HTTPBasic application-layer gate.

Three evidence classes (kept deliberately distinct):

  1. source-tree/static evidence -- frozen-fingerprint guard:
       * SHA-256 of libs/asr/router_runtime.py at HEAD must equal the
         SHA-256 of the same blob at the B14.0 phase-approval tracker-
         closure commit (FROZEN_ANCHOR_COMMIT).
       * Canonical RouterFields-shape fingerprint of
         services/frontend/app/demo/types.ts at HEAD must equal the
         same fingerprint of the blob at FROZEN_ANCHOR_COMMIT.
       Both anchors are derived deterministically at runtime via
       `git cat-file` from the concrete commit id below; no ambiguous
       SHA-256 literal is embedded.

  2. committed-report re-emission evidence:
       For BR-02..BR-07 and B14_0-02..B14_0-07, the committed sentinel
       report is located, its presence + SHA-256 recorded, and (where a
       validator sentinel is expected) its OK sentinel string confirmed.

  3. loopback runtime evidence:
       Against a loopback-only --base-url running PUBLIC_DEMO_EXPOSURE=
       true: unauthenticated GET /demo/health -> 401 + canonical realm;
       recruiter-authenticated GET /demo/health -> 200 + byte-exact
       b'{"status":"ok"}' (the BR-02 health invariant re-emitted under
       public exposure).

Modes:
  * live mode    -- --base-url provided: runs all three evidence classes.
  * fixture mode -- --fixtures-root provided and --base-url omitted:
                    replays the scenario classifier against the paired
                    fixture descriptors and self-checks the adversarial
                    round-trip (positive classifies PASS, negatives
                    classify FAIL).

Credential-handling contract:
  * Recruiter credentials are read from os.environ via env-var NAMES
    passed on the CLI; credential bytes are never printed nor written
    into the report.

Emits OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE on PASS or
B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE on FAIL.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

VALIDATOR_ID = "validate_b14_1_broute_compatibility_under_public_exposure"
SENTINEL_PASS = "OK_B14_1_BROUTE_COMPATIBILITY_UNDER_PUBLIC_EXPOSURE"
SENTINEL_FAIL = "B14_1_BROUTE_REGRESSION_UNDER_PUBLIC_EXPOSURE"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# Concrete, immutable anchor: the B14.0 phase-approval tracker-closure
# commit recorded in docs/progress/rp5_progress.yaml under
# phase_approvals.B14.0.accepted_tracker_closure_commit. The frozen
# fingerprints are derived from this commit's git blobs at runtime, so no
# ambiguous SHA-256 literal is hardcoded here.
FROZEN_ANCHOR_COMMIT = "7730a4f53744eeb99d118f6f5b283c2f1c35dfc8"

ROUTER_RUNTIME_PATH = "libs/asr/router_runtime.py"
FRONTEND_TYPES_PATH = "services/frontend/app/demo/types.ts"
ROUTER_TYPE_BLOCK_NAMES = ["RouterDecisionView", "AssembledResponseView"]

# Committed-report re-emission catalogue. Each entry:
#   (task_id, report_path, expected_sentinel_or_None)
# expected_sentinel is None for a deliverable that is a declarative input
# document rather than a validator report (BR-07 future_constraints).
COMMITTED_SENTINEL_CATALOG = [
    ("BR-02", "reports/rp5/broute_health_contract.md",
     "OK_BROUTE_HEALTH_PUBLIC_PAYLOAD"),
    ("BR-02", "reports/rp5/broute_public_security_invariants.md",
     "OK_PUBLIC_SECURITY_INVARIANTS"),
    ("BR-03", "reports/rp5/broute_cache_key_contract.md",
     "OK_BROUTE_CACHE_KEY_CONTRACT"),
    ("BR-04", "reports/rp5/broute_frontend_backend_contract.md",
     "OK_FRONTEND_BACKEND_CONTRACT"),
    ("BR-05", "reports/rp5/broute_manual_smoke.md",
     "OK_BROUTE_MANUAL_SMOKE"),
    ("BR-06", "reports/rp5/broute_router_stub_smoke.md",
     "OK_BROUTE_ROUTER_STUB_SMOKE"),
    ("BR-07", "reports/rp5/broute_future_constraints.md", None),
    ("B14_0-02", "reports/rp5/b14_0_recruiter_auth_contract.md",
     "OK_B14_0_RECRUITER_AUTH_CONTRACT"),
    ("B14_0-02", "reports/rp5/b14_0_health_payload_under_auth.md",
     "OK_B14_0_HEALTH_UNDER_AUTH"),
    ("B14_0-03", "reports/rp5/b14_0_auth_separation_invariants.md",
     "OK_B14_0_AUTH_SEPARATION"),
    ("B14_0-04", "reports/rp5/b14_0_frontend_auth_contract.md",
     "OK_B14_0_FRONTEND_AUTH"),
    ("B14_0-05", "reports/rp5/b14_0_manual_smoke_with_auth.md",
     "OK_B14_0_MANUAL_SMOKE_WITH_AUTH"),
    ("B14_0-06", "reports/rp5/b14_0_no_credential_leak.md",
     "OK_B14_0_NO_CRED_LEAK"),
    ("B14_0-07", "reports/rp5/b14_0_broute_compatibility_under_auth.md",
     "OK_B14_0_BROUTE_COMPATIBILITY"),
]


def _check(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


# ---------------------------------------------------------------------------
# git anchor derivation
# ---------------------------------------------------------------------------


def _git_blob(commit, path):
    res = subprocess.run(
        ["git", "cat-file", "-p", f"{commit}:{path}"],
        capture_output=True, cwd=str(REPO_ROOT),
    )
    if res.returncode != 0:
        return None
    return res.stdout


def _router_shape_fingerprint(types_ts_bytes):
    """Canonical RouterFields-shape fingerprint of types.ts.

    Uses the exact canonicalisation pinned by B14_0-04/B14_0-07: extract
    each named RouterFields-bearing block, strip per-line whitespace, join
    with a fixed separator, SHA-256 the result.
    """
    text = types_ts_bytes.decode("utf-8")
    parts = []
    block_rx_template = r"export\s+type\s+{name}\s*=\s*\{{(?P<body>[^}}]*)\}}\s*;"
    for name in ROUTER_TYPE_BLOCK_NAMES:
        rx = re.compile(block_rx_template.format(name=name), re.DOTALL)
        m = rx.search(text)
        if not m:
            parts.append(f"{name}:MISSING")
        else:
            canonical_lines = [
                line.strip() for line in m.group("body").splitlines()
                if line.strip()
            ]
            parts.append(f"{name}:" + "\n".join(canonical_lines))
    blob = ("\n----\n".join(parts)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def derive_anchors():
    """Return (router_anchor_sha, types_shape_anchor_sha, error_or_None)."""
    router_blob = _git_blob(FROZEN_ANCHOR_COMMIT, ROUTER_RUNTIME_PATH)
    if router_blob is None:
        return None, None, (
            f"git cat-file failed for {FROZEN_ANCHOR_COMMIT}:{ROUTER_RUNTIME_PATH}"
        )
    types_blob = _git_blob(FROZEN_ANCHOR_COMMIT, FRONTEND_TYPES_PATH)
    if types_blob is None:
        return None, None, (
            f"git cat-file failed for {FROZEN_ANCHOR_COMMIT}:{FRONTEND_TYPES_PATH}"
        )
    return (
        hashlib.sha256(router_blob).hexdigest(),
        _router_shape_fingerprint(types_blob),
        None,
    )


# ---------------------------------------------------------------------------
# scenario classifier (shared by live mode and fixture mode)
# ---------------------------------------------------------------------------


def classify_scenario(scenario, router_anchor, types_anchor):
    """Classify a compatibility scenario.

    scenario keys:
      router_runtime_sha256        : observed SHA-256 hex string
      types_router_shape_sha256    : observed SHA-256 hex string
      health_probe.unauth_status   : int
      health_probe.unauth_www_authenticate : str or None
      health_probe.auth_status     : int
      health_probe.auth_body       : bytes

    Returns (sentinel, checks).
    """
    checks = []
    classification = None

    router_ok = scenario["router_runtime_sha256"] == router_anchor
    checks.append(_check(
        "FROZEN_router_runtime_sha256_matches_anchor", router_ok,
        f"observed={scenario['router_runtime_sha256']} anchor={router_anchor}",
    ))
    if not router_ok:
        classification = SENTINEL_FAIL

    types_ok = scenario["types_router_shape_sha256"] == types_anchor
    checks.append(_check(
        "FROZEN_router_fields_shape_sha256_matches_anchor", types_ok,
        f"observed={scenario['types_router_shape_sha256']} anchor={types_anchor}",
    ))
    if not types_ok:
        classification = classification or SENTINEL_FAIL

    probe = scenario["health_probe"]
    unauth_ok = (probe["unauth_status"] == 401
                 and probe["unauth_www_authenticate"] == EXPECTED_WWW_AUTHENTICATE)
    checks.append(_check(
        "BR02_demo_health_unauthenticated_401_canonical_realm", unauth_ok,
        f"status={probe['unauth_status']} "
        f"realm={probe['unauth_www_authenticate']!r}",
    ))
    if not unauth_ok:
        classification = classification or SENTINEL_FAIL

    auth_ok = (probe["auth_status"] == 200
               and probe["auth_body"] == EXPECTED_HEALTH_BODY)
    checks.append(_check(
        "BR02_demo_health_authenticated_byte_exact_under_public_exposure",
        auth_ok,
        f"status={probe['auth_status']} body={probe['auth_body']!r} "
        f"expected={EXPECTED_HEALTH_BODY!r}",
    ))
    if not auth_ok:
        classification = classification or SENTINEL_FAIL

    return (classification or SENTINEL_PASS), checks


# ---------------------------------------------------------------------------
# live mode
# ---------------------------------------------------------------------------


class _CIHeaders:
    def __init__(self, items):
        self._lower = {k.lower(): v for k, v in items}

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)


def _http(method, url, headers=None, timeout=8.0):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _CIHeaders(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, _CIHeaders(e.headers.items()), e.read()


def _basic_header(username, password):
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def probe_loopback_health(base_url, username, password):
    """Return a scenario.health_probe dict from the live loopback server."""
    health_url = base_url.rstrip("/") + "/demo/health"

    unauth_status, unauth_headers, _ = _http("GET", health_url)
    auth_status, _h, auth_body = _http(
        "GET", health_url,
        headers={"Authorization": _basic_header(username, password)},
    )
    return {
        "unauth_status": unauth_status,
        "unauth_www_authenticate": unauth_headers.get("WWW-Authenticate"),
        "auth_status": auth_status,
        "auth_body": auth_body,
    }


def reemit_committed_sentinels():
    """committed-report re-emission evidence class."""
    checks = []
    classification = None
    rows = []
    for task_id, rel_path, expected_sentinel in COMMITTED_SENTINEL_CATALOG:
        path = REPO_ROOT / rel_path
        if not path.exists():
            checks.append(_check(
                f"committed_report_present_{task_id}_{rel_path}", False,
                f"missing committed report {rel_path}",
            ))
            classification = classification or SENTINEL_FAIL
            rows.append((task_id, rel_path, "MISSING", "n/a"))
            continue
        content = path.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        if expected_sentinel is None:
            checks.append(_check(
                f"committed_report_present_{task_id}_{rel_path}", True,
                f"present sha256={sha} (declarative input; no sentinel scan)",
            ))
            rows.append((task_id, rel_path, sha, "declarative_input"))
        else:
            has_sentinel = expected_sentinel.encode("ascii") in content
            checks.append(_check(
                f"committed_report_sentinel_{task_id}_{rel_path}", has_sentinel,
                f"sha256={sha} expected_sentinel={expected_sentinel} "
                f"observed={'present' if has_sentinel else 'absent'}",
            ))
            if not has_sentinel:
                classification = classification or SENTINEL_FAIL
            rows.append((task_id, rel_path, sha, expected_sentinel))
    return checks, classification, rows


def run_live_mode(base_url, username, password):
    sections = []
    overall = None

    anchors_error = None
    router_anchor, types_anchor, anchors_error = derive_anchors()
    if anchors_error is not None:
        return SENTINEL_FAIL, [(
            "Frozen-Fingerprint Anchor Derivation",
            [_check("git_anchor_derivation", False, anchors_error)],
        )], {}, []

    # source-tree/static evidence: HEAD fingerprints.
    router_path = REPO_ROOT / ROUTER_RUNTIME_PATH
    types_path = REPO_ROOT / FRONTEND_TYPES_PATH
    static_checks = []
    if not router_path.exists():
        static_checks.append(_check(
            "HEAD_router_runtime_present", False, f"missing {ROUTER_RUNTIME_PATH}"))
        overall = SENTINEL_FAIL
        head_router_sha = "missing"
    else:
        head_router_sha = hashlib.sha256(router_path.read_bytes()).hexdigest()
    if not types_path.exists():
        static_checks.append(_check(
            "HEAD_frontend_types_present", False, f"missing {FRONTEND_TYPES_PATH}"))
        overall = SENTINEL_FAIL
        head_types_sha = "missing"
    else:
        head_types_sha = _router_shape_fingerprint(types_path.read_bytes())

    scenario = {
        "router_runtime_sha256": head_router_sha,
        "types_router_shape_sha256": head_types_sha,
        "health_probe": probe_loopback_health(base_url, username, password),
    }
    static_classification, scenario_checks = classify_scenario(
        scenario, router_anchor, types_anchor,
    )
    static_checks += scenario_checks
    if static_classification != SENTINEL_PASS:
        overall = overall or static_classification
    sections.append(
        ("Frozen-Fingerprint Guard + Loopback BR-02 Health Re-emission",
         static_checks))

    # committed-report re-emission evidence.
    reemit_checks, reemit_classification, reemit_rows = reemit_committed_sentinels()
    if reemit_classification is not None:
        overall = overall or reemit_classification
    sections.append(
        ("Committed-Report Re-emission (BR-02..BR-07, B14_0-02..B14_0-07)",
         reemit_checks))

    fingerprints = {
        "router_anchor": router_anchor,
        "types_anchor": types_anchor,
        "head_router": head_router_sha,
        "head_types": head_types_sha,
        "anchor_commit": FROZEN_ANCHOR_COMMIT,
        "health_probe": scenario["health_probe"],
    }
    return (overall or SENTINEL_PASS), sections, fingerprints, reemit_rows


# ---------------------------------------------------------------------------
# fixture mode
# ---------------------------------------------------------------------------


def _scenario_from_descriptor(descriptor):
    probe = descriptor["health_probe"]
    return {
        "router_runtime_sha256": descriptor["router_runtime_sha256"],
        "types_router_shape_sha256": descriptor["types_router_shape_sha256"],
        "health_probe": {
            "unauth_status": probe["unauth_status"],
            "unauth_www_authenticate": probe["unauth_www_authenticate"],
            "auth_status": probe["auth_status"],
            "auth_body": base64.b64decode(probe["auth_body_b64"]),
        },
    }


def run_fixture_mode(fixtures_root):
    router_anchor, types_anchor, anchors_error = derive_anchors()
    if anchors_error is not None:
        return SENTINEL_FAIL, [(
            "Fixture-Mode Anchor Derivation",
            [_check("git_anchor_derivation", False, anchors_error)],
        )], []

    root = pathlib.Path(fixtures_root)
    descriptors = sorted(root.glob("*/descriptor.json"))
    checks = []
    rows = []
    overall = None
    if not descriptors:
        checks.append(_check(
            "fixture_descriptors_present", False,
            f"no */descriptor.json under {fixtures_root}",
        ))
        return SENTINEL_FAIL, [("Fixture Round-Trip", checks)], []

    for desc_path in descriptors:
        descriptor = json.loads(desc_path.read_text(encoding="utf-8"))
        scenario = _scenario_from_descriptor(descriptor)
        verdict, _scenario_checks = classify_scenario(
            scenario, router_anchor, types_anchor,
        )
        expected = descriptor["expected_sentinel"]
        consistent = verdict == expected
        checks.append(_check(
            f"fixture_roundtrip_{descriptor['fixture_id']}", consistent,
            f"kind={descriptor['kind']} classified={verdict} "
            f"expected={expected}",
        ))
        if not consistent:
            overall = SENTINEL_FAIL
        rows.append((descriptor["fixture_id"], descriptor["kind"],
                     verdict, expected, consistent))

    return (overall or SENTINEL_PASS), [("Fixture Round-Trip", checks)], rows


# ---------------------------------------------------------------------------
# report emission
# ---------------------------------------------------------------------------


def _emit_report(out_path, sentinel, mode, sections, fingerprints,
                 reemit_rows, fixture_rows):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    lines = [
        "# B14_1-07 B-route and B14.0 Compatibility Under Public Exposure",
        "",
        f"generated_at_utc: {now}",
        f"validator: {VALIDATOR_ID}",
        f"mode: {mode}",
        "schema_reference: docs/plans/b14_1/state_packet_schemas.yaml",
        "agent_plan_section_reference: docs/plans/b14_1/agent_plan.md "
        "section 10 row B14_1-07",
        "orchestrator_plan_section_reference: docs/plans/b14_1/"
        "orchestrator_plan.md section 3 (FC-BROUTE-FROZEN, "
        "FC-B14-0-GATE-PRESERVED) and section 8 (AUD-BROUTE-FROZEN)",
        "public_exposure_flag: PUBLIC_DEMO_EXPOSURE_true",
        "",
    ]
    if fingerprints:
        lines += [
            "## Frozen-Fingerprint Anchors",
            "",
            f"- anchor_commit: {fingerprints.get('anchor_commit', 'n/a')}",
            f"- {ROUTER_RUNTIME_PATH} anchor_sha256: "
            f"{fingerprints.get('router_anchor', 'n/a')}",
            f"- {ROUTER_RUNTIME_PATH} head_sha256: "
            f"{fingerprints.get('head_router', 'n/a')}",
            f"- {FRONTEND_TYPES_PATH} RouterFields-shape anchor_sha256: "
            f"{fingerprints.get('types_anchor', 'n/a')}",
            f"- {FRONTEND_TYPES_PATH} RouterFields-shape head_sha256: "
            f"{fingerprints.get('head_types', 'n/a')}",
            "",
        ]
    if reemit_rows:
        lines += [
            "## Committed-Report Re-emission Inventory",
            "",
            "| Task | Report | SHA-256 | Sentinel |",
            "|---|---|---|---|",
        ]
        for task_id, rel_path, sha, sentinel_name in reemit_rows:
            lines.append(f"| {task_id} | {rel_path} | {sha} | {sentinel_name} |")
        lines.append("")
    if fixture_rows:
        lines += [
            "## Fixture Round-Trip Inventory",
            "",
            "| Fixture | Kind | Classified | Expected | Consistent |",
            "|---|---|---|---|---|",
        ]
        for fid, kind, verdict, expected, consistent in fixture_rows:
            lines.append(
                f"| {fid} | {kind} | {verdict} | {expected} | {consistent} |")
        lines.append("")
    for title, checks in sections:
        lines.append(f"## {title}")
        lines.append("")
        for c in checks:
            status = "PASS" if c["passed"] else "FAIL"
            lines.append(f"- [{status}] {c['name']}: {c['detail']}")
        lines.append("")
    lines += ["## Result", "", sentinel]
    out_path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    parser.add_argument("--out", required=True)
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--fixtures-root")
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # fixture mode: --fixtures-root supplied, --base-url omitted.
    if args.fixtures_root and not args.base_url:
        sentinel, sections, fixture_rows = run_fixture_mode(args.fixtures_root)
        _emit_report(out_path, sentinel, "fixture", sections, {}, [],
                     fixture_rows)
        print(sentinel)
        return 0 if sentinel == SENTINEL_PASS else 1

    # live mode.
    if not args.base_url:
        out_path.write_text(
            f"{SENTINEL_FAIL}: --base-url is required for live mode "
            "(or pass --fixtures-root for fixture-only mode).\n"
        )
        print(SENTINEL_FAIL)
        return 1
    if not args.base_url.startswith(("http://127.0.0.1", "http://localhost")):
        out_path.write_text(
            f"{SENTINEL_FAIL}: --base-url must be a loopback URL; "
            f"got {args.base_url}\n"
        )
        print(SENTINEL_FAIL)
        return 1

    import os
    username = os.environ.get(args.recruiter_username_env, "")
    password = os.environ.get(args.recruiter_password_env, "")
    if not username or not password:
        out_path.write_text(
            f"{SENTINEL_FAIL}: env vars {args.recruiter_username_env} and "
            f"{args.recruiter_password_env} must be non-empty.\n"
        )
        print(SENTINEL_FAIL)
        return 1

    sentinel, sections, fingerprints, reemit_rows = run_live_mode(
        args.base_url, username, password,
    )
    _emit_report(out_path, sentinel, "live", sections, fingerprints,
                 reemit_rows, [])
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
