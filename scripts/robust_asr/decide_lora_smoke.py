#!/usr/bin/env python3
"""Decide LoRA smoke outcome from P3.1 evaluation + export results.

Implements the mechanical Section 5.1 booleans of the agent plan
(docs/plans/robust_asr_agent_plan_v3_4_7.md):

    SMOKE_PASS    = (macro_wa_gain >= 0.005 AND clean_regression <= 0.010)
                    OR (max_family_wa_gain >= 0.010 AND clean_regression <= 0.010)
    SMOKE_PARTIAL = (NOT SMOKE_PASS
                     AND max_family_wa_gain >= 0.010
                     AND clean_regression <= 0.020)
    SMOKE_FAIL    = otherwise
    HALTED        = export-input failed (EXPORT_BLOCKED).

Inputs:
    --input         reports/robust_asr/lora/lora_smoke_result.json
    --export-input  artifacts/robust_asr/lora_smoke/export_smoke_result.json
    --out           reports/robust_asr/lora/lora_smoke_report.md

Behavior:
    - On missing --input, exit 1.
    - On export-input with outcome != PASS, outcome = HALTED, marker = EXPORT_BLOCKED.
    - On degenerate evaluate file (per_family_wa_gain_variance == 0.0), outcome = FAIL.
    - Writes lora_smoke_report.md with the outcome string on its first line.
    - Emits OK_LORA_SMOKE_DECISION:<outcome> on stdout for PASS exit.

Exit codes:
    0 = success (decision rendered).
    1 = generic failure (missing/invalid input file).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SMOKE_GLOBAL_WA_GAIN_MIN = 0.005
SMOKE_FAMILY_WA_GAIN_MIN = 0.010
SMOKE_CLEAN_REGRESSION_MAX_PASS = 0.010
SMOKE_CLEAN_REGRESSION_MAX_PARTIAL = 0.020


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def decide(eval_metrics: dict, export_outcome: str) -> tuple[str, str, list[str]]:
    """Return (outcome, marker_or_empty, reasons)."""
    reasons: list[str] = []

    if export_outcome != "PASS":
        reasons.append(f"export_smoke_outcome={export_outcome} (not PASS)")
        return "HALTED", "EXPORT_BLOCKED", reasons

    variance = eval_metrics.get("per_family_wa_gain_variance", None)
    if variance is not None and float(variance) == 0.0:
        reasons.append("per_family_wa_gain_variance == 0.0 (degenerate evaluation)")
        return "FAIL", "", reasons

    macro = float(eval_metrics["macro_wa_gain"])
    max_family = float(eval_metrics["max_family_wa_gain"])
    clean_reg = float(eval_metrics["clean_wa_regression"])

    pass_branch_a = (
        macro >= SMOKE_GLOBAL_WA_GAIN_MIN
        and clean_reg <= SMOKE_CLEAN_REGRESSION_MAX_PASS
    )
    pass_branch_b = (
        max_family >= SMOKE_FAMILY_WA_GAIN_MIN
        and clean_reg <= SMOKE_CLEAN_REGRESSION_MAX_PASS
    )
    if pass_branch_a or pass_branch_b:
        reasons.append(
            f"macro_wa_gain={macro:.4f} (>={SMOKE_GLOBAL_WA_GAIN_MIN}) or "
            f"max_family_wa_gain={max_family:.4f} (>={SMOKE_FAMILY_WA_GAIN_MIN}); "
            f"clean_wa_regression={clean_reg:.4f} (<={SMOKE_CLEAN_REGRESSION_MAX_PASS})"
        )
        return "PASS", "", reasons

    partial = (
        max_family >= SMOKE_FAMILY_WA_GAIN_MIN
        and clean_reg <= SMOKE_CLEAN_REGRESSION_MAX_PARTIAL
    )
    if partial:
        reasons.append(
            f"max_family_wa_gain={max_family:.4f} (>={SMOKE_FAMILY_WA_GAIN_MIN}) AND "
            f"clean_wa_regression={clean_reg:.4f} (<={SMOKE_CLEAN_REGRESSION_MAX_PARTIAL}); "
            f"macro_wa_gain={macro:.4f} (<{SMOKE_GLOBAL_WA_GAIN_MIN})"
        )
        return "PARTIAL", "", reasons

    if macro < SMOKE_GLOBAL_WA_GAIN_MIN:
        reasons.append(
            f"macro_wa_gain={macro:.4f} < {SMOKE_GLOBAL_WA_GAIN_MIN}"
        )
    if clean_reg > SMOKE_CLEAN_REGRESSION_MAX_PASS:
        reasons.append(
            f"clean_wa_regression={clean_reg:.4f} > {SMOKE_CLEAN_REGRESSION_MAX_PASS}"
        )
    if max_family < SMOKE_FAMILY_WA_GAIN_MIN:
        reasons.append(
            f"max_family_wa_gain={max_family:.4f} < {SMOKE_FAMILY_WA_GAIN_MIN}"
        )
    if clean_reg > SMOKE_CLEAN_REGRESSION_MAX_PARTIAL:
        reasons.append(
            f"clean_wa_regression={clean_reg:.4f} > {SMOKE_CLEAN_REGRESSION_MAX_PARTIAL}"
        )
    return "FAIL", "", reasons


def render_report(
    outcome: str,
    marker: str,
    reasons: list[str],
    eval_metrics: dict,
    export_outcome: str,
    eval_path: Path,
    export_path: Path,
) -> str:
    macro = eval_metrics.get("macro_wa_gain")
    max_family = eval_metrics.get("max_family_wa_gain")
    clean_reg = eval_metrics.get("clean_wa_regression")
    variance = eval_metrics.get("per_family_wa_gain_variance")
    per_family = eval_metrics.get("per_family_wa_gain", {}) or {}

    lines: list[str] = []
    lines.append(outcome)
    lines.append("")
    lines.append("# LoRA Smoke Report")
    lines.append("")
    lines.append(f"- Outcome: {outcome}")
    if marker:
        lines.append(f"- Marker: {marker}")
    lines.append(f"- Decided at (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(f"- Evaluate input: `{eval_path}`")
    lines.append(f"- Export input:   `{export_path}` (outcome={export_outcome})")
    lines.append("")
    lines.append("## Smoke metrics")
    lines.append("")
    lines.append(f"- macro_wa_gain: {macro}")
    lines.append(f"- max_family_wa_gain: {max_family}")
    lines.append(f"- clean_wa_regression: {clean_reg}")
    lines.append(f"- per_family_wa_gain_variance: {variance}")
    lines.append("")
    if per_family:
        lines.append("## Per-family WA gain")
        lines.append("")
        for fam in sorted(per_family):
            lines.append(f"- {fam}: {per_family[fam]}")
        lines.append("")
    lines.append("## Section 5.1 thresholds")
    lines.append("")
    lines.append(f"- smoke_global_wa_gain_min        = {SMOKE_GLOBAL_WA_GAIN_MIN}")
    lines.append(f"- smoke_family_wa_gain_min        = {SMOKE_FAMILY_WA_GAIN_MIN}")
    lines.append(f"- smoke_clean_regression_max_pass = {SMOKE_CLEAN_REGRESSION_MAX_PASS}")
    lines.append(f"- smoke_clean_regression_max_partial = {SMOKE_CLEAN_REGRESSION_MAX_PARTIAL}")
    lines.append("")
    lines.append("## Reasons")
    lines.append("")
    for reason in reasons:
        lines.append(f"- {reason}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--export-input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"ERROR: --input file not found: {args.input}", file=sys.stderr)
        return 1
    if not args.export_input.exists():
        print(f"ERROR: --export-input file not found: {args.export_input}", file=sys.stderr)
        return 1

    try:
        eval_metrics = _load_json(args.input)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: failed to read {args.input}: {exc}", file=sys.stderr)
        return 1
    try:
        export_data = _load_json(args.export_input)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: failed to read {args.export_input}: {exc}", file=sys.stderr)
        return 1

    export_outcome = str(export_data.get("outcome", "")).upper() or "MISSING"

    outcome, marker, reasons = decide(eval_metrics, export_outcome)

    report = render_report(
        outcome=outcome,
        marker=marker,
        reasons=reasons,
        eval_metrics=eval_metrics,
        export_outcome=export_outcome,
        eval_path=args.input,
        export_path=args.export_input,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")

    print(f"OK_LORA_SMOKE_DECISION:{outcome}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
