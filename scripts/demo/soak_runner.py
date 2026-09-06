#!/usr/bin/env python3
"""B13.1 soak runner for the ASR Enhancement public demo.

Stdlib-only. No imports from libs.* or services.*. Run as a host-side
long-lived process. See ``docs/setup/rp5_soak.md`` for the operator runbook.

The runner schedules three streams against the local demo API:

* every 15 min  -- one cached ``/demo/run-cached`` call;
* every  6 h    -- one forced-recomputation upload of a curated clean WAV;
* every  2 h    -- one synthetic 10 s upload.

It writes JSONL artefacts under ``--out`` (typically ``runs/soak_<TS>/``).
Privacy: no transcripts, ground truth, titles, raw result payloads, headers,
credentials, session IDs, or upload filenames beyond synthetic basenames are
ever persisted.
"""
from __future__ import annotations

import argparse
import array
import datetime
import json
import os
import pathlib
import random
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import wave

CACHED_INTERVAL_S = 15 * 60
RECOMPUTE_INTERVAL_S = 6 * 3600
UPLOAD_INTERVAL_S = 2 * 3600
METRIC_INTERVAL_S = 60
JOB_POLL_INTERVAL_S = 5
JOB_POLL_TIMEOUT_S = 300
HTTP_TIMEOUT_S = 30

WHISPER_PROVIDER = "whisper"
BYPASS_ENHANCER = "bypass"

API_CONTAINER_NAME = "asr-demo-demo-api-1"
WORKER_CONTAINER_NAME = "asr-demo-demo-worker-1"


_log_path: pathlib.Path | None = None
_shutdown = False


def _utc_now_iso() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _log(level: str, event: str, **fields) -> None:
    record = {"ts": _utc_now_iso(), "level": level, "event": event}
    record.update(fields)
    line = json.dumps(record, separators=(",", ":"), default=str)
    print(line, flush=True)
    if _log_path is not None:
        try:
            with _log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass


def log_info(event: str, **fields) -> None:
    _log("info", event, **fields)


def log_warn(event: str, **fields) -> None:
    _log("warn", event, **fields)


def log_error(event: str, **fields) -> None:
    _log("error", event, **fields)


def http_get_json(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            return exc.code, {}
    except Exception as exc:
        raise RuntimeError(type(exc).__name__) from exc


def http_post_json(url: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            return exc.code, {}
    except Exception as exc:
        raise RuntimeError(type(exc).__name__) from exc


def http_get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return resp.read()
    except Exception as exc:
        raise RuntimeError(type(exc).__name__) from exc


def http_post_multipart(
    url: str,
    fields: dict,
    file_field: str,
    file_name: str,
    file_bytes: bytes,
) -> tuple[int, dict]:
    boundary = "soak_boundary_" + uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n'
                f"\r\n{value}\r\n"
            ).encode("utf-8")
        )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{file_name}"\r\n'
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode("utf-8")
        + file_bytes
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            return exc.code, {}
    except Exception as exc:
        raise RuntimeError(type(exc).__name__) from exc


def make_synthetic_wav(
    path: pathlib.Path, duration_s: int = 10, sample_rate: int = 16000
) -> None:
    """Write a mono 16-bit PCM WAV with low-amplitude white noise."""
    n_samples = duration_s * sample_rate
    samples = array.array(
        "h", (random.randint(-1000, 1000) for _ in range(n_samples))
    )
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


def db_count_active_jobs(db_path: pathlib.Path) -> int:
    try:
        with sqlite3.connect(
            f"file:{db_path}?mode=ro", uri=True, timeout=5
        ) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status IN ('queued','running')"
            ).fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return -1


def db_count_failed_jobs(db_path: pathlib.Path) -> int:
    try:
        with sqlite3.connect(
            f"file:{db_path}?mode=ro", uri=True, timeout=5
        ) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status='failed'"
            ).fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return -1


_MEM_UNITS = (
    ("GiB", 1024.0),
    ("MiB", 1.0),
    ("KiB", 1.0 / 1024),
    ("GB", 1000.0 * 1000.0 * 1000.0 / 1048576.0),
    ("MB", 1000.0 * 1000.0 / 1048576.0),
    ("KB", 1000.0 / 1048576.0),
    ("B", 1.0 / 1048576.0),
)


def _parse_mem_mib(mem_usage: str) -> float | None:
    """Parse a docker-stats MemUsage string like '123.4MiB / 7.9GiB'."""
    if not mem_usage:
        return None
    used = mem_usage.split("/", 1)[0].strip()
    for unit, mult in _MEM_UNITS:
        if used.endswith(unit):
            num = used[: -len(unit)].strip()
            try:
                return float(num) * mult
            except ValueError:
                return None
    return None


def docker_mem_mib(container_name: str) -> float | None:
    try:
        result = subprocess.run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{.Name}}\t{{.MemUsage}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        for line in result.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2 and parts[0].strip() == container_name:
                return _parse_mem_mib(parts[1].strip())
    except Exception:
        pass
    return None


def read_cpu_temp_c() -> float | None:
    try:
        raw = pathlib.Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()
        return round(int(raw) / 1000.0, 2)
    except Exception:
        return None


def read_disk_usage(runtime_root: pathlib.Path) -> tuple[float | None, int | None, int | None]:
    """Return ``(used_percent, free_bytes, total_bytes)``. Path is never logged."""
    try:
        usage = shutil.disk_usage(str(runtime_root))
        pct = (usage.used / usage.total * 100.0) if usage.total else 0.0
        return round(pct, 2), int(usage.free), int(usage.total)
    except Exception:
        return None, None, None


def read_log_sizes(logs_dir: pathlib.Path) -> dict:
    """Return ``{basename: size_bytes}`` for files in ``logs_dir`` (basenames only)."""
    out: dict = {}
    try:
        for entry in logs_dir.iterdir():
            if entry.is_file():
                try:
                    out[entry.name] = int(entry.stat().st_size)
                except OSError:
                    pass
    except Exception:
        pass
    return out


def write_jsonl(path: pathlib.Path, record: dict) -> None:
    line = json.dumps(record, separators=(",", ":"), default=str)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def compute_p95(values) -> float:
    """Return the 95th-percentile value (nearest-rank). Empty list returns nan."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0:
        return float("nan")
    idx = max(0, min(n - 1, int(round(0.95 * n)) - 1))
    return float(sorted_vals[idx])


def discover_cache_hit_pairs(target_url: str) -> list:
    """Probe every (example_id, degradation_id) pair; keep only cache_hit ones.

    Exits with code 1 if no pairs return cache_hit. Result objects are not
    persisted; only example_id/degradation_id pairs are returned.
    """
    log_info("discover.start", target_url=target_url)
    code, data = http_get_json(f"{target_url}/demo/examples")
    if code != 200:
        log_error("discover.examples_failed", http_status=code)
        sys.exit(1)
    examples = data.get("examples", [])
    if not examples:
        log_error("discover.no_examples")
        sys.exit(1)

    pairs: list = []
    for ex in examples:
        eid = ex.get("example_id", "")
        for did in ex.get("degradation_ids", []):
            t0 = time.monotonic()
            try:
                code, resp = http_post_json(
                    f"{target_url}/demo/run-cached",
                    {
                        "example_id": eid,
                        "degradation_id": did,
                        "provider": WHISPER_PROVIDER,
                        "enhancer_version": BYPASS_ENHANCER,
                    },
                )
                error_class = None
            except RuntimeError as exc:
                code, resp = -1, {}
                error_class = str(exc)
            latency_ms = int((time.monotonic() - t0) * 1000)
            status = resp.get("status", "")
            log_info(
                "discover.probe",
                example_id=eid,
                degradation_id=did,
                http_status=code,
                latency_ms=latency_ms,
                status=status,
                error_class=error_class,
            )
            if code == 200 and status == "cache_hit":
                pairs.append({"example_id": eid, "degradation_id": did})

    if not pairs:
        log_error("discover.no_cache_hit_pairs", probed_examples=len(examples))
        sys.exit(1)

    log_info("discover.done", cache_hit_pairs=len(pairs))
    return pairs


def measure_baseline(target_url: str, pairs: list, n_samples: int = 30) -> dict:
    """Collect ``n_samples`` cache-hit calls and return P50/P95 stats."""
    log_info("baseline.start", n_samples=n_samples, pair_count=len(pairs))
    latencies: list = []
    misses = 0
    for i in range(n_samples):
        pair = random.choice(pairs)
        t0 = time.monotonic()
        try:
            code, resp = http_post_json(
                f"{target_url}/demo/run-cached",
                {
                    "example_id": pair["example_id"],
                    "degradation_id": pair["degradation_id"],
                    "provider": WHISPER_PROVIDER,
                    "enhancer_version": BYPASS_ENHANCER,
                },
            )
        except RuntimeError as exc:
            log_warn("baseline.error", iteration=i, error_class=str(exc))
            continue
        latency_ms = (time.monotonic() - t0) * 1000.0
        if code == 200 and resp.get("status") == "cache_hit":
            latencies.append(latency_ms)
        else:
            misses += 1
            log_warn(
                "baseline.miss",
                iteration=i,
                http_status=code,
                status=resp.get("status"),
            )
        time.sleep(0.5)

    if not latencies:
        log_error("baseline.no_valid_samples")
        sys.exit(1)

    sorted_lats = sorted(latencies)
    n = len(sorted_lats)
    return {
        "n_samples": n,
        "n_requested": n_samples,
        "n_misses": misses,
        "p50_ms": round(sorted_lats[max(0, int(round(0.50 * n)) - 1)], 1),
        "p95_ms": round(compute_p95(sorted_lats), 1),
        "min_ms": round(sorted_lats[0], 1),
        "max_ms": round(sorted_lats[-1], 1),
    }


def run_cached_job(target_url: str, pairs: list, cached_path: pathlib.Path) -> None:
    """Run one cached-path call and append a redacted record."""
    pair = random.choice(pairs)
    t0 = time.monotonic()
    error_class = None
    try:
        code, resp = http_post_json(
            f"{target_url}/demo/run-cached",
            {
                "example_id": pair["example_id"],
                "degradation_id": pair["degradation_id"],
                "provider": WHISPER_PROVIDER,
                "enhancer_version": BYPASS_ENHANCER,
            },
        )
    except RuntimeError as exc:
        code, resp = -1, {}
        error_class = str(exc)
    latency_ms = int((time.monotonic() - t0) * 1000)
    status = resp.get("status", "")
    write_jsonl(
        cached_path,
        {
            "ts": _utc_now_iso(),
            "example_id": pair["example_id"],
            "degradation_id": pair["degradation_id"],
            "http_status": code,
            "latency_ms": latency_ms,
            "status": status,
            "error_class": error_class,
        },
    )
    log_info(
        "cached.done",
        http_status=code,
        latency_ms=latency_ms,
        status=status,
        error_class=error_class,
    )


def _poll_job(target_url: str, job_id: str) -> str:
    """Poll ``/demo/jobs/{id}`` until terminal. Returns terminal status string."""
    deadline = time.monotonic() + JOB_POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        if _shutdown:
            return "interrupted"
        try:
            code, resp = http_get_json(f"{target_url}/demo/jobs/{job_id}")
            status = resp.get("status", "")
            if status in ("completed", "failed"):
                return status
        except RuntimeError:
            pass
        time.sleep(JOB_POLL_INTERVAL_S)
    return "timeout"


def run_recompute_job(
    target_url: str,
    pairs: list,
    tmp_dir: pathlib.Path,
    jobs_path: pathlib.Path,
) -> None:
    """Force a recompute by uploading a curated clean WAV via Whisper."""
    pair = random.choice(pairs)
    eid = pair["example_id"]
    did = pair["degradation_id"]
    log_info("recompute.start", example_id=eid, degradation_id=did)

    try:
        wav_bytes = http_get_bytes(f"{target_url}/demo/examples/{eid}/audio/clean")
    except RuntimeError as exc:
        log_error("recompute.fetch_failed", error_class=str(exc))
        write_jsonl(jobs_path, {
            "ts": _utc_now_iso(),
            "stream": "recompute",
            "example_id": eid,
            "degradation_id": did,
            "http_status": -1,
            "latency_ms_submit": -1,
            "job_id": None,
            "terminal_status": "fetch_failed",
            "terminal_latency_ms": None,
            "error_class": str(exc),
        })
        return

    tmp_basename = f"recompute_{uuid.uuid4().hex}.wav"
    tmp_wav = tmp_dir / tmp_basename
    try:
        tmp_wav.write_bytes(wav_bytes)
    except OSError as exc:
        log_error("recompute.tmp_write_failed", error_class=type(exc).__name__)
        return

    t0 = time.monotonic()
    error_class: str | None = None
    try:
        code, resp = http_post_multipart(
            f"{target_url}/demo/upload",
            fields={"provider": WHISPER_PROVIDER, "degradation_id": did},
            file_field="file",
            file_name=tmp_basename,
            file_bytes=wav_bytes,
        )
    except RuntimeError as exc:
        code, resp = -1, {}
        error_class = str(exc)
    submit_ms = int((time.monotonic() - t0) * 1000)

    job_id = resp.get("job_id")
    if code not in (200, 202) or not job_id:
        try:
            tmp_wav.unlink(missing_ok=True)
        except Exception:
            pass
        write_jsonl(jobs_path, {
            "ts": _utc_now_iso(),
            "stream": "recompute",
            "example_id": eid,
            "degradation_id": did,
            "http_status": code,
            "latency_ms_submit": submit_ms,
            "job_id": None,
            "terminal_status": "submit_failed",
            "terminal_latency_ms": None,
            "error_class": error_class,
        })
        log_warn("recompute.submit_failed", http_status=code, error_class=error_class)
        return

    t1 = time.monotonic()
    terminal_status = _poll_job(target_url, job_id)
    terminal_ms = int((time.monotonic() - t1) * 1000)

    try:
        tmp_wav.unlink(missing_ok=True)
    except Exception:
        pass

    write_jsonl(jobs_path, {
        "ts": _utc_now_iso(),
        "stream": "recompute",
        "example_id": eid,
        "degradation_id": did,
        "http_status": code,
        "latency_ms_submit": submit_ms,
        "job_id": job_id,
        "terminal_status": terminal_status,
        "terminal_latency_ms": terminal_ms,
        "error_class": None,
    })
    log_info(
        "recompute.done",
        terminal_status=terminal_status,
        submit_ms=submit_ms,
        terminal_ms=terminal_ms,
    )


def run_synthetic_upload(
    target_url: str,
    tmp_dir: pathlib.Path,
    jobs_path: pathlib.Path,
) -> None:
    """Generate a 10 s synthetic WAV, upload it, poll to terminal, delete."""
    tmp_basename = f"synth_{uuid.uuid4().hex}.wav"
    tmp_wav = tmp_dir / tmp_basename
    log_info("synthetic.start")
    try:
        make_synthetic_wav(tmp_wav, duration_s=10, sample_rate=16000)
        wav_bytes = tmp_wav.read_bytes()
    except Exception as exc:
        log_error("synthetic.gen_failed", error_class=type(exc).__name__)
        return

    t0 = time.monotonic()
    error_class: str | None = None
    try:
        code, resp = http_post_multipart(
            f"{target_url}/demo/upload",
            fields={"provider": WHISPER_PROVIDER},
            file_field="file",
            file_name=tmp_basename,
            file_bytes=wav_bytes,
        )
    except RuntimeError as exc:
        code, resp = -1, {}
        error_class = str(exc)
    submit_ms = int((time.monotonic() - t0) * 1000)

    job_id = resp.get("job_id")
    if code not in (200, 202) or not job_id:
        try:
            tmp_wav.unlink(missing_ok=True)
        except Exception:
            pass
        write_jsonl(jobs_path, {
            "ts": _utc_now_iso(),
            "stream": "synthetic_upload",
            "http_status": code,
            "latency_ms_submit": submit_ms,
            "job_id": None,
            "terminal_status": "submit_failed",
            "terminal_latency_ms": None,
            "error_class": error_class,
        })
        log_warn("synthetic.submit_failed", http_status=code, error_class=error_class)
        return

    t1 = time.monotonic()
    terminal_status = _poll_job(target_url, job_id)
    terminal_ms = int((time.monotonic() - t1) * 1000)

    try:
        tmp_wav.unlink(missing_ok=True)
    except Exception:
        pass

    write_jsonl(jobs_path, {
        "ts": _utc_now_iso(),
        "stream": "synthetic_upload",
        "http_status": code,
        "latency_ms_submit": submit_ms,
        "job_id": job_id,
        "terminal_status": terminal_status,
        "terminal_latency_ms": terminal_ms,
        "error_class": None,
    })
    log_info(
        "synthetic.done",
        terminal_status=terminal_status,
        submit_ms=submit_ms,
        terminal_ms=terminal_ms,
    )


def collect_metrics(
    target_url: str,
    db_path: pathlib.Path,
    runtime_root: pathlib.Path,
    metrics_path: pathlib.Path,
) -> None:
    ts = _utc_now_iso()

    t0 = time.monotonic()
    try:
        hcode, hdata = http_get_json(f"{target_url}/demo/health")
    except RuntimeError:
        hcode, hdata = -1, {}
    health_latency_ms = int((time.monotonic() - t0) * 1000)

    t0 = time.monotonic()
    try:
        ecode, _ = http_get_json(f"{target_url}/demo/examples")
    except RuntimeError:
        ecode = -1
    examples_latency_ms = int((time.monotonic() - t0) * 1000)

    cpu_temp_c = read_cpu_temp_c()
    disk_used_pct, disk_free_bytes, disk_total_bytes = read_disk_usage(runtime_root)
    api_mem = docker_mem_mib(API_CONTAINER_NAME)
    worker_mem = docker_mem_mib(WORKER_CONTAINER_NAME)
    log_sizes = read_log_sizes(runtime_root / "logs")
    db_active = db_count_active_jobs(db_path)
    db_failed = db_count_failed_jobs(db_path)

    record = {
        "ts": ts,
        "health_http_status": hcode,
        "health_latency_ms": health_latency_ms,
        "health_status": hdata.get("status"),
        "health_db_ok": hdata.get("db_ok"),
        "health_queue_depth": hdata.get("queue_depth", -1),
        "examples_http_status": ecode,
        "examples_latency_ms": examples_latency_ms,
        "cpu_temp_c": cpu_temp_c,
        "disk_used_pct": disk_used_pct,
        "disk_free_bytes": disk_free_bytes,
        "disk_total_bytes": disk_total_bytes,
        "docker_api_mem_mib": round(api_mem, 1) if api_mem is not None else None,
        "docker_worker_mem_mib": round(worker_mem, 1) if worker_mem is not None else None,
        "log_sizes": log_sizes,
        "db_active_jobs": db_active,
        "db_failed_jobs": db_failed,
    }
    write_jsonl(metrics_path, record)


def write_state(
    run_dir: pathlib.Path,
    pid: int,
    start_utc: str,
    duration_h: float,
    target_url: str,
) -> None:
    branch = "unknown"
    head = "unknown"
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=10
        ).strip()
    except Exception:
        pass
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
    except Exception:
        pass
    state = {
        "run_dir": str(run_dir),
        "pid": pid,
        "start_time_utc": start_utc,
        "requested_duration_hours": duration_h,
        "target_url": target_url,
        "branch": branch,
        "head_commit": head,
    }
    (run_dir / "state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )


def _on_signal(signum, frame) -> None:
    global _shutdown
    log_info("runner.signal_received", signal=int(signum))
    _shutdown = True


def _parse_duration(s: str) -> float:
    """Parse a duration string into hours. Accepts ``Nh`` or ``Nm``."""
    s = s.strip().lower()
    if s.endswith("h"):
        try:
            return float(s[:-1])
        except ValueError:
            pass
    elif s.endswith("m"):
        try:
            return float(s[:-1]) / 60.0
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(
        f"Unrecognised duration {s!r}; use e.g. 48h or 1440m."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="B13.1 soak runner (stdlib only)")
    parser.add_argument(
        "--target",
        default=os.environ.get("B13_TARGET_URL", "http://localhost:8001"),
    )
    parser.add_argument(
        "--runtime-root",
        default=os.environ.get(
            "B13_RUNTIME_ROOT", "/home/gbibbo/asr_enhancement_runtime"
        ),
    )
    parser.add_argument(
        "--db-path",
        default=os.environ.get("B13_DB_PATH", ""),
    )
    parser.add_argument(
        "--examples-config",
        default=os.environ.get(
            "B13_EXAMPLES_CONFIG", "config/demo_examples.json"
        ),
    )
    parser.add_argument("--out", required=True, help="Output run directory")
    parser.add_argument(
        "--duration",
        default="48h",
        type=_parse_duration,
        help="Soak duration (e.g. 48h, 24h, 1440m)",
    )
    parser.add_argument(
        "--baseline-samples",
        type=int,
        default=30,
        help="Number of baseline cached calls (default 30)",
    )
    args = parser.parse_args()

    duration_h = float(args.duration)
    target_url = args.target.rstrip("/")
    runtime_root = pathlib.Path(args.runtime_root)
    db_path_str = args.db_path or str(runtime_root / "db" / "demo.db")
    db_path = pathlib.Path(db_path_str)

    run_dir = pathlib.Path(args.out)
    tmp_dir = run_dir / "tmp"
    run_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(exist_ok=True)

    global _log_path
    _log_path = run_dir / "runner.log"

    pointer = pathlib.Path("runs") / "b13_1_current_run.txt"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(run_dir.resolve()) + "\n", encoding="utf-8")

    start_utc = _utc_now_iso()
    log_info(
        "runner.start",
        target_url=target_url,
        duration_hours=duration_h,
        run_dir=str(run_dir),
    )

    try:
        uname = subprocess.check_output(["uname", "-a"], text=True, timeout=10).strip()
    except Exception:
        uname = "unavailable"
    try:
        docker_ver = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        docker_ver = "unavailable"
    try:
        free_h = subprocess.run(
            ["free", "-h"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        free_h = "unavailable"
    (run_dir / "host.txt").write_text(
        f"uname: {uname}\ndocker: {docker_ver}\nfree -h:\n{free_h}\n",
        encoding="utf-8",
    )

    write_state(run_dir, os.getpid(), start_utc, duration_h, target_url)

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    pairs = discover_cache_hit_pairs(target_url)
    (run_dir / "cache_hit_pairs.json").write_text(
        json.dumps(pairs, indent=2), encoding="utf-8"
    )

    baseline = measure_baseline(target_url, pairs, n_samples=args.baseline_samples)
    (run_dir / "baseline.json").write_text(
        json.dumps(baseline, indent=2), encoding="utf-8"
    )
    log_info("baseline.written", **baseline)

    metrics_path = run_dir / "metrics.jsonl"
    cached_path = run_dir / "cached.jsonl"
    jobs_path = run_dir / "jobs.jsonl"

    soak_start = time.monotonic()
    end_monotonic = soak_start + duration_h * 3600.0

    last_metric = 0.0
    last_cached = soak_start
    last_upload = soak_start
    last_recompute = soak_start

    log_info("runner.soak_started", duration_hours=duration_h)

    while not _shutdown and time.monotonic() < end_monotonic:
        now = time.monotonic()

        if now - last_metric >= METRIC_INTERVAL_S:
            try:
                collect_metrics(target_url, db_path, runtime_root, metrics_path)
            except Exception as exc:
                log_error("metrics.error", error_class=type(exc).__name__)
            last_metric = time.monotonic()

        if now - last_cached >= CACHED_INTERVAL_S:
            try:
                run_cached_job(target_url, pairs, cached_path)
            except Exception as exc:
                log_error("cached.error", error_class=type(exc).__name__)
            last_cached = time.monotonic()

        if now - last_upload >= UPLOAD_INTERVAL_S:
            try:
                run_synthetic_upload(target_url, tmp_dir, jobs_path)
            except Exception as exc:
                log_error("synthetic.error", error_class=type(exc).__name__)
            last_upload = time.monotonic()

        if now - last_recompute >= RECOMPUTE_INTERVAL_S:
            try:
                run_recompute_job(target_url, pairs, tmp_dir, jobs_path)
            except Exception as exc:
                log_error("recompute.error", error_class=type(exc).__name__)
            last_recompute = time.monotonic()

        now2 = time.monotonic()
        next_events = [
            last_metric + METRIC_INTERVAL_S - now2,
            last_cached + CACHED_INTERVAL_S - now2,
            last_upload + UPLOAD_INTERVAL_S - now2,
            last_recompute + RECOMPUTE_INTERVAL_S - now2,
            end_monotonic - now2,
        ]
        positive = [t for t in next_events if t > 0]
        sleep_s = min(positive) if positive else 1.0
        time.sleep(max(1.0, min(60.0, sleep_s)))

    end_utc = _utc_now_iso()
    elapsed_h = round((time.monotonic() - soak_start) / 3600.0, 3)

    if _shutdown:
        log_info("runner.stopped_by_signal", end_time_utc=end_utc, elapsed_hours=elapsed_h)
    else:
        log_info("runner.duration_complete", end_time_utc=end_utc, elapsed_hours=elapsed_h)

    try:
        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        state["end_time_utc"] = end_utc
        state["elapsed_hours"] = elapsed_h
        state["stopped_by_signal"] = _shutdown
        (run_dir / "state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        log_warn("runner.state_update_failed", error_class=type(exc).__name__)


if __name__ == "__main__":
    main()
