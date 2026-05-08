# Robust ASR — degradation_v1 build summary (P1.4)

Date: 2026-05-08
Sentinel: `OK_DEGRADATION_V1`
Slurm job: `2129647` on `aisurrey01.surrey.ac.uk` (partition `2080ti`,
COMPLETED `0:0` in 1 min 3 s, MaxRSS 11 077 812 KiB).
Container sha256: `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`.

## Source data (eval-only)

```
librispeech_validation.parquet     2 703 rows
librispeech_locked_test.parquet    2 620 rows
TOTAL source rows                   5 323
```

`lora_train` and `router_train` are deliberately excluded; training-time
degradation is owned by P3.1 / P4.1.

## Per-family results

| family            | tier      | rows  | bad_output | bad_ratio | err | wall (s) | per-family parquet sha256 |
|-------------------|-----------|------:|-----------:|----------:|----:|---------:|---------------------------|
| clean             | id        | 5 323 | 0          | 0.0000    | 0   |     0.02 | `fde856ea…`               |
| clean             | ood_param | 5 323 | 0          | 0.0000    | 0   |     0.02 | `dc8d4101…`               |
| cafe_noise        | id        | 5 323 | 0          | 0.0000    | 0   |     6.18 | `bae18ae2…`               |
| cafe_noise        | ood_param | 5 323 | 0          | 0.0000    | 0   |     6.12 | `b958b37c…`               |
| phone_band        | id        | 5 323 | 0          | 0.0000    | 0   |     8.25 | `b0e7cabe…`               |
| phone_band        | ood_param | 5 323 | 0          | 0.0000    | 0   |     8.28 | `218e5bf8…`               |
| far_field_room    | id        | 5 323 | 0          | 0.0000    | 0   |     6.63 | `ec1be39c…`               |
| far_field_room    | ood_param | 5 323 | 0          | 0.0000    | 0   |     7.05 | `3ea8c734…`               |
| muffled_lowpass   | id        | 5 323 | 0          | 0.0000    | 0   |     5.09 | `742e25ab…`               |
| muffled_lowpass   | ood_param | 5 323 | 0          | 0.0000    | 0   |     4.97 | `5c6c4dc1…`               |
| **TOTAL**         |           | 53 230| **0**      | **0.0000**| 0   |    54.65 |                           |

Section 9 P1.4 Decision rule 1 (BAD_OUTPUT > 1 % per family): NOT FIRED.

## Eval manifests (committed)

```
artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet
  rows   = 26 615   (5 families x 5 323 source rows)
  sha256 = cf0f0bce49cb0d2a813ce65ab764485ddc1cc7c5e5b9756f1668d0950a4d9a49

artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet
  rows   = 26 615   (5 families x 5 323 source rows)
  sha256 = 30684dc489bef980f02a2bc0c45cb4aa8bc8fc605e373de10dd97397b2308314
```

Per-family per-tier parquet files are also committed (10 files;
sha256s in the table above and in
`artifacts/robust_asr/manifests/degradation_v1_build_summary.json`).

## Audio outputs (scratch only — not committed)

```
/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degradation_v1/
  cafe_noise/{id,ood_param}/<audio_id>.wav            (10 646 wavs)
  phone_band/{id,ood_param}/<audio_id>.wav            (10 646 wavs)
  far_field_room/{id,ood_param}/<audio_id>.wav        (10 646 wavs)
  muffled_lowpass/{id,ood_param}/<audio_id>.wav       (10 646 wavs)
```

42 584 wavs total. clean is identity (manifest rows point at the source
`.flac`; no audio rewritten).

## Scratch budget

```
Section 5.8 budget       50.000 GB
free pre-build         1764.371 GB
free post-build        1754.074 GB
scratch used (build)     10.297 GB     (4.86x under budget)
```

## Determinism

Per-row seed = `SHA-256(f"degradation_v1|{family}|{tier}|{audio_id}|{master_seed}")`
truncated to 63 bits (fits pyarrow int64). Master seed `20260508` recorded
in `configs/robust_asr/degradation_v1.yaml`. Re-running the script with the
same config and inputs reproduces the same per-row seed and (for the
deterministic families and any stochastic family seeded from `seed`) the same
output sha256.

## ID vs OOD-param disjointness

Verified by `tests/robust_asr/test_degradation_v1.py::test_id_ood_param_disjoint_for_continuous_families`
and `…::test_phone_band_ood_changes_bit_depth`:

| family            | ID range / value          | OOD-param range / value     |
|-------------------|---------------------------|-----------------------------|
| cafe_noise        | snr_db ∈ [10, 25]         | snr_db ∈ [0, 7]             |
| phone_band        | bit_depth = 8             | bit_depth = 4               |
| far_field_room    | rt60_s ∈ [0.20, 0.45]     | rt60_s ∈ [0.55, 0.90]       |
|                   | mic_dist ∈ [1.0, 2.5] m   | mic_dist ∈ [3.0, 5.0] m     |
| muffled_lowpass   | lowpass ∈ [2500, 4000] Hz | lowpass ∈ [1200, 1800] Hz   |
|                   | atten ∈ [-9, -3] dB       | atten ∈ [-15, -10] dB       |

## Markers / claims

`BLOCKED_OOD_PUBLIC` carried (P1.4 does not unblock OOD-real; it builds
parameter-OOD on LibriSpeech only). `claims_enabled.ood_real=false` carried.
`degradation_version=degradation_v1` (libs/common/versions.py value
unchanged; sample_<family> additions are non-breaking).
