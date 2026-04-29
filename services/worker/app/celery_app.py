import socket
from celery import Celery
from libs.common.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "asr_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["services.worker.app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="debug.ping")
def ping() -> dict:
    return {"pong": True, "worker": socket.gethostname()}
