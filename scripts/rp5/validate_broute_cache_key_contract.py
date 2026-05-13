#!/usr/bin/env python3
"""
B-route cache-key contract validator.
Statically and dynamically verifies libs/asr/router_runtime.py:build_cache_key
against the cache_key_required_fields contract from agent_plan.md section 2.
Emits OK_BROUTE_CACHE_KEY_CONTRACT on success or B_ROUTE_CACHE_KEY_INCOMPLETE on failure.
"""
import argparse
import datetime
import importlib.util
import inspect
import pathlib
import sys


CACHE_KEY_REQUIRED_FIELDS = [
    "audio_hash",
    "selected_backend",
    "asr_model_and_version",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "degradation_version",
    "metrics_or_features_version",
]

FORBIDDEN_SUBSTRINGS = [
    "ASSEMBLYAI_API_KEY",
    "http://",
    "https://",
    "hostname",
    "transcript",
    "hypothesis",
    "ground_truth",
    "session_id_hash",
    "raw_payload",
    "@",
]

BASELINE_KWARGS = {
    "audio_hash": "sha256_baseline_abc",
    "selected_backend": "whisper_base_ct2_int8",
    "asr_model_and_version": "whisper_base:int8",
    "router_kind": "deterministic_selector",
    "router_version": "stub-v0",
    "routing_profile": "balanced",
    "allow_third_party": False,
    "degradation_version": "degradation_v1",
    "metrics_or_features_version": "1.0",
}


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def load_module(source_file):
    module_name = "router_runtime_under_test"
    spec = importlib.util.spec_from_file_location(module_name, str(source_file))
    if spec is None or spec.loader is None:
        return None, f"cannot create import spec for {source_file}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        sys.modules.pop(module_name, None)
        return None, f"import failed: {type(exc).__name__}: {exc}"
    return mod, None


def run_checks(source_file):
    results = []
    mod, err = load_module(source_file)
    results.append(_check("module_importable", mod is not None, err or f"loaded {source_file}"))
    if mod is None:
        return results

    bck = getattr(mod, "build_cache_key", None)
    present = bck is not None and callable(bck)
    results.append(_check("build_cache_key_present", present, "callable" if present else "build_cache_key missing or not callable"))
    if not present:
        return results

    try:
        sig = inspect.signature(bck)
    except (TypeError, ValueError) as exc:
        results.append(_check("signature_introspection", False, f"{type(exc).__name__}: {exc}"))
        return results
    params = set(sig.parameters)
    missing = [f for f in CACHE_KEY_REQUIRED_FIELDS if f not in params]
    results.append(_check(
        "signature_has_all_9_fields",
        len(missing) == 0,
        f"missing: {missing}" if missing else f"all {len(CACHE_KEY_REQUIRED_FIELDS)} fields present",
    ))
    if missing:
        return results

    try:
        baseline_key = bck(**BASELINE_KWARGS)
        baseline_key_2 = bck(**BASELINE_KWARGS)
    except Exception as exc:
        results.append(_check("baseline_call_succeeds", False, f"{type(exc).__name__}: {exc}"))
        return results
    results.append(_check("baseline_call_succeeds", isinstance(baseline_key, str) and baseline_key != "", "non-empty str returned"))
    results.append(_check("determinism", baseline_key == baseline_key_2, "two calls with identical kwargs returned equal strings"))

    variations = {}
    string_fields = [f for f in CACHE_KEY_REQUIRED_FIELDS if f != "allow_third_party"]
    sensitive_failures = []
    for fld in string_fields:
        modified = dict(BASELINE_KWARGS)
        modified[fld] = BASELINE_KWARGS[fld] + "_VARIED"
        varied_key = bck(**modified)
        variations[fld] = varied_key
        if varied_key == baseline_key:
            sensitive_failures.append(fld)

    toggled_kwargs = dict(BASELINE_KWARGS)
    toggled_kwargs["allow_third_party"] = True
    third_party_true_key = bck(**toggled_kwargs)
    if third_party_true_key == baseline_key:
        sensitive_failures.append("allow_third_party")

    results.append(_check(
        "sensitivity_per_field",
        len(sensitive_failures) == 0,
        f"insensitive fields: {sensitive_failures}" if sensitive_failures else "all 9 fields cause key change when modified",
    ))

    toggled_again = dict(BASELINE_KWARGS)
    toggled_again["allow_third_party"] = True
    second_true = bck(**toggled_again)
    third_party_encoding_ok = (
        third_party_true_key != baseline_key
        and third_party_true_key == second_true
        and isinstance(third_party_true_key, str)
    )
    results.append(_check(
        "allow_third_party_boolean_encoding",
        third_party_encoding_ok,
        "True vs False produce distinct deterministic encodings" if third_party_encoding_ok else "boolean encoding non-deterministic or collides",
    ))

    forbidden_hits = [s for s in FORBIDDEN_SUBSTRINGS if s in baseline_key]
    results.append(_check(
        "no_forbidden_content_in_baseline_key",
        len(forbidden_hits) == 0,
        f"forbidden substrings present: {forbidden_hits}" if forbidden_hits else "none of the forbidden substrings present",
    ))

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", default="libs/asr/router_runtime.py")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source_file = pathlib.Path(args.source_file)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not source_file.exists():
        out_path.write_text(f"B_ROUTE_CACHE_KEY_INCOMPLETE: source file does not exist: {source_file}\n")
        print("B_ROUTE_CACHE_KEY_INCOMPLETE")
        return 1

    results = run_checks(source_file)
    failures = [r for r in results if not r["passed"]]

    lines = [
        "# BR-03 B-route Cache-Key Contract Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"source_file: {source_file}",
        f"checks: {len(results)}",
        f"failures: {len(failures)}",
        "",
        "## Required Cache-Key Fields",
        "",
    ]
    for f in CACHE_KEY_REQUIRED_FIELDS:
        lines.append(f"- {f}")
    lines += ["", "## Check Results", ""]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")

    if failures:
        lines += ["", "## Result: B_ROUTE_CACHE_KEY_INCOMPLETE", "", "B_ROUTE_CACHE_KEY_INCOMPLETE"]
        sentinel = "B_ROUTE_CACHE_KEY_INCOMPLETE"
    else:
        lines += ["", "## Result: OK_BROUTE_CACHE_KEY_CONTRACT", "", f"All {len(results)} checks passed.", "", "OK_BROUTE_CACHE_KEY_CONTRACT"]
        sentinel = "OK_BROUTE_CACHE_KEY_CONTRACT"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_BROUTE_CACHE_KEY_CONTRACT" else 1


if __name__ == "__main__":
    sys.exit(main())
