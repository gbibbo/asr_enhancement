# Runtime Contract Smoke (P0.4 skeleton)

Produced by: P0.4
Date: 2026-05-08
Mode: `--strict-skeleton`
Outcome: **PASS** (`OK_CONTRACT_SKELETON`)

## Job

| field | value |
|---|---|
| Slurm job_id | 2129642 |
| Job name | `robust_asr_p0_4_contract_smoke` |
| Partition | 2080ti |
| Host | aisurrey01.surrey.ac.uk |
| State | COMPLETED |
| Exit code | 0:0 |
| Elapsed | 00:00:05 |
| MaxRSS | 3872 KiB |
| Submitted (UTC) | 2026-05-08T03:51:31Z |
| Started (UTC) | 2026-05-08T03:51:31Z |
| Completed (UTC) | 2026-05-08T03:51:36Z |
| Container | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif` |
| Container sha256 | `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713` |
| Env isolation | `PYTHONNOUSERSITE=1`, `PYTHONPATH=`, `PYTHONUSERBASE=`, `PIP_USER=0` |

## Fixtures

- `artifacts/robust_asr/runtime_contract/rp5_request_fixture.json`
- `artifacts/robust_asr/runtime_contract/rp5_response_fixture.json`

## Validator

- Script: `scripts/robust_asr/validate_runtime_contract.py`
- Schema module: `libs/common/runtime_contract.py`
- Mode: `--strict-skeleton`
- Sentinel emitted: `OK_CONTRACT_SKELETON`
- Validator exit code: 0

## 19 assertions

| id | result | summary |
|---|---|---|
| A01 | PASS | Both JSON files parsed |
| A02 | PASS | request_id non-empty and matches across request/response (`11111111-1111-4111-8111-111111111111`) |
| A03 | PASS | `audio.encoding='wav'` ∈ {wav,flac,webm_opus} |
| A04 | PASS | `audio.sample_rate_hz=16000` |
| A05 | PASS | `audio.channels=1` |
| A06 | PASS | `audio.duration_s=3.5` > 0 |
| A07 | PASS | `audio.sha256` is 64 lowercase hex chars |
| A08 | PASS | `constraints.profile='balanced'` ∈ {balanced,quality_first,local_first} |
| A09 | PASS | `constraints.allow_third_party=False` is bool |
| A10 | PASS | `constraints.max_latency_ms=1500` is positive int |
| A11 | PASS | `response.ask_repeat=False` is bool |
| A12 | PASS | (transcript is null) iff (ask_repeat=true OR errors non-empty) — both sides False |
| A13 | PASS | selected_backend null iff ask_repeat=true — both sides False |
| A14 | PASS | `router_kind='deterministic_selector'` ∈ {ml_router,deterministic_selector} |
| A15 | PASS | `cost_usd=0.0` ≥ 0.0 |
| A16 | PASS | selected_backend != 'assemblyai'; third_party_provider=null is acceptable |
| A17 | PASS | latency_ms backend=240 ≤ server=280 ≤ end_to_end=320 |
| A18 | PASS | `confidence=0.92` ∈ [0.0, 1.0] |
| A19 | PASS | report_links.{model_card,router_card} are strings (skeleton: empty allowed) |

Total: 19/19 PASS.

## Unit tests

Inside the SIF, `python3 -m pytest -q tests/robust_asr/test_runtime_contract_skeleton.py`:
- 20 tests passed in 1.06s.
- Coverage: skeleton-fixtures-pass (1), per-assertion-mutation A02..A19 (18), A01 malformed-request (1).

## Reproducer

```
./slurm/tools/on_submit.sh sbatch \
  /mnt/fast/nobackup/users/gb0048/asr_enhancement/slurm/jobs/p0_4_contract_smoke.sh
```

Or, from inside the SIF directly:

```
apptainer exec \
  --env PYTHONNOUSERSITE=1 --env PYTHONPATH= --env PYTHONUSERBASE= --env PIP_USER=0 \
  /mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif \
  python3 scripts/robust_asr/validate_runtime_contract.py \
    --strict-skeleton \
    --request artifacts/robust_asr/runtime_contract/rp5_request_fixture.json \
    --response artifacts/robust_asr/runtime_contract/rp5_response_fixture.json
```

Expected last line of stdout: `OK_CONTRACT_SKELETON`. Exit code 0.
