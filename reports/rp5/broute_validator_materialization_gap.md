# BR-02 Validator Materialization Gap Recovery Report

```yaml
marker: VALIDATOR_MATERIALIZATION_GAP
recovery_packet_id: RP-VALIDATOR-MATERIALIZATION-GAP
phase: B-route
task: BR-02 (blocked until recovery accepted)
generated_at_utc: 2026-05-13T15:45:00
```

## 1. Defect

The path-lock validator at `scripts/rp5/validate_changed_files_against_path_locks.py` (committed in BR-00, commit 5a76594) did not implement PL-BR-API-DEMO consistently with agent_plan.md section 1, which states that PL-BR-API-DEMO covers "demo route, upload route, result route, response assembly" files under `services/`. The file `services/api/app/demo_main.py` is the demo route file — it defines `/demo/health`, `/demo/upload`, `/demo/jobs`, `/demo/run-cached`, `/demo/providers/assemblyai/status`, and `/admin/stats` — yet the existing predicate did not classify it.

This is the predicate `VALIDATOR_MATERIALIZATION_GAP predicate is true` from agent_plan.md section 3 row 9. Because BR-02 actions require modifying `services/api/app/demo_main.py`, BR-02 could not pass path-lock closure without first closing this gap.

## 2. Canonical diagnosis (per RP-VALIDATOR-MATERIALIZATION-GAP)

```
command: python3 scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out /tmp/validator_materialization_gap_canonical_diagnosis.md
sentinel: OK_PLAN_COMPILES
```

The canonical diagnosis confirms that the PLAN documents themselves are internally consistent. The gap is in the validator implementation, not in the plan.

## 3. Concrete before-fix evidence

```
command: python3 -c "import importlib.util; spec = importlib.util.spec_from_file_location('vcp', 'scripts/rp5/validate_changed_files_against_path_locks.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('BEFORE_FIX:', m.classify_file('services/api/app/demo_main.py'))"
observed: BEFORE_FIX: None
```

The original PL-BR-API-DEMO predicate was:

```python
lambda p: (
    any(seg in p for seg in ["/demo/", "demo/health", "demo/upload", "demo/results"])
    and "assemble_demo_response" not in p
    or "assemble_demo_response" in p
) and p.startswith("services/")
```

For `p = "services/api/app/demo_main.py"`:
- `"/demo/" in p` → False (path contains `demo_`, not `/demo/`)
- `"demo/health" in p` → False
- `"demo/upload" in p` → False
- `"demo/results" in p` → False
- `"assemble_demo_response" in p` → False
- result: None

## 4. Fix

Only the PL-BR-API-DEMO predicate was modified. No other lock predicate was changed.

New predicate:

```python
lambda p: p.startswith("services/") and (
    "demo_main" in p
    or "/demo/" in p
    or "demo/health" in p
    or "demo/upload" in p
    or "demo/results" in p
    or "assemble_demo_response" in p
)
```

The change adds `"demo_main" in p` so that `services/api/app/demo_main.py` (the demo route source file) is correctly classified as PL-BR-API-DEMO. The other disjuncts (`/demo/`, `demo/health`, `demo/upload`, `demo/results`, `assemble_demo_response`) are preserved verbatim from the BR-00 validator so any path that classified under the old predicate continues to classify identically.

## 5. Concrete after-fix evidence

```
command: python3 -c "import importlib.util; spec = importlib.util.spec_from_file_location('vcp', 'scripts/rp5/validate_changed_files_against_path_locks.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('AFTER_FIX:', m.classify_file('services/api/app/demo_main.py'))"
observed: AFTER_FIX: PL-BR-API-DEMO
```

Cross-check that no other lock regressed:

| Path | Expected lock | Observed lock |
|---|---|---|
| `scripts/rp5/validate_changed_files_against_path_locks.py` | PL-BR-SCRIPTS | PL-BR-SCRIPTS |
| `reports/rp5/broute_validator_materialization_gap.md` | PL-BR-REPORTS | PL-BR-REPORTS |
| `libs/asr/router_runtime.py` | PL-BR-ASR | PL-BR-ASR |
| `tests/demo/test_demo_api.py` | PL-BR-TESTS | PL-BR-TESTS |
| `docs/progress/rp5_progress.yaml` | PROTOCOL-TRACKER | PROTOCOL-TRACKER |
| `reports/rp5/tracker_missing.md` | PROTOCOL-RP-REPORTS | PROTOCOL-RP-REPORTS |
| `docs/CLAUDE.md` | None | None |

All non-target locks are unchanged.

## 6. File modified

Exactly one file was modified by this recovery commit:

- `scripts/rp5/validate_changed_files_against_path_locks.py` (PL-BR-API-DEMO predicate only)

Plus this report file (`reports/rp5/broute_validator_materialization_gap.md`), created new for the recovery record.

## 7. Phase A diff is invariant under old and new path-lock classification

The recovery commit's diff contains two files:

| File | Old classification | New classification |
|---|---|---|
| `scripts/rp5/validate_changed_files_against_path_locks.py` | PL-BR-SCRIPTS (matches `scripts/rp5/` prefix) | PL-BR-SCRIPTS (unchanged predicate for this lock) |
| `reports/rp5/broute_validator_materialization_gap.md` | PL-BR-REPORTS (matches `reports/rp5/` prefix + `broute_*.md`) | PL-BR-REPORTS (unchanged predicate for this lock) |

Both files classify identically under the old and the new validator versions. The predicate change affects only the PL-BR-API-DEMO disjunct, which is exercised by `services/api/app/demo_main.py`. That file is not in this commit. Therefore the path-lock closure result for this commit is invariant to which validator version runs — the enforcement rule for this diff is not being changed by this diff.

## 8. Recovery sentinel

```
OK_VALIDATOR_MATERIALIZATION_GAP_CLOSED
```

Retry used: 0 (within retry_limit: 1 per RP-VALIDATOR-MATERIALIZATION-GAP).

Next state: BR-02 implementation (Phase B) becomes executable in a fresh planning cycle after this recovery commit is accepted by ORCHESTRATOR_DECISION.
