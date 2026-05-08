#!/usr/bin/env python3
"""Speaker-disjoint check for robust_asr split labels.

Reads configs/robust_asr/data_v1.yaml and asserts that, for every
declared `disjoint_constraints` entry, the union of `speakers` in the
listed splits is pairwise disjoint.

Empty splits are allowed (P1.1 may declare splits whose audio is not yet
present on host); empty splits trivially satisfy disjointness. The check
emits OK_SPEAKER_DISJOINT to stdout on success.

Exit codes:
  0  OK_SPEAKER_DISJOINT
  2  configuration error (missing config or malformed entries)
  3  disjointness violation
"""
from __future__ import annotations

import argparse
import sys
from itertools import combinations
from pathlib import Path

import yaml


def _split_speaker_set(cfg: dict, name: str) -> set:
    splits = cfg.get("splits") or {}
    s = splits.get(name)
    if s is None:
        raise SystemExit(f"ERROR: split label not declared: {name}")
    return set(str(x) for x in (s.get("speakers") or []))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/robust_asr/data_v1.yaml",
        help="Path to data_v1.yaml",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=None,
        help="Optional explicit list of split labels; overrides "
        "disjoint_constraints in the config",
    )
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_file():
        print(f"ERROR: config not found: {cfg_path}", file=sys.stderr)
        return 2
    cfg = yaml.safe_load(cfg_path.read_text())

    if args.splits:
        constraints = [{"splits": list(args.splits), "keys": ["speaker_id"]}]
    else:
        constraints = cfg.get("disjoint_constraints") or []
        if not constraints:
            print("ERROR: no disjoint_constraints in config", file=sys.stderr)
            return 2

    violations = []
    for entry in constraints:
        names = entry.get("splits") or []
        sets = {n: _split_speaker_set(cfg, n) for n in names}
        for a, b in combinations(names, 2):
            overlap = sets[a] & sets[b]
            if overlap:
                violations.append((a, b, sorted(overlap)))

    if violations:
        for a, b, ov in violations:
            print(
                f"VIOLATION: speaker overlap between {a} and {b}: "
                f"{len(ov)} ids: {ov[:10]}{'...' if len(ov) > 10 else ''}",
                file=sys.stderr,
            )
        return 3

    print("OK_SPEAKER_DISJOINT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
