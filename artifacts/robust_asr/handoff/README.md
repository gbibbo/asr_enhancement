# Robust ASR Handoff Package

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Phase: P9.1 — Handoff package
Produced by: datamove1
Consumed by: RP5 web demo branch

---

## 1. Purpose and scope

This bundle is the datamove1 → RP5 handoff for the robust ASR runtime
contract. It packages the deterministic selector, the deployable backend
config, a smoke script, a rollback script, an RP5-side validation
template, and the README you are reading.

The handoff is internal to the project. **It is not a public release and
it is not evidence for any `claims_enabled.*` flag.** The robust_asr
tracker (`docs/progress/robust_asr_progress.yaml`) is the authoritative
source of truth for what this handoff claims and does not claim.

In scope:

- the runtime contract finalized by P9.0 (request/response schemas);
- the deterministic selector packaged by P7.3;
- the local whisper_base_ct2_int8 backend declaration (no secrets);
- the smoke and rollback scripts;
- the disclosure of the demo bundle's upstream overlap (Section 6).

Out of scope for P9.1:

- C5 exclusion verification — that is a P10.1 obligation, not P9.1;
- LoRA inclusion — `lora_status=SKIPPED_BY_DECISION_A`;
- AssemblyAI inclusion — `BLOCKED_API`;
- training, evaluation, or any positive system claim.

## 2. Artifacts and checksums

| path                                                  | sha256                                                           |
| :---------------------------------------------------- | :--------------------------------------------------------------- |
| `backend_configs/whisper_base_ct2_int8.yaml`          | `011af9618d6e68d2834bfe5d2979ef5d823de00cd33ca4df9a5003c5f1f32951` |
| `handoff_smoke.py`                                    | `cfde7d69601fce86e01ddcf54954752c399513d02bff0c7ef3fcb8cc40e77fa3` |
| `handoff_validation_template.md`                      | `225f251ddd1b5e78c1b5c78bd0a418924529d2d7c85ae671a7ecee3b8bbd6435` |
| `rollback_to_previous_handoff.py`                     | `998b8068c31e9a5923d7892dbdba686781c5d711c0e080e2e7f370c7d0ce8a33` |
| `selected_router/deterministic_selector.json`         | `41d194218b52c13b795d782eb92c381ac3eaa696f56fd217cab43e6a059df3fd` |
| `selected_router/metadata.json`                       | `93dfd0cc2b385d4859cb6c723664fbf1cb4876e27c513590d3f8842d915ff924` |
| `selected_router/rp5_inference.py`                    | `62f0caab558dbd26dd63e9cdf3c931831b527a0ec9f520811d145e7408378427` |
| `selected_router/test_vectors.json`                   | `e57fc83e8e19763389a02e9aa6798e3e70026f7a2c041162fa33a3dec732739d` |

Final runtime contract artifacts (linked from §4; not duplicated in the
handoff directory):

- `artifacts/robust_asr/runtime_contract/final_request_schema.json` —
  `ab7021219b9bd9f341a70e74e59b55a4cd421b1b76b6087bce84d1abeb9e3276`
- `artifacts/robust_asr/runtime_contract/final_response_schema.json` —
  `c0162941182914b9a536b6ab86510fcb608a6e151d6c048a3a7470ed3b069c3d`
- `artifacts/robust_asr/runtime_contract/final_request_fixture.json` —
  `e87b8927bafb377eaddd6043d3f674b9340c6c33150e9f8cbc4a240b0b2dd0eb`
- `artifacts/robust_asr/runtime_contract/final_response_fixture.json` —
  `2a2e35b8f001d8effb1dbad5295d0bac465aad7a94202e819d23b75e6cbd20eb`

## 3. Reproduction commands

```text
# verify the package itself (assertions 1-6 + strict assertion 7)
python3 scripts/robust_asr/verify_handoff_package.py --strict \
  --handoff artifacts/robust_asr/handoff

# smoke the package (loads selector + backend config, transcribes one
# demo audio file read in place; no network)
python3 artifacts/robust_asr/handoff/handoff_smoke.py

# validate the final runtime contract on its fixtures
python3 scripts/robust_asr/validate_runtime_contract.py --strict-final \
  --request artifacts/robust_asr/runtime_contract/final_request_fixture.json \
  --response artifacts/robust_asr/runtime_contract/final_response_fixture.json

# full robust_asr test suite (must remain green)
python3 -m pytest tests/robust_asr/

# rollback to a previous handoff snapshot
python3 artifacts/robust_asr/handoff/rollback_to_previous_handoff.py \
  handoff/<YYYYMMDD>-<short_sha>
```

## 4. Runtime contract

The deployable runtime contract is finalized by P9.0 and lives at:

- request schema:
  `artifacts/robust_asr/runtime_contract/final_request_schema.json`
  ($id `https://robust-asr.local/schemas/rp5_request.final.json`)
- response schema:
  `artifacts/robust_asr/runtime_contract/final_response_schema.json`
  ($id `https://robust-asr.local/schemas/rp5_response.final.json`)
- request fixture:
  `artifacts/robust_asr/runtime_contract/final_request_fixture.json`
- response fixture:
  `artifacts/robust_asr/runtime_contract/final_response_fixture.json`

Contract scope (P9.0):

- **Deployable backend set:** `whisper_base_ct2_int8` only.
- **router_kind:** `deterministic_selector` only.
- **third_party_provider:** `null` in every response.
- **selected_backend:** `null` (when `ask_repeat==true`) or
  `"whisper_base_ct2_int8"`.
- **report_links.model_card** and **report_links.router_card** are
  non-empty strings (validator A19 in `--strict-final`).
- The 19 assertions of `scripts/robust_asr/validate_runtime_contract.py
  --strict-final` all PASS on the bundled fixtures
  (sentinel `OK_CONTRACT_FINAL`, recorded in P9.0 report).

## 5. Smoke and rollback scripts

### handoff_smoke.py

Loads `selected_router/deterministic_selector.json` and
`backend_configs/whisper_base_ct2_int8.yaml`, reads one demo WAV file
in place from `artifacts/robust_asr/demo/audio/`, prints
`OK_HANDOFF_SMOKE` on success, exits 0.

No network access required. No demo WAV bytes are duplicated into the
handoff package. The smoke is **not** evaluation evidence.

```text
python3 artifacts/robust_asr/handoff/handoff_smoke.py
# ...
# OK_HANDOFF_SMOKE
```

### rollback_to_previous_handoff.py

Takes a previous `handoff/<YYYYMMDD>-<short_sha>` tag argument and
restores `artifacts/robust_asr/handoff/` from that tag via
`git checkout <tag> -- artifacts/robust_asr/handoff/`.

```text
python3 artifacts/robust_asr/handoff/rollback_to_previous_handoff.py \
  handoff/20260101-abcd123
# OK_ROLLBACK: artifacts/robust_asr/handoff/ restored from handoff/20260101-abcd123
```

## 6. Risks, limits, disabled claims

### 6.1 Disabled claims

All four `claims_enabled.*` flags are `false` in the active tracker
(`docs/progress/robust_asr_progress.yaml`), and this handoff **does not
support, imply, or enable any of the following claims**:

- `claims_enabled.ood_real`            = `false`
- `claims_enabled.cloud_tradeoff`      = `false`
- `claims_enabled.positive_lora`       = `false`
- `claims_enabled.positive_system`     = `false`

The RP5 branch must not re-enable any of these flags by virtue of
consuming this handoff.

### 6.2 LoRA is not a deployed backend

LoRA is excluded from this handoff. The tracker holds
`lora_status = SKIPPED_BY_DECISION_A` because P3.2 returned
`Decision_A_smoke = FAIL`, which set
`decisions.Decision_B_lora_full.include_lora_in_router = false`.
No LoRA checkpoint, no LoRA config, and no LoRA reference appears in
this handoff. **LoRA is not a deployed backend.**

### 6.3 AssemblyAI is not an enabled backend

AssemblyAI is excluded from this handoff. The marker `BLOCKED_API` is
active and `claims_enabled.cloud_tradeoff = false`. The handoff backend
config contains only `whisper_base_ct2_int8`. **AssemblyAI is not an
enabled backend.** The handoff contains no `ASSEMBLYAI_API_KEY`, no
`sk_*` token, and no `Bearer` credential
(`verify_handoff_package.py` assertion 6).

### 6.4 Demo overlap with upstream LibriSpeech dev-clean (C4 disclosure)

The demo bundle at `artifacts/robust_asr/demo/` is **UI/demo-only**.
Per the enacted deviation
`P8_2_demo_only_upstream_overlap` (status `ENACTED`,
manifest_version `v1.2-deviation-enacted`, manifest SHA-256
`850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba`),
the 8 demo audio files were rendered from LibriSpeech dev-clean
clean-source utterances. **The demo bundle's upstream provenance
overlaps the upstream locked validation set under the normalized
audio_id schema** (13 of 16 locked manifests are affected at the
upstream level).

#### Affected upstream utterances (5)

- `1272-128104-0000`
- `1673-143396-0002`
- `174-168635-0000`
- `1993-147149-0000`
- `2086-149214-0000`

#### Affected upstream speakers (5)

- `1272`
- `1673`
- `174`
- `1993`
- `2086`

#### Explicit non-evidence statement

**The demo bundle is NOT evidence for any `claims_enabled.*` flag.**

Demo artifacts MUST NOT feed:

- any WER/CER/robustness metric;
- any `claims_enabled.*` flag (all four remain `false`);
- the P8.1 system evaluation;
- the P10.1 final verification metrics;
- any backend evaluation parquet (`artifacts/robust_asr/eval_tables/**`);
- `artifacts/robust_asr/router/selector_evidence.parquet`;
- any oracle parquet;
- any `system_eval` input set.

The C5 exclusion verification — proving that demo manifest paths and
demo `audio_id` / `upstream_audio_id` values do not appear in any of
the above artifacts — is a **P10.1 obligation**, not P9.1.

Cross-references:

- `reports/robust_asr/demo/provenance_audit.md` final verdict
  `PASS_WITH_DEMO_ONLY_DEVIATION` with binding constraints C1-C5;
- `reports/robust_asr/task_reports/P8.2_demo_manifest.md`;
- `reports/robust_asr/task_reports/P8_GATE_attempt2.md`.

### 6.5 OOD-real

`BLOCKED_OOD_PUBLIC` remains active. `claims_enabled.ood_real = false`.
This handoff does not support any out-of-distribution real-audio
claim.

### 6.6 System-level positive claim

`OUTCOME_E_DETERMINISTIC_SELECTOR` is active and
`OUTCOME_E_NARROWED_SCOPE` is recorded on `tasks.P8.1` /
`decisions.Decision_D_positive_system`.
`claims_enabled.positive_system = false`. This handoff does not
support any positive system-level claim.

## 7. Provenance

- repository: `https://github.com/gbibbo/asr_enhancement`
- branch: `feature/robust-asr-lora-router-datamove1-v1`
- package commit: recorded in `docs/progress/robust_asr_progress.yaml`
  at `tracker.artifacts.handoff_package.tag_commit` (also visible via
  `git rev-list -n 1 handoff/<YYYYMMDD>-<short_sha>`)
- handoff tag: `handoff/<YYYYMMDD>-<short_sha>` pushed to `origin`
  (assertion 7 of `verify_handoff_package.py --strict`)
- final runtime contract source commit: `f7a195b8828278e42fcc642090cc315309404e07`
  (P9.0 acceptance commit)
- P8 phase approval commit: `0b221c9e213c68636ce0cbf0da75b67baae7d31a`
  (PHASE_APPROVE(P8))
- P0-P8 phase acceptance pattern recorded in
  `docs/progress/robust_asr_progress.md` and
  `docs/progress/robust_asr_state_capsule.md`.

## 8. Contact and license

- **Contact:** Gabriel Bibbó &lt;gabobibbo@gmail.com&gt; (datamove1 owner)
- **License:** see `docs/reports/robust_asr/model_card_lora.md` and
  `docs/reports/robust_asr/router_card.md` (P0.5 templates; final
  license recorded on the model and router cards).
- **RP5-side validation:** see
  `artifacts/robust_asr/handoff/handoff_validation_template.md`. The
  RP5 branch fills the `TODO_FILLED_IN_RP5` placeholders and produces
  `reports/robust_asr/handoff_validation_<tag>.md` per orchestrator
  plan §1010-1034.
