# T3.2 Degraded-Audio Whisper Baseline

Status: complete

Mode: full

| Field | Value |
|---|---|
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Degradation version | `degradation_v1` |
| Source clean manifest SHA-256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Source degraded manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Manifest records | 13465 |
| Processed records | 13465 |
| Failure count | 0 |
| Whisper model | `base.en` (openai-whisper 20250625) |
| Metrics version | `metrics_v1` |
| Code commit at run | `73808ed975940b0847404794dcd74fbda0b570ef` |
| Result commit | `34e93c8dddfedb58584f49afe1868618ddec4f56` |
| Smoke Slurm job ID | `2126085` |
| Full Slurm job ID | `2126086` |
| Full elapsed | `04:54:54` |
| Full MaxRSS | `3.58 GB` |
| Date (UTC) | `2026-05-02T17:50:02.381757Z` |

## Per-family results (mean per-record WER and Word Accuracy)

| Family | Count | Mean per-record WER | Mean per-record Word Accuracy | Δ WER vs clean | Δ WA vs clean |
|---|---|---|---|---|---|
| broadband_hiss | 2693 | 0.1271 | 0.8742 | +0.0626 | -0.0619 |
| cafe_background | 2693 | 0.1632 | 0.8390 | +0.0987 | -0.0971 |
| far_field_room | 2693 | 0.1659 | 0.8356 | +0.1014 | -0.1005 |
| muffled | 2693 | 0.3863 | 0.6361 | +0.3218 | -0.3000 |
| phone_call | 2693 | 0.0789 | 0.9217 | +0.0144 | -0.0144 |

## Overall — macro over families (headline)

| Metric | Value | Δ vs clean |
|---|---|---|
| Mean per-record WER | 0.1843 | +0.1198 |
| Mean per-record Word Accuracy | 0.8213 | -0.1148 |

## Consistency check — record_micro

This is NOT corpus WER. It is the mean of per-record values across all predictions. Because per-family counts are equal (2693 each in full mode), this matches the macro headline.

| Metric | Value | abs(macro − record_micro) |
|---|---|---|
| Mean per-record WER | 0.1843 | 3.28e-15 |
| Mean per-record Word Accuracy | 0.8213 | 1.45e-14 |

## Reference clean baseline (T3.1)

| Metric | Value |
|---|---|
| Mean per-record WER | 0.0645 |
| Mean per-record Word Accuracy | 0.9361 |

## Interpretation

`muffled` produces the strongest degradation: mean WER rises to 0.3863 (+0.3218 vs clean), Word Accuracy drops to 0.6361 (-0.3000). `phone_call` is the closest to clean: mean WER 0.0789 (+0.0144), Word Accuracy 0.9217 (-0.0144), likely because the narrow-band telephone codec preserves enough formant energy for `base.en`. `broadband_hiss`, `cafe_background`, and `far_field_room` cluster in the mid-range (WER 0.127–0.166, WA 0.836–0.874).
