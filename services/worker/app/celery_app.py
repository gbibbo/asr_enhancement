import socket
import threading
import time
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


from celery.signals import worker_process_init  # noqa: E402
from libs.observability import configure_logging  # noqa: E402
from libs.observability.metrics import WORKER_HEARTBEAT, start_worker_metrics_server  # noqa: E402
from libs.observability.tracing import configure_tracing  # noqa: E402


def _start_heartbeat_thread() -> None:
    def _loop():
        while True:
            WORKER_HEARTBEAT.set(time.time())
            time.sleep(30)
    threading.Thread(target=_loop, daemon=True, name="worker-heartbeat").start()


@worker_process_init.connect
def _configure_worker_logging(**kwargs):
    configure_logging("worker")
    configure_tracing("asr-worker")
    start_worker_metrics_server(9091)
    _start_heartbeat_thread()
