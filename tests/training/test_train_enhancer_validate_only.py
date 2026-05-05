"""T5.2 — static tests for scripts/training/train_enhancer.py.

These tests do not import torch, whisper, SpeechBrain, or enhancement code.
They invoke the script via subprocess in --validate-only mode and verify
exit codes and output text, plus a lightweight in-process check of the
GIT_COMMIT_AT_RUN / GIT_BRANCH_AT_RUN env-var fallback added in T5.3 so
that Slurm/Apptainer runs do not depend on `git` being installed inside
the container. They do not create any run artifacts.
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "training" / "train_enhancer.py"
CONFIG = REPO_ROOT / "configs" / "training" / "dry_run.yaml"
SCRIPT_DIR = REPO_ROOT / "scripts" / "training"


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


def _import_train_enhancer():
    """Import scripts/training/train_enhancer.py as a module without touching
    torch / whisper / matplotlib (none are imported at module load time).
    """
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    if "train_enhancer" in sys.modules:
        return importlib.reload(sys.modules["train_enhancer"])
    return importlib.import_module("train_enhancer")


def test_resolve_git_value_prefers_env_over_subprocess(monkeypatch) -> None:
    """T5.3 fix: GIT_COMMIT_AT_RUN / GIT_BRANCH_AT_RUN env vars must be
    preferred over the `git` subprocess. This is what allows the Slurm
    Apptainer run to record real git metadata without `git` being
    installed inside the container.
    """
    te = _import_train_enhancer()
    monkeypatch.setenv("GIT_COMMIT_AT_RUN", "deadbeefcafe1234")
    monkeypatch.setenv("GIT_BRANCH_AT_RUN", "feature/test-branch-name")
    assert (
        te._resolve_git_value("GIT_COMMIT_AT_RUN", "rev-parse", "HEAD")
        == "deadbeefcafe1234"
    )
    assert (
        te._resolve_git_value(
            "GIT_BRANCH_AT_RUN", "rev-parse", "--abbrev-ref", "HEAD"
        )
        == "feature/test-branch-name"
    )


def test_resolve_git_value_empty_env_falls_through(monkeypatch) -> None:
    """An empty env var must be treated as absent, not adopted as the value."""
    te = _import_train_enhancer()
    monkeypatch.setenv("GIT_COMMIT_AT_RUN", "")
    val = te._resolve_git_value("GIT_COMMIT_AT_RUN", "rev-parse", "HEAD")
    assert val != "", "empty env var must not be returned as the git value"


def test_resolve_git_value_unknown_when_no_env_and_no_git(monkeypatch) -> None:
    """If the env var is unset and `git` is not on PATH, the helper must
    return the literal string 'unknown' (matching the in-container case
    where git is missing). Verifies the failure mode is graceful, not a
    crash.
    """
    te = _import_train_enhancer()
    monkeypatch.delenv("GIT_COMMIT_AT_RUN", raising=False)
    monkeypatch.setenv("PATH", "")
    val = te._resolve_git_value("GIT_COMMIT_AT_RUN", "rev-parse", "HEAD")
    assert val == "unknown", f"expected 'unknown' fallback, got {val!r}"
