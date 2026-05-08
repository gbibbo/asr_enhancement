#!/usr/bin/env python3
"""build_whisper_base_ct2_int8.py — convert openai-whisper base.en to CT2 INT8.

Pinned source: /mnt/.../cache/whisper/base.en.pt (sha256
25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead).
The script verifies the source sha256 against the canonical openai-whisper
_MODELS["base.en"] hash, then attempts conversion strategies in order:

  1. ctranslate2.converters.OpenAIWhisperConverter on the local .pt
     (offline; preferred when ctranslate2 still ships the legacy class).
  2. ct2-transformers-converter --model openai/whisper-base.en
     (HF mirror; same canonical openai-whisper base.en bytes).

Writes a provenance.json under the output directory with source sha256,
output file sha256s, ctranslate2 version, quantization, container sha256,
and Slurm job id. Emits sentinel OK_CT2_BUILD on PASS (exit 0).

Returns:
  0  PASS (OK_CT2_BUILD).
  1  FAIL_CT2_BUILD with reason.
  13 MISSING_EVIDENCE (source absent or sha256 mismatch).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CANONICAL_SHA = "25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead"
DEFAULT_SOURCE = (
    "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/"
    "cache/whisper/base.en.pt"
)
DEFAULT_OUTPUT = (
    "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/"
    "runtime/whisper_models/whisper_base_en_ct2_int8"
)
HF_MIRROR = "openai/whisper-base.en"
COPY_FILES = [
    "preprocessor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "generation_config.json",
    "vocab.json",
    "merges.txt",
    "added_tokens.json",
    "normalizer.json",
]


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fingerprint_outputs(out: Path) -> dict[str, str]:
    return {
        p.name: sha256_file(p)
        for p in sorted(out.iterdir())
        if p.is_file() and p.name != "provenance.json"
    }


def attempt_openai_whisper_converter(src: Path, out: Path, quantization: str) -> tuple[bool, str]:
    """Strategy 1 — offline conversion via ctranslate2 OpenAIWhisperConverter."""
    try:
        from ctranslate2.converters import OpenAIWhisperConverter  # type: ignore
    except (ImportError, AttributeError) as e:
        return False, f"OpenAIWhisperConverter unavailable: {type(e).__name__}: {e}"
    try:
        conv = OpenAIWhisperConverter(str(src))
        conv.convert(str(out), quantization=quantization, force=True)
    except Exception as e:  # noqa: BLE001
        return False, f"OpenAIWhisperConverter failed: {type(e).__name__}: {e}"
    if not (out / "model.bin").exists():
        return False, "OpenAIWhisperConverter produced no model.bin"
    return True, "ctranslate2.converters.OpenAIWhisperConverter (offline; local base.en.pt)"


def attempt_transformers_converter(out: Path, quantization: str) -> tuple[bool, str]:
    """Strategy 2 — TransformersConverter via HF mirror openai/whisper-base.en."""
    cmd = [
        "ct2-transformers-converter",
        "--model", HF_MIRROR,
        "--output_dir", str(out),
        "--quantization", quantization,
        "--copy_files", *COPY_FILES,
        "--force",
    ]
    print("running:", " ".join(cmd), flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout, flush=True)
    if res.stderr:
        print(res.stderr, file=sys.stderr, flush=True)
    if res.returncode != 0:
        return False, f"ct2-transformers-converter exit {res.returncode}"
    if not (out / "model.bin").exists():
        return False, "ct2-transformers-converter produced no model.bin"
    return True, f"ct2-transformers-converter --model {HF_MIRROR} (HF mirror of canonical openai-whisper base.en)"


def attempt_transformers_converter_patched(out: Path, quantization: str) -> tuple[bool, str]:
    """Strategy 3 — TransformersConverter (Python API) with `dtype` kwarg
    stripped to work around transformers/ctranslate2 incompatibility where
    ctranslate2 4.7.x passes `dtype` to `from_pretrained`, which transformers
    <4.50 forwards into the model `__init__`, raising TypeError."""
    try:
        from ctranslate2.converters.transformers import TransformersConverter  # type: ignore
    except Exception as e:  # noqa: BLE001
        return False, f"TransformersConverter import failed: {type(e).__name__}: {e}"

    class _PatchedConverter(TransformersConverter):  # type: ignore[misc]
        def load_model(self, model_class, model_name_or_path, **kwargs):
            kwargs.pop("dtype", None)
            kwargs.pop("torch_dtype", None)
            return model_class.from_pretrained(model_name_or_path, **kwargs)

    try:
        conv = _PatchedConverter(
            HF_MIRROR,
            copy_files=COPY_FILES,
            load_as_float16=False,
            low_cpu_mem_usage=False,
        )
        conv.convert(str(out), quantization=quantization, force=True)
    except Exception as e:  # noqa: BLE001
        return False, f"PatchedConverter failed: {type(e).__name__}: {e}"
    if not (out / "model.bin").exists():
        return False, "PatchedConverter produced no model.bin"
    return True, (
        "ctranslate2 TransformersConverter (Python API; patched load_model "
        "to strip `dtype`/`torch_dtype` kwargs for transformers compatibility)"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    ap.add_argument("--quantization", default="int8")
    args = ap.parse_args()

    src = Path(args.source)
    out = Path(args.output)

    if not src.exists():
        print(f"MISSING_EVIDENCE: source not found: {src}", flush=True)
        return 13
    src_sha = sha256_file(src)
    print(f"source_sha256={src_sha}", flush=True)
    print(f"canonical_sha256={CANONICAL_SHA}", flush=True)
    if src_sha != CANONICAL_SHA:
        print(
            f"MISSING_EVIDENCE: source sha256 mismatch (got {src_sha}, "
            f"expected canonical {CANONICAL_SHA}); refusing to convert.",
            flush=True,
        )
        return 13

    # Idempotency: if model.bin and provenance.json already match this source,
    # skip conversion.
    prov_path = out / "provenance.json"
    if (out / "model.bin").exists() and prov_path.exists():
        try:
            prov = json.loads(prov_path.read_text())
            if prov.get("source_sha256") == src_sha:
                print(f"already_converted={out}", flush=True)
                print("OK_CT2_BUILD", flush=True)
                return 0
        except Exception:
            pass

    out.mkdir(parents=True, exist_ok=True)
    # Clean any partial prior output without provenance match.
    for p in list(out.iterdir()):
        if p.is_file() or p.is_dir():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

    import ctranslate2  # type: ignore
    ct2_version = getattr(ctranslate2, "__version__", "unknown")
    print(f"ctranslate2_version={ct2_version}", flush=True)

    def _wipe(d: Path) -> None:
        for p in list(d.iterdir()):
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

    attempts: list[dict[str, str]] = []
    ok, note = attempt_openai_whisper_converter(src, out, args.quantization)
    attempts.append({"strategy": "OpenAIWhisperConverter", "ok": str(ok), "note": note})
    if not ok:
        _wipe(out)
        ok, note = attempt_transformers_converter(out, args.quantization)
        attempts.append({"strategy": "TransformersConverter", "ok": str(ok), "note": note})
    if not ok:
        _wipe(out)
        ok, note = attempt_transformers_converter_patched(out, args.quantization)
        attempts.append({"strategy": "TransformersConverterPatched", "ok": str(ok), "note": note})

    if not ok:
        print("FAIL_CT2_BUILD: all conversion strategies failed", file=sys.stderr)
        for a in attempts:
            print(json.dumps(a), file=sys.stderr)
        return 1

    output_files = _fingerprint_outputs(out)

    container_sha = os.environ.get("APPTAINER_CONTAINER_SHA256", "unknown")

    provenance = {
        "source_path": str(src),
        "source_sha256": src_sha,
        "source_canonical_sha256": CANONICAL_SHA,
        "source_provenance": (
            "openai-whisper base.en checkpoint; canonical sha256 from "
            "openai/whisper repository whisper/__init__.py _MODELS dict"
        ),
        "conversion_method": note,
        "conversion_attempts": attempts,
        "ctranslate2_version": ct2_version,
        "quantization": args.quantization,
        "output_dir": str(out),
        "output_files": output_files,
        "container_sha256": container_sha,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "unknown"),
        "slurm_job_name": os.environ.get("SLURM_JOB_NAME", "unknown"),
        "host": os.environ.get("HOSTNAME", os.environ.get("SLURMD_NODENAME", "unknown")),
        "built_at_utc": _utc(),
    }
    prov_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")

    print(f"output_dir={out}", flush=True)
    print(f"output_files={list(output_files.keys())}", flush=True)
    print(f"provenance={prov_path}", flush=True)
    print("OK_CT2_BUILD", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
