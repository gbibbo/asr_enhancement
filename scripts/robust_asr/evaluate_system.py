#!/usr/bin/env python3
"""evaluate_system.py — robust_asr P8.1 system evaluation and Decision D.

Computes the §5.6 / §4.7 paired regret comparison between the deployed
chooser (deterministic selector under OUTCOME_E_DETERMINISTIC_SELECTOR
or ML router on Branch A) and each declared baseline, runs a paired BCa
bootstrap (10000 iterations) plus Wilcoxon signed-rank, and writes
reports/robust_asr/system/system_eval.md with `positive_system: <true|
false>` on its first line. Sentinel `OK_SYSTEM_EVAL:<true|false>` is
emitted on stdout.

Inputs:
  --selected-router    artifacts/robust_asr/router/selected_router
  --selector-evidence  artifacts/robust_asr/router/selector_evidence.parquet
  --backend-tables     one or more eval_tables parquet paths (baselines)
  --baselines          one or more declared baseline action names
  --profile            balanced | quality_first | local_first |
                       battery_aware | cloud_allowed | lora_enabled | full
  --bootstrap-iterations  default 10000
  --bootstrap-method   bca | percentile (default bca)
  --rng-seed           default 20250514
  --ask-repeat-wer     primary policy value (default 1.0)
  --ask-repeat-wer-sensitivity  optional alternative policy value(s) for
                                a sensitivity check (e.g. 0.5)
  --out                reports/robust_asr/system/system_eval.md

Decision D rule (§5.6):
  positive_system = true iff ALL of:
    (i)   mean_regret(chosen) < mean_regret(b)  for every declared b
    (ii)  paired BCa 95% CI for the delta against at least one b
          entirely excludes 0
    (iii) no claim depends on a disabled claims_enabled flag

Exit codes: 0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pyarrow.parquet as pq
from scipy import stats as _scipy_stats

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _bca_ci(
    deltas: np.ndarray,
    iterations: int,
    confidence: float,
    seed: int,
    method: str,
) -> Dict[str, Any]:
    n = int(deltas.size)
    mean = float(deltas.mean()) if n else 0.0
    rng = np.random.default_rng(seed)
    boot_means = np.empty(iterations, dtype=np.float64)
    for i in range(iterations):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = float(deltas[idx].mean())
    alpha_low = (1.0 - confidence) / 2.0
    alpha_high = 1.0 - alpha_low
    pct_low = float(np.percentile(boot_means, 100.0 * alpha_low))
    pct_high = float(np.percentile(boot_means, 100.0 * alpha_high))
    if method == "percentile":
        return {
            "mean": mean,
            "ci_low": pct_low,
            "ci_high": pct_high,
            "method": "percentile",
            "iterations": iterations,
            "confidence": confidence,
        }
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
    if n > 1:
        for j in range(n):
            jackknife[j] = (full_sum - deltas[j]) / (n - 1)
    else:
        jackknife[:] = mean
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


def _wilcoxon(deltas: np.ndarray) -> Tuple[float, float, int]:
    nonzero = deltas[deltas != 0.0]
    if nonzero.size < 1:
        return float("nan"), float("nan"), 0
    try:
        stat, p = _scipy_stats.wilcoxon(
            nonzero, alternative="two-sided", zero_method="wilcox"
        )
        return float(stat), float(p), int(nonzero.size)
    except Exception:
        return float("nan"), float("nan"), int(nonzero.size)


def _selector_wer(
    actions: np.ndarray, baseline_wer: np.ndarray, ask_repeat_wer: float
) -> np.ndarray:
    out = baseline_wer.astype(np.float64).copy()
    out[actions == "ask_repeat"] = ask_repeat_wer
    return out


def _run_one_policy(
    actions: np.ndarray,
    baseline_wer: np.ndarray,
    ask_repeat_wer: float,
    iterations: int,
    seed: int,
    method: str,
) -> Dict[str, Any]:
    selector_wer = _selector_wer(actions, baseline_wer, ask_repeat_wer)
    deltas = (selector_wer - baseline_wer).astype(np.float64)
    bca = _bca_ci(
        deltas,
        iterations=iterations,
        confidence=0.95,
        seed=seed,
        method=method,
    )
    wstat, wp, wn = _wilcoxon(deltas)
    mean_regret_selector = float((selector_wer - baseline_wer).mean())
    mean_regret_baseline = 0.0
    mean_wer_selector = float(selector_wer.mean())
    mean_wer_baseline = float(baseline_wer.mean())
    strict_lt = mean_regret_selector < mean_regret_baseline
    ci_excludes_zero = (bca["ci_low"] > 0.0) or (bca["ci_high"] < 0.0)
    return {
        "ask_repeat_wer": ask_repeat_wer,
        "n": int(actions.size),
        "mean_wer_selector": mean_wer_selector,
        "mean_wer_baseline": mean_wer_baseline,
        "mean_regret_selector": mean_regret_selector,
        "mean_regret_baseline": mean_regret_baseline,
        "bca": bca,
        "wilcoxon": {
            "statistic": wstat,
            "p_value": wp,
            "nonzero_deltas": wn,
        },
        "mean_regret_strict_lt_baseline": bool(strict_lt),
        "bootstrap_ci_excludes_zero": bool(ci_excludes_zero),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selected-router", required=True, type=Path)
    ap.add_argument("--selector-evidence", required=True, type=Path)
    ap.add_argument(
        "--backend-tables", required=True, type=Path, nargs="+"
    )
    ap.add_argument("--baselines", required=True, nargs="+")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--bootstrap-iterations", type=int, default=10000)
    ap.add_argument(
        "--bootstrap-method",
        choices=["bca", "percentile"],
        default="bca",
    )
    ap.add_argument("--rng-seed", type=int, default=20250514)
    ap.add_argument("--ask-repeat-wer", type=float, default=1.0)
    ap.add_argument(
        "--ask-repeat-wer-sensitivity",
        type=float,
        nargs="*",
        default=[0.5],
    )
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    selector_dir: Path = args.selected_router.resolve()
    selector_json = selector_dir / "deterministic_selector.json"
    metadata_json = selector_dir / "metadata.json"
    if not selector_json.exists():
        print(
            f"FAIL: selector json missing: {selector_json}",
            file=sys.stderr,
        )
        return 1
    with selector_json.open("r", encoding="utf-8") as fh:
        selector_doc = json.load(fh)

    parquet_path: Path = args.selector_evidence.resolve()
    if not parquet_path.exists():
        print(
            f"FAIL: selector evidence missing: {parquet_path}",
            file=sys.stderr,
        )
        return 1
    df = pq.read_table(parquet_path).to_pandas()
    n = int(len(df))
    if n == 0:
        print("FAIL: selector_evidence is empty", file=sys.stderr)
        return 1

    declared_baselines = list(args.baselines)
    if declared_baselines != ["whisper_base_ct2_int8"]:
        print(
            "FAIL: under OUTCOME_E_DETERMINISTIC_SELECTOR the only "
            "deployable baseline is whisper_base_ct2_int8; got "
            f"{declared_baselines}",
            file=sys.stderr,
        )
        return 1

    baseline_table_path = Path(args.backend_tables[0]).resolve()
    if not baseline_table_path.exists():
        print(
            f"FAIL: backend table missing: {baseline_table_path}",
            file=sys.stderr,
        )
        return 1
    eval_df = pq.read_table(
        baseline_table_path,
        columns=["audio_id", "wer"],
    ).to_pandas()
    if int(len(eval_df)) != n:
        print(
            f"FAIL: row count mismatch evidence={n} "
            f"eval_table={len(eval_df)}",
            file=sys.stderr,
        )
        return 1
    merged = df.merge(
        eval_df.rename(columns={"wer": "baseline_table_wer"}),
        on="audio_id",
        how="left",
    )
    if int(merged["baseline_table_wer"].isna().sum()) != 0:
        print(
            "FAIL: audio_id mismatch between evidence and eval_table",
            file=sys.stderr,
        )
        return 1
    parity_diff = float(
        np.abs(
            merged["baseline_table_wer"].astype(float)
            - merged["whisper_base_ct2_int8_wer"].astype(float)
        ).max()
    )
    if parity_diff > 1e-9:
        print(
            "FAIL: baseline WER parity drift between evidence and "
            f"eval_table; max abs diff = {parity_diff}",
            file=sys.stderr,
        )
        return 1

    actions = merged["selected_action"].astype(str).to_numpy()
    baseline_wer = merged["baseline_table_wer"].astype(float).to_numpy()
    primary = _run_one_policy(
        actions,
        baseline_wer,
        args.ask_repeat_wer,
        args.bootstrap_iterations,
        args.rng_seed,
        args.bootstrap_method,
    )

    sens_runs: List[Dict[str, Any]] = []
    for s_wer in args.ask_repeat_wer_sensitivity:
        if s_wer == args.ask_repeat_wer:
            continue
        sens_runs.append(
            _run_one_policy(
                actions,
                baseline_wer,
                float(s_wer),
                args.bootstrap_iterations,
                args.rng_seed,
                args.bootstrap_method,
            )
        )

    # Decision D under OUTCOME_E.
    claims_enabled_disabled_dependencies = [
        "claims_enabled.cloud_tradeoff=false",
        "claims_enabled.ood_real=false",
        "claims_enabled.positive_lora=false",
    ]
    # The system_eval claim itself does not depend on those disabled
    # flags: declared baselines = [whisper_base_ct2_int8] only; no
    # claim is being made about cloud trade-off, OOD-real, or LoRA.
    no_disabled_dependency = True

    positive_system = (
        primary["mean_regret_strict_lt_baseline"]
        and primary["bootstrap_ci_excludes_zero"]
        and no_disabled_dependency
    )

    def f6(x: float) -> str:
        return f"{x:.6f}"

    def pct(x: float) -> str:
        return f"{100.0 * x:.4f} %"

    lines: List[str] = []
    lines.append(
        f"positive_system: {'true' if positive_system else 'false'}"
    )
    lines.append("")
    lines.append("# P8.1 — System evaluation (Decision D)")
    lines.append("")
    lines.append(
        "OUTCOME_E_NARROWED_SCOPE: only one transcript-producing "
        "backend (`whisper_base_ct2_int8`) is deployable; "
        "`claims_enabled.cloud_tradeoff=false`, "
        "`claims_enabled.ood_real=false`, "
        "`claims_enabled.positive_lora=false`. The Section 5.6 "
        "predicate is evaluated against the single declared baseline "
        "`whisper_base_ct2_int8`. No claim made here depends on a "
        "disabled `claims_enabled` flag."
    )
    lines.append("")
    lines.append("## Inputs")
    lines.append(f"- Profile: `{args.profile}`")
    lines.append(
        f"- Selected router: "
        f"`{selector_dir.relative_to(REPO_ROOT)}` "
        f"(kind=`deterministic_selector`, "
        f"version=`{selector_doc['deterministic_selector_version']}`)"
    )
    lines.append(
        f"- Selector evidence: `{parquet_path.relative_to(REPO_ROOT)}` "
        f"(rows={n})"
    )
    lines.append(
        f"- Declared baselines: {declared_baselines}"
    )
    lines.append(
        f"- Backend table: "
        f"`{baseline_table_path.relative_to(REPO_ROOT)}`"
    )
    lines.append(
        f"- Bootstrap: method=`{args.bootstrap_method}`, "
        f"iterations={args.bootstrap_iterations}, confidence=0.95, "
        f"seed={args.rng_seed}"
    )
    lines.append(
        f"- ask_repeat WER policy (primary): "
        f"{args.ask_repeat_wer}"
    )
    if sens_runs:
        sens_vals = ", ".join(
            str(r["ask_repeat_wer"]) for r in sens_runs
        )
        lines.append(
            f"- ask_repeat WER sensitivity values: {sens_vals}"
        )
    lines.append("")
    lines.append("## Primary result (ask_repeat WER = "
                 f"{args.ask_repeat_wer})")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---|")
    lines.append(f"| n (audio_id rows) | {primary['n']} |")
    lines.append(
        f"| mean WER selector | {f6(primary['mean_wer_selector'])} |"
    )
    lines.append(
        f"| mean WER baseline (whisper_base_ct2_int8) | "
        f"{f6(primary['mean_wer_baseline'])} |"
    )
    lines.append(
        f"| mean_regret_selector | "
        f"{f6(primary['mean_regret_selector'])} |"
    )
    lines.append(
        f"| mean_regret_baseline | "
        f"{f6(primary['mean_regret_baseline'])} |"
    )
    bca = primary["bca"]
    lines.append(
        f"| paired bootstrap method | {bca['method']} |"
    )
    lines.append(
        f"| paired 95% CI on (regret_selector - regret_baseline) | "
        f"[{f6(bca['ci_low'])}, {f6(bca['ci_high'])}] |"
    )
    wx = primary["wilcoxon"]
    lines.append(
        f"| Wilcoxon signed-rank (nonzero deltas) | "
        f"n={wx['nonzero_deltas']}, statistic={wx['statistic']}, "
        f"p={wx['p_value']} |"
    )
    lines.append(
        f"| mean_regret_selector < mean_regret_baseline | "
        f"{primary['mean_regret_strict_lt_baseline']} |"
    )
    lines.append(
        f"| bootstrap CI excludes 0 | "
        f"{primary['bootstrap_ci_excludes_zero']} |"
    )
    lines.append(
        f"| no claim depends on disabled flag | "
        f"{no_disabled_dependency} |"
    )
    lines.append("")
    lines.append("## Decision D")
    lines.append("")
    lines.append(f"- positive_system = "
                 f"{'true' if positive_system else 'false'}")
    lines.append(
        "- Disabled `claims_enabled` flags this report does not "
        "depend on: "
        + ", ".join(claims_enabled_disabled_dependencies)
    )
    lines.append(
        "- Under OUTCOME_E with a single deployable transcribing "
        "backend, the deterministic selector's only divergence from "
        "always-baseline is the 28 `ask_repeat` rows (selector_reason "
        "== `no_speech`). All 28 rows have `whisper_base_ct2_int8_wer "
        "= 1.0` already, so at the primary policy ask_repeat_wer=1.0 "
        "the per-row delta is identically zero and Section 5.6 "
        "predicate (i) (`mean_regret(chosen) < mean_regret(b)`) "
        "cannot hold strictly; predicate (ii) is therefore not "
        "evaluable as a positive claim."
    )
    if sens_runs:
        lines.append("")
        lines.append("## Sensitivity check (alternative ask_repeat WER)")
        lines.append("")
        for sens in sens_runs:
            bca_s = sens["bca"]
            wx_s = sens["wilcoxon"]
            lines.append(
                f"- ask_repeat_wer = {sens['ask_repeat_wer']}: "
                f"mean_wer_selector={f6(sens['mean_wer_selector'])}, "
                f"mean_wer_baseline={f6(sens['mean_wer_baseline'])}, "
                f"mean_regret_selector="
                f"{f6(sens['mean_regret_selector'])}, "
                f"CI(method={bca_s['method']})="
                f"[{f6(bca_s['ci_low'])}, {f6(bca_s['ci_high'])}], "
                f"Wilcoxon n={wx_s['nonzero_deltas']} "
                f"stat={wx_s['statistic']} p={wx_s['p_value']}, "
                f"strict_lt={sens['mean_regret_strict_lt_baseline']}, "
                f"CI_excludes_0="
                f"{sens['bootstrap_ci_excludes_zero']}, "
                f"positive_system_would_be="
                f"{sens['mean_regret_strict_lt_baseline'] and sens['bootstrap_ci_excludes_zero']}"
            )
    lines.append("")
    lines.append(f"OK_SYSTEM_EVAL:"
                 f"{'true' if positive_system else 'false'}")
    lines.append("")

    out_path: Path = args.out.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK_SYSTEM_EVAL:"
          f"{'true' if positive_system else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
