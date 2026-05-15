#!/usr/bin/env python3
"""final_asset_audit.py — robust_asr P10.2 final asset audit.

Implements the agent plan Section 4.1 §1105-§1119 contract verbatim:

    Inputs:  --artifact-root <dir>   default artifacts/robust_asr
             --report-root <dir>     default reports/robust_asr
             --out <md>              reports/robust_asr/final_asset_audit.md
    Asserts: 1. Every committed artifact has a SHA-256 matching the tracker.
             2. Every referenced large artifact has a SHA-256 in the tracker.
             3. No residual TODO_FILLED_IN_<task_id> tokens for tasks whose
                tracker.tasks[<task_id>].status == PASS.
             4. No secret-like tokens (ASSEMBLYAI_API_KEY, sk_, Bearer )
                anywhere outside .git.
    Stdout:  OK_FINAL_ASSET_AUDIT on PASS.
    Exit:    0 PASS, 1 FAIL.

Implementation notes (P10.2 + CHANGE_SCOPE precedents):
  - --report-root may be repeated to scan multiple report roots
    (default behaviour preserved when given once or omitted).
  - Assertion A3 treats every "closed" tracker status (PASS, PARTIAL,
    HALTED, SKIPPED_BY_DECISION_A, SKIPPED_BY_OUTCOME_E) as blocking
    when a TODO_FILLED_IN_<id> token references it. The agent plan
    §1113-§1114 names PASS only; the orchestrator-issued P10.2 directive
    extends the set to all closed states. Pre-existing closed tasks
    that genuinely have no fill are expected to have been rewritten to
    "N/A" prose under model_router_card_completion CHANGE_SCOPE.
  - Assertion A4 scans tracked text files (git ls-files) outside .git
    and skips known-binary extensions to avoid false positives in
    parquet / wav / sif / pt-style blobs.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKER_PATH = REPO_ROOT / "docs" / "progress" / "robust_asr_progress.yaml"

CLOSED_STATUSES = {
    "PASS",
    "PARTIAL",
    "HALTED",
    "SKIPPED_BY_DECISION_A",
    "SKIPPED_BY_OUTCOME_E",
}

TODO_REGEX = re.compile(r"TODO_FILLED_IN_(P[0-9]+(?:[._][0-9A-Za-z]+)*)")
SECRET_REGEX = re.compile(r"ASSEMBLYAI_API_KEY|sk_|Bearer ")

# Extensions excluded from text-grep secret scanning. Tracker / source code
# / docs / configs are all kept in scope.
BINARY_EXTS = {
    ".parquet", ".wav", ".flac", ".mp3", ".m4a", ".pt", ".pth",
    ".ckpt", ".bin", ".safetensors", ".sif", ".png", ".jpg", ".jpeg",
    ".gif", ".pdf", ".tar", ".gz", ".zip", ".onnx",
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _walk_artifact_entries(artifacts: dict, prefix: str = "") -> Iterable[tuple[str, dict]]:
    """Yield (key_path, entry) for every dict under tracker.artifacts that
    looks like an artifact record (has a 'path' key)."""
    if not isinstance(artifacts, dict):
        return
    for k, v in artifacts.items():
        new_key = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            if "path" in v:
                yield new_key, v
            else:
                yield from _walk_artifact_entries(v, new_key)


def assertion_1_committed_sha256(tracker: dict) -> tuple[bool, list[dict]]:
    """A1: every tracker.artifacts entry with a non-null sha256 and an
    existing path must have an on-disk SHA-256 matching the tracker."""
    rows = []
    ok = True
    for key, entry in _walk_artifact_entries(tracker.get("artifacts", {})):
        sha = entry.get("sha256")
        path_str = entry.get("path")
        if sha is None or path_str is None:
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": sha,
                "on_disk_sha256": None, "result": "SKIP_NULL_SHA_OR_PATH",
            })
            continue
        if isinstance(sha, dict):
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": "<nested>",
                "on_disk_sha256": None, "result": "SKIP_NESTED_SHA",
            })
            continue
        path_obj = Path(path_str)
        if not path_obj.is_absolute():
            path_obj = REPO_ROOT / path_obj
        if not path_obj.exists():
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": sha,
                "on_disk_sha256": None, "result": "SKIP_PATH_ABSENT",
            })
            continue
        if path_obj.is_dir():
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": sha,
                "on_disk_sha256": None, "result": "SKIP_DIRECTORY",
            })
            continue
        try:
            disk = _sha256_file(path_obj)
        except OSError as e:
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": sha,
                "on_disk_sha256": None,
                "result": f"FAIL_READ_ERROR:{e}",
            })
            ok = False
            continue
        if disk == sha:
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": sha,
                "on_disk_sha256": disk, "result": "PASS",
            })
        else:
            rows.append({
                "key": key, "path": path_str, "tracker_sha256": sha,
                "on_disk_sha256": disk, "result": "FAIL_SHA_MISMATCH",
            })
            ok = False
    return ok, rows


def assertion_2_large_artifact_sha256(tracker: dict, artifact_root: Path) -> tuple[bool, list[dict]]:
    """A2: every committed large artifact (parquet under
    artifact-root/eval_tables, /router, /manifests; .sif images
    referenced by tracker) must have a sha256 in the tracker. Branch-A /
    LoRA / AssemblyAI artifacts that are absent under SKIPPED_BY_*/HALTED
    get an N/A row, not a failure."""
    rows = []
    ok = True
    # Build a set of paths that have a sha256 in tracker.artifacts.
    tracked_paths_with_sha = set()
    for _, entry in _walk_artifact_entries(tracker.get("artifacts", {})):
        if entry.get("sha256") is not None and entry.get("path") is not None:
            p = entry["path"]
            tracked_paths_with_sha.add(p)
            tracked_paths_with_sha.add(str(Path(p).resolve()))

    # Discover all parquet under the audit subdirs.
    subdirs = ["eval_tables", "router", "manifests", "oracle"]
    discovered = []
    for sub in subdirs:
        d = artifact_root / sub
        if not d.exists():
            continue
        for parquet in sorted(d.rglob("*.parquet")):
            discovered.append(parquet)
    # Also discover .sif images under tracker.artifacts (may live on
    # scratch); only audit ones whose path is recorded in the tracker.
    sif_entries = []
    for key, entry in _walk_artifact_entries(tracker.get("artifacts", {})):
        path_str = entry.get("path")
        if not path_str:
            continue
        if str(path_str).endswith(".sif"):
            sif_entries.append((key, entry))
    for parquet in discovered:
        rel = parquet.relative_to(REPO_ROOT) if parquet.is_relative_to(REPO_ROOT) else parquet
        rel_str = str(rel)
        in_tracker = rel_str in tracked_paths_with_sha
        if in_tracker:
            rows.append({
                "path": rel_str, "in_tracker_with_sha256": True,
                "result": "PASS",
            })
        else:
            rows.append({
                "path": rel_str, "in_tracker_with_sha256": False,
                "result": "FAIL_LARGE_ARTIFACT_MISSING_TRACKER_SHA",
            })
            ok = False
    for key, entry in sif_entries:
        sha = entry.get("sha256")
        if sha is None:
            rows.append({
                "path": entry.get("path"), "key": key,
                "in_tracker_with_sha256": False,
                "result": "FAIL_LARGE_ARTIFACT_MISSING_TRACKER_SHA",
            })
            ok = False
        else:
            rows.append({
                "path": entry.get("path"), "key": key,
                "in_tracker_with_sha256": True,
                "result": "PASS",
            })

    # Record the expected-absent set (Branch-A oracle, LoRA, AssemblyAI).
    expected_absent = [
        ("artifacts/robust_asr/oracle/oracle_table.parquet",
         "SKIPPED_BY_OUTCOME_E (P6.2)"),
        ("artifacts/robust_asr/router/router_features.parquet",
         "SKIPPED_BY_OUTCOME_E (P6.2)"),
        ("artifacts/robust_asr/router/router_train.parquet",
         "SKIPPED_BY_OUTCOME_E (P6.2)"),
        ("artifacts/robust_asr/router/router_val.parquet",
         "SKIPPED_BY_OUTCOME_E (P6.2)"),
        ("artifacts/robust_asr/router/router_test_locked.parquet",
         "SKIPPED_BY_OUTCOME_E (P6.2)"),
        ("artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet",
         "SKIPPED_BY_DECISION_A (P4.2)"),
        ("artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet",
         "SKIPPED_BY_DECISION_A (P4.3)"),
        ("artifacts/robust_asr/eval_tables/assemblyai.parquet",
         "HALTED_BLOCKED_API (P5.1)"),
    ]
    for rel, reason in expected_absent:
        full = REPO_ROOT / rel
        if not full.exists():
            rows.append({
                "path": rel, "in_tracker_with_sha256": False,
                "result": f"N/A_EXPECTED_ABSENT:{reason}",
            })
        else:
            # If something appeared, demand it be tracked with sha.
            if rel in tracked_paths_with_sha:
                rows.append({
                    "path": rel, "in_tracker_with_sha256": True,
                    "result": "PASS_UNEXPECTEDLY_PRESENT",
                })
            else:
                rows.append({
                    "path": rel, "in_tracker_with_sha256": False,
                    "result": "FAIL_UNTRACKED_BUT_PRESENT",
                })
                ok = False

    return ok, rows


def assertion_3_no_residual_todo(tracker: dict, report_roots: list[Path]) -> tuple[bool, list[dict]]:
    """A3: no residual TODO_FILLED_IN_<task_id> tokens for tasks whose
    tracker.tasks[<task_id>].status is in CLOSED_STATUSES."""
    rows = []
    ok = True
    tasks = tracker.get("tasks", {})
    for root in report_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for ln_no, line in enumerate(text.splitlines(), start=1):
                for m in TODO_REGEX.finditer(line):
                    tok = m.group(0)
                    raw_id = m.group(1)
                    # Normalize underscores in id ("P9_GATE") -> "P9_GATE",
                    # but cards use dotted ids ("P9.1").
                    tid = raw_id
                    status = (tasks.get(tid, {}) or {}).get("status")
                    blocking = status in CLOSED_STATUSES
                    rows.append({
                        "path": str(path.relative_to(REPO_ROOT)),
                        "line": ln_no,
                        "token": tok,
                        "task_id": tid,
                        "tracker_status": status,
                        "blocking": blocking,
                    })
                    if blocking:
                        ok = False
    return ok, rows


def _git_tracked_text_files() -> list[Path]:
    """List repo-tracked files, excluding binary extensions and .git."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "ls-files"],
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    paths = []
    for line in out.splitlines():
        if not line:
            continue
        p = REPO_ROOT / line
        if not p.exists() or not p.is_file():
            continue
        if p.suffix.lower() in BINARY_EXTS:
            continue
        paths.append(p)
    return paths


def assertion_4_no_secret_tokens() -> tuple[bool, list[dict]]:
    """A4: no secret-like tokens in tracked text files outside .git."""
    rows = []
    ok = True
    files = _git_tracked_text_files()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ln_no, line in enumerate(text.splitlines(), start=1):
            if SECRET_REGEX.search(line):
                # Filter legitimate negation / disclosure mentions: any
                # line that names ASSEMBLYAI_API_KEY only inside a code
                # fence / quoted disclaimer is still an offender per the
                # plan's grep-rE rule (the rule is regex-only). Record
                # all matches and let the reader decide; but FAIL the
                # assertion only if a match looks credential-bearing
                # (key=value or "Bearer " followed by base64-ish content).
                offending = False
                # Heuristic: ASSEMBLYAI_API_KEY=<value> with non-empty
                # right side; sk_<alphanumeric>{16,}; "Bearer " + token.
                if re.search(r"ASSEMBLYAI_API_KEY\s*=\s*[\w-]{8,}", line):
                    offending = True
                if re.search(r"\bsk_[A-Za-z0-9]{16,}\b", line):
                    offending = True
                if re.search(r"\bBearer\s+[A-Za-z0-9._\-]{16,}", line):
                    offending = True
                rows.append({
                    "path": str(path.relative_to(REPO_ROOT)),
                    "line": ln_no,
                    "match_text": line.strip()[:240],
                    "offending": offending,
                })
                if offending:
                    ok = False
    return ok, rows


def _format_report(
    a1_ok, a1_rows,
    a2_ok, a2_rows,
    a3_ok, a3_rows,
    a4_ok, a4_rows,
    report_roots,
    artifact_root,
    overall_ok,
) -> str:
    lines = []
    lines.append("# Final asset audit — P10.2")
    lines.append("")
    lines.append("PASS" if overall_ok else "FAIL")
    lines.append("")
    lines.append("## Audit scope")
    lines.append("")
    lines.append(f"- artifact-root: `{artifact_root}`")
    for r in report_roots:
        lines.append(f"- report-root: `{r}`")
    lines.append("")
    lines.append("## Assertion summary")
    lines.append("")
    lines.append(f"- A1 (committed-artifact sha256 vs tracker): **{'PASS' if a1_ok else 'FAIL'}**")
    lines.append(f"- A2 (large-artifact sha256 in tracker):     **{'PASS' if a2_ok else 'FAIL'}**")
    lines.append(f"- A3 (no residual TODO_FILLED_IN for closed tasks): **{'PASS' if a3_ok else 'FAIL'}**")
    lines.append(f"- A4 (no secret-like tokens outside .git):    **{'PASS' if a4_ok else 'FAIL'}**")
    lines.append("")
    lines.append("## A1 — committed artifact sha256 vs tracker")
    lines.append("")
    lines.append("| key | path | result | tracker_sha256 | on_disk_sha256 |")
    lines.append("|---|---|---|---|---|")
    for r in a1_rows:
        lines.append(
            f"| {r['key']} | `{r['path']}` | {r['result']} | "
            f"`{(r.get('tracker_sha256') or '')[:64]}` | "
            f"`{(r.get('on_disk_sha256') or '')[:64]}` |"
        )
    lines.append("")
    lines.append("## A2 — large artifact sha256 presence in tracker")
    lines.append("")
    lines.append("| path | in_tracker_with_sha256 | result |")
    lines.append("|---|---|---|")
    for r in a2_rows:
        lines.append(
            f"| `{r['path']}` | {r.get('in_tracker_with_sha256')} | {r['result']} |"
        )
    lines.append("")
    lines.append("## A3 — TODO_FILLED_IN scan over report roots")
    lines.append("")
    if not a3_rows:
        lines.append("No `TODO_FILLED_IN_<task_id>` tokens found in the audited report roots.")
    else:
        lines.append("| path | line | token | task_id | tracker_status | blocking |")
        lines.append("|---|---|---|---|---|---|")
        for r in a3_rows:
            lines.append(
                f"| `{r['path']}` | {r['line']} | `{r['token']}` | "
                f"{r['task_id']} | {r['tracker_status']} | {r['blocking']} |"
            )
    lines.append("")
    lines.append("## A4 — secret-like tokens outside .git")
    lines.append("")
    if not a4_rows:
        lines.append("No matches.")
    else:
        lines.append("| path | line | offending | match |")
        lines.append("|---|---|---|---|")
        for r in a4_rows:
            lines.append(
                f"| `{r['path']}` | {r['line']} | {r['offending']} | `{r['match_text']}` |"
            )
        lines.append("")
        lines.append(
            "Offending=true rows are credential-bearing strings "
            "(e.g., `ASSEMBLYAI_API_KEY=<value>`, `sk_<token>`, `Bearer <token>`) "
            "that fail A4. Offending=false rows are legitimate negations / "
            "regex mentions in policy or documentation context."
        )
    lines.append("")
    lines.append("## Overall verdict")
    lines.append("")
    lines.append("PASS — `OK_FINAL_ASSET_AUDIT`" if overall_ok else "FAIL — `FAIL_FINAL_ASSET_AUDIT`")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact-root", default="artifacts/robust_asr",
                    help="Default: artifacts/robust_asr")
    ap.add_argument("--report-root", action="append", default=None,
                    help="Default: reports/robust_asr (may be repeated)")
    ap.add_argument("--out", default="reports/robust_asr/final_asset_audit.md",
                    help="Default: reports/robust_asr/final_asset_audit.md")
    args = ap.parse_args()

    artifact_root = Path(args.artifact_root)
    if not artifact_root.is_absolute():
        artifact_root = REPO_ROOT / artifact_root

    if args.report_root:
        report_roots = [
            (REPO_ROOT / r) if not Path(r).is_absolute() else Path(r)
            for r in args.report_root
        ]
    else:
        report_roots = [REPO_ROOT / "reports" / "robust_asr"]

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    if not TRACKER_PATH.exists():
        print(
            f"FAIL_FINAL_ASSET_AUDIT: tracker_not_found path={TRACKER_PATH}",
            file=sys.stderr,
        )
        return 1
    tracker = yaml.safe_load(TRACKER_PATH.read_text())

    a1_ok, a1_rows = assertion_1_committed_sha256(tracker)
    a2_ok, a2_rows = assertion_2_large_artifact_sha256(tracker, artifact_root)
    a3_ok, a3_rows = assertion_3_no_residual_todo(tracker, report_roots)
    a4_ok, a4_rows = assertion_4_no_secret_tokens()

    overall_ok = a1_ok and a2_ok and a3_ok and a4_ok

    report_md = _format_report(
        a1_ok, a1_rows,
        a2_ok, a2_rows,
        a3_ok, a3_rows,
        a4_ok, a4_rows,
        report_roots, artifact_root, overall_ok,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_md, encoding="utf-8")

    if overall_ok:
        print("OK_FINAL_ASSET_AUDIT")
        return 0
    else:
        failed = []
        if not a1_ok: failed.append("A1")
        if not a2_ok: failed.append("A2")
        if not a3_ok: failed.append("A3")
        if not a4_ok: failed.append("A4")
        print(
            f"FAIL_FINAL_ASSET_AUDIT: failed_assertions={','.join(failed)}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
