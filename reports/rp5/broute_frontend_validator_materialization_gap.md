# BR-04 Frontend Validator Materialization Gap Recovery Report

```yaml
marker: VALIDATOR_MATERIALIZATION_GAP
recovery_packet_id: RP-VALIDATOR-MATERIALIZATION-GAP
phase: B-route
task: BR-04 (blocked until recovery accepted)
generated_at_utc: 2026-05-13T17:30:00
```

## 1. Defect

Two coupled defects in `scripts/rp5/validate_changed_files_against_path_locks.py` (at HEAD 94fb848, post-BR-03 closure) prevent BR-04 implementation:

**Defect A — PL-BR-FRONTEND predicate is incomplete.**
The original predicate only matched paths containing the literal symbol tokens `RouterFieldsPanel`, `UploadForm`, or `ResultView`. None of the existing `services/frontend/app/demo/*` files (e.g. `types.ts`, `page.tsx`) carry those tokens in their paths, so they were never classified under PL-BR-FRONTEND.

**Defect B — PL-BR-API-DEMO predicate bleeds into frontend.**
After the BR-02 Phase A recovery (commit 54c24a4), PL-BR-API-DEMO became `p.startswith("services/") and ("/demo/" in p or ...)`. The `services/` prefix is too broad — it captures `services/frontend/app/demo/*`, contradicting agent_plan.md §1 which assigns `services/frontend/` files exclusively to PL-BR-FRONTEND.

Together these defects make BR-04's required action ("update only files named by that report and path lock PL-BR-FRONTEND") unimplementable: the file BR-04 must modify (`services/frontend/app/demo/types.ts`) is misclassified as PL-BR-API-DEMO and unreachable through PL-BR-FRONTEND.

This satisfies the predicate "VALIDATOR_MATERIALIZATION_GAP predicate is true" from agent §3 row 9. Recovery proceeds per RP-VALIDATOR-MATERIALIZATION-GAP (agent §11) with orchestrator §7/§8 protocol.

## 2. Canonical diagnosis (per RP-VALIDATOR-MATERIALIZATION-GAP)

```
command: python3 scripts/rp5/validate_plan_compiles.py --plan-dir docs/plans/broute --out /tmp/frontend_validator_materialization_gap_canonical_diagnosis.md
sentinel: OK_PLAN_COMPILES
```

Confirms the plan documents are internally consistent. The gap lies in the validator implementation, not in the plan.

## 3. Before-fix classification evidence

```
BEFORE_FIX: services/frontend/app/demo/types.ts -> PL-BR-API-DEMO    (defect: should be PL-BR-FRONTEND)
BEFORE_FIX: services/frontend/app/demo/page.tsx -> PL-BR-API-DEMO    (defect: should be PL-BR-FRONTEND)
BEFORE_FIX: services/api/app/demo_main.py -> PL-BR-API-DEMO          (correct)
BEFORE_FIX: services/frontend/app/layout.tsx -> None                  (correct — outside any B-route lock)
BEFORE_FIX: services/frontend/app/api/[...path]/route.ts -> None      (correct — Next.js proxy, not a demo route)
```

## 4. Exact predicate changes

Only the PL-BR-API-DEMO and PL-BR-FRONTEND predicates were modified.

### 4.1 PL-BR-API-DEMO — narrowed prefix

```python
# Before
"pattern": lambda p: p.startswith("services/") and (
    "demo_main" in p
    or "/demo/" in p
    or "demo/health" in p
    or "demo/upload" in p
    or "demo/results" in p
    or "assemble_demo_response" in p
),

# After
"pattern": lambda p: p.startswith("services/api/") and (
    "demo_main" in p
    or "/demo/" in p
    or "demo/health" in p
    or "demo/upload" in p
    or "demo/results" in p
    or "assemble_demo_response" in p
),
```

Only the prefix was tightened from `services/` to `services/api/`. The disjunction is preserved verbatim. `services/api/app/demo_main.py` still matches (it starts with `services/api/` and contains `demo_main`).

### 4.2 PL-BR-FRONTEND — broadened disjunction

```python
# Before
"pattern": lambda p: (
    p.startswith("services/frontend/") and any(
        sym in p for sym in ["RouterFieldsPanel", "UploadForm", "ResultView"]
    )
),

# After
"pattern": lambda p: p.startswith("services/frontend/") and (
    "/app/demo/" in p
    or "/demo/" in p
    or any(sym in p for sym in ["RouterFieldsPanel", "UploadForm", "ResultView"])
),
```

The `services/frontend/` prefix is preserved. The disjunction adds two substring checks (`"/app/demo/"`, `"/demo/"`) so existing demo frontend files are covered, while still matching any future component file named for the three router-aware symbols. No other lock predicate was touched.

## 5. After-fix classification evidence

```
AFTER_FIX: services/frontend/app/demo/types.ts -> PL-BR-FRONTEND
AFTER_FIX: services/frontend/app/demo/page.tsx -> PL-BR-FRONTEND
AFTER_FIX: services/api/app/demo_main.py -> PL-BR-API-DEMO
AFTER_FIX: services/frontend/app/layout.tsx -> None
AFTER_FIX: services/frontend/app/api/[...path]/route.ts -> None
```

Cross-check that no unrelated lock regressed (independent expected-vs-observed verification):

| Path | Expected lock | Observed lock |
|---|---|---|
| `scripts/rp5/validate_changed_files_against_path_locks.py` | PL-BR-SCRIPTS | PL-BR-SCRIPTS |
| `reports/rp5/broute_frontend_validator_materialization_gap.md` | PL-BR-REPORTS | PL-BR-REPORTS |
| `libs/asr/router_runtime.py` | PL-BR-ASR | PL-BR-ASR |
| `tests/demo/test_demo_api.py` | PL-BR-TESTS | PL-BR-TESTS |
| `docs/progress/rp5_progress.yaml` | PROTOCOL-TRACKER | PROTOCOL-TRACKER |
| `reports/rp5/tracker_missing.md` | PROTOCOL-RP-REPORTS | PROTOCOL-RP-REPORTS |
| `docs/CLAUDE.md` | None | None |

All non-target locks are unchanged.

## 6. Phase A diff is invariant under old and new classifications

The recovery commit contains exactly two files:

| File | Old classification | New classification |
|---|---|---|
| `scripts/rp5/validate_changed_files_against_path_locks.py` | PL-BR-SCRIPTS (matches `scripts/rp5/` prefix) | PL-BR-SCRIPTS (predicate for PL-BR-SCRIPTS untouched) |
| `reports/rp5/broute_frontend_validator_materialization_gap.md` | PL-BR-REPORTS (matches `reports/rp5/` + `broute_*.md`) | PL-BR-REPORTS (predicate for PL-BR-REPORTS untouched) |

Both files classify identically under old and new validator versions. The predicate edits affect only PL-BR-API-DEMO and PL-BR-FRONTEND. Neither file in this Phase A diff is touched by those clauses. The orchestrator's prohibition ("modifying the validator and using it to validate the same diff") is satisfied: the enforcement-rule change has no effect on this commit's classification.

## 7. Recovery sentinel

```
OK_VALIDATOR_MATERIALIZATION_GAP_CLOSED
```

Retry used: 0 (within retry_limit: 1 per RP-VALIDATOR-MATERIALIZATION-GAP).

Next state: BR-04 Phase B implementation becomes path-lock-eligible in a fresh planning cycle after ORCHESTRATOR_DECISION accepts this recovery.
