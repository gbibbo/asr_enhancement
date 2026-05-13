#!/usr/bin/env python3
"""build_selector_evidence_table.py — robust_asr P6.1 (Outcome E).

Builds artifacts/robust_asr/router/selector_evidence.parquet from the
deployable backend eval tables, applying the Section 5.5 deterministic
selector to every audio_id under OUTCOME_E_DETERMINISTIC_SELECTOR.

Schema (per agent plan §982-§1001 and §1498-§1513):

  audio_id                          str
  reference_normalized              str
  whisper_base_ct2_int8_wer         float
  whisper_base_ct2_int8_latency_ms  float
  selected_action                   str  in {whisper_base_ct2_int8,
                                              assemblyai,
                                              whisper_lora_ct2_int8,
                                              ask_repeat}
  selector_reason                   str
  ask_repeat_allowed                bool
  assemblyai_available              bool
  lora_available                    bool
  no_speech_prob_proxy              float  (0.0 or 1.0)
  avg_logprob_proxy                 float  (0.0 default; not exposed in P2.1 table)
  whisper_base_ct2_int8_wa          float
  condition_family                  str
  degradation_id                    str
  source_split                      str
  deterministic_selector_version    str
  normalization_version             str

Output: a single parquet with one row per audio_id and a stdout sentinel
  OK_SELECTOR_EVIDENCE_BUILD rows=<N>

Exit codes: 0 PASS, 1 FAIL.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

# Make libs/common importable for the version constants.
sys.path.insert(0, str(REPO_ROOT))
from libs.common.versions import (  # noqa: E402
    DETERMINISTIC_SELECTOR_VERSION,
    NORMALIZATION_VERSION,
)


def deterministic_select(
    no_speech_prob: float,
    avg_logprob: float,
    *,
    assemblyai_available: bool,
    lora_available: bool,
    ask_repeat_threshold: float,
    escalate_threshold: float,
    no_speech_threshold: float,
) -> tuple[str, str]:
    """Reference implementation of agent plan Section 5.5.

    Returns (selected_action, selector_reason).

    Note: lora_available is consumed by the validator but does not change
    the Section 5.5 predicate (which never returns
    whisper_lora_ct2_int8 directly — LoRA selection is the router's job).
    """
    if no_speech_prob > no_speech_threshold:
        return "ask_repeat", "no_speech"
    if avg_logprob < ask_repeat_threshold:
        return "ask_repeat", "low_logprob"
    if assemblyai_available and avg_logprob < escalate_threshold:
        return "assemblyai", "escalate_cloud"
    return "whisper_base_ct2_int8", "baseline"


def _required_eval_columns() -> list[str]:
    return [
        "audio_id",
        "reference_normalized",
        "normalized_transcript",
        "wer",
        "wa",
        "backend_latency_ms",
        "backend_name",
        "condition_family",
        "degradation_id",
        "source_split",
    ]


def _load_backend_table(path: Path, expected_backend: str) -> pa.Table:
    if not path.exists():
        raise FileNotFoundError(f"backend table not found: {path}")
    table = pq.read_table(path)
    missing = [c for c in _required_eval_columns() if c not in table.column_names]
    if missing:
        raise ValueError(f"{path}: missing required columns {missing}")
    distinct = set(table.column("backend_name").to_pylist())
    if distinct != {expected_backend}:
        raise ValueError(
            f"{path}: expected backend_name={expected_backend!r}, got {distinct}"
        )
    return table


def build(
    backend_tables: list[Path],
    cfg: dict,
    out_path: Path,
) -> int:
    if not backend_tables:
        print("FAIL_SELECTOR_EVIDENCE_BUILD: no backend tables supplied", file=sys.stderr)
        return 1

    sev_cfg = cfg["selector_evidence"]
    det_cfg = cfg["deterministic_selector"]

    assemblyai_available = bool(sev_cfg["assemblyai_available"])
    lora_available = bool(sev_cfg["lora_available"])

    ask_repeat_threshold = float(det_cfg["ask_repeat_threshold"])
    escalate_threshold = float(det_cfg["escalate_threshold"])
    no_speech_threshold = float(det_cfg["no_speech_threshold"])

    proxy_cfg = sev_cfg["no_speech_proxy"]
    if proxy_cfg["source"] != "empty_normalized_transcript":
        print(
            f"FAIL_SELECTOR_EVIDENCE_BUILD: unsupported no_speech_proxy source "
            f"{proxy_cfg['source']!r}",
            file=sys.stderr,
        )
        return 1
    value_when_empty = float(proxy_cfg["value_when_empty"])
    value_when_nonempty = float(proxy_cfg["value_when_nonempty"])
    avg_logprob_default = float(sev_cfg["avg_logprob_default"])

    # Currently OUTCOME_E gives a single deployable backend; the build is
    # written so additional deployable backends could be joined here. For
    # P6.1 we hard-require whisper_base_ct2_int8 as the per-row source of
    # WER/latency/WA columns named in the validator schema.
    base_table_path = backend_tables[0]
    base = _load_backend_table(base_table_path, "whisper_base_ct2_int8")

    audio_id = base.column("audio_id").to_pylist()
    reference_normalized = base.column("reference_normalized").to_pylist()
    normalized_transcript = base.column("normalized_transcript").to_pylist()
    wer = base.column("wer").to_pylist()
    wa = base.column("wa").to_pylist()
    latency_ms = base.column("backend_latency_ms").to_pylist()
    condition_family = base.column("condition_family").to_pylist()
    degradation_id = base.column("degradation_id").to_pylist()
    source_split = base.column("source_split").to_pylist()

    n = len(audio_id)
    if n == 0:
        print(
            "FAIL_SELECTOR_EVIDENCE_BUILD: backend table has zero rows",
            file=sys.stderr,
        )
        return 1

    seen = set()
    duplicates: list[str] = []
    selected_action: list[str] = []
    selector_reason: list[str] = []
    no_speech_proxy_vals: list[float] = []
    avg_logprob_vals: list[float] = []

    for i in range(n):
        aid = audio_id[i]
        if aid in seen:
            duplicates.append(aid)
        seen.add(aid)

        nt = normalized_transcript[i]
        is_empty = (nt is None) or (str(nt).strip() == "")
        ns_proxy = value_when_empty if is_empty else value_when_nonempty
        no_speech_proxy_vals.append(ns_proxy)
        avg_logprob_vals.append(avg_logprob_default)

        action, reason = deterministic_select(
            no_speech_prob=ns_proxy,
            avg_logprob=avg_logprob_default,
            assemblyai_available=assemblyai_available,
            lora_available=lora_available,
            ask_repeat_threshold=ask_repeat_threshold,
            escalate_threshold=escalate_threshold,
            no_speech_threshold=no_speech_threshold,
        )
        selected_action.append(action)
        selector_reason.append(reason)

    if duplicates:
        print(
            f"FAIL_SELECTOR_EVIDENCE_BUILD: duplicate audio_id rows "
            f"({len(duplicates)} duplicates, first={duplicates[0]!r})",
            file=sys.stderr,
        )
        return 1

    ask_repeat_allowed = [True] * n
    assemblyai_avail_col = [assemblyai_available] * n
    lora_avail_col = [lora_available] * n
    det_ver_col = [DETERMINISTIC_SELECTOR_VERSION] * n
    norm_ver_col = [NORMALIZATION_VERSION] * n

    out = pa.table(
        {
            "audio_id": audio_id,
            "reference_normalized": reference_normalized,
            "whisper_base_ct2_int8_wer": wer,
            "whisper_base_ct2_int8_latency_ms": latency_ms,
            "whisper_base_ct2_int8_wa": wa,
            "selected_action": selected_action,
            "selector_reason": selector_reason,
            "ask_repeat_allowed": ask_repeat_allowed,
            "assemblyai_available": assemblyai_avail_col,
            "lora_available": lora_avail_col,
            "no_speech_prob_proxy": no_speech_proxy_vals,
            "avg_logprob_proxy": avg_logprob_vals,
            "condition_family": condition_family,
            "degradation_id": degradation_id,
            "source_split": source_split,
            "deterministic_selector_version": det_ver_col,
            "normalization_version": norm_ver_col,
        }
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(out, out_path, compression="snappy")

    print(f"OK_SELECTOR_EVIDENCE_BUILD rows={n}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--backend-tables",
        nargs="+",
        required=True,
        help="One or more backend eval-table parquet files (deployable backends only).",
    )
    ap.add_argument(
        "--selector-config",
        required=True,
        help="Path to configs/robust_asr/router_v1.yaml.",
    )
    ap.add_argument(
        "--out",
        required=True,
        help="Output parquet path (artifacts/robust_asr/router/selector_evidence.parquet).",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    cfg = yaml.safe_load(Path(args.selector_config).read_text())
    backend_tables = [Path(p) for p in args.backend_tables]
    return build(backend_tables, cfg, Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
