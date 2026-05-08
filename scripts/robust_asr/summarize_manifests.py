#!/usr/bin/env python3
"""Summarize public dataset manifests under --manifest-root.

Per agent plan v3.4.7 Section 4.3 / Section 9 P1.3.

Inputs:
  --manifest-root <dir>
  --out <md>
  [--data-config <yaml>]   # optional; informs OOD claim status

Behavior:
  Reads every *.parquet under --manifest-root. For each, computes
  row count, sum(duration_s), distinct speaker count, and parquet
  byte sha256. Writes a markdown summary to --out and reports the
  OOD-real claim status (`enabled` / `disabled (BLOCKED_OOD_PUBLIC)`)
  derived from --data-config.ood_real if provided.

Stdout:
  OK_MANIFEST_SUMMARY on PASS.

Exit:
  0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
import yaml


def sha256_of_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            buf = fh.read(chunk_size)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def summarize_one(parquet_path: Path) -> dict:
    table = pq.read_table(parquet_path)
    cols = table.column_names
    n_rows = table.num_rows
    duration_total = 0.0
    if "duration_s" in cols and n_rows > 0:
        duration_total = float(sum(table.column("duration_s").to_pylist()))
    speakers = set()
    if "speaker_id" in cols and n_rows > 0:
        speakers = set(table.column("speaker_id").to_pylist())
    return {
        "path": parquet_path,
        "rows": n_rows,
        "duration_s": duration_total,
        "speakers": len(speakers),
        "columns": cols,
        "sha256": sha256_of_file(parquet_path),
        "size_bytes": parquet_path.stat().st_size,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--data-config", type=Path, default=None)
    args = ap.parse_args()

    if not args.manifest_root.is_dir():
        print(
            f"FAIL_MANIFEST_SUMMARY manifest_root_absent={args.manifest_root}",
            file=sys.stderr,
        )
        return 1

    parquets = sorted(args.manifest_root.glob("*.parquet"))
    if not parquets:
        print(
            f"FAIL_MANIFEST_SUMMARY no_parquets_under={args.manifest_root}",
            file=sys.stderr,
        )
        return 1

    summaries: list[dict] = []
    for p in parquets:
        try:
            summaries.append(summarize_one(p))
        except Exception as exc:  # noqa: BLE001
            print(
                f"FAIL_MANIFEST_SUMMARY parquet={p} error={exc}",
                file=sys.stderr,
            )
            return 1

    # OOD claim status.
    ood_status = "unknown"
    ood_reason = ""
    if args.data_config is not None and args.data_config.is_file():
        with args.data_config.open("r") as fh:
            cfg = yaml.safe_load(fh)
        ood_blocked = bool(cfg.get("ood_real", {}).get("blocked", False))
        if ood_blocked:
            ood_status = "disabled (BLOCKED_OOD_PUBLIC)"
            ood_reason = (cfg.get("ood_real", {}).get("blocked_reason") or "").strip()
        else:
            ood_status = "enabled"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append("# Robust ASR — Public Manifest Summary")
    lines.append("")
    lines.append(f"Produced by: P1.3 (`scripts/robust_asr/summarize_manifests.py`)")
    lines.append(f"Generated at: {now}")
    lines.append(f"Manifest root: `{args.manifest_root}`")
    lines.append(f"OOD-real claim status: **{ood_status}**")
    if ood_reason:
        lines.append("")
        lines.append(f"OOD-real reason: {ood_reason}")
    lines.append("")
    lines.append("## Per-manifest summary")
    lines.append("")
    lines.append("| Manifest | Rows | Speakers | Duration (s) | Duration (h) | Bytes | sha256 |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")
    total_rows = 0
    total_duration = 0.0
    for s in summaries:
        rel = s["path"].name
        hours = s["duration_s"] / 3600.0
        lines.append(
            f"| `{rel}` | {s['rows']} | {s['speakers']} | "
            f"{s['duration_s']:.2f} | {hours:.4f} | {s['size_bytes']} | "
            f"`{s['sha256']}` |"
        )
        total_rows += s["rows"]
        total_duration += s["duration_s"]
    lines.append("")
    lines.append(f"**Total rows:** {total_rows}")
    lines.append(f"**Total duration (s):** {total_duration:.2f}")
    lines.append(f"**Total duration (h):** {total_duration / 3600.0:.4f}")
    lines.append("")
    lines.append("## Columns")
    lines.append("")
    for s in summaries:
        lines.append(f"- `{s['path'].name}`: {', '.join(s['columns'])}")
    lines.append("")
    args.out.write_text("\n".join(lines) + "\n")

    print(
        f"OK_MANIFEST_SUMMARY parquets={len(summaries)} total_rows={total_rows} "
        f"total_duration_s={total_duration:.2f} ood_status='{ood_status}' "
        f"out={args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
