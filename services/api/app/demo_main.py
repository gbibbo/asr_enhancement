from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from libs.observability.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("demo-api")
    yield


app = FastAPI(title="ASR Enhancement Demo", version="0.1.0", lifespan=lifespan)


@app.get("/demo/health")
async def demo_health():
    return {"status": "ok", "mode": "demo"}
