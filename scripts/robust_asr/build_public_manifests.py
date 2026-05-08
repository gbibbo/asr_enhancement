#!/usr/bin/env python3
"""Build public dataset manifests for the splits declared in data_v1.yaml.

Per agent plan v3.4.7 Section 4.3 / Section 9 P1.3.

Inputs:
  --config <configs/robust_asr/data_v1.yaml>
  --out-root <artifacts/robust_asr/manifests>
  [--workers <int>]
  [--dry-run]

Behavior:
  Reads dataset roots from --config. For every declared split whose
  source_dataset root resolves on host, walks the relevant LibriSpeech
  subset and writes one parquet manifest per <dataset>_<split> with
  columns:

      audio_id          : "<dataset>/<subset>/<speaker>-<chapter>-<utt>"
      source_dataset    : e.g. "librispeech"
      source_subset     : e.g. "train-clean-100"
      speaker_id        : LibriSpeech speaker dir name (string)
      chapter_id        : LibriSpeech chapter dir name (string)
      utterance_id      : <speaker>-<chapter>-<utt>
      audio_path_or_uri : absolute local path
      audio_sha256      : sha256 of audio bytes
      duration_s        : float64, soundfile.info(...).duration
      sample_rate       : int32 (LibriSpeech is 16 kHz; recorded for audit)
      num_frames        : int64
      split_label       : robust_asr split label (lora_train, ..., locked_test)

  Splits whose source_dataset root does not resolve on host (OOD-real,
  Common Voice demo reservation) are skipped with explicit
  BLOCKED_OOD_PUBLIC notation on stdout. The script halts (exit 1) only
  if a *required* LibriSpeech split has no resolvable rows.

Outputs:
  <out-root>/<dataset>_<split>.parquet (one per resolvable split)

Stdout:
  Per-split status line plus, on PASS:
    OK_PUBLIC_MANIFESTS dataset=<...> ...

Exit:
  0 on PASS (LibriSpeech splits non-empty; OOD-real may be skipped),
  1 on FAIL.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import soundfile as sf
import yaml


REQUIRED_LIBRISPEECH_SPLITS = ("lora_train", "router_train", "validation", "locked_test")
OOD_OR_DEMO_SPLITS = ("ood_real_locked", "common_voice_demo_reserved")


def sha256_of_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            buf = fh.read(chunk_size)
            if not buf:
                break
            h.update(buf)
    return h.hexdigest()


def probe_audio(path: Path) -> tuple[float, int, int]:
    info = sf.info(str(path))
    duration = float(info.frames) / float(info.samplerate)
    return duration, int(info.samplerate), int(info.frames)


def collect_speaker_files(subset_root: Path, speaker_id: int) -> list[Path]:
    spk_dir = subset_root / str(speaker_id)
    if not spk_dir.is_dir():
        return []
    files: list[Path] = []
    for chapter_dir in sorted(spk_dir.iterdir()):
        if not chapter_dir.is_dir():
            continue
        files.extend(sorted(chapter_dir.glob("*.flac")))
    return files


def build_one_row(audio_path: Path, dataset: str, subset: str, split_label: str) -> dict:
    name = audio_path.stem  # e.g. 26-495-0000
    parts = name.split("-")
    if len(parts) != 3:
        raise ValueError(f"Unexpected LibriSpeech filename layout: {audio_path}")
    speaker_id, chapter_id, utt_id = parts
    duration_s, sample_rate, num_frames = probe_audio(audio_path)
    audio_sha256 = sha256_of_file(audio_path)
    audio_id = f"{dataset}/{subset}/{speaker_id}-{chapter_id}-{utt_id}"
    return {
        "audio_id": audio_id,
        "source_dataset": dataset,
        "source_subset": subset,
        "speaker_id": speaker_id,
        "chapter_id": chapter_id,
        "utterance_id": f"{speaker_id}-{chapter_id}-{utt_id}",
        "audio_path_or_uri": str(audio_path),
        "audio_sha256": audio_sha256,
        "duration_s": duration_s,
        "sample_rate": sample_rate,
        "num_frames": num_frames,
        "split_label": split_label,
    }


MANIFEST_SCHEMA = pa.schema(
    [
        ("audio_id", pa.string()),
        ("source_dataset", pa.string()),
        ("source_subset", pa.string()),
        ("speaker_id", pa.string()),
        ("chapter_id", pa.string()),
        ("utterance_id", pa.string()),
        ("audio_path_or_uri", pa.string()),
        ("audio_sha256", pa.string()),
        ("duration_s", pa.float64()),
        ("sample_rate", pa.int32()),
        ("num_frames", pa.int64()),
        ("split_label", pa.string()),
    ]
)


def write_parquet(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=MANIFEST_SCHEMA)
    pq.write_table(table, out_path, compression="zstd")


def build_librispeech_split(
    cfg: dict,
    split_label: str,
    out_root: Path,
    workers: int,
    dry_run: bool,
) -> dict:
    split_cfg = cfg["splits"][split_label]
    dataset_key = split_cfg["source_dataset"]
    subset_name = split_cfg["source_subset"]
    speakers = list(split_cfg["speakers"])

    dataset_cfg = cfg["datasets"][dataset_key]
    root = Path(dataset_cfg["root"])
    subset_root = root / subset_name

    if not subset_root.is_dir():
        return {
            "split": split_label,
            "dataset": dataset_key,
            "subset": subset_name,
            "status": "FAIL_SUBSET_ABSENT",
            "rows": 0,
            "speakers": 0,
            "duration_s": 0.0,
            "out_path": None,
        }

    files: list[tuple[Path, str]] = []
    speakers_with_audio: set[str] = set()
    for spk in speakers:
        spk_files = collect_speaker_files(subset_root, spk)
        if spk_files:
            speakers_with_audio.add(str(spk))
            for f in spk_files:
                files.append((f, split_label))

    if not files:
        return {
            "split": split_label,
            "dataset": dataset_key,
            "subset": subset_name,
            "status": "FAIL_EMPTY_SPLIT",
            "rows": 0,
            "speakers": 0,
            "duration_s": 0.0,
            "out_path": None,
        }

    if dry_run:
        return {
            "split": split_label,
            "dataset": dataset_key,
            "subset": subset_name,
            "status": "DRY_RUN",
            "rows": len(files),
            "speakers": len(speakers_with_audio),
            "duration_s": 0.0,
            "out_path": None,
        }

    rows: list[dict] = []

    def _build(item):
        path, label = item
        return build_one_row(path, dataset_key, subset_name, label)

    if workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for row in ex.map(_build, files, chunksize=64):
                rows.append(row)
    else:
        for item in files:
            rows.append(_build(item))

    rows.sort(key=lambda r: r["audio_id"])

    out_path = out_root / f"{dataset_key}_{split_label}.parquet"
    write_parquet(rows, out_path)

    duration_total = sum(r["duration_s"] for r in rows)
    return {
        "split": split_label,
        "dataset": dataset_key,
        "subset": subset_name,
        "status": "OK",
        "rows": len(rows),
        "speakers": len({r["speaker_id"] for r in rows}),
        "duration_s": duration_total,
        "out_path": str(out_path),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument(
        "--out-root",
        type=Path,
        default=Path("artifacts/robust_asr/manifests"),
    )
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with args.config.open("r") as fh:
        cfg = yaml.safe_load(fh)

    args.out_root.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    failures: list[str] = []

    # Process required LibriSpeech splits.
    for split_label in REQUIRED_LIBRISPEECH_SPLITS:
        if split_label not in cfg.get("splits", {}):
            failures.append(f"split missing in config: {split_label}")
            continue
        res = build_librispeech_split(
            cfg, split_label, args.out_root, args.workers, args.dry_run
        )
        results.append(res)
        if res["status"].startswith("FAIL"):
            failures.append(f"{split_label}: {res['status']}")
        line = (
            f"split={res['split']:<22} dataset={res['dataset']:<12} "
            f"subset={res['subset']:<18} status={res['status']:<14} "
            f"rows={res['rows']:>6} speakers={res['speakers']:>4} "
            f"duration_s={res['duration_s']:.2f}"
        )
        print(line)

    # Process OOD-real / demo-reserved splits: skip if dataset root is absent
    # or split is empty per data_v1.yaml.
    ood_real_blocked = bool(cfg.get("ood_real", {}).get("blocked", False))
    for split_label in OOD_OR_DEMO_SPLITS:
        scfg = cfg.get("splits", {}).get(split_label)
        if scfg is None:
            print(f"split={split_label:<22} status=ABSENT_FROM_CONFIG")
            continue
        ds_key = scfg.get("source_dataset")
        if ds_key is None:
            print(
                f"split={split_label:<22} status=SKIPPED_OOD_PUBLIC_DEFERRED "
                f"reason=no_source_dataset_selected ood_real_blocked={ood_real_blocked}"
            )
            results.append(
                {"split": split_label, "status": "SKIPPED_OOD_PUBLIC_DEFERRED",
                 "rows": 0, "speakers": 0, "duration_s": 0.0,
                 "reason": "no_source_dataset_selected"}
            )
            continue
        ds_cfg = cfg["datasets"].get(ds_key, {})
        present = bool(ds_cfg.get("present_on_host", False))
        speakers = scfg.get("speakers") or []
        if not present or not speakers:
            print(
                f"split={split_label:<22} dataset={ds_key:<12} "
                f"status=SKIPPED_OOD_PUBLIC_DEFERRED "
                f"reason=root_absent_or_empty present_on_host={present} "
                f"declared_speakers={len(speakers)} "
                f"ood_real_blocked={ood_real_blocked}"
            )
            results.append(
                {"split": split_label, "status": "SKIPPED_OOD_PUBLIC_DEFERRED",
                 "rows": 0, "speakers": 0, "duration_s": 0.0,
                 "reason": "root_absent_or_empty"}
            )
            continue
        # Otherwise we'd build it; treat as out-of-scope for P1.3 today.
        print(
            f"split={split_label:<22} dataset={ds_key:<12} "
            f"status=SKIPPED_OOD_PUBLIC_DEFERRED reason=p1_3_no_ood_build"
        )
        results.append(
            {"split": split_label, "status": "SKIPPED_OOD_PUBLIC_DEFERRED",
             "rows": 0, "speakers": 0, "duration_s": 0.0,
             "reason": "p1_3_no_ood_build"}
        )

    # Decision rules.
    librispeech_ok = all(
        r["status"] == "OK" and r["rows"] > 0
        for r in results
        if r.get("dataset") == "librispeech"
    )
    if not librispeech_ok or failures:
        print(f"FAIL_PUBLIC_MANIFESTS reasons={failures}", file=sys.stderr)
        return 1

    summary = {
        "results": [
            {k: v for k, v in r.items() if k != "out_path"}
            for r in results
        ]
    }
    print(
        f"OK_PUBLIC_MANIFESTS librispeech_splits=4 "
        f"ood_skipped={sum(1 for r in results if r['status']=='SKIPPED_OOD_PUBLIC_DEFERRED')} "
        f"summary={json.dumps(summary)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
