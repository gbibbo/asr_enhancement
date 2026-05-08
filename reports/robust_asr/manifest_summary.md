# Robust ASR — Public Manifest Summary

Produced by: P1.3 (`scripts/robust_asr/summarize_manifests.py`)
Generated at: 2026-05-08T04:44:28Z
Manifest root: `artifacts/robust_asr/manifests`
OOD-real claim status: **disabled (BLOCKED_OOD_PUBLIC)**

OOD-real reason: Common Voice clips/ empty and no transcripts; TED-LIUM R3 and CHiME-6 absent. No Section 1.1 OOD-real source resolves on host. Section 1.1 rule 4 / P1.1 rule 2 -> BLOCKED_OOD_PUBLIC, claims_enabled.ood_real=false (tracker).

## Per-manifest summary

| Manifest | Rows | Speakers | Duration (s) | Duration (h) | Bytes | sha256 |
|---|---:|---:|---:|---:|---:|---|
| `librispeech_locked_test.parquet` | 2620 | 40 | 19452.48 | 5.4035 | 138482 | `ad4f401e06e3c840aaa5d34e5cae22d1cdbb1fb34c7ea671dde0f8a712661da8` |
| `librispeech_lora_train.parquet` | 22507 | 200 | 286505.07 | 79.5847 | 1082018 | `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a` |
| `librispeech_router_train.parquet` | 6032 | 51 | 75622.10 | 21.0061 | 306026 | `c3d281ab0a53304b8a04753e9042bf3e62ea5e1957dc6ef1c524a2f2bac812fc` |
| `librispeech_validation.parquet` | 2703 | 40 | 19396.12 | 5.3878 | 143351 | `977a6f01d72171e9cfb9ce8aee71d4961a99d66397784225c71efbcf1d53733f` |

**Total rows:** 33862
**Total duration (s):** 400975.77
**Total duration (h):** 111.3822

## Columns

- `librispeech_locked_test.parquet`: audio_id, source_dataset, source_subset, speaker_id, chapter_id, utterance_id, audio_path_or_uri, audio_sha256, duration_s, sample_rate, num_frames, split_label
- `librispeech_lora_train.parquet`: audio_id, source_dataset, source_subset, speaker_id, chapter_id, utterance_id, audio_path_or_uri, audio_sha256, duration_s, sample_rate, num_frames, split_label
- `librispeech_router_train.parquet`: audio_id, source_dataset, source_subset, speaker_id, chapter_id, utterance_id, audio_path_or_uri, audio_sha256, duration_s, sample_rate, num_frames, split_label
- `librispeech_validation.parquet`: audio_id, source_dataset, source_subset, speaker_id, chapter_id, utterance_id, audio_path_or_uri, audio_sha256, duration_s, sample_rate, num_frames, split_label

