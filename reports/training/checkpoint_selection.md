# T7.1 Checkpoint Selection

Generated (UTC): `2026-05-06T22:04:35Z`

Plan §17 selection rule:

- primary metric: average Word Accuracy over the five official degradations;
- tiebreaker 1: best worst-case (per-family) Word Accuracy;
- tiebreaker 2: most recent (highest) checkpoint step.

## Identities

| Field | Value |
|---|---|
| Config | `configs/training/full_training.yaml` |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Training split version | `devclean_speaker_split_v1` |
| Metrics version | `metrics_v1` |
| Degradation version | `degradation_v1` |
| ASR model | `base.en` (`20250625`) |
| ASR device | `cuda` |
| eval_per_family_cap | `533` |
| T3.2 degraded macro WA baseline | `0.8213` |

## latest.pt alias verification

- `sha256(latest.pt) == sha256(checkpoint_step_0020000.pt)`: **True**
- `latest.pt` SHA-256: `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e`
- `checkpoint_step_0020000.pt` SHA-256: `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e`

## Candidates

| Step | Macro WA | Worst-case WA | Macro WER | SHA-256 (prefix) |
|---|---|---|---|---|
| 10000 | 0.512384 | 0.370847 | 0.487616 | `1ed2e1fae94f20da…` |
| 12500 | 0.510349 | 0.367664 | 0.489651 | `f55d65af13bf6988…` |
| 15000 | 0.514670 | 0.369340 | 0.485330 | `63f58bce27a7a58f…` |
| 17500 | 0.511481 | 0.367951 | 0.488519 | `94bb5eb86b437cf4…` |
| 20000 | 0.525542 | 0.369799 | 0.474458 | `a6ae240a1b210ad5…` |

## Selection rule application trace

| Rank | Step | Macro WA | Worst-case WA | Macro WER |
|---|---|---|---|---|
| 1 | 20000 | 0.525542 | 0.369799 | 0.474458 |
| 2 | 15000 | 0.514670 | 0.369340 | 0.485330 |
| 3 | 10000 | 0.512384 | 0.370847 | 0.487616 |
| 4 | 17500 | 0.511481 | 0.367951 | 0.488519 |
| 5 | 12500 | 0.510349 | 0.367664 | 0.489651 |

## Selected checkpoint

- Step: `20000`
- Canonical path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt`
- SHA-256: `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e`
- Alias paths: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt`
- Macro Word Accuracy: `0.525542`
- Macro WER: `0.474458`
- Worst-case family Word Accuracy: `0.369799`
- Δ macro WA vs T3.2 degraded: `-0.295758`
- Tier at selection: `null_or_negative`
- Deployment decision: `not_selected_pending_review`

## Posture

- `t7_2_required`: **True**
- `do_not_modify_model_card`: **True**

## Source evidence (read-only references)

- step 10000: eval_metadata `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t7_1_post_hoc_whisper_step_10000_2129063/eval_metadata.json`; verify JSON `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t7_1_post_hoc_whisper_step_10000_verify_2129063.json`
- step 12500: eval_metadata `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t7_1_post_hoc_whisper_step_12500_2129064/eval_metadata.json`; verify JSON `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t7_1_post_hoc_whisper_step_12500_verify_2129064.json`
- step 15000: eval_metadata `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t7_1_post_hoc_whisper_step_15000_2129065/eval_metadata.json`; verify JSON `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t7_1_post_hoc_whisper_step_15000_verify_2129065.json`
- step 17500: eval_metadata `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t7_1_post_hoc_whisper_step_17500_2129066/eval_metadata.json`; verify JSON `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t7_1_post_hoc_whisper_step_17500_verify_2129066.json`
- step 20000: eval_metadata `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_3_post_hoc_whisper_full_2129017/eval_metadata.json`; verify JSON `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t6_3_post_hoc_whisper_full_verify_2129017.json`

