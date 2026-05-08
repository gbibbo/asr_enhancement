"""P1.2 — Tests for the canonical eval schema (Section 3, rules 1-7).

Test 1: All required columns exist (set equality with Section 3).
Test 2: Rows are unique on (audio_id, backend_name, decode_config_hash).
Test 3: audio_id stable across backends (audio_path_or_uri + audio_sha256
        agree across backends for the same audio_id).
Test 4: reference_normalized identical across backends per audio_id.
Test 5: normalization_version recorded on every row.
Test 6: error_or_null non-null whenever any latency field is null.
Test 7: cost_usd is numeric or null; null only when local_only == true.

Synthetic in-memory rows are used; populated parquet validation is the
job of validate_eval_table.py at later phases.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "libs" / "common" / "eval_schema.yaml"

# Canonical Section 3 columns (mirrored from validate_eval_schema.py).
SECTION_3_COLUMNS = [
    "audio_id", "source_dataset", "source_split", "speaker_id",
    "utterance_id", "condition_family", "degradation_id",
    "degradation_params_json", "audio_path_or_uri", "audio_sha256",
    "reference_text", "reference_normalized", "backend_name",
    "backend_version", "backend_kind", "decode_config_json",
    "raw_transcript", "normalized_transcript", "normalization_version",
    "wer", "cer", "wa", "backend_latency_ms",
    "server_processing_latency_ms", "end_to_end_latency_ms",
    "ram_peak_mb", "cost_usd", "local_only", "third_party_provider",
    "error_or_null", "created_at_utc",
]


@pytest.fixture(scope="module")
def schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def schema_columns(schema: Dict[str, Any]) -> List[str]:
    return [c["name"] for c in schema["columns"]]


def _decode_config_hash(decode_config_json: str) -> str:
    return hashlib.sha256(decode_config_json.encode("utf-8")).hexdigest()


def _row(**overrides: Any) -> Dict[str, Any]:
    decode_cfg = overrides.pop(
        "decode_config_json",
        json.dumps({"task": "transcribe", "language": "en", "condition_on_previous_text": False}),
    )
    base: Dict[str, Any] = {
        "audio_id": "ls_test_clean_61_70968_0001",
        "source_dataset": "librispeech",
        "source_split": "test-clean",
        "speaker_id": "61",
        "utterance_id": "70968_0001",
        "condition_family": "clean",
        "degradation_id": "clean",
        "degradation_params_json": json.dumps({}),
        "audio_path_or_uri": "/data/61/70968/61-70968-0001.flac",
        "audio_sha256": "a" * 64,
        "reference_text": "hello world",
        "reference_normalized": "hello world",
        "backend_name": "whisper_base_ct2_int8",
        "backend_version": "whisper_base_ct2_int8_v1",
        "backend_kind": "local_asr",
        "decode_config_json": decode_cfg,
        "raw_transcript": "hello world",
        "normalized_transcript": "hello world",
        "normalization_version": "normalization_v1",
        "wer": 0.0,
        "cer": 0.0,
        "wa": 1.0,
        "backend_latency_ms": 120.0,
        "server_processing_latency_ms": 5.0,
        "end_to_end_latency_ms": 130.0,
        "ram_peak_mb": 320.0,
        "cost_usd": None,
        "local_only": True,
        "third_party_provider": None,
        "error_or_null": None,
        "created_at_utc": "2026-05-08T12:00:00Z",
    }
    base.update(overrides)
    return base


# --- Test 1 ---------------------------------------------------------------


def test_1_required_columns_exist(schema_columns: List[str]) -> None:
    assert set(schema_columns) == set(SECTION_3_COLUMNS), (
        f"missing={sorted(set(SECTION_3_COLUMNS) - set(schema_columns))} "
        f"extra={sorted(set(schema_columns) - set(SECTION_3_COLUMNS))}"
    )
    assert len(schema_columns) == len(set(schema_columns)), "duplicate column names"


# --- Test 2 ---------------------------------------------------------------


def _check_unique_pk(rows: List[Dict[str, Any]]) -> None:
    seen = set()
    for r in rows:
        pk = (r["audio_id"], r["backend_name"], _decode_config_hash(r["decode_config_json"]))
        assert pk not in seen, f"duplicate pk: {pk}"
        seen.add(pk)


def test_2_unique_pk_passes_for_distinct_rows() -> None:
    rows = [
        _row(),
        _row(backend_name="whisper_lora_ct2_int8", backend_version="lora_v1"),
        _row(backend_name="assemblyai", backend_kind="cloud_asr",
             local_only=False, third_party_provider="assemblyai", cost_usd=0.0026),
    ]
    _check_unique_pk(rows)


def test_2_unique_pk_fails_for_duplicate_pk() -> None:
    rows = [_row(), _row()]
    with pytest.raises(AssertionError):
        _check_unique_pk(rows)


# --- Test 3 ---------------------------------------------------------------


def _check_audio_id_stable(rows: List[Dict[str, Any]]) -> None:
    by_id: Dict[str, Dict[str, str]] = {}
    for r in rows:
        rec = by_id.setdefault(r["audio_id"], {
            "audio_path_or_uri": r["audio_path_or_uri"],
            "audio_sha256": r["audio_sha256"],
        })
        assert rec["audio_path_or_uri"] == r["audio_path_or_uri"]
        assert rec["audio_sha256"] == r["audio_sha256"]


def test_3_audio_id_stable_across_backends() -> None:
    rows = [
        _row(),
        _row(backend_name="whisper_lora_ct2_int8", raw_transcript="hello world"),
        _row(backend_name="assemblyai", local_only=False,
             third_party_provider="assemblyai", cost_usd=0.0026),
    ]
    _check_audio_id_stable(rows)


def test_3_audio_id_unstable_audio_sha256_fails() -> None:
    rows = [
        _row(),
        _row(backend_name="whisper_lora_ct2_int8", audio_sha256="b" * 64),
    ]
    with pytest.raises(AssertionError):
        _check_audio_id_stable(rows)


# --- Test 4 ---------------------------------------------------------------


def _check_reference_normalized_identical(rows: List[Dict[str, Any]]) -> None:
    by_id: Dict[str, str] = {}
    for r in rows:
        prev = by_id.setdefault(r["audio_id"], r["reference_normalized"])
        assert prev == r["reference_normalized"]


def test_4_reference_normalized_identical_across_backends() -> None:
    rows = [
        _row(),
        _row(backend_name="whisper_lora_ct2_int8"),
        _row(backend_name="assemblyai", local_only=False,
             third_party_provider="assemblyai", cost_usd=0.0026),
    ]
    _check_reference_normalized_identical(rows)


def test_4_reference_normalized_mismatch_fails() -> None:
    rows = [
        _row(),
        _row(backend_name="assemblyai", reference_normalized="hello",
             local_only=False, third_party_provider="assemblyai", cost_usd=0.0026),
    ]
    with pytest.raises(AssertionError):
        _check_reference_normalized_identical(rows)


# --- Test 5 ---------------------------------------------------------------


def test_5_normalization_version_recorded() -> None:
    rows = [_row(), _row(backend_name="assemblyai", local_only=False,
                         third_party_provider="assemblyai", cost_usd=0.0026)]
    for r in rows:
        assert r.get("normalization_version"), "normalization_version is empty"


def test_5_normalization_version_missing_fails() -> None:
    r = _row(normalization_version=None)
    assert not r.get("normalization_version")


# --- Test 6 ---------------------------------------------------------------


_LATENCY_FIELDS = (
    "backend_latency_ms",
    "server_processing_latency_ms",
    "end_to_end_latency_ms",
)


def _check_error_implies_null_latency(rows: List[Dict[str, Any]]) -> None:
    for r in rows:
        any_null = any(r.get(f) is None for f in _LATENCY_FIELDS)
        if any_null:
            assert r["error_or_null"] is not None, (
                f"row has null latency without error_or_null: {r['audio_id']}/{r['backend_name']}"
            )


def test_6_error_implies_null_latency_passes() -> None:
    rows = [
        _row(),
        _row(backend_name="assemblyai",
             backend_latency_ms=None,
             server_processing_latency_ms=None,
             end_to_end_latency_ms=None,
             raw_transcript=None, normalized_transcript=None,
             wer=None, cer=None, wa=None,
             ram_peak_mb=None,
             cost_usd=None,
             local_only=False, third_party_provider="assemblyai",
             error_or_null="provider timeout"),
    ]
    _check_error_implies_null_latency(rows)


def test_6_error_implies_null_latency_fails_when_no_error() -> None:
    rows = [_row(backend_latency_ms=None, error_or_null=None)]
    with pytest.raises(AssertionError):
        _check_error_implies_null_latency(rows)


# --- Test 7 ---------------------------------------------------------------


def _check_cost_usd_local_only(rows: List[Dict[str, Any]]) -> None:
    for r in rows:
        if r["local_only"]:
            assert r["cost_usd"] is None, (
                f"local_only row must have null cost_usd: {r['audio_id']}/{r['backend_name']}"
            )
        else:
            assert isinstance(r["cost_usd"], (int, float)), (
                f"non-local row must have numeric cost_usd: {r['audio_id']}/{r['backend_name']}"
            )


def test_7_cost_usd_local_only_passes() -> None:
    rows = [
        _row(),
        _row(backend_name="assemblyai",
             local_only=False, third_party_provider="assemblyai",
             cost_usd=0.0026),
    ]
    _check_cost_usd_local_only(rows)


def test_7_local_only_with_cost_fails() -> None:
    rows = [_row(cost_usd=0.001)]
    with pytest.raises(AssertionError):
        _check_cost_usd_local_only(rows)


def test_7_remote_with_null_cost_fails() -> None:
    rows = [_row(local_only=False, third_party_provider="assemblyai", cost_usd=None)]
    with pytest.raises(AssertionError):
        _check_cost_usd_local_only(rows)
