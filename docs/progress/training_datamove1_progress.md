# Training Task Progress

Branch: feature/training-datamove1-v1
Integration branch: demo-rp5-v1
Current cut: T4
Current phase: Phase 4
Current task: Task T4.3
Last completed task: T4.2
Blocked: false
Blocker: none

## Completed

- T0.1: inspected datamove1 repository state. Repo root `/mnt/fast/nobackup/users/gb0048/asr_enhancement`, remote `git@github.com:gbibbo/asr_enhancement.git`, working tree clean, branch on `feature/training-datamove1-v1`.
- T0.2: training Claude profile activated on `feature/training-datamove1-v1` (commit `243ed48`). Root `CLAUDE.md` mirrors `docs/profiles/CLAUDE.training.md`; `.gitattributes` declares `CLAUDE.md merge=ours`; local `merge.ours.driver` configured to `true`.
- T0.3: created independent training trackers `docs/progress/training_datamove1_progress.{md,yaml}` per training plan §8 format. Legacy `docs/claude_task_progress.*` left untouched as historical.
- T0.4: added training runtime ignore patterns to `.gitignore` (`runs/`, `artifacts/`, `checkpoints/`, `data/`, `.cache/`, `*.wav`, `*.flac`, `*.mp3`, `*.m4a`, `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`). No duplicates of existing rules; source, configs, docs, plans, and trackers remain trackable.
- T0.5: minimal Slurm gate job submitted through the committed wrapper and completed cleanly. Job `2125754` ran on `aisurrey01.surrey.ac.uk`, sacct state `COMPLETED`, exit code `0:0`. Output `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.out` reports Python `3.10.13` and platform `Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31` from inside the Apptainer container; stderr `…2125754.err` carries the expected `WARNING: Not mounting current directory: user bind control is disabled by system administrator` (already encoded in CLAUDE.md §8 constraint 8). The Cut T0 gate is complete.
- T1.1: Apptainer environment configured. Image `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` (~3.22 GiB) confirmed readable from datamove1 and from the Slurm execution context (re-using T0.5 job `2125754` evidence on `aisurrey01.surrey.ac.uk`). Python `3.10.13` inside the container (mismatch with plan §5 nominal 3.11 recorded; acceptance gated on T1.2 dependency imports). `slurm/templates/apptainer_job_template.job` already encodes the required absolute-path, `--env`-only, no-`--bind`, no-`--pwd`, no-`--nv` pattern; no new T1.1 probe job submitted; no venv-based training execution path introduced. YAML drift on `current_cut`/`current_phase` (T0/0 → T1/1) corrected as part of this closure.
- T1.2: training dependencies installed into an external prefix (`$TRAIN_ROOT/python_env/site-packages-py310`), consumed at runtime via `PYTHONPATH=$REPO:$PREFIX` with `PYTHONNOUSERSITE=1` and `python3 -s` to keep `~/.local` out of the import path. PyTorch 2.1.0, torchaudio 2.1.0 and numpy 1.26.0 remain image-resident under `/opt/conda` (not reinstalled, not shadowed). All required project modules import from the live repo; `openai-whisper`, all pyproject deps, and the audio IO stack import from the prefix. Python `3.10.13` accepted as the runtime gate. No `requirements.lock.x86_64` generated. No venv-based Slurm execution path introduced.
- T1.3: audio processing gate job passed. Synthetic 2-second 440 Hz WAV generated, processed through `libs.audio_pipeline.pipeline.apply_preset("denoise")` (high-pass filter + gain normalization), output validated. Job `2125808` ran on `aisurrey03.surrey.ac.uk`, sacct state `COMPLETED`, exit code `0:0`. Output peak `0.950012` (target 0.95). `libs.audio_pipeline.pipeline` resolved from REPO; `numpy` from `/opt/conda`; `scipy` and `soundfile` from PREFIX. `PYTHONNOUSERSITE=1` enforced; `site.ENABLE_USER_SITE=False`; no user-local module paths detected. Cut T1 gate complete.
- T2.1: LibriSpeech source configuration defined at `configs/training/librispeech_sources.yaml`. Authoritative dataset root at `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech` confirmed via bounded find. Splits `test-clean` and `train-clean-100` present; `dev-clean`, `dev-other`, `test-other`, `train-clean-360`, `train-other-500` missing. Forum-build copies excluded (different project context). No download, no manifest, no Slurm job. YAML valid. T2.2 blocked on `dev-clean` missing.
- T2.2: LibriSpeech dev-clean manifest generated. Job `2125865` ran on `aisurrey03.surrey.ac.uk`, sacct `COMPLETED 0:0`. 2703 records from dev-clean; zero missing FLACs, zero soundfile errors, all 16 kHz, all validated. `test-clean` and `train-clean-100` recorded as `present_empty` (anomaly). Manifest at scratch path, not committed.
- T2.3: public demo example exclusion gate created (placeholder mode). Job `2125885` ran on `aisurrey03.surrey.ac.uk`, sacct `COMPLETED 0:0`. B6 not yet started; no `demo_examples.json` found in bounded inspected locations (repo root, `configs/`, `configs/training/`, `docs/`). Exclusion config committed at `configs/training/public_examples_excluded.yaml` with `status: pending_public_examples`. Zero exclusions applied. Filtered manifest NOT written. T2.3 must be re-run after B6.2 closes. T3.1 must not run while `configs/training/public_examples_excluded.yaml` has `status: pending_public_examples`.
- T2.4: dataset version defined and manifest checksum recorded. Job `2125887` ran on `aisurrey03.surrey.ac.uk`, sacct `COMPLETED 0:0`. Version string `librispeech_devclean_v1_exclpending_sha256_bacd6f7ba89c` written to `configs/training/dataset_version.yaml`; SHA-256 `bacd6f7ba89c439bd73ee4b94e3430db318cf0a62cd8a506fa6972a9a9feb60f` cross-checked with `sha256sum` (match). Report at `reports/training/dataset_version_v1.md`. `exclusion_policy.status: pending_public_examples` and `t3_blocked_while_pending: true` preserved. `later_tasks_must_embed_dataset_version: true` recorded.
- T2.5: model card template created at `docs/model_card.md`. No Slurm required. Template/draft status: all training, evaluation, and artifact fields are explicit `<!-- PLACEHOLDER -->` markers (53 total). Pre-filled fields: dataset version, manifest path, manifest SHA-256 (2703 records), split policy, LibriSpeech CC BY 4.0 licence, degradation families, reference ASR, Apptainer image, Python version. Public examples exclusion gate prominently stated as `pending_public_examples`. `train-clean-100` present_empty caveat included. All 8 validation checks passed.
- T2.3b: public examples exclusion gate resolved. Phase A — reserved 10 dev-clean examples deterministically (job `2125890`, aisurrey03, COMPLETED 0:0); sanity check matched expected ordered list; all SHA-256 hashes computed. Phase B — `public_examples_excluded.yaml` updated to `status: complete`. T2.3 re-run in complete mode (job `2125891`, aisurrey03, COMPLETED 0:0); filtered manifest written at scratch path; 2693 records; validation passed; no excluded IDs remain; source manifest SHA-256 unchanged. T2.4 re-run (job `2125892`, aisurrey03, COMPLETED 0:0); new dataset version `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8`; YAML validation OK. `docs/model_card.md` updated; TEMPLATE/DRAFT status preserved. T3.1 unblocked.
- T3.1: clean-audio Whisper baseline complete. Smoke: job `2125894`, 50 records, 0 failures, WER 0.1234. Full: job `2125895`, COMPLETED 0:0, 55:36 elapsed, 2693/2693 records, 0 failures. Results: mean_wer=0.0645, mean_word_accuracy=0.9361. `openai-whisper base.en 20250625`, `metrics_v1`. Predictions at scratch (not committed). Summary committed at `reports/training/baseline_clean_wer.md`. Model card updated. T3.2 requires degraded audio — see T3.2 prerequisite note.
- T3.2a: degradation bank `degradation_v1` built. `libs/audio/degradations.py` defines five frozen families (`far_field_room`, `cafe_background`, `phone_call`, `muffled`, `broadband_hiss`); `apply_degradation` enforces length contract (output_samples == input_samples), finiteness, and peak ≤ 0.95; per-(utterance, family) seed via SHA-256. `DEGRADATION_VERSION = "degradation_v1"` set in `libs/common/versions.py`. Generation script writes to per-job staging tree, validates (manifest counts, source SHA, reserved-ID absence, format, length, deterministic recomputation of 50 entries) before atomic `os.replace` promotion to final tree. Smoke: job `2125896`, COMPLETED 0:0, 5 s elapsed, 50 files, 0 failures. Full: job `2125897`, COMPLETED 0:0, 02:59 elapsed, MaxRSS 3097852K, 2693 × 5 = 13 465 files, 0 failures. Per-family counts 2693 each. Source manifest SHA-256 unchanged (`dc6674bcf7a8…`). Final degraded manifest SHA-256 `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c`. Audio format WAV PCM_16, 16 kHz mono. Final audio root `$TRAIN_ROOT/datasets/degraded/degradation_v1`; final degraded manifest `$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl` (not committed). Reserved demo IDs absent from degraded manifest. `file_sha256.tsv` (13 465 lines) and `generation_summary.json` under run root, not committed. Summary committed at `reports/training/degradation_bank_v1.md`; model card `DEGRADATION_VERSION` placeholders replaced with `degradation_v1`. T3.2 unblocked.
- T3.2: degraded-audio Whisper baseline complete. Smoke: job `2126085`, 25 records (5 × 5 families), 0 failures, COMPLETED 0:0. Full: job `2126086`, COMPLETED 0:0, elapsed 04:54:54, MaxRSS 3.58 GB, 13 465/13 465 records, 0 failures. Per-family results (mean WER / mean WA): broadband_hiss 0.1271/0.8742, cafe_background 0.1632/0.8390, far_field_room 0.1659/0.8356, muffled 0.3863/0.6361, phone_call 0.0789/0.9217. Overall macro: mean WER 0.1843, mean WA 0.8213 (Δ vs T3.1 clean: +0.1198 / -0.1148). macro == record_micro (abs diff 3.28e-15). Source manifest SHAs unchanged. Reserved demo IDs absent from manifest and predictions. Dataset version `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8`, degradation_version `degradation_v1`, metrics_version `metrics_v1`. Summary committed at `reports/training/baseline_degraded_wer.md`; model card degraded baseline section filled. current_task → T3.3.
- T3.3: baseline summary report produced. `reports/training/baseline_summary.md` consolidates T3.1 clean baseline and T3.2 degraded baseline into one comparison view. No Slurm jobs run; no scripts modified. Cut T3 gate complete. current_task → T4.1. Result commit: 5baf32c.
- T4.2 (closed via T4.2d): MetricGAN+ pretrained Whisper evaluation complete. Smoke job `2127690` (COMPLETED 0:0, 02:04 elapsed, 25/25 records, 0 failures). Full job `2127693` (COMPLETED 0:0, 06:47:48 elapsed, MaxRSS 908608K, aisurrey05, 13 465/13 465 records, 0 failures). Per-family enhanced (mean WER / mean WA): broadband_hiss 0.2666/0.7390, cafe_background 0.4716/0.5401, far_field_room 0.5920/0.4264, muffled 0.6657/0.3978, phone_call 0.1592/0.8429. Macro: WER 0.4310, WA 0.5892 (Δ vs T3.2 degraded: WER +0.2467 / WA −0.2321; Δ vs T3.1 clean: WER +0.3665 / WA −0.3469). macro == record_micro (abs diff ≤ 4.44e-16). MetricGAN+ pretrained **worsened** ASR on this benchmark; tier `null_or_negative`. Manifest SHAs unchanged; reserved demo IDs absent from manifest and predictions. Enhanced manifest SHA `544d6fa5…79c9`; degraded source SHA `c6f8745…0bbb7c`; enhancer_version `metricgan_plus_pretrained`; enhancement_version `enhancement_v1`; metrics_version `metrics_v1`; whisper `base.en` (`20250625`). Summary committed at `reports/training/metricgan_plus_wer.md`. `docs/model_card.md` not modified — deferred to T4.3. current_task → T4.3. Result commit: PENDING_RESULT_COMMIT.

## Current blocker

None.

## T0.5 closure evidence (2026-05-01)

Submitted through the committed wrapper from datamove1:

```bash
./slurm/tools/on_submit.sh sbatch /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/t0_minimal_job.sh
```

| Field | Value |
|---|---|
| Job ID | `2125754` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Execution node | `aisurrey01.surrey.ac.uk` |
| Output log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.out` |
| Error log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.err` |
| Python (in Apptainer) | `3.10.13` |
| Platform (in Apptainer) | `Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31` |
| Apptainer warning (stderr) | `WARNING: Not mounting current directory: user bind control is disabled by system administrator` |

The expected cwd-bind warning is already encoded as a hard constraint in CLAUDE.md §8 (item 8) and reflected in `slurm/jobs/t0_minimal_job.sh` and `slurm/templates/apptainer_job_template.job`, so all training jobs must continue to use absolute paths.

## T1.1 closure evidence (2026-05-01)

T1.1 closes by recording the Apptainer environment already exercised by T0.5 job `2125754`; no new Slurm job was submitted. Raw logs from that job were re-read end-to-end before this closure; all claims below come from the on-disk log content, not from prior tracker text.

| Field | Value |
|---|---|
| Apptainer image | `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` |
| Image size | `3459866624` bytes (~3.22 GiB) |
| Image host mtime | `2026-01-15T21:22:00` |
| Readable from datamove1 | yes (`ls -la` on the login node) |
| Readable from Slurm execution context | yes (T0.5 job `2125754` ran `apptainer exec` against this exact path on `aisurrey01.surrey.ac.uk`) |
| Apptainer required for Slurm Python jobs | yes (single execution mode; no venv-based training path introduced) |
| Python inside container | `3.10.13 (main, Sep 11 2023, 13:44:35) [GCC 11.2.0]` |
| Platform inside container | `Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31` |
| Python version nominal (plan §5) | `3.11` |
| Python version mismatch | recorded; conditionally accepted, gated on T1.2 dependency import success inside the same container (plan §11 T1.1 decision rule 4) |
| Reusable Slurm template | `slurm/templates/apptainer_job_template.job` — already sufficient (absolute paths, `--env` exports, no `--bind`/`--pwd`/`--nv`); not modified |
| New T1.1 probe job | not required; T0.5 evidence covers all T1.1 “done when” criteria |
| Source evidence (stdout) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.out` |
| Source evidence (stderr) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t0_minimal_2125754.err` |

Raw T0.5 log excerpts re-confirmed in this closure:

- stdout line 5: `Container: /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`
- stdout lines 14–16: `--- Python version (inside Apptainer) ---` / `Python: 3.10.13 (main, Sep 11 2023, 13:44:35) [GCC 11.2.0]` / `Platform: Linux-5.14.0-427.42.1.el9_4.x86_64-x86_64-with-glibc2.31`
- stdout line 18: `=== T0.5 minimal job complete ===` (clean exit; matches sacct `COMPLETED 0:0`)
- stderr lines 1–3: `INFO: Setting 'NVIDIA_VISIBLE_DEVICES=all' …`, `INFO: Setting --writable-tmpfs …`, `WARNING: Not mounting current directory: user bind control is disabled by system administrator`

## T1.2 closure evidence (2026-05-02)

Stage history:

| Stage | Job ID | sacct | Outcome | Notes |
|---|---|---|---|---|
| Clean Stage A (probe) | `2125796` | `COMPLETED 0:0` | accepted | First Stage A (`2125795`) was rejected because `~/.local` was satisfying torch/torchaudio/scipy/soundfile inside the container; ran clean with `--env PYTHONNOUSERSITE=1` and `python3 -s`. |
| Stage B+C attempt 1 | `2125798` | `FAILED 7:0` | rejected | `pip install --target --constraint torch==2.1.0` only **pinned** torch — pip still installed it (and numpy 2.2.6, ~5 GiB of CUDA wheels) into `$PREFIX`. Bash pre-Stage-C guard tripped with `BLOCKER: torch_shadowed_in_prefix`. Contaminated `$PREFIX` and `cache/pip` were removed (guarded `rm -rf` of those exact paths only) before retry. |
| Stage B+C retry  | `2125804` | `COMPLETED 0:0` | accepted | Strategy switched to: clean dry-run (no `--target`, sees `/opt/conda`) → forbidden-stack guard on the dry-run report → `pip install --target --no-deps -r resolved_set`. Resolved set: 69 distributions, none in the forbidden set (`torch torchaudio torchvision torchtext numpy triton nvidia-*`). |

Artifact paths (all under `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training`):

| Kind | Path |
|---|---|
| Clean Stage A log | `logs/asr_t1_2_probe_2125796.out` |
| Clean Stage A JSON | `artifacts/t1_2_probe_2125796.json` |
| Stage B+C log (retry) | `logs/asr_t1_2_install_2125804.out` |
| Stage C verify JSON | `artifacts/t1_2_verify_2125804.json` |
| Pip dry-run report | `artifacts/t1_2_pip_dryrun_2125804.json` |
| Resolved install set | `artifacts/t1_2_resolved_install_set_2125804.txt` |
| Pip install command | `artifacts/t1_2_pip_install_cmd_2125804.txt` |
| Dependency prefix | `python_env/site-packages-py310` (446 MiB, 69 distributions) |
| Pip cache | `cache/pip` |

Exact pip install command (verbatim, from the recorded cmd file):

```text
python3 -s -m pip install --no-warn-script-location --target /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/python_env/site-packages-py310 --cache-dir /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache/pip --no-deps -r /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t1_2_resolved_install_set_2125804.txt
```

Runtime discipline carried forward (every later T1.x Apptainer call must keep these):

- `--env PYTHONNOUSERSITE=1`
- `python3 -s`
- `PYTHONPATH=$REPO:$PREFIX`

Origin assertions (from `t1_2_verify_2125804.json` `origin_assertions`):

- `all_libs_under_repo`: `true` (every `libs.*` resolved under `$REPO`)
- `no_project_dirs_in_prefix`: `true` (the third-party `alembic` distribution in `$PREFIX` is not a project shadow — the repo's `alembic/` has no `__init__.py`; the probe now requires `$REPO/<name>/__init__.py` before flagging)
- `torch_not_in_prefix`: `true`
- `torchaudio_not_in_prefix`: `true`
- `numpy_not_in_prefix`: `true`
- `any_user_local_module_paths_detected`: `false`

Resolved versions (image-resident under `/opt/conda` ↦ `IMG`; external prefix ↦ `PREFIX`):

| Package | Version | Origin |
|---|---|---|
| torch | 2.1.0 | IMG |
| torchaudio | 2.1.0 | IMG |
| numpy | 1.26.0 | IMG |
| scipy | 1.15.3 | PREFIX |
| soundfile | 0.13.1 | PREFIX |
| openai-whisper (`whisper`) | 20250625 | PREFIX |
| fastapi | 0.136.1 | PREFIX |
| celery | 5.6.3 | PREFIX |
| sqlalchemy | 2.0.49 | PREFIX |
| pydantic | 2.13.3 | PREFIX |
| pydantic-settings | 2.14.0 | PREFIX |
| pip | 23.2.1 | IMG |

Torch CUDA fields (CPU verify node, expected): `torch.version.cuda = 12.1`, `torch.cuda.is_available() = False`. GPU not required for T1.2.

Project module imports verified (all `libs.*`, all resolving under `$REPO`):

- required: `libs.asr_adapter`, `libs.asr_adapter.factory`, `libs.audio_pipeline`, `libs.audio_pipeline.pipeline`, `libs.common`, `libs.common.settings`, `libs.observability`, `libs.observability.logging`
- optional (also imported successfully): `libs.asr_adapter.assemblyai`, `libs.common.db`, `libs.common.models`, `libs.common.storage`, `libs.observability.metrics`, `libs.observability.tracing`

`Settings()` is **not** instantiated; `services.api.app.main` is **not** imported. T1.2 is an import gate, not an application startup test.

Python 3.10.13 vs nominal 3.11 verdict: **accepted** because every required import succeeded inside the same Apptainer container with user-site disabled. `pyproject.toml` declares `requires-python = ">=3.9"`.

Lock file: `requirements.lock.x86_64` was absent and unused; T1.2 did **not** generate it (deferred per explicit instruction). The exact pip install command and the resolved install set file are the reproducibility evidence.

## Sync status

Last synced from demo-rp5-v1: 2026-05-01 (T0.2 commit `243ed48`, 1 ahead / 0 behind).

## T1.3 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Job ID | `2125808` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Execution node | `aisurrey03.surrey.ac.uk` |
| Elapsed | `00:00:02` |
| Stdout log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t1_3_audio_probe_2125808.out` |
| Stderr log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t1_3_audio_probe_2125808.err` |
| JSON evidence | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t1_3_probe_2125808.json` |
| Input WAV | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t1_3_input_2125808.wav` |
| Output dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t1_3_audio_output_2125808/` |
| Output WAV | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t1_3_audio_output_2125808/denoise.wav` |
| Preset applied | `denoise` |
| `enhanced` | `true` |
| `enhancement_fallback` | `false` |
| Output frames | `32000` |
| Output sample rate | `16000 Hz` |
| Output peak | `0.950012` (target 0.95; pass range [0.93, 0.97]) |
| `audio_pipeline_origin` | `…/asr_enhancement/libs/audio_pipeline/pipeline.py` (REPO) |
| `numpy_origin` | `/opt/conda/lib/python3.10/site-packages/numpy/__init__.py` |
| `scipy_origin` | `…/site-packages-py310/scipy/__init__.py` (PREFIX) |
| `soundfile_origin` | `…/site-packages-py310/soundfile.py` (PREFIX) |
| `site_enable_user_site` | `false` |
| `any_user_local_module_paths_detected` | `false` |
| `pythonnousersite_env` | `"1"` |
| `success` | `true` |
| Stdout terminal line | `T1.3 COMPLETE` |

## T2.1 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Config created | `configs/training/librispeech_sources.yaml` |
| YAML valid | `python3 yaml.safe_load` → OK |
| Bounded search 1 | `find /mnt/fast/nobackup/scratch4weeks/gb0048 -maxdepth 5 -type d ( -name dev-clean -o -name dev-other -o -name test-clean … )` |
| Bounded search 2 | `find /mnt/fast/nobackup/users/gb0048 -maxdepth 5 -type d ( -name dev-clean -o … )` → no matches |
| Authoritative source root | `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech` |
| Splits present | `test-clean`, `train-clean-100` |
| Splits missing | `dev-clean`, `dev-other`, `test-other`, `train-clean-360`, `train-other-500` |
| Forum-build copies | Excluded — different project context |
| `dev-clean` required before T2.2 | true |
| Output manifest path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1.jsonl` |
| Download performed | false |
| Slurm job submitted | false |
| Manifest generated | false |

## T2 staging closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Download source | `https://www.openslr.org/resources/12/dev-clean.tar.gz` |
| License | CC BY 4.0 (OpenSLR resource 12) |
| Archive temp path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/downloads/dev-clean.tar.gz` |
| MD5 expected | `42e2234ba48799c1f50f24a7926300a1` |
| MD5 actual | `42e2234ba48799c1f50f24a7926300a1` |
| MD5 validated | true |
| Tar safety gate | `grep -Ev '^(LibriSpeech/\|LibriSpeech/dev-clean(/\|$))'` → empty (pass) |
| Target pre-existence check | `dev-clean` absent before extraction → OK |
| Extraction command | `tar -xzf dev-clean.tar.gz -C …/sources/librispeech/` |
| Extraction result | success |
| dev-clean path | `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech/dev-clean` |
| FLAC count | 2703 |
| Transcript count | 97 |
| Speaker/chapter tree | confirmed |
| test-clean after extraction | present |
| train-clean-100 after extraction | present |
| Archive deleted | true |
| Slurm job required | false |
| No data staged in Git | true |

## T2.2 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Job ID | `2125865` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Execution node | `aisurrey03.surrey.ac.uk` |
| Elapsed | `00:00:08` |
| Stdout log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_2_build_manifest_2125865.out` |
| Stderr log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_2_build_manifest_2125865.err` |
| Summary artifact | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t2_2_manifest_summary_2125865.json` |
| Manifest path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1.jsonl` |
| Manifest committed | false — lives under scratch path, outside Git |
| Manifest scope | `all_present_splits` (only `dev-clean` declared `present` in config) |
| Config path | `configs/training/librispeech_sources.yaml` |
| Stdout terminal line | `T2.2 COMPLETE` |

**Split summary:**

| Split | Config status | FLAC files | trans.txt files | Manifest records |
|---|---|---|---|---|
| dev-clean | present | 2703 | 97 | 2703 |
| test-clean | present_empty | 0 | 0 | 0 (excluded) |
| train-clean-100 | present_empty | 0 | 0 | 0 (excluded) |

**Anomaly note:** `test-clean` and `train-clean-100` directories exist in the authoritative LibriSpeech root but contain zero FLAC and transcript files. Verified by read-only pre-plan checks (2026-05-02). Config updated: `split_status: present_empty` for both, with `split_status_note`. The manifest is dev-clean-only as a result; this is sufficient for T2.3 (exclusion filtering) and T3.1 (baseline, which only requires dev-clean).

**Validation results (every JSONL line checked):**

| Check | Result |
|---|---|
| missing FLAC count | 0 |
| soundfile.info() errors | 0 |
| duplicate utterance_id | 0 |
| missing transcript chapters | 0 |
| validation lines checked | 2703 |
| sample_rate == 16000 (all records) | pass |
| duration_seconds > 0 (all records) | pass |
| all required fields present | pass |
| audio_path exists on disk | pass |
| JSON parse (every line) | pass |

## T2.3 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Mode | placeholder (B6 not yet started) |
| Job ID | `2125885` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Execution node | `aisurrey03.surrey.ac.uk` |
| Elapsed | `00:00:01` |
| Stdout log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_3_exclude_examples_2125885.out` |
| Stderr log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_3_exclude_examples_2125885.err` |
| Summary artifact | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t2_3_exclude_summary_2125885.json` |
| Exclusion config | `configs/training/public_examples_excluded.yaml` |
| Exclusion status | `pending_public_examples` |
| Source manifest | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1.jsonl` |
| Source manifest records | 2703 (unchanged) |
| Filtered manifest | NOT written |
| Excluded count | 0 |
| Stdout terminal line | `T2.3 COMPLETE (PLACEHOLDER MODE)` |

**Bounded locations inspected for `demo_examples.json`:** repo root, `configs/`, `configs/training/`, `docs/`. Not found in any of these locations.

**Gate note:** T2.3 must be re-run after B6.2 produces `demo_examples.json`. T3.1 must not run while `configs/training/public_examples_excluded.yaml` has `status: pending_public_examples`.

## T2.4 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Job ID | `2125887` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Execution node | `aisurrey03.surrey.ac.uk` |
| Elapsed | `00:00:02` |
| Stdout log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_4_dataset_version_2125887.out` |
| Stderr log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t2_4_dataset_version_2125887.err` |
| Evidence JSON | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/artifacts/t2_4_dataset_version_2125887.json` |
| Dataset version config | `configs/training/dataset_version.yaml` |
| Dataset version report | `reports/training/dataset_version_v1.md` |
| `dataset_version` | `librispeech_devclean_v1_exclpending_sha256_bacd6f7ba89c` |
| Manifest path | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1.jsonl` |
| Manifest records | 2703 |
| Manifest SHA-256 | `bacd6f7ba89c439bd73ee4b94e3430db318cf0a62cd8a506fa6972a9a9feb60f` |
| SHA-256 prefix (in version string) | `bacd6f7ba89c` |
| SHA-256 cross-check | `sha256sum` match (independent) |
| Exclusion status | `pending_public_examples` |
| Filtered manifest | NOT written |
| `t3_blocked_while_pending` | `true` |
| `later_tasks_must_embed_dataset_version` | `true` |
| Stdout terminal line | `T2.4 COMPLETE` |
| YAML validation (inside Apptainer) | `YAML validation: OK` |

## T3.1 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Smoke job ID | `2125894` |
| Smoke sacct state | `COMPLETED` |
| Smoke exit code | `0:0` |
| Smoke processed records | 50 |
| Smoke failure count | 0 |
| Smoke mean WER | 0.1234 |
| Smoke mean Word Accuracy | 0.8766 |
| Smoke summary md | `reports/training/baseline_clean_wer_smoke.md` |
| Full job ID | `2125895` |
| Full sacct state | `COMPLETED` |
| Full exit code | `0:0` |
| Full elapsed | `00:55:36` |
| Full output log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_1_whisper_baseline_full_2125895.out` |
| Run dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_1_baseline_full_2125895` |
| predictions.jsonl line count | 2693 |
| success | true |
| processed_records | 2693 |
| failure_count | 0 |
| **mean_wer** | **0.0645** |
| **mean_word_accuracy** | **0.9361** |
| dataset_version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| whisper_model | `base.en` (openai-whisper 20250625) |
| metrics_version | `metrics_v1` |
| git_commit_at_run | `6e7d9d4464bd5900467d075221478905421945ce` |
| prep_commit 1 | `6e0e342` (libs, scripts, slurm jobs, tests) |
| prep_commit 2 | `6e7d9d4` (git fix: capture git state in Slurm shell) |
| result_commit | `a753b15` |
| backfill_commit | `c3cc95e` (backfill result_commit hash in summaries and trackers) |
| summary_md | `reports/training/baseline_clean_wer.md` |

**T3.2 prerequisite note:** T3.2 (degraded baseline) requires degraded audio. The degradation bank is not yet built. T3.1 clean baseline is the sole T3.1 artefact.

## T3.2a closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Smoke job ID | `2125896` |
| Smoke sacct | COMPLETED 0:0, elapsed 00:00:05 |
| Smoke files generated | 50 (10 records × 5 families), 0 failures |
| Smoke run dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2a_bank_smoke_2125896` |
| Full job ID | `2125897` |
| Full sacct | COMPLETED 0:0, elapsed 00:02:59, MaxRSS 3097852K |
| Full execution node | aisurrey03.surrey.ac.uk |
| Full files generated | **13 465** (2693 × 5), 0 failures |
| Per-family counts | 2693 × {`broadband_hiss`, `cafe_background`, `far_field_room`, `muffled`, `phone_call`} |
| Final audio root | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degraded/degradation_v1` |
| Final degraded manifest | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl` |
| Final degraded manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Source manifest SHA-256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| Source manifest unchanged | `True` |
| Reserved demo IDs in degraded manifest | 0 |
| Deterministic validation sample size | 50 |
| `file_sha256.tsv` (13 465 lines) | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2a_bank_full_2125897/file_sha256.tsv` |
| `generation_summary.json` | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2a_bank_full_2125897/generation_summary.json` |
| Audio format | WAV, 16 kHz mono, PCM_16 |
| Length contract | `output_samples == input_samples` enforced by `apply_degradation` |
| Degradation version | `degradation_v1` |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| `git_commit_at_run` | `e89db8dcb9fbfb486930d697d9345b3361c6e93d` |
| Prep commit | `e89db8d` |
| Result commit | `c4ee5f4` |
| Summary report (Git) | `reports/training/degradation_bank_v1.md` |

### Apptainer runtime validation (post-T3.2a)

| Field | Value |
|---|---|
| Pytest job (rejected) | `2125898` — FAILED 1:0, `pytest` not installed in runtime; no degradation code exercised |
| Pytest stdout / stderr | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2a_pytest_degradations_2125898.{out,err}` |
| Inline validation job | `2125899` — COMPLETED 0:0, elapsed 00:00:02, aisurrey03 |
| Inline validation runtime | Apptainer `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif` |
| Inline validation command | `python3 -s` inline assertions for `libs.audio.degradations` |
| Inline validation script | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/tmp/t3_2a_degradations_inline_validation.sh` (scratch, not committed) |
| Inline stdout / stderr | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2a_degradations_inline_validation_2125899.{out,err}` |
| Result | `T3.2a inline degradation validation PASSED` |
| Assertions covered | `DEGRADATION_VERSION == "degradation_v1"`; registry keys; stochastic/deterministic sets; `DEGRADATION_PARAMS` keys; `apply_degradation` 1-D / length preserved / finite / peak ≤ 0.9501; same (utt, family) deterministic for every family; stochastic families differ across `utterance_id`; deterministic families ignore `utterance_id` |

## T3.2 closure evidence (2026-05-02)

| Field | Value |
|---|---|
| Prep commit | `9ac0fbc5d776e20fe7056769f500081d5b384526` |
| Wall-time adjustment commit | `73808ed975940b0847404794dcd74fbda0b570ef` |
| Smoke job ID | `2126085` |
| Smoke sacct state | `COMPLETED` |
| Smoke exit code | `0:0` |
| Smoke elapsed | `00:01:13` |
| Smoke processed records | 25 (5 × 5 families) |
| Smoke failure count | 0 |
| Full job ID | `2126086` |
| Full sacct state | `COMPLETED` |
| Full exit code | `0:0` |
| Full elapsed | `04:54:54` |
| Full MaxRSS | `3.58 GB` |
| Full output log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2_baseline_degraded_full_2126086.out` |
| Full error log | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/logs/asr_t3_2_baseline_degraded_full_2126086.err` |
| Run dir | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2_baseline_degraded_full_2126086` |
| predictions.jsonl | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2_baseline_degraded_full_2126086/predictions.jsonl` |
| predictions.jsonl line count | 13465 |
| metrics_summary.json | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2_baseline_degraded_full_2126086/metrics_summary.json` |
| success | true |
| total_manifest_records | 13465 |
| processed_records | 13465 |
| failure_count | 0 |
| reserved_demo_ids_checked | 10 |
| reserved_demo_ids_in_predictions | 0 |
| reserved_demo_ids_absent_from_manifest | true |
| dataset_version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| degradation_version | `degradation_v1` |
| metrics_version | `metrics_v1` |
| whisper_model | `base.en` (openai-whisper 20250625) |
| code_commit_at_run | `73808ed975940b0847404794dcd74fbda0b570ef` |
| result_commit | `34e93c8dddfedb58584f49afe1868618ddec4f56` |
| source_clean_manifest_sha256 | `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b` |
| source_clean_manifest_sha256_unchanged | true |
| source_degraded_manifest_sha256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| source_degraded_manifest_sha256_unchanged | true |
| summary_md | `reports/training/baseline_degraded_wer.md` |

### Per-family results

| Family | Count | Mean per-record WER | Mean per-record Word Accuracy | Δ WER vs clean | Δ WA vs clean |
|---|---|---|---|---|---|
| broadband_hiss | 2693 | 0.1271 | 0.8742 | +0.0626 | -0.0619 |
| cafe_background | 2693 | 0.1632 | 0.8390 | +0.0987 | -0.0971 |
| far_field_room | 2693 | 0.1659 | 0.8356 | +0.1014 | -0.1005 |
| muffled | 2693 | 0.3863 | 0.6361 | +0.3218 | -0.3000 |
| phone_call | 2693 | 0.0789 | 0.9217 | +0.0144 | -0.0144 |

### Overall (macro over families, headline)

| Metric | Value | Δ vs T3.1 clean |
|---|---|---|
| Mean per-record WER | 0.1843 | +0.1198 |
| Mean per-record Word Accuracy | 0.8213 | -0.1148 |

macro_record_micro_equivalent: true (abs macro − record_micro WER = 3.28e-15)

### Clean baseline reference (T3.1)

| Metric | Value |
|---|---|
| Mean per-record WER | 0.0645 |
| Mean per-record Word Accuracy | 0.9361 |

## T3.3 closure evidence (2026-05-03)

No Slurm jobs. Documentation-only task.

| Field | Value |
|---|---|
| Report created | `reports/training/baseline_summary.md` |
| Sources | `reports/training/baseline_clean_wer.md`, `reports/training/baseline_degraded_wer.md` |
| Result commit | 5baf32c |

## T4.1 closure evidence (2026-05-04)

No Slurm jobs. No SpeechBrain installation. No real-WAV enhancement. No Whisper run.

| Field | Value |
|---|---|
| B5.3 source-of-truth | `origin/feature/demo-runtime-rp5-v1` (B5.3 hook is absent from `origin/demo-rp5-v1`) |
| Source blob | `aee9ded8d0eba2cd21731bfb6000e164f4ea8575` |
| Retrieval method | `git show origin/feature/demo-runtime-rp5-v1:libs/audio/enhancement.py > libs/audio/enhancement.py` (path-limited, no merge, no cherry-pick, no implicit index change) |
| Interface preservation | `EnhancerAdapter`, `BypassEnhancer`, `EnhancementResult`, presets, version constants byte-identical to source |
| MetricGAN+ implementation | `speechbrain/metricgan-plus-voicebank` via `SpectralMaskEnhancement`; lazy imports inside `MetricGANPlusEnhancer.enhance()` |
| Optional extra | `[project.optional-dependencies] training-enhancer` with `speechbrain>=1.0`, `hyperpyyaml>=1.2`, `huggingface_hub>=0.20`, `sentencepiece>=0.2` |
| Required dependencies modified | false |
| Dependencies installed in T4.1 | false |
| Real-WAV runtime smoke | deferred to T4.2 prep / dependency-validation step |
| Files added | `libs/audio/enhancement.py`, `scripts/training/enhance_metricgan_plus.py`, `tests/audio/test_metricgan_plus_import.py`, `docs/training/metricgan_plus_dependency_notes.md` |
| Files modified | `pyproject.toml`, `docs/progress/training_datamove1_progress.md`, `docs/progress/training_datamove1_progress.yaml` |
| Validation: import smoke | pass |
| Validation: `pytest tests/audio/test_metricgan_plus_import.py -q` | 4 passed |
| Validation: yaml/toml parse | pass |
| Validation: `py_compile` + `ast.parse` | pass |
| Validation: ruff / mypy | not run — tools unavailable on login-node Python; documented and substituted with `py_compile` + `ast.parse` |
| Validation: diff vs source blob | confined to body and docstring of `MetricGANPlusEnhancer.enhance()` |
| `libs/common/versions.py` `ENHANCER_VERSION` | unchanged (`None`); per `CLAUDE.training.md` rule 6, updated only at T8.1 export |
| PR into `demo-rp5-v1` | deferred; documented future integration path only |
| Stash@{0} | untouched |
| Result commit | 061a646 |

## T4.2 — in progress

T4.2 is executing through gated subtasks. T4.2a (dependency validation), T4.2b (one-file enhancement smoke), and T4.2c (full-scale MetricGAN+ enhancement bank generation) are complete. T4.2d (Whisper evaluation on the enhanced manifest) is the next gate. T4.2 itself remains pending and only closes after the Whisper evaluation is complete.

### T4.2a — complete (2026-05-04)

SpeechBrain dependency stack installed into `$PREFIX` and validated inside Apptainer. All four required packages import from PREFIX; torch, torchaudio, numpy remain exclusively under `/opt/conda`. No forbidden-stack contamination detected.

| Field | Value |
|---|---|
| Prep commit | `06af152497e50bacf2a973ee51bdbc8e35d9dc20` |
| Slurm job ID | `2126933` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Elapsed | `00:00:27` |
| Node | `aisurrey05` |
| Stdout log | `$TRAIN_ROOT/logs/asr_t4_2a_install_speechbrain_2126933.out` |
| Stderr log | `$TRAIN_ROOT/logs/asr_t4_2a_install_speechbrain_2126933.err` |
| Dry-run pkg count | 22 |
| Filtered pkg count | 22 |
| Forbidden in dry-run | none |
| Forbidden removed | none |
| Import validation | pass |
| Contamination detected | false |

**Installed versions (all in PREFIX):**

| Package | Version | Origin |
|---|---|---|
| speechbrain | 1.1.0 | `$PREFIX/speechbrain/__init__.py` |
| hyperpyyaml | 1.2.3 | `$PREFIX/hyperpyyaml/__init__.py` |
| huggingface_hub | 1.13.0 | `$PREFIX/huggingface_hub/__init__.py` |
| sentencepiece | 0.2.1 | `$PREFIX/sentencepiece/__init__.py` |

**Forbidden stack (all in `/opt/conda`, not in PREFIX):**

| Package | Origin |
|---|---|
| torch 2.1.0 | `/opt/conda/lib/python3.10/site-packages/torch/__init__.py` |
| torchaudio 2.1.0 | `/opt/conda/lib/python3.10/site-packages/torchaudio/__init__.py` |
| numpy 1.26.0 | `/opt/conda/lib/python3.10/site-packages/numpy/__init__.py` |

Evidence commit: `68bdba2`

### T4.2b — complete (2026-05-04)

One-file MetricGAN+ enhancement smoke executed inside Apptainer on the deterministic
first record of the degraded manifest. SpeechBrain loaded
`speechbrain/metricgan-plus-voicebank`, model files were placed under TRAIN_ROOT cache
(no writes to `$HOME/.cache` or `$HOME/.local`), one valid 16 kHz mono 4.815 s enhanced
WAV was produced, and the consolidated verify JSON reported `validation_passed: true`.
T4.2 remains open; T4.2c (full-scale enhancement of all 13 465 degraded records) is the
next gate.

| Field | Value |
|---|---|
| Prep commit | `ca2851b1ce4714835406876720807bd837aec34e` |
| Slurm job ID | `2126934` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Elapsed | `00:00:32` |
| MaxRSS | `2476K` (batch step) |
| Node | `aisurrey05` |
| Stdout log | `$TRAIN_ROOT/logs/asr_t4_2b_smoke_enhance_2126934.out` |
| Stderr log | `$TRAIN_ROOT/logs/asr_t4_2b_smoke_enhance_2126934.err` |
| Run dir | `$TRAIN_ROOT/runs/t4_2b_smoke_enhance_2126934` |
| Raw stdout | `$TRAIN_ROOT/runs/t4_2b_smoke_enhance_2126934/enhance_stdout_raw.txt` |
| Enhance result JSON | `$TRAIN_ROOT/runs/t4_2b_smoke_enhance_2126934/enhance_result.json` |
| Output WAV | `$TRAIN_ROOT/runs/t4_2b_smoke_enhance_2126934/metricgan_plus_pretrained.wav` |
| Verify JSON | `$TRAIN_ROOT/artifacts/t4_2b_smoke_verify_2126934.json` |

**Input record (deterministic, manifest line 1):**

| Field | Value |
|---|---|
| `utterance_id` | `1272-128104-0001` |
| `family` | `broadband_hiss` |
| Input WAV | `$TRAIN_ROOT/datasets/degraded/degradation_v1/broadband_hiss/1272-128104-0001.wav` |
| Input SHA-256 expected | `abebf43b4c73b0cf644b838a52f0794932f16c86565399ef37b53c369a7a8446` |
| Input SHA-256 observed | `abebf43b4c73b0cf644b838a52f0794932f16c86565399ef37b53c369a7a8446` |
| SHA-256 match | true |

**Enhancement result:**

| Field | Value |
|---|---|
| `enhanced` | `true` |
| `enhancement_fallback` | `false` |
| `enhancer_version` | `metricgan_plus_pretrained` |
| `diagnostic.model_id` | `speechbrain/metricgan-plus-voicebank` |
| `diagnostic.input_sample_rate_hz` | `16000` |
| `diagnostic.output_sample_rate_hz` | `16000` |

**Output WAV validation:**

| Check | Value |
|---|---|
| frames | `77040` |
| samplerate | `16000` |
| channels | `1` |
| duration_seconds | `4.815` |
| frames_nonzero | true |
| samplerate_16khz | true |
| channels_mono | true |
| duration_in_range | true (3.0 ≤ 4.815 ≤ 7.0) |

**Cache validation:**

| Check | Value |
|---|---|
| SpeechBrain savedir | `$TRAIN_ROOT/cache/speechbrain/metricgan_plus_voicebank` |
| savedir exists | true |
| savedir non-empty | true (2 symlinks: `enhance_model.ckpt`, `hyperparams.yaml`) |
| HuggingFace cache | `$TRAIN_ROOT/cache/huggingface/hub` (model `speechbrain/metricgan-plus-voicebank`, 7.3 MB checkpoint + 1.1 KB hparams) |
| `$HOME/.cache` pollution | false |
| `$HOME/.local` pollution | false |
| All model files under TRAIN_ROOT cache | true |

**Non-actions:**

- No Whisper run.
- No other Slurm jobs submitted.
- No tracker modification before this evidence commit.
- `stash@{0}` untouched.

Evidence commit: `6c3dac46c15d17adafb918393ba9bbab2e48b099`

### T4.2c — complete (2026-05-04)

Full-scale MetricGAN+ enhancement bank generated. All 13 465 degraded records were
enhanced with the pretrained `speechbrain/metricgan-plus-voicebank` model in a single
load-once Apptainer process; the enhanced WAVs and the enhanced manifest were written
to `$TRAIN_ROOT/datasets/enhanced/...` and `$TRAIN_ROOT/datasets/...jsonl` respectively
(both outside Git). The smoke gate (5 records per family = 25 records, isolated under
the smoke run dir) passed first; the full job ran fresh with no resume. T4.2 remains
open; T4.2d (Whisper evaluation on the enhanced manifest) is the next gate.

**Prep commit:** `658d0a3614f13c2dff4d6f26976126b0df9038aa`

**Smoke job (gate before full):**

| Field | Value |
|---|---|
| Slurm job ID | `2127631` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Elapsed | `00:00:40` |
| Node | `aisurrey05` |
| Stdout log | `$TRAIN_ROOT/logs/asr_t4_2c_enhance_smoke_2127631.out` |
| Stderr log | `$TRAIN_ROOT/logs/asr_t4_2c_enhance_smoke_2127631.err` |
| Run dir | `$TRAIN_ROOT/runs/t4_2c_enhance_smoke_2127631` |
| Verify JSON | `$TRAIN_ROOT/artifacts/t4_2c_smoke_verify_2127631.json` |
| `enhanced_count` | `25` |
| `newly_enhanced_count` | `25` |
| `skipped_count` | `0` |
| `failure_count` | `0` |
| Per-family counts | broadband_hiss=5, cafe_background=5, far_field_room=5, muffled=5, phone_call=5 |
| `validation_passed` | `true` |

**Full job:**

| Field | Value |
|---|---|
| Slurm job ID | `2127639` |
| sacct state | `COMPLETED` |
| Exit code | `0:0` |
| Elapsed | `00:26:00` |
| MaxRSS | `443208K` batch step (~432 MiB) |
| Node | `aisurrey05` |
| Stdout log | `$TRAIN_ROOT/logs/asr_t4_2c_enhance_full_2127639.out` |
| Stderr log | `$TRAIN_ROOT/logs/asr_t4_2c_enhance_full_2127639.err` |
| Run dir | `$TRAIN_ROOT/runs/t4_2c_enhance_full_2127639` |
| Run summary | `$TRAIN_ROOT/runs/t4_2c_enhance_full_2127639/run_summary.json` |
| Failures JSONL | `$TRAIN_ROOT/runs/t4_2c_enhance_full_2127639/failures.jsonl` (0 entries) |
| Verify JSON | `$TRAIN_ROOT/artifacts/t4_2c_full_verify_2127639.json` |
| `enhanced_count` | `13465` |
| `newly_enhanced_count` | `13465` |
| `skipped_count` | `0` |
| `failure_count` | `0` |
| Per-family counts | broadband_hiss=2693, cafe_background=2693, far_field_room=2693, muffled=2693, phone_call=2693 |
| `validation_passed` | `true` |

**Enhanced bank:**

| Field | Value |
|---|---|
| Enhanced audio root | `$TRAIN_ROOT/datasets/enhanced/metricgan_plus_pretrained/enhancement_v1` |
| Enhanced manifest | `$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl` |
| Enhanced manifest records | `13465` |
| Enhanced manifest SHA-256 | `544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9` |
| `enhancer_version` | `metricgan_plus_pretrained` |
| `enhancement_version` | `enhancement_v1` |

**Runtime:**

| Field | Value |
|---|---|
| Model load | `0.30 s` |
| Processing | `1528.77 s` (~25.5 min) |
| Throughput | `8.81 records/s` |
| Seconds per file | `0.114 s` |
| Wall-time budget | `16:00:00` |
| Wall-time used | `~2.7%` |

**Cache validation:**

| Check | Value |
|---|---|
| `$HOME/.cache` pollution | false |
| `$HOME/.local` pollution | false |
| All model files under TRAIN_ROOT cache | true |

**Non-actions:**

- No Whisper run.
- No other Slurm jobs submitted.
- No tracker modification before this evidence commit.
- `stash@{0}` untouched.

Evidence commit: `7141e39`

## T4.2d closure evidence (2026-05-05)

T4.2 closes via T4.2d: Whisper `base.en` on the MetricGAN+ enhanced manifest.

**Smoke (job `2127690`):**

| Field | Value |
|---|---|
| sacct State | `COMPLETED` |
| ExitCode | `0:0` |
| Elapsed | `00:02:04` |
| MaxRSS (batch) | `867360K` (~847 MiB) |
| Node | `aisurrey05` |
| Stdout log | `$TRAIN_ROOT/logs/asr_t4_2d_whisper_enhanced_smoke_2127690.out` |
| Stderr log | `$TRAIN_ROOT/logs/asr_t4_2d_whisper_enhanced_smoke_2127690.err` |
| Run dir | `$TRAIN_ROOT/runs/t4_2d_whisper_enhanced_smoke_2127690` |
| Predictions | 25 lines (5 per family × 5 families) |
| Failures | 0 |
| Inference | 4.480 s/record on aisurrey05 (smoke projected ~16.76 h for full) |

**Full (job `2127693`):**

| Field | Value |
|---|---|
| sacct State | `COMPLETED` |
| ExitCode | `0:0` |
| Elapsed | `06:47:48` |
| MaxRSS (batch) | `908608K` (~887 MiB) |
| Node | `aisurrey05` |
| Stdout log | `$TRAIN_ROOT/logs/asr_t4_2d_whisper_enhanced_full_2127693.out` |
| Stderr log | `$TRAIN_ROOT/logs/asr_t4_2d_whisper_enhanced_full_2127693.err` |
| Run dir | `$TRAIN_ROOT/runs/t4_2d_whisper_enhanced_full_2127693` |
| `predictions.jsonl` | 13 465 lines |
| `failures.jsonl` | 0 lines |
| `metrics_summary.json` | present |
| `config_snapshot.json` | present |
| `run_summary.md` | present |
| Whisper model | `base.en` (openai-whisper `20250625`) |
| Metrics version | `metrics_v1` |
| Enhancer version | `metricgan_plus_pretrained` |
| Enhancement version | `enhancement_v1` |
| Dataset version | `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8` |
| Degradation version | `degradation_v1` |
| Enhanced manifest SHA-256 | `544d6fa580e22cb0fa1d23053edf3083877416b7b96819f488e446c8c67a79c9` |
| Degraded source manifest SHA-256 | `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c` |
| Enhanced manifest SHA unchanged after run | true |
| Degraded source manifest SHA unchanged after run | true |
| Reserved demo IDs absent from manifest | true |
| Reserved demo IDs absent from predictions | true |

**Per-family enhanced (mean per-record WER / WA):**

| Family | Count | Enhanced WER | Enhanced WA | Δ WER vs degraded | Δ WA vs degraded |
|---|---|---|---|---|---|
| broadband_hiss | 2693 | 0.2666 | 0.7390 | +0.1395 | −0.1352 |
| cafe_background | 2693 | 0.4716 | 0.5401 | +0.3084 | −0.2989 |
| far_field_room | 2693 | 0.5920 | 0.4264 | +0.4261 | −0.4092 |
| muffled | 2693 | 0.6657 | 0.3978 | +0.2794 | −0.2383 |
| phone_call | 2693 | 0.1592 | 0.8429 | +0.0803 | −0.0788 |

**Macro:**

| Metric | Macro | record_micro | abs(macro − record_micro) | Δ vs degraded | Δ vs clean |
|---|---|---|---|---|---|
| Mean per-record WER | 0.4310 | 0.4310 | 4.44e-16 | +0.2467 | +0.3665 |
| Mean per-record Word Accuracy | 0.5892 | 0.5892 | 3.33e-16 | −0.2321 | −0.3469 |

**Headline:** MetricGAN+ pretrained **worsened** ASR on this dev-clean degraded
benchmark. Macro Word Accuracy dropped from 0.8213 (degraded) to 0.5892 (enhanced).
Tier classification: **`null_or_negative`**.

**Non-actions:**

- No enhancement run.
- No other Slurm jobs submitted.
- `docs/model_card.md` not modified (deferred to T4.3).
- `stash@{0}` untouched.

Prep commit: `1baa80b`. Wall-time bump commit: `8a40b4f`. Result commit: `PENDING_RESULT_COMMIT`. Report committed at `reports/training/metricgan_plus_wer.md`.

## Next task

T4.3 — update `docs/model_card.md` with the MetricGAN+ pretrained evaluation summary
(per-family + macro + tier from `reports/training/metricgan_plus_wer.md`) and activate
the B6.5 RP5 validation request. T4.3 is **pending authorization**.
