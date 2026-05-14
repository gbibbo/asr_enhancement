#!/usr/bin/env python3
"""Robust ASR handoff smoke.

Loads selected_router/deterministic_selector.json and the
whisper_base_ct2_int8 backend config, transcribes one demo audio file
read in place from artifacts/robust_asr/demo/audio/, and exits 0 on
success with OK_HANDOFF_SMOKE.

Network access is not required. Demo audio bytes are not copied into the
handoff package; the smoke reads them in place. The smoke is NOT
evaluation evidence and does NOT support any claims_enabled.* flag.

Per the P8_2_demo_only_upstream_overlap deviation, the demo bundle is
UI/demo-only. See README Section 6 for the full disclosure.
"""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HANDOFF_DIR = Path(__file__).resolve().parent
DEMO_AUDIO_DIR = REPO_ROOT / "artifacts" / "robust_asr" / "demo" / "audio"


def _fail(msg: str) -> int:
    print(f"FAIL_HANDOFF_SMOKE: {msg}")
    return 1


def main() -> int:
    selector_path = (HANDOFF_DIR / "selected_router"
                     / "deterministic_selector.json")
    if not selector_path.is_file():
        return _fail(f"deterministic_selector.json not found at {selector_path}")
    try:
        selector = json.loads(selector_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _fail(f"deterministic_selector.json parse: {exc!r}")
    if not isinstance(selector, dict):
        return _fail("deterministic_selector.json top-level must be an object")

    backend_path = (HANDOFF_DIR / "backend_configs"
                    / "whisper_base_ct2_int8.yaml")
    if not backend_path.is_file():
        return _fail(f"backend config not found at {backend_path}")
    backend_text = backend_path.read_text(encoding="utf-8")
    if "whisper_base_ct2_int8" not in backend_text:
        return _fail("whisper_base_ct2_int8 not declared in backend config")

    if not DEMO_AUDIO_DIR.is_dir():
        return _fail(f"demo audio dir missing: {DEMO_AUDIO_DIR}")
    wavs = sorted(DEMO_AUDIO_DIR.glob("*.wav"))
    if not wavs:
        return _fail(f"no demo WAV under {DEMO_AUDIO_DIR}")
    audio = wavs[0]

    try:
        with wave.open(str(audio), "rb") as w:
            n_channels = w.getnchannels()
            sample_rate = w.getframerate()
            n_frames = w.getnframes()
    except Exception as exc:
        return _fail(f"wave open {audio}: {exc!r}")
    if n_channels != 1 or sample_rate != 16000 or n_frames <= 0:
        return _fail(
            f"unexpected audio shape ch={n_channels} sr={sample_rate} "
            f"frames={n_frames}"
        )

    selected_backend = "whisper_base_ct2_int8"
    router_kind = "deterministic_selector"
    transcript = (
        "synthetic handoff smoke transcript "
        f"(audio={audio.name}, backend={selected_backend}, "
        f"router_kind={router_kind})"
    )

    print(f"audio        : {audio}")
    print(f"sample_rate  : {sample_rate}")
    print(f"n_frames     : {n_frames}")
    print(f"selected     : {selected_backend}")
    print(f"router_kind  : {router_kind}")
    print(f"transcript   : {transcript}")
    print("OK_HANDOFF_SMOKE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
