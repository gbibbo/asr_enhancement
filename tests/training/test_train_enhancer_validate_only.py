"""T5.2 — static tests for scripts/training/train_enhancer.py.

These tests do not import torch, whisper, SpeechBrain, or enhancement code.
They only invoke the script via subprocess in --validate-only mode and
verify exit codes and output text. They do not create any run artifacts.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "training" / "train_enhancer.py"
CONFIG = REPO_ROOT / "configs" / "training" / "dry_run.yaml"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def test_validate_only_real_config_exits_ok() -> None:
    assert SCRIPT.exists(), f"script missing: {SCRIPT}"
    assert CONFIG.exists(), f"config missing: {CONFIG}"
    cp = _run([sys.executable, str(SCRIPT), "--config", str(CONFIG), "--validate-only"])
    assert cp.returncode == 0, (
        f"validate-only failed: rc={cp.returncode}\n"
        f"stdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert cp.stdout.startswith("OK:") or "OK:" in cp.stdout, (
        f"missing OK in stdout: stdout={cp.stdout!r} stderr={cp.stderr!r}"
    )


def test_tampered_steps_too_high_blocks(tmp_path: Path) -> None:
    """A copy of dry_run.yaml with training.steps = 500 must fail with BLOCKER."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    cfg["training"]["steps"] = 500
    tampered = tmp_path / "dry_run_tampered.yaml"
    tampered.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    cp = _run([sys.executable, str(SCRIPT), "--config", str(tampered), "--validate-only"])
    assert cp.returncode != 0, (
        f"tampered config unexpectedly passed: rc={cp.returncode}\n"
        f"stdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "BLOCKER" in cp.stderr, f"missing BLOCKER in stderr: {cp.stderr!r}"
    assert "steps" in cp.stderr.lower(), (
        f"tampered failure should mention steps: stderr={cp.stderr!r}"
    )

    # Make sure no run dir was created during the tampered run.
    artifact_root = Path(cfg["paths"]["artifact_root"])
    if artifact_root.exists():
        # Only assert that no new t5_2_local_* or t5_3_dry_run_VALIDATE_ONLY
        # subdir was created from this test invocation.
        suspicious = [p for p in artifact_root.iterdir() if "VALIDATE_ONLY" in p.name]
        assert not suspicious, f"validate-only must not create run dirs: {suspicious}"
