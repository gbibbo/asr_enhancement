#!/usr/bin/env python3
"""
B-route schema contract validator.
Performs static structural analysis of libs/asr/router_runtime.py against the
RouterDecision and AssembledResponse field contracts in agent_plan.md section 2.
Emits OK_BROUTE_SCHEMA_CONTRACT on success or ROUTER_SCHEMA_DRIFT on failure.
"""
import argparse
import dataclasses
import datetime
import importlib.util
import pathlib
import sys


ROUTER_DECISION_FIELDS = [
    "selected_backend",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "third_party_provider",
    "cost_policy",
    "estimated_cost_usd",
    "predicted_confidence",
    "predicted_ask_repeat",
    "routing_explanation",
    "router_latency_ms",
]

ASSEMBLED_RESPONSE_FIELDS = [
    "transcript_text",
    "selected_backend",
    "router_kind",
    "router_version",
    "routing_profile",
    "allow_third_party",
    "third_party_provider",
    "estimated_cost_usd",
    "cost_usd",
    "backend_confidence",
    "ask_repeat",
    "latency_ms",
    "routing_explanation",
]

LATENCY_MS_SUBFIELDS = ["backend", "server", "end_to_end"]


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


def dataclass_field_names(cls):
    if not dataclasses.is_dataclass(cls):
        return None
    return [f.name for f in dataclasses.fields(cls)]


def run_checks(source_file):
    results = []

    mod, err = load_module(source_file)
    results.append(_check("module_importable", mod is not None, err or f"loaded {source_file}"))
    if mod is None:
        return results

    required_names = ["RouterRuntime", "RouterDecision", "AssembledResponse", "build_cache_key"]
    for name in required_names:
        present = hasattr(mod, name)
        results.append(_check(f"{name}_present", present, "found" if present else f"{name} missing from module"))

    rt = getattr(mod, "RouterRuntime", None)
    if rt is not None:
        has_route = hasattr(rt, "route") and callable(getattr(rt, "route"))
        results.append(_check("RouterRuntime_has_route", has_route, "route method present" if has_route else "RouterRuntime.route missing or not callable"))

    rd = getattr(mod, "RouterDecision", None)
    if rd is not None:
        rd_fields = dataclass_field_names(rd)
        if rd_fields is None:
            results.append(_check("RouterDecision_is_dataclass", False, "RouterDecision is not a dataclass"))
        else:
            missing = [f for f in ROUTER_DECISION_FIELDS if f not in rd_fields]
            results.append(_check(
                "RouterDecision_fields_complete",
                len(missing) == 0,
                f"missing fields: {missing}" if missing else f"all {len(ROUTER_DECISION_FIELDS)} fields present",
            ))

    ar = getattr(mod, "AssembledResponse", None)
    if ar is not None:
        ar_fields = dataclass_field_names(ar)
        if ar_fields is None:
            results.append(_check("AssembledResponse_is_dataclass", False, "AssembledResponse is not a dataclass"))
        else:
            missing = [f for f in ASSEMBLED_RESPONSE_FIELDS if f not in ar_fields]
            results.append(_check(
                "AssembledResponse_fields_complete",
                len(missing) == 0,
                f"missing fields: {missing}" if missing else f"all {len(ASSEMBLED_RESPONSE_FIELDS)} fields present",
            ))

            ar_field_objs = {f.name: f for f in dataclasses.fields(ar)}
            latency_field = ar_field_objs.get("latency_ms")
            if latency_field is not None:
                latency_type = latency_field.type
                if isinstance(latency_type, str):
                    latency_type = getattr(mod, latency_type, None)
                latency_sub = dataclass_field_names(latency_type) if latency_type else None
                if latency_sub is None:
                    results.append(_check(
                        "latency_ms_subfields",
                        False,
                        f"latency_ms type is not a dataclass or unresolvable: {latency_field.type}",
                    ))
                else:
                    missing_sub = [s for s in LATENCY_MS_SUBFIELDS if s not in latency_sub]
                    results.append(_check(
                        "latency_ms_subfields",
                        len(missing_sub) == 0,
                        f"missing latency_ms subfields: {missing_sub}" if missing_sub else f"all {len(LATENCY_MS_SUBFIELDS)} latency subfields present",
                    ))

    bck = getattr(mod, "build_cache_key", None)
    if bck is not None:
        results.append(_check("build_cache_key_callable", callable(bck), "callable" if callable(bck) else "build_cache_key is not callable"))

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
        out_path.write_text(f"ROUTER_SCHEMA_DRIFT: source file does not exist: {source_file}\n")
        print("ROUTER_SCHEMA_DRIFT")
        return 1

    results = run_checks(source_file)
    failures = [r for r in results if not r["passed"]]

    lines = [
        "# BR-01 B-route Schema Contract Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"source_file: {source_file}",
        f"checks: {len(results)}",
        f"failures: {len(failures)}",
        "",
        "## Check Results",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")

    lines += ["", "## Required Field Sets", ""]
    lines.append(f"RouterDecision required fields: {ROUTER_DECISION_FIELDS}")
    lines.append(f"AssembledResponse required fields: {ASSEMBLED_RESPONSE_FIELDS}")
    lines.append(f"latency_ms required subfields: {LATENCY_MS_SUBFIELDS}")

    if failures:
        lines += ["", "## Result: ROUTER_SCHEMA_DRIFT", "", f"{len(failures)} check(s) failed:", ""]
        for f in failures:
            lines.append(f"  - {f['name']}: {f['detail']}")
        lines += ["", "ROUTER_SCHEMA_DRIFT"]
        sentinel = "ROUTER_SCHEMA_DRIFT"
    else:
        lines += ["", "## Result: OK_BROUTE_SCHEMA_CONTRACT", "", f"All {len(results)} checks passed.", "", "OK_BROUTE_SCHEMA_CONTRACT"]
        sentinel = "OK_BROUTE_SCHEMA_CONTRACT"

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if sentinel == "OK_BROUTE_SCHEMA_CONTRACT" else 1


if __name__ == "__main__":
    sys.exit(main())
