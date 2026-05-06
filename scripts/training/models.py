"""T6.2b — architecture registry and `spectral_unet_small_v1` implementation.

PyTorch primitives only. No SpeechBrain, no audio-domain libraries.

Architecture decision is recorded in configs/training/full_training.yaml under
`model:` (T6.2a). This module instantiates that architecture; it does NOT
re-decide topology — the configurable hyperparameters
(`sample_rate`, `n_fft`, `hop_length`, `win_length`, `window`, `target`,
`phase`) flow in from `cfg.model.params`.

Public API:
  build_model(architecture: str, params: dict) -> nn.Module
  get_registered_architectures() -> tuple[str, ...]

The trainer imports this module lazily (never at module import time of
scripts/training/train_enhancer.py) so that login-node `--validate-only`
does not require torch.
"""
from __future__ import annotations

import math
from typing import Callable

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Architecture registry
# ---------------------------------------------------------------------------

_ARCHITECTURE_REGISTRY: dict[str, Callable[[dict], nn.Module]] = {}


def register_architecture(name: str) -> Callable[[Callable[[dict], nn.Module]], Callable[[dict], nn.Module]]:
    """Decorator: register an architecture builder under `name`."""

    def _decorator(fn: Callable[[dict], nn.Module]) -> Callable[[dict], nn.Module]:
        if name in _ARCHITECTURE_REGISTRY:
            raise ValueError(f"architecture already registered: {name!r}")
        if "metricgan" in name.lower():
            raise ValueError(
                f"MetricGAN+ must not be registered as a trainable architecture: {name!r}"
            )
        _ARCHITECTURE_REGISTRY[name] = fn
        return fn

    return _decorator


def build_model(architecture: str, params: dict) -> nn.Module:
    """Build a model for `architecture` from `params` (cfg.model.params).

    Raises KeyError if the architecture is not registered.
    """
    if "metricgan" in str(architecture).lower():
        raise ValueError(
            f"MetricGAN+ is not a trainable architecture: {architecture!r}"
        )
    try:
        builder = _ARCHITECTURE_REGISTRY[architecture]
    except KeyError as exc:
        raise KeyError(
            f"unknown architecture {architecture!r}; "
            f"registered: {sorted(_ARCHITECTURE_REGISTRY)}"
        ) from exc
    return builder(params or {})


def get_registered_architectures() -> tuple[str, ...]:
    return tuple(sorted(_ARCHITECTURE_REGISTRY))


# ---------------------------------------------------------------------------
# spectral_unet_small_v1
# ---------------------------------------------------------------------------


class _GnAct(nn.Module):
    """GroupNorm + GELU. GroupNorm groups capped to gcd(channels, 8)."""

    def __init__(self, channels: int) -> None:
        super().__init__()
        groups = max(1, math.gcd(channels, 8))
        self.norm = nn.GroupNorm(num_groups=groups, num_channels=channels)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.norm(x))


class _EncBlock(nn.Module):
    """Conv2d(stride=2) + GroupNorm + GELU."""

    def __init__(self, in_c: int, out_c: int) -> None:
        super().__init__()
        self.conv = nn.Conv2d(in_c, out_c, kernel_size=3, stride=2, padding=1)
        self.gnact = _GnAct(out_c)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.gnact(self.conv(x))


class _DecBlock(nn.Module):
    """ConvTranspose2d(stride=2) + GroupNorm + GELU + skip-cat + Conv2d + GroupNorm + GELU."""

    def __init__(self, in_c: int, out_c: int, skip_c: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(
            in_c, out_c, kernel_size=4, stride=2, padding=1
        )
        self.gnact_up = _GnAct(out_c)
        self.skip_conv = nn.Conv2d(out_c + skip_c, out_c, kernel_size=3, padding=1)
        self.gnact_skip = _GnAct(out_c)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        u = self.gnact_up(self.up(x))
        # Pad u to skip's spatial dims if a stride/odd dim caused a 1-pixel
        # mismatch (shouldn't happen with our explicit 16x padding, but guard).
        if u.shape[-1] != skip.shape[-1] or u.shape[-2] != skip.shape[-2]:
            u = F.pad(
                u,
                (
                    0, max(0, skip.shape[-1] - u.shape[-1]),
                    0, max(0, skip.shape[-2] - u.shape[-2]),
                ),
            )
            u = u[..., : skip.shape[-2], : skip.shape[-1]]
        cat = torch.cat([u, skip], dim=1)
        return self.gnact_skip(self.skip_conv(cat))


class SpectralUnetSmallV1(nn.Module):
    """Small log-magnitude U-Net predicting a bounded ratio mask.

    Operates on STFT magnitude [B, 1, F, T] of the degraded waveform; predicts
    a bounded mask M in [0, mask_max], multiplies the degraded magnitude by
    M, and reconstructs the waveform by combining with the degraded phase
    (configured `phase: degraded_pass_through`).

    Channel widths: 1 -> 16 -> 32 -> 64 -> 96, bottleneck 96 -> 96.
    Parameter count target: 0.2M-1.0M.
    """

    EXPECTED_PHASE = "degraded_pass_through"
    EXPECTED_TARGET = "bounded_log_mag_ratio_mask"

    def __init__(
        self,
        sample_rate: int = 16000,
        n_fft: int = 512,
        hop_length: int = 128,
        win_length: int = 512,
        mask_max: float = 2.0,
        log_eps: float = 1.0e-7,
    ) -> None:
        super().__init__()
        self.sample_rate = int(sample_rate)
        self.n_fft = int(n_fft)
        self.hop_length = int(hop_length)
        self.win_length = int(win_length)
        self.mask_max = float(mask_max)
        self.log_eps = float(log_eps)
        self._pad_multiple = 16  # 4 down-samplings

        chs = (16, 32, 64, 96)
        self.enc1 = _EncBlock(1, chs[0])      # /2
        self.enc2 = _EncBlock(chs[0], chs[1])  # /4
        self.enc3 = _EncBlock(chs[1], chs[2])  # /8
        self.enc4 = _EncBlock(chs[2], chs[3])  # /16

        self.bottleneck = nn.Sequential(
            nn.Conv2d(chs[3], chs[3], kernel_size=3, padding=1),
            _GnAct(chs[3]),
        )

        self.dec4 = _DecBlock(chs[3], chs[2], skip_c=chs[2])  # /8
        self.dec3 = _DecBlock(chs[2], chs[1], skip_c=chs[1])  # /4
        self.dec2 = _DecBlock(chs[1], chs[0], skip_c=chs[0])  # /2
        # final upsample back to original (no skip at this level)
        self.up_final = nn.ConvTranspose2d(
            chs[0], chs[0], kernel_size=4, stride=2, padding=1
        )
        self.gnact_final = _GnAct(chs[0])
        self.head = nn.Conv2d(chs[0], 1, kernel_size=1)

        # buffer holds a Hann window cached on the right device/dtype
        self.register_buffer(
            "_window",
            torch.hann_window(self.win_length, dtype=torch.float32),
            persistent=False,
        )

    @staticmethod
    def _pad_to_multiple(x: torch.Tensor, k: int) -> tuple[torch.Tensor, int, int]:
        f, t = x.shape[-2], x.shape[-1]
        pf = (k - f % k) % k
        pt = (k - t % k) % k
        if pf or pt:
            x = F.pad(x, (0, pt, 0, pf))
        return x, f, t

    def _u_net(self, x: torch.Tensor) -> torch.Tensor:
        x_pad, f, t = self._pad_to_multiple(x, self._pad_multiple)
        s1 = self.enc1(x_pad)   # /2
        s2 = self.enc2(s1)      # /4
        s3 = self.enc3(s2)      # /8
        s4 = self.enc4(s3)      # /16
        b = self.bottleneck(s4)
        d4 = self.dec4(b, s3)
        d3 = self.dec3(d4, s2)
        d2 = self.dec2(d3, s1)
        u_final = self.gnact_final(self.up_final(d2))
        logits = self.head(u_final)
        return logits[..., :f, :t]

    def forward(self, waveform: torch.Tensor) -> torch.Tensor:
        """Enhance a [B, 1, L] waveform. Output shape == input shape."""
        if waveform.dim() != 3 or waveform.size(1) != 1:
            raise ValueError(
                f"SpectralUnetSmallV1 expects [B, 1, L]; got {tuple(waveform.shape)}"
            )
        b, _, length = waveform.shape

        window = self._window.to(device=waveform.device, dtype=waveform.dtype)
        spec = torch.stft(
            waveform.squeeze(1),
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window=window,
            center=True,
            pad_mode="reflect",
            normalized=False,
            onesided=True,
            return_complex=True,
        )  # [B, F, T]
        mag = spec.abs()
        log_mag = torch.log(mag + self.log_eps).unsqueeze(1)  # [B, 1, F, T]

        logits = self._u_net(log_mag).squeeze(1)  # [B, F, T]
        mask = self.mask_max * torch.sigmoid(logits)

        enhanced_mag = mask * mag
        # Use degraded phase: spec / (mag + eps).
        unit_phase = spec / (mag + self.log_eps)
        enhanced_complex = enhanced_mag * unit_phase

        waveform_out = torch.istft(
            enhanced_complex,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window=window,
            center=True,
            normalized=False,
            onesided=True,
            length=length,
        )
        return waveform_out.unsqueeze(1)


@register_architecture("spectral_unet_small_v1")
def _build_spectral_unet_small_v1(params: dict) -> nn.Module:
    target = str(params.get("target", SpectralUnetSmallV1.EXPECTED_TARGET))
    if target != SpectralUnetSmallV1.EXPECTED_TARGET:
        raise ValueError(
            f"spectral_unet_small_v1 supports target="
            f"{SpectralUnetSmallV1.EXPECTED_TARGET!r}; got {target!r}"
        )
    phase = str(params.get("phase", SpectralUnetSmallV1.EXPECTED_PHASE))
    if phase != SpectralUnetSmallV1.EXPECTED_PHASE:
        raise ValueError(
            f"spectral_unet_small_v1 supports phase="
            f"{SpectralUnetSmallV1.EXPECTED_PHASE!r}; got {phase!r}"
        )
    window = str(params.get("window", "hann"))
    if window != "hann":
        raise ValueError(
            f"spectral_unet_small_v1 supports window='hann'; got {window!r}"
        )
    return SpectralUnetSmallV1(
        sample_rate=int(params.get("sample_rate", 16000)),
        n_fft=int(params.get("n_fft", 512)),
        hop_length=int(params.get("hop_length", 128)),
        win_length=int(params.get("win_length", 512)),
    )


def parameter_count(model: nn.Module) -> int:
    """Trainable parameter count."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


__all__ = [
    "build_model",
    "get_registered_architectures",
    "register_architecture",
    "parameter_count",
    "SpectralUnetSmallV1",
]
