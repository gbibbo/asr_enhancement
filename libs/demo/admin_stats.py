"""Builder for the B12.1 ``/admin/stats`` response.

Pure composition: persistence reads + provider-state admin view + read-only
probes + in-process counters from ``app.state``. Keeps
``services/api/app/demo_main.py`` thin and testable.

Privacy contract (rev-2 plan §E):

* No filesystem paths in the response — disk usage carries ``scope =
  "demo_runtime_root"`` (constant label), not the actual path.
* ``last_errors`` is demo-api process-local; demo-worker errors are NOT
  aggregated here. Worker error visibility is provided by
  ``demo.worker.log`` once file logging is enabled.
* Spend/cap fields come from ``compute_admin_view`` and stay inside the
  Basic-auth gate; the public ``compute_public_view`` is unchanged.
* No transcript, GT, raw_payload, session_id_hash, ledger_id, filename, or
  cloudflared URL ever appears in the response.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from libs.common.demo_settings import DemoSettings
from libs.demo.cleanup import LAST_CLEANUP_KEY
from libs.demo.persistence import (
    count_active_jobs,
    count_cache_entries,
    get_admin_state_value,
    get_jobs_stats,
)
from libs.demo.probes import (
    read_cloudflare_tunnel_state,
    read_cpu_temp_celsius,
    read_disk_usage,
)
from libs.demo.usage import compute_admin_view
from libs.observability.error_buffer import _ErrorBufferHandler, buffer_snapshot


def build_admin_stats(
    *,
    settings: DemoSettings,
    request_count_total: int,
    cache_hit_count: int,
    cache_miss_count: int,
    error_buffer_handler: Optional[_ErrorBufferHandler] = None,
) -> dict[str, Any]:
    """Compose the authenticated /admin/stats response.

    Caller (demo_main.lifespan -> /admin/stats) supplies the in-process
    counters that this module does not own. ``error_buffer_handler`` may be
    ``None`` (e.g. unit tests that bypass lifespan); in that case
    ``last_errors`` is an empty list.
    """
    db_path = settings.demo_db_path
    startup_iso = get_admin_state_value(db_path, "startup_time")
    uptime = 0.0
    if startup_iso:
        delta = datetime.now(timezone.utc) - datetime.fromisoformat(startup_iso)
        uptime = max(0.0, delta.total_seconds())

    hits = max(0, int(cache_hit_count))
    misses = max(0, int(cache_miss_count))
    denom = hits + misses
    hit_rate = (hits / denom) if denom > 0 else 0.0

    last_errors: list[dict[str, Any]]
    if error_buffer_handler is None:
        last_errors = []
    else:
        last_errors = buffer_snapshot(error_buffer_handler)

    return {
        "startup_time": startup_iso,
        "uptime_seconds": uptime,
        "queue_depth": count_active_jobs(db_path),
        "jobs_by_status": get_jobs_stats(db_path),
        "provider_state": compute_admin_view(db_path, settings),
        "request_count_total": int(request_count_total),
        "cache": {
            "entries_total": count_cache_entries(db_path),
            "hits_total": hits,
            "misses_total": misses,
            "hit_rate": round(hit_rate, 6),
        },
        "disk": read_disk_usage(settings),
        "cpu_temperature": read_cpu_temp_celsius(),
        "last_errors": last_errors,
        "cloudflare_tunnel": read_cloudflare_tunnel_state(),
        "last_cleanup_at": get_admin_state_value(db_path, LAST_CLEANUP_KEY),
    }
