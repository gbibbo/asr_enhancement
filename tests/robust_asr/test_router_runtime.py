"""Runtime regression for the packaged deterministic selector (P7.3).

Required by agent plan §2669 (P7 gate Branch B predicate): the
deterministic selector at
artifacts/robust_asr/router/selected_router/ must satisfy every
test_vectors.json tuple via the packaged rp5_inference.predict()
function. The test also enforces the mandatory no-touch invariants on
the selected_router/ directory (no audio, model weights, secrets, or
binary checkpoints).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTED_ROUTER = REPO_ROOT / "artifacts" / "robust_asr" / "router" / "selected_router"

SELECTOR_JSON = SELECTED_ROUTER / "deterministic_selector.json"
METADATA_JSON = SELECTED_ROUTER / "metadata.json"
RP5_INFERENCE_PY = SELECTED_ROUTER / "rp5_inference.py"
TEST_VECTORS_JSON = SELECTED_ROUTER / "test_vectors.json"

FORBIDDEN_SUFFIXES = (
    ".wav", ".flac", ".mp3", ".m4a",
    ".pt", ".pth", ".ckpt", ".bin", ".safetensors",
    ".key", ".pem", ".token",
)


def _load_rp5_inference():
    """Import rp5_inference.py from the packaged location."""
    spec = importlib.util.spec_from_file_location(
        "rp5_inference", RP5_INFERENCE_PY
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selected_router_files_exist():
    for path in (SELECTOR_JSON, METADATA_JSON, RP5_INFERENCE_PY, TEST_VECTORS_JSON):
        assert path.exists(), f"missing: {path}"
        assert path.is_file(), f"not a regular file: {path}"


def test_selected_router_has_no_forbidden_artifacts():
    """No audio, model weights, secrets, or binary checkpoints."""
    for p in SELECTED_ROUTER.rglob("*"):
        if not p.is_file():
            continue
        name = p.name
        suf = p.suffix.lower()
        assert suf not in FORBIDDEN_SUFFIXES, (
            f"forbidden suffix under selected_router: {p}"
        )
        assert not name.startswith(".env"), (
            f"forbidden .env-prefixed file under selected_router: {p}"
        )
        assert name not in (".env",), (
            f"forbidden file under selected_router: {p}"
        )


def test_rp5_inference_is_stdlib_only():
    """rp5_inference.py must not import third-party packages.

    The RP5 device only has the stdlib + the CT2 runtime available at
    inference time; the deterministic selector must be loadable
    without numpy/torch/requests/etc.
    """
    src = RP5_INFERENCE_PY.read_text(encoding="utf-8")
    forbidden_imports = (
        "import numpy", "from numpy",
        "import torch", "from torch",
        "import requests", "from requests",
        "import yaml", "from yaml",
        "import pandas", "from pandas",
        "import pyarrow", "from pyarrow",
        "import scipy", "from scipy",
    )
    for token in forbidden_imports:
        assert token not in src, f"rp5_inference.py contains {token!r}"


def test_selector_json_constants_match_section_5_5():
    doc = json.loads(SELECTOR_JSON.read_text(encoding="utf-8"))
    constants = doc["constants"]
    assert constants["ask_repeat_threshold"] == -1.0
    assert constants["escalate_threshold"] == -0.5
    assert constants["no_speech_threshold"] == 0.6
    assert constants["health_check_ttl_seconds"] == 300
    assert doc["selector_kind"] == "deterministic_selector"
    assert doc["deterministic_selector_version"] == "deterministic_selector_v1"
    assert doc["deployable_actions"] == ["whisper_base_ct2_int8", "ask_repeat"]


def test_metadata_records_outcome_e_claims():
    md = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
    assert md["selector_kind"] == "deterministic_selector"
    assert md["outcome_e_deterministic_selector"] is True
    assert md["cloud_available_at_build"] is False
    assert md["lora_available_at_build"] is False
    assert md["deployable_backends"] == ["whisper_base_ct2_int8"]
    claims = md["claims_enabled_at_build"]
    assert claims["ood_real"] is False
    assert claims["cloud_tradeoff"] is False
    assert claims["positive_lora"] is False
    assert claims["positive_system"] == "pending"


def test_test_vectors_has_at_least_16_tuples():
    doc = json.loads(TEST_VECTORS_JSON.read_text(encoding="utf-8"))
    assert doc["count"] >= 16, doc["count"]
    assert len(doc["vectors"]) == doc["count"]
    # Coverage: every Section 5.5 branch must be exercised somewhere.
    expected_actions = {"whisper_base_ct2_int8", "assemblyai", "ask_repeat"}
    seen_actions = {v["expected_action"] for v in doc["vectors"]}
    assert seen_actions == expected_actions, seen_actions
    expected_reasons = {"no_speech", "low_logprob", "escalate_cloud", "baseline"}
    seen_reasons = {v["expected_reason"] for v in doc["vectors"]}
    assert seen_reasons == expected_reasons, seen_reasons


def test_rp5_inference_matches_test_vectors():
    module = _load_rp5_inference()
    doc = json.loads(TEST_VECTORS_JSON.read_text(encoding="utf-8"))
    failures = []
    for v in doc["vectors"]:
        result = module.predict(
            v["decode_features"],
            assemblyai_available=v["assemblyai_available"],
        )
        if (
            result["action"] != v["expected_action"]
            or result["reason"] != v["expected_reason"]
        ):
            failures.append((v["id"], v, result))
    assert not failures, failures


def test_rp5_inference_defaults_are_outcome_e_safe():
    """assemblyai_available defaults to False (matches BLOCKED_API)."""
    module = _load_rp5_inference()
    result = module.predict({"no_speech_prob": 0.0, "avg_logprob": -0.7})
    assert result["action"] == "whisper_base_ct2_int8"
    assert result["reason"] == "baseline"


def test_rp5_inference_does_not_emit_cloud_without_flag():
    """If assemblyai_available is False, no row may route to assemblyai."""
    module = _load_rp5_inference()
    for avg_logprob in (-0.6, -0.51, -0.5, -0.99, -1.0, 0.0):
        result = module.predict(
            {"no_speech_prob": 0.0, "avg_logprob": avg_logprob},
            assemblyai_available=False,
        )
        assert result["action"] != "assemblyai", (avg_logprob, result)


def test_selected_router_dir_has_only_expected_files():
    """No stray files under selected_router/ — exactly the four
    package files plus optionally a .gitkeep are allowed."""
    allowed = {
        "deterministic_selector.json",
        "metadata.json",
        "rp5_inference.py",
        "test_vectors.json",
        ".gitkeep",
    }
    found = {p.name for p in SELECTED_ROUTER.iterdir() if p.is_file()}
    extras = found - allowed
    assert not extras, f"unexpected files under selected_router: {extras}"


def test_metadata_file_sha256s_match_on_disk():
    """metadata.files[*].sha256 must match the actual file contents.

    Catches accidental post-build edits to the packaged files.
    """
    import hashlib

    md = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
    for fname, info in md["files"].items():
        actual_path = SELECTED_ROUTER / fname
        h = hashlib.sha256()
        with actual_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        assert h.hexdigest() == info["sha256"], (
            f"{fname}: metadata sha256 != on-disk sha256"
        )


def test_selector_evidence_sha256_matches_parquet():
    """metadata.selector_evidence.sha256 must match the parquet on disk."""
    import hashlib

    md = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
    evidence_path = REPO_ROOT / md["selector_evidence"]["path"]
    if not evidence_path.exists():
        pytest.skip("selector_evidence.parquet missing")
    h = hashlib.sha256()
    with evidence_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == md["selector_evidence"]["sha256"]


def test_rp5_inference_runs_under_stdlib_only_subprocess():
    """Sanity: rp5_inference imports and runs in a clean subprocess
    that has no PYTHONPATH pointing at this repo's libs/."""
    script = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location("
        f"'rp5_inference', r'{RP5_INFERENCE_PY}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        "r = m.predict({'no_speech_prob': 0.99, 'avg_logprob': 0.0})\n"
        "assert r['action'] == 'ask_repeat' and r['reason'] == 'no_speech', r\n"
        "print('OK')\n"
    )
    env_clean = {"PATH": "/usr/bin:/bin"}
    proc = subprocess.run(
        [sys.executable, "-I", "-c", script],
        env=env_clean,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "OK" in proc.stdout, proc.stdout
