# B14.1 Local Bypass Justification

Produced by: B14_1-05 (local bypass justification).
Schema: docs/plans/b14_1/state_packet_schemas.yaml — local_bypass_justification_record.
No literal public URL, stable hostname, Tailscale auth-key, Cloudflare token, recruiter password, admin password, or Authorization value appears in this file. The flag is referenced only by env-var name (PUBLIC_DEMO_EXPOSURE) and accessor name (get_public_demo_exposure_flag).

## STATE SNAPSHOT

```yaml
repo_root: /home/gbibbo/code/asr_enhancement
branch: feature/demo-runtime-rp5-v1
current_phase: B14.1
current_task: B14_1-05
last_completed_phase: B14.0
last_completed_task: B14_1-04
active_markers: []
expected_next_task: B14_1-05
requested_task_matches_tracker: true
```

## local_bypass_justification_record

```yaml
record_kind: local_bypass_justification_record
classification: explicit_NA_zero_bypasses
bypass_count: 0
applies_when_flag_is: PUBLIC_DEMO_EXPOSURE_false
must_be_disabled_when_flag_is: PUBLIC_DEMO_EXPOSURE_true
validator: validate_b14_1_local_bypass_justification
marker: B14_1_LOCAL_BYPASS_UNJUSTIFIED
bypasses: []
```

## Rationale (B14_1-01 through B14_1-04 source-tree state)

The B14.1 application-layer surface, as constructed across B14_1-01..B14_1-04, contains no local/dev authority-bypass surface that is active when PUBLIC_DEMO_EXPOSURE=false and would need to be disabled when PUBLIC_DEMO_EXPOSURE=true. Each B14.1 deliverable preserves authority semantics independent of the exposure flag:

- B14_1-01 introduced `services/api/app/public_exposure.py` as a single-purpose, read-only accessor (`get_public_demo_exposure_flag`). The module performs no FastAPI hook installation, no router mutation, and no authority decision; it returns a boolean only and never reads or logs any credential, hostname, token, or auth-key material.
- B14_1-02 confirmed that recruiter HTTPBasic remains the sole application-layer authority for public `/demo/*` access under PUBLIC_DEMO_EXPOSURE=true. No application-layer authority decision is keyed on network origin, client IP, source interface, Tailscale identity, X-Forwarded-For, or any header the public surface cannot independently authenticate.
- B14_1-03 preserved the recruiter gate end-to-end under PUBLIC_DEMO_EXPOSURE=true and flipped only the OpenAPI/docs/redoc visibility surface (`openapi_url`, `docs_url`, `redoc_url` set to `None` when the flag is true). This is a visibility decision, not an authority decision: the recruiter dependency on the six recruiter-protected `/demo/*` routes is identical in both modes.
- B14_1-04 authored only the placeholder Tailscale Funnel template at `infra/tunnel/funnel_config.template.yaml` with no application-layer surface, no real Tailscale auth-key, no Cloudflare token, no stable hostname literal, and no public URL literal.

The only effective use of the exposure flag inside the application-layer surface is the OpenAPI/docs/redoc visibility toggle in `services/api/app/demo_main.py`, which is classified by the paired validator as `OPENAPI_DOCS_VISIBILITY_TOGGLE` (CLASS C — visibility-only, not an authority bypass) and is governed by the B14_1-03 deliverable. No environment-keyed auth-skip predicate, route-allowlist short-circuit, debug-flag bypass, recruiter-gate dependency override, or `if PUBLIC_DEMO_EXPOSURE is false: skip` shaped predicate exists in the application source tree.

## Scan scope

The paired validator scans the following subtrees for any reference to the flag identifier `PUBLIC_DEMO_EXPOSURE` or the accessor `get_public_demo_exposure_flag` and classifies each hit:

- `services/api/app/**.py`
- `libs/**.py`
- `tests/demo/**.py`

Classifications:

- CLASS A — `ACCESSOR_MODULE` — the read-only accessor at `services/api/app/public_exposure.py` is allow-listed by path.
- CLASS B — `IMPORT_OR_TEXT` — bare `import` / `from` lines and comment-only lines referencing the flag identifier.
- CLASS C — `OPENAPI_DOCS_VISIBILITY_TOGGLE` — a conditional whose immediate textual context references only the visibility vocabulary (`openapi_url`, `docs_url`, `redoc_url`, `FastAPI(`, `app =`, `application =`, `title=`, `version=`, `lifespan=`) and none of the authority vocabulary (`recruiter_auth`, `RecruiterAuthChallenge`, `Depends(`, `RECRUITER_`, `Authorization`, `compare_digest`, `WWW-Authenticate`, `HTTPBasic`, `status_code=401`, `raise HTTPException`, `return Response(`).
- CLASS D — `BYPASS_CANDIDATE` — every other hit. A non-zero CLASS D count would force `B14_1_LOCAL_BYPASS_UNJUSTIFIED` and is incompatible with `classification: explicit_NA_zero_bypasses`.

The validator additionally cross-checks this record's `validator` and `marker` fields and ensures the `bypasses:` list is empty when `classification: explicit_NA_zero_bypasses` is asserted.

## HAR posture (informational, not resolved by B14_1-05)

```yaml
HAR-B14_1-FUNNEL-CAPABILITY-001:
  status: partially_resolved_at_B14_1-04_threshold
  residual_blocker_carried_forward: tailscale_authkey_supplied_as_host_env_TAILSCALE_AUTHKEY=false
  blocks_B14_1-05: false
  action_in_this_task: none
HAR-B14_1-STABLE-HOSTNAME-001:
  status: pre_declared_unresolved
  blocks_B14_1-05: false
  action_in_this_task: none
```

## Failure routing

If a future change to the application-layer surface introduces a flag-keyed authority-bypass surface, the validator will emit `B14_1_LOCAL_BYPASS_UNJUSTIFIED` and the corresponding recovery packet `RP-B14_1-LOCAL-BYPASS-UNJUSTIFIED` (agent_plan §11) gates a same-task retry. Authoring `tests/demo/test_b14_1_local_bypass_disabled_under_public_exposure.py` is not part of the B14_1-05 primary route; introducing any such bypass requires `CHANGE_SCOPE`.

## Validator command

```bash
python3 scripts/rp5/validate_b14_1_local_bypass_justification.py \
  --root . \
  --out /tmp/b14_1_05_local_bypass_validation.md
```

Expected sentinel: `OK_B14_1_LOCAL_BYPASS_JUSTIFIED`.

## Notes

- The classification `explicit_NA_zero_bypasses` is the primary B14_1-05 legal route under the current source-tree state.
- No public URL, stable hostname, auth-key, token, credential, or Authorization value appears in this report.
- No tracker mutation, public-exposure action, Funnel run, Cloudflare run, systemd install, multi-network smoke, or HAR resolution occurs as part of this task.
