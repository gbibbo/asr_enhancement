from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from libs.asr.assemblyai_provider import AssemblyAIAdapter
from libs.asr.base import ASRAdapter
from libs.asr.demo_assemblyai_provider import (
    DemoAssemblyAIAdapter,
    _QUOTA_MESSAGE,
    _RETRY_WAIT_SECONDS,
    _SAFE_ERROR_MESSAGE,
)
from libs.asr.errors import (
    AdapterHTTPError,
    AdapterTimeoutError,
    AdapterTranscriptionError,
    InputFileNotFoundError,
)
from libs.asr.schema import ASRResult


def _make_result(**kw) -> ASRResult:
    base = dict(
        text="Hello.",
        language="en",
        duration_seconds=1.0,
        segments=[],
        words=[],
        provider="assemblyai",
        provider_job_id="t-1",
        raw_payload={},
    )
    return ASRResult(**(base | kw))


def _http_error(status_code: int) -> AdapterHTTPError:
    return AdapterHTTPError(f"HTTP {status_code}", status_code=status_code)


def _adapter(**kwargs) -> DemoAssemblyAIAdapter:
    return DemoAssemblyAIAdapter(api_key="k", _sleep=MagicMock(), **kwargs)


def _audio(tmp_path: Path) -> Path:
    p = tmp_path / "audio.wav"
    p.write_bytes(b"RIFF")
    return p


# ---------------------------------------------------------------------------
# 1–2. Inheritance
# ---------------------------------------------------------------------------

def test_demo_adapter_is_asr_adapter():
    assert issubclass(DemoAssemblyAIAdapter, ASRAdapter)


def test_demo_adapter_is_assemblyai_adapter():
    assert issubclass(DemoAssemblyAIAdapter, AssemblyAIAdapter)


# ---------------------------------------------------------------------------
# 3–5. Provider status
# ---------------------------------------------------------------------------

def test_status_disabled_when_key_is_none():
    assert DemoAssemblyAIAdapter.get_status(None) == DemoAssemblyAIAdapter.STATUS_DISABLED


def test_status_disabled_when_key_is_empty_string():
    assert DemoAssemblyAIAdapter.get_status("") == DemoAssemblyAIAdapter.STATUS_DISABLED


def test_status_available_when_key_present():
    assert DemoAssemblyAIAdapter.get_status("sk-xxx") == DemoAssemblyAIAdapter.STATUS_AVAILABLE


# ---------------------------------------------------------------------------
# 6. Success — no retry, no sleep
# ---------------------------------------------------------------------------

def test_success_no_retry_no_sleep(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    expected = _make_result()
    with patch.object(AssemblyAIAdapter, "transcribe", return_value=expected):
        result = adapter.transcribe(_audio(tmp_path), job_id="j1")
    sleep_mock.assert_not_called()
    assert result is expected


# ---------------------------------------------------------------------------
# 7. 5xx triggers exactly one retry
# ---------------------------------------------------------------------------

def test_5xx_triggers_one_retry(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    expected = _make_result()
    with patch.object(
        AssemblyAIAdapter, "transcribe",
        side_effect=[_http_error(503), expected],
    ):
        result = adapter.transcribe(_audio(tmp_path), job_id="j1")
    sleep_mock.assert_called_once_with(_RETRY_WAIT_SECONDS)
    assert result is expected


# ---------------------------------------------------------------------------
# 8. Timeout triggers exactly one retry
# ---------------------------------------------------------------------------

def test_timeout_triggers_one_retry(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    expected = _make_result()
    with patch.object(
        AssemblyAIAdapter, "transcribe",
        side_effect=[AdapterTimeoutError("timed out"), expected],
    ):
        result = adapter.transcribe(_audio(tmp_path), job_id="j1")
    sleep_mock.assert_called_once_with(_RETRY_WAIT_SECONDS)
    assert result is expected


# ---------------------------------------------------------------------------
# 9. Retry sleep is exactly 2 seconds
# ---------------------------------------------------------------------------

def test_retry_sleep_is_exactly_two_seconds(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    with patch.object(
        AssemblyAIAdapter, "transcribe",
        side_effect=[_http_error(500), _make_result()],
    ):
        adapter.transcribe(_audio(tmp_path), job_id="j1")
    sleep_mock.assert_called_once_with(2.0)


# ---------------------------------------------------------------------------
# 10. 4xx does not retry
# ---------------------------------------------------------------------------

def test_4xx_does_not_retry(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    err = _http_error(401)
    with patch.object(AssemblyAIAdapter, "transcribe", side_effect=err):
        with pytest.raises(AdapterHTTPError) as exc_info:
            adapter.transcribe(_audio(tmp_path), job_id="j1")
    sleep_mock.assert_not_called()
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# 11. InputFileNotFoundError does not retry
# ---------------------------------------------------------------------------

def test_missing_file_not_retried(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    with patch.object(
        AssemblyAIAdapter, "transcribe",
        side_effect=InputFileNotFoundError("not found"),
    ):
        with pytest.raises(InputFileNotFoundError):
            adapter.transcribe(_audio(tmp_path), job_id="j1")
    sleep_mock.assert_not_called()


# ---------------------------------------------------------------------------
# 12. Double 5xx returns safe message
# ---------------------------------------------------------------------------

def test_safe_message_on_5xx_double_failure(tmp_path):
    sleep_mock = MagicMock()
    adapter = DemoAssemblyAIAdapter(api_key="k", _sleep=sleep_mock)
    with patch.object(
        AssemblyAIAdapter, "transcribe",
        side_effect=[_http_error(503), _http_error(503)],
    ):
        with pytest.raises(AdapterTranscriptionError) as exc_info:
            adapter.transcribe(_audio(tmp_path), job_id="j1")
    assert str(exc_info.value) == _SAFE_ERROR_MESSAGE


# ---------------------------------------------------------------------------
# 13. quota_exhausted=True never calls AssemblyAIAdapter.transcribe
# ---------------------------------------------------------------------------

def test_quota_exhausted_does_not_call_super(tmp_path):
    adapter = DemoAssemblyAIAdapter(api_key="k", quota_exhausted=True)
    with patch.object(AssemblyAIAdapter, "transcribe") as mock_super:
        with pytest.raises(AdapterTranscriptionError) as exc_info:
            adapter.transcribe(_audio(tmp_path), job_id="j1")
    mock_super.assert_not_called()
    assert str(exc_info.value) == _QUOTA_MESSAGE


# ---------------------------------------------------------------------------
# 14. No silent fallback to Whisper
# ---------------------------------------------------------------------------

def test_no_silent_fallback_to_whisper(tmp_path):
    adapter = _adapter()
    with patch.object(
        AssemblyAIAdapter, "transcribe",
        side_effect=[_http_error(500), _http_error(500)],
    ):
        with pytest.raises(AdapterTranscriptionError) as exc_info:
            adapter.transcribe(_audio(tmp_path), job_id="j1")
    result_or_error = exc_info.value
    assert not isinstance(result_or_error, ASRResult)
    assert getattr(result_or_error, "provider", None) != "whisper"
