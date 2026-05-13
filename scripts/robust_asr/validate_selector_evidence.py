#!/usr/bin/env python3
"""validate_selector_evidence.py — robust_asr P6.1 (Outcome E) validator.

Asserts agent plan §982-§1001 on the selector-evidence parquet:

  1. File exists and has non-zero rows.
  2. Required columns present.
  3. selected_action in {whisper_base_ct2_int8, assemblyai,
     whisper_lora_ct2_int8, ask_repeat}.
  4. assemblyai_available == False  =>  selected_action never assemblyai.
  5. lora_available == False        =>  selected_action never whisper_lora_ct2_int8.
  6. Every audio_id disjoint from demo examples and from any LoRA
     fine-tuning audio_id.

Stdout sentinel: OK_SELECTOR_EVIDENCE on PASS.
Exit codes: 0 PASS, 1 FAIL with the failing assertion key on stderr.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_COLUMNS = [
    "audio_id",
    "reference_normalized",
    "whisper_base_ct2_int8_wer",
    "whisper_base_ct2_int8_latency_ms",
    "selected_action",
    "selector_reason",
    "ask_repeat_allowed",
    "assemblyai_available",
    "lora_available",
]

SELECTED_ACTION_CODOMAIN = {
    "whisper_base_ct2_int8",
    "assemblyai",
    "whisper_lora_ct2_int8",
    "ask_repeat",
}

# Demo-examples manifest is produced by P8.2; treated as empty pre-P8.2.
DEMO_MANIFEST = REPO_ROOT / "artifacts" / "robust_asr" / "demo" / "demo_examples_manifest.json"

# LoRA fine-tuning manifests; restricted to audio_ids that LoRA actually
# trained on (smoke or full). Full LoRA is SKIPPED_BY_DECISION_A, so only
# the smoke train manifest is in scope.
LORA_TRAIN_MANIFESTS = [
    REPO_ROOT / "artifacts" / "robust_asr" / "manifests" / "librispeech_lora_train.parquet",
]


def _eval_base_stem(audio_id: str) -> str:
    """Strip ``::<degradation_id>`` suffix from an eval audio_id.

    Eval rows look like ``librispeech/dev-clean/1272-128104-0000::clean::id``;
    LoRA train rows look like ``librispeech/train-clean-100/103-1240-0000``.
    Disjointness is checked at the LoRA-side granularity (no suffix).
    """
    return audio_id.split("::", 1)[0]


def _load_demo_ids() -> set[str]:
    if not DEMO_MANIFEST.exists():
        return set()
    try:
        data = json.loads(DEMO_MANIFEST.read_text())
    except Exception as e:
        raise RuntimeError(f"could not parse {DEMO_MANIFEST}: {e}") from e
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("examples") or data.get("audio_ids") or []
    else:
        items = []
    return {x if isinstance(x, str) else x.get("audio_id") for x in items} - {None}


def _load_lora_train_ids() -> set[str]:
    ids: set[str] = set()
    for path in LORA_TRAIN_MANIFESTS:
        if not path.exists():
            continue
        table = pq.read_table(path, columns=["audio_id"])
        ids.update(table.column("audio_id").to_pylist())
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"FAIL_SELECTOR_EVIDENCE: file_not_found path={in_path}", file=sys.stderr)
        return 1

    table = pq.read_table(in_path)
    n = table.num_rows
    if n == 0:
        print("FAIL_SELECTOR_EVIDENCE: zero_rows", file=sys.stderr)
        return 1

    missing = [c for c in REQUIRED_COLUMNS if c not in table.column_names]
    if missing:
        print(f"FAIL_SELECTOR_EVIDENCE: missing_columns {missing}", file=sys.stderr)
        return 1

    selected_action = table.column("selected_action").to_pylist()
    assemblyai_available = table.column("assemblyai_available").to_pylist()
    lora_available = table.column("lora_available").to_pylist()
    audio_id = table.column("audio_id").to_pylist()

    # 3. codomain
    bad = {a for a in selected_action if a not in SELECTED_ACTION_CODOMAIN}
    if bad:
        print(f"FAIL_SELECTOR_EVIDENCE: bad_selected_action {bad}", file=sys.stderr)
        return 1

    # 4. assemblyai_available=false  =>  never assemblyai
    for i in range(n):
        if (not assemblyai_available[i]) and selected_action[i] == "assemblyai":
            print(
                f"FAIL_SELECTOR_EVIDENCE: assemblyai_selected_without_availability "
                f"row={i} audio_id={audio_id[i]!r}",
                file=sys.stderr,
            )
            return 1

    # 5. lora_available=false  =>  never whisper_lora_ct2_int8
    for i in range(n):
        if (not lora_available[i]) and selected_action[i] == "whisper_lora_ct2_int8":
            print(
                f"FAIL_SELECTOR_EVIDENCE: lora_selected_without_availability "
                f"row={i} audio_id={audio_id[i]!r}",
                file=sys.stderr,
            )
            return 1

    # 6. disjointness vs demo + LoRA train
    demo_ids = _load_demo_ids()
    lora_ids = _load_lora_train_ids()

    eval_stems = {_eval_base_stem(a) for a in audio_id}
    eval_ids = set(audio_id)

    demo_overlap = (eval_ids & demo_ids) | (eval_stems & demo_ids)
    if demo_overlap:
        sample = next(iter(demo_overlap))
        print(
            f"FAIL_SELECTOR_EVIDENCE: demo_overlap count={len(demo_overlap)} "
            f"sample={sample!r}",
            file=sys.stderr,
        )
        return 1

    lora_overlap = (eval_ids & lora_ids) | (eval_stems & lora_ids)
    if lora_overlap:
        sample = next(iter(lora_overlap))
        print(
            f"FAIL_SELECTOR_EVIDENCE: lora_overlap count={len(lora_overlap)} "
            f"sample={sample!r}",
            file=sys.stderr,
        )
        return 1

    print("OK_SELECTOR_EVIDENCE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
