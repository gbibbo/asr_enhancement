from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

import httpx
import pytest

from libs.asr_adapter.assemblyai import AssemblyAIAdapter
from libs.asr_adapter.base import ASRAdapter
from libs.asr_adapter.errors import AdapterTranscriptionError, InputFileNotFoundError
from libs.asr_adapter.schema import ASRResult

_API_KEY = "test-key-should-not-appear-in-errors"
_JOB_ID = "test-job-id"
_TRANSCRIPT_ID = "t_abc123"
_UPLOAD_URL = "https://cdn.assemblyai.com/upload/test"
_BASE_URL = "https://api.assemblyai.com"

_FULL_RESPONSE = {
    "id": _TRANSCRIPT_ID,
    "status": "completed",
    "text": "Hello world",
    "language_code": "en",
    "audio_duration": 3.5,
    "words": [{"text": "Hello", "start": 0, "end": 450, "confidence": 0.99}],
    "utterances": [{"speaker": "A", "text": "Hello world", "start": 0, "end": 450}],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _audio(tmp_path: Path, name: str = "audio.wav", content: bytes = b"RIFF") -> Path:
    f = tmp_path / name
    f.write_bytes(content)
    return f


def _resp(json_data: dict, status_code: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data
    if status_code >= 400:
        err = httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=MagicMock(),
            response=MagicMock(status_code=status_code),
        )
        r.raise_for_status.side_effect = err
    else:
        r.raise_for_status.return_value = None
    return r


def _make_mock_client(
    *,
    upload_url: str = _UPLOAD_URL,
    transcript_id: str = _TRANSCRIPT_ID,
    poll_response: dict | None = None,
    poll_side_effect: list | None = None,
    upload_raises: httpx.HTTPStatusError | None = None,
    submit_raises: httpx.HTTPStatusError | None = None,
    poll_raises: httpx.HTTPStatusError | None = None,
) -> MagicMock:
    client = MagicMock()

    upload_resp = _resp({"upload_url": upload_url})
    if upload_raises:
        upload_resp.raise_for_status.side_effect = upload_raises

    submit_resp = _resp({"id": transcript_id, "status": "queued"})
    if submit_raises:
        submit_resp.raise_for_status.side_effect = submit_raises

    client.post.side_effect = [upload_resp, submit_resp]

    if poll_raises:
        poll_resp = _resp({}, 500)
        poll_resp.raise_for_status.side_effect = poll_raises
        client.get.return_value = poll_resp
    elif poll_side_effect is not None:
        client.get.side_effect = poll_side_effect
    else:
        final = poll_response if poll_response is not None else dict(_FULL_RESPONSE)
        client.get.return_value = _resp(final)

    return client


def _adapter(mock_client: MagicMock, **kwargs) -> AssemblyAIAdapter:
    return AssemblyAIAdapter(
        api_key=_API_KEY,
        _http_client=mock_client,
        _sleep=lambda s: None,
        poll_interval_seconds=0,
        max_wait_seconds=999,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 1. Interface
# ---------------------------------------------------------------------------

def test_assemblyai_adapter_is_subclass_of_asr_adapter():
    assert issubclass(AssemblyAIAdapter, ASRAdapter)


# ---------------------------------------------------------------------------
# 2–3. Missing input file
# ---------------------------------------------------------------------------

def test_missing_file_raises_input_file_not_found(tmp_path):
    missing = tmp_path / "nonexistent.wav"
    client = _make_mock_client()
    with pytest.raises(InputFileNotFoundError):
        _adapter(client).transcribe(missing, _JOB_ID)


def test_input_file_not_found_is_adapter_error(tmp_path):
    from libs.asr_adapter.errors import AdapterError
    missing = tmp_path / "nonexistent.wav"
    client = _make_mock_client()
    with pytest.raises(AdapterError):
        _adapter(client).transcribe(missing, _JOB_ID)


# ---------------------------------------------------------------------------
# 4–13. Successful transcription — result fields
# ---------------------------------------------------------------------------

def test_successful_transcription_returns_asr_result(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert isinstance(result, ASRResult)


def test_result_text_from_response(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.text == "Hello world"


def test_result_provider_is_assemblyai(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.provider == "assemblyai"


def test_result_provider_job_id_from_response(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.provider_job_id == _TRANSCRIPT_ID


def test_result_language_from_response(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.language == "en"


def test_result_duration_from_response(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.duration_seconds == 3.5


def test_result_words_from_response(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.words == _FULL_RESPONSE["words"]


def test_result_segments_from_utterances(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.segments == _FULL_RESPONSE["utterances"]


def test_result_segments_empty_when_utterances_null(tmp_path):
    resp = dict(_FULL_RESPONSE, utterances=None)
    result = _adapter(_make_mock_client(poll_response=resp)).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.segments == []


def test_result_raw_payload_contains_full_response(tmp_path):
    result = _adapter(_make_mock_client()).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.raw_payload["id"] == _TRANSCRIPT_ID
    assert result.raw_payload["text"] == "Hello world"


# ---------------------------------------------------------------------------
# 14–16. HTTP request shape
# ---------------------------------------------------------------------------

def test_upload_post_called_with_correct_endpoint_and_auth_header(tmp_path):
    client = _make_mock_client()
    _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    upload_call = client.post.call_args_list[0]
    assert upload_call.args[0] == f"{_BASE_URL}/v2/upload"
    assert upload_call.kwargs["headers"]["Authorization"] == _API_KEY


def test_submit_post_called_with_correct_json_body_and_audio_url(tmp_path):
    client = _make_mock_client()
    _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert submit_call.args[0] == f"{_BASE_URL}/v2/transcript"
    assert submit_call.kwargs["json"] == {
        "audio_url": _UPLOAD_URL,
        "speech_models": ["universal"],
        "language_code": "en",
    }


def test_poll_get_called_with_correct_endpoint_and_auth_header(tmp_path):
    client = _make_mock_client()
    _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    get_call = client.get.call_args
    assert get_call.args[0] == f"{_BASE_URL}/v2/transcript/{_TRANSCRIPT_ID}"
    assert get_call.kwargs["headers"]["Authorization"] == _API_KEY


# ---------------------------------------------------------------------------
# 17. Timeout values
# ---------------------------------------------------------------------------

def test_upload_uses_upload_timeout_seconds(tmp_path):
    client = _make_mock_client()
    _adapter(client, upload_timeout_seconds=77.0).transcribe(_audio(tmp_path), _JOB_ID)
    upload_call = client.post.call_args_list[0]
    assert upload_call.kwargs["timeout"] == 77.0


# ---------------------------------------------------------------------------
# 18. Multi-poll
# ---------------------------------------------------------------------------

def test_poll_completes_after_multiple_processing_responses(tmp_path):
    processing = _resp({"id": _TRANSCRIPT_ID, "status": "processing", "text": None,
                        "language_code": None, "audio_duration": None,
                        "words": None, "utterances": None})
    completed = _resp(dict(_FULL_RESPONSE))
    client = _make_mock_client(poll_side_effect=[processing, processing, completed])
    result = _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    assert result.text == "Hello world"
    assert client.get.call_count == 3


# ---------------------------------------------------------------------------
# 19–22. Error cases
# ---------------------------------------------------------------------------

def test_upload_http_error_raises_transcription_error(tmp_path):
    http_err = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock(status_code=401)
    )
    client = _make_mock_client(upload_raises=http_err)
    with pytest.raises(AdapterTranscriptionError, match="upload failed: HTTP 401"):
        _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)


def test_submit_http_error_raises_transcription_error(tmp_path):
    http_err = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock(status_code=500)
    )
    client = _make_mock_client(submit_raises=http_err)
    with pytest.raises(AdapterTranscriptionError, match="submit failed: HTTP 500"):
        _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)


def test_poll_http_error_raises_transcription_error(tmp_path):
    http_err = httpx.HTTPStatusError(
        "503", request=MagicMock(), response=MagicMock(status_code=503)
    )
    client = _make_mock_client(poll_raises=http_err)
    with pytest.raises(AdapterTranscriptionError, match="poll failed: HTTP 503"):
        _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)


def test_provider_error_status_raises_transcription_error(tmp_path):
    error_resp = {
        "id": _TRANSCRIPT_ID, "status": "error",
        "error": "Audio file could not be decoded",
    }
    client = _make_mock_client(poll_response=error_resp)
    with pytest.raises(AdapterTranscriptionError, match="Audio file could not be decoded"):
        _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)


# ---------------------------------------------------------------------------
# 23. Polling timeout
# ---------------------------------------------------------------------------

def test_poll_timeout_raises_transcription_error(tmp_path):
    processing = _resp({"id": _TRANSCRIPT_ID, "status": "processing",
                        "text": None, "language_code": None,
                        "audio_duration": None, "words": None, "utterances": None})
    client = _make_mock_client(poll_side_effect=[processing] * 10)
    adapter = AssemblyAIAdapter(
        api_key=_API_KEY,
        _http_client=client,
        _sleep=lambda s: None,
        poll_interval_seconds=1,
        max_wait_seconds=0,
    )
    with pytest.raises(AdapterTranscriptionError, match="timed out"):
        adapter.transcribe(_audio(tmp_path), _JOB_ID)


# ---------------------------------------------------------------------------
# 24–26. speech_models and language_code
# ---------------------------------------------------------------------------

def test_submit_default_speech_models_is_universal(tmp_path):
    client = _make_mock_client()
    _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert submit_call.kwargs["json"]["speech_models"] == ["universal"]


def test_submit_custom_speech_models_honored(tmp_path):
    client = _make_mock_client()
    _adapter(client, speech_models=["nano"]).transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert submit_call.kwargs["json"]["speech_models"] == ["nano"]


def test_submit_multiple_custom_speech_models(tmp_path):
    client = _make_mock_client()
    _adapter(client, speech_models=["universal", "nano"]).transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert submit_call.kwargs["json"]["speech_models"] == ["universal", "nano"]


def test_submit_default_language_code_is_en(tmp_path):
    client = _make_mock_client()
    _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert submit_call.kwargs["json"]["language_code"] == "en"


def test_submit_custom_language_code_honored(tmp_path):
    client = _make_mock_client()
    _adapter(client, language_code="fr").transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert submit_call.kwargs["json"]["language_code"] == "fr"


def test_submit_none_language_code_omits_field(tmp_path):
    client = _make_mock_client()
    _adapter(client, language_code=None).transcribe(_audio(tmp_path), _JOB_ID)
    submit_call = client.post.call_args_list[1]
    assert "language_code" not in submit_call.kwargs["json"]


# ---------------------------------------------------------------------------
# 30–31. Key safety
# ---------------------------------------------------------------------------

def test_api_key_not_in_any_raised_error_message(tmp_path):
    http_err = httpx.HTTPStatusError(
        "401", request=MagicMock(), response=MagicMock(status_code=401)
    )
    client = _make_mock_client(upload_raises=http_err)
    with pytest.raises(AdapterTranscriptionError) as exc_info:
        _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    assert _API_KEY not in str(exc_info.value)


def test_api_key_not_in_submit_error_message(tmp_path):
    http_err = httpx.HTTPStatusError(
        "400", request=MagicMock(), response=MagicMock(status_code=400)
    )
    client = _make_mock_client(submit_raises=http_err)
    with pytest.raises(AdapterTranscriptionError) as exc_info:
        _adapter(client).transcribe(_audio(tmp_path), _JOB_ID)
    assert _API_KEY not in str(exc_info.value)
