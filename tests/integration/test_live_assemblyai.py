"""
Live AssemblyAI smoke test.

Runs only when both variables are set:
  RUN_LIVE_ASSEMBLYAI_TEST=1
  ASSEMBLYAI_API_KEY=<your key>

In all other contexts the module is skipped at collection time (not failed).

Run command:
  RUN_LIVE_ASSEMBLYAI_TEST=1 ASSEMBLYAI_API_KEY=<key> \\
    pytest tests/integration/test_live_assemblyai.py -v -s
"""
from __future__ import annotations

import io
import os
import wave
from pathlib import Path

import pytest

# ------------------------------------------------------------------
# Module-level gate — evaluated once at collection time
# ------------------------------------------------------------------
_RUN_LIVE = os.getenv("RUN_LIVE_ASSEMBLYAI_TEST", "0") == "1"
_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

_missing: list[str] = []
if not _RUN_LIVE:
    _missing.append("RUN_LIVE_ASSEMBLYAI_TEST=1")
if not _API_KEY:
    _missing.append("ASSEMBLYAI_API_KEY")

if _missing:
    pytest.skip(
        f"Live AssemblyAI smoke test skipped — set: {', '.join(_missing)}",
        allow_module_level=True,
    )

# Imports deferred past the skip so they don't execute during a skipped collection.
from libs.asr.assemblyai_provider import AssemblyAIAdapter  # noqa: E402
from libs.asr.schema import ASRResult  # noqa: E402

_POLL_INTERVAL_S = 5.0
_MAX_WAIT_S = 300.0  # 5-minute hard ceiling; real 1-s audio typically < 30 s


def _write_minimal_wav(path: Path) -> None:
    """Write a 1-second silent mono 16 kHz 16-bit PCM WAV to path."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00" * 32000)  # 1 s × 16000 Hz × 2 bytes/sample
    path.write_bytes(buf.getvalue())


@pytest.mark.live_provider
def test_assemblyai_live_transcription(tmp_path: Path) -> None:
    """Submit a 1-second silent WAV to AssemblyAI and verify a normalized result."""
    audio_file = tmp_path / "live_smoke_input.wav"
    _write_minimal_wav(audio_file)

    adapter = AssemblyAIAdapter(
        api_key=_API_KEY,
        poll_interval_seconds=_POLL_INTERVAL_S,
        max_wait_seconds=_MAX_WAIT_S,
    )

    result = adapter.transcribe(audio_file, job_id="live-smoke-test")

    assert isinstance(result, ASRResult), (
        f"Expected ASRResult, got {type(result).__name__}"
    )
    assert result.provider == "assemblyai", (
        f"Expected provider='assemblyai', got {result.provider!r}"
    )
    assert isinstance(result.provider_job_id, str) and result.provider_job_id, (
        "provider_job_id must be a non-empty string"
    )
    assert isinstance(result.text, str), (
        "result.text must be a str (may be empty for silent audio)"
    )
