"""CLI wrapper around MetricGANPlusEnhancer (T4.1).

Enhances a single WAV file using the SpeechBrain MetricGAN+ pretrained model
and writes the enhanced audio under ``--output-dir``. SpeechBrain and its
dependencies must be installed in the active environment; see
``docs/training/metricgan_plus_dependency_notes.md`` for the install pattern.

Example (run inside the training Apptainer image; not executed in T4.1):

    apptainer exec --env ASR_REPO_ROOT="$REPO" \\
                   --env ASR_CACHE_ROOT="$ASR_CACHE_ROOT" \\
                   "$CONTAINER" \\
                   python3 scripts/training/enhance_metricgan_plus.py \\
                       --input  /path/to/degraded.wav \\
                       --output-dir /path/to/output_dir \\
                       --job-id   t4_1_smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from libs.audio.enhancement import MetricGANPlusEnhancer


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enhance a single WAV with MetricGAN+ pretrained.",
    )
    parser.add_argument("--input", type=Path, required=True, help="Path to input WAV.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where the enhanced WAV will be written.",
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default="t4_1_cli",
        help="Job identifier recorded in the diagnostic (default: t4_1_cli).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    enhancer = MetricGANPlusEnhancer()
    result = enhancer.enhance(args.input, args.output_dir, args.job_id)
    payload = {
        "enhancer_version": enhancer.enhancer_version,
        "output_path": str(result.output_path),
        "preset_applied": result.preset_applied,
        "enhanced": result.enhanced,
        "enhancement_fallback": result.enhancement_fallback,
        "diagnostic": result.diagnostic,
    }
    print(json.dumps(payload, indent=2))
    return 0 if result.enhanced else 1


if __name__ == "__main__":
    sys.exit(main())
