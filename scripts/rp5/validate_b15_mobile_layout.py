#!/usr/bin/env python3
"""
B15 mobile-layout validator (vantage-point-conditional).

Reads the declarative B15-05 smoke-results deliverable and asserts the
mobile_layout_observed value on each multi_network_smoke_result_record
under the per-vantage-point rule pinned by
docs/plans/b15/state_packet_schemas.yaml > multi_network_smoke_result_record:

  * for vantage_point == mobile_cellular: mobile_layout_observed must be
    no_horizontal_scroll (PASS) or horizontal_scroll_observed (FAIL ->
    B15_MOBILE_LAYOUT_REGRESSION); not_applicable is illegal on the mobile
    vantage point and is treated as B15_MOBILE_LAYOUT_REGRESSION.
  * for vantage_point in {windows_local, other_wifi, vpn_or_external_tester}:
    mobile_layout_observed must be no_horizontal_scroll (PASS) or
    not_applicable (PASS); horizontal_scroll_observed remains a regression.
  * any value outside the schema enum is a regression marker.

The validator is pure: it reads one declarative record file and writes
only the requested --out report. It performs no public network call.

Emits OK_B15_MOBILE_LAYOUT_OK on PASS or
B15_MOBILE_LAYOUT_REGRESSION on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_B15_MOBILE_LAYOUT_OK"
SENTINEL_FAIL = "B15_MOBILE_LAYOUT_REGRESSION"

RECORD_KEY = "multi_network_smoke_result_record"
FIELD = "mobile_layout_observed"
VANTAGE_FIELD = "vantage_point"

LEGAL_VALUES = {"no_horizontal_scroll", "horizontal_scroll_observed", "not_applicable"}
MOBILE_VANTAGE_POINTS = {"mobile_cellular"}
NON_MOBILE_VANTAGE_POINTS = {"windows_local", "other_wifi", "vpn_or_external_tester"}

PASS_VALUES_BY_VANTAGE = {
    "mobile_cellular": {"no_horizontal_scroll"},
    "windows_local": {"no_horizontal_scroll", "not_applicable"},
    "other_wifi": {"no_horizontal_scroll", "not_applicable"},
    "vpn_or_external_tester": {"no_horizontal_scroll", "not_applicable"},
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
        "# B15 Mobile-Layout Validation",
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
        vp = r.get(VANTAGE_FIELD)
        if value not in LEGAL_VALUES:
            failures.append(
                f"{rid}: {FIELD} '{value}' is not a legal value {sorted(LEGAL_VALUES)}"
            )
            continue
        if vp in MOBILE_VANTAGE_POINTS:
            if value == "not_applicable":
                failures.append(
                    f"{rid}: {FIELD} 'not_applicable' is not legal on vantage_point "
                    f"'{vp}'; mobile_cellular must observe no_horizontal_scroll or "
                    f"horizontal_scroll_observed"
                )
            elif value != "no_horizontal_scroll":
                failures.append(
                    f"{rid}: {FIELD} is '{value}' on vantage_point '{vp}'; the "
                    f"mobile layout must be observed as 'no_horizontal_scroll'"
                )
        elif vp in NON_MOBILE_VANTAGE_POINTS:
            allowed = PASS_VALUES_BY_VANTAGE[vp]
            if value not in allowed:
                failures.append(
                    f"{rid}: {FIELD} is '{value}' on vantage_point '{vp}'; "
                    f"expected one of {sorted(allowed)}"
                )
        else:
            failures.append(
                f"{rid}: vantage_point '{vp}' is not recognized; expected one of "
                f"{sorted(MOBILE_VANTAGE_POINTS | NON_MOBILE_VANTAGE_POINTS)}"
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
        f"- [PASS] every result record observed a legal {FIELD} value under "
        f"its vantage_point (mobile_cellular: no_horizontal_scroll; non-mobile: "
        f"no_horizontal_scroll or not_applicable)",
        "",
        "## Result",
        "",
        "The mobile layout showed no horizontal scroll on the mobile vantage "
        "point, and non-mobile vantage points observed a legal value (either "
        "no_horizontal_scroll or not_applicable).",
        "",
        SENTINEL_PASS,
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
