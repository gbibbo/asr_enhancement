from __future__ import annotations

import json
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
    from libs.demo.persistence import (
        claim_next_job,
        ensure_runtime_dirs,
        init_schema,
        update_job_artifacts,
        update_job_status,
    )
    from libs.demo.processing import (
        default_asr_factory,
        default_enhancer_factory,
        process_upload_job,
    )

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    settings = DemoSettings()
    ensure_runtime_dirs(settings)
    init_schema(settings.demo_db_path)

    asr_factory = default_asr_factory(settings)
    enhancer_factory = default_enhancer_factory(settings)

    log.info("Demo worker started, polling SQLite queue at %s", settings.demo_db_path)

    while not _shutdown:
        job = claim_next_job(settings.demo_db_path)
        if job is None:
            time.sleep(1)
            continue

        job_id = job["job_id"]

        def _update_artifacts(**kwargs: object) -> None:
            update_job_artifacts(settings.demo_db_path, job_id, **kwargs)  # type: ignore[arg-type]

        try:
            outcome = process_upload_job(
                job,
                settings,
                asr_factory=asr_factory,
                enhancer_factory=enhancer_factory,
                update_artifacts=_update_artifacts,
            )
        except Exception as exc:  # pragma: no cover - defensive
            log.exception("Worker crash while processing job %s", job_id)
            update_job_status(
                settings.demo_db_path,
                job_id,
                "failed",
                error_message=f"Worker error: {type(exc).__name__}.",
            )
            continue

        if outcome.status == "completed":
            update_job_status(
                settings.demo_db_path,
                job_id,
                "completed",
                result_json=json.dumps(outcome.result, ensure_ascii=False),
            )
        else:
            update_job_status(
                settings.demo_db_path,
                job_id,
                "failed",
                error_message=outcome.error_message,
            )

    log.info("Demo worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
