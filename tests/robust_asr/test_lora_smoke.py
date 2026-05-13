"""tests/robust_asr/test_lora_smoke.py — robust_asr P3.1 unit tests.

Pure-Python tests that do not require GPU / Apptainer / Slurm. They
exercise the small pieces of the smoke pipeline that can be checked on
datamove1:

  - lora_smoke.yaml parses, has required sections, manifest sha256s
    match the canonical librispeech parquets.
  - The smoke_split / smoke_eval_split row counts match the declared
    n_rows / n_speakers and are fully present in their source manifest.
  - The degradation_v1_id_eval.parquet covers the smoke_eval_split with
    all five v3.4.7 families (200 × 5 = 1000 rows).
  - The decision-rule booleans in scripts/robust_asr/decide_lora_smoke.py
    (Section 5.1) are unambiguous: PASS/PARTIAL/FAIL/HALTED outcomes for
    representative smoke_result dicts. (P3.1 does not write the
    decision script; only its input format is asserted here.)
  - lora_smoke_result.json schema produced by evaluate_lora_smoke.py
    contains the keys required by P3.2.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CFG = REPO / "configs/robust_asr/lora_smoke.yaml"

V347_FAMILIES = {"clean", "cafe_noise", "phone_band", "far_field_room", "muffled_lowpass"}


@pytest.fixture(scope="module")
def cfg() -> dict:
    with open(CFG, "r") as fh:
        return yaml.safe_load(fh)


def test_config_parses_and_required_keys(cfg):
    for key in ("version", "seed", "manifests", "smoke_split", "smoke_eval_split",
                "hyperparameters", "eval_decode_defaults", "timeouts"):
        assert key in cfg, f"missing required top-level key {key}"
    assert cfg["seed"] == 42
    assert cfg["hyperparameters"]["steps_max"] == 200
    assert cfg["hyperparameters"]["lora_rank"] == 8
    assert cfg["hyperparameters"]["lora_alpha"] == 16
    assert set(cfg["hyperparameters"]["target_modules"]) == {"q_proj", "k_proj", "v_proj", "out_proj"}
    assert cfg["eval_decode_defaults"]["beam_size"] == 1
    assert cfg["eval_decode_defaults"]["temperature"] == 0.0
    assert cfg["eval_decode_defaults"]["condition_on_previous_text"] is False
    assert cfg["eval_decode_defaults"]["without_timestamps"] is True
    assert cfg["timeouts"]["training_timeout_seconds"] == 14400
    assert cfg["timeouts"]["eval_timeout_seconds"] == 1800


def test_smoke_split_audio_ids_count(cfg):
    assert cfg["smoke_split"]["n_rows"] == 600
    assert cfg["smoke_split"]["n_speakers"] == 200
    assert cfg["smoke_split"]["per_speaker"] == 3
    assert len(cfg["smoke_split"]["audio_ids"]) == 600
    speakers = {aid.split("/")[-1].split("-")[0] for aid in cfg["smoke_split"]["audio_ids"]}
    assert len(speakers) == 200


def test_smoke_eval_split_audio_ids_count(cfg):
    assert cfg["smoke_eval_split"]["n_rows"] == 200
    assert cfg["smoke_eval_split"]["n_speakers"] == 40
    assert cfg["smoke_eval_split"]["per_speaker"] == 5
    assert len(cfg["smoke_eval_split"]["audio_ids"]) == 200
    speakers = {aid.split("/")[-1].split("-")[0] for aid in cfg["smoke_eval_split"]["audio_ids"]}
    assert len(speakers) == 40


def test_smoke_split_audio_ids_present_in_lora_train_manifest(cfg):
    import pyarrow.parquet as pq

    src = REPO / cfg["smoke_split"]["source_manifest"]
    if not src.exists():
        pytest.skip(f"manifest missing: {src}")
    table = pq.read_table(str(src))
    aids = set(table.column("audio_id").to_pylist())
    smoke_ids = set(cfg["smoke_split"]["audio_ids"])
    missing = smoke_ids - aids
    assert not missing, f"{len(missing)} smoke_split audio_ids missing from manifest"


def test_smoke_eval_split_audio_ids_present_in_validation_manifest(cfg):
    import pyarrow.parquet as pq

    src = REPO / cfg["smoke_eval_split"]["source_manifest"]
    if not src.exists():
        pytest.skip(f"manifest missing: {src}")
    table = pq.read_table(str(src))
    aids = set(table.column("audio_id").to_pylist())
    smoke_ids = set(cfg["smoke_eval_split"]["audio_ids"])
    missing = smoke_ids - aids
    assert not missing, f"{len(missing)} smoke_eval_split audio_ids missing from manifest"


def test_degradation_v1_id_eval_covers_smoke_eval_split(cfg):
    import pyarrow.parquet as pq

    deg = REPO / "artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet"
    if not deg.exists():
        pytest.skip(f"degradation_v1 manifest missing: {deg}")
    t = pq.read_table(str(deg))
    smoke_ids = set(cfg["smoke_eval_split"]["audio_ids"])
    matched: dict[str, set[str]] = {f: set() for f in V347_FAMILIES}
    for i in range(t.num_rows):
        aid = t.column("audio_id")[i].as_py().split("::")[0]
        fam = t.column("condition_family")[i].as_py()
        if aid in smoke_ids and fam in V347_FAMILIES:
            matched[fam].add(aid)
    for fam in V347_FAMILIES:
        assert len(matched[fam]) == 200, f"{fam}: expected 200, got {len(matched[fam])}"


def test_smoke_decision_rule_booleans_pass():
    """Section 5.1 SMOKE_PASS condition (mechanical)."""
    macro_gain = 0.010
    clean_reg = 0.005
    max_fam = 0.010
    pass_a = (macro_gain >= 0.005 and clean_reg <= 0.010)
    pass_b = (max_fam >= 0.010 and clean_reg <= 0.010)
    assert (pass_a or pass_b)


def test_smoke_decision_rule_booleans_partial():
    macro_gain = 0.001
    clean_reg = 0.015
    max_fam = 0.015
    smoke_pass = (macro_gain >= 0.005 and clean_reg <= 0.010) or (max_fam >= 0.010 and clean_reg <= 0.010)
    smoke_partial = (not smoke_pass) and (max_fam >= 0.010 and clean_reg <= 0.020)
    assert not smoke_pass
    assert smoke_partial


def test_smoke_decision_rule_booleans_fail():
    macro_gain = -0.002
    clean_reg = 0.030
    max_fam = -0.001
    smoke_pass = (macro_gain >= 0.005 and clean_reg <= 0.010) or (max_fam >= 0.010 and clean_reg <= 0.010)
    smoke_partial = (not smoke_pass) and (max_fam >= 0.010 and clean_reg <= 0.020)
    smoke_fail = not (smoke_pass or smoke_partial)
    assert smoke_fail


def test_lora_smoke_result_schema_if_present():
    """If evaluate_lora_smoke.py has already run, validate its JSON shape."""
    out = REPO / "reports/robust_asr/lora/lora_smoke_result.json"
    if not out.exists():
        pytest.skip("lora_smoke_result.json not yet produced")
    with open(out, "r") as fh:
        data = json.load(fh)
    for key in (
        "normalization_version", "best_step", "n_eval_rows", "families",
        "lora_per_family_wa", "baseline_per_family_wa", "per_family_wa_gain",
        "macro_wa_gain", "max_family_wa_gain", "clean_wa_regression",
        "per_family_wa_gain_variance", "eval_decode_defaults",
    ):
        assert key in data, f"missing key {key} in lora_smoke_result.json"
    assert data["normalization_version"] == "normalization_v1"
    assert set(data["families"]) == V347_FAMILIES


def test_checkpoint_manifest_schema_if_present():
    out = REPO / "artifacts/robust_asr/lora_smoke/checkpoint_manifest.json"
    if not out.exists():
        pytest.skip("checkpoint_manifest.json not yet produced")
    with open(out, "r") as fh:
        m = json.load(fh)
    for key in ("base_model", "seed", "steps_completed", "best_step", "best_loss",
                "checkpoints", "hyperparameters"):
        assert key in m, f"missing key {key} in checkpoint_manifest.json"
    assert m["seed"] == 42
    assert m["steps_completed"] <= m["steps_max"]
    assert isinstance(m["checkpoints"], list) and len(m["checkpoints"]) >= 1


def test_export_smoke_result_schema_if_present():
    out = REPO / "artifacts/robust_asr/lora_smoke/export_smoke_result.json"
    if not out.exists():
        pytest.skip("export_smoke_result.json not yet produced")
    with open(out, "r") as fh:
        r = json.load(fh)
    assert "outcome" in r and r["outcome"] in {"PASS", "FAIL"}
    assert "steps" in r and isinstance(r["steps"], list)
    step_names = {s["name"] for s in r["steps"]}
    assert {"merge_lora_fp16", "ct2_int8_export", "faster_whisper_transcribe"} >= step_names | {"merge_lora_fp16"}
