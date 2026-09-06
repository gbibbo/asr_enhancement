# B14.2 OpenAPI / Docs / Redoc Visibility Under Public Exposure

generated_at_utc: 2026-05-24T00:50:35.414182+00:00
mode: live
base_url: http://127.0.0.1:18001
public_exposure_flag_expected: PUBLIC_DEMO_EXPOSURE=true
expected_route_state: unmounted (HTTP 404)
checks: 2
failures: 0

## Routes Probed

- openapi: /openapi.json
- docs: /docs
- redoc: /redoc

## Invariant Results

- [PASS] every_docs_route_observed: all 3 docs routes observed
- [PASS] every_docs_route_returns_404_under_public_exposure_true: every docs route returned 404 (unmounted)

## Sentinel

OK_B14_2_OPENAPI_DOCS_OFF
