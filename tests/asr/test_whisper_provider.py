from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.asr.base import ASRAdapter
from libs.asr.errors import AdapterTranscriptionError, InputFileNotFoundError
from libs.asr.schema import ASRResult
from libs.asr.whisper_provider import WhisperAdapter, _FASTER_WHISPER_AVAILABLE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_model(
    *,
    language: str = "en",
    language_probability: float = 0.99,
    segments: list | None = None,
) -> MagicMock:
    seg = MagicMock()
    seg.text = "Hello."
    seg.start = 0.0
    seg.end = 1.2
    info = MagicMock()
    info.language = language
    info.language_probability = language_probability
    info.duration = 1.5
    mock = MagicMock()
    mock.transcribe.return_value = (iter(segments if segments is not None else [seg]), info)
    return mock


def _audio_file(tmp_path: Path, name: str = "audio.wav") -> Path:
    f = tmp_path / name
    f.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    return f


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------

def test_whisper_adapter_is_asr_adapter():
    assert issubclass(WhisperAdapter, ASRAdapter)


def test_model_name_constant():
    assert WhisperAdapter.MODEL_NAME == "tiny.en"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_raises_when_file_missing(tmp_path: Path):
    adapter = WhisperAdapter(_model=_make_mock_model())
    with pytest.raises(InputFileNotFoundError):
        adapter.transcribe(tmp_path / "nonexistent.wav", job_id="j1")


def test_raises_when_path_is_directory(tmp_path: Path):
    d = tmp_path / "audio_dir"
    d.mkdir()
    adapter = WhisperAdapter(_model=_make_mock_model())
    with pytest.raises(InputFileNotFoundError):
        adapter.transcribe(d, job_id="j1")


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def test_transcribes_english_audio(tmp_path: Path):
    f = _audio_file(tmp_path)
    adapter = WhisperAdapter(_model=_make_mock_model(language="en", language_probability=0.99))
    result = adapter.transcribe(f, job_id="j1")
    assert result.provider == "whisper"
    assert result.language == "en"
    assert result.text == "Hello."
    assert "language_warning" not in result.raw_payload


def test_result_schema_matches_other_providers(tmp_path: Path):
    f = _audio_file(tmp_path)
    adapter = WhisperAdapter(_model=_make_mock_model())
    result = adapter.transcribe(f, job_id="j1")
    assert isinstance(result, ASRResult)
    field_names = {field.name for field in fields(ASRResult)}
    expected = {
        "text", "language", "duration_seconds", "segments",
        "words", "provider", "provider_job_id", "raw_payload",
    }
    assert expected <= field_names
    assert result.provider_job_id is None
    assert result.words == []


def test_segments_normalized(tmp_path: Path):
    f = _audio_file(tmp_path)
    seg1 = MagicMock()
    seg1.text = "Hello"
    seg1.start = 0.0
    seg1.end = 0.5
    seg2 = MagicMock()
    seg2.text = "world"
    seg2.start = 0.6
    seg2.end = 1.2
    info = MagicMock()
    info.language = "en"
    info.language_probability = 0.99
    info.duration = 1.5
    mock = MagicMock()
    mock.transcribe.return_value = (iter([seg1, seg2]), info)
    adapter = WhisperAdapter(_model=mock)
    result = adapter.transcribe(f, job_id="j1")
    assert len(result.segments) == 2
    assert result.segments[0] == {"start": 0.0, "end": 0.5, "text": "Hello"}
    assert result.segments[1] == {"start": 0.6, "end": 1.2, "text": "world"}


def test_empty_segments_produce_empty_text(tmp_path: Path):
    f = _audio_file(tmp_path)
    info = MagicMock()
    info.language = "en"
    info.language_probability = 0.99
    info.duration = 1.0
    mock = MagicMock()
    mock.transcribe.return_value = (iter([]), info)
    adapter = WhisperAdapter(_model=mock)
    result = adapter.transcribe(f, job_id="j1")
    assert result.text == ""
    assert result.segments == []


def test_raw_payload_includes_model_name(tmp_path: Path):
    f = _audio_file(tmp_path)
    adapter = WhisperAdapter(_model=_make_mock_model())
    result = adapter.transcribe(f, job_id="j1")
    assert result.raw_payload["model"] == "tiny.en"


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def test_non_english_sets_language_warning(tmp_path: Path):
    f = _audio_file(tmp_path)
    adapter = WhisperAdapter(_model=_make_mock_model(language="fr", language_probability=0.8))
    result = adapter.transcribe(f, job_id="j1")
    assert "language_warning" in result.raw_payload
    assert "not English" in result.raw_payload["language_warning"]


def test_non_english_below_threshold_no_warning(tmp_path: Path):
    f = _audio_file(tmp_path)
    adapter = WhisperAdapter(_model=_make_mock_model(language="fr", language_probability=0.3))
    result = adapter.transcribe(f, job_id="j1")
    assert "language_warning" not in result.raw_payload


def test_english_above_threshold_no_warning(tmp_path: Path):
    f = _audio_file(tmp_path)
    adapter = WhisperAdapter(_model=_make_mock_model(language="en", language_probability=0.99))
    result = adapter.transcribe(f, job_id="j1")
    assert "language_warning" not in result.raw_payload


# ---------------------------------------------------------------------------
# Availability guard
# ---------------------------------------------------------------------------

def test_raises_if_faster_whisper_unavailable():
    with patch("libs.asr.whisper_provider._FASTER_WHISPER_AVAILABLE", False):
        with pytest.raises(AdapterTranscriptionError, match="faster-whisper is not installed"):
            WhisperAdapter()


# ---------------------------------------------------------------------------
# Live import check (skipped when faster-whisper absent)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _FASTER_WHISPER_AVAILABLE,
    reason="faster-whisper not installed in this environment",
)
def test_import_check():
    adapter = WhisperAdapter(_model=MagicMock())
    assert isinstance(adapter, ASRAdapter)
