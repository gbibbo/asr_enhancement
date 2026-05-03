from __future__ import annotations


def test_degradation_version_importable():
    from libs.common.versions import DEGRADATION_VERSION  # noqa: F401


def test_metrics_version_importable():
    from libs.common.versions import METRICS_VERSION  # noqa: F401


def test_default_enhancer_version_importable():
    from libs.common.versions import DEFAULT_ENHANCER_VERSION  # noqa: F401


def test_degradation_version_is_nonempty_string():
    from libs.common.versions import DEGRADATION_VERSION

    assert isinstance(DEGRADATION_VERSION, str)
    assert DEGRADATION_VERSION


def test_metrics_version_is_nonempty_string():
    from libs.common.versions import METRICS_VERSION

    assert isinstance(METRICS_VERSION, str)
    assert METRICS_VERSION


def test_default_enhancer_version_is_nonempty_string():
    from libs.common.versions import DEFAULT_ENHANCER_VERSION

    assert isinstance(DEFAULT_ENHANCER_VERSION, str)
    assert DEFAULT_ENHANCER_VERSION


def test_degradation_version_is_frozen_at_v1():
    from libs.common.versions import DEGRADATION_VERSION

    assert DEGRADATION_VERSION == "degradation_v1"
