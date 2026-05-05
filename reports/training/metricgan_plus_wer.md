# T4.2 MetricGAN+ Pretrained Whisper Evaluation

Status: complete

## Scope

Whisper `base.en` on the MetricGAN+ pretrained enhanced manifest produced at T4.2c.
Per-record WER and Word Accuracy are computed via `libs/audio/metrics.py` (`metrics_v1`),
aggregated per family (5 families × 2693 records) and macro over families. Results are
compared against the T3.2 degraded baseline (primary) and T3.1 clean baseline (secondary).

## Result

**The pretrained MetricGAN+ enhancer worsened ASR performance on this benchmark.**
Macro Word Accuracy dropped from 0.8213 (degraded) to 0.5892 (enhanced), a delta of
−0.2321 vs the T3.2 degraded baseline. The same direction holds for every degradation
family. Tier classification: **`null_or_negative`**.

## Full run identity

| Field | Value |
|---|---|
| Slurm job ID (full) | `2127693` |
| sacct State | `COMPLETED` |
| ExitCode | `0:0` |
| Elapsed | `06:47:48` |
| MaxRSS (batch) | `908608K` (~887 MB) |
| Execution node | `aisurrey05` |
| Code commit at run | `8a40b4fc840127801b5255d6d230841a7b06f3ae` |
| Result commit | `PENDING_RESULT_COMMIT` |
| Date (UTC) | `2026-05-04T23:55:47.996392Z` |
| Whisper model | `base.en` (openai-whisper `20250625`) |
| Metrics version | `metrics_v1` |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Degradation version | `degradation_v1` |
| Enhancer version | `metricgan_plus_pretrained` |
| Enhancement version | `enhancement_v1` |
| Enhanced manifest | `$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl` |
| Enhanced manifest SHA-256 | `544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9` |
| Degraded source manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Manifest records | `13465` |
| Processed records | `13465` |
| Failure count | `0` |
| Run dir | `$TRAIN_ROOT/runs/t4_2d_whisper_enhanced_full_2127693` |
| Smoke job ID | `2127690` (`COMPLETED 0:0`, 25 records, 0 failures) |

## Reference clean baseline (T3.1)

| Metric | Value |
|---|---|
| Mean per-record WER | 0.0645 |
| Mean per-record Word Accuracy | 0.9361 |

Per-family clean values are not available (T3.1 reports overall only).

## Reference degraded baseline (T3.2)

| Family | Count | Mean per-record WER | Mean per-record Word Accuracy |
|---|---|---|---|
| broadband_hiss | 2693 | 0.1271 | 0.8742 |
| cafe_background | 2693 | 0.1632 | 0.8390 |
| far_field_room | 2693 | 0.1659 | 0.8356 |
| muffled | 2693 | 0.3863 | 0.6361 |
| phone_call | 2693 | 0.0789 | 0.9217 |

Macro: WER 0.1843, Word Accuracy 0.8213.

## Per-family enhanced results vs baselines

| Family | Count | Enhanced WER | Enhanced WA | Degraded WER | Degraded WA | Δ WER vs degraded | Δ WA vs degraded | Δ WER vs clean | Δ WA vs clean |
|---|---|---|---|---|---|---|---|---|---|
| broadband_hiss | 2693 | 0.2666 | 0.7390 | 0.1271 | 0.8742 | +0.1395 | −0.1352 | N/A | N/A |
| cafe_background | 2693 | 0.4716 | 0.5401 | 0.1632 | 0.8390 | +0.3084 | −0.2989 | N/A | N/A |
| far_field_room | 2693 | 0.5920 | 0.4264 | 0.1659 | 0.8356 | +0.4261 | −0.4092 | N/A | N/A |
| muffled | 2693 | 0.6657 | 0.3978 | 0.3863 | 0.6361 | +0.2794 | −0.2383 | N/A | N/A |
| phone_call | 2693 | 0.1592 | 0.8429 | 0.0789 | 0.9217 | +0.0803 | −0.0788 | N/A | N/A |

Δ WER vs clean and Δ WA vs clean are reported macro-only because the T3.1 clean baseline
does not provide per-family values.

## Macro comparison

| Macro metric | Clean | Degraded | Enhanced | Enhanced − degraded | Enhanced − clean |
|---|---|---|---|---|---|
| Mean per-record WER | 0.0645 | 0.1843 | 0.4310 | +0.2467 | +0.3665 |
| Mean per-record Word Accuracy | 0.9361 | 0.8213 | 0.5892 | −0.2321 | −0.3469 |

Negative Δ WA and positive Δ WER mean the enhancer made the ASR task harder.

## Consistency check — record_micro

Per-family counts are equal (2693 each), so the macro headline equals the record_micro
mean over all 13 465 predictions to floating-point precision.

| Metric | Macro | record_micro | abs(macro − record_micro) |
|---|---|---|---|
| Mean per-record WER | 0.4310 | 0.4310 | 4.44e-16 |
| Mean per-record Word Accuracy | 0.5892 | 0.5892 | 3.33e-16 |

This is NOT corpus WER. It is the mean of per-record values across all predictions.

## Tier classification

Tier is assigned on the macro Word Accuracy delta vs the T3.2 degraded baseline:

- `strong` if Δ WA ≥ +0.05
- `partial` if 0 < Δ WA < +0.05
- `null_or_negative` if Δ WA ≤ 0

Δ macro Word Accuracy vs degraded: **−0.2321**. Tier: **`null_or_negative`**.

## Interpretation

The pretrained MetricGAN+ enhancer degraded Whisper `base.en` performance on this
dev-clean degraded benchmark. Do not claim improvement. The result should be reported
as a negative pretrained-baseline finding and used to motivate careful enhancer
selection or task-specific validation. Every degradation family individually confirms
the regression: the smallest impact is on `phone_call` (Δ WA −0.0788), the largest on
`far_field_room` (Δ WA −0.4092), with `cafe_background`, `muffled`, and `broadband_hiss`
in between.

## Limitations

- LibriSpeech dev-clean only (2693 utterances per family).
- Whisper `base.en` only; no other ASR model evaluated.
- MetricGAN+ VoiceBank pretrained only; no other enhancer evaluated.
- `degradation_v1` synthetic degradation families only.
- No fine-tuning of either the enhancer or Whisper.
- CPU inference only; no GPU run.
- ASR metric only (WER / Word Accuracy via `metrics_v1`); no perceptual quality metric
  (e.g. PESQ, STOI, MOS) computed alongside.

## Next step

T4.3 updates `docs/model_card.md` with the MetricGAN+ pretrained evaluation summary
and activates the B6.5 RP5 validation request. No RP5 work starts in T4.2d.
