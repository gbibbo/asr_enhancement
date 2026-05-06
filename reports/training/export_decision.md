# T8.1 Export Decision — Explicit Skip

Generated (UTC): `2026-05-06T22:41:41Z`

## Status / Scope

T8.1 is the export-or-explicit-skip gate that follows T7.2 under
`docs/plans/training_datamove1_plan.md` §18. It applies the T7.2 verdict
(`tier = framework_only`, `sub_status = framework_only_strict_negative`,
`deployment_decision = not_selected_for_deployment`,
`export_posture = export_may_proceed_only_as_reproducibility_framework_artifact_or_be_explicitly_skipped_in_T8.1`)
and records the decision **not** to export the selected enhancer.

T8.1 explicitly does **not**:

- run any new evaluation;
- submit any Slurm job;
- create `scripts/training/export_enhancer.py`;
- write any export artifact (`.pt`, `.onnx`, `.tar`, `.zip`, copied
  checkpoint, packaged model directory, alias, or symlink) under
  `$ASR_TRAINING_ROOT/exports/`, the repository, or any other location;
- register a non-null `ENHANCER_VERSION` in `libs/common/versions.py`;
- amend `reports/training/checkpoint_selection.{md,json}` or
  `reports/training/publishability_tier.{md,json}`;
- modify `reports/training/full_training_summary.md`,
  `reports/training/baseline_summary.md`, or
  `reports/training/metricgan_plus_wer.md`;
- modify `docs/model_card.md` (T8.2 owns that);
- modify `configs/`, `libs/`, `scripts/`, `slurm/`;
- modify any external run artifact under
  `runs/t6_2_full_training_2128952/`,
  `runs/t6_3_post_hoc_whisper_full_2129017/`, or
  `runs/t7_1_post_hoc_whisper_step_*/`;
- modify demo / RP files or trackers;
- touch `stash@{0}`.

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

## Inputs (frozen, read-only)

- `reports/training/publishability_tier.md`
- `reports/training/publishability_tier.json`
- `reports/training/checkpoint_selection.md`
- `reports/training/checkpoint_selection.json`
- `reports/training/full_training_summary.md`
- `reports/training/baseline_summary.md`
- `reports/training/metricgan_plus_wer.md`
- `docs/plans/training_datamove1_plan.md` (§17, §18)
- `configs/training/full_training.yaml`

## Selected checkpoint (frozen at T7.1; verified read-only at T8.1)

- Step: `20000`
- Canonical path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt`
- Alias path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt`
- SHA-256: `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e`
- Size on disk (each): `4916439` bytes
- Macro Word Accuracy: `0.5255416`
- Macro WER: `0.4744584`
- Worst-case family Word Accuracy: `0.369799` (`muffled`)
- Δ macro WA vs T3.2 degraded: `-0.2957584`
- Δ macro WA vs T4.2 MetricGAN+ pretrained: `-0.0636584`

## Tier inputs (carried verbatim from T7.2)

| Field | Value |
|---|---|
| `tier` | `framework_only` |
| `sub_status` | `framework_only_strict_negative` |
| `defensible_reason_override_applied` | `false` |
| `deployment_decision` | `not_selected_for_deployment` |
| `selection_purpose` | `reproducibility_and_framework_demonstration_only` |
| `export_posture` | `export_may_proceed_only_as_reproducibility_framework_artifact_or_be_explicitly_skipped_in_T8.1` |
| `metricgan_plus_role` | `prior_negative_baseline_only` |

## Decision

| Field | Value |
|---|---|
| `decision.path` | `explicit_skip` |
| `decision.export_performed` | `false` |
| `decision.enhancer_version` | `null` |
| `decision.exported_artifact_path` | `null` |
| `decision.exported_artifact_sha256` | `null` |

No export artifact is produced. `ENHANCER_VERSION` remains `null` in
`libs/common/versions.py`. No Slurm job is submitted.

## Rationale

1. **Strict-negative tier on the §17 primary metric.** All five evaluated
   candidate checkpoints have `delta_macro_wa_vs_t3_2_degraded` ≤ 0; the
   selected step 20000 has delta `-0.2957584`. There is no marginal case
   and no §17 defensible-reason override.
2. **Worse than the prior negative MetricGAN+ baseline at the macro
   level.** Δ macro WA vs T4.2 MetricGAN+ pretrained is `-0.0636584` —
   the trained enhancer's macro Word Accuracy `0.5255416` is below
   MetricGAN+'s `0.5892`. MetricGAN+ already classified as
   `null_or_negative` and `not_selected` for deployment; T7.2 confirms the
   T6.2-trained enhancer falls into the same posture and is also worse
   than that prior negative baseline at the macro level.
3. **Deployment is closed.** T7.2 set
   `deployment_decision = not_selected_for_deployment`. Producing an
   export artifact under `framework_only_strict_negative` would create a
   deployable-looking file whose existence could be misread as implicit
   endorsement, contrary to plan §20 ("Do not claim ASR improvement
   without WER or Word Accuracy evidence").
4. **Reproducibility is already preserved off-Git.** The canonical
   checkpoint, the alias `latest.pt`, the per-checkpoint
   `eval_metadata.json` files, and the `verify JSON` files all live under
   `$ASR_TRAINING_ROOT/runs/t6_2_full_training_2128952/`,
   `$ASR_TRAINING_ROOT/runs/t6_3_post_hoc_whisper_full_2129017/`, and
   `$ASR_TRAINING_ROOT/runs/t7_1_post_hoc_whisper_step_*/`. Each is
   referenced by its absolute path and SHA-256 from
   `reports/training/checkpoint_selection.json` and
   `reports/training/publishability_tier.json`. Re-packaging adds no
   reproducibility value.
5. **`ENHANCER_VERSION` stays honest.** Leaving the placeholder `None` in
   `libs/common/versions.py` matches the truth: no enhancer is being
   shipped to RP5 from T8.1. Stamping a version under
   `framework_only_strict_negative` would mislead T8.3 and the demo
   branch.
6. **Smallest scope, smallest blast radius.** Explicit skip stays inside
   the training branch's `reports/training/` directory; no new scripts,
   no new Slurm jobs, no scratch writes, no risk of touching T6.2 / T6.3
   / T7.1 / T7.2 evidence, no risk of contaminating T8.2 (model card) or
   T8.3 (handoff) with a deployable-looking artifact.

## Posture flags

- `do_not_modify_model_card: true`
- `do_not_modify_publishability_tier: true`
- `do_not_modify_checkpoint_selection: true`
- `do_not_modify_full_training_summary: true`
- `do_not_modify_baseline_summary: true`
- `do_not_modify_metricgan_plus_wer: true`
- `do_not_modify_external_run_artifacts: true`
- `do_not_modify_configs: true`
- `do_not_modify_libs: true`
- `do_not_modify_scripts: true`
- `do_not_modify_slurm_jobs: true`
- `do_not_create_export_artifact: true`
- `do_not_register_enhancer_version: true`
- `do_not_modify_demo_files: true`
- `do_not_modify_demo_trackers: true`
- `stash_untouched: true`

## Treatment of MetricGAN+

MetricGAN+ pretrained continues to be a **prior negative baseline only**,
never a deployment candidate. T4.2 already classified it as
`null_or_negative` (delta `-0.2321` vs T3.2). T7.2 reaffirmed
`metricgan_plus_role = prior_negative_baseline_only`. T8.1 carries the
same role forward. T8.1 does not modify any T4.2 artifact.

## Slurm policy and forward-looking notification rule

T8.1 submitted no Slurm job:
- `slurm_required_for_t8_1: false`
- `slurm_notification_policy: not_applicable_no_slurm_job_submitted`

Forward-looking rule (recorded for any future Slurm job from this branch,
e.g. an export job for a future `publicable_*` checkpoint, retraining
experiments, ablation evals): include either (a) native Slurm
`--mail-type=END,FAIL --mail-user=<addr>` if the cluster mail relay is
confirmed reliable, or (b) a session-side watcher polling
`./slurm/tools/on_submit.sh sacct -j <id>` / `squeue -u $USER` at ≥30 s
and reporting terminal state, or (c) an explicit "manual check" command
stated up-front. **Not** applied retroactively to T6.2 / T6.3 / T7.1 /
T7.2 jobs.

## Limitations

- Dev-clean only (533 records per family for the val_degraded subset;
  2693 records per family for the T3.2 reference).
- Single ASR model: openai-whisper `base.en` (`20250625`) only.
- Single enhancer architecture: `spectral_unet_small_v1`, 403 201
  parameters, single 20 000-step run with the configured loss / schedule.
- Cropped 4-second val windows via `_maybe_run_whisper_validation` in the
  post-hoc Whisper evaluation mode.
- ASR metrics only (WER and Word Accuracy via `metrics_v1`); no
  PESQ / STOI / MOS.
- No fine-tuning of Whisper.
- Single Whisper version; CUDA decode (fp16, `beam_size=1`,
  `temperature=0.0`).
- Tier rule is applied on macro Word Accuracy over the five official
  degradations; per-family disaggregation reproduces the same
  `null_or_negative` direction.
- Selection inputs are frozen: T8.1 does not amend
  `reports/training/checkpoint_selection.{md,json}`,
  `reports/training/publishability_tier.{md,json}`, or any external run
  artifact.

## What this report does not claim

- That the T6.2-trained enhancer improves ASR over the T3.2 degraded
  baseline. It does not.
- That the T6.2-trained enhancer is preferable to the T4.2 MetricGAN+
  pretrained prior negative baseline. It is not at the macro level
  (delta `-0.0636584`).
- That re-running selection on the same evidence would yield a different
  tier.
- That the explicit skip precludes future re-training under a different
  architecture, loss, or schedule.
- That T8.1 has decided anything for T8.2 or T8.3. T8.2 owns
  `docs/model_card.md`; T8.3 owns handoff.

No ASR improvement is claimed by this report. The T6.2-trained enhancer
is **not deployable** under the §17 tier rule on the available evidence.

## Next gate

`T8.2_model_card`.

T8.1 does not start T8.2 in any form. Tracker closure for T8.1 happens
in a separate authorised step.
