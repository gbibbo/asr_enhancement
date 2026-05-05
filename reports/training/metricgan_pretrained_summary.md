# T4.3 MetricGAN+ Pretrained Summary

Status: complete (documentation only)

## Headline

**MetricGAN+ pretrained worsened Whisper `base.en` ASR on the dev-clean
degraded benchmark; macro Word Accuracy dropped from 0.8213 (degraded)
to 0.5892 (enhanced); tier `null_or_negative`.**

This is a negative pretrained-baseline finding. The pretrained MetricGAN+
enhancer is **not** recommended for deployment on the public Raspberry Pi 5
demo. No claim of ASR improvement is made. No fine-tuning has been performed.
No selected checkpoint exists.

## Scope

T4.3 is a documentation task. It propagates the T4.2 result into
`docs/model_card.md`, this summary, and the training trackers, and emits
the B6.5 RP5 cross-validation request as a training-side note. T4.3 does
**not** run Slurm, Whisper, enhancement, fine-tuning, or any RP5 work.

The canonical numerical evidence (per-record predictions, per-family means,
record_micro consistency check, Slurm job IDs, log paths) lives in:

- [`reports/training/metricgan_plus_wer.md`](metricgan_plus_wer.md)

This summary deliberately reproduces only the headline numbers needed to
make the result self-contained for the model card and the B6.5 request.

## Macro comparison

| Macro metric                  | Clean  | Degraded | Enhanced | Δ vs degraded | Δ vs clean |
|------------------------------|--------|----------|----------|---------------|------------|
| Mean per-record WER          | 0.0645 | 0.1843   | 0.4310   | +0.2467       | +0.3665    |
| Mean per-record Word Accuracy| 0.9361 | 0.8213   | 0.5892   | −0.2321       | −0.3469    |

Negative ΔWA and positive ΔWER mean the enhancer made the ASR task harder.
This is **not** corpus WER — it is the mean of per-record values. With
equal per-family counts (2693 each), the macro headline equals the
record_micro mean over 13 465 predictions to floating-point precision
(see `metricgan_plus_wer.md` for the abs difference).

## Per-family enhanced results

| Family            | Count | Degraded WER | Enhanced WER | Degraded WA | Enhanced WA | Δ WER vs degraded | Δ WA vs degraded |
|-------------------|-------|--------------|--------------|-------------|-------------|-------------------|------------------|
| broadband_hiss    | 2693  | 0.1271       | 0.2666       | 0.8742      | 0.7390      | +0.1395           | −0.1352          |
| cafe_background   | 2693  | 0.1632       | 0.4716       | 0.8390      | 0.5401      | +0.3084           | −0.2989          |
| far_field_room    | 2693  | 0.1659       | 0.5920       | 0.8356      | 0.4264      | +0.4261           | −0.4092          |
| muffled           | 2693  | 0.3863       | 0.6657       | 0.6361      | 0.3978      | +0.2794           | −0.2383          |
| phone_call        | 2693  | 0.0789       | 0.1592       | 0.9217      | 0.8429      | +0.0803           | −0.0788          |

Direction is uniform across all five families: every family shows positive
ΔWER and negative ΔWA. Smallest magnitude is `phone_call` (ΔWA −0.0788),
largest is `far_field_room` (ΔWA −0.4092).

## Tier

Tier is assigned on macro Word Accuracy delta vs the T3.2 degraded baseline:

- `strong` if Δ WA ≥ +0.05
- `partial` if 0 < Δ WA < +0.05
- `null_or_negative` if Δ WA ≤ 0

Observed Δ macro Word Accuracy: **−0.2321** → **`null_or_negative`**.

## Identities (T4.2 evaluation under summary)

| Field                                | Value |
|-------------------------------------|-------|
| Dataset version                     | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Source clean manifest SHA-256       | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Source degraded manifest SHA-256    | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Enhanced manifest SHA-256           | `544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9` |
| Manifest records (per family)       | 2693 |
| Total enhanced records              | 13 465 (5 families × 2693) |
| Whisper model                       | `base.en` (openai-whisper `20250625`) |
| Metrics version                     | `metrics_v1` |
| Degradation version                 | `degradation_v1` |
| Enhancer version                    | `metricgan_plus_pretrained` |
| Enhancement version                 | `enhancement_v1` |
| Pretrained model id                 | `speechbrain/metricgan-plus-voicebank` |
| Loader class                        | `speechbrain.inference.enhancement.SpectralMaskEnhancement` |
| T4.2d full Slurm job ID             | `2127693` |
| T4.2d full sacct State              | `COMPLETED` |
| T4.2d full ExitCode                 | `0:0` |
| T4.2d full Elapsed                  | `06:47:48` |
| T4.2 result commit                  | `8baa2ccc7798a54162b0c5659154864f316fb144` |
| T4.2 backfill commit                | `fb763464f82728f6847a6a6693356eb12956f72a` |
| T4.3 result commit                  | `b6ecd71c02ce577cf9e4c1d80b7f1b1bec6c5048` |
| Reserved public examples (excluded) | 10, see [`configs/training/reserved_public_demo_examples.yaml`](../../configs/training/reserved_public_demo_examples.yaml) |
| Canonical T4.2 evidence report      | [`reports/training/metricgan_plus_wer.md`](metricgan_plus_wer.md) |

## B6.5 RP5 validation request

Status: **`requested`** (training-side documentation only — no RP5 execution
in this commit, no demo trackers modified, no PR opened).

Decision rule applied: training plan §14.4.3.2 — pretrained evaluation is
complete but weak (`null_or_negative`); B6.5 *may* still run to document
demo behavior. The plan also reminds that if the wrapper is not
RP5-compatible, B6.5 must use an exported or bypass-compatible path
(§14.4.3.3).

Recommendation to the demo branch:

1. **Do not promote** `metricgan_plus_pretrained` to the default RP5
   enhancer. Keep `BypassEnhancer` (`bypass`) as the RP5 default.
2. B6.5 may run MetricGAN+ pretrained on RP5 strictly as a documented
   negative comparison, in parallel with the existing bypass baseline.
3. If RP5 cannot host the SpeechBrain stack at acceptable latency, B6.5
   should skip the live enhancer and instead consume the pre-computed
   enhanced WAVs from the training-side enhanced bank (paths and SHA-256
   below) or fall back to the bypass-compatible path.

Wrapper RP5-compatibility note:

- Implementation: `libs/audio/enhancement.py` `MetricGANPlusEnhancer`,
  CPU inference; lazy imports for `torch`, `torchaudio`, `speechbrain`,
  `hyperpyyaml`, `huggingface_hub`.
- Optional dependency group `training-enhancer` in `pyproject.toml`;
  install discipline (forbidden stack, `--target $PREFIX --no-deps`)
  documented in
  [`docs/training/metricgan_plus_dependency_notes.md`](../../docs/training/metricgan_plus_dependency_notes.md).
- The wrapper has not been validated on RP5 hardware. Latency, memory,
  and model-cache footprint on RP5 are unknown and out of scope for the
  training branch.

Inputs the demo branch needs for B6.5:

| Input | Reference |
|-------|-----------|
| Enhancer version       | `metricgan_plus_pretrained` |
| Enhancement version    | `enhancement_v1` |
| Enhanced audio root    | `$TRAIN_ROOT/datasets/enhanced/metricgan_plus_pretrained/enhancement_v1` |
| Enhanced manifest      | `$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl` |
| Enhanced manifest SHA-256 | `544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9` |
| Degraded source manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Dataset version        | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Degradation version    | `degradation_v1` |
| Metrics version        | `metrics_v1` |
| Whisper model          | `base.en` (`openai-whisper 20250625`) |
| Reserved public example IDs | `configs/training/reserved_public_demo_examples.yaml` |
| Canonical T4.2 evidence | `reports/training/metricgan_plus_wer.md` (commit `8baa2ccc7798a54162b0c5659154864f316fb144`) |
| Dependency notes       | `docs/training/metricgan_plus_dependency_notes.md` |

The cross-branch notification path (a future PR from
`feature/training-datamove1-v1` into `demo-rp5-v1`) is deferred per
`docs/training/metricgan_plus_dependency_notes.md`. T4.3 does not open,
prepare, or modify any PR, and does not write to demo trackers.

## Limitations

- LibriSpeech `dev-clean` only (2693 utterances per family; 10 reserved
  public examples excluded).
- Whisper `base.en` only; no other ASR model evaluated.
- MetricGAN+ VoiceBank pretrained only; no other enhancer evaluated.
- `degradation_v1` synthetic degradation families only.
- No fine-tuning of either the enhancer or Whisper.
- CPU inference only (no GPU run).
- ASR metric only (WER / Word Accuracy via `metrics_v1`); no perceptual
  quality metric (PESQ, STOI, MOS) computed.
- The wrapper has not been validated on RP5 hardware.

## What this report does not claim

- The pretrained MetricGAN+ enhancer **did not** improve ASR; it worsened it.
- No fine-tuned model exists, no checkpoint has been selected, no
  enhancer artifact has been exported, no model has been deployed.
- B6.5 has **not** been executed; this is a documentation-only request.
- `docs/model_card.md` `status` remains `template_draft`.
- Nothing here promotes MetricGAN+ pretrained to the public RP5 demo.

## Next step

T5.1 — create `configs/training/dry_run.yaml`. T5.1 is **not** started by
T4.3.
