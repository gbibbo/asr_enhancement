from __future__ import annotations


class AdapterError(Exception):
    """Base class for all ASR adapter errors."""


class InputFileNotFoundError(AdapterError):
    """Raised when the input audio file does not exist."""


class AdapterTranscriptionError(AdapterError):
    """Raised when the adapter fails to produce a transcript."""


class AdapterHTTPError(AdapterTranscriptionError):
    """Raised when an HTTP request to a provider returns a non-2xx status."""

    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class AdapterTimeoutError(AdapterTranscriptionError):
    """Raised when an HTTP request to a provider times out."""
