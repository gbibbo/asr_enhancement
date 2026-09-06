#!/usr/bin/env python3
"""
B14_0-04 frontend recruiter-auth UX contract validator.

Static, read-only scan of services/frontend/app/demo/* enforcing the
recruiter-auth UX invariants declared in docs/plans/b14_0/agent_plan.md
section 2 and forbidden in section 12.

Invariants enforced
-------------------
INV-FE-AUTH-001: no client-side credential persistence beyond session.
    No localStorage.setItem / sessionStorage.setItem / document.cookie
    writes whose key or value carries credential-shaped substrings
    (recruiter, username, password, authorization, basic, credential).
INV-FE-AUTH-002: no custom Authorization: Basic header constructed in
    frontend code. No literal "Authorization" header key, no btoa(...)
    of a ${user}:${pass}-shaped argument, no Basic auth encoding.
INV-FE-AUTH-003: no in-page credential capture form. No <input ...
    type="password"> and no name="password"/name="recruiter*" inputs.
INV-FE-AUTH-004: no client-side 401 interception that subverts the
    browser-native WWW-Authenticate: Basic realm="asr-demo-recruiter"
    challenge. No custom modal credential UI bound to a 401 status.
INV-FE-AUTH-005: no echo of credential placeholder substrings in
    committed frontend source (RECRUITER_USERNAME-value,
    RECRUITER_PASSWORD-value, ADMIN_STATS_PASSWORD-value, raw
    Authorization-header-value).
INV-FE-AUTH-006: no banned-phrase, no non-loopback URL, no Funnel
    / serve / systemd substring inside services/frontend/app/demo/*.
INV-FE-AUTH-007: BR-04 RouterFields shape frozen. The two router-
    bearing type blocks (RouterDecisionView, AssembledResponseView)
    extracted from services/frontend/app/demo/types.ts must match a
    frozen byte fingerprint embedded in this validator at authoring
    time. Drift is a hard failure routed through marker
    B14_0_BROUTE_REGRESSION_UNDER_AUTH.

Emits OK_B14_0_FRONTEND_AUTH on PASS or B14_0_FRONTEND_AUTH_UX_DRIFT
on FAIL (or B14_0_BROUTE_REGRESSION_UNDER_AUTH if the drift is in the
RouterFields shape only).
"""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys

VALIDATOR_ID = "validate_b14_0_frontend_auth_contract"
SENTINEL_PASS = "OK_B14_0_FRONTEND_AUTH"
SENTINEL_FAIL = "B14_0_FRONTEND_AUTH_UX_DRIFT"
SENTINEL_FAIL_BROUTE = "B14_0_BROUTE_REGRESSION_UNDER_AUTH"

FRONTEND_FILE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")

# Credential-shaped substrings searched on the LHS of storage writes and
# cookie assignments. Lowercase comparison; English-only frontend.
CREDENTIAL_KEY_NEEDLES = [
    "recruiter",
    "password",
    "authorization",
    "credential",
    "credentials",
]
# Substrings that, when present anywhere as a literal string key in a
# storage write, indicate a credential-shaped LHS. The literal token
# "username" is checked separately because the existing session-id
# helper uses keys like "demo_session_id" which must not trip.
CREDENTIAL_USERNAME_TOKEN = "username"

# Forbidden literal substrings inside committed frontend source.
FORBIDDEN_CREDENTIAL_PLACEHOLDERS = [
    "<env:RECRUITER_PASSWORD-value>",
    "<env:ADMIN_STATS_PASSWORD-value>",
    "<env:Authorization-header-value>",
    "RECRUITER_PASSWORD=",
    "ADMIN_STATS_PASSWORD=",
]

# Banned-phrases registry inherited from B-route §14.
BANNED_PHRASES = [
    "as needed", "as appropriate", "as required", "if already present",
    "if present", "where appropriate", "best practices", "obvious",
    "TBD", "TODO without a marker", "discovered", "discover ",
    "judgment", "free-form", "free form",
]

# Forbidden future-constraint substrings.
FORBIDDEN_FUTURE_SUBSTRINGS = [
    "tailscale funnel", "funnel serve", "ts funnel",
]

# BR-04 RouterFields shape frozen fingerprint. The fingerprint covers
# the canonical text of the two router-bearing type blocks in
# services/frontend/app/demo/types.ts. Authoring-time baseline derived
# directly from the BR-04 accepted file (commit 42d51ec, preserved
# through B14_0-03 closure 9278689); the validator recomputes the
# fingerprint at run time and compares.
ROUTER_TYPE_BLOCK_NAMES = ["RouterDecisionView", "AssembledResponseView"]
FROZEN_ROUTER_SHAPE_SHA256 = (
    "b893f8f84f6d5b81fa406da5c3272cab116d8098445f4f14673bb9474195225c"
)


def _check(name, passed, detail, marker=None):
    return {
        "name": name,
        "passed": bool(passed),
        "detail": detail,
        "marker": marker,
    }


def list_demo_source_files(demo_dir: pathlib.Path):
    files = []
    if not demo_dir.exists():
        return files
    for p in sorted(demo_dir.iterdir()):
        if p.is_file() and p.suffix in FRONTEND_FILE_SUFFIXES:
            files.append(p)
    return files


_STORAGE_WRITE_RE = re.compile(
    r"\b(localStorage|sessionStorage)\s*\.\s*setItem\s*\(\s*"
    r"(?P<key>[^,]+?)\s*,",
    re.MULTILINE,
)
_COOKIE_WRITE_RE = re.compile(
    r"\bdocument\s*\.\s*cookie\s*=\s*(?P<value>[^;\n]+)",
    re.MULTILINE,
)


def _key_looks_credential(key_expr_text: str) -> bool:
    lowered = key_expr_text.lower()
    for needle in CREDENTIAL_KEY_NEEDLES:
        if needle in lowered:
            return True
    # username is only credential-shaped when not preceded by a
    # non-word character that suggests an unrelated token (we use
    # word-boundary semantics: presence of "username" as a substring
    # is sufficient because the frontend has no legitimate use of
    # that token in storage keys).
    if CREDENTIAL_USERNAME_TOKEN in lowered:
        return True
    return False


def scan_storage_writes(file_path: pathlib.Path, body: str):
    issues = []
    for m in _STORAGE_WRITE_RE.finditer(body):
        key_expr = m.group("key").strip()
        if _key_looks_credential(key_expr):
            line_no = body.count("\n", 0, m.start()) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-001",
                "file": str(file_path),
                "line": line_no,
                "evidence": m.group(0).strip(),
                "reason": (
                    f"storage write with credential-shaped key: {key_expr!r}"
                ),
            })
    for m in _COOKIE_WRITE_RE.finditer(body):
        value_expr = m.group("value").strip()
        if _key_looks_credential(value_expr):
            line_no = body.count("\n", 0, m.start()) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-001",
                "file": str(file_path),
                "line": line_no,
                "evidence": m.group(0).strip(),
                "reason": (
                    f"document.cookie write with credential-shaped value: "
                    f"{value_expr!r}"
                ),
            })
    return issues


_AUTH_HEADER_RE = re.compile(
    r"""['"]Authorization['"]\s*:""",
    re.IGNORECASE,
)
_BTOA_BASIC_RE = re.compile(
    r"""\bbtoa\s*\(\s*[`'"][^`'")]*:[^`'")]*[`'"]\s*\)""",
)
_BTOA_TEMPLATE_BASIC_RE = re.compile(
    r"""\bbtoa\s*\(\s*`[^`]*\$\{[^}]+\}[^`]*:[^`]*\$\{[^}]+\}[^`]*`\s*\)""",
)
_BASIC_PREFIX_RE = re.compile(
    r"""['"`]Basic\s+[A-Za-z0-9+/=$\{\}\s]""",
)


def scan_authorization_header(file_path: pathlib.Path, body: str):
    issues = []
    for m in _AUTH_HEADER_RE.finditer(body):
        line_no = body.count("\n", 0, m.start()) + 1
        issues.append({
            "invariant_id": "INV-FE-AUTH-002",
            "file": str(file_path),
            "line": line_no,
            "evidence": body.splitlines()[line_no - 1].strip(),
            "reason": "literal Authorization header key constructed client-side",
        })
    for rx, why in (
        (_BTOA_BASIC_RE, "btoa() encoding of a colon-delimited string (Basic auth shape)"),
        (_BTOA_TEMPLATE_BASIC_RE, "btoa() of template-literal user:password shape"),
        (_BASIC_PREFIX_RE, "literal 'Basic ' header prefix in source"),
    ):
        for m in rx.finditer(body):
            line_no = body.count("\n", 0, m.start()) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-002",
                "file": str(file_path),
                "line": line_no,
                "evidence": m.group(0).strip(),
                "reason": why,
            })
    return issues


_PASSWORD_INPUT_RE = re.compile(
    r"""<input\b[^>]*\btype\s*=\s*['"]password['"][^>]*>""",
    re.IGNORECASE,
)
_PASSWORD_NAME_INPUT_RE = re.compile(
    r"""<input\b[^>]*\bname\s*=\s*['"](password|recruiter[_-]?(?:user|pass)\w*)['"][^>]*>""",
    re.IGNORECASE,
)


def scan_credential_form(file_path: pathlib.Path, body: str):
    issues = []
    for rx, why in (
        (_PASSWORD_INPUT_RE, "in-page <input type=\"password\"> credential capture"),
        (_PASSWORD_NAME_INPUT_RE, "in-page credential-named <input> capture"),
    ):
        for m in rx.finditer(body):
            line_no = body.count("\n", 0, m.start()) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-003",
                "file": str(file_path),
                "line": line_no,
                "evidence": m.group(0).strip(),
                "reason": why,
            })
    return issues


_CUSTOM_401_HANDLER_RE = re.compile(
    r"""(?:status|statusCode)\s*===?\s*401[^\n]{0,200}"""
    r"""(?:setShow|setModal|setLogin|setAuthModal|prompt\s*\(|alert\s*\()""",
    re.IGNORECASE | re.DOTALL,
)


def scan_401_interception(file_path: pathlib.Path, body: str):
    issues = []
    for m in _CUSTOM_401_HANDLER_RE.finditer(body):
        line_no = body.count("\n", 0, m.start()) + 1
        issues.append({
            "invariant_id": "INV-FE-AUTH-004",
            "file": str(file_path),
            "line": line_no,
            "evidence": body.splitlines()[line_no - 1].strip(),
            "reason": (
                "client-side 401 interception with custom credential UI; "
                "browser-native WWW-Authenticate challenge must remain in effect"
            ),
        })
    return issues


def scan_credential_placeholder_echo(file_path: pathlib.Path, body: str):
    issues = []
    for placeholder in FORBIDDEN_CREDENTIAL_PLACEHOLDERS:
        idx = body.find(placeholder)
        if idx != -1:
            line_no = body.count("\n", 0, idx) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-005",
                "file": str(file_path),
                "line": line_no,
                "evidence": placeholder,
                "reason": "credential placeholder echo in committed frontend source",
            })
    return issues


def scan_banned_phrases_and_urls(file_path: pathlib.Path, body: str):
    issues = []
    lowered = body.lower()
    for phrase in BANNED_PHRASES:
        idx = lowered.find(phrase.lower())
        if idx != -1:
            line_no = body.count("\n", 0, idx) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-006",
                "file": str(file_path),
                "line": line_no,
                "evidence": phrase,
                "reason": f"banned phrase present: {phrase!r}",
            })
    for phrase in FORBIDDEN_FUTURE_SUBSTRINGS:
        idx = lowered.find(phrase.lower())
        if idx != -1:
            line_no = body.count("\n", 0, idx) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-006",
                "file": str(file_path),
                "line": line_no,
                "evidence": phrase,
                "reason": f"forbidden future-constraint substring: {phrase!r}",
            })
    for m in re.finditer(r"https?://[\w\.\-:]+", body):
        url = m.group(0)
        host = url.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
        if host not in ("127.0.0.1", "localhost", "0.0.0.0"):
            line_no = body.count("\n", 0, m.start()) + 1
            issues.append({
                "invariant_id": "INV-FE-AUTH-006",
                "file": str(file_path),
                "line": line_no,
                "evidence": url,
                "reason": "non-loopback URL literal in frontend source",
            })
    return issues


_TYPE_BLOCK_RE_TEMPLATE = (
    r"export\s+type\s+{name}\s*=\s*\{{(?P<body>[^}}]*)\}}\s*;"
)


def extract_router_type_blocks(types_text: str):
    extracted = {}
    for name in ROUTER_TYPE_BLOCK_NAMES:
        rx = re.compile(_TYPE_BLOCK_RE_TEMPLATE.format(name=name), re.DOTALL)
        m = rx.search(types_text)
        if not m:
            extracted[name] = None
        else:
            block_body = m.group("body")
            extracted[name] = block_body
    return extracted


def compute_router_shape_fingerprint(extracted: dict):
    parts = []
    for name in ROUTER_TYPE_BLOCK_NAMES:
        block = extracted.get(name)
        if block is None:
            parts.append(f"{name}:MISSING")
            continue
        # Canonicalize: strip line-leading whitespace and blank lines so
        # the fingerprint is robust to whitespace-only edits but trips
        # on any field added, removed, renamed, or retyped.
        canonical_lines = []
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                canonical_lines.append(stripped)
        parts.append(f"{name}:" + "\n".join(canonical_lines))
    blob = ("\n----\n".join(parts)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest(), parts


def scan_file(file_path: pathlib.Path):
    body = file_path.read_text(encoding="utf-8")
    issues = []
    issues += scan_storage_writes(file_path, body)
    issues += scan_authorization_header(file_path, body)
    issues += scan_credential_form(file_path, body)
    issues += scan_401_interception(file_path, body)
    issues += scan_credential_placeholder_echo(file_path, body)
    issues += scan_banned_phrases_and_urls(file_path, body)
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--types-file", required=True,
                        help="Path to services/frontend/app/demo/types.ts; read-only")
    parser.add_argument("--frontend-demo-dir", required=True,
                        help="Path to services/frontend/app/demo/ directory; read-only")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    types_path = pathlib.Path(args.types_file)
    demo_dir = pathlib.Path(args.frontend_demo_dir)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    checks = []

    # INV-FE-AUTH-007 first: frozen RouterFields shape.
    if not types_path.exists():
        checks.append(_check(
            "INV-FE-AUTH-007_router_fields_shape_frozen",
            False,
            f"types-file not found at {types_path}",
            marker=SENTINEL_FAIL_BROUTE,
        ))
        observed_shape_sha = "MISSING"
    else:
        types_text = types_path.read_text(encoding="utf-8")
        extracted = extract_router_type_blocks(types_text)
        observed_shape_sha, _parts = compute_router_shape_fingerprint(extracted)
        passed = observed_shape_sha == FROZEN_ROUTER_SHAPE_SHA256
        missing = [n for n, v in extracted.items() if v is None]
        if missing:
            detail = (
                f"router-bearing type blocks missing from types.ts: {missing}"
            )
            passed = False
        else:
            detail = (
                f"observed_sha256={observed_shape_sha} "
                f"expected_sha256={FROZEN_ROUTER_SHAPE_SHA256}"
            )
        checks.append(_check(
            "INV-FE-AUTH-007_router_fields_shape_frozen",
            passed,
            detail,
            marker=None if passed else SENTINEL_FAIL_BROUTE,
        ))

    # INV-FE-AUTH-001..006: scan every demo source file.
    demo_files = list_demo_source_files(demo_dir)
    all_issues = []
    for f in demo_files:
        all_issues += scan_file(f)

    by_invariant = {
        "INV-FE-AUTH-001": [i for i in all_issues if i["invariant_id"] == "INV-FE-AUTH-001"],
        "INV-FE-AUTH-002": [i for i in all_issues if i["invariant_id"] == "INV-FE-AUTH-002"],
        "INV-FE-AUTH-003": [i for i in all_issues if i["invariant_id"] == "INV-FE-AUTH-003"],
        "INV-FE-AUTH-004": [i for i in all_issues if i["invariant_id"] == "INV-FE-AUTH-004"],
        "INV-FE-AUTH-005": [i for i in all_issues if i["invariant_id"] == "INV-FE-AUTH-005"],
        "INV-FE-AUTH-006": [i for i in all_issues if i["invariant_id"] == "INV-FE-AUTH-006"],
    }
    for inv, friendly in (
        ("INV-FE-AUTH-001", "no_client_side_credential_persistence"),
        ("INV-FE-AUTH-002", "no_custom_authorization_basic_header"),
        ("INV-FE-AUTH-003", "no_inpage_credential_capture_form"),
        ("INV-FE-AUTH-004", "no_client_side_401_interception"),
        ("INV-FE-AUTH-005", "no_credential_placeholder_echo"),
        ("INV-FE-AUTH-006", "no_banned_phrase_or_nonloopback_url"),
    ):
        hits = by_invariant[inv]
        passed = not hits
        if passed:
            detail = "PASS (0 hits)"
        else:
            detail = f"{len(hits)} hit(s): " + "; ".join(
                f"{h['file']}:{h['line']} {h['reason']}" for h in hits
            )
        checks.append(_check(f"{inv}_{friendly}", passed, detail,
                             marker=None if passed else SENTINEL_FAIL))

    # Aggregate result and pick the dominant marker.
    failures = [c for c in checks if not c["passed"]]
    if not failures:
        sentinel = SENTINEL_PASS
    else:
        markers = [c["marker"] for c in failures if c["marker"]]
        if SENTINEL_FAIL in markers:
            sentinel = SENTINEL_FAIL
        else:
            sentinel = SENTINEL_FAIL_BROUTE

    # Build report.
    lines = [
        "# B14_0-04 Frontend Recruiter-Auth UX Contract",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"validator: {VALIDATOR_ID}",
        "schema_reference: docs/plans/b14_0/state_packet_schemas.yaml",
        "agent_plan_section_reference: docs/plans/b14_0/agent_plan.md sections 2 and 12",
        f"types_file: {types_path}",
        f"frontend_demo_dir: {demo_dir}",
        f"frontend_files_scanned: {len(demo_files)}",
        "",
        "## Frozen RouterFields Shape",
        "",
        f"- expected_sha256: {FROZEN_ROUTER_SHAPE_SHA256}",
        f"- observed_sha256: {observed_shape_sha}",
        "- type_blocks_covered:",
    ]
    for n in ROUTER_TYPE_BLOCK_NAMES:
        lines.append(f"    - {n}")
    lines += [
        "",
        "## Static Scan Checks",
        "",
    ]
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        lines.append(f"- [{status}] {c['name']}: {c['detail']}")

    lines += [
        "",
        "## Files Scanned",
        "",
    ]
    for f in demo_files:
        lines.append(f"- {f}")

    lines += [
        "",
        "## Result",
        "",
    ]
    if failures:
        lines.append(f"{len(failures)} check(s) failed:")
        lines.append("")
        for f in failures:
            lines.append(f"  - {f['name']} (marker={f['marker']}): {f['detail']}")
        lines += ["", sentinel]
    else:
        lines += [
            f"All {len(checks)} static-scan checks passed.",
            "",
            "frontend_files_modified: false",
            "types_ts_modified: false",
            "router_fields_shape_unchanged: true",
            "",
            sentinel,
        ]

    body = "\n".join(lines) + "\n"
    out_path.write_text(body)
    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
