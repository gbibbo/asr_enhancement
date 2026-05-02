---
# Model Card — ASR Enhancement Enhancer
# Status: TEMPLATE / DRAFT — no model trained yet. All performance fields are placeholders.
status: template_draft
template_version: "1"
dataset_version: librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8
public_examples_exclusion_status: complete
model_family: "<!-- PLACEHOLDER: e.g. MetricGAN+, SpeechEnhancer, bypass -->"
enhancer_version: "<!-- PLACEHOLDER: set after T8.1 export -->"
---

> **Status: TEMPLATE / DRAFT**
> No model has been trained.
> No evaluation metrics exist yet.
> T3.1 is unblocked. Public examples exclusion resolved (T2.3b complete). B6.2 must consume the reserved examples from `configs/training/reserved_public_demo_examples.yaml`.

---

## Model overview

| Field | Value |
|---|---|
| Card type | Template — to be completed by T3–T8 tasks |
| Model family | `<!-- PLACEHOLDER: MetricGAN+, SpeechEnhancer, or bypass -->` |
| Enhancer version | `<!-- PLACEHOLDER: set after T8.1 export -->` |
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

Five official degradation families are applied to training and evaluation audio. Parameters are frozen at degradation version `<!-- PLACEHOLDER: DEGRADATION_VERSION, set at B7 -->`.

| Family | Description |
|---|---|
| `far_field_room` | Room reverberation simulating far-field microphone placement |
| `cafe_background` | Background noise typical of a busy café environment |
| `phone_call` | Narrowband telephone codec simulation |
| `muffled` | Low-frequency muffling, e.g. audio heard through a wall or fabric |
| `broadband_hiss` | Broadband white/pink hiss overlay |

Degradation implementation: `libs/audio/degradations.py`
Degradation version: `<!-- PLACEHOLDER: DEGRADATION_VERSION (defined in libs/common/versions.py at B7) -->`

---

## Training procedure

No training has been run yet. This section will be completed by tasks T5–T6.

| Field | Value |
|---|---|
| Training script | `scripts/training/train_enhancer.py` |
| Dry-run config | `configs/training/dry_run.yaml` (to be created at T5.1) |
| Full training config | `configs/training/full_training.yaml` (to be created at T6.1) |
| Run ID | `<!-- PLACEHOLDER: assigned at run time -->` |
| Git commit at run time | `<!-- PLACEHOLDER: record after training job completes -->` |
| Slurm job ID | `<!-- PLACEHOLDER: record after job submission -->` |
| Steps (dry-run) | 100 |
| Steps (full training) | `<!-- PLACEHOLDER: set in full_training.yaml -->` |
| Learning rate | `<!-- PLACEHOLDER: set in training config -->` |
| Batch size | `<!-- PLACEHOLDER: set in training config -->` |
| Random seed | `<!-- PLACEHOLDER: set in training config -->` |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Degradation version | `<!-- PLACEHOLDER: DEGRADATION_VERSION -->` |
| Metrics version | `<!-- PLACEHOLDER: METRICS_VERSION -->` |
| Output artifact root | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/<run_id>/` |

---

## Evaluation setup

Evaluation uses `openai-whisper` on Surrey compute (Slurm). Shared metric implementation: `libs/audio/metrics.py`.

| Field | Value |
|---|---|
| Reference ASR | `openai-whisper` |
| ASR model version | `<!-- PLACEHOLDER: record whisper model size and package version -->` |
| Metrics implementation | `libs/audio/metrics.py` |
| Metrics version | `<!-- PLACEHOLDER: METRICS_VERSION (defined in libs/common/versions.py) -->` |
| Normalization | shared normalization function in `libs/audio/metrics.py` |
| Evaluation granularity | per-degradation results required; average reported separately |
| Evaluation split | `dev-clean` (baseline and training evaluation) |
| Final evaluation split | `test-clean` (only after T7 — not yet available) |

---

## Evaluation results

**No evaluation has been run.** This table will be filled by T3 (baseline) and T7 (selected checkpoint).

### Baseline (no enhancement)

| Degradation | Clean WER | Degraded WER | Clean Word Acc | Degraded Word Acc |
|---|---|---|---|---|
| `far_field_room` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `cafe_background` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `phone_call` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `muffled` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `broadband_hiss` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| **Average** | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |

### MetricGAN+ pretrained evaluation (T4)

| Degradation | Degraded WER | Enhanced WER | Word Acc improvement |
|---|---|---|---|
| `far_field_room` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `cafe_background` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `phone_call` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `muffled` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `broadband_hiss` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| **Average** | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |

### Selected checkpoint evaluation (T7)

| Degradation | Degraded WER | Enhanced WER | Word Acc improvement |
|---|---|---|---|
| `far_field_room` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `cafe_background` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `phone_call` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `muffled` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| `broadband_hiss` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |
| **Average** | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` | `<!-- PLACEHOLDER -->` |

### Publishability tier

Tiers are assigned at T7.2 based on average Word Accuracy improvement:

| Tier | Condition |
|---|---|
| Strong | Average Word Accuracy improvement ≥ 5 percentage points |
| Acceptable | Improvement positive but below 5 percentage points |
| Framework-only | Improvement zero or negative; documented as evaluation framework, not enhancement claim |

**Assigned tier:** `<!-- PLACEHOLDER: assigned at T7.2 -->` — not yet assigned.

---

## Limitations

- **No training run has been completed.** This card will be updated after T5–T8.
- **`train-clean-100` is currently `present_empty`**: the directory exists but contains zero FLAC and transcript files. Training tasks (T5+) must verify or stage usable training data before using this split.
- **Public examples exclusion is complete (T2.3b)**: 10 examples removed from the active manifest. Filtered manifest has 2693 records.
- **Evaluation is Surrey-only**: results use `openai-whisper` on Surrey compute. Demo branch metrics (RP5, `faster-whisper tiny.en`) are cross-validated separately in task B6.5.
- **Python version mismatch**: the Apptainer container provides Python 3.10.13; the nominal training environment specifies 3.11. All required imports verified at 3.10.13.
- **Per-degradation failure modes:** `<!-- PLACEHOLDER: record after T3 and T7 evaluation -->`.
- **If result is bypass-only:** this card must not claim a trained or pretrained enhancer.
- **If result is pretrained-only:** this card must name the pretrained model, its source, and its limitations explicitly.

---

## Ethical and privacy considerations

- **Dataset licence:** LibriSpeech is published under CC BY 4.0 (OpenSLR resource 12). Use consistent with licence terms.
- **Speaker data:** LibriSpeech contains read-aloud speech from volunteer contributors. Speaker IDs are included in the manifest for reproducibility but are not used as training targets.
- **Public demo examples:** the 10 public demo audio files must not appear in any training or validation split. This is enforced by `configs/training/public_examples_excluded.yaml` once B6.2 closes.
- **Demo audio handling:** uploaded audio on the public demo is subject to the privacy and retention policy defined by the `demo-rp5-v1` branch. This training branch does not own or modify that policy.
- **No PII in training targets:** transcript text is from LibriSpeech (public domain literary works). No personal identifiers are used as supervision targets.

---

## Deployment target

- **Platform:** Raspberry Pi 5
- **Runtime branch:** `demo-rp5-v1`
- **Demo ASR:** `faster-whisper tiny.en` (RP5 runtime)
- **Surrey eval ASR:** `openai-whisper` (not deployed to RP5)
- **Exported artifact path:** `<!-- PLACEHOLDER: set after T8.1 export -->`
- **Exported artifact checksum:** `<!-- PLACEHOLDER: set after T8.1 export -->`
- **`ENHANCER_VERSION`:** `<!-- PLACEHOLDER: set after T8.1 export -->`
- **CPU compatibility:** required — RP5 has no GPU
- **Latency constraint:** `<!-- PLACEHOLDER: measure at T8.1 export validation -->`

Handoff procedure (defined in training plan T8.3):
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
| Degradation version | `<!-- PLACEHOLDER: DEGRADATION_VERSION -->` |
| Metrics version | `<!-- PLACEHOLDER: METRICS_VERSION -->` |
| Training run ID | `<!-- PLACEHOLDER: assigned at run time -->` |
| Training git commit | `<!-- PLACEHOLDER: record after job submission -->` |
| Training config path | `<!-- PLACEHOLDER: e.g. configs/training/full_training.yaml -->` |
| Slurm job ID(s) | `<!-- PLACEHOLDER: record after submission -->` |
| Checkpoint path | `<!-- PLACEHOLDER: scratch path outside Git -->` |
| Checkpoint checksum | `<!-- PLACEHOLDER: record at T7.1 selection -->` |

---

## Artifact paths

All heavy artifacts live outside Git under the training root.

| Artifact | Path |
|---|---|
| Training root | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/` |
| Manifest (filtered, active) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered.jsonl` |
| Run outputs | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/<run_id>/` |
| Checkpoints | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/<run_id>/checkpoints/` |
| Exported model | `<!-- PLACEHOLDER: set after T8.1 export -->` |
| Logs | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/` |

**Note:** `scratch4weeks` storage is not permanent. Final artifacts must be exported or transferred through the T8.3 handoff process before the scratch allocation expires.

---

## Reference documents

- Dataset version report: [`reports/training/dataset_version_v1.md`](../reports/training/dataset_version_v1.md)
- Dataset version config: [`configs/training/dataset_version.yaml`](../configs/training/dataset_version.yaml)
- Exclusion gate config: [`configs/training/public_examples_excluded.yaml`](../configs/training/public_examples_excluded.yaml)
- LibriSpeech source config: [`configs/training/librispeech_sources.yaml`](../configs/training/librispeech_sources.yaml)
- Training plan: [`docs/plans/training_datamove1_plan.md`](plans/training_datamove1_plan.md)
- Baseline summary (to be created at T3.3): `reports/training/baseline_summary.md`
- MetricGAN+ pretrained summary (to be created at T4.3): `reports/training/metricgan_pretrained_summary.md`
- Full training summary (to be created at T6.3): `reports/training/full_training_summary.md`
