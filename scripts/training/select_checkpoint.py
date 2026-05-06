#!/usr/bin/env python3
"""T7.1 deterministic checkpoint selector.

Plan §17 selection rule, sourced from
configs/training/full_training.yaml `checkpoint_policy`:

    primary_metric : average Word Accuracy over the five official degradations
    tiebreaker_1   : best worst-case (per-family) Word Accuracy
    tiebreaker_2   : most recent (highest) checkpoint step

Inputs are explicit. Globbing is not used. The script reads, for each of
the five expected steps {10000, 12500, 15000, 17500, 20000}, the
`eval_metadata.json` produced by `scripts/training/train_enhancer.py
--eval-checkpoint` and the read-only verify JSON written by the matching
Slurm job. It cross-checks SHA-256 between the on-disk canonical
checkpoint files and the metadata's `checkpoint_path`, applies strict
fail-fast handling for the latest.pt / checkpoint_step_0020000.pt alias
relationship, deterministically picks the winner, and writes:

    --out-md   reports/training/checkpoint_selection.md
    --out-json reports/training/checkpoint_selection.json

The script never modifies T6.2 source artifacts. Selection failure
exits non-zero and writes no output files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_STEPS = (10000, 12500, 15000, 17500, 20000)
EXPECTED_FAMILIES = (
    "broadband_hiss",
    "cafe_background",
    "far_field_room",
    "muffled",
    "phone_call",
)
DEFAULT_T3_2_DEGRADED_MACRO_WA = 0.8213  # reports/training/baseline_summary.md


def _die(msg: str) -> None:
    print(f"BLOCKER: {msg}", file=sys.stderr)
    sys.exit(2)


def _parse_step_eq_path(items, flag):
    out = {}
    for item in items or []:
        if "=" not in item:
            _die(f"{flag} expects STEP=PATH; got {item!r}")
        step_str, path_str = item.split("=", 1)
        try:
            step = int(step_str)
        except ValueError:
            _die(f"{flag}: STEP not int: {step_str!r}")
        if step in out:
            _die(f"{flag}: duplicate STEP key {step}")
        out[step] = Path(path_str)
    return out


def _check_steps_match_expected(steps, flag):
    seen = set(steps)
    expected = set(EXPECTED_STEPS)
    missing = expected - seen
    extra = seen - expected
    if missing:
        _die(f"{flag} missing STEP keys: {sorted(missing)}")
    if extra:
        _die(f"{flag} unexpected STEP keys: {sorted(extra)}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path, what: str) -> dict:
    if not path.exists():
        _die(f"{what} not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _die(f"{what} unparseable JSON ({path}): {exc!s}")


def _validate_finite(value, label):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        _die(f"{label} not numeric: {value!r}")
    if not math.isfinite(value):
        _die(f"{label} non-finite: {value!r}")


def _tier_for(delta_wa: float) -> str:
    if delta_wa >= 0.05:
        return "strong"
    if delta_wa > 0.0:
        return "partial"
    return "null_or_negative"


def _deployment_decision(tier: str) -> str:
    return {
        "strong": "selected_pending_t7_2",
        "partial": "partial_pending_t7_2",
        "null_or_negative": "not_selected_pending_review",
    }[tier]


def _scalar_from_yaml(path: Path, key: str) -> str | None:
    """Tiny stdlib regex extractor for top-level scalar `key: value` lines.

    Avoids a pyyaml dependency for environments without it. Returns None
    if the key is not found or not a simple scalar.
    """
    if not path.exists():
        return None
    pattern = re.compile(rf"^{re.escape(key)}:\s*([^\s#].*?)\s*(?:#.*)?$")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            v = m.group(1).strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            return v
    return None


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="T7.1 deterministic checkpoint selector")
    p.add_argument(
        "--eval-metadata",
        action="append",
        default=[],
        metavar="STEP=PATH",
        help="path to eval_metadata.json for STEP (repeatable; required for all five expected steps)",
    )
    p.add_argument(
        "--verify-json",
        action="append",
        default=[],
        metavar="STEP=PATH",
        help="path to Slurm Step-2 verify JSON for STEP (repeatable; required for all five expected steps)",
    )
    p.add_argument(
        "--checkpoints-dir",
        required=True,
        type=Path,
        help="T6.2 checkpoints directory containing checkpoint_step_<NNNN>.pt and latest.pt",
    )
    p.add_argument(
        "--config",
        required=True,
        type=Path,
        help="path to configs/training/full_training.yaml",
    )
    p.add_argument("--out-md", required=True, type=Path)
    p.add_argument("--out-json", required=True, type=Path)
    p.add_argument(
        "--baseline-summary",
        type=Path,
        default=None,
        help="optional reports/training/baseline_summary.md path (recorded only)",
    )
    p.add_argument(
        "--t3-2-degraded-macro-wa",
        type=float,
        default=DEFAULT_T3_2_DEGRADED_MACRO_WA,
        help=f"T3.2 macro WA baseline used for tier classification (default {DEFAULT_T3_2_DEGRADED_MACRO_WA})",
    )
    args = p.parse_args(argv)

    eval_meta_paths = _parse_step_eq_path(args.eval_metadata, "--eval-metadata")
    verify_paths = _parse_step_eq_path(args.verify_json, "--verify-json")
    _check_steps_match_expected(eval_meta_paths.keys(), "--eval-metadata")
    _check_steps_match_expected(verify_paths.keys(), "--verify-json")

    checkpoints_dir: Path = args.checkpoints_dir
    if not checkpoints_dir.is_dir():
        _die(f"--checkpoints-dir not a directory: {checkpoints_dir}")

    if not args.config.exists():
        _die(f"--config not found: {args.config}")

    # 1. Validate verify JSONs.
    for step, vpath in verify_paths.items():
        v = _load_json(vpath, f"verify JSON for step {step}")
        if v.get("validation_passed") is not True:
            _die(f"verify JSON for step {step} has validation_passed != true: {vpath}")
        errs = v.get("errors") or []
        if errs:
            _die(f"verify JSON for step {step} has non-empty errors: {errs}")

    # 2. Compute on-disk SHAs for all six expected files.
    canonical_paths = {
        step: checkpoints_dir / f"checkpoint_step_{step:07d}.pt"
        for step in EXPECTED_STEPS
    }
    latest_path = checkpoints_dir / "latest.pt"
    on_disk_shas: dict[int, str] = {}
    for step, ck in canonical_paths.items():
        if not ck.exists() or ck.stat().st_size == 0:
            _die(f"canonical checkpoint missing/empty: {ck}")
        on_disk_shas[step] = _sha256(ck)
    if not latest_path.exists() or latest_path.stat().st_size == 0:
        _die(f"latest.pt missing/empty: {latest_path}")
    latest_sha = _sha256(latest_path)

    # 3. Strict latest.pt alias handling for step 20000 metrics reuse.
    if latest_sha != on_disk_shas[20000]:
        _die(
            "T6.3b evaluated latest.pt but sha256(latest.pt) != "
            "sha256(checkpoint_step_0020000.pt); step 20000 lacks valid "
            "canonical metrics. T7.1 cannot continue. Re-evaluate "
            "checkpoint_step_0020000.pt explicitly or otherwise resolve "
            f"the discrepancy. latest.pt={latest_sha}; "
            f"step_0020000={on_disk_shas[20000]}"
        )

    # 4. Build per-step records.
    candidates = []
    eval_metas: dict[int, dict] = {}
    for step in EXPECTED_STEPS:
        meta = _load_json(eval_meta_paths[step], f"eval_metadata for step {step}")
        eval_metas[step] = meta

        per_fam_wa = meta.get("per_family_mean_word_accuracy")
        per_fam_wer = meta.get("per_family_mean_wer")
        if not isinstance(per_fam_wa, dict) or not isinstance(per_fam_wer, dict):
            _die(
                f"step {step}: per_family_mean_word_accuracy / "
                f"per_family_mean_wer missing or wrong type in {eval_meta_paths[step]}"
            )
        for fam in EXPECTED_FAMILIES:
            if fam not in per_fam_wa:
                _die(f"step {step}: per_family_mean_word_accuracy missing family {fam!r}")
            if fam not in per_fam_wer:
                _die(f"step {step}: per_family_mean_wer missing family {fam!r}")
            _validate_finite(per_fam_wa[fam], f"step {step} per_family_mean_word_accuracy[{fam}]")
            _validate_finite(per_fam_wer[fam], f"step {step} per_family_mean_wer[{fam}]")

        if "macro_word_accuracy" in meta:
            _validate_finite(meta["macro_word_accuracy"], f"step {step} macro_word_accuracy")
        if "macro_wer" in meta:
            _validate_finite(meta["macro_wer"], f"step {step} macro_wer")

        recomputed_macro_wa = sum(per_fam_wa[f] for f in EXPECTED_FAMILIES) / len(EXPECTED_FAMILIES)
        recomputed_macro_wer = sum(per_fam_wer[f] for f in EXPECTED_FAMILIES) / len(EXPECTED_FAMILIES)
        worst_case_wa = min(per_fam_wa[f] for f in EXPECTED_FAMILIES)

        ck_path_meta_str = meta.get("checkpoint_path")
        if not ck_path_meta_str:
            _die(f"step {step}: eval_metadata.checkpoint_path missing")
        ck_path_meta = Path(ck_path_meta_str)
        meta_step = meta.get("checkpoint_step")
        if meta_step is not None and int(meta_step) != step:
            _die(
                f"step {step}: eval_metadata.checkpoint_step={meta_step!r} "
                f"!= --eval-metadata STEP key {step}"
            )
        if step == 20000:
            if ck_path_meta.name not in {"checkpoint_step_0020000.pt", "latest.pt"}:
                _die(
                    f"step 20000: unexpected eval_metadata.checkpoint_path "
                    f"basename: {ck_path_meta.name!r}"
                )
        else:
            expected_name = f"checkpoint_step_{step:07d}.pt"
            if ck_path_meta.name != expected_name:
                _die(
                    f"step {step}: eval_metadata.checkpoint_path basename "
                    f"{ck_path_meta.name!r} != {expected_name!r}"
                )
            if not ck_path_meta.exists():
                _die(
                    f"step {step}: eval_metadata.checkpoint_path does not "
                    f"exist on disk: {ck_path_meta}"
                )
            on_disk_for_meta = _sha256(ck_path_meta)
            if on_disk_for_meta != on_disk_shas[step]:
                _die(
                    f"step {step}: eval_metadata.checkpoint_path SHA-256 "
                    f"differs from canonical file under --checkpoints-dir. "
                    f"meta_path={ck_path_meta} meta_sha={on_disk_for_meta}; "
                    f"canonical={canonical_paths[step]} canonical_sha="
                    f"{on_disk_shas[step]}"
                )

        candidates.append({
            "step": step,
            "canonical_path": str(canonical_paths[step]),
            "sha256": on_disk_shas[step],
            "alias_paths": ([str(latest_path)] if step == 20000 else []),
            "per_family_mean_word_accuracy": dict(per_fam_wa),
            "per_family_mean_wer": dict(per_fam_wer),
            "macro_word_accuracy": recomputed_macro_wa,
            "macro_wer": recomputed_macro_wer,
            "worst_case_word_accuracy": worst_case_wa,
            "eval_metadata_path": str(eval_meta_paths[step]),
            "verify_json_path": str(verify_paths[step]),
            "validation_passed": True,
        })

    # 5. Sort: primary, then tiebreaker 1, then tiebreaker 2.
    ordered = sorted(
        candidates,
        key=lambda c: (-c["macro_word_accuracy"], -c["worst_case_word_accuracy"], -c["step"]),
    )
    keys_for_dup = [
        (c["macro_word_accuracy"], c["worst_case_word_accuracy"], c["step"]) for c in ordered
    ]
    if len(set(keys_for_dup)) != len(keys_for_dup):
        _die("post-tiebreaker tie detected (steps must be unique; refusing to continue)")

    winner = ordered[0]
    delta_wa = winner["macro_word_accuracy"] - args.t3_2_degraded_macro_wa
    tier = _tier_for(delta_wa)
    deployment = _deployment_decision(tier)

    trace = []
    for rank, c in enumerate(ordered, start=1):
        trace.append({
            "rank": rank,
            "step": c["step"],
            "macro_word_accuracy": c["macro_word_accuracy"],
            "worst_case_word_accuracy": c["worst_case_word_accuracy"],
            "macro_wer": c["macro_wer"],
        })

    # 6. Cross-step consistency for identity fields.
    def _consistent_field(meta_key: str):
        vals = []
        for step in EXPECTED_STEPS:
            v = eval_metas[step].get(meta_key)
            if v is not None:
                vals.append(v)
        unique = list({json.dumps(v, sort_keys=True): v for v in vals}.values())
        if len(unique) > 1:
            _die(f"inconsistent {meta_key} across candidates: {unique!r}")
        return unique[0] if unique else None

    dataset_version = _consistent_field("checkpoint_dataset_version") or _consistent_field("dataset_version")
    training_split_version = _consistent_field("checkpoint_training_split_version") or _consistent_field("training_split_version")
    whisper_model = _consistent_field("whisper_model")
    whisper_version = _consistent_field("whisper_version")
    whisper_device = _consistent_field("whisper_device")
    eval_per_family_cap = _consistent_field("eval_per_family_cap")

    metrics_version = _scalar_from_yaml(args.config, "metrics_version") or "metrics_v1"
    degradation_version = _scalar_from_yaml(args.config, "degradation_version") or "degradation_v1"

    output = {
        "schema_version": "1",
        "task": "T7.1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_path": str(args.config),
        "baseline_summary_path": (str(args.baseline_summary) if args.baseline_summary else None),
        "t3_2_degraded_macro_word_accuracy": args.t3_2_degraded_macro_wa,
        "dataset_version": dataset_version,
        "training_split_version": training_split_version,
        "metrics_version": metrics_version,
        "degradation_version": degradation_version,
        "asr": {
            "model": whisper_model,
            "version": whisper_version,
            "device": whisper_device,
        },
        "eval_per_family_cap": eval_per_family_cap,
        "candidates": candidates,
        "selection_primary_metric": "average_word_accuracy_over_official_degradations",
        "tiebreaker_1": "best_worst_case_degradation",
        "tiebreaker_2": "most_recent_checkpoint",
        "selection_rule_application_trace": trace,
        "selected_checkpoint": {
            "step": winner["step"],
            "canonical_path": winner["canonical_path"],
            "sha256": winner["sha256"],
            "alias_paths": winner["alias_paths"],
            "macro_word_accuracy": winner["macro_word_accuracy"],
            "macro_wer": winner["macro_wer"],
            "worst_case_word_accuracy": winner["worst_case_word_accuracy"],
            "delta_macro_wa_vs_t3_2_degraded": delta_wa,
            "tier_at_selection": tier,
            "deployment_decision": deployment,
        },
        "t7_2_required": True,
        "do_not_modify_model_card": True,
        "latest_pt_alias": {
            "latest_pt_path": str(latest_path),
            "latest_pt_sha256": latest_sha,
            "checkpoint_step_0020000_sha256": on_disk_shas[20000],
            "alias_accepted": True,
        },
    }

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(args.out_json, json.dumps(output, indent=2, sort_keys=True) + "\n")
    _atomic_write_text(args.out_md, _render_md(output))
    print(f"OK: selected step={winner['step']} tier={tier} deployment_decision={deployment}")
    print(f"OK: wrote {args.out_json}")
    print(f"OK: wrote {args.out_md}")
    return 0


def _render_md(output: dict) -> str:
    sel = output["selected_checkpoint"]
    out = []
    out.append("# T7.1 Checkpoint Selection")
    out.append("")
    out.append(f"Generated (UTC): `{output['generated_at_utc']}`")
    out.append("")
    out.append("Plan §17 selection rule:")
    out.append("")
    out.append("- primary metric: average Word Accuracy over the five official degradations;")
    out.append("- tiebreaker 1: best worst-case (per-family) Word Accuracy;")
    out.append("- tiebreaker 2: most recent (highest) checkpoint step.")
    out.append("")
    out.append("## Identities")
    out.append("")
    out.append("| Field | Value |")
    out.append("|---|---|")
    out.append(f"| Config | `{output['config_path']}` |")
    out.append(f"| Dataset version | `{output['dataset_version']}` |")
    out.append(f"| Training split version | `{output['training_split_version']}` |")
    out.append(f"| Metrics version | `{output['metrics_version']}` |")
    out.append(f"| Degradation version | `{output['degradation_version']}` |")
    out.append(f"| ASR model | `{output['asr']['model']}` (`{output['asr']['version']}`) |")
    out.append(f"| ASR device | `{output['asr']['device']}` |")
    out.append(f"| eval_per_family_cap | `{output['eval_per_family_cap']}` |")
    out.append(f"| T3.2 degraded macro WA baseline | `{output['t3_2_degraded_macro_word_accuracy']}` |")
    out.append("")
    out.append("## latest.pt alias verification")
    out.append("")
    la = output["latest_pt_alias"]
    out.append(
        f"- `sha256(latest.pt) == sha256(checkpoint_step_0020000.pt)`: "
        f"**{la['alias_accepted']}**"
    )
    out.append(f"- `latest.pt` SHA-256: `{la['latest_pt_sha256']}`")
    out.append(f"- `checkpoint_step_0020000.pt` SHA-256: `{la['checkpoint_step_0020000_sha256']}`")
    out.append("")
    out.append("## Candidates")
    out.append("")
    out.append("| Step | Macro WA | Worst-case WA | Macro WER | SHA-256 (prefix) |")
    out.append("|---|---|---|---|---|")
    for c in output["candidates"]:
        out.append(
            f"| {c['step']} | {c['macro_word_accuracy']:.6f} | "
            f"{c['worst_case_word_accuracy']:.6f} | {c['macro_wer']:.6f} | "
            f"`{c['sha256'][:16]}…` |"
        )
    out.append("")
    out.append("## Selection rule application trace")
    out.append("")
    out.append("| Rank | Step | Macro WA | Worst-case WA | Macro WER |")
    out.append("|---|---|---|---|---|")
    for t in output["selection_rule_application_trace"]:
        out.append(
            f"| {t['rank']} | {t['step']} | {t['macro_word_accuracy']:.6f} | "
            f"{t['worst_case_word_accuracy']:.6f} | {t['macro_wer']:.6f} |"
        )
    out.append("")
    out.append("## Selected checkpoint")
    out.append("")
    out.append(f"- Step: `{sel['step']}`")
    out.append(f"- Canonical path: `{sel['canonical_path']}`")
    out.append(f"- SHA-256: `{sel['sha256']}`")
    aliases = sel["alias_paths"] or []
    out.append("- Alias paths: " + (", ".join(f"`{p}`" for p in aliases) if aliases else "(none)"))
    out.append(f"- Macro Word Accuracy: `{sel['macro_word_accuracy']:.6f}`")
    out.append(f"- Macro WER: `{sel['macro_wer']:.6f}`")
    out.append(f"- Worst-case family Word Accuracy: `{sel['worst_case_word_accuracy']:.6f}`")
    out.append(f"- Δ macro WA vs T3.2 degraded: `{sel['delta_macro_wa_vs_t3_2_degraded']:+.6f}`")
    out.append(f"- Tier at selection: `{sel['tier_at_selection']}`")
    out.append(f"- Deployment decision: `{sel['deployment_decision']}`")
    out.append("")
    out.append("## Posture")
    out.append("")
    out.append(f"- `t7_2_required`: **{output['t7_2_required']}**")
    out.append(f"- `do_not_modify_model_card`: **{output['do_not_modify_model_card']}**")
    out.append("")
    out.append("## Source evidence (read-only references)")
    out.append("")
    for c in output["candidates"]:
        out.append(
            f"- step {c['step']}: eval_metadata `{c['eval_metadata_path']}`; "
            f"verify JSON `{c['verify_json_path']}`"
        )
    out.append("")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
