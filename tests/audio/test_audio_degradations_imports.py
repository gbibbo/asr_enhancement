from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import libs.common.versions as _versions


def test_degradation_result_importable():
    from libs.audio.degradations import DegradationResult  # noqa: F401


def test_degradation_spec_importable():
    from libs.audio.degradations import DegradationSpec  # noqa: F401


def test_apply_degradation_importable():
    from libs.audio.degradations import apply_degradation  # noqa: F401


def test_get_degradation_importable():
    from libs.audio.degradations import get_degradation  # noqa: F401


def test_degradation_registry_importable():
    from libs.audio.degradations import DEGRADATION_REGISTRY  # noqa: F401


def test_known_degradation_ids_importable():
    from libs.audio.degradations import KNOWN_DEGRADATION_IDS  # noqa: F401


def test_package_init_re_exports_degradation_result():
    from libs.audio import DegradationResult  # noqa: F401


def test_package_init_re_exports_apply_degradation():
    from libs.audio import apply_degradation  # noqa: F401


def test_package_init_re_exports_degradation_registry():
    from libs.audio import DEGRADATION_REGISTRY  # noqa: F401


def test_degradation_result_is_frozen():
    from libs.audio.degradations import DegradationResult

    result = DegradationResult(
        output_path=Path("/tmp/x.wav"),
        degradation_id="broadband_hiss",
        params_applied={"snr_db": 30.0},
        degradation_version="1.0",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.degradation_id = "other"  # type: ignore[misc]


def test_degradation_version_not_hardcoded(tmp_path, monkeypatch):
    from libs.audio.degradations import apply_degradation

    n = int(16000 * 0.5)
    samples = (0.5 * np.sin(2 * np.pi * 440 * np.arange(n) / 16000)).astype(np.float64)
    wav = tmp_path / "input.wav"
    sf.write(wav, samples, 16000)

    monkeypatch.setattr(_versions, "DEGRADATION_VERSION", "SENTINEL")
    result = apply_degradation("broadband_hiss", wav, tmp_path / "out", seed=0)
    assert result.degradation_version == "SENTINEL"
