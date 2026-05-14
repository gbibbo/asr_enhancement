positive_system: false

# P8.1 — System evaluation (Decision D)

OUTCOME_E_NARROWED_SCOPE: only one transcript-producing backend (`whisper_base_ct2_int8`) is deployable; `claims_enabled.cloud_tradeoff=false`, `claims_enabled.ood_real=false`, `claims_enabled.positive_lora=false`. The Section 5.6 predicate is evaluated against the single declared baseline `whisper_base_ct2_int8`. No claim made here depends on a disabled `claims_enabled` flag.

## Inputs
- Profile: `battery_aware`
- Selected router: `artifacts/robust_asr/router/selected_router` (kind=`deterministic_selector`, version=`deterministic_selector_v1`)
- Selector evidence: `artifacts/robust_asr/router/selector_evidence.parquet` (rows=53230)
- Declared baselines: ['whisper_base_ct2_int8']
- Backend table: `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`
- Bootstrap: method=`bca`, iterations=10000, confidence=0.95, seed=20250514
- ask_repeat WER policy (primary): 1.0
- ask_repeat WER sensitivity values: 0.5

## Primary result (ask_repeat WER = 1.0)

| metric | value |
|---|---|
| n (audio_id rows) | 53230 |
| mean WER selector | 0.209797 |
| mean WER baseline (whisper_base_ct2_int8) | 0.209797 |
| mean_regret_selector | 0.000000 |
| mean_regret_baseline | 0.000000 |
| paired bootstrap method | percentile_fallback |
| paired 95% CI on (regret_selector - regret_baseline) | [0.000000, 0.000000] |
| Wilcoxon signed-rank (nonzero deltas) | n=0, statistic=nan, p=nan |
| mean_regret_selector < mean_regret_baseline | False |
| bootstrap CI excludes 0 | False |
| no claim depends on disabled flag | True |

## Decision D

- positive_system = false
- Disabled `claims_enabled` flags this report does not depend on: claims_enabled.cloud_tradeoff=false, claims_enabled.ood_real=false, claims_enabled.positive_lora=false
- Under OUTCOME_E with a single deployable transcribing backend, the deterministic selector's only divergence from always-baseline is the 28 `ask_repeat` rows (selector_reason == `no_speech`). All 28 rows have `whisper_base_ct2_int8_wer = 1.0` already, so at the primary policy ask_repeat_wer=1.0 the per-row delta is identically zero and Section 5.6 predicate (i) (`mean_regret(chosen) < mean_regret(b)`) cannot hold strictly; predicate (ii) is therefore not evaluable as a positive claim.

## Sensitivity check (alternative ask_repeat WER)

- ask_repeat_wer = 0.5: mean_wer_selector=0.209534, mean_wer_baseline=0.209797, mean_regret_selector=-0.000263, CI(method=BCa)=[-0.000385, -0.000188], Wilcoxon n=28 stat=0.0 p=1.2131545083660686e-07, strict_lt=True, CI_excludes_0=True, positive_system_would_be=True

OK_SYSTEM_EVAL:false
