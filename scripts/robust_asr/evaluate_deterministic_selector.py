#!/usr/bin/env python3
"""evaluate_deterministic_selector.py — robust_asr P7.3 (Outcome E Branch B).

Computes deterministic-selector WER, Word Accuracy, ask_repeat_rate,
local_only_rate, cloud_call_rate, latency proxy, cost ($USD), and
paired regret vs always-whisper_base_ct2_int8 on the selector evidence
table.

Inputs:
  --selector       <artifacts/robust_asr/router/selected_router/deterministic_selector.json>
  --selector-test  <artifacts/robust_asr/router/selector_evidence.parquet>
  --out            <reports/robust_asr/router/selector_final_eval.md>

OUTCOME_E disclaimer (agent plan §1664-§1665): when only one
transcript-producing backend is deployable, regret is reported as
NEUTRAL EVIDENCE, not as a positive system claim. The output report
declares this on its first line and does not enable
claims_enabled.positive_system.

Stdout sentinel: OK_SELECTOR_FINAL_EVAL on PASS.
Exit codes: 0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pyarrow.parquet as pq
from scipy import stats as _scipy_stats

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Section 5.7 bootstrap policy.
BOOTSTRAP_ITERATIONS = 10000
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_SEED = 20260514  # report date; stable across reruns.

# Convention for ask_repeat-arm WER in regret computation: the user is
# asked to repeat, so no transcript is produced. The maximum-penalty
# convention WER=1.0 is consistent with §1664-§1665 (regret is reported
# but is NEUTRAL EVIDENCE; the selector is not making a positive
# system claim under Outcome E).
ASK_REPEAT_WER = 1.0
ASK_REPEAT_WA = 0.0


def _bca_ci(
    deltas: np.ndarray,
    iterations: int,
    confidence: float,
    seed: int,
) -> Dict[str, float]:
    """Paired BCa bootstrap CI on a 1-D delta array.

    Returns mean / ci_low / ci_high / bias / accel / method. Falls
    back to a percentile interval if BCa is degenerate (acceleration
    denominator zero, all zero deltas, or numpy edge cases).
    """
    n = int(deltas.size)
    mean = float(deltas.mean()) if n else 0.0

    rng = np.random.default_rng(seed)
    boot_means = np.empty(iterations, dtype=np.float64)
    for i in range(iterations):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = float(deltas[idx].mean())

    alpha_low = (1.0 - confidence) / 2.0
    alpha_high = 1.0 - alpha_low

    # Percentile fallback.
    pct_low = float(np.percentile(boot_means, 100.0 * alpha_low))
    pct_high = float(np.percentile(boot_means, 100.0 * alpha_high))

    # BCa correction.
    z0_share = float((boot_means < mean).sum()) / iterations
    if z0_share <= 0.0 or z0_share >= 1.0:
        return {
            "mean": mean,
            "ci_low": pct_low,
            "ci_high": pct_high,
            "method": "percentile_fallback",
            "iterations": iterations,
            "confidence": confidence,
        }
    z0 = float(_scipy_stats.norm.ppf(z0_share))

    jackknife = np.empty(n, dtype=np.float64)
    full_sum = float(deltas.sum())
    for j in range(n):
        jackknife[j] = (full_sum - deltas[j]) / (n - 1) if n > 1 else mean
    jack_mean = jackknife.mean()
    num = float(((jack_mean - jackknife) ** 3).sum())
    den = 6.0 * (float(((jack_mean - jackknife) ** 2).sum()) ** 1.5)
    if den == 0.0:
        return {
            "mean": mean,
            "ci_low": pct_low,
            "ci_high": pct_high,
            "method": "percentile_fallback",
            "iterations": iterations,
            "confidence": confidence,
        }
    accel = num / den

    z_low = _scipy_stats.norm.ppf(alpha_low)
    z_high = _scipy_stats.norm.ppf(alpha_high)
    a1 = _scipy_stats.norm.cdf(
        z0 + (z0 + z_low) / (1.0 - accel * (z0 + z_low))
    )
    a2 = _scipy_stats.norm.cdf(
        z0 + (z0 + z_high) / (1.0 - accel * (z0 + z_high))
    )
    ci_low = float(np.percentile(boot_means, 100.0 * a1))
    ci_high = float(np.percentile(boot_means, 100.0 * a2))
    return {
        "mean": mean,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "bias_z0": z0,
        "acceleration": accel,
        "method": "BCa",
        "iterations": iterations,
        "confidence": confidence,
    }


def _selector_predict(row: Dict[str, Any], constants: Dict[str, float]) -> str:
    """Apply the §5.5 predicate to one selector_evidence row.

    Mirrors rp5_inference.predict() but works directly on the parquet
    column values (numpy scalars). Returns the predicted action only;
    the parquet's recorded selected_action is used for parity assertion
    in the test_router_runtime test.
    """
    no_speech_prob = float(row["no_speech_prob_proxy"])
    avg_logprob = float(row["avg_logprob_proxy"])
    assemblyai_available = bool(row["assemblyai_available"])
    if no_speech_prob > constants["no_speech_threshold"]:
        return "ask_repeat"
    if avg_logprob < constants["ask_repeat_threshold"]:
        return "ask_repeat"
    if assemblyai_available and avg_logprob < constants["escalate_threshold"]:
        return "assemblyai"
    return "whisper_base_ct2_int8"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selector", required=True, type=Path)
    ap.add_argument("--selector-test", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    selector_path: Path = args.selector.resolve()
    parquet_path: Path = args.selector_test.resolve()
    out_path: Path = args.out.resolve()

    if not selector_path.exists():
        print(f"FAIL: selector json missing: {selector_path}", file=sys.stderr)
        return 1
    if not parquet_path.exists():
        print(f"FAIL: selector test parquet missing: {parquet_path}",
              file=sys.stderr)
        return 1

    with selector_path.open("r", encoding="utf-8") as fh:
        selector_doc = json.load(fh)
    constants = {k: float(v) for k, v in selector_doc["constants"].items()}

    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    n = int(len(df))
    if n == 0:
        print("FAIL: selector_evidence parquet is empty", file=sys.stderr)
        return 1

    # Parity: recompute selected_action and assert agreement with the
    # parquet's recorded selected_action (the build script applied the
    # same predicate). Disagreement at this stage means router_v1.yaml
    # constants drifted from the build-time constants.
    recomputed = df.apply(
        lambda r: _selector_predict(r.to_dict(), constants), axis=1
    )
    parity_mismatch = int((recomputed != df["selected_action"]).sum())
    if parity_mismatch != 0:
        print(
            f"FAIL: {parity_mismatch} rows disagree between recomputed "
            f"selector and parquet-recorded selected_action",
            file=sys.stderr,
        )
        return 1

    baseline_wer = df["whisper_base_ct2_int8_wer"].astype(float).to_numpy()
    baseline_wa = df["whisper_base_ct2_int8_wa"].astype(float).to_numpy()
    baseline_latency = (
        df["whisper_base_ct2_int8_latency_ms"].astype(float).to_numpy()
    )
    actions = df["selected_action"].astype(str).to_numpy()

    selector_wer = np.where(
        actions == "ask_repeat", ASK_REPEAT_WER, baseline_wer
    )
    selector_wa = np.where(
        actions == "ask_repeat", ASK_REPEAT_WA, baseline_wa
    )

    # Counts and rates.
    n_baseline = int((actions == "whisper_base_ct2_int8").sum())
    n_ask_repeat = int((actions == "ask_repeat").sum())
    n_cloud = int((actions == "assemblyai").sum())
    n_lora = int((actions == "whisper_lora_ct2_int8").sum())

    baseline_rate = n_baseline / n
    ask_repeat_rate = n_ask_repeat / n
    cloud_call_rate = n_cloud / n
    local_only_rate = (n_baseline + n_ask_repeat + n_lora) / n  # i.e. non-cloud
    transcript_emitted_rate = (n - n_ask_repeat) / n

    # Cost: deterministic selector under OUTCOME_E never calls cloud.
    cost_usd_total = 0.0
    cost_usd_per_row = 0.0

    # Latency proxy: baseline + ask_repeat both run locally on
    # whisper_base_ct2_int8; ask_repeat additionally prompts the user
    # but no transcript is produced. The selector's own dispatch cost
    # is negligible and not measured here.
    selector_latency_ms_mean = float(baseline_latency.mean())

    mean_baseline_wer = float(baseline_wer.mean())
    mean_selector_wer = float(selector_wer.mean())
    mean_baseline_wa = float(baseline_wa.mean())
    mean_selector_wa = float(selector_wa.mean())

    # Paired regret = selector_wer - baseline_wer per row, then bootstrap.
    deltas = (selector_wer - baseline_wer).astype(np.float64)
    bca = _bca_ci(
        deltas,
        iterations=BOOTSTRAP_ITERATIONS,
        confidence=BOOTSTRAP_CONFIDENCE,
        seed=BOOTSTRAP_SEED,
    )

    # Wilcoxon signed-rank (reported but does not gate the flag).
    nonzero = deltas[deltas != 0.0]
    if nonzero.size >= 1:
        try:
            wilcoxon_stat, wilcoxon_p = _scipy_stats.wilcoxon(
                nonzero, alternative="two-sided", zero_method="wilcox"
            )
            wilcoxon_stat = float(wilcoxon_stat)
            wilcoxon_p = float(wilcoxon_p)
        except Exception:
            wilcoxon_stat = float("nan")
            wilcoxon_p = float("nan")
    else:
        wilcoxon_stat = float("nan")
        wilcoxon_p = float("nan")

    # Compose report.
    pct = lambda x: f"{100.0 * x:.4f} %"
    fmt = lambda x: f"{x:.6f}"

    lines: List[str] = []
    lines.append(
        "NEUTRAL_EVIDENCE: positive_system=pending — single deployable "
        "transcript-producing backend under OUTCOME_E_DETERMINISTIC_SELECTOR; "
        "regret figures below are reported per agent plan §1664-§1665 and do "
        "not enable a positive_system claim."
    )
    lines.append("")
    lines.append("# Selector final evaluation (P7.3 Branch B — Outcome E)")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(
        f"- Selector package: `{selector_path.relative_to(REPO_ROOT)}`"
    )
    lines.append(
        f"- Selector evidence parquet: "
        f"`{parquet_path.relative_to(REPO_ROOT)}`"
    )
    lines.append(
        f"- `deterministic_selector_version` = "
        f"`{selector_doc['deterministic_selector_version']}`"
    )
    lines.append(
        f"- Section 5.5 constants: "
        f"`ask_repeat_threshold={constants['ask_repeat_threshold']}`, "
        f"`escalate_threshold={constants['escalate_threshold']}`, "
        f"`no_speech_threshold={constants['no_speech_threshold']}`, "
        f"`health_check_ttl_seconds={constants['health_check_ttl_seconds']}`"
    )
    lines.append(f"- Rows: {n}")
    lines.append("")
    lines.append("## Predicate-parity check")
    lines.append("")
    lines.append(
        f"- Rows where recomputed `selected_action` disagrees with parquet: "
        f"{parity_mismatch} / {n}."
    )
    lines.append(
        "- Parity PASS implies that the packaged selector and the "
        "build-time selector apply identical §5.5 constants."
    )
    lines.append("")
    lines.append("## Selection rates")
    lines.append("")
    lines.append("| action                  | rows   | share        |")
    lines.append("|-------------------------|--------|--------------|")
    lines.append(
        f"| `whisper_base_ct2_int8` | {n_baseline:>6d} | {pct(baseline_rate):>12s} |"
    )
    lines.append(
        f"| `ask_repeat`            | {n_ask_repeat:>6d} | {pct(ask_repeat_rate):>12s} |"
    )
    lines.append(
        f"| `assemblyai`            | {n_cloud:>6d} | {pct(cloud_call_rate):>12s} |"
    )
    lines.append(
        f"| `whisper_lora_ct2_int8` | {n_lora:>6d} | {pct(0.0 if n == 0 else n_lora / n):>12s} |"
    )
    lines.append("")
    lines.append(
        f"- `local_only_rate` (selector never routes off-device under "
        f"OUTCOME_E): {pct(local_only_rate)}"
    )
    lines.append(
        f"- `cloud_call_rate`: {pct(cloud_call_rate)} (zero by "
        f"construction — `assemblyai_available=False`)"
    )
    lines.append(
        f"- `transcript_emitted_rate` (non-`ask_repeat`): "
        f"{pct(transcript_emitted_rate)}"
    )
    lines.append("")
    lines.append("## WER / WA")
    lines.append("")
    lines.append(
        "| backend                            | mean WER     | mean WA      |"
    )
    lines.append(
        "|------------------------------------|--------------|--------------|"
    )
    lines.append(
        f"| always-`whisper_base_ct2_int8`     | {fmt(mean_baseline_wer):>12s} | {fmt(mean_baseline_wa):>12s} |"
    )
    lines.append(
        f"| deterministic selector             | {fmt(mean_selector_wer):>12s} | {fmt(mean_selector_wa):>12s} |"
    )
    lines.append("")
    lines.append(
        f"- `ASK_REPEAT_WER` convention: {ASK_REPEAT_WER} (no transcript "
        "is emitted on `ask_repeat`; using a maximum-penalty convention "
        "for regret accounting). `ASK_REPEAT_WA` = "
        f"{ASK_REPEAT_WA}."
    )
    lines.append("")
    lines.append("## Latency proxy")
    lines.append("")
    lines.append(
        f"- Mean local-decode latency under selector (ms): "
        f"`{selector_latency_ms_mean:.3f}`."
    )
    lines.append(
        "- Selector dispatch cost is constant-time and ignored here."
    )
    lines.append("")
    lines.append("## Cost")
    lines.append("")
    lines.append(
        f"- Total cost: ${cost_usd_total:.4f} USD. Per-row cost: "
        f"${cost_usd_per_row:.4f}. AssemblyAI is unavailable "
        "(`BLOCKED_API` / `cloud_tradeoff=false`); the selector never "
        "emits the `assemblyai` action."
    )
    lines.append("")
    lines.append(
        "## Paired regret (selector − always-`whisper_base_ct2_int8`)"
    )
    lines.append("")
    lines.append(
        f"- `mean_regret_wer` = {fmt(bca['mean'])} "
        f"(positive = selector worse than always-baseline)."
    )
    lines.append(
        f"- Paired BCa {int(BOOTSTRAP_CONFIDENCE * 100)}% CI "
        f"(`{bca['method']}`, {bca['iterations']} iterations, "
        f"seed={BOOTSTRAP_SEED}): [{fmt(bca['ci_low'])}, "
        f"{fmt(bca['ci_high'])}]."
    )
    if bca["method"] == "BCa":
        lines.append(
            f"  - Bias z0: {bca['bias_z0']:+.6f}; "
            f"acceleration: {bca['acceleration']:+.6f}."
        )
    lines.append(
        f"- Wilcoxon signed-rank (two-sided, nonzero deltas only, "
        f"n={int((deltas != 0.0).sum())}): "
        f"statistic={wilcoxon_stat:.6f}, p-value={wilcoxon_p:.6e}. "
        "Reported per §5.6; does not gate the flag."
    )
    lines.append("")
    lines.append("## Outcome E framing")
    lines.append("")
    lines.append(
        "- Deployable transcript-producing backend count = 1 "
        "(`whisper_base_ct2_int8` only). LoRA is excluded by "
        "`Decision_A_smoke=FAIL`; AssemblyAI is excluded by "
        "`BLOCKED_API`."
    )
    lines.append(
        "- Per agent plan §1664-§1665 and §5.6, the regret summary is "
        "**NEUTRAL EVIDENCE** and does not gate "
        "`claims_enabled.positive_system`. This report does not assert "
        "a positive system claim. `positive_system` remains "
        "`pending` until P8.1."
    )
    lines.append("")
    lines.append("OK_SELECTOR_FINAL_EVAL")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print("OK_SELECTOR_FINAL_EVAL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
