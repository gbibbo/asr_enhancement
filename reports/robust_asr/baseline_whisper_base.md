# Baseline summary: whisper_base_ct2_int8

- rows: 53230
- rows_failed: 0
- backend_versions: ['faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8']
- normalization_versions: ['normalization_v1']
- total_end_to_end_latency_ms: 10408373.0
- total_cost_usd: 0.0000

## Per-family WER / WA (mean over successful rows)

| family | n | mean_WER | mean_WA |
|--------|---|----------|---------|
| cafe_noise | 10646 | 0.1241 | 0.8784 |
| clean | 10646 | 0.0709 | 0.9367 |
| far_field_room | 10646 | 0.1410 | 0.8623 |
| muffled_lowpass | 10646 | 0.1072 | 0.9027 |
| phone_band | 10646 | 0.6058 | 0.6034 |
