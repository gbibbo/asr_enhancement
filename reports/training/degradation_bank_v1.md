# T3.2a Degradation Bank (degradation_v1)

Status: complete  
Mode: full  
Degradation version: `degradation_v1`  
Dataset version: `librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8`  
Source manifest records: 2693  
Source manifest SHA-256: `dc6674bcf7a82db070ec490ede4624e326d7405b95a9e360f57f542f39a5f80b`  
Source manifest SHA-256 unchanged: True  
Degraded files: 13465  
Per-family count: `{'broadband_hiss': 2693, 'cafe_background': 2693, 'far_field_room': 2693, 'muffled': 2693, 'phone_call': 2693}`  
Final audio root: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/degraded/degradation_v1`  
Final degraded manifest path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/datasets/librispeech_manifest_v1_filtered_degraded_v1.jsonl`  
Final degraded manifest SHA-256: `c6f87452f146760077a7c281f9cb7b6bd9c4ebd22e65927a6109344cba0dbb7c`  
file_sha256.tsv path: `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runs/t3_2a_bank_full_2125897/file_sha256.tsv`  
Deterministic validation sample size: 50  
Audio format: WAV, 16 kHz mono, PCM_16  
Length contract: output_samples == input_samples (apply_degradation)  
Code commit at run: `e89db8dcb9fbfb486930d697d9345b3361c6e93d`  
Result commit: `c4ee5f4`  
Smoke Slurm job ID: `2125896`  
Full Slurm job ID: `2125897`  
Full elapsed: `00:02:59`  
Full MaxRSS: `3097852K`  
Date (UTC): `2026-05-02T05:33:40.299730Z`  

## Families and parameters (frozen)

| Family | Stochastic | Parameters |
|---|---|---|
| far_field_room   | yes | IR length 0.8 s (12800 samples), RT60 0.6 s, tau = RT60/ln(1000), DRR -6 dB, direct sample at index 0 |
| cafe_background  | yes | Speech-shaped Gaussian (Butterworth bandpass 200-4000 Hz, order 4), SNR 5 dB |
| phone_call       | no  | Butterworth bandpass 300-3400 Hz order 6 -> resample 16->8 kHz -> mu-law G.711 round-trip -> resample 8->16 kHz |
| muffled          | no  | Butterworth lowpass 800 Hz order 4, then -6 dB attenuation |
| broadband_hiss   | yes | Gaussian white noise, SNR 10 dB |

All numeric constants are duplicated in `DEGRADATION_PARAMS` in `libs/audio/degradations.py`.
