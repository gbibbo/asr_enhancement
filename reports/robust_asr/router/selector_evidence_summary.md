# Selector evidence summary — P6.1 (Outcome E)

Produced by: `scripts/robust_asr/build_selector_evidence_table.py`
Validated by: `scripts/robust_asr/validate_selector_evidence.py`
DETERMINISTIC_SELECTOR_VERSION: `deterministic_selector_v1`
Routing branch: B (selector-evidence path; OUTCOME_E_DETERMINISTIC_SELECTOR active)

## Artifact

- Path: `artifacts/robust_asr/router/selector_evidence.parquet`
- SHA-256: `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7`
- Size: 1 295 162 bytes
- Rows: 53 230 (one per audio_id × degradation_id pair from
  `whisper_base_ct2_int8.parquet`)

## Selector configuration

- Source: `configs/robust_asr/router_v1.yaml`
- Section 5.5 constants: `ask_repeat_threshold=-1.0`,
  `escalate_threshold=-0.5`, `no_speech_threshold=0.6`,
  `health_check_ttl_seconds=300`.
- Deployable backends: `whisper_base_ct2_int8` only
  (`assemblyai_available=False` by `BLOCKED_API`;
  `lora_available=False` by `SKIPPED_BY_DECISION_A`).
- Decode-feature proxy: P2.1's `whisper_base_ct2_int8.parquet` does
  not expose `avg_logprob` or `no_speech_prob` (those are produced by
  the P6.2 `extract_router_features.py`). For the selector-evidence
  table, `no_speech_prob` is proxied from
  `normalized_transcript == ""` (1.0 when empty, 0.0 otherwise) and
  `avg_logprob` is fixed at 0.0; the escalation branch is unreachable
  because `assemblyai_available=False`.

## Selector outcome distribution

| `selected_action`       | rows  | share   | `selector_reason` |
|-------------------------|-------|---------|-------------------|
| `whisper_base_ct2_int8` | 53 202 | 99.9474 % | `baseline`        |
| `ask_repeat`            | 28    | 0.0526 %  | `no_speech`       |
| `assemblyai`            | 0     | 0 %     | —                 |
| `whisper_lora_ct2_int8` | 0     | 0 %     | —                 |

`ask_repeat_allowed = True` on every row.

## Source split + degradation breakdown

| `source_split` | rows  |
|----------------|-------|
| validation     | 27 030 |
| locked_test    | 26 200 |

| `condition_family` | rows  |
|--------------------|-------|
| clean              | 10 646 |
| cafe_noise         | 10 646 |
| phone_band         | 10 646 |
| far_field_room     | 10 646 |
| muffled_lowpass    | 10 646 |

## Disjointness checks (validator §997-§998)

- Demo examples: `artifacts/robust_asr/demo/demo_examples_manifest.json`
  does not yet exist (P8.2 not started; `BLOCKED_OOD_PUBLIC` held);
  treated as the empty set ⇒ trivial disjointness.
- LoRA fine-tuning audio_ids:
  `artifacts/robust_asr/manifests/librispeech_lora_train.parquet`
  (22 507 rows, all under `librispeech/train-clean-100/…`). Eval
  audio_ids are under `librispeech/dev-clean/…` and
  `librispeech/test-clean/…` (per the 28-column eval schema's
  `source_split ∈ {validation, locked_test}`). Intersection at both
  full-id and base-stem granularity: 0.

## Validator result

```
$ python3 scripts/robust_asr/validate_selector_evidence.py \
    --input artifacts/robust_asr/router/selector_evidence.parquet
OK_SELECTOR_EVIDENCE
```

All §982-§1001 assertions PASS: file exists with non-zero rows;
required columns present; `selected_action` ⊆
{`whisper_base_ct2_int8`, `assemblyai`, `whisper_lora_ct2_int8`,
`ask_repeat`}; `assemblyai_available=False` ⇒ never `assemblyai`;
`lora_available=False` ⇒ never `whisper_lora_ct2_int8`; demo and
LoRA-train disjointness hold.
