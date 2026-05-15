#!/usr/bin/env python3
"""
B15 provider-quota-state accuracy validator.

Reads the declarative B15-05 smoke-results deliverable and asserts that
every multi_network_smoke_result_record reports a quota_state_observed
value drawn from the four canonical AssemblyAI quota states. A value
outside that set is a misrepresented provider quota state.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_QUOTA_STATE_ACCURATE on PASS or
B15_QUOTA_STATE_MISREPRESENTED on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_QUOTA_STATE_ACCURATE"
SENTINEL_FAIL = "B15_QUOTA_STATE_MISREPRESENTED"

RECORD_KEY = "multi_network_smoke_result_record"
FIELD = "quota_state_observed"
LEGAL_VALUES = {
    "AssemblyAI available",
    "AssemblyAI daily quota reached",
    "AssemblyAI quota exhausted",
    "AssemblyAI disabled",
}

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
        "# B15 Provider-Quota-State Accuracy Validation",
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
                f"{rid}: {FIELD} '{value}' is not a canonical AssemblyAI "
                f"quota state {sorted(LEGAL_VALUES)}"
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
        f"- [PASS] every result record reports a canonical {FIELD}",
        "",
        "## Result",
        "",
        "Every result record reports an accurate provider quota state.",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
