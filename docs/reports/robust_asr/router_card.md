# Router Card (robust_asr)

Produced by: P0.5 (template) → finalized by `model_router_card_completion` CHANGE_SCOPE on accepted_report_commit `d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d` per agent plan Section 10 items 11–12.
Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Card lifecycle: created P0.5 → fields filled across P6–P8 → finalized via `model_router_card_completion` before P10.2 final_asset_audit.

This card describes the deployed router as of handoff tag `handoff/20260514-64eba43` → `64eba4345f3207af38f0fba8ac2c43c6084e8852`. The deployed router is a **deterministic selector** (`deterministic_selector_v1`), not a learned ML router. Several router-card fields originally reserved for the ML-router branch are recorded as **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`** because tasks `P6.2`, `P7.1`, `P7.2` are `SKIPPED_BY_OUTCOME_E`. Those N/A entries are NOT positive claims; `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system} = false` (held).

## intended_use

Role of the router in the robust_asr system.

- Purpose: at inference time, decide which deployable backend handles a given input clip. Per `artifacts/robust_asr/router/selected_router/deterministic_selector.json`, the deployable action set is `[whisper_base_ct2_int8, ask_repeat]`. `assemblyai` and `whisper_lora_ct2_int8` are present in the action vocabulary but unreachable at runtime: `assemblyai_available = false` (BLOCKED_API), `lora_available = false` (SKIPPED_BY_DECISION_A). See handoff README §6.2 (LoRA not deployed) and §6.3 (AssemblyAI not enabled).
- Decision kind (learned router vs. deterministic selector): **deterministic selector** (`deterministic_selector_v1`). Per `artifacts/robust_asr/router/selected_router/metadata.json`: `selector_kind = deterministic_selector`, `outcome_e_deterministic_selector = true`. The ML-router branch was deselected under `OUTCOME_E_DETERMINISTIC_SELECTOR`; `tasks.P6.2`, `tasks.P7.1`, `tasks.P7.2` = `SKIPPED_BY_OUTCOME_E`. Section reference: agent plan §1642–§1652 + §4001–§4046 (Branch B).

## inputs

Features consumed by the router.

- Feature set and feature provenance: **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `extract_router_features.py` (P6.2) was skipped; `artifacts/robust_asr/router/router_features.parquet` was never produced. The deterministic selector consumes only the per-row `audio_id, reference_normalized, whisper_base_ct2_int8_wer, whisper_base_ct2_int8_latency_ms, no_speech_prob_proxy, avg_logprob_proxy, condition_family, degradation_id, source_split` columns of `artifacts/robust_asr/router/selector_evidence.parquet` (sha256 `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7`, 53 230 rows; see `reports/robust_asr/router/selector_evidence_summary.md`). Decode-feature proxy policy: `no_speech_prob` is proxied from `normalized_transcript == ""` (1.0 / 0.0); `avg_logprob` is fixed at 0.0 because the escalation branch is unreachable (`assemblyai_available = false`).
- Feature dimensionality and dtype: **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`** (no router_features.parquet exists). The deterministic selector operates on the proxy scalars listed above.
- Audio-side preprocessing (sample rate, framing, normalization): the deterministic selector inherits the baseline backend's preprocessing (faster_whisper 1.2.1 default for `whisper_base_en_ct2_int8`); `normalization_version = normalization_v1` per `artifacts/robust_asr/router/selected_router/deterministic_selector.json`. Per the selector-evidence summary, sample rate / framing are inherited from `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` (53 230 rows produced by P2.1 under `faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8`).

## decision_rule

How the router maps inputs to back-end choices.

- Decision rule (model class, thresholds, fallbacks): the deployed selector is the §5.5 deterministic constants block recorded in `artifacts/robust_asr/router/selected_router/deterministic_selector.json`: `ask_repeat_threshold = -1.0`, `escalate_threshold = -0.5`, `no_speech_threshold = 0.6`, `health_check_ttl_seconds = 300.0`. Deployable action set: `[whisper_base_ct2_int8, ask_repeat]`. Decision rule (effective): if `no_speech_prob_proxy >= no_speech_threshold` then `ask_repeat`; else if `assemblyai_available && avg_logprob_proxy <= escalate_threshold` then `assemblyai` (currently unreachable, `assemblyai_available = false`); else `whisper_base_ct2_int8`. Predicate-parity check (P7.3) recorded 0/53 230 disagreements between the packaged selector and the build-time selector (`reports/robust_asr/router/selector_final_eval.md`). Package contents: `deterministic_selector.json` (sha256 `41d194218b52c13b795d782eb92c381ac3eaa696f56fd217cab43e6a059df3fd`), `metadata.json`, `rp5_inference.py` (sha256 `62f0caab558dbd26dd63e9cdf3c931831b527a0ec9f520811d145e7408378427`), `test_vectors.json` (sha256 `e57fc83e8e19763389a02e9aa6798e3e70026f7a2c041162fa33a3dec732739d`).
- Selector vs. learned router selection: **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `tasks.P7.1` is `SKIPPED_BY_OUTCOME_E`; the ML-router was never trained. Decision C was driven by Branch B routing (selector-evidence path) at the P5/P6/P7 gates because the deployable transcript-producing backend count = 1 (only `whisper_base_ct2_int8`); per agent plan §1642–§1652 the deterministic selector is mandatory in this regime.
- Calibration and threshold tuning: **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `tasks.P7.2` is `SKIPPED_BY_OUTCOME_E`. The deterministic selector's thresholds are §5.5 plan constants (not learned); see `decision_rule` above.

## training_data

Data used to train (or define) the router.

- Router training matrix: **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `tasks.P6.2` is `SKIPPED_BY_OUTCOME_E`; `train_matrix` / `val_matrix` / `test_locked_matrix` were never produced. The deterministic selector is defined by §5.5 plan constants and consumes `artifacts/robust_asr/router/selector_evidence.parquet` (53 230 rows) directly — see `reports/robust_asr/router/selector_evidence_summary.md`.
- Oracle table backing per-row labels: **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `artifacts/robust_asr/oracle/oracle_table.parquet` was never produced (per `find artifacts/robust_asr/oracle -name '*.parquet'` returning empty in the P10.1 final verification). Branch A (oracle / router-matrix path) is not active.
- Speaker-disjoint guarantee inherited from manifests: **PARTIAL** — inherited from the LibriSpeech manifests under `artifacts/robust_asr/manifests/`: `librispeech_lora_train` (200 speakers), `librispeech_router_train` (51 speakers), `librispeech_validation` (40 speakers), `librispeech_locked_test` (40 speakers); `tests/robust_asr/test_leakage.py` PASSES (5/5). PARTIAL because the OOD-real disjointness conjunct is out of scope under `BLOCKED_OOD_PUBLIC` (`claims_enabled.ood_real = false`); see `reports/robust_asr/manifest_summary.md`.

## evaluation

How the router was evaluated.

- Held-out router evaluation metrics (top-1 selection accuracy, regret vs. oracle, per-degradation gains): **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `tasks.P7.2` is `SKIPPED_BY_OUTCOME_E`; no learned router was trained, so no held-out top-1 / regret-vs-oracle evaluation exists. The deterministic selector is reported as NEUTRAL_EVIDENCE in `reports/robust_asr/router/selector_final_eval.md` (first line: `NEUTRAL_EVIDENCE: positive_system=pending`). Selection rates over 53 230 rows: `whisper_base_ct2_int8` 99.9474 % (53 202 rows, reason `baseline`), `ask_repeat` 0.0526 % (28 rows, reason `no_speech`), `assemblyai` 0 %, `whisper_lora_ct2_int8` 0 %; `local_only_rate = 100 %`; `cloud_call_rate = 0 %`.
- System-level evaluation under the selected router: per `reports/robust_asr/system/system_eval.md` (first line `positive_system: false`): `mean WER selector = 0.209797 = mean WER baseline`; `mean_regret_selector = 0`, `mean_regret_baseline = 0`; paired bootstrap 95% CI on `(regret_selector − regret_baseline) = [0.000000, 0.000000]`; `mean_regret_selector < mean_regret_baseline` is `False`. Inputs: profile `battery_aware`; `selector_evidence.parquet` (53 230 rows); declared baselines `[whisper_base_ct2_int8]`; bootstrap method `bca`, iterations 10 000, seed 20 250 514.
- Decision D (positive_system claim) outcome: `Decision_D_positive_system.outcome = false` under `OUTCOME_E_NARROWED_SCOPE` held on `tasks.P8.1` and `decisions.Decision_D_positive_system`. Per `system_eval.md` Decision D: under `OUTCOME_E` with a single deployable transcript-producing backend, the deterministic selector's only divergence from always-baseline is 28 `ask_repeat` rows (selector_reason = `no_speech`), all of which already had `whisper_base_ct2_int8_wer = 1.0`, so the per-row delta is identically zero and Section 5.6 predicate (i) cannot hold strictly. `claims_enabled.positive_system = false`.

## fallbacks

Behavior under degraded or out-of-distribution inputs.

- Implementation fallback chain (lightgbm → xgboost → sklearn HistGB): **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. The ROUTER_IMPL_FALLBACK_* sentinel lineage applies to learned ML-router builds (P7.2). Under Branch B, no boosting / HistGB framework is invoked at runtime; the deterministic selector is a constants-only decision rule (`deterministic_selector.json`). No fallback chain to record.
- Cold-start / missing-feature handling: when feature proxies are missing or invalid, the deterministic selector defaults to `whisper_base_ct2_int8` (the unique deployable transcript-producing backend; `assemblyai_available = false`, `lora_available = false`). The `ask_repeat` action is emitted only when the empty-transcript proxy crosses `no_speech_threshold = 0.6`. See `artifacts/robust_asr/router/selected_router/rp5_inference.py` and `reports/robust_asr/router/selector_final_eval.md`.
- AssemblyAI fallback (unavailable cache or quota exceeded): **N/A — HALTED under `BLOCKED_API`**. AssemblyAI is not an enabled backend; `assemblyai_available = false` is hardwired in the deployed runtime per `metadata.json` `cloud_available_at_build = false`; the handoff contains no `ASSEMBLYAI_API_KEY` / `sk_*` / `Bearer` token (verified by `verify_handoff_package.py --strict` A6). No quota or cache dependency exists at runtime. See handoff README §6.3.

## risks

Risks of relying on the router.

- Distribution shift between router_train and inference: under `OUTCOME_E_DETERMINISTIC_SELECTOR` there is no learned router trained on `router_train`; the §5.5 deterministic-constants selector is invariant to that shift. The residual shift risk reduces to the baseline backend's own shift profile, which is partially characterized by the per-family baseline WER table in `reports/robust_asr/baseline_whisper_base.md` (worst case: `phone_band` mean WER 0.6058). The OOD-real shift dimension is out of scope under `BLOCKED_OOD_PUBLIC`.
- Public-example leakage through router features: the deterministic selector consumes only the columns of `selector_evidence.parquet` listed under `inputs` above. P6.1 recorded `demo_overlap = 0` and `lora_overlap = 0` at build time (`reports/robust_asr/router/selector_evidence_summary.md`). The C5 exclusion verification (P10.1) re-confirmed that demo `audio_id` / demo `audio_sha256` / demo `upstream_audio_id` are disjoint from `selector_evidence.parquet` (`audio_id` intersection = 0; `upstream_audio_id` and `audio_sha256` columns absent → vacuous PASS; built-in `validate_selector_evidence.py` demo-overlap assertion re-confirmed). Sentinel `C5_EXCLUSION_PASS`; see `reports/robust_asr/final_verification.md`.
- Mis-routing cost vs. always-baseline policy: per `reports/robust_asr/system/system_eval.md`, the deterministic selector is mathematically equivalent to always-baseline on 53 202/53 230 rows (99.9474 %) and emits `ask_repeat` on 28 rows where the baseline already had `whisper_base_ct2_int8_wer = 1.0`. `mean_regret_selector − mean_regret_baseline = 0` and the bootstrap 95% CI is `[0, 0]`. Mis-routing cost vs. always-baseline policy is therefore zero under the primary `ask_repeat_wer = 1.0` convention. `claims_enabled.positive_system = false` (no positive system claim is enabled by these neutral results).

## license

License of the router artifact and of feature pipeline components.

- Router package license: the deployed router package at `artifacts/robust_asr/router/selected_router/` is MIT (project license; same as the deployed `whisper_base_ct2_int8` backend; recorded under the project's `LICENSE` if present and inherited via `libs/common/versions.py`). Per `metadata.json`, the package was built on `datamove1.surrey.ac.uk` by `gb0048` at `2026-05-13T23:17:42+00:00` from git commit `394df2d2778e0f7204aba8155fa66e2eea8cb1a9`.
- Upstream feature-extractor licenses: under `OUTCOME_E_DETERMINISTIC_SELECTOR` the deployed selector consumes only `selector_evidence.parquet` columns derived from `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` (faster_whisper 1.2.1, MIT) and from `libs/audio/**` / `libs/common/normalization.py` / `libs/common/metrics.py` / `libs/common/versions.py` (project code, project license). No external feature-extractor binary is invoked at runtime.

## contact

Maintainer and reporting channel.

- Primary maintainer: Gabriel Bibbó (`gabobibbo@gmail.com`).
- Issue / handoff channel: handoff package at `artifacts/robust_asr/handoff/` (canonical tag `handoff/20260514-64eba43` → commit `64eba4345f3207af38f0fba8ac2c43c6084e8852`, present locally and on `origin`); RP5-side validation template at `artifacts/robust_asr/handoff/handoff_validation_template.md`. Contact details in handoff README §8.
