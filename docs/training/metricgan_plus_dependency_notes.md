# MetricGAN+ Pretrained — Dependency and Cache Notes (T4.1)

## Source-of-truth for the B5.3 hook

`libs/audio/enhancement.py` (the B5.3 enhancer interface, `BypassEnhancer`,
empty `MetricGANPlusEnhancer` hook, and version constants) was created on the
demo-runtime branch.

State at T4.1:

- `origin/feature/training-datamove1-v1` did **not** contain `libs/audio/enhancement.py`.
- `origin/demo-rp5-v1` does **not** contain `libs/audio/enhancement.py`. The integration branch has not yet absorbed B5.3.
- `origin/feature/demo-runtime-rp5-v1` contains `libs/audio/enhancement.py` with the B5.3 interface intact.

T4.1 therefore brought the file in from `origin/feature/demo-runtime-rp5-v1`
using a path-limited retrieval that does not modify the index:

```bash
git show origin/feature/demo-runtime-rp5-v1:libs/audio/enhancement.py \
  > libs/audio/enhancement.py
```

`git checkout origin/feature/demo-runtime-rp5-v1 -- libs/audio/enhancement.py`
was deliberately **not** used, so that staging stays explicit.

The byte-equality of the B5.3 interface (everything except the body of
`MetricGANPlusEnhancer.enhance()` and the surrounding docstring) was verified
with `diff` against the source blob.

## Future integration path back into the demo branch

T4.1 does **not** prepare, open, merge, or modify any pull request. The
documented future path is:

1. B5.3 reaches `origin/demo-rp5-v1` (either by an independent demo-side
   merge or by a PR from `origin/feature/demo-runtime-rp5-v1`).
2. After (1), the training branch can be PR'd into `origin/demo-rp5-v1` so
   the filled `MetricGANPlusEnhancer.enhance()` reaches the integration
   branch. This PR is owned by a separate task (T4.2 prep or later); it is
   out of scope for T4.1.

T4.1 does not write to `origin/demo-rp5-v1` or
`origin/feature/demo-runtime-rp5-v1`.

## Pretrained model

| Field | Value |
|---|---|
| Model id | `speechbrain/metricgan-plus-voicebank` |
| Loader class | `speechbrain.inference.enhancement.SpectralMaskEnhancement` |
| Sample rate | 16 kHz mono (input is resampled and channel-averaged when needed) |
| Output | 16-bit PCM WAV named `metricgan_plus_pretrained.wav` under the caller's `output_dir` |
| Inference device | CPU (the training Apptainer image provides `torch 2.1.0` from `/opt/conda`; CUDA is not required at this step) |

## Optional dependency group

The SpeechBrain stack is declared in `pyproject.toml` only as an optional
extra. It is **not** part of `[project.dependencies]`. Required dependencies
were not modified by T4.1.

```toml
[project.optional-dependencies]
training-enhancer = [
    "speechbrain>=1.0",
    "hyperpyyaml>=1.2",
    "huggingface_hub>=0.20",
    "sentencepiece>=0.2",
]
```

T4.1 does **not** install these packages. Installation is deferred to a
follow-up dependency-validation step (or to T4.2 prep).

`libs/audio/enhancement.py` imports SpeechBrain, hyperpyyaml,
huggingface_hub, torch, and torchaudio **lazily** inside
`MetricGANPlusEnhancer.enhance()`, so module import does not require the
optional extra.

## Cache and storage policy

Per `CLAUDE.md` storage rules, model weights and HuggingFace caches must
not land in the repository. The wrapper resolves caches from
`ASR_CACHE_ROOT` when set:

| Cache | Resolution |
|---|---|
| HuggingFace hub | `HF_HOME=$ASR_CACHE_ROOT/huggingface` (caller exports this env var) |
| `huggingface_hub` cache | `HUGGINGFACE_HUB_CACHE=$ASR_CACHE_ROOT/huggingface/hub` (caller exports) |
| SpeechBrain `savedir` | `$ASR_CACHE_ROOT/speechbrain/metricgan_plus_voicebank` (computed inside `enhance()`) |

When `ASR_CACHE_ROOT` is not set, the wrapper falls back to a
`_speechbrain_savedir/` directory under the caller-supplied `output_dir`
to keep weights out of the repo by default.

Default values for the platform:

```text
ASR_CACHE_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/cache
```

`/mnt/fast/nobackup/scratch4weeks/` is already excluded from git via
`.gitignore`.

## Future install pattern (deferred)

Installation must reuse `/opt/conda` `torch` / `torchaudio` from the
Apptainer image. SpeechBrain itself depends on `torch`, so the install
must follow the same `--target $PREFIX --no-deps` discipline established
at T1.2 to avoid bringing in a second `torch` / `torchaudio` and tripping
the forbidden stack.

Forbidden stack carried forward from T1.2:

```text
torch torchaudio torchvision torchtext numpy triton nvidia-*
```

The expected pattern (executed by a separate, explicitly-approved task,
**not** in T4.1):

```bash
PREFIX=/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/python_env/site-packages-py310

apptainer exec \
  --env PYTHONNOUSERSITE=1 \
  --env ASR_REPO_ROOT="$REPO" \
  --env ASR_CACHE_ROOT="$ASR_CACHE_ROOT" \
  "$CONTAINER" \
  python3 -s -m pip install \
      --no-warn-script-location \
      --target "$PREFIX" \
      --no-deps \
      speechbrain hyperpyyaml huggingface_hub sentencepiece \
      <other resolved deps from a prior dry-run minus the forbidden stack>
```

The actual resolved-set is to be produced by a clean dry-run in the same
Apptainer environment, with the forbidden-stack guard re-applied, mirroring
`t1_2_evidence.install_strategy`.

## What was validated in T4.1

- `libs/audio/enhancement.py` exists on the training branch with the B5.3
  interface byte-identical to `origin/feature/demo-runtime-rp5-v1`.
- `MetricGANPlusEnhancer.enhance()` filled with a SpeechBrain-backed
  implementation using lazy imports.
- Optional extra `training-enhancer` declared in `pyproject.toml`; required
  deps unchanged.
- Module imports successfully without SpeechBrain installed
  (`tests/audio/test_metricgan_plus_import.py`).
- Lint / type / yaml / toml checks pass.

## What was deliberately not done in T4.1

- No SpeechBrain installation.
- No real-WAV enhancement (`MetricGANPlusEnhancer.enhance()` was not invoked
  on actual audio).
- No Slurm job, no Whisper run, no enhancer inference at scale.
- No edits to `origin/demo-rp5-v1` or `origin/feature/demo-runtime-rp5-v1`.
- No PR opened or modified.
- No edits to `libs/common/versions.py` (`ENHANCER_VERSION` remains `None`
  per `CLAUDE.training.md` rule 6).
- No edits to T3.x reports, manifests, configs, model card, demo/RP files,
  or Slurm scripts.
- No interaction with `stash@{0}`.
