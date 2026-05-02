from __future__ import annotations

import logging
import signal
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("demo-worker")

_shutdown = False


def _handle_signal(signum: int, frame: object) -> None:
    global _shutdown
    log.info("Demo worker received signal %d, shutting down", signum)
    _shutdown = True


def main() -> None:
    from libs.common.demo_settings import DemoSettings
    from libs.demo.persistence import claim_next_job, ensure_runtime_dirs, init_schema, update_job_status

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    settings = DemoSettings()
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)

    log.info("Demo worker started, polling SQLite queue at %s", settings.demo_db_path)

    while not _shutdown:
        job = claim_next_job(settings.demo_db_path)
        if job is None:
            time.sleep(1)
            continue
        log.info("Processing job %s (B3.2 lifecycle placeholder — no real processing)", job["job_id"])
        update_job_status(
            settings.demo_db_path,
            job["job_id"],
            "failed",
            error_message="processing not yet implemented (B5)",
        )

    log.info("Demo worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
