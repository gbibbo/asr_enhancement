from __future__ import annotations

import logging

from services.worker.app.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="worker.transcribe_job")
def transcribe_job(job_id: str) -> None:
    logger.info(
        "transcribe_job stub received job_id=%s; real processing is Task 3.4", job_id
    )
