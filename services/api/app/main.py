from __future__ import annotations

import asyncio
from typing import Any

import redis as redis_lib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from libs.common.db import make_engine
from libs.common.settings import Settings, get_settings
from libs.common.storage import StorageClient

app = FastAPI(title="ASR Enhancement Platform", version="0.1.0")

_READINESS_TIMEOUT = 5.0


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


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "Internal server error"},
    )


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
