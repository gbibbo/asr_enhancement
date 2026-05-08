#!/usr/bin/env python3
"""build_degradation_v1.py — robust_asr P1.4 §4.3 contract.

Generates ID and OOD-param degraded audio for the five Section 3 families
(clean + cafe_noise + phone_band + far_field_room + muffled_lowpass) over
the LibriSpeech eval splits and writes parquet manifests.

Outputs (under --out-manifest-root):
    degradation_v1_id_eval.parquet
    degradation_v1_ood_param_eval.parquet
    degradation_v1_<family>_<tier>.parquet           (per-family files)

Audio outputs land under <output_audio_root>/<family>/<tier>/<audio_id>.wav.
clean is identity (no audio rewritten; manifest row points at source).

Sentinel: OK_DEGRADATION_V1 on PASS, with per-family success/skip counts.
Exit:     0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from libs.audio.degradations import (  # noqa: E402
    SAMPLE_FUNCTIONS,
    V347_FAMILIES,
    DEGRADATION_VERSION,
)


_SEED_MASK = (1 << 63) - 1  # 63-bit unsigned -> fits in pyarrow int64


def _seed_for(audio_id: str, family: str, tier: str, master_seed: int) -> int:
    digest = hashlib.sha256(
        f"{DEGRADATION_VERSION}|{family}|{tier}|{audio_id}|{master_seed}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") & _SEED_MASK


def _sample_params(family: str, tier_cfg: dict, rng: np.random.Generator) -> dict:
    if family == "clean":
        return {}
    if family == "cafe_noise":
        return {
            "snr_db": float(rng.uniform(tier_cfg["snr_db_min"], tier_cfg["snr_db_max"])),
            "bandpass_low_hz": float(tier_cfg["bandpass_low_hz"]),
            "bandpass_high_hz": float(tier_cfg["bandpass_high_hz"]),
            "bandpass_order": int(tier_cfg["bandpass_order"]),
        }
    if family == "phone_band":
        return {
            "bandpass_low_hz": float(tier_cfg["bandpass_low_hz"]),
            "bandpass_high_hz": float(tier_cfg["bandpass_high_hz"]),
            "bandpass_order": int(tier_cfg["bandpass_order"]),
            "target_sr_hz": int(tier_cfg["target_sr_hz"]),
            "bit_depth": int(tier_cfg["bit_depth"]),
        }
    if family == "far_field_room":
        return {
            "rt60_s": float(rng.uniform(tier_cfg["rt60_s_min"], tier_cfg["rt60_s_max"])),
            "mic_distance_m": float(
                rng.uniform(tier_cfg["mic_distance_m_min"], tier_cfg["mic_distance_m_max"])
            ),
        }
    if family == "muffled_lowpass":
        return {
            "lowpass_hz": float(rng.uniform(tier_cfg["lowpass_hz_min"], tier_cfg["lowpass_hz_max"])),
            "attenuation_db": float(
                rng.uniform(tier_cfg["attenuation_db_min"], tier_cfg["attenuation_db_max"])
            ),
            "lowpass_order": int(tier_cfg["lowpass_order"]),
        }
    raise ValueError(f"unknown family {family!r}")


def _check_bad_output(out_path: str, rms_min: float, clip_ratio_max: float) -> tuple:
    """Return (is_bad, reason)."""
    import soundfile as sf

    samples, _sr = sf.read(out_path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if samples.size == 0:
        return True, "empty"
    if not np.isfinite(samples).all():
        return True, "non_finite"
    rms = float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))
    if rms < rms_min:
        return True, f"rms_below_min:{rms:.3e}"
    peak = float(np.max(np.abs(samples)))
    if peak > 0.0:
        clip_ratio = float(np.mean(np.abs(samples) >= 0.999))
        if clip_ratio > clip_ratio_max:
            return True, f"clipping:{clip_ratio:.3f}"
    return False, ""


def _process_one(args: tuple) -> dict:
    (
        row,
        family,
        tier,
        params,
        seed,
        output_audio_root,
        rms_min,
        clip_ratio_max,
    ) = args
    audio_id = row["audio_id"]
    src_path = row["audio_path_or_uri"]
    src_sha = row["audio_sha256"]
    if family == "clean":
        return {
            "audio_id": audio_id,
            "source_dataset": row["source_dataset"],
            "source_split": row.get("split_label", row.get("source_subset", "")),
            "speaker_id": row["speaker_id"],
            "utterance_id": row["utterance_id"],
            "condition_family": "clean",
            "tier": tier,
            "degradation_id": f"clean::{tier}",
            "audio_path_or_uri": src_path,
            "audio_sha256": src_sha,
            "duration_s": float(row["duration_s"]),
            "random_seed": int(seed),
            "snr_db": None,
            "rir_id_or_null": None,
            "filter_params_json": json.dumps({}, sort_keys=True),
            "source_audio_sha256": src_sha,
            "output_audio_sha256": src_sha,
            "bad_output": False,
            "bad_output_reason": "",
            "error_or_null": None,
        }

    out_dir = os.path.join(output_audio_root, family, tier)
    out_path = os.path.join(out_dir, f"{audio_id}.wav")
    fn = SAMPLE_FUNCTIONS[family]
    try:
        meta = fn(src_path, out_path, int(seed), params)
        is_bad, reason = _check_bad_output(out_path, rms_min, clip_ratio_max)
        return {
            "audio_id": audio_id,
            "source_dataset": row["source_dataset"],
            "source_split": row.get("split_label", row.get("source_subset", "")),
            "speaker_id": row["speaker_id"],
            "utterance_id": row["utterance_id"],
            "condition_family": family,
            "tier": tier,
            "degradation_id": f"{family}::{tier}",
            "audio_path_or_uri": out_path,
            "audio_sha256": meta["output_audio_sha256"],
            "duration_s": float(row["duration_s"]),
            "random_seed": int(meta["random_seed"]),
            "snr_db": meta["snr_db"],
            "rir_id_or_null": meta["rir_id_or_null"],
            "filter_params_json": meta["filter_params_json"],
            "source_audio_sha256": meta["source_audio_sha256"],
            "output_audio_sha256": meta["output_audio_sha256"],
            "bad_output": is_bad,
            "bad_output_reason": reason,
            "error_or_null": None,
        }
    except Exception as e:  # pylint: disable=broad-except
        return {
            "audio_id": audio_id,
            "source_dataset": row["source_dataset"],
            "source_split": row.get("split_label", row.get("source_subset", "")),
            "speaker_id": row["speaker_id"],
            "utterance_id": row["utterance_id"],
            "condition_family": family,
            "tier": tier,
            "degradation_id": f"{family}::{tier}",
            "audio_path_or_uri": "",
            "audio_sha256": "",
            "duration_s": float(row["duration_s"]),
            "random_seed": int(seed),
            "snr_db": None,
            "rir_id_or_null": None,
            "filter_params_json": json.dumps({}, sort_keys=True),
            "source_audio_sha256": src_sha,
            "output_audio_sha256": "",
            "bad_output": True,
            "bad_output_reason": f"exception:{type(e).__name__}",
            "error_or_null": f"{type(e).__name__}: {e}",
        }


def _read_manifest(path: str) -> list:
    table = pq.read_table(path)
    cols = table.column_names
    rows = []
    for batch in table.to_batches():
        d = batch.to_pydict()
        n = len(d[cols[0]])
        for i in range(n):
            rows.append({c: d[c][i] for c in cols})
    return rows


def _write_manifest(rows: list, path: str) -> str:
    columns = [
        "audio_id",
        "source_dataset",
        "source_split",
        "speaker_id",
        "utterance_id",
        "condition_family",
        "tier",
        "degradation_id",
        "audio_path_or_uri",
        "audio_sha256",
        "duration_s",
        "random_seed",
        "snr_db",
        "rir_id_or_null",
        "filter_params_json",
        "source_audio_sha256",
        "output_audio_sha256",
        "bad_output",
        "bad_output_reason",
        "error_or_null",
    ]
    arrays = {c: [r[c] for r in rows] for c in columns}
    table = pa.table(arrays)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="P1.4 build degradation_v1 manifests.")
    ap.add_argument("--config", required=True)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    audio_root = cfg["output_audio_root"]
    manifest_root = cfg["output_manifest_root"]
    families = cfg["families"]
    tiers = cfg["tiers"]
    master_seed = int(cfg["master_seed"])
    rms_min = float(cfg["bad_output"]["rms_min"])
    clip_ratio_max = float(cfg["bad_output"]["clipping_ratio_max"])
    fail_ratio_max = float(cfg["bad_output"]["per_family_fail_ratio_max"])
    required_scratch_gb = float(cfg["required_scratch_gb_min"])

    if set(families) != set(V347_FAMILIES):
        print(f"FAIL_FAMILIES_MISMATCH expected={sorted(V347_FAMILIES)} got={sorted(families)}", file=sys.stderr)
        return 1
    Path(audio_root).mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(audio_root).free / (1024 ** 3)
    if free_gb < required_scratch_gb:
        print(
            f"INSUFFICIENT_SCRATCH free_gb={free_gb:.2f} required_gb={required_scratch_gb:.2f}",
            file=sys.stderr,
        )
        return 1

    src_rows: list = []
    for src in cfg["source_manifests"]:
        rows = _read_manifest(src)
        src_rows.extend(rows)
    if not src_rows:
        print("FAIL_NO_SOURCE_ROWS", file=sys.stderr)
        return 1
    print(f"INFO source_rows={len(src_rows)} from {len(cfg['source_manifests'])} manifests")

    summary = {
        "degradation_version": DEGRADATION_VERSION,
        "source_rows": len(src_rows),
        "families": {},
        "wall_clock_s_total": None,
        "audio_root": audio_root,
        "free_gb_pre": round(free_gb, 3),
    }

    per_family_per_tier_rows: dict = {}
    t0 = time.time()
    for family in families:
        summary["families"][family] = {}
        for tier in tiers:
            tier_cfg = cfg["families_params"][family][tier]
            jobs = []
            for row in src_rows:
                seed = _seed_for(row["audio_id"], family, tier, master_seed)
                rng = np.random.default_rng(seed)
                params = _sample_params(family, tier_cfg, rng)
                jobs.append(
                    (
                        row,
                        family,
                        tier,
                        params,
                        seed,
                        audio_root,
                        rms_min,
                        clip_ratio_max,
                    )
                )
            t_fam = time.time()
            if family == "clean" or args.workers <= 1:
                results = [_process_one(j) for j in jobs]
            else:
                with mp.get_context("fork").Pool(processes=args.workers) as pool:
                    results = pool.map(_process_one, jobs, chunksize=64)
            elapsed_fam = time.time() - t_fam
            bad = sum(1 for r in results if r["bad_output"])
            err = sum(1 for r in results if r["error_or_null"] is not None)
            ratio = bad / len(results) if results else 0.0
            print(
                f"INFO family={family} tier={tier} rows={len(results)} bad={bad} err={err} "
                f"bad_ratio={ratio:.4f} elapsed_s={elapsed_fam:.2f}"
            )
            summary["families"][family][tier] = {
                "rows": len(results),
                "bad_output_count": bad,
                "error_count": err,
                "bad_output_ratio": ratio,
                "elapsed_s": round(elapsed_fam, 3),
            }
            per_family_per_tier_rows[(family, tier)] = results
            per_path = os.path.join(manifest_root, f"degradation_v1_{family}_{tier}.parquet")
            sha = _write_manifest(results, per_path)
            summary["families"][family][tier]["per_family_path"] = per_path
            summary["families"][family][tier]["per_family_sha256"] = sha
            if family != "clean" and ratio > fail_ratio_max:
                print(
                    f"FAIL_BAD_OUTPUT family={family} tier={tier} bad_ratio={ratio:.4f} "
                    f"> threshold={fail_ratio_max}",
                    file=sys.stderr,
                )
                return 1

    id_rows: list = []
    ood_rows: list = []
    for (family, tier), rows in per_family_per_tier_rows.items():
        if tier == "id":
            id_rows.extend(rows)
        else:
            ood_rows.extend(rows)
    id_path = os.path.join(manifest_root, "degradation_v1_id_eval.parquet")
    ood_path = os.path.join(manifest_root, "degradation_v1_ood_param_eval.parquet")
    id_sha = _write_manifest(id_rows, id_path)
    ood_sha = _write_manifest(ood_rows, ood_path)
    summary["id_eval_manifest"] = {"path": id_path, "sha256": id_sha, "rows": len(id_rows)}
    summary["ood_param_eval_manifest"] = {"path": ood_path, "sha256": ood_sha, "rows": len(ood_rows)}
    summary["wall_clock_s_total"] = round(time.time() - t0, 3)
    free_gb_post = shutil.disk_usage(audio_root).free / (1024 ** 3)
    summary["free_gb_post"] = round(free_gb_post, 3)
    summary["scratch_used_gb"] = round(free_gb - free_gb_post, 3)

    Path(manifest_root).mkdir(parents=True, exist_ok=True)
    summary_path = os.path.join(manifest_root, "degradation_v1_build_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    print(
        "OK_DEGRADATION_V1 "
        + " ".join(
            f"{fam}_{t}={d['rows']}/{d['bad_output_count']}"
            for fam, fams in summary["families"].items()
            for t, d in fams.items()
        )
        + f" id_rows={len(id_rows)} ood_param_rows={len(ood_rows)}"
        + f" wall_clock_s={summary['wall_clock_s_total']}"
        + f" scratch_used_gb={summary['scratch_used_gb']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
