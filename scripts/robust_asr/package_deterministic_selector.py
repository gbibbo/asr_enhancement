#!/usr/bin/env python3
"""package_deterministic_selector.py — robust_asr P7.3 (Outcome E Branch B).

Packages the Section 5.5 deterministic selector into the RP5-deployable
artifact tree:

  artifacts/robust_asr/router/selected_router/
    deterministic_selector.json
    metadata.json
    rp5_inference.py
    test_vectors.json

Inputs:
  --selector-config <configs/robust_asr/router_v1.yaml>
  --out             <artifacts/robust_asr/router/selected_router>

Behavior (agent plan §1642-§1652, §4001-§4046):
  1. Loads deterministic-selector constants from router_v1.yaml.
  2. Writes deterministic_selector.json with constants, provenance,
     and version pins (DETERMINISTIC_SELECTOR_VERSION,
     NORMALIZATION_VERSION, METRICS_VERSION).
  3. Writes rp5_inference.py — a stdlib-only Python module that
     exposes predict(decode_features, assemblyai_available=False)
     wrapping the Section 5.5 reference implementation. Constants are
     loaded from the sibling deterministic_selector.json (never
     hardcoded) so that the runtime cannot drift from the packaged
     metadata.
  4. Writes test_vectors.json with >=16 (decode_features,
     assemblyai_available, expected_action, expected_reason) tuples
     covering every Section 5.5 branch and each threshold boundary.
  5. Writes metadata.json with git commit / branch / claims_enabled
     snapshot / per-file sha256 / deployable-backend list.

Forbidden inside the output dir (mandatory no-touch per CLAUDE.md §12
and reuse_policy_v1.yaml): *.wav, *.flac, *.mp3, *.m4a, *.pt, *.pth,
*.ckpt, *.bin, *.safetensors, .env, .env.*, *.key, *.pem, *.token.
The packager asserts none of these patterns ever lands under --out.

Stdout sentinel: OK_DETERMINISTIC_SELECTOR_PACKAGE on PASS.
Exit codes: 0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from libs.common.versions import (  # noqa: E402
    DETERMINISTIC_SELECTOR_VERSION,
    METRICS_VERSION,
    NORMALIZATION_VERSION,
)

FORBIDDEN_SUFFIXES = (
    ".wav", ".flac", ".mp3", ".m4a",
    ".pt", ".pth", ".ckpt", ".bin", ".safetensors",
    ".key", ".pem", ".token",
)
FORBIDDEN_BASENAMES = (".env",)

# rp5_inference.py is written verbatim into selected_router/. Keep this
# module stdlib-only — no torch, no requests, no numpy. It is the only
# Python that runs on the RP5 device for selector inference.
RP5_INFERENCE_SOURCE = '''\
"""rp5_inference.py — robust_asr deterministic selector (Outcome E).

Stdlib-only wrapper around the Section 5.5 deterministic_select
predicate. Constants are loaded from the sibling
deterministic_selector.json so that runtime behavior cannot drift from
the packaged metadata.

Public API:

    predict(decode_features, assemblyai_available=False) -> dict
        Returns {"action", "confidence", "reason"}.

    selector_constants() -> dict
        Returns the loaded constants (read-only view).

This module is imported by the RP5 runtime; it MUST NOT import any
third-party packages.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent
_CFG_PATH = _HERE / "deterministic_selector.json"

ACTION_BASELINE = "whisper_base_ct2_int8"
ACTION_CLOUD = "assemblyai"
ACTION_ASK_REPEAT = "ask_repeat"


def _load_cfg() -> Dict[str, Any]:
    with _CFG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


_CFG = _load_cfg()
_CONSTANTS = dict(_CFG["constants"])


def selector_constants() -> Dict[str, Any]:
    """Return a copy of the loaded Section 5.5 constants."""
    return dict(_CONSTANTS)


def predict(
    decode_features: Dict[str, Any],
    assemblyai_available: bool = False,
) -> Dict[str, Any]:
    """Apply the Section 5.5 deterministic selector.

    decode_features: mapping with optional keys
        "no_speech_prob" (float; default 0.0) and
        "avg_logprob"    (float; default 0.0).
    assemblyai_available: runtime probe result. Defaults to False to
        match OUTCOME_E_DETERMINISTIC_SELECTOR (BLOCKED_API).

    Returns a dict {"action", "confidence", "reason"}. The selector is
    deterministic, so confidence is always 1.0; "reason" identifies the
    Section 5.5 branch that fired.
    """
    no_speech_prob = float(decode_features.get("no_speech_prob", 0.0))
    avg_logprob = float(decode_features.get("avg_logprob", 0.0))

    no_speech_threshold = _CONSTANTS["no_speech_threshold"]
    ask_repeat_threshold = _CONSTANTS["ask_repeat_threshold"]
    escalate_threshold = _CONSTANTS["escalate_threshold"]

    if no_speech_prob > no_speech_threshold:
        return {
            "action": ACTION_ASK_REPEAT,
            "confidence": 1.0,
            "reason": "no_speech",
        }
    if avg_logprob < ask_repeat_threshold:
        return {
            "action": ACTION_ASK_REPEAT,
            "confidence": 1.0,
            "reason": "low_logprob",
        }
    if assemblyai_available and avg_logprob < escalate_threshold:
        return {
            "action": ACTION_CLOUD,
            "confidence": 1.0,
            "reason": "escalate_cloud",
        }
    return {
        "action": ACTION_BASELINE,
        "confidence": 1.0,
        "reason": "baseline",
    }
'''


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(args: List[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
    except Exception:
        return ""


def _assert_no_forbidden(out_dir: Path) -> None:
    for p in out_dir.rglob("*"):
        if not p.is_file():
            continue
        name = p.name
        suf = p.suffix.lower()
        if suf in FORBIDDEN_SUFFIXES or name in FORBIDDEN_BASENAMES:
            raise SystemExit(
                f"FAIL: forbidden file under selected_router: {p}"
            )
        if name.startswith(".env"):
            raise SystemExit(
                f"FAIL: forbidden .env-prefixed file under selected_router: {p}"
            )


def _load_constants(cfg_path: Path) -> Dict[str, float]:
    with cfg_path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    block = cfg.get("deterministic_selector") or {}
    required = (
        "ask_repeat_threshold",
        "escalate_threshold",
        "no_speech_threshold",
        "health_check_ttl_seconds",
    )
    missing = [k for k in required if k not in block]
    if missing:
        raise SystemExit(
            f"FAIL: deterministic_selector missing keys: {missing}"
        )
    return {k: float(block[k]) for k in required}


def _build_test_vectors(
    constants: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Return >=16 (decode_features, flag, expected_action, expected_reason)
    tuples that cover every Section 5.5 branch plus thresholds."""
    ar = constants["ask_repeat_threshold"]   # -1.0
    es = constants["escalate_threshold"]     # -0.5
    ns = constants["no_speech_threshold"]    # 0.6

    eps = 1e-3

    vectors: List[Dict[str, Any]] = [
        # no_speech branch (1-4): fires regardless of avg_logprob and
        # AssemblyAI availability.
        {"id": "no_speech_high_baseline",
         "decode_features": {"no_speech_prob": ns + eps, "avg_logprob": 0.0},
         "assemblyai_available": False,
         "expected_action": "ask_repeat",
         "expected_reason": "no_speech"},
        {"id": "no_speech_high_with_cloud",
         "decode_features": {"no_speech_prob": 0.99, "avg_logprob": 0.0},
         "assemblyai_available": True,
         "expected_action": "ask_repeat",
         "expected_reason": "no_speech"},
        {"id": "no_speech_at_threshold_below_baseline",
         "decode_features": {"no_speech_prob": ns, "avg_logprob": 0.0},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "no_speech_zero_baseline",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": 0.0},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},

        # low-logprob branch (5-8): fires regardless of AssemblyAI.
        {"id": "low_logprob_below_threshold_no_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": ar - eps},
         "assemblyai_available": False,
         "expected_action": "ask_repeat",
         "expected_reason": "low_logprob"},
        {"id": "low_logprob_below_threshold_with_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": ar - eps},
         "assemblyai_available": True,
         "expected_action": "ask_repeat",
         "expected_reason": "low_logprob"},
        {"id": "low_logprob_at_threshold_no_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": ar},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "low_logprob_at_threshold_with_cloud_escalates",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": ar},
         "assemblyai_available": True,
         "expected_action": "assemblyai",
         "expected_reason": "escalate_cloud"},

        # escalate branch (9-12): only fires when assemblyai_available.
        {"id": "escalate_with_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": es - eps},
         "assemblyai_available": True,
         "expected_action": "assemblyai",
         "expected_reason": "escalate_cloud"},
        {"id": "escalate_just_below_threshold_with_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": -0.51},
         "assemblyai_available": True,
         "expected_action": "assemblyai",
         "expected_reason": "escalate_cloud"},
        {"id": "escalate_no_cloud_falls_back_to_baseline",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": es - eps},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "escalate_no_cloud_well_below",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": -0.8},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},

        # baseline branch (13-16): high-confidence decodes.
        {"id": "baseline_at_escalate_threshold_no_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": es},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "baseline_at_escalate_threshold_with_cloud",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": es},
         "assemblyai_available": True,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "baseline_high_confidence_no_cloud",
         "decode_features": {"no_speech_prob": 0.01, "avg_logprob": -0.1},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "baseline_high_confidence_with_cloud",
         "decode_features": {"no_speech_prob": 0.01, "avg_logprob": -0.1},
         "assemblyai_available": True,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},

        # Extra coverage (17-20): missing-key defaults and proxy values
        # matching the P6.1 selector_evidence parquet.
        {"id": "missing_keys_default_to_baseline",
         "decode_features": {},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "p6_1_proxy_empty_transcript_no_speech",
         "decode_features": {"no_speech_prob": 1.0, "avg_logprob": 0.0},
         "assemblyai_available": False,
         "expected_action": "ask_repeat",
         "expected_reason": "no_speech"},
        {"id": "p6_1_proxy_nonempty_transcript_baseline",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": 0.0},
         "assemblyai_available": False,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
        {"id": "p6_1_proxy_with_cloud_baseline",
         "decode_features": {"no_speech_prob": 0.0, "avg_logprob": 0.0},
         "assemblyai_available": True,
         "expected_action": "whisper_base_ct2_int8",
         "expected_reason": "baseline"},
    ]
    return vectors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selector-config", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    cfg_path: Path = args.selector_config.resolve()
    out_dir: Path = args.out.resolve()

    if not cfg_path.exists():
        print(f"FAIL: selector config missing: {cfg_path}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    constants = _load_constants(cfg_path)

    # Provenance: selector_evidence.parquet sha256 if present.
    evidence_path = (
        REPO_ROOT
        / "artifacts"
        / "robust_asr"
        / "router"
        / "selector_evidence.parquet"
    )
    evidence_sha = _sha256(evidence_path) if evidence_path.exists() else None

    selector_doc: Dict[str, Any] = {
        "selector_kind": "deterministic_selector",
        "deterministic_selector_version": DETERMINISTIC_SELECTOR_VERSION,
        "constants": constants,
        "deployable_actions": ["whisper_base_ct2_int8", "ask_repeat"],
        "assemblyai_action_emitted_when": "assemblyai_available==true",
        "config_source": "configs/robust_asr/router_v1.yaml",
        "config_sha256": _sha256(cfg_path),
        "selector_evidence_sha256": evidence_sha,
        "features_version": None,
        "router_version": None,
        "metrics_version": METRICS_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "section_reference": "agent_plan_v3_4_7 §5.5",
    }

    selector_path = out_dir / "deterministic_selector.json"
    with selector_path.open("w", encoding="utf-8") as fh:
        json.dump(selector_doc, fh, indent=2, sort_keys=True)
        fh.write("\n")

    rp5_path = out_dir / "rp5_inference.py"
    with rp5_path.open("w", encoding="utf-8") as fh:
        fh.write(RP5_INFERENCE_SOURCE)

    vectors = _build_test_vectors(constants)
    if len(vectors) < 16:
        print(
            f"FAIL: test_vectors.json must have >=16 tuples; got {len(vectors)}",
            file=sys.stderr,
        )
        return 1
    test_vectors_doc: Dict[str, Any] = {
        "schema": "robust_asr.router.test_vectors.v1",
        "deterministic_selector_version": DETERMINISTIC_SELECTOR_VERSION,
        "constants": constants,
        "count": len(vectors),
        "vectors": vectors,
    }
    test_vectors_path = out_dir / "test_vectors.json"
    with test_vectors_path.open("w", encoding="utf-8") as fh:
        json.dump(test_vectors_doc, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # metadata.json — depends on the other three files' sha256s.
    metadata: Dict[str, Any] = {
        "selector_kind": "deterministic_selector",
        "deterministic_selector_version": DETERMINISTIC_SELECTOR_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "metrics_version": METRICS_VERSION,
        "features_version": None,
        "router_version": None,
        "deployable_backends": ["whisper_base_ct2_int8"],
        "ask_repeat_supported": True,
        "cloud_available_at_build": False,
        "lora_available_at_build": False,
        "outcome_e_deterministic_selector": True,
        "claims_enabled_at_build": {
            "ood_real": False,
            "cloud_tradeoff": False,
            "positive_lora": False,
            "positive_system": "pending",
        },
        "git": {
            "commit": _git(["rev-parse", "HEAD"]),
            "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        },
        "build": {
            "host": socket.gethostname(),
            "user": os.environ.get("USER", "unknown"),
            "utc": _dt.datetime.now(_dt.timezone.utc).isoformat(
                timespec="seconds"
            ),
        },
        "selector_config": {
            "path": "configs/robust_asr/router_v1.yaml",
            "sha256": _sha256(cfg_path),
        },
        "selector_evidence": {
            "path": "artifacts/robust_asr/router/selector_evidence.parquet",
            "sha256": evidence_sha,
        },
        "files": {
            "deterministic_selector.json": {
                "sha256": _sha256(selector_path),
                "size_bytes": selector_path.stat().st_size,
            },
            "rp5_inference.py": {
                "sha256": _sha256(rp5_path),
                "size_bytes": rp5_path.stat().st_size,
            },
            "test_vectors.json": {
                "sha256": _sha256(test_vectors_path),
                "size_bytes": test_vectors_path.stat().st_size,
            },
        },
        "section_reference": "agent_plan_v3_4_7 §1642-§1652 + §4001-§4046 (Branch B)",
    }
    metadata_path = out_dir / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, sort_keys=True)
        fh.write("\n")

    _assert_no_forbidden(out_dir)

    print("OK_DETERMINISTIC_SELECTOR_PACKAGE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
