# T6.3 Full-Training Summary

Status: T6.3 report committed. T6.2 full training **complete**. T6.3b post-hoc Whisper evaluation **complete**. T6.3 itself remains `pending` until tracker evidence is recorded in a separate authorised step.

## Scope

Consolidation only. This report combines:

- the T6.2 full-training Slurm run (the first 20 000-step training of the `spectral_unet_small_v1` enhancer on the speaker-disjoint dev-clean split);
- the T6.3b post-hoc Whisper evaluation Slurm run (the first non-placeholder per-family WER / Word Accuracy measurement of the T6.2 `latest.pt` checkpoint over the full val_degraded subset);
- the existing T3.1 / T3.2 / T4.2 baselines as comparison context.

T6.3 does **not** select a checkpoint, does **not** export the enhancer, and does **not** modify the model card. Those are owned by T7.1, T8.1, and T8.2 respectively.

## Identities

| Field | Value |
|---|---|
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Clean manifest records | 2693 |
| Clean manifest SHA-256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Degraded manifest records | 13465 (5 families × 2693) |
| Degraded manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Training split version | `devclean_speaker_split_v1` |
| Train clean records | 2160 |
| Val clean records | 533 |
| Train degraded records | 10800 (5 × 2160) |
| Val degraded records | 2665 (5 × 533) |
| ASR model | `base.en` (openai-whisper `20250625`) |
| Decode options | `language=en, task=transcribe, beam_size=1, temperature=0.0, fp16=true (CUDA)` |
| Metrics version | `metrics_v1` |
| Degradation version | `degradation_v1` |
| Enhancer architecture | `spectral_unet_small_v1` |
| Enhancer parameter count | 403201 (in `[200_000, 1_000_000]` budget) |

## T6.2 — Full-training Slurm run

| Field | Value |
|---|---|
| Slurm job | `2128952` |
| State / ExitCode | `COMPLETED` / `0:0` |
| Elapsed | `00:06:33` |
| Submit / Dispatch | `2026-05-06T16:51:53` / `2026-05-06T17:38:42` |
| Node / Partition | `aisurrey26` / `a100` |
| AllocTRES | `cpu=8,gres/gpu:nvidia_a100-sxm4-80gb=1,gres/gpu=1,mem=32G,node=1` |
| MaxRSS (batch step) | 1 479 996 K |
| Run dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952` |
| Verify JSON | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t6_2_full_training_verify_2128952.json` |
| `validation_passed` | true |
| Steps executed | 20000 |
| `device` / `gpu_used` / `apptainer_nv_used` | `cuda` / true / true |
| `expected_cuda` / `torch_cuda_is_available` | true / true |
| `metrics.csv` train rows | 200 (log_every_steps=100) |
| `metrics.csv` val rows | 20 (val_every_steps=1000) |
| Checkpoint metadata check | pass |
| `state_dict` roundtrip | pass |
| `whisper_validation_enabled` (inline) | false |

Code commit: `6a0c25911aea3125eff25a1511b2864fa1e2d8c1` (HEAD at run start). Prep commit: `e5ab5501ca33790e094df0f764a262b694b1f009`.

### Training-loss observation

| Step | Phase | Loss |
|---|---|---|
| 100 | train | 2.743973 |
| 19 900 | train | 1.157826 |
| 20 000 | train | 1.505096 |
| 20 000 | val | 2.011323 |

All `loss` values in `metrics.csv` are finite. The full 20 000-step schedule completed; train loss trended down across the run.

### Checkpoint inventory

`save_every_steps=2500`, `keep_last_n=5` over 20 000 steps retained the most recent five step checkpoints plus `latest.pt`:

```
runs/t6_2_full_training_2128952/checkpoints/
  checkpoint_step_0010000.pt    4 916 439 B
  checkpoint_step_0012500.pt    4 916 439 B
  checkpoint_step_0015000.pt    4 916 439 B
  checkpoint_step_0017500.pt    4 916 439 B
  checkpoint_step_0020000.pt    4 916 439 B
  latest.pt                     4 916 439 B
```

`latest.pt` carries `payload_step=20000`, `model_architecture=spectral_unet_small_v1`, `parameter_count=403201`, `dataset_version=librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8`, `training_split_version=devclean_speaker_split_v1`. State-dict round-trip via `models.build_model` inside Apptainer: pass.

### Six-artifact contract (T6.2 run)

`config.yaml` 12 679 B (with `runtime:` block); `metrics.csv` 9 143 B; `wer_by_degradation.csv` 282 B (placeholder rows — Whisper inline was OFF, deferred to T6.3); `loss_curve.png` 101 B (matplotlib placeholder; container lacks matplotlib); `val_wer_curve.png` 104 B (placeholder); `run_summary.md` 1 668 B (legacy "Dry-run training run summary" wording — see "Caveats" below).

## T6.3b — Post-hoc Whisper full evaluation

| Field | Value |
|---|---|
| Slurm job | `2129017` |
| State / ExitCode | `COMPLETED` / `0:0` |
| Elapsed | `00:08:34` |
| Submit / Dispatch | `2026-05-06T19:55:08` / `2026-05-06T20:15:23` |
| Node / Partition | `aisurrey24` / `a100` |
| AllocTRES | `cpu=8,gres/gpu:nvidia_a100-sxm4-80gb=1,gres/gpu=1,mem=32G,node=1` |
| Eval out dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_3_post_hoc_whisper_full_2129017` |
| Verify JSON | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t6_3_post_hoc_whisper_full_verify_2129017.json` |
| `validation_passed` / `errors` | true / `[]` |
| Source checkpoint | `runs/t6_2_full_training_2128952/checkpoints/latest.pt` (step 20 000) |
| `eval_per_family_cap` | 533 |
| `total_expected_transcriptions` | 2665 |
| `total_completed_transcriptions` | 2665 |
| `temp_wavs_written` / `temp_dir_cleaned` | 2665 / true |
| `missing_transcript_count` | 0 |
| `per_record_predictions_count` (line count match) | 2665 |
| `whisper_model` / `whisper_version` | `base.en` / `20250625` |
| `whisper_device` / `enhancer_device` | `cuda` / `cuda` |
| `gpu_used` / `apptainer_nv_used` | true / true |
| `expected_cuda` / `torch_cuda_is_available` | true / true |
| `enhancement_run` / `enhancement_bank_generation_artifacts_found` | false / false |

Prep commit (introducing `--eval-checkpoint` mode and the two T6.3 Slurm jobs): `45295895db15bde521d171eb8828618571275dcf`. T6.3a smoke (1-per-family validation of the new mode on real CUDA hardware): job `2129005`, COMPLETED 0:0 in 00:00:18 on `aisurrey26`, evidence recorded at result commit `a726d57c73667b89d10ba47b99ae0b9499f8f054`.

### T6.3b — Per-family WER / Word Accuracy

| Family | Count | Mean WER | Mean WA | Δ WER vs T3.2 degraded | Δ WA vs T3.2 degraded |
|---|---|---|---|---|---|
| broadband_hiss | 533 | 0.4147 | 0.5853 | +0.2876 | −0.2889 |
| cafe_background | 533 | 0.4700 | 0.5300 | +0.3068 | −0.3090 |
| far_field_room | 533 | 0.4847 | 0.5153 | +0.3188 | −0.3203 |
| muffled | 533 | 0.6302 | 0.3698 | +0.2439 | −0.2663 |
| phone_call | 533 | 0.3727 | 0.6273 | +0.2938 | −0.2944 |

### T6.3b — Macro

| Metric | Value | Δ vs T3.2 degraded |
|---|---|---|
| Mean per-record WER | 0.4745 | +0.2902 |
| Mean per-record Word Accuracy | 0.5255 | −0.2958 |

(All five families have equal counts (533 each), so macro and record_micro coincide to floating-point precision.)

## Comparison vs baselines

| Run | Macro WER | Macro WA | Δ macro WA vs T3.2 degraded |
|---|---|---|---|
| T3.1 clean baseline | 0.0645 | 0.9361 | (clean reference) |
| T3.2 degraded baseline | 0.1843 | 0.8213 | (degraded reference) |
| T4.2 MetricGAN+ pretrained | 0.4310 | 0.5892 | **−0.2321** (`null_or_negative`) |
| T6.3 post-hoc on T6.2 `latest.pt` | **0.4745** | **0.5255** | **−0.2958** |

T3.1 and T3.2 numbers are quoted from `reports/training/baseline_summary.md`. T4.2 numbers are quoted from `reports/training/metricgan_plus_wer.md`.

## Tier classification

Apply the existing tier rule from `reports/training/metricgan_plus_wer.md`:

- `strong` if Δ WA ≥ +0.05
- `partial` if 0 < Δ WA < +0.05
- `null_or_negative` if Δ WA ≤ 0

Δ macro Word Accuracy of T6.3 vs T3.2 degraded: **−0.2958**. Tier: **`null_or_negative`**.

This is a **modelling outcome**, not a pipeline failure. The T6.3 gate evaluates whether the post-hoc evaluation pipeline produced finite, non-placeholder, contractual artifacts; by that criterion T6.3b passes (2 665 / 2 665 transcriptions, all guards green, T6.2 source artifacts unchanged). The fact that the trained enhancer's macro Word Accuracy is below the unenhanced T3.2 degraded baseline — and slightly below the T4.2 MetricGAN+ prior negative baseline — is information for the deployment-decision tasks (T7.1 / T7.2 / T8.1), not a T6.3 closure blocker.

MetricGAN+ continues to appear here only as a **prior negative baseline**, never as a deployment candidate (`tier: null_or_negative`, `deployment_decision: not_selected` per T4.2). The T6.2-trained enhancer falls into the same tier; whether to declare it `not_selected_pending_review`, attempt other candidate checkpoints, or change architecture/loss/schedule is an explicit T7.1 decision.

## Limitations and caveats

- **Legacy run-summary wording (T6.2 only).** `runs/t6_2_full_training_2128952/run_summary.md` carries the legacy "Dry-run training run summary" / "dry-run artifact contract proof" wording, because the run-summary writer's whisper-disabled branch reuses T5.3 phrasing. Do not treat that file as the source of truth for T6.2; use the verify JSON, `metrics.csv`, the `runtime:` block of `runs/t6_2_full_training_2128952/config.yaml`, the checkpoint payloads, and Slurm `sacct` evidence instead. The artifact is intentionally NOT modified retroactively.
- **Placeholder PNGs.** `loss_curve.png` (101 B) and `val_wer_curve.png` (104 B) in the T6.2 run dir are placeholder PNGs because matplotlib is not available in the container. The numeric `metrics.csv` is the source of truth for training/validation losses.
- **Latest-only post-hoc evaluation.** T6.3b evaluates `latest.pt` (step 20 000) only; it does **not** evaluate the four earlier kept checkpoints (`checkpoint_step_0010000.pt … checkpoint_step_0017500.pt`). T7.1 owns checkpoint selection. If T7.1 needs WER / WA for additional candidates it must either (a) run additional `--eval-checkpoint` evaluations using the same Slurm job pattern, or (b) explicitly justify selecting `latest.pt` by policy.
- **Single utterance per family in the T6.3a smoke.** The smoke selected the same `utterance_id` (`1272-128104-0001`) under five degradations — the deterministic-no-shuffle subset selector. Acceptable because the smoke validates the integration path; the full T6.3b run uses the full 533/family scope.
- **Whisper inline was OFF during T6.2.** `wer_by_degradation.csv` inside the T6.2 run dir holds placeholder rows (`note=placeholder_no_whisper_t6_2b`); the **non-placeholder** equivalent for the trained model is the T6.3b `wer_by_degradation.csv` quoted above. The T6.2 placeholder file is intentionally NOT modified.
- **Cropped 4-second val windows.** The `_maybe_run_whisper_validation` helper used by `--eval-checkpoint` reuses the val DataLoader's centered 4-second crop (matching `PairedDevCleanDataset.mode="val"`). For longer utterances this evaluates the central window, not the full waveform.
- **Single ASR model and single Whisper version.** `base.en` / `20250625` only.
- **No PESQ / STOI / MOS metrics** — same scope as T4.2.
- **Dev-clean only.** No train split or test split evaluated.

## Closure checklist (informational; tracker closure is a separate step)

- [x] T6.2 full-training run completed (Slurm `COMPLETED 0:0`, six artifacts, candidate checkpoints, finite metrics).
- [x] T6.3a post-hoc Whisper smoke validated the `--eval-checkpoint` mode end-to-end on real CUDA hardware.
- [x] T6.3b post-hoc Whisper full evaluation produced non-placeholder per-family WER / WA over the full val_degraded subset.
- [x] T6.2 source run artifacts not modified retroactively.
- [x] `docs/model_card.md` not modified (T8.2 owns this).
- [x] MetricGAN+ kept as prior negative baseline only.
- [ ] Tracker evidence committed and T6.3 closed (separate authorised step; not in this commit).

## Next gate

**T7.1 — Checkpoint selection.** Reads:

- this report (`reports/training/full_training_summary.md`),
- `runs/t6_3_post_hoc_whisper_full_2129017/wer_by_degradation.csv`,
- `runs/t6_3_post_hoc_whisper_full_2129017/per_record_predictions.jsonl`,
- the candidate checkpoint list under `runs/t6_2_full_training_2128952/checkpoints/`,

and applies `cfg.checkpoint_policy.selection_primary_metric: average_word_accuracy_over_official_degradations` plus the configured tiebreakers. If T7.1 cannot proceed because the only post-hoc-evaluated candidate falls into `null_or_negative`, the decision rule is to surface that to the user (do not auto-export, do not auto-update model card; T8.1 / T8.2 only run on a `selected` checkpoint).

T6.3 tracker closure happens after this report is committed, in a separate authorised step.

## What this report does not claim

- The T6.2-trained enhancer is a deployable improvement over the T3.2 degraded baseline. (It is not — Δ macro WA = −0.2958, tier `null_or_negative`.)
- The T6.2-trained enhancer is preferable to the T4.2 MetricGAN+ pretrained baseline. (Δ macro WA between them is −0.0637 in MetricGAN+'s favour at the macro level; both remain `null_or_negative`.)
- The current architecture / loss / schedule converged to a useful enhancer. The training loss trend (2.743 → 1.158 → 1.505) is suggestive of optimisation working but not of a competitive WER outcome at `latest.pt`.
- Earlier checkpoints (`checkpoint_step_0010000.pt … 0017500.pt`) would necessarily perform worse, or better, than `latest.pt`. This report evaluates `latest.pt` only.
- Any decision about whether to ship, retrain, change architecture, change loss, or extend the schedule. Those are T7.1 / T7.2 / T8.1 decisions.
