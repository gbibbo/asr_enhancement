import logging
import socket
import threading
import time
from celery import Celery
from libs.common.settings import get_settings

logger = logging.getLogger(__name__)

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


from celery.signals import worker_process_init  # noqa: E402
from libs.observability import configure_logging  # noqa: E402
from libs.observability.metrics import (  # noqa: E402
    QUEUE_BACKLOG,
    WORKER_HEARTBEAT,
    start_worker_metrics_server,
)
from libs.observability.tracing import configure_tracing  # noqa: E402


def _start_heartbeat_thread() -> None:
    def _loop():
        while True:
            WORKER_HEARTBEAT.set(time.time())
            time.sleep(30)
    threading.Thread(target=_loop, daemon=True, name="worker-heartbeat").start()


def _resolve_default_queue_name() -> str:
    name = getattr(celery_app.conf, "task_default_queue", None)
    return name if isinstance(name, str) and name else "celery"


def _poll_queue_backlog_once(client, queue_name: str) -> int:
    depth = int(client.llen(queue_name))
    QUEUE_BACKLOG.set(depth)
    return depth


def _start_queue_backlog_thread(poll_seconds: float = 5.0) -> None:
    def _loop():
        import redis
        while True:
            try:
                client = redis.Redis.from_url(settings.redis_url)
                _poll_queue_backlog_once(client, _resolve_default_queue_name())
            except Exception as exc:
                logger.warning(
                    "queue_backlog_poll_failed",
                    extra={"error": str(exc)},
                )
            time.sleep(poll_seconds)
    threading.Thread(
        target=_loop, daemon=True, name="worker-queue-backlog"
    ).start()


@worker_process_init.connect
def _configure_worker_logging(**kwargs):
    configure_logging("worker")
    configure_tracing("asr-worker")
    start_worker_metrics_server(9091)
    _start_heartbeat_thread()
    _start_queue_backlog_thread()
