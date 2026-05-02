from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from libs.common.demo_settings import DemoSettings
from libs.demo.examples import get_safe_audio_path, load_examples
from libs.demo.persistence import QueueFullError, count_active_jobs, ensure_runtime_dirs, init_schema, try_create_job
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
