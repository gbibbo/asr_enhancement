#!/usr/bin/env python3
"""
Validate future-constraint preservation records.

Reads a markdown file containing one section per future constraint, each
section holding the eight fields declared by the
`future_constraint_preservation_record` schema. Confirms the required
constraint ids are present, every record carries the eight required fields,
no literal public URL appears, and no forbidden_current_plan_regression
string is enacted as active-plan scope.

This validator is profile-parameterized. The legacy `broute` profile keeps the
original B-route/B14.0 contract (required ids include FC-B14-0-PUBLIC-GATE,
record field `source_preplan_section`, regression scan over docs/plans/broute).
The `b14_1` profile validates the B14.1 future-constraint contract (the five
B14.1 constraint ids, record field `source_section`, regression scan over
docs/plans/b14_1). The profile is taken from --constraint-profile when given,
otherwise inferred deterministically from the --constraints basename.

Emits OK_FUTURE_CONSTRAINTS on success or FUTURE_CONSTRAINT_REGRESSION on
failure.
"""
import argparse
import datetime
import pathlib
import re
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


# Legacy B-route / B14.0 contract. Preserved verbatim so existing
# reports/rp5/broute_future_constraints.md and
# reports/rp5/b14_0_future_constraints.md keep validating with
# OK_FUTURE_CONSTRAINTS.
BROUTE_PROFILE = {
    "required_constraint_ids": [
        "FC-B14-0-PUBLIC-GATE",
        "FC-B14-1-FUNNEL",
        "FC-B15-MULTI-NETWORK",
        "FC-HANDOFF-DATAMOVE1",
    ],
    "required_fields": [
        "constraint_id",
        "source_preplan_section",
        "current_scope_impact",
        "must_preserve_in_current_plan",
        "forbidden_current_plan_regression",
        "validator_or_review_check",
        "future_phase_owner",
        "out_of_scope_but_preserved",
    ],
    "reject_extra_ids": False,
    "scan_plan_files": [
        "docs/plans/broute/agent_plan.md",
        "docs/plans/broute/orchestrator_plan.md",
        "docs/plans/broute/state_packet_schemas.yaml",
    ],
    "forbidden_markers": {
        "FC-B14-1-FUNNEL": [
            "tailscale funnel enabled in b-route",
            "funnel serve command added in b-route",
            "systemd unit for funnel installed by b-route",
        ],
        "FC-B14-0-PUBLIC-GATE": [
            "recruiter password set in b-route runtime",
            "public tunnel exposed by b-route",
        ],
        "FC-B15-MULTI-NETWORK": [
            "public smoke coverage claimed from b-route tests",
        ],
        "FC-HANDOFF-DATAMOVE1": [
            "router schema changed after handoff gate without diff report",
        ],
    },
}


# B14.1 future-constraint contract. Required ids and the record field name
# match docs/plans/b14_1/orchestrator_plan.md section 3 and
# docs/plans/b14_1/state_packet_schemas.yaml future_constraint_preservation_record.
B14_1_PROFILE = {
    "required_constraint_ids": [
        "FC-B14-1-FUNNEL",
        "FC-B15-MULTI-NETWORK",
        "FC-HANDOFF-DATAMOVE1",
        "FC-BROUTE-FROZEN",
        "FC-B14-0-GATE-PRESERVED",
    ],
    "required_fields": [
        "constraint_id",
        "source_section",
        "current_scope_impact",
        "must_preserve_in_current_plan",
        "forbidden_current_plan_regression",
        "validator_or_review_check",
        "future_phase_owner",
        "out_of_scope_but_preserved",
    ],
    "reject_extra_ids": True,
    "scan_plan_files": [
        "docs/plans/b14_1/agent_plan.md",
        "docs/plans/b14_1/orchestrator_plan.md",
        "docs/plans/b14_1/state_packet_schemas.yaml",
    ],
    "forbidden_markers": {
        "FC-B14-1-FUNNEL": [
            "b14.1 enables tailscale funnel serve",
            "ephemeral tunnel url accepted as success evidence",
        ],
        "FC-B15-MULTI-NETWORK": [
            "b14.1 claims multi-network public smoke coverage",
        ],
        "FC-HANDOFF-DATAMOVE1": [
            "b14.1 changes the router runtime schema",
        ],
        "FC-BROUTE-FROZEN": [
            "b14.1 edits the broute plan deliverables",
        ],
        "FC-B14-0-GATE-PRESERVED": [
            "b14.1 removes the recruiter http basic gate",
        ],
    },
}


PROFILES = {
    "broute": BROUTE_PROFILE,
    "b14_1": B14_1_PROFILE,
}


PUBLIC_URL_LITERAL_RE = re.compile(
    r"https?://(?!127\.0\.0\.1)(?!localhost)[A-Za-z0-9.-]+(?::\d+)?(?:/\S*)?"
)


def infer_profile(constraints_path):
    """Deterministically pick a profile from the --constraints basename."""
    name = pathlib.Path(constraints_path).name
    if name.startswith("b14_1_"):
        return "b14_1"
    if name.startswith("b14_0_"):
        return "broute"
    if name.startswith("broute"):
        return "broute"
    return "broute"


def parse_records(text):
    records = {}
    current_id = None
    current_record = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        header = re.match(r"^##\s+(FC-[A-Z0-9\-]+)\s*$", line)
        if header:
            if current_id is not None:
                records[current_id] = current_record
            current_id = header.group(1)
            current_record = {}
            continue
        if current_id is None:
            continue
        kv = re.match(r"^-\s*([A-Za-z_]+):\s*(.+)$", line)
        if kv:
            key = kv.group(1).strip()
            value = kv.group(2).strip()
            current_record[key] = value
    if current_id is not None:
        records[current_id] = current_record
    return records


def check_no_public_url_literal(text):
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in PUBLIC_URL_LITERAL_RE.finditer(line):
            hits.append((line_no, m.group(0)))
    return hits


def check_no_enactment_of_forbidden_strings(records, profile):
    findings = []
    forbidden_markers = profile["forbidden_markers"]
    haystacks = []
    for rel_path in profile["scan_plan_files"]:
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        haystacks.append((path, path.read_text().lower()))
    for fc_id, _record in records.items():
        for needle in forbidden_markers.get(fc_id, []):
            for path, hay in haystacks:
                if needle.lower() in hay:
                    findings.append((fc_id, needle, str(path.relative_to(REPO_ROOT))))
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--constraints", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--constraint-profile",
        choices=("broute", "b14_1"),
        default=None,
        help="future-constraint contract profile; inferred from --constraints "
        "basename when omitted",
    )
    args = parser.parse_args()

    constraints_path = pathlib.Path(args.constraints)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    profile_name = args.constraint_profile or infer_profile(args.constraints)
    profile = PROFILES[profile_name]
    required_ids = profile["required_constraint_ids"]
    required_fields = profile["required_fields"]

    issues = []

    if not constraints_path.exists():
        issues.append(f"constraints file not found: {constraints_path}")
        records = {}
        text = ""
    else:
        text = constraints_path.read_text()
        records = parse_records(text)

    # 1. All required constraint ids present
    for fc_id in required_ids:
        if fc_id not in records:
            issues.append(f"missing constraint id: {fc_id}")

    # 1b. Reject extra ids when the profile forbids them
    if profile["reject_extra_ids"]:
        for fc_id in records:
            if fc_id not in required_ids:
                issues.append(f"extra constraint id not permitted: {fc_id}")

    # 2. Each record carries all required fields
    for fc_id, rec in records.items():
        for field in required_fields:
            if field not in rec or rec[field] == "":
                issues.append(f"{fc_id}: missing or empty field {field}")
        if rec.get("constraint_id") and rec.get("constraint_id") != fc_id:
            issues.append(
                f"{fc_id}: constraint_id field {rec['constraint_id']!r} does not match section header"
            )

    # 3. out_of_scope_but_preserved must be true
    for fc_id, rec in records.items():
        if fc_id in required_ids:
            value = rec.get("out_of_scope_but_preserved", "").strip().lower()
            if value != "true":
                issues.append(
                    f"{fc_id}: out_of_scope_but_preserved must be true, got {value!r}"
                )

    # 4. No literal public URL in the constraints document
    url_hits = check_no_public_url_literal(text)
    for line_no, literal in url_hits:
        issues.append(f"public URL literal at line {line_no}: {literal}")

    # 5. No active-plan enactment of forbidden_current_plan_regression strings
    enactments = check_no_enactment_of_forbidden_strings(records, profile)
    for fc_id, needle, path in enactments:
        issues.append(f"{fc_id}: forbidden enactment marker {needle!r} found in {path}")

    failed = len(issues) > 0
    sentinel = "FUTURE_CONSTRAINT_REGRESSION" if failed else "OK_FUTURE_CONSTRAINTS"

    lines = [
        "# Future Constraint Validation Report",
        "",
        f"generated_at_utc: {datetime.datetime.utcnow().isoformat()}",
        f"constraints_file: {args.constraints}",
        f"constraint_profile: {profile_name}",
        f"records_parsed: {len(records)}",
        f"required_constraint_ids: {len(required_ids)}",
        f"issues: {len(issues)}",
        "",
        "## Constraint Ids Present",
        "",
    ]
    for fc_id in required_ids:
        present = "PASS" if fc_id in records else "FAIL"
        lines.append(f"- [{present}] {fc_id}")
    lines += ["", "## Issues", ""]
    if issues:
        for i in issues:
            lines.append(f"- {i}")
    else:
        lines.append("- none")
    lines += ["", f"## Result: {sentinel}", "", sentinel]

    out_path.write_text("\n".join(lines) + "\n")
    print(sentinel)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
