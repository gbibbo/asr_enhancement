from __future__ import annotations

import dataclasses
from typing import Optional


@dataclasses.dataclass
class RouterDecision:
    selected_backend: str
    router_kind: str
    router_version: str
    routing_profile: str
    allow_third_party: bool
    third_party_provider: Optional[str]
    cost_policy: str
    estimated_cost_usd: float
    predicted_confidence: float
    predicted_ask_repeat: float
    routing_explanation: str
    router_latency_ms: float


@dataclasses.dataclass
class LatencyMs:
    backend: float
    server: float
    end_to_end: float


@dataclasses.dataclass
class AssembledResponse:
    transcript_text: str
    selected_backend: str
    router_kind: str
    router_version: str
    routing_profile: str
    allow_third_party: bool
    third_party_provider: Optional[str]
    estimated_cost_usd: float
    cost_usd: float
    backend_confidence: float
    ask_repeat: float
    latency_ms: LatencyMs
    routing_explanation: str


STUB_ROUTER_KIND = "deterministic_selector"
STUB_ROUTER_VERSION = "stub-v0"
STUB_SELECTED_BACKEND = "whisper_base_ct2_int8"


def build_cache_key(
    *,
    audio_hash: str,
    selected_backend: str,
    asr_model_and_version: str,
    router_kind: str,
    router_version: str,
    routing_profile: str,
    allow_third_party: bool,
    degradation_version: str,
    metrics_or_features_version: str,
) -> str:
    third_party_flag = "1" if allow_third_party else "0"
    return (
        f"{audio_hash}|{selected_backend}|{asr_model_and_version}|"
        f"{router_kind}|{router_version}|{routing_profile}|"
        f"{third_party_flag}|{degradation_version}|{metrics_or_features_version}"
    )


class RouterRuntime:
    def route(
        self,
        *,
        routing_profile: str = "balanced",
        allow_third_party: bool = False,
    ) -> RouterDecision:
        return RouterDecision(
            selected_backend=STUB_SELECTED_BACKEND,
            router_kind=STUB_ROUTER_KIND,
            router_version=STUB_ROUTER_VERSION,
            routing_profile=routing_profile,
            allow_third_party=allow_third_party,
            third_party_provider=None,
            cost_policy="zero_direct_cost",
            estimated_cost_usd=0.0,
            predicted_confidence=0.0,
            predicted_ask_repeat=0.0,
            routing_explanation="stub: awaiting datamove1 handoff",
            router_latency_ms=0.0,
        )
