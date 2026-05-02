# Training Task Progress

Branch: feature/training-datamove1-v1
Integration branch: demo-rp5-v1
Current cut: T3
Current phase: Phase 3
Current task: Task T3.2
Last completed task: T3.2a
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
| Result commit | `PENDING_RESULT_COMMIT` |
| Summary report (Git) | `reports/training/degradation_bank_v1.md` |

## Next task

Task T3.2. Run degraded-audio Whisper baseline. **Unblocked.** Consume `$TRAIN_ROOT/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl` (SHA-256 `c6f87452f146…`).
