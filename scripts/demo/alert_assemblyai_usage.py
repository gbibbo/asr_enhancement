"""AssemblyAI usage-rate email alert.

Designed for cron execution. Fires an email when more than
``demo_alert_assemblyai_usage_threshold`` AssemblyAI uses occur within the
rolling window (default 24h), at most once per cooldown. Exits 0 on all paths
(including internal errors) so cron does not flood MAILTO= on transient issues.

Usage:
    python -m scripts.demo.alert_assemblyai_usage

Config is read via DemoSettings (reads .env.demo when present). The email is
only sent when DEMO_ALERT_EMAIL_ENABLED=true and the SMTP fields are configured;
otherwise send_alert logs a dry-run line and delivers nothing.
"""

from __future__ import annotations

import logging
import sys

_log = logging.getLogger("demo-alerts")


def main() -> int:
    try:
        from datetime import datetime, timedelta, timezone

        from libs.common.demo_settings import DemoSettings
        from libs.demo.persistence import count_assemblyai_uses_since
        from libs.observability.alert_state import (
            mark_assemblyai_usage_alert_sent,
            should_fire_assemblyai_usage,
        )
        from libs.observability.alerts import send_alert
        from libs.observability.logging import configure_logging

        configure_logging("demo-alerts")

        settings = DemoSettings()
        db_path = settings.demo_db_path

        window_hours = settings.demo_alert_assemblyai_usage_window_hours
        threshold = settings.demo_alert_assemblyai_usage_threshold
        cooldown_hours = settings.demo_alert_assemblyai_usage_cooldown_hours

        since_iso = (
            datetime.now(timezone.utc) - timedelta(hours=window_hours)
        ).isoformat()
        usage_count = count_assemblyai_uses_since(db_path, since_iso)

        fire = should_fire_assemblyai_usage(
            usage_count=usage_count,
            threshold=threshold,
            cooldown_hours=cooldown_hours,
            db_path=db_path,
        )

        if fire:
            result = send_alert(
                settings,
                event="assemblyai_usage_high",
                severity="warning",
                fields={
                    "provider": "assemblyai",
                    "assemblyai_usage_count": usage_count,
                    "assemblyai_usage_threshold": threshold,
                    "window_hours": window_hours,
                },
            )
            if result.delivered:
                mark_assemblyai_usage_alert_sent(db_path)

    except Exception as exc:  # noqa: BLE001
        try:
            _log.error(
                "alert.script_error",
                extra={
                    "error_class": type(exc).__name__,
                    "script": "alert_assemblyai_usage",
                },
            )
        except Exception:  # noqa: BLE001
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
