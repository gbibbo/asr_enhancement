"""T6.2b — tests for the architecture registry and `spectral_unet_small_v1`.

Requires torch. Login-node Python on datamove1 has no torch; these tests run
inside Apptainer via slurm/jobs/t6_2b_pytest_apptainer.sh.
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

from models import (  # noqa: E402
    SpectralUnetSmallV1,
    build_model,
    get_registered_architectures,
    parameter_count,
)


def test_registry_contains_spectral_unet_small_v1() -> None:
    assert "spectral_unet_small_v1" in get_registered_architectures()


def test_metricgan_is_not_registered() -> None:
    for name in get_registered_architectures():
        assert "metricgan" not in name.lower(), (
            f"MetricGAN+ must not be a trainable architecture: registered={name!r}"
        )


def test_metricgan_build_rejected() -> None:
    with pytest.raises(ValueError):
        build_model("metricgan_plus_pretrained", {})


def test_unknown_architecture_rejected() -> None:
    with pytest.raises(KeyError):
        build_model("does_not_exist_v1", {})


def test_spectral_unet_small_v1_parameter_count_in_budget() -> None:
    model = build_model(
        "spectral_unet_small_v1",
        {
            "sample_rate": 16000,
            "n_fft": 512,
            "hop_length": 128,
            "win_length": 512,
            "window": "hann",
            "target": "bounded_log_mag_ratio_mask",
            "phase": "degraded_pass_through",
        },
    )
    assert isinstance(model, torch.nn.Module)
    p = parameter_count(model)
    assert 200_000 <= p <= 1_000_000, (
        f"spectral_unet_small_v1 parameter count {p} outside [0.2M, 1.0M]"
    )


def test_spectral_unet_small_v1_forward_shape_matches_input() -> None:
    model = build_model(
        "spectral_unet_small_v1",
        {
            "sample_rate": 16000,
            "n_fft": 512,
            "hop_length": 128,
            "win_length": 512,
            "window": "hann",
            "target": "bounded_log_mag_ratio_mask",
            "phase": "degraded_pass_through",
        },
    ).eval()
    x = torch.randn(2, 1, 16000)  # [B=2, C=1, L=1s @ 16kHz]
    with torch.no_grad():
        y = model(x)
    assert y.shape == x.shape, f"expected {tuple(x.shape)}, got {tuple(y.shape)}"


def test_spectral_unet_small_v1_gradient_flows() -> None:
    model = build_model(
        "spectral_unet_small_v1",
        {
            "sample_rate": 16000,
            "n_fft": 512,
            "hop_length": 128,
            "win_length": 512,
            "window": "hann",
            "target": "bounded_log_mag_ratio_mask",
            "phase": "degraded_pass_through",
        },
    )
    model.train()
    x = torch.randn(1, 1, 8000, requires_grad=False)
    y = model(x)
    loss = y.abs().mean()
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.requires_grad]
    assert grads, "no trainable parameters"
    nonzero = [g for g in grads if g is not None and torch.any(g != 0)]
    assert nonzero, "no gradient flowed through any trainable parameter"


def test_spectral_unet_small_v1_rejects_wrong_target() -> None:
    with pytest.raises(ValueError):
        build_model("spectral_unet_small_v1", {"target": "magnitude"})


def test_spectral_unet_small_v1_rejects_wrong_phase() -> None:
    with pytest.raises(ValueError):
        build_model(
            "spectral_unet_small_v1",
            {"target": "bounded_log_mag_ratio_mask", "phase": "predicted"},
        )


def test_spectral_unet_small_v1_rejects_non_hann_window() -> None:
    with pytest.raises(ValueError):
        build_model(
            "spectral_unet_small_v1",
            {
                "target": "bounded_log_mag_ratio_mask",
                "phase": "degraded_pass_through",
                "window": "hamming",
            },
        )


def test_spectral_unet_small_v1_class_constants() -> None:
    assert SpectralUnetSmallV1.EXPECTED_PHASE == "degraded_pass_through"
    assert SpectralUnetSmallV1.EXPECTED_TARGET == "bounded_log_mag_ratio_mask"
