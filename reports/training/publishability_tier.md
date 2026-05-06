# T7.2 Publishability Tier Assignment

Generated (UTC): `2026-05-06T22:26:49Z`

## Status / Scope

T7.2 is a written synthesis over already-committed evidence. It applies the publishability tier rule from `docs/plans/training_datamove1_plan.md` §17 to the T7.1 deterministic checkpoint selection and records the resulting tier and deployment posture.

T7.2 does **not**:

- run any new evaluation;
- submit any Slurm job;
- amend `reports/training/checkpoint_selection.md` or `reports/training/checkpoint_selection.json`;
- modify `docs/model_card.md` (T8.2 owns that);
- modify any external run artifact under `runs/t6_2_full_training_2128952/`, `runs/t6_3_post_hoc_whisper_full_2129017/`, or `runs/t7_1_post_hoc_whisper_step_*/`;
- modify any T3.x / T4.2 / T6.3 baseline report;
- decide T8.1 export-or-skip (that decision is owned by T8.1).

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
| `eval_per_family_cap` | `533` |
| T3.2 degraded macro Word Accuracy | `0.8213` |
| T4.2 MetricGAN+ pretrained macro Word Accuracy | `0.5892` |

## Inputs (frozen)

- `reports/training/checkpoint_selection.md`
- `reports/training/checkpoint_selection.json`
- `reports/training/full_training_summary.md`
- `reports/training/baseline_summary.md`
- `reports/training/metricgan_plus_wer.md`
- `docs/plans/training_datamove1_plan.md` (§17)
- Per-checkpoint eval evidence (read-only):
  - step 10000: `runs/t7_1_post_hoc_whisper_step_10000_2129063/eval_metadata.json`; verify `artifacts/t7_1_post_hoc_whisper_step_10000_verify_2129063.json`
  - step 12500: `runs/t7_1_post_hoc_whisper_step_12500_2129064/eval_metadata.json`; verify `artifacts/t7_1_post_hoc_whisper_step_12500_verify_2129064.json`
  - step 15000: `runs/t7_1_post_hoc_whisper_step_15000_2129065/eval_metadata.json`; verify `artifacts/t7_1_post_hoc_whisper_step_15000_verify_2129065.json`
  - step 17500: `runs/t7_1_post_hoc_whisper_step_17500_2129066/eval_metadata.json`; verify `artifacts/t7_1_post_hoc_whisper_step_17500_verify_2129066.json`
  - step 20000: `runs/t6_3_post_hoc_whisper_full_2129017/eval_metadata.json`; verify `artifacts/t6_3_post_hoc_whisper_full_verify_2129017.json`

## Tier rule (plan §17, verbatim)

- `publicable_strong` if Δ macro Word Accuracy ≥ +0.05
- `publicable_acceptable` if 0 < Δ macro Word Accuracy < +0.05
- `framework_only` if Δ macro Word Accuracy ≤ 0

Primary metric: macro Word Accuracy over the five official degradations vs the T3.2 degraded baseline.

## Per-candidate tier table

| Step | Macro WA | Worst-case WA | Worst-case family | Δ macro WA vs T3.2 | Δ macro WA vs T4.2 | Tier |
|---|---|---|---|---|---|---|
| 10000 | 0.5123842 | 0.370847 | muffled | −0.3089158 | −0.0768158 | `framework_only` |
| 12500 | 0.510349 | 0.367664 | muffled | −0.310951 | −0.078851 | `framework_only` |
| 15000 | 0.5146698 | 0.36934 | muffled | −0.3066302 | −0.0745302 | `framework_only` |
| 17500 | 0.5114806 | 0.367951 | muffled | −0.3098194 | −0.0777194 | `framework_only` |
| 20000 | 0.5255416 | 0.369799 | muffled | **−0.2957584** | **−0.0636584** | **`framework_only`** |

## Selected-checkpoint verdict

- Step: `20000`
- Canonical path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt`
- Alias: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt`
- SHA-256: `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e`
- Macro Word Accuracy: `0.5255416`
- Macro WER: `0.4744584`
- Worst-case family Word Accuracy: `0.369799` (`muffled`)
- Δ macro WA vs T3.2 degraded: `-0.2957584`
- Δ macro WA vs T4.2 MetricGAN+ pretrained: `-0.0636584`

| Field | Value |
|---|---|
| `tier` | `framework_only` |
| `sub_status` | `framework_only_strict_negative` |
| `defensible_reason_override_applied` | `false` |
| `deployment_decision` | `not_selected_for_deployment` |
| `selection_purpose` | `reproducibility_and_framework_demonstration_only` |
| `export_posture` | `export_may_proceed_only_as_reproducibility_framework_artifact_or_be_explicitly_skipped_in_T8.1` |
| `metricgan_plus_role` | `prior_negative_baseline_only` |

## Rationale

All five evaluated candidate checkpoints have `delta_macro_wa_vs_t3_2_degraded ≤ 0`; the selected checkpoint at step 20000 has delta `-0.2957584`. Every per-family Word Accuracy is also below the corresponding T3.2 degraded family baseline. MetricGAN+ pretrained sits at delta `-0.2321` vs T3.2 (also `null_or_negative`); the trained enhancer's macro WA `0.5255` is below MetricGAN+'s `0.5892`. No metric basis exists to override the default `framework_only` verdict.

The `framework_only_strict_negative` sub-status records that this is not a tie or marginal case: every candidate is strictly negative on the primary metric, and every per-family Word Accuracy is also below the T3.2 family baseline. The §17 "defensible reason" override is not invoked.

## Treatment of T3.2 degraded underperformance

The T6.2-trained enhancer falls below the T3.2 degraded baseline at every evaluated checkpoint. This is a **modelling outcome**, not a pipeline failure: T6.3 already validated the post-hoc Whisper evaluation pipeline as contractually green (T6.3b: `validation_passed=true`, 2665/2665 transcriptions, all guards green). The most plausible attribution is the architecture / loss / schedule limitations of `spectral_unet_small_v1` (403 201 parameters) at 20 000 steps with the current schedule on the speaker-disjoint dev-clean split, not an evaluation defect.

## Treatment of MetricGAN+

MetricGAN+ pretrained continues to be a **prior negative baseline only**, never a deployment candidate. T4.2 already classified it as `null_or_negative` (delta `-0.2321` vs T3.2). It is reported here for comparison with the T6.2-trained enhancer (which is also `null_or_negative`, and worse than MetricGAN+ at the macro level). T7.2 does not modify any T4.2 artifact.

## Posture flags

- `do_not_modify_model_card: true`
- `do_not_modify_checkpoint_selection: true`
- `do_not_modify_external_run_artifacts: true`

## Slurm policy and forward-looking notification rule

T7.2 submitted no Slurm job: `slurm_required_for_t7_2: false`, `slurm_notification_policy: not_applicable_no_slurm_job_submitted`.

Forward-looking rule (recorded for future Slurm jobs from this branch, e.g. T8.1 export jobs, retraining experiments, ablation evals): include either (a) native Slurm `--mail-type=END,FAIL --mail-user=<addr>` if the cluster mail relay is confirmed reliable, or (b) a session-side watcher polling `./slurm/tools/on_submit.sh sacct -j <id>` / `squeue -u $USER` at ≥30 s and reporting terminal state, or (c) an explicit "manual check" command stated up-front. This rule is **not** applied retroactively to T6.2 / T6.3 / T7.1 jobs.

## Limitations

- Dev-clean only (533 records per family for the val_degraded subset; 2693 records per family for the T3.2 reference).
- Single ASR model: openai-whisper `base.en` (`20250625`) only.
- Single enhancer architecture: `spectral_unet_small_v1`, 403 201 parameters, single 20 000-step run with the configured loss / schedule.
- Cropped 4-second val windows via `_maybe_run_whisper_validation` in the post-hoc Whisper evaluation mode.
- ASR metrics only (WER and Word Accuracy via `metrics_v1`); no PESQ / STOI / MOS.
- No fine-tuning of Whisper.
- Single Whisper version; CUDA decode (fp16, `beam_size=1`, `temperature=0.0`).
- Tier rule is applied on macro Word Accuracy over the five official degradations; per-family disaggregation reproduces the same `null_or_negative` direction.
- Selection inputs are frozen: T7.2 does not amend `reports/training/checkpoint_selection.{md,json}` or any external run artifact.

## What this report does not claim

- That the T6.2-trained enhancer is a deployable improvement over the T3.2 degraded baseline. It is not.
- That the T6.2-trained enhancer is preferable to the T4.2 MetricGAN+ pretrained baseline. It is not (Δ `-0.0637` vs MetricGAN+).
- That earlier checkpoints would necessarily fall under a more favourable tier. The five evaluated steps all classify as `framework_only`.
- That export must, or must not, proceed in T8.1. T7.2 only sets `export_posture`; the export-or-skip decision is owned by T8.1.

## Next gate

`T8.1_export_or_explicit_skip`.

T7.2 does not start T8.1 in any form. The export-vs-skip decision is owned by T8.1.
