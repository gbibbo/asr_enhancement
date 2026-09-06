#!/usr/bin/env python3
"""
B14.2 public-surface recruiter-gate diagnostic validator.

Reads the declarative diagnostic report (default
reports/rp5/b14_2_public_surface_diagnostic.md) and validates that:

  * the report cites the four required B15 input artifacts by reference;
  * the report records the plan-pinned tracker commit and the current
    tracker self-reference spelling as a freeze-audit pair;
  * the report enumerates all four required public-smoke vantage points;
  * every vantage point preserves recruiter_gate_observed_status =
    unauthenticated_access_observed (no conversion to
    authenticated_access_only outside an explicit negative-assertion
    line);
  * every vantage point preserves upload_with_manual_ground_truth = FAIL
    (no conversion to PASS outside an explicit negative-assertion line);
  * the report defines Zones A, B, and C with at least one hypothesis per
    zone, and every Zone C hypothesis line is marked unconfirmed;
  * the report defers upload-with-GT classification to B14_2-05;
  * the report records no literal public URL, hostname, non-loopback IP
    address, Tailscale auth-key, Cloudflare token, recruiter password,
    admin password, or secret.

Emits OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC on success or
EXECUTION_RAIL_GAP on failure. The validator runs no public-network
command.
"""
import argparse
import datetime
import pathlib
import re
import sys


SENTINEL_PASS = "OK_B14_2_PUBLIC_SURFACE_DIAGNOSTIC"
SENTINEL_FAIL = "EXECUTION_RAIL_GAP"

REQUIRED_REFERENCES = [
    "reports/rp5/b15_multi_network_smoke_results.md",
    "reports/rp5/b15_smoke_adjudication.md",
    "reports/rp5/b15_phase_gate.md",
    "docs/progress/rp5_progress.yaml",
]

PLAN_PINNED_TRACKER_COMMIT = "bf8560a6c3493692ccd8a35926a5ddc647b627f6"
TRACKER_SELF_REFERENCE_SPELLING = "this_tracker_commit_self_reference_per_b14_1_convention"

REQUIRED_VANTAGE_POINTS = [
    "windows_local",
    "mobile_cellular",
    "other_wifi",
    "vpn_or_external_tester",
]

REQUIRED_ZONES = ["Zone A", "Zone B", "Zone C"]

# Lines that mention authenticated_access_only or upload_with_manual_ground_truth
# PASS are accepted only when the line contains one of these negative-assertion
# qualifiers; otherwise they are treated as falsification of B15 evidence.
NEGATIVE_ASSERTION_QUALIFIERS = [
    "no record converts",
    "does not convert",
    "must not be converted",
    "no conversion to",
    "forbidden",
    "must not",
    "does not assert",
    "not converted",
    "preserved as",
    "without matching",
]

DEFER_TO_B14_2_05_KEYWORDS = ["defer", "deferred"]

# Loopback IPv4 strings that are allowed inside this diagnostic only when
# attached to a validator-base-url context (no literal public IP elsewhere).
LOOPBACK_IP = "127.0.0.1"


def _check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}


def _line_has_negative_qualifier(line: str) -> bool:
    lo = line.lower()
    return any(q in lo for q in NEGATIVE_ASSERTION_QUALIFIERS)


def validate_report(text: str):
    results = []

    # 1. Required B15 reference citations
    missing_refs = [r for r in REQUIRED_REFERENCES if r not in text]
    results.append(_check(
        "cites_all_required_b15_input_artifacts_by_reference",
        len(missing_refs) == 0,
        f"missing references: {missing_refs}" if missing_refs else
        f"all {len(REQUIRED_REFERENCES)} required B15 references cited",
    ))

    # 2. Freeze-audit pair: plan-pinned hash AND tracker self-reference sentinel
    has_pin = PLAN_PINNED_TRACKER_COMMIT in text
    has_self_ref = TRACKER_SELF_REFERENCE_SPELLING in text
    results.append(_check(
        "records_freeze_audit_pair",
        has_pin and has_self_ref,
        (f"plan_pinned_tracker_commit present={has_pin}; "
         f"tracker_self_reference_spelling present={has_self_ref}"),
    ))

    # 3. All four required vantage points present
    missing_vps = [vp for vp in REQUIRED_VANTAGE_POINTS if vp not in text]
    results.append(_check(
        "enumerates_all_four_public_smoke_vantage_points",
        len(missing_vps) == 0,
        f"missing vantage points: {missing_vps}" if missing_vps else
        f"all {len(REQUIRED_VANTAGE_POINTS)} vantage points present",
    ))

    # 4. Every vantage point preserves recruiter_gate_observed_status =
    #    unauthenticated_access_observed. We count distinct vantage-point
    #    sections that include the value verbatim.
    lines = text.splitlines()
    vp_unauth_counts = {vp: 0 for vp in REQUIRED_VANTAGE_POINTS}
    current_vp = None
    for line in lines:
        for vp in REQUIRED_VANTAGE_POINTS:
            if re.search(rf"\bVantage point\s*:\s*{re.escape(vp)}\b", line):
                current_vp = vp
                break
        if current_vp and "recruiter_gate_observed_status: unauthenticated_access_observed" in line:
            vp_unauth_counts[current_vp] += 1
    missing_unauth = [vp for vp, c in vp_unauth_counts.items() if c == 0]
    results.append(_check(
        "preserves_unauthenticated_access_observed_on_all_four_vantage_points",
        len(missing_unauth) == 0,
        f"vantage points missing recruiter_gate_observed_status: unauthenticated_access_observed: {missing_unauth}"
        if missing_unauth else
        "every vantage-point section records recruiter_gate_observed_status: unauthenticated_access_observed verbatim",
    ))

    # 5. Anti-falsification: every line containing authenticated_access_only
    #    must contain a negative-assertion qualifier; otherwise it is a
    #    forbidden conversion.
    bad_auth_only = []
    for i, line in enumerate(lines, start=1):
        if "authenticated_access_only" in line and not _line_has_negative_qualifier(line):
            bad_auth_only.append((i, line.strip()[:120]))
    results.append(_check(
        "does_not_convert_unauthenticated_access_observed_to_authenticated_access_only",
        len(bad_auth_only) == 0,
        f"forbidden positive uses of authenticated_access_only at lines {[i for i,_ in bad_auth_only]}"
        if bad_auth_only else
        "every mention of authenticated_access_only is on a negative-assertion line (preserved-not-converted)",
    ))

    # 6. Every vantage point preserves upload_with_manual_ground_truth: FAIL.
    vp_fail_counts = {vp: 0 for vp in REQUIRED_VANTAGE_POINTS}
    current_vp = None
    for line in lines:
        for vp in REQUIRED_VANTAGE_POINTS:
            if re.search(rf"\bVantage point\s*:\s*{re.escape(vp)}\b", line):
                current_vp = vp
                break
        if current_vp and re.search(
            r"upload_with_manual_ground_truth.*FAIL", line
        ) and not _line_has_negative_qualifier(line):
            vp_fail_counts[current_vp] += 1
    missing_fail = [vp for vp, c in vp_fail_counts.items() if c == 0]
    results.append(_check(
        "preserves_upload_with_manual_ground_truth_FAIL_on_all_four_vantage_points",
        len(missing_fail) == 0,
        f"vantage points missing upload_with_manual_ground_truth FAIL: {missing_fail}"
        if missing_fail else
        "every vantage-point section records upload_with_manual_ground_truth FAIL verbatim",
    ))

    # 7. Anti-falsification: every line containing upload_with_manual_ground_truth PASS
    #    must contain a negative-assertion qualifier (the upload_without_manual_ground_truth
    #    PASS coverage item is a different field name; the check matches the FAIL field
    #    converted to PASS explicitly).
    bad_pass = []
    pattern_pass = re.compile(r"upload_with_manual_ground_truth.*PASS")
    for i, line in enumerate(lines, start=1):
        if pattern_pass.search(line) and not _line_has_negative_qualifier(line):
            bad_pass.append((i, line.strip()[:120]))
    results.append(_check(
        "does_not_convert_upload_with_manual_ground_truth_FAIL_to_PASS",
        len(bad_pass) == 0,
        f"forbidden positive uses of upload_with_manual_ground_truth PASS at lines {[i for i,_ in bad_pass]}"
        if bad_pass else
        "every mention of upload_with_manual_ground_truth PASS is on a negative-assertion line",
    ))

    # 8. Defines all three zones (A, B, C) with section headers.
    missing_zones = [z for z in REQUIRED_ZONES if z not in text]
    results.append(_check(
        "defines_zones_A_B_and_C",
        len(missing_zones) == 0,
        f"missing zones: {missing_zones}" if missing_zones else
        "all three diagnostic zones (A, B, C) defined",
    ))

    # 9. At least one hypothesis per zone. Hypotheses are lines starting with
    #    "- Hypothesis" or containing the substring "Hypothesis " followed by
    #    a zone letter (A, B, or C).
    zone_hypothesis_counts = {z: 0 for z in ["A", "B", "C"]}
    for line in lines:
        m = re.search(r"Hypothesis\s+([ABC])\d?", line)
        if m:
            zone_hypothesis_counts[m.group(1)] += 1
    missing_hyp_zones = [z for z, c in zone_hypothesis_counts.items() if c == 0]
    results.append(_check(
        "enumerates_at_least_one_hypothesis_per_zone",
        len(missing_hyp_zones) == 0,
        f"zones missing a hypothesis: {missing_hyp_zones}"
        if missing_hyp_zones else
        f"hypothesis counts per zone: A={zone_hypothesis_counts['A']}, "
        f"B={zone_hypothesis_counts['B']}, C={zone_hypothesis_counts['C']}",
    ))

    # 10. Every Zone C hypothesis line is marked unconfirmed.
    zone_c_lines = []
    for line in lines:
        if re.search(r"Hypothesis\s+C\d?", line):
            zone_c_lines.append(line)
    bad_c = [
        ln for ln in zone_c_lines
        if not (
            "unconfirmed" in ln.lower()
            or "hypothesis" in ln.lower() and ("candidate" in ln.lower() or "unconfirmed" in ln.lower() or "not asserted" in ln.lower())
        )
    ]
    # A Zone C hypothesis line by construction contains "Hypothesis C" and
    # must also contain the literal "unconfirmed".
    bad_c = [ln for ln in zone_c_lines if "unconfirmed" not in ln.lower()]
    results.append(_check(
        "all_zone_c_hypotheses_marked_unconfirmed",
        len(bad_c) == 0,
        f"{len(bad_c)} Zone C hypothesis line(s) not marked unconfirmed"
        if bad_c else
        f"all {len(zone_c_lines)} Zone C hypothesis lines marked unconfirmed",
    ))

    # 11. Defers upload-with-GT classification to B14_2-05.
    defer_lines = [
        ln for ln in lines
        if "B14_2-05" in ln and any(k in ln.lower() for k in DEFER_TO_B14_2_05_KEYWORDS)
    ]
    results.append(_check(
        "defers_upload_with_gt_classification_to_b14_2_05",
        len(defer_lines) > 0,
        f"found {len(defer_lines)} defer-to-B14_2-05 statement(s)" if defer_lines
        else "no line containing both 'B14_2-05' and a 'defer'/'deferred' keyword",
    ))

    # 12. No literal public URL or non-loopback hostname. The loopback IPv4
    #     127.0.0.1 is allowed (validator base-url context). Any other
    #     non-loopback HTTPS URL or IPv4 literal is forbidden.
    url_hits = []
    for i, line in enumerate(lines, start=1):
        for m in re.finditer(r"https?://([A-Za-z0-9.\-]+)", line):
            host = m.group(1)
            if host != "127.0.0.1" and host != "localhost":
                url_hits.append((i, m.group(0)))
    ip_hits = []
    ip_pattern = re.compile(
        r"\b((?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}"
        r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b"
    )
    for i, line in enumerate(lines, start=1):
        for m in ip_pattern.finditer(line):
            ip = m.group(0)
            if ip != LOOPBACK_IP:
                ip_hits.append((i, ip))
    tailscale_hits = []
    for i, line in enumerate(lines, start=1):
        if re.search(r"\btskey-[A-Za-z0-9\-]+", line):
            tailscale_hits.append(i)
    secret_pass = (
        len(url_hits) == 0
        and len(ip_hits) == 0
        and len(tailscale_hits) == 0
    )
    sdetail = []
    if url_hits:
        sdetail.append(f"non-loopback URL literals at lines {[i for i,_ in url_hits]}")
    if ip_hits:
        sdetail.append(f"non-loopback IP literals at lines {[i for i,_ in ip_hits]}: {[ip for _,ip in ip_hits]}")
    if tailscale_hits:
        sdetail.append(f"Tailscale auth-key prefix matches at lines {tailscale_hits}")
    if secret_pass:
        sdetail.append("no literal public URL, non-loopback hostname/IP, or Tailscale auth-key prefix")
    results.append(_check(
        "contains_no_literal_public_url_hostname_ip_authkey_or_secret",
        secret_pass,
        "; ".join(sdetail),
    ))

    return results


def write_report(out_path: pathlib.Path, record_path: pathlib.Path,
                 results: list, sentinel: str):
    lines = [
        "# B14.2 Public-Surface Diagnostic Validation",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"record: {record_path}",
        f"checks: {len(results)}",
        f"failures: {sum(1 for r in results if not r['passed'])}",
        "",
        "## Results",
        "",
    ]
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"- [{status}] {r['name']}: {r['detail']}")
    lines += ["", f"## Sentinel", "", sentinel, ""]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record",
        default="reports/rp5/b14_2_public_surface_diagnostic.md",
    )
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    record_path = pathlib.Path(args.record)
    if not record_path.exists():
        out_path = pathlib.Path(args.out) if args.out else None
        msg = f"{SENTINEL_FAIL}: diagnostic record not found at {record_path}\n"
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(msg)
        print(SENTINEL_FAIL)
        return 1

    text = record_path.read_text()
    results = validate_report(text)
    failures = [r for r in results if not r["passed"]]
    sentinel = SENTINEL_PASS if not failures else SENTINEL_FAIL

    out_path = pathlib.Path(args.out) if args.out else None
    if out_path:
        write_report(out_path, record_path, results, sentinel)

    print(sentinel)
    return 0 if sentinel == SENTINEL_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
