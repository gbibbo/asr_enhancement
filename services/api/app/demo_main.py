from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from libs.common.demo_settings import DemoSettings
from libs.demo.persistence import QueueFullError, ensure_runtime_dirs, init_schema, try_create_job
from libs.observability.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("demo-api")
    settings = DemoSettings()
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)
    app.state.settings = settings
    yield


app = FastAPI(title="ASR Enhancement Demo", version="0.1.0", lifespan=lifespan)


@app.get("/demo/health")
async def demo_health():
    return {"status": "ok", "mode": "demo"}


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
