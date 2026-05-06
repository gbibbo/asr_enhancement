"""T6.2b — login-node-runnable static tests for `--validate-only` on
configs/training/full_training.yaml. Uses subprocess only; no torch import
required.

Mirrors the existing tests/training/test_train_enhancer_validate_only.py
patterns.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "training" / "train_enhancer.py"
CONFIG = REPO_ROOT / "configs" / "training" / "full_training.yaml"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def test_validate_only_full_training_yaml_exits_ok() -> None:
    assert SCRIPT.exists(), f"script missing: {SCRIPT}"
    assert CONFIG.exists(), f"config missing: {CONFIG}"
    cp = _run([sys.executable, str(SCRIPT), "--config", str(CONFIG), "--validate-only"])
    assert cp.returncode == 0, (
        f"validate-only failed: rc={cp.returncode}\n"
        f"stdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "OK: guards passed" in cp.stdout, (
        f"missing 'OK: guards passed' in stdout: {cp.stdout!r}"
    )
    assert "OK: training_split verified" in cp.stdout, (
        f"missing 'OK: training_split verified' in stdout: {cp.stdout!r}"
    )
    # The first OK line must report the real full-training counts.
    assert "train=2693" in cp.stdout, cp.stdout
    assert "val=13465" in cp.stdout, cp.stdout
    assert "families=5" in cp.stdout, cp.stdout
    # The training_split line must report the speaker-disjoint counts.
    assert "version=devclean_speaker_split_v1" in cp.stdout, cp.stdout
    assert "train_clean=2160" in cp.stdout, cp.stdout
    assert "val_clean=533" in cp.stdout, cp.stdout
    assert "train_degraded=10800" in cp.stdout, cp.stdout
    assert "val_degraded=2665" in cp.stdout, cp.stdout


def test_tampered_training_split_sha_blocks(tmp_path: Path) -> None:
    """Flipping one byte of any training_split.*_sha256 must yield BLOCKER."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    sha = cfg["training_split"]["train_clean_manifest_sha256"]
    # Flip the last hex character so the sha256 is the right length but wrong.
    last = sha[-1]
    flipped = "0" if last != "0" else "1"
    cfg["training_split"]["train_clean_manifest_sha256"] = sha[:-1] + flipped

    tampered = tmp_path / "full_training_tampered_sha.yaml"
    tampered.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    cp = _run([sys.executable, str(SCRIPT), "--config", str(tampered), "--validate-only"])
    assert cp.returncode != 0, (
        f"tampered training_split sha unexpectedly passed: rc={cp.returncode}\n"
        f"stdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "BLOCKER" in cp.stderr, f"missing BLOCKER in stderr: {cp.stderr!r}"
    assert "training_split.train_clean_manifest" in cp.stderr, cp.stderr
    assert "sha256 mismatch" in cp.stderr, cp.stderr


def test_tampered_training_split_path_blocks(tmp_path: Path) -> None:
    """Pointing a training_split.*_manifest at a non-existent path must yield BLOCKER."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    cfg["training_split"]["val_clean_manifest"] = str(
        tmp_path / "does_not_exist.jsonl"
    )

    tampered = tmp_path / "full_training_tampered_path.yaml"
    tampered.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    cp = _run([sys.executable, str(SCRIPT), "--config", str(tampered), "--validate-only"])
    assert cp.returncode != 0, (
        f"tampered training_split path unexpectedly passed: rc={cp.returncode}\n"
        f"stdout={cp.stdout!r}\nstderr={cp.stderr!r}"
    )
    assert "BLOCKER" in cp.stderr, cp.stderr
    assert "val_clean_manifest" in cp.stderr, cp.stderr
    assert "file not found" in cp.stderr, cp.stderr
