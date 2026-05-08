# Whisper base CT2 INT8 build (P2.1-model-build)

- Task: P2.1-model-build (subtask of P2.1)
- Phase: P2
- Branch: feature/robust-asr-lora-router-datamove1-v1
- Status: PASS — sentinel `OK_CT2_BUILD` emitted
- Marker: none added; **MISSING_EVIDENCE NOT cleared on the parent P2.1 task** (clears only after `slurm/jobs/p2_1_baseline.sh` rerun emits `OK_BACKEND_EVAL`/`OK_BACKEND_SUMMARY`/`OK_EVAL_TABLE`).

## Approval packets accepted

- `APPROVE_EXECUTION(P2.1-model-scope-change)` on
  `accepted_report_commit=7253b878b61c4416f2e1164257e802ca7627a73b`,
  `next_expected_task=P2.1`. Two new reuse_policy override rows
  (`…/cache/whisper/base.en.pt` read-only sha256-pinned;
  `…/runtime/whisper_models/**` read_write) and the touch_policy P2.1
  row extension are now binding.
- `APPROVE_PLAN(P2.1-model-build)` on
  `accepted_report_commit=7253b878b61c4416f2e1164257e802ca7627a73b`,
  `next_expected_task=P2.1`. Build accepted on the model-scope-change
  commit; `state_transport.last_accepted_report_commit` is NOT
  advanced to the build implementation commit per orchestrator
  instruction.

## Source

- Path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache/whisper/base.en.pt`
- Observed sha256: `25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead`
- Canonical sha256: `25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead` (openai-whisper `whisper/__init__.py` `_MODELS["base.en"]`).
- Provenance string: "openai-whisper base.en checkpoint; canonical sha256 from openai/whisper repository whisper/__init__.py _MODELS dict".

## Output

- Directory: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/whisper_models/whisper_base_en_ct2_int8/`
- 12 files, 76,396,161 bytes (`model.bin`) + 11 ancillary tokenizer/config files + `provenance.json`.
- Per-file sha256s recorded in `provenance.json` (machine-readable), reproduced here:
  - `model.bin` `4ed9e9b5ff94611603854e0abf79badb1d9f3ae3a4b1f3537d93a116e31db33f`
  - `config.json` `48089efbd589828d0d8e7c7869c4ea9c28e81d0a5e62e2191218e772fe1543b5`
  - `generation_config.json` `c5750f05d94777579e00ce26ef65e5d87c108439f90e3ac519df2587b9d5d41f`
  - `tokenizer.json` `5eb60cec1e77aeeb6869a2bb5a8e01a84c3fe5d072d75369343021fe6f5310d0`
  - `tokenizer_config.json` `14f84bdf4b9ecdbd4738ddc81c17a1baedfc02bb93c6e049c951e15a1b40b70d`
  - `special_tokens_map.json` `014f8f802366ed818919550be0ad9e35907327cb9e142e8aaa102420f460bda8`
  - `added_tokens.json` `560be47bea388757f8d4cc185c5d82067426cbb6361e38016dd90ddc01ab203a`
  - `merges.txt` `1ce1664773c50f3e0cc8842619a93edc4624525b728b188a9e0be33b7726adc5`
  - `vocab.json` `3ba3c3109ff33976c4bd966589c11ee14fcaa1f4c9e5e154c2ed7f99d80709e7`
  - `vocabulary.json` `4dadfee7c4a871665f65c06037f5f5ec893fb2d7f5eb4cf11063618e31dbe11a`
  - `preprocessor_config.json` `9b5cd03a36fbb8a627c64d98a5b5b126ead95a77720723944487311f0110b666`
  - `normalizer.json` `bf1c507dc8724ca9cf9903640dacfb69dae2f00edee4f21ceba106a7392f26dd`

## Conversion

- Quantization: `int8`.
- ctranslate2 version: `4.7.1`.
- Conversion strategies attempted (in order; the first successful strategy was used):
  1. `ctranslate2.converters.OpenAIWhisperConverter` — FAIL: import unavailable
     (`cannot import name 'OpenAIWhisperConverter'`; class removed in
     ctranslate2 4.x in favor of `TransformersConverter`).
  2. `ct2-transformers-converter` CLI on `openai/whisper-base.en` — FAIL:
     transformers/ctranslate2 API mismatch
     (`TypeError: WhisperForConditionalGeneration.__init__() got an
     unexpected keyword argument 'dtype'`).
  3. **`TransformersConverter` Python API with patched `load_model` that
     strips the `dtype`/`torch_dtype` kwargs before calling
     `from_pretrained`** — PASS. This is the conversion that produced
     the artifacts.
- Source bytes for the conversion: HF model hub mirror
  `openai/whisper-base.en` (same canonical openai-whisper base.en
  weights as the local `base.en.pt` source verified above; the hub
  download is a deterministic pointer to the same checkpoint).

## Slurm execution

- Wrapper: `./slurm/tools/on_submit.sh sbatch /…/slurm/jobs/p2_1_build_ct2_model.sh`.
- Job: `2129651`, name `asr_p2_1_build_ct2`, partition `2080ti`,
  CPU-only, host `aisurrey04`.
- State / ExitCode: `COMPLETED 0:0` in 32 s. MaxRSS 836,324 KiB.
- Container sha256: `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`
  (matches `tracker.artifacts.runtime_image_v1`).
- Env-isolated: `PYTHONNOUSERSITE=1`, cleared `PYTHONPATH`/`PYTHONUSERBASE`,
  `PIP_USER=0`. `HF_HOME` set to scratch HF cache.
- Sentinel: `OK_CT2_BUILD`.
- Prior attempt: job `2129650` FAILED `1:0` in 31 s on `aisurrey04`
  (same sentinel `FAIL_CT2_BUILD: all conversion strategies failed`;
  strategy 3 not yet implemented at that commit). No partial output
  retained: `_wipe()` cleared the directory between strategies, and
  the failure path produced no provenance.json.

## Files written by this build

- `scripts/robust_asr/build_whisper_base_ct2_int8.py`
  (sha256 `79f29b5c18ba12f5230a31beb07dd58184f80b29b2e60e1b9183a4af5633835e`).
- `slurm/jobs/p2_1_build_ct2_model.sh`
  (sha256 `e575f8740d07248b0b8c4c47ac0f612e1281214d4e827537fc2c9ba6859d9e1e`).
- `reports/robust_asr/whisper_base_ct2_int8_build.md` (this file).
- Model artifacts under
  `…/runtime/whisper_models/whisper_base_en_ct2_int8/` (large_artifact;
  never committed).
- Tracker updates: `docs/progress/robust_asr_progress.{yaml,md}`,
  `docs/progress/robust_asr_state_capsule.md`.

## reuse_policy_rows_used

- `scripts/robust_asr/**` (write build script).
- `slurm/jobs/**` (write `p2_1_build_ct2_model.sh`).
- `slurm/tools/**` (read; on_submit wrapper).
- `…/runtime/robust_asr_py311_cuda12.sif` (exec_only; sha256 recorded).
- `/mnt/.../cache/whisper/base.en.pt` (read_only; sha256-pinned override
  added in the P2.1-model scope-change at commit `7253b87`).
- `/mnt/.../runtime/whisper_models/**` (read_write; new model_root row
  added in the P2.1-model scope-change).
- `reports/robust_asr/**` (write build report).
- `docs/progress/robust_asr_progress.{yaml,md}`,
  `docs/progress/robust_asr_state_capsule.md` (write).

## Tracker stance

- Parent task `P2.1` stays `HALTED` with `marker=MISSING_EVIDENCE`
  until the baseline rerun resolves to PASS.
- `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` — held.
- `blocked=true`; `blocker` text held.
- `current_task=P2.1`; `last_completed_task=P1.4`; `current_phase=P2`.
- `state_transport.last_accepted_report_commit=49b4bdc…` — held; not
  advanced by this build.
- `latest_approval_packet=APPROVE_PLAN(P2.1-model-build)` on `7253b87`.
- A new `tasks.P2.1.subtasks.P2.1-model-build` block records this PASS
  with the Slurm job id, sentinel, output path, and provenance link.

## Unblock path for parent P2.1

Rerun the existing `slurm/jobs/p2_1_baseline.sh` (no code change). The
probe in `run_backend_eval.py` resolves the new model directory at the
primary candidate path `…/runtime/whisper_models/whisper_base_en_ct2_int8`,
loads the CT2 INT8 model with `faster_whisper`, and proceeds to score
the v3.4.7 ID and OOD-param eval manifests. On `OK_BACKEND_EVAL` +
`OK_BACKEND_SUMMARY` + `OK_EVAL_TABLE`, MISSING_EVIDENCE clears,
`tasks.P2.1.status` flips to PASS, and P2.2 becomes the next task.
