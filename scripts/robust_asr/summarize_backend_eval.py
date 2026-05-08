#!/usr/bin/env python3
"""summarize_backend_eval.py — robust_asr §4.2 backend summary."""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

import pyarrow.parquet as pq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"FAIL: input not found: {in_path}", file=sys.stderr)
        return 1
    table = pq.read_table(in_path)
    n = table.num_rows
    cols = {c: table.column(c).to_pylist() for c in table.column_names}

    rows_failed = sum(1 for e in cols["error_or_null"] if e)
    norm_versions = sorted({v for v in cols["normalization_version"] if v})
    backend_names = sorted({v for v in cols["backend_name"] if v})
    backend_versions = sorted({v for v in cols["backend_version"] if v})

    def _by_family(metric: str):
        agg: dict[str, list[float]] = {}
        for fam, val, err in zip(cols["condition_family"], cols[metric], cols["error_or_null"]):
            if err or val is None:
                continue
            agg.setdefault(fam, []).append(float(val))
        return {f: (statistics.mean(v) if v else None, len(v)) for f, v in agg.items()}

    fam_wer = _by_family("wer")
    fam_wa = _by_family("wa")

    lat_total = sum(v for v in cols["end_to_end_latency_ms"] if v is not None)
    cost_total = sum(v for v in cols["cost_usd"] if v is not None)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        f.write(f"# Baseline summary: {','.join(backend_names)}\n\n")
        f.write(f"- rows: {n}\n")
        f.write(f"- rows_failed: {rows_failed}\n")
        f.write(f"- backend_versions: {backend_versions}\n")
        f.write(f"- normalization_versions: {norm_versions}\n")
        f.write(f"- total_end_to_end_latency_ms: {lat_total:.1f}\n")
        f.write(f"- total_cost_usd: {cost_total:.4f}\n\n")
        f.write("## Per-family WER / WA (mean over successful rows)\n\n")
        f.write("| family | n | mean_WER | mean_WA |\n")
        f.write("|--------|---|----------|---------|\n")
        for fam in sorted(set(fam_wer) | set(fam_wa)):
            wer_mean, n_w = fam_wer.get(fam, (None, 0))
            wa_mean, _ = fam_wa.get(fam, (None, 0))
            wer_s = f"{wer_mean:.4f}" if wer_mean is not None else "n/a"
            wa_s = f"{wa_mean:.4f}" if wa_mean is not None else "n/a"
            f.write(f"| {fam} | {n_w} | {wer_s} | {wa_s} |\n")
    print(f"summary={out}", flush=True)
    print("OK_BACKEND_SUMMARY", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
