# RP5 vs Surrey Whisper Reference Comparison (B6.5.1)

- Verdict: **comparable**  (thresholds: comparable ≤ 0.02, discrepant > 0.05)
- Requires model card update: False
- degradation_version: `degradation_v1`  metrics_version: `1.0`  default_enhancer_version: `1.0`
- RP5: engine=`faster-whisper` model=`tiny.en` host=`a6488873933a` generated_at=`2026-05-03T00:58:12.801695+00:00`
- Surrey: engine=`openai-whisper` model=`tiny.en` host=`aisurrey03.surrey.ac.uk` generated_at=`2026-05-03T01:29:54.035235+00:00`

## Primary aggregates (25 degraded rows)

- degraded_mean_delta_wa: -0.0024
- degraded_mean_abs_delta_wa: 0.0024
- degraded_max_abs_delta_wa: 0.0588

Per degradation:

| degradation_id | mean_delta_wa |
|----------------|---------------|
| broadband_hiss | 0.0000 |
| cafe_background | 0.0000 |
| far_field_room | 0.0000 |
| muffled | -0.0118 |
| phone_call | 0.0000 |

## Auxiliary (clean + all rows)

- clean_mean_delta_wa: 0.0000
- clean_max_abs_delta_wa: 0.0000
- all_rows_mean_delta_wa: -0.0020
- latency_seconds_total_rp5: 53.2376  latency_seconds_total_surrey: 37.6577

## Per-pair detail

| example_id | degradation_id | wa_rp5 | wa_surrey | delta_wa |
|------------|----------------|--------|-----------|----------|
| ex001 | broadband_hiss | 0.9412 | 0.9412 | 0.0000 |
| ex001 | cafe_background | 0.9412 | 0.9412 | 0.0000 |
| ex001 | clean | 0.9412 | 0.9412 | 0.0000 |
| ex001 | far_field_room | 0.9412 | 0.9412 | 0.0000 |
| ex001 | muffled | 0.8824 | 0.8824 | 0.0000 |
| ex001 | phone_call | 0.9412 | 0.9412 | 0.0000 |
| ex003 | broadband_hiss | 0.9474 | 0.9474 | 0.0000 |
| ex003 | cafe_background | 0.9474 | 0.9474 | 0.0000 |
| ex003 | clean | 0.9474 | 0.9474 | 0.0000 |
| ex003 | far_field_room | 0.9474 | 0.9474 | 0.0000 |
| ex003 | muffled | 0.8947 | 0.8947 | 0.0000 |
| ex003 | phone_call | 0.9474 | 0.9474 | 0.0000 |
| ex004 | broadband_hiss | 1.0000 | 1.0000 | 0.0000 |
| ex004 | cafe_background | 1.0000 | 1.0000 | 0.0000 |
| ex004 | clean | 1.0000 | 1.0000 | 0.0000 |
| ex004 | far_field_room | 0.7500 | 0.7500 | 0.0000 |
| ex004 | muffled | 0.8750 | 0.8750 | 0.0000 |
| ex004 | phone_call | 1.0000 | 1.0000 | 0.0000 |
| ex007 | broadband_hiss | 1.0000 | 1.0000 | 0.0000 |
| ex007 | cafe_background | 1.0000 | 1.0000 | 0.0000 |
| ex007 | clean | 1.0000 | 1.0000 | 0.0000 |
| ex007 | far_field_room | 0.0000 | 0.0000 | 0.0000 |
| ex007 | muffled | 0.7647 | 0.8235 | -0.0588 |
| ex007 | phone_call | 1.0000 | 1.0000 | 0.0000 |
| ex010 | broadband_hiss | 1.0000 | 1.0000 | 0.0000 |
| ex010 | cafe_background | 0.9333 | 0.9333 | 0.0000 |
| ex010 | clean | 1.0000 | 1.0000 | 0.0000 |
| ex010 | far_field_room | 1.0000 | 1.0000 | 0.0000 |
| ex010 | muffled | 1.0000 | 1.0000 | 0.0000 |
| ex010 | phone_call | 1.0000 | 1.0000 | 0.0000 |
