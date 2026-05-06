---
# Model Card — ASR Enhancement Enhancer
# Status: framework-only / strict-negative outcome closed at T8.2. No enhancer was exported. No deployable model is claimed.
status: framework_only_strict_negative
template_version: "2"
dataset_version: librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8
public_examples_exclusion_status: complete
model_family: "spectral_unet_small_v1 (T6.2-trained; not selected for deployment; retained as reproducibility / framework reference)"
enhancer_version: "null — no enhancer exported; T8.1 explicit_skip; ENHANCER_VERSION unchanged in libs/common/versions.py"
selected_checkpoint_step: 20000
selected_checkpoint_sha256: "a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e"
tier: framework_only
sub_status: framework_only_strict_negative
deployment_decision: not_selected_for_deployment
selection_purpose: reproducibility_and_framework_demonstration_only
metricgan_plus_role: prior_negative_baseline_only
export_performed: false
exported_artifact_path: null
exported_artifact_sha256: null
---

> **Status: framework-only / strict-negative — closed at T8.2.**
> The T6.2-trained `spectral_unet_small_v1` enhancer (403 201 parameters,
> 20 000 steps, `devclean_speaker_split_v1`) was evaluated end-to-end and
> **did not improve ASR** over the unenhanced T3.2 degraded baseline.
> T7.1 deterministically selected step 20000 (macro Word Accuracy
> `0.5255416`, macro WER `0.4744584`, SHA-256
> `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e`).
> T7.2 assigned tier `framework_only`, sub_status
> `framework_only_strict_negative`, and
> `deployment_decision = not_selected_for_deployment`. T8.1 took the
> `explicit_skip` path: **no export artifact was produced**, no
> `ENHANCER_VERSION` was registered (`libs/common/versions.py`
> `ENHANCER_VERSION` remains `None`), and no Slurm job was submitted.
> The selected checkpoint is retained on scratch only as a
> **reproducibility / framework reference**, not as a deployable model.
> T3.1 clean baseline: WER `0.0645`, Word Accuracy `0.9361` (2693 records,
> openai-whisper `base.en 20250625`, `metrics_v1`).
> T3.2 degraded baseline: macro WER `0.1843`, macro Word Accuracy
> `0.8213` (13 465 records across five families).
> T4.2 MetricGAN+ pretrained: macro WER `0.4310`, macro Word Accuracy
> `0.5892`, tier `null_or_negative` — `prior_negative_baseline_only`,
> not a deployment candidate.
> Δ macro Word Accuracy of the T6.2-trained enhancer vs T3.2 degraded:
> `−0.2957584`. Δ vs T4.2 MetricGAN+ pretrained: `−0.0636584`. **No ASR
> improvement is claimed.**
> See
> [`reports/training/export_decision.md`](../reports/training/export_decision.md),
> [`reports/training/publishability_tier.md`](../reports/training/publishability_tier.md),
> [`reports/training/checkpoint_selection.md`](../reports/training/checkpoint_selection.md),
> [`reports/training/full_training_summary.md`](../reports/training/full_training_summary.md),
> [`reports/training/metricgan_pretrained_summary.md`](../reports/training/metricgan_pretrained_summary.md),
> and [`reports/training/metricgan_plus_wer.md`](../reports/training/metricgan_plus_wer.md).
> B6.2 must consume the reserved examples from `configs/training/reserved_public_demo_examples.yaml`.

---

## Model overview

| Field | Value |
|---|---|
| Card type | Closed at T8.2 — framework-only / strict-negative; **not deployable** |
| Model family | `spectral_unet_small_v1` (T6.2-trained); **not selected for deployment**; retained as reproducibility / framework reference |
| Enhancer version | `null` — no artifact exported (T8.1 `explicit_skip`); `ENHANCER_VERSION` unchanged in `libs/common/versions.py` |
| Selected checkpoint step | 20000 |
| Selected checkpoint SHA-256 | `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e` |
| Tier | `framework_only` |
| Sub-status | `framework_only_strict_negative` |
| Deployment decision | `not_selected_for_deployment` |
| Selection purpose | `reproducibility_and_framework_demonstration_only` |
| MetricGAN+ role | `prior_negative_baseline_only` |
| Training branch | `feature/training-datamove1-v1` |
| Integration branch | `demo-rp5-v1` |
| Reference ASR (Surrey eval) | `openai-whisper` |
| Demo ASR (Raspberry Pi 5) | `faster-whisper tiny.en` |
| Primary metrics | WER, Word Accuracy |
| Deployment target | Raspberry Pi 5 public demo (`demo-rp5-v1` branch) |
| Training host | datamove1 + Surrey Slurm (Apptainer) |
| Apptainer image | `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` |
| Python (container) | 3.10.13 |

---

## Intended use

This enhancer is designed to improve ASR robustness for English speech audio that has been degraded by controlled acoustic transformations. The intended deployment context is:

- **Target language:** English
- **Input:** 16 kHz mono WAV audio, degraded by one of the five official degradation families
- **Output:** Enhanced audio intended for downstream ASR transcription
- **Deployment:** Raspberry Pi 5 public demo via the `demo-rp5-v1` branch
- **ASR pipeline:** enhanced audio → `faster-whisper tiny.en` on RP5

---

## Not intended use

- Live or streaming audio
- Non-English speech
- High-stakes decisions (medical, legal, safety-critical)
- Environments not represented by the five official degradation families
- Any use where the enhancer is described as production-ready before T8 export validation passes

---

## Training data

### Dataset

| Field | Value |
|---|---|
| Dataset | LibriSpeech |
| Source root | `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech` |
| Licence | CC BY 4.0 (OpenSLR resource 12) |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |

### Manifest

| Field | Value |
|---|---|
| Manifest path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered.jsonl` |
| Manifest records | 2693 (10 public demo examples excluded) |
| Manifest SHA-256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Manifest scope | `dev-clean` only (only currently usable split) |
| Source manifest (pre-exclusion) | `librispeech_manifest_v1.jsonl`, 2703 records, SHA-256 `bacd6f7ba89c…` |
| Manifest committed to Git | No — lives under scratch path |

Reference: [`reports/training/dataset_version_v1.md`](../reports/training/dataset_version_v1.md) and [`configs/training/dataset_version.yaml`](../configs/training/dataset_version.yaml).

### Split policy

| Split | Role | Status |
|---|---|---|
| `dev-clean` | Baseline validation | `present` — 2703 records |
| `train-clean-100` | Training | `present_empty` — directory exists, zero FLAC files; **not in current manifest** |
| `dev-other` | Optional harder validation | `missing` |
| `test-clean` | Final evaluation | `present_empty` — not used before T7 |
| `test-other` | Final evaluation harder | `missing` |
| `train-clean-360` | Extended training | `missing` |
| `train-other-500` | Full training | `missing` |

**Note on `train-clean-100`:** This split is the intended future training data, but it is currently marked `present_empty` in the source configuration and is not represented in the current manifest (`librispeech_manifest_v1.jsonl`). Training tasks (T5+) must verify or stage usable training data before using this split.

### Public-demo exclusion gate

✅ **Status: `complete`** (resolved by T2.3b)

10 public demo examples have been reserved and excluded from the manifest.

- Reserved examples config: [`configs/training/reserved_public_demo_examples.yaml`](../configs/training/reserved_public_demo_examples.yaml)
- Gate config: [`configs/training/public_examples_excluded.yaml`](../configs/training/public_examples_excluded.yaml)
- Excluded IDs count: 10
- Excluded audio SHA-256 count: 10
- Filtered manifest: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered.jsonl`
- Filtered manifest records: 2693
- `t3_blocked_while_pending: false`
- B6.2 must consume the reserved examples from `configs/training/reserved_public_demo_examples.yaml`.

---

## Degradation bank

Five official degradation families are applied to training and evaluation audio. Parameters are frozen at degradation version `degradation_v1`.

| Family | Description |
|---|---|
| `far_field_room` | Room reverberation simulating far-field microphone placement |
| `cafe_background` | Background noise typical of a busy café environment |
| `phone_call` | Narrowband telephone codec simulation |
| `muffled` | Low-frequency muffling, e.g. audio heard through a wall or fabric |
| `broadband_hiss` | Broadband white/pink hiss overlay |

Degradation implementation: `libs/audio/degradations.py`
Degradation version: `degradation_v1` (defined in `libs/common/versions.py`, frozen at T3.2a)

---

## Training procedure

T6.2 full training is complete. Values below are quoted from
[`reports/training/full_training_summary.md`](../reports/training/full_training_summary.md)
(T6.3 consolidation report) and from the T6.2 run's `runtime:` block in
`runs/t6_2_full_training_2128952/config.yaml`. The training config in
this repo is `configs/training/full_training.yaml` (not modified by
T8.2).

| Field | Value |
|---|---|
| Training script | `scripts/training/train_enhancer.py` |
| Full training config | `configs/training/full_training.yaml` |
| Enhancer architecture | `spectral_unet_small_v1` |
| Enhancer parameter count | 403 201 (within the `[200_000, 1_000_000]` budget) |
| Run ID | `t6_2_full_training_2128952` |
| Run dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952` |
| Slurm job ID (T6.2 training) | `2128952` |
| Slurm state / ExitCode | `COMPLETED` / `0:0` |
| Slurm elapsed | `00:06:33` |
| Slurm node / partition | `aisurrey26` / `a100` |
| AllocTRES | `cpu=8, gres/gpu:nvidia_a100-sxm4-80gb=1, mem=32G, node=1` |
| Code commit at run start | `6a0c25911aea3125eff25a1511b2864fa1e2d8c1` |
| T6.2 prep commit | `e5ab5501ca33790e094df0f764a262b694b1f009` |
| Steps executed | 20 000 |
| Checkpoint cadence | `save_every_steps=2500`, `keep_last_n=5` (plus `latest.pt`) |
| Validation cadence | `val_every_steps=1000` (20 val rows in `metrics.csv`) |
| Logging cadence | `log_every_steps=100` (200 train rows in `metrics.csv`) |
| Other hyperparameters (LR, batch size, seed, loss, schedule) | See `runs/t6_2_full_training_2128952/config.yaml` (`runtime:` block) and `configs/training/full_training.yaml`; not duplicated here |
| Whisper inline validation during training | `false` (deferred to T6.3b post-hoc evaluation) |
| Train clean records | 2160 |
| Val clean records | 533 |
| Train degraded records | 10 800 (5 × 2160) |
| Val degraded records | 2665 (5 × 533) |
| Training split version | `devclean_speaker_split_v1` |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Degradation version | `degradation_v1` |
| Metrics version | `metrics_v1` |
| Output artifact root | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/` |
| `metrics.csv` finite-loss check | pass (all values finite; train loss 2.743973 → 1.157826 → 1.505096 over 20 000 steps; val loss 2.011323 at step 20 000) |
| Checkpoint metadata / state-dict round-trip | pass |
| Result family | fine-tuned (own training run); **not selected for deployment** under §17 tier rule |

---

## Evaluation setup

Evaluation uses `openai-whisper` on Surrey compute (Slurm). Shared metric implementation: `libs/audio/metrics.py`.

| Field | Value |
|---|---|
| Reference ASR | `openai-whisper` |
| ASR model version | `base.en` (openai-whisper 20250625) |
| Metrics implementation | `libs/audio/metrics.py` |
| Metrics version | `metrics_v1` |
| Normalization | shared normalization function in `libs/audio/metrics.py` |
| Evaluation granularity | per-degradation results required; average reported separately |
| Evaluation split | `dev-clean` (baseline and training evaluation) |
| Final evaluation split | `test-clean` (only after T7 — not yet available) |

---

## Evaluation results

T3.1 clean baseline and T3.2 degraded baseline are complete (`openai-whisper base.en 20250625`, `metrics_v1`, `degradation_v1`). T7 (selected checkpoint) results remain pending.

### Baseline (no enhancement)

Mean per-record WER and Word Accuracy (`base.en`, `metrics_v1`, `dev-clean`, 2693 records per family).

| Degradation | Clean WER | Degraded WER | Δ WER | Clean Word Acc | Degraded Word Acc | Δ WA |
|---|---|---|---|---|---|---|
| `broadband_hiss` | 0.0645 | 0.1271 | +0.0626 | 0.9361 | 0.8742 | -0.0619 |
| `cafe_background` | 0.0645 | 0.1632 | +0.0987 | 0.9361 | 0.8390 | -0.0971 |
| `far_field_room` | 0.0645 | 0.1659 | +0.1014 | 0.9361 | 0.8356 | -0.1005 |
| `muffled` | 0.0645 | 0.3863 | +0.3218 | 0.9361 | 0.6361 | -0.3000 |
| `phone_call` | 0.0645 | 0.0789 | +0.0144 | 0.9361 | 0.9217 | -0.0144 |
| **Average (macro)** | **0.0645** | **0.1843** | **+0.1198** | **0.9361** | **0.8213** | **-0.1148** |

Dataset version: `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8`. Source clean manifest SHA-256: `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b`. Source degraded manifest SHA-256: `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c`. Full baseline report: [`reports/training/baseline_degraded_wer.md`](../reports/training/baseline_degraded_wer.md).

### MetricGAN+ pretrained evaluation (T4.2)

Mean per-record WER and Word Accuracy on the dev-clean degraded benchmark
(`base.en`, `metrics_v1`, `degradation_v1`, enhancer `metricgan_plus_pretrained`,
enhancement `enhancement_v1`, 2693 records per family). Source manifest SHA-256
`544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9`. Full
Slurm job `2127693`. Canonical detail: [`reports/training/metricgan_plus_wer.md`](../reports/training/metricgan_plus_wer.md).
T4.3 summary: [`reports/training/metricgan_pretrained_summary.md`](../reports/training/metricgan_pretrained_summary.md).

| Degradation | Degraded WER | Enhanced WER | Degraded Word Acc | Enhanced Word Acc | Δ Word Acc |
|---|---|---|---|---|---|
| `far_field_room`  | 0.1659 | 0.5920 | 0.8356 | 0.4264 | -0.4092 |
| `cafe_background` | 0.1632 | 0.4716 | 0.8390 | 0.5401 | -0.2989 |
| `phone_call`      | 0.0789 | 0.1592 | 0.9217 | 0.8429 | -0.0788 |
| `muffled`         | 0.3863 | 0.6657 | 0.6361 | 0.3978 | -0.2383 |
| `broadband_hiss`  | 0.1271 | 0.2666 | 0.8742 | 0.7390 | -0.1352 |
| **Average (macro)** | **0.1843** | **0.4310** | **0.8213** | **0.5892** | **-0.2321** |

Δ vs clean (macro only; T3.1 has no per-family values): WER +0.3665, Word Accuracy −0.3469.

**MetricGAN+ pretrained tier (T4.2): `null_or_negative`** — Δ macro Word Accuracy = −0.2321 vs T3.2 degraded baseline. The pretrained MetricGAN+ enhancer **worsened** Whisper `base.en` ASR on this benchmark; every family individually shows positive ΔWER and negative ΔWA. The pretrained enhancer is **not** a candidate for deployment. No fine-tuning has been performed; no checkpoint has been selected; no enhancer artifact has been exported.

### Selected checkpoint evaluation (T7.1 selection / T6.3b post-hoc Whisper)

Step 20000 was selected deterministically by the §17 rule (primary
metric: average Word Accuracy over the five official degradations;
tiebreaker 1: best worst-case per-family Word Accuracy; tiebreaker 2:
most recent checkpoint). Per-family numbers below are quoted **verbatim**
from
[`reports/training/checkpoint_selection.json`](../reports/training/checkpoint_selection.json)
and
[`reports/training/full_training_summary.md`](../reports/training/full_training_summary.md);
the source eval is the T6.3b post-hoc Whisper run (`base.en 20250625`,
`metrics_v1`, `degradation_v1`, 533 records per family;
`eval_metadata.json` at
`runs/t6_3_post_hoc_whisper_full_2129017/eval_metadata.json`).

| Degradation | Degraded WER (T3.2) | Enhanced WER (step 20000) | Degraded Word Acc (T3.2) | Enhanced Word Acc (step 20000) |
|---|---|---|---|---|
| `broadband_hiss`  | 0.1271 | 0.414715 | 0.8742 | 0.585285 |
| `cafe_background` | 0.1632 | 0.469957 | 0.8390 | 0.530043 |
| `far_field_room`  | 0.1659 | 0.484717 | 0.8356 | 0.515283 |
| `muffled`         | 0.3863 | 0.630201 | 0.6361 | 0.369799 |
| `phone_call`      | 0.0789 | 0.372702 | 0.9217 | 0.627298 |
| **Average (macro)** | **0.1843** | **0.4744584** | **0.8213** | **0.5255416** |

Macro deltas (carried verbatim from
[`reports/training/publishability_tier.json`](../reports/training/publishability_tier.json)
and
[`reports/training/export_decision.json`](../reports/training/export_decision.json)):

- Δ macro Word Accuracy vs T3.2 degraded baseline: **`−0.2957584`** (every
  per-family Word Accuracy is also below the corresponding T3.2 degraded
  family baseline; worst-case family `muffled` at WA `0.369799`).
- Δ macro Word Accuracy vs T4.2 MetricGAN+ pretrained prior negative
  baseline: **`−0.0636584`** (the T6.2-trained enhancer is below the T4.2
  MetricGAN+ baseline at the macro level).

The five evaluated candidate steps (10000, 12500, 15000, 17500, 20000)
all classify as `framework_only`; the per-candidate tier table is
recorded in
[`reports/training/publishability_tier.md`](../reports/training/publishability_tier.md).

### Publishability tier (assigned at T7.2)

§17 tier rule (verbatim):

| Tier | Condition (Δ macro Word Accuracy vs T3.2 degraded) |
|---|---|
| `publicable_strong` | Δ ≥ +0.05 |
| `publicable_acceptable` | 0 < Δ < +0.05 |
| `framework_only` | Δ ≤ 0 |

**Assigned tier:** `framework_only`.
**Sub-status:** `framework_only_strict_negative` — every evaluated
candidate has Δ ≤ 0 and every per-family Word Accuracy is also below the
T3.2 degraded family baseline; the §17 "defensible reason" override is
**not** invoked (`defensible_reason_override_applied: false`).
**Deployment decision:** `not_selected_for_deployment`.
**Selection purpose:** `reproducibility_and_framework_demonstration_only`.
This is a **modelling outcome**, not a pipeline failure — T6.3b
contractually validated the post-hoc Whisper evaluation pipeline as
green (2665 / 2665 transcriptions, all guards green). Source:
[`reports/training/publishability_tier.md`](../reports/training/publishability_tier.md).

### Export decision (T8.1)

T8.1 took the `explicit_skip` path under §18, applied to the T7.2
verdict (`tier = framework_only`,
`sub_status = framework_only_strict_negative`,
`deployment_decision = not_selected_for_deployment`,
`export_posture = export_may_proceed_only_as_reproducibility_framework_artifact_or_be_explicitly_skipped_in_T8.1`).
Source:
[`reports/training/export_decision.md`](../reports/training/export_decision.md)
and
[`reports/training/export_decision.json`](../reports/training/export_decision.json).

| Field | Value |
|---|---|
| `decision.path` | `explicit_skip` |
| `decision.export_performed` | `false` |
| `decision.enhancer_version` | `null` |
| `decision.exported_artifact_path` | `null` |
| `decision.exported_artifact_sha256` | `null` |
| ENHANCER_VERSION | `None` — unchanged in [`libs/common/versions.py`](../libs/common/versions.py) |
| Slurm job submitted | none (`slurm_required_for_t8_1: false`) |
| `metricgan_plus_role` | `prior_negative_baseline_only` |

Selected checkpoint identity (frozen at T7.1; verified read-only at
T8.1):

| Field | Value |
|---|---|
| Step | 20000 |
| Canonical path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt` |
| Alias path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt` |
| SHA-256 | `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e` |
| Size on disk (each) | 4 916 439 bytes |
| Macro Word Accuracy | `0.5255416` |
| Macro WER | `0.4744584` |
| Worst-case family Word Accuracy | `0.369799` (`muffled`) |
| Δ macro Word Accuracy vs T3.2 degraded | `−0.2957584` |
| Δ macro Word Accuracy vs T4.2 MetricGAN+ pretrained | `−0.0636584` |

Rationale (summary, full text in
[`reports/training/export_decision.md`](../reports/training/export_decision.md)):
all five evaluated candidate checkpoints have
`delta_macro_wa_vs_t3_2_degraded ≤ 0`; the selected step 20000 has delta
`−0.2957584` — there is no marginal case and no §17 defensible-reason
override. The T6.2-trained enhancer's macro Word Accuracy `0.5255416` is
also below the T4.2 MetricGAN+ pretrained prior negative baseline
(`0.5892`). T7.2 already set
`deployment_decision = not_selected_for_deployment`. Producing an export
artifact under `framework_only_strict_negative` would create a
deployable-looking file in a regime where no ASR improvement is
supported by metrics; explicit skip preserves an honest record.
Reproducibility is already preserved off-Git via the canonical
checkpoint and the alias `latest.pt` on scratch, both referenced by
absolute path and SHA-256 from the closed reports. `ENHANCER_VERSION`
remains `None` in `libs/common/versions.py` — no enhancer is being
shipped from T8.1, so stamping a version would mislead T8.3 and the
demo branch.

T8.1 explicitly does **not** start T8.3, does **not** modify any
external run artifact under
`runs/t6_2_full_training_2128952/`,
`runs/t6_3_post_hoc_whisper_full_2129017/`, or
`runs/t7_1_post_hoc_whisper_step_*/`, does **not** touch the closed
T3 / T4 / T6 reports, and does **not** touch demo / RP files or
trackers.

---

## Limitations

- **The T6.2-trained `spectral_unet_small_v1` enhancer falls below the T3.2 degraded baseline at every evaluated checkpoint.** Selected step 20000 has Δ macro Word Accuracy `−0.2957584` vs T3.2 degraded and `−0.0636584` vs T4.2 MetricGAN+ pretrained. Tier: `framework_only_strict_negative`. Deployment decision: `not_selected_for_deployment`. T8.1 took `explicit_skip`: **no export, no `ENHANCER_VERSION`, no deployable artifact**. The selected checkpoint exists only as a reproducibility / framework reference; **T8.3 must not treat it as a deployable artifact**. **No ASR improvement is claimed.**
- **MetricGAN+ pretrained worsened ASR on this benchmark (T4.2)**: tier `null_or_negative` (Δ macro Word Accuracy `−0.2321` vs T3.2 degraded baseline). The pretrained enhancer is **not** recommended for the public Raspberry Pi 5 demo and is **not** a deployment candidate. Role at T7.2 / T8.1: `prior_negative_baseline_only`. The B6.5 RP5 cross-validation request, if executed, must treat MetricGAN+ pretrained strictly as a documented negative comparison and keep the bypass enhancer as the RP5 default. See [`reports/training/metricgan_pretrained_summary.md`](../reports/training/metricgan_pretrained_summary.md).
- **Per-degradation failure modes (T6.3b post-hoc Whisper, step 20000):** worst-case family is `muffled` (Word Accuracy `0.369799`, WER `0.630201`); every per-family Word Accuracy is below the corresponding T3.2 degraded family baseline. The same worst-case family (`muffled`) holds at every evaluated step (10000, 12500, 15000, 17500, 20000) per [`reports/training/publishability_tier.md`](../reports/training/publishability_tier.md).
- **Most plausible attribution (per T7.2):** architecture / loss / schedule limitations of `spectral_unet_small_v1` (403 201 parameters) at 20 000 steps with the configured schedule on the speaker-disjoint dev-clean split. T6.3 already validated the post-hoc Whisper evaluation pipeline as contractually green; this is a modelling outcome, not an evaluation defect.
- **Single architecture, single run:** `spectral_unet_small_v1`, 403 201 parameters, single 20 000-step run with the configured loss / schedule; no ablations.
- **Cropped 4-second val windows:** T6.3b uses `_maybe_run_whisper_validation` with the val DataLoader's centred 4-second crop (matching `PairedDevCleanDataset.mode="val"`). For longer utterances this evaluates the central window, not the full waveform.
- **Evaluation cap:** T7 evaluations use `eval_per_family_cap = 533` (533 records per family for the val_degraded subset); T3.2 reference uses 2693 records per family.
- **ASR metrics only:** WER and Word Accuracy via `metrics_v1`; no PESQ / STOI / MOS.
- **Single ASR model and single Whisper version:** `base.en (20250625)` only; CUDA decode (fp16, `beam_size=1`, `temperature=0.0`); no fine-tuning of Whisper.
- **`train-clean-100` is currently `present_empty`**: the directory exists but contains zero FLAC and transcript files. Any future retraining must verify or stage usable training data before using this split.
- **Public examples exclusion is complete (T2.3b)**: 10 examples removed from the active manifest. Filtered manifest has 2693 records.
- **Evaluation is Surrey-only**: results use `openai-whisper` on Surrey compute. Demo branch metrics (RP5, `faster-whisper tiny.en`) are cross-validated separately in task B6.5.
- **Python version mismatch**: the Apptainer container provides Python 3.10.13; the nominal training environment specifies 3.11. All required imports verified at 3.10.13.
- **Selection inputs are frozen.** T8.2 does **not** amend `reports/training/checkpoint_selection.{md,json}`, `reports/training/publishability_tier.{md,json}`, `reports/training/export_decision.{md,json}`, `reports/training/full_training_summary.md`, `reports/training/baseline_summary.md`, or `reports/training/metricgan_plus_wer.md`; it does **not** modify `configs/training/full_training.yaml`, `libs/common/versions.py`, or any external run artifact.

---

## Ethical and privacy considerations

- **Dataset licence:** LibriSpeech is published under CC BY 4.0 (OpenSLR resource 12). Use consistent with licence terms.
- **Speaker data:** LibriSpeech contains read-aloud speech from volunteer contributors. Speaker IDs are included in the manifest for reproducibility but are not used as training targets.
- **Public demo examples:** the 10 public demo audio files must not appear in any training or validation split. This is enforced by `configs/training/public_examples_excluded.yaml` once B6.2 closes.
- **Demo audio handling:** uploaded audio on the public demo is subject to the privacy and retention policy defined by the `demo-rp5-v1` branch. This training branch does not own or modify that policy.
- **No PII in training targets:** transcript text is from LibriSpeech (public domain literary works). No personal identifiers are used as supervision targets.

---

## Deployment target

- **Platform (nominal):** Raspberry Pi 5
- **Runtime branch:** `demo-rp5-v1`
- **Demo ASR:** `faster-whisper tiny.en` (RP5 runtime)
- **Surrey eval ASR:** `openai-whisper` (not deployed to RP5)
- **Exported artifact path:** `null` — T8.1 `explicit_skip`; **no exported artifact was created**.
- **Exported artifact checksum:** `null` — T8.1 `explicit_skip`.
- **`ENHANCER_VERSION`:** `null` — unchanged in [`libs/common/versions.py`](../libs/common/versions.py); no enhancer version was registered.
- **CPU compatibility:** not measured — no export was performed at T8.1; RP5 CPU compatibility was therefore not characterised.
- **Latency constraint:** not measured — no export was performed at T8.1; CPU latency on RP5 was not characterised.
- **Deployment decision (T7.2 / T8.1):** `not_selected_for_deployment`. The selected checkpoint is retained only as a reproducibility / framework reference under `runs/t6_2_full_training_2128952/checkpoints/` on scratch.
- **MetricGAN+ pretrained:** `prior_negative_baseline_only` — also **not** a deployment candidate.

> **Handoff procedure — not applicable for the current T8.1 `explicit_skip` outcome.** No `ENHANCER_VERSION` is being shipped to RP5 from T8.1, so the seven steps below must **not** be executed against the current selected checkpoint. The procedure is retained verbatim as the **future** handoff template for any later, publicable enhancer that crosses the §17 tier rule. T8.3 owns the actual handoff scoping under the current state and must not treat the selected checkpoint as a deployable artifact.

Handoff procedure (template defined in training plan §18 Task T8.3 — for future use only):
1. Set `ENHANCER_VERSION` in RP5 `.env`.
2. Restart demo worker.
3. Run `prewarm_cache.py --bypass-budget-check --enhancer-version=<new>`.
4. Run `validate_cache.py`.
5. Validate 2 examples manually.
6. Run public smoke test.
7. Roll back to previous `ENHANCER_VERSION` if validation fails.

---

## Reproducibility

| Field | Value |
|---|---|
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Manifest SHA-256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Manifest records | 2693 (filtered; 10 public demo examples excluded) |
| Manifest path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered.jsonl` |
| Branch | `feature/training-datamove1-v1` |
| Apptainer image | `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` |
| Python (container) | 3.10.13 |
| Degradation version | `degradation_v1` |
| Metrics version | `metrics_v1` |
| Training run ID | `t6_2_full_training_2128952` |
| Training git commit | `6a0c25911aea3125eff25a1511b2864fa1e2d8c1` (HEAD at T6.2 run start; T6.2 prep commit `e5ab5501ca33790e094df0f764a262b694b1f009`) |
| Training config path | `configs/training/full_training.yaml` |
| Slurm job IDs | T6.2 training: `2128952`; T6.3a post-hoc Whisper smoke: `2129005`; T6.3b post-hoc Whisper full: `2129017`; T7.1 per-checkpoint Whisper jobs: `2129063` (step 10000), `2129064` (step 12500), `2129065` (step 15000), `2129066` (step 17500); T7.2 / T8.1: no Slurm job submitted |
| Checkpoint path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/checkpoint_step_0020000.pt` |
| Checkpoint alias path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t6_2_full_training_2128952/checkpoints/latest.pt` |
| Checkpoint SHA-256 | `a6ae240a1b210ad551d8b6b9dd38c9de4c25bb65daf7218a46014452a4939b5e` |
| Checkpoint role | reproducibility / framework reference only — **not deployable** |

---

## Artifact paths

All heavy artifacts live outside Git under the training root.

| Artifact | Path |
|---|---|
| Training root | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/` |
| Manifest (filtered, active) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered.jsonl` |
| Run outputs | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/<run_id>/` |
| Checkpoints | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/<run_id>/checkpoints/` |
| Exported model | `null` — T8.1 `explicit_skip`; **no exported artifact was created**. `ENHANCER_VERSION` remains `None` in `libs/common/versions.py`. |
| Logs | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/` |

**Note:** `scratch4weeks` storage is not permanent. Final artifacts must be exported or transferred through the T8.3 handoff process before the scratch allocation expires.

---

## Reference documents

- Dataset version report: [`reports/training/dataset_version_v1.md`](../reports/training/dataset_version_v1.md)
- Dataset version config: [`configs/training/dataset_version.yaml`](../configs/training/dataset_version.yaml)
- Exclusion gate config: [`configs/training/public_examples_excluded.yaml`](../configs/training/public_examples_excluded.yaml)
- LibriSpeech source config: [`configs/training/librispeech_sources.yaml`](../configs/training/librispeech_sources.yaml)
- Training plan: [`docs/plans/training_datamove1_plan.md`](plans/training_datamove1_plan.md)
- Baseline summary (T3.3): [`reports/training/baseline_summary.md`](../reports/training/baseline_summary.md)
- MetricGAN+ pretrained summary (T4.3): [`reports/training/metricgan_pretrained_summary.md`](../reports/training/metricgan_pretrained_summary.md)
- MetricGAN+ pretrained canonical evidence (T4.2): [`reports/training/metricgan_plus_wer.md`](../reports/training/metricgan_plus_wer.md)
- Full training summary (T6.3): [`reports/training/full_training_summary.md`](../reports/training/full_training_summary.md)
- Checkpoint selection (T7.1): [`reports/training/checkpoint_selection.md`](../reports/training/checkpoint_selection.md), [`reports/training/checkpoint_selection.json`](../reports/training/checkpoint_selection.json)
- Publishability tier (T7.2): [`reports/training/publishability_tier.md`](../reports/training/publishability_tier.md), [`reports/training/publishability_tier.json`](../reports/training/publishability_tier.json)
- Export decision / explicit skip (T8.1): [`reports/training/export_decision.md`](../reports/training/export_decision.md), [`reports/training/export_decision.json`](../reports/training/export_decision.json)
- Cache and model version source: [`libs/common/versions.py`](../libs/common/versions.py) — `ENHANCER_VERSION` remains `None` after T8.1 `explicit_skip`.
