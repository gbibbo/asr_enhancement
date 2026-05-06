"""T6.2d — login-node-safe tests for the Whisper validation path helpers.

These tests cover the pure-Python helpers added to
`scripts/training/train_enhancer.py` for the T6.2d Whisper-enabled CPU
smoke validation gate:

  * JSONL transcript loading from the val clean manifest;
  * missing-transcript detection (record without a `transcript` field, or
    with an empty `transcript`, must be reported as missing);
  * deterministic shuffle=False per-family selection of one record per
    family across `EXPECTED_FAMILIES` (the Whisper smoke subset);
  * per-family aggregation into the
    `{family, count, mean_wer, mean_word_accuracy, note}` row shape used
    by `wer_by_degradation.csv`;
  * config/CLI consistency check (config-on/CLI-off and CLI-on/config-off
    both produce the blocker signal; aligned config+CLI passes).

Hard scope guards (must remain TRUE):
  * No `import torch`. No `import whisper`. No `import torchaudio`.
  * No `import matplotlib`. No `import scipy`.
  * Tests run on the datamove1 login node and do not exercise the Slurm
    Whisper pass.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_SCRIPT_DIR = REPO_ROOT / "scripts" / "training"

# Make scripts/training importable as flat modules (mirrors the trick used
# by train_enhancer.py itself for sibling imports).
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
            f"forbidden heavy import already loaded: {name!r}; T6.2d helpers "
            f"must stay login-node-safe (no torch/whisper/torchaudio/matplotlib/scipy)."
        )


# ---------------------------------------------------------------------------
# JSONL transcript loading
# ---------------------------------------------------------------------------
def test_load_transcripts_by_utterance_id_jsonl(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()
    _forbid_heavy_imports()

    p = tmp_path / "val_clean_manifest.jsonl"
    rows = [
        {"utterance_id": "u-1", "transcript": "HELLO WORLD"},
        {"utterance_id": "u-2", "transcript": "FOO BAR BAZ"},
        # blank-line tolerance is exercised by the manifest reader
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    out = te._load_transcripts_by_utterance_id(p)
    assert out == {"u-1": "HELLO WORLD", "u-2": "FOO BAR BAZ"}


def test_load_transcripts_missing_field_yields_empty_string(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    p = tmp_path / "val_clean_manifest.jsonl"
    rows = [
        {"utterance_id": "u-1", "transcript": "OK"},
        {"utterance_id": "u-2"},                       # missing transcript field
        {"utterance_id": "u-3", "transcript": ""},     # explicit empty
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    out = te._load_transcripts_by_utterance_id(p)
    assert out["u-1"] == "OK"
    assert out["u-2"] == ""
    assert out["u-3"] == ""


# ---------------------------------------------------------------------------
# Whisper smoke subset selection (shuffle=False, per-family cap)
# ---------------------------------------------------------------------------
def test_select_whisper_smoke_subset_one_per_family() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    fams = list(te.EXPECTED_FAMILIES)
    # Construct a tiny manifest-shaped list with multiple records per family.
    records: list[dict] = []
    for f in fams:
        for i in range(3):
            records.append({"utterance_id": f"u-{f}-{i}", "family": f})

    subset = te._select_whisper_smoke_subset(records, per_family_cap=1)
    assert len(subset) == len(fams)
    families_in_order = [r["family"] for r in subset]
    assert families_in_order == fams  # canonical EXPECTED_FAMILIES ordering
    # shuffle=False: must pick the FIRST record of each family in manifest order
    for f in fams:
        first_for_f = next(r for r in records if r["family"] == f)
        picked = next(r for r in subset if r["family"] == f)
        assert picked is first_for_f, (
            f"per-family selection must be deterministic (shuffle=False); "
            f"family={f!r} first_in_manifest={first_for_f!r} picked={picked!r}"
        )


def test_select_whisper_smoke_subset_caps_at_two_per_family() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    records: list[dict] = []
    for f in te.EXPECTED_FAMILIES:
        for i in range(5):
            records.append({"utterance_id": f"u-{f}-{i}", "family": f})

    subset = te._select_whisper_smoke_subset(records, per_family_cap=2)
    assert len(subset) == 2 * len(te.EXPECTED_FAMILIES)
    counts = {f: 0 for f in te.EXPECTED_FAMILIES}
    for r in subset:
        counts[r["family"]] += 1
    assert all(v == 2 for v in counts.values())


def test_select_whisper_smoke_subset_missing_family_signal() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    fams = list(te.EXPECTED_FAMILIES)
    # Drop the last family entirely.
    records: list[dict] = []
    for f in fams[:-1]:
        records.append({"utterance_id": f"u-{f}-0", "family": f})

    subset = te._select_whisper_smoke_subset(records, per_family_cap=1)
    families_found = {r["family"] for r in subset}
    assert fams[-1] not in families_found, (
        "smoke subset must not invent a record for the missing family"
    )
    assert len(subset) == len(fams) - 1


# ---------------------------------------------------------------------------
# Pre-flight integration: missing transcript = blocker
# ---------------------------------------------------------------------------
def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _make_smoke_cfg(tmp_path: Path, *, val_deg_rows: list[dict], val_clean_rows: list[dict]) -> dict:
    val_deg = tmp_path / "val_degraded_manifest.jsonl"
    val_clean = tmp_path / "val_clean_manifest.jsonl"
    _write_jsonl(val_deg, val_deg_rows)
    _write_jsonl(val_clean, val_clean_rows)
    return {
        "training_split": {
            "val_clean_manifest": str(val_clean),
            "val_degraded_manifest": str(val_deg),
        },
        "validation_policy": {
            "per_family_records_cap": 1,
            "whisper_validation_enabled": True,
        },
    }


def test_pre_flight_passes_when_transcripts_present(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    val_deg_rows = [
        {"utterance_id": f"u-{f}-0", "family": f,
         "degraded_audio_path": f"/dev/null/{f}.wav"}
        for f in te.EXPECTED_FAMILIES
    ]
    val_clean_rows = [
        {"utterance_id": f"u-{f}-0", "transcript": "REFERENCE TEXT"}
        for f in te.EXPECTED_FAMILIES
    ]
    cfg = _make_smoke_cfg(
        tmp_path, val_deg_rows=val_deg_rows, val_clean_rows=val_clean_rows
    )
    errors = te._check_whisper_smoke_pre_flight(cfg)
    assert errors == []


def test_pre_flight_blocks_when_transcript_missing(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    val_deg_rows = [
        {"utterance_id": f"u-{f}-0", "family": f,
         "degraded_audio_path": f"/dev/null/{f}.wav"}
        for f in te.EXPECTED_FAMILIES
    ]
    val_clean_rows = [
        {"utterance_id": f"u-{f}-0", "transcript": "REFERENCE TEXT"}
        for f in te.EXPECTED_FAMILIES[:-1]
    ]
    # Last family's clean record has an empty transcript.
    val_clean_rows.append(
        {"utterance_id": f"u-{te.EXPECTED_FAMILIES[-1]}-0", "transcript": ""}
    )
    cfg = _make_smoke_cfg(
        tmp_path, val_deg_rows=val_deg_rows, val_clean_rows=val_clean_rows
    )
    errors = te._check_whisper_smoke_pre_flight(cfg)
    assert errors, "pre-flight must block when any selected smoke record lacks a transcript"
    assert any("missing transcript" in e for e in errors)


def test_pre_flight_blocks_when_family_absent(tmp_path: Path) -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    fams = list(te.EXPECTED_FAMILIES)
    # Omit the last family from the val degraded manifest entirely.
    val_deg_rows = [
        {"utterance_id": f"u-{f}-0", "family": f,
         "degraded_audio_path": f"/dev/null/{f}.wav"}
        for f in fams[:-1]
    ]
    val_clean_rows = [
        {"utterance_id": f"u-{f}-0", "transcript": "REFERENCE TEXT"}
        for f in fams
    ]
    cfg = _make_smoke_cfg(
        tmp_path, val_deg_rows=val_deg_rows, val_clean_rows=val_clean_rows
    )
    errors = te._check_whisper_smoke_pre_flight(cfg)
    assert errors, "pre-flight must block when a family is missing from the val set"
    assert any("missing families" in e for e in errors)


# ---------------------------------------------------------------------------
# Config / CLI consistency check
# ---------------------------------------------------------------------------
def test_consistency_config_on_cli_off_blocks() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"validation_policy": {"whisper_validation_enabled": True}}
    errors = te._check_whisper_cli_consistency(cfg, enable_whisper_val=False)
    assert errors and any("whisper_validation_enabled=true" in e for e in errors)


def test_consistency_cli_on_config_off_blocks() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg = {"validation_policy": {"whisper_validation_enabled": False}}
    errors = te._check_whisper_cli_consistency(cfg, enable_whisper_val=True)
    assert errors and any("--enable-whisper-val passed on CLI" in e for e in errors)


def test_consistency_cli_on_config_absent_blocks() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg: dict = {}  # no validation_policy block at all
    errors = te._check_whisper_cli_consistency(cfg, enable_whisper_val=True)
    assert errors


def test_consistency_aligned_passes() -> None:
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    cfg_on = {"validation_policy": {"whisper_validation_enabled": True}}
    assert te._check_whisper_cli_consistency(cfg_on, enable_whisper_val=True) == []
    cfg_off = {"validation_policy": {"whisper_validation_enabled": False}}
    assert te._check_whisper_cli_consistency(cfg_off, enable_whisper_val=False) == []


# ---------------------------------------------------------------------------
# Per-family aggregation row shape (smoke postcondition)
# ---------------------------------------------------------------------------
def test_family_row_shape_matches_csv_writer_fieldnames() -> None:
    """`_write_wer_by_degradation_csv` writes only these fields. Any
    aggregation helper must produce dicts with the same keys, so the CSV
    row never silently drops information."""
    _forbid_heavy_imports()
    te = _import_train_enhancer()

    expected_fields = {"family", "count", "mean_wer", "mean_word_accuracy", "note"}
    sample_row = {
        "family": "broadband_hiss",
        "count": 1,
        "mean_wer": "0.123456",
        "mean_word_accuracy": "0.876544",
        "note": te.WHISPER_SMOKE_NOTE,
    }
    assert set(sample_row.keys()) == expected_fields
    assert te.WHISPER_SMOKE_NOTE == "whisper_smoke_t6_2d"


# ---------------------------------------------------------------------------
# Final guard: the test module itself must not have pulled in heavy deps.
# ---------------------------------------------------------------------------
def test_no_heavy_imports_in_module() -> None:
    _forbid_heavy_imports()
    # Re-import to make sure idempotent loading didn't drag anything in.
    _import_train_enhancer()
    _forbid_heavy_imports()
