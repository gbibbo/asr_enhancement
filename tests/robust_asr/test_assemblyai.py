"""Unit tests for robust_asr P5.1 AssemblyAI scripts.

Covers:
  - probe_assemblyai_runtime.py key_unset path
  - populate_assemblyai_cache.py: pricing-validation, freshness, key-unset,
    budget guard (estimated cost > cap), running-cost guard, dry-run path
  - evaluate_assemblyai_from_cache.py: canonical schema row dict + parquet
    write with no_cache_entry and synthetic transcript rows

No AssemblyAI network calls are performed.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

PROBE = REPO_ROOT / "scripts" / "robust_asr" / "probe_assemblyai_runtime.py"
POPULATE = REPO_ROOT / "scripts" / "robust_asr" / "populate_assemblyai_cache.py"
EVALUATE = REPO_ROOT / "scripts" / "robust_asr" / "evaluate_assemblyai_from_cache.py"
PRICING_PATH = REPO_ROOT / "configs" / "robust_asr" / "pricing_v1.yaml"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def probe_mod():
    return _load("probe_assemblyai_runtime", PROBE)


@pytest.fixture(scope="module")
def populate_mod():
    return _load("populate_assemblyai_cache", POPULATE)


@pytest.fixture(scope="module")
def evaluate_mod():
    return _load("evaluate_assemblyai_from_cache", EVALUATE)


# ----- probe ---------------------------------------------------------------


def test_probe_key_unset(probe_mod):
    out = probe_mod.probe(env={})
    assert out == "ASSEMBLYAI_RUNTIME=false reason=key_unset"


def test_probe_cli_key_unset(monkeypatch):
    monkeypatch.delenv("ASSEMBLYAI_API_KEY", raising=False)
    import subprocess
    r = subprocess.run([sys.executable, str(PROBE)],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "ASSEMBLYAI_RUNTIME=false" in r.stdout
    assert "reason=key_unset" in r.stdout


# ----- pricing validation --------------------------------------------------


def test_pricing_validates_real_config(populate_mod):
    pricing = yaml.safe_load(PRICING_PATH.read_text(encoding="utf-8"))
    assert populate_mod.validate_pricing(pricing) == []


def test_pricing_missing_fields(populate_mod):
    bad = {"assemblyai_pricing_checked_date": "2026-05-13"}
    missing = populate_mod.validate_pricing(bad)
    assert "max_total_cost_usd" in missing
    assert "unit_price_usd_per_audio_second" in missing


def test_pricing_freshness_pass(populate_mod):
    pricing = {"assemblyai_pricing_checked_date":
               date.today().isoformat()}
    assert populate_mod.pricing_is_fresh(pricing) is True


def test_pricing_freshness_stale(populate_mod):
    pricing = {"assemblyai_pricing_checked_date":
               (date.today() - timedelta(days=120)).isoformat()}
    assert populate_mod.pricing_is_fresh(pricing) is False


# ----- populate cost estimate ---------------------------------------------


def test_estimate_cost_sums_durations(populate_mod):
    pricing = {"unit_price_usd_per_audio_second": 0.001}
    rows = [{"duration_s": 60.0, "audio_sha256": "a"},
            {"duration_s": 30.0, "audio_sha256": "b"}]
    assert populate_mod.estimate_cost(rows, pricing) == pytest.approx(0.09)


def test_populate_cli_key_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("ASSEMBLYAI_API_KEY", raising=False)
    manifests = tmp_path / "m.yaml"
    manifests.write_text("manifest_set: t\nmanifests: []\n", encoding="utf-8")
    import subprocess
    r = subprocess.run(
        [sys.executable, str(POPULATE),
         "--manifests", str(manifests),
         "--cache-dir", str(tmp_path / "cache"),
         "--pricing-config", str(PRICING_PATH)],
        capture_output=True, text=True,
        env={**{k: v for k, v in os.environ.items()
                if k != "ASSEMBLYAI_API_KEY"}},
    )
    assert r.returncode == 8, r.stderr
    assert "ASSEMBLYAI_API_KEY_UNSET" in r.stderr


def test_populate_cli_pricing_stale(tmp_path, monkeypatch):
    stale_pricing = yaml.safe_load(PRICING_PATH.read_text(encoding="utf-8"))
    stale_pricing["assemblyai_pricing_checked_date"] = \
        (date.today() - timedelta(days=180)).isoformat()
    stale_path = tmp_path / "pricing_stale.yaml"
    stale_path.write_text(yaml.safe_dump(stale_pricing), encoding="utf-8")
    manifests = tmp_path / "m.yaml"
    manifests.write_text("manifest_set: t\nmanifests: []\n", encoding="utf-8")
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test")
    import subprocess
    r = subprocess.run(
        [sys.executable, str(POPULATE),
         "--manifests", str(manifests),
         "--cache-dir", str(tmp_path / "cache"),
         "--pricing-config", str(stale_path)],
        capture_output=True, text=True,
    )
    assert r.returncode == 12, r.stderr
    assert "PENDING_PRICING_VERIFICATION" in r.stderr


def test_populate_dry_run_under_budget(tmp_path, monkeypatch):
    # Empty manifest set → cost 0 → under any budget; dry-run exits 0 without
    # network calls.
    manifests = tmp_path / "m.yaml"
    manifests.write_text("manifest_set: t\nmanifests: []\n", encoding="utf-8")
    monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test")
    import subprocess
    r = subprocess.run(
        [sys.executable, str(POPULATE),
         "--manifests", str(manifests),
         "--cache-dir", str(tmp_path / "cache"),
         "--pricing-config", str(PRICING_PATH),
         "--dry-run"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "PRE_SPEND_SUMMARY" in r.stdout


def test_populate_budget_exceeded(populate_mod, tmp_path):
    # Estimate path: synthesize a row set that exceeds the cap.
    pricing = {"unit_price_usd_per_audio_second": 1.0,
               "max_total_cost_usd": 0.5}
    rows = [{"duration_s": 1.0, "audio_sha256": "a"},
            {"duration_s": 1.0, "audio_sha256": "b"}]
    est = populate_mod.estimate_cost(rows, pricing)
    assert est > pricing["max_total_cost_usd"]


def test_populate_running_cost_guard(populate_mod, tmp_path):
    pricing = {"unit_price_usd_per_audio_second": 1.0,
               "max_total_cost_usd": 0.5,
               "request_timeout_seconds": 1.0,
               "http_429_max_retries": 0,
               "http_5xx_max_retries": 0,
               "http_5xx_partial_threshold_pct": 1.0}
    rows = [{"duration_s": 1.0, "audio_sha256": "first",
             "audio_id": "a", "audio_path_or_uri": "/nonexistent/x.flac"}]

    class _Session:
        def post(self, *a, **kw):
            raise AssertionError("populate should not make network calls "
                                 "when running cost would exceed cap")

    rc, summary = populate_mod.populate(rows, pricing, tmp_path,
                                        key="test", session=_Session())
    assert rc == populate_mod.EXIT_BUDGET
    assert summary["outcome"] == "BUDGET_EXCEEDED"


# ----- evaluate -----------------------------------------------------------


def test_evaluate_row_dict_no_cache(evaluate_mod):
    mrow = {"audio_id": "id_a", "source_dataset": "librispeech",
            "source_split": "test-clean", "speaker_id": "1",
            "utterance_id": "u1", "condition_family": "clean",
            "degradation_id": "clean",
            "filter_params_json": "{}", "snr_db": None,
            "rir_id_or_null": None,
            "audio_path_or_uri": "/x.flac",
            "audio_sha256": "abc",
            "reference_text": "hello world"}
    row = evaluate_mod._row_dict(mrow, None, {}, "2026-05-13T00:00:00+00:00")
    assert row["error_or_null"] == "no_cache_entry"
    assert row["wer"] is None
    assert row["wa"] is None
    assert row["local_only"] is False
    assert row["third_party_provider"] == "assemblyai"
    assert row["backend_name"] == "assemblyai"
    assert row["backend_kind"] == "cloud_asr"


def test_evaluate_row_dict_with_cached_transcript(evaluate_mod):
    mrow = {"audio_id": "id_a", "source_dataset": "librispeech",
            "source_split": "test-clean", "speaker_id": "1",
            "utterance_id": "u1", "condition_family": "clean",
            "degradation_id": "clean",
            "filter_params_json": "{}", "snr_db": None,
            "rir_id_or_null": None,
            "audio_path_or_uri": "/x.flac",
            "audio_sha256": "abc",
            "reference_text": "hello world"}
    cached = {"cost_usd": 0.01,
              "assemblyai": {"status": "completed", "text": "hello world"}}
    row = evaluate_mod._row_dict(mrow, cached, {}, "2026-05-13T00:00:00+00:00")
    assert row["error_or_null"] is None
    assert row["wer"] == pytest.approx(0.0)
    assert row["wa"] == pytest.approx(1.0)
    assert row["cost_usd"] == pytest.approx(0.01)
    assert row["raw_transcript"] == "hello world"


def test_evaluate_writes_parquet(tmp_path, evaluate_mod):
    rows = []
    mrow = {"audio_id": "id_a", "source_dataset": "librispeech",
            "source_split": "test-clean", "speaker_id": "1",
            "utterance_id": "u1", "condition_family": "clean",
            "degradation_id": "clean",
            "filter_params_json": "{}", "snr_db": None,
            "rir_id_or_null": None,
            "audio_path_or_uri": "/x.flac",
            "audio_sha256": "abc",
            "reference_text": "hello"}
    rows.append(evaluate_mod._row_dict(mrow, None, {},
                                       "2026-05-13T00:00:00+00:00"))
    out = tmp_path / "out.parquet"
    evaluate_mod.write_parquet(rows, out)
    import pyarrow.parquet as pq
    t = pq.read_table(out)
    assert t.num_rows == 1
    assert "audio_id" in t.column_names
    assert "local_only" in t.column_names
    assert t.column("third_party_provider").to_pylist() == ["assemblyai"]
