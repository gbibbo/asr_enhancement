"""T2.4: Define dataset version and record manifest checksum.

Reads librispeech_sources.yaml and public_examples_excluded.yaml, computes the
SHA-256 of the source manifest, and writes a stable dataset version config to
configs/training/dataset_version.yaml plus a small committed Markdown report.

Version string format:
  librispeech_devclean_v1_exclpending_sha256_<first12>

where <first12> is the first 12 hex characters of the manifest SHA-256.

Exit 0 on success; exit 1 on any failure.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _count_lines(path: pathlib.Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for _ in fh:
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="T2.4 define dataset version")
    parser.add_argument("--sources-config", required=True,
                        help="Path to librispeech_sources.yaml")
    parser.add_argument("--exclusion-config", required=True,
                        help="Path to public_examples_excluded.yaml")
    parser.add_argument("--manifest", required=True,
                        help="Path to source JSONL manifest (T2.2 output)")
    parser.add_argument("--out-config", required=True,
                        help="Output path for dataset_version.yaml (in repo)")
    parser.add_argument("--report", required=True,
                        help="Output path for dataset_version_v1.md (in repo reports/training/)")
    parser.add_argument("--summary", required=True,
                        help="Path for external evidence JSON artifact")
    args = parser.parse_args()

    import yaml

    failures = []
    evidence = {
        "task": "T2.4",
        "success": False,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "pythonnousersite_env": os.environ.get("PYTHONNOUSERSITE", "NOT_SET"),
        "sources_config_path": args.sources_config,
        "exclusion_config_path": args.exclusion_config,
        "manifest_path": args.manifest,
        "out_config_path": args.out_config,
        "summary_path": args.summary,
        "dataset_version": None,
        "manifest_sha256": None,
        "manifest_sha256_prefix": None,
        "manifest_records": None,
        "manifest_size_bytes": None,
        "manifest_mtime_utc": None,
        "exclusion_status": None,
        "all_failures": failures,
    }

    # --- Guard: PYTHONNOUSERSITE ---
    if evidence["pythonnousersite_env"] != "1":
        failures.append(
            f"PYTHONNOUSERSITE is not '1': {evidence['pythonnousersite_env']}"
        )
        _write_summary(args.summary, evidence)
        print(f"T2.4 FAILED: {failures}")
        return 1

    # --- Phase 1: Load sources config ---
    sources_path = pathlib.Path(args.sources_config)
    if not sources_path.exists():
        failures.append(f"FATAL: sources config not found: {args.sources_config}")
        _write_summary(args.summary, evidence)
        print(f"T2.4 FAILED: {failures}")
        return 1

    with sources_path.open("r") as fh:
        sources_cfg = yaml.safe_load(fh)

    dataset_root = sources_cfg.get("dataset_root", "")
    output_manifest_path = sources_cfg.get("output_manifest_path", "")
    splits_cfg = sources_cfg.get("splits", {})
    splits_used = sorted(
        name for name, info in splits_cfg.items()
        if info.get("split_status") == "present"
    )
    baseline_validation = sources_cfg.get("allowed_splits_for_baseline", [])
    training_splits = sources_cfg.get("allowed_splits_for_training", [])

    print(f"Sources config: {args.sources_config}")
    print(f"Dataset root:   {dataset_root}")
    print(f"Splits used:    {splits_used}")

    # --- Phase 2: Load exclusion config ---
    excl_path = pathlib.Path(args.exclusion_config)
    if not excl_path.exists():
        failures.append(f"FATAL: exclusion config not found: {args.exclusion_config}")
        _write_summary(args.summary, evidence)
        print(f"T2.4 FAILED: {failures}")
        return 1

    with excl_path.open("r") as fh:
        excl_cfg = yaml.safe_load(fh)

    for key in ("status", "excluded_ids", "excluded_audio_sha256"):
        if key not in excl_cfg:
            failures.append(f"FATAL: missing key in exclusion config: {key}")

    if failures:
        _write_summary(args.summary, evidence)
        print(f"T2.4 FAILED: {failures}")
        return 1

    excl_status = excl_cfg["status"]
    excl_ids = excl_cfg.get("excluded_ids", [])
    excl_hashes = excl_cfg.get("excluded_audio_sha256", [])
    filled_after = excl_cfg.get("filled_after_demo_task", None)
    t3_blocked = excl_cfg.get("t3_blocked_while_pending", True)
    rerun_required = excl_cfg.get("rerun_required_after_b6_2", True)
    filtered_manifest = excl_cfg.get("filtered_manifest", None)

    evidence["exclusion_status"] = excl_status
    print(f"Exclusion status: {excl_status}")

    # --- Phase 3: Verify manifest ---
    manifest_path = pathlib.Path(args.manifest)
    if not manifest_path.exists() or manifest_path.stat().st_size == 0:
        failures.append(f"FATAL: manifest not found or empty: {args.manifest}")
        _write_summary(args.summary, evidence)
        print(f"T2.4 FAILED: {failures}")
        return 1

    stat = manifest_path.stat()
    evidence["manifest_size_bytes"] = stat.st_size
    evidence["manifest_mtime_utc"] = (
        datetime.datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
    )

    print(f"Counting manifest lines: {args.manifest}")
    line_count = _count_lines(manifest_path)
    evidence["manifest_records"] = line_count
    print(f"Manifest records: {line_count}")

    if line_count != 2703:
        failures.append(
            f"FATAL: manifest line count is {line_count}, expected 2703 "
            f"(manifest may have changed)"
        )
        _write_summary(args.summary, evidence)
        print(f"T2.4 FAILED: {failures}")
        return 1

    # --- Phase 4: Compute SHA-256 ---
    print(f"Computing SHA-256: {args.manifest}")
    sha256_full = _sha256_file(manifest_path)
    sha256_prefix = sha256_full[:12]
    evidence["manifest_sha256"] = sha256_full
    evidence["manifest_sha256_prefix"] = sha256_prefix
    print(f"SHA-256:        {sha256_full}")
    print(f"SHA-256 prefix: {sha256_prefix}")

    # --- Phase 5: Assemble dataset version ---
    dataset_version = f"librispeech_devclean_v1_exclpending_sha256_{sha256_prefix}"
    evidence["dataset_version"] = dataset_version
    print(f"Dataset version: {dataset_version}")

    # --- Phase 6: Write dataset_version.yaml ---
    version_doc = {
        "dataset_version": dataset_version,
        "dataset_version_components": {
            "source": "librispeech",
            "splits": splits_used,
            "split_policy": "dev_clean_only",
            "exclusion_policy": excl_status,
            "manifest_sha256_prefix": sha256_prefix,
        },
        "source": {
            "dataset": "LibriSpeech",
            "root": dataset_root,
            "splits_used": splits_used,
        },
        "split_policy": {
            "baseline_validation": baseline_validation,
            "training": training_splits,
        },
        "exclusion_policy": {
            "status": excl_status,
            "filled_after_demo_task": filled_after,
            "excluded_ids_count": len(excl_ids),
            "excluded_hashes_count": len(excl_hashes),
            "filtered_manifest_path": filtered_manifest,
            "t3_blocked_while_pending": t3_blocked,
            "rerun_required_after_b6_2": rerun_required,
        },
        "manifest": {
            "path": output_manifest_path or args.manifest,
            "records": line_count,
            "sha256": sha256_full,
            "size_bytes": stat.st_size,
            "mtime_utc": evidence["manifest_mtime_utc"],
        },
        "later_tasks_must_embed_dataset_version": True,
        "generated_by": "scripts/training/t2_4_define_dataset_version.py",
    }

    out_config_path = pathlib.Path(args.out_config)
    out_config_path.parent.mkdir(parents=True, exist_ok=True)
    with out_config_path.open("w") as fh:
        yaml.dump(version_doc, fh, default_flow_style=False, allow_unicode=True,
                  sort_keys=False)
    print(f"Written: {args.out_config}")

    # --- Phase 7: Write Markdown report ---
    report_path = pathlib.Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Dataset Version: T2.4",
        "",
        f"**dataset_version:** `{dataset_version}`",
        "",
        "## Manifest",
        "",
        f"- **Path:** `{output_manifest_path or args.manifest}`",
        f"- **Records:** {line_count}",
        f"- **SHA-256:** `{sha256_full}`",
        "",
        "## Exclusion policy",
        "",
        f"- **Status:** `{excl_status}`",
        f"- **Filtered manifest:** `{filtered_manifest}`",
        "",
        "## Gates",
        "",
        "- T2.3 must be re-run after B6.2 produces `demo_examples.json`.",
        "- T3.1 must not run while `configs/training/public_examples_excluded.yaml`",
        "  has `status: pending_public_examples`.",
    ]
    with report_path.open("w") as fh:
        fh.write("\n".join(report_lines) + "\n")
    print(f"Written: {report_path}")

    # --- Phase 8: Write evidence JSON ---
    evidence["success"] = True
    evidence["all_failures"] = []
    evidence["dataset_version_config_path"] = args.out_config
    evidence["dataset_version_report_path"] = str(report_path)
    evidence["timestamp_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    _write_summary(args.summary, evidence)

    print()
    print(f"dataset_version : {dataset_version}")
    print(f"manifest_records: {line_count}")
    print(f"manifest_sha256 : {sha256_full}")
    print(f"exclusion_status: {excl_status}")
    print(f"out_config      : {args.out_config}")
    print(f"report          : {report_path}")
    print(f"summary         : {args.summary}")
    print()
    print("T2.4 COMPLETE")
    return 0


def _write_summary(path: str, evidence: dict) -> None:
    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)


if __name__ == "__main__":
    sys.exit(main())
