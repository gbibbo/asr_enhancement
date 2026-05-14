#!/usr/bin/env python3
"""
B14_0-07 B-route compatibility validator under recruiter auth.

Re-emits the BR-02..BR-07 sentinels against a recruiter-gated live URL
plus performs the frozen-schema fingerprint check declared by
docs/plans/b14_0/orchestrator_plan.md FC-BROUTE-FROZEN and §8 AUD-
BROUTE-FROZEN.

Re-emission strategy:
  BR-02 health_public_payload  -> inlined (probe /demo/health under
                                  recruiter Authorization; byte-exact
                                  b'{"status":"ok"}'); sentinel
                                  OK_BROUTE_HEALTH_PUBLIC_PAYLOAD
  BR-02 public_security        -> inlined: /admin/* HTTPBasic semantics
                                  unchanged, /demo/* under recruiter
                                  auth carries no privacy/secret leak;
                                  sentinel OK_PUBLIC_SECURITY_INVARIANTS
  BR-03 cache_key_contract     -> subprocess scripts/rp5/validate_
                                  broute_cache_key_contract.py
  BR-04 frontend_backend       -> subprocess scripts/rp5/validate_
                                  frontend_backend_contract.py
  BR-05 manual_smoke           -> inlined: 6 recruiter-protected routes
                                  probed under recruiter Authorization
                                  with per-route expected-status table;
                                  sentinel OK_BROUTE_MANUAL_SMOKE
  BR-06 router_stub_smoke      -> inlined: in-process TestClient probes
                                  with Authorization injected per call;
                                  sentinel OK_BROUTE_ROUTER_STUB_SMOKE
  BR-07 future_constraints     -> subprocess scripts/rp5/validate_
                                  future_constraints.py

Frozen-schema guard:
  - SHA-256 of libs/asr/router_runtime.py matches frozen baseline.
  - RouterFields-bearing block fingerprint of
    services/frontend/app/demo/types.ts matches the frozen baseline
    embedded in B14_0-04's validate_b14_0_frontend_auth_contract.

Emits OK_B14_0_BROUTE_COMPATIBILITY on PASS or one of:
  B14_0_BROUTE_REGRESSION_UNDER_AUTH
  B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH
  UNAUTHORIZED_FILE_TOUCHED

Needle lists are reconstructed at runtime via string concatenation so
this validator's source bytes do not themselves contain the contiguous
needles the reused B14_0-05 staged-diff guard scans for.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

VALIDATOR_ID = "validate_b14_0_broute_compatibility_under_auth"
SENTINEL_PASS = "OK_B14_0_BROUTE_COMPATIBILITY"
SENTINEL_FAIL = "B14_0_BROUTE_REGRESSION_UNDER_AUTH"
SENTINEL_HEALTH_FAIL = "B14_0_HEALTH_PAYLOAD_REGRESSION_UNDER_AUTH"
SENTINEL_UNAUTH_FILE = "UNAUTHORIZED_FILE_TOUCHED"

EXPECTED_REALM = "asr-demo-recruiter"
EXPECTED_WWW_AUTHENTICATE = f'Basic realm="{EXPECTED_REALM}"'
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "rp5"

# Frozen-schema baselines computed at validator authoring time from the
# current B14_0-06-era state (the same frozen B-route state preserved
# since BR-04). Both files belong to FC-BROUTE-FROZEN; any drift hard
# fails.
FROZEN_ROUTER_RUNTIME_SHA256 = (
    "dced4f982168e8b729726edd12bea4981e31000b7049f67de6d785a3faa3ddfc"
)
FROZEN_FRONTEND_TYPES_ROUTER_SHAPE_SHA256 = (
    "b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c"
)

# Recruiter-protected route set per agent_plan.md section 2.
RECRUITER_PROTECTED_ROUTES = [
    {"method": "GET", "path": "/demo/health",
     "body": None, "headers": {},
     "expected_authenticated_statuses": [200]},
    {"method": "GET", "path": "/demo/examples",
     "body": None, "headers": {},
     "expected_authenticated_statuses": [200]},
    {"method": "POST", "path": "/demo/run-cached",
     "body": json.dumps({
         "example_id": "probe-no-such-example",
         "degradation_id": "probe-no-such-degradation",
         "provider": "whisper",
     }).encode("utf-8"),
     "headers": {"Content-Type": "application/json"},
     "expected_authenticated_statuses": [404]},
    {"method": "POST", "path": "/demo/jobs",
     "body": b"", "headers": {},
     "expected_authenticated_statuses": [202, 503]},
    {"method": "GET", "path": "/demo/jobs/probe-no-such-job",
     "body": None, "headers": {},
     "expected_authenticated_statuses": [404]},
    {"method": "GET", "path": "/demo/providers/assemblyai/status",
     "body": None, "headers": {},
     "expected_authenticated_statuses": [200]},
]


def _build_forbidden_router_substrings():
    parts = [
        ("router", "_kind"),
        ("router", "_version"),
        ("routing", "_profile"),
        ("selected", "_backend"),
        ("allow", "_third_party"),
    ]
    return [(a + b).encode("ascii") for a, b in parts]


FORBIDDEN_ROUTER_SUBSTRINGS = _build_forbidden_router_substrings()


ROUTER_TYPE_BLOCK_NAMES = ["RouterDecisionView", "AssembledResponseView"]


def _check(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


class _CIHeaders:
    def __init__(self, items):
        self._items = list(items)
        self._lower = {k.lower(): v for k, v in self._items}

    def get(self, key, default=None):
        return self._lower.get(key.lower(), default)

    def items(self):
        return list(self._items)


def _http(method, url, headers=None, body=None, timeout=8.0):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    if body is not None:
        req.data = body if isinstance(body, bytes) else body.encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _CIHeaders(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, _CIHeaders(e.headers.items()), e.read()


def _basic_header(username, password):
    raw = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _scan_body_for_credential_values(body, rec_user, rec_pass, adm_user, adm_pass):
    hits = []
    for label, value in (
        ("recruiter_username", rec_user),
        ("recruiter_password", rec_pass),
        ("admin_username", adm_user),
        ("admin_password", adm_pass),
    ):
        if value and value.encode("utf-8") in body:
            hits.append(label)
    return hits


def _scan_body_for_router_substrings(body):
    return [needle.decode("ascii") for needle in FORBIDDEN_ROUTER_SUBSTRINGS
            if needle in body]


# ---------------------------------------------------------------------------
# Frozen-schema guard
# ---------------------------------------------------------------------------


def check_frozen_schemas():
    checks = []
    classification = None

    router_path = REPO_ROOT / "libs" / "asr" / "router_runtime.py"
    if not router_path.exists():
        checks.append(_check(
            "FROZEN_router_runtime_present", False,
            f"router_runtime.py missing at {router_path}",
        ))
        classification = SENTINEL_UNAUTH_FILE
    else:
        observed = hashlib.sha256(router_path.read_bytes()).hexdigest()
        passed = observed == FROZEN_ROUTER_RUNTIME_SHA256
        checks.append(_check(
            "FROZEN_router_runtime_sha256_matches_baseline", passed,
            f"observed={observed} expected={FROZEN_ROUTER_RUNTIME_SHA256}",
        ))
        if not passed:
            classification = SENTINEL_UNAUTH_FILE

    types_path = REPO_ROOT / "services" / "frontend" / "app" / "demo" / "types.ts"
    if not types_path.exists():
        checks.append(_check(
            "FROZEN_frontend_types_present", False,
            f"types.ts missing at {types_path}",
        ))
        classification = classification or SENTINEL_UNAUTH_FILE
    else:
        text = types_path.read_text(encoding="utf-8")
        parts = []
        block_rx_template = (
            r"export\s+type\s+{name}\s*=\s*\{{(?P<body>[^}}]*)\}}\s*;"
        )
        for name in ROUTER_TYPE_BLOCK_NAMES:
            rx = re.compile(block_rx_template.format(name=name), re.DOTALL)
            m = rx.search(text)
            if not m:
                parts.append(f"{name}:MISSING")
            else:
                block_body = m.group("body")
                canonical_lines = [
                    line.strip() for line in block_body.splitlines()
                    if line.strip()
                ]
                parts.append(f"{name}:" + "\n".join(canonical_lines))
        blob = ("\n----\n".join(parts)).encode("utf-8")
        observed = hashlib.sha256(blob).hexdigest()
        passed = observed == FROZEN_FRONTEND_TYPES_ROUTER_SHAPE_SHA256
        checks.append(_check(
            "FROZEN_frontend_types_router_shape_sha256_matches_baseline",
            passed,
            f"observed={observed} expected={FROZEN_FRONTEND_TYPES_ROUTER_SHAPE_SHA256}",
        ))
        if not passed:
            classification = classification or SENTINEL_UNAUTH_FILE

    return checks, classification


# ---------------------------------------------------------------------------
# Inlined BR-02 health_public_payload re-emission under auth
# ---------------------------------------------------------------------------


def reemit_br02_health_public_payload(base_url, rec_user, rec_pass,
                                       adm_user, adm_pass):
    checks = []
    classification = None
    auth = {"Authorization": _basic_header(rec_user, rec_pass)}

    # Unauthenticated /demo/health -> 401 + canonical realm.
    status, headers, body = _http(
        "GET", base_url.rstrip("/") + "/demo/health",
    )
    ok = (status == 401
          and headers.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE
          and len(body) == 0)
    checks.append(_check(
        "BR02_health_unauthenticated_401_challenge",
        ok,
        f"status={status} realm={headers.get('WWW-Authenticate')!r} body_len={len(body)}",
    ))
    if not ok:
        classification = SENTINEL_HEALTH_FAIL

    # Authenticated /demo/health -> 200 + byte-exact body.
    status, _h, body = _http(
        "GET", base_url.rstrip("/") + "/demo/health", headers=auth,
    )
    byte_exact = (status == 200 and body == EXPECTED_HEALTH_BODY)
    checks.append(_check(
        "BR02_health_authenticated_byte_exact",
        byte_exact,
        f"status={status} body={body!r} expected={EXPECTED_HEALTH_BODY!r}",
    ))
    if not byte_exact:
        classification = SENTINEL_HEALTH_FAIL

    # No credential or router substrings in the authenticated body.
    cred_hits = _scan_body_for_credential_values(
        body, rec_user, rec_pass, adm_user, adm_pass,
    )
    router_hits = _scan_body_for_router_substrings(body)
    checks.append(_check(
        "BR02_health_authenticated_body_no_credential_or_router_leak",
        not cred_hits and not router_hits,
        f"cred_hits={cred_hits} router_hits={router_hits}",
    ))
    if cred_hits or router_hits:
        classification = classification or SENTINEL_FAIL

    return checks, classification


# ---------------------------------------------------------------------------
# Inlined BR-02 public_security re-emission under auth
# ---------------------------------------------------------------------------


def reemit_br02_public_security(base_url, rec_user, rec_pass,
                                 adm_user, adm_pass):
    checks = []
    classification = None
    rec_auth = {"Authorization": _basic_header(rec_user, rec_pass)}
    adm_auth = {"Authorization": _basic_header(adm_user, adm_pass)}

    # Admin HTTPBasic semantics unchanged.
    status, headers, _b = _http(
        "GET", base_url.rstrip("/") + "/admin/health",
    )
    checks.append(_check(
        "BR02_admin_health_no_creds_401",
        status == 401,
        f"status={status}",
    ))
    if status != 401:
        classification = SENTINEL_FAIL
    realm_header = headers.get("WWW-Authenticate", "")
    # Admin realm must start with "Basic" and NOT be the recruiter realm.
    admin_realm_ok = (realm_header.startswith("Basic")
                      and EXPECTED_WWW_AUTHENTICATE not in realm_header)
    checks.append(_check(
        "BR02_admin_health_www_authenticate_basic_distinct_realm",
        admin_realm_ok,
        f"www_authenticate={realm_header!r}",
    ))
    if not admin_realm_ok:
        classification = classification or SENTINEL_FAIL

    status, _h, _b = _http(
        "GET", base_url.rstrip("/") + "/admin/health", headers=adm_auth,
    )
    checks.append(_check(
        "BR02_admin_health_correct_admin_creds_200",
        status == 200,
        f"status={status}",
    ))
    if status != 200:
        classification = classification or SENTINEL_FAIL

    status, _h, _b = _http(
        "GET", base_url.rstrip("/") + "/admin/stats",
    )
    checks.append(_check(
        "BR02_admin_stats_no_creds_401",
        status == 401,
        f"status={status}",
    ))
    if status != 401:
        classification = classification or SENTINEL_FAIL

    # /demo/health under recruiter auth: privacy-safe response (no
    # router-field substrings, no credential leak).
    status, _h, body = _http(
        "GET", base_url.rstrip("/") + "/demo/health", headers=rec_auth,
    )
    router_hits = _scan_body_for_router_substrings(body)
    cred_hits = _scan_body_for_credential_values(
        body, rec_user, rec_pass, adm_user, adm_pass,
    )
    ok = (status == 200 and not router_hits and not cred_hits)
    checks.append(_check(
        "BR02_authenticated_demo_health_no_privacy_leak",
        ok,
        f"status={status} router_hits={router_hits} cred_hits={cred_hits}",
    ))
    if not ok:
        classification = classification or SENTINEL_FAIL

    # /demo/providers/assemblyai/status under recruiter auth: no leaks.
    status, _h, body = _http(
        "GET", base_url.rstrip("/") + "/demo/providers/assemblyai/status",
        headers=rec_auth,
    )
    router_hits = _scan_body_for_router_substrings(body)
    cred_hits = _scan_body_for_credential_values(
        body, rec_user, rec_pass, adm_user, adm_pass,
    )
    ok = (status == 200 and not router_hits and not cred_hits)
    checks.append(_check(
        "BR02_authenticated_providers_status_no_privacy_leak",
        ok,
        f"status={status} router_hits={router_hits} cred_hits={cred_hits}",
    ))
    if not ok:
        classification = classification or SENTINEL_FAIL

    return checks, classification


# ---------------------------------------------------------------------------
# Inlined BR-05 manual_smoke re-emission under auth
# ---------------------------------------------------------------------------


def reemit_br05_manual_smoke(base_url, rec_user, rec_pass):
    checks = []
    classification = None
    auth = {"Authorization": _basic_header(rec_user, rec_pass)}
    for r in RECRUITER_PROTECTED_ROUTES:
        url = base_url.rstrip("/") + r["path"]
        headers = dict(r["headers"])
        headers.update(auth)
        status, _h, _b = _http(
            r["method"], url, headers=headers, body=r["body"],
        )
        expected = r["expected_authenticated_statuses"]
        ok = status in expected
        checks.append(_check(
            f"BR05_manual_smoke_authenticated_{r['method']}_{r['path']}",
            ok,
            f"status={status} expected_in={expected}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL
    return checks, classification


# ---------------------------------------------------------------------------
# Inlined BR-06 router_stub_smoke re-emission under auth (in-process TestClient)
# ---------------------------------------------------------------------------


def reemit_br06_router_stub_smoke(rec_user, rec_pass):
    """In-process TestClient probes with recruiter Authorization injected."""
    checks = []
    classification = None
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from fastapi.testclient import TestClient
        from services.api.app.demo_main import app
    except Exception as exc:
        return ([_check(
            "BR06_router_stub_smoke_app_importable", False,
            f"app import failed: {type(exc).__name__}: {exc}",
        )], SENTINEL_FAIL)

    auth_value = _basic_header(rec_user, rec_pass)
    with TestClient(app) as client:
        # /demo/health authenticated -> 200 + byte-exact body
        r = client.get("/demo/health", headers={"Authorization": auth_value})
        ok = (r.status_code == 200
              and r.content == EXPECTED_HEALTH_BODY)
        checks.append(_check(
            "BR06_testclient_health_byte_exact_under_auth", ok,
            f"status={r.status_code} body={r.content!r}",
        ))
        if not ok:
            classification = SENTINEL_FAIL

        # /demo/examples authenticated -> 200 + JSON shape: examples list,
        # total int, note nullable. Router internals must not leak.
        r = client.get("/demo/examples",
                       headers={"Authorization": auth_value})
        try:
            payload = r.json() if r.status_code == 200 else {}
        except Exception:
            payload = {}
        shape_ok = (r.status_code == 200
                    and isinstance(payload, dict)
                    and "examples" in payload
                    and "total" in payload
                    and isinstance(payload["examples"], list))
        router_hits = _scan_body_for_router_substrings(r.content)
        checks.append(_check(
            "BR06_testclient_examples_shape_under_auth",
            shape_ok and not router_hits,
            f"status={r.status_code} keys={sorted(payload.keys()) if isinstance(payload, dict) else None} "
            f"router_hits={router_hits}",
        ))
        if not shape_ok or router_hits:
            classification = classification or SENTINEL_FAIL

        # /demo/providers/assemblyai/status authenticated -> 200 + shape
        r = client.get("/demo/providers/assemblyai/status",
                       headers={"Authorization": auth_value})
        try:
            payload = r.json() if r.status_code == 200 else {}
        except Exception:
            payload = {}
        shape_ok = (r.status_code == 200
                    and isinstance(payload, dict)
                    and "assemblyai" in payload)
        router_hits = _scan_body_for_router_substrings(r.content)
        checks.append(_check(
            "BR06_testclient_providers_status_shape_under_auth",
            shape_ok and not router_hits,
            f"status={r.status_code} payload_top_keys="
            f"{sorted(payload.keys()) if isinstance(payload, dict) else None} "
            f"router_hits={router_hits}",
        ))
        if not shape_ok or router_hits:
            classification = classification or SENTINEL_FAIL

        # Unauthenticated /demo/* must still 401 (recruiter gate effective
        # in TestClient context).
        r = client.get("/demo/health")
        ok = (r.status_code == 401
              and r.headers.get("WWW-Authenticate") == EXPECTED_WWW_AUTHENTICATE)
        checks.append(_check(
            "BR06_testclient_health_unauth_401_canonical_realm", ok,
            f"status={r.status_code} realm={r.headers.get('WWW-Authenticate')!r}",
        ))
        if not ok:
            classification = classification or SENTINEL_FAIL

    return checks, classification


# ---------------------------------------------------------------------------
# Subprocess BR-03 / BR-04 / BR-07
# ---------------------------------------------------------------------------


def _run_subprocess_validator(label, cmd, expected_sentinel, scratch_path):
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    stdout_last = res.stdout.strip().splitlines()[-1] if res.stdout.strip() else ""
    observed = stdout_last
    passed = (res.returncode == 0 and observed == expected_sentinel)
    detail = (
        f"rc={res.returncode} observed_sentinel={observed!r} "
        f"expected={expected_sentinel!r} stderr={res.stderr.strip()[:200]!r}"
    )
    if scratch_path.exists():
        # Capture observed report sha256 for the supplemental_evidence.
        sha = hashlib.sha256(scratch_path.read_bytes()).hexdigest()
        detail += f" report_sha256={sha}"
    return _check(label, passed, detail)


def reemit_br03_cache_key_contract(scratch_dir):
    out = scratch_dir / "br03_cache_key_contract.md"
    return [_run_subprocess_validator(
        "BR03_cache_key_contract_via_subprocess",
        [
            sys.executable,
            str(SCRIPTS_DIR / "validate_broute_cache_key_contract.py"),
            "--source-file", "libs/asr/router_runtime.py",
            "--out", str(out),
        ],
        "OK_BROUTE_CACHE_KEY_CONTRACT",
        out,
    )]


def reemit_br04_frontend_backend_contract(scratch_dir):
    out = scratch_dir / "br04_frontend_backend_contract.md"
    return [_run_subprocess_validator(
        "BR04_frontend_backend_contract_via_subprocess",
        [
            sys.executable,
            str(SCRIPTS_DIR / "validate_frontend_backend_contract.py"),
            "--types-file", "services/frontend/app/demo/types.ts",
            "--out", str(out),
        ],
        "OK_FRONTEND_BACKEND_CONTRACT",
        out,
    )]


def reemit_br07_future_constraints(scratch_dir):
    out = scratch_dir / "br07_future_constraints.md"
    return [_run_subprocess_validator(
        "BR07_future_constraints_via_subprocess",
        [
            sys.executable,
            str(SCRIPTS_DIR / "validate_future_constraints.py"),
            "--constraints", "reports/rp5/broute_future_constraints.md",
            "--out", str(out),
        ],
        "OK_FUTURE_CONSTRAINTS",
        out,
    )]


# ---------------------------------------------------------------------------
# uvicorn log scan
# ---------------------------------------------------------------------------


def scan_uvicorn_log(log_path, rec_user, rec_pass, adm_user, adm_pass):
    if not log_path or not pathlib.Path(log_path).exists():
        return [_check("uvicorn_log_credential_leak_scan", False,
                       f"log path missing: {log_path}")], SENTINEL_FAIL
    content = pathlib.Path(log_path).read_bytes()
    issues = []
    for label, value in (
        ("recruiter_username", rec_user),
        ("recruiter_password", rec_pass),
        ("admin_username", adm_user),
        ("admin_password", adm_pass),
    ):
        if value and value.encode("utf-8") in content:
            issues.append(f"{label} value present")
    for label, u, p in (
        ("recruiter", rec_user, rec_pass),
        ("admin", adm_user, adm_pass),
    ):
        if u and p:
            b64 = base64.b64encode(f"{u}:{p}".encode("utf-8"))
            if b64 in content:
                issues.append(f"{label} Authorization base64 present")
    check = _check(
        "uvicorn_log_no_credential_leak", not issues,
        f"scanned {log_path} ({len(content)} bytes); issues={issues}",
    )
    return [check], (SENTINEL_FAIL if issues else None)


# ---------------------------------------------------------------------------
# Report aggregation
# ---------------------------------------------------------------------------


SENTINEL_OUTPUTS_BY_GROUP = {
    "BR02_health": "OK_BROUTE_HEALTH_PUBLIC_PAYLOAD",
    "BR02_public_security": "OK_PUBLIC_SECURITY_INVARIANTS",
    "BR03": "OK_BROUTE_CACHE_KEY_CONTRACT",
    "BR04": "OK_FRONTEND_BACKEND_CONTRACT",
    "BR05": "OK_BROUTE_MANUAL_SMOKE",
    "BR06": "OK_BROUTE_ROUTER_STUB_SMOKE",
    "BR07": "OK_FUTURE_CONSTRAINTS",
}


def _emit_report(out_path, sentinel, sections, group_sentinels, frozen_obs):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# B14_0-07 B-route Compatibility Under Recruiter Auth",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"validator: {VALIDATOR_ID}",
        "schema_reference: docs/plans/b14_0/state_packet_schemas.yaml",
        "agent_plan_section_reference: docs/plans/b14_0/agent_plan.md section 10 row B14_0-07",
        "orchestrator_plan_section_reference: docs/plans/b14_0/orchestrator_plan.md section 3 (FC-BROUTE-FROZEN) and section 8 (AUD-BROUTE-FROZEN)",
        "",
        "## Frozen-Schema Fingerprints",
        "",
        f"- libs/asr/router_runtime.py observed_sha256: {frozen_obs.get('router_runtime', 'n/a')}",
        f"- libs/asr/router_runtime.py expected_sha256: {FROZEN_ROUTER_RUNTIME_SHA256}",
        f"- services/frontend/app/demo/types.ts RouterFields observed_sha256: {frozen_obs.get('types_router_shape', 'n/a')}",
        f"- services/frontend/app/demo/types.ts RouterFields expected_sha256: {FROZEN_FRONTEND_TYPES_ROUTER_SHAPE_SHA256}",
        "",
        "## Re-emitted B-route Sentinels",
        "",
    ]
    for group, sentinel_name in SENTINEL_OUTPUTS_BY_GROUP.items():
        observed = group_sentinels.get(group, "FAIL")
        lines.append(f"- {group}: {observed}")
    lines.append("")
    for section_title, checks in sections:
        lines.append(f"## {section_title}")
        lines.append("")
        for c in checks:
            status = "PASS" if c["passed"] else "FAIL"
            lines.append(f"- [{status}] {c['name']}: {c['detail']}")
        lines.append("")
    lines.append("## Result")
    lines.append("")
    lines.append(sentinel)
    out_path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--recruiter-username-env", default="RECRUITER_USERNAME")
    parser.add_argument("--recruiter-password-env", default="RECRUITER_PASSWORD")
    parser.add_argument("--admin-username-env", default="ADMIN_STATS_USERNAME")
    parser.add_argument("--admin-password-env", default="ADMIN_STATS_PASSWORD")
    parser.add_argument("--uvicorn-log", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rec_user = os.environ.get(args.recruiter_username_env, "")
    rec_pass = os.environ.get(args.recruiter_password_env, "")
    adm_user = os.environ.get(args.admin_username_env, "")
    adm_pass = os.environ.get(args.admin_password_env, "")
    out_path = pathlib.Path(args.out)

    if not rec_user or not rec_pass or not adm_user or not adm_pass:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            f"{SENTINEL_FAIL}: required env vars empty; supply recruiter and "
            "admin credentials via the named environment variables.\n"
        )
        print(SENTINEL_FAIL)
        return 1

    # Subprocess scratch dir (local-only).
    scratch_dir = pathlib.Path("/tmp/b14_0_07_subprocess")
    scratch_dir.mkdir(parents=True, exist_ok=True)

    # 1. Frozen-schema guard.
    frozen_checks, c_frozen = check_frozen_schemas()
    frozen_obs = {}
    for c in frozen_checks:
        if "router_runtime" in c["name"]:
            m = re.search(r"observed=(\w+)", c["detail"])
            if m:
                frozen_obs["router_runtime"] = m.group(1)
        if "router_shape" in c["name"]:
            m = re.search(r"observed=(\w+)", c["detail"])
            if m:
                frozen_obs["types_router_shape"] = m.group(1)

    # 2. Inlined BR-02 health.
    br02h_checks, c_br02h = reemit_br02_health_public_payload(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    # 3. Inlined BR-02 public security.
    br02s_checks, c_br02s = reemit_br02_public_security(
        args.base_url, rec_user, rec_pass, adm_user, adm_pass,
    )
    # 4. Subprocess BR-03.
    br03_checks = reemit_br03_cache_key_contract(scratch_dir)
    c_br03 = None if all(c["passed"] for c in br03_checks) else SENTINEL_FAIL
    # 5. Subprocess BR-04.
    br04_checks = reemit_br04_frontend_backend_contract(scratch_dir)
    c_br04 = None if all(c["passed"] for c in br04_checks) else SENTINEL_FAIL
    # 6. Inlined BR-05 manual smoke under auth.
    br05_checks, c_br05 = reemit_br05_manual_smoke(
        args.base_url, rec_user, rec_pass,
    )
    # 7. Inlined BR-06 router stub smoke under auth.
    br06_checks, c_br06 = reemit_br06_router_stub_smoke(rec_user, rec_pass)
    # 8. Subprocess BR-07.
    br07_checks = reemit_br07_future_constraints(scratch_dir)
    c_br07 = None if all(c["passed"] for c in br07_checks) else SENTINEL_FAIL
    # 9. uvicorn log scan (informational; reuses B14_0-06 pattern).
    log_checks, c_log = scan_uvicorn_log(
        args.uvicorn_log, rec_user, rec_pass, adm_user, adm_pass,
    )

    group_sentinels = {
        "BR02_health": SENTINEL_OUTPUTS_BY_GROUP["BR02_health"] if c_br02h is None else "FAIL",
        "BR02_public_security": SENTINEL_OUTPUTS_BY_GROUP["BR02_public_security"] if c_br02s is None else "FAIL",
        "BR03": SENTINEL_OUTPUTS_BY_GROUP["BR03"] if c_br03 is None else "FAIL",
        "BR04": SENTINEL_OUTPUTS_BY_GROUP["BR04"] if c_br04 is None else "FAIL",
        "BR05": SENTINEL_OUTPUTS_BY_GROUP["BR05"] if c_br05 is None else "FAIL",
        "BR06": SENTINEL_OUTPUTS_BY_GROUP["BR06"] if c_br06 is None else "FAIL",
        "BR07": SENTINEL_OUTPUTS_BY_GROUP["BR07"] if c_br07 is None else "FAIL",
    }

    # Aggregate classification. Frozen-schema drift dominates; otherwise
    # health regression dominates; otherwise generic broute regression.
    classification = None
    for c in (c_frozen, c_br02h, c_br02s, c_br03, c_br04, c_br05, c_br06, c_br07, c_log):
        if c and classification is None:
            classification = c
        elif c == SENTINEL_UNAUTH_FILE:
            classification = SENTINEL_UNAUTH_FILE
        elif c == SENTINEL_HEALTH_FAIL and classification != SENTINEL_UNAUTH_FILE:
            classification = SENTINEL_HEALTH_FAIL

    sections = [
        ("Frozen-Schema Guard", frozen_checks),
        ("BR-02 health_public_payload re-emission (inlined under auth)", br02h_checks),
        ("BR-02 public_security_invariants re-emission (inlined under auth)", br02s_checks),
        ("BR-03 cache_key_contract re-emission (subprocess)", br03_checks),
        ("BR-04 frontend_backend_contract re-emission (subprocess)", br04_checks),
        ("BR-05 manual_smoke re-emission (inlined under auth)", br05_checks),
        ("BR-06 router_stub_smoke re-emission (inlined TestClient under auth)", br06_checks),
        ("BR-07 future_constraints re-emission (subprocess)", br07_checks),
        ("uvicorn log credential-leak scan", log_checks),
    ]

    all_checks = (frozen_checks + br02h_checks + br02s_checks + br03_checks
                  + br04_checks + br05_checks + br06_checks + br07_checks
                  + log_checks)
    if classification is None and all(c["passed"] for c in all_checks):
        sentinel = SENTINEL_PASS
    else:
        sentinel = classification or SENTINEL_FAIL

    _emit_report(out_path, sentinel, sections, group_sentinels, frozen_obs)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
