"""Unit tests for the P0.4 runtime contract validator.

Covers:
  - The skeleton fixtures pass all 19 assertions (--strict-skeleton).
  - For each of A01..A19, a targeted mutation makes the validator fail
    with that assertion id reported in the FAIL_CONTRACT_SKELETON line.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "robust_asr" / "validate_runtime_contract.py"
REQ_FIXTURE = REPO_ROOT / "artifacts" / "robust_asr" / "runtime_contract" / "rp5_request_fixture.json"
RES_FIXTURE = REPO_ROOT / "artifacts" / "robust_asr" / "runtime_contract" / "rp5_response_fixture.json"


def _load_fixtures() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with open(REQ_FIXTURE, "r", encoding="utf-8") as f:
        req = json.load(f)
    with open(RES_FIXTURE, "r", encoding="utf-8") as f:
        res = json.load(f)
    return req, res


def _run(req_path: Path, res_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--strict-skeleton",
            "--request", str(req_path),
            "--response", str(res_path),
        ],
        capture_output=True, text=True, check=False,
    )


def test_skeleton_fixtures_pass() -> None:
    proc = _run(REQ_FIXTURE, RES_FIXTURE)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK_CONTRACT_SKELETON" in proc.stdout
    for i in range(1, 20):
        aid = f"A{i:02d}"
        assert f"{aid} PASS" in proc.stdout, (aid, proc.stdout)


# ---------------------------------------------------------------------------
# Mutations: each mutator turns a known-good pair of fixtures into one that
# violates exactly one assertion. The validator must FAIL with that aid.
# ---------------------------------------------------------------------------

# A01: malformed JSON in request
def _mut_a01_request_malformed(tmp: Path) -> Tuple[Path, Path]:
    bad_req = tmp / "request_bad.json"
    bad_req.write_text("{not-json", encoding="utf-8")
    res = tmp / "response.json"
    _, r = _load_fixtures()
    res.write_text(json.dumps(r), encoding="utf-8")
    return bad_req, res


def _write_mut(tmp: Path, mutate: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> Tuple[Path, Path]:
    req, res = _load_fixtures()
    req = copy.deepcopy(req)
    res = copy.deepcopy(res)
    mutate(req, res)
    rp = tmp / "request.json"
    sp = tmp / "response.json"
    rp.write_text(json.dumps(req), encoding="utf-8")
    sp.write_text(json.dumps(res), encoding="utf-8")
    return rp, sp


MUTATIONS: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], None]] = {
    "A02": lambda q, s: s.__setitem__("request_id", "ZZZZZZZZ-ZZZZ-4ZZZ-8ZZZ-ZZZZZZZZZZZZ"),
    "A03": lambda q, s: q["audio"].__setitem__("encoding", "mp3"),
    "A04": lambda q, s: q["audio"].__setitem__("sample_rate_hz", 8000),
    "A05": lambda q, s: q["audio"].__setitem__("channels", 2),
    "A06": lambda q, s: q["audio"].__setitem__("duration_s", 0),
    "A07": lambda q, s: q["audio"].__setitem__("sha256", "not-hex"),
    "A08": lambda q, s: q["constraints"].__setitem__("profile", "fastest"),
    "A09": lambda q, s: q["constraints"].__setitem__("allow_third_party", "yes"),
    "A10": lambda q, s: q["constraints"].__setitem__("max_latency_ms", 0),
    "A11": lambda q, s: s.__setitem__("ask_repeat", "false"),
    # A12: ask_repeat=False, errors=[] but transcript=null -> RHS False, LHS True
    "A12": lambda q, s: s.__setitem__("transcript", None),
    # A13: ask_repeat=False but selected_backend=null -> LHS True, RHS False
    "A13": lambda q, s: s.__setitem__("selected_backend", None),
    "A14": lambda q, s: s.__setitem__("router_kind", "magic"),
    "A15": lambda q, s: s.__setitem__("cost_usd", -0.01),
    # A16: claim AssemblyAI as backend without matching provider
    "A16": lambda q, s: (
        s.__setitem__("selected_backend", "assemblyai"),
        s.__setitem__("third_party_provider", None),
    ),
    "A17": lambda q, s: s["latency_ms"].__setitem__("end_to_end", 1),
    "A18": lambda q, s: s.__setitem__("confidence", 1.5),
    "A19": lambda q, s: s["report_links"].__setitem__("model_card", 123),
}


@pytest.mark.parametrize("aid", sorted(MUTATIONS.keys()))
def test_mutation_fails_named_assertion(tmp_path: Path, aid: str) -> None:
    rp, sp = _write_mut(tmp_path, MUTATIONS[aid])
    proc = _run(rp, sp)
    assert proc.returncode == 1, (aid, proc.stdout, proc.stderr)
    # Validator emits "FAIL_CONTRACT_SKELETON: <aid_list>" on the last line.
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("FAIL_CONTRACT_SKELETON")]
    assert lines, (aid, proc.stdout)
    assert aid in lines[-1], (aid, lines[-1])
    assert f"{aid} FAIL" in proc.stdout, (aid, proc.stdout)


def test_mutation_a01_request_malformed(tmp_path: Path) -> None:
    rp, sp = _mut_a01_request_malformed(tmp_path)
    proc = _run(rp, sp)
    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert "A01 FAIL" in proc.stdout, proc.stdout
    assert "FAIL_CONTRACT_SKELETON: A01" in proc.stdout, proc.stdout
