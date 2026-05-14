# RP5 Handoff Validation — Template

> The RP5 branch copies this template to
> `reports/robust_asr/handoff_validation_<tag>.md` on its side and fills
> in the `TODO_FILLED_IN_RP5` placeholders.
> Datamove1 records `handoff_tag`, this report path, and the verification
> outcome in `docs/progress/robust_asr_progress.yaml` per orchestrator
> plan §1010-1034.

## 1. Tag

- handoff_tag: `TODO_FILLED_IN_RP5`
- handoff_tag_commit: `TODO_FILLED_IN_RP5`
- received_on: `TODO_FILLED_IN_RP5`  (UTC date)

## 2. Package integrity

- README.md 8-section order: `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- artifact SHA-256 match for every row of README Section 2:
  `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- handoff_smoke.py executable: `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- rollback_to_previous_handoff.py executable: `TODO_FILLED_IN_RP5`
  (PASS | FAIL)
- handoff_validation_template.md present in package:
  `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- no_secrets grep (ASSEMBLYAI_API_KEY, sk_, Bearer):
  `TODO_FILLED_IN_RP5`  (PASS | FAIL)

## 3. Runtime contract

- final_request_schema sha256 matches tracker:
  `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- final_response_schema sha256 matches tracker:
  `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- validate_runtime_contract.py --strict-final on the bundled fixtures:
  `TODO_FILLED_IN_RP5`  (OK_CONTRACT_FINAL | FAIL)

## 4. Smoke

- handoff_smoke.py exit code: `TODO_FILLED_IN_RP5`
- handoff_smoke.py stdout sentinel: `TODO_FILLED_IN_RP5`
  (expected OK_HANDOFF_SMOKE)
- selected backend: `TODO_FILLED_IN_RP5`  (expected whisper_base_ct2_int8)
- router_kind: `TODO_FILLED_IN_RP5`  (expected deterministic_selector)

## 5. Disabled-claims acknowledgement

The RP5 branch confirms by signing this row that none of the following
flags are reactivated by this handoff:

- claims_enabled.ood_real: `TODO_FILLED_IN_RP5`  (must remain false)
- claims_enabled.cloud_tradeoff: `TODO_FILLED_IN_RP5`  (must remain false)
- claims_enabled.positive_lora: `TODO_FILLED_IN_RP5`  (must remain false)
- claims_enabled.positive_system: `TODO_FILLED_IN_RP5`  (must remain false)

## 6. Disclosed demo overlap (C4 acknowledgement)

The RP5 branch acknowledges the upstream LibriSpeech dev-clean overlap
declared in README Section 6 and confirms it will NOT use the demo
bundle as evidence for any positive claim.

- acknowledged: `TODO_FILLED_IN_RP5`  (yes | no)
- signed-by: `TODO_FILLED_IN_RP5`

## 7. Final result

- overall: `TODO_FILLED_IN_RP5`  (PASS | FAIL)
- notes: `TODO_FILLED_IN_RP5`
