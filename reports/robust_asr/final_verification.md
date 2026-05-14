# Final Verification — P10.1

PASS

## STATE SNAPSHOT

- project: `robust_asr_lora_router`
- branch: `feature/robust-asr-lora-router-datamove1-v1`
- head_commit_full (pre-exec): `d08dfa821957d4dfa5c3049fc1a60a850d2097ac`
- git_status_short (pre-exec): clean (0 lines)
- current_phase: `P10`
- current_task at entry: `P10.1`
- last_completed_task at entry: `P9_GATE`
- state_transport.expected_next_task at entry: `P10.1`
- state_transport.last_accepted_report_commit at entry: `a3c7d3713809e6d77e4d53e423cc50973b5fa5a4`
- state_transport.latest_approval_packet at entry: `APPROVE_PLAN(P10.1)` recorded this exec with accepted_report_commit `d08dfa821957d4dfa5c3049fc1a60a850d2097ac`
- markers at entry: `[BLOCKED_OOD_PUBLIC, BLOCKED_API, OUTCOME_E_DETERMINISTIC_SELECTOR]`
- claims_enabled at entry: `{ood_real: false, cloud_tradeoff: false, positive_lora: false, positive_system: false}`
- router_status: `SELECTOR_PACKAGED`
- lora_status: `SKIPPED_BY_DECISION_A`
- system_status: `NOT_STARTED`
- proposed_deviations.P8_2_demo_only_upstream_overlap.status: `ENACTED`
- decisions.Decision_D_positive_system.outcome: `false` (held under `OUTCOME_E_NARROWED_SCOPE`)
- canonical handoff tag: `handoff/20260514-64eba43` -> `64eba4345f3207af38f0fba8ac2c43c6084e8852` (local + on `origin`, unchanged this task)
- active profile: `ROBUST_ASR_PROFILE` block in `CLAUDE.md`
- active plans: `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md`, `docs/plans/robust_asr_agent_plan_v3_4_7.md`
- active schemas: `docs/plans/state_packet_schemas_v1.yaml`

## BRANCH SELECTION (Action 3, agent plan §4234–§4243)

- `OUTCOME_E_DETERMINISTIC_SELECTOR` is present in `tracker.markers`.
- `tracker.tasks.P6.2.status` = `SKIPPED_BY_OUTCOME_E` (read from `docs/progress/robust_asr_progress.yaml`).
- Therefore **Branch B (deterministic selector evidence path)** is the active P10.1 verification branch.
- `validate_oracle_table.py` and `validate_router_matrices.py` are not in scope (they do not exist in `scripts/robust_asr/` and Branch A is not active). Recorded explicitly as out-of-scope per the "Exactly one of these branches must be active" rule (§4243).

## PYTEST RESULT (Action 1, §4234)

- Command: `python3 -m pytest tests/robust_asr/`
- Result: **137 passed in 4.59s** across:
  - `test_assemblyai.py` (15)
  - `test_decide_lora_smoke.py` (12)
  - `test_degradation_v1.py` (24)
  - `test_eval_schema.py` (14)
  - `test_leakage.py` (5)
  - `test_lora_smoke.py` (12)
  - `test_normalization_metrics.py` (22)
  - `test_router_runtime.py` (13)
  - `test_runtime_contract_skeleton.py` (20)
- Exit code: `0`.
- Sentinel: `pytest_tests_robust_asr_137_of_137`.

## VALIDATE_EVAL_TABLE RESULTS (Action 2, §4235)

Discovery of every committed parquet under `artifacts/robust_asr/eval_tables/**/*.parquet`:

- `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`
  (sha256 `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6`)

Other deployed-backend parquets are absent by design: LoRA is `SKIPPED_BY_DECISION_A` (no `whisper_lora_*.parquet`); AssemblyAI is `BLOCKED_API` (no `assemblyai*.parquet`).

| Parquet | Command | Sentinel | Result |
|---|---|---|---|
| `whisper_base_ct2_int8.parquet` | `python3 scripts/robust_asr/validate_eval_table.py --input artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` | `OK_EVAL_TABLE` | PASS (rows=53230, unique_pk=53230, unique_audio_id=53230) |

## VALIDATE_SELECTOR_EVIDENCE RESULT (Action 3 Branch B, §4239–§4242)

- `tracker.tasks.P6.2.status == SKIPPED_BY_OUTCOME_E` — **CONFIRMED** by direct read of `docs/progress/robust_asr_progress.yaml`.
- Command: `python3 scripts/robust_asr/validate_selector_evidence.py --input artifacts/robust_asr/router/selector_evidence.parquet`
- Input: `artifacts/robust_asr/router/selector_evidence.parquet` (sha256 `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7`, rows=53230)
- Stdout sentinel: `OK_SELECTOR_EVIDENCE`
- Exit code: `0`
- Built-in disjointness assertion (script lines 147–172) re-confirmed: `demo_overlap = 0`, `lora_overlap = 0`.

## VERIFY_HANDOFF_PACKAGE --strict RESULT (Action 4, §4244)

- Command: `python3 scripts/robust_asr/verify_handoff_package.py --strict --handoff artifacts/robust_asr/handoff`
- Per-assertion result:
  - A1 PASS: 8 numbered README sections present in order
  - A2 PASS: 8 artifact(s) verified with matching SHA-256
  - A3 PASS: `handoff_smoke.py` is executable (mode=0o755)
  - A4 PASS: `rollback_to_previous_handoff.py` is executable (mode=0o755)
  - A5 PASS: `handoff_validation_template.md` present
  - A6 PASS: no `ASSEMBLYAI_API_KEY` / `sk_` / `Bearer` in `backend_configs/`
  - A7 PASS: canonical tag exists locally and on origin: `handoff/20260514-64eba43` -> `64eba4345f3207af38f0fba8ac2c43c6084e8852` (source=git_tag_list)
- Stdout sentinel: `OK_HANDOFF_PACKAGE`
- Exit code: `0`

## VALIDATE_RUNTIME_CONTRACT --strict-final RESULT (defense-in-depth, optional under P10.1)

Run as a defense-in-depth check against drift between P9 PASS and P10.1 entry. Not mandated by P10.1 Actions §4234–§4249, but recorded for completeness.

- Command: `python3 scripts/robust_asr/validate_runtime_contract.py --strict-final --request artifacts/robust_asr/runtime_contract/final_request_fixture.json --response artifacts/robust_asr/runtime_contract/final_response_fixture.json`
- All 19 assertions PASS (A01–A19): request/response IDs match; audio encoding `wav`, sample_rate `16000`, channels `1`, duration `4.0s`; constraints `local_first`, `allow_third_party=False`, `max_latency_ms=2000`; response `ask_repeat=False`, transcript present, no errors; `selected_backend='whisper_base_ct2_int8'`, `router_kind='deterministic_selector'`, `cost_usd=0.0`, `third_party_provider=None`; latencies recorded; confidence `0.88`; model/router card paths resolved.
- Stdout sentinel: `OK_CONTRACT_FINAL`
- Exit code: `0`

## CLAIMS RECONCILIATION (Actions 5 and 6, §4245–§4247)

Read from `docs/progress/robust_asr_progress.yaml` lines 32–36:

| Flag | Value | Type | Status |
|---|---|---|---|
| `claims_enabled.ood_real` | `false` | boolean (not `pending`) | PASS |
| `claims_enabled.cloud_tradeoff` | `false` | boolean (not `pending`) | PASS |
| `claims_enabled.positive_lora` | `false` | boolean (not `pending`) | PASS |
| `claims_enabled.positive_system` | `false` | boolean (not `pending`) | PASS |

All four flags are explicit booleans, satisfying Action 5.

### No-claim-depends-on-disabled-flag cross-walk (Action 6)

Handoff README §6 disabled-claims language (`artifacts/robust_asr/handoff/README.md`):

- §6.1 Disabled claims: lists all four flags as `false`; states "this handoff does not support, imply, or enable any of the following claims".
- §6.2 LoRA is not a deployed backend (consistent with `claims_enabled.positive_lora=false`, `lora_status=SKIPPED_BY_DECISION_A`).
- §6.3 AssemblyAI is not an enabled backend (consistent with `claims_enabled.cloud_tradeoff=false`, `BLOCKED_API`).
- §6.4 Demo overlap with upstream LibriSpeech dev-clean (C4 disclosure): explicitly states "The demo bundle is NOT evidence for any `claims_enabled.*` flag."
- §6.5 OOD-real (consistent with `claims_enabled.ood_real=false`, `BLOCKED_OOD_PUBLIC`).
- §6.6 System-level positive claim (consistent with `claims_enabled.positive_system=false`, `OUTCOME_E_NARROWED_SCOPE` on `Decision_D_positive_system`).

`reports/robust_asr/system/system_eval.md` line 5: "No claim made here depends on a disabled `claims_enabled` flag."

**Result: no claim in any in-scope report depends on a disabled `claims_enabled` flag.**

## C5 EXCLUSION VERIFICATION

Per the enacted deviation `P8_2_demo_only_upstream_overlap` (`artifacts/robust_asr/demo/demo_examples_manifest.json` §C5, lines 297–298): "P10.1 final verification MUST assert demo manifest paths and audio_id/upstream_audio_id values do not appear in any `artifacts/robust_asr/eval_tables/**.parquet`, in `selector_evidence.parquet`, in `oracle/**.parquet`, or in any `system_eval` input set."

Handoff README §6.4 (C4 disclosure) reiterates that C5 enforcement is a P10.1 obligation.

### Demo identifiers checked

Source: `artifacts/robust_asr/demo/demo_examples_manifest.json` (manifest_version `v1.2-deviation-enacted`, manifest sha256 `850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba`, `n_examples=8`).

- `demo_audio_id` (n=8):
  - `demo/ex001/clean`
  - `demo/ex003/cafe_background`
  - `demo/ex004/phone_call`
  - `demo/ex007/far_field_room`
  - `demo/ex010/muffled`
  - `demo/ex001/broadband_hiss`
  - `demo/ex003/broadband_hiss`
  - `demo/ex004/broadband_hiss`
- `demo_upstream_audio_id` (n=5):
  - `librispeech/dev-clean/1272/128104/1272-128104-0000`
  - `librispeech/dev-clean/1673/143396/1673-143396-0002`
  - `librispeech/dev-clean/174/168635/174-168635-0000`
  - `librispeech/dev-clean/1993/147149/1993-147149-0000`
  - `librispeech/dev-clean/2086/149214/2086-149214-0000`
- `demo_audio_sha256` (n=8):
  - `799f78ed4beb4de7ceae3a809262d4ce242394342ccd1d58cef7d49dbc2def46`
  - `05cd65e8496ae70569d9f246379d998010192b5052b7d22a4bee4d5447daa961`
  - `678efe82dd10946d899f4e833a567b21d3a1a219fd3cc5c6d508d8c6608e2d2e`
  - `4721085b74ca6422db61746bfad86795a6c84751bf7e66e118712c5a2e41c996`
  - `68d9a1c41254bd8fbc6c5be2339c89c21a94bf71e8ff6c91d8d600b6a3a7eedb`
  - `490de44d785167be8a46279fb526a47a75e987ab9d451cdd8480d10ddca79e45`
  - `5ae95b34541fbe9afb7411352bbf46ecee2273ef9825a4ef72cec603a5bb7d6a`
  - `16b5316119181a43a2060de4119c83c03d476e1fe1fd1a864e31584b0a6d07bf`
- `demo_path_substr`: `artifacts/robust_asr/demo/`

### Parquet scopes checked

1. **Eval tables**: `artifacts/robust_asr/eval_tables/**/*.parquet`
   - `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` (rows=53230).
2. **Selector evidence**: `artifacts/robust_asr/router/selector_evidence.parquet` (rows=53230).
3. **Oracle parquets**: `artifacts/robust_asr/oracle/**/*.parquet` — **none present** (consistent with Branch B / `OUTCOME_E_DETERMINISTIC_SELECTOR`; P6.2 `SKIPPED_BY_OUTCOME_E`). C5 oracle check is N/A by construction.
4. **System_eval input set**: per `reports/robust_asr/system/system_eval.md` §10–§12, the only inputs are the two parquets above; the eval/selector C5 results cover system_eval entirely.

### Per-parquet results

#### `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet`

- rows: 53230
- columns: `audio_id`, `source_dataset`, `source_split`, `speaker_id`, `utterance_id`, `condition_family`, `degradation_id`, `degradation_params_json`, `audio_path_or_uri`, `audio_sha256`, `reference_text`, `reference_normalized`, `backend_name`, `backend_version`, `backend_kind`, `decode_config_json`, `raw_transcript`, `normalized_transcript`, `normalization_version`, `wer`, `cer`, `wa`, `backend_latency_ms`, `server_processing_latency_ms`, `end_to_end_latency_ms`, `ram_peak_mb`, `cost_usd`, `local_only`, `third_party_provider`, `error_or_null`, `created_at_utc`
- `audio_id` ∩ `demo_audio_id` = ∅ (count=0)
- `upstream_audio_id` column absent → vacuous PASS for that identifier
- `audio_sha256` ∩ `demo_audio_sha256` = ∅ (count=0)
- path columns inspected: `[audio_path_or_uri]`; rows containing `"artifacts/robust_asr/demo/"` = 0
- PASS

#### `artifacts/robust_asr/router/selector_evidence.parquet`

- rows: 53230
- columns: `audio_id`, `reference_normalized`, `whisper_base_ct2_int8_wer`, `whisper_base_ct2_int8_latency_ms`, `whisper_base_ct2_int8_wa`, `selected_action`, `selector_reason`, `ask_repeat_allowed`, `assemblyai_available`, `lora_available`, `no_speech_prob_proxy`, `avg_logprob_proxy`, `condition_family`, `degradation_id`, `source_split`, `deterministic_selector_version`, `normalization_version`
- `audio_id` ∩ `demo_audio_id` = ∅ (count=0)
- `upstream_audio_id` column absent → vacuous PASS
- `audio_sha256` column absent → vacuous PASS
- path columns absent → vacuous PASS
- PASS (also re-confirmed by the built-in `_load_demo_ids` disjointness assertion in `validate_selector_evidence.py`)

#### Oracle (`artifacts/robust_asr/oracle/**/*.parquet`)

- No parquets present (only `deterministic_selector.json`, `metadata.json`, `rp5_inference.py`, `test_vectors.json`, `system_eval.md`).
- N/A — Branch B path.

#### `system_eval` input set

- All inputs already covered by the eval-table and selector-evidence checks above.

### Overall C5 verdict

**`C5_EXCLUSION_PASS`** — all intersections empty across every in-scope parquet; no demo path appears in any path-typed column; the oracle scope is N/A by construction; the system_eval input set is fully covered.

## ARTIFACT POINTERS

| Artifact | Path | SHA-256 |
|---|---|---|
| Demo manifest | `artifacts/robust_asr/demo/demo_examples_manifest.json` | `850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba` |
| Eval parquet (whisper_base_ct2_int8) | `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` | `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6` |
| Selector evidence | `artifacts/robust_asr/router/selector_evidence.parquet` | `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7` |
| Handoff README | `artifacts/robust_asr/handoff/README.md` | `36f3c610571402851213bc0c7eb73384512caf2f24c3ed3a4c9a179160cf3b18` |
| Runtime contract final request fixture | `artifacts/robust_asr/runtime_contract/final_request_fixture.json` | `e87b8927bafb377eaddd6043d3f674b9340c6c33150e9f8cbc4a240b0b2dd0eb` |
| Runtime contract final response fixture | `artifacts/robust_asr/runtime_contract/final_response_fixture.json` | `2a2e35b8f001d8effb1dbad5295d0bac465aad7a94202e819d23b75e6cbd20eb` |
| System eval report | `reports/robust_asr/system/system_eval.md` | `4bdf8f670749537320c55b54c7bc17767d40891cb70693917ec2d3f349fe93ff` |
| Canonical handoff tag | `handoff/20260514-64eba43` | `64eba4345f3207af38f0fba8ac2c43c6084e8852` (local + on `origin`) |

## OVERALL VERDICT

**P10.1 = PASS**

All required Actions §4234–§4249 are satisfied under Branch B:

- Action 1 (`pytest tests/robust_asr/`): PASS (137/137).
- Action 2 (`validate_eval_table.py` on every committed eval parquet): PASS (`OK_EVAL_TABLE` on `whisper_base_ct2_int8.parquet`; the only committed parquet).
- Action 3 Branch B (`validate_selector_evidence.py` + tracker `tasks.P6.2.status == SKIPPED_BY_OUTCOME_E`): PASS (`OK_SELECTOR_EVIDENCE` + confirmed).
- Action 4 (`verify_handoff_package.py --strict`): PASS (`OK_HANDOFF_PACKAGE`, A1–A7 PASS).
- Action 5 (`claims_enabled.positive_lora` and `.positive_system` boolean, not `pending`): PASS (both `false`).
- Action 6 (no claim depends on a disabled `claims_enabled` flag): PASS (handoff README §6.1–§6.6 and `system_eval.md` line 5 cross-walked).
- Action 7 (write this report): satisfied by this file.

C5 exclusion verification (deviation `P8_2_demo_only_upstream_overlap` binding constraint): **PASS**.

Defense-in-depth runtime contract check: PASS (`OK_CONTRACT_FINAL`).

No markers cleared. No `claims_enabled.*` flag flipped. No forbidden path modified. The canonical handoff tag `handoff/20260514-64eba43` is unchanged. P10.2 is not started; awaits orchestrator `APPROVE_EXECUTION(P10.1)`.

## NEXT LEGAL ACTION

Return the Execution Report. Stop. Do not start P10.2. Await orchestrator `APPROVE_EXECUTION(P10.1)` (or `FIX_BEFORE_CLOSE` / `SUPPLEMENTAL_EVIDENCE`).
