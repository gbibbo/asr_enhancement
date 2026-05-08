# Robust ASR — Asset Inventory

Produced by: P0.2
Date: 2026-05-08
Status: OBSERVATION ONLY — no reuse permission granted by this document.

Every asset listed here requires an explicit row in
`configs/robust_asr/reuse_policy_v1.yaml` before any robust_asr task may
read or import it. Listing an asset here does not grant any reuse permission.

---

## 1. Repository top-level files

| Path | Git-tracked | Notes |
|------|-------------|-------|
| CLAUDE.md | yes | Active profile; ROBUST_ASR_PROFILE block installed |
| README.md | yes | Project readme |
| plan.md | yes | Legacy state placeholder (611 B) |
| pyproject.toml | yes | Python project config |
| alembic.ini | yes | DB migration config |
| .env.example | yes | Safe example env file |
| .gitattributes | yes | Git merge attributes |
| .gitignore | yes | Ignore rules |

---

## 2. Legacy state paths

These paths are git-tracked and must not be edited by any robust_asr task.
They may be read by P10.3 (plan_tracker_consistency) only.

| Path | Size | Git-tracked | Class |
|------|------|-------------|-------|
| docs/progress/training_datamove1_progress.md | 169 KB | yes | legacy_state |
| docs/progress/training_datamove1_progress.yaml | 139 KB | yes | legacy_state |
| docs/progress/demo_platform_progress.md | 638 B | yes | legacy_state |
| docs/progress/demo_platform_progress.yaml | 413 B | yes | legacy_state |
| plan.md | 611 B | yes | legacy_state |
| docs/plans/archive/legacy_reference_plans/README.md | small | yes | legacy_state |
| docs/plans/archive/legacy_reference_plans/20260507T223435Z/demo_platform_plan.md | large | yes | legacy_state |
| docs/plans/archive/legacy_reference_plans/20260507T223435Z/training_datamove1_plan.md | large | yes | legacy_state |

Absent (not found in repo):
- `docs/claude_task_progress.md` — ABSENT
- `docs/claude_task_progress.yaml` — ABSENT
- `docs/plans/demo_platform_plan.md` (canonical) — ABSENT; archived at path above
- `docs/plans/training_datamove1_plan.md` (canonical) — ABSENT; archived at path above

---

## 3. Implementation code paths

All paths below are git-tracked. Class: implementation_reuse. Default
permitted_use: read_only. Tasks that need to extend them must request
CHANGE_SCOPE with an approved row in reuse_policy_v1.yaml.

| Path | Notes |
|------|-------|
| services/api/ | FastAPI service |
| services/worker/ | Celery worker service |
| services/frontend/ | Frontend (not in agent plan list, observed) |
| libs/asr_adapter/ | ASR adapter library |
| libs/audio_pipeline/ | Audio pipeline library |
| libs/audio/ | Audio utilities (metrics.py, degradations.py, enhancement.py) |
| libs/common/ | Shared common library (versions.py) |
| libs/observability/ | Observability library (not in agent plan list, observed) |
| infra/ | Infrastructure configs (compose, grafana, otel, prometheus) |
| scripts/training/ | Training scripts |
| slurm/tools/on_submit.sh | Slurm submit wrapper (504 B, git-tracked) |
| slurm/jobs/ | Slurm job scripts (29 files) |
| tests/ | Test suite (excluding tests/robust_asr/) |
| configs/training/ | Training configs |

Absent implementation paths:
- `scripts/demo/` — ABSENT (not present in repo)

---

## 4. Active robust_asr state paths

Owned by this plan. Written by approved tasks.

| Path | Notes |
|------|-------|
| docs/progress/robust_asr_progress.yaml | Live tracker |
| docs/progress/robust_asr_progress.md | Prose tracker |
| docs/progress/robust_asr_state_capsule.md | State capsule |
| reports/robust_asr/ | Task and phase reports |
| artifacts/robust_asr/ | Eval tables, manifests, router, handoff |
| configs/robust_asr/ | Robust ASR configs (reuse_policy_v1.yaml, etc.) |
| scripts/robust_asr/ | Robust ASR scripts |
| tests/robust_asr/ | Robust ASR tests |
| docs/reports/robust_asr/ | Model card, router card |
| docs/profiles/CLAUDE.robust_asr.md | Active Claude profile |

---

## 5. External host assets — candidate runtime

These paths are on the host filesystem outside the repository.
None are committed to git. All are large_artifact=true or no_touch=true.
No reuse is granted by this listing.

### 5.1 Apptainer image

| Path | Size | Modified | Git-tracked | Class |
|------|------|----------|-------------|-------|
| /mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif | 3.3 GB | 2026-01-15 | no | no_touch (external binary) |

### 5.2 Slurm submit wrapper (in repo)

| Path | Size | Git-tracked | Class |
|------|------|-------------|-------|
| slurm/tools/on_submit.sh | 504 B | yes | implementation_reuse |

### 5.3 Training root

Base: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/`

| Subdirectory | Modified | Notes |
|--------------|----------|-------|
| artifacts/ | 2026-05-06 | Prior training artifacts |
| cache/ | 2026-05-06 | Whisper + HuggingFace caches |
| datasets/ | 2026-05-06 | Dataset manifests and audio |
| demo_reference_artifacts/ | 2026-05-03 | Demo reference examples |
| dependency_reports/ | 2026-05-04 | Dependency probe reports |
| logs/ | 2026-05-06 | Slurm job logs |
| runs/ | 2026-05-06 | Training run directories |
| runtime/ | 2026-05-01 | Runtime files |
| tmp/ | 2026-05-02 | Temporary files |

### 5.4 Prior checkpoints (no_touch)

All `.pt` and `.ckpt` files are mandatory no-touch.

| Path | Class |
|------|-------|
| .../cache/whisper/base.en.pt | no_touch |
| .../cache/whisper/tiny.en.pt | no_touch |
| .../cache/speechbrain/metricgan_plus_voicebank/enhance_model.ckpt | no_touch |
| .../cache/huggingface/hub/models--speechbrain--metricgan-plus-voicebank/.../enhance_model.ckpt | no_touch |
| .../runs/_smoke/t6_2_gpu_preflight_2128737/checkpoints/*.pt (3 files) | no_touch |
| .../runs/_smoke/t6_2c_cpu_micro_2128640/checkpoints/*.pt (3 files) | no_touch |
| .../runs/_smoke/t6_2d_cpu_whisper_smoke_2128714/checkpoints/*.pt (2 files) | no_touch |
| .../runs/t6_2_full_training_2128952/checkpoints/*.pt (6 files) | no_touch |

### 5.5 Dataset root

| Path | Notes |
|------|-------|
| .../datasets/librispeech_manifest_v1.jsonl | Librispeech manifest |
| .../datasets/librispeech_manifest_v1_filtered.jsonl | Filtered manifest |
| .../datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl | Degraded manifest |
| .../datasets/librispeech_manifest_v1_filtered_degraded_v1_enhanced_metricgan_plus_pretrained.jsonl | Enhanced manifest |
| .../datasets/librispeech_manifest_v1_filtered_degraded_v1_smoke.jsonl | Smoke manifest |
| .../datasets/degraded/ | Degraded audio (no_touch *.wav/*.flac) |
| .../datasets/enhanced/ | Enhanced audio (no_touch *.wav/*.flac) |
| .../datasets/splits/ | Dataset split files |
| .../datasets/degraded_build/ | Build artifacts |
| .../datasets/degraded_smoke/ | Smoke build artifacts |

### 5.6 Demo reference artifacts

| Path | Contents |
|------|----------|
| .../demo_reference_artifacts/examples/ | 5 examples: ex001, ex003, ex004, ex007, ex010 |

### 5.7 Prior training runs

| Run ID | Notes |
|--------|-------|
| t3_1_baseline_full_2125895 | Whisper baseline full |
| t3_1_baseline_smoke_2125894 | Whisper baseline smoke |
| t3_2_baseline_degraded_full_2126086 | Degraded baseline full |
| t3_2_baseline_degraded_smoke_2126085 | Degraded baseline smoke |
| t3_2a_bank_full_2125897 | Degradation bank full |
| t3_2a_bank_smoke_2125896 | Degradation bank smoke |
| t4_2b_smoke_enhance_2126934 | Enhancement smoke |
| t4_2c_enhance_full_2127639 | Enhancement full |
| t4_2c_enhance_smoke_2127631 | Enhancement smoke |
| t4_2d_whisper_enhanced_full_2127693 | Whisper on enhanced full |
| t4_2d_whisper_enhanced_smoke_2127690 | Whisper on enhanced smoke |
| t5_3_dry_run_2128437 | Dry-run training |
| t5_3_dry_run_2128458 | Dry-run training |
| t6_2_full_training_2128952 | Full LoRA training run |
| t6_3_post_hoc_whisper_full_2129017 | Post-hoc Whisper eval |
| t7_1_post_hoc_whisper_step_10000/12500/15000/17500_2129063-66 | Per-checkpoint eval |

These runs are prior-branch artifacts. They are NOT valid robust_asr evidence
until P-phase validators accept them under the current plan.

### 5.8 AssemblyAI cache

NOT FOUND on host. No cache directories detected.

### 5.9 Pricing configs

NOT FOUND on host.

---

## 6. Absent paths (referenced in agent plan but not present)

| Path | Status |
|------|--------|
| scripts/demo/ | ABSENT — directory does not exist |
| docs/claude_task_progress.md | ABSENT — file does not exist |
| docs/claude_task_progress.yaml | ABSENT — file does not exist |
| docs/plans/demo_platform_plan.md (canonical) | ABSENT — archived |
| docs/plans/training_datamove1_plan.md (canonical) | ABSENT — archived |

---

## 7. Observation summary

- 5 legacy state paths present; 2 absent (docs/claude_task_progress.*)
- 2 legacy plans archived under docs/plans/archive/; canonical paths absent
- 11 implementation code dirs present; scripts/demo/ absent
- 1 Apptainer image candidate (3.3 GB, external)
- 1 Slurm submit wrapper (in repo, implementation_reuse)
- Training root present with 18+ prior run directories
- 18 prior checkpoint files (all no_touch)
- AssemblyAI cache: NOT FOUND
- Pricing configs: NOT FOUND
- 5 demo reference examples in external training root
