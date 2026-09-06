"""B11.1c executable scoring self-test.

Static regex over a numerical helper is not enough. This test compiles
``services/frontend/app/demo/scoring.ts`` inside an ephemeral
``node:20-bookworm-slim`` container and asserts canonical metric values
end-to-end. We deliberately avoid adding a JS test framework to the project
(no jest, no vitest) — the existing TypeScript compiler that ships with the
frontend's dev dependencies is enough.

The test skips when ``docker`` is not on PATH (e.g. running outside the demo
runtime). On RP5 the docker engine and the ``node:20-bookworm-slim`` image
are already present from B11.1a/B11.1b, so the test runs without prep.

Side effects:
  * ``services/frontend/node_modules`` may be created or refreshed inside
    the host bind-mount; it is gitignored so the working tree stays clean.
  * Compiled JS output goes to ``/tmp/b11_1c_scoring`` inside the container
    only — never written to the host workspace.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _REPO_ROOT / "services" / "frontend"
_NODE_IMAGE = "node:20-bookworm-slim"


_RUN_SCRIPT = r"""
set -eu
cd /app
if [ ! -x ./node_modules/.bin/tsc ]; then
  npm ci --no-audit --no-fund >/dev/null 2>&1
fi
./node_modules/.bin/tsc app/demo/scoring.ts \
    --target ES2020 --module commonjs \
    --outDir /tmp/b11_1c_scoring --skipLibCheck >/dev/null
cat > /tmp/runner.js <<'NODE'
const { computeMetrics, normalizeText } = require("/tmp/b11_1c_scoring/scoring.js");

function approx(a, b) {
  if (Math.abs(a - b) > 1e-9) {
    throw new Error("approx failed: " + a + " != " + b);
  }
}
function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

// --- normalization ----------------------------------------------------
assert(normalizeText("Hello, WORLD!") === "hello world", "basic normalization");
assert(normalizeText("Hugh's written") === "hughs written", "apostrophe stripped");
assert(normalizeText("  multiple   spaces  ") === "multiple spaces", "whitespace collapse");
assert(normalizeText("") === "", "empty input -> empty");

// --- exact match ------------------------------------------------------
let m = computeMetrics("hello world", "hello world");
assert(m.available === true, "exact-match available");
approx(m.wer, 0);
approx(m.wordAccuracy, 1);

// --- empty hypothesis with non-empty reference ------------------------
m = computeMetrics("", "hello world");
assert(m.available === true, "empty-hyp available");
approx(m.wer, 1);
approx(m.wordAccuracy, 0);

// --- one substitution -------------------------------------------------
m = computeMetrics("hello there", "hello world");
assert(m.available === true, "substitution available");
approx(m.wer, 0.5);
approx(m.wordAccuracy, 0.5);

// --- one deletion -----------------------------------------------------
m = computeMetrics("hello", "hello world");
assert(m.available === true, "deletion available");
approx(m.wer, 0.5);
approx(m.wordAccuracy, 0.5);

// --- one insertion ----------------------------------------------------
m = computeMetrics("hello brave world", "hello world");
assert(m.available === true, "insertion available");
approx(m.wer, 0.5);
approx(m.wordAccuracy, 0.5);

// --- WER > 1 clamps wordAccuracy to 0 --------------------------------
m = computeMetrics("a b c d", "x");
assert(m.available === true, "high-WER available");
assert(m.wer > 1, "WER must exceed 1: got " + m.wer);
approx(m.wordAccuracy, 0);

// --- empty reference --------------------------------------------------
m = computeMetrics("anything", "");
assert(m.available === false, "empty reference unavailable");
assert(m.wer === null, "empty reference WER null");
assert(m.wordAccuracy === null, "empty reference WA null");

// --- whitespace-only reference ---------------------------------------
m = computeMetrics("anything", "   \t  ");
assert(m.available === false, "whitespace reference unavailable");
assert(m.wer === null, "whitespace reference WER null");
assert(m.wordAccuracy === null, "whitespace reference WA null");

// --- case + punctuation fold compares as same ------------------------
m = computeMetrics("Hello, World!", "hello world");
assert(m.available === true, "case-fold available");
approx(m.wer, 0);
approx(m.wordAccuracy, 1);

console.log("scoring self-test passed");
NODE
node /tmp/runner.js
rm -f /tmp/runner.js
rm -rf /tmp/b11_1c_scoring
"""


@pytest.fixture(scope="module")
def docker_bin() -> str:
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("docker not on PATH; executable scoring self-test skipped.")
    return docker


def test_scoring_self_test_runs_in_node_20(docker_bin: str) -> None:
    cmd = [
        docker_bin,
        "run",
        "--rm",
        "-v",
        f"{_FRONTEND_DIR}:/app",
        "-w",
        "/app",
        _NODE_IMAGE,
        "sh",
        "-c",
        _RUN_SCRIPT,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, (
        f"scoring self-test exited non-zero: rc={proc.returncode}\n"
        f"--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}"
    )
    assert "scoring self-test passed" in proc.stdout, (
        "scoring self-test stdout missing success marker:\n"
        f"--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}"
    )
