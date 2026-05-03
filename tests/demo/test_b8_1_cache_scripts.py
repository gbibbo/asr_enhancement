"""Tests for the B8.1 cache scripts.

Covers:

* scripts/prewarm_cache.py
* scripts/validate_cache.py
* scripts/invalidate_cache.py
* libs/demo/persistence.py cache_entries helpers
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from libs.common import versions
from libs.demo import persistence
from libs.demo.cache import build_cache_key

REPO_ROOT = Path(__file__).resolve().parents[2]
PREWARM = REPO_ROOT / "scripts" / "prewarm_cache.py"
VALIDATE = REPO_ROOT / "scripts" / "validate_cache.py"
INVALIDATE = REPO_ROOT / "scripts" / "invalidate_cache.py"

EXAMPLES = (
    ("ex001", ("phone_call", "muffled")),
    ("ex003", ("phone_call",)),
)
ARTIFACTS_ABS = "/home/gbibbo/asr_enhancement_runtime/artifacts/examples"


def _load_script(label: str, path: Path):
    spec = importlib.util.spec_from_file_location(label, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def prewarm_mod():
    return _load_script("b8_1_prewarm_under_test", PREWARM)


@pytest.fixture
def validate_mod():
    return _load_script("b8_1_validate_under_test", VALIDATE)


@pytest.fixture
def invalidate_mod():
    return _load_script("b8_1_invalidate_under_test", INVALIDATE)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def fixture_dirs(tmp_path: Path) -> dict:
    artifacts_root = tmp_path / "artifacts"
    artifacts_root.mkdir()
    examples_payload = []
    baseline_results = []
    for ex_id, degs in EXAMPLES:
        ex_dir = artifacts_root / ex_id
        ex_dir.mkdir()
        for variant in ("clean",) + degs:
            audio_bytes = f"audio-{ex_id}-{variant}".encode("utf-8")
            (ex_dir / f"{variant}.wav").write_bytes(audio_bytes)
            baseline_results.append(
                {
                    "example_id": ex_id,
                    "source_recording_id": f"src-{ex_id}",
                    "degradation_id": variant,
                    "audio_path_relative": f"{ex_id}/{variant}.wav",
                    "audio_sha256": _sha256(audio_bytes),
                    "hypothesis": f"hyp {ex_id} {variant}",
                    "wer": 0.1,
                    "word_accuracy": 0.9,
                    "latency_seconds": 1.23,
                }
            )
        examples_payload.append(
            {
                "example_id": ex_id,
                "title": f"title {ex_id}",
                "description": "test",
                "duration_seconds": 5.0,
                "degradation_ids": list(degs),
                "ground_truth": f"gt {ex_id}",
                "audio_available": True,
                "clean_audio_path": f"{ex_id}/clean.wav",
                "degraded_audio_paths": {d: f"{ex_id}/{d}.wav" for d in degs},
            }
        )
    examples_path = tmp_path / "examples.json"
    examples_path.write_text(json.dumps(examples_payload), encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "engine": "faster-whisper",
                "model": "tiny.en",
                "artifacts_root": str(artifacts_root),
                "results": baseline_results,
            }
        ),
        encoding="utf-8",
    )
    db_path = tmp_path / "demo.db"
    return {
        "artifacts_root": artifacts_root,
        "examples": examples_path,
        "baseline": baseline_path,
        "db": db_path,
        "expected_pairs": [
            (ex_id, variant)
            for ex_id, degs in EXAMPLES
            for variant in ("clean",) + degs
        ],
    }


def _common_prewarm_args(fixture_dirs: dict) -> list[str]:
    return [
        "--examples", str(fixture_dirs["examples"]),
        "--artifacts-root", str(fixture_dirs["artifacts_root"]),
        "--baseline-report", str(fixture_dirs["baseline"]),
        "--db", str(fixture_dirs["db"]),
        "--asr-provider", "whisper",
        "--asr-model", "tiny.en",
        "--enhancer", "bypass",
        "--source", "reports",
    ]


def test_prewarm_writes_one_row_per_variant(prewarm_mod, fixture_dirs):
    rc = prewarm_mod.main(_common_prewarm_args(fixture_dirs))
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    assert len(rows) == len(fixture_dirs["expected_pairs"])
    pairs_in_db = {(r["example_id"], r["degradation_id"]) for r in rows}
    assert pairs_in_db == set(fixture_dirs["expected_pairs"])
    for row in rows:
        expected_key = build_cache_key(
            example_id=row["example_id"],
            degradation_id=row["degradation_id"],
            asr_provider="whisper",
            asr_model_version="tiny.en",
            enhancer_version="bypass",
        )
        assert row["cache_key"] == expected_key
        assert row["asr_provider"] == "whisper"
        assert row["asr_model_version"] == "tiny.en"
        assert row["enhancer_version"] == "bypass"
        assert row["degradation_version"] == versions.DEGRADATION_VERSION
        assert row["metrics_version"] == versions.METRICS_VERSION
        payload = json.loads(row["result_json"])
        assert payload["audio_path_relative"] == (
            f"{row['example_id']}/{row['degradation_id']}.wav"
        )
        assert len(payload["audio_sha256"]) == 64
        assert row["validated_at"] is None


def test_prewarm_dry_run_writes_nothing(prewarm_mod, fixture_dirs):
    rc = prewarm_mod.main(_common_prewarm_args(fixture_dirs) + ["--dry-run"])
    assert rc == 0
    # DB schema is initialized but no rows inserted
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    assert rows == []


def test_prewarm_aborts_on_sha_mismatch(prewarm_mod, fixture_dirs):
    target = fixture_dirs["artifacts_root"] / "ex001" / "clean.wav"
    target.write_bytes(b"tampered audio bytes")
    rc = prewarm_mod.main(_common_prewarm_args(fixture_dirs))
    assert rc == 1
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    assert rows == []


def test_prewarm_skips_pairs_missing_in_report(prewarm_mod, fixture_dirs):
    baseline = json.loads(fixture_dirs["baseline"].read_text(encoding="utf-8"))
    baseline["results"] = [
        r for r in baseline["results"]
        if not (r["example_id"] == "ex001" and r["degradation_id"] == "muffled")
    ]
    fixture_dirs["baseline"].write_text(
        json.dumps(baseline), encoding="utf-8"
    )
    rc = prewarm_mod.main(_common_prewarm_args(fixture_dirs))
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    pairs = {(r["example_id"], r["degradation_id"]) for r in rows}
    assert ("ex001", "muffled") not in pairs
    assert ("ex001", "phone_call") in pairs


def test_prewarm_rejects_assemblyai_as_deferred(
    prewarm_mod, fixture_dirs, capsys
):
    args = _common_prewarm_args(fixture_dirs)
    args[args.index("--asr-provider") + 1] = "assemblyai"
    rc = prewarm_mod.main(args)
    assert rc == 2
    assert "deferred" in capsys.readouterr().err.lower()
    assert not fixture_dirs["db"].exists()


def test_prewarm_rejects_source_run_as_deferred(
    prewarm_mod, fixture_dirs, capsys
):
    args = _common_prewarm_args(fixture_dirs)
    args[args.index("--source") + 1] = "run"
    rc = prewarm_mod.main(args)
    assert rc == 2
    assert "--source reports" in capsys.readouterr().err
    assert not fixture_dirs["db"].exists()


def test_prewarm_rejects_metricgan_enhancer(
    prewarm_mod, fixture_dirs, capsys
):
    args = _common_prewarm_args(fixture_dirs)
    args[args.index("--enhancer") + 1] = "metricgan_plus_pretrained"
    rc = prewarm_mod.main(args)
    assert rc == 2
    err = capsys.readouterr().err
    assert "T4.1" in err
    assert not fixture_dirs["db"].exists()


def test_prewarm_artifact_root_is_artifacts_root_not_per_example(
    prewarm_mod, fixture_dirs
):
    rc = prewarm_mod.main(_common_prewarm_args(fixture_dirs))
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    artifacts_root_resolved = str(fixture_dirs["artifacts_root"].resolve())
    for row in rows:
        assert row["artifact_root"] == artifacts_root_resolved
        payload = json.loads(row["result_json"])
        rel = payload["audio_path_relative"]
        assert rel.startswith(f"{row['example_id']}/")
        resolved = (Path(row["artifact_root"]) / rel).resolve()
        assert resolved.is_file()


def _common_validate_args(fixture_dirs: dict, tmp_path: Path) -> list[str]:
    return [
        "--db", str(fixture_dirs["db"]),
        "--artifacts-root", str(fixture_dirs["artifacts_root"]),
        "--report-json", str(tmp_path / "report.json"),
        "--report-md", str(tmp_path / "report.md"),
    ]


def _prewarm_then(prewarm_mod, fixture_dirs):
    rc = prewarm_mod.main(_common_prewarm_args(fixture_dirs))
    assert rc == 0


def test_validate_passes_for_freshly_prewarmed_db(
    prewarm_mod, validate_mod, fixture_dirs, tmp_path
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    rc = validate_mod.main(
        _common_validate_args(fixture_dirs, tmp_path) + ["--strict"]
    )
    assert rc == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["total_rows"] == len(fixture_dirs["expected_pairs"])
    assert report["outcomes"]["ok"] == report["total_rows"]
    for outcome in (
        "stale_version",
        "key_mismatch",
        "missing_artifact",
        "sha256_mismatch",
        "bad_payload",
    ):
        assert report["outcomes"][outcome] == 0
    assert (tmp_path / "report.md").is_file()


def test_validate_flags_stale_version(
    prewarm_mod, validate_mod, fixture_dirs, tmp_path, monkeypatch
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    monkeypatch.setattr(versions, "METRICS_VERSION", "STALE_TEST")
    rc = validate_mod.main(_common_validate_args(fixture_dirs, tmp_path))
    assert rc == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["outcomes"]["stale_version"] == report["total_rows"]
    assert report["outcomes"]["ok"] == 0


def test_validate_flags_missing_artifact(
    prewarm_mod, validate_mod, fixture_dirs, tmp_path
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    (fixture_dirs["artifacts_root"] / "ex001" / "clean.wav").unlink()
    rc = validate_mod.main(_common_validate_args(fixture_dirs, tmp_path))
    assert rc == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["outcomes"]["missing_artifact"] >= 1


def test_validate_flags_sha_mismatch(
    prewarm_mod, validate_mod, fixture_dirs, tmp_path
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    target = fixture_dirs["artifacts_root"] / "ex001" / "clean.wav"
    target.write_bytes(b"different bytes")
    rc = validate_mod.main(_common_validate_args(fixture_dirs, tmp_path))
    assert rc == 0
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["outcomes"]["sha256_mismatch"] >= 1


def test_validate_strict_exits_nonzero_on_failure(
    prewarm_mod, validate_mod, fixture_dirs, tmp_path
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    (fixture_dirs["artifacts_root"] / "ex001" / "clean.wav").unlink()
    rc = validate_mod.main(
        _common_validate_args(fixture_dirs, tmp_path) + ["--strict"]
    )
    assert rc == 1


def test_validate_mark_validated_sets_timestamp_only_on_ok(
    prewarm_mod, validate_mod, fixture_dirs, tmp_path
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    target = fixture_dirs["artifacts_root"] / "ex001" / "clean.wav"
    target.write_bytes(b"different bytes")
    rc = validate_mod.main(
        _common_validate_args(fixture_dirs, tmp_path) + ["--mark-validated"]
    )
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    bad_row = next(
        r for r in rows
        if r["example_id"] == "ex001" and r["degradation_id"] == "clean"
    )
    assert bad_row["validated_at"] is None
    ok_rows = [
        r for r in rows
        if not (r["example_id"] == "ex001" and r["degradation_id"] == "clean")
    ]
    assert ok_rows
    for row in ok_rows:
        assert row["validated_at"] is not None


def _common_invalidate_args(fixture_dirs: dict) -> list[str]:
    return ["--db", str(fixture_dirs["db"])]


def test_invalidate_refuses_without_filter(
    prewarm_mod, invalidate_mod, fixture_dirs, capsys
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    rc = invalidate_mod.main(_common_invalidate_args(fixture_dirs))
    assert rc == 1
    assert "filter is required" in capsys.readouterr().err
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    assert len(rows) == len(fixture_dirs["expected_pairs"])


def test_invalidate_dry_run_does_not_delete(
    prewarm_mod, invalidate_mod, fixture_dirs
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    rc = invalidate_mod.main(
        _common_invalidate_args(fixture_dirs)
        + ["--by-asr-provider", "whisper"]
    )
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    assert len(rows) == len(fixture_dirs["expected_pairs"])


def test_invalidate_apply_deletes_only_matching(
    prewarm_mod, invalidate_mod, fixture_dirs
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    rc = invalidate_mod.main(
        _common_invalidate_args(fixture_dirs)
        + ["--by-example-id", "ex001", "--apply"]
    )
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    pairs = {(r["example_id"], r["degradation_id"]) for r in rows}
    assert all(ex_id != "ex001" for ex_id, _ in pairs)
    assert ("ex003", "clean") in pairs


def test_invalidate_does_not_touch_artifact_files(
    prewarm_mod, invalidate_mod, fixture_dirs
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    rc = invalidate_mod.main(
        _common_invalidate_args(fixture_dirs)
        + ["--by-example-id", "ex001", "--apply"]
    )
    assert rc == 0
    assert (fixture_dirs["artifacts_root"] / "ex001" / "clean.wav").is_file()
    assert (fixture_dirs["artifacts_root"] / "ex001" / "phone_call.wav").is_file()


def test_invalidate_not_match_mode(
    prewarm_mod, invalidate_mod, fixture_dirs
):
    _prewarm_then(prewarm_mod, fixture_dirs)
    rc = invalidate_mod.main(
        _common_invalidate_args(fixture_dirs)
        + [
            "--by-degradation-version",
            versions.DEGRADATION_VERSION,
            "--mode",
            "not-match",
            "--apply",
        ]
    )
    assert rc == 0
    rows = persistence.list_cache_entries(fixture_dirs["db"])
    assert len(rows) == len(fixture_dirs["expected_pairs"])


def test_persistence_helpers_roundtrip(tmp_path):
    db_path = tmp_path / "demo.db"
    persistence.init_schema(db_path)
    payload_kwargs = dict(
        cache_key="ex|clean|x|whisper|tiny.en|bypass|1.0",
        example_id="ex",
        degradation_id="clean",
        degradation_version="x",
        asr_provider="whisper",
        asr_model_version="tiny.en",
        enhancer_version="bypass",
        metrics_version="1.0",
        result_json=json.dumps({"audio_path_relative": "ex/clean.wav"}),
        artifact_root=ARTIFACTS_ABS,
    )
    action = persistence.upsert_cache_entry(db_path, **payload_kwargs)
    assert action == "inserted"
    action = persistence.upsert_cache_entry(db_path, **payload_kwargs)
    assert action == "updated"
    rows = persistence.list_cache_entries(db_path)
    assert len(rows) == 1
    assert rows[0]["cache_key"] == payload_kwargs["cache_key"]
    assert rows[0]["validated_at"] is None
    persistence.mark_cache_entry_validated(db_path, payload_kwargs["cache_key"])
    rows = persistence.list_cache_entries(db_path)
    assert rows[0]["validated_at"] is not None
    matched, sample = persistence.delete_cache_entries(
        db_path,
        where_sql="example_id = ?",
        params=("ex",),
        dry_run=True,
    )
    assert matched == 1
    assert sample == [payload_kwargs["cache_key"]]
    assert len(persistence.list_cache_entries(db_path)) == 1
    matched, _ = persistence.delete_cache_entries(
        db_path,
        where_sql="example_id = ?",
        params=("ex",),
        dry_run=False,
    )
    assert matched == 1
    assert persistence.list_cache_entries(db_path) == []
    with pytest.raises(ValueError):
        persistence.delete_cache_entries(
            db_path, where_sql="   ", params=(), dry_run=True
        )
