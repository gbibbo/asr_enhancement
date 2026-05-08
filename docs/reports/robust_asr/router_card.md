# Router Card (robust_asr)

Produced by: P0.5 (template; placeholders resolved by downstream tasks).
Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Card lifecycle: created P0.5 → fields filled across P6–P8 → finalized in P9.1 / P10.1.

This is a template. Every `TODO_FILLED_IN_<task_id>` marker is the
contract that the named task will resolve the field with concrete
evidence. Do not delete markers; replace them.

## intended_use

Role of the router in the robust_asr system.

- Purpose: TODO_FILLED_IN_P9.1 — at inference time, decide which ASR
  back-end (whisper_base_ct2_int8 baseline / whisper_lora_ct2_int8 / cloud
  reference) handles a given input clip.
- Decision kind (learned router vs. deterministic selector): TODO_FILLED_IN_P7.1.

## inputs

Features consumed by the router.

- Feature set and feature provenance: TODO_FILLED_IN_P6.2 — feature
  table at `artifacts/robust_asr/router/router_features.parquet`.
- Feature dimensionality and dtype: TODO_FILLED_IN_P6.2.
- Audio-side preprocessing (sample rate, framing, normalization): TODO_FILLED_IN_P6.1.

## decision_rule

How the router maps inputs to back-end choices.

- Decision rule (model class, thresholds, fallbacks): TODO_FILLED_IN_P7.3 —
  package at `artifacts/robust_asr/router/selected_router/`.
- Selector vs. learned router selection: TODO_FILLED_IN_P7.1 — Decision C
  outcome and rationale.
- Calibration and threshold tuning: TODO_FILLED_IN_P7.2.

## training_data

Data used to train (or define) the router.

- Router training matrix: TODO_FILLED_IN_P6.2 — `train_matrix` /
  `val_matrix` / `test_locked_matrix` paths under `artifacts/robust_asr/router/`.
- Oracle table backing per-row labels: TODO_FILLED_IN_P6.1 — table at
  `artifacts/robust_asr/oracle/oracle_table.parquet`.
- Speaker-disjoint guarantee inherited from manifests: TODO_FILLED_IN_P1.3.

## evaluation

How the router was evaluated.

- Held-out router evaluation metrics (top-1 selection accuracy, regret
  vs. oracle, per-degradation gains): TODO_FILLED_IN_P7.2.
- System-level evaluation under the selected router: TODO_FILLED_IN_P8.1 —
  report at `reports/robust_asr/system/system_eval.md`.
- Decision D (positive_system claim) outcome: TODO_FILLED_IN_P8.1.

## fallbacks

Behavior under degraded or out-of-distribution inputs.

- Implementation fallback chain (lightgbm → xgboost → sklearn HistGB):
  TODO_FILLED_IN_P7.2 — record `ROUTER_IMPL_FALLBACK_*` sentinel state.
- Cold-start / missing-feature handling: TODO_FILLED_IN_P7.3.
- AssemblyAI fallback (unavailable cache or quota exceeded): TODO_FILLED_IN_P5.1.

## risks

Risks of relying on the router.

- Distribution shift between router_train and inference: TODO_FILLED_IN_P9.1.
- Public-example leakage through router features: TODO_FILLED_IN_P8.2.
- Mis-routing cost vs. always-baseline policy: TODO_FILLED_IN_P8.1.

## license

License of the router artifact and of feature pipeline components.

- Router package license: TODO_FILLED_IN_P9.1.
- Upstream feature-extractor licenses: TODO_FILLED_IN_P9.1 — inherited
  from `libs/audio/**` and runtime image components.

## contact

Maintainer and reporting channel.

- Primary maintainer: Gabriel Bibbó (`gabobibbo@gmail.com`).
- Issue / handoff channel: TODO_FILLED_IN_P9.1 — handoff package path
  and contact details for RP5 integration.
