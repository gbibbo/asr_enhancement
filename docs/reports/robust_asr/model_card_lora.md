# Model Card — Whisper + LoRA (robust_asr)

Produced by: P0.5 (template) → finalized by `model_router_card_completion` CHANGE_SCOPE on accepted_report_commit `d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d` per agent plan Section 10 items 11–12.
Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Card lifecycle: created P0.5 → fields filled across P1–P9 → finalized via `model_router_card_completion` before P10.2 final_asset_audit.

This card describes the deployed robust_asr artifact set as of handoff tag `handoff/20260514-64eba43` → `64eba4345f3207af38f0fba8ac2c43c6084e8852`. Several fields are deliberately recorded as **N/A** because the corresponding tasks were closed under `SKIPPED_BY_DECISION_A` (full LoRA), `SKIPPED_BY_OUTCOME_E` (ML-router and oracle), or `HALTED` (AssemblyAI under `BLOCKED_API`). Those N/A entries are NOT positive claims; `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system} = false` (held).

## intended_use

Primary intended use of this artifact.

- Use case: per `artifacts/robust_asr/handoff/README.md` §1, the deployed runtime is `whisper_base_ct2_int8` only. The handoff supports public RP5 demo and offline batch evaluation of English speech-to-text on adversarial / noisy audio, under the deterministic selector (`deterministic_selector_v1`). The "Whisper + LoRA" card title refers to the project plan's intended scope; the deployed-backend set excludes any LoRA adapter (see §6.2 of the handoff README and `lora_status = SKIPPED_BY_DECISION_A`).
- Out-of-scope uses: non-English audio; safety-critical decisions; long-form transcription beyond the evaluated clip lengths in `artifacts/robust_asr/manifests/librispeech_validation.parquet` and `librispeech_locked_test.parquet` (mean ≈ 7.2 s, see `reports/robust_asr/manifest_summary.md`). The handoff README §6 details the disabled claims.

## training_data

Datasets, splits, and preprocessing used for LoRA fine-tuning.

- Source datasets and versions: **PARTIAL** — LibriSpeech subsets (CC BY 4.0, OpenSLR #12) restored at the canonical root (see `reports/robust_asr/data_inventory.md`); subsets in scope are `train-clean-100` (251 speakers / ~102 h), `dev-clean` (40 speakers / 5.39 h), `test-clean` (40 speakers / ~5.47 h). The Section 1.1 OOD-real fallbacks (Common Voice English, TED-LIUM R3, CHiME-6) are not resolved on host; marker `BLOCKED_OOD_PUBLIC` is active and `claims_enabled.ood_real = false`. Configuration: `configs/robust_asr/data_v1.yaml`.
- LoRA training manifest: `artifacts/robust_asr/manifests/librispeech_lora_train.parquet` (sha256 `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a`; rows 22 507; 200 speakers; ~79.58 h; columns: `audio_id, source_dataset, source_subset, speaker_id, chapter_id, utterance_id, audio_path_or_uri, audio_sha256, duration_s, sample_rate, num_frames, split_label`). Companion train-clean-100 manifest entries are summarized in `reports/robust_asr/manifest_summary.md`.
- Degradation manifest: `configs/robust_asr/degradation_v1.yaml` declares `degradation_version = degradation_v1`, `master_seed = 20260508`, source manifests = `librispeech_validation.parquet` + `librispeech_locked_test.parquet` (eval-only; train-time degradation is owned by P3.1/P4.1), and families `[clean, cafe_noise, phone_band, far_field_room]` over tiers `[id, ood_param]` (see `reports/robust_asr/degradation_v1_summary.md`, sentinel `OK_DEGRADATION_V1`). `DEGRADATION_VERSION = degradation_v1` is recorded in `libs/common/versions.py`.
- Speaker-disjoint guarantee: **PARTIAL** — `reports/robust_asr/manifest_summary.md` records that `librispeech_lora_train` (200 speakers), `librispeech_router_train` (51 speakers), `librispeech_validation` (40 speakers), and `librispeech_locked_test` (40 speakers) are disjoint at the LibriSpeech level. Section 3 leakage tests (`tests/robust_asr/test_leakage.py`) PASS (5/5 in the latest pytest run, 137/137 total). `BLOCKED_OOD_PUBLIC` keeps the OOD-real disjointness conjunct out of scope until the OOD-real source resolves on host.

## hyperparameters

LoRA training configuration.

- LoRA rank, alpha, target modules, dropout: **N/A — skipped by Decision A**. Full LoRA training (P4.1) is `SKIPPED_BY_DECISION_A` because `Decision_A_smoke = FAIL` (mechanical per agent plan §5.1). See `reports/robust_asr/lora/decision_a_smoke.md`. No `artifacts/robust_asr/lora_full/` run config was produced; no rank/alpha/target-modules/dropout/optimizer/seed values exist.
- Optimizer, learning rate schedule, batch size, gradient accumulation, max steps: **N/A — skipped by Decision A** (same as above; no full-LoRA run config was produced).
- Smoke-run hyperparameters used for Decision A: P3.1 produced `reports/robust_asr/lora/lora_smoke_report.md` and `reports/robust_asr/lora/lora_smoke_result.json` (Slurm job 2131980). Smoke metrics: `macro_wa_gain = -0.12843`, `max_family_wa_gain = -0.11345`, `clean_wa_regression = 0.11345`, `per_family_wa_gain_variance = 1.79e-4`. Per-family WA gain (LoRA − baseline): clean `-0.11345`, cafe_noise `-0.14546`, far_field_room `-0.14358`, muffled_lowpass `-0.11834`, phone_band `-0.12132`. The smoke run used the configuration in `configs/robust_asr/lora_smoke.yaml`; full smoke-config values are recorded in the result JSON and in the artifact tree under `artifacts/robust_asr/lora_smoke/`.
- Random seeds and determinism flags: **N/A — skipped by Decision A**. Full-LoRA seeds were never recorded because P4.1 was skipped. The smoke run's seeds are recorded inside `lora_smoke_result.json` and `artifacts/robust_asr/lora_smoke/export_smoke_result.json`.

## evaluation_data

Datasets used to evaluate the trained artifact.

- Locked test split definition: `librispeech_locked_test.parquet` (sha256 `ad4f401e06e3c840aaa5d34e5cae22d1cdbb1fb34c7ea671dde0f8a712661da8`; 2 620 rows; 40 speakers; 5.40 h). Split rule recorded in `configs/robust_asr/data_v1.yaml` and summarized in `reports/robust_asr/manifest_summary.md`.
- OOD-real evaluation source: **HALTED / BLOCKED_OOD_PUBLIC** — no Section 1.1 OOD-real source resolves on host (Common Voice English: empty `clips/` and no transcripts; TED-LIUM R3 and CHiME-6 absent). Marker `BLOCKED_OOD_PUBLIC` is active; `claims_enabled.ood_real = false`. See `reports/robust_asr/data_inventory.md` Executive summary.
- Public-demo exclusion: `artifacts/robust_asr/demo/demo_examples_manifest.json` (manifest_version `v1.2-deviation-enacted`; sha256 `850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba`; 8 entries) is the demo bundle. The deviation `P8_2_demo_only_upstream_overlap` (status `ENACTED`) makes the demo bundle UI/demo-only. The C5 exclusion verification was completed in P10.1 and PASSED: per-parquet intersections of demo `audio_id`, demo `upstream_audio_id`, and demo `audio_sha256` against `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` and `artifacts/robust_asr/router/selector_evidence.parquet` are all empty (see `reports/robust_asr/final_verification.md` "C5 EXCLUSION VERIFICATION" section).

## metrics

Quantitative results, per-degradation and per-split.

- Baseline (`whisper_base_ct2_int8`) WER / Word Accuracy: per `reports/robust_asr/baseline_whisper_base.md` and `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` (sha256 `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6`; 53 230 rows; 0 failed; backend `faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8`; normalization `normalization_v1`; `total_cost_usd = 0.0000`). Per-family mean WER / WA: `clean` 0.0709 / 0.9367; `cafe_noise` 0.1241 / 0.8784; `far_field_room` 0.1410 / 0.8623; `muffled_lowpass` 0.1072 / 0.9027; `phone_band` 0.6058 / 0.6034. validate_eval_table.py emits `OK_EVAL_TABLE` (re-confirmed in P10.1).
- LoRA smoke (Decision A) outcome: **FAIL** (sentinel `OK_LORA_SMOKE_DECISION:FAIL`, mechanical per agent plan §5.1). Per `reports/robust_asr/lora/decision_a_smoke.md`: `macro_wa_gain = -0.12843` (threshold ≥ 0.005, NOT satisfied); `max_family_wa_gain = -0.11345` (threshold ≥ 0.010, NOT satisfied); `clean_wa_regression = 0.11345` (threshold ≤ 0.010 PASS / ≤ 0.020 PARTIAL, NOT satisfied at either tier). All five evaluated families show negative WA gain vs. baseline. Decision_A_smoke = FAIL routed `tasks.P4.{1,2,3}.status` to `SKIPPED_BY_DECISION_A` and set `lora_status = SKIPPED_BY_DECISION_A`.
- Full LoRA fp16 evaluation: **N/A — skipped by Decision A**. P4.2 is `SKIPPED_BY_DECISION_A`; `artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet` was never produced; `reports/robust_asr/lora/full_lora_eval.md` does not exist.
- LoRA → CT2 int8 preservation: **N/A — skipped by Decision A**. P4.3 is `SKIPPED_BY_DECISION_A`; `artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet` was never produced; `reports/robust_asr/lora/lora_ct2_int8_preservation.md` does not exist; `artifacts/robust_asr/lora_ct2_int8/` is absent. LoRA is NOT a deployed backend (handoff README §6.2; `claims_enabled.positive_lora = false`).
- AssemblyAI reference numbers: **N/A — HALTED under BLOCKED_API**. P5.1 is `HALTED` because `ASSEMBLYAI_API_KEY` is unset, exit-8 guard `BLOCKED_API` engaged. `artifacts/robust_asr/eval_tables/assemblyai.parquet` was never produced. AssemblyAI is NOT an enabled backend (handoff README §6.3; `claims_enabled.cloud_tradeoff = false`); the handoff backend config contains only `whisper_base_ct2_int8` and contains no `ASSEMBLYAI_API_KEY` / `sk_*` / `Bearer` token (verified by `verify_handoff_package.py --strict` A6, re-confirmed in P10.1).
- System-level metrics (selector applied): per `reports/robust_asr/system/system_eval.md` (first line `positive_system: false`): under `OUTCOME_E_NARROWED_SCOPE` with the single deployable transcript-producing backend `whisper_base_ct2_int8`, `mean WER selector = 0.209797 = mean WER baseline`; `mean_regret_selector = 0` and paired bootstrap 95% CI on `(regret_selector − regret_baseline) = [0.000000, 0.000000]`; `mean_regret_selector < mean_regret_baseline` is `False`. The deterministic selector's only divergence from always-baseline is 28 `ask_repeat` rows (selector_reason = `no_speech`). `Decision_D_positive_system.outcome = false`; `claims_enabled.positive_system = false`.

## fairness_and_limitations

Known limitations of the artifact and its evaluation.

- Language and accent coverage: English-only. Accent distribution is inherited from LibriSpeech `train-clean-100` / `dev-clean` / `test-clean` (US-leaning read prompts); the OOD-real pathway that would have introduced Common Voice multi-accent / TED-LIUM is `BLOCKED_OOD_PUBLIC` (`claims_enabled.ood_real = false`). See `reports/robust_asr/data_inventory.md`.
- Domain coverage: read-prompt LibriSpeech style dominates (per the manifests in `reports/robust_asr/manifest_summary.md`). Spontaneous speech and conversational far-field conditions are only partially represented via `degradation_v1` (`far_field_room`, `cafe_noise`, `phone_band`, `muffled_lowpass` synthesized from `dev-clean` / `test-clean` per `reports/robust_asr/degradation_v1_summary.md`). No genuine far-field corpus is in scope.
- Known degradation regimes where artifact underperforms baseline: **N/A — skipped by Decision A** for the LoRA artifact (no full-LoRA evaluation was produced). For the deployed `whisper_base_ct2_int8` baseline itself, per `reports/robust_asr/baseline_whisper_base.md` the `phone_band` family shows a markedly higher mean WER (0.6058) than `clean` / `cafe_noise` / `far_field_room` / `muffled_lowpass` (0.07–0.14), establishing `phone_band` as the worst-case in-scope condition for the deployed backend.

## risks

Risks of deploying or relying on this artifact.

- Mis-transcription in safety-critical contexts: handoff README §1 declares the deployed runtime is for public RP5 demo and offline batch evaluation only; safety-critical use is OUT-OF-SCOPE per the `intended_use` section above. The handoff README §6 enumerates disabled-claims and explicitly states the runtime supports no positive system claim (`claims_enabled.positive_system = false`).
- Public-example leakage risk and mitigation: the demo bundle `artifacts/robust_asr/demo/demo_examples_manifest.json` (manifest sha256 `850c02db…`) overlaps the upstream LibriSpeech dev-clean corpus at the upstream level (5 affected utterances, 5 affected speakers; disclosed in handoff README §6.4 as the C4 disclosure under deviation `P8_2_demo_only_upstream_overlap` status `ENACTED`). Mitigation: the demo bundle is UI/demo-only (`claims_enabled.*` all `false`) and the C5 exclusion verification (P10.1) PROVED that demo `audio_id`, demo `upstream_audio_id`, and demo `audio_sha256` are all disjoint from `artifacts/robust_asr/eval_tables/**.parquet` and from `artifacts/robust_asr/router/selector_evidence.parquet` (sentinel `C5_EXCLUSION_PASS`; see `reports/robust_asr/final_verification.md`).
- AssemblyAI reference dependency and cost: **N/A — HALTED under BLOCKED_API**. AssemblyAI is not an enabled backend, the handoff contains no AssemblyAI credentials (verified by `verify_handoff_package.py --strict` A6), no AssemblyAI API call is made by the deployed runtime, and `total_cost_usd = 0.0000` for the bundled baseline evaluation (`reports/robust_asr/baseline_whisper_base.md`). No cost or quota dependency exists for the deployed runtime.

## license

License of the artifact and of upstream components.

- Whisper base model license: MIT (upstream OpenAI Whisper). The deployed backend is `whisper_base_ct2_int8` (faster_whisper 1.2.1 conversion of `whisper_base_en` to CT2 int8), as recorded in `reports/robust_asr/baseline_whisper_base.md` (`backend_versions = ['faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8']`). Upstream releases referenced via `libs/common/versions.py`.
- Training data licenses: LibriSpeech is licensed CC BY 4.0 (OpenSLR #12, https://www.openslr.org/12). License URL is recorded in `configs/robust_asr/data_v1.yaml` and `reports/robust_asr/data_inventory.md`. The OOD-real Section 1.1 sources (Common Voice / TED-LIUM R3 / CHiME-6) would have separate licenses but are not in scope under `BLOCKED_OOD_PUBLIC`.
- LoRA adapter and merged-fp16 artifact license: **N/A — skipped by Decision A**. No LoRA adapter and no merged-fp16 artifact were produced (P4.{1,2,3} = `SKIPPED_BY_DECISION_A`). LoRA is NOT a deployed backend.

## contact

Maintainer and reporting channel.

- Primary maintainer: Gabriel Bibbó (`gabobibbo@gmail.com`).
- Issue / handoff channel: handoff package at `artifacts/robust_asr/handoff/` (canonical tag `handoff/20260514-64eba43` → commit `64eba4345f3207af38f0fba8ac2c43c6084e8852`, present locally and on `origin`); RP5-side validation template at `artifacts/robust_asr/handoff/handoff_validation_template.md`. Contact details in handoff README §8.
