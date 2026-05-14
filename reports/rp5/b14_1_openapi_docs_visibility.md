# B14_1-03 OpenAPI / Interactive Docs Visibility

generated_at_utc: 2026-05-14T20:42:49.259007+00:00
base_url: http://127.0.0.1:8001
routes_probed: 3

## openapi_docs_visibility_record

```yaml
visibility_id: ODV-B14_1-03
public_exposure_flag: PUBLIC_DEMO_EXPOSURE_true
openapi_route_state: unmounted
docs_route_state: unmounted
redoc_route_state: unmounted
narrow_admin_only_exception_path: not_enacted
validator: validate_b14_1_openapi_docs_visibility
marker: B14_1_OPENAPI_OR_DOCS_LEAK_DETECTED
```

## Checks

- [PASS] openapi_route_state_under_public_exposure: path=/openapi.json state=unmounted status=404
- [PASS] docs_route_state_under_public_exposure: path=/docs state=unmounted status=404
- [PASS] redoc_route_state_under_public_exposure: path=/redoc state=unmounted status=404

## Result

All probed docs routes are unmounted or admin-only under PUBLIC_DEMO_EXPOSURE=true.

OK_B14_1_OPENAPI_DOCS_OFF
