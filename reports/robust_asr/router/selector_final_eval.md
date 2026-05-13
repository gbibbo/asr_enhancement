NEUTRAL_EVIDENCE: positive_system=pending — single deployable transcript-producing backend under OUTCOME_E_DETERMINISTIC_SELECTOR; regret figures below are reported per agent plan §1664-§1665 and do not enable a positive_system claim.

# Selector final evaluation (P7.3 Branch B — Outcome E)

## Inputs

- Selector package: `artifacts/robust_asr/router/selected_router/deterministic_selector.json`
- Selector evidence parquet: `artifacts/robust_asr/router/selector_evidence.parquet`
- `deterministic_selector_version` = `deterministic_selector_v1`
- Section 5.5 constants: `ask_repeat_threshold=-1.0`, `escalate_threshold=-0.5`, `no_speech_threshold=0.6`, `health_check_ttl_seconds=300.0`
- Rows: 53230

## Predicate-parity check

- Rows where recomputed `selected_action` disagrees with parquet: 0 / 53230.
- Parity PASS implies that the packaged selector and the build-time selector apply identical §5.5 constants.

## Selection rates

| action                  | rows   | share        |
|-------------------------|--------|--------------|
| `whisper_base_ct2_int8` |  53202 |    99.9474 % |
| `ask_repeat`            |     28 |     0.0526 % |
| `assemblyai`            |      0 |     0.0000 % |
| `whisper_lora_ct2_int8` |      0 |     0.0000 % |

- `local_only_rate` (selector never routes off-device under OUTCOME_E): 100.0000 %
- `cloud_call_rate`: 0.0000 % (zero by construction — `assemblyai_available=False`)
- `transcript_emitted_rate` (non-`ask_repeat`): 99.9474 %

## WER / WA

| backend                            | mean WER     | mean WA      |
|------------------------------------|--------------|--------------|
| always-`whisper_base_ct2_int8`     |     0.209797 |     0.836701 |
| deterministic selector             |     0.209797 |     0.836701 |

- `ASK_REPEAT_WER` convention: 1.0 (no transcript is emitted on `ask_repeat`; using a maximum-penalty convention for regret accounting). `ASK_REPEAT_WA` = 0.0.

## Latency proxy

- Mean local-decode latency under selector (ms): `195.536`.
- Selector dispatch cost is constant-time and ignored here.

## Cost

- Total cost: $0.0000 USD. Per-row cost: $0.0000. AssemblyAI is unavailable (`BLOCKED_API` / `cloud_tradeoff=false`); the selector never emits the `assemblyai` action.

## Paired regret (selector − always-`whisper_base_ct2_int8`)

- `mean_regret_wer` = 0.000000 (positive = selector worse than always-baseline).
- Paired BCa 95% CI (`percentile_fallback`, 10000 iterations, seed=20260514): [0.000000, 0.000000].
- Wilcoxon signed-rank (two-sided, nonzero deltas only, n=0): statistic=nan, p-value=nan. Reported per §5.6; does not gate the flag.

## Outcome E framing

- Deployable transcript-producing backend count = 1 (`whisper_base_ct2_int8` only). LoRA is excluded by `Decision_A_smoke=FAIL`; AssemblyAI is excluded by `BLOCKED_API`.
- Per agent plan §1664-§1665 and §5.6, the regret summary is **NEUTRAL EVIDENCE** and does not gate `claims_enabled.positive_system`. This report does not assert a positive system claim. `positive_system` remains `pending` until P8.1.

OK_SELECTOR_FINAL_EVAL
