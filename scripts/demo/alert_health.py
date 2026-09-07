"""B12.2 Health check alert script.

Designed for cron execution. Exits 0 on all paths (including internal errors)
so cron does not flood MAILTO= on transient problems.

Usage:
    python -m scripts.demo.alert_health

Environment variables are read via DemoSettings (reads .env.demo when present).
The URL string from DEMO_ALERT_HEALTH_URL is NEVER logged — only the constant
label "demo_health_local" appears in log output.

/demo/health sits behind the recruiter HTTPBasic gate, so the probe sends
Basic credentials from RECRUITER_USERNAME / RECRUITER_PASSWORD when both are
set (same env the API container already receives from .env.demo). Without
them the probe would get a permanent 401 and report a healthy demo as down.
Credentials are read only to build the Authorization header and are NEVER
logged nor included in the alert body.

Host-side vs. Compose-cron execution:
- Host/manual dry-run: DEMO_ALERT_HEALTH_URL default is http://localhost:8001/demo/health
- Compose-cron: override to http://demo-api:8000/demo/health (Compose network DNS)
  via: -e DEMO_ALERT_HEALTH_URL=http://demo-api:8000/demo/health
"""

from __future__ import annotations

import base64
import logging
import os
import sys
import urllib.error
import urllib.request

_log = logging.getLogger("demo-alerts")

# Fixed HTTP probe timeout in seconds. Not a settings field — separate concern
# from SMTP timeout and simpler to keep hardcoded.
_HTTP_TIMEOUT_SECONDS = 5.0

# Constant label used in logs and alert body (URL string is never logged).
_ENDPOINT_LABEL = "demo_health_local"

# Env names of the recruiter gate credentials, mirroring
# services/api/app/recruiter_auth.py. Read directly from the environment so the
# values never enter DemoSettings or any log/alert payload.
_RECRUITER_USERNAME_ENV = "RECRUITER_USERNAME"
_RECRUITER_PASSWORD_ENV = "RECRUITER_PASSWORD"


def _build_probe_request(url: str) -> urllib.request.Request:
    """Build the probe request, adding recruiter Basic auth when configured.

    The url and the credentials are used only to construct the request; neither
    is ever logged.
    """
    request = urllib.request.Request(url)
    username = os.environ.get(_RECRUITER_USERNAME_ENV, "")
    password = os.environ.get(_RECRUITER_PASSWORD_ENV, "")
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    return request


def _classify_urlopen(url: str) -> tuple[bool, str]:
    """Attempt GET on url; return (success, status_kind).

    status_kind values: "ok", "http_4xx", "http_5xx", "timeout",
    "connection_error".
    The url argument is only used for the actual request; it is NEVER logged.
    """
    try:
        request = _build_probe_request(url)
        with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
            code = resp.status
    except urllib.error.HTTPError as exc:
        code = exc.code
        if 400 <= code < 500:
            return False, "http_4xx"
        return False, "http_5xx"
    except TimeoutError:
        return False, "timeout"
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, TimeoutError):
            return False, "timeout"
        return False, "connection_error"
    except OSError:
        return False, "connection_error"

    if 200 <= code < 300:
        return True, "ok"
    if 400 <= code < 500:
        return False, "http_4xx"
    return False, "http_5xx"


def main() -> int:
    try:
        from libs.common.demo_settings import DemoSettings
        from libs.observability.alert_state import update_health_state
        from libs.observability.alerts import send_alert
        from libs.observability.logging import configure_logging

        configure_logging("demo-alerts")

        settings = DemoSettings()

        # URL string is read only for the HTTP call, never logged.
        url = settings.demo_alert_health_url
        success, status_kind = _classify_urlopen(url)

        state_path = settings.demo_alert_health_state_file

        decision = update_health_state(
            state_path,
            success=success,
            status_kind=status_kind,
            threshold=settings.demo_alert_health_consecutive_failures,
            cooldown_minutes=settings.demo_alert_health_cooldown_minutes,
        )

        if decision.should_fire:
            from libs.demo.persistence import get_admin_state_value
            last_check_at = None
            try:
                import json as _json
                raw = state_path.read_text(encoding="utf-8")
                data = _json.loads(raw)
                last_check_at = data.get("last_check_at")
            except Exception:  # noqa: BLE001
                pass

            fields = {
                "endpoint_label": _ENDPOINT_LABEL,
                "consecutive_failures": decision.consecutive_failures,
                "last_status_kind": decision.last_status_kind,
                "last_check_at_utc": last_check_at or "",
            }
            send_alert(
                settings,
                event="health_check_failed",
                severity="error",
                fields=fields,
            )

    except Exception as exc:  # noqa: BLE001
        error_class = type(exc).__name__
        try:
            _log.error(
                "alert.script_error",
                extra={"error_class": error_class, "script": "alert_health"},
            )
        except Exception:  # noqa: BLE001
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
