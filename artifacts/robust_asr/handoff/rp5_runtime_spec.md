# RP5 Runtime Spec (robust_asr handoff)

Project: robust_asr_lora_router
Branch: feature/robust-asr-lora-router-datamove1-v1
Phase: P9.2 — RP5 runtime spec
Produced by: datamove1
Consumed by: RP5 web demo branch
Handoff tag: handoff/20260514-64eba43 (commit 64eba4345f3207af38f0fba8ac2c43c6084e8852, unchanged)

This document is a runtime spec, not a release. It is internal to the
project. The robust_asr tracker
(`docs/progress/robust_asr_progress.yaml`) is the only source of truth
for what the handoff claims; this spec inherits that truth and does
not extend it.

This spec references only artifacts present in
`artifacts/robust_asr/handoff/` together with the final runtime contract
schemas linked from README §4 (`final_request_schema.json` and
`final_response_schema.json` under
`artifacts/robust_asr/runtime_contract/`). It introduces no other
external references.

**Carried-forward constraints (all held; not changed by P9.2):**

- Deployable backend set: `whisper_base_ct2_int8` only.
- Router kind: `deterministic_selector` only.
- LoRA is excluded as a deployed backend
  (`lora_status=SKIPPED_BY_DECISION_A`,
  `claims_enabled.positive_lora=false`).
- AssemblyAI is excluded as an enabled backend
  (`BLOCKED_API` active, `claims_enabled.cloud_tradeoff=false`).
- `claims_enabled.{ood_real, cloud_tradeoff, positive_lora, positive_system}`
  remain `false`.
- Active markers: `BLOCKED_OOD_PUBLIC`, `BLOCKED_API`,
  `OUTCOME_E_DETERMINISTIC_SELECTOR`, `OUTCOME_E_NARROWED_SCOPE`.
- Demo bundle is UI/demo-only and not evidence for any
  `claims_enabled.*` flag (deviation
  `P8_2_demo_only_upstream_overlap` remains `ENACTED`).
- C4 disclosure is recorded in handoff `README.md` §6.4.
- C5 (demo exclusion verification) remains a **P10.1** obligation. P9.2
  does not perform or claim C5 verification.

---

## 1. input contract

The RP5 runtime accepts requests conforming to the final P9.0 request
schema referenced from handoff `README.md` §4:

- `artifacts/robust_asr/runtime_contract/final_request_schema.json`
  (`$id`: `https://robust-asr.local/schemas/rp5_request.final.json`,
  schema dialect: JSON Schema 2020-12)

The input contract fields and constraints follow that schema verbatim
and are restated here as the runtime-facing surface.

### 1.1 Browser audio formats

`audio.encoding` MUST be one of:

- `wav`
- `flac`
- `webm_opus`

No other encodings are accepted. Server-side decoding to PCM is
performed before any selector or backend invocation (see §2 and §3).

### 1.2 Sample-rate and channel requirements

- `audio.sample_rate_hz` MUST equal `16000` (schema `const`).
- `audio.channels` MUST equal `1` (schema `const`).

Multichannel or non-16 kHz audio is rejected at validation time
(§2). Resampling is not performed by the runtime; the browser-side
capture/encoder MUST emit 16 kHz mono before upload.

### 1.3 Duration limits

- `audio.duration_s` MUST be a number with `exclusiveMinimum: 0`.
- The upper bound is enforced server-side from
  `constraints.max_latency_ms` (see §2 and §5); the contract itself
  does not pin a numeric ceiling, and this spec does not invent one.

### 1.4 sha256 expectations

- `audio.sha256` MUST match `^[0-9a-f]{64}$` (64-hex lowercase).
- The runtime SHALL recompute the sha256 of the decoded payload
  bytes and compare against `audio.sha256` (see §2).

### 1.5 request_id and client fields

- `request_id` is a non-empty string. It is echoed verbatim in the
  response (§4).
- `client` is required and includes:
  - `client.browser_user_agent` (string)
  - `client.client_version` (string)

Both `client.*` fields are mandatory; additional client metadata is
permitted by `additionalProperties: true` but is not consumed by the
selector or backend.

### 1.6 constraints.profile and allow_third_party behavior

`constraints` is required and includes:

- `constraints.max_latency_ms` (integer, `exclusiveMinimum: 0`).
- `constraints.allow_third_party` (boolean).
- `constraints.profile` ∈ {`balanced`, `quality_first`, `local_first`}.

`allow_third_party=true` is **not honored as cloud usage** in this
handoff. The deployable runtime treats `allow_third_party=true` as an
unsupported request and maps it to the deterministic_selector
local-first pathway, per the schema's
`x-robust-asr-final-constraint` annotation on
`constraints.allow_third_party` in `final_request_schema.json`. The
runtime records this downgrade in `response.errors`
(`third_party_disabled`; see §6). `BLOCKED_API` remains active;
`claims_enabled.cloud_tradeoff=false`.

`constraints.profile` is forwarded to the selector as
`decode_features` context; it does not change the deployable backend
set, which remains `whisper_base_ct2_int8` only.

---

## 2. server-side validation

All input is validated before any inference. No backend is invoked
until validation succeeds.

1. **JSON Schema 2020-12 validation** of the request body against
   `artifacts/robust_asr/runtime_contract/final_request_schema.json`.
   Required keys: `request_id`, `audio`, `client`, `constraints`. All
   sub-field constraints from §1 are enforced here (encoding enum,
   `sample_rate_hz==16000`, `channels==1`, `duration_s>0`,
   `audio.sha256` 64-hex, non-empty `uri_or_inline`,
   `request_id` non-empty, `client.*` present,
   `max_latency_ms>0`, `profile` enum).

2. **Audio sha256 recomputation.** The runtime decodes
   `audio.uri_or_inline` (URL fetch or inline bytes, depending on the
   transport chosen by the RP5 host), recomputes
   `sha256(decoded_pcm_or_container_payload)` per the convention
   pinned by the host, and compares against `audio.sha256`. Mismatch
   maps to `response.errors` (`audio_sha256_mismatch`; see §6).

3. **Duration and latency-budget check.** The runtime confirms
   `audio.duration_s` is consistent with the decoded PCM length
   (within the rounding tolerance the host chooses; this spec does
   not pin a numeric tolerance because none is present in the
   artifacts). The runtime applies a duration ceiling derived from
   `constraints.max_latency_ms` together with the deployable
   backend's expected real-time factor (the backend config does not
   pin a numeric RTF; this spec does not invent one and the host
   MUST derive the ceiling from observed backend latency rather than
   a hard-coded constant). A request whose duration cannot fit in
   `max_latency_ms` is mapped to `response.errors`
   (`duration_exceeds_budget`; see §6).

4. **Schema failure mapping.** Any of the three failures above
   results in a response whose top-level required fields are filled
   per §4 (with `transcript=null`, `raw_transcript=null`,
   `confidence=null`, `ask_repeat=true`, `selected_backend=null`,
   `router_kind="deterministic_selector"`,
   `latency_ms.{backend,server,end_to_end}` integers ≥ 0,
   `cost_usd=null`, `third_party_provider=null`,
   `report_links.{model_card, router_card}` non-empty,
   `routing_features={}`) and whose `response.errors[*]` contains
   one entry per failure with a category tag from §6. No backend is
   invoked.

5. **No inference before validation succeeds.** Backend execution
   (§3) is entered only after steps 1–3 PASS. There is no partial
   transcription, no streaming preview, and no "best-effort"
   decoding in this handoff.

---

## 3. inference steps

Once validation passes, the runtime computes decode features, routes
through the deterministic selector, and runs at most one local
backend.

### 3.1 Decode features

The runtime decodes the audio (per §2) and computes the two decode
features consumed by the deterministic selector
(`artifacts/robust_asr/handoff/selected_router/deterministic_selector.json`
and the predicate in
`artifacts/robust_asr/handoff/selected_router/rp5_inference.py`):

- `no_speech_prob` (float; default `0.0` if absent).
- `avg_logprob` (float; default `0.0` if absent).

These features are emitted by the local Whisper decoder during the
first decoding pass; the runtime does not require any feature beyond
these two for routing. Additional features (e.g., `snr_db_est`,
`voiced_ratio`, `profile`) are permitted by the response schema's
`routing_features: object` but are advisory only and do not change
the selector branch.

### 3.2 Route using deterministic_selector

The runtime invokes
`artifacts/robust_asr/handoff/selected_router/rp5_inference.py`'s
`predict(decode_features, assemblyai_available=False)`. Constants
are loaded from
`artifacts/robust_asr/handoff/selected_router/deterministic_selector.json`:

- `no_speech_threshold = 0.6`
- `ask_repeat_threshold = -1.0`
- `escalate_threshold = -0.5`
- `health_check_ttl_seconds = 300`

The selector applies the Section 5.5 branches in this priority order:

1. If `no_speech_prob > 0.6` → `action = "ask_repeat"`,
   `reason = "no_speech"`.
2. Else if `avg_logprob < -1.0` → `action = "ask_repeat"`,
   `reason = "low_logprob"`.
3. Else if `assemblyai_available && avg_logprob < -0.5` →
   `action = "assemblyai"`, `reason = "escalate_cloud"`.
   This branch is **unreachable in this handoff** because
   `assemblyai_available` is hardwired to `False` (see §3.3).
4. Else → `action = "whisper_base_ct2_int8"`,
   `reason = "baseline"`.

Confidence is always `1.0` for a deterministic selector
(`selector_kind = "deterministic_selector"`).

### 3.3 Run only whisper_base_ct2_int8

The deployable backend is declared in
`artifacts/robust_asr/handoff/backend_configs/whisper_base_ct2_int8.yaml`:

- `deployable_backends: [whisper_base_ct2_int8]`
- `excluded_backends:`
  - `lora_ct2_int8` — `lora_status=SKIPPED_BY_DECISION_A;
    claims_enabled.positive_lora=false`
  - `assemblyai` — `BLOCKED_API; claims_enabled.cloud_tradeoff=false`
- `router_kind: deterministic_selector`
- `deterministic_selector_version: deterministic_selector_v1`
- `backend_endpoints.whisper_base_ct2_int8`:
  - `backend_kind: local_asr`
  - `local_only: true`
  - `third_party_provider: null`
  - `model_size: base.en`
  - `compute_type: int8`
  - `expected_repo: Systran/faster-whisper-base.en`
  - `candidate_local_paths`: the 5 paths declared in the YAML
  - `halt_if_missing_marker: MISSING_EVIDENCE`

When `action == "whisper_base_ct2_int8"` the runtime loads the model
from the first matching `candidate_local_paths` entry and runs
faster-whisper (int8) on the decoded PCM. Output text becomes
`raw_transcript`; `transcript` is the normalized form per
`libs/common/normalization.py` (consumed transitively through the
host's normalization layer; this spec does not duplicate the
normalization rules).

When `action == "ask_repeat"` the runtime SKIPS backend execution
and returns a response with `ask_repeat=true`,
`selected_backend=null`, `transcript=null`, `raw_transcript=null`,
`confidence=null` (see §4).

When `action == "assemblyai"` (unreachable in this handoff; see
§3.4): the runtime treats it as an unsupported action and falls back
to the local-first pathway (`ask_repeat` with
`response.errors[*] = "third_party_disabled"`; see §6).

### 3.4 assemblyai_available fixed false

The runtime SHALL pass `assemblyai_available=False` to
`predict()`. This is hardwired in this handoff because:

- `BLOCKED_API` marker is active in the active tracker.
- `claims_enabled.cloud_tradeoff = false` in the active tracker.
- The deterministic_selector config
  (`deterministic_selector.json`) lists
  `deployable_actions = ["whisper_base_ct2_int8", "ask_repeat"]`;
  `assemblyai` is **not** in `deployable_actions`. The field
  `assemblyai_action_emitted_when` is `"assemblyai_available==true"`,
  i.e. the cloud action is only emitted under a condition that this
  handoff never satisfies.

The `health_check_ttl_seconds = 300` constant is retained from the
selector constants for forward-compatibility; in this handoff the
runtime MUST NOT probe AssemblyAI health and MUST NOT toggle
`assemblyai_available=True` based on any runtime probe. There is no
AssemblyAI client, no API key consumer, and no Bearer-token
construction in the handoff package.

### 3.5 ACTION_CLOUD / assemblyai as non-deployed dead code

`rp5_inference.py` defines three module-level action constants:

- `ACTION_BASELINE = "whisper_base_ct2_int8"`
- `ACTION_CLOUD = "assemblyai"`
- `ACTION_ASK_REPEAT = "ask_repeat"`

`ACTION_CLOUD` is **dead code in this handoff**. It is retained in
the source to keep the predicate's source-of-truth aligned with
agent plan §5.5, but the runtime never reaches the third branch
(see §3.4) and `assemblyai` is not packaged as a deployable
backend. Any runtime that does reach the third branch (e.g. a
future fork that flips `assemblyai_available=True`) would violate
this handoff's invariants and is out of scope.

### 3.6 No LoRA backend

The handoff package contains no `lora_ct2_int8/` directory, no LoRA
checkpoint, no LoRA tokenizer, no LoRA-specific config, and no LoRA
import in `rp5_inference.py`. LoRA is excluded as a deployed
backend (`lora_status=SKIPPED_BY_DECISION_A`;
`decisions.Decision_B_lora_full.include_lora_in_router=false`;
`claims_enabled.positive_lora=false`). The runtime SHALL NOT load,
merge, or proxy a LoRA adapter.

---

## 4. response shape mapping

Every response conforms to the final P9.0 response schema referenced
from handoff `README.md` §4:

- `artifacts/robust_asr/runtime_contract/final_response_schema.json`
  (`$id`: `https://robust-asr.local/schemas/rp5_response.final.json`)

The required fields are mapped from runtime state as follows:

- `request_id` — echoed verbatim from the request
  (see §1.5).
- `transcript` — normalized transcript string from the local
  backend, or `null` when `ask_repeat=true`.
- `raw_transcript` — pre-normalization decoder text from the local
  backend, or `null` when `ask_repeat=true`.
- `confidence` — number in `[0.0, 1.0]` or `null`; the deterministic
  selector emits `1.0` (selector confidence) but the runtime MAY
  surface the backend's per-token aggregate confidence if available
  (still within `[0.0, 1.0]`); `null` when `ask_repeat=true` or
  when no backend has produced a confidence.
- `ask_repeat` — boolean. `true` whenever the selector branch is
  `no_speech` or `low_logprob`, or when validation in §2 fails, or
  when the host triggers a fallback (backend unavailable, backend
  timeout, `third_party_disabled` downgrade).
- `selected_backend` — `"whisper_base_ct2_int8"` when the backend
  ran; `null` when `ask_repeat=true`. No other value is permitted by
  the schema enum.
- `router_kind` — constant `"deterministic_selector"` (schema enum
  has a single value).
- `routing_features` — object with the decode features consumed by
  the selector (see §3.1). At minimum:
  `{ "no_speech_prob": <float>, "avg_logprob": <float> }`. May
  include advisory fields (e.g. `snr_db_est`, `voiced_ratio`,
  `profile`, `deterministic_selector_version`) for
  diagnostic/telemetry use.
- `latency_ms` — object with integer fields ≥ 0:
  - `backend` — milliseconds spent in the local backend
    (`0` if `ask_repeat=true`).
  - `server` — milliseconds spent on validation + selector +
    response shaping (excludes backend).
  - `end_to_end` — total milliseconds from request receipt to
    response emit; SHOULD satisfy
    `end_to_end ≈ server + backend + transport` (see §5).
- `cost_usd` — `null` for every response in this handoff (no
  third-party billing path; `BLOCKED_API`;
  `claims_enabled.cloud_tradeoff=false`). The schema allows a
  non-negative number for forward-compatibility, but the runtime
  emits `null`.
- `third_party_provider` — `null` for every response (schema
  enforces `type: null`).
- `report_links` — object with two non-empty string fields:
  - `report_links.model_card` — non-empty string pointing at the
    model card (e.g. `docs/reports/robust_asr/model_card_lora.md`;
    the exact string is host-configured but MUST be non-empty per
    validator A19 of `--strict-final`).
  - `report_links.router_card` — non-empty string pointing at the
    router card (e.g. `docs/reports/robust_asr/router_card.md`).
- `errors` — array. Empty `[]` on the happy path; otherwise contains
  one or more entries from §6.

The schema permits `additionalProperties: true` at the top level
and on each sub-object; hosts MAY include extra diagnostic keys but
MUST NOT rename or omit required keys.

---

## 5. latency budgets and deterministic_selector fallback

### 5.1 Budget source

The latency budget is sourced from `request.constraints.max_latency_ms`
(integer milliseconds, `>0`). The runtime SHALL treat this as a soft
end-to-end budget for the response and SHALL NOT exceed it without
falling back to `ask_repeat` and/or emitting a `response.errors`
entry (§6).

This spec does not invent a fixed latency threshold. Specifically:

- No numeric `max_latency_ms` default is declared in the handoff
  package; the host's request transport is the source of truth.
- The backend config does not pin an RTF; the host MAY use a
  running estimate but MUST NOT hard-code a constant in this spec.
- The only numeric constant in the handoff that resembles a
  "timeout" is `health_check_ttl_seconds=300` in the selector
  constants, and it applies to the AssemblyAI health probe, which
  this handoff hardwires off (§3.4) — i.e. it is not a request
  latency budget.

### 5.2 Backend timeout maps to ask_repeat or response.errors

If the local backend exceeds the remaining budget
(`max_latency_ms − server_elapsed_ms − transport_overhead_ms`), the
runtime SHALL:

1. Cancel the backend invocation.
2. Set `selected_backend = null`, `ask_repeat = true`,
   `transcript = null`, `raw_transcript = null`,
   `confidence = null`.
3. Append a `response.errors` entry with the `backend_timeout`
   category (§6).
4. Keep `router_kind = "deterministic_selector"` and
   `third_party_provider = null`.

This pathway corresponds to the Section 5.5 deterministic-selector
fallback: when the deployable backend cannot satisfy the budget, the
selector's `ask_repeat` action is the only legal fallback (no cloud
escalation; see §5.3 and §5.4).

### 5.3 allow_third_party=true is not honored as cloud usage

`constraints.allow_third_party=true` does **not** enable
AssemblyAI in this handoff. The runtime SHALL keep
`assemblyai_available=False` (§3.4) and SHALL append a
`response.errors` entry with the `third_party_disabled` category
(§6). The local deterministic path remains enforced and the response
preserves `third_party_provider=null` and
`selected_backend ∈ {null, "whisper_base_ct2_int8"}`.

### 5.4 BLOCKED_API remains active

`BLOCKED_API` is held in the active tracker for the duration of this
handoff. No code path in the runtime, no future config flip, and no
runtime probe is permitted to clear `BLOCKED_API` from inside the
RP5 runtime. Clearing `BLOCKED_API` is a tracker-level action gated
by an orchestrator decision, not a runtime decision.

`claims_enabled.cloud_tradeoff=false` is held in the active tracker
for the duration of this handoff. The runtime SHALL NOT emit any
response field, telemetry, or log that would support a positive
cloud-tradeoff claim.

---

## 6. failure modes and response.errors mapping

Every failure mode maps to one or more entries in `response.errors`
(an array; the schema is permissive about entry shape but each entry
MUST carry a non-empty `code` or equivalent identifier so the host
can render the failure). The eight categories below are exhaustive
for this handoff; any additional internal failure SHALL be mapped to
the closest category, never silently swallowed.

1. **`schema_validation_failed`** — request body fails JSON Schema
   2020-12 validation against `final_request_schema.json` (see §2.1).
   Response shaping: `ask_repeat=true`, `selected_backend=null`,
   `transcript=null`, `raw_transcript=null`,
   `confidence=null`. No backend invoked.

2. **`audio_sha256_mismatch`** — recomputed sha256 of the decoded
   audio payload does not equal `audio.sha256` (see §2.2).
   Response shaping as above. No backend invoked.

3. **`duration_exceeds_budget`** — `audio.duration_s` cannot fit in
   the host's runtime-estimated budget derived from
   `constraints.max_latency_ms` (see §2.3 and §5.1). Response
   shaping as above. No backend invoked.

4. **`backend_unavailable`** — the deployable backend's model files
   cannot be located via any of the `candidate_local_paths` in
   `backend_configs/whisper_base_ct2_int8.yaml`, or the backend
   import fails. This corresponds to the backend config's
   `halt_if_missing_marker: MISSING_EVIDENCE`. Response shaping:
   `ask_repeat=true`, `selected_backend=null`, etc.

5. **`backend_timeout`** — the local backend exceeded the remaining
   budget (see §5.2). Response shaping as above.

6. **`selector_low_confidence`** — the deterministic selector
   returned `ask_repeat` because `no_speech_prob > 0.6` or
   `avg_logprob < -1.0` (see §3.2). This is **not** an error in the
   strict sense; the host SHOULD render it as an "ask the user to
   repeat" UI affordance. The runtime MAY emit a
   `selector_low_confidence` entry in `response.errors` with the
   selector `reason` (`no_speech` or `low_logprob`) for telemetry,
   but it is not required.

7. **`third_party_disabled`** — `constraints.allow_third_party=true`
   was requested but AssemblyAI is not enabled in this handoff
   (see §1.6 and §5.3). The runtime downgrades to the local-first
   deterministic path. If the local path then yields an `ask_repeat`
   action or fails, a second `response.errors` entry from the
   relevant category above is also emitted.

8. **`report_links_required`** — `report_links.model_card` or
   `report_links.router_card` is missing or empty at response
   shaping time. This is a 500-class internal failure that violates
   validator A19 of `--strict-final` and MUST NOT occur in a
   correctly configured RP5 host. If the runtime detects it, it
   SHALL emit a `report_links_required` entry and fail closed
   (do not return a response that omits or empties these fields).

---

## 7. Backend presence validation (P9.2 obligation)

P9.2 requires that every backend referenced in
`selected_router/rp5_inference.py` is either present in the handoff
package as a deployable backend, or explicitly documented as
non-deployed dead code under this handoff's invariants. The
enumeration and result:

| reference in rp5_inference.py | resolution | handoff artifact |
| :---------------------------- | :--------- | :--------------- |
| `ACTION_BASELINE = "whisper_base_ct2_int8"` | deployable backend; PRESENT | `backend_configs/whisper_base_ct2_int8.yaml` (declared `deployable_backends: [whisper_base_ct2_int8]`); `selected_router/deterministic_selector.json` `deployable_actions` includes `whisper_base_ct2_int8` |
| `ACTION_CLOUD = "assemblyai"` | non-deployed dead code; UNREACHABLE | `selected_router/deterministic_selector.json` `deployable_actions` excludes `assemblyai`; `assemblyai_action_emitted_when = "assemblyai_available==true"` and `assemblyai_available` is hardwired `False` in this handoff (§3.4); `backend_configs/whisper_base_ct2_int8.yaml` `excluded_backends.assemblyai` reason `BLOCKED_API; claims_enabled.cloud_tradeoff=false`; no `backend_configs/assemblyai*.yaml` exists in the package |
| `ACTION_ASK_REPEAT = "ask_repeat"` | control action (not a backend); PRESENT as a deployable action | `selected_router/deterministic_selector.json` `deployable_actions` includes `ask_repeat`; no backend invocation required |

Result: backend presence is **OK** under the agent plan's P9.2
Action 2 requirement. The deployable backend
`whisper_base_ct2_int8` is present in the handoff. The
`ACTION_CLOUD` reference is documented as non-deployed dead code,
matching the selector configuration and the tracker invariants.
There is no LoRA reference in `rp5_inference.py` and no
`lora_ct2_int8/` directory in the handoff package, so the LoRA
exclusion is enforced by absence.

---

## 8. Carry-forward / non-claims

- This spec does not change `claims_enabled.*`. All four flags
  remain `false`.
- This spec does not move, retag, or rewrite the handoff tag
  `handoff/20260514-64eba43`. It still points to commit
  `64eba4345f3207af38f0fba8ac2c43c6084e8852`.
- This spec does not modify handoff `README.md`, the README §2
  sha256 table, the runtime contract schemas, the selected_router
  source artifacts, the smoke or rollback scripts, the validation
  template, the backend config, the demo bundle, or the
  selected_router source under `artifacts/robust_asr/router/`.
- The new artifact `rp5_runtime_spec.md` is intentionally not
  listed in handoff `README.md` §2 to preserve the P9.1 handoff
  tag invariants; this is recorded as a known artifact-set delta
  in the P9.2 execution report.
- This spec does not perform C5 (demo exclusion verification);
  C5 remains a **P10.1** obligation, restated here for the
  RP5-side reader's awareness only.
- No real-provider call. No GPU. No Slurm submission. No
  AssemblyAI client. No LoRA loader.

---

## 9. Cross-references

- `artifacts/robust_asr/handoff/README.md` (P9.1 handoff README,
  8 numbered sections; §6.4 carries the C4 disclosure).
- `artifacts/robust_asr/handoff/selected_router/rp5_inference.py`
  (deterministic selector predicate; the runtime entry point for
  routing).
- `artifacts/robust_asr/handoff/selected_router/deterministic_selector.json`
  (Section 5.5 selector constants, `deployable_actions`,
  `assemblyai_action_emitted_when`).
- `artifacts/robust_asr/handoff/backend_configs/whisper_base_ct2_int8.yaml`
  (the only deployable backend's config; no secrets).
- `artifacts/robust_asr/handoff/handoff_smoke.py` (smoke entry
  point; reads one demo WAV in place, prints `OK_HANDOFF_SMOKE`).
- `artifacts/robust_asr/handoff/rollback_to_previous_handoff.py`
  (rollback to a previous `handoff/<date>-<sha>` tag).
- `artifacts/robust_asr/handoff/handoff_validation_template.md`
  (RP5-side validation template).
- `artifacts/robust_asr/runtime_contract/final_request_schema.json`
  (linked from README §4; the final request schema).
- `artifacts/robust_asr/runtime_contract/final_response_schema.json`
  (linked from README §4; the final response schema).
