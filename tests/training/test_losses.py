"""T6.2b — tests for the composite reconstruction loss.

Requires torch. Login-node Python on datamove1 has no torch; these tests
run inside Apptainer via slurm/jobs/t6_2b_pytest_apptainer.sh.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts" / "training"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import torch  # noqa: E402

from losses import (  # noqa: E402
    CompositeReconstructionLoss,
    L1LogMagLoss,
    MultiResolutionSTFTLoss,
)


def _make_pair(seed: int = 0, length: int = 16000):
    g = torch.Generator().manual_seed(seed)
    y = torch.randn(2, 1, length, generator=g)
    yhat = y + 0.05 * torch.randn(2, 1, length, generator=g)
    return yhat, y


def test_l1_log_mag_loss_finite_and_nonneg() -> None:
    yhat, y = _make_pair(seed=1)
    loss_fn = L1LogMagLoss()
    val = loss_fn(yhat, y)
    assert val.dim() == 0
    assert torch.isfinite(val)
    assert float(val.item()) >= 0.0


def test_l1_log_mag_loss_zero_for_identical() -> None:
    y = torch.randn(1, 1, 8000)
    val = L1LogMagLoss()(y, y)
    assert float(val.item()) < 1.0e-5


def test_multi_resolution_stft_loss_finite() -> None:
    yhat, y = _make_pair(seed=2)
    loss_fn = MultiResolutionSTFTLoss()
    val = loss_fn(yhat, y)
    assert val.dim() == 0
    assert torch.isfinite(val)
    assert float(val.item()) >= 0.0


def test_composite_loss_returns_scalar_and_components() -> None:
    yhat, y = _make_pair(seed=3)
    loss_fn = CompositeReconstructionLoss(l1_log_mag_w=1.0, mrstft_w=0.5)
    val, components = loss_fn(yhat, y)
    assert val.dim() == 0
    assert torch.isfinite(val)
    assert float(val.item()) >= 0.0
    assert set(components.keys()) == {"l1_log_mag", "mrstft"}
    for c in components.values():
        assert torch.isfinite(c)


def test_composite_loss_weighted_sum_matches_components() -> None:
    yhat, y = _make_pair(seed=4)
    loss_fn = CompositeReconstructionLoss(l1_log_mag_w=1.0, mrstft_w=0.5)
    val, components = loss_fn(yhat, y)
    expected = 1.0 * float(components["l1_log_mag"].item()) + 0.5 * float(
        components["mrstft"].item()
    )
    assert float(val.item()) == pytest.approx(expected, rel=1e-5, abs=1e-6)


def test_composite_loss_gradient_flows() -> None:
    yhat, y = _make_pair(seed=5)
    yhat = yhat.clone().detach().requires_grad_(True)
    loss_fn = CompositeReconstructionLoss(l1_log_mag_w=1.0, mrstft_w=0.5)
    val, _ = loss_fn(yhat, y)
    val.backward()
    assert yhat.grad is not None
    assert torch.any(yhat.grad != 0.0)


def test_composite_loss_decreases_when_yhat_approaches_y() -> None:
    y = torch.randn(1, 1, 8000)
    yhat_far = y + 0.5 * torch.randn(1, 1, 8000)
    yhat_close = y + 0.01 * torch.randn(1, 1, 8000)
    loss_fn = CompositeReconstructionLoss(l1_log_mag_w=1.0, mrstft_w=0.5)
    far_val, _ = loss_fn(yhat_far, y)
    close_val, _ = loss_fn(yhat_close, y)
    assert float(close_val.item()) < float(far_val.item())
