FAIL

# LoRA Smoke Report

- Outcome: FAIL
- Decided at (UTC): 2026-05-13T21:42:14Z
- Evaluate input: `reports/robust_asr/lora/lora_smoke_result.json`
- Export input:   `artifacts/robust_asr/lora_smoke/export_smoke_result.json` (outcome=PASS)

## Smoke metrics

- macro_wa_gain: -0.12843126450321876
- max_family_wa_gain: -0.11345487026714807
- clean_wa_regression: 0.11345487026714807
- per_family_wa_gain_variance: 0.0001791772669176124

## Per-family WA gain

- cafe_noise: -0.14545611499354005
- clean: -0.11345487026714807
- far_field_room: -0.14357895349050576
- muffled_lowpass: -0.11834285151588042
- phone_band: -0.12132353224901948

## Section 5.1 thresholds

- smoke_global_wa_gain_min        = 0.005
- smoke_family_wa_gain_min        = 0.01
- smoke_clean_regression_max_pass = 0.01
- smoke_clean_regression_max_partial = 0.02

## Reasons

- macro_wa_gain=-0.1284 < 0.005
- clean_wa_regression=0.1135 > 0.01
- max_family_wa_gain=-0.1135 < 0.01
- clean_wa_regression=0.1135 > 0.02
