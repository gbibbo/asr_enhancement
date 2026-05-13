#!/usr/bin/env python3
"""probe_assemblyai_runtime.py — robust_asr §1748 runtime probe.

Behavior:
  - If ASSEMBLYAI_API_KEY is unset, prints
      "ASSEMBLYAI_RUNTIME=false reason=key_unset"
    and exits 0.
  - Else issues a HEAD request to AssemblyAI with a 5 s timeout.
    On HTTP 200 prints "ASSEMBLYAI_RUNTIME=true reason=health_ok".
    Else prints "ASSEMBLYAI_RUNTIME=false reason=<status_or_error>".
    Always exits 0 (this script is informational; callers decide).

The script never logs or persists the value of ASSEMBLYAI_API_KEY.
"""
from __future__ import annotations

import argparse
import os
import sys

DEFAULT_HEALTH_URL = "https://api.assemblyai.com/v2/transcript"
DEFAULT_TIMEOUT_S = 5.0


def probe(url: str = DEFAULT_HEALTH_URL,
          timeout_s: float = DEFAULT_TIMEOUT_S,
          env: dict | None = None) -> str:
    env = env if env is not None else os.environ
    key = env.get("ASSEMBLYAI_API_KEY")
    if not key:
        return "ASSEMBLYAI_RUNTIME=false reason=key_unset"
    try:
        import requests  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - requests is in the image
        return f"ASSEMBLYAI_RUNTIME=false reason=requests_unavailable:{type(exc).__name__}"
    headers = {"authorization": key}
    try:
        r = requests.head(url, headers=headers, timeout=timeout_s)
    except Exception as exc:
        return f"ASSEMBLYAI_RUNTIME=false reason={type(exc).__name__}"
    if r.status_code == 200:
        return "ASSEMBLYAI_RUNTIME=true reason=health_ok"
    return f"ASSEMBLYAI_RUNTIME=false reason=http_{r.status_code}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_HEALTH_URL)
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    args = ap.parse_args()
    print(probe(args.url, args.timeout))
    return 0


if __name__ == "__main__":
    sys.exit(main())
