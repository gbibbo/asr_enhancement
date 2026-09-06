from __future__ import annotations


class AdapterError(Exception):
    """Base class for all ASR adapter errors."""


class InputFileNotFoundError(AdapterError):
    """Raised when the input audio file does not exist."""


class AdapterTranscriptionError(AdapterError):
    """Raised when the adapter fails to produce a transcript."""
