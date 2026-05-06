"""T6.2 — login-node-safe tests for the GPU device-selection helper.

These tests cover the pure-Python helper added to
`scripts/training/train_enhancer.py` for the T6.2 GPU device-selection
patch (`_resolve_training_device`):

  * cpu_only target resolves to CPU regardless of CUDA availability.
  * gpu_required + CUDA absent ⇒ blocker (errors non-empty).
  * gpu_preferred + CUDA absent + cpu_fallback=True ⇒ resolves to CPU
    (preserves T6.2c/T6.2d cpu-smoke behaviour when ASR_EXPECT_CUDA is
    unset).
  * gpu_preferred + CUDA absent + cpu_fallback=False ⇒ blocker.
  * gpu_preferred + CUDA present ⇒ resolves to CUDA.
  * gpu_required + CUDA present ⇒ resolves to CUDA.
  * **ASR_EXPECT_CUDA=1 + CUDA absent ⇒ blocker** even if cpu_fallback is
    True (this is the T6.2 GPU-Slurm fail-fast guard).

Plus subprocess regression checks asserting:
  * `--validate-only` against `configs/training/full_training.yaml` still
    exits 0 after the patch.
  * `--validate-only` against `configs/training/full_training_gpu_micro.yaml`
    exits 0.
  * `--validate-only --enable-whisper-val` against `full_training.yaml`
    exits 2 (consistency-check blocker, since
    `validation_policy.whisper_validation_enabled` is absent in the full
    config).

Hard scope guards (must remain TRUE):
  * No `import torch`. No `import whisper`. No `import torchaudio`.
  * No `import matplotlib`. No `import scipy`.
  * Tests run on the datamove1 login node and do not exercise CUDA.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_SCRIPT_DIR = REPO_ROOT / "scripts" / "training"
SCRIPT = TRAIN_SCRIPT_DIR / "train_enhancer.py"
FULL_CONFIG = REPO_ROOT / "configs" / "training" / "full_training.yaml"
GPU_MICRO_CONFIG = REPO_ROOT / "configs" / "training" / "full_training_gpu_micro.yaml"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TRAIN_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TRAIN_SCRIPT_DIR))


def _import_train_enhancer():
    return importlib.import_module("train_enhancer")


def _forbid_heavy_imports() -> None:
    forbidden = ("torch", "whisper", "torchaudio", "matplotlib", "scipy")
    for name in forbidden:
        assert name not in sys.modules, (
            f"forbidden heavy import already loaded: {name!r}; T6.2 device-selection "
            f"helper must stay login-node-safe (no torch/whisper/torchaudio/"
            f"matplotlib/scipy)."
        )


# ---------------------------------------------------------------------------
# _resolve_training_device — pure helper, no torch import.
# ---------------------------------------------------------------------------
def test_cpu_only_resolves_cpu_regardless_of_cuda() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()
    _forbid_heavy_imports()

    cfg = {"hardware": {"target": "cpu_only", "cpu_fallback": False}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=False, expect_cuda=False)
    assert dev == "cpu"
    assert errs == []
    dev2, errs2 = te._resolve_training_device(cfg, cuda_available=True, expect_cuda=False)
    assert dev2 == "cpu"
    assert errs2 == []


def test_gpu_required_without_cuda_blocks() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_required", "cpu_fallback": False}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=False, expect_cuda=False)
    assert dev == "cpu"  # by convention; caller must inspect errors
    assert errs and any("gpu_required" in e for e in errs)


def test_gpu_required_with_cuda_resolves_cuda() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_required", "cpu_fallback": False}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=True, expect_cuda=False)
    assert dev == "cuda"
    assert errs == []


def test_gpu_preferred_without_cuda_with_fallback_resolves_cpu() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_preferred", "cpu_fallback": True}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=False, expect_cuda=False)
    assert dev == "cpu"
    assert errs == []


def test_gpu_preferred_without_cuda_no_fallback_blocks() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_preferred", "cpu_fallback": False}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=False, expect_cuda=False)
    assert dev == "cpu"
    assert errs and any("gpu_preferred" in e for e in errs)


def test_gpu_preferred_with_cuda_resolves_cuda() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_preferred", "cpu_fallback": True}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=True, expect_cuda=False)
    assert dev == "cuda"
    assert errs == []


def test_expect_cuda_blocks_when_cuda_absent_even_with_cpu_fallback() -> None:
    """T6.2 GPU Slurm jobs export ASR_EXPECT_CUDA=1; the helper must NOT
    silently fall back to CPU even if the config's cpu_fallback is True."""
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_preferred", "cpu_fallback": True}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=False, expect_cuda=True)
    assert dev == "cpu"
    assert errs and any("ASR_EXPECT_CUDA" in e for e in errs)


def test_expect_cuda_passes_when_cuda_available() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"hardware": {"target": "gpu_preferred", "cpu_fallback": True}}
    dev, errs = te._resolve_training_device(cfg, cuda_available=True, expect_cuda=True)
    assert dev == "cuda"
    assert errs == []


def test_missing_hardware_block_resolves_cpu() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    dev, errs = te._resolve_training_device({}, cuda_available=False, expect_cuda=False)
    assert dev == "cpu"
    assert errs == []


# ---------------------------------------------------------------------------
# Subprocess --validate-only regression guards.
# ---------------------------------------------------------------------------
def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def test_validate_only_full_training_yaml_still_passes() -> None:
    _forbid_heavy_imports()
    assert SCRIPT.exists(), f"script missing: {SCRIPT}"
    assert FULL_CONFIG.exists(), f"config missing: {FULL_CONFIG}"
    cp = _run([sys.executable, str(SCRIPT), "--config", str(FULL_CONFIG), "--validate-only"])
    assert cp.returncode == 0, (
        f"validate-only on full_training.yaml failed after device patch: "
        f"rc={cp.returncode}\nstdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "OK:" in cp.stdout


def test_validate_only_full_training_yaml_with_enable_whisper_val_blocks() -> None:
    _forbid_heavy_imports()
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--enable-whisper-val",
    ])
    assert cp.returncode == 2, (
        f"expected consistency-check blocker; got rc={cp.returncode}\n"
        f"stdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "whisper-cli-consistency" in cp.stderr


def test_validate_only_gpu_micro_yaml_passes() -> None:
    _forbid_heavy_imports()
    assert GPU_MICRO_CONFIG.exists(), f"GPU micro config missing: {GPU_MICRO_CONFIG}"
    cp = _run([sys.executable, str(SCRIPT), "--config", str(GPU_MICRO_CONFIG), "--validate-only"])
    assert cp.returncode == 0, (
        f"validate-only on full_training_gpu_micro.yaml failed: "
        f"rc={cp.returncode}\nstdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "OK:" in cp.stdout


# ---------------------------------------------------------------------------
# Final guard: this module must not have pulled in heavy deps.
# ---------------------------------------------------------------------------
def test_no_heavy_imports_in_module() -> None:
    _forbid_heavy_imports()
    _import_train_enhancer()
    _forbid_heavy_imports()
