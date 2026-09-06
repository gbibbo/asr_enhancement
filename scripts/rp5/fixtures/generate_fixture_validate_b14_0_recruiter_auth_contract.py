#!/usr/bin/env python3
"""
Fixture generator paired with validate_b14_0_recruiter_auth_contract.

Produces positive and negative fixtures for the
recruiter_auth_invariant_record and credential_storage_policy_record
shapes declared in docs/plans/b14_0/state_packet_schemas.yaml, with a
sha256 manifest. Positive fixtures pass the contract self-check; each
negative fixture violates exactly one rule.

Emits OK_FIXTURE_VALIDATE_B14_0_RECRUITER_AUTH_CONTRACT on PASS or
B14_0_RECRUITER_AUTH_CONTRACT_FAILED on FAIL.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import sys

SENTINEL_PASS = "OK_FIXTURE_VALIDATE_B14_0_RECRUITER_AUTH_CONTRACT"
SENTINEL_FAIL = "B14_0_RECRUITER_AUTH_CONTRACT_FAILED"
KINDS_ALLOWED = ["positive_and_negative"]

POSITIVE_AUTH_INVARIANT = {
    "invariant_id": "RECRUITER-AUTH-INVARIANT-001",
    "protected_route_glob": [
        "GET /demo/health",
        "GET /demo/examples",
        "POST /demo/run-cached",
        "POST /demo/jobs",
        "GET /demo/jobs/{job_id}",
        "GET /demo/providers/assemblyai/status",
    ],
    "expected_unauthenticated_status": 401,
    "expected_www_authenticate_value": 'Basic realm="asr-demo-recruiter"',
    "expected_authenticated_health_payload": '{"status":"ok"}',
    "forbidden_response_body_substrings": [
        "router_kind", "router_version", "routing_profile",
        "selected_backend", "allow_third_party",
        "<env:Authorization-header-value>",
        "<env:RECRUITER_PASSWORD-value>",
        "<env:ADMIN_STATS_PASSWORD-value>",
    ],
    "validator": "validate_b14_0_recruiter_auth_contract",
    "marker": "B14_0_RECRUITER_AUTH_CONTRACT_FAILED",
}

POSITIVE_CRED_POLICY = {
    "policy_id": "RECRUITER-CRED-STORAGE-001",
    "credential_name": "RECRUITER_USERNAME",
    "source": "environment_variable",
    "allowed_storage": ["environment_variable", "host_systemd_service_env"],
    "forbidden_storage": [
        "git_committed_file", "dockerfile_literal", "compose_file_literal",
        "plan_file_literal", "log_output", "error_response_body",
    ],
    "rotation_policy": "deferred_to_HAR-B14_0-RECRUITER-CREDS-001",
    "validator": "validate_b14_0_recruiter_auth_contract",
    "marker": "B14_0_RECRUITER_AUTH_CONTRACT_FAILED",
}


def _mutate(rec, **changes):
    out = copy.deepcopy(rec)
    for k, v in changes.items():
        if v is _DEL:
            out.pop(k, None)
        else:
            out[k] = v
    return out


class _DelSentinel:
    pass


_DEL = _DelSentinel()


def build_positive_fixtures():
    return [
        ("positive_recruiter_auth_invariant_canonical.json", POSITIVE_AUTH_INVARIANT),
        ("positive_credential_storage_policy_canonical.json", POSITIVE_CRED_POLICY),
    ]


def build_negative_fixtures():
    return [
        # Negative recruiter_auth_invariant_record fixtures
        ("negative_auth_invariant_missing_invariant_id.json",
         _mutate(POSITIVE_AUTH_INVARIANT, invariant_id=_DEL),
         "missing required field invariant_id"),
        ("negative_auth_invariant_wrong_status.json",
         _mutate(POSITIVE_AUTH_INVARIANT, expected_unauthenticated_status=200),
         "expected_unauthenticated_status not in schema enum [401]"),
        ("negative_auth_invariant_wrong_realm.json",
         _mutate(POSITIVE_AUTH_INVARIANT,
                 expected_www_authenticate_value='Basic realm="Restricted"'),
         "expected_www_authenticate_value does not match schema fixed value"),
        ("negative_auth_invariant_wrong_health_payload.json",
         _mutate(POSITIVE_AUTH_INVARIANT,
                 expected_authenticated_health_payload='{"status":"degraded"}'),
         "expected_authenticated_health_payload does not match schema fixed value"),
        ("negative_auth_invariant_missing_forbidden_substring.json",
         _mutate(POSITIVE_AUTH_INVARIANT,
                 forbidden_response_body_substrings=[
                     "router_version", "routing_profile",
                     "selected_backend", "allow_third_party",
                 ]),
         "forbidden_response_body_substrings missing literal needle router_kind"),
        ("negative_auth_invariant_truncated_protected_routes.json",
         _mutate(POSITIVE_AUTH_INVARIANT,
                 protected_route_glob=["GET /demo/health"]),
         "protected_route_glob does not match section 2 enumeration"),
        # Negative credential_storage_policy_record fixtures
        ("negative_cred_policy_wrong_source.json",
         _mutate(POSITIVE_CRED_POLICY, source="config_file"),
         "source not in schema enum [environment_variable]"),
        ("negative_cred_policy_extra_allowed_storage.json",
         _mutate(POSITIVE_CRED_POLICY,
                 allowed_storage=["environment_variable",
                                  "host_systemd_service_env",
                                  "git_committed_file"]),
         "allowed_storage outside schema enum"),
        ("negative_cred_policy_missing_forbidden_storage_value.json",
         _mutate(POSITIVE_CRED_POLICY,
                 forbidden_storage=["dockerfile_literal", "compose_file_literal",
                                    "plan_file_literal", "log_output",
                                    "error_response_body"]),
         "forbidden_storage missing schema-mandated value git_committed_file"),
        ("negative_cred_policy_empty_rotation_policy.json",
         _mutate(POSITIVE_CRED_POLICY, rotation_policy=""),
         "rotation_policy must be a non-empty string"),
    ]


def sha256_bytes(b):
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=KINDS_ALLOWED)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    manifest_path = pathlib.Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fixtures_dir = manifest_path.parent / "validate_b14_0_recruiter_auth_contract"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    positive = build_positive_fixtures()
    negative = build_negative_fixtures()

    manifest = {
        "validator": "validate_b14_0_recruiter_auth_contract",
        "kind": args.kind,
        "positive": [],
        "negative": [],
        "owned_marker": "B14_0_RECRUITER_AUTH_CONTRACT_FAILED",
        "sentinel_pass": SENTINEL_PASS,
    }

    for name, payload in positive:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / name
        path.write_bytes(body)
        manifest["positive"].append({
            "path": str(path),
            "sha256": sha256_bytes(body),
            "size_bytes": len(body),
            "expected_validator_outcome": "PASS",
        })

    for name, payload, violation in negative:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        path = fixtures_dir / name
        path.write_bytes(body)
        manifest["negative"].append({
            "path": str(path),
            "sha256": sha256_bytes(body),
            "size_bytes": len(body),
            "expected_validator_outcome": "FAIL",
            "violated_rule": violation,
        })

    # Adversarial smoke proof: feed each negative fixture through the same
    # schema-conformance predicates the validator uses, and confirm each
    # produces at least one error. This proves the negative fixtures are
    # genuinely negative; without it the fixture set is not adversarial.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    import validate_b14_0_recruiter_auth_contract as v

    adversarial_failures = []
    for entry, neg_record in zip(manifest["negative"],
                                 [n[1] for n in negative]):
        if "auth_invariant" in entry["path"]:
            errs = v.validate_recruiter_auth_invariant(neg_record)
        elif "cred_policy" in entry["path"]:
            errs = v.validate_credential_storage_policy(neg_record)
        else:
            errs = []
        entry["adversarial_smoke_errors"] = errs
        if not errs:
            adversarial_failures.append(entry["path"])

    for entry, pos_record in zip(manifest["positive"],
                                 [p[1] for p in positive]):
        if "auth_invariant" in entry["path"]:
            errs = v.validate_recruiter_auth_invariant(pos_record)
        elif "cred_policy" in entry["path"]:
            errs = v.validate_credential_storage_policy(pos_record)
        else:
            errs = []
        entry["adversarial_smoke_errors"] = errs
        if errs:
            adversarial_failures.append(entry["path"])

    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(manifest_body)
    manifest_sha = sha256_bytes(manifest_body)

    print(f"manifest_sha256: {manifest_sha}")
    print(f"positive_count: {len(manifest['positive'])}")
    print(f"negative_count: {len(manifest['negative'])}")
    if adversarial_failures:
        print(f"adversarial_failures: {adversarial_failures}")
        print(SENTINEL_FAIL)
        return 1

    print(SENTINEL_PASS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
