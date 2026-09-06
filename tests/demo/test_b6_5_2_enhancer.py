"""Unit tests for scripts/demo/run_enhancer_validation.py (B6.5.2).

Tests load the script via importlib so they do not depend on /app/scripts
being on sys.path. They patch the WhisperAdapter via the runner's
_Transcriber stub so no real Whisper inference runs.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "demo" / "run_enhancer_validation.py"

EXAMPLE_IDS = ("ex001", "ex003", "ex004", "ex007", "ex010")
DEGRADATIONS = (
    "far_field_room", "cafe_background", "phone_call",
    "muffled", "broadband_hiss",
)
VARIANTS = ("clean",) + DEGRADATIONS


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location(
        "run_enhancer_validation_under_test", SCRIPT_PATH
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
    payload = []
    for ex_id in EXAMPLE_IDS:
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
    root = tmp_path / "artifacts"
    for ex_id in EXAMPLE_IDS:
        ex_dir = root / ex_id
        ex_dir.mkdir(parents=True, exist_ok=True)
        for variant in VARIANTS:
            (ex_dir / f"{variant}.wav").write_bytes(
                f"audio-{ex_id}-{variant}".encode("utf-8")
            )
    return root


def _build_baseline(
    artifacts_root: Path,
    candidates_json: Path,
    examples_json: Path,
    *,
    word_accuracy_per_pair: dict[tuple[str, str], float] | None = None,
):
    """Construct a baseline payload whose word_accuracy values match what the
    runner will compute from the stub transcriber, so delta_wa == 0.0 for all
    rows by default. Tests can pass word_accuracy_per_pair to perturb a row.
    """
    examples = json.loads(examples_json.read_text())
    candidates = json.loads(candidates_json.read_text())
    candidates_by_id = {c["example_id"]: c for c in candidates}

    rows = []
    for ex in examples:
        ex_id = ex["example_id"]
        for variant in VARIANTS:
            wa = None
            if word_accuracy_per_pair is not None and (ex_id, variant) in word_accuracy_per_pair:
                wa = word_accuracy_per_pair[(ex_id, variant)]
            rows.append({
                "example_id": ex_id,
                "source_recording_id": candidates_by_id[ex_id]["source_recording_id"],
                "degradation_id": variant,
                "word_accuracy": wa,
                "wer": None,
            })
    return {
        "engine": "faster-whisper",
        "model": "tiny.en",
        "generated_at": "2026-05-03T00:58:12.801695+00:00",
        "results": rows,
    }


class _StubTranscriber:
    """Returns the candidate ground truth verbatim → word_accuracy == 1.0."""

    def __init__(self, examples_path: Path, candidates_path: Path):
        candidates = json.loads(Path(candidates_path).read_text())
        self._gt_by_id = {c["example_id"]: c["ground_truth"] for c in candidates}
        self.calls: list[tuple[str, str]] = []

    def transcribe(self, audio_path: Path, job_id: str) -> str:
        self.calls.append((str(audio_path), job_id))
        ex_id = job_id.split("-")[0]
        return self._gt_by_id[ex_id]


def _patch_transcriber(runner, examples_json: Path, candidates_json: Path):
    stub = _StubTranscriber(examples_json, candidates_json)
    return patch.object(runner, "_Transcriber", lambda model_name=None: stub), stub


def test_runner_produces_30_bypass_rows_and_correct_metadata(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    baseline = _build_baseline(artifacts_root, candidates_json, examples_json)
    # Stub transcriber returns ground truth → wa = 1.0 for every row.
    for row in baseline["results"]:
        row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    out = tmp_path / "report.json"
    md = tmp_path / "report.md"
    enhanced_root = tmp_path / "enhanced"

    patch_ctx, stub = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        report = runner.run(
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            baseline_rp5_path=baseline_path,
            enhanced_output_root=enhanced_root,
            output_path=out,
            md_path=md,
        )

    assert report["task"] == "B6.5.2"
    assert report["asr_engine"] == "faster-whisper"
    assert report["asr_model"] == "tiny.en"
    assert report["degradation_version"] == "degradation_v1"
    assert report["metrics_version"] == "1.0"
    assert report["default_enhancer_version"] == "1.0"
    assert report["scope"] == list(EXAMPLE_IDS)
    assert report["variant_ids"] == list(VARIANTS)

    bypass = report["enhancers"]["bypass"]
    assert bypass["enhancer_version"] == "bypass"
    assert bypass["status"] == "ok"
    assert bypass["offenders"] == []
    assert len(bypass["rows"]) == 30
    assert {(r["example_id"], r["degradation_id"]) for r in bypass["rows"]} == {
        (ex, v) for ex in EXAMPLE_IDS for v in VARIANTS
    }

    agg = bypass["aggregates"]
    assert agg["n_rows"] == 30
    assert agg["n_input_equals_output"] == 30
    assert agg["n_rows_with_nonzero_delta"] == 0
    assert agg["max_abs_delta_wa_vs_baseline"] == 0.0
    assert agg["mean_delta_wa_vs_baseline"] == 0.0

    # The JSON written to disk must equal the in-memory report.
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk == report

    # Markdown is written and contains key headers.
    md_text = md.read_text(encoding="utf-8")
    assert "B6.5.2 — Enhancer Validation on RP5" in md_text
    assert "default_enhancer = `bypass`" in md_text
    assert "metricgan_plus_pretrained".replace("_", "_") in md_text or "MetricGAN" in md_text


def test_each_bypass_row_has_input_equals_output_and_zero_delta(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    baseline = _build_baseline(artifacts_root, candidates_json, examples_json)
    for row in baseline["results"]:
        row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    patch_ctx, _ = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        report = runner.run(
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            baseline_rp5_path=baseline_path,
            enhanced_output_root=tmp_path / "enhanced",
            output_path=tmp_path / "out.json",
            md_path=tmp_path / "out.md",
        )

    for row in report["enhancers"]["bypass"]["rows"]:
        assert row["input_equals_output"] is True
        assert row["preset_applied"] == "bypass"
        assert row["enhanced_flag"] is False
        assert row["enhancement_fallback"] is False
        assert row["audio_input_sha256"] == row["audio_enhanced_sha256"]
        assert len(row["audio_input_sha256"]) == 64
        assert row["delta_wa_vs_baseline"] == 0.0
        assert row["enhance_latency_seconds"] >= 0
        assert row["asr_latency_seconds"] >= 0


def test_metricgan_plus_records_not_implemented(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    baseline = _build_baseline(artifacts_root, candidates_json, examples_json)
    for row in baseline["results"]:
        row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    patch_ctx, _ = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        report = runner.run(
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            baseline_rp5_path=baseline_path,
            enhanced_output_root=tmp_path / "enhanced",
            output_path=tmp_path / "out.json",
            md_path=tmp_path / "out.md",
        )

    mgp = report["enhancers"]["metricgan_plus_pretrained"]
    assert mgp["enhancer_version"] == "metricgan_plus_pretrained"
    assert mgp["status"] == "not_implemented"
    assert mgp["error_class"] == "NotImplementedError"
    assert "T4.1" in mgp["error_message"]


def test_decision_is_bypass_with_t41_blocker(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    baseline = _build_baseline(artifacts_root, candidates_json, examples_json)
    for row in baseline["results"]:
        row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    patch_ctx, _ = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        report = runner.run(
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            baseline_rp5_path=baseline_path,
            enhanced_output_root=tmp_path / "enhanced",
            output_path=tmp_path / "out.json",
            md_path=tmp_path / "out.md",
        )

    decision = report["decision"]
    assert decision["default_enhancer"] == "bypass"
    assert decision["ui_label_for_bypass"] == "honest passthrough"
    assert decision["ui_label_for_metricgan_plus"] == "unavailable"
    assert "T4.1" in decision["blocked_on_upstream_task"]


def test_main_returns_zero_on_success_and_writes_both_files(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    baseline = _build_baseline(artifacts_root, candidates_json, examples_json)
    for row in baseline["results"]:
        row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    out = tmp_path / "out.json"
    md = tmp_path / "out.md"

    patch_ctx, _ = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        rc = runner.main([
            "--examples", str(examples_json),
            "--candidates", str(candidates_json),
            "--artifacts", str(artifacts_root),
            "--baseline-rp5", str(baseline_path),
            "--output", str(out),
            "--md", str(md),
            "--enhanced-output-root", str(tmp_path / "enhanced"),
        ])

    assert rc == 0
    assert out.is_file()
    assert md.is_file()


def test_main_returns_nonzero_when_a_row_breaks_strict_tolerance(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    # Perturb exactly one (example_id, variant_id) baseline value so delta != 0.
    baseline = _build_baseline(
        artifacts_root, candidates_json, examples_json,
        word_accuracy_per_pair={("ex007", "muffled"): 0.5},
    )
    # Other rows: stub transcriber returns ground truth → wa==1.0; baseline==1.0 too.
    for row in baseline["results"]:
        if row["word_accuracy"] is None:
            row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    patch_ctx, _ = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        rc = runner.main([
            "--examples", str(examples_json),
            "--candidates", str(candidates_json),
            "--artifacts", str(artifacts_root),
            "--baseline-rp5", str(baseline_path),
            "--output", str(tmp_path / "out.json"),
            "--md", str(tmp_path / "out.md"),
            "--enhanced-output-root", str(tmp_path / "enhanced"),
        ])

    assert rc == 1
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    bypass = payload["enhancers"]["bypass"]
    assert bypass["status"] == "fail"
    assert any(
        o["example_id"] == "ex007" and o["degradation_id"] == "muffled"
        for o in bypass["offenders"]
    )


def test_baseline_file_is_opened_read_only(
    runner, examples_json, candidates_json, artifacts_root, tmp_path
):
    """Sanity check: the runner must not modify the baseline file in place."""
    baseline = _build_baseline(artifacts_root, candidates_json, examples_json)
    for row in baseline["results"]:
        row["word_accuracy"] = 1.0
    baseline_path = tmp_path / "baseline.json"
    original_text = json.dumps(baseline, sort_keys=True)
    baseline_path.write_text(original_text, encoding="utf-8")

    patch_ctx, _ = _patch_transcriber(runner, examples_json, candidates_json)
    with patch_ctx:
        runner.run(
            examples_path=examples_json,
            candidates_path=candidates_json,
            artifacts_root=artifacts_root,
            baseline_rp5_path=baseline_path,
            enhanced_output_root=tmp_path / "enhanced",
            output_path=tmp_path / "out.json",
            md_path=tmp_path / "out.md",
        )

    # The baseline file must still parse to the same JSON content.
    after = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert after == json.loads(original_text)


def test_resolve_variant_path_clean_and_degraded(runner, tmp_path):
    example = {
        "example_id": "ex001",
        "clean_audio_path": "ex001/clean.wav",
        "degraded_audio_paths": {"phone_call": "ex001/phone_call.wav"},
    }
    assert (
        runner._resolve_variant_path(example, tmp_path, "clean")
        == tmp_path / "ex001/clean.wav"
    )
    assert (
        runner._resolve_variant_path(example, tmp_path, "phone_call")
        == tmp_path / "ex001/phone_call.wav"
    )


def test_baseline_index_handles_missing_rows_gracefully(runner):
    payload = {"results": [
        {"example_id": "ex001", "degradation_id": "clean", "word_accuracy": 0.9},
        {"example_id": None, "degradation_id": "clean", "word_accuracy": 0.8},
        {"example_id": "ex003"},  # missing degradation_id
    ]}
    idx = runner._baseline_index(payload)
    assert ("ex001", "clean") in idx
    assert (None, "clean") not in idx
    assert ("ex003", None) not in idx
