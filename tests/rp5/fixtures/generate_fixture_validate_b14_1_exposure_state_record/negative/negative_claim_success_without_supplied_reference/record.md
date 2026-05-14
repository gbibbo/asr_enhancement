# Exposure State Record Fixture

## exposure_state_record

```yaml
exposure_state_id: ESR-FIXTURE-NEGATIVE
exposure_mode: loopback_only
public_exposure_flag: PUBLIC_DEMO_EXPOSURE_false
stable_hostname_source_reference: env_var_name_PUBLIC_DEMO_STABLE_HOSTNAME
stable_hostname_supplied_by_reference: false
blocker_if_unsupplied: HAR-B14_1-STABLE-HOSTNAME-001
validator: validate_b14_1_exposure_state_record
marker: B14_1_EPHEMERAL_URL_SUCCESS_CLAIM
```

## public_exposure_claim_record

```yaml
claim_id: PECR-FIXTURE-NEGATIVE
claim_status: SUCCESS_WITH_STABLE_NAMED_EXPOSURE
stable_named_exposure_supplied_by_reference: false
explicit_blocker_id: null
blocker_recovery_packet: null
validator: validate_b14_1_exposure_state_record
marker: B14_1_EPHEMERAL_URL_SUCCESS_CLAIM
```
