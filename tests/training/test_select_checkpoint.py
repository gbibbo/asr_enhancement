"""Selector unit tests for scripts/training/select_checkpoint.py.

Drives the script through subprocess to exercise the real CLI.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTOR = REPO_ROOT / "scripts" / "training" / "select_checkpoint.py"
CONFIG = REPO_ROOT / "configs" / "training" / "full_training.yaml"

EXPECTED_STEPS = (10000, 12500, 15000, 17500, 20000)
EXPECTED_FAMILIES = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)


def _per_family(value_by_family):
    """Build a per-family dict; accept either scalar (broadcast) or full dict."""
    if isinstance(value_by_family, dict):
        return dict(value_by_family)
    return {fam: float(value_by_family) for fam in EXPECTED_FAMILIES}


def _make_eval_metadata(step, checkpoint_path, *, wa, wer=None, stringify_per_family=True):
    """Build a synthetic eval_metadata.json matching what
    scripts/training/train_enhancer.py emits for `--eval-checkpoint`
    runs. The trainer formats per_family_mean_* values as
    string-encoded floats (e.g. "0.580191") while macro_* are real
    floats. The default `stringify_per_family=True` mirrors that
    real-data shape; tests that need pure-float fixtures can opt out.
    """
    per_fam_wa = _per_family(wa)
    per_fam_wer = _per_family(wer if wer is not None else {fam: 1.0 - per_fam_wa[fam] for fam in EXPECTED_FAMILIES})
    macro_wa = sum(per_fam_wa.values()) / len(EXPECTED_FAMILIES)
    macro_wer = sum(per_fam_wer.values()) / len(EXPECTED_FAMILIES)
    if stringify_per_family:
        per_fam_wa_emit = {fam: f"{v:.6f}" for fam, v in per_fam_wa.items()}
        per_fam_wer_emit = {fam: f"{v:.6f}" for fam, v in per_fam_wer.items()}
    else:
        per_fam_wa_emit = dict(per_fam_wa)
        per_fam_wer_emit = dict(per_fam_wer)
    return {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_step": step,
        "checkpoint_model_architecture": "spectral_unet_small_v1",
        "checkpoint_parameter_count": 403201,
        "checkpoint_dataset_version": "librispeech_devclean_v1_excl10_sha256_dc6674bcf7a8",
        "checkpoint_training_split_version": "devclean_speaker_split_v1",
        "eval_per_family_cap": 533,
        "total_expected_transcriptions": 2665,
        "total_completed_transcriptions": 2665,
        "selected_families": list(EXPECTED_FAMILIES),
        "per_family_counts": {fam: 533 for fam in EXPECTED_FAMILIES},
        "per_family_mean_wer": per_fam_wer_emit,
        "per_family_mean_word_accuracy": per_fam_wa_emit,
        "macro_wer": macro_wer,
        "macro_word_accuracy": macro_wa,
        "whisper_model": "base.en",
        "whisper_version": "20250625",
        "whisper_device": "cuda",
        "enhancer_device": "cuda",
        "gpu_used": True,
        "apptainer_nv_used": True,
        "expected_cuda": True,
        "torch_cuda_is_available": True,
        "enhancement_run": False,
    }


def _make_verify_json(step, *, validation_passed=True, errors=None):
    return {
        "validation_passed": validation_passed,
        "errors": list(errors or []),
        "phase": f"t7_1_post_hoc_whisper_step_{step}",
        "t7_1_step": step,
    }


def _setup_world(tmp_path: Path, *, wa_by_step, latest_bytes=None, step20000_bytes=None,
                 step20000_meta_path_basename="latest.pt"):
    """Build a tmp world with checkpoints, eval_metadata.json files, and verify JSON files.

    Returns (checkpoints_dir, eval_meta_paths_by_step, verify_paths_by_step,
             out_md, out_json).
    """
    ck_dir = tmp_path / "checkpoints"
    ck_dir.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    canonical_paths = {}
    for step in EXPECTED_STEPS:
        ck = ck_dir / f"checkpoint_step_{step:07d}.pt"
        if step == 20000 and step20000_bytes is not None:
            ck.write_bytes(step20000_bytes)
        else:
            ck.write_bytes(f"checkpoint_step_{step:07d}".encode("utf-8") + b"\x00" * 32)
        canonical_paths[step] = ck

    latest = ck_dir / "latest.pt"
    if latest_bytes is not None:
        latest.write_bytes(latest_bytes)
    else:
        # Default: bit-equivalent to step 20000.
        latest.write_bytes(canonical_paths[20000].read_bytes())

    eval_paths = {}
    verify_paths = {}
    for step in EXPECTED_STEPS:
        meta_ck_path = (
            ck_dir / step20000_meta_path_basename if step == 20000 else canonical_paths[step]
        )
        meta = _make_eval_metadata(step, meta_ck_path, wa=wa_by_step[step])
        meta_path = artifacts / f"eval_metadata_step_{step:07d}.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        eval_paths[step] = meta_path

        verify = _make_verify_json(step)
        verify_path = artifacts / f"verify_step_{step:07d}.json"
        verify_path.write_text(json.dumps(verify, indent=2), encoding="utf-8")
        verify_paths[step] = verify_path

    out_md = tmp_path / "checkpoint_selection.md"
    out_json = tmp_path / "checkpoint_selection.json"
    return ck_dir, eval_paths, verify_paths, out_md, out_json


def _run_selector(ck_dir, eval_paths, verify_paths, out_md, out_json, **extra):
    cmd = [sys.executable, str(SELECTOR), "--checkpoints-dir", str(ck_dir),
           "--config", str(CONFIG), "--out-md", str(out_md), "--out-json", str(out_json)]
    for step, p in eval_paths.items():
        cmd += ["--eval-metadata", f"{step}={p}"]
    for step, p in verify_paths.items():
        cmd += ["--verify-json", f"{step}={p}"]
    for k, v in extra.items():
        cmd += [f"--{k.replace('_', '-')}", str(v)]
    return subprocess.run(cmd, capture_output=True, text=True)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Sanity / discovery
# ---------------------------------------------------------------------------

def test_selector_script_exists():
    assert SELECTOR.is_file(), SELECTOR


def test_config_exists():
    assert CONFIG.is_file(), CONFIG


# ---------------------------------------------------------------------------
# Selection rule
# ---------------------------------------------------------------------------

def test_primary_metric_picks_highest_macro_wa(tmp_path):
    wa = {10000: 0.50, 12500: 0.55, 15000: 0.70, 17500: 0.60, 20000: 0.65}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)
    assert out["selected_checkpoint"]["step"] == 15000
    # Trace must be sorted descending by macro WA.
    trace_steps = [t["step"] for t in out["selection_rule_application_trace"]]
    assert trace_steps == [15000, 20000, 17500, 12500, 10000]


def test_tiebreaker1_worst_case_wa(tmp_path):
    # Equal macro WA across two leaders, but different worst-case.
    wa_step_a = {fam: 0.6 for fam in EXPECTED_FAMILIES}
    wa_step_b = dict(wa_step_a)
    wa_step_b["muffled"] = 0.4
    wa_step_b["phone_call"] = 0.8  # keeps macro at 0.6
    wa = {
        10000: 0.5,
        12500: wa_step_a,    # macro 0.6, worst 0.6  → wins tiebreaker 1
        15000: wa_step_b,    # macro 0.6, worst 0.4
        17500: 0.45,
        20000: 0.4,
    }
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)
    assert out["selected_checkpoint"]["step"] == 12500


def test_tiebreaker2_higher_step(tmp_path):
    # Equal macro AND equal worst-case → highest step wins.
    flat = {fam: 0.5 for fam in EXPECTED_FAMILIES}
    wa = {step: dict(flat) for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)
    assert out["selected_checkpoint"]["step"] == 20000


def test_all_null_or_negative_emits_pending_review(tmp_path):
    # Every macro WA below T3.2 baseline (0.8213).
    wa = {10000: 0.30, 12500: 0.40, 15000: 0.50, 17500: 0.55, 20000: 0.52}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)
    sel = out["selected_checkpoint"]
    assert sel["step"] == 17500
    assert sel["tier_at_selection"] == "null_or_negative"
    assert sel["deployment_decision"] == "not_selected_pending_review"
    assert out["t7_2_required"] is True
    assert out["do_not_modify_model_card"] is True


# ---------------------------------------------------------------------------
# latest.pt alias handling
# ---------------------------------------------------------------------------

def test_latest_alias_sha_match_uses_canonical_step_20000(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    wa[20000] = 0.9  # make step 20000 the winner
    # Both step20000 and latest get the same bytes by default.
    ck_dir, em, vj, md, js = _setup_world(
        tmp_path,
        wa_by_step=wa,
        step20000_meta_path_basename="latest.pt",  # T6.3b convention
    )
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)
    sel = out["selected_checkpoint"]
    assert sel["step"] == 20000
    assert sel["canonical_path"].endswith("checkpoint_step_0020000.pt")
    assert sel["alias_paths"], sel["alias_paths"]
    assert sel["alias_paths"][0].endswith("latest.pt")
    la = out["latest_pt_alias"]
    assert la["alias_accepted"] is True
    assert la["latest_pt_sha256"] == la["checkpoint_step_0020000_sha256"]


def test_latest_alias_sha_mismatch_fails_no_output(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(
        tmp_path,
        wa_by_step=wa,
        step20000_bytes=b"step20000-canonical-bytes" + b"\x00" * 32,
        latest_bytes=b"DIFFERENT-BYTES-FOR-LATEST" + b"\x00" * 32,
    )
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "latest.pt" in r.stderr
    assert "checkpoint_step_0020000" in r.stderr
    assert not md.exists(), "out-md must NOT be written on SHA mismatch"
    assert not js.exists(), "out-json must NOT be written on SHA mismatch"


# ---------------------------------------------------------------------------
# Negative inputs
# ---------------------------------------------------------------------------

def test_missing_per_family_metric_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    # Corrupt step 10000: drop one family from per_family_mean_word_accuracy.
    meta = json.loads(em[10000].read_text(encoding="utf-8"))
    del meta["per_family_mean_word_accuracy"]["muffled"]
    em[10000].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "muffled" in r.stderr
    assert not md.exists() and not js.exists()


def test_non_finite_value_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    # Inject NaN via allow_nan=True; json.dumps default with allow_nan
    # writes 'NaN' which Python json.loads accepts.
    meta = json.loads(em[12500].read_text(encoding="utf-8"))
    meta["per_family_mean_word_accuracy"]["broadband_hiss"] = float("nan")
    em[12500].write_text(json.dumps(meta, indent=2, allow_nan=True), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "non-finite" in r.stderr
    assert not md.exists() and not js.exists()


def test_duplicate_step_key_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    cmd = [sys.executable, str(SELECTOR),
           "--checkpoints-dir", str(ck_dir),
           "--config", str(CONFIG),
           "--out-md", str(md), "--out-json", str(js)]
    for step, p in em.items():
        cmd += ["--eval-metadata", f"{step}={p}"]
    cmd += ["--eval-metadata", f"10000={em[10000]}"]  # duplicate
    for step, p in vj.items():
        cmd += ["--verify-json", f"{step}={p}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "duplicate STEP" in r.stderr
    assert not md.exists() and not js.exists()


def test_missing_step_key_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    em.pop(15000)  # omit one expected key
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "missing STEP keys" in r.stderr
    assert "15000" in r.stderr
    assert not md.exists() and not js.exists()


def test_validation_passed_false_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    bad = _make_verify_json(17500, validation_passed=False, errors=["fake"])
    vj[17500].write_text(json.dumps(bad, indent=2), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "validation_passed" in r.stderr
    assert not md.exists() and not js.exists()


# ---------------------------------------------------------------------------
# Real-data scalar encoding: train_enhancer.py emits per_family_mean_*
# as string-formatted floats (e.g. "0.580191"). The selector must accept
# these and emit numeric floats in checkpoint_selection.json.
# ---------------------------------------------------------------------------

def test_string_encoded_per_family_metrics_accepted_emit_floats(tmp_path):
    # Default fixtures already stringify per-family values (matching real
    # eval_metadata.json shape from scripts/training/train_enhancer.py).
    wa = {10000: 0.50, 12500: 0.55, 15000: 0.70, 17500: 0.60, 20000: 0.65}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)

    # Sanity: confirm fixtures actually wrote strings.
    sample = json.loads(em[10000].read_text(encoding="utf-8"))
    assert all(isinstance(v, str) for v in sample["per_family_mean_word_accuracy"].values()), \
        "fixture should encode per-family WA as strings to mirror real data"
    assert all(isinstance(v, str) for v in sample["per_family_mean_wer"].values()), \
        "fixture should encode per-family WER as strings to mirror real data"

    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)

    # Winner picked by primary metric → step 15000 here.
    assert out["selected_checkpoint"]["step"] == 15000

    # Output JSON must carry floats, not stringified scalars.
    for cand in out["candidates"]:
        for fam, v in cand["per_family_mean_word_accuracy"].items():
            assert isinstance(v, float), (cand["step"], fam, type(v).__name__)
        for fam, v in cand["per_family_mean_wer"].items():
            assert isinstance(v, float), (cand["step"], fam, type(v).__name__)
        assert isinstance(cand["macro_word_accuracy"], float)
        assert isinstance(cand["macro_wer"], float)
        assert isinstance(cand["worst_case_word_accuracy"], float)
    sel = out["selected_checkpoint"]
    for k in ("macro_word_accuracy", "macro_wer", "worst_case_word_accuracy",
              "delta_macro_wa_vs_t3_2_degraded"):
        assert isinstance(sel[k], float), (k, type(sel[k]).__name__)


def test_float_encoded_per_family_metrics_still_accepted(tmp_path):
    # Regression: pure-float fixtures (the prep-commit shape) must keep working.
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    wa[15000] = 0.7  # break the tie so we have a clear winner
    ck_dir = tmp_path / "checkpoints"
    ck_dir.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    canonical = {}
    for step in EXPECTED_STEPS:
        ck = ck_dir / f"checkpoint_step_{step:07d}.pt"
        ck.write_bytes(f"checkpoint_step_{step:07d}".encode("utf-8") + b"\x00" * 32)
        canonical[step] = ck
    (ck_dir / "latest.pt").write_bytes(canonical[20000].read_bytes())
    em, vj = {}, {}
    for step in EXPECTED_STEPS:
        meta = _make_eval_metadata(step, canonical[step], wa=wa[step], stringify_per_family=False)
        # Sanity: confirm fixture is float-encoded.
        for v in meta["per_family_mean_word_accuracy"].values():
            assert isinstance(v, float)
        em[step] = artifacts / f"eval_metadata_step_{step:07d}.json"
        em[step].write_text(json.dumps(meta, indent=2), encoding="utf-8")
        vj[step] = artifacts / f"verify_step_{step:07d}.json"
        vj[step].write_text(json.dumps(_make_verify_json(step), indent=2), encoding="utf-8")
    md = tmp_path / "checkpoint_selection.md"
    js = tmp_path / "checkpoint_selection.json"
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode == 0, r.stderr
    out = _read_json(js)
    assert out["selected_checkpoint"]["step"] == 15000


def test_non_numeric_string_per_family_value_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    meta = json.loads(em[10000].read_text(encoding="utf-8"))
    meta["per_family_mean_word_accuracy"]["muffled"] = "not_a_number"
    em[10000].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "not numeric" in r.stderr
    assert "muffled" in r.stderr
    assert not md.exists() and not js.exists()


@pytest.mark.parametrize("bad", ["nan", "NaN", "NAN", "inf", "Inf", "-inf", "-Inf", "+inf"])
def test_nan_inf_string_per_family_values_fail(tmp_path, bad):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    meta = json.loads(em[15000].read_text(encoding="utf-8"))
    meta["per_family_mean_word_accuracy"]["broadband_hiss"] = bad
    em[15000].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "non-finite" in r.stderr
    assert "broadband_hiss" in r.stderr
    assert not md.exists() and not js.exists()


def test_non_scalar_per_family_value_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    meta = json.loads(em[12500].read_text(encoding="utf-8"))
    meta["per_family_mean_word_accuracy"]["phone_call"] = [0.5]  # list, not scalar
    em[12500].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "not numeric" in r.stderr
    assert "phone_call" in r.stderr
    assert not md.exists() and not js.exists()


def test_null_per_family_value_fails(tmp_path):
    wa = {step: 0.5 for step in EXPECTED_STEPS}
    ck_dir, em, vj, md, js = _setup_world(tmp_path, wa_by_step=wa)
    meta = json.loads(em[17500].read_text(encoding="utf-8"))
    meta["per_family_mean_word_accuracy"]["far_field_room"] = None
    em[17500].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    r = _run_selector(ck_dir, em, vj, md, js)
    assert r.returncode != 0
    assert "not numeric" in r.stderr
    assert "far_field_room" in r.stderr
    assert not md.exists() and not js.exists()
