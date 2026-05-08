#!/usr/bin/env python3
"""validate_eval_schema.py — robust_asr P1.2 / Section 4.1.

Inputs:
  --schema <yaml>   optional; defaults to libs/common/eval_schema.yaml

Asserts:
  1. Schema YAML loads.
  2. Listed columns equal the Section 3 column set (set equality, order
     irrelevant; the canonical list is hard-coded below from
     docs/plans/robust_asr_agent_plan_v3_4_7.md Section 3).
  3. Each column entry has a non-empty 'type' string recorded.

Stdout: ``OK_EVAL_SCHEMA`` on PASS, ``FAIL_EVAL_SCHEMA: <reason>`` otherwise.
Exit:   0 PASS, 1 FAIL.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "libs" / "common" / "eval_schema.yaml"

# Canonical Section 3 columns (verbatim names, plan v3.4.7).
SECTION_3_COLUMNS: List[str] = [
    "audio_id",
    "source_dataset",
    "source_split",
    "speaker_id",
    "utterance_id",
    "condition_family",
    "degradation_id",
    "degradation_params_json",
    "audio_path_or_uri",
    "audio_sha256",
    "reference_text",
    "reference_normalized",
    "backend_name",
    "backend_version",
    "backend_kind",
    "decode_config_json",
    "raw_transcript",
    "normalized_transcript",
    "normalization_version",
    "wer",
    "cer",
    "wa",
    "backend_latency_ms",
    "server_processing_latency_ms",
    "end_to_end_latency_ms",
    "ram_peak_mb",
    "cost_usd",
    "local_only",
    "third_party_provider",
    "error_or_null",
    "created_at_utc",
]


def _fail(reason: str) -> int:
    print(f"FAIL_EVAL_SCHEMA: {reason}")
    return 1


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Validate the robust_asr eval schema YAML.")
    p.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Path to eval_schema.yaml")
    args = p.parse_args(argv)

    schema_path = Path(args.schema)

    # Assertion 1: YAML loads.
    try:
        import yaml  # local import so --help works without yaml installed
    except Exception as exc:  # pragma: no cover - should be present in SIF
        return _fail(f"PyYAML import failed: {exc!r}")

    if not schema_path.is_file():
        return _fail(f"schema file not found: {schema_path}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return _fail(f"YAML parse error: {exc!r}")

    if not isinstance(schema, dict):
        return _fail("schema root must be a mapping")
    columns = schema.get("columns")
    if not isinstance(columns, list) or not columns:
        return _fail("schema.columns must be a non-empty list")

    # Assertion 2: column-name set equality with Section 3.
    listed = []
    for i, col in enumerate(columns):
        if not isinstance(col, dict):
            return _fail(f"columns[{i}] is not a mapping")
        name = col.get("name")
        if not isinstance(name, str) or not name:
            return _fail(f"columns[{i}].name missing or non-string")
        listed.append(name)

    listed_set = set(listed)
    expected_set = set(SECTION_3_COLUMNS)
    if len(listed) != len(listed_set):
        # find duplicates
        seen = set()
        dups = sorted({c for c in listed if (c in seen) or seen.add(c)})
        return _fail(f"duplicate column names: {sorted(dups)}")

    missing = sorted(expected_set - listed_set)
    extra = sorted(listed_set - expected_set)
    if missing or extra:
        return _fail(f"column set mismatch with Section 3: missing={missing} extra={extra}")

    # Assertion 3: each column declares a non-empty string 'type'.
    for col in columns:
        t = col.get("type")
        if not isinstance(t, str) or not t.strip():
            return _fail(f"column {col.get('name')!r} missing non-empty 'type'")

    print("OK_EVAL_SCHEMA")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
