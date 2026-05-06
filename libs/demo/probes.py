"""Read-only probes for the B12.1 admin_stats response.

All three probes are designed to **never** expose filesystem paths in their
return values. ``read_disk_usage`` reports the constant scope label
``"demo_runtime_root"`` rather than the sampled path, so the absolute path
(``/home/...``, override paths, per-subdir paths) never reaches the HTTP
response. CPU temperature reads the RP5 ``/sys/class/thermal/thermal_zone0``
node and degrades to ``unavailable`` per §B12.1 decision rule 2. Cloudflare
tunnel state defaults to ``unavailable`` per decision rule 3 — B14.1 owns
the cloudflared install and will populate a control-plane file later.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Optional

from libs.common.demo_settings import DemoSettings


_CPU_TEMP_PATH_DEFAULT = Path("/sys/class/thermal/thermal_zone0/temp")


def read_cpu_temp_celsius(
    *,
    sysfs_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Return ``{"state": "available", "celsius": float}`` or ``{"state": "unavailable"}``.

    ``sysfs_path`` is parametrised for testability; production callers omit it
    and the function looks up the module-level ``_CPU_TEMP_PATH_DEFAULT`` at
    call time so monkeypatch.setattr on the module attribute works.
    """
    target = sysfs_path if sysfs_path is not None else _CPU_TEMP_PATH_DEFAULT
    try:
        raw = target.read_text(encoding="utf-8").strip()
        millidegrees = int(raw)
        celsius = millidegrees / 1000.0
    except (FileNotFoundError, PermissionError, ValueError, OSError):
        return {"state": "unavailable"}
    return {"state": "available", "celsius": round(celsius, 3)}


def read_disk_usage(settings: DemoSettings) -> dict[str, Any]:
    """Return disk usage for the demo runtime root, with no path leakage.

    The sample target is ``DemoSettings.demo_admin_disk_usage_path`` (which
    defaults to ``demo_runtime_root`` via the settings model_validator).
    The response carries only the constant label ``scope =
    "demo_runtime_root"`` — never the absolute path.
    """
    target = settings.demo_admin_disk_usage_path or settings.demo_runtime_root
    try:
        usage = shutil.disk_usage(str(target))
    except (FileNotFoundError, PermissionError, OSError):
        return {
            "scope": "demo_runtime_root",
            "total_bytes": 0,
            "used_bytes": 0,
            "free_bytes": 0,
            "used_percent": 0.0,
        }
    total = int(usage.total)
    used = int(usage.used)
    free = int(usage.free)
    pct = (used / total * 100.0) if total > 0 else 0.0
    return {
        "scope": "demo_runtime_root",
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "used_percent": round(pct, 3),
    }


def read_cloudflare_tunnel_state() -> dict[str, Any]:
    """Default to ``{"state": "unavailable"}`` per §B12.1 decision rule 3.

    B12.1 only wires the read-side contract; B14.1 owns cloudflared install
    and will populate a control-plane file later. No tunnel URL or token is
    ever returned from this probe.
    """
    return {"state": "unavailable"}
