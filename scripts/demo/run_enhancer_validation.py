"""B6.5.2 — validate enhancer behavior on RP5.

Runs both EnhancerAdapter subclasses on the 5 public demo examples × 6
audio variants and writes a JSON + Markdown report.

For BypassEnhancer:
    - calls enhance() per (example_id, degradation_id);
    - asserts output_path == input_path (honest passthrough);
    - asserts SHA256(input) == SHA256(enhancer-reported output);
    - transcribes the enhanced output via WhisperAdapter (faster-whisper tiny.en);
    - compares word_accuracy against the matching row in
      reports/demo/b6_5_1_rp5_results.json;
    - requires exact equality (delta_wa_vs_baseline == 0.0) on every row.

For MetricGANPlusEnhancer:
    - a single call on ex001/clean.wav must raise NotImplementedError;
    - records error_class and error_message; no 30-row run.

The runner never modifies the B6.5.1 baseline (read-only) and never writes
cache_entries. It writes its own outputs to --output (JSON) and --md
(Markdown) in a single invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Allow `python /app/scripts/demo/run_enhancer_validation.py` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from libs.audio.enhancement import BypassEnhancer, MetricGANPlusEnhancer
from libs.audio.metrics import compute_metrics
from libs.common import versions

CLEAN_DEGRADATION_ID = "clean"
DEGRADATION_IDS: tuple[str, ...] = (
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
)
ALL_VARIANT_IDS: tuple[str, ...] = (CLEAN_DEGRADATION_ID,) + DEGRADATION_IDS

ASR_ENGINE = "faster-whisper"
ASR_MODEL = "tiny.en"

WA_DECIMALS = 6
DELTA_DECIMALS = 6


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate BypassEnhancer and MetricGANPlusEnhancer on RP5.",
    )
    p.add_argument("--examples", type=Path, required=True,
                   help="Path to config/demo_examples.json")
    p.add_argument("--candidates", type=Path, required=True,
                   help="Path to config/demo_example_candidates.json")
    p.add_argument("--artifacts", type=Path, required=True,
                   help="Directory containing per-example WAV subdirectories")
    p.add_argument("--baseline-rp5", type=Path, required=True,
                   help="Path to reports/demo/b6_5_1_rp5_results.json (read-only)")
    p.add_argument("--output", type=Path, required=True,
                   help="Output JSON report path")
    p.add_argument("--md", type=Path, required=True,
                   help="Output Markdown summary path")
    p.add_argument(
        "--enhanced-output-root",
        type=Path,
        default=Path(
            "/home/gbibbo/asr_enhancement_runtime/artifacts/enhanced/b6_5_2"
        ),
        help="Root directory passed to BypassEnhancer.enhance() as output_dir",
    )
    return p.parse_args(argv)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_variant_path(example: dict, artifacts_root: Path, variant_id: str) -> Path:
    if variant_id == CLEAN_DEGRADATION_ID:
        rel = example["clean_audio_path"]
    else:
        rel = example["degraded_audio_paths"][variant_id]
    return artifacts_root / rel


def _baseline_index(baseline_payload: Any) -> dict[tuple[str, str], dict]:
    if not isinstance(baseline_payload, dict):
        raise ValueError("Baseline payload must be a JSON object")
    results = baseline_payload.get("results")
    if not isinstance(results, list):
        raise ValueError("Baseline payload missing 'results' list")
    out: dict[tuple[str, str], dict] = {}
    for row in results:
        key = (row.get("example_id"), row.get("degradation_id"))
        if all(k is not None for k in key):
            out[key] = row
    return out


class _Transcriber:
    """Lazy faster-whisper transcriber wrapper. Mirrors B6.5.1 _Transcriber."""

    def __init__(self, model_name: str = ASR_MODEL):
        self._model_name = model_name
        self._impl: Optional[Any] = None

    def transcribe(self, audio_path: Path, job_id: str) -> str:
        from libs.asr.whisper_provider import WhisperAdapter
        import os

        if self._impl is None:
            self._impl = WhisperAdapter(
                model_name=self._model_name,
                model_cache_dir=os.environ.get("WHISPER_MODEL_CACHE")
                or "/home/gbibbo/asr_enhancement_runtime/cache/whisper",
            )
        result = self._impl.transcribe(audio_path, job_id=job_id)
        return result.text


def _build_bypass_row(
    *,
    example: dict,
    candidate: dict,
    variant_id: str,
    artifacts_root: Path,
    enhanced_output_root: Path,
    transcriber: _Transcriber,
    baseline_row: Optional[dict],
) -> dict:
    audio_path = _resolve_variant_path(example, artifacts_root, variant_id)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Missing WAV: {audio_path}")

    job_id = f"{example['example_id']}-{variant_id}"
    enhancer = BypassEnhancer()
    output_dir = (
        enhanced_output_root
        / enhancer.enhancer_version
        / example["example_id"]
        / variant_id
    )

    audio_input_sha256 = _sha256_file(audio_path)

    enh_start = time.perf_counter()
    enh_result = enhancer.enhance(audio_path, output_dir, job_id)
    enh_latency = time.perf_counter() - enh_start

    enhanced_path = enh_result.output_path
    audio_enhanced_sha256 = _sha256_file(enhanced_path)
    input_equals_output = (
        enhanced_path == audio_path
        and audio_input_sha256 == audio_enhanced_sha256
    )

    asr_start = time.perf_counter()
    hypothesis = transcriber.transcribe(enhanced_path, job_id=job_id)
    asr_latency = time.perf_counter() - asr_start

    metrics = compute_metrics(hypothesis, candidate["ground_truth"])
    word_accuracy = (
        round(metrics.word_accuracy, WA_DECIMALS)
        if metrics.word_accuracy is not None
        else None
    )
    wer = round(metrics.wer, WA_DECIMALS) if metrics.wer is not None else None

    if baseline_row is not None:
        wa_baseline = baseline_row.get("word_accuracy")
    else:
        wa_baseline = None

    if word_accuracy is None or wa_baseline is None:
        delta = None
    else:
        delta = round(word_accuracy - wa_baseline, DELTA_DECIMALS)

    return {
        "example_id": example["example_id"],
        "source_recording_id": candidate["source_recording_id"],
        "degradation_id": variant_id,
        "audio_path_relative": str(
            Path(example["clean_audio_path"]).parent / audio_path.name
        ),
        "audio_input_sha256": audio_input_sha256,
        "audio_enhanced_sha256": audio_enhanced_sha256,
        "input_equals_output": input_equals_output,
        "preset_applied": enh_result.preset_applied,
        "enhanced_flag": enh_result.enhanced,
        "enhancement_fallback": enh_result.enhancement_fallback,
        "enhanced_output_path": str(enhanced_path),
        "enhance_latency_seconds": round(enh_latency, 6),
        "asr_latency_seconds": round(asr_latency, 6),
        "transcription": hypothesis,
        "wer": wer,
        "word_accuracy": word_accuracy,
        "wa_baseline_b6_5_1": wa_baseline,
        "delta_wa_vs_baseline": delta,
    }


def _aggregate_bypass(rows: list[dict]) -> dict:
    deltas = [r["delta_wa_vs_baseline"] for r in rows
              if r["delta_wa_vs_baseline"] is not None]
    abs_deltas = [abs(d) for d in deltas]
    n_nonzero = sum(1 for d in deltas if d != 0.0)
    enh_lat = [r["enhance_latency_seconds"] for r in rows]
    asr_lat = [r["asr_latency_seconds"] for r in rows]

    def _p95(values: list[float]) -> Optional[float]:
        if not values:
            return None
        ordered = sorted(values)
        # nearest-rank p95
        idx = max(0, int(round(0.95 * len(ordered))) - 1)
        return round(ordered[idx], 6)

    return {
        "n_rows": len(rows),
        "n_input_equals_output": sum(1 for r in rows if r["input_equals_output"]),
        "n_rows_with_nonzero_delta": n_nonzero,
        "max_abs_delta_wa_vs_baseline": (
            round(max(abs_deltas), DELTA_DECIMALS) if abs_deltas else None
        ),
        "mean_delta_wa_vs_baseline": (
            round(statistics.fmean(deltas), DELTA_DECIMALS) if deltas else None
        ),
        "mean_enhance_latency_seconds": (
            round(statistics.fmean(enh_lat), 6) if enh_lat else None
        ),
        "p95_enhance_latency_seconds": _p95(enh_lat),
        "mean_asr_latency_seconds": (
            round(statistics.fmean(asr_lat), 6) if asr_lat else None
        ),
        "p95_asr_latency_seconds": _p95(asr_lat),
    }


def _check_metricgan_plus(
    *,
    example: dict,
    artifacts_root: Path,
    enhanced_output_root: Path,
) -> dict:
    """Single call: must raise NotImplementedError."""
    audio_path = _resolve_variant_path(example, artifacts_root, CLEAN_DEGRADATION_ID)
    enhancer = MetricGANPlusEnhancer()
    output_dir = (
        enhanced_output_root
        / enhancer.enhancer_version
        / example["example_id"]
        / CLEAN_DEGRADATION_ID
    )
    job_id = f"{example['example_id']}-metricgan-probe"

    record: dict[str, Any] = {
        "enhancer_version": enhancer.enhancer_version,
        "probe_audio_path": str(audio_path),
        "probe_job_id": job_id,
    }
    try:
        enhancer.enhance(audio_path, output_dir, job_id)
    except NotImplementedError as exc:
        record.update(
            status="not_implemented",
            error_class="NotImplementedError",
            error_message=str(exc),
        )
        return record
    except Exception as exc:  # pragma: no cover - contract violation path
        record.update(
            status="contract_violation",
            error_class=type(exc).__name__,
            error_message=str(exc),
            traceback=traceback.format_exc(),
        )
        return record

    record.update(
        status="contract_violation",
        error_class=None,
        error_message=(
            "MetricGANPlusEnhancer.enhance() returned without raising "
            "NotImplementedError; the demo branch contract requires the hook "
            "to remain explicitly unimplemented until T4.1 is synced."
        ),
    )
    return record


def _build_decision(
    *,
    bypass_status: str,
    metricgan_status: str,
) -> dict:
    rationale_parts = [
        "MetricGAN+ wrapper is owned by T4.1 in feature/training-datamove1-v1 "
        "and is not yet synced into demo-rp5-v1. The demo branch must not "
        "implement a second MetricGAN+ wrapper (CLAUDE.md §10.4).",
    ]
    if metricgan_status == "not_implemented":
        rationale_parts.append(
            "MetricGANPlusEnhancer.enhance() correctly raises "
            "NotImplementedError, so there is no silent fallback risk."
        )
    if bypass_status == "ok":
        rationale_parts.append(
            "BypassEnhancer is an honest passthrough: enhanced output is "
            "byte-identical to the input and produces the same ASR transcripts "
            "as the B6.5.1 raw-path baseline."
        )
    return {
        "default_enhancer": "bypass",
        "rationale": " ".join(rationale_parts),
        "ui_label_for_bypass": "honest passthrough",
        "ui_label_for_metricgan_plus": "unavailable",
        "blocked_on_upstream_task": "T4.1 in feature/training-datamove1-v1",
    }


def _bypass_status(rows: list[dict], aggregates: dict) -> tuple[str, list[dict]]:
    """Return ('ok', []) or ('fail', offending_rows)."""
    offenders: list[dict] = []
    for row in rows:
        problems = []
        if not row["input_equals_output"]:
            problems.append("input!=output")
        if row["enhanced_flag"]:
            problems.append("enhanced_flag=True")
        if row["enhancement_fallback"]:
            problems.append("enhancement_fallback=True")
        delta = row["delta_wa_vs_baseline"]
        if delta is None or delta != 0.0:
            problems.append(f"delta_wa_vs_baseline={delta!r}")
        if problems:
            offenders.append({
                "example_id": row["example_id"],
                "degradation_id": row["degradation_id"],
                "problems": problems,
                "wa": row["word_accuracy"],
                "wa_baseline": row["wa_baseline_b6_5_1"],
            })

    if offenders:
        return "fail", offenders
    if aggregates.get("max_abs_delta_wa_vs_baseline") not in (0.0, None):
        return "fail", offenders
    return "ok", offenders


def _render_markdown(report: dict) -> str:
    bypass = report["enhancers"]["bypass"]
    mgp = report["enhancers"]["metricgan_plus_pretrained"]
    agg = bypass["aggregates"]

    lines: list[str] = []
    lines.append("# B6.5.2 — Enhancer Validation on RP5")
    lines.append("")
    lines.append(f"- Decision: **default_enhancer = `{report['decision']['default_enhancer']}`**")
    lines.append(f"- BypassEnhancer status: **{bypass['status']}**")
    lines.append(f"- MetricGANPlusEnhancer status: **{mgp['status']}**")
    lines.append(
        f"- ASR engine: `{report['asr_engine']}` model: `{report['asr_model']}`"
    )
    lines.append(
        f"- degradation_version: `{report['degradation_version']}`  "
        f"metrics_version: `{report['metrics_version']}`  "
        f"default_enhancer_version: `{report['default_enhancer_version']}`"
    )
    lines.append(
        f"- Host: `{report['host']}` generated_at: `{report['generated_at']}`"
    )
    lines.append(
        f"- Baseline: `{report['baseline_rp5_path']}` "
        f"(generated_at `{report.get('baseline_rp5_generated_at')}`)"
    )
    lines.append("")
    lines.append("## BypassEnhancer aggregates (30 rows)")
    lines.append("")
    lines.append(f"- n_rows: {agg['n_rows']}")
    lines.append(f"- n_input_equals_output: {agg['n_input_equals_output']}")
    lines.append(f"- n_rows_with_nonzero_delta: {agg['n_rows_with_nonzero_delta']}")
    lines.append(f"- max_abs_delta_wa_vs_baseline: {agg['max_abs_delta_wa_vs_baseline']}")
    lines.append(f"- mean_delta_wa_vs_baseline: {agg['mean_delta_wa_vs_baseline']}")
    lines.append(f"- mean_enhance_latency_seconds: {agg['mean_enhance_latency_seconds']}")
    lines.append(f"- p95_enhance_latency_seconds: {agg['p95_enhance_latency_seconds']}")
    lines.append(f"- mean_asr_latency_seconds: {agg['mean_asr_latency_seconds']}")
    lines.append(f"- p95_asr_latency_seconds: {agg['p95_asr_latency_seconds']}")
    lines.append("")
    lines.append("## MetricGANPlusEnhancer probe")
    lines.append("")
    lines.append(f"- enhancer_version: `{mgp['enhancer_version']}`")
    lines.append(f"- status: **{mgp['status']}**")
    lines.append(f"- error_class: `{mgp.get('error_class')}`")
    lines.append(f"- error_message: {mgp.get('error_message')!r}")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(f"- default_enhancer: **{report['decision']['default_enhancer']}**")
    lines.append(f"- bypass UI label: `{report['decision']['ui_label_for_bypass']}`")
    lines.append(f"- MetricGAN+ UI label: `{report['decision']['ui_label_for_metricgan_plus']}`")
    lines.append(f"- blocked_on_upstream_task: `{report['decision']['blocked_on_upstream_task']}`")
    lines.append("")
    lines.append(f"Rationale: {report['decision']['rationale']}")
    lines.append("")
    lines.append("## Per-row detail (BypassEnhancer)")
    lines.append("")
    lines.append("| example_id | degradation_id | input==output | wa | wa_baseline | delta_wa | enh_lat (s) | asr_lat (s) |")
    lines.append("|------------|----------------|---------------|----|-------------|----------|-------------|-------------|")
    for row in bypass["rows"]:
        lines.append(
            f"| {row['example_id']} | {row['degradation_id']} | "
            f"{row['input_equals_output']} | {row['word_accuracy']} | "
            f"{row['wa_baseline_b6_5_1']} | {row['delta_wa_vs_baseline']} | "
            f"{row['enhance_latency_seconds']} | {row['asr_latency_seconds']} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- DSP presets `light_clean`, `denoise`, `denoise_dereverb` are intentionally "
        "out of scope for B6.5.2; they are pipeline presets in `apply_preset()` and "
        "not `EnhancerAdapter` subclasses."
    )
    lines.append(
        "- Real MetricGAN+ inference depends on T4.1 (`feature/training-datamove1-v1`). "
        "Until that wrapper is synced into `demo-rp5-v1`, the demo runtime keeps "
        "`enhancer_version=\"bypass\"` as the honest default."
    )
    lines.append("")
    return "\n".join(lines)


def run(
    *,
    examples_path: Path,
    candidates_path: Path,
    artifacts_root: Path,
    baseline_rp5_path: Path,
    enhanced_output_root: Path,
    output_path: Path,
    md_path: Path,
) -> dict:
    examples = _load_json(examples_path)
    candidates = _load_json(candidates_path)
    if not isinstance(examples, list) or not isinstance(candidates, list):
        raise ValueError("examples and candidates must be JSON arrays")
    candidates_by_id = {c["example_id"]: c for c in candidates}

    baseline_payload = _load_json(baseline_rp5_path)
    baseline_index = _baseline_index(baseline_payload)

    transcriber = _Transcriber(model_name=ASR_MODEL)

    bypass_rows: list[dict] = []
    for example in examples:
        example_id = example["example_id"]
        if example_id not in candidates_by_id:
            raise ValueError(f"Example {example_id!r} has no matching candidate")
        candidate = candidates_by_id[example_id]
        for variant_id in ALL_VARIANT_IDS:
            baseline_row = baseline_index.get((example_id, variant_id))
            row = _build_bypass_row(
                example=example,
                candidate=candidate,
                variant_id=variant_id,
                artifacts_root=artifacts_root,
                enhanced_output_root=enhanced_output_root,
                transcriber=transcriber,
                baseline_row=baseline_row,
            )
            bypass_rows.append(row)

    aggregates = _aggregate_bypass(bypass_rows)
    bypass_status, offenders = _bypass_status(bypass_rows, aggregates)

    metricgan_record = _check_metricgan_plus(
        example=examples[0],
        artifacts_root=artifacts_root,
        enhanced_output_root=enhanced_output_root,
    )

    decision = _build_decision(
        bypass_status=bypass_status,
        metricgan_status=metricgan_record["status"],
    )

    report = {
        "task": "B6.5.2",
        "host": platform.node(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "examples_config": str(examples_path),
        "candidates_config": str(candidates_path),
        "artifacts_root": str(artifacts_root),
        "baseline_rp5_path": str(baseline_rp5_path),
        "baseline_rp5_generated_at": (
            baseline_payload.get("generated_at")
            if isinstance(baseline_payload, dict) else None
        ),
        "asr_engine": ASR_ENGINE,
        "asr_model": ASR_MODEL,
        "degradation_version": versions.DEGRADATION_VERSION,
        "metrics_version": versions.METRICS_VERSION,
        "default_enhancer_version": versions.DEFAULT_ENHANCER_VERSION,
        "scope": [e["example_id"] for e in examples],
        "variant_ids": list(ALL_VARIANT_IDS),
        "enhancers": {
            "bypass": {
                "enhancer_version": BypassEnhancer().enhancer_version,
                "status": bypass_status,
                "offenders": offenders,
                "rows": bypass_rows,
                "aggregates": aggregates,
            },
            "metricgan_plus_pretrained": metricgan_record,
        },
        "decision": decision,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    return report


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run(
        examples_path=args.examples,
        candidates_path=args.candidates,
        artifacts_root=args.artifacts,
        baseline_rp5_path=args.baseline_rp5,
        enhanced_output_root=args.enhanced_output_root,
        output_path=args.output,
        md_path=args.md,
    )
    bypass = report["enhancers"]["bypass"]
    mgp = report["enhancers"]["metricgan_plus_pretrained"]
    print(
        f"Wrote {args.output} and {args.md} — "
        f"bypass.status={bypass['status']} "
        f"bypass.rows={bypass['aggregates']['n_rows']} "
        f"max_abs_delta_wa={bypass['aggregates']['max_abs_delta_wa_vs_baseline']} "
        f"metricgan_plus.status={mgp['status']}"
    )
    if bypass["status"] != "ok":
        print(
            "FAIL: bypass status is not 'ok'. Offending rows:",
            json.dumps(bypass["offenders"], indent=2),
            file=sys.stderr,
        )
        return 1
    if mgp["status"] != "not_implemented":
        print(
            f"FAIL: MetricGANPlusEnhancer status is {mgp['status']!r}; "
            f"expected 'not_implemented'.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
