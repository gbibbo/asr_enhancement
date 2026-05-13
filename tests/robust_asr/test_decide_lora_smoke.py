"""Unit tests for scripts/robust_asr/decide_lora_smoke.py.

Covers the Section 5.1 mechanical booleans:
  SMOKE_PASS / SMOKE_PARTIAL / SMOKE_FAIL / HALTED (EXPORT_BLOCKED)
plus the degenerate-evaluate-file guard.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "robust_asr" / "decide_lora_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("decide_lora_smoke", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_module()


def _eval_payload(
    macro: float,
    max_family: float,
    clean_reg: float,
    variance: float = 1e-4,
):
    return {
        "macro_wa_gain": macro,
        "max_family_wa_gain": max_family,
        "clean_wa_regression": clean_reg,
        "per_family_wa_gain_variance": variance,
        "per_family_wa_gain": {
            "clean": -clean_reg,
            "cafe_noise": max_family,
        },
    }


def test_pass_branch_a(mod):
    """macro_wa_gain >= 0.005 AND clean_regression <= 0.010 -> PASS."""
    outcome, marker, _ = mod.decide(_eval_payload(0.020, 0.020, 0.005), "PASS")
    assert outcome == "PASS"
    assert marker == ""


def test_pass_branch_b_low_macro(mod):
    """max_family >= 0.010 AND clean_regression <= 0.010 -> PASS even if macro low."""
    outcome, marker, _ = mod.decide(_eval_payload(0.001, 0.015, 0.005), "PASS")
    assert outcome == "PASS"
    assert marker == ""


def test_partial_above_pass_clean_threshold(mod):
    """max_family >= 0.010 AND clean_regression in (0.010, 0.020] -> PARTIAL."""
    outcome, marker, _ = mod.decide(_eval_payload(0.001, 0.015, 0.015), "PASS")
    assert outcome == "PARTIAL"
    assert marker == ""


def test_fail_low_family_gain(mod):
    """max_family < 0.010 cannot be PARTIAL -> FAIL."""
    outcome, marker, _ = mod.decide(_eval_payload(0.001, 0.005, 0.015), "PASS")
    assert outcome == "FAIL"
    assert marker == ""


def test_fail_clean_regression_too_high(mod):
    """clean_regression > 0.020 -> FAIL even with family gain."""
    outcome, marker, _ = mod.decide(_eval_payload(0.010, 0.020, 0.030), "PASS")
    assert outcome == "FAIL"
    assert marker == ""


def test_fail_negative_gains_real_p3_1_inputs(mod):
    """Mirrors the recorded P3.1 result.json (macro=-0.128, max_family=-0.113, clean=0.113)."""
    outcome, marker, reasons = mod.decide(
        _eval_payload(-0.12843, -0.11345, 0.11345, variance=1.79e-4),
        "PASS",
    )
    assert outcome == "FAIL"
    assert marker == ""
    assert reasons


def test_halted_on_export_blocked(mod):
    """Any non-PASS export outcome forces HALTED + EXPORT_BLOCKED."""
    outcome, marker, _ = mod.decide(_eval_payload(0.05, 0.05, 0.001), "FAIL")
    assert outcome == "HALTED"
    assert marker == "EXPORT_BLOCKED"


def test_degenerate_zero_variance_forces_fail(mod):
    """per_family_wa_gain_variance == 0.0 -> FAIL regardless of gains."""
    outcome, marker, reasons = mod.decide(
        _eval_payload(0.05, 0.05, 0.005, variance=0.0),
        "PASS",
    )
    assert outcome == "FAIL"
    assert marker == ""
    assert any("degenerate" in r.lower() for r in reasons)


def test_pass_boundary_exact_thresholds(mod):
    """Boundary at exactly the thresholds is PASS (>=, <=)."""
    outcome, marker, _ = mod.decide(_eval_payload(0.005, 0.010, 0.010), "PASS")
    assert outcome == "PASS"
    assert marker == ""


def test_partial_boundary_exact_thresholds(mod):
    """max_family == 0.010 with clean == 0.020 and macro < 0.005 -> PARTIAL."""
    outcome, marker, _ = mod.decide(
        _eval_payload(0.001, 0.010, 0.020), "PASS"
    )
    assert outcome == "PARTIAL"
    assert marker == ""


def test_cli_writes_report_first_line(tmp_path):
    """End-to-end: CLI writes outcome on first line and emits OK sentinel."""
    eval_payload = {
        "macro_wa_gain": -0.12843,
        "max_family_wa_gain": -0.11345,
        "clean_wa_regression": 0.11345,
        "per_family_wa_gain_variance": 1.79e-4,
        "per_family_wa_gain": {"clean": -0.11345},
    }
    export_payload = {"outcome": "PASS"}
    eval_path = tmp_path / "eval.json"
    export_path = tmp_path / "export.json"
    out_path = tmp_path / "report.md"
    eval_path.write_text(json.dumps(eval_payload), encoding="utf-8")
    export_path.write_text(json.dumps(export_payload), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(eval_path),
            "--export-input",
            str(export_path),
            "--out",
            str(out_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK_LORA_SMOKE_DECISION:FAIL" in proc.stdout
    first_line = out_path.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "FAIL"


def test_cli_missing_input_exits_1(tmp_path):
    out_path = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(tmp_path / "does_not_exist.json"),
            "--export-input",
            str(tmp_path / "also_missing.json"),
            "--out",
            str(out_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert not out_path.exists()
