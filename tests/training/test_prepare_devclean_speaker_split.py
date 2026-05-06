"""T6.2a — tests for scripts/training/prepare_devclean_speaker_split.py.

Login-node-only (stdlib + pyyaml + pytest). No torch, no whisper, no
matplotlib, no audio IO. Uses tiny synthetic manifests with
--skip-source-sha-check so the strict source SHA-256 check is bypassed
for the synthetic data; the strict check is exercised separately by the
real split build at T6.2a closure.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "training" / "prepare_devclean_speaker_split.py"

EXPECTED_FAMILIES = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_synthetic_manifests(tmp_path: Path) -> tuple[Path, Path, Path]:
    speakers = ["100", "101", "102", "103", "104", "105", "106", "107", "108", "109"]
    clean_rows: list[dict] = []
    degraded_rows: list[dict] = []
    for spk in speakers:
        for i in range(3):
            uid = f"{spk}-c-{i:04d}"
            clean_rows.append(
                {
                    "dataset": "LibriSpeech",
                    "split": "dev-clean",
                    "speaker_id": spk,
                    "utterance_id": uid,
                    "audio_path": f"/tmp/{uid}.flac",
                    "transcript": "hello world",
                    "duration_seconds": 4.0,
                    "sample_rate": 16000,
                }
            )
            for fam in EXPECTED_FAMILIES:
                degraded_rows.append(
                    {
                        "utterance_id": uid,
                        "family": fam,
                        "split": "dev-clean",
                        "speaker_id": spk,
                        "transcript": "hello world",
                        "duration_seconds": 4.0,
                        "sample_rate": 16000,
                        "clean_audio_path": f"/tmp/{uid}.flac",
                        "degraded_audio_path": f"/tmp/{fam}/{uid}.wav",
                        "dataset_version": "synthetic_test",
                        "degradation_version": "degradation_v1",
                    }
                )
    clean_path = tmp_path / "clean.jsonl"
    with clean_path.open("w", encoding="utf-8") as f:
        for r in clean_rows:
            f.write(json.dumps(r) + "\n")
    deg_path = tmp_path / "degraded.jsonl"
    with deg_path.open("w", encoding="utf-8") as f:
        for r in degraded_rows:
            f.write(json.dumps(r) + "\n")
    reserved = {
        "examples": [
            {"utterance_id": "999-x-0000", "speaker_id": "999"},
            {"utterance_id": "998-x-0000", "speaker_id": "998"},
        ]
    }
    reserved_path = tmp_path / "reserved.yaml"
    reserved_path.write_text(yaml.safe_dump(reserved, sort_keys=False), encoding="utf-8")
    return clean_path, deg_path, reserved_path


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def _invoke(
    *,
    clean: Path,
    degraded: Path,
    reserved: Path,
    out_dir: Path,
    seed: int = 1234,
    val_fraction: float = 0.20,
    extra: list[str] | None = None,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--source-clean-manifest",
        str(clean),
        "--source-degraded-manifest",
        str(degraded),
        "--reserved-yaml",
        str(reserved),
        "--out-dir",
        str(out_dir),
        "--seed",
        str(seed),
        "--val-fraction",
        str(val_fraction),
        "--skip-source-sha-check",
    ]
    if extra:
        cmd.extend(extra)
    return _run(cmd)


def test_script_exists_and_compiles() -> None:
    assert SCRIPT.exists()
    cp = _run([sys.executable, "-m", "py_compile", str(SCRIPT)])
    assert cp.returncode == 0, cp.stderr


def test_split_is_speaker_disjoint(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    summary = json.loads((out / "split_summary.json").read_text(encoding="utf-8"))
    train = set((out / "train_speakers.txt").read_text().split())
    val = set((out / "val_speakers.txt").read_text().split())
    assert train & val == set()
    assert summary["speaker_overlap"] == []
    assert summary["train_speaker_count"] + summary["val_speaker_count"] == 10


def test_reserved_demo_ids_absent_in_both_splits(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp.returncode == 0, cp.stderr
    summary = json.loads((out / "split_summary.json").read_text(encoding="utf-8"))
    assert summary["reserved_demo_ids_absent_in_train"] is True
    assert summary["reserved_demo_ids_absent_in_val"] is True
    train_uids = {
        json.loads(line)["utterance_id"]
        for line in (out / "train_clean_manifest.jsonl").read_text().splitlines()
        if line.strip()
    }
    val_uids = {
        json.loads(line)["utterance_id"]
        for line in (out / "val_clean_manifest.jsonl").read_text().splitlines()
        if line.strip()
    }
    assert "999-x-0000" not in train_uids and "999-x-0000" not in val_uids


def test_deterministic_for_fixed_seed(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    cp_a = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out_a, seed=1234)
    cp_b = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out_b, seed=1234)
    assert cp_a.returncode == 0 and cp_b.returncode == 0
    for name in (
        "train_clean_manifest.jsonl",
        "val_clean_manifest.jsonl",
        "train_degraded_manifest.jsonl",
        "val_degraded_manifest.jsonl",
    ):
        assert _sha256_of_file(out_a / name) == _sha256_of_file(out_b / name), name


def test_summary_sha256_matches_files(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp.returncode == 0, cp.stderr
    summary = json.loads((out / "split_summary.json").read_text(encoding="utf-8"))
    for key, name in (
        ("train_clean_manifest_sha256", "train_clean_manifest.jsonl"),
        ("val_clean_manifest_sha256", "val_clean_manifest.jsonl"),
        ("train_degraded_manifest_sha256", "train_degraded_manifest.jsonl"),
        ("val_degraded_manifest_sha256", "val_degraded_manifest.jsonl"),
    ):
        assert summary[key] == _sha256_of_file(out / name), key


def test_per_family_counts_cover_all_five(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp.returncode == 0, cp.stderr
    summary = json.loads((out / "split_summary.json").read_text(encoding="utf-8"))
    for fam in EXPECTED_FAMILIES:
        assert fam in summary["per_family_train_counts"]
        assert fam in summary["per_family_val_counts"]
    train_total = sum(summary["per_family_train_counts"].values())
    val_total = sum(summary["per_family_val_counts"].values())
    assert train_total == summary["train_degraded_records"]
    assert val_total == summary["val_degraded_records"]
    assert train_total + val_total == 10 * 3 * len(EXPECTED_FAMILIES)


def test_refuses_overwrite_without_force(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp1 = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp1.returncode == 0
    cp2 = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp2.returncode != 0
    assert "BLOCKER" in cp2.stderr


def test_force_allows_overwrite(tmp_path: Path) -> None:
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp1 = _invoke(clean=clean, degraded=degraded, reserved=reserved, out_dir=out)
    assert cp1.returncode == 0
    cp2 = _invoke(
        clean=clean, degraded=degraded, reserved=reserved, out_dir=out, extra=["--force"]
    )
    assert cp2.returncode == 0


def test_strict_source_sha_check_rejects_mismatch(tmp_path: Path) -> None:
    """When --skip-source-sha-check is NOT passed, the strict SHA gate must
    reject synthetic manifests (their SHA-256 will not match the frozen
    production values).
    """
    clean, degraded, reserved = _make_synthetic_manifests(tmp_path)
    out = tmp_path / "out"
    cp = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source-clean-manifest",
            str(clean),
            "--source-degraded-manifest",
            str(degraded),
            "--reserved-yaml",
            str(reserved),
            "--out-dir",
            str(out),
            "--seed",
            "1234",
            "--val-fraction",
            "0.20",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert cp.returncode != 0
    assert "BLOCKER" in cp.stderr
    assert "sha256" in cp.stderr.lower()
