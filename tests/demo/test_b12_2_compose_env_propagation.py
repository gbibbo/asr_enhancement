"""B12.2 docker-compose.demo.yml x-demo-env propagation check.

Static check: every demo_alert_* field in DemoSettings.model_fields must have
a corresponding upper-snake-case env key in the x-demo-env block of the
compose file.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


_COMPOSE_PATH = Path(__file__).parent.parent.parent / "infra" / "compose" / "docker-compose.demo.yml"


def _load_x_demo_env() -> dict:
    with _COMPOSE_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("x-demo-env", {})


def _get_alert_setting_field_names() -> list[str]:
    from libs.common.demo_settings import DemoSettings
    return [
        name for name in DemoSettings.model_fields
        if name.startswith("demo_alert_")
    ]


def test_compose_file_exists():
    assert _COMPOSE_PATH.exists(), f"Compose file not found: {_COMPOSE_PATH}"


def test_all_demo_alert_fields_have_compose_env_entry():
    x_demo_env = _load_x_demo_env()
    compose_keys = set(x_demo_env.keys())
    alert_fields = _get_alert_setting_field_names()

    assert len(alert_fields) > 0, "No demo_alert_* fields found in DemoSettings"

    missing = []
    for field_name in alert_fields:
        env_key = field_name.upper()
        if env_key not in compose_keys:
            missing.append((field_name, env_key))

    assert not missing, (
        "The following demo_alert_* settings fields have no x-demo-env entry:\n"
        + "\n".join(f"  {f!r} -> expected {k!r}" for f, k in missing)
    )


def test_compose_env_smtp_password_uses_empty_default():
    """SMTP password must use ${VAR:-} (empty default) not a real value."""
    x_demo_env = _load_x_demo_env()
    smtp_pass_val = x_demo_env.get("DEMO_ALERT_SMTP_PASSWORD", "")
    # The value should be the interpolation expression, which yaml loads as a string.
    # It should not contain any non-empty literal password.
    # A valid empty-default form when loaded by yaml is either empty string or
    # the expression string. It must NOT be a 16+ char alphanum that looks like a real password.
    val_str = str(smtp_pass_val)
    import re
    assert not re.search(r"[A-Za-z0-9]{16,}", val_str), (
        f"DEMO_ALERT_SMTP_PASSWORD in compose looks like a real password: {val_str!r}"
    )


def test_compose_env_smtp_username_uses_empty_default():
    """SMTP username must use ${VAR:-} (empty default) not a real value."""
    x_demo_env = _load_x_demo_env()
    val = x_demo_env.get("DEMO_ALERT_SMTP_USERNAME", "")
    val_str = str(val)
    assert "@" not in val_str or "${" in val_str or val_str == "", (
        f"DEMO_ALERT_SMTP_USERNAME in compose looks like a real address: {val_str!r}"
    )


def test_compose_email_to_empty_default():
    """DEMO_ALERT_EMAIL_TO must use empty default."""
    x_demo_env = _load_x_demo_env()
    val = x_demo_env.get("DEMO_ALERT_EMAIL_TO", "")
    val_str = str(val)
    # Must not contain an actual email address (only interpolation or empty).
    assert "@" not in val_str or "${" in val_str or val_str == "", (
        f"DEMO_ALERT_EMAIL_TO in compose looks like a real address: {val_str!r}"
    )
