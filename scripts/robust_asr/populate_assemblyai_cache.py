#!/usr/bin/env python3
"""populate_assemblyai_cache.py — robust_asr §4.5 cache populator.

Submits every audio_id in the eval manifests to AssemblyAI exactly once
and stores the response JSON keyed by audio_sha256. Cache is
resume-safe: existing <audio_sha256>.json entries are skipped.

Paid-API guard (Section 5.7 and Section 5.10 BUDGET_EXCEEDED):
  1. If ASSEMBLYAI_API_KEY is unset → exit 8 (KEY_UNSET); no requests.
  2. If pricing_v1.yaml's assemblyai_pricing_checked_date is older than
     90 days from today → exit 12 (PENDING_PRICING_VERIFICATION);
     no requests.
  3. Before any upload, compute and print a pre-spend summary using
     duration_s from the enabled manifests and pricing_v1.yaml's
     unit_price_usd_per_audio_second. If the estimate exceeds
     max_total_cost_usd → exit 11 (BUDGET_EXCEEDED); no requests.
  4. Running cost is tracked in cache_summary.json; populate halts when
     running cost would exceed max_total_cost_usd.
  5. ASSEMBLYAI_API_KEY is never logged or written to disk.

Stdout (PASS only):  OK_ASSEMBLYAI_CACHE <cached>/<requested>
Exit codes:
   0 success
   1 generic failure (validation/IO)
   8 ASSEMBLYAI_API_KEY_UNSET
   9 ASSEMBLYAI_AUTH_FAIL          (HTTP 401/403)
  10 ASSEMBLYAI_QUOTA              (HTTP 429 after retries)
  11 BUDGET_EXCEEDED               (estimated or running cost > cap)
  12 PENDING_PRICING_VERIFICATION  (pricing checked_date too old)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import yaml
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSEMBLYAI_API_BASE = "https://api.assemblyai.com/v2"
PRICING_CHECKED_MAX_AGE_DAYS = 90

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_KEY_UNSET = 8
EXIT_AUTH = 9
EXIT_QUOTA = 10
EXIT_BUDGET = 11
EXIT_PRICING_STALE = 12


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


REQUIRED_PRICING_FIELDS = (
    "assemblyai_pricing_checked_date",
    "pricing_source_url",
    "billing_unit",
    "unit_price_usd_per_audio_second",
    "max_total_cost_usd",
    "http_5xx_partial_threshold_pct",
    "http_429_max_retries",
    "http_5xx_max_retries",
    "request_timeout_seconds",
)


def validate_pricing(pricing: dict) -> list[str]:
    missing = [f for f in REQUIRED_PRICING_FIELDS if f not in pricing]
    return missing


def pricing_is_fresh(pricing: dict, today: date | None = None) -> bool:
    today = today or date.today()
    checked = pricing.get("assemblyai_pricing_checked_date")
    if not checked:
        return False
    try:
        ts = date.fromisoformat(str(checked))
    except Exception:
        return False
    return (today - ts).days <= PRICING_CHECKED_MAX_AGE_DAYS


def collect_enabled_audio(manifests_doc: dict,
                          repo_root: Path = REPO_ROOT) -> list[dict]:
    rows: list[dict] = []
    seen_sha = set()
    for m in manifests_doc.get("manifests", []):
        if not m.get("enabled", True):
            continue
        path = repo_root / m["path"]
        if not path.exists():
            continue
        t = pq.read_table(path,
                          columns=["audio_id", "audio_sha256",
                                   "audio_path_or_uri", "duration_s",
                                   "bad_output"])
        bad = t.column("bad_output").to_pylist()
        ids = t.column("audio_id").to_pylist()
        shas = t.column("audio_sha256").to_pylist()
        paths = t.column("audio_path_or_uri").to_pylist()
        durs = t.column("duration_s").to_pylist()
        for i in range(t.num_rows):
            if bad[i]:
                continue
            sha = shas[i]
            if sha in seen_sha:
                continue
            seen_sha.add(sha)
            rows.append({"audio_id": ids[i],
                         "audio_sha256": sha,
                         "audio_path_or_uri": paths[i],
                         "duration_s": float(durs[i])})
    return rows


def estimate_cost(rows: list[dict], pricing: dict) -> float:
    unit = float(pricing["unit_price_usd_per_audio_second"])
    total_seconds = sum(r["duration_s"] for r in rows)
    return total_seconds * unit


def _upload(session, file_path: Path, key: str, timeout_s: float) -> tuple[int, str | None]:
    with file_path.open("rb") as fh:
        r = session.post(f"{ASSEMBLYAI_API_BASE}/upload",
                         headers={"authorization": key},
                         data=fh, timeout=timeout_s)
    if r.status_code != 200:
        return r.status_code, None
    return 200, r.json().get("upload_url")


def _request_transcript(session, upload_url: str, key: str,
                        timeout_s: float) -> tuple[int, str | None]:
    payload = {"audio_url": upload_url, "language_code": "en"}
    r = session.post(f"{ASSEMBLYAI_API_BASE}/transcript",
                     headers={"authorization": key,
                              "content-type": "application/json"},
                     json=payload, timeout=timeout_s)
    if r.status_code != 200:
        return r.status_code, None
    return 200, r.json().get("id")


def _poll_transcript(session, transcript_id: str, key: str,
                     timeout_s: float, poll_every_s: float = 2.0,
                     max_wait_s: float = 600.0) -> tuple[int, dict | None]:
    deadline = time.monotonic() + max_wait_s
    url = f"{ASSEMBLYAI_API_BASE}/transcript/{transcript_id}"
    while True:
        r = session.get(url, headers={"authorization": key},
                        timeout=timeout_s)
        if r.status_code != 200:
            return r.status_code, None
        data = r.json()
        status = data.get("status")
        if status == "completed":
            return 200, data
        if status == "error":
            return 200, data
        if time.monotonic() > deadline:
            return 0, None
        time.sleep(poll_every_s)


def write_cache_summary(cache_dir: Path, summary: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "cache_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")


def populate(rows: list[dict], pricing: dict, cache_dir: Path,
             key: str, session=None) -> tuple[int, dict]:
    import requests  # type: ignore[import-not-found]
    session = session or requests.Session()
    unit = float(pricing["unit_price_usd_per_audio_second"])
    max_cap = float(pricing["max_total_cost_usd"])
    timeout_s = float(pricing.get("request_timeout_seconds", 60.0))
    max_429 = int(pricing.get("http_429_max_retries", 5))
    max_5xx = int(pricing.get("http_5xx_max_retries", 1))

    cache_dir.mkdir(parents=True, exist_ok=True)
    requested = 0
    cached = 0
    failures = []
    running_cost = 0.0
    started_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        requested += 1
        out_path = cache_dir / f"{row['audio_sha256']}.json"
        if out_path.exists():
            cached += 1
            continue
        if running_cost + row["duration_s"] * unit > max_cap:
            summary = _build_summary(rows, requested, cached, failures,
                                     running_cost, started_at, "BUDGET_EXCEEDED")
            write_cache_summary(cache_dir, summary)
            return EXIT_BUDGET, summary
        audio_path = Path(row["audio_path_or_uri"])
        if not audio_path.exists():
            failures.append({"audio_sha256": row["audio_sha256"],
                             "reason": "audio_missing"})
            continue
        upload_url, code = None, 0
        for attempt in range(max_429 + 1):
            code, upload_url = _upload(session, audio_path, key, timeout_s)
            if code == 200:
                break
            if code in (401, 403):
                return EXIT_AUTH, _build_summary(rows, requested, cached,
                                                 failures, running_cost,
                                                 started_at, "AUTH_FAIL")
            if code == 429:
                time.sleep(min(60, 2 ** attempt))
                continue
            if 500 <= code < 600:
                if attempt < max_5xx:
                    time.sleep(60)
                    continue
                failures.append({"audio_sha256": row["audio_sha256"],
                                 "reason": f"upload_http_{code}"})
                break
            failures.append({"audio_sha256": row["audio_sha256"],
                             "reason": f"upload_http_{code}"})
            break
        if code == 429:
            return EXIT_QUOTA, _build_summary(rows, requested, cached,
                                              failures, running_cost,
                                              started_at, "QUOTA")
        if code != 200 or not upload_url:
            continue
        code, transcript_id = _request_transcript(session, upload_url,
                                                  key, timeout_s)
        if code in (401, 403):
            return EXIT_AUTH, _build_summary(rows, requested, cached,
                                             failures, running_cost,
                                             started_at, "AUTH_FAIL")
        if code != 200 or not transcript_id:
            failures.append({"audio_sha256": row["audio_sha256"],
                             "reason": f"request_http_{code}"})
            continue
        code, data = _poll_transcript(session, transcript_id, key, timeout_s)
        if code != 200 or not data:
            failures.append({"audio_sha256": row["audio_sha256"],
                             "reason": f"poll_http_{code}"})
            continue
        cost = row["duration_s"] * unit
        running_cost += cost
        out_path.write_text(json.dumps({
            "audio_sha256": row["audio_sha256"],
            "audio_id": row["audio_id"],
            "duration_s": row["duration_s"],
            "cost_usd": cost,
            "assemblyai": {k: v for k, v in data.items()
                           if k != "audio_url"},
        }, indent=2, sort_keys=True), encoding="utf-8")
        cached += 1
    failure_rate = len(failures) / max(1, requested) * 100.0
    threshold = float(pricing.get("http_5xx_partial_threshold_pct", 1.0))
    outcome = "PASS" if failure_rate <= threshold else "PARTIAL"
    summary = _build_summary(rows, requested, cached, failures,
                             running_cost, started_at, outcome)
    write_cache_summary(cache_dir, summary)
    return EXIT_OK, summary


def _build_summary(rows: list[dict], requested: int, cached: int,
                   failures: list[dict], running_cost: float,
                   started_at: str, outcome: str) -> dict:
    return {
        "outcome": outcome,
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested": requested,
        "cached": cached,
        "missing": len(failures),
        "running_cost_usd": running_cost,
        "estimated_total_seconds": sum(r["duration_s"] for r in rows),
        "missing_audio_sha256": [f["audio_sha256"] for f in failures],
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--pricing-config", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute and print pre-spend summary only; no requests.")
    args = ap.parse_args(argv)

    cache_dir = Path(args.cache_dir)
    pricing_path = Path(args.pricing_config)
    manifests_path = Path(args.manifests)

    if not pricing_path.exists():
        print(f"FAIL: pricing config not found: {pricing_path}", file=sys.stderr)
        return EXIT_FAIL
    if not manifests_path.exists():
        print(f"FAIL: manifests config not found: {manifests_path}", file=sys.stderr)
        return EXIT_FAIL

    pricing = _load_yaml(pricing_path)
    missing = validate_pricing(pricing)
    if missing:
        print(f"FAIL: pricing config missing fields: {missing}", file=sys.stderr)
        return EXIT_FAIL
    if not pricing_is_fresh(pricing):
        print("PENDING_PRICING_VERIFICATION", file=sys.stderr)
        return EXIT_PRICING_STALE

    key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not key:
        print("ASSEMBLYAI_API_KEY_UNSET", file=sys.stderr)
        return EXIT_KEY_UNSET

    manifests_doc = _load_yaml(manifests_path)
    rows = collect_enabled_audio(manifests_doc)
    est_cost = estimate_cost(rows, pricing)
    cap = float(pricing["max_total_cost_usd"])
    total_s = sum(r["duration_s"] for r in rows)
    print("PRE_SPEND_SUMMARY",
          f"audio_ids={len(rows)}",
          f"total_seconds={total_s:.1f}",
          f"unit_price_usd={pricing['unit_price_usd_per_audio_second']}",
          f"estimated_cost_usd={est_cost:.4f}",
          f"max_total_cost_usd={cap:.4f}")
    if est_cost > cap:
        print("BUDGET_EXCEEDED", file=sys.stderr)
        return EXIT_BUDGET
    if args.dry_run:
        return EXIT_OK
    rc, summary = populate(rows, pricing, cache_dir, key)
    if rc == EXIT_OK:
        print(f"OK_ASSEMBLYAI_CACHE {summary['cached']}/{summary['requested']}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
