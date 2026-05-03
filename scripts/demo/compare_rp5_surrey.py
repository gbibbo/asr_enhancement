"""B6.5.1 — comparator for RP5 vs Surrey ASR reference reports.

Reads two JSON reports produced by ``scripts/demo/run_reference_whisper.py``,
verifies they describe the same audio under the same frozen versions, and
emits a JSON+Markdown comparison applying the §29 decision rule:

- ``abs(degraded_mean_delta_wa) <= 0.02`` → ``"comparable"``
- ``abs(degraded_mean_delta_wa) >  0.05`` → ``"discrepant"``
- otherwise                              → ``"caution"``

The verdict is computed over **degraded rows only** (5 examples × 5
degradations = 25 rows). Clean rows are recorded as a sanity floor and may
emit an ``aux_warning`` but never change the verdict.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

CLEAN_DEGRADATION_ID = "clean"
COMPARABLE_THRESHOLD = 0.02
DISCREPANT_THRESHOLD = 0.05

VERDICT_COMPARABLE = "comparable"
VERDICT_CAUTION = "caution"
VERDICT_DISCREPANT = "discrepant"


class CompareError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Compare RP5 vs Surrey whisper reference reports (B6.5.1).",
    )
    p.add_argument("--rp5", type=Path, required=True)
    p.add_argument("--surrey", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--md", type=Path, required=True)
    return p.parse_args(argv)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_key(row: dict) -> tuple[str, str]:
    return (row["example_id"], row["degradation_id"])


def _safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def _abs(x: float | None) -> float | None:
    return abs(x) if x is not None else None


def _verdict_from(degraded_mean_delta_wa: float | None) -> str:
    if degraded_mean_delta_wa is None:
        return VERDICT_CAUTION
    abs_mean = abs(degraded_mean_delta_wa)
    if abs_mean <= COMPARABLE_THRESHOLD:
        return VERDICT_COMPARABLE
    if abs_mean > DISCREPANT_THRESHOLD:
        return VERDICT_DISCREPANT
    return VERDICT_CAUTION


def compare(rp5_report: dict, surrey_report: dict) -> dict:
    if rp5_report.get("degradation_version") != surrey_report.get("degradation_version"):
        raise CompareError(
            f"degradation_version mismatch: "
            f"rp5={rp5_report.get('degradation_version')!r} "
            f"surrey={surrey_report.get('degradation_version')!r}"
        )
    if rp5_report.get("metrics_version") != surrey_report.get("metrics_version"):
        raise CompareError(
            f"metrics_version mismatch: "
            f"rp5={rp5_report.get('metrics_version')!r} "
            f"surrey={surrey_report.get('metrics_version')!r}"
        )

    rp5_rows = {_row_key(r): r for r in rp5_report.get("results", [])}
    surrey_rows = {_row_key(r): r for r in surrey_report.get("results", [])}
    if set(rp5_rows.keys()) != set(surrey_rows.keys()):
        only_rp5 = sorted(set(rp5_rows.keys()) - set(surrey_rows.keys()))
        only_surrey = sorted(set(surrey_rows.keys()) - set(rp5_rows.keys()))
        raise CompareError(
            f"(example_id, degradation_id) row sets differ. "
            f"only_rp5={only_rp5} only_surrey={only_surrey}"
        )

    pairs: list[dict] = []
    sha_mismatches: list[tuple[str, str]] = []
    for key in sorted(rp5_rows.keys()):
        rp5 = rp5_rows[key]
        sur = surrey_rows[key]
        if rp5.get("audio_sha256") != sur.get("audio_sha256"):
            sha_mismatches.append(key)
            continue
        wa_rp5 = rp5.get("word_accuracy")
        wa_sur = sur.get("word_accuracy")
        delta = (
            wa_rp5 - wa_sur
            if isinstance(wa_rp5, (int, float)) and isinstance(wa_sur, (int, float))
            else None
        )
        pairs.append({
            "example_id": rp5["example_id"],
            "degradation_id": rp5["degradation_id"],
            "audio_sha256": rp5["audio_sha256"],
            "rp5": {
                "hypothesis": rp5.get("hypothesis"),
                "wer": rp5.get("wer"),
                "word_accuracy": wa_rp5,
                "latency_seconds": rp5.get("latency_seconds"),
            },
            "surrey": {
                "hypothesis": sur.get("hypothesis"),
                "wer": sur.get("wer"),
                "word_accuracy": wa_sur,
                "latency_seconds": sur.get("latency_seconds"),
            },
            "delta_wa": delta,
            "abs_delta_wa": abs(delta) if delta is not None else None,
        })

    if sha_mismatches:
        raise CompareError(
            f"audio_sha256 mismatch on {len(sha_mismatches)} pairs: "
            f"{sha_mismatches}. Re-source audio so both sides transcribe "
            f"identical bytes before retrying."
        )

    degraded = [p for p in pairs if p["degradation_id"] != CLEAN_DEGRADATION_ID]
    clean = [p for p in pairs if p["degradation_id"] == CLEAN_DEGRADATION_ID]

    degraded_deltas = [p["delta_wa"] for p in degraded if p["delta_wa"] is not None]
    degraded_abs_deltas = [p["abs_delta_wa"] for p in degraded if p["abs_delta_wa"] is not None]
    clean_deltas = [p["delta_wa"] for p in clean if p["delta_wa"] is not None]
    clean_abs_deltas = [p["abs_delta_wa"] for p in clean if p["abs_delta_wa"] is not None]
    all_deltas = [p["delta_wa"] for p in pairs if p["delta_wa"] is not None]

    per_degradation_lists: dict[str, list[float]] = {
        p["degradation_id"]: [] for p in degraded
    }
    for p in degraded:
        if p["delta_wa"] is not None:
            per_degradation_lists[p["degradation_id"]].append(p["delta_wa"])
    per_degradation: dict[str, float | None] = {
        k: _safe_mean(v) for k, v in per_degradation_lists.items()
    }

    degraded_mean_delta_wa = _safe_mean(degraded_deltas)
    degraded_mean_abs_delta_wa = _safe_mean(degraded_abs_deltas)
    degraded_max_abs_delta_wa = max(degraded_abs_deltas) if degraded_abs_deltas else None

    clean_mean_delta_wa = _safe_mean(clean_deltas)
    clean_max_abs_delta_wa = max(clean_abs_deltas) if clean_abs_deltas else None
    all_rows_mean_delta_wa = _safe_mean(all_deltas)

    verdict = _verdict_from(degraded_mean_delta_wa)

    aux_warnings: list[str] = []
    if (
        clean_max_abs_delta_wa is not None
        and clean_max_abs_delta_wa > COMPARABLE_THRESHOLD
    ):
        aux_warnings.append(
            f"clean_max_abs_delta_wa={clean_max_abs_delta_wa:.4f} exceeds "
            f"COMPARABLE_THRESHOLD={COMPARABLE_THRESHOLD}; RP5 and Surrey "
            f"disagree on undegraded audio, casting doubt on the degraded "
            f"comparison even though the verdict is {verdict!r}."
        )
    if (
        verdict == VERDICT_COMPARABLE
        and degraded_mean_abs_delta_wa is not None
        and degraded_mean_abs_delta_wa > DISCREPANT_THRESHOLD
    ):
        aux_warnings.append(
            f"degraded_mean_abs_delta_wa={degraded_mean_abs_delta_wa:.4f} "
            f"exceeds DISCREPANT_THRESHOLD={DISCREPANT_THRESHOLD} while the "
            f"signed mean stays under COMPARABLE_THRESHOLD; per-pair errors "
            f"may be cancelling. Investigate before relying on the verdict."
        )

    requires_model_card_update = verdict == VERDICT_DISCREPANT

    latency_total_rp5 = sum(
        (p["rp5"].get("latency_seconds") or 0.0) for p in pairs
    )
    latency_total_surrey = sum(
        (p["surrey"].get("latency_seconds") or 0.0) for p in pairs
    )

    return {
        "rp5_report": {
            "engine": rp5_report.get("engine"),
            "model": rp5_report.get("model"),
            "host": rp5_report.get("host"),
            "generated_at": rp5_report.get("generated_at"),
        },
        "surrey_report": {
            "engine": surrey_report.get("engine"),
            "model": surrey_report.get("model"),
            "host": surrey_report.get("host"),
            "generated_at": surrey_report.get("generated_at"),
        },
        "degradation_version": rp5_report.get("degradation_version"),
        "metrics_version": rp5_report.get("metrics_version"),
        "default_enhancer_version": rp5_report.get("default_enhancer_version"),
        "degradation_parameters_signature": rp5_report.get(
            "degradation_parameters_signature"
        ),
        "thresholds": {
            "COMPARABLE_THRESHOLD": COMPARABLE_THRESHOLD,
            "DISCREPANT_THRESHOLD": DISCREPANT_THRESHOLD,
        },
        "row_counts": {
            "all": len(pairs),
            "degraded": len(degraded),
            "clean": len(clean),
        },
        "primary": {
            "degraded_mean_delta_wa": degraded_mean_delta_wa,
            "degraded_mean_abs_delta_wa": degraded_mean_abs_delta_wa,
            "degraded_max_abs_delta_wa": degraded_max_abs_delta_wa,
            "degraded_per_degradation_mean_delta_wa": per_degradation,
        },
        "auxiliary": {
            "clean_mean_delta_wa": clean_mean_delta_wa,
            "clean_max_abs_delta_wa": clean_max_abs_delta_wa,
            "all_rows_mean_delta_wa": all_rows_mean_delta_wa,
            "latency_seconds_total_rp5": round(latency_total_rp5, 6),
            "latency_seconds_total_surrey": round(latency_total_surrey, 6),
        },
        "verdict": verdict,
        "requires_model_card_update": requires_model_card_update,
        "aux_warnings": aux_warnings,
        "pairs": pairs,
    }


def _fmt(v: float | None, prec: int = 4) -> str:
    return f"{v:.{prec}f}" if isinstance(v, (int, float)) else "—"


def render_markdown(comparison: dict) -> str:
    lines: list[str] = []
    lines.append("# RP5 vs Surrey Whisper Reference Comparison (B6.5.1)")
    lines.append("")
    lines.append(
        f"- Verdict: **{comparison['verdict']}**  "
        f"(thresholds: comparable ≤ {COMPARABLE_THRESHOLD}, "
        f"discrepant > {DISCREPANT_THRESHOLD})"
    )
    lines.append(f"- Requires model card update: {comparison['requires_model_card_update']}")
    lines.append(
        f"- degradation_version: `{comparison.get('degradation_version')}`  "
        f"metrics_version: `{comparison.get('metrics_version')}`  "
        f"default_enhancer_version: `{comparison.get('default_enhancer_version')}`"
    )
    rp5 = comparison["rp5_report"]
    sur = comparison["surrey_report"]
    lines.append(
        f"- RP5: engine=`{rp5.get('engine')}` model=`{rp5.get('model')}` "
        f"host=`{rp5.get('host')}` generated_at=`{rp5.get('generated_at')}`"
    )
    lines.append(
        f"- Surrey: engine=`{sur.get('engine')}` model=`{sur.get('model')}` "
        f"host=`{sur.get('host')}` generated_at=`{sur.get('generated_at')}`"
    )
    lines.append("")
    primary = comparison["primary"]
    aux = comparison["auxiliary"]
    lines.append("## Primary aggregates (25 degraded rows)")
    lines.append("")
    lines.append(f"- degraded_mean_delta_wa: {_fmt(primary['degraded_mean_delta_wa'])}")
    lines.append(f"- degraded_mean_abs_delta_wa: {_fmt(primary['degraded_mean_abs_delta_wa'])}")
    lines.append(f"- degraded_max_abs_delta_wa: {_fmt(primary['degraded_max_abs_delta_wa'])}")
    lines.append("")
    lines.append("Per degradation:")
    lines.append("")
    lines.append("| degradation_id | mean_delta_wa |")
    lines.append("|----------------|---------------|")
    for k, v in sorted(primary["degraded_per_degradation_mean_delta_wa"].items()):
        lines.append(f"| {k} | {_fmt(v)} |")
    lines.append("")
    lines.append("## Auxiliary (clean + all rows)")
    lines.append("")
    lines.append(f"- clean_mean_delta_wa: {_fmt(aux['clean_mean_delta_wa'])}")
    lines.append(f"- clean_max_abs_delta_wa: {_fmt(aux['clean_max_abs_delta_wa'])}")
    lines.append(f"- all_rows_mean_delta_wa: {_fmt(aux['all_rows_mean_delta_wa'])}")
    lines.append(
        f"- latency_seconds_total_rp5: {_fmt(aux['latency_seconds_total_rp5'])}  "
        f"latency_seconds_total_surrey: {_fmt(aux['latency_seconds_total_surrey'])}"
    )
    lines.append("")
    if comparison["aux_warnings"]:
        lines.append("## Aux warnings")
        lines.append("")
        for w in comparison["aux_warnings"]:
            lines.append(f"- {w}")
        lines.append("")
    lines.append("## Per-pair detail")
    lines.append("")
    lines.append(
        "| example_id | degradation_id | wa_rp5 | wa_surrey | delta_wa |"
    )
    lines.append("|------------|----------------|--------|-----------|----------|")
    for p in comparison["pairs"]:
        lines.append(
            f"| {p['example_id']} | {p['degradation_id']} | "
            f"{_fmt(p['rp5'].get('word_accuracy'))} | "
            f"{_fmt(p['surrey'].get('word_accuracy'))} | "
            f"{_fmt(p['delta_wa'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    rp5 = _load(args.rp5)
    surrey = _load(args.surrey)
    try:
        comparison = compare(rp5, surrey)
    except CompareError as exc:
        print(f"ERROR: {exc.message}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.md.write_text(render_markdown(comparison), encoding="utf-8")

    print(
        f"Wrote {args.output} and {args.md} — verdict={comparison['verdict']} "
        f"degraded_mean_delta_wa={comparison['primary']['degraded_mean_delta_wa']!r} "
        f"requires_model_card_update={comparison['requires_model_card_update']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
