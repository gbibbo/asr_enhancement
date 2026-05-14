#!/usr/bin/env python3
"""Verify a robust_asr handoff package directory.

Implements the 7 assertions defined in
docs/plans/robust_asr_agent_plan_v3_4_7.md Section 4, lines 1037-1055:

  1. README.md has the 8 numbered sections from P9.1 in order.
  2. Every artifact in README Section 2 exists at the listed path with
     matching SHA-256.
  3. handoff_smoke.py is executable.
  4. rollback_to_previous_handoff.py is executable.
  5. handoff_validation_template.md exists.
  6. Backend configs do not contain literal secrets
     (grep for ASSEMBLYAI_API_KEY, sk_, Bearer ).
  7. If --strict, a tag of the form handoff/<date>-<short_sha> exists
     locally and on origin.

Emits OK_HANDOFF_PACKAGE on full PASS.
Exit 0 on PASS; exit 1 on any FAIL.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "1. Purpose and scope",
    "2. Artifacts and checksums",
    "3. Reproduction commands",
    "4. Runtime contract",
    "5. Smoke and rollback scripts",
    "6. Risks, limits, disabled claims",
    "7. Provenance",
    "8. Contact and license",
]

SECRET_PATTERNS = [
    "ASSEMBLYAI_API_KEY",
    "sk_",
    "Bearer ",
]

ARTIFACT_TABLE_RE = re.compile(
    r"^\|\s*`?(?P<path>[^`|]+?)`?\s*\|\s*`?(?P<sha>[0-9a-f]{64})`?\s*\|",
    re.MULTILINE,
)


def emit(aid: str, ok: bool, msg: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"{aid} {status}: {msg}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_readme_sections(readme_path: Path, failed: list) -> str:
    if not readme_path.is_file():
        emit("A1", False, f"README.md not found at {readme_path}")
        failed.append("A1")
        return ""
    text = readme_path.read_text(encoding="utf-8")
    last_idx = -1
    for section in REQUIRED_SECTIONS:
        idx = text.find(section)
        if idx == -1:
            emit("A1", False, f"section heading missing: {section!r}")
            failed.append("A1")
            return text
        if idx < last_idx:
            emit("A1", False, f"section out of order: {section!r}")
            failed.append("A1")
            return text
        last_idx = idx
    emit("A1", True, "8 numbered README sections present in order")
    return text


def assert_artifact_checksums(handoff_dir: Path, readme_text: str,
                              failed: list) -> None:
    rows = list(ARTIFACT_TABLE_RE.finditer(readme_text))
    if not rows:
        emit("A2", False, "no artifact rows found in README Section 2")
        failed.append("A2")
        return
    checked = 0
    for m in rows:
        rel = m.group("path").strip()
        expected = m.group("sha").strip().lower()
        if rel.startswith("path "):
            continue
        if "----" in rel:
            continue
        artifact = (handoff_dir / rel).resolve()
        if not artifact.is_file():
            emit("A2", False, f"artifact missing: {rel}")
            failed.append("A2")
            return
        actual = sha256_file(artifact)
        if actual != expected:
            emit("A2", False,
                 f"sha256 mismatch for {rel}: expected {expected} got {actual}")
            failed.append("A2")
            return
        checked += 1
    emit("A2", True, f"{checked} artifact(s) verified with matching SHA-256")


def assert_executable(path: Path, aid: str, failed: list) -> None:
    if not path.is_file():
        emit(aid, False, f"file missing: {path}")
        failed.append(aid)
        return
    mode = path.stat().st_mode
    if not (mode & 0o111):
        emit(aid, False, f"file not executable: {path} (mode={oct(mode)})")
        failed.append(aid)
        return
    emit(aid, True, f"{path.name} is executable (mode={oct(mode & 0o777)})")


def assert_validation_template(handoff_dir: Path, failed: list) -> None:
    p = handoff_dir / "handoff_validation_template.md"
    if not p.is_file():
        emit("A5", False, f"handoff_validation_template.md missing at {p}")
        failed.append("A5")
        return
    emit("A5", True, "handoff_validation_template.md present")


def assert_no_secrets(handoff_dir: Path, failed: list) -> None:
    # Per agent plan §1049-1050: "Backend configs do not contain literal
    # secrets (grep for ASSEMBLYAI_API_KEY, sk_, Bearer )." The scope is
    # the backend_configs/ subtree only — disclosure prose elsewhere
    # (README §6, validation template) legitimately names these strings.
    backend_dir = handoff_dir / "backend_configs"
    if not backend_dir.is_dir():
        emit("A6", False,
             f"backend_configs/ missing under {handoff_dir}")
        failed.append("A6")
        return
    findings: list[str] = []
    for root, _dirs, files in os.walk(backend_dir):
        for name in files:
            fp = Path(root) / name
            try:
                data = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in SECRET_PATTERNS:
                if pat in data:
                    findings.append(f"{fp.relative_to(handoff_dir)}: {pat}")
    if findings:
        emit("A6", False, f"backend config secret-like strings found: {findings}")
        failed.append("A6")
        return
    emit("A6", True,
         "no ASSEMBLYAI_API_KEY / sk_ / Bearer in backend_configs/")


def assert_tag(failed: list) -> None:
    today = subprocess.check_output(
        ["date", "-u", "+%Y%m%d"], text=True
    ).strip()
    short_sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], text=True
    ).strip()
    tag = f"handoff/{today}-{short_sha}"

    local = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
        capture_output=True, text=True,
    )
    if local.returncode != 0:
        emit("A7", False, f"local tag missing: {tag}")
        failed.append("A7")
        return
    remote = subprocess.run(
        ["git", "ls-remote", "--tags", "origin", tag],
        capture_output=True, text=True,
    )
    if remote.returncode != 0 or tag not in (remote.stdout or ""):
        emit("A7", False, f"tag not on origin: {tag}")
        failed.append("A7")
        return
    emit("A7", True, f"tag exists locally and on origin: {tag}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a robust_asr handoff package (7 assertions).",
    )
    parser.add_argument("--handoff", required=True, type=Path,
                        help="Path to artifacts/robust_asr/handoff")
    parser.add_argument("--strict", action="store_true",
                        help="Also require handoff/<date>-<short_sha> tag "
                             "to exist locally and on origin.")
    args = parser.parse_args()

    handoff_dir = args.handoff.resolve()
    if not handoff_dir.is_dir():
        print(f"FAIL: handoff dir not found: {handoff_dir}", file=sys.stderr)
        print("FAIL_HANDOFF_PACKAGE: HANDOFF_DIR_MISSING")
        return 1

    failed: list[str] = []

    readme_text = assert_readme_sections(handoff_dir / "README.md", failed)
    if readme_text:
        assert_artifact_checksums(handoff_dir, readme_text, failed)
    assert_executable(handoff_dir / "handoff_smoke.py", "A3", failed)
    assert_executable(handoff_dir / "rollback_to_previous_handoff.py",
                      "A4", failed)
    assert_validation_template(handoff_dir, failed)
    assert_no_secrets(handoff_dir, failed)
    if args.strict:
        assert_tag(failed)

    if failed:
        print(f"FAIL_HANDOFF_PACKAGE: {','.join(sorted(set(failed)))}")
        return 1
    print("OK_HANDOFF_PACKAGE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
