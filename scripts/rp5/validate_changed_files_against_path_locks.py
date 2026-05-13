#!/usr/bin/env python3
"""
Path lock closure validator for B-route.
Checks that all files in the given git diff fall within the approved path locks.
Emits OK_CHANGED_FILES_PATH_LOCKED on success or UNAUTHORIZED_FILE_TOUCHED on failure.
"""
import argparse
import datetime
import pathlib
import subprocess
import sys

# Path lock definitions from agent_plan.md section 1
PATH_LOCKS = [
    {
        "lock_id": "PL-BR-CONFIG",
        "pattern": lambda p: p == "config/demo_examples.json",
        "max_files": 1,
    },
    {
        "lock_id": "PL-BR-API-DEMO",
        "pattern": lambda p: p.startswith("services/") and (
            "demo_main" in p
            or "/demo/" in p
            or "demo/health" in p
            or "demo/upload" in p
            or "demo/results" in p
            or "assemble_demo_response" in p
        ),
        "max_files": 6,
    },
    {
        "lock_id": "PL-BR-ASR",
        "pattern": lambda p: (
            p.startswith("libs/asr/") or
            "router_runtime" in p or
            "RouterRuntime" in p or
            "RouterDecision" in p or
            "AssembledResponse" in p or
            "build_cache_key" in p
        ),
        "max_files": 8,
    },
    {
        "lock_id": "PL-BR-FRONTEND",
        "pattern": lambda p: (
            p.startswith("services/frontend/") and any(
                sym in p for sym in ["RouterFieldsPanel", "UploadForm", "ResultView"]
            )
        ),
        "max_files": 8,
    },
    {
        "lock_id": "PL-BR-TESTS",
        "pattern": lambda p: (
            p.startswith("tests/") and
            any(x in p for x in ["demo", "router", "api"])
        ),
        "max_files": 12,
    },
    {
        "lock_id": "PL-BR-SCRIPTS",
        "pattern": lambda p: (
            p.startswith("scripts/rp5/") or
            p.startswith("scripts/demo/")
        ),
        "max_files": 18,
    },
    {
        "lock_id": "PL-BR-REPORTS",
        "pattern": lambda p: (
            p.startswith("reports/rp5/") and
            pathlib.Path(p).name.startswith("broute_")
        ),
        "max_files": 20,
    },
    # Tracker is a protocol artifact updated by orchestration protocol, not an implementation file
    {
        "lock_id": "PROTOCOL-TRACKER",
        "pattern": lambda p: p == "docs/progress/rp5_progress.yaml",
        "max_files": 1,
    },
    # Recovery report artifacts (RP-* packet outputs)
    {
        "lock_id": "PROTOCOL-RP-REPORTS",
        "pattern": lambda p: (
            p.startswith("reports/rp5/") and
            any(x in pathlib.Path(p).name for x in [
                "tracker_missing", "tracker_mismatch", "plan_conflict",
                "recovery", "pending", "tracker_state",
            ])
        ),
        "max_files": 10,
    },
]


def classify_file(path):
    for lock in PATH_LOCKS:
        if lock["pattern"](path):
            return lock["lock_id"]
    return None


def get_changed_files(diff_spec):
    result = subprocess.run(
        ["git", "diff", "--name-only", diff_spec],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None, result.stderr.strip()
    files = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
    return files, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", default="HEAD~1..HEAD")
    parser.add_argument("--out", required=True)
    parser.add_argument("--lock", help="validate only a specific lock (informational)")
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    changed_files, err = get_changed_files(args.diff)
    if changed_files is None:
        out_path.write_text(f"UNAUTHORIZED_FILE_TOUCHED: git diff error: {err}\n")
        print("UNAUTHORIZED_FILE_TOUCHED")
        return 1

    file_lock_map = {}
    unauthorized = []

    for f in changed_files:
        lock = classify_file(f)
        if lock is None:
            unauthorized.append(f)
        else:
            file_lock_map[f] = lock

    lock_counts = {}
    for lock in file_lock_map.values():
        lock_counts[lock] = lock_counts.get(lock, 0) + 1

    lines = [
        "# B-route Path Lock Validation",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"diff_spec: {args.diff}",
        f"files_checked: {len(changed_files)}",
        "",
        "## File Lock Assignments",
        "",
    ]
    for f in sorted(file_lock_map):
        lines.append(f"- {f} → {file_lock_map[f]}")

    if unauthorized:
        lines += ["", "## UNAUTHORIZED FILES (no matching path lock)", ""]
        for f in unauthorized:
            lines.append(f"- {f}")
        lines += ["", "UNAUTHORIZED_FILE_TOUCHED"]
        out_path.write_text("\n".join(lines) + "\n")
        print("UNAUTHORIZED_FILE_TOUCHED")
        return 1

    lines += [
        "",
        "## Lock File Counts",
        "",
    ]
    for lock_id, count in sorted(lock_counts.items()):
        lines.append(f"- {lock_id}: {count} file(s)")

    lines += ["", "## Result", "", "All changed files are within approved path locks.", "", "OK_CHANGED_FILES_PATH_LOCKED"]
    out_path.write_text("\n".join(lines) + "\n")
    print("OK_CHANGED_FILES_PATH_LOCKED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
