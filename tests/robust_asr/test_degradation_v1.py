"""tests/robust_asr/test_degradation_v1.py — P1.4 §9 Actions 4 + ID/OOD disjointness."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from libs.audio.degradations import (  # noqa: E402
    SAMPLE_FUNCTIONS,
    V347_FAMILIES,
    DEGRADATION_VERSION,
    sample_clean,
)


SR = 16000


@pytest.fixture(scope="module")
def fixture_wav(tmp_path_factory):
    rng = np.random.default_rng(42)
    n = SR * 3
    t = np.arange(n) / SR
    base = 0.3 * np.sin(2 * np.pi * 440.0 * t).astype(np.float64)
    base += 0.05 * rng.standard_normal(n)
    base = np.clip(base, -1.0, 1.0)
    pcm = (base * 32767.0).astype(np.int16)
    p = tmp_path_factory.mktemp("p1_4") / "fixture.wav"
    sf.write(str(p), pcm, SR, subtype="PCM_16")
    return str(p)


@pytest.fixture(scope="module")
def cfg():
    cfg_path = REPO / "configs" / "robust_asr" / "degradation_v1.yaml"
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _params_for(family: str, tier: str, cfg: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    tc = cfg["families_params"][family][tier]
    if family == "clean":
        return {}
    if family == "cafe_noise":
        return {
            "snr_db": float(rng.uniform(tc["snr_db_min"], tc["snr_db_max"])),
            "bandpass_low_hz": float(tc["bandpass_low_hz"]),
            "bandpass_high_hz": float(tc["bandpass_high_hz"]),
            "bandpass_order": int(tc["bandpass_order"]),
        }
    if family == "phone_band":
        return {
            "bandpass_low_hz": float(tc["bandpass_low_hz"]),
            "bandpass_high_hz": float(tc["bandpass_high_hz"]),
            "bandpass_order": int(tc["bandpass_order"]),
            "target_sr_hz": int(tc["target_sr_hz"]),
            "bit_depth": int(tc["bit_depth"]),
        }
    if family == "far_field_room":
        return {
            "rt60_s": float(rng.uniform(tc["rt60_s_min"], tc["rt60_s_max"])),
            "mic_distance_m": float(
                rng.uniform(tc["mic_distance_m_min"], tc["mic_distance_m_max"])
            ),
        }
    if family == "muffled_lowpass":
        return {
            "lowpass_hz": float(rng.uniform(tc["lowpass_hz_min"], tc["lowpass_hz_max"])),
            "attenuation_db": float(
                rng.uniform(tc["attenuation_db_min"], tc["attenuation_db_max"])
            ),
            "lowpass_order": int(tc["lowpass_order"]),
        }
    raise AssertionError(family)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rms(arr: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(arr.astype(np.float64)))))


def _clip_ratio(arr: np.ndarray) -> float:
    return float(np.mean(np.abs(arr) >= 0.999))


@pytest.mark.parametrize("family", list(V347_FAMILIES))
def test_metadata_fields_present(family, fixture_wav, cfg, tmp_path):
    seed = int(hashlib.sha256(f"{family}|test".encode()).digest()[:8].hex(), 16)
    params = _params_for(family, "id", cfg, seed)
    out_path = str(tmp_path / f"{family}.wav")
    if family == "clean":
        meta = sample_clean(fixture_wav, fixture_wav, seed, params)
    else:
        meta = SAMPLE_FUNCTIONS[family](fixture_wav, out_path, seed, params)
    expected = {
        "condition_family",
        "random_seed",
        "snr_db",
        "rir_id_or_null",
        "filter_params_json",
        "source_audio_sha256",
        "output_audio_sha256",
    }
    assert set(meta.keys()) >= expected, f"missing keys for {family}: {expected - set(meta.keys())}"
    assert meta["condition_family"] == family
    assert isinstance(meta["random_seed"], int)
    json.loads(meta["filter_params_json"])  # parses


@pytest.mark.parametrize("family", [f for f in V347_FAMILIES if f != "clean"])
def test_rms_above_threshold(family, fixture_wav, cfg, tmp_path):
    seed = int(hashlib.sha256(f"{family}|rms".encode()).digest()[:8].hex(), 16)
    params = _params_for(family, "id", cfg, seed)
    out_path = str(tmp_path / f"{family}.wav")
    SAMPLE_FUNCTIONS[family](fixture_wav, out_path, seed, params)
    samples, sr = sf.read(out_path, dtype="float32", always_2d=False)
    assert sr == SR
    assert _rms(samples) >= 1e-6, f"{family}: rms below 1e-6"


@pytest.mark.parametrize("family", [f for f in V347_FAMILIES if f != "clean"])
def test_clipping_ratio_below_half(family, fixture_wav, cfg, tmp_path):
    seed = int(hashlib.sha256(f"{family}|clip".encode()).digest()[:8].hex(), 16)
    params = _params_for(family, "id", cfg, seed)
    out_path = str(tmp_path / f"{family}.wav")
    SAMPLE_FUNCTIONS[family](fixture_wav, out_path, seed, params)
    samples, _sr = sf.read(out_path, dtype="float32", always_2d=False)
    assert _clip_ratio(samples) < 0.5, f"{family}: clipping_ratio >= 0.5"


@pytest.mark.parametrize("family", [f for f in V347_FAMILIES if f != "clean"])
def test_source_audio_sha256_matches(family, fixture_wav, cfg, tmp_path):
    seed = int(hashlib.sha256(f"{family}|sha".encode()).digest()[:8].hex(), 16)
    params = _params_for(family, "id", cfg, seed)
    out_path = str(tmp_path / f"{family}.wav")
    meta = SAMPLE_FUNCTIONS[family](fixture_wav, out_path, seed, params)
    src_sha = _sha256_file(fixture_wav)
    assert meta["source_audio_sha256"] == src_sha


def test_clean_output_equals_source_sha(fixture_wav):
    seed = 12345
    meta = sample_clean(fixture_wav, fixture_wav, seed, {})
    src_sha = _sha256_file(fixture_wav)
    assert meta["source_audio_sha256"] == src_sha
    assert meta["output_audio_sha256"] == src_sha
    assert meta["condition_family"] == "clean"


@pytest.mark.parametrize("family", [f for f in V347_FAMILIES if f != "clean"])
def test_determinism(family, fixture_wav, cfg, tmp_path):
    seed = int(hashlib.sha256(f"{family}|det".encode()).digest()[:8].hex(), 16)
    params = _params_for(family, "id", cfg, seed)
    p1 = str(tmp_path / f"{family}_a.wav")
    p2 = str(tmp_path / f"{family}_b.wav")
    SAMPLE_FUNCTIONS[family](fixture_wav, p1, seed, params)
    SAMPLE_FUNCTIONS[family](fixture_wav, p2, seed, params)
    assert _sha256_file(p1) == _sha256_file(p2), f"{family}: not deterministic for fixed seed"


def test_id_ood_param_disjoint_for_continuous_families(cfg):
    """ID and OOD-param ranges must be disjoint for cafe_noise, far_field_room, muffled_lowpass."""
    fp = cfg["families_params"]
    # cafe_noise: snr_db ranges
    a = (fp["cafe_noise"]["id"]["snr_db_min"], fp["cafe_noise"]["id"]["snr_db_max"])
    b = (
        fp["cafe_noise"]["ood_param"]["snr_db_min"],
        fp["cafe_noise"]["ood_param"]["snr_db_max"],
    )
    assert b[1] < a[0] or a[1] < b[0], f"cafe_noise snr ranges overlap: id={a} ood={b}"
    # far_field_room: rt60_s ranges
    a = (fp["far_field_room"]["id"]["rt60_s_min"], fp["far_field_room"]["id"]["rt60_s_max"])
    b = (
        fp["far_field_room"]["ood_param"]["rt60_s_min"],
        fp["far_field_room"]["ood_param"]["rt60_s_max"],
    )
    assert b[1] < a[0] or a[1] < b[0], f"far_field_room rt60 ranges overlap"
    a = (
        fp["far_field_room"]["id"]["mic_distance_m_min"],
        fp["far_field_room"]["id"]["mic_distance_m_max"],
    )
    b = (
        fp["far_field_room"]["ood_param"]["mic_distance_m_min"],
        fp["far_field_room"]["ood_param"]["mic_distance_m_max"],
    )
    assert b[1] < a[0] or a[1] < b[0], f"far_field_room mic_distance ranges overlap"
    # muffled_lowpass: lowpass_hz ranges
    a = (
        fp["muffled_lowpass"]["id"]["lowpass_hz_min"],
        fp["muffled_lowpass"]["id"]["lowpass_hz_max"],
    )
    b = (
        fp["muffled_lowpass"]["ood_param"]["lowpass_hz_min"],
        fp["muffled_lowpass"]["ood_param"]["lowpass_hz_max"],
    )
    assert b[1] < a[0] or a[1] < b[0], f"muffled_lowpass lowpass ranges overlap"


def test_phone_band_ood_changes_bit_depth(cfg):
    id_bd = cfg["families_params"]["phone_band"]["id"]["bit_depth"]
    ood_bd = cfg["families_params"]["phone_band"]["ood_param"]["bit_depth"]
    assert ood_bd < id_bd, f"phone_band ood bit_depth must be < id ({ood_bd} >= {id_bd})"
