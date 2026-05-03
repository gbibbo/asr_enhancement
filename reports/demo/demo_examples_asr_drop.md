# Demo Examples ASR Drop Report

- Generated: 2026-05-02T23:59:40.242536+00:00
- Amended:   2026-05-03T00:14:53.716234+00:00
- Whisper model: `tiny.en`
- Model cache: `/home/gbibbo/asr_enhancement_runtime/cache/whisper`
- Pass threshold: `clean_word_accuracy - degraded_word_accuracy >= 0.01`
- Candidate pool size (B6.1): 10
- Final demo set size (B6.2): 5
- Excluded count: 5
- Overall pass: **True**

## Scope note

B6.1 candidate pool was 10 reserved examples from datamove1. B6.2 final public demo set is the 5 examples that satisfied the ASR drop criterion under DEGRADATION_VERSION 1.0 with faster-whisper tiny.en. The 5 excluded examples remain reserved/excluded from training but are not exposed via config/demo_examples.json.

## Final public demo set (passes ASR drop criterion)

| example_id | source_recording_id | clean WA | degradation | deg WA | drop | pass |
|------------|---------------------|----------|-------------|--------|------|------|
| ex001 | 1272-128104-0000 | 0.941 | far_field_room | 0.941 | 0.000 | False |
| ex001 | 1272-128104-0000 | 0.941 | cafe_background | 0.941 | 0.000 | False |
| ex001 | 1272-128104-0000 | 0.941 | phone_call | 0.941 | 0.000 | False |
| ex001 | 1272-128104-0000 | 0.941 | muffled | 0.882 | 0.059 | True |
| ex001 | 1272-128104-0000 | 0.941 | broadband_hiss | 0.941 | 0.000 | False |
| ex003 | 1673-143396-0002 | 0.947 | far_field_room | 0.947 | 0.000 | False |
| ex003 | 1673-143396-0002 | 0.947 | cafe_background | 0.947 | 0.000 | False |
| ex003 | 1673-143396-0002 | 0.947 | phone_call | 0.947 | 0.000 | False |
| ex003 | 1673-143396-0002 | 0.947 | muffled | 0.895 | 0.053 | True |
| ex003 | 1673-143396-0002 | 0.947 | broadband_hiss | 0.947 | 0.000 | False |
| ex004 | 174-168635-0000 | 1.000 | far_field_room | 0.750 | 0.250 | True |
| ex004 | 174-168635-0000 | 1.000 | cafe_background | 1.000 | 0.000 | False |
| ex004 | 174-168635-0000 | 1.000 | phone_call | 1.000 | 0.000 | False |
| ex004 | 174-168635-0000 | 1.000 | muffled | 0.875 | 0.125 | True |
| ex004 | 174-168635-0000 | 1.000 | broadband_hiss | 1.000 | 0.000 | False |
| ex007 | 1993-147149-0000 | 1.000 | far_field_room | 0.000 | 1.000 | True |
| ex007 | 1993-147149-0000 | 1.000 | cafe_background | 1.000 | 0.000 | False |
| ex007 | 1993-147149-0000 | 1.000 | phone_call | 1.000 | 0.000 | False |
| ex007 | 1993-147149-0000 | 1.000 | muffled | 0.765 | 0.235 | True |
| ex007 | 1993-147149-0000 | 1.000 | broadband_hiss | 1.000 | 0.000 | False |
| ex010 | 2086-149214-0000 | 1.000 | far_field_room | 1.000 | 0.000 | False |
| ex010 | 2086-149214-0000 | 1.000 | cafe_background | 0.933 | 0.067 | True |
| ex010 | 2086-149214-0000 | 1.000 | phone_call | 1.000 | 0.000 | False |
| ex010 | 2086-149214-0000 | 1.000 | muffled | 1.000 | 0.000 | False |
| ex010 | 2086-149214-0000 | 1.000 | broadband_hiss | 1.000 | 0.000 | False |

## Excluded examples (do not satisfy ASR drop criterion under current degradation parameters)

| example_id | source_recording_id | clean WA | best drop | reason |
|------------|---------------------|----------|-----------|--------|
| ex002 | 1462-170138-0001 | 0.818 | 0.000 | No degradation satisfied clean_word_accuracy - degraded_word_accuracy >= 0.01; best observed drop = 0.0000 |
| ex005 | 1919-142785-0003 | 1.000 | 0.000 | No degradation satisfied clean_word_accuracy - degraded_word_accuracy >= 0.01; best observed drop = 0.0000 |
| ex006 | 1988-147956-0002 | 1.000 | 0.000 | No degradation satisfied clean_word_accuracy - degraded_word_accuracy >= 0.01; best observed drop = 0.0000 |
| ex008 | 2035-147960-0000 | 1.000 | 0.000 | No degradation satisfied clean_word_accuracy - degraded_word_accuracy >= 0.01; best observed drop = 0.0000 |
| ex009 | 2078-142845-0009 | 1.000 | 0.000 | No degradation satisfied clean_word_accuracy - degraded_word_accuracy >= 0.01; best observed drop = 0.0000 |

Excluded examples remain reserved in `config/demo_example_candidates.json` and
remain excluded from training, but are not exposed via the public demo API.
