"""B12.2 build_alert_body closed-allowlist enforcement.

Verifies that build_alert_body never includes fields from the §D forbidden
list when callers try to pass them via the fields= dict.
"""

from __future__ import annotations

import pytest

from libs.observability.alerts import build_alert_body


_FORBIDDEN_VALUES = {
    "transcript": "SENTINEL_TRANSCRIPT",
    "text": "SENTINEL_TEXT",
    "hypothesis": "SENTINEL_HYPOTHESIS",
    "reference": "SENTINEL_REFERENCE",
    "reference_text": "SENTINEL_REFERENCE_TEXT",
    "ground_truth": "SENTINEL_GROUND_TRUTH",
    "gt": "SENTINEL_GT",
    "raw_payload": "SENTINEL_RAW_PAYLOAD",
    "provider_payload": "SENTINEL_PROVIDER_PAYLOAD",
    "session_id": "SENTINEL_SESSION_ID",
    "session_id_hash": "SENTINEL_SESSION_HASH",
    "ledger_id": "SENTINEL_LEDGER_ID",
    "audio_path": "/etc/passwd",
    "input_path": "/home/gbibbo/secret.wav",
    "degraded_path": "/tmp/degraded.wav",
    "enhanced_path": "/tmp/enhanced.wav",
    "result_path": "/tmp/result.json",
    "filename": "my_secret_file.wav",
    "original_filename": "upload_secret.wav",
    "upload_filename": "private.wav",
    "cloudflared_url": "https://my-tunnel.trycloudflare.com",
    "tunnel_token": "TOKEN_XYZ_SECRET",
    "tunnel_url": "https://secret.tunnel.example.com",
    "api_key": "sk-123456789abcdef",
    "assemblyai_api_key": "AKEY_SECRET",
    "smtp_password": "SMTPPASSWORD_SECRET",
    "smtp_username": "smtp_user@example.invalid",
}


def test_build_alert_body_drops_all_forbidden_fields():
    body = build_alert_body(
        "disk_usage_high",
        "warning",
        fields=_FORBIDDEN_VALUES,
    )
    for value in _FORBIDDEN_VALUES.values():
        assert value not in body, (
            f"Forbidden value {value!r} leaked into alert body"
        )


def test_build_alert_body_drops_forbidden_keys():
    body = build_alert_body(
        "disk_usage_high",
        "warning",
        fields=_FORBIDDEN_VALUES,
    )
    for key in _FORBIDDEN_VALUES:
        assert f"\n{key}:" not in body, (
            f"Forbidden key {key!r} appeared in alert body"
        )


def test_build_alert_body_disk_contains_only_allowed_fields():
    disk_fields = {
        "disk_used_percent": 84.3,
        "disk_total_bytes": 30_000_000_000,
        "disk_free_bytes": 4_710_000_000,
        "threshold_percent": 80.0,
        "scope": "demo_runtime_root",
        # Inject a forbidden field that should be dropped:
        "audio_path": "/etc/passwd",
    }
    body = build_alert_body("disk_usage_high", "warning", fields=disk_fields)
    assert "scope: demo_runtime_root" in body
    assert "disk_used_percent: 84.3" in body
    assert "/etc/passwd" not in body
    assert "/home/" not in body


def test_build_alert_body_disk_scope_label_only_no_path():
    body = build_alert_body(
        "disk_usage_high",
        "warning",
        fields={"scope": "demo_runtime_root", "disk_used_percent": 85.0},
    )
    assert "demo_runtime_root" in body
    # No absolute path should appear.
    assert "/home/" not in body
    assert "/tmp/" not in body
    assert "/var/" not in body


def test_build_alert_body_health_endpoint_label_only():
    body = build_alert_body(
        "health_check_failed",
        "error",
        fields={
            "endpoint_label": "demo_health_local",
            "consecutive_failures": 3,
            "last_status_kind": "connection_error",
            "last_check_at_utc": "2026-05-05T12:00:00Z",
            # Inject URL that should be dropped:
            "tunnel_url": "https://secret.tunnel.example.com",
        },
    )
    assert "endpoint_label: demo_health_local" in body
    assert "consecutive_failures: 3" in body
    assert "last_status_kind: connection_error" in body
    assert "secret.tunnel" not in body
    assert "https://" not in body


def test_build_alert_body_last_status_kind_valid_enum():
    for kind in ("ok", "connection_error", "timeout", "http_4xx", "http_5xx"):
        body = build_alert_body(
            "health_check_failed",
            "error",
            fields={"last_status_kind": kind},
        )
        assert f"last_status_kind: {kind}" in body


def test_build_alert_body_constant_header_always_present():
    body = build_alert_body("test_event", "warning", fields={})
    assert "service: demo" in body
    assert "event: test_event" in body
    assert "severity: warning" in body
    assert "timestamp_utc:" in body
    assert "host: asr-rp5" in body


def test_build_alert_body_no_forbidden_field_names_in_output():
    forbidden_keys = [
        "transcript", "hypothesis", "session_id", "api_key",
        "smtp_password", "audio_path", "cloudflared_url",
    ]
    body = build_alert_body(
        "disk_usage_high",
        "warning",
        fields={k: f"value_{k}" for k in forbidden_keys},
    )
    for key in forbidden_keys:
        assert f"{key}:" not in body
