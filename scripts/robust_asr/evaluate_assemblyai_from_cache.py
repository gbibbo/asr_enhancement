#!/usr/bin/env python3
"""evaluate_assemblyai_from_cache.py — robust_asr §4.5 cache evaluator.

Reads AssemblyAI cached transcripts and writes a canonical 28-column
eval table parquet. local_only=false, third_party_provider="assemblyai".
For audio_ids without a cache entry, writes one row with
error_or_null="no_cache_entry" and all latency fields null.

Stdout (PASS):  OK_ASSEMBLYAI_EVAL <rows> <missing>
Exit codes:     0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from libs.common.normalization import NORMALIZATION_VERSION, normalize_text  # noqa: E402
from libs.common.metrics import wer as compute_wer, cer as compute_cer, wa as compute_wa  # noqa: E402

ASSEMBLYAI_BACKEND_VERSION = "assemblyai_universal_v1"

DECODE_CONFIG = {
    "provider": "assemblyai",
    "language_code": "en",
    "model": "universal",
}


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def collect_manifest_rows(manifests_doc: dict,
                          repo_root: Path = REPO_ROOT) -> list[dict]:
    rows: list[dict] = []
    for m in manifests_doc.get("manifests", []):
        if not m.get("enabled", True):
            continue
        path = repo_root / m["path"]
        if not path.exists():
            continue
        t = pq.read_table(path)
        names = t.column_names
        cols = {n: t.column(n).to_pylist() for n in names}
        for i in range(t.num_rows):
            if cols.get("bad_output", [False] * t.num_rows)[i]:
                continue
            rows.append({n: cols[n][i] for n in names})
    return rows


def _row_dict(manifest_row: dict, cached: dict | None,
              pricing: dict, created_at: str) -> dict:
    decode_json = json.dumps(DECODE_CONFIG, sort_keys=True)
    base = {
        "audio_id": manifest_row.get("audio_id"),
        "source_dataset": manifest_row.get("source_dataset"),
        "source_split": manifest_row.get("source_split"),
        "speaker_id": str(manifest_row.get("speaker_id")),
        "utterance_id": manifest_row.get("utterance_id"),
        "condition_family": manifest_row.get("condition_family"),
        "degradation_id": manifest_row.get("degradation_id"),
        "degradation_params_json": json.dumps({
            "filter_params_json": manifest_row.get("filter_params_json"),
            "snr_db": manifest_row.get("snr_db"),
            "rir_id_or_null": manifest_row.get("rir_id_or_null"),
        }, sort_keys=True),
        "audio_path_or_uri": manifest_row.get("audio_path_or_uri"),
        "audio_sha256": manifest_row.get("audio_sha256"),
        "reference_text": manifest_row.get("reference_text", ""),
        "reference_normalized": normalize_text(manifest_row.get("reference_text", "")),
        "backend_name": "assemblyai",
        "backend_version": ASSEMBLYAI_BACKEND_VERSION,
        "backend_kind": "cloud_asr",
        "decode_config_json": decode_json,
        "normalization_version": NORMALIZATION_VERSION,
        "local_only": False,
        "third_party_provider": "assemblyai",
        "created_at_utc": created_at,
    }
    if cached is None:
        base.update({
            "raw_transcript": None,
            "normalized_transcript": None,
            "wer": None,
            "cer": None,
            "wa": None,
            "backend_latency_ms": None,
            "server_processing_latency_ms": None,
            "end_to_end_latency_ms": None,
            "ram_peak_mb": None,
            "cost_usd": None,
            "error_or_null": "no_cache_entry",
        })
        return base
    aa = cached.get("assemblyai", {})
    raw = aa.get("text") or ""
    ref_norm = base["reference_normalized"]
    hyp_norm = normalize_text(raw)
    if aa.get("status") == "error" or not raw:
        base.update({
            "raw_transcript": raw or None,
            "normalized_transcript": hyp_norm or None,
            "wer": None,
            "cer": None,
            "wa": None,
            "backend_latency_ms": None,
            "server_processing_latency_ms": None,
            "end_to_end_latency_ms": None,
            "ram_peak_mb": None,
            "cost_usd": float(cached.get("cost_usd", 0.0)) or None,
            "error_or_null": aa.get("error") or "empty_transcript",
        })
        return base
    w = compute_wer(ref_norm, hyp_norm)
    c = compute_cer(ref_norm, hyp_norm)
    base.update({
        "raw_transcript": raw,
        "normalized_transcript": hyp_norm,
        "wer": float(w),
        "cer": float(c),
        "wa": float(compute_wa(w)),
        "backend_latency_ms": None,
        "server_processing_latency_ms": None,
        "end_to_end_latency_ms": None,
        "ram_peak_mb": None,
        "cost_usd": float(cached.get("cost_usd", 0.0)),
        "error_or_null": None,
    })
    return base


def build_rows(manifest_rows: list[dict], cache_dir: Path,
               pricing: dict) -> tuple[list[dict], int]:
    created_at = datetime.now(timezone.utc).isoformat()
    out: list[dict] = []
    missing = 0
    for mrow in manifest_rows:
        sha = mrow.get("audio_sha256")
        cache_path = cache_dir / f"{sha}.json"
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                cached = None
                missing += 1
        else:
            cached = None
            missing += 1
        out.append(_row_dict(mrow, cached, pricing, created_at))
    return out, missing


SCHEMA_PATH = REPO_ROOT / "libs" / "common" / "eval_schema.yaml"


def _arrow_schema() -> pa.Schema:
    schema_doc = yaml.safe_load(SCHEMA_PATH.read_text())
    type_map = {"string": pa.string(), "float64": pa.float64(),
                "bool": pa.bool_()}
    fields = []
    for col in schema_doc["columns"]:
        fields.append(pa.field(col["name"], type_map[col["type"]],
                               nullable=not col["required"]))
    return pa.schema(fields)


def write_parquet(rows: list[dict], out_path: Path) -> None:
    schema = _arrow_schema()
    cols: dict[str, list] = {f.name: [] for f in schema}
    for r in rows:
        for f in schema:
            cols[f.name].append(r.get(f.name))
    table = pa.table(cols, schema=schema)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--pricing-config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    manifests_doc = _load_yaml(Path(args.manifests))
    pricing = _load_yaml(Path(args.pricing_config))
    manifest_rows = collect_manifest_rows(manifests_doc)
    rows, missing = build_rows(manifest_rows, Path(args.cache_dir), pricing)
    write_parquet(rows, Path(args.out))
    print(f"OK_ASSEMBLYAI_EVAL {len(rows)} {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
