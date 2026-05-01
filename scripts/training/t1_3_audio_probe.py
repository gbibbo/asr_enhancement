#!/usr/bin/env python3
"""T1.3 audio processing probe.

Generates a synthetic WAV, processes it with apply_preset("denoise"),
validates the output, checks import origins and user-site isolation,
then writes JSON evidence to --out.

Exit 0 on full success; exit 1 on any failure.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import site
import sys
from pathlib import Path

_USER_LOCAL_MARKERS = [
    "/.local/",
    "/.local/lib/python",
    "/mnt/fast/nobackup/users/gb0048/.local",
    "/home/gb0048/.local",
]

_REPO = "/mnt/fast/nobackup/users/gb0048/asr_enhancement"
_PREFIX = (
    "/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training"
    "/python_env/site-packages-py310"
)
_OPT_CONDA = "/opt/conda"


def _has_user_local(path_str: str) -> bool:
    return any(m in path_str for m in _USER_LOCAL_MARKERS)


def _approved_third_party(path_str: str) -> bool:
    return path_str.startswith(_OPT_CONDA) or path_str.startswith(_PREFIX)


def main() -> None:
    parser = argparse.ArgumentParser(description="T1.3 audio processing probe")
    parser.add_argument("--out", required=True, type=Path, help="JSON evidence output path")
    parser.add_argument("--input-wav", required=True, type=Path, help="Synthetic input WAV path")
    parser.add_argument("--output-dir", required=True, type=Path, help="apply_preset output directory")
    args = parser.parse_args()

    evidence: dict = {"task": "T1.3", "success": False}
    failures: list[str] = []

    # --- Python runtime ---
    evidence["python_executable"] = sys.executable
    evidence["python_version"] = sys.version.split()[0]
    evidence["pythonnousersite_env"] = os.environ.get("PYTHONNOUSERSITE", "NOT_SET")

    # --- User-site isolation ---
    evidence["site_enable_user_site"] = getattr(site, "ENABLE_USER_SITE", None)
    evidence["site_user_site"] = getattr(site, "USER_SITE", None)
    evidence["site_user_site_in_sys_path"] = bool(
        hasattr(site, "USER_SITE") and site.USER_SITE and site.USER_SITE in sys.path
    )
    user_local_in_syspath = [p for p in sys.path if _has_user_local(p)]
    evidence["user_local_syspath_entries"] = user_local_in_syspath

    if evidence["pythonnousersite_env"] != "1":
        failures.append(
            f"PYTHONNOUSERSITE is not '1': {evidence['pythonnousersite_env']}"
        )
    if evidence["site_enable_user_site"]:
        failures.append("site.ENABLE_USER_SITE is True")
    if evidence["site_user_site_in_sys_path"]:
        failures.append("USER_SITE is in sys.path")
    if user_local_in_syspath:
        failures.append(f"user-local entries in sys.path: {user_local_in_syspath}")

    # --- Third-party imports ---
    import numpy as np
    import scipy
    import soundfile as sf

    evidence["numpy_origin"] = str(np.__file__)
    evidence["scipy_origin"] = str(scipy.__file__)
    evidence["soundfile_origin"] = str(sf.__file__)

    # --- Project import ---
    from libs.audio_pipeline.pipeline import apply_preset
    import libs.audio_pipeline.pipeline as _pipe_mod

    evidence["audio_pipeline_origin"] = str(Path(_pipe_mod.__file__).resolve())

    # --- Origin assertions ---
    if not evidence["audio_pipeline_origin"].startswith(_REPO):
        failures.append(
            f"audio_pipeline not from REPO: {evidence['audio_pipeline_origin']}"
        )
    if not evidence["numpy_origin"].startswith(_OPT_CONDA):
        failures.append(f"numpy not from /opt/conda: {evidence['numpy_origin']}")
    for name, p in [
        ("scipy", evidence["scipy_origin"]),
        ("soundfile", evidence["soundfile_origin"]),
    ]:
        if not _approved_third_party(p):
            failures.append(f"{name} not from approved origin: {p}")

    user_local_module_paths = {
        k: v
        for k, v in {
            "numpy": evidence["numpy_origin"],
            "scipy": evidence["scipy_origin"],
            "soundfile": evidence["soundfile_origin"],
            "audio_pipeline": evidence["audio_pipeline_origin"],
        }.items()
        if _has_user_local(v)
    }
    evidence["user_local_paths_detected"] = user_local_module_paths
    evidence["any_user_local_module_paths_detected"] = bool(user_local_module_paths)
    if user_local_module_paths:
        failures.append(f"user-local module paths detected: {user_local_module_paths}")

    evidence["origin_failures_snapshot"] = failures[:]

    # --- Generate synthetic WAV (2 s, 440 Hz, 16 kHz, peak ~0.9) ---
    sr = 16_000
    t = np.linspace(0.0, 2.0, int(sr * 2.0), endpoint=False)
    samples = (0.9 * np.sin(2.0 * np.pi * 440.0 * t)).astype("float64")
    args.input_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.input_wav), samples, sr)
    evidence["input_wav"] = str(args.input_wav)

    # --- Run apply_preset("denoise") ---
    expected_output_wav = args.output_dir / "denoise.wav"
    evidence["output_dir"] = str(args.output_dir)
    evidence["expected_output_wav"] = str(expected_output_wav)

    result = apply_preset("denoise", args.input_wav, args.output_dir)

    evidence["preset_applied"] = result.preset_applied
    evidence["enhanced"] = result.enhanced
    evidence["enhancement_fallback"] = result.enhancement_fallback
    evidence["output_wav"] = str(result.output_path)
    evidence["diagnostic"] = result.diagnostic

    # --- Validate EnhancementResult fields ---
    if result.output_path != expected_output_wav:
        failures.append(
            f"output_path mismatch: got {result.output_path}, expected {expected_output_wav}"
        )
    if not result.output_path.exists():
        failures.append(f"output WAV does not exist: {result.output_path}")
    if result.preset_applied != "denoise":
        failures.append(f"preset_applied != 'denoise': {result.preset_applied}")
    if not result.enhanced:
        detail = result.diagnostic.get("fallback_reason", "unknown")
        failures.append(f"enhanced is False (fallback_reason: {detail})")
    if result.enhancement_fallback:
        failures.append("enhancement_fallback is True")

    # --- Validate output audio ---
    if result.output_path.exists():
        info = sf.info(str(result.output_path))
        evidence["output_frames"] = info.frames
        evidence["output_samplerate"] = info.samplerate
        out_samples, _ = sf.read(str(result.output_path), dtype="float64")
        peak = float(np.max(np.abs(out_samples)))
        evidence["output_peak"] = round(peak, 6)

        if info.frames == 0:
            failures.append("output WAV has 0 frames")
        if info.samplerate != sr:
            failures.append(
                f"sample rate mismatch: got {info.samplerate}, expected {sr}"
            )
        if not (0.93 <= peak <= 0.97):
            failures.append(f"output_peak {peak:.6f} outside [0.93, 0.97]")
    else:
        failures.append("output WAV does not exist; audio validation skipped")

    # --- Final result ---
    evidence["all_failures"] = failures
    evidence["success"] = len(failures) == 0
    evidence["timestamp_utc"] = datetime.datetime.utcnow().isoformat() + "Z"

    # --- Write JSON ---
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(evidence, fh, indent=2)

    # --- Summary to stdout ---
    print(f"python_executable          : {evidence['python_executable']}")
    print(f"python_version             : {evidence['python_version']}")
    print(f"audio_pipeline_origin      : {evidence['audio_pipeline_origin']}")
    print(f"soundfile_origin           : {evidence['soundfile_origin']}")
    print(f"scipy_origin               : {evidence['scipy_origin']}")
    print(f"numpy_origin               : {evidence['numpy_origin']}")
    print(f"output_peak                : {evidence.get('output_peak', 'N/A')}")
    print(f"enhanced                   : {evidence.get('enhanced')}")
    print(f"enhancement_fallback       : {evidence.get('enhancement_fallback')}")
    print(f"site_enable_user_site      : {evidence['site_enable_user_site']}")
    print(f"any_user_local_detected    : {evidence['any_user_local_module_paths_detected']}")
    print(f"JSON written to            : {args.out}")
    print()

    if evidence["success"]:
        print("T1.3 COMPLETE")
        sys.exit(0)
    else:
        print(f"T1.3 FAILED: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
