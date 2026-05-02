from __future__ import annotations

import dataclasses

import libs.common.versions as _versions


def test_normalize_text_importable():
    from libs.audio.metrics import normalize_text  # noqa: F401


def test_compute_metrics_importable():
    from libs.audio.metrics import compute_metrics  # noqa: F401


def test_metrics_result_importable():
    from libs.audio.metrics import MetricsResult  # noqa: F401


def test_package_init_re_exports_metrics_result():
    from libs.audio import MetricsResult  # noqa: F401


def test_package_init_re_exports_compute_metrics():
    from libs.audio import compute_metrics  # noqa: F401


def test_package_init_re_exports_normalize_text():
    from libs.audio import normalize_text  # noqa: F401


def test_metrics_result_is_frozen():
    from libs.audio.metrics import MetricsResult

    result = MetricsResult(wer=0.0, word_accuracy=1.0,
                           metrics_version="1.0", available=True)
    with __import__("pytest").raises(dataclasses.FrozenInstanceError):
        result.wer = 0.5  # type: ignore[misc]


def test_metrics_result_metrics_version_matches_constant():
    from libs.audio.metrics import compute_metrics

    result = compute_metrics("hello", "hello")
    assert result.metrics_version == _versions.METRICS_VERSION


def test_metrics_version_not_hardcoded(monkeypatch):
    from libs.audio.metrics import compute_metrics

    monkeypatch.setattr(_versions, "METRICS_VERSION", "SENTINEL")
    result = compute_metrics("hello", "hello")
    assert result.metrics_version == "SENTINEL"
