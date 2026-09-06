# Model Card — ASR Enhancement Demo

## Summary

The demo compares ASR transcription of clean vs. degraded speech, with an
enhancement stage in front of the recogniser. It is a portfolio / research demo,
not a production ASR product.

## ASR model

- **Engine:** faster-whisper (CTranslate2) running Whisper **`tiny.en`**.
- **Scope:** English speech, short clips (curated examples and uploads up to
  30 s). `tiny.en` is chosen so it runs comfortably on a Raspberry Pi 5 CPU with
  low latency; it is not the most accurate Whisper size and will make errors,
  especially on heavily degraded audio.
- **Optional cloud provider:** AssemblyAI, disabled by default and cost-capped
  when enabled (see [`docs/privacy.md`](privacy.md) and the README cost-controls
  section). The demo never silently switches provider.

## Enhancement stage — honest status

The enhancer is a **bypass baseline** (`ENHANCER_VERSION = 1.0`, label
`bypass`). The audio pipeline, version/cache contract, and UI treat enhancement
as a first-class stage, but **no learned enhancement model is deployed**.

- The demo makes **no claim** of a learned accuracy improvement from enhancement.
- Where "enhanced transcript" is shown with the bypass enhancer, it is labelled
  as a baseline, not as a learned improvement.
- The parallel training branch (`feature/training-datamove1-v1`) completed
  without producing a deployable artifact
  (`training_branch_complete_no_artifact_handoff`); per the plan's handoff rule,
  the demo keeps the honest bypass rather than implying a model that does not
  exist.
- A clean integration seam is kept at `libs/audio/enhancement.py` (enhancer
  interface + bypass + an empty MetricGAN+ hook) so a trained model can be
  activated later by setting `ENHANCER_VERSION` and re-warming the cache, with a
  documented rollback.

## Degradations

Applied deterministically and versioned (`DEGRADATION_VERSION = degradation_v1`):
far-field room, café background, phone call, muffled, broadband hiss. These are
synthetic acoustic conditions used to show ASR robustness, not a claim about any
specific real-world channel.

## Metrics

Word Accuracy and WER (`METRICS_VERSION = 1.0`) are computed against ground
truth. Curated examples ship verified ground truth. For uploads, ground truth is
optional, entered by the user, computed in the browser, and never stored.

## Intended use and limitations

- **Intended:** demonstrating the degradation → ASR → enhancement pipeline and
  the engineering around it (RP5 deployment, caching, cost controls, privacy).
- **Not intended:** high-accuracy transcription, non-English audio, long-form
  audio, or any decision-making use. Results on degraded audio are expected to
  contain errors.

## Reproducibility

Curated example results are cached with keys that include the example id,
degradation id, `DEGRADATION_VERSION`, ASR provider and model version,
`ENHANCER_VERSION`, and `METRICS_VERSION`, so a change to any of these
invalidates stale cache entries rather than serving them silently.
