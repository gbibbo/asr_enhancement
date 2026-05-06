"""T6.2a — deterministic dev-clean speaker-disjoint split builder.

Plan reference: docs/plans/training_datamove1_plan.md §16 (T6.2 prerequisites)
and the T6.2a sub-plan agreed on 2026-05-06.

Produces a derived training/validation split from the existing frozen
dev-clean manifests:
  - source clean manifest:
      $ASR_TRAINING_ROOT/datasets/librispeech_manifest_v1_filtered.jsonl
      sha256 dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b
  - source degraded manifest:
      $ASR_TRAINING_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl
      sha256 c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c

Policy:
  - Option B: speaker-disjoint split of dev-clean. No dataset_version bump.
    The source dataset_version stays as
    `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8`. The split is a
    derived training split identified by `training_split_version:
    devclean_speaker_split_v1`.
  - Reserved public demo utterance IDs (10) must already be absent from
    the source manifests; the script asserts this and records the result.
  - Architecture: this script is independent of the trainable enhancer
    architecture. The architecture decision (`spectral_unet_small_v1`) is
    recorded in `configs/training/full_training.yaml` separately.

Output (under --out-dir, by default
`$ASR_TRAINING_ROOT/datasets/splits/devclean_speaker_split_v1/`):
  - train_speakers.txt
  - val_speakers.txt
  - train_clean_manifest.jsonl
  - val_clean_manifest.jsonl
  - train_degraded_manifest.jsonl
  - val_degraded_manifest.jsonl
  - split_summary.json

This script does NOT submit Slurm, run training, run Whisper, run
enhancement, modify `train_enhancer.py`, modify `dataset_version.yaml`,
modify `dry_run.yaml`, or touch the model card. It is a pure metadata
helper. It runs on the datamove1 login node (stdlib + pyyaml only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Iterable

import yaml

EXPECTED_FAMILIES = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)

EXPECTED_CLEAN_SHA256 = (
    "dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b"
)
EXPECTED_DEGRADED_SHA256 = (
    "c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c"
)
SOURCE_DATASET_VERSION = "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8"
TRAINING_SPLIT_VERSION = "devclean_speaker_split_v1"


def _blocker(msg: str) -> int:
    print(f"BLOCKER: {msg}", file=sys.stderr)
    return 2


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl_sorted(rows: Iterable[dict], path: Path, sort_keys: tuple[str, ...]) -> None:
    sorted_rows = sorted(rows, key=lambda r: tuple(r.get(k, "") for k in sort_keys))
    with path.open("w", encoding="utf-8") as f:
        for r in sorted_rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def _load_reserved_utterance_ids(reserved_yaml: Path) -> list[str]:
    if not reserved_yaml.exists():
        raise FileNotFoundError(f"reserved demo IDs yaml not found: {reserved_yaml}")
    cfg = yaml.safe_load(reserved_yaml.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError(f"reserved demo yaml not a mapping: {reserved_yaml}")
    examples = cfg.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError(f"reserved demo yaml has no 'examples' list: {reserved_yaml}")
    ids: list[str] = []
    for entry in examples:
        if not isinstance(entry, dict) or "utterance_id" not in entry:
            raise ValueError(f"reserved demo entry missing utterance_id: {entry!r}")
        ids.append(str(entry["utterance_id"]))
    return ids


def _split_speakers(speakers: list[str], val_fraction: float, seed: int) -> tuple[list[str], list[str]]:
    speakers_sorted = sorted(speakers)
    rng = random.Random(seed)
    rng.shuffle(speakers_sorted)
    n_total = len(speakers_sorted)
    n_val = max(1, int(round(val_fraction * n_total)))
    n_train = n_total - n_val
    if n_train <= 0:
        raise ValueError(
            f"speaker split leaves no training speakers: total={n_total}, val={n_val}"
        )
    train = sorted(speakers_sorted[:n_train])
    val = sorted(speakers_sorted[n_train:])
    return train, val


def _per_family_counts(rows: list[dict]) -> dict[str, int]:
    out = {fam: 0 for fam in EXPECTED_FAMILIES}
    for r in rows:
        fam = r.get("family")
        if fam in out:
            out[fam] += 1
    return out


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "T6.2a — build deterministic dev-clean speaker-disjoint split "
            "(devclean_speaker_split_v1)."
        )
    )
    p.add_argument("--source-clean-manifest", type=Path, required=True)
    p.add_argument("--source-degraded-manifest", type=Path, required=True)
    p.add_argument("--reserved-yaml", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--val-fraction", type=float, default=0.20)
    p.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting existing split artifacts in --out-dir.",
    )
    p.add_argument(
        "--skip-source-sha-check",
        action="store_true",
        help=(
            "Skip the strict source manifest SHA-256 check. Use only for "
            "synthetic-manifest tests; production runs must NOT skip."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))

    clean_path: Path = args.source_clean_manifest
    degraded_path: Path = args.source_degraded_manifest
    reserved_yaml: Path = args.reserved_yaml
    out_dir: Path = args.out_dir
    seed: int = int(args.seed)
    val_fraction: float = float(args.val_fraction)
    force: bool = bool(args.force)
    skip_source_sha_check: bool = bool(args.skip_source_sha_check)

    if not clean_path.exists():
        return _blocker(f"source clean manifest not found: {clean_path}")
    if not degraded_path.exists():
        return _blocker(f"source degraded manifest not found: {degraded_path}")
    if not reserved_yaml.exists():
        return _blocker(f"reserved demo yaml not found: {reserved_yaml}")
    if not (0.0 < val_fraction < 1.0):
        return _blocker(f"val-fraction must be in (0,1): got {val_fraction}")

    clean_sha = _sha256_of_file(clean_path)
    degraded_sha = _sha256_of_file(degraded_path)
    if not skip_source_sha_check:
        if clean_sha != EXPECTED_CLEAN_SHA256:
            return _blocker(
                f"source clean manifest sha256 mismatch: expected="
                f"{EXPECTED_CLEAN_SHA256} actual={clean_sha} path={clean_path}"
            )
        if degraded_sha != EXPECTED_DEGRADED_SHA256:
            return _blocker(
                f"source degraded manifest sha256 mismatch: expected="
                f"{EXPECTED_DEGRADED_SHA256} actual={degraded_sha} path={degraded_path}"
            )

    try:
        reserved_ids = set(_load_reserved_utterance_ids(reserved_yaml))
    except (FileNotFoundError, ValueError) as exc:
        return _blocker(f"reserved demo IDs: {exc}")
    if not reserved_ids:
        return _blocker("reserved demo IDs set is empty")

    clean_rows = _read_jsonl(clean_path)
    degraded_rows = _read_jsonl(degraded_path)
    if not clean_rows:
        return _blocker(f"source clean manifest is empty: {clean_path}")
    if not degraded_rows:
        return _blocker(f"source degraded manifest is empty: {degraded_path}")

    clean_uids = {r.get("utterance_id") for r in clean_rows}
    degraded_uids = {r.get("utterance_id") for r in degraded_rows}
    leaked_clean = sorted(reserved_ids & clean_uids)
    leaked_degraded = sorted(reserved_ids & degraded_uids)
    if leaked_clean:
        return _blocker(
            f"reserved demo IDs present in source clean manifest: {leaked_clean}"
        )
    if leaked_degraded:
        return _blocker(
            f"reserved demo IDs present in source degraded manifest: {leaked_degraded}"
        )

    speakers = sorted({str(r.get("speaker_id")) for r in clean_rows if r.get("speaker_id") is not None})
    if not speakers:
        return _blocker("no speaker_id values in source clean manifest")

    train_speakers, val_speakers = _split_speakers(speakers, val_fraction, seed)
    overlap = sorted(set(train_speakers) & set(val_speakers))
    if overlap:
        return _blocker(f"speaker overlap is not empty: {overlap}")

    train_speaker_set = set(train_speakers)
    val_speaker_set = set(val_speakers)

    train_clean_rows = [r for r in clean_rows if str(r.get("speaker_id")) in train_speaker_set]
    val_clean_rows = [r for r in clean_rows if str(r.get("speaker_id")) in val_speaker_set]
    train_degraded_rows = [r for r in degraded_rows if str(r.get("speaker_id")) in train_speaker_set]
    val_degraded_rows = [r for r in degraded_rows if str(r.get("speaker_id")) in val_speaker_set]

    if len(train_clean_rows) + len(val_clean_rows) != len(clean_rows):
        return _blocker(
            "clean record partition does not cover the source manifest "
            f"(train={len(train_clean_rows)} val={len(val_clean_rows)} "
            f"source={len(clean_rows)})"
        )
    if len(train_degraded_rows) + len(val_degraded_rows) != len(degraded_rows):
        return _blocker(
            "degraded record partition does not cover the source manifest "
            f"(train={len(train_degraded_rows)} val={len(val_degraded_rows)} "
            f"source={len(degraded_rows)})"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "train_speakers_txt": out_dir / "train_speakers.txt",
        "val_speakers_txt": out_dir / "val_speakers.txt",
        "train_clean_manifest": out_dir / "train_clean_manifest.jsonl",
        "val_clean_manifest": out_dir / "val_clean_manifest.jsonl",
        "train_degraded_manifest": out_dir / "train_degraded_manifest.jsonl",
        "val_degraded_manifest": out_dir / "val_degraded_manifest.jsonl",
        "split_summary_json": out_dir / "split_summary.json",
    }
    if not force:
        existing = [str(p) for p in paths.values() if p.exists()]
        if existing:
            return _blocker(
                "split artifacts already exist (use --force to overwrite): "
                f"{existing}"
            )

    paths["train_speakers_txt"].write_text(
        "\n".join(train_speakers) + ("\n" if train_speakers else ""),
        encoding="utf-8",
    )
    paths["val_speakers_txt"].write_text(
        "\n".join(val_speakers) + ("\n" if val_speakers else ""),
        encoding="utf-8",
    )
    _write_jsonl_sorted(train_clean_rows, paths["train_clean_manifest"], ("utterance_id",))
    _write_jsonl_sorted(val_clean_rows, paths["val_clean_manifest"], ("utterance_id",))
    _write_jsonl_sorted(
        train_degraded_rows,
        paths["train_degraded_manifest"],
        ("utterance_id", "family"),
    )
    _write_jsonl_sorted(
        val_degraded_rows,
        paths["val_degraded_manifest"],
        ("utterance_id", "family"),
    )

    train_clean_sha = _sha256_of_file(paths["train_clean_manifest"])
    val_clean_sha = _sha256_of_file(paths["val_clean_manifest"])
    train_degraded_sha = _sha256_of_file(paths["train_degraded_manifest"])
    val_degraded_sha = _sha256_of_file(paths["val_degraded_manifest"])

    train_train_uids = {r.get("utterance_id") for r in train_clean_rows} | {
        r.get("utterance_id") for r in train_degraded_rows
    }
    val_val_uids = {r.get("utterance_id") for r in val_clean_rows} | {
        r.get("utterance_id") for r in val_degraded_rows
    }
    reserved_in_train = sorted(reserved_ids & train_train_uids)
    reserved_in_val = sorted(reserved_ids & val_val_uids)
    if reserved_in_train:
        return _blocker(
            f"reserved demo IDs leaked into train split: {reserved_in_train}"
        )
    if reserved_in_val:
        return _blocker(
            f"reserved demo IDs leaked into val split: {reserved_in_val}"
        )

    summary = {
        "training_split_version": TRAINING_SPLIT_VERSION,
        "source_dataset_version": SOURCE_DATASET_VERSION,
        "source_clean_manifest": str(clean_path),
        "source_clean_manifest_sha256": clean_sha,
        "source_clean_manifest_records": len(clean_rows),
        "source_degraded_manifest": str(degraded_path),
        "source_degraded_manifest_sha256": degraded_sha,
        "source_degraded_manifest_records": len(degraded_rows),
        "seed": seed,
        "val_fraction_target": val_fraction,
        "speaker_count_total": len(speakers),
        "train_speaker_count": len(train_speakers),
        "val_speaker_count": len(val_speakers),
        "speaker_overlap": overlap,
        "reserved_demo_ids_count": len(reserved_ids),
        "reserved_demo_ids_absent_in_source_clean": True,
        "reserved_demo_ids_absent_in_source_degraded": True,
        "reserved_demo_ids_absent_in_train": True,
        "reserved_demo_ids_absent_in_val": True,
        "train_speakers_txt": str(paths["train_speakers_txt"]),
        "val_speakers_txt": str(paths["val_speakers_txt"]),
        "train_clean_manifest": str(paths["train_clean_manifest"]),
        "train_clean_manifest_sha256": train_clean_sha,
        "train_clean_records": len(train_clean_rows),
        "val_clean_manifest": str(paths["val_clean_manifest"]),
        "val_clean_manifest_sha256": val_clean_sha,
        "val_clean_records": len(val_clean_rows),
        "train_degraded_manifest": str(paths["train_degraded_manifest"]),
        "train_degraded_manifest_sha256": train_degraded_sha,
        "train_degraded_records": len(train_degraded_rows),
        "val_degraded_manifest": str(paths["val_degraded_manifest"]),
        "val_degraded_manifest_sha256": val_degraded_sha,
        "val_degraded_records": len(val_degraded_rows),
        "per_family_train_counts": _per_family_counts(train_degraded_rows),
        "per_family_val_counts": _per_family_counts(val_degraded_rows),
    }
    paths["split_summary_json"].write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        "OK: split written "
        f"(train_speakers={len(train_speakers)} val_speakers={len(val_speakers)} "
        f"train_clean={len(train_clean_rows)} val_clean={len(val_clean_rows)} "
        f"train_degraded={len(train_degraded_rows)} val_degraded={len(val_degraded_rows)} "
        f"families={len(EXPECTED_FAMILIES)} "
        f"out_dir={out_dir})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
