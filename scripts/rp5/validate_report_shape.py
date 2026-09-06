#!/usr/bin/env python3
"""
Reusable protocol validator: report / declarative-record shape checker.

Materialized by the B15-03 scope-change repair (orchestrator decision
APPROVE_SCOPE_CHANGE_EXECUTION, scope=scope_change, task_id=B15-03). It
was previously referenced by the B15 plan as a reusable protocol validator
"invoked directly" but had never been materialized in reachable HEAD.

Validates a report or declarative-record file against the active B15 schema
file docs/plans/b15/state_packet_schemas.yaml. It supports two kinds of
schema entry:

  * report shapes carrying `section_order` -- the report is markdown and
    every section name in section_order must appear as a heading
    (planning_report, execution_report, phase_gate_report, ...);
  * declarative records carrying `fields` / `required_fields` -- the record
    is a fenced ```yaml block and every required field must be present
    (b15_human_action_packet, multi_network_smoke_coverage_record, ...).

The report file may be a markdown file embedding one or more fenced ```yaml
blocks, or a plain .yaml / .yml file.

Pure: reads the schema file and the report file, writes only the optional
--out report (default under /tmp). No network call, no project-state
mutation.

Emits OK_REPORT_SHAPE on PASS or REPORT_SCHEMA_INVALID on FAIL.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import yaml

SENTINEL_PASS = "OK_REPORT_SHAPE"
SENTINEL_FAIL = "REPORT_SCHEMA_INVALID"

DEFAULT_SCHEMAS = "docs/plans/b15/state_packet_schemas.yaml"
DEFAULT_OUT = "/tmp/validate_report_shape_out.md"

_YAML_BLOCK = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)


def _extract_yaml_mappings(report_path: pathlib.Path):
    """Return the list of top-level mappings parsed from the report file."""
    text = report_path.read_text()
    raw_blocks = []
    if report_path.suffix.lower() in (".yaml", ".yml"):
        raw_blocks.append(text)
    raw_blocks.extend(_YAML_BLOCK.findall(text))
    mappings = []
    for raw in raw_blocks:
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict):
            mappings.append(doc)
    return text, mappings


def _resolve_schema_entry(schemas: dict, shape_name: str):
    """Resolve a schema entry, following a single `same_as` alias hop."""
    entry = schemas.get(shape_name)
    if isinstance(entry, dict) and "same_as" in entry:
        alias = entry["same_as"]
        aliased = schemas.get(alias)
        if isinstance(aliased, dict):
            return aliased, alias
    return entry, shape_name


def run_checks(schemas_path: pathlib.Path, report_path: pathlib.Path,
               shape_arg: str | None):
    failures = []
    notes = []

    schemas = yaml.safe_load(schemas_path.read_text())
    if not isinstance(schemas, dict):
        return ["schema file did not parse to a mapping"], notes, None

    text, mappings = _extract_yaml_mappings(report_path)
    if not mappings:
        notes.append("no fenced ```yaml block parsed from the report")

    schema_names = set(schemas.keys())

    # Determine the shape name and, for record shapes, the record body.
    shape_name = shape_arg
    record_body = None
    if shape_name is None:
        for m in mappings:
            single = list(m.keys())
            if len(single) == 1 and single[0] in schema_names:
                shape_name = single[0]
                record_body = m[single[0]]
                break
    else:
        for m in mappings:
            if shape_name in m and len(m) == 1:
                record_body = m[shape_name]
                break

    if shape_name is None:
        failures.append(
            "could not determine the report shape: pass --shape or embed a "
            "single-key ```yaml block whose key names a schema entry"
        )
        return failures, notes, None

    if shape_name not in schema_names:
        failures.append(f"shape '{shape_name}' is not defined in the schema file")
        return failures, notes, shape_name

    entry, resolved = _resolve_schema_entry(schemas, shape_name)
    if resolved != shape_name:
        notes.append(f"shape '{shape_name}' resolved via same_as -> '{resolved}'")
    if not isinstance(entry, dict):
        failures.append(f"schema entry for '{resolved}' is not a mapping")
        return failures, notes, shape_name

    section_order = entry.get("section_order")
    required_fields = entry.get("required_fields") or entry.get("fields")

    if section_order:
        # Report-shape mode: every section name must appear as a heading.
        upper = text.upper()
        missing = [s for s in section_order if s.upper() not in upper]
        if missing:
            failures.append(f"report sections missing from '{resolved}': {missing}")
        else:
            notes.append(
                f"all {len(section_order)} section_order headings present for "
                f"'{resolved}'"
            )
    elif required_fields:
        # Record mode: required fields must be present in the record body.
        if record_body is None:
            for m in mappings:
                if all(f in m for f in required_fields):
                    record_body = m
                    break
        if not isinstance(record_body, dict):
            failures.append(
                f"no ```yaml mapping carrying the '{resolved}' record body found"
            )
        else:
            missing = [f for f in required_fields if f not in record_body]
            if missing:
                failures.append(
                    f"record '{resolved}' missing required fields: {missing}"
                )
            else:
                notes.append(
                    f"all {len(required_fields)} required fields present for "
                    f"'{resolved}'"
                )
    else:
        failures.append(
            f"schema entry '{resolved}' declares neither section_order nor "
            f"required_fields/fields; cannot validate shape"
        )

    return failures, notes, shape_name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas", default=DEFAULT_SCHEMAS,
                        help="path to the active B15 state_packet_schemas.yaml")
    parser.add_argument("--report", required=True,
                        help="path to the report / declarative-record file to validate")
    parser.add_argument("--shape",
                        help="explicit schema shape name; inferred from the "
                             "report when omitted")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="path for the transient validation report")
    args = parser.parse_args()

    schemas_path = pathlib.Path(args.schemas)
    report_path = pathlib.Path(args.report)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Report Shape Validation",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"schemas: {args.schemas}",
        f"report: {args.report}",
    ]

    if not schemas_path.is_file():
        lines += ["", f"{SENTINEL_FAIL}: schema file not found: {args.schemas}"]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1
    if not report_path.is_file():
        lines += ["", f"{SENTINEL_FAIL}: report file not found: {args.report}"]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    failures, notes, shape_name = run_checks(schemas_path, report_path, args.shape)
    lines.append(f"shape: {shape_name}")
    lines += ["", "## Notes", ""]
    lines += [f"- {n}" for n in notes] or ["- (none)"]

    if failures:
        lines += ["", "## Failures", ""]
        lines += [f"- {f}" for f in failures]
        lines += ["", SENTINEL_FAIL]
        out_path.write_text("\n".join(lines) + "\n")
        print(SENTINEL_FAIL)
        return 1

    lines += ["", "## Result", "",
              f"Report shape '{shape_name}' conforms to the schema.", "",
              SENTINEL_PASS]
    out_path.write_text("\n".join(lines) + "\n")
    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
