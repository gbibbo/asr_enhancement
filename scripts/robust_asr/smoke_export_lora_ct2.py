#!/usr/bin/env python3
"""smoke_export_lora_ct2.py — robust_asr §4.4 LoRA export smoke.

Merges the smoke LoRA adapter into FP16 base.en, exports to CTranslate2
INT8, loads with faster-whisper, transcribes one fixture audio file.
Records each step's success/failure and elapsed time.

Emits OK_LORA_EXPORT_SMOKE on PASS. Exit 5 with
CT2_UNSUPPORTED_VERSION_OR_OP if CTranslate2 reports unsupported.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--checkpoint", required=True, type=Path,
                    help="LoRA adapter directory (e.g. step_00200)")
    ap.add_argument("--out", required=True, type=Path,
                    help="JSON output file")
    args = ap.parse_args(argv)

    with open(args.config, "r") as fh:
        cfg = yaml.safe_load(fh)

    result: dict = {
        "checkpoint": str(args.checkpoint),
        "steps": [],
        "outcome": "FAIL",
        "created_at_utc": _utc(),
    }

    def record_step(name: str, status: str, elapsed: float, detail: dict | None = None):
        result["steps"].append(
            {"name": name, "status": status, "elapsed_seconds": round(elapsed, 2), "detail": detail or {}}
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: merge LoRA into FP16
    merged_dir = REPO_ROOT / "artifacts/robust_asr/lora_smoke/merged_fp16"
    if merged_dir.exists():
        shutil.rmtree(merged_dir)
    merged_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        from peft import PeftModel
        import torch

        base_name = os.environ.get("WHISPER_BASE_MODEL", "openai/whisper-base.en")
        processor = WhisperProcessor.from_pretrained(base_name, local_files_only=True)
        base = WhisperForConditionalGeneration.from_pretrained(base_name, local_files_only=True)
        wrapped = PeftModel.from_pretrained(base, str(args.checkpoint))
        merged = wrapped.merge_and_unload()
        merged = merged.half()
        merged.save_pretrained(str(merged_dir), safe_serialization=True)
        processor.save_pretrained(str(merged_dir))
        # Copy auxiliary tokenizer files that processor.save_pretrained may
        # not write (e.g. tokenizer.json fast-tokenizer file required by ct2).
        snapshot_dir = Path(base_name)
        if snapshot_dir.is_dir():
            for aux in ("tokenizer.json",):
                src = snapshot_dir / aux
                dst = merged_dir / aux
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)
        record_step("merge_lora_fp16", "OK", time.time() - t0,
                    {"merged_dir": str(merged_dir.relative_to(REPO_ROOT))})
    except Exception as e:
        record_step("merge_lora_fp16", "FAIL", time.time() - t0,
                    {"error": str(e), "traceback": traceback.format_exc()[-1500:]})
        with open(args.out, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
        print("merge_lora_fp16 FAIL", file=sys.stderr, flush=True)
        return 1

    # Step 2: CT2 INT8 export — Python API with patched load_model to strip
    # dtype/torch_dtype kwargs (transformers/ctranslate2 4.7.x incompatibility).
    ct2_dir = REPO_ROOT / "artifacts/robust_asr/lora_smoke/ct2_int8"
    if ct2_dir.exists():
        shutil.rmtree(ct2_dir)
    t0 = time.time()
    try:
        from ctranslate2.converters.transformers import TransformersConverter  # type: ignore

        class _PatchedConverter(TransformersConverter):
            def load_model(self, model_class, model_name_or_path, **kwargs):
                kwargs.pop("dtype", None)
                kwargs.pop("torch_dtype", None)
                return model_class.from_pretrained(model_name_or_path, local_files_only=True, **kwargs)

        copy_files = [
            "tokenizer.json", "tokenizer_config.json", "preprocessor_config.json",
            "generation_config.json", "special_tokens_map.json", "added_tokens.json",
            "merges.txt", "vocab.json",
        ]
        conv = _PatchedConverter(
            str(merged_dir),
            copy_files=copy_files,
            load_as_float16=True,
            low_cpu_mem_usage=False,
        )
        conv.convert(str(ct2_dir), quantization="int8", force=True)
        if not (ct2_dir / "model.bin").exists():
            raise RuntimeError("converter produced no model.bin")
        record_step("ct2_int8_export", "OK", time.time() - t0,
                    {"ct2_dir": str(ct2_dir.relative_to(REPO_ROOT)),
                     "model_bin_bytes": (ct2_dir / "model.bin").stat().st_size})
    except Exception as e:
        msg = str(e).lower()
        unsupported = any(m in msg for m in ("unsupported", "not supported", "unknown operator"))
        record_step("ct2_int8_export", "FAIL", time.time() - t0,
                    {"error": str(e), "traceback": traceback.format_exc()[-1500:]})
        with open(args.out, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
        if unsupported:
            print(f"CT2_UNSUPPORTED_VERSION_OR_OP: {e}", file=sys.stderr, flush=True)
            return 5
        print("ct2_int8_export FAIL", file=sys.stderr, flush=True)
        return 1

    # Step 3: faster-whisper load + one-fixture transcription
    t0 = time.time()
    try:
        # Use one row from the smoke_eval_split as a fixture (resolved from manifest)
        import pyarrow.parquet as pq

        deg_path = REPO_ROOT / "artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet"
        t = pq.read_table(str(deg_path))
        eval_audio_ids = set(cfg["smoke_eval_split"]["audio_ids"])
        fixture_path = None
        for i in range(t.num_rows):
            base_aid = t.column("audio_id")[i].as_py().split("::")[0]
            if base_aid in eval_audio_ids and t.column("condition_family")[i].as_py() == "clean":
                fixture_path = t.column("audio_path_or_uri")[i].as_py()
                break
        if fixture_path is None:
            raise RuntimeError("no clean fixture row found in smoke_eval_split")

        from faster_whisper import WhisperModel

        wm = WhisperModel(str(ct2_dir), device="cuda", compute_type="int8")
        segments, info = wm.transcribe(
            fixture_path,
            beam_size=1,
            condition_on_previous_text=False,
            without_timestamps=True,
            temperature=0.0,
            language="en",
            task="transcribe",
        )
        text_pieces: list[str] = []
        for seg in segments:
            text_pieces.append(seg.text)
        text = "".join(text_pieces).strip()
        record_step("faster_whisper_transcribe", "OK", time.time() - t0,
                    {"fixture_path": fixture_path, "transcript_excerpt": text[:200],
                     "duration_s": info.duration if hasattr(info, "duration") else None})
    except Exception as e:
        msg = str(e).lower()
        unsupported = any(m in msg for m in ("unsupported", "not supported", "unknown operator"))
        record_step("faster_whisper_transcribe", "FAIL", time.time() - t0,
                    {"error": str(e), "traceback": traceback.format_exc()[-1500:]})
        with open(args.out, "w") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
        if unsupported:
            print(f"CT2_UNSUPPORTED_VERSION_OR_OP: {e}", file=sys.stderr, flush=True)
            return 5
        return 1

    result["outcome"] = "PASS"
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)

    print("OK_LORA_EXPORT_SMOKE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
