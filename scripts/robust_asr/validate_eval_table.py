#!/usr/bin/env python3
"""validate_eval_table.py — robust_asr §4.1 eval table validator.

Asserts Section 3 schema tests 1..7 on a populated parquet table.
Sentinel `OK_EVAL_TABLE` on PASS (exit 0); `FAIL_EVAL_TABLE: <reason>`
on the first failing assertion (exit 1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "libs" / "common" / "eval_schema.yaml"


def _decode_config_hash(s: str) -> str:
    try:
        d = json.loads(s)
    except Exception:
        return hashlib.sha256(s.encode()).hexdigest()[:16]
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"FAIL_EVAL_TABLE: input not found: {in_path}", file=sys.stderr)
        return 1
    schema_doc = yaml.safe_load(SCHEMA_PATH.read_text())
    required = [c["name"] for c in schema_doc["columns"]]
    table = pq.read_table(in_path)

    # test 1: required columns exist
    missing = [c for c in required if c not in table.column_names]
    if missing:
        print(f"FAIL_EVAL_TABLE: missing columns: {missing}", file=sys.stderr)
        return 1

    cols = {c: table.column(c).to_pylist() for c in table.column_names}
    n = table.num_rows

    # test 2: unique on (audio_id, backend_name, decode_config_hash)
    seen = set()
    for i in range(n):
        pk = (cols["audio_id"][i], cols["backend_name"][i],
              _decode_config_hash(cols["decode_config_json"][i]))
        if pk in seen:
            print(f"FAIL_EVAL_TABLE: duplicate primary key at row {i}: {pk}",
                  file=sys.stderr)
            return 1
        seen.add(pk)

    # test 3: audio_id stable across backends (single-backend table → trivially ok)
    by_aid = {}
    for i in range(n):
        aid = cols["audio_id"][i]
        prev = by_aid.get(aid)
        cur = (cols["audio_path_or_uri"][i], cols["audio_sha256"][i])
        if prev is not None and prev != cur:
            print(f"FAIL_EVAL_TABLE: audio_id {aid} differs across rows: {prev} vs {cur}",
                  file=sys.stderr)
            return 1
        by_aid[aid] = cur

    # test 4: reference_normalized identical across backends for same audio_id
    by_aid_ref = {}
    for i in range(n):
        aid = cols["audio_id"][i]
        rn = cols["reference_normalized"][i]
        prev = by_aid_ref.get(aid)
        if prev is not None and prev != rn:
            print(f"FAIL_EVAL_TABLE: reference_normalized differs for {aid}",
                  file=sys.stderr)
            return 1
        by_aid_ref[aid] = rn

    # test 5: normalization_version non-null
    if any(v is None or v == "" for v in cols["normalization_version"]):
        print("FAIL_EVAL_TABLE: normalization_version null on at least one row",
              file=sys.stderr)
        return 1

    # test 6: error_or_null non-null whenever any latency is null
    for i in range(n):
        any_null = any(cols[k][i] is None for k in (
            "backend_latency_ms", "server_processing_latency_ms", "end_to_end_latency_ms"))
        if any_null and (cols["error_or_null"][i] is None or cols["error_or_null"][i] == ""):
            print(f"FAIL_EVAL_TABLE: row {i} has null latency without error_or_null",
                  file=sys.stderr)
            return 1

    # test 7: cost_usd null only when local_only true; numeric otherwise
    for i in range(n):
        if cols["cost_usd"][i] is None and not bool(cols["local_only"][i]):
            print(f"FAIL_EVAL_TABLE: cost_usd null with local_only=false at row {i}",
                  file=sys.stderr)
            return 1

    print(f"rows={n} unique_pk={len(seen)} unique_audio_id={len(by_aid)}", flush=True)
    print("OK_EVAL_TABLE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
