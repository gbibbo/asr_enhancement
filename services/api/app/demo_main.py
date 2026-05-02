from __future__ import annotations

import json
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from libs.common.demo_settings import DemoSettings
from libs.demo.cache import build_cache_key
from libs.demo.examples import get_safe_audio_path, load_examples
from libs.demo.persistence import (
    QueueFullError,
    count_active_jobs,
    ensure_runtime_dirs,
    get_admin_state_value,
    get_cache_entry,
    get_job,
    get_jobs_stats,
    init_schema,
    set_admin_state,
    try_create_job,
)
from libs.demo.upload import FileTooLargeError, UnsupportedExtensionError, save_upload
from libs.observability.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("demo-api")
    settings = DemoSettings()
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    set_admin_state(
        settings.demo_db_path,
        "startup_time",
        datetime.now(timezone.utc).isoformat(),
    )
    app.state.settings = settings
    yield


app = FastAPI(title="ASR Enhancement Demo", version="0.1.0", lifespan=lifespan)

_basic = HTTPBasic(auto_error=False)

_ASR_MODEL_DEFAULTS: dict[str, str] = {
    "whisper": "tiny.en",
    "assemblyai": "best",
}


class _RunCachedRequest(BaseModel):
    example_id: str
    degradation_id: str
    provider: str = "whisper"
    asr_model_version: str | None = None
    enhancer_version: str | None = None


@app.get("/demo/health")
async def demo_health(request: Request):
    settings: DemoSettings = request.app.state.settings
    try:
        queue_depth = count_active_jobs(settings.demo_db_path)
        db_ok = True
    except Exception:
        queue_depth = -1
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "mode": "demo",
        "db_ok": db_ok,
        "queue_depth": queue_depth,
    }


@app.get("/demo/examples")
async def list_demo_examples(request: Request):
    settings: DemoSettings = request.app.state.settings
    examples = load_examples(settings.demo_examples_config)
    note = None if examples else "No curated examples loaded. Run Phase B6 to populate."
    return {"examples": [e.model_dump() for e in examples], "total": len(examples), "note": note}


@app.get("/demo/examples/{example_id}/audio/clean")
async def get_clean_audio(example_id: str, request: Request):
    settings: DemoSettings = request.app.state.settings
    examples = load_examples(settings.demo_examples_config)
    example = next((e for e in examples if e.example_id == example_id), None)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    audio_root = settings.demo_artifacts_dir / "examples"
    target = get_safe_audio_path(audio_root, example.clean_audio_path)
    if target is None:
        raise HTTPException(status_code=404, detail="Clean audio not available")
    return FileResponse(target, media_type="audio/wav")


@app.get("/demo/examples/{example_id}/audio/degraded/{degradation_id}")
async def get_degraded_audio(example_id: str, degradation_id: str, request: Request):
    settings: DemoSettings = request.app.state.settings
    examples = load_examples(settings.demo_examples_config)
    example = next((e for e in examples if e.example_id == example_id), None)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    path_str = example.degraded_audio_paths.get(degradation_id)
    if path_str is None:
        raise HTTPException(status_code=404, detail="Degraded audio not available for this degradation")
    audio_root = settings.demo_artifacts_dir / "examples"
    target = get_safe_audio_path(audio_root, path_str)
    if target is None:
        raise HTTPException(status_code=404, detail="Degraded audio not available")
    return FileResponse(target, media_type="audio/wav")


@app.post("/demo/jobs", status_code=202)
async def create_demo_job(request: Request):
    settings: DemoSettings = request.app.state.settings
    try:
        job_id = try_create_job(
            settings.demo_db_path,
            queue_max=settings.demo_queue_max,
            provider="whisper",
        )
    except QueueFullError:
        return JSONResponse(
            status_code=503,
            content={"detail": "Queue full. Try again later."},
        )
    return {"job_id": job_id, "status": "queued"}


@app.post("/demo/run-cached")
async def run_cached(body: _RunCachedRequest, request: Request):
    settings: DemoSettings = request.app.state.settings
    examples = load_examples(settings.demo_examples_config)
    example = next((e for e in examples if e.example_id == body.example_id), None)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    if body.degradation_id not in example.degradation_ids:
        raise HTTPException(status_code=404, detail="Degradation not available for this example")
    asr_model_version = body.asr_model_version or _ASR_MODEL_DEFAULTS.get(body.provider, body.provider)
    cache_key = build_cache_key(
        example_id=body.example_id,
        degradation_id=body.degradation_id,
        asr_provider=body.provider,
        asr_model_version=asr_model_version,
        enhancer_version=body.enhancer_version,
    )
    entry = get_cache_entry(settings.demo_db_path, cache_key)
    if entry:
        return {
            "status": "cache_hit",
            "result": json.loads(entry["result_json"]),
            "cache_key": cache_key,
        }
    return {"status": "cache_miss", "detail": "No cached result for this configuration."}


@app.post("/demo/upload")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Form("whisper"),
    degradation_id: str | None = Form(None),
    enhancer_version: str | None = Form(None),
):
    settings: DemoSettings = request.app.state.settings
    try:
        saved_path, _ = await save_upload(
            file,
            settings.demo_upload_dir,
            settings.demo_upload_limit_bytes,
        )
    except UnsupportedExtensionError:
        raise HTTPException(status_code=415, detail="Unsupported file type.")
    except FileTooLargeError:
        raise HTTPException(status_code=413, detail="File too large.")
    try:
        job_id = try_create_job(
            settings.demo_db_path,
            queue_max=settings.demo_queue_max,
            provider=provider,
            degradation_id=degradation_id,
            enhancer_version=enhancer_version,
            input_artifact_path=str(saved_path),
        )
    except QueueFullError:
        saved_path.unlink(missing_ok=True)
        return JSONResponse(
            status_code=503,
            content={"detail": "Queue full. Try again later."},
        )
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise
    return JSONResponse(status_code=202, content={"job_id": job_id, "status": "queued"})


@app.get("/demo/jobs/{job_id}")
async def get_demo_job(job_id: str, request: Request):
    settings: DemoSettings = request.app.state.settings
    job = get_job(settings.demo_db_path, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/demo/jobs/{job_id}/result")
async def get_demo_job_result(job_id: str, request: Request):
    settings: DemoSettings = request.app.state.settings
    job = get_job(settings.demo_db_path, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] in ("queued", "running"):
        return JSONResponse(
            status_code=202,
            content={"job_id": job_id, "status": job["status"]},
        )
    if job["status"] == "completed":
        result = json.loads(job["result_json"]) if job.get("result_json") else {}
        return {"job_id": job_id, "status": "completed", "result": result}
    return {"job_id": job_id, "status": "failed", "error": job.get("error_message")}


@app.get("/admin/stats")
async def admin_stats(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(_basic),
):
    settings: DemoSettings = request.app.state.settings
    _unauth = HTTPException(
        status_code=401,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Basic"},
    )
    if credentials is None or settings.admin_stats_password is None:
        raise _unauth
    ok_user = secrets.compare_digest(
        credentials.username.encode(), settings.admin_stats_username.encode()
    )
    ok_pass = secrets.compare_digest(
        credentials.password.encode(), settings.admin_stats_password.encode()
    )
    if not (ok_user and ok_pass):
        raise _unauth
    startup_iso = get_admin_state_value(settings.demo_db_path, "startup_time")
    uptime = 0.0
    if startup_iso:
        delta = datetime.now(timezone.utc) - datetime.fromisoformat(startup_iso)
        uptime = delta.total_seconds()
    return {
        "startup_time": startup_iso,
        "uptime_seconds": uptime,
        "queue_depth": count_active_jobs(settings.demo_db_path),
        "jobs_by_status": get_jobs_stats(settings.demo_db_path),
    }
