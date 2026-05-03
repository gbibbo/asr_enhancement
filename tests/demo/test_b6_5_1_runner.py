"""Unit tests for scripts/demo/run_reference_whisper.py (B6.5.1).

Tests load the script via importlib.util.spec_from_file_location so they do
not depend on /app/scripts being on sys.path inside the demo container.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "demo" / "run_reference_whisper.py"


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location(
        "run_reference_whisper_under_test", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def candidates_json(tmp_path: Path) -> Path:
    payload = []
    for ex_id, gt in [
        ("ex001", "MISTER QUILTER IS THE APOSTLE OF THE MIDDLE CLASSES"),
        ("ex003", "YET THE MOST CHARITABLE CRITICISM"),
        ("ex004", "HE HAD NEVER BEEN FATHER LOVER HUSBAND FRIEND"),
        ("ex007", "HOW INFINITE THE WEALTH OF LOVE AND HOPE"),
        ("ex010", "THE NARRATIVE IT MAY BE IS WOVEN OF SO HUMBLE A TEXTURE"),
    ]:
        payload.append({
            "example_id": ex_id,
            "source_recording_id": f"src-{ex_id}",
            "ground_truth": gt,
            "speaker_id": "999",
            "duration_seconds": 5.0,
            "audio_sha256": "0" * 64,
        })
    p = tmp_path / "candidates.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


@pytest.fixture
def examples_json(tmp_path: Path) -> Path:
    DEGRADATIONS = [
        "far_field_room", "cafe_background", "phone_call",
        "muffled", "broadband_hiss",
    ]
    payload = []
    for ex_id in ("ex001", "ex003", "ex004", "ex007", "ex010"):
        payload.append({
            "example_id": ex_id,
            "title": f"title {ex_id}",
            "description": "test",
            "duration_seconds": 5.0,
            "degradation_ids": list(DEGRADATIONS),
            "ground_truth": f"gt {ex_id}",
            "audio_available": True,
            "clean_audio_path": f"{ex_id}/clean.wav",
            "degraded_audio_paths": {
                d: f"{ex_id}/{d}.wav" for d in DEGRADATIONS
            },
        })
    p = tmp_path / "examples.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


@pytest.fixture
def artifacts_root(tmp_path: Path) -> Path:
    """Write 30 tiny WAV files (5 examples × 6 variants), each with unique bytes."""
    root = tmp_path / "artifacts"
    DEGRADATIONS = [
        "far_field_room", "cafe_background", "phone_call",
        "muffled", "broadband_hiss",
    ]
    for ex_id in ("ex001", "ex003", "ex004", "ex007", "ex010"):
        ex_dir = root / ex_id
        ex_dir.mkdir(parents=True, exist_ok=True)
        for variant in ("clean", *DEGRADATIONS):
            (ex_dir / f"{variant}.wav").write_bytes(
                f"audio-{ex_id}-{variant}".encode("utf-8")
            )
    return root


def _make_fake_transcriber():
    """Replace _Transcriber with a deterministic stub."""
    class _Fake:
        def __init__(self, engine: str, model: str):
            self.engine = engine
            self.model_name = model
            self.calls: list[tuple[str, str]] = []

        def transcribe(self, audio_path: Path, job_id: str) -> str:
            self.calls.append((str(audio_path), job_id))
            return f"hyp-{job_id}"
    return _Fake


def test_run_writes_30_rows_with_frozen_versions(
    runner, candidates_json, examples_json, artifacts_root, tmp_path
):
    out = tmp_path / "out.json"
    Fake = _make_fake_transcriber()
    with patch.object(runner, "_Transcriber", Fake):
        report = runner.run(
            engine="faster-whisper",
            model="tiny.en",
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            output_path=out,
            resume=False,
        )

    assert report["engine"] == "faster-whisper"
    assert report["model"] == "tiny.en"
    assert report["degradation_version"] == "degradation_v1"
    assert report["metrics_version"] == "1.0"
    assert report["default_enhancer_version"] == "1.0"
    assert len(report["results"]) == 30
    assert {r["example_id"] for r in report["results"]} == {
        "ex001", "ex003", "ex004", "ex007", "ex010"
    }
    assert {r["degradation_id"] for r in report["results"]} == {
        "clean", "far_field_room", "cafe_background", "phone_call",
        "muffled", "broadband_hiss",
    }
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk == report


def test_each_row_has_sha256_and_nonneg_latency(
    runner, candidates_json, examples_json, artifacts_root, tmp_path
):
    out = tmp_path / "out.json"
    Fake = _make_fake_transcriber()
    with patch.object(runner, "_Transcriber", Fake):
        report = runner.run(
            engine="faster-whisper",
            model="tiny.en",
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            output_path=out,
            resume=False,
        )

    seen_sha = set()
    for row in report["results"]:
        assert isinstance(row["audio_sha256"], str) and len(row["audio_sha256"]) == 64
        assert row["latency_seconds"] >= 0
        assert row["wer"] is not None
        assert 0.0 <= row["word_accuracy"] <= 1.0
        assert isinstance(row["hypothesis"], str)
        seen_sha.add(row["audio_sha256"])
    assert len(seen_sha) == 30


def test_resume_skips_existing_pairs(
    runner, candidates_json, examples_json, artifacts_root, tmp_path
):
    out = tmp_path / "out.json"
    Fake = _make_fake_transcriber()

    fake1 = Fake("faster-whisper", "tiny.en")
    with patch.object(runner, "_Transcriber", lambda **kw: fake1):
        runner.run(
            engine="faster-whisper", model="tiny.en",
            examples_path=examples_json, candidates_path=candidates_json,
            artifacts_root=artifacts_root, output_path=out, resume=False,
        )
    initial_calls = len(fake1.calls)
    assert initial_calls == 30

    # Drop one row from the persisted JSON, then resume.
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    on_disk["results"] = on_disk["results"][:-1]
    out.write_text(json.dumps(on_disk), encoding="utf-8")

    fake2 = Fake("faster-whisper", "tiny.en")
    with patch.object(runner, "_Transcriber", lambda **kw: fake2):
        report = runner.run(
            engine="faster-whisper", model="tiny.en",
            examples_path=examples_json, candidates_path=candidates_json,
            artifacts_root=artifacts_root, output_path=out, resume=True,
        )
    # Only the dropped row should have been re-transcribed.
    assert len(fake2.calls) == 1
    assert len(report["results"]) == 30


def test_openai_whisper_engine_does_not_import_whisper_when_unselected(
    runner, candidates_json, examples_json, artifacts_root, tmp_path
):
    """The bare `whisper` module must not be imported under the faster-whisper engine."""
    sys.modules.pop("whisper", None)

    Fake = _make_fake_transcriber()
    out = tmp_path / "out.json"
    with patch.object(runner, "_Transcriber", Fake):
        runner.run(
            engine="faster-whisper", model="tiny.en",
            examples_path=examples_json, candidates_path=candidates_json,
            artifacts_root=artifacts_root, output_path=out, resume=False,
        )

    assert "whisper" not in sys.modules


def test_openai_whisper_path_uses_whisper_module(
    runner, candidates_json, examples_json, artifacts_root, tmp_path
):
    """Selecting --engine openai-whisper must call into a `whisper` module."""
    fake_whisper = types.ModuleType("whisper")

    class _FakeModel:
        def transcribe(self, audio_path, language="en"):
            return {"text": f"openai-hyp::{Path(audio_path).name}"}

    fake_whisper.load_model = MagicMock(return_value=_FakeModel())  # type: ignore[attr-defined]

    out = tmp_path / "out.json"
    sys.modules["whisper"] = fake_whisper
    try:
        report = runner.run(
            engine="openai-whisper", model="tiny.en",
            examples_path=examples_json, candidates_path=candidates_json,
            artifacts_root=artifacts_root, output_path=out, resume=False,
        )
    finally:
        sys.modules.pop("whisper", None)

    fake_whisper.load_model.assert_called_once_with("tiny.en")
    assert report["engine"] == "openai-whisper"
    assert all(r["hypothesis"].startswith("openai-hyp::") for r in report["results"])


def test_resolve_variant_path_handles_clean_and_degraded(runner, tmp_path):
    example = {
        "example_id": "ex001",
        "clean_audio_path": "ex001/clean.wav",
        "degraded_audio_paths": {"phone_call": "ex001/phone_call.wav"},
    }
    root = tmp_path
    assert (
        runner._resolve_variant_path(example, root, "clean")
        == root / "ex001/clean.wav"
    )
    assert (
        runner._resolve_variant_path(example, root, "phone_call")
        == root / "ex001/phone_call.wav"
    )


def test_degradation_parameters_signature_is_stable(runner):
    sig1 = runner._degradation_parameters_signature()
    sig2 = runner._degradation_parameters_signature()
    assert sig1 == sig2
    # When the registry is importable the signature must be a sha256 hex.
    if sig1:
        assert len(sig1) == 64
        int(sig1, 16)
