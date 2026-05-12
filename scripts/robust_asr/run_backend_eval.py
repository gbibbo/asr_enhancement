#!/usr/bin/env python3
"""run_backend_eval.py — robust_asr §4.2 backend evaluation.

Reads the eval_manifests_v1.yaml; for each enabled manifest, evaluates
the requested backend on every row; writes one row per audio_id to the
canonical 31-column eval schema.

Halts cleanly with sentinel `MISSING_EVIDENCE` (exit 13) when CT2 INT8
weights for whisper_base_ct2_int8 are not present at any candidate
local path. No model bytes are downloaded; provenance is not invented.

Sentinel `OK_BACKEND_EVAL` on PASS, exit 0.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from libs.common.normalization import normalize_text  # noqa: E402
from libs.common import metrics as metrics_mod  # noqa: E402
from libs.common.versions import NORMALIZATION_VERSION  # noqa: E402

EVAL_COLUMNS = [
    "audio_id", "source_dataset", "source_split", "speaker_id", "utterance_id",
    "condition_family", "degradation_id", "degradation_params_json",
    "audio_path_or_uri", "audio_sha256", "reference_text", "reference_normalized",
    "backend_name", "backend_version", "backend_kind", "decode_config_json",
    "raw_transcript", "normalized_transcript", "normalization_version",
    "wer", "cer", "wa",
    "backend_latency_ms", "server_processing_latency_ms", "end_to_end_latency_ms",
    "ram_peak_mb", "cost_usd", "local_only", "third_party_provider",
    "error_or_null", "created_at_utc",
]


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(p))


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _decode_config_hash(d: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def probe_ct2_model(candidate_paths: List[str]) -> Optional[Path]:
    for raw in candidate_paths:
        c = _expand(raw)
        if not c.exists():
            continue
        if (c / "model.bin").exists() and (c / "config.json").exists():
            return c
        snaps = c / "snapshots"
        if snaps.exists():
            for s in snaps.iterdir():
                if (s / "model.bin").exists() and (s / "config.json").exists():
                    return s
    return None


def build_reference_index_from_librispeech(audio_paths: Iterable[str]) -> Dict[str, str]:
    """Resolve reference_text from LibriSpeech *.trans.txt files."""
    trans_files: set[Path] = set()
    for ap in audio_paths:
        p = Path(ap)
        # /…/LibriSpeech/<subset>/<spk>/<chap>/<spk>-<chap>-<utt>.flac
        if p.suffix.lower() == ".flac" and "LibriSpeech" in p.parts:
            try:
                spk, chap, _ = p.stem.split("-", 2)
            except ValueError:
                continue
            trans_files.add(p.parent / f"{spk}-{chap}.trans.txt")
    idx: Dict[str, str] = {}
    for tf in trans_files:
        if not tf.exists():
            continue
        for line in tf.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            key, _, text = line.partition(" ")
            idx[key] = text
    return idx


def load_manifests(cfg: Dict[str, Any], repo_root: Path) -> List[Tuple[str, str, pa.Table]]:
    out: List[Tuple[str, str, pa.Table]] = []
    for m in cfg["manifests"]:
        if not m.get("enabled", False):
            print(f"SKIP {m['name']}: enabled=false ({m.get('blocker', 'no_reason')})", flush=True)
            continue
        path = repo_root / m["path"]
        if not path.exists():
            print(f"FAIL: manifest missing: {path}", file=sys.stderr)
            sys.exit(1)
        out.append((m["name"], m["tier"], pq.read_table(path)))
    return out


def emit_eval_table(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    arrays: Dict[str, list] = {c: [] for c in EVAL_COLUMNS}
    for r in rows:
        for c in EVAL_COLUMNS:
            arrays[c].append(r.get(c))
    schema = pa.schema([
        (c, pa.float64() if c in {"wer", "cer", "wa", "backend_latency_ms",
                                   "server_processing_latency_ms",
                                   "end_to_end_latency_ms", "ram_peak_mb",
                                   "cost_usd"} else
            pa.bool_() if c == "local_only" else pa.string())
        for c in EVAL_COLUMNS
    ])
    table = pa.Table.from_pydict(arrays, schema=schema)
    pq.write_table(table, out_path)


def run(args: argparse.Namespace) -> int:
    repo_root = REPO_ROOT
    cfg = yaml.safe_load(Path(args.manifests).read_text())

    backend = args.backend
    backends = cfg.get("backend_endpoints", {})
    if backend not in backends:
        print(f"FAIL: backend not declared in eval_manifests: {backend}", file=sys.stderr)
        return 1
    bspec = backends[backend]

    if backend == "whisper_base_ct2_int8":
        model_dir = probe_ct2_model(bspec.get("candidate_local_paths", []))
        if model_dir is None:
            print(
                "MISSING_EVIDENCE: CT2 INT8 weights for whisper_base_ct2_int8 "
                "not found at any candidate_local_paths. Provenance is not "
                "invented; halting.",
                flush=True,
            )
            print(f"candidate_local_paths_searched={bspec.get('candidate_local_paths', [])}", flush=True)
            return 13
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            print(f"MISSING_EVIDENCE: faster_whisper unavailable: {e}", flush=True)
            return 13
        try:
            import faster_whisper as fw_mod
            backend_version = f"faster_whisper-{getattr(fw_mod, '__version__', 'unknown')}+ct2-int8+{model_dir.name}"
        except Exception:
            backend_version = f"faster_whisper+ct2-int8+{model_dir.name}"
        device = "cuda" if args.use_gpu else "cpu"
        model = WhisperModel(str(model_dir), device=device, compute_type="int8")
    else:
        print(f"FAIL: P2.1 implements only whisper_base_ct2_int8; got {backend}", file=sys.stderr)
        return 1

    decode_cfg = cfg.get("decode_defaults", {})
    decode_json = json.dumps(decode_cfg, sort_keys=True)
    decode_hash = _decode_config_hash(decode_cfg)

    manifests = load_manifests(cfg, repo_root)
    if not manifests:
        print("FAIL: no enabled manifests", file=sys.stderr)
        return 1

    all_audio_paths: List[str] = []
    for _, _, t in manifests:
        all_audio_paths.extend(t.column("audio_path_or_uri").to_pylist())
    ref_index = build_reference_index_from_librispeech(all_audio_paths)
    print(f"reference_index_size={len(ref_index)}", flush=True)
    if not ref_index:
        print("FAIL: no reference_text resolvable from LibriSpeech .trans.txt", file=sys.stderr)
        return 1

    out_rows: List[Dict[str, Any]] = []
    seen_pk: set[Tuple[str, str, str]] = set()
    transcription_cache: Dict[str, Dict[str, Any]] = {}

    n_total = sum(t.num_rows for _, _, t in manifests)
    n_done = 0
    n_decoded = 0
    n_cached = 0
    t_start = time.time()
    for mname, tier, table in manifests:
        cols = {c: table.column(c).to_pylist() for c in table.column_names}
        for i in range(table.num_rows):
            source_audio_id = cols["audio_id"][i]
            audio_path = cols["audio_path_or_uri"][i]
            audio_sha256 = cols["audio_sha256"][i]
            speaker_id = cols["speaker_id"][i]
            utterance_id = cols["utterance_id"][i]
            condition_family = cols["condition_family"][i]
            degradation_id = cols["degradation_id"][i]
            source_dataset = cols["source_dataset"][i]
            source_split = cols["source_split"][i]
            # Eval-table audio_id encodes degradation so each
            # (source x condition_family x tier) combination is a unique
            # scoreable row per Section 3 PK rule.
            eval_audio_id = f"{source_audio_id}::{degradation_id}"
            params = {
                "tier": tier,
                "snr_db": cols.get("snr_db", [None] * table.num_rows)[i],
                "rir_id_or_null": cols.get("rir_id_or_null", [None] * table.num_rows)[i],
                "filter_params_json": cols.get("filter_params_json", ["{}"] * table.num_rows)[i],
                "random_seed": cols.get("random_seed", [None] * table.num_rows)[i],
            }
            params_json = json.dumps(params, sort_keys=True, default=str)

            ref_text = ref_index.get(utterance_id, "")
            ref_norm = normalize_text(ref_text)

            pk = (eval_audio_id, backend, decode_hash)
            if pk in seen_pk:
                continue
            seen_pk.add(pk)

            row: Dict[str, Any] = {
                "audio_id": eval_audio_id,
                "source_dataset": source_dataset,
                "source_split": source_split,
                "speaker_id": speaker_id,
                "utterance_id": utterance_id,
                "condition_family": condition_family,
                "degradation_id": degradation_id,
                "degradation_params_json": params_json,
                "audio_path_or_uri": audio_path,
                "audio_sha256": audio_sha256,
                "reference_text": ref_text,
                "reference_normalized": ref_norm,
                "backend_name": backend,
                "backend_version": backend_version,
                "backend_kind": bspec.get("backend_kind", "local_asr"),
                "decode_config_json": decode_json,
                "raw_transcript": None,
                "normalized_transcript": None,
                "normalization_version": NORMALIZATION_VERSION,
                "wer": None, "cer": None, "wa": None,
                "backend_latency_ms": None,
                "server_processing_latency_ms": None,
                "end_to_end_latency_ms": None,
                "ram_peak_mb": None,
                "cost_usd": None,
                "local_only": bool(bspec.get("local_only", True)),
                "third_party_provider": bspec.get("third_party_provider"),
                "error_or_null": None,
                "created_at_utc": _utc(),
            }
            try:
                if audio_sha256 in transcription_cache:
                    cached = transcription_cache[audio_sha256]
                    raw = cached["raw"]
                    lat_ms = cached["lat_ms"]
                    n_cached += 1
                else:
                    t0 = time.time()
                    segments, info = model.transcribe(
                        audio_path,
                        language=decode_cfg.get("language", "en"),
                        task=decode_cfg.get("task", "transcribe"),
                        beam_size=int(decode_cfg.get("beam_size", 5)),
                        best_of=int(decode_cfg.get("best_of", 5)),
                        temperature=float(decode_cfg.get("temperature", 0.0)),
                        condition_on_previous_text=bool(decode_cfg.get("condition_on_previous_text", False)),
                        vad_filter=bool(decode_cfg.get("vad_filter", False)),
                        word_timestamps=bool(decode_cfg.get("word_timestamps", False)),
                    )
                    segs = list(segments)
                    t1 = time.time()
                    raw = " ".join(s.text for s in segs).strip()
                    lat_ms = (t1 - t0) * 1000.0
                    transcription_cache[audio_sha256] = {"raw": raw, "lat_ms": lat_ms}
                    n_decoded += 1
                hyp_norm = normalize_text(raw)
                row["raw_transcript"] = raw
                row["normalized_transcript"] = hyp_norm
                row["wer"] = float(metrics_mod.wer(ref_norm, hyp_norm))
                row["cer"] = float(metrics_mod.cer(ref_norm, hyp_norm))
                row["wa"] = float(metrics_mod.wa(ref_norm, hyp_norm))
                row["backend_latency_ms"] = lat_ms
                row["end_to_end_latency_ms"] = lat_ms
                row["server_processing_latency_ms"] = 0.0
                row["ram_peak_mb"] = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)
            except Exception as e:  # noqa: BLE001
                row["error_or_null"] = f"{type(e).__name__}: {e}"
            out_rows.append(row)
            n_done += 1
            if n_done % 1000 == 0:
                elapsed = time.time() - t_start
                print(f"progress {n_done}/{n_total} decoded={n_decoded} cached={n_cached} elapsed={elapsed:.1f}s", flush=True)

    out_path = Path(args.out)
    emit_eval_table(out_rows, out_path)
    print(f"rows_written={len(out_rows)} out={out_path}", flush=True)
    print("OK_BACKEND_EVAL", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True)
    ap.add_argument("--manifests", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--use-gpu", action="store_true")
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
