"""T6.2b — tests for `PairedDevCleanDataset`.

Requires torch + soundfile + numpy. Login-node Python on datamove1 has no
torch; these tests run inside Apptainer via
slurm/jobs/t6_2b_pytest_apptainer.sh. They use synthetic WAV files written
to `tmp_path` so they do not depend on the real on-disk split.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts" / "training"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402

from datasets import PairedDevCleanDataset  # noqa: E402


SAMPLE_RATE = 16000
EXPECTED_FAMILIES = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_wav(path: Path, n_seconds: float, freq_hz: float, sr: int = SAMPLE_RATE) -> None:
    n = int(round(n_seconds * sr))
    t = np.arange(n, dtype=np.float32) / sr
    samples = 0.1 * np.sin(2 * np.pi * freq_hz * t).astype(np.float32)
    sf.write(str(path), samples, sr, subtype="PCM_16")


def _build_synthetic_split(tmp_path: Path) -> tuple[Path, Path, str, str]:
    audio_root = tmp_path / "audio"
    audio_root.mkdir(parents=True, exist_ok=True)

    speakers = ["100", "101"]
    utterance_ids = []
    clean_rows: list[dict] = []
    degraded_rows: list[dict] = []
    for spk in speakers:
        for i in range(2):
            uid = f"{spk}-c-{i:04d}"
            utterance_ids.append(uid)
            clean_path = audio_root / f"clean_{uid}.wav"
            _write_wav(clean_path, n_seconds=2.5, freq_hz=220.0)
            clean_rows.append(
                {
                    "utterance_id": uid,
                    "speaker_id": spk,
                    "split": "dev-clean",
                    "audio_path": str(clean_path),
                    "transcript": "hello world",
                    "duration_seconds": 2.5,
                    "sample_rate": SAMPLE_RATE,
                }
            )
            for fam in EXPECTED_FAMILIES:
                deg_path = audio_root / f"deg_{fam}_{uid}.wav"
                _write_wav(deg_path, n_seconds=2.5, freq_hz=220.0 + hash(fam) % 50)
                degraded_rows.append(
                    {
                        "utterance_id": uid,
                        "speaker_id": spk,
                        "split": "dev-clean",
                        "family": fam,
                        "clean_audio_path": str(clean_path),
                        "degraded_audio_path": str(deg_path),
                        "transcript": "hello world",
                        "duration_seconds": 2.5,
                        "sample_rate": SAMPLE_RATE,
                        "dataset_version": "synthetic_test",
                        "degradation_version": "degradation_v1",
                    }
                )

    clean_manifest = tmp_path / "clean.jsonl"
    with clean_manifest.open("w", encoding="utf-8") as f:
        for r in clean_rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    degraded_manifest = tmp_path / "degraded.jsonl"
    with degraded_manifest.open("w", encoding="utf-8") as f:
        for r in degraded_rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    return (
        clean_manifest,
        degraded_manifest,
        _sha256_of_file(clean_manifest),
        _sha256_of_file(degraded_manifest),
    )


def test_paired_dataset_construction_and_item_shape(tmp_path: Path) -> None:
    cm, dm, csha, dsha = _build_synthetic_split(tmp_path)
    ds = PairedDevCleanDataset(
        clean_manifest=cm,
        degraded_manifest=dm,
        clean_sha256=csha,
        degraded_sha256=dsha,
        mode="train",
        sample_rate=SAMPLE_RATE,
        crop_seconds=4.0,
        seed=1234,
    )
    # 2 speakers * 2 utterances * 5 families = 20 paired items.
    assert len(ds) == 20

    item = ds[0]
    assert set(item.keys()) >= {
        "clean", "degraded", "utterance_id", "family", "sample_rate",
    }
    assert isinstance(item["clean"], torch.Tensor)
    assert isinstance(item["degraded"], torch.Tensor)
    assert item["sample_rate"] == SAMPLE_RATE
    expected_len = int(4.0 * SAMPLE_RATE)
    assert item["clean"].shape == (1, expected_len)
    assert item["degraded"].shape == (1, expected_len)
    assert item["clean"].dtype == torch.float32
    assert item["degraded"].dtype == torch.float32
    assert item["family"] in EXPECTED_FAMILIES


def test_paired_dataset_train_random_crop_is_seeded(tmp_path: Path) -> None:
    cm, dm, csha, dsha = _build_synthetic_split(tmp_path)
    ds_a = PairedDevCleanDataset(
        clean_manifest=cm, degraded_manifest=dm,
        clean_sha256=csha, degraded_sha256=dsha,
        mode="train", sample_rate=SAMPLE_RATE, crop_seconds=2.0, seed=42,
    )
    ds_b = PairedDevCleanDataset(
        clean_manifest=cm, degraded_manifest=dm,
        clean_sha256=csha, degraded_sha256=dsha,
        mode="train", sample_rate=SAMPLE_RATE, crop_seconds=2.0, seed=42,
    )
    a = ds_a[0]["degraded"]
    b = ds_b[0]["degraded"]
    assert torch.equal(a, b), "train mode random crop must be deterministic for same seed"


def test_paired_dataset_val_center_crop_is_deterministic(tmp_path: Path) -> None:
    cm, dm, csha, dsha = _build_synthetic_split(tmp_path)
    ds = PairedDevCleanDataset(
        clean_manifest=cm, degraded_manifest=dm,
        clean_sha256=csha, degraded_sha256=dsha,
        mode="val", sample_rate=SAMPLE_RATE, crop_seconds=2.0, seed=1234,
    )
    a = ds[0]["degraded"]
    b = ds[0]["degraded"]
    assert torch.equal(a, b)


def test_paired_dataset_short_audio_is_right_padded(tmp_path: Path) -> None:
    cm, dm, csha, dsha = _build_synthetic_split(tmp_path)
    ds = PairedDevCleanDataset(
        clean_manifest=cm, degraded_manifest=dm,
        clean_sha256=csha, degraded_sha256=dsha,
        mode="val", sample_rate=SAMPLE_RATE,
        crop_seconds=10.0,  # longer than synthetic 2.5s WAVs
        seed=1234,
    )
    item = ds[0]
    expected_len = int(10.0 * SAMPLE_RATE)
    assert item["clean"].shape == (1, expected_len)
    # Trailing samples must be zero-padded.
    tail = item["clean"][0, int(2.5 * SAMPLE_RATE) :]
    assert torch.all(tail == 0.0)


def test_paired_dataset_sha_mismatch_rejected(tmp_path: Path) -> None:
    cm, dm, csha, _ = _build_synthetic_split(tmp_path)
    bad_sha = "0" * 64
    with pytest.raises(ValueError):
        PairedDevCleanDataset(
            clean_manifest=cm, degraded_manifest=dm,
            clean_sha256=csha, degraded_sha256=bad_sha,
            mode="train", sample_rate=SAMPLE_RATE, seed=1234,
        )


def test_paired_dataset_collate_stacks_batch(tmp_path: Path) -> None:
    cm, dm, csha, dsha = _build_synthetic_split(tmp_path)
    ds = PairedDevCleanDataset(
        clean_manifest=cm, degraded_manifest=dm,
        clean_sha256=csha, degraded_sha256=dsha,
        mode="val", sample_rate=SAMPLE_RATE, crop_seconds=2.0, seed=1234,
    )
    batch = PairedDevCleanDataset.collate([ds[0], ds[1], ds[2]])
    assert batch["clean"].shape[0] == 3
    assert batch["degraded"].shape[0] == 3
    assert isinstance(batch["family"], list) and len(batch["family"]) == 3


def test_paired_dataset_invalid_mode_rejected(tmp_path: Path) -> None:
    cm, dm, csha, dsha = _build_synthetic_split(tmp_path)
    with pytest.raises(ValueError):
        PairedDevCleanDataset(
            clean_manifest=cm, degraded_manifest=dm,
            clean_sha256=csha, degraded_sha256=dsha,
            mode="not_a_mode", sample_rate=SAMPLE_RATE, seed=1234,
        )
