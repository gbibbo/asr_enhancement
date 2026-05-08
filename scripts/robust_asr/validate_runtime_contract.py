#!/usr/bin/env python3
"""Validate the RP5 runtime contract request/response fixtures.

Emits one line per assertion (A01..A19), then a final sentinel:
  OK_CONTRACT_SKELETON   on full pass under --strict-skeleton
  OK_CONTRACT_FINAL      on full pass under --strict-final
  FAIL_CONTRACT_SKELETON / FAIL_CONTRACT_FINAL otherwise.

Exit 0 on full pass; exit 1 on any assertion FAIL or load error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is importable so `libs.common.runtime_contract` resolves.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from libs.common.runtime_contract import run_assertions  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate RP5 runtime contract fixtures (P0.4 skeleton).",
    )
    p.add_argument("--request", required=True, help="Path to request JSON.")
    p.add_argument("--response", required=True, help="Path to response JSON.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--strict-skeleton", action="store_true",
        help="Skeleton mode (P0.4): report_links may be empty strings.",
    )
    mode.add_argument(
        "--strict-final", action="store_true",
        help="Final mode (P9.0): report_links must be non-empty strings.",
    )
    return p.parse_args()


def _emit_a01_fail(msg: str, mode_sentinel: str) -> int:
    print(f"A01 FAIL: {msg}")
    print(f"FAIL_CONTRACT_{mode_sentinel}: A01")
    return 1


def main() -> int:
    args = _parse_args()
    mode_sentinel = "SKELETON" if args.strict_skeleton else "FINAL"

    # A01 — JSON parses
    try:
        with open(args.request, "r", encoding="utf-8") as f:
            request = json.load(f)
    except Exception as e:  # noqa: BLE001
        return _emit_a01_fail(f"request load: {e!r}", mode_sentinel)
    try:
        with open(args.response, "r", encoding="utf-8") as f:
            response = json.load(f)
    except Exception as e:  # noqa: BLE001
        return _emit_a01_fail(f"response load: {e!r}", mode_sentinel)

    if not isinstance(request, dict):
        return _emit_a01_fail(
            f"request top-level is {type(request).__name__}, expected object",
            mode_sentinel,
        )
    if not isinstance(response, dict):
        return _emit_a01_fail(
            f"response top-level is {type(response).__name__}, expected object",
            mode_sentinel,
        )

    results = run_assertions(
        request, response,
        strict_skeleton=args.strict_skeleton,
        strict_final=args.strict_final,
    )

    failed: list[str] = []
    for aid, status, msg in results:
        print(f"{aid} {status}: {msg}")
        if status == "FAIL":
            failed.append(aid)

    if failed:
        print(f"FAIL_CONTRACT_{mode_sentinel}: {','.join(failed)}")
        return 1
    print(f"OK_CONTRACT_{mode_sentinel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
