from __future__ import annotations

import dataclasses
import json
import logging
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from libs.asr_adapter.factory import make_asr_adapter
from libs.audio_pipeline.errors import UnknownPresetError
from libs.audio_pipeline.pipeline import apply_preset
from libs.common.db import make_engine, make_session_factory
from libs.common.models import Job, JobMode, JobStatus
from libs.common.settings import get_settings
from libs.common.storage import StorageClient
from libs.observability.metrics import JOB_COUNTER
from services.worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)


def _enum_or_str(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


@dataclasses.dataclass(frozen=True)
class JobSnapshot:
    id: uuid.UUID
    status: JobStatus
    raw_audio_uri: Optional[str]
    mode: str = "transcribe_only"
    preset: str = "bypass"


# ---------------------------------------------------------------------------
# DB helpers  (each creates/disposes its own engine — monkeypatchable)
# ---------------------------------------------------------------------------

def _load_job(database_url: str, job_id: uuid.UUID) -> Optional[JobSnapshot]:
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            return JobSnapshot(
                id=job.id,
                status=job.status,
                raw_audio_uri=job.raw_audio_uri,
                mode=_enum_or_str(job.mode or JobMode.transcribe_only),
                preset=job.preset or "bypass",
            )
    finally:
        engine.dispose()


def _mark_job_running(database_url: str, job_id: uuid.UUID) -> None:
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = session.get(Job, job_id)
            if job is not None:
                job.status = JobStatus.running
                job.started_at = datetime.now(timezone.utc)
                session.commit()
    finally:
        engine.dispose()


def _mark_job_completed(
    database_url: str,
    job_id: uuid.UUID,
    transcript_text: str,
    transcript_uri: str,
    provider_payload_uri: Optional[str] = None,
    enhanced_audio_uri: Optional[str] = None,
) -> None:
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = session.get(Job, job_id)
            if job is not None:
                job.status = JobStatus.completed
                job.transcript_text = transcript_text
                job.transcript_uri = transcript_uri
                job.provider_payload_uri = provider_payload_uri
                job.enhanced_audio_uri = enhanced_audio_uri
                job.completed_at = datetime.now(timezone.utc)
                session.commit()
    finally:
        engine.dispose()


def _mark_job_failed(
    database_url: str, job_id: uuid.UUID, error_message: str
) -> None:
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = session.get(Job, job_id)
            if job is not None:
                job.status = JobStatus.failed
                job.error_message = error_message
                job.completed_at = datetime.now(timezone.utc)
                session.commit()
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Storage helper
# ---------------------------------------------------------------------------

def _uri_to_key(uri: str, bucket: str) -> str:
    prefix = f"s3://{bucket}/"
    if not uri.startswith(prefix):
        raise ValueError(f"Unexpected URI format: {uri!r}")
    return uri[len(prefix):]


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@celery_app.task(name="worker.transcribe_job")
def transcribe_job(job_id: str) -> None:
    # Step 0: parse job_id — malformed strings exit silently
    try:
        job_id_uuid = uuid.UUID(job_id)
    except ValueError:
        logger.error("transcribe_job: malformed job_id=%r; skipping", job_id, extra={"job_id": job_id})
        return

    logger.info("worker.job_received", extra={"job_id": job_id})
    settings = get_settings()

    # Step 1: load job
    job = _load_job(settings.database_url, job_id_uuid)
    if job is None:
        logger.error("transcribe_job: job_id=%s not found; skipping", job_id, extra={"job_id": job_id})
        return

    # Step 2: idempotency / status guard
    if job.status == JobStatus.completed:
        logger.info("transcribe_job: job_id=%s already completed; skipping", job_id, extra={"job_id": job_id})
        return
    if job.status == JobStatus.failed:
        logger.info("transcribe_job: job_id=%s already failed; skipping", job_id, extra={"job_id": job_id})
        return
    if job.status == JobStatus.running:
        logger.warning("transcribe_job: job_id=%s already running; skipping", job_id, extra={"job_id": job_id})
        return

    # Step 3: mark running
    _mark_job_running(settings.database_url, job_id_uuid)
    JOB_COUNTER.labels(status="running", mode=job.mode).inc()
    logger.info("worker.job_running", extra={"job_id": job_id, "mode": job.mode, "preset": job.preset})

    # Steps 4a–4f: processing — any exception marks the job failed
    try:
        # 4a: validate raw_audio_uri
        if not job.raw_audio_uri:
            raise RuntimeError(f"Job {job_id_uuid} has no raw_audio_uri")

        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "input_audio"

            # 4b: download raw audio
            audio_key = _uri_to_key(job.raw_audio_uri, settings.minio_bucket)
            storage = StorageClient.from_settings(settings)
            storage.get_to_file(audio_key, audio_path)

            # 4c: enhancement (enhance_and_transcribe mode only)
            asr_input_path = audio_path
            enhanced_audio_uri = None
            enhancement_meta: dict = {}

            if job.mode == "enhance_and_transcribe":
                output_dir = Path(tmp_dir) / "enhanced"
                enh = apply_preset(job.preset, audio_path, output_dir)

                if enh.enhanced and not enh.enhancement_fallback:
                    enhanced_key = f"enhanced_audio/{job_id}/output.wav"
                    enhanced_audio_uri = storage.put(
                        enhanced_key, enh.output_path, content_type="audio/wav"
                    )
                    asr_input_path = enh.output_path

                enhancement_meta = {
                    "enhancement_preset": enh.preset_applied,
                    "enhancement_applied": enh.enhanced,
                    "enhancement_fallback": enh.enhancement_fallback,
                    "enhancement_diagnostic": enh.diagnostic,
                }

            # 4d: call ASR adapter (provider determined by settings)
            adapter = make_asr_adapter(settings)
            result = adapter.transcribe(asr_input_path, job_id)

            # 4e: persist transcript JSON to object storage
            transcript_key = f"transcripts/{job_id}/transcript.json"
            transcript_data = dataclasses.asdict(result)
            transcript_data.update(enhancement_meta)
            payload = json.dumps(transcript_data).encode("utf-8")
            transcript_uri = storage.put(
                transcript_key,
                payload,
                content_type="application/json",
            )

            # 4e2: persist raw provider payload when present (non-empty)
            provider_payload_uri = None
            if result.raw_payload:
                payload_key = f"provider_payloads/{job_id}/provider_response.json"
                provider_payload_data = json.dumps(result.raw_payload).encode("utf-8")
                provider_payload_uri = storage.put(
                    payload_key,
                    provider_payload_data,
                    content_type="application/json",
                )

            # 4f: artifact existence check
            if not storage.exists(transcript_key):
                raise RuntimeError(
                    f"Transcript artifact missing after upload: {transcript_key!r}"
                )

            # 4g: persist to PostgreSQL and mark completed
            _mark_job_completed(
                settings.database_url, job_id_uuid, result.text, transcript_uri,
                provider_payload_uri, enhanced_audio_uri,
            )
            JOB_COUNTER.labels(status="completed", mode=job.mode).inc()
            logger.info("worker.job_completed", extra={"job_id": job_id, "mode": job.mode, "preset": job.preset})

    except Exception as exc:
        JOB_COUNTER.labels(status="failed", mode=job.mode).inc()
        logger.exception("worker.job_failed", extra={"job_id": job_id})
        try:
            _mark_job_failed(settings.database_url, job_id_uuid, str(exc))
        except Exception as fail_exc:
            logger.error(
                "transcribe_job: could not mark job %s failed: %s", job_id, fail_exc,
                extra={"job_id": job_id},
            )
