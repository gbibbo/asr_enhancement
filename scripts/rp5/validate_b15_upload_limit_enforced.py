#!/usr/bin/env python3
"""
B15 upload-limit-enforced validator.

Reads the declarative B15-05 smoke-results deliverable and asserts that
every multi_network_smoke_result_record observed the upload limit as
enforced. A record reporting upload_limit_observed=not_enforced is an
upload-limit regression under public smoke.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_UPLOAD_LIMIT_ENFORCED on PASS or
B15_UPLOAD_LIMIT_REGRESSION on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_UPLOAD_LIMIT_ENFORCED"
SENTINEL_FAIL = "B15_UPLOAD_LIMIT_REGRESSION"

RECORD_KEY = "multi_network_smoke_result_record"
FIELD = "upload_limit_observed"
EXPECTED = "enforced"
LEGAL_VALUES = {"enforced", "not_enforced"}

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
        "# B15 Upload-Limit-Enforced Validation",
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
        value = r.get(FIELD)
        if value not in LEGAL_VALUES:
            failures.append(
                f"{rid}: {FIELD} '{value}' is not a legal value {sorted(LEGAL_VALUES)}"
            )
        elif value != EXPECTED:
            failures.append(
                f"{rid}: {FIELD} is '{value}'; the upload limit must be "
                f"observed as '{EXPECTED}'"
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
        f"- [PASS] every result record observed {FIELD}={EXPECTED}",
        "",
        "## Result",
        "",
        "The upload limit was enforced across every result record.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
