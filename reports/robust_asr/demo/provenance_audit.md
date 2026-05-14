PASS (provenance fields)
FAIL (upstream disjointness)

# P8.2 — Demo provenance audit (provenance OK; upstream-level disjointness FAIL)

Verdict (provenance fields):       **PASS**
Verdict (upstream disjointness):   **FAIL** — DEMO_UPSTREAM_LOCKED_OVERLAP
Phase: P8
Task: P8.2-upstream-leakage-audit (follow-up to P8.2-provenance-rerun)
Audited at commit: this commit
Routing: BLOCKED_OOD_PUBLIC + claims_enabled.ood_real=false (LibriSpeech-derived public path; common_voice_demo_reserved unused).
Prior verdicts: see "Prior verdicts" sections at the bottom.

## Question audited

Does the P8.2 demo bundle, after the provenance repair at commit
`003fc0d`, still satisfy the leakage rule at the **upstream** level
(per-entry `upstream_audio_id` and `upstream_speaker_id`) — not only
at the demo-side level (`audio_id`, `speaker_id`, `audio_sha256` of
the rendered WAV)?

The previous re-audit ("Prior verdict (asr-rp5 evidence applied)"
below) explicitly disclosed that the upstream LibriSpeech utterances
come from the `dev-clean` subset which feeds the locked validation /
degradation_v1 eval manifests. The leakage test
(`tests/robust_asr/test_leakage.py`) is scoped to demo-side
identifiers only and does **not** check `upstream_audio_id` /
`upstream_speaker_id`. This audit measures that gap.

## Method

1. Read `artifacts/robust_asr/demo/demo_examples_manifest.json` (8
   entries; `manifest_version=v1.1-provenance-repaired`).
2. Extract `upstream_audio_id` (5 unique values; 3 OOD-param
   illustrative entries reuse 3 of the 5 clean-source upstreams) and
   `upstream_speaker_id` (5 unique values: `1272`, `1673`, `174`,
   `1993`, `2086`).
3. Compare against every locked manifest:
   - `artifacts/robust_asr/manifests/librispeech_lora_train.parquet`
   - `artifacts/robust_asr/manifests/librispeech_router_train.parquet`
   - `artifacts/robust_asr/manifests/librispeech_validation.parquet`
   - `artifacts/robust_asr/manifests/librispeech_locked_test.parquet`
   - `artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet`
   - `artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet`
   - all 10 per-family `degradation_v1_<family>_{id,ood_param}.parquet`
   subset manifests.
4. Compare `upstream_audio_id` two ways:
   - **raw** (literal string match against the manifest's directory-style
     value `librispeech/dev-clean/<spk>/<chap>/<utt>`),
   - **normalized** (reduced to the locked-manifest schema
     `librispeech/dev-clean/<utt>`, since the locked manifests use the
     flat audio_id format observed in
     `librispeech_validation.parquet:audio_id`).

   The raw form returns 0 intersections everywhere only because the
   manifest's upstream IDs use a non-matching format; the normalized
   form is the true functional check.

## Demo upstream identifiers (extracted)

| audio_id (manifest, raw)                                      | normalized to locked schema                       | upstream_speaker_id |
|---------------------------------------------------------------|---------------------------------------------------|---------------------|
| librispeech/dev-clean/1272/128104/1272-128104-0000             | librispeech/dev-clean/1272-128104-0000             | 1272                |
| librispeech/dev-clean/1673/143396/1673-143396-0002             | librispeech/dev-clean/1673-143396-0002             | 1673                |
| librispeech/dev-clean/174/168635/174-168635-0000               | librispeech/dev-clean/174-168635-0000              | 174                 |
| librispeech/dev-clean/1993/147149/1993-147149-0000             | librispeech/dev-clean/1993-147149-0000             | 1993                |
| librispeech/dev-clean/2086/149214/2086-149214-0000             | librispeech/dev-clean/2086-149214-0000             | 2086                |

(3 OOD-param illustrative entries use the same upstream as `ex001`,
`ex003`, `ex004`, so distinct upstream count = 5.)

## Overlap table (upstream-level)

| locked manifest                                            | upstream_audio_id ∩ (raw) | upstream_audio_id ∩ (normalized) | upstream_speaker_id ∩ |
|------------------------------------------------------------|---------------------------:|---------------------------------:|----------------------:|
| librispeech_lora_train                                     | 0                          | 0                                | 0                     |
| librispeech_router_train                                   | 0                          | 0                                | 0                     |
| librispeech_validation                                     | 0                          | **5/5**                          | **5/5**               |
| librispeech_locked_test                                    | 0                          | 0                                | 0                     |
| degradation_v1_id_eval                                     | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_ood_param_eval                              | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_clean_id                                    | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_clean_ood_param                             | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_cafe_noise_id                               | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_cafe_noise_ood_param                        | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_phone_band_id                               | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_phone_band_ood_param                        | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_far_field_room_id                           | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_far_field_room_ood_param                    | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_muffled_lowpass_id                          | 0                          | **5/5**                          | **5/5**               |
| degradation_v1_muffled_lowpass_ood_param                   | 0                          | **5/5**                          | **5/5**               |

**Specific overlapping items (normalized upstream_audio_id):**

```
librispeech/dev-clean/1272-128104-0000   ∈ {validation, deg_id_eval, deg_ood_param_eval, all per-family subsets}
librispeech/dev-clean/1673-143396-0002   ∈ {validation, deg_id_eval, deg_ood_param_eval, all per-family subsets}
librispeech/dev-clean/174-168635-0000    ∈ {validation, deg_id_eval, deg_ood_param_eval, all per-family subsets}
librispeech/dev-clean/1993-147149-0000   ∈ {validation, deg_id_eval, deg_ood_param_eval, all per-family subsets}
librispeech/dev-clean/2086-149214-0000   ∈ {validation, deg_id_eval, deg_ood_param_eval, all per-family subsets}
```

**Specific overlapping speakers (upstream_speaker_id):**

```
{1272, 1673, 174, 1993, 2086} ⊆ validation.speaker_id
{1272, 1673, 174, 1993, 2086} ⊆ degradation_v1_id_eval.speaker_id
{1272, 1673, 174, 1993, 2086} ⊆ degradation_v1_ood_param_eval.speaker_id
{1272, 1673, 174, 1993, 2086} ⊆ every degradation_v1_<family>_{id,ood_param}.speaker_id
```

(LibriSpeech `dev-clean` contains exactly 40 speakers and all 2,703
utterances; `librispeech_validation.parquet` is the full 2,703-row
mirror of `dev-clean`. Therefore *any* `dev-clean` utterance overlaps
validation by both `audio_id` and `speaker_id`.)

## Findings

### F1. Provenance fields are PASS

The provenance enrichment at commit `003fc0d` correctly populated
`upstream_corpus`, `upstream_audio_id`, `upstream_url`,
`license_spdx=CC-BY-4.0`, `license_url`, `attribution`,
`recording_method`, `degradation_id`, `degradation_params`,
`degradation_version`, `seed`, `artifact_sha256`, and
`provenance_notes` for all 8 entries. License/attribution evidence is
sufficient for P9.1 handoff §6/§8 and P10 license review. No
operator-supplied evidence was invented; `upstream_audio_sha256` is
honestly recorded as `null`.

### F2. Upstream-level leakage FAILS Section 3 leakage rule 5

The 5 demo upstream utterances are 5/5 present in
`librispeech_validation.parquet`, `degradation_v1_id_eval.parquet`,
`degradation_v1_ood_param_eval.parquet`, and every per-family
`degradation_v1_<family>_{id,ood_param}.parquet` subset. The 5 demo
upstream speakers are 5/5 in the same locked manifests.

Section 3 leakage rule 5 ("Demo examples may not be drawn from locked
evaluation sets") is **violated at the upstream level**. The demo
audio bytes are derived (via `degradation_v1` transforms applied by
asr-rp5 `materialize_demo_examples.py` with `seed=0`) from the same
LibriSpeech `dev-clean` utterances that the locked validation /
degradation_v1 eval manifests transcribe. Reporting WER on demo
audio that derives from the same upstream as locked-eval audio
permits the model to score against material it has effectively
already seen during validation-time WER measurement.

The demo-side disjointness recorded by the existing leakage test
(`audio_id` `demo/...`, `speaker_id` `exNNN`, on-disk WAV `audio_sha256`)
remains intact, but it is **insufficient** to satisfy the leakage
guard once provenance discloses that the upstream is locked-eval
material.

### F3. Manifest upstream_audio_id format mismatch (latent gap)

The manifest at commit `003fc0d` records
`upstream_audio_id = "librispeech/dev-clean/<spk>/<chap>/<utt>"`
(directory-style) but the locked manifests use
`audio_id = "librispeech/dev-clean/<utt>"` (flat). A naive string-
intersection check would silently report 0 overlap and miss the
real leakage. This audit normalized both sides to the flat schema
to expose the true overlap. Future leakage tests must do the same
normalization (or the manifest must be re-rendered to the locked
schema). The mismatch is a latent gap, not a falsification — the
upstream identifiers point to the correct utterances; only the
string format differs.

### F4. Functional consequence

`tasks.P8.2.status` cannot be advanced to `PASS`. The provenance
gate is satisfied, but the upstream-level leakage gate is not.
Per orchestrator instruction "P8.2 still cannot be approved until
upstream-level disjointness is proven or a new legal public demo
source is supplied".

## What this audit did NOT do

- Did NOT edit any of the 8 demo WAV files. Bytes byte-unchanged;
  per-row `audio_sha256` unchanged.
- Did NOT delete or replace `artifacts/robust_asr/demo/demo_examples_manifest.json`.
- Did NOT edit `scripts/robust_asr/build_demo_examples.py`.
- Did NOT edit `tests/robust_asr/test_leakage.py` (deliberately —
  see "Recommended next steps" §3).
- Did NOT change `claims_enabled.*` (all four flags remain `false`).
- Did NOT clear `BLOCKED_OOD_PUBLIC`, `BLOCKED_API`, or
  `OUTCOME_E_DETERMINISTIC_SELECTOR`.
- Did NOT advance `current_task` (held at `P8.2`).
- Did NOT advance `state_transport.last_accepted_report_commit` to
  this audit commit.
- Did NOT approve `tasks.P8.2-provenance-rerun` or `tasks.P8.2`.

## Recommended next steps (operator-side; out of Claude scope)

EITHER **(A)** supply 8 new public demo audios whose
`upstream_audio_id` and `upstream_speaker_id` are disjoint from every
LibriSpeech locked manifest (`lora_train`, `router_train`,
`validation`, `locked_test`, all `degradation_v1_*` subsets). Likely
sources: a held-out subset of LibriSpeech `train-other-500` /
`dev-other` / `test-other` (none currently restored on host); a
public Common Voice EN subset disjoint from the eventual OOD-real
locked split; or a CC-licensed demo corpus distinct from LibriSpeech.

OR **(B)** record an approved plan deviation explicitly accepting
the upstream overlap with `dev-clean` for a *demo-only* artifact
under documented constraints: (i) the demo bundle is never used to
report WER or as evidence for any `claims_enabled.*` flag; (ii) the
P9.1 handoff README §6 ("Risks, limits, disabled claims") explicitly
calls out the dev-clean upstream overlap; (iii) `tasks.P8.2.status`
advances under a separate `APPROVE_PLAN(P8.2-deviation)` packet that
records the deviation rationale and the upstream-overlap leakage
gap.

OR **(C)** re-partition `data_v1.yaml` to free a held-out speaker
pool from `train-clean-100` / `dev-clean` / `test-clean`, re-render
the demo from those held-out speakers via asr-rp5
`materialize_demo_examples.py` (`seed=0`, `degradation_v1`), then
rerun this audit. This requires CHANGE_SCOPE on `data_v1.yaml`,
re-validation of every downstream manifest, and is the most invasive
option.

In addition, regardless of (A)/(B)/(C), the leakage test should be
extended to read `upstream_audio_id` / `upstream_speaker_id` from
the demo manifest and assert disjointness against the locked
manifests with the schema-normalization fix from §F3 applied. That
test extension belongs in a future P8.2 scope-change.

## Verification snapshot (audit time)

- 8 WAV files on disk under `artifacts/robust_asr/demo/audio/`
  (count = 8); per-row on-disk sha256 == manifest `audio_sha256`
  (no drift).
- demo-side `audio_id` ∩ locked = ∅; demo-side `speaker_id` ∩ locked
  = ∅; demo-side `audio_sha256` ∩ locked = ∅ (re-verified).
- upstream `audio_id` (normalized) ∩ locked = **5/5** in 13 of 16
  locked manifests (see overlap table).
- upstream `speaker_id` ∩ locked = **5/5** in 13 of 16 locked
  manifests (see overlap table).
- `pytest tests/robust_asr/test_leakage.py` → PASS (5/5) — but this
  is **insufficient** because it does not test upstream fields (see
  §F2).
- `pytest tests/robust_asr/` → PASS (137/137).
- `validate_report_shape.py` → `OK_REPORT_SHAPE`.
- `python -c "import yaml; yaml.safe_load(open(...))"` →
  `OK_PROGRESS_YAML_PARSE`.

---

## Prior verdict (asr-rp5 evidence applied)

# P8.2 — Demo provenance audit (re-run; provenance repaired)

Verdict: **PASS**
Phase: P8
Task: P8.2-provenance-rerun (operator-supplied asr-rp5 evidence applied)
Audited at commit: `003fc0d725d57875a7ecde79af4bb4d801deae9d`
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

(See full enrichment narrative in commit `003fc0d`.)

---

## Prior verdict (initial run)

# P8.2 — Demo provenance audit (initial run)

Verdict: **INSUFFICIENT**
Phase: P8
Task: P8.2 (provenance audit under CHANGE_SCOPE(P8.2-provenance) on `6783789b61bc4c8e05b263c0b245b67c9d33dc77`)
Audited at commit: `5cf704adda14b4d8b4184e258a72634abf4828d1`

Findings: source dir contained zero metadata files; manifest carried
`license=demo_reserve_public` (not SPDX) and no upstream attribution;
build script was a bit-identical copier with no LibriSpeech reference;
disjointness vs locked manifests intact at the demo-side level. Per
orchestrator instruction "Do not invent license/provenance.", no
manifest fields were added in the initial audit.
