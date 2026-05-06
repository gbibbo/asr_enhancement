"""T6.2b — tests for checkpoint save/load round-trip and metadata.

Requires torch. Login-node Python on datamove1 has no torch; these tests
run inside Apptainer via slurm/jobs/t6_2b_pytest_apptainer.sh.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts" / "training"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402


def _import_train_enhancer():
    if "train_enhancer" in sys.modules:
        return importlib.reload(sys.modules["train_enhancer"])
    return importlib.import_module("train_enhancer")


class _TinyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.conv = nn.Conv1d(1, 1, kernel_size=3, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # noqa: D401
        return self.conv(x)


def _state_dicts_equal(a: dict, b: dict) -> bool:
    if set(a.keys()) != set(b.keys()):
        return False
    for k, va in a.items():
        vb = b[k]
        if not torch.equal(va, vb):
            return False
    return True


def _make_cfg(tmp_path: Path) -> dict:
    return {
        "config_name": "test_cfg",
        "dataset_version": "test_dataset_v1",
        "degradation_version": "degradation_v1",
        "metrics_version": "metrics_v1",
        "training_split_version": "devclean_speaker_split_v1",
        "model": {
            "architecture": "spectral_unet_small_v1",
            "params": {
                "sample_rate": 16000,
                "n_fft": 512,
                "hop_length": 128,
                "win_length": 512,
            },
        },
    }


def test_save_checkpoint_writes_file(tmp_path: Path) -> None:
    te = _import_train_enhancer()
    model = _TinyModel()
    opt = torch.optim.Adam(model.parameters(), lr=1.0e-4)
    cfg = _make_cfg(tmp_path)
    ckpt = tmp_path / "ckpt" / "checkpoint_step_0000010.pt"
    out = te.save_checkpoint(
        path=ckpt,
        model=model,
        optimizer=opt,
        scheduler=None,
        step=10,
        cfg=cfg,
        config_path=tmp_path / "fake_config.yaml",
        config_sha256="0" * 64,
        run_id="test_run_id",
        slurm_job_id="local_test",
        parameter_count=sum(p.numel() for p in model.parameters()),
    )
    assert out == ckpt
    assert ckpt.exists()


def test_load_checkpoint_restores_model_state(tmp_path: Path) -> None:
    te = _import_train_enhancer()
    src = _TinyModel()
    # randomize weights, capture
    with torch.no_grad():
        for p in src.parameters():
            p.uniform_(-1.0, 1.0)
    opt = torch.optim.Adam(src.parameters(), lr=1.0e-4)
    cfg = _make_cfg(tmp_path)
    ckpt = tmp_path / "ckpt" / "checkpoint_step_0000020.pt"
    te.save_checkpoint(
        path=ckpt, model=src, optimizer=opt, scheduler=None, step=20,
        cfg=cfg, config_path=tmp_path / "cfg.yaml",
        config_sha256="a" * 64, run_id="rid", slurm_job_id="sj",
        parameter_count=sum(p.numel() for p in src.parameters()),
    )

    dst = _TinyModel()
    # Make sure dst state differs from src before load.
    with torch.no_grad():
        for p in dst.parameters():
            p.zero_()
    payload = te.load_checkpoint(ckpt, model=dst)
    assert payload["step"] == 20
    assert _state_dicts_equal(src.state_dict(), dst.state_dict())


def test_checkpoint_metadata_contains_required_keys(tmp_path: Path) -> None:
    te = _import_train_enhancer()
    model = _TinyModel()
    opt = torch.optim.Adam(model.parameters(), lr=1.0e-4)
    cfg = _make_cfg(tmp_path)
    ckpt = tmp_path / "ckpt" / "checkpoint_step_0000030.pt"
    te.save_checkpoint(
        path=ckpt, model=model, optimizer=opt, scheduler=None, step=30,
        cfg=cfg, config_path=tmp_path / "cfg.yaml",
        config_sha256="b" * 64, run_id="rid", slurm_job_id="sj",
        parameter_count=42,
    )
    payload = te.load_checkpoint(ckpt)
    for key in te.CHECKPOINT_METADATA_KEYS:
        assert key in payload, f"missing checkpoint metadata key: {key}"
    assert payload["model_architecture"] == "spectral_unet_small_v1"
    assert payload["training_split_version"] == "devclean_speaker_split_v1"
    assert payload["dataset_version"] == "test_dataset_v1"
    assert payload["degradation_version"] == "degradation_v1"
    assert payload["metrics_version"] == "metrics_v1"
    assert payload["parameter_count"] == 42
    assert payload["run_id"] == "rid"
    assert payload["slurm_job_id"] == "sj"


def test_prune_old_checkpoints_keeps_last_n(tmp_path: Path) -> None:
    te = _import_train_enhancer()
    cdir = tmp_path / "cks"
    cdir.mkdir(parents=True)
    for step in (10, 20, 30, 40, 50, 60, 70):
        (cdir / f"checkpoint_step_{step:07d}.pt").write_bytes(b"x")
    te._prune_old_checkpoints(cdir, keep_last_n=3)
    remaining = sorted(p.name for p in cdir.glob("checkpoint_step_*.pt"))
    assert remaining == [
        "checkpoint_step_0000050.pt",
        "checkpoint_step_0000060.pt",
        "checkpoint_step_0000070.pt",
    ]


def test_save_then_load_round_trip_preserves_optimizer(tmp_path: Path) -> None:
    te = _import_train_enhancer()
    model = _TinyModel()
    opt = torch.optim.Adam(model.parameters(), lr=2.0e-3)
    # take a step to populate optimizer state
    x = torch.randn(1, 1, 100)
    loss = model(x).abs().mean()
    loss.backward()
    opt.step()

    ckpt = tmp_path / "ck" / "checkpoint_step_0000100.pt"
    te.save_checkpoint(
        path=ckpt, model=model, optimizer=opt, scheduler=None, step=100,
        cfg=_make_cfg(tmp_path), config_path=tmp_path / "c.yaml",
        config_sha256="c" * 64, run_id="rid", slurm_job_id="sj",
        parameter_count=99,
    )

    new_model = _TinyModel()
    new_opt = torch.optim.Adam(new_model.parameters(), lr=2.0e-3)
    payload = te.load_checkpoint(ckpt, model=new_model, optimizer=new_opt)
    assert payload["step"] == 100
    # optimizer state restored: param_groups present and non-empty.
    assert new_opt.state_dict()["param_groups"]
