from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Optional

import httpx

from libs.asr_adapter.base import ASRAdapter
from libs.asr_adapter.errors import AdapterTranscriptionError, InputFileNotFoundError
from libs.asr_adapter.schema import ASRResult


class AssemblyAIAdapter(ASRAdapter):
    """Pre-recorded transcription adapter for AssemblyAI.

    Uses plain HTTP (httpx) against the AssemblyAI v2 REST API. Polls for
    completion and normalizes the response into the project's ASRResult schema.

    Args:
        api_key: AssemblyAI API key (required).
        base_url: API base URL; override in tests if needed.
        speech_models: Model list sent in the transcript submit body.
            Defaults to ["universal"].
        poll_interval_seconds: Seconds to wait between poll requests.
        max_wait_seconds: Total polling budget; raises on timeout.
        upload_timeout_seconds: httpx timeout for the audio upload POST.
        submit_timeout_seconds: httpx timeout for the transcript submit POST.
        poll_timeout_seconds: httpx timeout for each poll GET.
        _http_client: Injected HTTP client (for unit tests only).
        _sleep: Injected sleep callable (for unit tests only).
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.assemblyai.com",
        speech_models: Optional[list[str]] = None,
        poll_interval_seconds: float = 3.0,
        max_wait_seconds: float = 600.0,
        upload_timeout_seconds: float = 120.0,
        submit_timeout_seconds: float = 30.0,
        poll_timeout_seconds: float = 30.0,
        _http_client: Optional[Any] = None,
        _sleep: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._speech_models: list[str] = speech_models if speech_models is not None else ["universal"]
        self._poll_interval = poll_interval_seconds
        self._max_wait = max_wait_seconds
        self._upload_timeout = upload_timeout_seconds
        self._submit_timeout = submit_timeout_seconds
        self._poll_timeout = poll_timeout_seconds
        self._client: Any = _http_client if _http_client is not None else httpx.Client()
        self._sleep: Callable[[float], None] = _sleep if _sleep is not None else time.sleep

    def __repr__(self) -> str:
        return (
            f"AssemblyAIAdapter(base_url={self._base_url!r}, "
            f"max_wait_seconds={self._max_wait})"
        )

    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult:
        if not audio_path.exists():
            raise InputFileNotFoundError(f"Input file not found: {audio_path}")
        upload_url = self._upload(audio_path)
        transcript_id = self._submit(upload_url)
        data = self._poll(transcript_id)
        return self._normalize(data)

    # ------------------------------------------------------------------
    # Private helpers — auth header is built inline inside each httpx
    # call so it never exists as a named local variable in the frame.
    # This prevents the Authorization value from appearing in pytest
    # traceback frame-locals output on failures.
    # ------------------------------------------------------------------

    def _upload(self, audio_path: Path) -> str:
        raw_bytes = audio_path.read_bytes()
        try:
            resp = self._client.post(
                f"{self._base_url}/v2/upload",
                headers={"Authorization": self._api_key},
                content=raw_bytes,
                timeout=self._upload_timeout,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AdapterTranscriptionError(
                f"AssemblyAI upload failed: HTTP {exc.response.status_code}"
            ) from None
        return resp.json()["upload_url"]

    def _submit(self, upload_url: str) -> str:
        try:
            resp = self._client.post(
                f"{self._base_url}/v2/transcript",
                headers={"Authorization": self._api_key, "Content-Type": "application/json"},
                json={"audio_url": upload_url, "speech_models": self._speech_models},
                timeout=self._submit_timeout,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AdapterTranscriptionError(
                f"AssemblyAI submit failed: HTTP {exc.response.status_code}"
            ) from None
        return resp.json()["id"]

    def _poll(self, transcript_id: str) -> dict[str, Any]:
        elapsed = 0.0
        while True:
            try:
                resp = self._client.get(
                    f"{self._base_url}/v2/transcript/{transcript_id}",
                    headers={"Authorization": self._api_key},
                    timeout=self._poll_timeout,
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise AdapterTranscriptionError(
                    f"AssemblyAI poll failed: HTTP {exc.response.status_code}"
                ) from None

            data: dict[str, Any] = resp.json()
            status = data.get("status", "")

            if status == "completed":
                return data
            if status == "error":
                msg = data.get("error") or "Provider reported an error"
                raise AdapterTranscriptionError(msg)

            # Non-terminal status; check timeout before sleeping
            if elapsed >= self._max_wait:
                raise AdapterTranscriptionError(
                    f"Polling timed out after {elapsed:.0f}s"
                )
            self._sleep(self._poll_interval)
            elapsed += self._poll_interval

    @staticmethod
    def _normalize(data: dict[str, Any]) -> ASRResult:
        return ASRResult(
            text=data.get("text") or "",
            language=data.get("language_code"),
            duration_seconds=data.get("audio_duration"),
            segments=data.get("utterances") or [],
            words=data.get("words") or [],
            provider="assemblyai",
            provider_job_id=data["id"],
            raw_payload=data,
        )
