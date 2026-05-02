# Dataset Version: T2.4

**dataset_version:** `librispeech_devclean_v1_exclpending_sha256_bacd6f7ba89c`

## Manifest

- **Path:** `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1.jsonl`
- **Records:** 2703
- **SHA-256:** `bacd6f7ba89c439bd73ee4b94e3430db318cf0a62cd8a506fa6972a9a9feb60f`

## Exclusion policy

- **Status:** `pending_public_examples`
- **Filtered manifest:** `None`

## Gates

- T2.3 must be re-run after B6.2 produces `demo_examples.json`.
- T3.1 must not run while `configs/training/public_examples_excluded.yaml`
  has `status: pending_public_examples`.
