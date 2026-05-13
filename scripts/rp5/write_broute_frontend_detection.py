#!/usr/bin/env python3
"""
B-route frontend detection.
Enumerates services/frontend/app/demo/ TS/TSX files that reference BR-route
contract surfaces (DemoHealthResponse, /api/demo/* endpoints, router-aware
response fields, named PL-BR-FRONTEND components). Confirms each named file
classifies as PL-BR-FRONTEND under the active path-lock validator.
Emits OK_BROUTE_FRONTEND_DETECTION on success or FRONTEND_BACKEND_DRIFT on failure.
"""
import argparse
import datetime
import importlib.util
import pathlib
import sys


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


BR_RELEVANT_TOKENS = [
    "DemoHealthResponse",
    "/api/demo/health",
    "/api/demo/upload",
    "/api/demo/results",
    "selected_backend",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "RouterFieldsPanel",
    "UploadForm",
    "ResultView",
]

EXCLUDE_DIRS = {".next", "node_modules", "dist", "build"}


def load_classifier():
    spec = importlib.util.spec_from_file_location(
        "vcp", str(_REPO_ROOT / "scripts/rp5/validate_changed_files_against_path_locks.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.classify_file


def walk_demo_files():
    demo_root = _REPO_ROOT / "services/frontend/app/demo"
    if not demo_root.exists():
        return []
    out = []
    for path in sorted(demo_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in (".ts", ".tsx"):
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        out.append(path)
    return out


def scan_file_for_tokens(path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    return [tok for tok in BR_RELEVANT_TOKENS if tok in text]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    classify = load_classifier()
    candidates = walk_demo_files()

    matched = []
    misclassified = []
    for path in candidates:
        tokens = scan_file_for_tokens(path)
        if not tokens:
            continue
        rel = str(path.relative_to(_REPO_ROOT))
        lock = classify(rel)
        entry = {"path": rel, "tokens": tokens, "lock": lock}
        if lock == "PL-BR-FRONTEND":
            matched.append(entry)
        else:
            misclassified.append(entry)

    eligible = len(matched) > 0 and len(misclassified) == 0
    sentinel = "OK_BROUTE_FRONTEND_DETECTION" if eligible else "FRONTEND_BACKEND_DRIFT"

    lines = [
        "# BR-04 B-route Frontend Detection Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"demo_root_scanned: services/frontend/app/demo",
        f"br_relevant_tokens: {BR_RELEVANT_TOKENS}",
        f"candidates_scanned: {len(candidates)}",
        f"eligible_files: {len(matched)}",
        f"misclassified_files: {len(misclassified)}",
        "",
        "## Eligible Files (PL-BR-FRONTEND)",
        "",
    ]
    if matched:
        for e in matched:
            lines.append(f"- {e['path']} (lock={e['lock']}, tokens={e['tokens']})")
    else:
        lines.append("(none)")

    if misclassified:
        lines += ["", "## Misclassified Files (token match but not PL-BR-FRONTEND)", ""]
        for e in misclassified:
            lines.append(f"- {e['path']} (lock={e['lock']}, tokens={e['tokens']})")

    lines += ["", f"## Result: {sentinel}", "", sentinel]
    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_BROUTE_FRONTEND_DETECTION" else 1


if __name__ == "__main__":
    sys.exit(main())
