from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

import redis as redis_lib
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import text

from libs.common.db import make_engine, make_session_factory
from libs.common.models import Job, JobMode, JobStatus
from libs.common.settings import Settings, get_settings
from libs.common.storage import StorageClient
from services.api.app.upload_validation import (
    UploadValidationError,
    validate_and_buffer_upload,
)

app = FastAPI(title="ASR Enhancement Platform", version="0.1.0")

logger = logging.getLogger(__name__)

_READINESS_TIMEOUT = 5.0


# ---------------------------------------------------------------------------
# Readiness helpers
# ---------------------------------------------------------------------------

def _check_postgres(database_url: str) -> dict[str, Any]:
    engine = make_engine(database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "error": None}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        engine.dispose()


def _check_redis(redis_url: str) -> dict[str, Any]:
    client = None
    try:
        client = redis_lib.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        return {"status": "ok", "error": None}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        if client is not None:
            client.close()


def _check_storage(settings: Settings) -> dict[str, Any]:
    try:
        sc = StorageClient.from_settings(settings)
        sc.ensure_bucket(create_if_missing=False)
        return {"status": "ok", "error": None}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Transcribe helpers  (each creates/disposes its own engine — monkeypatchable)
# ---------------------------------------------------------------------------

def _create_job(database_url: str, mode: JobMode, provider: str) -> uuid.UUID:
    job_id = uuid.uuid4()
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = Job(
                id=job_id,
                status=JobStatus.queued,
                mode=mode,
                provider=provider,
                preset="bypass",
            )
            session.add(job)
            session.commit()
        return job_id
    finally:
        engine.dispose()


def _set_raw_audio_uri(
    database_url: str, job_id: uuid.UUID, raw_audio_uri: str
) -> None:
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = session.get(Job, job_id)
            if job is None:
                raise RuntimeError(
                    f"Job {job_id} not found when updating raw_audio_uri"
                )
            job.raw_audio_uri = raw_audio_uri
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
                session.commit()
    finally:
        engine.dispose()


def _upload_raw_audio(
    settings: Settings,
    job_id: uuid.UUID,
    tmp_path: Path,
    ext: str,
    content_type: Optional[str],
) -> str:
    key = f"raw_audio/{job_id}/input{ext}"
    sc = StorageClient.from_settings(settings)
    return sc.put(key, tmp_path, content_type=content_type or "application/octet-stream")


def _enqueue_transcribe(job_id: str) -> None:
    from services.worker.app.celery_app import celery_app  # lazy — avoids module-level settings init
    celery_app.send_task("worker.transcribe_job", args=[job_id])


# ---------------------------------------------------------------------------
# Exception handlers  (UploadValidationError must be before generic Exception)
# ---------------------------------------------------------------------------

@app.exception_handler(UploadValidationError)
async def _upload_validation_error_handler(
    request: Request, exc: UploadValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> JSONResponse:
    settings = get_settings()

    async def _run(fn, *args, name: str) -> dict[str, Any]:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(fn, *args),
                timeout=_READINESS_TIMEOUT,
            )
        except asyncio.TimeoutError:
            return {"status": "error", "error": f"{name} check timed out"}

    pg, rd, st = await asyncio.gather(
        _run(_check_postgres, settings.database_url, name="postgres"),
        _run(_check_redis, settings.redis_url, name="redis"),
        _run(_check_storage, settings, name="storage"),
    )

    deps = {"postgres": pg, "redis": rd, "storage": st}
    all_ok = all(d["status"] == "ok" for d in deps.values())
    return JSONResponse(
        content={"status": "ok" if all_ok else "degraded", "dependencies": deps},
        status_code=200 if all_ok else 503,
    )


@app.post("/v1/transcribe")
async def transcribe(file: UploadFile = File(...)) -> JSONResponse:
    settings = get_settings()

    tmp_dir: Optional[Path] = None
    if settings.asr_runtime_root is not None:
        tmp_dir = settings.asr_runtime_root / "uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: validate upload — UploadValidationError propagates to its handler;
        # the validator deletes any temp file it created before raising.
        validated = await validate_and_buffer_upload(
            file,
            settings.upload_limit_bytes,
            tmp_dir=tmp_dir,
        )

        try:
            # Step 2: create job row
            try:
                job_id = await asyncio.to_thread(
                    _create_job,
                    settings.database_url,
                    JobMode.transcribe_only,
                    settings.asr_provider,
                )
            except Exception as exc:
                logger.error("Job creation failed: %s", exc)
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "internal_server_error",
                        "detail": "Failed to create job",
                    },
                )

            # Step 3: upload raw audio to MinIO
            try:
                raw_audio_uri = await asyncio.to_thread(
                    _upload_raw_audio,
                    settings,
                    job_id,
                    validated.path,
                    validated.extension,
                    validated.content_type,
                )
            except Exception as exc:
                logger.error("Raw audio upload failed for job %s: %s", job_id, exc)
                await asyncio.to_thread(
                    _mark_job_failed,
                    settings.database_url,
                    job_id,
                    f"Raw audio upload failed: {exc}",
                )
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "internal_server_error",
                        "detail": "Failed to persist audio",
                    },
                )

            # Step 3b: persist raw_audio_uri in DB
            try:
                await asyncio.to_thread(
                    _set_raw_audio_uri, settings.database_url, job_id, raw_audio_uri
                )
            except Exception as exc:
                logger.error(
                    "Failed to update raw_audio_uri for job %s: %s", job_id, exc
                )
                await asyncio.to_thread(
                    _mark_job_failed,
                    settings.database_url,
                    job_id,
                    f"Failed to record audio URI: {exc}",
                )
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "internal_server_error",
                        "detail": "Failed to persist audio",
                    },
                )

            # Step 4: enqueue Celery task
            try:
                await asyncio.to_thread(_enqueue_transcribe, str(job_id))
            except Exception as exc:
                logger.error("Task enqueue failed for job %s: %s", job_id, exc)
                await asyncio.to_thread(
                    _mark_job_failed,
                    settings.database_url,
                    job_id,
                    f"Task enqueue failed: {exc}",
                )
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "internal_server_error",
                        "detail": "Failed to queue transcription task",
                    },
                )

            return JSONResponse(
                status_code=202,
                content={"job_id": str(job_id), "status": "queued"},
            )

        finally:
            validated.path.unlink(missing_ok=True)

    finally:
        await file.close()
