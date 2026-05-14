#!/usr/bin/env python3
"""Restore artifacts/robust_asr/handoff/ from a previous handoff tag.

Usage:
    rollback_to_previous_handoff.py handoff/<YYYYMMDD>-<short_sha>

Runs:
    git checkout <tag> -- artifacts/robust_asr/handoff/

Exits 0 on success, non-zero on failure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: rollback_to_previous_handoff.py handoff/<date>-<sha>",
              file=sys.stderr)
        return 2
    tag = sys.argv[1]
    if not tag.startswith("handoff/"):
        print(f"FAIL_ROLLBACK: tag must start with 'handoff/': {tag}",
              file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parents[3]
    verify = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify",
         f"refs/tags/{tag}"],
        capture_output=True, text=True,
    )
    if verify.returncode != 0:
        print(f"FAIL_ROLLBACK: tag not found locally: {tag}", file=sys.stderr)
        return 1

    checkout = subprocess.run(
        ["git", "-C", str(repo_root), "checkout", tag, "--",
         "artifacts/robust_asr/handoff/"],
        capture_output=True, text=True,
    )
    if checkout.returncode != 0:
        print(f"FAIL_ROLLBACK: git checkout failed:\n{checkout.stderr}",
              file=sys.stderr)
        return checkout.returncode

    print(f"OK_ROLLBACK: artifacts/robust_asr/handoff/ restored from {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
