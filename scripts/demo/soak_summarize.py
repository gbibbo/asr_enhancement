#!/usr/bin/env python3
"""B13.1 soak summarizer.

Stdlib-only. Reads the JSONL artefacts produced by ``soak_runner.py`` under a
single run directory and emits a redacted ``summary.md``. Acceptance criteria
follow plan §B13.1: zero crashes, cached P95 < 2x baseline, RAM stable,
sustained CPU temperature < 75 C, disk stable, cleanup works.

Privacy: the summary contains numeric metrics and small enumerated counts
only -- no transcripts, no full filesystem paths, no audio bytes, no DB rows,
no headers, no credentials, no upload filenames beyond synthetic basenames
already present in the runner's redacted JSONL records.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib


SUSTAINED_TEMP_THRESHOLD_C = 75.0
SUSTAINED_TEMP_CONSECUTIVE_SAMPLES = 3
RAM_GROWTH_FLAG_MIB = 50.0
DISK_GROWTH_FLAG_PCT = 5.0


def compute_p95(values) -> float:
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0:
        return float("nan")
    idx = max(0, min(n - 1, int(round(0.95 * n)) - 1))
    return float(sorted_vals[idx])


def parse_jsonl(path: pathlib.Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def assess_p95(baseline: dict, cached_records: list) -> dict:
    successful = [
        r["latency_ms"]
        for r in cached_records
        if r.get("http_status") == 200
        and r.get("status") == "cache_hit"
        and isinstance(r.get("latency_ms"), (int, float))
    ]
    soak_p95 = compute_p95(successful)
    soak_p50 = (
        sorted(successful)[max(0, int(round(0.50 * len(successful))) - 1)]
        if successful
        else float("nan")
    )
    baseline_p95 = float(baseline.get("p95_ms", float("nan")))
    ratio = soak_p95 / baseline_p95 if baseline_p95 and not math.isnan(soak_p95) else float("nan")
    passes = (
        not math.isnan(soak_p95)
        and not math.isnan(baseline_p95)
        and soak_p95 < 2.0 * baseline_p95
    )
    return {
        "baseline_p95_ms": round(baseline_p95, 1) if not math.isnan(baseline_p95) else None,
        "baseline_n": int(baseline.get("n_samples", 0)),
        "soak_p95_ms": round(soak_p95, 1) if not math.isnan(soak_p95) else None,
        "soak_p50_ms": round(soak_p50, 1) if not math.isnan(soak_p50) else None,
        "soak_n": len(successful),
        "ratio": round(ratio, 2) if not math.isnan(ratio) else None,
        "passes": bool(passes),
    }


def assess_temperature(metrics: list) -> dict:
    temps = [m.get("cpu_temp_c") for m in metrics if isinstance(m.get("cpu_temp_c"), (int, float))]
    if not temps:
        return {
            "n_samples": 0,
            "max_c": None,
            "mean_c": None,
            "sustained_above_threshold": False,
            "passes": False,
            "note": "no temperature samples",
        }
    max_c = max(temps)
    mean_c = sum(temps) / len(temps)
    consecutive = 0
    sustained = False
    for t in temps:
        if t >= SUSTAINED_TEMP_THRESHOLD_C:
            consecutive += 1
            if consecutive >= SUSTAINED_TEMP_CONSECUTIVE_SAMPLES:
                sustained = True
                break
        else:
            consecutive = 0
    return {
        "n_samples": len(temps),
        "max_c": round(max_c, 2),
        "mean_c": round(mean_c, 2),
        "sustained_above_threshold": sustained,
        "passes": (not sustained) and max_c < SUSTAINED_TEMP_THRESHOLD_C,
    }


def _ram_trend(values: list) -> dict:
    nums = [v for v in values if isinstance(v, (int, float))]
    if len(nums) < 4:
        return {"n_samples": len(nums), "first_half_mean": None, "second_half_mean": None, "growth_mib": None, "passes": True}
    half = len(nums) // 2
    first_mean = sum(nums[:half]) / half
    second_mean = sum(nums[half:]) / (len(nums) - half)
    growth = second_mean - first_mean
    return {
        "n_samples": len(nums),
        "first_half_mean": round(first_mean, 1),
        "second_half_mean": round(second_mean, 1),
        "growth_mib": round(growth, 1),
        "passes": growth < RAM_GROWTH_FLAG_MIB,
    }


def assess_ram(metrics: list) -> dict:
    api = _ram_trend([m.get("docker_api_mem_mib") for m in metrics])
    worker = _ram_trend([m.get("docker_worker_mem_mib") for m in metrics])
    return {
        "api": api,
        "worker": worker,
        "passes": bool(api["passes"]) and bool(worker["passes"]),
    }


def assess_disk(metrics: list) -> dict:
    pct = [m.get("disk_used_pct") for m in metrics if isinstance(m.get("disk_used_pct"), (int, float))]
    if not pct:
        return {"n_samples": 0, "start_pct": None, "end_pct": None, "delta_pct": None, "max_pct": None, "passes": False, "note": "no disk samples"}
    delta = pct[-1] - pct[0]
    return {
        "n_samples": len(pct),
        "start_pct": round(pct[0], 2),
        "end_pct": round(pct[-1], 2),
        "delta_pct": round(delta, 2),
        "max_pct": round(max(pct), 2),
        "passes": abs(delta) < DISK_GROWTH_FLAG_PCT,
    }


def assess_log_rotation(metrics: list) -> dict:
    if not metrics:
        return {"max_single_file_bytes": None, "files_seen": 0, "passes": True}
    max_bytes = 0
    seen: set = set()
    for m in metrics:
        sizes = m.get("log_sizes") or {}
        if isinstance(sizes, dict):
            for name, size in sizes.items():
                if isinstance(size, (int, float)):
                    max_bytes = max(max_bytes, int(size))
                    seen.add(name)
    return {
        "max_single_file_bytes": max_bytes,
        "files_seen": len(seen),
        "passes": True,
    }


def assess_jobs(jobs_records: list) -> dict:
    counts: dict = {}
    by_stream: dict = {}
    for j in jobs_records:
        s = j.get("terminal_status", "unknown")
        counts[s] = counts.get(s, 0) + 1
        stream = j.get("stream", "unknown")
        by_stream.setdefault(stream, {})
        by_stream[stream][s] = by_stream[stream].get(s, 0) + 1
    failed = counts.get("failed", 0) + counts.get("timeout", 0) + counts.get("submit_failed", 0) + counts.get("fetch_failed", 0)
    return {
        "total": len(jobs_records),
        "by_terminal_status": counts,
        "by_stream": by_stream,
        "failed_or_timeout": failed,
    }


def assess_crashes(runner_log_path: pathlib.Path, metrics: list, jobs: dict) -> dict:
    error_counts: dict = {}
    for rec in parse_jsonl(runner_log_path):
        if rec.get("level") == "error":
            event = rec.get("event", "unknown")
            error_counts[event] = error_counts.get(event, 0) + 1
    health_non_200 = sum(
        1
        for m in metrics
        if isinstance(m.get("health_http_status"), int)
        and m.get("health_http_status") != 200
    )
    total_runner_errors = sum(error_counts.values())
    passes = total_runner_errors == 0 and health_non_200 == 0
    return {
        "runner_error_events_total": total_runner_errors,
        "runner_error_event_counts": error_counts,
        "health_non_200_samples": health_non_200,
        "jobs_failed_or_timeout": jobs.get("failed_or_timeout", 0),
        "passes": passes,
    }


def assess_cleanup(run_dir: pathlib.Path) -> dict:
    early = run_dir / "cleanup_dryrun.early.log"
    late = run_dir / "cleanup_dryrun.late.log"
    return {
        "early_dryrun_present": early.exists(),
        "early_dryrun_bytes": early.stat().st_size if early.exists() else None,
        "late_dryrun_present": late.exists(),
        "late_dryrun_bytes": late.stat().st_size if late.exists() else None,
        "note": "Final cleanup --apply verification (curated examples / cache rows / logs untouched) is performed manually in the closure session, see docs/setup/rp5_soak.md.",
    }


def assess_queue_final(metrics: list) -> dict:
    if not metrics:
        return {"final_queue_depth": None, "max_queue_depth": None}
    depths = [
        m.get("health_queue_depth")
        for m in metrics
        if isinstance(m.get("health_queue_depth"), int) and m.get("health_queue_depth") >= 0
    ]
    return {
        "final_queue_depth": depths[-1] if depths else None,
        "max_queue_depth": max(depths) if depths else None,
    }


def render_markdown(summary: dict) -> str:
    lines: list = []
    lines.append("# B13.1 Local Soak Summary")
    lines.append("")
    state = summary["state"]
    lines.append("## Run state")
    lines.append("")
    lines.append(f"- start_time_utc: `{state.get('start_time_utc')}`")
    lines.append(f"- end_time_utc: `{state.get('end_time_utc')}`")
    lines.append(f"- elapsed_hours: `{state.get('elapsed_hours')}`")
    lines.append(f"- requested_duration_hours: `{state.get('requested_duration_hours')}`")
    lines.append(f"- target_url: `{state.get('target_url')}`")
    lines.append(f"- branch: `{state.get('branch')}`")
    lines.append(f"- head_commit: `{state.get('head_commit')}`")
    lines.append(f"- stopped_by_signal: `{state.get('stopped_by_signal')}`")
    lines.append("")

    p95 = summary["p95"]
    lines.append("## Cached-path P95 (criterion 2)")
    lines.append("")
    lines.append(f"- baseline_p95_ms: `{p95['baseline_p95_ms']}` (n={p95['baseline_n']})")
    lines.append(f"- soak_p95_ms: `{p95['soak_p95_ms']}` (n={p95['soak_n']})")
    lines.append(f"- soak_p50_ms: `{p95['soak_p50_ms']}`")
    lines.append(f"- ratio (soak/baseline): `{p95['ratio']}`")
    lines.append(f"- passes (<2x): **{p95['passes']}**")
    lines.append("")

    temp = summary["temperature"]
    lines.append("## CPU temperature (criterion 4)")
    lines.append("")
    lines.append(f"- max_c: `{temp.get('max_c')}`")
    lines.append(f"- mean_c: `{temp.get('mean_c')}`")
    lines.append(f"- sustained ≥ {SUSTAINED_TEMP_THRESHOLD_C}C ({SUSTAINED_TEMP_CONSECUTIVE_SAMPLES}+ consecutive): `{temp.get('sustained_above_threshold')}`")
    lines.append(f"- passes (max < {SUSTAINED_TEMP_THRESHOLD_C}C and not sustained): **{temp['passes']}**")
    lines.append("")

    ram = summary["ram"]
    lines.append("## RAM trend (criterion 3)")
    lines.append("")
    lines.append("- demo-api:")
    lines.append(f"  - first_half_mean_mib: `{ram['api']['first_half_mean']}`")
    lines.append(f"  - second_half_mean_mib: `{ram['api']['second_half_mean']}`")
    lines.append(f"  - growth_mib: `{ram['api']['growth_mib']}`")
    lines.append(f"  - passes: `{ram['api']['passes']}`")
    lines.append("- demo-worker:")
    lines.append(f"  - first_half_mean_mib: `{ram['worker']['first_half_mean']}`")
    lines.append(f"  - second_half_mean_mib: `{ram['worker']['second_half_mean']}`")
    lines.append(f"  - growth_mib: `{ram['worker']['growth_mib']}`")
    lines.append(f"  - passes: `{ram['worker']['passes']}`")
    lines.append(f"- combined passes (<{RAM_GROWTH_FLAG_MIB} MiB growth): **{ram['passes']}**")
    lines.append("")

    disk = summary["disk"]
    lines.append("## Disk usage (criterion 5)")
    lines.append("")
    lines.append(f"- start_pct: `{disk.get('start_pct')}`")
    lines.append(f"- end_pct: `{disk.get('end_pct')}`")
    lines.append(f"- delta_pct: `{disk.get('delta_pct')}`")
    lines.append(f"- max_pct: `{disk.get('max_pct')}`")
    lines.append(f"- passes (|delta| < {DISK_GROWTH_FLAG_PCT}): **{disk['passes']}**")
    lines.append("")

    queue = summary["queue"]
    lines.append("## Queue depth (final state)")
    lines.append("")
    lines.append(f"- final_queue_depth: `{queue['final_queue_depth']}`")
    lines.append(f"- max_queue_depth: `{queue['max_queue_depth']}`")
    lines.append("")

    jobs = summary["jobs"]
    lines.append("## Job status counts")
    lines.append("")
    lines.append(f"- total: `{jobs['total']}`")
    lines.append(f"- by_terminal_status: `{json.dumps(jobs['by_terminal_status'], sort_keys=True)}`")
    lines.append(f"- by_stream: `{json.dumps(jobs['by_stream'], sort_keys=True)}`")
    lines.append(f"- failed_or_timeout: `{jobs['failed_or_timeout']}`")
    lines.append("")

    crashes = summary["crashes"]
    lines.append("## Crashes / errors (criterion 1)")
    lines.append("")
    lines.append(f"- runner_error_events_total: `{crashes['runner_error_events_total']}`")
    lines.append(f"- runner_error_event_counts: `{json.dumps(crashes['runner_error_event_counts'], sort_keys=True)}`")
    lines.append(f"- health_non_200_samples: `{crashes['health_non_200_samples']}`")
    lines.append(f"- jobs_failed_or_timeout: `{crashes['jobs_failed_or_timeout']}`")
    lines.append(f"- passes (zero runner errors and zero health failures): **{crashes['passes']}**")
    lines.append("")

    cleanup = summary["cleanup"]
    lines.append("## Cleanup (criterion 6)")
    lines.append("")
    lines.append(f"- early_dryrun_present: `{cleanup['early_dryrun_present']}` (bytes={cleanup['early_dryrun_bytes']})")
    lines.append(f"- late_dryrun_present: `{cleanup['late_dryrun_present']}` (bytes={cleanup['late_dryrun_bytes']})")
    lines.append(f"- note: {cleanup['note']}")
    lines.append("")

    log_rot = summary["log_rotation"]
    lines.append("## Log rotation")
    lines.append("")
    lines.append(f"- files_seen: `{log_rot['files_seen']}`")
    lines.append(f"- max_single_file_bytes: `{log_rot['max_single_file_bytes']}`")
    lines.append("")

    overall = (
        bool(p95["passes"])
        and bool(temp["passes"])
        and bool(ram["passes"])
        and bool(disk["passes"])
        and bool(crashes["passes"])
    )
    lines.append("## Overall decision")
    lines.append("")
    lines.append(f"- automated pass (criteria 1-5): **{overall}**")
    lines.append(
        "- criterion 6 (cleanup) requires manual closure-session verification per "
        "docs/setup/rp5_soak.md."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="B13.1 soak summarizer")
    parser.add_argument("--run-dir", required=True, help="Soak run directory")
    parser.add_argument(
        "--out",
        default=None,
        help="Output summary path (default <run-dir>/summary.md)",
    )
    args = parser.parse_args()

    run_dir = pathlib.Path(args.run_dir)
    if not run_dir.is_dir():
        raise SystemExit(f"Run directory not found: {run_dir}")

    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    baseline_path = run_dir / "baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}

    cached_records = list(parse_jsonl(run_dir / "cached.jsonl"))
    jobs_records = list(parse_jsonl(run_dir / "jobs.jsonl"))
    metrics = list(parse_jsonl(run_dir / "metrics.jsonl"))

    p95 = assess_p95(baseline, cached_records)
    temp = assess_temperature(metrics)
    ram = assess_ram(metrics)
    disk = assess_disk(metrics)
    queue = assess_queue_final(metrics)
    jobs_summary = assess_jobs(jobs_records)
    log_rotation = assess_log_rotation(metrics)
    crashes = assess_crashes(run_dir / "runner.log", metrics, jobs_summary)
    cleanup = assess_cleanup(run_dir)

    summary = {
        "state": state,
        "p95": p95,
        "temperature": temp,
        "ram": ram,
        "disk": disk,
        "queue": queue,
        "jobs": jobs_summary,
        "crashes": crashes,
        "cleanup": cleanup,
        "log_rotation": log_rotation,
    }

    out_path = pathlib.Path(args.out) if args.out else (run_dir / "summary.md")
    out_path.write_text(render_markdown(summary), encoding="utf-8")
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"summary written: {out_path}")


if __name__ == "__main__":
    main()
