#!/usr/bin/env python3
"""evaluate_lora_smoke.py — robust_asr §4.4 LoRA smoke evaluation.

Loads the best-loss LoRA adapter (per checkpoint_manifest), evaluates on
the smoke_eval_split (200 base audio_ids × 5 families = 1000 rows from
degradation_v1_id_eval.parquet), computes per-family WA, macro WA gain
over Whisper base on the same audio_ids, max family WA gain, clean WA
regression. Asserts variance > 0 across families.

On degenerate variance → write lora_smoke_degenerate.md, exit 4.
Emits OK_LORA_SMOKE_EVAL on PASS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from libs.common.normalization import normalize_text  # noqa: E402
from libs.common.metrics import wer as wer_fn  # noqa: E402
from libs.common.versions import NORMALIZATION_VERSION  # noqa: E402

V347_FAMILIES = ["clean", "cafe_noise", "phone_band", "far_field_room", "muffled_lowpass"]


def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr, flush=True)
    sys.exit(code)


def wa_from_wer(w: float) -> float:
    return max(0.0, 1.0 - w)


def load_audio_mono16k_arr(path: str) -> np.ndarray:
    import soundfile as sf

    samples, sr = sf.read(path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if sr != 16000:
        import librosa

        samples = librosa.resample(samples.astype(np.float64), orig_sr=sr, target_sr=16000)
    return samples.astype(np.float32)


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--checkpoint-manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    with open(args.config, "r") as fh:
        cfg = yaml.safe_load(fh)
    with open(args.checkpoint_manifest, "r") as fh:
        manifest = json.load(fh)

    decode = cfg["eval_decode_defaults"]
    eval_timeout = int(cfg["timeouts"]["eval_timeout_seconds"])
    eval_audio_ids = list(cfg["smoke_eval_split"]["audio_ids"])
    eval_id_set = set(eval_audio_ids)

    # Load the manifest of pre-built degraded eval audio.
    import pyarrow.parquet as pq

    deg_path = REPO_ROOT / "artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet"
    table = pq.read_table(str(deg_path))
    deg_rows: list[dict] = []
    for i in range(table.num_rows):
        manifest_aid = table.column("audio_id")[i].as_py()
        base_aid = manifest_aid.split("::")[0]
        if base_aid not in eval_id_set:
            continue
        deg_id = table.column("degradation_id")[i].as_py()
        eval_aid = manifest_aid if "::" in manifest_aid else f"{base_aid}::{deg_id}"
        deg_rows.append(
            {
                "eval_audio_id": eval_aid,
                "base_audio_id": base_aid,
                "speaker_id": table.column("speaker_id")[i].as_py(),
                "utterance_id": table.column("utterance_id")[i].as_py(),
                "condition_family": table.column("condition_family")[i].as_py(),
                "degradation_id": deg_id,
                "audio_path": table.column("audio_path_or_uri")[i].as_py(),
            }
        )
    if len(deg_rows) != len(eval_id_set) * len(V347_FAMILIES):
        print(
            f"WARNING: expected {len(eval_id_set) * len(V347_FAMILIES)} deg rows, got {len(deg_rows)}",
            file=sys.stderr,
            flush=True,
        )

    # Resolve reference text from baseline parquet so we use the same source.
    base_path = REPO_ROOT / "artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet"
    base_table = pq.read_table(str(base_path))
    base_aid_col = base_table.column("audio_id").to_pylist()
    base_refs_col = base_table.column("reference_normalized").to_pylist()
    base_wer_col = base_table.column("wer").to_pylist()
    base_family_col = base_table.column("condition_family").to_pylist()
    base_lookup: dict[str, dict] = {}
    for i, aid in enumerate(base_aid_col):
        base_lookup[aid] = {
            "reference_normalized": base_refs_col[i],
            "wer": base_wer_col[i],
            "condition_family": base_family_col[i],
        }

    # Load base.en + LoRA adapter at best_step
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from peft import PeftModel

    base_name = os.environ.get("WHISPER_BASE_MODEL", manifest.get("base_model", "openai/whisper-base.en"))
    print(f"loading {base_name} ...", flush=True)
    processor = WhisperProcessor.from_pretrained(base_name, local_files_only=True)
    base_model = WhisperForConditionalGeneration.from_pretrained(base_name, local_files_only=True)
    base_model.config.forced_decoder_ids = None
    base_model.config.suppress_tokens = []

    best_step = int(manifest["best_step"])
    adapter_path = REPO_ROOT / f"artifacts/robust_asr/lora_smoke/checkpoints/step_{best_step:05d}"
    if not adapter_path.exists():
        fail(f"adapter checkpoint missing: {adapter_path}", 1)
    print(f"loading LoRA adapter at step {best_step}: {adapter_path}", flush=True)
    model = PeftModel.from_pretrained(base_model, str(adapter_path))
    model.eval()
    if not torch.cuda.is_available():
        fail("CUDA not available for eval", 1)
    device = torch.device("cuda")
    model.to(device)

    decoder_start_token_id = base_model.config.decoder_start_token_id
    # gen kwargs from Section 3 decode defaults
    gen_kwargs = dict(
        max_new_tokens=224,
        do_sample=False,
        num_beams=int(decode.get("beam_size", 1)),
        temperature=float(decode.get("temperature", 0.0)),
    )

    # Per-row evaluation
    start = time.time()
    rows: list[dict] = []
    for idx, r in enumerate(deg_rows):
        if (time.time() - start) > eval_timeout:
            fail(f"EVAL_TIMEOUT_EXCEEDED elapsed={time.time() - start:.0f}s budget={eval_timeout}s row={idx}", 1)
        try:
            samples = load_audio_mono16k_arr(r["audio_path"])
        except Exception as e:
            print(f"WARNING: audio load failed for {r['eval_audio_id']}: {e}", file=sys.stderr, flush=True)
            continue
        feat = processor.feature_extractor(samples, sampling_rate=16000, return_tensors="pt")
        input_features = feat["input_features"].to(device).to(model.dtype if hasattr(model, "dtype") else torch.float32)
        with torch.inference_mode():
            with torch.amp.autocast("cuda", dtype=torch.float16):
                gen_ids = model.generate(input_features=input_features, **gen_kwargs)
        text = processor.tokenizer.batch_decode(gen_ids, skip_special_tokens=True)[0]
        hyp_norm = normalize_text(text)
        ref_norm = base_lookup.get(r["eval_audio_id"], {}).get("reference_normalized")
        if ref_norm is None or not ref_norm:
            print(f"WARNING: missing ref for {r['eval_audio_id']}", file=sys.stderr, flush=True)
            continue
        w = wer_fn(ref_norm, hyp_norm)
        rows.append(
            {
                "eval_audio_id": r["eval_audio_id"],
                "base_audio_id": r["base_audio_id"],
                "condition_family": r["condition_family"],
                "reference_normalized": ref_norm,
                "normalized_transcript": hyp_norm,
                "wer": w,
                "wa": wa_from_wer(w),
            }
        )
        if (idx + 1) % 50 == 0:
            print(f"eval row {idx + 1}/{len(deg_rows)} elapsed={time.time() - start:.1f}s", flush=True)

    if not rows:
        fail("no eval rows produced", 1)

    # Aggregate per-family WA
    fam_wa: dict[str, list[float]] = {f: [] for f in V347_FAMILIES}
    for row in rows:
        fam_wa.setdefault(row["condition_family"], []).append(row["wa"])
    fam_wa_mean: dict[str, float] = {
        f: (float(np.mean(v)) if v else float("nan")) for f, v in fam_wa.items()
    }

    # Baseline per-family WA on the same eval_audio_ids
    base_fam_wa: dict[str, list[float]] = {f: [] for f in V347_FAMILIES}
    lora_eval_aids = {row["eval_audio_id"] for row in rows}
    for aid in lora_eval_aids:
        info = base_lookup.get(aid)
        if info is None:
            continue
        fam = info["condition_family"]
        base_fam_wa.setdefault(fam, []).append(wa_from_wer(info["wer"]))
    base_fam_wa_mean: dict[str, float] = {
        f: (float(np.mean(v)) if v else float("nan")) for f, v in base_fam_wa.items()
    }

    # Per-family WA gain
    fam_wa_gain = {
        f: (
            float(fam_wa_mean[f] - base_fam_wa_mean[f])
            if (f in fam_wa_mean and f in base_fam_wa_mean and not np.isnan(fam_wa_mean[f]) and not np.isnan(base_fam_wa_mean[f]))
            else float("nan")
        )
        for f in V347_FAMILIES
    }
    finite_gains = [v for v in fam_wa_gain.values() if not np.isnan(v)]
    macro_wa_gain = float(np.mean(finite_gains)) if finite_gains else float("nan")
    max_family_wa_gain = float(max(finite_gains)) if finite_gains else float("nan")
    fam_wa_gain_variance = float(np.var(finite_gains)) if len(finite_gains) >= 2 else 0.0

    clean_regression = (
        float(base_fam_wa_mean["clean"] - fam_wa_mean["clean"])
        if not np.isnan(fam_wa_mean.get("clean", float("nan")))
        and not np.isnan(base_fam_wa_mean.get("clean", float("nan")))
        else float("nan")
    )

    result = {
        "normalization_version": NORMALIZATION_VERSION,
        "best_step": best_step,
        "n_eval_rows": len(rows),
        "n_eval_audio_ids": len(lora_eval_aids),
        "families": V347_FAMILIES,
        "lora_per_family_wa": fam_wa_mean,
        "baseline_per_family_wa": base_fam_wa_mean,
        "per_family_wa_gain": fam_wa_gain,
        "macro_wa_gain": macro_wa_gain,
        "max_family_wa_gain": max_family_wa_gain,
        "clean_wa_regression": clean_regression,
        "per_family_wa_gain_variance": fam_wa_gain_variance,
        "eval_decode_defaults": decode,
        "created_at_utc": _utc(),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)

    # Degenerate check
    if fam_wa_gain_variance == 0.0:
        deg_path_md = REPO_ROOT / "reports/robust_asr/lora/lora_smoke_degenerate.md"
        deg_path_md.parent.mkdir(parents=True, exist_ok=True)
        with open(deg_path_md, "w") as fh:
            fh.write(
                "# LoRA smoke — DEGENERATE result\n\n"
                f"variance over families of WA gain == 0.0\n\n"
                f"per_family_wa_gain: {json.dumps(fam_wa_gain, indent=2)}\n\n"
                f"normalization_version: {NORMALIZATION_VERSION}\n"
                f"best_step: {best_step}\n"
                f"created_at_utc: {_utc()}\n"
            )
        print("DEGENERATE_SMOKE_RESULT", file=sys.stderr, flush=True)
        return 4

    print(
        f"OK_LORA_SMOKE_EVAL macro_wa_gain={macro_wa_gain:.4f} "
        f"max_family_wa_gain={max_family_wa_gain:.4f} clean_regression={clean_regression:.4f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
