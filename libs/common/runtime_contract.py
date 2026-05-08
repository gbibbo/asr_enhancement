"""Robust ASR runtime contract — request/response schemas and assertion runner.

Authored under P0.4 (skeleton); finalized under P9.0. Pure stdlib so the
runtime SIF need not pin third-party JSON Schema libraries; schemas are
declared as JSON Schema 2020-12 draft dicts for documentation and for
optional external validation, while in-process checks are performed by
the explicit per-assertion functions in this module.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIO_ENCODINGS = ("wav", "flac", "webm_opus")
PROFILES = ("balanced", "quality_first", "local_first")
ROUTER_KINDS = ("ml_router", "deterministic_selector")
SAMPLE_RATE_HZ = 16000
CHANNELS = 1
SHA256_HEX_LEN = 64
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

# ---------------------------------------------------------------------------
# JSON Schema 2020-12 draft schemas (declarative; not used for runtime checks)
# ---------------------------------------------------------------------------

REQUEST_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://robust-asr.local/schemas/rp5_request.skeleton.json",
    "title": "RP5 ASR request (skeleton)",
    "type": "object",
    "required": ["request_id", "audio", "client", "constraints"],
    "properties": {
        "request_id": {"type": "string", "minLength": 1},
        "audio": {
            "type": "object",
            "required": [
                "encoding", "sample_rate_hz", "channels",
                "duration_s", "sha256", "uri_or_inline",
            ],
            "properties": {
                "encoding": {"enum": list(AUDIO_ENCODINGS)},
                "sample_rate_hz": {"type": "integer", "const": SAMPLE_RATE_HZ},
                "channels": {"type": "integer", "const": CHANNELS},
                "duration_s": {"type": "number", "exclusiveMinimum": 0},
                "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "uri_or_inline": {"type": "string", "minLength": 1},
            },
        },
        "client": {
            "type": "object",
            "required": ["browser_user_agent", "client_version"],
            "properties": {
                "browser_user_agent": {"type": "string"},
                "client_version": {"type": "string"},
            },
        },
        "constraints": {
            "type": "object",
            "required": ["max_latency_ms", "allow_third_party", "profile"],
            "properties": {
                "max_latency_ms": {"type": "integer", "exclusiveMinimum": 0},
                "allow_third_party": {"type": "boolean"},
                "profile": {"enum": list(PROFILES)},
            },
        },
    },
}

RESPONSE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://robust-asr.local/schemas/rp5_response.skeleton.json",
    "title": "RP5 ASR response (skeleton)",
    "type": "object",
    "required": [
        "request_id", "transcript", "raw_transcript", "confidence",
        "ask_repeat", "selected_backend", "router_kind",
        "routing_features", "latency_ms", "cost_usd",
        "third_party_provider", "report_links", "errors",
    ],
    "properties": {
        "request_id": {"type": "string", "minLength": 1},
        "transcript": {"type": ["string", "null"]},
        "raw_transcript": {"type": ["string", "null"]},
        "confidence": {
            "type": ["number", "null"],
            "minimum": 0.0, "maximum": 1.0,
        },
        "ask_repeat": {"type": "boolean"},
        "selected_backend": {"type": ["string", "null"]},
        "router_kind": {"enum": list(ROUTER_KINDS)},
        "routing_features": {"type": "object"},
        "latency_ms": {
            "type": "object",
            "required": ["backend", "server", "end_to_end"],
            "properties": {
                "backend": {"type": "integer", "minimum": 0},
                "server": {"type": "integer", "minimum": 0},
                "end_to_end": {"type": "integer", "minimum": 0},
            },
        },
        "cost_usd": {"type": ["number", "null"], "minimum": 0.0},
        "third_party_provider": {"type": ["string", "null"]},
        "report_links": {
            "type": "object",
            "required": ["model_card", "router_card"],
            "properties": {
                "model_card": {"type": "string"},
                "router_card": {"type": "string"},
            },
        },
        "errors": {"type": "array"},
    },
}


# ---------------------------------------------------------------------------
# Assertion runner
# ---------------------------------------------------------------------------

# Each assertion is identified A01..A19 (matches agent plan §9 P0.4 step 4).
_AID = lambda i: f"A{i:02d}"  # noqa: E731


def _is_bool(x: Any) -> bool:
    return isinstance(x, bool)


def _is_int_pos(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool) and x > 0


def _is_int_nonneg(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool) and x >= 0


def _is_str(x: Any) -> bool:
    return isinstance(x, str)


def _get(obj: Any, *path: str) -> Any:
    cur = obj
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return _MISSING
        cur = cur[k]
    return cur


_MISSING = object()


def run_assertions(
    request: Dict[str, Any],
    response: Dict[str, Any],
    *,
    strict_skeleton: bool = True,
    strict_final: bool = False,
) -> List[Tuple[str, str, str]]:
    """Run all 19 assertions and return [(aid, status, msg)] in order.

    `status` is "PASS" or "FAIL". On parse error A01 is handled by the
    caller before this runner is invoked.
    """
    out: List[Tuple[str, str, str]] = []

    def emit(aid: str, ok: bool, msg: str) -> None:
        out.append((aid, "PASS" if ok else "FAIL", msg))

    # A01 — JSON parses (caller proves this by reaching here)
    emit(_AID(1), True, "both JSON files parsed")

    # A02 — request_id non-empty and matches across request/response
    req_id = _get(request, "request_id")
    res_id = _get(response, "request_id")
    a02 = (
        _is_str(req_id) and req_id != ""
        and _is_str(res_id) and res_id == req_id
    )
    emit(_AID(2), a02, f"request_id={req_id!r} response.request_id={res_id!r}")

    # A03 — audio.encoding in AUDIO_ENCODINGS
    enc = _get(request, "audio", "encoding")
    emit(_AID(3), enc in AUDIO_ENCODINGS, f"audio.encoding={enc!r}")

    # A04 — audio.sample_rate_hz == 16000
    sr = _get(request, "audio", "sample_rate_hz")
    emit(_AID(4), sr == SAMPLE_RATE_HZ, f"audio.sample_rate_hz={sr!r}")

    # A05 — audio.channels == 1
    ch = _get(request, "audio", "channels")
    emit(_AID(5), ch == CHANNELS, f"audio.channels={ch!r}")

    # A06 — audio.duration_s > 0
    dur = _get(request, "audio", "duration_s")
    a06 = isinstance(dur, (int, float)) and not isinstance(dur, bool) and dur > 0
    emit(_AID(6), a06, f"audio.duration_s={dur!r}")

    # A07 — audio.sha256 is 64-hex (lowercase)
    sha = _get(request, "audio", "sha256")
    a07 = _is_str(sha) and bool(SHA256_HEX_RE.match(sha))
    emit(_AID(7), a07, f"audio.sha256={sha!r}")

    # A08 — constraints.profile in PROFILES
    prof = _get(request, "constraints", "profile")
    emit(_AID(8), prof in PROFILES, f"constraints.profile={prof!r}")

    # A09 — constraints.allow_third_party is bool
    a3p = _get(request, "constraints", "allow_third_party")
    emit(_AID(9), _is_bool(a3p), f"constraints.allow_third_party={a3p!r}")

    # A10 — constraints.max_latency_ms is positive int
    mlm = _get(request, "constraints", "max_latency_ms")
    emit(_AID(10), _is_int_pos(mlm), f"constraints.max_latency_ms={mlm!r}")

    # A11 — response.ask_repeat is bool
    ar = _get(response, "ask_repeat")
    emit(_AID(11), _is_bool(ar), f"response.ask_repeat={ar!r}")

    # A12 — (transcript is null) iff (ask_repeat==True OR errors non-empty)
    transcript = _get(response, "transcript")
    errors = _get(response, "errors")
    transcript_is_null = transcript is None
    errors_nonempty = isinstance(errors, list) and len(errors) > 0
    rhs = (ar is True) or errors_nonempty
    a12 = (transcript_is_null == rhs)
    emit(
        _AID(12), a12,
        f"transcript_is_null={transcript_is_null} ask_repeat={ar!r} "
        f"errors_nonempty={errors_nonempty}",
    )

    # A13 — selected_backend is null iff ask_repeat == True
    sb = _get(response, "selected_backend")
    sb_is_null = sb is None
    a13 = (sb_is_null == (ar is True))
    emit(
        _AID(13), a13,
        f"selected_backend={sb!r} ask_repeat={ar!r}",
    )

    # A14 — router_kind in ROUTER_KINDS
    rk = _get(response, "router_kind")
    emit(_AID(14), rk in ROUTER_KINDS, f"router_kind={rk!r}")

    # A15 — cost_usd is null OR >= 0.0
    cu = _get(response, "cost_usd")
    a15 = (
        cu is None
        or (isinstance(cu, (int, float)) and not isinstance(cu, bool) and cu >= 0.0)
    )
    emit(_AID(15), a15, f"cost_usd={cu!r}")

    # A16 — third_party_provider matching when selected_backend == "assemblyai"
    tpp = _get(response, "third_party_provider")
    if sb == "assemblyai":
        a16 = (tpp == "assemblyai")
        msg = f"selected_backend=assemblyai third_party_provider={tpp!r}"
    else:
        a16 = (tpp is None or _is_str(tpp))
        msg = f"selected_backend={sb!r} third_party_provider={tpp!r}"
    emit(_AID(16), a16, msg)

    # A17 — latency_ms.end_to_end >= server >= backend
    lat_b = _get(response, "latency_ms", "backend")
    lat_s = _get(response, "latency_ms", "server")
    lat_e = _get(response, "latency_ms", "end_to_end")
    a17 = (
        _is_int_nonneg(lat_b) and _is_int_nonneg(lat_s) and _is_int_nonneg(lat_e)
        and lat_e >= lat_s >= lat_b
    )
    emit(
        _AID(17), a17,
        f"latency_ms backend={lat_b!r} server={lat_s!r} end_to_end={lat_e!r}",
    )

    # A18 — confidence is null OR in [0.0, 1.0]
    conf = _get(response, "confidence")
    a18 = (
        conf is None
        or (
            isinstance(conf, (int, float)) and not isinstance(conf, bool)
            and 0.0 <= conf <= 1.0
        )
    )
    emit(_AID(18), a18, f"confidence={conf!r}")

    # A19 — report_links.{model_card,router_card} are strings
    mc = _get(response, "report_links", "model_card")
    rc = _get(response, "report_links", "router_card")
    a19_types = _is_str(mc) and _is_str(rc)
    if strict_final:
        a19 = a19_types and len(mc) > 0 and len(rc) > 0
        msg = f"strict_final: model_card={mc!r} router_card={rc!r}"
    else:
        # strict_skeleton: empty allowed
        a19 = a19_types
        msg = f"strict_skeleton: model_card={mc!r} router_card={rc!r}"
    emit(_AID(19), a19, msg)

    return out


__all__ = [
    "AUDIO_ENCODINGS",
    "PROFILES",
    "ROUTER_KINDS",
    "SAMPLE_RATE_HZ",
    "CHANNELS",
    "SHA256_HEX_LEN",
    "REQUEST_SCHEMA",
    "RESPONSE_SCHEMA",
    "run_assertions",
]
