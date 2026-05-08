# Robust ASR — Data Root Inventory (P1.1)

Produced by: P1.1
Date: 2026-05-08
Outcome: **HALTED** (marker `MISSING_EVIDENCE`)

## Executive summary

P1.1 inventoried the four planned dataset roots on the host
(`datamove1.surrey.ac.uk` view of `/mnt/fast/nobackup`). Only
LibriSpeech `dev-clean` is populated. The other three required
LibriSpeech subsets (`train-clean-100`, `train-clean-360`, `test-clean`)
have no audio files. No Section 1.1 OOD-real fallback (Common Voice
English, TED-LIUM Release 3, CHiME-6) is present and resolvable.

Per Decision rule 1 of agent plan Section 9 P1.1, this triggers
status = HALTED, marker = MISSING_EVIDENCE. Decision rule 2
(BLOCKED_OOD_PUBLIC) also applies in principle but is superseded by the
LibriSpeech HALT.

## Per-dataset inventory

### LibriSpeech

- Root: `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech/LibriSpeech`
- Version: official 2014 release (BOOKS.TXT, CHAPTERS.TXT, LICENSE.TXT,
  README.TXT, SPEAKERS.TXT present at root)
- License: https://www.openslr.org/12 (CC BY 4.0)
- Access method: local
- Speakers in SPEAKERS.TXT: 2484 (across all official subsets, not all
  on disk)
- Subsets present at the root level: `train-clean-100`, `dev-clean`,
  `test-clean` (directory entries); `train-clean-360` is absent.

| Subset | Speaker dirs | flac files | Hours (dur from manifest) | Status |
|---|---:|---:|---:|---|
| train-clean-100 | 251 | 0 | 0.000 | **MISSING AUDIO** — chapter dirs exist but contain no `.flac` |
| train-clean-360 | 0 | 0 | 0.000 | **ABSENT** — subset directory not present on host |
| dev-clean | 40 | 2703 | 5.388 | **OK** — fully populated |
| test-clean | 40 | 0 | 0.000 | **MISSING AUDIO** — chapter dirs exist but contain no `.flac` |

Notes:
- `dev-clean` total disk usage: 349 MiB.
- Legacy filtered manifest
  `…/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered.jsonl`
  contains 2693 dev-clean utterances (~5.371 h, 40 unique speakers)
  after the prior filter step.
- File sizes for `train-clean-100` and `test-clean` directories:
  `du -sh` reports 0 bytes (skeleton only).

### Common Voice English (cv-corpus-24.0-2025-12-05)

- Root: `/mnt/fast/nobackup/scratch4weeks/gb0048/sources/commonvoice/cv-corpus-24.0-2025-12-05/en`
- Version: cv-corpus-24.0-2025-12-05 (release directory present)
- License: https://commonvoice.mozilla.org/en/license (CC0)
- Access method: local
- Contents: only `clips/` directory; no `.tsv` transcripts; `clips/` is
  empty (`ls` returns no files).
- Section 1.1 approval predicate fails: condition (1) requires "official
  public transcripts"; transcripts absent.

### TED-LIUM Release 3

- Root: not present on `/mnt/fast/nobackup`
- `find /mnt/fast/nobackup -maxdepth 5 -type d -iname '*tedlium*'`
  returns nothing.
- Section 1.1 approval predicate fails: dataset absent on host.

### CHiME-6

- Root: not present on `/mnt/fast/nobackup`
- `find /mnt/fast/nobackup -maxdepth 5 -type d -iname '*chime*'`
  returns only unrelated paths (e.g. `RING@PHONE-CHIMES` directories
  belonging to other users).
- Section 1.1 approval predicate fails: dataset absent on host.

## Section 1.1 fallback resolution

Following Section 1.1 Decision rules in agent plan:

1. Common Voice → does not satisfy approval predicate (no transcripts).
2. TED-LIUM Release 3 → does not satisfy approval predicate (absent).
3. CHiME-6 → does not satisfy approval predicate (absent).
4. ⇒ Decision rule 4 would normally apply: set
   `claims_enabled.ood_real = false` and record `BLOCKED_OOD_PUBLIC`.
   However, the LibriSpeech HALT (Decision rule 1 of P1.1) supersedes
   this PARTIAL outcome; tracker marker is set to `MISSING_EVIDENCE`
   only, and the orchestrator may decide whether to also flip
   `claims_enabled.ood_real` once the LibriSpeech HALT is resolved.

`configs/robust_asr/data_v1.yaml` records `ood_real.selected_source: null`
and `ood_real.blocked: true` so that downstream tasks have a stable
declaration of the OOD-real status.

## Provisional speaker partition for dev-clean

40 dev-clean speakers, partitioned as recorded in
`/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/splits/devclean_speaker_split_v1/{train,val}_speakers.txt`:

- `validation` (8 speakers): 1272, 1673, 1988, 1993, 2035, 3853, 6241, 7976
- remaining (32 speakers): 174, 251, 422, 652, 777, 84, 1462, 1919, 2078,
  2086, 2277, 2412, 2428, 2803, 2902, 3000, 3081, 3170, 3536, 3576,
  3752, 5338, 5536, 5694, 5895, 6295, 6313, 6319, 6345, 7850, 8297,
  8842

This partition is recorded in `data_v1.yaml` under
`librispeech_devclean_speaker_partition_provisional`. It is **not**
authoritative until P1.3 manifests are built and verified, and it does
not by itself satisfy the four required split labels (lora_train,
router_train, locked_test still resolve empty).

## Speaker-disjoint check

`scripts/robust_asr/check_speaker_disjoint.py --config
configs/robust_asr/data_v1.yaml` emits `OK_SPEAKER_DISJOINT`. Note: the
check trivially passes because `lora_train`, `router_train`, and
`locked_test` are empty; this does NOT satisfy the P1.1 done-when
condition that "all four split labels resolve to non-empty file lists".

## Why this is HALTED, not PARTIAL

Agent plan Section 9 P1.1 done-when:

```
- data_v1.yaml parses.                                          [met]
- At least LibriSpeech is available; all four split labels      [NOT met]
  resolve to non-empty file lists; speaker-disjoint check       [met for non-empty splits]
  passes for LibriSpeech splits.
- Either Common Voice resolves OR a Section 1.1 fallback is     [met by recording BLOCKED]
  declared OR BLOCKED_OOD_PUBLIC is recorded.
```

Decision rule 1 of P1.1: "If LibriSpeech missing: status = HALTED,
marker = MISSING_EVIDENCE." LibriSpeech is partially missing
(`train-clean-100`, `train-clean-360`, `test-clean` have no audio).
`lora_train`, `router_train`, and `locked_test` cannot resolve to
non-empty file lists; this is the inventory invariant failure that
triggers the HALT.

## Unblock path (orchestrator action)

To clear the HALT, restore the missing LibriSpeech audio under the
existing root. Suggested commands (run by the user, not by this task):

```bash
# Stage download under the documented root
DATA_ROOT=/mnt/fast/nobackup/scratch4weeks/gb0048/sources/librispeech
cd "$DATA_ROOT"

# train-clean-100 (~6.3 GB)
wget https://www.openslr.org/resources/12/train-clean-100.tar.gz
tar -xzf train-clean-100.tar.gz   # already produces LibriSpeech/train-clean-100/

# test-clean (~346 MB)
wget https://www.openslr.org/resources/12/test-clean.tar.gz
tar -xzf test-clean.tar.gz

# Optional: train-clean-360 (~23 GB) for full LoRA scale
wget https://www.openslr.org/resources/12/train-clean-360.tar.gz
tar -xzf train-clean-360.tar.gz
```

After restore, P1.1 is rerun (no scope change required) and the
inventory invariant is rechecked.

To clear `BLOCKED_OOD_PUBLIC` separately, populate Common Voice clips +
transcripts under the existing
`/mnt/fast/nobackup/scratch4weeks/gb0048/sources/commonvoice/cv-corpus-24.0-2025-12-05/en/`
root or stage TED-LIUM R3 / CHiME-6 dev under a new root and amend the
reuse policy.

## Files produced by P1.1

- `configs/robust_asr/data_v1.yaml`
- `reports/robust_asr/data_inventory.md` (this file)
- `scripts/robust_asr/check_speaker_disjoint.py`
- `reports/robust_asr/task_reports/P1.1_data_inventory.md`

Tracker mutations:
- `tasks.P1.1.status: HALTED`
- `markers: [MISSING_EVIDENCE]`
- `blocked: true`, `blocker: "LibriSpeech train-clean-100/train-clean-360/test-clean audio missing on host"`
- `current_task: P1.1` (held)
- `last_completed_task: P0.5` (held)
- `state_transport.last_accepted_report_commit`: held at
  `3129c11edd5105d7c247b48eb1a170d7c1507cde` (P0 phase-gate acceptance);
  NOT advanced to the P1.1 commit per orchestrator instruction.

No Slurm. No Apptainer. No GPU. No external API.
