import importlib
import sys

import pytest
from celery import Celery


@pytest.fixture
def celery_module(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")

    from libs.common.settings import get_settings
    get_settings.cache_clear()

    sys.modules.pop("services.worker.app.celery_app", None)
    module = importlib.import_module("services.worker.app.celery_app")

    yield module

    get_settings.cache_clear()
    sys.modules.pop("services.worker.app.celery_app", None)


def test_celery_app_is_celery_instance(celery_module):
    assert isinstance(celery_module.celery_app, Celery)


def test_ping_task_registered_by_name(celery_module):
    assert "debug.ping" in celery_module.celery_app.tasks


def test_ping_task_returns_pong(celery_module):
    result = celery_module.ping.run()
    assert result["pong"] is True
    assert result["worker"]


@pytest.fixture
def tasks_module(celery_module):
    sys.modules.pop("services.worker.app.tasks", None)
    module = importlib.import_module("services.worker.app.tasks")
    yield module
    sys.modules.pop("services.worker.app.tasks", None)


def test_transcribe_job_registered(tasks_module, celery_module):
    assert "worker.transcribe_job" in celery_module.celery_app.tasks
