"""B11.1a drift guard: keep the frontend's hardcoded degradation IDs in sync
with the backend registry in libs.audio.degradations.

The /demo page lists the 5 frozen degradation IDs in
services/frontend/app/demo/degradations.ts. Both the order and the set must
match the backend registry. If a future task adds, removes, or renames an
entry in DEGRADATION_REGISTRY without updating the frontend constant, this
test fails and surfaces the drift before a release.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from libs.audio.degradations import DEGRADATION_REGISTRY


EXPECTED_IDS: tuple[str, ...] = (
    "far_field_room",
    "cafe_background",
    "phone_call",
    "muffled",
    "broadband_hiss",
)


def _frontend_constant_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "services"
        / "frontend"
        / "app"
        / "demo"
        / "degradations.ts"
    )


def test_backend_registry_matches_expected_set() -> None:
    assert set(DEGRADATION_REGISTRY.keys()) == set(EXPECTED_IDS)


def test_backend_registry_has_exactly_five_entries() -> None:
    assert len(DEGRADATION_REGISTRY) == 5


def test_frontend_constant_lists_same_ids_in_same_order() -> None:
    ts_path = _frontend_constant_path()
    if not ts_path.exists():
        pytest.fail(f"Expected frontend constant at {ts_path}, but file is missing.")
    text = ts_path.read_text(encoding="utf-8")

    match = re.search(
        r"export const DEGRADATION_IDS\s*=\s*\[(.*?)\]\s*as const;",
        text,
        re.DOTALL,
    )
    assert match is not None, (
        "Could not find `export const DEGRADATION_IDS = [...] as const;` "
        "in services/frontend/app/demo/degradations.ts."
    )
    body = match.group(1)
    quoted = re.findall(r'"([^"\\]+)"', body)
    assert tuple(quoted) == EXPECTED_IDS, (
        "Frontend DEGRADATION_IDS list drifted from the backend registry. "
        f"Frontend has: {quoted!r}. Expected (backend order): {list(EXPECTED_IDS)!r}."
    )


def test_frontend_label_map_covers_all_ids() -> None:
    ts_path = _frontend_constant_path()
    if not ts_path.exists():
        pytest.fail(f"Expected frontend constant at {ts_path}, but file is missing.")
    text = ts_path.read_text(encoding="utf-8")

    match = re.search(
        r"export const DEGRADATION_LABELS:[^=]*=\s*\{(.*?)\};",
        text,
        re.DOTALL,
    )
    assert match is not None, (
        "Could not find `export const DEGRADATION_LABELS: ... = { ... };` "
        "in services/frontend/app/demo/degradations.ts."
    )
    body = match.group(1)
    keys = set(re.findall(r"(\w+)\s*:\s*\"", body))
    missing = set(EXPECTED_IDS) - keys
    assert not missing, f"DEGRADATION_LABELS is missing entries for: {sorted(missing)}"
