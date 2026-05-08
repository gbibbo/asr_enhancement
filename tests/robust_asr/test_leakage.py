"""P1.2 — Leakage tests (Section 3 leakage guard).

Five named tests:
  - test_speaker_disjoint_lora_vs_router_train
  - test_audio_id_disjoint_lora_train_vs_router_targets
  - test_locked_test_sets_disjoint_from_train
  - test_demo_examples_disjoint_from_eval_sets
  - test_common_voice_demo_disjoint_from_ood_locked

Each test, on failure, writes the intersecting IDs to
reports/robust_asr/leakage/<test_name>.failure.txt and asserts via
pytest. Section 3 manifest data is not yet built (P1.3); placeholder
audio_id fixtures are derived from the data_v1.yaml speaker partition.

OOD-real-dependent tests honor claims_enabled.ood_real=false (current
state under BLOCKED_OOD_PUBLIC) by treating empty splits as trivially
disjoint and recording a SKIP_OOD_PUBLIC_DEFERRED note in the failure
artifact directory if ever invoked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Set

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_V1 = REPO_ROOT / "configs" / "robust_asr" / "data_v1.yaml"
LEAKAGE_DIR = REPO_ROOT / "reports" / "robust_asr" / "leakage"


@pytest.fixture(scope="module")
def data_v1():
    with open(DATA_V1, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _speakers(data_v1, split: str) -> Set[str]:
    spec = data_v1["splits"].get(split) or {}
    return {str(s) for s in (spec.get("speakers") or [])}


def _record_intersection(test_name: str, intersection: Iterable) -> Path:
    LEAKAGE_DIR.mkdir(parents=True, exist_ok=True)
    p = LEAKAGE_DIR / f"{test_name}.failure.txt"
    with open(p, "w", encoding="utf-8") as f:
        for item in sorted(map(str, intersection)):
            f.write(item + "\n")
    return p


def _assert_disjoint(test_name: str, a: Set, b: Set) -> None:
    inter = a & b
    if inter:
        artifact = _record_intersection(test_name, inter)
        pytest.fail(
            f"intersection of size {len(inter)}: e.g. {sorted(map(str, inter))[:5]}; "
            f"written to {artifact}"
        )


def _placeholder_audio_ids(speakers: Iterable, k: int = 3) -> Set[str]:
    """Synthesize stable audio_ids from a speaker set (placeholder for P1.3)."""
    out: Set[str] = set()
    for spk in speakers:
        for j in range(1, k + 1):
            out.add(f"placeholder-{spk}-utt{j:03d}")
    return out


# --- 1. speaker_disjoint_lora_vs_router_train ------------------------------


def test_speaker_disjoint_lora_vs_router_train(data_v1) -> None:
    lora = _speakers(data_v1, "lora_train")
    router = _speakers(data_v1, "router_train")
    assert lora, "lora_train speakers must be non-empty after P1.1"
    assert router, "router_train speakers must be non-empty after P1.1"
    _assert_disjoint("test_speaker_disjoint_lora_vs_router_train", lora, router)


# --- 2. audio_id_disjoint_lora_train_vs_router_targets ---------------------


def test_audio_id_disjoint_lora_train_vs_router_targets(data_v1) -> None:
    lora_ids = _placeholder_audio_ids(_speakers(data_v1, "lora_train"))
    # "router targets" at this stage is router_train (real manifests at P1.3).
    router_ids = _placeholder_audio_ids(_speakers(data_v1, "router_train"))
    assert lora_ids and router_ids, "placeholder audio_id sets must be non-empty"
    _assert_disjoint(
        "test_audio_id_disjoint_lora_train_vs_router_targets", lora_ids, router_ids
    )


# --- 3. locked_test_sets_disjoint_from_train -------------------------------


def test_locked_test_sets_disjoint_from_train(data_v1) -> None:
    train = _speakers(data_v1, "lora_train") | _speakers(data_v1, "router_train")
    locked = _speakers(data_v1, "locked_test")
    assert train, "training speaker set must be non-empty after P1.1"
    assert locked, "locked_test speakers must be non-empty after P1.1"
    _assert_disjoint(
        "test_locked_test_sets_disjoint_from_train", train, locked
    )


# --- 4. demo_examples_disjoint_from_eval_sets ------------------------------


def test_demo_examples_disjoint_from_eval_sets(data_v1) -> None:
    # demo manifests are produced at P8.2; under BLOCKED_OOD_PUBLIC the
    # common_voice_demo_reserved split is empty. We construct a placeholder
    # demo set from common_voice_demo_reserved (currently empty) plus any
    # future LibriSpeech-derived demo seeds; eval sets are validation +
    # locked_test + ood_real_locked.
    demo = _speakers(data_v1, "common_voice_demo_reserved")
    eval_set = (
        _speakers(data_v1, "validation")
        | _speakers(data_v1, "locked_test")
        | _speakers(data_v1, "ood_real_locked")
    )
    # Empty demo set is trivially disjoint; record SKIP note.
    if not demo:
        LEAKAGE_DIR.mkdir(parents=True, exist_ok=True)
        with open(LEAKAGE_DIR / "test_demo_examples_disjoint_from_eval_sets.note.txt", "w", encoding="utf-8") as f:
            f.write(
                "SKIP_OOD_PUBLIC_DEFERRED: demo split empty under BLOCKED_OOD_PUBLIC; "
                "claims_enabled.ood_real=false. Re-run when P8.2 produces real demo manifests.\n"
            )
    _assert_disjoint(
        "test_demo_examples_disjoint_from_eval_sets", demo, eval_set
    )


# --- 5. common_voice_demo_disjoint_from_ood_locked -------------------------


def test_common_voice_demo_disjoint_from_ood_locked(data_v1) -> None:
    cv_demo = _speakers(data_v1, "common_voice_demo_reserved")
    ood = _speakers(data_v1, "ood_real_locked")
    if not cv_demo and not ood:
        LEAKAGE_DIR.mkdir(parents=True, exist_ok=True)
        with open(LEAKAGE_DIR / "test_common_voice_demo_disjoint_from_ood_locked.note.txt", "w", encoding="utf-8") as f:
            f.write(
                "SKIP_OOD_PUBLIC_DEFERRED: both splits empty under BLOCKED_OOD_PUBLIC; "
                "claims_enabled.ood_real=false. Re-run when Common Voice + OOD-real are populated.\n"
            )
    _assert_disjoint(
        "test_common_voice_demo_disjoint_from_ood_locked", cv_demo, ood
    )
