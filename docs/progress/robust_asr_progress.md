# Robust ASR LoRA Router — Progress

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Status: IN_PROGRESS

## Current state

- Phase: P2 (Whisper base baseline)
- Current task: P2.1 (Whisper base CT2 INT8 evaluation) — PASS (current_task held until orchestrator APPROVE_EXECUTION)
- Last completed: P1.4 (PASS — degradation_v1 generators and manifests; OK_DEGRADATION_V1; 0 BAD_OUTPUT)
- Phase summary: P0=PASS, P1=PASS
- Active markers: [BLOCKED_OOD_PUBLIC]
- Blocked: false
- Blocker: null
- claims_enabled.ood_real: false (no Section 1.1 OOD-real fallback resolves on host)
- normalization_version: normalization_v1 (frozen at P1.2)
- metrics_version: metrics_v1 (preserved; libs/audio/metrics.py unchanged)
- state_transport.last_accepted_report_commit: 28dddae0c503208f3042bb5989e2bf3f5798ef56 (advanced from 49b4bdc... by APPROVE_EXECUTION(P2.1-model-build) at commit 28dddae; the subsequent APPROVE_PLAN(P2.1-rerun) does not further advance, and the P2.1-rerun implementation commit is NOT recorded as accepted per orchestrator instruction)
- state_transport.expected_next_task: P2.1 (held — awaiting orchestrator APPROVE_EXECUTION(P2.1))
- latest_approval_packet: APPROVE_PLAN(P2.1-rerun) on `28dddae` (next P2.2)
- prior_approval_packet: APPROVE_EXECUTION(P2.1-model-build) on `28dddae` (next P2.1)
- prior_approval_packet_p2_1_model_build_plan: APPROVE_PLAN(P2.1-model-build) on `7253b87` (next P2.1)
- prior_approval_packet_p2_1_model_scope_exec: APPROVE_EXECUTION(P2.1-model-scope-change) on `7253b87` (next P2.1)
- prior_approval_packet_p2_1_model_change_scope: CHANGE_SCOPE(P2.1-model) on `268b8e9` (next P2.1)
- prior_approval_packet_p2_1_plan: APPROVE_PLAN(P2.1) on `def8458` (next P2.2)

## Tracker fix — last_accepted_report_commit advanced 49b4bdc -> 28dddae

- The P2.1 PASS update recorded
  `state_transport.last_accepted_report_commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db`
  (PHASE_APPROVE(P1) acceptance), but
  `APPROVE_EXECUTION(P2.1-model-build)` had accepted commit
  `28dddae0c503208f3042bb5989e2bf3f5798ef56`, which should have
  advanced the accepted commit at P2.1-rerun acceptance time.
  `APPROVE_PLAN(P2.1-rerun)` accepts the same commit and does not
  further advance.
- Tracker corrected:
  `state_transport.last_accepted_report_commit` set to
  `28dddae0c503208f3042bb5989e2bf3f5798ef56`. No code, no test, no
  task-status change. P2.1 PASS state held.
- Held: `current_task=P2.1`, `last_completed_task=P1.4`,
  `current_phase=P2`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `blocker=null`, `claims_enabled.ood_real=false`,
  `tasks.P2.1.status=PASS`, `tasks.P2.1.next_task=P2.2`,
  `state_transport.expected_next_task=P2.1`,
  `latest_approval_packet`=APPROVE_PLAN(P2.1-rerun) on `28dddae`,
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1-model-build) on
  `28dddae`.

## P2.1 PASS — whisper_base_ct2_int8 baseline evaluation (53,230 rows; MISSING_EVIDENCE cleared)

- ORCHESTRATOR_DECISIONs recorded:
  - `APPROVE_EXECUTION(P2.1-model-build)` on
    `accepted_report_commit=28dddae0c503208f3042bb5989e2bf3f5798ef56`,
    `next_expected_task=P2.1`. CT2 INT8 model at
    `…/runtime/whisper_models/whisper_base_en_ct2_int8/` is the binding
    baseline backend.
  - `APPROVE_PLAN(P2.1-rerun)` on
    `accepted_report_commit=28dddae0c503208f3042bb5989e2bf3f5798ef56`,
    `next_expected_task=P2.2`. Rerun accepted on the model-build
    commit; `state_transport.last_accepted_report_commit` NOT advanced.
- Deliverables (sha256 in tracker yaml `artifacts.*` / `tasks.P2.1.artifacts_added.*`):
  - `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`
    (53,230 rows; 31 columns; 16,591,882 bytes; sha256
    `0dc98736…f4a6`).
  - `reports/robust_asr/baseline_whisper_base.md`
    (sha256 `6e5e2f04…55e1`).
  - `scripts/robust_asr/run_backend_eval.py` (edited; sha256
    `36ba31bb…55e1`; prior `56ab650f…fa209d`). Added
    `eval_audio_id = source_audio_id + '::' + degradation_id` and a
    transcription cache keyed on `audio_sha256` so each
    `(source × condition_family × tier)` row is a distinct eval-table
    row and identical audio decodes once.
- Slurm execution (final PASS run):
  - Wrapper: `./slurm/tools/on_submit.sh sbatch /…/slurm/jobs/p2_1_baseline.sh`.
  - Job: `2129900`, name `asr_p2_1_baseline`, partition `2080ti`, host
    `aisurrey04`, GPU job.
  - State / ExitCode: `COMPLETED 0:0` in 2 h 40 m 00 s. MaxRSS
    811,860 KiB. Container sha256 `8db5364c…ce8713`.
  - 53,230 successful inferences; 0 row failures.
  - §5.8 budget: 10800 s (3 h); actual 9600 s (11.1 % margin).
- Per-family metrics (mean over successful rows; n=10,646 per family =
  2 tiers × 5323):
  - clean: WER 0.0709, WA 0.9367
  - muffled_lowpass: WER 0.1072, WA 0.9027
  - cafe_noise: WER 0.1241, WA 0.8784
  - far_field_room: WER 0.1410, WA 0.8623
  - phone_band: WER 0.6058, WA 0.6034
- Backend / model provenance:
  `backend_version=faster_whisper-1.2.1+ct2-int8+whisper_base_en_ct2_int8`;
  model.bin sha256 `4ed9e9b5…db33f`; source openai-whisper base.en.pt
  sha256 `25a8566e…ad` (canonical); ctranslate2 4.7.1; quantization
  int8; local_only=true; third_party_provider=null; cost_usd=null;
  normalization_version=normalization_v1.
- Verifications:
  - `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE` all emitted.
  - `validate_eval_table.py` → `rows=53230 unique_pk=53230
    unique_audio_id=53230`, `OK_EVAL_TABLE`, exit 0.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `pytest -q test_runtime_contract_skeleton.py test_eval_schema.py
    test_normalization_metrics.py test_leakage.py test_degradation_v1.py`
    → 85/85 PASS in 6.88 s.
- Bug-fix history:
  - Attempt 1 (Slurm `2129649`): HALTED `13:0` in 14 s,
    `MISSING_EVIDENCE` — CT2 weights absent. Resolved by
    CHANGE_SCOPE(P2.1-model) + P2.1-model-build (`2129651`).
  - Attempt 2 (Slurm `2129652`): COMPLETED `0:0` in 18 m 32 s; all
    sentinels emitted but only 5,323 rows (clean tier only) due to
    PK collapse on source-only audio_id. Detected post-run; no PASS
    declared on under-counted parquet.
  - Attempt 3 (Slurm `2129900`, this PASS): COMPLETED `0:0` in
    2 h 40 m 00 s; 53,230 rows; full coverage.
- Tracker mutations: `tasks.P2.1.status=PASS`;
  `tasks.P2.1.next_task=P2.2`; `tasks.P2.1.marker=null`;
  `tasks.P2.1.slurm.job_id=2129900`, `state=COMPLETED`, `exit_code=0:0`,
  `sentinel=OK_BACKEND_EVAL`; history block records attempts 1 and 2.
  `markers=[BLOCKED_OOD_PUBLIC]` (MISSING_EVIDENCE cleared;
  BLOCKED_OOD_PUBLIC held — non-blocking, `claims_enabled.ood_real=false`).
  `blocked=false`; `blocker=null`. `current_task=P2.1` held (orchestrator
  finalizes via APPROVE_EXECUTION before P2.2 may start);
  `last_completed_task=P1.4` held. `state_transport.last_accepted_report_commit`
  STAYS `49b4bdc…` per orchestrator instruction;
  `state_transport.expected_next_task=P2.1` held.
  `latest_approval_packet`=APPROVE_PLAN(P2.1-rerun) on `28dddae`;
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1-model-build) on
  `28dddae`. `artifacts.baseline_table.{sha256,rows}` and
  `artifacts.baseline_report.sha256` populated. New
  `tasks.P2.1.artifacts_added.{eval_table, baseline_report_full}` entries.

## P2.1-model-build PASS — CT2 INT8 weights produced (parent P2.1 still HALTED)

- ORCHESTRATOR_DECISIONs recorded:
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
    advanced.
- Implementation deliverables:
  - `scripts/robust_asr/build_whisper_base_ct2_int8.py`
    (sha256 `79f29b5c…835e`). Source-sha256 verification, three
    conversion strategies in order, idempotent provenance write.
  - `slurm/jobs/p2_1_build_ct2_model.sh`
    (sha256 `e575f874…9e1e`). Apptainer SIF exec, env-isolated,
    CPU-only, `--time=00:30:00`, `--mem=8G`, `--cpus-per-task=2`.
  - `reports/robust_asr/whisper_base_ct2_int8_build.md`.
- Slurm job 2129651 COMPLETED 0:0 in 32 s on aisurrey04 (partition
  `2080ti`); MaxRSS 836,324 KiB; container sha256 `8db5364c…ce8713`
  matches tracker; sentinel `OK_CT2_BUILD` printed.
- Conversion outcome: strategy 1 (`OpenAIWhisperConverter`) — class
  removed from ctranslate2 4.x; strategy 2 (`ct2-transformers-converter`
  CLI) — failed with `TypeError: WhisperForConditionalGeneration.__init__()
  got an unexpected keyword argument 'dtype'` (transformers/ctranslate2
  API mismatch); strategy 3 (`TransformersConverter` Python API with
  patched `load_model` that strips `dtype`/`torch_dtype` before
  `from_pretrained`) — PASS.
- Model directory:
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/whisper_models/whisper_base_en_ct2_int8/`
  - `model.bin` (76,396,161 bytes; sha256 `4ed9e9b5…db33f`).
  - 11 ancillary files (config, tokenizer, vocab, normalizer, generation
    config, etc.); per-file sha256s in `provenance.json`.
  - `provenance.json` records: source path + sha256 +
    `source_canonical_sha256=25a8566e…ad`,
    `ctranslate2_version=4.7.1`, `quantization=int8`, three conversion
    attempts, `container_sha256`, `slurm_job_id=2129651`, host, UTC
    timestamp.
- Source: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/cache/whisper/base.en.pt`,
  sha256 `25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead`,
  matches the canonical openai-whisper `_MODELS["base.en"]` hash.
  HF mirror `openai/whisper-base.en` was used for model-class load only;
  conversion outputs derive from those (canonically identical) bytes.
- Prior attempt: Slurm job `2129650` FAILED `1:0` in 31 s
  (strategies 1+2; strategy 3 not yet present at that commit). No
  partial output retained because the build script wipes the output
  directory between strategies and writes provenance.json only on
  full success.
- Verifications: `OK_CT2_BUILD` emitted; model.bin present; 12 output
  files written; provenance.json records all required fields. P2.1
  baseline rerun NOT executed; non-regression checks not re-run on this
  build (no robust_asr code under test changed).
- Tracker mutations: new `tasks.P2.1.subtasks.P2.1-model-build` block
  with status PASS and Slurm metadata; new
  `tasks.P2.1.artifacts_added.{build_whisper_base_ct2_int8_script,
  p2_1_build_ct2_model_slurm_job, whisper_base_ct2_int8_build_report,
  whisper_base_ct2_int8_model}` entries; `latest_approval_packet`
  replaced with APPROVE_PLAN(P2.1-model-build) and
  APPROVE_EXECUTION(P2.1-model-scope-change) shifted to
  `prior_approval_packet`. **`tasks.P2.1.status` stays `HALTED`** (the
  build does not by itself satisfy the parent task's PASS criteria).
  `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` held; `blocked=true`
  held; `current_task=P2.1` held; `last_completed_task=P1.4` held;
  `state_transport.last_accepted_report_commit=49b4bdc…` held.

## P2.1 model-remediation scope change (no conversion; CT2 source/output paths authorized)

- ORCHESTRATOR_DECISION: scope=scope_change task=P2.1-model phase=P2
  decision=CHANGE_SCOPE accepted_report_commit=`268b8e9d0f999bce905a4f2f3652b821ff08a0c3`
  next_expected_task=P2.1.
- Required fix: Authorize read-only use of the local OpenAI Whisper
  `base.en.pt` checkpoint and read-write robust_asr CT2 INT8 model
  output path.
- `configs/robust_asr/reuse_policy_v1.yaml` amended with two new override
  rows under the `…/cache/**` no_touch and `…/runtime/**` data_root blocks:
  - `/mnt/.../cache/whisper/base.en.pt` — `class=data_root`,
    `permitted_use=read_only`, `allowed_tasks=[P2.1]`,
    `validator=sha256==25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead`,
    `checksum_required=true`, `large_artifact=true`,
    `commit_allowed=false`. Cache root retains its no_touch posture for
    every other path.
  - `/mnt/.../runtime/whisper_models/**` — `class=model_root`,
    `permitted_use=read_write`,
    `allowed_tasks=[P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P7.2, P8.1]`,
    `validator=sha256_recorded_in_provenance_json`,
    `checksum_required=true`, `large_artifact=true`,
    `commit_allowed=false`. P2.1 writes
    `whisper_base_en_ct2_int8/{model.bin,config.json,tokenizer*,vocabulary*,provenance.json}`;
    downstream tasks read the same root.
  - New sha256: `9766167cccd3d246a31adb488d89dcc6950b35c00e0eb5959b523c4c5fa8811b`,
    `last_amended_by=P2.1_model_scope_change`.
- `reports/robust_asr/touch_policy.md` P2.1 row extended (additive) with:
  - allowed_write_paths: `scripts/robust_asr/build_whisper_base_ct2_int8.py`,
    `slurm/jobs/p2_1_build_ct2_model.sh`,
    `reports/robust_asr/whisper_base_ct2_int8_build.md`.
  - external_paths_requiring_approval: read-only access to
    `/mnt/.../cache/whisper/base.en.pt` (sha256-pinned 25a8566e…ad);
    read_write access to `/mnt/.../runtime/whisper_models/**`.
  - New sha256: `e51dc99337cbd22e5f7f359f5ae154e79351b50d58b31d4259242a764dc03db3`,
    `last_amended_by=P2.1_model_scope_change`.
- `configs/robust_asr/eval_manifests_v1.yaml` updated to put the new
  robust_asr-controlled path
  `/mnt/.../runtime/whisper_models/whisper_base_en_ct2_int8` first in
  `backend_endpoints.whisper_base_ct2_int8.candidate_local_paths`; the
  prior four paths are kept as fallbacks. New sha256:
  `1e371f369b7585099aa3eaaf24202371070eff61d6b7600ccb1158e1e9859130`.
- Tracker mutations: `latest_approval_packet` replaced with the
  CHANGE_SCOPE(P2.1-model) packet (prior APPROVE_PLAN(P2.1) shifted to
  `prior_approval_packet`; APPROVE_EXECUTION(P2.1-scope-change) shifted
  to `prior_approval_packet_p2_1_scope_exec`);
  `artifacts.reuse_policy_config.sha256` and
  `artifacts.touch_policy.sha256` updated; both `last_amended_by` set to
  `P2.1_model_scope_change`. `artifacts_added.eval_manifests_v1.sha256`
  updated; `last_amended_by=P2.1_model_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS `49b4bdc…`
  (PHASE_APPROVE(P1) acceptance; CHANGE_SCOPE does not advance).
  `state_transport.expected_next_task` STAYS `P2.1`.
- Held: `current_phase=P2`, `current_task=P2.1` (still HALTED),
  `last_completed_task=P1.4`,
  `markers=[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]` (MISSING_EVIDENCE NOT
  cleared), `blocked=true`, `claims_enabled.ood_real=false`,
  `phase_summary={P0:PASS, P1:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`.
- Conversion NOT executed: no `build_whisper_base_ct2_int8.py`, no
  Slurm build job, no model bytes written under `runtime/whisper_models/`,
  no rerun of `slurm/jobs/p2_1_baseline.sh`, no Apptainer call, no GPU,
  no external API.
- Non-regression: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE`.

## P2.1 HALTED — MISSING_EVIDENCE (CT2 INT8 weights absent)

- ORCHESTRATOR_DECISIONs recorded by P2.1:
  - `APPROVE_EXECUTION(P2.1-scope-change)` on
    `accepted_report_commit=def84589316237a7e2239967ae93448ecacd63a2`,
    `next_expected_task=P2.1`. Scope-change rows from CHANGE_SCOPE(P2.1)
    (configs/robust_asr/** P2.1 allowed_tasks; rewritten touch_policy
    P2.1 row) are now binding.
  - `APPROVE_PLAN(P2.1)` on
    `accepted_report_commit=def84589316237a7e2239967ae93448ecacd63a2`,
    `next_expected_task=P2.2`. Implementation accepted on the
    scope-change commit; `state_transport.last_accepted_report_commit`
    is NOT advanced to the P2.1 implementation commit per orchestrator
    instruction.
- Implementation deliverables (sha256 in `tasks.P2.1.artifacts_added`):
  - `configs/robust_asr/eval_manifests_v1.yaml`
  - `scripts/robust_asr/run_backend_eval.py`
    (Section 4.2 contract; CT2 weight probe; clean MISSING_EVIDENCE halt)
  - `scripts/robust_asr/summarize_backend_eval.py`
    (Section 4.2 contract; per-family WER/WA aggregation)
  - `scripts/robust_asr/validate_eval_table.py`
    (Section 4.1 contract; Section 3 schema tests 1..7)
  - `slurm/jobs/p2_1_baseline.sh`
    (apptainer --nv; --gres=gpu:1; cpus=4; mem=24G; time=03:00:00;
    partition=2080ti; env-isolation matching P0.3-rerun-2 pattern)
  - `reports/robust_asr/task_reports/P2.1_baseline.md`
- Slurm job 2129649 FAILED 13:0 in 14 s on aisurrey04 (partition
  2080ti). Container sha256 `8db5364c…` matches tracker. Sentinel
  `MISSING_EVIDENCE` printed to stdout; the script exited 13 BEFORE
  attempting any model load, network access, or row evaluation.
- candidate_local_paths probed (none resolved):
  `${ASR_CACHE_ROOT}/whisper_ct2_int8_base_en`,
  `/mnt/.../scratch4weeks/.../runtime/whisper_models/Systran--faster-whisper-base.en`,
  `${HF_HOME}/hub/models--Systran--faster-whisper-base.en`,
  `${ASR_CACHE_ROOT}/huggingface/hub/models--Systran--faster-whisper-base.en`.
- On host: `…/cache/whisper/` holds only `base.en.pt` + `tiny.en.pt`
  (openai-whisper PyTorch checkpoints, not CT2 INT8); HF hub holds
  only `models--speechbrain--metricgan-plus-voicebank/`. The cache
  root is classified `no_touch` in `reuse_policy_v1.yaml`, so
  populating CT2 INT8 weights requires a CHANGE_SCOPE that names the
  destination host path and the provenance source.
- Verifications (host Python):
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `pytest -q tests/robust_asr/test_runtime_contract_skeleton.py
    test_eval_schema.py test_normalization_metrics.py test_leakage.py
    test_degradation_v1.py` → 85/85 PASS in 2.87 s (non-regression).
  - `OK_BACKEND_EVAL`, `OK_BACKEND_SUMMARY`, `OK_EVAL_TABLE`: NOT
    EMITTED (intended HALT).
  - `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
    `reports/robust_asr/baseline_whisper_base.md`: NOT WRITTEN.
- Tracker mutations: `tasks.P2.1.status=HALTED`,
  `tasks.P2.1.marker=MISSING_EVIDENCE`,
  `tasks.P2.1.next_task=P2.1` (held); `markers` extended to
  `[BLOCKED_OOD_PUBLIC, MISSING_EVIDENCE]`; `blocked=true`;
  `blocker` set; `current_task=P2.1` held; `last_completed_task=P1.4`
  held; `state_transport.last_accepted_report_commit` STAYS `49b4bdc`
  per orchestrator instruction; `state_transport.expected_next_task=P2.1`
  held. `latest_approval_packet`=APPROVE_PLAN(P2.1) on `def8458`;
  `prior_approval_packet`=APPROVE_EXECUTION(P2.1-scope-change) on
  `def8458`.
- Unblock path: provide CT2 INT8 weights at one of the declared
  candidate paths (Systran/faster-whisper-base.en snapshot; converted
  openai-whisper base.en.pt via ct2-converters; or a vetted internal
  mirror) under a CHANGE_SCOPE packet that records the host path and
  provenance. After weights resolve, rerun `slurm/jobs/p2_1_baseline.sh`;
  no code change needed in `run_backend_eval.py`.

## P2.1 scope change (no P2.1 implementation; baseline eval paths authorized)

- ORCHESTRATOR_DECISION: scope=scope_change task=P2.1 phase=P2
  decision=CHANGE_SCOPE accepted_report_commit=`22201db1a11586151811f814b14219e099e1a1ed`
  next_expected_task=P2.1.
- Required fix: Authorize P2.1 eval config and backend-eval scripts;
  update stale touch_policy P2.1 row.
- `configs/robust_asr/reuse_policy_v1.yaml` amended:
  - `configs/robust_asr/**` row: P2.1 added to `allowed_tasks`
    (now `[P0.2, P0.3, P0.4, P1.1, P1.2, P1.4, P2.1]`). Authorizes
    P2.1 to author `configs/robust_asr/eval_manifests_v1.yaml`.
  - New sha256: `678d86a37ae471448736b08a68a9b34802ad6599ea12b08f3a0a33041d2aab6f`,
    `last_amended_by=P2.1_scope_change`.
- `reports/robust_asr/touch_policy.md` P2.1 row REWRITTEN to authorize
  the v3.4.7 P2.1 deliverables: `configs/robust_asr/eval_manifests_v1.yaml`,
  `scripts/robust_asr/run_backend_eval.py`,
  `scripts/robust_asr/summarize_backend_eval.py`,
  `scripts/robust_asr/validate_eval_table.py`,
  `slurm/jobs/p2_1_baseline.sh`,
  `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`,
  `reports/robust_asr/baseline_whisper_base.md`,
  `reports/robust_asr/task_reports/P2.1_baseline.md`,
  scope-change rows on `reuse_policy_v1.yaml`/`touch_policy.md`,
  three live trackers. Reads include `configs/robust_asr/data_v1.yaml`,
  `configs/robust_asr/degradation_v1.yaml`, `libs/common/eval_schema.yaml`,
  `libs/common/normalization.py`, `libs/common/metrics.py`,
  `libs/common/versions.py`, `libs/audio/**`, `libs/asr_adapter/**`,
  `libs/audio_pipeline/**`, robust_asr public manifests, and
  degradation_v1 manifests. External: Slurm submit; Apptainer (exec)
  on the robust_asr SIF; LibriSpeech and degradation_v1 audio
  (read-only).
  New sha256: `1b38914f1e814619d202a610ba98ca1cc18d404b9d507f5084d5871b2721c0e3`,
  `last_amended_by=P2.1_scope_change`.
- Tracker mutations: `latest_approval_packet` replaced with the P2.1
  CHANGE_SCOPE packet (prior PHASE_APPROVE(P1) shifted to
  `prior_approval_packet`; APPROVE_EXECUTION(P1.4) shifted to
  `prior_approval_packet_p1_gate`); `artifacts.reuse_policy_config.sha256`
  and `artifacts.touch_policy.sha256` updated; both `last_amended_by`
  set to `P2.1_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS `49b4bdc…`
  (PHASE_APPROVE(P1) acceptance; CHANGE_SCOPE does not advance).
  `state_transport.expected_next_task` STAYS `P2.1`.
- Held: `current_phase=P2`, `current_task=P2.1`,
  `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `claims_enabled.ood_real=false`,
  `phase_summary={P0:PASS, P1:PASS}`,
  `orchestrator_approvals={P0:PHASE_APPROVE, P1:PHASE_APPROVE}`.
- P2.1 implementation NOT executed: no `eval_manifests_v1.yaml`, no
  `run_backend_eval.py`, no `summarize_backend_eval.py`, no
  `validate_eval_table.py`, no Slurm job, no eval table, no baseline
  report, no Slurm, no Apptainer, no GPU, no external API.
- Non-regression: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE`.

## P1 phase gate (PHASE_APPROVE)

- ORCHESTRATOR_DECISION: scope=phase phase=P1 decision=PHASE_APPROVE
  accepted_report_commit=`49b4bdc122b9b9768b380ab9bb9c28bec49455db`
  next_expected_task=P2.1.
- Rationale: P1 phase gate accepted as PASS_WITH_PREDICATE_NOTE.
  P1.1 and P1.3 are PARTIAL only because OOD-real is unavailable;
  `BLOCKED_OOD_PUBLIC` is active, non-blocking, and
  `claims_enabled.ood_real=false`. P1.2 and P1.4 are PASS. Required
  LibriSpeech manifests, eval schema, normalization, metrics, leakage
  tests, and degradation_v1 artifacts are present. No active blocking
  markers (no MISSING_EVIDENCE, no PLAN_CONFLICT).
- Tracker mutations: `phase_summary.P1=PASS`,
  `orchestrator_approvals.P1=PHASE_APPROVE`,
  `current_phase=P2`, `current_task=P2.1`,
  `last_completed_task=P1.4` (held),
  `state_transport.last_accepted_report_commit` STAYS `49b4bdc`
  (PHASE_APPROVE accepted on the P1.4 PASS implementation commit;
  not advanced),
  `state_transport.expected_next_task=P2.1`.
- Held: `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `claims_enabled.cloud_tradeoff=true`,
  `claims_enabled.positive_lora=pending`,
  `claims_enabled.positive_system=pending`,
  `degradation_version=degradation_v1`,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1`.

## P1.4 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P1.4 phase=P1
  decision=APPROVE_EXECUTION
  accepted_report_commit=`49b4bdc122b9b9768b380ab9bb9c28bec49455db`
  next_expected_task=P1_GATE.
- Rationale: P1.4 passed. `OK_DEGRADATION_V1` emitted, 0 BAD_OUTPUT,
  degradation_v1 manifests built for ID and OOD-param eval, scratch
  usage stayed under budget, tests and report-shape validation passed.
  `BLOCKED_OOD_PUBLIC` remains active and non-blocking.
- Tracker: `current_phase=P1`, `current_task=P1_GATE`,
  `last_completed_task=P1.4`, `markers=[BLOCKED_OOD_PUBLIC]` held,
  `blocked=false` held, `claims_enabled.ood_real=false` held,
  `degradation_version=degradation_v1` held,
  `state_transport.last_accepted_report_commit` advanced
  `d230971 -> 49b4bdc`,
  `state_transport.expected_next_task=P1_GATE`,
  `tasks.P1.4.next_task=P1_GATE`,
  `tasks.P1.4.commit=49b4bdc122b9b9768b380ab9bb9c28bec49455db`.
- P1 gate predicate (Section 8 P1) satisfiable: tasks[P1.1=PARTIAL accepted,
  P1.2=PASS, P1.4=PASS] and tasks[P1.3=PARTIAL accepted]. Awaiting orchestrator
  PHASE_APPROVE(P1) before P2.1 may begin.

## P1.4 PASS — degradation_v1 generators and manifests

- ORCHESTRATOR_DECISIONs: APPROVE_EXECUTION(P1.4-scope-change) and
  APPROVE_PLAN(P1.4), both on `accepted_report_commit=5c72769d1cdf6f7aa7e789a02c2f05aa69284341`.
  APPROVE_EXECUTION(P1.4-scope-change) sets `next_expected_task=P1.4`;
  APPROVE_PLAN(P1.4) sets `next_expected_task=P1_GATE`.
- Deliverables (sha256 in tracker yaml `artifacts.*`):
  - `libs/audio/degradations.py` — additive narrow patch: appended
    `sample_clean`, `sample_cafe_noise`, `sample_phone_band`,
    `sample_far_field_room`, `sample_muffled_lowpass` and a
    `SAMPLE_FUNCTIONS` registry. Existing `apply_degradation`,
    `DEGRADATION_FAMILIES`, `DEGRADATION_PARAMS`, and
    `DEGRADATION_VERSION` value `"degradation_v1"` preserved.
  - `configs/robust_asr/degradation_v1.yaml` — eval-only sources
    (`librispeech_validation`, `librispeech_locked_test`); per-family
    ID and OOD-param ranges (disjoint per family); master_seed=20260508;
    50 GB scratch budget recorded.
  - `scripts/robust_asr/build_degradation_v1.py` — §4.3 contract;
    emits `OK_DEGRADATION_V1`; per-family success/skip/BAD_OUTPUT counts;
    `INSUFFICIENT_SCRATCH` halt; idempotent resume per-row.
  - `slurm/jobs/p1_4_build_degradation_v1.sh` — Apptainer SIF exec;
    cpus=16 mem=16G time=06:00:00 partition=2080ti.
  - `tests/robust_asr/test_degradation_v1.py` — 24 tests covering
    metadata fields, RMS ≥ 1e-6, clipping_ratio < 0.5, source sha256
    match, determinism, ID/OOD parameter disjointness, phone_band
    bit_depth.
  - `artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet`
    (26 615 rows; sha256 `cf0f0bce…`).
  - `artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet`
    (26 615 rows; sha256 `30684dc4…`).
  - 10 per-family parquets (5 families × 2 tiers; 5 323 rows each;
    sha256s in `degradation_v1_build_summary.json`).
  - `artifacts/robust_asr/manifests/degradation_v1_build_summary.json`.
  - `reports/robust_asr/degradation_v1_summary.md`.
  - `reports/robust_asr/task_reports/P1.4_degradation_v1.md`.
- Source data: 5 323 LibriSpeech eval rows (validation 2 703 +
  locked_test 2 620). `lora_train` and `router_train` deliberately
  excluded — training-time degradation is owned by P3.1 / P4.1.
- Audio output: 42 584 `.wav` (8 wavs/source; clean is identity, no
  audio rewritten) under
  `/mnt/fast/nobackup/scratch4weeks/.../datasets/degradation_v1/<family>/<tier>/<audio_id>.wav`.
  Never committed.
- Verifications (Slurm + non-regression + report shape):
  - Slurm job `2129647` COMPLETED `0:0` in 1 min 3 s on aisurrey01
    (partition `2080ti`, MaxRSS 11 077 812 KiB). Sentinel
    `OK_DEGRADATION_V1` with per-family/tier counts `5323/0`.
  - `pytest -q tests/robust_asr/test_degradation_v1.py
    tests/robust_asr/test_eval_schema.py
    tests/robust_asr/test_normalization_metrics.py
    tests/robust_asr/test_leakage.py
    tests/robust_asr/test_runtime_contract_skeleton.py` →
    85/85 PASS in 2.59 s.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
- Section 5.8 budget: 50 GB scratch, 6 h/family wall-clock; actual
  10.297 GB scratch used and ~9 s/family/tier. Safety margin ≥ 4×.
- Section 9 P1.4 Decision rule 1 (BAD_OUTPUT > 1 % per family):
  NOT FIRED. 0 / 53 230 BAD_OUTPUT across all 5 families × 2 tiers.
- ID vs OOD-param disjointness verified (cafe_noise snr, far_field_room
  rt60 + mic_distance, muffled_lowpass lowpass + attenuation,
  phone_band bit_depth).
- Prior attempt: Slurm job `2129646` FAILED `1:0` in 10 s due to
  `pyarrow OverflowError: Python int too large to convert to C long`
  on uint64 seeds. Fixed by masking the per-row seed to 63 bits
  (`(1<<63)-1`) so it fits pyarrow `int64`. Determinism preserved
  (SHA-256-derived 63-bit unsigned space, 9.2e18 distinct seeds).
  No partial parquets were committed.
- Tracker mutations: `tasks.P1.4.status=PASS`,
  `tasks.P1.4.next_task=P1_GATE`, `tasks.P1.4.marker=BLOCKED_OOD_PUBLIC`;
  `degradation_version=degradation_v1`; `current_task=P1.4` held;
  `last_completed_task=P1.3` held;
  `markers=[BLOCKED_OOD_PUBLIC]` held; `blocked=false` held;
  `claims_enabled.ood_real=false` held;
  `state_transport.last_accepted_report_commit` STAYS
  `d230971e8995484449095ae914b58c47c4d43b94` per orchestrator
  instruction (not advanced to the P1.4 implementation commit);
  `state_transport.expected_next_task=P1.4` (held until orchestrator
  reviews the P1.4 Execution Report).
  `latest_approval_packet`=APPROVE_PLAN(P1.4) on `5c72769`;
  `prior_approval_packet`=APPROVE_EXECUTION(P1.4-scope-change) on `5c72769`.

## P1.4 scope change (no implementation; reuse_policy + touch_policy amended)

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.4 phase=P1
  decision=CHANGE_SCOPE
  accepted_report_commit=`d230971e8995484449095ae914b58c47c4d43b94`
  next_expected_task=P1.4.
- Required fix: Authorize additive P1.4 degradation_v1 implementation,
  Slurm job, runtime SIF exec, and scratch dataset writes.
- `configs/robust_asr/reuse_policy_v1.yaml` amended:
  - NEW override row for `libs/audio/degradations.py`
    (class=existing_runtime_code, permitted_use=append_functions_only,
    allowed_tasks=[P1.4], validator=tests/robust_asr/test_degradation_v1.py,
    checksum_required=true, commit_allowed=true). Authorizes the five
    Section 3 `sample_<family>` additions; preserves `apply_degradation`,
    `DEGRADATION_FAMILIES`, and the `DEGRADATION_VERSION` value.
  - `slurm/jobs/**` row: P1.4 added to `allowed_tasks`.
  - `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif`
    row: P1.4 added to `allowed_tasks` (exec_only).
  - `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**`
    row: P1.4 added to `allowed_tasks` (read_only for source LibriSpeech audio).
  - NEW override row for
    `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degradation_v1/**`
    (class=data_root, permitted_use=read_write, allowed_tasks=[P1.4, P2.1, P3.1,
    P4.1, P4.2, P4.3, P8.1], large_artifact, never committed). P1.4 audio outputs
    land here under Section 5.8 budget (max 50 GB scratch).
  - New sha256: `f0528f7d4d14638b3cfdc4ede17c25c347cd3b838e844399fdfaf36464d81757`,
    last_amended_by=`P1.4_scope_change`.
- `reports/robust_asr/touch_policy.md` P1.4 row REWRITTEN to authorize the
  v3.4.7 P1.4 deliverables (`libs/audio/degradations.py` append-only narrow
  patch, `configs/robust_asr/degradation_v1.yaml`,
  `scripts/robust_asr/build_degradation_v1.py`,
  `slurm/jobs/p1_4_build_degradation_v1.sh`,
  `tests/robust_asr/test_degradation_v1.py`,
  `artifacts/robust_asr/manifests/degradation_v1_*.parquet`,
  `reports/robust_asr/degradation_v1_summary.md`,
  `reports/robust_asr/task_reports/P1.4_degradation_v1.md`,
  scope-change rows on policy files, three live trackers). External resources:
  Slurm submit; Apptainer (exec) on the robust_asr SIF; LibriSpeech sources
  (read-only); degradation_v1 scratch subtree (read_write).
  New sha256: `ede82ac0889628c87eab523d9fbd238995f2b041272004a835931ca5fb501f66`,
  last_amended_by=`P1.4_scope_change`.
- Tracker mutations: `latest_approval_packet` replaced with the P1.4
  CHANGE_SCOPE packet (prior P1.3 APPROVE_EXECUTION shifted to
  `prior_approval_packet`; previous APPROVE_PLAN(P1.3) and
  APPROVE_EXECUTION(P1.3-scope-change) shifted to `prior_approval_packet_00`
  and `prior_approval_packet_001`); `artifacts.reuse_policy_config.sha256`
  and `artifacts.touch_policy.sha256` updated; both `last_amended_by` set
  to `P1.4_scope_change`.
  `state_transport.last_accepted_report_commit` advanced
  `b049f94 -> d230971` per the APPROVE_EXECUTION(P1.3) packet; CHANGE_SCOPE
  does not further advance.
- Held: `current_task=P1.4`, `last_completed_task=P1.3`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `phase_summary.P0=PASS`,
  `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.4 implementation NOT executed: no `degradations.py` patch, no
  `degradation_v1.yaml`, no `build_degradation_v1.py`, no Slurm job, no
  manifests, no test file, no pytest run, no Apptainer, no GPU, no external API.
- Non-regression: `validate_report_shape.py` against the canonical
  fixtures emitted `OK_REPORT_SHAPE`.

## P1.3 PARTIAL — public LibriSpeech manifests; OOD-real splits skipped

- ORCHESTRATOR_DECISIONs recorded by P1.3:
  - `APPROVE_EXECUTION(P1.3-scope-change)` on `accepted_report_commit=7579602`,
    `next_expected_task=P1.3`. Rewritten touch_policy P1.3 row authorizing
    `build_public_manifests.py`, `summarize_manifests.py`, manifest parquets,
    summary, and task report is now binding.
  - `APPROVE_PLAN(P1.3)` on `accepted_report_commit=7579602`,
    `next_expected_task=P1.4`.
- Deliverables (sha256 in tracker yaml `artifacts.*`):
  - `scripts/robust_asr/build_public_manifests.py` — reads `data_v1.yaml`,
    walks LibriSpeech subsets, hashes each `.flac`, probes duration with
    `soundfile.info`, writes one parquet per `<dataset>_<split>` with
    columns `{audio_id, source_dataset, source_subset, speaker_id,
    chapter_id, utterance_id, audio_path_or_uri, audio_sha256,
    duration_s, sample_rate, num_frames, split_label}`. Halts (exit 1)
    only when a required LibriSpeech split has no resolvable rows.
  - `scripts/robust_asr/summarize_manifests.py` — emits markdown summary
    with per-manifest row count, duration, distinct speaker count,
    parquet byte sha256, and OOD-real claim status.
  - `artifacts/robust_asr/manifests/librispeech_{lora_train,router_train,validation,locked_test}.parquet`
  - `reports/robust_asr/manifest_summary.md`
  - `reports/robust_asr/task_reports/P1.3_manifest_summary.md`.
- Manifest counts:
  - `librispeech_lora_train.parquet`: 22 507 rows, 200 spk, 286 505.07 s
    (79.5848 h), sha256 `7896175e…`.
  - `librispeech_router_train.parquet`: 6 032 rows, 51 spk, 75 622.10 s
    (21.0061 h), sha256 `c3d281ab…`.
  - `librispeech_validation.parquet`: 2 703 rows, 40 spk, 19 396.12 s
    (5.3878 h), sha256 `977a6f01…`.
  - `librispeech_locked_test.parquet`: 2 620 rows, 40 spk, 19 452.48 s
    (5.4035 h), sha256 `ad4f401e…`.
  - Totals: 33 862 rows, 331 distinct speakers, 400 975.77 s (111.3822 h).
  - Cross-check: lora_train + router_train = 28 539 = train-clean-100;
    validation = 2 703 = dev-clean; locked_test = 2 620 = test-clean.
- OOD-real / demo splits skipped (Decision rule 1 fired):
  - `ood_real_locked`: `SKIPPED_OOD_PUBLIC_DEFERRED`
    (`no_source_dataset_selected`).
  - `common_voice_demo_reserved`: `SKIPPED_OOD_PUBLIC_DEFERRED`
    (`root_absent_or_empty`; `present_on_host=false`,
    `declared_speakers=0`).
  - `marker=BLOCKED_OOD_PUBLIC` and `claims_enabled.ood_real=false`
    held; no fallback admitted in P1.3 (plan §1 rule 5).
- Verifications (host Python; no Slurm, no SIF, no GPU, no external API):
  - `build_public_manifests.py` → `OK_PUBLIC_MANIFESTS`, exit 0,
    wall-clock 10.151 s for 33 862 files (~7 GiB).
  - `summarize_manifests.py` → `OK_MANIFEST_SUMMARY`, exit 0.
  - `validate_report_shape.py` → `OK_REPORT_SHAPE`, exit 0.
  - `check_speaker_disjoint.py --splits lora_train router_train
    validation locked_test` → `OK_SPEAKER_DISJOINT` (non-trivial).
  - `pytest -q test_runtime_contract_skeleton.py test_eval_schema.py
    test_normalization_metrics.py test_leakage.py` → 61/61 PASS in 1.42 s.
- Tracker mutations: `tasks.P1.3.status=PARTIAL`,
  `tasks.P1.3.marker=BLOCKED_OOD_PUBLIC`, `tasks.P1.3.next_task=P1.4`,
  `current_task=P1.4`, `last_completed_task=P1.3`,
  `markers=[BLOCKED_OOD_PUBLIC]` held, `blocked=false` held,
  `claims_enabled.ood_real=false` held,
  `state_transport.last_accepted_report_commit` STAYS `b049f9494f9acf163d6b5799f1f6450eaeee36c5`
  (per orchestrator instruction; NOT advanced to the P1.3
  implementation commit), `state_transport.expected_next_task=P1.4`,
  `latest_approval_packet=APPROVE_PLAN(P1.3)` on `7579602`,
  `prior_approval_packet=APPROVE_EXECUTION(P1.3-scope-change)` on `7579602`.
  `artifacts.manifest_summary`, `artifacts.build_public_manifests_script`,
  `artifacts.summarize_manifests_script`, and a new
  `artifacts.public_manifests` block populated.

## P1.3 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.3 phase=P1
  decision=CHANGE_SCOPE accepted_report_commit=`b049f9494f9acf163d6b5799f1f6450eaeee36c5`
  next_expected_task=P1.3.
- Required fix: Amend touch_policy P1.3 row to authorize
  `build_public_manifests.py` and `summarize_manifests.py`.
- Rationale: P1.3 requires new manifest build and summary scripts under
  `scripts/robust_asr/**`, but the current touch_policy P1.3 row omits
  those write paths.
- `reports/robust_asr/touch_policy.md` P1.3 row rewritten to authorize:
  `scripts/robust_asr/build_public_manifests.py`,
  `scripts/robust_asr/summarize_manifests.py`,
  `artifacts/robust_asr/manifests/*.parquet`,
  `reports/robust_asr/manifest_summary.md`,
  `reports/robust_asr/task_reports/P1.3_manifest_summary.md`,
  `reports/robust_asr/touch_policy.md` (scope-change row),
  the three live trackers. Reads include `configs/robust_asr/data_v1.yaml`,
  `libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/versions.py`. External reads:
  `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/**` and
  `…/asr_enhancement_training/datasets/**` (read-only ls/stat/open).
- Tracker mutations: `latest_approval_packet` set to the P1.3
  CHANGE_SCOPE packet (prior `APPROVE_EXECUTION(P1.2)` shifted to
  `prior_approval_packet`; older P1.2 packets shifted to
  `prior_approval_packet_0a`/`prior_approval_packet_0b`).
  `artifacts.touch_policy.sha256` →
  `f0ec8dcbf4b3dd09cb76794150745e0f2ec5b6bd701d94c6a623f4dd8b21d4a5`,
  `last_amended_by=P1.3_scope_change`.
  `state_transport.last_accepted_report_commit` STAYS
  `b049f9494f9acf163d6b5799f1f6450eaeee36c5`
  (P1.2 APPROVE_EXECUTION acceptance; CHANGE_SCOPE does not advance).
- Held: `current_task=P1.3`, `last_completed_task=P1.2`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`, `phase_summary.P0=PASS`,
  `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.3 implementation NOT executed: no `build_public_manifests.py`, no
  `summarize_manifests.py`, no parquet manifests, no manifest summary,
  no Slurm, no Apptainer, no GPU, no external API.
- Non-regression: `validate_report_shape.py` against canonical fixtures
  emitted `OK_REPORT_SHAPE`.

## Tracker fix — last_accepted_report_commit advanced 587b7483 -> 8185501

- The P1.2 PASS Execution Report recorded
  `state_transport.last_accepted_report_commit=587b7483…`,
  but `APPROVE_EXECUTION(P1.2-scope-change)` had accepted commit
  `8185501955f5bb5ecf44c926fcabdc8f27ae2af9`, which should have
  advanced the accepted commit at P1.2 commit time.
- Corrected: `state_transport.last_accepted_report_commit` set to
  `8185501955f5bb5ecf44c926fcabdc8f27ae2af9`. No code, no test, no
  task-status change. P1.2 PASS state held.
- Held: `current_task=P1.3`, `last_completed_task=P1.2`,
  `tasks.P1.2.status=PASS`, `markers=[BLOCKED_OOD_PUBLIC]`,
  `blocked=false`, `claims_enabled.ood_real=false`,
  `state_transport.expected_next_task=P1.3`,
  `latest_approval_packet`=APPROVE_PLAN(P1.2) on `8185501…`,
  `prior_approval_packet`=APPROVE_EXECUTION(P1.2-scope-change) on
  `8185501…`.

## P1.2 PASS — eval schema, normalization, metrics, leakage tests

- ORCHESTRATOR_DECISIONs recorded by P1.2:
  - `APPROVE_EXECUTION(P1.2-scope-change)` on
    `accepted_report_commit=8185501955f5bb5ecf44c926fcabdc8f27ae2af9`,
    `next_expected_task=P1.2`. Scope-change rows in
    `configs/robust_asr/reuse_policy_v1.yaml` and the rewritten P1.2
    row in `reports/robust_asr/touch_policy.md` are now binding.
  - `APPROVE_PLAN(P1.2)` on
    `accepted_report_commit=8185501955f5bb5ecf44c926fcabdc8f27ae2af9`,
    `next_expected_task=P1.3`.
- Implementation deliverables (sha256 in tracker yaml `artifacts.*`):
  `libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/metrics.py`, `libs/common/versions.py` (NORMALIZATION_VERSION
  appended; existing constants preserved),
  `scripts/robust_asr/validate_eval_schema.py`,
  `tests/robust_asr/test_eval_schema.py`,
  `tests/robust_asr/test_normalization_metrics.py`,
  `tests/robust_asr/test_leakage.py`,
  `reports/robust_asr/task_reports/P1.2_eval_schema.md`.
- Verifications:
  - `python3 -m pytest -q tests/robust_asr/test_eval_schema.py
    tests/robust_asr/test_normalization_metrics.py
    tests/robust_asr/test_leakage.py` → **41/41 PASS in 0.21 s**.
  - `python3 scripts/robust_asr/validate_eval_schema.py --schema
    libs/common/eval_schema.yaml` → `OK_EVAL_SCHEMA`, exit 0.
  - `python3 scripts/robust_asr/validate_report_shape.py …` →
    `OK_REPORT_SHAPE`, exit 0 (non-regression).
  - `python3 -m pytest -q tests/robust_asr/test_runtime_contract_skeleton.py`
    → **20/20 PASS** (P0.4 non-regression).
- `NORMALIZATION_VERSION = "normalization_v1"` appended to
  `libs/common/versions.py`. Existing `METRICS_VERSION="metrics_v1"`,
  `DEGRADATION_VERSION="degradation_v1"`, `ENHANCER_VERSION=None`
  preserved. New `libs/common/metrics.py` is the canonical robust_asr
  metrics module (distinct from training-profile
  `libs/audio/metrics.py`, which remains unmodified).
- Plan-text inconsistency: Section 3 header reads "Columns (28):" but
  enumerates 31 column names. The 31 names are encoded verbatim in the
  schema YAML; the validator checks set equality with the Section 3
  list, not the header count. Reported as a plan-text inconsistency,
  not a P1.2 deviation.
- Leakage tests 4 and 5 honor `BLOCKED_OOD_PUBLIC` /
  `claims_enabled.ood_real=false`: empty Common Voice / OOD-real /
  demo-reserved splits are treated as trivially disjoint and a
  `SKIP_OOD_PUBLIC_DEFERRED` note is written under
  `reports/robust_asr/leakage/`.
- Tracker mutations: `tasks.P1.2.status=PASS`,
  `current_task=P1.3`, `last_completed_task=P1.2`,
  `markers=[BLOCKED_OOD_PUBLIC]` held, `blocked=false` held,
  `claims_enabled.ood_real=false` held,
  `normalization_version=normalization_v1`,
  `metrics_version=metrics_v1` held,
  `state_transport.last_accepted_report_commit` STAYS `587b7483…`
  (per orchestrator instruction; not advanced to the P1.2 commit),
  `state_transport.expected_next_task=P1.3`,
  `latest_approval_packet`=APPROVE_PLAN(P1.2) on `8185501…`,
  `prior_approval_packet`=APPROVE_EXECUTION(P1.2-scope-change) on
  `8185501…`.

## P1.2 CHANGE_SCOPE recorded

- ORCHESTRATOR_DECISION: scope=scope_change task=P1.2 phase=P1
  decision=CHANGE_SCOPE
  accepted_report_commit=`1ecbaa447e380d5ed3637e80b679bcc83ae77c17`
  next_expected_task=P1.2.
- Rationale: P1.2 requires `libs/common/eval_schema.yaml`,
  `libs/common/normalization.py`, `libs/common/metrics.py`, and
  `libs/common/versions.py` update, but the current reuse_policy only
  allows read-only access under `libs/common/**` except
  `libs/common/runtime_contract.py`.
- Required fix: Authorize P1.2 writes under `libs/common/**` and
  update the stale touch_policy P1.2 row from the old manifests scope
  to eval schema / normalization / metrics / leakage tests.
- `configs/robust_asr/reuse_policy_v1.yaml` amended with four new
  rows under the libs/common/** override block:
  - `libs/common/eval_schema.yaml`: class=robust_asr_owned_extension,
    permitted_use=read_write, allowed_tasks=[P1.2, P9.0],
    validator=`scripts/robust_asr/validate_eval_schema.py`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
  - `libs/common/normalization.py`: class=robust_asr_owned_extension,
    permitted_use=read_write,
    allowed_tasks=[P1.2, P2.1, P3.1, P4.2, P4.3, P5.1, P6.1, P7.3, P8.1, P9.0],
    validator=`tests/robust_asr/test_normalization_metrics.py`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
  - `libs/common/metrics.py`: class=robust_asr_owned_extension,
    permitted_use=read_write,
    allowed_tasks=[P1.2, P2.1, P3.1, P4.1, P4.2, P4.3, P5.1, P6.1, P7.3, P8.1],
    validator=`tests/robust_asr/test_normalization_metrics.py`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
  - `libs/common/versions.py`: class=existing_runtime_code,
    permitted_use=append_constants_only, allowed_tasks=[P1.2],
    validator=`NORMALIZATION_VERSION_constant_present`,
    checksum_required=true, large_artifact=false, commit_allowed=true.
- `reports/robust_asr/touch_policy.md` P1.2 row rewritten to
  authorize the v3.4.7 P1.2 write paths
  (`libs/common/eval_schema.yaml`, `libs/common/normalization.py`,
  `libs/common/metrics.py`, `libs/common/versions.py` (append-only),
  `scripts/robust_asr/validate_eval_schema.py`,
  `tests/robust_asr/test_eval_schema.py`,
  `tests/robust_asr/test_normalization_metrics.py`,
  `tests/robust_asr/test_leakage.py`,
  `reports/robust_asr/task_reports/P1.2_eval_schema.md`, scope-change
  rows on `reuse_policy_v1.yaml`/`touch_policy.md`, the three live
  trackers). Reads include `configs/robust_asr/data_v1.yaml`,
  `libs/audio/metrics.py`, `libs/common/runtime_contract.py`. No Slurm,
  no Apptainer, no GPU, no external API.
- Tracker mutations:
  - `latest_approval_packet` set to the P1.2 CHANGE_SCOPE packet
    (prior P1.1 APPROVE_EXECUTION shifted to `prior_approval_packet`;
    the older P1.1 APPROVE_PLAN shifted to `prior_approval_packet_1b`).
  - `artifacts.reuse_policy_config.sha256` →
    `c2999d597c1e35ecf1340e8dace4e3eaca0640a30fd2d802f1f26a34df853905`,
    `last_amended_by=P1.2_scope_change`.
  - `artifacts.touch_policy.sha256` →
    `f09f4006ff0a6acfd2b296a974bd7ea49ab7e6288a77440a5a06d6e779204c01`,
    `last_amended_by=P1.2_scope_change`.
  - `state_transport.last_accepted_report_commit` STAYS
    `587b7483a6d37a24e0cf31549d449427c4708234`
    (P1.1 APPROVE_EXECUTION acceptance).
  - `state_transport.expected_next_task` STAYS `P1.2`.
- Held: `current_task=P1.2`, `last_completed_task=P1.1`,
  `current_phase=P1`, `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`,
  `claims_enabled.ood_real=false`,
  `phase_summary.P0=PASS`, `orchestrator_approvals.P0=PHASE_APPROVE`.
- P1.2 implementation NOT executed: no `eval_schema.yaml`, no
  `normalization.py`, no `metrics.py`, no `versions.py` mutation, no
  validator script, no tests, no pytest run, no Slurm, no Apptainer,
  no GPU, no external API.
- Non-regression: `python3 scripts/robust_asr/validate_report_shape.py
  --schemas docs/plans/state_packet_schemas_v1.yaml --fixtures
  artifacts/robust_asr/state_packets/report_shape_fixtures` →
  `OK_REPORT_SHAPE`.

## P1.1 APPROVE_EXECUTION recorded

- ORCHESTRATOR_DECISION: scope=task task=P1.1 phase=P1 decision=APPROVE_EXECUTION
  accepted_report_commit=`587b7483a6d37a24e0cf31549d449427c4708234`
  next_expected_task=P1.2.
- Rationale: LibriSpeech inventory usable after operator restore;
  required splits non-empty and speaker-disjoint; OOD-real remains
  unavailable so PARTIAL with `BLOCKED_OOD_PUBLIC` and
  `claims_enabled.ood_real=false` is accepted.
- Tracker: `current_phase=P1`, `current_task=P1.2`,
  `last_completed_task=P1.1`, `markers=[BLOCKED_OOD_PUBLIC]` held,
  `blocked=false` held, `claims_enabled.ood_real=false` held,
  `state_transport.last_accepted_report_commit` advanced
  `3129c11e -> 587b7483`, `state_transport.expected_next_task=P1.2`.
- `tasks.P1.1.next_task` set to `P1.2`. P1.2 not started.

## P0 phase gate

- ORCHESTRATOR_DECISION: scope=phase phase=P0 decision=PHASE_APPROVE
  accepted_report_commit=`d0ba20c532477a94f359b55c03dc6c835529c1fa`
  next_expected_task=P1.1.
- Rationale: P0.0 through P0.5 PASS; required artifacts and sentinels
  present (OK_REPORT_SHAPE, BUILD_OK_8db5364c, OK_APPTAINER_INSPECT,
  OK_RUNTIME_SMOKE, OK_CONTRACT_SKELETON, OK_CARD_TEMPLATES); runtime
  smoke and contract skeleton passed; model/router card placeholder
  counts exceed minima; no blockers or active markers.
- Tracker: `phase_summary.P0=PASS`; `orchestrator_approvals.P0=PHASE_APPROVE`;
  `state_transport.last_accepted_report_commit` advanced
  `40406fc3` → `d0ba20c5`; `state_transport.expected_next_task=P1.1`.
- `current_task=P1.1`, `last_completed_task=P0.5`, `blocked=false`,
  `markers=[]` unchanged.

## Completed tasks

- P0.0 PASS: Pre-bootstrap inventory (read-only, no commit)
- P0.1 PASS: Branch created, profile installed, tracker initialized
- P0.2 PASS: Asset inventory, reuse policy, touch policy, validate_report_shape.py
- P0.3 PASS: Runtime smoke (Slurm + Apptainer + 11 imports). Closed via P0.3-rerun-2 (job 2129641) against new SIF (sha256 8db5364c...) with env-isolated apptainer exec. Sub-tasks: P0.3-rebuild PASS (image build), P0.3-rerun HALTED (user-site shadowing), P0.3-rerun-2 PASS (env-isolation cleared shadowing).
- P0.4 PASS: RP5 runtime contract skeleton — request/response fixtures + `libs/common/runtime_contract.py` schema + `scripts/robust_asr/validate_runtime_contract.py` (19 assertions) + 20 unit tests. Slurm CPU job 2129642 COMPLETED 0:0 in 5 s on aisurrey01 (env-isolated apptainer exec). `OK_CONTRACT_SKELETON` emitted; pytest 20/20 passing. `tracker.artifacts.runtime_contract_fixture.contract_skeleton_validation_passed = true`. P0.4 acceptance commit: `40406fc31ad167500bf8ce317286f5c2b5eeb96f`.
- P0.5 PASS: Model card and router card templates. `docs/reports/robust_asr/model_card_lora.md` (9 sections; 30 `TODO_FILLED_IN_<task_id>` placeholders, ≥ 10 required; sha256 `6f1a6ba8...`) and `docs/reports/robust_asr/router_card.md` (9 sections; 24 placeholders, ≥ 8 required; sha256 `bc5dd87d...`). No scope change, no compute. `validate_report_shape.py` still emits `OK_REPORT_SHAPE`. `current_task` advanced P0.5 → P1.1; `last_completed_task` P0.4 → P0.5. `state_transport.last_accepted_report_commit` advanced `0b47b76e` → `40406fc3` (P0.4 acceptance, per orchestrator instruction; not advanced to the P0.5 commit).

## Scope changes

- P1.1 CHANGE_SCOPE applied: amended `configs/robust_asr/reuse_policy_v1.yaml`
  to (a) add `P1.1` to `allowed_tasks` of the existing `data_root` row
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/**`
  and (b) add a new `data_root` row
  `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/**`
  (`permitted_use=read_only`, `allowed_tasks=[P1.1, P1.2, P1.3, P2.1, P3.1, P4.1, P4.2, P4.3, P8.1]`,
  `validator=none`, `checksum_required=false`, `large_artifact=true`,
  `commit_allowed=false`). `reports/robust_asr/touch_policy.md` P1.1 row
  rewritten to authorize the actual P1.1 write paths
  (`configs/robust_asr/data_v1.yaml`, `reports/robust_asr/data_inventory.md`,
  `reports/robust_asr/task_reports/P1.1_data_inventory.md`,
  `scripts/robust_asr/check_speaker_disjoint.py`, scope-change rows on
  `reuse_policy_v1.yaml`/`touch_policy.md`, the three live trackers) and
  to record the read-only inventory authorization on
  `…/sources/**` and `…/asr_enhancement_training/datasets/**`. Tracker:
  `latest_approval_packet` set to the P1.1 CHANGE_SCOPE packet (prior
  P0 PHASE_APPROVE shifted to `prior_approval_packet`);
  `artifacts.reuse_policy_config.sha256` →
  `16f2b5f682055f6863e5e68a396dded32e6b8346af08efb2243d147b2664f406`,
  `last_amended_by=P1.1_scope_change`;
  `artifacts.touch_policy.sha256` →
  `7a0b85d6257d03d3ca322160c0080d2c6c91f5a90222114d3ad768af324ff16c`,
  `last_amended_by=P1.1_scope_change`. `current_task` stays `P1.1`,
  `last_completed_task` stays `P0.5`, `blocked=false`, `markers=[]`,
  `state_transport.last_accepted_report_commit` stays
  `3129c11edd5105d7c247b48eb1a170d7c1507cde`. P1.1 inventory not
  executed; no Slurm; no Apptainer; no GPU.

- P0.3 CHANGE_SCOPE applied: amended `configs/robust_asr/reuse_policy_v1.yaml`
  to authorize exec-only use of the Apptainer image (class=container_image,
  permitted_use=exec_only) and to make `slurm/jobs/**` writable for
  robust_asr `p<task_id>_*.sh` scripts (permitted_use=read_only_with_robust_asr_writes).
  current_task remains P0.3; last_completed_task remains P0.2.
- P0.3 CHANGE_SCOPE (Option A) applied: added a new robust_asr-specific
  Apptainer image path under `scratch4weeks/.../asr_enhancement_training/runtime/`
  to `configs/robust_asr/reuse_policy_v1.yaml`
  (class=container_image, permitted_use=exec_only, same allowed_tasks
  as `slurm/tools/**`) and a `data_root` parent row
  (`runtime/**`, permitted_use=read_write, allowed_tasks=[P0.3]) for
  the build outputs. The legacy image at `/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif`
  is preserved untouched. `reports/robust_asr/touch_policy.md` extended
  with the P0.3 runtime remediation write paths. current_task remains
  P0.3, last_completed_task remains P0.2, BLOCKED_RUNTIME stays active,
  last_accepted_report_commit stays at 635a711.

## P0.3 first attempt (HALTED)

- Slurm job 2129637 ran in container; exit_code=1.
- Container Python 3.10.13 (must be 3.11) and missing imports
  ctranslate2/faster_whisper/pytest. Lightgbm and xgboost also missing
  (would have triggered ROUTER_IMPL_FALLBACK_SKLEARN, superseded by HALTED).
- Evidence committed at `reports/robust_asr/runtime_smoke.md`,
  `reports/robust_asr/task_reports/P0.3_runtime_smoke.md`,
  `artifacts/robust_asr/runtime_smoke/` (metadata + stdout + stderr).
- Awaiting orchestrator decision: rebuild image (likely a CHANGE_SCOPE
  if the new image lives at a different host path) and rerun P0.3.

## P0.3-rerun sub-task (HALTED — BLOCKED_RUNTIME persists; CHANGE_SCOPE needed)

- Slurm job 2129640 against new image: FAILED 1:0 in 10 s on aisurrey01.
- Container Python 3.11.15 OK; lightgbm OK; ctranslate2/faster_whisper/pytest OK
  (Decision rules 2/3 cleared; previous attempt 1 gaps gone).
- transformers and peft FAIL — shadowed user-site transformers ≥4.50
  needs tokenizers ≥0.22 but only tokenizers 0.21.4 is on the path.
- Root cause: auto-bound `/mnt/fast/nobackup` exposes user-site packages
  that shadow the SIF's correctly-pinned packages. SIF itself is correct
  (build log 2129639: torch 2.5.1+cu121, transformers 4.49.0,
  tokenizers 0.21.4 [compatible w/ 4.49], numpy 1.26.4).
- Fix: add `--env PYTHONNOUSERSITE=1` (+ clear `PYTHONUSERBASE`/`PYTHONPATH`)
  to the apptainer exec in `slurm/jobs/p0_3_runtime_smoke.sh`. CHANGE_SCOPE
  required — the P0.3-rerun plan only authorized a single-line CONTAINER
  repoint.

## P0.3-rebuild sub-task (PASS — BLOCKED_RUNTIME still active)

- Slurm job 2129638 (attempt 1): FAILED 1:0 in 12 min — recipe quoting
  bug (`<X` interpreted as input redirect by dash inside `%post`).
  Fixed by single-quoting every `'>=…,<…'` pip spec in the recipe.
- Slurm job 2129639 (attempt 2): COMPLETED 0:0 in 8 min 39 s via
  `apptainer build --fakeroot` on aisurrey01. Image size 5.24 GB.
  Recipe `%test` block ran `Python 3.11.15` and
  `robust_asr runtime image v1 test PASS`.
- Image at the authorized path:
  `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif`
  sha256 `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713`
  recipe sha256 `e6e7f79bae25e8f6bf3726ab8024a75f4769ad0825eddc15f8b1e50ae377f63e`
- Legacy SIF at `/mnt/.../opro2/pytorch_2.1_cuda12.sif` untouched.
- Tracker: `tasks["P0.3-rebuild"]=PASS`,
  `artifacts.runtime_image_v1` populated,
  `tasks.P0.3.next_task=P0.3-rerun`. **BLOCKED_RUNTIME stays active**;
  `current_task` stays `P0.3`; `last_completed_task` stays `P0.2`;
  `state_transport.last_accepted_report_commit` stays `635a711...`

## P0.4 (PASS)

- Files added: fixtures (`rp5_request_fixture.json`, `rp5_response_fixture.json`),
  schema (`libs/common/runtime_contract.py` — JSON Schema 2020-12 draft +
  pure-stdlib assertion runner), validator
  (`scripts/robust_asr/validate_runtime_contract.py` with `--strict-skeleton`
  and `--strict-final`), tests
  (`tests/robust_asr/test_runtime_contract_skeleton.py` — 20 tests covering
  fixtures-pass + per-assertion mutations A01..A19), and Slurm job
  (`slurm/jobs/p0_4_contract_smoke.sh`).
- Scope-change at commit `22b685a` authorized `libs/common/runtime_contract.py`
  (reuse_policy row, `class=robust_asr_owned_extension`, `commit_allowed=true`,
  `allowed_tasks=[P0.4, P9.0]`) and added the validator/tests/Slurm-job paths
  to the touch_policy P0.4 row.
- Slurm CPU job 2129642 on aisurrey01 (partition 2080ti) COMPLETED 0:0 in 5 s,
  MaxRSS 3872 KiB. Env isolation: `PYTHONNOUSERSITE=1`, cleared
  `PYTHONPATH`/`PYTHONUSERBASE`, `PIP_USER=0`. Container sha256
  `8db5364c...` matches `tracker.artifacts.runtime_image_v1`.
- 19/19 assertions PASS in `--strict-skeleton`; sentinel `OK_CONTRACT_SKELETON`.
- 20/20 unit tests passing in 1.06 s inside the SIF.
- `tracker.artifacts.runtime_contract_fixture.contract_skeleton_validation_passed = true`;
  `contract_final_validation_passed` stays `false` (final validation finalized in P9.0).
- `current_task` advanced from P0.4 → P0.5; `last_completed_task` P0.3 → P0.4;
  `state_transport.last_accepted_report_commit` UNCHANGED at `0b47b76e` per
  orchestrator instruction; `state_transport.expected_next_task` stays
  `P0.4` until orchestrator reviews the P0.4 Execution Report.

## P1.1 (PARTIAL — BLOCKED_OOD_PUBLIC; rerun after operator restore)

- Operator restored LibriSpeech audio at the canonical root via
  `wget` + `tar -xzf` of `train-clean-100.tar.gz` and
  `test-clean.tar.gz` from `https://www.openslr.org/resources/12/`
  (gzip integrity OK; tar exit codes 0). `train-clean-360` not
  restored (P1.1 does not require it).
- Post-restore counts:
  - `train-clean-100`: 251 spk, 28 539 `.flac`, 585 `.trans.txt`,
    ~102.30 h, 6.3 GiB.
  - `dev-clean`: 40 spk, 2 703 `.flac`, 97 `.trans.txt`, 5.388 h,
    349 MiB.
  - `test-clean`: 40 spk, 2 620 `.flac`, 87 `.trans.txt`, ~5.47 h,
    356 MiB.
- Cross-split speaker overlap within LibriSpeech: zero.
- Deterministic split partition (recorded in `data_v1.yaml`):
  `lora_train` = 200 train-clean-100 speakers; `router_train` = 51
  train-clean-100 speakers (every 5th sorted ID); `validation` = 40
  dev-clean speakers; `locked_test` = 40 test-clean speakers.
- OOD-real candidates unchanged: Common Voice EN `clips/` empty with no
  `.tsv` transcripts; TED-LIUM R3 and CHiME-6 absent.
- Decision rule 1 (LibriSpeech missing → HALTED + MISSING_EVIDENCE) is
  cleared. Decision rule 2 / Section 1.1 rule 4 (no OOD-real fallback →
  PARTIAL + BLOCKED_OOD_PUBLIC + `claims_enabled.ood_real=false`) is
  the operative outcome.
- Verifications: `OK_DATA_V1_CONFIG`, `OK_SPEAKER_DISJOINT`
  (non-trivial — 4 non-empty splits), `OK_REPORT_SHAPE`. No Slurm,
  no Apptainer, no GPU, no external API.
- Tracker mutations: `tasks.P1.1.status=PARTIAL`,
  `tasks.P1.1.marker=BLOCKED_OOD_PUBLIC`,
  `markers=[BLOCKED_OOD_PUBLIC]`, `blocked=false`, `blocker=null`,
  `claims_enabled.ood_real=false` (was `true`),
  `current_task=P1.1` (held — orchestrator finalizes via APPROVE_EXECUTION),
  `last_completed_task=P0.5` (held),
  `state_transport.last_accepted_report_commit` STAYS
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the rerun commit per orchestrator instruction.
  Approval-packet chain unchanged from prior P1.1.
- Prior attempt history: `tasks.P1.1.history.attempt_1` records the
  HALTED state at commit `1470ebc1da1a1cc70fdf9965480a070a0c248e4d`.

## P1.1 attempt 1 (HALTED — MISSING_EVIDENCE; cleared by operator restore)

- Inventory of dataset roots completed and recorded in
  `reports/robust_asr/data_inventory.md` and `configs/robust_asr/data_v1.yaml`.
- Findings:
  - LibriSpeech `dev-clean`: 40 speakers, 2703 `.flac`, ~5.388 h, 349 MiB on disk — populated.
  - LibriSpeech `train-clean-100`: 251 speaker dirs, **0 `.flac`**, 0 bytes — skeleton only.
  - LibriSpeech `train-clean-360`: subset directory **absent** on host.
  - LibriSpeech `test-clean`: 40 speaker dirs, **0 `.flac`**, 0 bytes — skeleton only.
  - Common Voice EN cv-corpus-24.0-2025-12-05: `clips/` empty, no `.tsv` transcripts.
  - TED-LIUM Release 3: absent.
  - CHiME-6: absent.
- Decision rule 1 of P1.1 fires: LibriSpeech (partially) missing →
  HALTED + `MISSING_EVIDENCE`. Three of four required split labels
  (`lora_train`, `router_train`, `locked_test`) cannot resolve to
  non-empty file lists.
- Decision rule 2 / Section 1.1 rule 4 (BLOCKED_OOD_PUBLIC) is also
  triggered (no Section 1.1 OOD-real source resolves) but is superseded
  by the LibriSpeech HALT. `data_v1.yaml.ood_real.blocked=true` records
  the OOD-real status; `claims_enabled.ood_real` flag is not flipped at
  this report and awaits orchestrator instruction.
- Verifications: `OK_DATA_V1_CONFIG`, `OK_SPEAKER_DISJOINT` (trivial — 3
  of 4 splits empty), `OK_REPORT_SHAPE`. No Slurm, no Apptainer, no GPU,
  no external API.
- Tracker mutations: `tasks.P1.1.status=HALTED`,
  `markers=[MISSING_EVIDENCE]`, `blocked=true`,
  `current_task=P1.1` (held), `last_completed_task=P0.5` (held),
  `state_transport.last_accepted_report_commit` STAYS
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the P1.1 commit per orchestrator instruction.
  Approval-packet chain on tracker:
  `latest_approval_packet`=APPROVE_PLAN(P1.1) on `e4a5677…` (next P1.2);
  `prior_approval_packet`=APPROVE_EXECUTION(P1.1-scope-change) on
  `e4a5677…` (next P1.1);
  `prior_approval_packet_2`=CHANGE_SCOPE(P1.1) on `3129c11e…` (next P1.1);
  `prior_approval_packet_3`=PHASE_APPROVE(P0) on `d0ba20c5…` (next P1.1).

## Pending

- P0 gate → P1 (schema, manifests, degradations) — blocked at P1.1 by MISSING_EVIDENCE
- P1 → P2 (Whisper base baseline)
- P3 (LoRA smoke, Decision A)
- P4 (Full LoRA if Decision A PASS)
- P5 (AssemblyAI cache or BLOCKED_API)
- P6 (Oracle / selector evidence)
- P7 (Router or deterministic selector)
- P8 (System evaluation)
- P9 (Handoff package)
- P10 (Final reports and audit)
