#!/usr/bin/env python3
"""
B14.2 path lock closure validator.

Checks that all files in the given git diff fall within the approved B14.2
path locks declared in docs/plans/b14_2/agent_plan.md section 1, plus the
inherited protocol locks (tracker, recovery report artifacts).

B14.2 is a repair microphase for the public-surface recruiter HTTPBasic
gate regression routed from B15. B-route, B14.0, B14.1, and B15 canonical
plan files and reports are frozen. Any touch of those frozen paths is
classified separately and emits B14_2_PREDECESSOR_FILE_TOUCHED (a hard
stop marker per orchestrator_plan section 6).

Emits OK_CHANGED_FILES_PATH_LOCKED on success, UNAUTHORIZED_FILE_TOUCHED
on lock-classification failure, or B14_2_PREDECESSOR_FILE_TOUCHED when a
frozen predecessor file is touched.
"""
import argparse
import datetime
import pathlib
import re
import subprocess
import sys


def _is_b14_2_test_path(p):
    name = pathlib.Path(p).name
    if p.startswith("tests/demo/") and name.startswith("test_b14_2_") and name.endswith(".py"):
        return True
    if p.startswith("tests/rp5/fixtures/"):
        return True
    return False


def _is_b14_2_script_path(p):
    name = pathlib.Path(p).name
    if p.startswith("scripts/rp5/") and name.startswith("validate_b14_2_") and name.endswith(".py"):
        return True
    if p.startswith("scripts/rp5/fixtures/") and name.startswith("generate_fixture_validate_b14_2_") and name.endswith(".py"):
        return True
    if p.startswith("scripts/rp5/") and name.startswith("smoke_b14_2_") and name.endswith(".py"):
        return True
    return False


def _is_b14_2_report_path(p):
    name = pathlib.Path(p).name
    return p.startswith("reports/rp5/") and name.startswith("b14_2_") and name.endswith(".md")


def _is_b14_2_config_path(p):
    if p == ".env.example":
        return True
    if p.startswith("services/") and pathlib.Path(p).name == ".env.example":
        return True
    return False


def _is_b14_2_api_demo_path(p):
    if not p.startswith("services/api/app/"):
        return False
    name = pathlib.Path(p).name
    # Application-layer recruiter HTTPBasic gate plumbing and any
    # application-side Funnel-aware wiring needed to preserve the gate
    # end-to-end on the public surface; the predicate excludes admin
    # auth code (frozen) and any router_runtime adapter.
    if name == "demo_main.py":
        return True
    if name.startswith("recruiter_auth"):
        return True
    if name.startswith("public_exposure"):
        return True
    if name.startswith("funnel_"):
        return True
    if name.startswith("openapi_docs_visibility"):
        return True
    if name.startswith("demo_") and name.endswith(".py") and "admin" not in name:
        return True
    return False


def _is_b14_2_tunnel_template_path(p):
    if not p.startswith("infra/tunnel/"):
        return False
    name = pathlib.Path(p).name
    # PL-B14_2-TUNNEL-TEMPLATE: placeholder template file only, max_files=1.
    # No real Tailscale auth-key, no Cloudflare token, no stable hostname
    # literal, no public URL literal, no non-loopback IP address literal.
    return name in ("funnel_config.template.yaml", "funnel_config.template.json")


def _is_protocol_rp_report_path(p):
    if not p.startswith("reports/rp5/"):
        return False
    name = pathlib.Path(p).name
    needles = [
        "tracker_missing", "tracker_mismatch", "plan_conflict",
        "recovery", "pending", "tracker_state",
    ]
    return any(needle in name for needle in needles)


def _is_predecessor_canonical_path(p):
    # docs/plans/(broute|b14_0|b14_1|b15)/**
    if re.match(r"^docs/plans/(broute|b14_0|b14_1|b15)/", p):
        return True
    # reports/rp5/(broute|b14_0|b14_1|b15)_*
    m = re.match(r"^reports/rp5/([^/]+)$", p)
    if m and re.match(r"^(broute|b14_0|b14_1|b15)_", m.group(1)):
        return True
    return False


PATH_LOCKS = [
    {"lock_id": "PL-B14_2-API-DEMO", "pattern": _is_b14_2_api_demo_path, "max_files": 6},
    {"lock_id": "PL-B14_2-CONFIG", "pattern": _is_b14_2_config_path, "max_files": 2},
    {"lock_id": "PL-B14_2-TESTS", "pattern": _is_b14_2_test_path, "max_files": 12},
    {"lock_id": "PL-B14_2-SCRIPTS", "pattern": _is_b14_2_script_path, "max_files": 20},
    {"lock_id": "PL-B14_2-REPORTS", "pattern": _is_b14_2_report_path, "max_files": 20},
    {"lock_id": "PL-B14_2-TUNNEL-TEMPLATE", "pattern": _is_b14_2_tunnel_template_path, "max_files": 1},
    {"lock_id": "PL-B14_2-TRACKER",
     "pattern": lambda p: p == "docs/progress/rp5_progress.yaml",
     "max_files": 1},
    {"lock_id": "PROTOCOL-TRACKER",
     "pattern": lambda p: p == "docs/progress/rp5_progress.yaml",
     "max_files": 1},
    {"lock_id": "PROTOCOL-RP-REPORTS", "pattern": _is_protocol_rp_report_path, "max_files": 10},
]


def classify_file(path):
    if _is_predecessor_canonical_path(path):
        return ("PREDECESSOR_FROZEN", "B14_2_PREDECESSOR_FILE_TOUCHED")
    for lock in PATH_LOCKS:
        if lock["pattern"](path):
            return (lock["lock_id"], None)
    return (None, None)


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
    predecessor_touches = []

    for f in changed_files:
        lock, predecessor_marker = classify_file(f)
        if predecessor_marker is not None:
            predecessor_touches.append(f)
        elif lock is None:
            unauthorized.append(f)
        else:
            file_lock_map[f] = lock

    lock_counts = {}
    for lock in file_lock_map.values():
        lock_counts[lock] = lock_counts.get(lock, 0) + 1

    lines = [
        "# B14.2 Path Lock Validation",
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

    if predecessor_touches:
        lines += ["", "## PREDECESSOR-FROZEN FILES TOUCHED (B14.2 freeze violation)", ""]
        for f in predecessor_touches:
            lines.append(f"- {f}")
        lines += ["", "B14_2_PREDECESSOR_FILE_TOUCHED"]
        out_path.write_text("\n".join(lines) + "\n")
        print("B14_2_PREDECESSOR_FILE_TOUCHED")
        return 1

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
        "All changed files are within approved B14.2 path locks.",
        "",
        "OK_CHANGED_FILES_PATH_LOCKED",
    ]
    out_path.write_text("\n".join(lines) + "\n")
    print("OK_CHANGED_FILES_PATH_LOCKED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
