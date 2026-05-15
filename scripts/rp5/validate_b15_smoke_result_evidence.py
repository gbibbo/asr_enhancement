#!/usr/bin/env python3
"""
B15 smoke-result evidence validator.

Reads the declarative B15-05 smoke-results deliverable and asserts that
every multi_network_smoke_result_record traces to operator-supplied
evidence: a non-null evidence_reference and a har_reference citing
HAR-B15-MULTI-NETWORK-SMOKE-001. A result record authored without a
non-null evidence_reference is treated as a fabricated smoke result.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_SMOKE_RESULT_EVIDENCE_TRACED on PASS or
B15_SMOKE_RESULT_FABRICATED on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_SMOKE_RESULT_EVIDENCE_TRACED"
SENTINEL_FAIL = "B15_SMOKE_RESULT_FABRICATED"

RECORD_KEY = "multi_network_smoke_result_record"
HAR_ID = "HAR-B15-MULTI-NETWORK-SMOKE-001"

YAML_BLOCK_RE = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def extract_records(text: str) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    for raw in YAML_BLOCK_RE.findall(text):
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            errors.append(f"a fenced yaml block failed to parse: {exc}")
            continue
        if isinstance(doc, dict) and isinstance(doc.get(RECORD_KEY), dict):
            records.append(doc[RECORD_KEY])
    return records, errors


def _is_null(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in ("", "null", "none"):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    results_path = pathlib.Path(args.results)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# B15 Smoke-Result Evidence Validation",
        "",
        f"generated_at_utc: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"results_path: {results_path}",
        "",
    ]

    if not results_path.exists():
        lines += [f"results file not found: {results_path}", "", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    records, errors = extract_records(results_path.read_text(encoding="utf-8"))
    failures: list[str] = list(errors)

    if not records:
        failures.append(f"no {RECORD_KEY} found in the results file")

    for idx, r in enumerate(records, start=1):
        rid = r.get("result_id", f"record#{idx}")
        if _is_null(r.get("evidence_reference")):
            failures.append(
                f"{rid}: evidence_reference is null/empty — smoke result is "
                "not traced to operator-supplied evidence"
            )
        har = r.get("har_reference")
        if _is_null(har):
            failures.append(f"{rid}: har_reference is null/empty")
        elif str(har).strip() != HAR_ID:
            failures.append(
                f"{rid}: har_reference '{har}' must cite {HAR_ID}"
            )

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- result records: {len(records)}")
    lines.append("")
    lines.append("## Rule Checks")
    lines.append("")
    if failures:
        for f in failures:
            lines.append(f"- [FAIL] {f}")
        lines += ["", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    lines += [
        "- [PASS] every result record cites a non-null evidence_reference",
        f"- [PASS] every result record cites har_reference {HAR_ID}",
        "",
        "## Result",
        "",
        "Every smoke-result record traces to operator-supplied evidence.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
