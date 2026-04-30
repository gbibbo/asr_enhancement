from __future__ import annotations

import pytest

from libs.observability.metrics import QUEUE_BACKLOG, get_metrics_output
from services.worker.app import celery_app as celery_app_module
from services.worker.app.celery_app import (
    _poll_queue_backlog_once,
    _resolve_default_queue_name,
    celery_app,
)


def _samples(output: str, metric_name: str) -> list[str]:
    return [
        line for line in output.splitlines()
        if (
            line.startswith(metric_name + "{") or line.startswith(metric_name + " ")
        ) and not line.startswith("#")
    ]


def test_queue_backlog_gauge_is_importable():
    assert QUEUE_BACKLOG is not None


def test_output_contains_queue_backlog_definition():
    output = get_metrics_output().decode("utf-8")
    assert "asr_queue_backlog_jobs" in output


def test_queue_backlog_value_appears_after_set():
    QUEUE_BACKLOG.set(42)
    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_queue_backlog_jobs")
    assert any(s.endswith(" 42.0") for s in samples), samples


def test_resolve_default_queue_name_uses_celery_conf(monkeypatch):
    monkeypatch.setattr(celery_app.conf, "task_default_queue", "asr_queue", raising=False)
    assert _resolve_default_queue_name() == "asr_queue"


def test_resolve_default_queue_name_falls_back_to_celery(monkeypatch):
    monkeypatch.setattr(celery_app.conf, "task_default_queue", None, raising=False)
    assert _resolve_default_queue_name() == "celery"


class _StubRedisOk:
    def __init__(self, depth: int):
        self._depth = depth
        self.calls: list[str] = []

    def llen(self, name: str) -> int:
        self.calls.append(name)
        return self._depth


class _StubRedisError:
    def llen(self, name: str):
        raise RuntimeError("redis down")


def test_poll_queue_backlog_once_sets_gauge_from_llen():
    QUEUE_BACKLOG.set(0)
    client = _StubRedisOk(depth=7)
    result = _poll_queue_backlog_once(client, "celery")
    assert result == 7
    assert client.calls == ["celery"]
    output = get_metrics_output().decode("utf-8")
    samples = _samples(output, "asr_queue_backlog_jobs")
    assert any(s.endswith(" 7.0") for s in samples), samples


def test_poll_queue_backlog_once_propagates_redis_error():
    client = _StubRedisError()
    with pytest.raises(RuntimeError):
        _poll_queue_backlog_once(client, "celery")
