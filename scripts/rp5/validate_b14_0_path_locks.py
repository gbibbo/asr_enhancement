#!/usr/bin/env python3
"""
B14.0 path lock closure validator.

Checks that all files in the given git diff fall within the approved B14.0
path locks declared in docs/plans/b14_0/agent_plan.md section 1, plus the
inherited protocol locks (tracker, recovery report artifacts).

Emits OK_CHANGED_FILES_PATH_LOCKED on success or UNAUTHORIZED_FILE_TOUCHED
on failure.
"""
import argparse
import datetime
import pathlib
import subprocess
import sys


def _is_b14_0_test_path(p):
    name = pathlib.Path(p).name
    if p.startswith("tests/demo/") and name.startswith("test_b14_0_") and name.endswith(".py"):
        return True
    if p.startswith("tests/rp5/fixtures/"):
        return True
    return False


def _is_b14_0_script_path(p):
    name = pathlib.Path(p).name
    if p.startswith("scripts/rp5/") and name.startswith("validate_b14_0_") and name.endswith(".py"):
        return True
    if p.startswith("scripts/rp5/fixtures/") and name.startswith("generate_fixture_validate_b14_0_") and name.endswith(".py"):
        return True
    if p.startswith("scripts/rp5/") and name.startswith("smoke_b14_0_") and name.endswith(".py"):
        return True
    return False


def _is_b14_0_report_path(p):
    name = pathlib.Path(p).name
    return p.startswith("reports/rp5/") and name.startswith("b14_0_") and name.endswith(".md")


def _is_b14_0_config_path(p):
    if p == ".env.example":
        return True
    if p.startswith("services/") and pathlib.Path(p).name == ".env.example":
        return True
    return False


def _is_b14_0_api_demo_path(p):
    if not p.startswith("services/api/app/"):
        return False
    name = pathlib.Path(p).name
    # Recruiter middleware and dependency wiring live under services/api/app/.
    # Allow demo_main.py and any recruiter_auth* helper module; the change-set
    # is bounded by the max_files cap (6) declared in agent_plan §1.
    if name == "demo_main.py":
        return True
    if name.startswith("recruiter_auth"):
        return True
    if name.startswith("demo_") and name.endswith(".py"):
        return True
    return False


def _is_b14_0_frontend_path(p):
    if not p.startswith("services/frontend/app/demo/"):
        return False
    return True


def _is_protocol_rp_report_path(p):
    if not p.startswith("reports/rp5/"):
        return False
    name = pathlib.Path(p).name
    needles = [
        "tracker_missing", "tracker_mismatch", "plan_conflict",
        "recovery", "pending", "tracker_state",
    ]
    return any(needle in name for needle in needles)


PATH_LOCKS = [
    {"lock_id": "PL-B14_0-API-DEMO", "pattern": _is_b14_0_api_demo_path, "max_files": 6},
    {"lock_id": "PL-B14_0-FRONTEND", "pattern": _is_b14_0_frontend_path, "max_files": 8},
    {"lock_id": "PL-B14_0-CONFIG", "pattern": _is_b14_0_config_path, "max_files": 2},
    {"lock_id": "PL-B14_0-TESTS", "pattern": _is_b14_0_test_path, "max_files": 12},
    {"lock_id": "PL-B14_0-SCRIPTS", "pattern": _is_b14_0_script_path, "max_files": 18},
    {"lock_id": "PL-B14_0-REPORTS", "pattern": _is_b14_0_report_path, "max_files": 20},
    {"lock_id": "PROTOCOL-TRACKER",
     "pattern": lambda p: p == "docs/progress/rp5_progress.yaml",
     "max_files": 1},
    {"lock_id": "PROTOCOL-RP-REPORTS", "pattern": _is_protocol_rp_report_path, "max_files": 10},
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
    parser.add_argument("--lock",
                        help="restrict reporting to a single lock id (informational filter)")
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.lock is not None:
        known_locks = {lock["lock_id"] for lock in PATH_LOCKS}
        if args.lock not in known_locks:
            out_path.write_text(
                f"UNAUTHORIZED_FILE_TOUCHED: unknown --lock {args.lock}; "
                f"known: {sorted(known_locks)}\n"
            )
            print("UNAUTHORIZED_FILE_TOUCHED")
            return 1

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
        "# B14.0 Path Lock Validation",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"diff_spec: {args.diff}",
        f"files_checked: {len(changed_files)}",
        f"lock_filter: {args.lock if args.lock else 'all'}",
        "",
        "## File Lock Assignments",
        "",
    ]
    for f in sorted(file_lock_map):
        if args.lock and file_lock_map[f] != args.lock:
            continue
        lines.append(f"- {f} -> {file_lock_map[f]}")

    if unauthorized:
        lines += ["", "## UNAUTHORIZED FILES (no matching path lock)", ""]
        for f in unauthorized:
            lines.append(f"- {f}")
        lines += ["", "UNAUTHORIZED_FILE_TOUCHED"]
        out_path.write_text("\n".join(lines) + "\n")
        print("UNAUTHORIZED_FILE_TOUCHED")
        return 1

    lines += ["", "## Lock File Counts", ""]
    for lock_id, count in sorted(lock_counts.items()):
        if args.lock and lock_id != args.lock:
            continue
        lines.append(f"- {lock_id}: {count} file(s)")

    # Enforce max_files caps from agent_plan §1
    cap_violations = []
    for lock in PATH_LOCKS:
        observed = lock_counts.get(lock["lock_id"], 0)
        if observed > lock["max_files"]:
            cap_violations.append(
                f"{lock['lock_id']}: {observed} files exceed max {lock['max_files']}"
            )
    if cap_violations:
        lines += ["", "## Max-File Cap Violations", ""]
        for v in cap_violations:
            lines.append(f"- {v}")
        lines += ["", "UNAUTHORIZED_FILE_TOUCHED"]
        out_path.write_text("\n".join(lines) + "\n")
        print("UNAUTHORIZED_FILE_TOUCHED")
        return 1

    lines += [
        "",
        "## Result",
        "",
        "All changed files are within approved B14.0 path locks.",
        "",
        "OK_CHANGED_FILES_PATH_LOCKED",
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print("OK_CHANGED_FILES_PATH_LOCKED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
