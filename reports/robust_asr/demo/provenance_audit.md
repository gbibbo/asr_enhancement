INSUFFICIENT

# P8.2 — Demo provenance audit

Verdict: **INSUFFICIENT**
Phase: P8
Task: P8.2 (provenance audit under CHANGE_SCOPE(P8.2-provenance) on `6783789b61bc4c8e05b263c0b245b67c9d33dc77`)
Audited at commit: `5cf704adda14b4d8b4184e258a72634abf4828d1`
Routing: BLOCKED_OOD_PUBLIC + claims_enabled.ood_real=false (LibriSpeech-derived public path; common_voice_demo_reserved unused).

## Question audited

Does the P8.2 demo bundle (8 WAV files + manifest) carry sufficient
public-corpus provenance, license identification, and upstream
attribution to support:

1. agent plan §4.7 wording "LibriSpeech-derived public" for the 5
   ID-family entries and "public LibriSpeech-derived material" for the
   3 illustrative-OOD entries;
2. P9.1 handoff `README.md` §6 ("Risks, limits, disabled claims") and
   §8 ("Contact and license");
3. P10.1 final verification and P10.2 final asset audit, including a
   license / redistribution review of every committed audio file?

## Sources audited

1. `artifacts/robust_asr/demo/demo_examples_manifest.json` — read
   verbatim; 8 entries; per-entry fields: `audio_id, speaker_id,
   family, tier, source, license, duration_s, audio_sha256,
   file_path, notes`.
2. `scripts/robust_asr/build_demo_examples.py` — read verbatim; 8
   selections hardcoded in `SELECTION`; behaviour is
   `shutil.copyfile(src, dst)` from the operator-staged scratch
   reserve to the repo demo audio dir; no LibriSpeech read; no call
   to `libs/audio/degradations.py`; no upstream metadata read; no
   license file read.
3. `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/demo_reference_artifacts/**`
   — exhaustive recursive listing executed at audit time.
4. `configs/robust_asr/reuse_policy_v1.yaml` row for the source path
   — read verbatim; classifies the dir as `data_root` /
   `permitted_use: read_only` / `notes: 5 demo reference examples;
   read by P8.2 to produce demo_examples_manifest.json`. No upstream
   corpus or license attribution recorded.
5. `configs/robust_asr/data_v1.yaml` — read verbatim; LibriSpeech
   `train-clean-100` / `dev-clean` / `test-clean` are fully consumed
   by `lora_train (200 spk)`, `router_train (51 spk)`, `validation
   (40 spk)`, `locked_test (40 spk)` = 331 of 331 host speakers; no
   LibriSpeech speakers remain free for a public demo pool.

## Findings

### F1. Source dir contains no provenance metadata

Exhaustive `find /mnt/fast/.../demo_reference_artifacts -type f`
returns exactly 30 files, all `.wav`:

  examples/{ex001,ex003,ex004,ex007,ex010}/{broadband_hiss,
                                            cafe_background,
                                            clean,
                                            far_field_room,
                                            muffled,
                                            phone_call}.wav

There is no `README*`, no `LICENSE*`, no `provenance.json`, no
`*.yaml`, no `*.txt`, no `*.csv`, no SPDX identifier file, no speaker
consent record, no recording method record, no dataset version file,
no signature or attestation. The five top-level directory names
(`ex001`, `ex003`, `ex004`, `ex007`, `ex010`) have no documented
mapping to any public corpus utterance ID.

### F2. Build script is a bit-identical copier, not a derivation

`scripts/robust_asr/build_demo_examples.py` selects 8 hardcoded
`(speaker_id, source_filename, family, tier, notes)` tuples,
`shutil.copyfile`s each upstream WAV to
`artifacts/robust_asr/demo/audio/`, recomputes sha256, and writes
the manifest. The script:

- never opens any LibriSpeech `.flac`,
- never resolves any LibriSpeech `*.trans.txt` line,
- never imports `libs.audio.degradations` (no `sample_clean`,
  `sample_cafe_noise`, `sample_phone_band`, `sample_far_field_room`,
  `sample_muffled_lowpass`, or `apply_degradation` call),
- never reads any license file or upstream provenance file,
- never writes upstream attribution into the manifest.

The on-disk audio in `artifacts/robust_asr/demo/audio/` is
bit-identical to the upstream WAVs (every demo `audio_sha256` equals
the corresponding `demo_reference_artifacts/examples/<exNNN>/<file>.wav`
sha256, re-verified at audit time).

### F3. Manifest provenance fields are assertional, not evidentiary

For every one of the 8 entries:

- `source = "demo_reference_artifacts/v1 (operator-staged public demo
  reserve; reuse_policy P8.2 read_only)"` — the literal string
  asserts "public demo reserve" without naming an upstream corpus,
  recording, or canonical license.
- `license = "demo_reserve_public"` — not a recognized license
  identifier; no SPDX (e.g. `CC0-1.0`, `CC-BY-4.0`); no `license_url`;
  no `license_attestation_path`.
- No `upstream_corpus`, `upstream_audio_id`, `upstream_audio_sha256`,
  `upstream_path`, `recording_method`, `attribution`, or
  `provenance_attestation` fields are present.

### F4. Plan drift vs §4.7

Agent plan §4.7 specifies "LibriSpeech-derived public" for the 5 ID
family entries and "public LibriSpeech-derived material disjoint from
locked eval" for the 3 illustrative-OOD entries. The implemented
build is bit-identical operator-staged audio whose origin is not
LibriSpeech. Under the current `data_v1.yaml` partition every
LibriSpeech speaker present on host (251 train-clean-100 + 40
dev-clean + 40 test-clean = 331) is in a locked manifest, so the
"LibriSpeech-derived" path was not feasible without either (a)
re-partitioning `data_v1.yaml` to free a held-out speaker pool, (b)
deriving demo audio by applying `degradation_v1` transforms to
locked-eval LibriSpeech audio (which would violate §3 leakage rule
5 and the orchestrator's hard requirement of disjointness from
locked eval), or (c) restoring an additional LibriSpeech subset
(`train-other-500`, `dev-other`, `test-other`) under
`/mnt/fast/.../sources/librispeech/LibriSpeech/`. None of these
options was taken; the operator-staged reserve was used instead.
The manifest does not declare this deviation.

### F5. Disjointness vs locked manifests is intact

Independently re-verified at audit time (no file edits):

| check                                                       | result |
|-------------------------------------------------------------|--------|
| demo `audio_id` ∩ locked (6 manifests union)                | ∅      |
| demo `speaker_id` ∩ locked                                  | ∅      |
| demo `audio_sha256` ∩ locked                                | ∅      |
| per-row on-disk sha256 == manifest sha256 (all 8)            | true   |
| 8 demo sha256s pairwise unique                               | true   |
| 8 WAV files present under artifacts/robust_asr/demo/audio/   | true   |

## Repair attempted

None applied. Per orchestrator instruction "Do not invent
license/provenance.": no upstream corpus, license URL, SPDX
identifier, recording method, or attribution can be recorded
truthfully without external evidence. The manifest is left untouched
(see §"What this audit did NOT do"). Demo WAV bytes are untouched.

## What this audit did NOT do

- Did NOT edit any of the 8 demo WAV files.
- Did NOT edit `artifacts/robust_asr/demo/demo_examples_manifest.json`
  (no field added, no field removed, no value changed). Per-row
  sha256s in the manifest still match on-disk audio bit-for-bit.
- Did NOT edit `scripts/robust_asr/build_demo_examples.py`.
- Did NOT rebuild the demo bundle.
- Did NOT change `claims_enabled.*`.
- Did NOT clear `BLOCKED_OOD_PUBLIC`, `BLOCKED_API`, or
  `OUTCOME_E_DETERMINISTIC_SELECTOR`.
- Did NOT advance `current_task` or `state_transport.last_accepted_report_commit`.

## Conclusion

The 8 P8.2 demo entries are functionally correct (8 files, 16 kHz
mono PCM16, deterministic, disjoint from every locked manifest by
audio_id/speaker_id/audio_sha256, leakage tests green) but lack the
public-corpus provenance, license identification, and upstream
attribution required by P9.1 handoff and P10 final verification.
The operator-staged source contains zero metadata files; no upstream
audio_id, no recording method, no license URL, and no attribution
exist on host. Without external evidence supplied by the operator,
P8.2 cannot be approved as a public-demo deliverable.

`tasks.P8.2.status` is set to `HALTED` with
`marker=MISSING_EVIDENCE` and `reason=DEMO_PROVENANCE_INSUFFICIENT`.
`current_task=P8.2` is held; `last_completed_task=P8.1` is held.
`state_transport.expected_next_task=P8_GATE` is held (the orchestrator
will redirect once provenance is supplied).

## Required external action to unblock

To clear `DEMO_PROVENANCE_INSUFFICIENT` the operator must supply, at
the source dir
`/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/demo_reference_artifacts/`,
verifiable provenance per source WAV, EITHER (A) by populating a
machine-readable manifest there:

```text
demo_reference_artifacts/
├── README.md                # corpus name, recording method, attribution
├── LICENSE.txt              # canonical license text
└── provenance.json          # machine-readable; per-file:
                             #   path, upstream_corpus, upstream_audio_id,
                             #   upstream_url, upstream_audio_sha256,
                             #   recording_method, license_spdx,
                             #   license_url, attribution
```

OR (B) by re-deriving the 8 demo WAVs from a documented public
corpus through a published pipeline, with the build script reading
the upstream IDs and license fields from the corpus and recording
them per-entry in the manifest.

Once one of (A) or (B) is in place, P8.2 must be re-executed under a
fresh `APPROVE_PLAN(P8.2-provenance-rerun)` to enrich
`demo_examples_manifest.json` with `upstream_corpus`,
`upstream_audio_id`, `upstream_audio_sha256`, `license` (SPDX),
`license_url`, `attribution`, and `origin` fields per entry, plus a
top-level `provenance` block, and to update
`reports/robust_asr/task_reports/P8.2_demo_manifest.md`.

## Verification snapshot (audit time)

- 8 WAV files on disk under `artifacts/robust_asr/demo/audio/` (count
  = 8).
- `manifest.n_examples = 8`.
- All 8 on-disk sha256 == manifest `audio_sha256` (no drift).
- demo ∩ locked = ∅ on `audio_id`, `speaker_id`, `audio_sha256`.
- `pytest tests/robust_asr/test_leakage.py` and full
  `pytest tests/robust_asr/` rerun results recorded in the P8.2 task
  report and the tracker entry for this audit.
