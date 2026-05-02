from __future__ import annotations

import libs.common.versions as versions


def build_cache_key(
    *,
    example_id: str,
    degradation_id: str,
    asr_provider: str,
    asr_model_version: str,
    enhancer_version: str | None = None,
) -> str:
    effective_enhancer_version = (
        enhancer_version if enhancer_version is not None else versions.DEFAULT_ENHANCER_VERSION
    )
    return (
        f"{example_id}|"
        f"{degradation_id}|"
        f"{versions.DEGRADATION_VERSION}|"
        f"{asr_provider}|"
        f"{asr_model_version}|"
        f"{effective_enhancer_version}|"
        f"{versions.METRICS_VERSION}"
    )
