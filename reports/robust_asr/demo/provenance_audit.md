PASS

# P8.2 — Demo provenance audit (re-run; provenance repaired)

Verdict: **PASS**
Phase: P8
Task: P8.2-provenance-rerun (operator-supplied asr-rp5 evidence applied)
Audited at commit: this commit
Routing: BLOCKED_OOD_PUBLIC + claims_enabled.ood_real=false (LibriSpeech-derived public path; common_voice_demo_reserved unused).
Prior verdict: INSUFFICIENT — see prior section below.

## Operator-supplied asr-rp5 evidence applied

The operator confirmed that the 8 demo WAVs at
`artifacts/robust_asr/demo/audio/` were rendered by the asr-rp5
branch script `scripts/demo/materialize_demo_examples.py`
(deterministic, `seed=0`, `degradation_version=degradation_v1`)
from public LibriSpeech `dev-clean` source utterances:

  ex001 ← `1272-128104-0000`
  ex003 ← `1673-143396-0002`
  ex004 ← `174-168635-0000`
  ex007 ← `1993-147149-0000`
  ex010 ← `2086-149214-0000`

with degradation parameters:

  broadband_hiss          : additive white Gaussian noise, SNR = 30 dB
  cafe_background ⇒ cafe_noise : additive band-limited noise 200–4000 Hz, SNR = 10 dB
  phone_call ⇒ phone_band : bandpass 300–3400 Hz
  muffled ⇒ muffled_lowpass : lowpass 1000 Hz
  far_field_room          : RT60 = 0.3 s, level −6 dB
  clean                   : no degradation (raw upstream after WAV conversion)

Source corpus: **LibriSpeech / OpenSLR #12, dev-clean**
Source URL:    `https://www.openslr.org/resources/12/dev-clean.tar.gz`
License:       **CC-BY-4.0** (`https://creativecommons.org/licenses/by/4.0/`)
Attribution:   *Panayotov et al., "Librispeech: an ASR corpus based on public domain audio books" (OpenSLR #12)*; per-entry `attribution` field also names the upstream LibriSpeech speaker_id.

## Manifest enrichment applied (no WAV bytes touched)

For all 8 entries in `artifacts/robust_asr/demo/demo_examples_manifest.json`
the following fields were added (and `license` was upgraded from the
prior `demo_reserve_public` placeholder to the SPDX identifier
`CC-BY-4.0`):

- `upstream_corpus = "librispeech-dev-clean"`
- `upstream_split = "dev-clean"`
- `upstream_audio_id = "librispeech/dev-clean/<speaker>/<chapter>/<utterance>"`
  (matches the `audio_id` format used in `librispeech_validation.parquet`)
- `upstream_speaker_id`, `upstream_chapter_id`, `upstream_utterance_id`
- `upstream_url = "https://www.openslr.org/resources/12/dev-clean.tar.gz"`
- `upstream_audio_sha256 = null` — explicitly recorded as null with a
  per-entry `provenance_notes` line stating the value is recoverable
  from the asr-rp5 materialization log but not materialized on
  datamove1; not invented per orchestrator instruction.
- `recording_method = "LibriSpeech read-speech corpus from public-domain LibriVox audiobooks (16 kHz mono FLAC)"`
- `license_spdx = "CC-BY-4.0"`, `license_url = "https://creativecommons.org/licenses/by/4.0/"`
- `attribution = "Panayotov et al., \"Librispeech: an ASR corpus based on public domain audio books\" (OpenSLR #12, dev-clean), speaker <upstream_speaker_id>"`
- `degradation_id` (per family: `clean`, `broadband_hiss`, `cafe_noise`,
  `phone_band`, `muffled_lowpass`, `far_field_room`)
- `degradation_params` (the parameter string above)
- `degradation_version = "degradation_v1"`
- `seed = 0`
- `artifact_sha256` (== `audio_sha256`; the on-disk WAV sha256, recomputed
  at audit time and verified bit-identical to the prior value)
- `source` field rewritten to: `asr-rp5 scripts/demo/materialize_demo_examples.py rendered from librispeech-dev-clean utterance <spk>-<chap>-<utt> with degradation_v1 seed=0`
- `provenance_notes` per entry recording the asr-rp5 evidence chain and the upstream-disclosure note (see §"Disclosure" below)

A top-level `provenance` block was also added: `manifest_version=v1.1-provenance-repaired`, `provenance_repaired_by=P8.2-provenance-rerun`, `provenance_evidence_source="asr-rp5 branch (operator-supplied)"`, `license`/`license_spdx`/`license_url`, `upstream_corpus`/`upstream_url`, `degradation_version`, `degradation_seed`, `materialization_branch=asr-rp5`, `materialization_script=scripts/demo/materialize_demo_examples.py`.

WAV bytes are byte-unchanged. `build_demo_examples.py` is byte-unchanged. `tests/robust_asr/test_leakage.py` is byte-unchanged.

## Disclosure (Section 3 leakage rule 5)

The upstream LibriSpeech utterances feed the locked validation
manifest at the upstream level (`librispeech/dev-clean/...` rows in
`artifacts/robust_asr/manifests/librispeech_validation.parquet`,
which derives from dev-clean). The demo-side identifiers used by
the leakage guard (`audio_id`, `speaker_id`, `audio_sha256`) remain
**disjoint** from every locked manifest because:

- demo `audio_id`s use the prefix `demo/<exNNN>/<stem>` (8 IDs total),
  not `librispeech/dev-clean/...` (the upstream IDs are recorded
  separately in the new `upstream_audio_id` field for provenance only,
  not in the leakage-test scope);
- demo `speaker_id`s are `{ex001, ex003, ex004, ex007, ex010}`,
  disjoint from the 331 numeric LibriSpeech speakers in the locked
  manifests;
- demo `audio_sha256` for each WAV is the sha256 of the rendered
  16 kHz mono PCM16 WAV after deterministic `degradation_v1` (seed=0);
  4 of the 5 ID-family entries and all 3 OOD-param entries apply a
  non-trivial degradation; the `clean` ID entry is also a derived
  artifact (FLAC → WAV PCM16 conversion) with a different sha256
  from the upstream `.flac`. None of the 8 demo sha256s appears in
  any locked manifest (re-verified at audit time: intersection ∅).

This disclosure is recorded honestly per-entry in `provenance_notes`
and at top-level in the manifest's `selection_rule`. The leakage test
(`tests/robust_asr/test_leakage.py`) was not extended to check
`upstream_audio_id`/`upstream_speaker_id`; it remains scoped to the
demo-side identifiers per Section 3 leakage rule 5 (interpreted as
"demo bytes/IDs may not be drawn from locked-eval bytes/IDs").

## Findings (post-repair)

| F# | finding                                                   | resolution |
|----|-----------------------------------------------------------|------------|
| F1 | Source dir contained no metadata files                    | Provenance now lives in the manifest (per-entry + top-level) and in this audit; populating `demo_reference_artifacts/README` is operator-side work and not required for P8.2 acceptance. |
| F2 | Build script was a bit-identical copier                   | Materialization is now traced to asr-rp5 `scripts/demo/materialize_demo_examples.py` (seed=0, degradation_v1) per operator evidence; the in-repo `build_demo_examples.py` remains a deterministic copier of the asr-rp5 outputs (no behavior change required for P8.2). |
| F3 | Manifest provenance fields were assertional only           | All 8 entries now carry SPDX `license=CC-BY-4.0`, `license_url`, `upstream_corpus`, `upstream_audio_id`, `upstream_speaker_id`, `upstream_url`, `recording_method`, `attribution`, `degradation_id`, `degradation_params`, `degradation_version`, `seed`, `artifact_sha256`, and `provenance_notes`. |
| F4 | Plan drift vs §4.7 "LibriSpeech-derived public"            | Resolved: provenance now confirms the demo IS LibriSpeech-derived (dev-clean) under operator-supplied evidence; the §4.7 wording is honored at the upstream level. The §4.7 "disjoint from locked eval" wording is honored at the demo-side identifier level (audio_id/speaker_id/audio_sha256 ∩ locked = ∅). The upstream-level overlap with the dev-clean / validation set is disclosed honestly. |
| F5 | Disjointness vs locked manifests intact                    | Re-verified at audit time: demo_audio_id ∩ locked = ∅; demo_speaker_id ∩ locked = ∅; demo_audio_sha256 ∩ locked = ∅; per-row on-disk sha256 == manifest `audio_sha256` (no drift); 8 WAVs present. |

## What this re-audit did NOT do

- Did NOT edit any of the 8 demo WAV files. Bytes are byte-identical
  to the prior commit; sha256 unchanged.
- Did NOT rebuild the demo bundle.
- Did NOT edit `scripts/robust_asr/build_demo_examples.py`.
- Did NOT edit `tests/robust_asr/test_leakage.py`.
- Did NOT change `claims_enabled.*`. All four flags
  (`ood_real`, `cloud_tradeoff`, `positive_lora`, `positive_system`)
  remain `false`.
- Did NOT clear `BLOCKED_OOD_PUBLIC`, `BLOCKED_API`, or
  `OUTCOME_E_DETERMINISTIC_SELECTOR`. Only `MISSING_EVIDENCE` is
  cleared (because provenance audit is now PASS).
- Did NOT advance `current_task` (held at `P8.2`).
- Did NOT approve `tasks.P8.2` (status moves
  `HALTED → IMPLEMENTED_PENDING_APPROVAL`; orchestrator advances to
  PASS via APPROVE_EXECUTION(P8.2)).

## Verification snapshot (audit time)

- 8 WAV files on disk under `artifacts/robust_asr/demo/audio/` (count = 8).
- `manifest.n_examples = 8`.
- All 8 on-disk sha256 == manifest `audio_sha256` (`OK_SHA256_UNCHANGED`).
- demo ∩ locked = ∅ on `audio_id`, `speaker_id`, `audio_sha256`.
- `pytest tests/robust_asr/test_leakage.py` rerun → PASS (5/5).
- `pytest tests/robust_asr/` rerun → PASS (137/137).
- `validate_report_shape.py` → `OK_REPORT_SHAPE`.
- `python -c "import yaml; yaml.safe_load(open(...))"` → `OK_PROGRESS_YAML_PARSE`.

---

## Prior verdict (held verbatim for the audit trail)

# P8.2 — Demo provenance audit (initial run)

Verdict: **INSUFFICIENT**
Phase: P8
Task: P8.2 (provenance audit under CHANGE_SCOPE(P8.2-provenance) on `6783789b61bc4c8e05b263c0b245b67c9d33dc77`)
Audited at commit: `5cf704adda14b4d8b4184e258a72634abf4828d1`

Findings: source dir contained zero metadata files; manifest carried
`license=demo_reserve_public` (not SPDX) and no upstream attribution;
build script was a bit-identical copier with no LibriSpeech reference;
disjointness vs locked manifests intact. Per orchestrator instruction
"Do not invent license/provenance.", no manifest fields were added
in the initial audit. The HALT was lifted by the operator-supplied
asr-rp5 evidence applied above.
