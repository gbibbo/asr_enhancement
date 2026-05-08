#!/usr/bin/env python3
"""Validate report fixture files against state_packet_schemas_v1.yaml.

Usage:
    python scripts/robust_asr/validate_report_shape.py \
        --schemas docs/plans/state_packet_schemas_v1.yaml \
        --fixtures artifacts/robust_asr/state_packets/report_shape_fixtures

Emits OK_REPORT_SHAPE on success. Exits 1 on the first inconsistency.
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not available. Install via: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SCHEMAS_TO_VALIDATE = [
    "prebootstrap_inventory_report",
    "planning_report",
    "execution_report",
    "phase_gate_report",
    "approval_packet",
    "supplemental_evidence_report",
]

APPROVAL_PACKET_WRAPPER = "ORCHESTRATOR_DECISION"


def die(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def get_required_field_names(fields_dict: dict) -> list:
    return [
        k for k, v in fields_dict.items()
        if isinstance(v, dict) and v.get("required") is True
    ]


def validate_fields_present(fields_dict: dict, section_data: dict,
                             section_name: str, schema_name: str) -> None:
    required = get_required_field_names(fields_dict)
    if section_data is None:
        section_data = {}
    for field in required:
        if field not in section_data:
            die(
                f"[{schema_name}] Section '{section_name}': "
                f"required field '{field}' missing from fixture"
            )


def validate_state_packet_present(state_packet_spec: dict, section_data: dict,
                                   section_name: str, schema_name: str) -> None:
    fields = state_packet_spec.get("fields", {})
    required = get_required_field_names(fields)
    if section_data is None:
        section_data = {}
    for field in required:
        if field not in section_data:
            die(
                f"[{schema_name}] Section '{section_name}' (state_packet content): "
                f"required field '{field}' missing"
            )


def validate_sections_based(schema_def: dict, fixture_data: dict,
                             schema_name: str, state_packet_spec: dict) -> None:
    sections = schema_def.get("sections", [])
    expected_names = [s["name"] for s in sections]

    if fixture_data is None:
        die(f"[{schema_name}] Fixture file is empty or null")

    actual_names = list(fixture_data.keys())

    if actual_names != expected_names:
        die(
            f"[{schema_name}] Section order or names mismatch.\n"
            f"  Expected: {expected_names}\n"
            f"  Got:      {actual_names}"
        )

    for section_spec in sections:
        section_name = section_spec["name"]
        section_data = fixture_data.get(section_name) or {}

        content = section_spec.get("content")
        if content == "state_packet":
            validate_state_packet_present(
                state_packet_spec, section_data, section_name, schema_name
            )
            # Also check additional_fields if defined
            additional = section_spec.get("additional_fields", {})
            if additional:
                required_additional = get_required_field_names(additional)
                for field in required_additional:
                    if field not in section_data:
                        die(
                            f"[{schema_name}] Section '{section_name}' "
                            f"additional_field '{field}' missing"
                        )
        elif "fields" in section_spec:
            validate_fields_present(
                section_spec["fields"], section_data, section_name, schema_name
            )


def validate_approval_packet(schema_def: dict, fixture_data: dict,
                              schema_name: str) -> None:
    if fixture_data is None:
        die(f"[{schema_name}] Fixture file is empty or null")

    top_level_keys = list(fixture_data.keys())

    if len(top_level_keys) != 1:
        die(
            f"[{schema_name}] Must have exactly one top-level key "
            f"(only_top_level_key_allowed), got {len(top_level_keys)}: {top_level_keys}"
        )

    if top_level_keys[0] != APPROVAL_PACKET_WRAPPER:
        die(
            f"[{schema_name}] Top-level key must be '{APPROVAL_PACKET_WRAPPER}', "
            f"got '{top_level_keys[0]}'"
        )

    wrapper_spec = schema_def.get("wrapper", {})
    wrapper_fields = wrapper_spec.get("fields", {})
    required = get_required_field_names(wrapper_fields)

    inner = fixture_data[APPROVAL_PACKET_WRAPPER] or {}
    for field in required:
        if field not in inner:
            die(
                f"[{schema_name}] {APPROVAL_PACKET_WRAPPER}: "
                f"required field '{field}' missing"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate report shape fixtures against state_packet_schemas_v1.yaml"
    )
    parser.add_argument(
        "--schemas", required=True,
        help="Path to state_packet_schemas_v1.yaml"
    )
    parser.add_argument(
        "--fixtures", required=True,
        help="Directory containing fixture YAML files"
    )
    args = parser.parse_args()

    schemas_path = Path(args.schemas)
    fixtures_dir = Path(args.fixtures)

    if not schemas_path.exists():
        die(f"Schemas file not found: {schemas_path}")

    if not fixtures_dir.is_dir():
        die(f"Fixtures directory not found: {fixtures_dir}")

    try:
        with open(schemas_path) as f:
            schemas = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        die(f"SCHEMA_PARSE_ERROR: {exc}")

    if not isinstance(schemas, dict):
        die("SCHEMA_PARSE_ERROR: top-level schemas value must be a mapping")

    state_packet_spec = schemas.get("state_packet")
    if not state_packet_spec:
        die("SCHEMA_PARSE_ERROR: 'state_packet' key missing from schemas file")

    for schema_name in SCHEMAS_TO_VALIDATE:
        fixture_path = fixtures_dir / f"{schema_name}.yaml"

        if not fixture_path.exists():
            die(f"[{schema_name}] Fixture file not found: {fixture_path}")

        try:
            with open(fixture_path) as f:
                fixture_data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            die(f"[{schema_name}] YAML parse error in fixture: {exc}")

        schema_def = schemas.get(schema_name)
        if not schema_def:
            die(f"Schema '{schema_name}' not found in schemas file")

        if schema_name == "approval_packet":
            validate_approval_packet(schema_def, fixture_data, schema_name)
        else:
            validate_sections_based(
                schema_def, fixture_data, schema_name, state_packet_spec
            )

    print("OK_REPORT_SHAPE")


if __name__ == "__main__":
    main()
