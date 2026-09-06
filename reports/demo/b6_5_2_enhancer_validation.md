# B6.5.2 — Enhancer Validation on RP5

- Decision: **default_enhancer = `bypass`**
- BypassEnhancer status: **ok**
- MetricGANPlusEnhancer status: **not_implemented**
- ASR engine: `faster-whisper` model: `tiny.en`
- degradation_version: `degradation_v1`  metrics_version: `1.0`  default_enhancer_version: `1.0`
- Host: `ede511dfa6a0` generated_at: `2026-05-03T02:01:43.995884+00:00`
- Baseline: `/out/reports/demo/b6_5_1_rp5_results.json` (generated_at `2026-05-03T00:58:12.801695+00:00`)

## BypassEnhancer aggregates (30 rows)

- n_rows: 30
- n_input_equals_output: 30
- n_rows_with_nonzero_delta: 0
- max_abs_delta_wa_vs_baseline: 0.0
- mean_delta_wa_vs_baseline: 0.0
- mean_enhance_latency_seconds: 1.1e-05
- p95_enhance_latency_seconds: 1.4e-05
- mean_asr_latency_seconds: 1.76236
- p95_asr_latency_seconds: 1.950359

## MetricGANPlusEnhancer probe

- enhancer_version: `metricgan_plus_pretrained`
- status: **not_implemented**
- error_class: `NotImplementedError`
- error_message: 'MetricGAN+ implementation is owned by task T4.1 in the training branch. Use BypassEnhancer until T4.1 is merged into demo-rp5-v1.'

## Decision

- default_enhancer: **bypass**
- bypass UI label: `honest passthrough`
- MetricGAN+ UI label: `unavailable`
- blocked_on_upstream_task: `T4.1 in feature/training-datamove1-v1`

Rationale: MetricGAN+ wrapper is owned by T4.1 in feature/training-datamove1-v1 and is not yet synced into demo-rp5-v1. The demo branch must not implement a second MetricGAN+ wrapper (CLAUDE.md §10.4). MetricGANPlusEnhancer.enhance() correctly raises NotImplementedError, so there is no silent fallback risk. BypassEnhancer is an honest passthrough: enhanced output is byte-identical to the input and produces the same ASR transcripts as the B6.5.1 raw-path baseline.

## Per-row detail (BypassEnhancer)

| example_id | degradation_id | input==output | wa | wa_baseline | delta_wa | enh_lat (s) | asr_lat (s) |
|------------|----------------|---------------|----|-------------|----------|-------------|-------------|
| ex001 | clean | True | 0.941176 | 0.941176 | 0.0 | 1e-05 | 3.376923 |
| ex001 | far_field_room | True | 0.941176 | 0.941176 | 0.0 | 1.6e-05 | 1.562971 |
| ex001 | cafe_background | True | 0.941176 | 0.941176 | 0.0 | 1.1e-05 | 1.366092 |
| ex001 | phone_call | True | 0.941176 | 0.941176 | 0.0 | 1.2e-05 | 1.332155 |
| ex001 | muffled | True | 0.882353 | 0.882353 | 0.0 | 1.4e-05 | 1.399434 |
| ex001 | broadband_hiss | True | 0.941176 | 0.941176 | 0.0 | 1.1e-05 | 1.411935 |
| ex003 | clean | True | 0.947368 | 0.947368 | 0.0 | 1.1e-05 | 1.470736 |
| ex003 | far_field_room | True | 0.947368 | 0.947368 | 0.0 | 1.6e-05 | 1.482846 |
| ex003 | cafe_background | True | 0.947368 | 0.947368 | 0.0 | 1.1e-05 | 1.737913 |
| ex003 | phone_call | True | 0.947368 | 0.947368 | 0.0 | 1e-05 | 1.441448 |
| ex003 | muffled | True | 0.894737 | 0.894737 | 0.0 | 1e-05 | 1.391576 |
| ex003 | broadband_hiss | True | 0.947368 | 0.947368 | 0.0 | 1.1e-05 | 1.461165 |
| ex004 | clean | True | 1.0 | 1.0 | 0.0 | 9e-06 | 1.168924 |
| ex004 | far_field_room | True | 0.75 | 0.75 | 0.0 | 1.2e-05 | 1.158645 |
| ex004 | cafe_background | True | 1.0 | 1.0 | 0.0 | 9e-06 | 1.191111 |
| ex004 | phone_call | True | 1.0 | 1.0 | 0.0 | 9e-06 | 1.09197 |
| ex004 | muffled | True | 0.875 | 0.875 | 0.0 | 9e-06 | 1.37067 |
| ex004 | broadband_hiss | True | 1.0 | 1.0 | 0.0 | 1.2e-05 | 1.143974 |
| ex007 | clean | True | 1.0 | 1.0 | 0.0 | 9e-06 | 1.369333 |
| ex007 | far_field_room | True | 0.0 | 0.0 | 0.0 | 1e-05 | 8.719185 |
| ex007 | cafe_background | True | 1.0 | 1.0 | 0.0 | 1.1e-05 | 1.33046 |
| ex007 | phone_call | True | 1.0 | 1.0 | 0.0 | 9e-06 | 1.254446 |
| ex007 | muffled | True | 0.764706 | 0.764706 | 0.0 | 8e-06 | 1.379863 |
| ex007 | broadband_hiss | True | 1.0 | 1.0 | 0.0 | 1e-05 | 1.345593 |
| ex010 | clean | True | 1.0 | 1.0 | 0.0 | 1e-05 | 1.850152 |
| ex010 | far_field_room | True | 1.0 | 1.0 | 0.0 | 1e-05 | 1.713784 |
| ex010 | cafe_background | True | 0.933333 | 0.933333 | 0.0 | 1e-05 | 1.950359 |
| ex010 | phone_call | True | 1.0 | 1.0 | 0.0 | 1e-05 | 1.740523 |
| ex010 | muffled | True | 1.0 | 1.0 | 0.0 | 1e-05 | 1.860669 |
| ex010 | broadband_hiss | True | 1.0 | 1.0 | 0.0 | 1.1e-05 | 1.795951 |

## Notes

- DSP presets `light_clean`, `denoise`, `denoise_dereverb` are intentionally out of scope for B6.5.2; they are pipeline presets in `apply_preset()` and not `EnhancerAdapter` subclasses.
- Real MetricGAN+ inference depends on T4.1 (`feature/training-datamove1-v1`). Until that wrapper is synced into `demo-rp5-v1`, the demo runtime keeps `enhancer_version="bypass"` as the honest default.
