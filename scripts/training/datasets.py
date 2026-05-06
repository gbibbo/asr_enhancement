"""T6.2b — paired clean/degraded dataset over the T6.2a speaker-disjoint split.

Reads the four manifests produced by
`scripts/training/prepare_devclean_speaker_split.py` and verifies their
SHA-256s against the values declared in `configs/training/full_training.yaml`
at construction time.

For each row in the degraded manifest we build a paired item whose input is
the audio at `degraded_audio_path` and whose target is the audio at
`clean_audio_path`. The dataset returns mono float32 tensors at
`sample_rate` (Hz, default 16000) of fixed length
`crop_seconds * sample_rate` (default 4.0 s -> 64000 samples), produced by:
  - train mode: seeded random crop with right-pad to `crop_len`;
  - val mode: deterministic center crop with right-pad to `crop_len`.

This module imports torch and soundfile at module level. It must only be
imported lazily by `scripts/training/train_enhancer.py` (and by the
torch-dependent tests). The trainer's module-level import path must NOT pull
this in — that keeps `--validate-only` runnable on a torch-less login node.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Iterable

import numpy as np
import soundfile as sf
import torch
from torch.utils.data import Dataset


__all__ = ["PairedDevCleanDataset"]


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _load_audio_mono(path: Path) -> tuple[np.ndarray, int]:
    samples, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if samples.ndim == 2:
        samples = samples.mean(axis=1).astype(np.float32, copy=False)
    elif samples.ndim != 1:
        raise ValueError(f"unexpected audio ndim {samples.ndim} for {path}")
    return samples, int(sr)


def _crop_or_pad(
    samples: np.ndarray, target_len: int, offset: int
) -> np.ndarray:
    """Right-pad with zeros to `target_len` after cropping at `offset`.

    `offset` is clamped to a valid range; if `samples` is shorter than
    `target_len` it is right-padded.
    """
    n = samples.shape[0]
    if n >= target_len:
        offset = max(0, min(offset, n - target_len))
        return samples[offset : offset + target_len].astype(np.float32, copy=False)
    out = np.zeros(target_len, dtype=np.float32)
    out[:n] = samples
    return out


class PairedDevCleanDataset(Dataset):
    """Paired clean/degraded items over `devclean_speaker_split_v1`."""

    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CROP_SECONDS = 4.0

    def __init__(
        self,
        clean_manifest: Path,
        degraded_manifest: Path,
        clean_sha256: str,
        degraded_sha256: str,
        mode: str,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        crop_seconds: float = DEFAULT_CROP_SECONDS,
        seed: int = 1234,
        verify_sha: bool = True,
    ) -> None:
        if mode not in ("train", "val"):
            raise ValueError(f"mode must be 'train' or 'val'; got {mode!r}")
        clean_manifest = Path(clean_manifest)
        degraded_manifest = Path(degraded_manifest)
        if not clean_manifest.exists():
            raise FileNotFoundError(f"clean manifest not found: {clean_manifest}")
        if not degraded_manifest.exists():
            raise FileNotFoundError(f"degraded manifest not found: {degraded_manifest}")

        if verify_sha:
            actual_c = _sha256_of_file(clean_manifest)
            if actual_c != clean_sha256:
                raise ValueError(
                    f"clean manifest sha256 mismatch: expected={clean_sha256} "
                    f"actual={actual_c} path={clean_manifest}"
                )
            actual_d = _sha256_of_file(degraded_manifest)
            if actual_d != degraded_sha256:
                raise ValueError(
                    f"degraded manifest sha256 mismatch: expected={degraded_sha256} "
                    f"actual={actual_d} path={degraded_manifest}"
                )

        clean_rows = _read_jsonl(clean_manifest)
        degraded_rows = _read_jsonl(degraded_manifest)

        clean_by_uid: dict[str, dict] = {}
        for r in clean_rows:
            uid = r.get("utterance_id")
            if uid is not None:
                clean_by_uid[str(uid)] = r
        if not clean_by_uid:
            raise ValueError(f"clean manifest has no utterance_id rows: {clean_manifest}")

        items: list[tuple[dict, dict]] = []
        for d in degraded_rows:
            uid = d.get("utterance_id")
            if uid is None:
                continue
            c = clean_by_uid.get(str(uid))
            if c is None:
                # cannot pair without a clean target; skip.
                continue
            items.append((c, d))
        if not items:
            raise ValueError(
                f"no paired items between {clean_manifest} and {degraded_manifest}"
            )

        self.mode = mode
        self.sample_rate = int(sample_rate)
        self.crop_seconds = float(crop_seconds)
        self.crop_len = int(round(self.crop_seconds * self.sample_rate))
        self.seed = int(seed)
        self.clean_manifest = clean_manifest
        self.degraded_manifest = degraded_manifest
        self._items = items

    def __len__(self) -> int:
        return len(self._items)

    def _resolve_offset(self, total_len: int, item_index: int) -> int:
        if total_len <= self.crop_len:
            return 0
        max_offset = total_len - self.crop_len
        if self.mode == "train":
            rng = random.Random((self.seed * 1_000_003) ^ item_index)
            return rng.randint(0, max_offset)
        return max_offset // 2  # val: deterministic center

    def __getitem__(self, idx: int) -> dict:
        clean_row, degraded_row = self._items[idx]
        clean_path = Path(degraded_row.get("clean_audio_path") or clean_row.get("audio_path"))
        degraded_path = Path(degraded_row["degraded_audio_path"])

        clean_samples, clean_sr = _load_audio_mono(clean_path)
        degraded_samples, degraded_sr = _load_audio_mono(degraded_path)

        if clean_sr != self.sample_rate:
            raise ValueError(
                f"clean sample_rate mismatch: expected={self.sample_rate} "
                f"actual={clean_sr} path={clean_path}"
            )
        if degraded_sr != self.sample_rate:
            raise ValueError(
                f"degraded sample_rate mismatch: expected={self.sample_rate} "
                f"actual={degraded_sr} path={degraded_path}"
            )

        # Use the shorter of the two as the alignment reference.
        common_len = min(clean_samples.shape[0], degraded_samples.shape[0])
        clean_samples = clean_samples[:common_len]
        degraded_samples = degraded_samples[:common_len]

        offset = self._resolve_offset(common_len, idx)
        clean_crop = _crop_or_pad(clean_samples, self.crop_len, offset)
        degraded_crop = _crop_or_pad(degraded_samples, self.crop_len, offset)

        clean_t = torch.from_numpy(clean_crop).unsqueeze(0)        # [1, L]
        degraded_t = torch.from_numpy(degraded_crop).unsqueeze(0)  # [1, L]

        return {
            "clean": clean_t,
            "degraded": degraded_t,
            "utterance_id": str(degraded_row.get("utterance_id")),
            "family": str(degraded_row.get("family", "")),
            "sample_rate": self.sample_rate,
        }

    @staticmethod
    def collate(batch: Iterable[dict]) -> dict:
        batch = list(batch)
        clean = torch.stack([b["clean"] for b in batch], dim=0)
        degraded = torch.stack([b["degraded"] for b in batch], dim=0)
        return {
            "clean": clean,
            "degraded": degraded,
            "utterance_id": [b["utterance_id"] for b in batch],
            "family": [b["family"] for b in batch],
            "sample_rate": batch[0]["sample_rate"] if batch else 0,
        }
