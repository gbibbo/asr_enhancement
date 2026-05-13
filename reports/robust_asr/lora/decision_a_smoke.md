# Decision A — LoRA Smoke

## Outcome

**Decision_A_smoke = FAIL** (mechanical per agent plan §5.1).

Sentinel: `OK_LORA_SMOKE_DECISION:FAIL`.

## Inputs

- Evaluate input: `reports/robust_asr/lora/lora_smoke_result.json`
  (produced by P3.1, Slurm job 2131980).
- Export input: `artifacts/robust_asr/lora_smoke/export_smoke_result.json`
  (`outcome=PASS`; merge_lora_fp16 → ct2_int8_export → faster_whisper_transcribe
  all OK).

## Metrics

| metric | value | threshold | satisfied |
|---|---:|---:|:---:|
| `macro_wa_gain` | -0.12843 | ≥ 0.005 | NO |
| `max_family_wa_gain` | -0.11345 | ≥ 0.010 | NO |
| `clean_wa_regression` | 0.11345 | ≤ 0.010 (PASS) / ≤ 0.020 (PARTIAL) | NO / NO |
| `per_family_wa_gain_variance` | 1.79e-4 | non-degenerate guard (≠ 0) | non-degenerate |
| `export_smoke_result.outcome` | PASS | not EXPORT_BLOCKED | not HALTED |

Per-family WA gain (LoRA − baseline):

- clean: -0.11345
- cafe_noise: -0.14546
- phone_band: -0.12132
- far_field_room: -0.14358
- muffled_lowpass: -0.11834

## Section 5.1 evaluation

```
SMOKE_PASS    = (macro_wa_gain >= 0.005 AND clean_regression <= 0.010)        -> false
                OR (max_family_wa_gain >= 0.010 AND clean_regression <= 0.010) -> false
SMOKE_PARTIAL = NOT SMOKE_PASS AND max_family_wa_gain >= 0.010 AND clean_regression <= 0.020
              -> false (max_family_wa_gain = -0.11345 < 0.010)
SMOKE_FAIL    -> TRUE
```

Booleans:

- `macro_wa_gain (-0.12843) < smoke_global_wa_gain_min (0.005)` → not PASS branch A.
- `max_family_wa_gain (-0.11345) < smoke_family_wa_gain_min (0.010)` → not PASS
  branch B, not PARTIAL.
- `clean_wa_regression (0.11345) > smoke_clean_regression_max_pass (0.010)` and
  `> smoke_clean_regression_max_partial (0.020)`.
- `per_family_wa_gain_variance = 1.79e-4 ≠ 0` → degenerate guard does NOT fire;
  the FAIL is on the smoke booleans themselves, not the degenerate path.
- `export_smoke_result.outcome = PASS` → no EXPORT_BLOCKED; not HALTED.

Result: **SMOKE_FAIL**.

## Expected P3 gate side effects (Section 0.1 / Section 5.10)

These mutations are enacted at the P3 gate (`PHASE_APPROVE(P3)`), not by
P3.2 itself:

- Routing: P4.1, P4.2, P4.3 → `SKIPPED_BY_DECISION_A`.
- `lora_status` → `SKIPPED_BY_DECISION_A` (transition owned by P3 gate; held at
  `SMOKE_DONE` at P3.2).
- `decisions.Decision_B_lora_full.include_lora_in_router = false`.
- `claims_enabled.positive_lora = false` (was `pending`).
- Next post-gate task: **P5.1** (AssemblyAI cloud eval).

## P3.2 tracker side effects (recorded by this commit)

- `tasks.P3.2.status = PASS`.
- `tasks.P3.2.sentinels = [OK_LORA_SMOKE_DECISION:FAIL]`.
- `decisions.Decision_A_smoke.outcome = FAIL`.
- `decisions.Decision_A_smoke.decided_at_task = P3.2`.
- `current_task = P3.2` held until `APPROVE_EXECUTION(P3.2)`.
- `last_completed_task = P3.1` held.
- `markers = [BLOCKED_OOD_PUBLIC]` held non-blocking.
- `lora_status = SMOKE_DONE` held (P3.2 does not transition this; the P3 gate does).
- `state_transport.last_accepted_report_commit = 096fe43...` stays.
- `state_transport.expected_next_task = P3_GATE`.

No P4 statuses or `claims_enabled.positive_lora` are written by P3.2 — the
orchestrator enacts those at the P3 gate.

## References

- Agent plan §3601–§3637 (P3.2 task spec).
- Agent plan §5.1 (smoke gate thresholds and booleans).
- Agent plan §1270–§1284 (decide_lora_smoke.py contract).
- Section 0.1 transition table (P3.2 Decision A FAIL → P5.1 after P3 gate).
- `reports/robust_asr/lora/lora_smoke_report.md` (first-line outcome: `FAIL`).
