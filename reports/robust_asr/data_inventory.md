# Robust ASR — Data Root Inventory (P1.1, rerun after restore)

Produced by: P1.1 (rerun)
Date: 2026-05-08
Outcome: **PARTIAL** (marker `BLOCKED_OOD_PUBLIC`)

## Executive summary

Operator restored the missing LibriSpeech audio at the canonical root.
The four required robust_asr split labels (`lora_train`, `router_train`,
`validation`, `locked_test`) all resolve to non-empty file lists and are
mutually speaker-disjoint. The LibriSpeech HALT (`MISSING_EVIDENCE`)
recorded in the prior P1.1 report is cleared.

No Section 1.1 OOD-real fallback resolves on host: Common Voice English
has no transcripts and an empty `clips/` directory; TED-LIUM Release 3
and CHiME-6 are absent. Per Section 1.1 rule 4 / P1.1 rule 2, this
yields outcome PARTIAL with marker `BLOCKED_OOD_PUBLIC` and
`claims_enabled.ood_real = false`.

## Per-dataset inventory

### LibriSpeech (restored)

- Root: `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech`
- Version: official 2014 release
- License: https://www.openslr.org/12 (CC BY 4.0)
- Access method: local

| Subset | Speakers | flac files | trans files | Hours | Disk | Status |
|---|---:|---:|---:|---:|---:|---|
| train-clean-100 | 251 | 28 539 | 585 | ~102.30 | 6.3 GiB | **OK (restored)** |
| train-clean-360 | 0 | 0 | 0 | 0.000 | 0 | absent (not restored at this rerun; optional) |
| dev-clean | 40 | 2 703 | 97 | 5.388 | 349 MiB | **OK** |
| test-clean | 40 | 2 620 | 87 | ~5.47 | 356 MiB | **OK (restored)** |

Notes:
- Restoration commands (run by operator before the rerun): `wget`
  + `tar -xzf` of `train-clean-100.tar.gz` and `test-clean.tar.gz` from
  `https://www.openslr.org/resources/12/`. `gzip -t` integrity check
  passed; tar exit codes 0.
- Cross-split speaker overlap (within LibriSpeech): zero. The corpus is
  speaker-disjoint by construction; verified empirically with
  `set(train) & set(dev) = ∅`, `set(train) & set(test) = ∅`,
  `set(dev) & set(test) = ∅`.
- `train-clean-100` hour estimate uses a stride-200 sample of FLAC
  durations through `soundfile.info` (n=143 sampled, mean dur ≈ 12.91 s,
  total ≈ 102.30 h). `dev-clean` hours come exactly from
  `librispeech_manifest_v1.jsonl`. `test-clean` is a similar stride-200
  estimate.
- `train-clean-360` is intentionally not restored at this rerun; P1.1
  done-when does not require it. P3/P4 may request it later if larger
  LoRA scale is needed.

### Common Voice English (cv-corpus-24.0-2025-12-05)

- Root: `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/commonvoice/cv-corpus-24.0-2025-12-05/en`
- Status unchanged from prior P1.1 inventory: `clips/` exists but is
  empty; no `.tsv` transcripts. Section 1.1 approval predicate fails
  on condition (1).

### TED-LIUM Release 3 / CHiME-6

- Both absent on `/mnt/fast/nobackup`. Status unchanged.

## Section 1.1 fallback resolution

1. Common Voice → fails approval predicate (no transcripts).
2. TED-LIUM Release 3 → absent.
3. CHiME-6 → absent.
4. ⇒ Decision rule 4 applies: set `claims_enabled.ood_real = false` and
   record `BLOCKED_OOD_PUBLIC`. With LibriSpeech now resolved, this is
   the operative outcome (no longer superseded by a HALT).

## Split labels and speaker partition

LibriSpeech speaker partitions are **deterministic**. Sort
`train-clean-100` speaker directories by integer ID. Then:
- `router_train` ← every 5th sorted speaker (indices 0, 5, 10, …);
  yields **51** speakers.
- `lora_train` ← the remaining **200** speakers.

The remaining splits use the full official LibriSpeech subsets:
- `validation` ← all 40 dev-clean speakers.
- `locked_test` ← all 40 test-clean speakers.
- `ood_real_locked`, `common_voice_demo_reserved` ← empty (BLOCKED_OOD_PUBLIC).

| Split | Source subset | Speakers | Notes |
|---|---|---:|---|
| lora_train | train-clean-100 | 200 | speaker-disjoint from router_train by construction |
| router_train | train-clean-100 | 51 | speaker-disjoint from lora_train by construction |
| validation | dev-clean | 40 | full dev-clean |
| locked_test | test-clean | 40 | full test-clean (locked; no fitting) |
| ood_real_locked | — | 0 | BLOCKED_OOD_PUBLIC |
| common_voice_demo_reserved | — | 0 | BLOCKED_OOD_PUBLIC |

Total speakers across the four LibriSpeech splits: 331; pairwise
disjoint.

## Speaker-disjoint check

```
$ python3 scripts/robust_asr/check_speaker_disjoint.py \
    --config configs/robust_asr/data_v1.yaml
OK_SPEAKER_DISJOINT

$ python3 scripts/robust_asr/check_speaker_disjoint.py \
    --config configs/robust_asr/data_v1.yaml \
    --splits lora_train router_train validation locked_test
OK_SPEAKER_DISJOINT
```

This non-trivially passes: every pair of the four required splits has a
non-empty speaker set, and intersections are all `∅`.

## Why this is PARTIAL, not PASS or HALTED

Agent plan Section 9 P1.1 done-when:

```
- data_v1.yaml parses.                                          [met]
- At least LibriSpeech is available; all four split labels      [met]
  resolve to non-empty file lists; speaker-disjoint check       [met]
  passes for LibriSpeech splits.
- Either Common Voice resolves OR a Section 1.1 fallback is     [BLOCKED]
  declared OR BLOCKED_OOD_PUBLIC is recorded.
```

Decision rules:
- Decision rule 1 (LibriSpeech missing → HALTED): **does not apply**;
  audio is restored.
- Decision rule 2 (no Section 1.1 OOD-real source resolves → PARTIAL,
  `BLOCKED_OOD_PUBLIC`, `claims_enabled.ood_real=false`): **applies**;
  this is the operative outcome.

## Files produced or refreshed by P1.1 rerun

- `configs/robust_asr/data_v1.yaml` (rewritten with populated splits)
- `reports/robust_asr/data_inventory.md` (this file, rewritten)
- `reports/robust_asr/task_reports/P1.1_data_inventory.md` (rewritten)
- `scripts/robust_asr/check_speaker_disjoint.py` (unchanged from prior)

Tracker mutations:
- `tasks.P1.1.status: PARTIAL`
- `markers: [BLOCKED_OOD_PUBLIC]`
- `claims_enabled.ood_real: false`
- `blocked: false`, `blocker: null`
- `current_task: P1.1` (held — orchestrator finalizes via APPROVE_EXECUTION)
- `last_completed_task: P0.5` (held)
- `state_transport.last_accepted_report_commit`: held at
  `3129c11edd5105d7c247b48eb1a170d7c1507cde`; NOT advanced to the
  rerun commit per orchestrator instruction.

No Slurm. No Apptainer. No GPU. No external API.

## Unblock path for OOD-real (separate from this rerun)

To clear `BLOCKED_OOD_PUBLIC` and re-enable OOD-real claims:

1. Populate Common Voice English clips + `.tsv` transcripts under the
   existing root
   `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/commonvoice/cv-corpus-24.0-2025-12-05/en/`,
   then rerun P1.1.
2. Or stage TED-LIUM R3 / CHiME-6 dev under a new host root (requires a
   CHANGE_SCOPE Approval Packet to add a `data_root` row for the new
   path).
3. Or accept the BLOCKED_OOD_PUBLIC outcome permanently; ID and
   OOD-param work continue without OOD-real claims.
