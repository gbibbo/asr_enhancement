"""T6.2b — composite reconstruction loss for spectral_unet_small_v1 training.

Defined in pure PyTorch primitives (`torch.stft`, `torch.nn.functional.l1_loss`).
Implements:
  - L1LogMagLoss: L1 distance between log-magnitude STFTs.
  - MultiResolutionSTFTLoss: average L1 (magnitude + log-magnitude) over
    multiple (n_fft, hop, win) resolutions.
  - CompositeReconstructionLoss: weighted sum of the two, returning a scalar
    plus a per-component dict for logging.

This module imports torch at module level. It must only be imported
lazily (from inside the trainer's `_run_training` and from the tests).
The trainer's module-level import path must NOT pull this in.

Reference: configs/training/full_training.yaml `model.loss_plan` (T6.2a):
  primary: l1_log_magnitude (weight 1.0)
  secondary: multi_resolution_stft (weight 0.5)
"""
from __future__ import annotations

from typing import Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


def _stft_magnitude(
    waveform: torch.Tensor,
    n_fft: int,
    hop_length: int,
    win_length: int,
) -> torch.Tensor:
    """Magnitude STFT for a [B, 1, L] or [B, L] waveform. Returns [B, F, T]."""
    if waveform.dim() == 3:
        if waveform.size(1) != 1:
            waveform = waveform.mean(dim=1, keepdim=False)
        else:
            waveform = waveform.squeeze(1)
    elif waveform.dim() != 2:
        raise ValueError(
            f"_stft_magnitude expects [B, 1, L] or [B, L]; got {tuple(waveform.shape)}"
        )

    window = torch.hann_window(win_length, device=waveform.device, dtype=waveform.dtype)
    spec = torch.stft(
        waveform,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        center=True,
        pad_mode="reflect",
        normalized=False,
        onesided=True,
        return_complex=True,
    )
    return spec.abs()


class L1LogMagLoss(nn.Module):
    """L1(log(|STFT(yhat)| + eps), log(|STFT(y)| + eps))."""

    def __init__(
        self,
        n_fft: int = 512,
        hop_length: int = 128,
        win_length: int = 512,
        eps: float = 1.0e-7,
    ) -> None:
        super().__init__()
        self.n_fft = int(n_fft)
        self.hop_length = int(hop_length)
        self.win_length = int(win_length)
        self.eps = float(eps)

    def forward(self, yhat: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        mag_hat = _stft_magnitude(yhat, self.n_fft, self.hop_length, self.win_length)
        mag = _stft_magnitude(y, self.n_fft, self.hop_length, self.win_length)
        log_hat = torch.log(mag_hat + self.eps)
        log_y = torch.log(mag + self.eps)
        return F.l1_loss(log_hat, log_y)


class MultiResolutionSTFTLoss(nn.Module):
    """Average L1 over multiple STFT resolutions (magnitude + log-magnitude)."""

    DEFAULT_RESOLUTIONS: tuple[tuple[int, int, int], ...] = (
        (512, 128, 512),
        (1024, 256, 1024),
        (256, 64, 256),
    )

    def __init__(
        self,
        resolutions: Sequence[tuple[int, int, int]] | None = None,
        eps: float = 1.0e-7,
    ) -> None:
        super().__init__()
        self.resolutions = tuple(resolutions) if resolutions else self.DEFAULT_RESOLUTIONS
        self.eps = float(eps)

    def forward(self, yhat: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        total = yhat.new_zeros(())
        for n_fft, hop, win in self.resolutions:
            mag_hat = _stft_magnitude(yhat, n_fft, hop, win)
            mag_y = _stft_magnitude(y, n_fft, hop, win)
            l1_mag = F.l1_loss(mag_hat, mag_y)
            l1_log = F.l1_loss(
                torch.log(mag_hat + self.eps),
                torch.log(mag_y + self.eps),
            )
            total = total + 0.5 * (l1_mag + l1_log)
        return total / max(len(self.resolutions), 1)


class CompositeReconstructionLoss(nn.Module):
    """Weighted L1 log-magnitude + multi-resolution STFT loss.

    Returns (scalar_loss, component_dict).
    """

    def __init__(
        self,
        l1_log_mag_w: float = 1.0,
        mrstft_w: float = 0.5,
        n_fft: int = 512,
        hop_length: int = 128,
        win_length: int = 512,
        mrstft_resolutions: Sequence[tuple[int, int, int]] | None = None,
        eps: float = 1.0e-7,
    ) -> None:
        super().__init__()
        self.l1_log_mag_w = float(l1_log_mag_w)
        self.mrstft_w = float(mrstft_w)
        self.l1_log_mag = L1LogMagLoss(
            n_fft=n_fft, hop_length=hop_length, win_length=win_length, eps=eps
        )
        self.mrstft = MultiResolutionSTFTLoss(
            resolutions=mrstft_resolutions, eps=eps
        )

    def forward(
        self, yhat: torch.Tensor, y: torch.Tensor
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        l1_log_val = self.l1_log_mag(yhat, y)
        mrstft_val = self.mrstft(yhat, y)
        loss = self.l1_log_mag_w * l1_log_val + self.mrstft_w * mrstft_val
        return loss, {"l1_log_mag": l1_log_val.detach(), "mrstft": mrstft_val.detach()}


__all__ = [
    "L1LogMagLoss",
    "MultiResolutionSTFTLoss",
    "CompositeReconstructionLoss",
]
