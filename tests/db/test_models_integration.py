from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

from libs.common.db import make_engine
from libs.common.models import Job, JobMode, JobStatus


@pytest.fixture
def db_session():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping PostgreSQL integration test")

    engine = make_engine(url)
    connection = engine.connect()
    transaction = connection.begin()

    if "jobs" not in sa_inspect(connection).get_table_names():
        transaction.rollback()
        connection.close()
        engine.dispose()
        pytest.fail(
            "'jobs' table not found — run 'alembic upgrade head' before integration tests"
        )

    factory = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)
    session = factory()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


def test_create_job(db_session):
    job = Job(
        status=JobStatus.queued,
        mode=JobMode.transcribe_only,
        provider="fake",
        preset="bypass",
    )
    db_session.add(job)
    db_session.flush()
    db_session.refresh(job)

    assert isinstance(job.id, uuid.UUID)
    assert job.status == JobStatus.queued
    assert job.mode == JobMode.transcribe_only
    assert job.provider == "fake"
    assert job.preset == "bypass"
    assert job.created_at is not None
    assert job.updated_at is not None
    assert job.raw_audio_uri is None
    assert job.enhanced_audio_uri is None
    assert job.transcript_uri is None
    assert job.transcript_text is None
    assert job.provider_payload_uri is None
    assert job.error_message is None
    assert job.started_at is None
    assert job.completed_at is None


def test_read_job_by_id(db_session):
    job = Job(
        status=JobStatus.queued,
        mode=JobMode.transcribe_only,
        provider="fake",
        preset="bypass",
    )
    db_session.add(job)
    db_session.flush()
    job_id = job.id

    fetched = db_session.get(Job, job_id)
    assert fetched is not None
    assert fetched.id == job_id
    assert fetched.status == JobStatus.queued


def test_provider_and_preset_defaults(db_session):
    job = Job(status=JobStatus.queued, mode=JobMode.transcribe_only)
    db_session.add(job)
    db_session.flush()
    db_session.refresh(job)

    assert job.provider == "fake"
    assert job.preset == "bypass"


def test_nullable_fields_accept_values(db_session):
    job = Job(
        status=JobStatus.completed,
        mode=JobMode.transcribe_only,
        provider="fake",
        preset="bypass",
        raw_audio_uri="raw_audio/test-id/input.wav",
        transcript_uri="transcripts/test-id/transcript.json",
        transcript_text="This is a test transcript.",
        provider_payload_uri="provider_payloads/test-id/provider_response.json",
    )
    db_session.add(job)
    db_session.flush()
    db_session.refresh(job)

    assert job.raw_audio_uri == "raw_audio/test-id/input.wav"
    assert job.transcript_uri == "transcripts/test-id/transcript.json"
    assert job.transcript_text == "This is a test transcript."
    assert job.provider_payload_uri == "provider_payloads/test-id/provider_response.json"
    assert job.enhanced_audio_uri is None
    assert job.error_message is None
