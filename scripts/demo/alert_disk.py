"""B12.2 Disk usage alert script.

Designed for cron execution. Exits 0 on all paths (including internal errors)
so cron does not flood MAILTO= on transient problems.

Usage:
    python -m scripts.demo.alert_disk

Environment variables are read via DemoSettings (reads .env.demo when present).
Override DEMO_ALERT_DISK_THRESHOLD_PERCENT=0.0 to force a dry-run smoke test.
"""

from __future__ import annotations

import logging
import sys

_log = logging.getLogger("demo-alerts")


def main() -> int:
    try:
        from libs.common.demo_settings import DemoSettings
        from libs.demo.probes import read_disk_usage
        from libs.observability.alert_state import (
            mark_disk_alert_cleared,
            mark_disk_alert_sent,
            should_fire_disk,
        )
        from libs.observability.alerts import send_alert
        from libs.observability.logging import configure_logging

        configure_logging("demo-alerts")

        settings = DemoSettings()
        db_path = settings.demo_db_path

        disk = read_disk_usage(settings)
        used_percent = disk["used_percent"]

        fire = should_fire_disk(settings, used_percent=used_percent, db_path=db_path)

        if fire:
            fields = {
                "disk_used_percent": used_percent,
                "disk_total_bytes": disk.get("total_bytes", 0),
                "disk_free_bytes": disk.get("free_bytes", 0),
                "threshold_percent": settings.demo_alert_disk_threshold_percent,
                "scope": disk.get("scope", "demo_runtime_root"),
            }
            result = send_alert(
                settings,
                event="disk_usage_high",
                severity="warning",
                fields=fields,
            )
            if result.delivered:
                mark_disk_alert_sent(db_path)
        elif used_percent <= settings.demo_alert_disk_threshold_percent:
            # Usage dropped back below threshold; record cleared state if a
            # prior high-water row exists (mark_disk_alert_cleared is safe to
            # call unconditionally — it writes/overwrites the cleared key).
            from libs.demo.persistence import get_admin_state_value
            prior = get_admin_state_value(db_path, "last_alert_disk_usage_high_at")
            if prior is not None:
                mark_disk_alert_cleared(db_path)

    except Exception as exc:  # noqa: BLE001
        error_class = type(exc).__name__
        try:
            _log.error(
                "alert.script_error",
                extra={"error_class": error_class, "script": "alert_disk"},
            )
        except Exception:  # noqa: BLE001
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
