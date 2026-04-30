from __future__ import annotations

from pathlib import Path

import pytest

from libs.asr_adapter.base import ASRAdapter
from libs.asr_adapter.errors import InputFileNotFoundError
from libs.asr_adapter.fake import _DEFAULT_TRANSCRIPT, FakeASRAdapter
from libs.asr_adapter.schema import ASRResult

_JOB_ID = "test-job-id"


def _audio(tmp_path: Path, name: str = "audio.wav", content: bytes = b"") -> Path:
    f = tmp_path / name
    f.write_bytes(content)
    return f


# --- transcript text ---

def test_default_transcript_when_no_fixture(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.text == _DEFAULT_TRANSCRIPT


def test_custom_transcript_when_fixture_provided(tmp_path):
    result = FakeASRAdapter(fake_transcript="hello world").transcribe(_audio(tmp_path), _JOB_ID)
    assert result.text == "hello world"


def test_empty_string_fixture_falls_back_to_default(tmp_path):
    result = FakeASRAdapter(fake_transcript="").transcribe(_audio(tmp_path), _JOB_ID)
    assert result.text == _DEFAULT_TRANSCRIPT


# --- missing file ---

def test_missing_file_raises_input_not_found(tmp_path):
    missing = tmp_path / "nonexistent.wav"
    with pytest.raises(InputFileNotFoundError):
        FakeASRAdapter().transcribe(missing, _JOB_ID)


def test_input_not_found_is_adapter_error(tmp_path):
    from libs.asr_adapter.errors import AdapterError
    missing = tmp_path / "nonexistent.wav"
    with pytest.raises(AdapterError):
        FakeASRAdapter().transcribe(missing, _JOB_ID)


# --- existing file returns result ---

def test_existing_file_returns_asr_result(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert isinstance(result, ASRResult)


def test_zero_byte_file_returns_result(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path, content=b""), _JOB_ID)
    assert isinstance(result, ASRResult)


# --- all normalized fields ---

def test_result_text_matches_default(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.text == _DEFAULT_TRANSCRIPT


def test_result_language_is_en(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.language == "en"


def test_result_duration_is_none(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.duration_seconds is None


def test_result_segments_is_empty_list(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.segments == []


def test_result_words_is_empty_list(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.words == []


def test_result_provider_is_fake(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.provider == "fake"


def test_result_provider_job_id_is_none(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.provider_job_id is None


def test_result_raw_payload_is_empty_dict(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), _JOB_ID)
    assert result.raw_payload == {}


# --- interface and job_id ---

def test_fake_adapter_is_subclass_of_asr_adapter():
    assert isinstance(FakeASRAdapter(), ASRAdapter)


def test_job_id_accepted_not_in_result(tmp_path):
    result = FakeASRAdapter().transcribe(_audio(tmp_path), "some-unique-job-id-xyz")
    assert result.provider_job_id is None
    assert "some-unique-job-id-xyz" not in result.text
