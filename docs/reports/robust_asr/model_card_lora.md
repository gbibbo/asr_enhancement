# Model Card — Whisper + LoRA (robust_asr)

Produced by: P0.5 (template; placeholders resolved by downstream tasks).
Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Card lifecycle: created P0.5 → fields filled across P1–P9 → finalized in P9.1 / P10.1.

This is a template. Every `TODO_FILLED_IN_<task_id>` marker is the
contract that the named task will resolve the field with concrete
evidence (a metric, an artifact path, a config value, or a
human-authored statement). Do not delete markers; replace them.

## intended_use

Primary intended use of this artifact.

- Use case: TODO_FILLED_IN_P9.1 — public RP5 demo and offline batch
  evaluation of robust speech-to-text on adversarial / noisy English audio.
- Out-of-scope uses: TODO_FILLED_IN_P9.1 — non-English audio; safety-critical
  decisions; long-form transcription beyond evaluated clip length.

## training_data

Datasets, splits, and preprocessing used for LoRA fine-tuning.

- Source datasets and versions: TODO_FILLED_IN_P1.1 — declared in
  `configs/robust_asr/data_v1.yaml` (LibriSpeech splits + selected OOD-real source).
- LoRA training manifest: TODO_FILLED_IN_P1.2 — manifest path under
  `artifacts/robust_asr/manifests/` with row count and SHA256.
- Degradation manifest: TODO_FILLED_IN_P1.4 — `configs/robust_asr/degradation_manifest_v1.yaml`
  declaring degradation families, ranges, and DEGRADATION_VERSION.
- Speaker-disjoint guarantee: TODO_FILLED_IN_P1.3 — manifest summary
  asserting lora_train / router_train / validation / locked_test are
  speaker-disjoint.

## hyperparameters

LoRA training configuration.

- LoRA rank, alpha, target modules, dropout: TODO_FILLED_IN_P4.1 —
  recorded in the run config under `artifacts/robust_asr/lora_full/`.
- Optimizer, learning rate schedule, batch size, gradient accumulation,
  max steps: TODO_FILLED_IN_P4.1 — recorded in the same run config.
- Smoke-run hyperparameters used for Decision A: TODO_FILLED_IN_P3.1 —
  recorded under `artifacts/robust_asr/lora_smoke/`.
- Random seeds and determinism flags: TODO_FILLED_IN_P4.1.

## evaluation_data

Datasets used to evaluate the trained artifact.

- Locked test split definition: TODO_FILLED_IN_P1.1 — split rule in
  `configs/robust_asr/data_v1.yaml`.
- OOD-real evaluation source: TODO_FILLED_IN_P1.2 — selected source
  (Common Voice / TED-LIUM / CHiME-6) and per-split file count.
- Public-demo exclusion: TODO_FILLED_IN_P8.2 — the 10 public demo
  examples must not appear in any evaluation split.

## metrics

Quantitative results, per-degradation and per-split.

- Baseline (whisper_base_ct2_int8) WER / Word Accuracy: TODO_FILLED_IN_P2.1 —
  table at `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`.
- LoRA smoke (Decision A) outcome: TODO_FILLED_IN_P3.2 — PASS/FAIL plus
  per-degradation deltas vs. baseline.
- Full LoRA fp16 evaluation: TODO_FILLED_IN_P4.2 — table at
  `artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet`; report
  at `reports/robust_asr/lora/full_lora_eval.md`.
- LoRA → CT2 int8 preservation: TODO_FILLED_IN_P4.3 — table at
  `artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet`;
  preservation report at
  `reports/robust_asr/lora/lora_ct2_int8_preservation.md`.
- AssemblyAI reference numbers: TODO_FILLED_IN_P5.1 — table at
  `artifacts/robust_asr/eval_tables/assemblyai.parquet`.
- System-level metrics (selector / router applied): TODO_FILLED_IN_P8.1.

## fairness_and_limitations

Known limitations of the artifact and its evaluation.

- Language and accent coverage: TODO_FILLED_IN_P9.1 — English-only;
  accent distribution inherited from training_data sources.
- Domain coverage: TODO_FILLED_IN_P9.1 — read-prompt LibriSpeech style
  dominates; spontaneous and far-field conditions only partially covered.
- Known degradation regimes where artifact underperforms baseline:
  TODO_FILLED_IN_P4.2.

## risks

Risks of deploying or relying on this artifact.

- Mis-transcription in safety-critical contexts: TODO_FILLED_IN_P9.1.
- Public-example leakage risk and mitigation: TODO_FILLED_IN_P8.2.
- AssemblyAI reference dependency and cost: TODO_FILLED_IN_P5.1.

## license

License of the artifact and of upstream components.

- Whisper base model license: TODO_FILLED_IN_P9.1 — MIT (upstream OpenAI
  Whisper); confirm release version.
- Training data licenses: TODO_FILLED_IN_P1.1 — license URL per source
  in `configs/robust_asr/data_v1.yaml`.
- LoRA adapter and merged-fp16 artifact license: TODO_FILLED_IN_P9.1.

## contact

Maintainer and reporting channel.

- Primary maintainer: Gabriel Bibbó (`gabobibbo@gmail.com`).
- Issue / handoff channel: TODO_FILLED_IN_P9.1 — handoff package path
  and contact details for RP5 integration.
