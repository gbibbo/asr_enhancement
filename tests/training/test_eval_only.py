"""T6.3 — login-node-safe tests for the `--eval-checkpoint` mode.

These tests cover the helpers added to `scripts/training/train_enhancer.py`
for the T6.3 post-hoc Whisper evaluation gate (`_check_eval_paths` and the
new `cmd_eval_only` dispatch surface):

  * `_check_eval_paths` rejects checkpoint missing / inside-repo;
  * `_check_eval_paths` rejects eval_out_dir inside-repo / inside the source
    checkpoint's run_dir;
  * `_check_eval_paths` accepts well-formed paths;
  * subprocess `--eval-checkpoint /tmp/missing.pt --validate-only` blocks
    cleanly with rc=2;
  * subprocess `--eval-checkpoint <real path> --eval-out-dir <inside repo>
    --validate-only` blocks with rc=2;
  * subprocess `--eval-checkpoint <real path> --eval-out-dir <inside source
    run_dir> --validate-only` blocks with rc=2;
  * subprocess `--eval-checkpoint <real path> --enable-whisper-val
    --validate-only` blocks (mutually exclusive flags);
  * subprocess regression: `--validate-only` against `full_training.yaml`
    (no eval flags) still exits 0;
  * subprocess regression: `--validate-only --enable-whisper-val` against
    `full_training.yaml` (no eval flags) still exits 2.

Hard scope guards (must remain TRUE):
  * No `import torch`. No `import whisper`. No `import torchaudio`.
  * No `import matplotlib`. No `import scipy`.
  * Tests run on the datamove1 login node and do not load any checkpoint
    (the "real path" used by the eval_out_dir tests is a tiny dummy file
    written by pytest under tmp_path; cmd_eval_only's --validate-only
    branch never torch.loads it).
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_SCRIPT_DIR = REPO_ROOT / "scripts" / "training"
SCRIPT = TRAIN_SCRIPT_DIR / "train_enhancer.py"
FULL_CONFIG = REPO_ROOT / "configs" / "training" / "full_training.yaml"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TRAIN_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(TRAIN_SCRIPT_DIR))


def _import_train_enhancer():
    return importlib.import_module("train_enhancer")


def _forbid_heavy_imports() -> None:
    forbidden = ("torch", "whisper", "torchaudio", "matplotlib", "scipy")
    for name in forbidden:
        assert name not in sys.modules, (
            f"forbidden heavy import already loaded: {name!r}; T6.3 eval-only "
            f"helper must stay login-node-safe (no torch/whisper/torchaudio/"
            f"matplotlib/scipy)."
        )


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


# ---------------------------------------------------------------------------
# _check_eval_paths — pure path-policy helper, no torch.
# ---------------------------------------------------------------------------
def test_check_eval_paths_rejects_missing_checkpoint(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()
    _forbid_heavy_imports()

    out = tmp_path / "eval_out"
    errors = te._check_eval_paths(
        eval_checkpoint=tmp_path / "no_such.pt", eval_out_dir=out
    )
    assert errors and any("not found" in e for e in errors)


def test_check_eval_paths_rejects_checkpoint_inside_repo(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    inside = REPO_ROOT / "scripts" / "training" / "train_enhancer.py"  # any tracked file
    errors = te._check_eval_paths(
        eval_checkpoint=inside, eval_out_dir=tmp_path / "eval_out"
    )
    assert errors and any("outside the repo" in e for e in errors)


def test_check_eval_paths_rejects_eval_out_dir_inside_repo(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    # Create a fake checkpoint outside the repo (under tmp_path).
    fake_ck = tmp_path / "run" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    inside_repo_out = REPO_ROOT / "tests" / "training" / "_eval_out_inside_repo"
    errors = te._check_eval_paths(
        eval_checkpoint=fake_ck, eval_out_dir=inside_repo_out
    )
    assert errors and any("eval-out-dir must be outside the repo" in e for e in errors)


def test_check_eval_paths_rejects_eval_out_dir_inside_source_run_dir(
    tmp_path: Path,
) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    fake_ck = tmp_path / "src_run_dir" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    bad_out = tmp_path / "src_run_dir" / "post_eval"  # inside the source run_dir
    errors = te._check_eval_paths(eval_checkpoint=fake_ck, eval_out_dir=bad_out)
    assert errors and any(
        "outside the T6.2 run_dir" in e for e in errors
    )


def test_check_eval_paths_accepts_well_formed(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    fake_ck = tmp_path / "src_run" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    # A sibling out dir under tmp_path is outside repo and outside src_run.
    out = tmp_path / "post_hoc_out"
    errors = te._check_eval_paths(eval_checkpoint=fake_ck, eval_out_dir=out)
    assert errors == []


# ---------------------------------------------------------------------------
# Subprocess --validate-only blockers and regressions.
# ---------------------------------------------------------------------------
def test_subprocess_validate_only_full_training_no_eval_flags_passes() -> None:
    _forbid_heavy_imports()
    cp = _run([sys.executable, str(SCRIPT), "--config", str(FULL_CONFIG), "--validate-only"])
    assert cp.returncode == 0, (
        f"validate-only on full_training.yaml regressed after T6.3 patch:\n"
        f"rc={cp.returncode} stdout={cp.stdout!r} stderr={cp.stderr!r}"
    )


def test_subprocess_validate_only_full_training_with_enable_whisper_val_blocks() -> None:
    _forbid_heavy_imports()
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--enable-whisper-val",
    ])
    assert cp.returncode == 2
    assert "whisper-cli-consistency" in cp.stderr


def test_subprocess_eval_checkpoint_missing_blocks(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    out = tmp_path / "eval_out"
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--eval-checkpoint", str(tmp_path / "no_such.pt"),
        "--eval-out-dir", str(out),
    ])
    assert cp.returncode == 2
    assert "eval-paths" in cp.stderr
    assert "not found" in cp.stderr


def test_subprocess_eval_out_dir_inside_repo_blocks(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    fake_ck = tmp_path / "run" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    inside_repo_out = REPO_ROOT / "tests" / "training" / "_eval_out_inside_repo"
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--eval-checkpoint", str(fake_ck),
        "--eval-out-dir", str(inside_repo_out),
    ])
    assert cp.returncode == 2
    assert "eval-paths" in cp.stderr
    assert "must be outside the repo" in cp.stderr


def test_subprocess_eval_out_dir_inside_source_run_dir_blocks(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    fake_ck = tmp_path / "src_run" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    bad_out = tmp_path / "src_run" / "post_eval"
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--eval-checkpoint", str(fake_ck),
        "--eval-out-dir", str(bad_out),
    ])
    assert cp.returncode == 2
    assert "eval-paths" in cp.stderr
    assert "outside the T6.2 run_dir" in cp.stderr


def test_subprocess_eval_with_enable_whisper_val_blocks(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    fake_ck = tmp_path / "src_run" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    out = tmp_path / "post_eval"
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--eval-checkpoint", str(fake_ck),
        "--eval-out-dir", str(out),
        "--enable-whisper-val",
    ])
    assert cp.returncode == 2
    assert "mutually exclusive" in cp.stderr


def test_subprocess_eval_well_formed_passes(tmp_path: Path) -> None:
    """Well-formed --validate-only --eval-checkpoint should pass: it
    performs path/version/SHA/manifest/transcript checks without loading
    the checkpoint with torch.
    """
    _forbid_heavy_imports()
    fake_ck = tmp_path / "src_run" / "checkpoints" / "latest.pt"
    fake_ck.parent.mkdir(parents=True)
    fake_ck.write_bytes(b"\x00")
    out = tmp_path / "post_eval"
    cp = _run([
        sys.executable, str(SCRIPT),
        "--config", str(FULL_CONFIG),
        "--validate-only",
        "--eval-checkpoint", str(fake_ck),
        "--eval-out-dir", str(out),
        "--eval-per-family-cap", "1",
        "--whisper-device", "cuda",
    ])
    assert cp.returncode == 0, (
        f"well-formed eval validate-only should pass:\n"
        f"rc={cp.returncode} stdout={cp.stdout!r} stderr={cp.stderr!r}"
    )
    assert "OK: eval-only pre-flight verified" in cp.stdout


# ---------------------------------------------------------------------------
# Final guard.
# ---------------------------------------------------------------------------
def test_no_heavy_imports_in_module() -> None:
    _forbid_heavy_imports()
    _import_train_enhancer()
    _forbid_heavy_imports()
