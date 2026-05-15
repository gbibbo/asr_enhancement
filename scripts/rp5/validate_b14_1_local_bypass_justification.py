#!/usr/bin/env python3
"""
B14.1 local-bypass-justification validator.

Scans the application-layer surface under a given --root for any local/dev
authority-bypass surface keyed on the PUBLIC_DEMO_EXPOSURE flag, and cross-
checks the committed declaration at
reports/rp5/b14_1_local_bypass_justification.md.

Scope of the scan:

  * services/api/app/**.py
  * libs/**.py
  * tests/demo/**.py

For each file, the scanner identifies references to the flag identifier
``PUBLIC_DEMO_EXPOSURE`` (env name) or ``get_public_demo_exposure_flag``
(read-only accessor). Each reference is classified:

  CLASS A  ACCESSOR_MODULE                — the read-only accessor in
           services/api/app/public_exposure.py is allow-listed by path.
  CLASS B  IMPORT_OR_TEXT                  — bare ``import``, ``from`` line,
           docstring/comment-only line referencing the flag identifier.
  CLASS C  OPENAPI_DOCS_VISIBILITY_TOGGLE — a conditional whose textual
           context (the hit line and the next four lines) sets only
           ``openapi_url``, ``docs_url``, ``redoc_url``, ``FastAPI(``, or
           assigns ``app =`` / ``application =``, and references nothing
           in the authority-context vocabulary.
  CLASS D  BYPASS_CANDIDATE                — every other hit.

The validator is sound, not exhaustive: any flag-keyed control-flow that
short-circuits an authority decision lands in CLASS D unless its
surrounding lines exclusively belong to the OpenAPI/docs visibility
vocabulary.

Authority-context vocabulary (any token here makes a hit ineligible for
CLASS C and forces classification re-evaluation): ``recruiter_auth``,
``RecruiterAuthChallenge``, ``Depends(``, ``RECRUITER_``, ``Authorization``,
``compare_digest``, ``WWW-Authenticate``, ``HTTPBasic``, ``status_code=401``,
``raise HTTPException``, ``return Response(``.

Report cross-check rule (state_packet_schemas.yaml §local_bypass_justification_record):

  * If the report asserts ``classification: explicit_NA_zero_bypasses`` and
    ``bypass_count: 0``, the scan must produce zero BYPASS_CANDIDATE hits.
  * If the report enumerates one or more bypass records, every CLASS D hit
    must be covered by a record whose ``justification_test_path`` exists
    under --root.

Emits OK_B14_1_LOCAL_BYPASS_JUSTIFIED on PASS or
B14_1_LOCAL_BYPASS_UNJUSTIFIED on FAIL. The validator never writes any
secret, hostname, public URL, or Authorization value to its --out report.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

SENTINEL_PASS = "OK_B14_1_LOCAL_BYPASS_JUSTIFIED"
MARKER_FAIL = "B14_1_LOCAL_BYPASS_UNJUSTIFIED"

FLAG_IDENTIFIERS = ("PUBLIC_DEMO_EXPOSURE", "get_public_demo_exposure_flag")

ACCESSOR_MODULE_REL = "services/api/app/public_exposure.py"

# Visibility vocabulary — tokens that may appear alongside a flag hit in
# CLASS C (OpenAPI/docs visibility) without converting it into a bypass.
VISIBILITY_VOCAB = (
    "openapi_url", "docs_url", "redoc_url",
    "FastAPI(", "app =", "application =",
    "title=", "version=", "lifespan=",
)

# Authority vocabulary — any token here forces a flag hit out of CLASS C.
AUTHORITY_VOCAB = (
    "recruiter_auth", "RecruiterAuthChallenge",
    "Depends(", "RECRUITER_", "Authorization",
    "compare_digest", "WWW-Authenticate", "HTTPBasic",
    "status_code=401", "raise HTTPException", "return Response(",
)

CONTEXT_LOOKAHEAD_LINES = 4

SCAN_SUBTREES = ("services/api/app", "libs", "tests/demo")

REPORT_REL = "reports/rp5/b14_1_local_bypass_justification.md"

SKIP_DIR_NAMES = {
    ".git", "__pycache__", "node_modules", ".next", "out", "dist",
    "build", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox",
}


def _is_skipped_dir(part: str) -> bool:
    return part in SKIP_DIR_NAMES


def _iter_python_files(root: pathlib.Path):
    for sub in SCAN_SUBTREES:
        base = root / sub
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if not path.is_file():
                continue
            if any(_is_skipped_dir(part) for part in path.parts):
                continue
            yield path.relative_to(root), path


_FLAG_RE = re.compile(r"\b(PUBLIC_DEMO_EXPOSURE|get_public_demo_exposure_flag)\b")
_IMPORT_LINE_RE = re.compile(r"^\s*(import\s|from\s)")
_DOCSTRING_OPEN_RE = re.compile(r'(^|\s)("""|\'\'\')')


def _line_is_import(line: str) -> bool:
    return bool(_IMPORT_LINE_RE.match(line))


def _line_is_comment_only(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("#")


def _classify_hit(rel_path: str, line_idx: int, lines: list[str]) -> str:
    rel_norm = rel_path.replace("\\", "/")
    if rel_norm == ACCESSOR_MODULE_REL:
        return "ACCESSOR_MODULE"
    line = lines[line_idx]
    if _line_is_import(line):
        return "IMPORT_OR_TEXT"
    if _line_is_comment_only(line):
        return "IMPORT_OR_TEXT"
    # Build context window: hit line through next CONTEXT_LOOKAHEAD_LINES.
    window_end = min(len(lines), line_idx + 1 + CONTEXT_LOOKAHEAD_LINES)
    window = lines[line_idx:window_end]
    window_text = "\n".join(window)
    has_authority = any(tok in window_text for tok in AUTHORITY_VOCAB)
    if has_authority:
        return "BYPASS_CANDIDATE"
    has_visibility = any(tok in window_text for tok in VISIBILITY_VOCAB)
    if has_visibility:
        return "OPENAPI_DOCS_VISIBILITY_TOGGLE"
    return "BYPASS_CANDIDATE"


def _scan_repo(root: pathlib.Path):
    hits = []
    files_scanned = 0
    for rel, abs_path in _iter_python_files(root):
        rel_str = str(rel).replace("\\", "/")
        try:
            text = abs_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        files_scanned += 1
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if not _FLAG_RE.search(line):
                continue
            classification = _classify_hit(rel_str, idx, lines)
            hits.append({
                "path": rel_str,
                "line": idx + 1,
                "classification": classification,
            })
    return hits, files_scanned


_REPORT_KV_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")
_REPORT_LIST_ITEM_RE = re.compile(r"^\s*-\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")


def _parse_report(text: str) -> dict:
    """Extract the declarative fields the validator needs.

    The report is a markdown document that contains one or more ```yaml
    fenced blocks. The parser is permissive but bounded: it reads the
    primary classification keys (``classification`` and ``bypass_count``)
    and any enumerated bypass records with their fields.
    """
    result = {
        "classification": None,
        "bypass_count": None,
        "validator": None,
        "marker": None,
        "bypasses": [],
    }
    in_yaml = False
    current_list_kind: str | None = None
    current_record: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            fence = line.strip()
            if fence.startswith("```yaml") or fence.startswith("```yml"):
                in_yaml = True
                continue
            if in_yaml and fence == "```":
                in_yaml = False
                current_list_kind = None
                current_record = None
                continue
            continue
        if not in_yaml:
            continue
        if not line.strip():
            continue
        m_top = _REPORT_KV_RE.match(line)
        if m_top and not line.startswith(" "):
            key, value = m_top.group(1), m_top.group(2)
            if key == "bypasses":
                current_list_kind = "bypasses"
                current_record = None
                continue
            current_list_kind = None
            current_record = None
            if key in ("classification", "validator", "marker"):
                result[key] = value.strip().strip('"').strip("'")
            elif key == "bypass_count":
                try:
                    result["bypass_count"] = int(value.strip())
                except ValueError:
                    result["bypass_count"] = None
            continue
        if current_list_kind == "bypasses":
            stripped = line.lstrip()
            if stripped.startswith("- "):
                # New record. Capture inline key/value from the dash line.
                m_item = _REPORT_LIST_ITEM_RE.match(line)
                current_record = {}
                result["bypasses"].append(current_record)
                if m_item:
                    current_record[m_item.group(1)] = (
                        m_item.group(2).strip().strip('"').strip("'")
                    )
                continue
            m_cont = _REPORT_KV_RE.match(line)
            if m_cont and current_record is not None:
                current_record[m_cont.group(1)] = (
                    m_cont.group(2).strip().strip('"').strip("'")
                )
                continue
    return result


def _validate_report_shape(report: dict, hits: list[dict]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    bypass_hits = [h for h in hits if h["classification"] == "BYPASS_CANDIDATE"]
    classification = report.get("classification")
    if report.get("validator") != "validate_b14_1_local_bypass_justification":
        failures.append(
            "report.validator must equal 'validate_b14_1_local_bypass_justification'; "
            f"got {report.get('validator')!r}"
        )
    if report.get("marker") != "B14_1_LOCAL_BYPASS_UNJUSTIFIED":
        failures.append(
            "report.marker must equal 'B14_1_LOCAL_BYPASS_UNJUSTIFIED'; "
            f"got {report.get('marker')!r}"
        )
    if classification == "explicit_NA_zero_bypasses":
        if report.get("bypass_count") != 0:
            failures.append(
                "report asserts explicit_NA_zero_bypasses but bypass_count is "
                f"{report.get('bypass_count')!r}; expected 0"
            )
        if bypass_hits:
            failures.append(
                f"report asserts explicit_NA_zero_bypasses but source-tree scan "
                f"found {len(bypass_hits)} BYPASS_CANDIDATE hit(s); first hit: "
                f"{bypass_hits[0]['path']}:{bypass_hits[0]['line']}"
            )
        if report.get("bypasses"):
            failures.append(
                "report asserts explicit_NA_zero_bypasses but enumerates "
                f"{len(report['bypasses'])} bypass record(s); list must be empty"
            )
        return (not failures), failures
    if classification is None:
        failures.append("report.classification is missing")
        return False, failures
    failures.append(
        f"report.classification = {classification!r} is not recognised; "
        "the primary B14_1-05 legal route is 'explicit_NA_zero_bypasses'. "
        "Non-NA classifications require CHANGE_SCOPE."
    )
    return False, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    hits, files_scanned = _scan_repo(root)
    bypass_hits = [h for h in hits if h["classification"] == "BYPASS_CANDIDATE"]
    accessor_hits = [h for h in hits if h["classification"] == "ACCESSOR_MODULE"]
    visibility_hits = [h for h in hits if h["classification"] == "OPENAPI_DOCS_VISIBILITY_TOGGLE"]
    text_hits = [h for h in hits if h["classification"] == "IMPORT_OR_TEXT"]

    report_path = root / REPORT_REL
    report_present = report_path.is_file()
    report = {"classification": None, "bypass_count": None,
              "validator": None, "marker": None, "bypasses": []}
    report_failures: list[str] = []
    if report_present:
        try:
            text = report_path.read_text(encoding="utf-8")
        except OSError as exc:
            report_failures.append(f"report unreadable: {exc}")
        else:
            report = _parse_report(text)
    else:
        report_failures.append(f"report missing at {REPORT_REL}")

    if report_present:
        ok, shape_failures = _validate_report_shape(report, hits)
        if not ok:
            report_failures.extend(shape_failures)

    lines_out = [
        "# B14.1 Local Bypass Justification — Scan Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"root: {root}",
        f"files_scanned: {files_scanned}",
        f"flag_identifier_hits_total: {len(hits)}",
        f"hits_class_accessor_module: {len(accessor_hits)}",
        f"hits_class_openapi_docs_visibility_toggle: {len(visibility_hits)}",
        f"hits_class_import_or_text: {len(text_hits)}",
        f"hits_class_bypass_candidate: {len(bypass_hits)}",
        f"report_present: {report_present}",
        f"report_classification: {report.get('classification')!r}",
        f"report_bypass_count: {report.get('bypass_count')!r}",
        "",
        "## Bypass Candidate Hits",
        "",
    ]
    if bypass_hits:
        for h in bypass_hits:
            lines_out.append(f"- {h['path']}:{h['line']} -> BYPASS_CANDIDATE")
    else:
        lines_out.append("- none")

    if args.verbose:
        lines_out += ["", "## All Hits (verbose)", ""]
        for h in hits:
            lines_out.append(f"- {h['path']}:{h['line']} -> {h['classification']}")

    lines_out += ["", "## Report Shape Failures", ""]
    if report_failures:
        for f in report_failures:
            lines_out.append(f"- {f}")
    else:
        lines_out.append("- none")

    fail = bool(bypass_hits) or bool(report_failures)
    if fail:
        lines_out += ["", MARKER_FAIL]
        out_path.write_text("\n".join(lines_out) + "\n")
        print(MARKER_FAIL)
        return 1

    lines_out += [
        "",
        "## Result",
        "",
        "No bypass-candidate hit found and report shape passes.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines_out) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
