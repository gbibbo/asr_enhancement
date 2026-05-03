"""B6.5.1 — runner for RP5 vs Surrey ASR reference comparison.

Transcribes the 5 public demo examples × 6 audio variants (clean + 5
degradations) with one of two ASR engines:

- ``--engine faster-whisper``  → ``libs.asr.whisper_provider.WhisperAdapter``
- ``--engine openai-whisper``  → top-level ``whisper`` package (Surrey only)

Writes a JSON report whose schema is the contract consumed by
``scripts/demo/compare_rp5_surrey.py``. The report stamps the frozen
``DEGRADATION_VERSION`` / ``METRICS_VERSION`` / ``DEFAULT_ENHANCER_VERSION``
read at runtime from ``libs.common.versions``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow `python /app/scripts/demo/run_reference_whisper.py` from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.audio.metrics import compute_metrics
from libs.common import versions

ENGINE_FASTER_WHISPER = "faster-whisper"
ENGINE_OPENAI_WHISPER = "openai-whisper"
SUPPORTED_ENGINES = (ENGINE_FASTER_WHISPER, ENGINE_OPENAI_WHISPER)

CLEAN_DEGRADATION_ID = "clean"
DEGRADATION_IDS: tuple[str, ...] = (
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
)
ALL_VARIANT_IDS: tuple[str, ...] = (CLEAN_DEGRADATION_ID,) + DEGRADATION_IDS


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run faster-whisper or openai-whisper on the 5 public demo examples.",
    )
    p.add_argument("--engine", choices=SUPPORTED_ENGINES, required=True)
    p.add_argument("--model", default="tiny.en")
    p.add_argument("--examples", type=Path, required=True,
                   help="Path to config/demo_examples.json")
    p.add_argument("--candidates", type=Path, required=True,
                   help="Path to config/demo_example_candidates.json")
    p.add_argument("--artifacts", type=Path, required=True,
                   help="Directory containing per-example WAV subdirectories")
    p.add_argument("--output", type=Path, required=True,
                   help="Output JSON path")
    p.add_argument("--resume", action="store_true",
                   help="Skip rows already present in --output")
    return p.parse_args(argv)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _degradation_parameters_signature() -> str:
    try:
        from libs.audio.degradations import DEGRADATION_REGISTRY
    except Exception:
        return ""
    payload = {
        deg_id: spec.params for deg_id, spec in sorted(DEGRADATION_REGISTRY.items())
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_variant_path(example: dict, artifacts_root: Path, variant_id: str) -> Path:
    if variant_id == CLEAN_DEGRADATION_ID:
        rel = example["clean_audio_path"]
    else:
        rel = example["degraded_audio_paths"][variant_id]
    return artifacts_root / rel


def _existing_rows(output_path: Path) -> dict[tuple[str, str], dict]:
    if not output_path.is_file():
        return {}
    try:
        prior = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[tuple[str, str], dict] = {}
    for row in prior.get("results", []):
        key = (row.get("example_id"), row.get("degradation_id"))
        if all(k is not None for k in key):
            out[key] = row
    return out


class _Transcriber:
    """Engine-agnostic wrapper. Returns hypothesis text for an audio path."""

    def __init__(self, engine: str, model: str):
        self._engine = engine
        self._model_name = model
        self._impl: object | None = None

    @property
    def engine(self) -> str:
        return self._engine

    @property
    def model_name(self) -> str:
        return self._model_name

    def transcribe(self, audio_path: Path, job_id: str) -> str:
        if self._engine == ENGINE_FASTER_WHISPER:
            return self._transcribe_faster_whisper(audio_path, job_id)
        if self._engine == ENGINE_OPENAI_WHISPER:
            return self._transcribe_openai_whisper(audio_path)
        raise ValueError(f"Unsupported engine: {self._engine}")

    def _transcribe_faster_whisper(self, audio_path: Path, job_id: str) -> str:
        from libs.asr.whisper_provider import WhisperAdapter

        if self._impl is None:
            self._impl = WhisperAdapter(
                model_name=self._model_name,
                model_cache_dir=os.environ.get("WHISPER_MODEL_CACHE")
                or "/home/gbibbo/asr_enhancement_runtime/cache/whisper",
            )
        result = self._impl.transcribe(audio_path, job_id=job_id)
        return result.text

    def _transcribe_openai_whisper(self, audio_path: Path) -> str:
        # Imported lazily so the runner is importable on RP5 without
        # openai-whisper installed.
        import whisper  # type: ignore[import-not-found]

        if self._impl is None:
            self._impl = whisper.load_model(self._model_name)
        result = self._impl.transcribe(str(audio_path), language="en")
        text = result.get("text", "")
        return text.strip() if isinstance(text, str) else ""


def _build_row(
    *,
    example: dict,
    candidate: dict,
    variant_id: str,
    artifacts_root: Path,
    transcriber: _Transcriber,
) -> dict:
    audio_path = _resolve_variant_path(example, artifacts_root, variant_id)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Missing WAV: {audio_path}")

    audio_sha256 = _sha256_file(audio_path)
    job_id = f"{example['example_id']}-{variant_id}"

    start = time.perf_counter()
    hypothesis = transcriber.transcribe(audio_path, job_id=job_id)
    latency = time.perf_counter() - start

    metrics = compute_metrics(hypothesis, candidate["ground_truth"])

    return {
        "example_id": example["example_id"],
        "source_recording_id": candidate["source_recording_id"],
        "degradation_id": variant_id,
        "audio_path_relative": str(
            Path(example["clean_audio_path"]).parent / audio_path.name
        ),
        "audio_sha256": audio_sha256,
        "hypothesis": hypothesis,
        "wer": round(metrics.wer, 6) if metrics.wer is not None else None,
        "word_accuracy": (
            round(metrics.word_accuracy, 6)
            if metrics.word_accuracy is not None
            else None
        ),
        "latency_seconds": round(latency, 6),
    }


def run(
    *,
    engine: str,
    model: str,
    examples_path: Path,
    candidates_path: Path,
    artifacts_root: Path,
    output_path: Path,
    resume: bool,
) -> dict:
    examples = _load_json(examples_path)
    candidates = _load_json(candidates_path)
    if not isinstance(examples, list) or not isinstance(candidates, list):
        raise ValueError("examples and candidates must be JSON arrays")

    candidates_by_id = {c["example_id"]: c for c in candidates}
    missing_candidates = [e["example_id"] for e in examples if e["example_id"] not in candidates_by_id]
    if missing_candidates:
        raise ValueError(
            f"Examples without matching candidates: {missing_candidates}"
        )

    prior_rows = _existing_rows(output_path) if resume else {}

    transcriber = _Transcriber(engine=engine, model=model)
    results: list[dict] = []

    for example in examples:
        example_id = example["example_id"]
        candidate = candidates_by_id[example_id]
        for variant_id in ALL_VARIANT_IDS:
            key = (example_id, variant_id)
            if key in prior_rows:
                results.append(prior_rows[key])
                continue
            row = _build_row(
                example=example,
                candidate=candidate,
                variant_id=variant_id,
                artifacts_root=artifacts_root,
                transcriber=transcriber,
            )
            results.append(row)

    report = {
        "engine": engine,
        "model": model,
        "host": platform.node(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "examples_config": str(examples_path),
        "candidates_config": str(candidates_path),
        "artifacts_root": str(artifacts_root),
        "degradation_version": versions.DEGRADATION_VERSION,
        "metrics_version": versions.METRICS_VERSION,
        "default_enhancer_version": versions.DEFAULT_ENHANCER_VERSION,
        "degradation_parameters_signature": _degradation_parameters_signature(),
        "scope": [e["example_id"] for e in examples],
        "variant_ids": list(ALL_VARIANT_IDS),
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run(
        engine=args.engine,
        model=args.model,
        examples_path=args.examples,
        candidates_path=args.candidates,
        artifacts_root=args.artifacts,
        output_path=args.output,
        resume=args.resume,
    )
    print(
        f"Wrote {args.output} — engine={report['engine']} model={report['model']} "
        f"rows={len(report['results'])} degradation_version={report['degradation_version']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
