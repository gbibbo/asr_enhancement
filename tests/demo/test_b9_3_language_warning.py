"""B9.3 — non-English language warning tests.

Covers ``libs/demo/processing.py``: the ``_language_warning`` helper and its
wiring into ``process_upload_job``. All ASR is mocked via ``_FakeASR``; no
real faster-whisper, no real audio content, no AssemblyAI, no network.

Privacy invariant: no test asserts on or logs ground-truth text. The
``_FakeASR.text`` value is a neutral placeholder, never a transcript of the
synthetic input. The backend MUST NOT see GT in B9.3 (or B9.x).
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pytest
import soundfile as sf

from libs.asr.errors import AdapterTranscriptionError
from libs.asr.schema import ASRResult


_DEMO_ENV_VARS = [
    "DEMO_RUNTIME_ROOT",
    "DEMO_DB_PATH",
    "DEMO_UPLOAD_DIR",
    "DEMO_CACHE_DIR",
    "DEMO_ARTIFACTS_DIR",
    "DEMO_LOGS_DIR",
    "DEMO_WORKER_CONCURRENCY",
    "DEMO_QUEUE_MAX",
    "DEMO_UPLOAD_LIMIT_BYTES",
    "DEMO_UPLOAD_MAX_DURATION_SECONDS",
    "ASSEMBLYAI_API_KEY",
    "ENHANCER_VERSION",
    "ADMIN_STATS_USERNAME",
    "ADMIN_STATS_PASSWORD",
    "DEMO_EXAMPLES_CONFIG",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings(tmp_path, monkeypatch):
    for var in _DEMO_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEMO_RUNTIME_ROOT", str(tmp_path))
    from libs.common.demo_settings import DemoSettings
    return DemoSettings()


@pytest.fixture()
def db_path(settings):
    from libs.demo.persistence import ensure_runtime_dirs, init_schema
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    return settings.demo_db_path


def _write_tone_wav(path: Path, *, seconds: float = 0.5, samplerate: int = 16000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(seconds * samplerate))
    t = np.arange(n, dtype=np.float64) / samplerate
    samples = (0.2 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
    sf.write(path, samples, samplerate, subtype="PCM_16")
    return path


def _insert_upload_job(
    db_path: Path,
    *,
    input_artifact_path: str,
    provider: str = "whisper",
    enhancer_version: Optional[str] = "bypass",
    degradation_id: Optional[str] = None,
) -> dict:
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO jobs
          (job_id, status, created_at, updated_at, provider,
           degradation_id, enhancer_version, input_artifact_path)
        VALUES (?, 'queued', ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            now,
            now,
            provider,
            degradation_id,
            enhancer_version,
            input_artifact_path,
        ),
    )
    conn.commit()
    conn.close()
    return {
        "job_id": job_id,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "provider": provider,
        "degradation_id": degradation_id,
        "enhancer_version": enhancer_version,
        "input_artifact_path": input_artifact_path,
    }


class _FakeASR:
    """Mocked ASR adapter that returns configurable language metadata.

    Supports omitting ``language_probability`` from ``raw_payload`` (set
    ``include_probability=False``) and overriding the value with a non-numeric
    type (``probability_value``) to exercise the suppression branches.
    """

    def __init__(
        self,
        *,
        text: str = "hello world",
        language: Optional[str] = "en",
        language_probability: float = 0.99,
        include_language: bool = True,
        include_probability: bool = True,
        probability_value: Any = None,
        raise_on_call: int = 0,
        raise_exc: Optional[BaseException] = None,
    ) -> None:
        self.text = text
        self.language = language
        self.language_probability = language_probability
        self.include_language = include_language
        self.include_probability = include_probability
        self.probability_value = probability_value
        self.raise_on_call = raise_on_call
        self.raise_exc = raise_exc
        self.calls: list[Path] = []

    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult:
        self.calls.append(audio_path)
        if self.raise_exc is not None and len(self.calls) == self.raise_on_call:
            raise self.raise_exc
        raw: dict[str, Any] = {"model": "tiny.en"}
        if self.include_language:
            raw["language"] = self.language
        if self.include_probability:
            raw["language_probability"] = (
                self.probability_value
                if self.probability_value is not None
                else self.language_probability
            )
        return ASRResult(
            text=self.text,
            language=self.language if self.include_language else None,
            duration_seconds=None,
            segments=[{"start": 0.0, "end": 0.5, "text": self.text}],
            words=[],
            provider="whisper",
            provider_job_id=None,
            raw_payload=raw,
        )


def _factory(value):
    return lambda _name: value


def _record_artifacts(store: list):
    def _impl(**kwargs):
        store.append(kwargs)
    return _impl


# ---------------------------------------------------------------------------
# _language_warning helper — direct unit tests
# ---------------------------------------------------------------------------


def _make_result(language: Any, probability: Any) -> ASRResult:
    raw: dict[str, Any] = {"model": "tiny.en"}
    if language is not _SENTINEL:
        raw["language"] = language
    if probability is not _SENTINEL:
        raw["language_probability"] = probability
    return ASRResult(
        text="placeholder",
        language=language if language is not _SENTINEL else None,
        duration_seconds=None,
        segments=[],
        words=[],
        provider="whisper",
        provider_job_id=None,
        raw_payload=raw,
    )


_SENTINEL = object()


def test_helper_returns_none_for_english():
    from libs.demo.processing import _language_warning

    assert _language_warning(_make_result("en", 0.99)) is None


def test_helper_returns_dict_for_non_english_above_threshold():
    from libs.demo.processing import (
        NON_ENGLISH_WARNING_CODE,
        NON_ENGLISH_WARNING_MESSAGE,
        _language_warning,
    )

    out = _language_warning(_make_result("fr", 0.83))
    assert out is not None
    assert out == {
        "code": NON_ENGLISH_WARNING_CODE,
        "message": NON_ENGLISH_WARNING_MESSAGE,
        "detected_language": "fr",
        "language_probability": 0.83,
    }


def test_helper_returns_none_when_probability_missing():
    from libs.demo.processing import _language_warning

    assert _language_warning(_make_result("fr", _SENTINEL)) is None


def test_helper_returns_none_when_probability_non_numeric():
    from libs.demo.processing import _language_warning

    # raw_payload["language_probability"] = "high" → _language_probability returns None
    assert _language_warning(_make_result("fr", "high")) is None


def test_helper_returns_none_when_language_missing_or_blank():
    from libs.demo.processing import _language_warning

    assert _language_warning(_make_result(None, 0.9)) is None
    assert _language_warning(_make_result("", 0.9)) is None


# ---------------------------------------------------------------------------
# process_upload_job — warning-emission paths
# ---------------------------------------------------------------------------


def test_warning_emitted_for_non_english_above_threshold(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import (
        NON_ENGLISH_WARNING_CODE,
        NON_ENGLISH_WARNING_MESSAGE,
        process_upload_job,
    )

    upload = _write_tone_wav(settings.demo_upload_dir / "u_fr.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(language="fr", language_probability=0.83)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    warnings = outcome.result["warnings"]
    assert isinstance(warnings, list)
    assert len(warnings) == 1
    w = warnings[0]
    assert w["code"] == NON_ENGLISH_WARNING_CODE
    assert w["message"] == NON_ENGLISH_WARNING_MESSAGE
    assert w["detected_language"] == "fr"
    assert w["language_probability"] == pytest.approx(0.83)


def test_no_warning_for_english(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_en.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(language="en", language_probability=0.99)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    assert outcome.result["warnings"] == []


@pytest.mark.parametrize("probability", [0.0, 0.1, 0.49, 0.5])
def test_no_warning_when_probability_at_or_below_threshold(settings, db_path, probability):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / f"u_low_{probability}.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(language="fr", language_probability=probability)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    assert outcome.result["warnings"] == []


def test_no_warning_when_probability_missing(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_no_prob.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(language="fr", include_probability=False)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    assert outcome.result["warnings"] == []
    # raw still surfaces what the adapter reported
    assert outcome.result["raw"]["language_probability"] is None


def test_no_warning_when_language_missing(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_no_lang.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(include_language=False, language_probability=0.9)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    assert outcome.result["warnings"] == []


def test_warning_emitted_independent_of_degradation(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_fr_muffled.wav", seconds=0.5)
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        degradation_id="muffled",
    )
    asr = _FakeASR(language="es", language_probability=0.7)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    r = outcome.result
    assert r["degradation_id"] == "muffled"
    assert r["degradation_applied"] is True
    assert r["degraded_audio_path"] is not None
    assert len(r["warnings"]) == 1
    assert r["warnings"][0]["detected_language"] == "es"


def test_warning_present_when_enhanced_path_fails(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_fr_enh_fail.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    # raise on the second transcribe call (the enhanced path)
    asr = _FakeASR(
        language="fr",
        language_probability=0.83,
        raise_on_call=2,
        raise_exc=AdapterTranscriptionError("boom"),
    )

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "completed"
    r = outcome.result
    assert r["enhanced"] is None
    assert r["enhanced_error"] is not None
    assert "Enhanced path unavailable" in r["enhanced_error"]
    assert len(r["warnings"]) == 1
    assert r["warnings"][0]["code"] == "non_english_language"


def test_warning_only_computed_once_for_completed_job(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_once.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(language="de", language_probability=0.9)

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    # raw + enhanced both ran
    assert len(asr.calls) == 2
    # but the warning was added only once at the top level
    assert len(outcome.result["warnings"]) == 1


def test_failed_raw_asr_returns_no_result_so_no_warning_field(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u_raw_fail.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    # raise on the first transcribe call (the raw path)
    asr = _FakeASR(
        language="fr",
        language_probability=0.83,
        raise_on_call=1,
        raise_exc=AdapterTranscriptionError("raw boom"),
    )

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts([]),
    )

    assert outcome.status == "failed"
    assert outcome.result is None


def test_warning_message_text_matches_canonical():
    from libs.demo.processing import NON_ENGLISH_WARNING_MESSAGE

    assert NON_ENGLISH_WARNING_MESSAGE == (
        "Detected language is not English. This demo is designed for English speech, "
        "so results may be unreliable. Continue?"
    )
