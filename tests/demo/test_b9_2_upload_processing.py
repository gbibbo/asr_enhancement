"""B9.2 — upload processing flow tests.

Covers ``libs/demo/processing.py`` (process_upload_job + factories) and the
new ``update_job_artifacts`` persistence helper. No AssemblyAI, no real
faster-whisper, no network.
"""

from __future__ import annotations

import io
import json
import logging
import sqlite3
import struct
import uuid
import wave
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
    """Returns a fixed transcript and counts calls per audio path."""

    def __init__(
        self,
        *,
        text: str = "hello world",
        language: str = "en",
        language_probability: float = 0.99,
        raise_on_call: int = 0,
        raise_exc: Optional[BaseException] = None,
    ) -> None:
        self.text = text
        self.language = language
        self.language_probability = language_probability
        self.raise_on_call = raise_on_call
        self.raise_exc = raise_exc
        self.calls: list[Path] = []

    def transcribe(self, audio_path: Path, job_id: str) -> ASRResult:
        self.calls.append(audio_path)
        if self.raise_exc is not None and len(self.calls) == self.raise_on_call:
            raise self.raise_exc
        return ASRResult(
            text=self.text,
            language=self.language,
            duration_seconds=None,
            segments=[{"start": 0.0, "end": 0.5, "text": self.text}],
            words=[],
            provider="whisper",
            provider_job_id=None,
            raw_payload={
                "model": "tiny.en",
                "language": self.language,
                "language_probability": self.language_probability,
            },
        )


def _factory(value):
    return lambda _name: value


def _record_artifacts(store: list):
    def _impl(**kwargs):
        store.append(kwargs)
    return _impl


# ---------------------------------------------------------------------------
# process_upload_job — happy paths
# ---------------------------------------------------------------------------


def test_no_degradation_bypass_returns_raw_and_enhanced(settings, db_path, tmp_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u1.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(text="hello world")
    artifacts: list = []

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts(artifacts),
    )

    assert outcome.status == "completed"
    assert outcome.error_message is None
    r = outcome.result
    assert r["source_type"] == "upload"
    assert r["provider"] == "whisper"
    assert r["asr_model_version"] == "tiny.en"
    assert r["enhancer_version"] == "bypass"
    assert r["degradation_id"] is None
    assert r["degradation_version"] is None
    assert r["degradation_applied"] is False
    assert r["degraded_audio_path"] is None
    assert r["enhanced_audio_path"] is None
    assert r["raw"]["transcript"] == "hello world"
    assert r["raw"]["language"] == "en"
    assert r["raw"]["language_probability"] == pytest.approx(0.99)
    assert r["raw"]["latency_seconds"] >= 0
    assert r["enhanced"] is not None
    assert r["enhanced"]["transcript"] == "hello world"
    assert r["enhanced"]["preset_applied"] == "bypass"
    assert r["enhanced"]["enhanced_flag"] is False
    assert r["enhanced"]["enhancement_fallback"] is False
    assert r["enhanced_error"] is None
    assert r["metrics"] == {}
    assert r["warnings"] == []
    assert artifacts == []  # bypass never writes a separate enhanced file
    # B10.2 bypass optimization: when enhancement.output_path == raw_input_path
    # (BypassEnhancer), the enhanced block reuses the raw transcribe result and
    # the second ASR call is suppressed.
    assert len(asr.calls) == 1
    assert asr.calls[0] == upload


def test_known_degradation_writes_file_and_persists_path(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u2.wav", seconds=0.5)
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        degradation_id="muffled",
    )
    asr = _FakeASR()
    artifacts: list = []

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts(artifacts),
    )

    assert outcome.status == "completed"
    expected_dir = settings.demo_artifacts_dir / "jobs" / job["job_id"]
    expected_file = expected_dir / "muffled.wav"
    assert expected_file.is_file()
    r = outcome.result
    assert r["degradation_id"] == "muffled"
    assert r["degradation_applied"] is True
    assert r["degradation_version"]  # set from libs.audio.degradations
    assert r["degraded_audio_path"] == str(expected_file)
    # B10.2 bypass optimization: BypassEnhancer returns the same path it was
    # given, so the worker reuses the raw transcribe result for the enhanced
    # block and does not call ASR a second time.
    assert asr.calls == [expected_file]
    # update_artifacts called once for degraded; no enhanced file persisted
    assert artifacts == [{"degraded_artifact_path": str(expected_file)}]


# ---------------------------------------------------------------------------
# process_upload_job — failure / rejection paths
# ---------------------------------------------------------------------------


def test_unknown_degradation_id_fails_clean(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u3.wav")
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        degradation_id="totally_made_up",
    )
    artifacts: list = []

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(_FakeASR()),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts(artifacts),
    )

    assert outcome.status == "failed"
    assert "Unknown degradation_id" in outcome.error_message
    assert outcome.result is None
    assert artifacts == []


def test_missing_input_file_fails(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(settings.demo_upload_dir / "missing.wav"),
    )
    artifacts: list = []

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(_FakeASR()),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts(artifacts),
    )

    assert outcome.status == "failed"
    assert outcome.error_message == "Uploaded audio file is missing."
    assert outcome.result is None
    assert artifacts == []


def test_blank_input_path_fails(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    job = _insert_upload_job(db_path, input_artifact_path="")
    artifacts: list = []

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(_FakeASR()),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=_record_artifacts(artifacts),
    )

    assert outcome.status == "failed"
    assert outcome.error_message == "Uploaded audio file is missing."


def test_rejects_metricgan_enhancer_with_t41_message(settings, db_path):
    from libs.demo.processing import default_enhancer_factory, process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u4.wav")
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        enhancer_version="metricgan_plus_pretrained",
    )
    artifacts: list = []

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(_FakeASR()),
        enhancer_factory=default_enhancer_factory(settings),
        update_artifacts=_record_artifacts(artifacts),
    )

    assert outcome.status == "failed"
    assert "T4.1" in outcome.error_message
    assert "bypass" in outcome.error_message
    assert artifacts == []


def test_rejects_unknown_enhancer(settings, db_path):
    from libs.demo.processing import default_enhancer_factory, process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u4b.wav")
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        enhancer_version="some_future_thing",
    )

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(_FakeASR()),
        enhancer_factory=default_enhancer_factory(settings),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "failed"
    assert "Unsupported enhancer" in outcome.error_message


def test_rejects_assemblyai_provider_when_no_key(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import default_asr_factory, process_upload_job
    from libs.demo.usage import MSG_DISABLED

    # The fixture clears ASSEMBLYAI_API_KEY, so default_asr_factory must
    # raise ProviderDisabledError with the canonical disabled message.
    upload = _write_tone_wav(settings.demo_upload_dir / "u5.wav")
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        provider="assemblyai",
    )

    outcome = process_upload_job(
        job, settings,
        asr_factory=default_asr_factory(settings),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "failed"
    assert outcome.error_message == MSG_DISABLED


def test_assemblyai_factory_returns_demo_adapter_when_key_configured(
    settings, monkeypatch
):
    from libs.asr.demo_assemblyai_provider import DemoAssemblyAIAdapter
    from libs.demo.processing import default_asr_factory

    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "sk-test-key")
    from libs.common.demo_settings import DemoSettings
    s = DemoSettings()
    factory = default_asr_factory(s)
    adapter = factory("assemblyai")
    assert isinstance(adapter, DemoAssemblyAIAdapter)


def test_rejects_unknown_provider(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import default_asr_factory, process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u5b.wav")
    job = _insert_upload_job(
        db_path,
        input_artifact_path=str(upload),
        provider="madeup",
    )

    outcome = process_upload_job(
        job, settings,
        asr_factory=default_asr_factory(settings),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "failed"
    assert "Unsupported provider" in outcome.error_message


def test_raw_asr_failure_marks_job_failed(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u6.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(raise_on_call=1, raise_exc=AdapterTranscriptionError("network down"))

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "failed"
    assert outcome.error_message.startswith("Raw ASR failed")
    assert outcome.result is None


def test_enhanced_asr_failure_keeps_raw_completed(settings, db_path):
    """Second ASR call can only fire when the enhancer rewrites the audio.

    Post-B10.2 BypassEnhancer reuses the raw transcribe result, so this
    coverage uses a fake enhancer that writes a distinct file to force a
    second ASR call.
    """
    from dataclasses import dataclass
    from libs.demo.processing import process_upload_job

    @dataclass
    class _FakeEnhancement:
        output_path: Path
        preset_applied: str = "fake_distinct"
        enhanced: bool = True
        enhancement_fallback: bool = False

    class _DistinctEnhancer:
        @property
        def enhancer_version(self) -> str:  # pragma: no cover - not exercised
            return "fake_distinct"

        def enhance(self, audio_path: Path, output_dir: Path, job_id: str):
            output_dir.mkdir(parents=True, exist_ok=True)
            out = output_dir / "enhanced.wav"
            out.write_bytes(audio_path.read_bytes())
            return _FakeEnhancement(output_path=out)

    upload = _write_tone_wav(settings.demo_upload_dir / "u7.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    # First call (raw) succeeds, second call (enhanced on the distinct file) raises.
    asr = _FakeASR(
        text="raw transcript",
        raise_on_call=2,
        raise_exc=AdapterTranscriptionError("enhanced step boom"),
    )

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(_DistinctEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "completed"
    r = outcome.result
    assert r["raw"]["transcript"] == "raw transcript"
    assert r["enhanced"] is None
    assert r["enhanced_error"]
    assert r["enhanced_error"].startswith("Enhanced path unavailable")


def test_enhancer_raise_keeps_raw_completed(settings, db_path):
    """If the enhancer's enhance() itself raises, the job still completes."""
    from libs.demo.processing import process_upload_job

    class _BoomEnhancer:
        @property
        def enhancer_version(self) -> str:  # pragma: no cover - not exercised
            return "bypass"

        def enhance(self, audio_path, output_dir, job_id):  # noqa: D401
            raise RuntimeError("preset crashed hard")

    upload = _write_tone_wav(settings.demo_upload_dir / "u7b.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(text="hello")

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(_BoomEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    assert outcome.status == "completed"
    assert outcome.result["enhanced"] is None
    assert outcome.result["enhanced_error"].startswith("Enhanced path unavailable")
    # Only the raw ASR call happened
    assert len(asr.calls) == 1


# ---------------------------------------------------------------------------
# Result schema and privacy
# ---------------------------------------------------------------------------


def test_result_json_schema_top_level_keys(settings, db_path):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    upload = _write_tone_wav(settings.demo_upload_dir / "u8.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))

    outcome = process_upload_job(
        job, settings,
        asr_factory=_factory(_FakeASR()),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    expected = {
        "source_type", "provider", "asr_model_version", "enhancer_version",
        "degradation_id", "degradation_version", "degradation_applied",
        "input_audio_path", "degraded_audio_path", "enhanced_audio_path",
        "raw", "enhanced", "enhanced_error", "metrics", "warnings",
    }
    assert set(outcome.result.keys()) == expected
    serialized = json.dumps(outcome.result)
    assert "ground_truth" not in serialized
    assert outcome.result["metrics"] == {}
    assert outcome.result["warnings"] == []


def test_logs_do_not_contain_transcripts_or_filenames(settings, db_path, caplog):
    from libs.audio.enhancement import BypassEnhancer
    from libs.demo.processing import process_upload_job

    secret_transcript = "supersecrettranscriptcontent"
    upload = _write_tone_wav(settings.demo_upload_dir / "u9.wav")
    job = _insert_upload_job(db_path, input_artifact_path=str(upload))
    asr = _FakeASR(text=secret_transcript)

    caplog.set_level(logging.INFO, logger="demo-worker.processing")
    process_upload_job(
        job, settings,
        asr_factory=_factory(asr),
        enhancer_factory=_factory(BypassEnhancer()),
        update_artifacts=lambda **kw: None,
    )

    captured = "\n".join(record.getMessage() for record in caplog.records)
    assert secret_transcript not in captured
    assert "u9.wav" not in captured  # uploaded filename must not leak
    assert "ground_truth" not in captured.lower()
    assert "ground truth" not in captured.lower()


# ---------------------------------------------------------------------------
# update_job_artifacts persistence helper
# ---------------------------------------------------------------------------


def test_update_job_artifacts_writes_only_provided_columns(db_path):
    from libs.demo.persistence import (
        get_job,
        update_job_artifacts,
    )

    # Insert a queued job manually
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider) "
        "VALUES (?, 'queued', ?, ?, 'whisper')",
        (job_id, now, now),
    )
    conn.commit()
    conn.close()

    update_job_artifacts(db_path, job_id, degraded_artifact_path="/abs/deg.wav")
    row = get_job(db_path, job_id)
    assert row["degraded_artifact_path"] == "/abs/deg.wav"
    assert row["enhanced_artifact_path"] is None

    update_job_artifacts(db_path, job_id, enhanced_artifact_path="/abs/enh.wav")
    row = get_job(db_path, job_id)
    assert row["degraded_artifact_path"] == "/abs/deg.wav"
    assert row["enhanced_artifact_path"] == "/abs/enh.wav"


def test_update_job_artifacts_noop_when_both_none(db_path):
    from libs.demo.persistence import get_job, update_job_artifacts

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO jobs (job_id, status, created_at, updated_at, provider) "
        "VALUES (?, 'queued', ?, ?, 'whisper')",
        (job_id, now, now),
    )
    conn.commit()
    conn.close()

    before = get_job(db_path, job_id)
    update_job_artifacts(db_path, job_id)  # both None
    after = get_job(db_path, job_id)
    assert before == after  # updated_at unchanged
