from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import redis as redis_lib
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from opentelemetry import propagate
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy import text

from libs.audio.enhancement import UnknownPresetError, resolve_preset
from libs.common.db import make_engine, make_session_factory
from libs.common.models import Job, JobMode, JobStatus
from libs.common.settings import Settings, get_settings
from libs.common.storage import StorageClient
from libs.observability import configure_logging, configure_tracing
from libs.observability.metrics import (
    API_ERRORS,
    API_REQUESTS,
    CONTENT_TYPE_LATEST,
    JOB_COUNTER,
    get_metrics_output,
)
from services.api.app.rate_limit import RateLimiter
from services.api.app.upload_validation import (
    UploadValidationError,
    validate_and_buffer_upload,
)

_RATE_LIMITED_PATHS: frozenset[str] = frozenset({
    "/v1/transcribe",
    "/v1/enhance-and-transcribe",
})


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("api")
    yield


app = FastAPI(title="ASR Enhancement Platform", version="0.1.0", lifespan=lifespan)
app.state.rate_limiter = RateLimiter(get_settings().rate_limit_per_minute)

# Tracing must be configured and FastAPI must be instrumented BEFORE the middleware
# stack is built. Starlette builds middleware_stack lazily on the first ASGI call —
# which is the lifespan event itself — and caches it.  Lifespan-time instrumentation
# would patch build_middleware_stack too late, so the cached stack would be missing
# the OTel wrapper and HTTP requests would produce no spans.
configure_tracing("asr-api")
if not getattr(app, "_is_instrumented_by_opentelemetry", False):
    FastAPIInstrumentor().instrument_app(app)

logger = logging.getLogger(__name__)

_READINESS_TIMEOUT = 5.0


@app.middleware("http")
async def _request_logger(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    API_REQUESTS.labels(
        method=request.method,
        path=request.url.path,
        status_code=str(response.status_code),
    ).inc()
    logger.info(
        "api.request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


# Starlette wraps middlewares in reverse-add order, so the last added is the
# outermost. Adding _rate_limit_middleware AFTER _request_logger keeps the
# logger as the outermost wrapper, so 429 responses are still counted in
# API_REQUESTS and api.request logs.
@app.middleware("http")
async def _rate_limit_middleware(request: Request, call_next):
    if request.method != "POST" or request.url.path not in _RATE_LIMITED_PATHS:
        return await call_next(request)

    client_key = request.client.host if request.client else "unknown"
    allowed, retry_after = await request.app.state.rate_limiter.is_allowed(client_key)
    if allowed:
        return await call_next(request)

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "detail": "Too many requests. Please try again in a moment.",
        },
        headers={"Retry-After": str(retry_after)},
    )


# ---------------------------------------------------------------------------
# Job status snapshot (immutable; serialized by route, never a detached ORM obj)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class JobStatusSnapshot:
    id: uuid.UUID
    status: Union[JobStatus, str]
    mode: Union[JobMode, str]
    provider: str
    preset: str
    raw_audio_uri: Optional[str]
    enhanced_audio_uri: Optional[str]
    transcript_uri: Optional[str]
    transcript_text: Optional[str]
    error_message: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


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
# Shared helpers  (each creates/disposes its own engine — monkeypatchable)
# ---------------------------------------------------------------------------

def _create_job(
    database_url: str, mode: JobMode, provider: str, preset: str = "bypass"
) -> uuid.UUID:
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
                preset=preset,
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


def _current_traceparent() -> Optional[str]:
    """Inject the W3C traceparent for the currently-active OTel context.

    Must be called from the async request context where the FastAPIInstrumentor
    server span is active. Calling this from inside asyncio.to_thread relies on
    contextvars propagation through the threadpool, which was empirically observed
    to drop the active span context under uvicorn in production (Docker WSL),
    yielding traceparent=None and breaking API→worker trace propagation.
    """
    carrier: dict = {}
    propagate.inject(carrier)
    return carrier.get("traceparent")


def _enqueue_transcribe(job_id: str, traceparent: Optional[str] = None) -> None:
    """Send the worker.transcribe_job Celery task with the W3C traceparent.

    The caller (an async route handler) MUST capture traceparent in its own
    async context via _current_traceparent() and pass it explicitly here.
    The optional default exists only for legacy unit tests that exercise this
    function directly while a span is already active in the test thread.
    """
    from services.worker.app.celery_app import (
        celery_app,  # lazy — avoids module-level settings init
    )
    if traceparent is None:
        traceparent = _current_traceparent()
    # Safe diagnostic — only trace metadata, no secrets or payload content.
    logger.info(
        "api.task_enqueued",
        extra={
            "job_id": job_id,
            "traceparent_present": traceparent is not None,
            "traceparent_trace_id": traceparent.split("-")[1] if traceparent else None,
        },
    )
    celery_app.send_task("worker.transcribe_job", args=[job_id, traceparent])


def _load_job(database_url: str, job_id: uuid.UUID) -> Optional[JobStatusSnapshot]:
    engine = make_engine(database_url)
    try:
        Session = make_session_factory(engine)
        with Session() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            return JobStatusSnapshot(
                id=job.id,
                status=job.status,
                mode=job.mode,
                provider=job.provider,
                preset=job.preset,
                raw_audio_uri=job.raw_audio_uri,
                enhanced_audio_uri=job.enhanced_audio_uri,
                transcript_uri=job.transcript_uri,
                transcript_text=job.transcript_text,
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
            )
    finally:
        engine.dispose()


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
    API_ERRORS.labels(path=request.url.path).inc()
    logger.exception("api.unhandled_exception", extra={"path": request.url.path})
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


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=get_metrics_output(), media_type=CONTENT_TYPE_LATEST)


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
            logger.info("api.job_created", extra={"job_id": str(job_id), "mode": "transcribe_only", "preset": "bypass"})
            JOB_COUNTER.labels(status="queued", mode="transcribe_only").inc()

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
                logger.error("Raw audio upload failed for job %s: %s", job_id, exc, extra={"job_id": str(job_id)})
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
                    "Failed to update raw_audio_uri for job %s: %s", job_id, exc,
                    extra={"job_id": str(job_id)},
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

            # Step 4: enqueue Celery task — capture traceparent in this async
            # context so it is not lost across the asyncio.to_thread boundary.
            traceparent = _current_traceparent()
            try:
                await asyncio.to_thread(_enqueue_transcribe, str(job_id), traceparent)
            except Exception as exc:
                logger.error("Task enqueue failed for job %s: %s", job_id, exc, extra={"job_id": str(job_id)})
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
            logger.info("api.job_enqueued", extra={"job_id": str(job_id)})

            return JSONResponse(
                status_code=202,
                content={"job_id": str(job_id), "status": "queued"},
            )

        finally:
            validated.path.unlink(missing_ok=True)

    finally:
        await file.close()


@app.post("/v1/enhance-and-transcribe")
async def enhance_and_transcribe(
    file: UploadFile = File(...),
    preset: Optional[str] = Form(None),
) -> JSONResponse:
    settings = get_settings()

    tmp_dir: Optional[Path] = None
    if settings.asr_runtime_root is not None:
        tmp_dir = settings.asr_runtime_root / "uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: validate upload
        validated = await validate_and_buffer_upload(
            file,
            settings.upload_limit_bytes,
            tmp_dir=tmp_dir,
        )

        try:
            # Step 2: validate preset before job creation
            try:
                resolved_preset = resolve_preset(preset)
            except UnknownPresetError as exc:
                return JSONResponse(
                    status_code=400,
                    content={"error": "unknown_preset", "detail": str(exc)},
                )

            # Step 3: create job row
            try:
                job_id = await asyncio.to_thread(
                    _create_job,
                    settings.database_url,
                    JobMode.enhance_and_transcribe,
                    settings.asr_provider,
                    resolved_preset,
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
            logger.info("api.job_created", extra={"job_id": str(job_id), "mode": "enhance_and_transcribe", "preset": resolved_preset})
            JOB_COUNTER.labels(status="queued", mode="enhance_and_transcribe").inc()

            # Step 4: upload raw audio to MinIO
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
                logger.error("Raw audio upload failed for job %s: %s", job_id, exc, extra={"job_id": str(job_id)})
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

            # Step 4b: persist raw_audio_uri in DB
            try:
                await asyncio.to_thread(
                    _set_raw_audio_uri, settings.database_url, job_id, raw_audio_uri
                )
            except Exception as exc:
                logger.error(
                    "Failed to update raw_audio_uri for job %s: %s", job_id, exc,
                    extra={"job_id": str(job_id)},
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

            # Step 5: enqueue Celery task (same task name — worker reads mode from DB).
            # Capture traceparent in this async context so it is not lost across
            # the asyncio.to_thread boundary.
            traceparent = _current_traceparent()
            try:
                await asyncio.to_thread(_enqueue_transcribe, str(job_id), traceparent)
            except Exception as exc:
                logger.error("Task enqueue failed for job %s: %s", job_id, exc, extra={"job_id": str(job_id)})
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
                        "detail": "Failed to queue enhancement task",
                    },
                )
            logger.info("api.job_enqueued", extra={"job_id": str(job_id)})

            return JSONResponse(
                status_code=202,
                content={"job_id": str(job_id), "status": "queued"},
            )

        finally:
            validated.path.unlink(missing_ok=True)

    finally:
        await file.close()


def _enum_or_str(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


@app.get("/v1/jobs/{job_id}/result")
async def get_job_result(job_id: uuid.UUID) -> JSONResponse:
    settings = get_settings()
    snap = await asyncio.to_thread(_load_job, settings.database_url, job_id)

    if snap is None:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "detail": f"Job {job_id} not found"},
        )

    status_str = _enum_or_str(snap.status)

    if status_str in ("queued", "running"):
        return JSONResponse(
            status_code=202,
            content={
                "job_id": str(snap.id),
                "status": status_str,
                "detail": "Job is not yet complete.",
            },
        )

    if status_str == "failed":
        return JSONResponse(
            status_code=200,
            content={
                "job_id": str(snap.id),
                "status": status_str,
                "error_message": snap.error_message,
            },
        )

    # status == "completed"
    if not snap.transcript_text or not snap.transcript_uri:
        err = "Completed job is missing required transcript data."
        try:
            await asyncio.to_thread(
                _mark_job_failed, settings.database_url, job_id, err
            )
        except Exception as exc:
            logger.error("Failed to mark job %s failed: %s", job_id, exc, extra={"job_id": str(job_id)})
        return JSONResponse(
            status_code=500,
            content={"error": "transcript_missing", "detail": err},
        )

    return JSONResponse(
        status_code=200,
        content={
            "job_id": str(snap.id),
            "status": status_str,
            "transcript_text": snap.transcript_text,
            "transcript_uri": snap.transcript_uri,
            "completed_at": snap.completed_at.isoformat() if snap.completed_at else None,
        },
    )


@app.get("/v1/jobs/{job_id}")
async def get_job(job_id: uuid.UUID) -> JSONResponse:
    settings = get_settings()
    snap = await asyncio.to_thread(_load_job, settings.database_url, job_id)
    if snap is None:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "detail": f"Job {job_id} not found"},
        )
    return JSONResponse(
        status_code=200,
        content={
            "job_id": str(snap.id),
            "status": _enum_or_str(snap.status),
            "mode": _enum_or_str(snap.mode),
            "provider": snap.provider,
            "preset": snap.preset,
            "raw_audio_uri": snap.raw_audio_uri,
            "enhanced_audio_uri": snap.enhanced_audio_uri,
            "transcript_uri": snap.transcript_uri,
            "transcript_text": snap.transcript_text,
            "error_message": snap.error_message,
            "created_at": snap.created_at.isoformat() if snap.created_at else None,
            "updated_at": snap.updated_at.isoformat() if snap.updated_at else None,
            "started_at": snap.started_at.isoformat() if snap.started_at else None,
            "completed_at": snap.completed_at.isoformat() if snap.completed_at else None,
        },
    )
