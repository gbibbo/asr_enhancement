# T8.3 Handoff — Framework / Reproducibility, No-Artifact

Generated (UTC): `2026-05-06T23:23:07Z`

## Status / Scope

T8.3 is the handoff gate that follows T7.1 (deterministic checkpoint
selection), T7.2 (publishability tier assignment), T8.1 (export
decision), and T8.2 (model-card closure) under
`docs/plans/training_datamove1_plan.md` §18. Given that T8.1 took the
`explicit_skip` path and T8.2 closed `docs/model_card.md` for
`framework_only_strict_negative`, T8.3 is a **framework / reproducibility
handoff only** — specifically an **explicit no-artifact handoff** — and
not a deployable-model handoff.

This report records, in writing, the no-artifact decision, the carried-
forward tier and posture, the reproducibility-only references for the
selected checkpoint and its evidence chain, and the explicit "demo
branch should do nothing on RP5" instruction. **No exported model
artifact exists**, **ENHANCER_VERSION remains null**, **demo / RP
integration is not triggered by this branch**, and **MetricGAN+ remains
prior_negative_baseline_only**.

T8.3 explicitly does **not**:

- run any new evaluation;
- submit any Slurm job;
- copy, package, export, alias, symlink, or otherwise produce any
  deployable model artifact (`.pt`, `.onnx`, `.tar`, `.zip`, copied
  checkpoint, packaged model directory) under `$ASR_TRAINING_ROOT/exports/`,
  the repository, or any other location;
- register a non-null `ENHANCER_VERSION` in `libs/common/versions.py`;
- modify `docs/model_card.md` (T8.2 closed it for this outcome and T8.3
  does not reopen it);
- modify `reports/training/export_decision.{md,json}`,
  `reports/training/publishability_tier.{md,json}`,
  `reports/training/checkpoint_selection.{md,json}`,
  `reports/training/full_training_summary.md`,
  `reports/training/baseline_summary.md`,
  `reports/training/metricgan_plus_wer.md`, or
  `reports/training/metricgan_pretrained_summary.md`;
- modify `configs/`, `libs/`, `scripts/`, or `slurm/`;
- modify any external run artifact under
  `runs/t6_2_full_training_2128952/`,
  `runs/t6_3_post_hoc_whisper_full_2129017/`, or
  `runs/t7_1_post_hoc_whisper_step_*_*/`;
- modify demo / RP files or trackers;
- open a pull request into `demo-rp5-v1`;
- touch `stash@{0}`.

## Decision summary

Under T8.1 `explicit_skip`, no exported model artifact exists. The
T6.2-trained `spectral_unet_small_v1` enhancer is **not deployable** on
the available evidence and **the enhancer is not recommended for
deployment**. The selected checkpoint at step 20000 is retained on
scratch as a **reproducibility / framework reference** only, addressed by
absolute path and SHA-256, and is **not** a deployment artifact. The
demo branch must keep its previous (pre-T8.3) enhancer choice in effect;
**ENHANCER_VERSION remains null** in `libs/common/versions.py`. **This
branch is not RP5-ready and not demo-ready**. **No ASR improvement is
claimed**.

## Identities

| Field | Value |
|---|---|
| Training branch | `feature/training-datamove1-v1` |
| Integration branch | `demo-rp5-v1` |
| HEAD before T8.3 | `9354f4c21461939c33622d7fde89a82c1b847b9d` |
| Plan reference | `docs/plans/training_datamove1_plan.md` §18 (T8.3) |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Training split version | `devclean_speaker_split_v1` |
| Metrics version | `metrics_v1` |
| Degradation version | `degradation_v1` |
| Enhancer architecture | `spectral_unet_small_v1` (403 201 parameters) |
| ASR model (Surrey eval) | `openai-whisper base.en (20250625)` |
| ASR device | `cuda` |
| `eval_per_family_cap` | `533` |
| `ENHANCER_VERSION` (`libs/common/versions.py`) | `None` (unchanged) |

## Selected checkpoint as reproducibility reference (not a deployment artifact)

The values below are carried verbatim from
`reports/training/checkpoint_selection.json` and
`reports/training/publishability_tier.json`. T8.3 does not amend either
file. **The selected checkpoint is not deployable.**

| Field | Value |
|---|---|
| Step | `20000` |
| Canonical path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt` |
| Alias path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt` |
| SHA-256 (canonical and alias) | `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e` |
| Size on disk (each) | `4916439` bytes |
| Macro Word Accuracy | `0.5255416` |
| Macro WER | `0.4744584` |
| Worst-case family Word Accuracy | `0.369799` (`muffled`) |
| Δ macro WA vs T3.2 degraded | `-0.2957584` |
| Δ macro WA vs T4.2 MetricGAN+ pretrained | `-0.0636584` |
| Tier (T7.2) | `framework_only` |
| Sub-status (T7.2) | `framework_only_strict_negative` |
| Deployment decision (T7.2) | `not_selected_for_deployment` |
| Selection purpose (T7.2) | `reproducibility_and_framework_demonstration_only` |
| Export decision (T8.1) | `explicit_skip` |
| Export performed | `false` |
| Exported artifact path | `null` |
| Exported artifact SHA-256 | `null` |

## MetricGAN+ posture

**MetricGAN+ remains prior_negative_baseline_only.** T4.2 classified
MetricGAN+ pretrained as `null_or_negative` (Δ macro WA `-0.2321` vs
T3.2 degraded). T7.2 reaffirmed `metricgan_plus_role =
prior_negative_baseline_only`. T8.1 carried that posture forward. T8.3
carries the same role forward and does not modify any T4.2 / MetricGAN+
artifact. MetricGAN+ is not a deployment candidate, not an RP5 input,
and not a demo input from this branch.

## What the demo branch should do

- Nothing on RP5. **Demo / RP integration is not triggered by this
  branch.**
- Do not run `prewarm_cache.py` or `validate_cache.py` for a "new"
  enhancer — there is no new enhancer.
- Do not modify the RP5 `.env` to point at any artifact produced by this
  branch.
- Do not bump `ENHANCER_VERSION` — there is no new value to register.
- Do not register a new artifact, open a deployment PR, or treat the
  selected checkpoint as a deployable input.
- If the demo branch wants a written confirmation, link this
  `reports/training/handoff.md` from its own tracker. No code change is
  required on the demo side as a result of this T8.3 closure.

## What the demo branch should not do

- Do not treat the selected checkpoint at
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt`
  as deployable.
- Do not point the demo runtime at the canonical or alias path.
- Do not import the selected checkpoint into the bypass enhancer
  pipeline, the MetricGAN+ pipeline, or any new pipeline.
- Do not publish the selected checkpoint as a model release, a Hugging
  Face entry, or any other public artifact.

## Slurm policy and forward-looking notification rule

T8.3 submitted no Slurm job:

- `slurm_required_for_t8_3: false`
- `slurm_notification_policy: not_applicable_no_slurm_job_submitted`

Forward-looking rule (recorded for any future Slurm job from this
branch — e.g. retraining experiments, ablation evals, or an export job
for a future `publicable_*` checkpoint): include either (a) native Slurm
`--mail-type=END,FAIL --mail-user=<addr>` if the cluster mail relay is
confirmed reliable, or (b) a session-side watcher polling
`./slurm/tools/on_submit.sh sacct -j <id>` / `squeue -u $USER` at ≥30 s
and reporting terminal state, or (c) an explicit "manual check" command
stated up-front. **Not** applied retroactively to T6.2 / T6.3 / T7.1 /
T7.2 / T8.1 / T8.2 jobs.

## Evidence manifest

All SHA-256s below were recomputed at T8.3 generation time. The first
seven match the values already recorded in
`docs/progress/training_datamove1_progress.yaml::t8_2_evidence.source_inputs`
verbatim; the remaining three are recomputed first-class references for
reports T8.2 did not directly consume.

| Path | SHA-256 | Size (bytes) | Role |
|---|---|---|---|
| `docs/model_card.md` | `cce2356ac1b5d85143fd73b65f73c88cceef12c6fdb9a2c02bc2f69cf0968c93` | 33084 | T8.2 closed model card (framework_only_strict_negative) |
| `reports/training/export_decision.md` | `bf8d18930e22523dcc0181806f60f24d5aec09135e4f495e995d056d0064abd4` | 10044 | T8.1 explicit_skip export decision (Markdown) |
| `reports/training/export_decision.json` | `7cee47023b8adcad0c3105276f00819cc68d45a18707dc217c09880546b63678` | 6893 | T8.1 explicit_skip export decision (JSON) |
| `reports/training/publishability_tier.md` | `03bb3bd9b8717dc7db4ebcc75c85b9839921327078a4d6671dcb4a0a5e26eb42` | 8762 | T7.2 publishability tier assignment (Markdown) |
| `reports/training/publishability_tier.json` | `14d4a8b6034dea106f4b99816d6c84d5ecd7990c0ee889e90c8b722c5778640a` | 6453 | T7.2 publishability tier assignment (JSON) |
| `reports/training/checkpoint_selection.md` | `1e2b99d79fdac1c031b1abb6e69a4913295026ae199a552b4f980a46a1a8373c` | 4107 | T7.1 deterministic checkpoint selection (Markdown) |
| `reports/training/checkpoint_selection.json` | `756cd39c294f1edc373fdbe54e12c7da0409a5bc36dcf8ae46db8924ef6f5ec3` | 9065 | T7.1 deterministic checkpoint selection (JSON) |
| `reports/training/full_training_summary.md` | `34d9aa0f645b203ff033915145bbcacb124e6fee089c5b267ad1c685b413d219` | 13702 | T6.3 full-training summary |
| `reports/training/baseline_summary.md` | `46866753051b96c6bb5b5b4ffc0c5899684baa1c682311c9fd64bb0e44046027` | 3228 | T3.3 baseline (clean + degraded) summary |
| `reports/training/metricgan_plus_wer.md` | `35ee596d13d822a666934026de7b0c3ee48539f91bd7d4003bc7cc11350155c4` | 5806 | T4.2 MetricGAN+ pretrained WER report (prior_negative_baseline_only) |
| `reports/training/metricgan_pretrained_summary.md` | `bd27502e45ee6dcda43d06de61edbd60fc75004031d42ad9bb5f4bca62fb00d5` | 9471 | T4.3 MetricGAN+ pretrained summary (prior_negative_baseline_only) |

Selected checkpoint reference (off-Git, scratch-only — not a deployment
artifact):

| Path | SHA-256 | Size (bytes) | Role |
|---|---|---|---|
| `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt` | `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e` | 4916439 | Reproducibility-only canonical reference; not a deployment artifact |
| `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt` | `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e` | 4916439 | Reproducibility-only alias; SHA-256 equals canonical; not a deployment artifact |

## Limitations

- Dev-clean only (533 records per family for the val_degraded subset;
  2693 records per family for the T3.2 reference).
- Single ASR model: openai-whisper `base.en` (`20250625`) only.
- Single enhancer architecture: `spectral_unet_small_v1`, 403 201
  parameters, single 20 000-step run with the configured loss / schedule.
- Cropped 4-second val windows via `_maybe_run_whisper_validation` in
  the post-hoc Whisper evaluation mode.
- ASR metrics only (WER and Word Accuracy via `metrics_v1`); no
  PESQ / STOI / MOS.
- No fine-tuning of Whisper.
- Single Whisper version; CUDA decode (fp16, `beam_size=1`,
  `temperature=0.0`).
- Tier rule applied on macro Word Accuracy over the five official
  degradations only; per-family disaggregation reproduces the same
  `null_or_negative` direction.
- Selection inputs are frozen: T8.3 does not amend
  `reports/training/checkpoint_selection.{md,json}`,
  `reports/training/publishability_tier.{md,json}`,
  `reports/training/export_decision.{md,json}`,
  `reports/training/full_training_summary.md`,
  `reports/training/baseline_summary.md`,
  `reports/training/metricgan_plus_wer.md`,
  `reports/training/metricgan_pretrained_summary.md`,
  `docs/model_card.md`, or any external run artifact.

## What this report does not claim

- That the T6.2-trained enhancer improves ASR over the T3.2 degraded
  baseline. It does not.
- That the T6.2-trained enhancer is preferable to the T4.2 MetricGAN+
  pretrained prior negative baseline. It is not at the macro level
  (Δ macro WA `-0.0636584`).
- That re-running selection on the same evidence would yield a different
  tier.
- That the explicit-skip / no-artifact handoff precludes future
  re-training under a different architecture, loss, or schedule.
- That T8.3 has decided anything for the demo branch beyond "do nothing
  on RP5 from this branch's T8.3 closure". Future demo decisions remain
  the demo branch's own.

**The selected checkpoint is not deployable. The enhancer is not
recommended for deployment. This branch is not RP5-ready and not
demo-ready.** **No ASR improvement is claimed.**

## Cross-references (read-only)

- [`docs/model_card.md`](../../docs/model_card.md)
- [`reports/training/export_decision.md`](export_decision.md)
- [`reports/training/publishability_tier.md`](publishability_tier.md)
- [`reports/training/checkpoint_selection.md`](checkpoint_selection.md)
- [`reports/training/full_training_summary.md`](full_training_summary.md)
- [`reports/training/baseline_summary.md`](baseline_summary.md)
- [`reports/training/metricgan_plus_wer.md`](metricgan_plus_wer.md)
- [`reports/training/metricgan_pretrained_summary.md`](metricgan_pretrained_summary.md)
- [`docs/plans/training_datamove1_plan.md`](../../docs/plans/training_datamove1_plan.md) (§18)

## Next gate

`training_branch_complete_no_artifact_handoff`.

T8.3 does not start any successor task. The training branch is complete
with respect to the deployable-artifact path under
`framework_only_strict_negative` / T8.1 `explicit_skip`. Tracker closure
for T8.3 is recorded in a separate authorised step (Commit B), and the
backfill of `t8_3_evidence.result_commit` is recorded in a third
authorised step (Commit C). Commit A (this report) does not update the
trackers and does not close T8.3.
