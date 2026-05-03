# T3.3 Baseline Summary

Status: complete

## Scope

Consolidation only. No enhancer has been evaluated.
This report closes Phase 3 (baseline evaluation) and enables T4.x (pretrained enhancer evaluation) to begin.
T3.3 does not start T4.x and does not claim any enhancement result.

## Identities

| Field | Value |
|---|---|
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Clean manifest records | 2693 |
| Clean manifest SHA-256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Degraded manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Degraded manifest records | 13465 (5 families × 2693) |
| ASR model | `base.en` (openai-whisper 20250625) |
| Metrics version | `metrics_v1` |
| Degradation version | `degradation_v1` |

## T3.1 — Clean Baseline

Slurm job: `2125895`. Code commit: `6e7d9d4464bd5900467d075221478905421945ce`. Result commit: `a753b15`.

| Metric | Value |
|---|---|
| Mean per-record WER | 0.0645 |
| Mean per-record Word Accuracy | 0.9361 |

## T3.2 — Degraded Baseline (per family)

Smoke job: `2126085`. Full job: `2126086` (elapsed `04:54:54`, MaxRSS `3.58 GB`).
Code commit: `73808ed975940b0847404794dcd74fbda0b570ef`. Result commit: `34e93c8dddfedb58584f49afe1868618ddec4f56`.

| Family | Count | Mean WER | Mean WA | Δ WER vs clean | Δ WA vs clean |
|---|---|---|---|---|---|
| broadband_hiss | 2693 | 0.1271 | 0.8742 | +0.0626 | -0.0619 |
| cafe_background | 2693 | 0.1632 | 0.8390 | +0.0987 | -0.0971 |
| far_field_room | 2693 | 0.1659 | 0.8356 | +0.1014 | -0.1005 |
| muffled | 2693 | 0.3863 | 0.6361 | +0.3218 | -0.3000 |
| phone_call | 2693 | 0.0789 | 0.9217 | +0.0144 | -0.0144 |

## T3.2 — Degraded Baseline (overall macro)

| Metric | Value | Δ vs clean |
|---|---|---|
| Mean per-record WER | 0.1843 | +0.1198 |
| Mean per-record Word Accuracy | 0.8213 | -0.1148 |

Consistency check: macro equals record_micro (abs diff 3.28e-15). Per-family counts are equal (2693 each), so macro and record_micro coincide.

## Interpretation

`muffled` produces the strongest degradation: mean WER rises to 0.3863 (+0.3218 vs clean), Word Accuracy drops to 0.6361 (-0.3000). `phone_call` is the closest to clean: mean WER 0.0789 (+0.0144), Word Accuracy 0.9217 (-0.0144), likely because the narrow-band telephone codec preserves enough formant energy for `base.en`. `broadband_hiss`, `cafe_background`, and `far_field_room` cluster in the mid-range (WER 0.127–0.166, WA 0.836–0.874).

## Limitations

- Corpus: LibriSpeech dev-clean only (2693 utterances); no train split evaluated.
- ASR model: `base.en` only; no other Whisper variants evaluated.
- Inference: CPU-only; no GPU timing.
- Degradation scope: `degradation_v1` only; 5 families, one deterministic version per utterance per family.
- Enhancement: no enhancer evaluated in T3. This report is a pre-enhancement baseline.
- Metrics: mean per-record WER and Word Accuracy only; these are not corpus-level WER values.

## What This Report Does Not Claim

- No enhancer has been applied or evaluated.
- No training has been run.
- No T4.x results are present here.
- No generalization beyond dev-clean or beyond `degradation_v1` is implied.
