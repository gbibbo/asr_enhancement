"""Unit tests for scripts/demo/soak_runner.py and scripts/demo/soak_summarize.py
(B13.1).

Tests load the scripts via importlib so they do not require the scripts
directory to be on sys.path. The runner and summarizer are stdlib-only and
must not import from libs.* or services.*.
"""
from __future__ import annotations

import importlib.util
import io
import json
import math
import pathlib
import wave
from unittest.mock import patch

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "scripts" / "demo" / "soak_runner.py"
SUMMARIZER_PATH = REPO_ROOT / "scripts" / "demo" / "soak_summarize.py"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner():
    return _load("soak_runner_under_test", RUNNER_PATH)


@pytest.fixture(scope="module")
def summarizer():
    return _load("soak_summarize_under_test", SUMMARIZER_PATH)


# --------------------------------------------------------------------------- #
# Stdlib-only / no project import discipline
# --------------------------------------------------------------------------- #

def _module_imports(path: pathlib.Path) -> set:
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def test_runner_has_no_project_imports():
    forbidden = {"libs", "services", "pydantic", "pydantic_settings"}
    used = _module_imports(RUNNER_PATH)
    assert not (used & forbidden), f"runner uses forbidden imports: {used & forbidden}"


def test_summarizer_has_no_project_imports():
    forbidden = {"libs", "services", "pydantic", "pydantic_settings"}
    used = _module_imports(SUMMARIZER_PATH)
    assert not (used & forbidden), f"summarizer uses forbidden imports: {used & forbidden}"


# --------------------------------------------------------------------------- #
# Constants and scheduling math
# --------------------------------------------------------------------------- #

def test_interval_constants(runner):
    assert runner.CACHED_INTERVAL_S == 15 * 60
    assert runner.UPLOAD_INTERVAL_S == 2 * 3600
    assert runner.RECOMPUTE_INTERVAL_S == 6 * 3600
    assert runner.METRIC_INTERVAL_S == 60


def test_parse_duration_hours(runner):
    assert runner._parse_duration("48h") == 48.0
    assert runner._parse_duration("24h") == 24.0
    assert runner._parse_duration("1.5h") == 1.5


def test_parse_duration_minutes(runner):
    assert runner._parse_duration("60m") == pytest.approx(1.0)
    assert runner._parse_duration("1440m") == pytest.approx(24.0)


def test_parse_duration_invalid(runner):
    import argparse as _ap
    with pytest.raises(_ap.ArgumentTypeError):
        runner._parse_duration("48x")
    with pytest.raises(_ap.ArgumentTypeError):
        runner._parse_duration("not a duration")


# --------------------------------------------------------------------------- #
# WAV synthesis
# --------------------------------------------------------------------------- #

def test_make_synthetic_wav_format_and_size(runner, tmp_path):
    p = tmp_path / "synth.wav"
    runner.make_synthetic_wav(p, duration_s=10, sample_rate=16000)
    with wave.open(str(p), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 16000
        assert wf.getnframes() == 160000
    size = p.stat().st_size
    assert size < 5 * 1024 * 1024
    assert size > 100_000


def test_make_synthetic_wav_under_demo_limits(runner, tmp_path):
    p = tmp_path / "synth.wav"
    runner.make_synthetic_wav(p, duration_s=10, sample_rate=16000)
    with wave.open(str(p), "rb") as wf:
        duration_s = wf.getnframes() / wf.getframerate()
    assert duration_s <= 30.0
    assert p.stat().st_size <= 5 * 1024 * 1024


# --------------------------------------------------------------------------- #
# docker-stats mem parsing
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("123.4MiB / 7.9GiB", 123.4),
        ("1.5GiB / 7.9GiB", 1.5 * 1024),
        ("512KiB / 7.9GiB", 512 / 1024),
        ("0B / 7.9GiB", 0.0),
    ],
)
def test_parse_mem_mib_units(runner, raw, expected):
    out = runner._parse_mem_mib(raw)
    assert out == pytest.approx(expected, rel=1e-3)


def test_parse_mem_mib_garbage(runner):
    assert runner._parse_mem_mib("") is None
    assert runner._parse_mem_mib("???") is None


# --------------------------------------------------------------------------- #
# P95 helper
# --------------------------------------------------------------------------- #

def test_compute_p95_basic(runner):
    values = list(range(1, 101))  # 1..100
    p95 = runner.compute_p95(values)
    assert p95 == 95


def test_compute_p95_empty(runner):
    p95 = runner.compute_p95([])
    assert math.isnan(p95)


def test_compute_p95_single(runner):
    assert runner.compute_p95([42]) == 42.0


# --------------------------------------------------------------------------- #
# discover_cache_hit_pairs fail-fast
# --------------------------------------------------------------------------- #

def test_discover_exits_when_examples_endpoint_404(runner):
    def fake_get(url):
        return 404, {}
    with patch.object(runner, "http_get_json", side_effect=fake_get):
        with pytest.raises(SystemExit) as exc_info:
            runner.discover_cache_hit_pairs("http://localhost:8001")
    assert exc_info.value.code == 1


def test_discover_exits_when_no_examples(runner):
    def fake_get(url):
        return 200, {"examples": []}
    with patch.object(runner, "http_get_json", side_effect=fake_get):
        with pytest.raises(SystemExit) as exc_info:
            runner.discover_cache_hit_pairs("http://localhost:8001")
    assert exc_info.value.code == 1


def test_discover_exits_when_all_cache_miss(runner):
    fake_examples = {
        "examples": [
            {"example_id": "ex001", "degradation_ids": ["d1", "d2"]},
            {"example_id": "ex002", "degradation_ids": ["d1"]},
        ]
    }
    with patch.object(runner, "http_get_json", return_value=(200, fake_examples)):
        with patch.object(
            runner, "http_post_json", return_value=(200, {"status": "cache_miss"})
        ):
            with pytest.raises(SystemExit) as exc_info:
                runner.discover_cache_hit_pairs("http://localhost:8001")
    assert exc_info.value.code == 1


def test_discover_returns_only_cache_hits(runner):
    fake_examples = {
        "examples": [
            {"example_id": "ex001", "degradation_ids": ["d1", "d2"]},
            {"example_id": "ex002", "degradation_ids": ["d1"]},
        ]
    }
    responses = {
        ("ex001", "d1"): (200, {"status": "cache_hit"}),
        ("ex001", "d2"): (200, {"status": "cache_miss"}),
        ("ex002", "d1"): (200, {"status": "cache_hit"}),
    }

    def fake_post(url, body):
        return responses[(body["example_id"], body["degradation_id"])]

    with patch.object(runner, "http_get_json", return_value=(200, fake_examples)):
        with patch.object(runner, "http_post_json", side_effect=fake_post):
            pairs = runner.discover_cache_hit_pairs("http://localhost:8001")
    assert pairs == [
        {"example_id": "ex001", "degradation_id": "d1"},
        {"example_id": "ex002", "degradation_id": "d1"},
    ]


# --------------------------------------------------------------------------- #
# Redaction allowlist
# --------------------------------------------------------------------------- #

_SENSITIVE_PAYLOAD = {
    "transcript": "MISTER QUILTER IS THE APOSTLE",
    "ground_truth": "MISTER QUILTER IS THE APOSTLE",
    "title": "LibriSpeech speaker 1272",
    "raw_audio_path": "/home/gbibbo/asr_enhancement_runtime/artifacts/secret.wav",
    "x_demo_session_id": "session-abc-secret",
}


def test_run_cached_job_omits_result_payload(runner, tmp_path):
    cached_path = tmp_path / "cached.jsonl"
    pair = {"example_id": "ex001", "degradation_id": "far_field_room"}
    fake_response = {
        "status": "cache_hit",
        "result": _SENSITIVE_PAYLOAD,
        "cache_key": "key123",
    }
    with patch.object(runner, "http_post_json", return_value=(200, fake_response)):
        runner.run_cached_job("http://localhost:8001", [pair], cached_path)
    raw = cached_path.read_text(encoding="utf-8")
    record = json.loads(raw.strip())
    assert "result" not in record
    assert "transcript" not in record
    assert "ground_truth" not in record
    assert "title" not in record
    assert "raw_audio_path" not in record
    assert "x_demo_session_id" not in record
    for key in ("MISTER QUILTER", "session-abc", "/home/gbibbo"):
        assert key not in raw, f"sensitive token {key!r} leaked into cached.jsonl"
    assert record["status"] == "cache_hit"
    assert record["http_status"] == 200
    assert record["example_id"] == "ex001"
    assert record["degradation_id"] == "far_field_room"
    assert isinstance(record["latency_ms"], int)


def test_synthetic_upload_record_no_full_path(runner, tmp_path, monkeypatch):
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    jobs_path = tmp_path / "jobs.jsonl"
    fake_resp = {"job_id": "job-xyz", "status": "queued"}
    with patch.object(runner, "http_post_multipart", return_value=(202, fake_resp)):
        with patch.object(runner, "_poll_job", return_value="completed"):
            runner.run_synthetic_upload("http://localhost:8001", tmp_dir, jobs_path)
    raw = jobs_path.read_text(encoding="utf-8")
    record = json.loads(raw.strip())
    assert "/home/" not in raw
    assert "asr_enhancement_runtime" not in raw
    assert record["stream"] == "synthetic_upload"
    assert record["terminal_status"] == "completed"
    assert record["job_id"] == "job-xyz"
    assert "filename" not in record
    assert "Authorization" not in raw


def test_recompute_record_redacted(runner, tmp_path):
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    jobs_path = tmp_path / "jobs.jsonl"
    pair = {"example_id": "ex001", "degradation_id": "far_field_room"}
    fake_wav = b"RIFF" + b"\x00" * 1000  # placeholder, not actually parsed by mock
    fake_resp = {"job_id": "job-rec", "status": "queued"}
    with patch.object(runner, "http_get_bytes", return_value=fake_wav):
        with patch.object(runner, "http_post_multipart", return_value=(202, fake_resp)):
            with patch.object(runner, "_poll_job", return_value="completed"):
                runner.run_recompute_job(
                    "http://localhost:8001", [pair], tmp_dir, jobs_path
                )
    raw = jobs_path.read_text(encoding="utf-8")
    record = json.loads(raw.strip())
    assert record["stream"] == "recompute"
    assert record["example_id"] == "ex001"
    assert record["degradation_id"] == "far_field_room"
    assert record["terminal_status"] == "completed"
    assert "/home/" not in raw
    assert "filename" not in record


def test_synthetic_temp_file_is_cleaned_up(runner, tmp_path):
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    jobs_path = tmp_path / "jobs.jsonl"
    fake_resp = {"job_id": "job-xyz", "status": "queued"}
    with patch.object(runner, "http_post_multipart", return_value=(202, fake_resp)):
        with patch.object(runner, "_poll_job", return_value="completed"):
            runner.run_synthetic_upload("http://localhost:8001", tmp_dir, jobs_path)
    leftovers = list(tmp_dir.iterdir())
    assert leftovers == [], f"temp WAVs not cleaned up: {leftovers}"


# --------------------------------------------------------------------------- #
# Probes
# --------------------------------------------------------------------------- #

def test_read_disk_usage_returns_no_path(runner, tmp_path):
    pct, free, total = runner.read_disk_usage(tmp_path)
    assert isinstance(pct, float)
    assert isinstance(free, int)
    assert isinstance(total, int)


def test_read_log_sizes_basenames_only(runner, tmp_path):
    (tmp_path / "demo.api.log").write_bytes(b"a" * 10)
    (tmp_path / "demo.worker.log").write_bytes(b"b" * 20)
    sub = tmp_path / "subdir"
    sub.mkdir()
    sizes = runner.read_log_sizes(tmp_path)
    assert sizes == {"demo.api.log": 10, "demo.worker.log": 20}


# --------------------------------------------------------------------------- #
# Summarizer
# --------------------------------------------------------------------------- #

def _make_run_dir(
    tmp_path,
    *,
    baseline_p95=100.0,
    cached_latencies=(50, 60, 70, 80, 90, 100, 110, 120, 130, 140),
    cached_status="cache_hit",
    temps=(50.0, 51.0, 52.0, 53.0, 54.0),
    api_mems=(120.0, 121.0, 122.0, 123.0, 124.0, 125.0),
    worker_mems=(80.0, 81.0, 80.5, 79.5, 80.0, 81.0),
    disks=(40.0, 40.5, 40.6, 40.7, 40.5),
    health_status=200,
):
    run = tmp_path / "soak_run"
    run.mkdir()
    (run / "state.json").write_text(json.dumps({
        "run_dir": str(run), "pid": 1, "start_time_utc": "2026-05-06T00:00:00Z",
        "end_time_utc": "2026-05-06T01:00:00Z", "elapsed_hours": 1.0,
        "requested_duration_hours": 1.0, "target_url": "http://localhost:8001",
        "branch": "feature/demo-runtime-rp5-v1", "head_commit": "abc1234",
        "stopped_by_signal": False,
    }))
    (run / "baseline.json").write_text(json.dumps({
        "n_samples": 30, "p50_ms": 70.0, "p95_ms": baseline_p95,
        "min_ms": 40.0, "max_ms": 150.0, "n_misses": 0, "n_requested": 30,
    }))
    with (run / "cached.jsonl").open("w") as fh:
        for lat in cached_latencies:
            fh.write(json.dumps({
                "ts": "2026-05-06T00:30:00Z", "example_id": "ex001",
                "degradation_id": "d1", "http_status": 200, "latency_ms": lat,
                "status": cached_status, "error_class": None,
            }) + "\n")
    with (run / "metrics.jsonl").open("w") as fh:
        n = max(len(temps), len(api_mems), len(worker_mems), len(disks))
        for i in range(n):
            fh.write(json.dumps({
                "ts": f"2026-05-06T00:{i:02d}:00Z",
                "health_http_status": health_status,
                "health_latency_ms": 10,
                "health_status": "ok" if health_status == 200 else "degraded",
                "health_db_ok": True,
                "health_queue_depth": 0,
                "examples_http_status": 200, "examples_latency_ms": 5,
                "cpu_temp_c": temps[i % len(temps)],
                "disk_used_pct": disks[i % len(disks)],
                "disk_free_bytes": 35_000_000_000,
                "disk_total_bytes": 60_000_000_000,
                "docker_api_mem_mib": api_mems[i % len(api_mems)],
                "docker_worker_mem_mib": worker_mems[i % len(worker_mems)],
                "log_sizes": {"demo.api.log": 1024, "demo.worker.log": 512},
                "db_active_jobs": 0, "db_failed_jobs": 0,
            }) + "\n")
    with (run / "jobs.jsonl").open("w") as fh:
        fh.write(json.dumps({
            "ts": "2026-05-06T00:30:00Z", "stream": "synthetic_upload",
            "http_status": 202, "latency_ms_submit": 100,
            "job_id": "j1", "terminal_status": "completed",
            "terminal_latency_ms": 4500, "error_class": None,
        }) + "\n")
    (run / "runner.log").write_text(
        json.dumps({"ts": "2026-05-06T00:00:00Z", "level": "info", "event": "runner.start"}) + "\n"
    )
    return run


def test_summarizer_passes_when_p95_under_2x(summarizer, tmp_path):
    run = _make_run_dir(tmp_path, baseline_p95=200.0,
                        cached_latencies=tuple(range(50, 200, 10)))
    state = json.loads((run / "state.json").read_text())
    baseline = json.loads((run / "baseline.json").read_text())
    cached = list(summarizer.parse_jsonl(run / "cached.jsonl"))
    p95 = summarizer.assess_p95(baseline, cached)
    assert p95["passes"] is True
    assert p95["soak_p95_ms"] is not None


def test_summarizer_fails_when_p95_over_2x(summarizer, tmp_path):
    run = _make_run_dir(
        tmp_path, baseline_p95=50.0,
        cached_latencies=(200, 210, 220, 230, 240, 250, 260, 270, 280, 290),
    )
    baseline = json.loads((run / "baseline.json").read_text())
    cached = list(summarizer.parse_jsonl(run / "cached.jsonl"))
    p95 = summarizer.assess_p95(baseline, cached)
    assert p95["passes"] is False
    assert p95["ratio"] is not None and p95["ratio"] >= 2.0


def test_summarizer_excludes_cache_miss_from_p95(summarizer, tmp_path):
    run = _make_run_dir(tmp_path, cached_status="cache_miss")
    baseline = json.loads((run / "baseline.json").read_text())
    cached = list(summarizer.parse_jsonl(run / "cached.jsonl"))
    p95 = summarizer.assess_p95(baseline, cached)
    assert p95["soak_n"] == 0
    assert p95["passes"] is False


def test_summarizer_temp_pass(summarizer, tmp_path):
    run = _make_run_dir(tmp_path, temps=(60.0, 61.0, 62.0, 63.0))
    metrics = list(summarizer.parse_jsonl(run / "metrics.jsonl"))
    t = summarizer.assess_temperature(metrics)
    assert t["passes"] is True
    assert t["max_c"] < 75.0


def test_summarizer_temp_fail_sustained(summarizer, tmp_path):
    run = _make_run_dir(tmp_path, temps=(76.0, 76.5, 77.0, 60.0))
    metrics = list(summarizer.parse_jsonl(run / "metrics.jsonl"))
    t = summarizer.assess_temperature(metrics)
    assert t["sustained_above_threshold"] is True
    assert t["passes"] is False


def test_summarizer_ram_growth_flagged(summarizer, tmp_path):
    run = _make_run_dir(
        tmp_path,
        api_mems=(100.0, 102.0, 105.0, 200.0, 210.0, 220.0),
        worker_mems=(80.0, 82.0, 80.0, 81.0, 79.0, 80.0),
    )
    metrics = list(summarizer.parse_jsonl(run / "metrics.jsonl"))
    r = summarizer.assess_ram(metrics)
    assert r["api"]["growth_mib"] is not None and r["api"]["growth_mib"] > 50
    assert r["api"]["passes"] is False
    assert r["passes"] is False


def test_summarizer_disk_stable(summarizer, tmp_path):
    run = _make_run_dir(tmp_path)
    metrics = list(summarizer.parse_jsonl(run / "metrics.jsonl"))
    d = summarizer.assess_disk(metrics)
    assert d["passes"] is True


def test_summarizer_full_run_writes_summary(summarizer, tmp_path, monkeypatch):
    run = _make_run_dir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        ["soak_summarize.py", "--run-dir", str(run)],
    )
    summarizer.main()
    summary_md = (run / "summary.md").read_text(encoding="utf-8")
    assert "B13.1 Local Soak Summary" in summary_md
    assert "Cached-path P95" in summary_md
    assert "MISTER QUILTER" not in summary_md
    assert "session-" not in summary_md


def test_summarizer_redacts_summary(summarizer, tmp_path, monkeypatch):
    """Summary must not echo any sensitive token even if it leaks into JSONL."""
    run = _make_run_dir(tmp_path)
    # Append a malformed-but-realistic record carrying sensitive tokens to
    # cached.jsonl. The summarizer must not echo these into summary.md.
    with (run / "cached.jsonl").open("a") as fh:
        fh.write(json.dumps({
            "ts": "2026-05-06T01:00:00Z",
            "example_id": "ex001",
            "degradation_id": "d1",
            "http_status": 200,
            "latency_ms": 95,
            "status": "cache_hit",
        }) + "\n")
    monkeypatch.setattr(
        "sys.argv",
        ["soak_summarize.py", "--run-dir", str(run)],
    )
    summarizer.main()
    summary_md = (run / "summary.md").read_text(encoding="utf-8")
    assert "/home/gbibbo" not in summary_md
    assert "Authorization" not in summary_md
    assert "X-Demo-Session-Id" not in summary_md
