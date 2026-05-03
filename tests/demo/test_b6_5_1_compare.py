"""Unit tests for scripts/demo/compare_rp5_surrey.py (B6.5.1)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "demo" / "compare_rp5_surrey.py"


@pytest.fixture
def comparator():
    spec = importlib.util.spec_from_file_location(
        "compare_rp5_surrey_under_test", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DEGRADATION_IDS = (
    "far_field_room", "cafe_background", "phone_call", "muffled", "broadband_hiss",
)
EXAMPLE_IDS = ("ex001", "ex003", "ex004", "ex007", "ex010")


def _make_report(
    *,
    engine: str,
    wa_by_pair: dict[tuple[str, str], float],
    sha_by_pair: dict[tuple[str, str], str] | None = None,
    degradation_version: str = "degradation_v1",
    metrics_version: str = "1.0",
) -> dict:
    sha_by_pair = sha_by_pair or {}
    results = []
    for ex_id in EXAMPLE_IDS:
        for variant in ("clean",) + DEGRADATION_IDS:
            key = (ex_id, variant)
            wa = wa_by_pair.get(key, 1.0)
            sha = sha_by_pair.get(key, f"sha-{ex_id}-{variant}")
            results.append({
                "example_id": ex_id,
                "source_recording_id": f"src-{ex_id}",
                "degradation_id": variant,
                "audio_path_relative": f"{ex_id}/{variant}.wav",
                "audio_sha256": sha,
                "hypothesis": f"hyp-{ex_id}-{variant}",
                "wer": round(1.0 - wa, 6),
                "word_accuracy": round(wa, 6),
                "latency_seconds": 0.5,
            })
    return {
        "engine": engine,
        "model": "tiny.en",
        "host": f"host-{engine}",
        "generated_at": "2026-05-02T00:00:00+00:00",
        "examples_config": "config/demo_examples.json",
        "candidates_config": "config/demo_example_candidates.json",
        "artifacts_root": "/tmp/artifacts",
        "degradation_version": degradation_version,
        "metrics_version": metrics_version,
        "default_enhancer_version": "1.0",
        "degradation_parameters_signature": "abc",
        "scope": list(EXAMPLE_IDS),
        "variant_ids": ["clean", *DEGRADATION_IDS],
        "results": results,
    }


def test_mismatched_degradation_version_raises(comparator):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={}, degradation_version="degradation_v1")
    sur = _make_report(engine="openai-whisper", wa_by_pair={}, degradation_version="other")
    with pytest.raises(comparator.CompareError, match="degradation_version mismatch"):
        comparator.compare(rp5, sur)


def test_mismatched_metrics_version_raises(comparator):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={}, metrics_version="1.0")
    sur = _make_report(engine="openai-whisper", wa_by_pair={}, metrics_version="2.0")
    with pytest.raises(comparator.CompareError, match="metrics_version mismatch"):
        comparator.compare(rp5, sur)


def test_mismatched_pair_set_raises(comparator):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={})
    sur = _make_report(engine="openai-whisper", wa_by_pair={})
    sur["results"] = sur["results"][:-1]  # drop one row
    with pytest.raises(comparator.CompareError, match="row sets differ"):
        comparator.compare(rp5, sur)


def test_audio_sha_mismatch_raises(comparator):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={})
    sur = _make_report(engine="openai-whisper", wa_by_pair={})
    sur["results"][0]["audio_sha256"] = "deadbeef"
    with pytest.raises(comparator.CompareError, match="audio_sha256 mismatch"):
        comparator.compare(rp5, sur)


def test_verdict_comparable(comparator):
    # Identical word accuracies → degraded_mean_delta_wa == 0.0 → comparable
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={})
    sur = _make_report(engine="openai-whisper", wa_by_pair={})
    out = comparator.compare(rp5, sur)
    assert out["verdict"] == "comparable"
    assert out["primary"]["degraded_mean_delta_wa"] == 0.0
    assert out["row_counts"] == {"all": 30, "degraded": 25, "clean": 5}
    assert out["requires_model_card_update"] is False


def test_verdict_caution(comparator):
    # RP5 is consistently 0.03 better on every degraded row → mean_delta = 0.03
    wa_rp5 = {(ex, deg): 1.0 for ex in EXAMPLE_IDS for deg in DEGRADATION_IDS}
    wa_sur = {(ex, deg): 0.97 for ex in EXAMPLE_IDS for deg in DEGRADATION_IDS}
    rp5 = _make_report(engine="faster-whisper", wa_by_pair=wa_rp5)
    sur = _make_report(engine="openai-whisper", wa_by_pair=wa_sur)
    out = comparator.compare(rp5, sur)
    assert out["verdict"] == "caution"
    assert abs(out["primary"]["degraded_mean_delta_wa"] - 0.03) < 1e-9
    assert out["requires_model_card_update"] is False


def test_verdict_discrepant(comparator):
    # RP5 is consistently 0.10 better on every degraded row → mean_delta = 0.10
    wa_rp5 = {(ex, deg): 1.0 for ex in EXAMPLE_IDS for deg in DEGRADATION_IDS}
    wa_sur = {(ex, deg): 0.90 for ex in EXAMPLE_IDS for deg in DEGRADATION_IDS}
    rp5 = _make_report(engine="faster-whisper", wa_by_pair=wa_rp5)
    sur = _make_report(engine="openai-whisper", wa_by_pair=wa_sur)
    out = comparator.compare(rp5, sur)
    assert out["verdict"] == "discrepant"
    assert out["requires_model_card_update"] is True


def test_clean_disagreement_emits_aux_warning(comparator):
    # Comparable verdict on degraded rows, but clean rows disagree → aux warning
    wa_rp5 = {(ex, "clean"): 1.0 for ex in EXAMPLE_IDS}
    wa_sur = {(ex, "clean"): 0.80 for ex in EXAMPLE_IDS}
    rp5 = _make_report(engine="faster-whisper", wa_by_pair=wa_rp5)
    sur = _make_report(engine="openai-whisper", wa_by_pair=wa_sur)
    out = comparator.compare(rp5, sur)
    assert out["verdict"] == "comparable"
    assert any("clean_max_abs_delta_wa" in w for w in out["aux_warnings"])


def test_thresholds_constants(comparator):
    assert comparator.COMPARABLE_THRESHOLD == 0.02
    assert comparator.DISCREPANT_THRESHOLD == 0.05


def test_render_markdown_includes_verdict_and_pair_table(comparator):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={})
    sur = _make_report(engine="openai-whisper", wa_by_pair={})
    out = comparator.compare(rp5, sur)
    md = comparator.render_markdown(out)
    assert "RP5 vs Surrey" in md
    assert "Verdict: **comparable**" in md
    assert "ex001" in md
    assert "phone_call" in md
    assert "Per-pair detail" in md


def test_main_writes_files_and_returns_zero(comparator, tmp_path):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={})
    sur = _make_report(engine="openai-whisper", wa_by_pair={})
    rp5_path = tmp_path / "rp5.json"
    sur_path = tmp_path / "surrey.json"
    rp5_path.write_text(json.dumps(rp5), encoding="utf-8")
    sur_path.write_text(json.dumps(sur), encoding="utf-8")
    out_json = tmp_path / "comparison.json"
    out_md = tmp_path / "comparison.md"
    rc = comparator.main([
        "--rp5", str(rp5_path),
        "--surrey", str(sur_path),
        "--output", str(out_json),
        "--md", str(out_md),
    ])
    assert rc == 0
    assert out_json.is_file()
    assert out_md.is_file()
    parsed = json.loads(out_json.read_text(encoding="utf-8"))
    assert parsed["verdict"] == "comparable"


def test_main_returns_nonzero_on_compare_error(comparator, tmp_path):
    rp5 = _make_report(engine="faster-whisper", wa_by_pair={}, degradation_version="degradation_v1")
    sur = _make_report(engine="openai-whisper", wa_by_pair={}, degradation_version="other")
    rp5_path = tmp_path / "rp5.json"
    sur_path = tmp_path / "surrey.json"
    rp5_path.write_text(json.dumps(rp5), encoding="utf-8")
    sur_path.write_text(json.dumps(sur), encoding="utf-8")
    rc = comparator.main([
        "--rp5", str(rp5_path),
        "--surrey", str(sur_path),
        "--output", str(tmp_path / "comparison.json"),
        "--md", str(tmp_path / "comparison.md"),
    ])
    assert rc == 2
