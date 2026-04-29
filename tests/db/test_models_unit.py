from __future__ import annotations

from libs.common.models import Job, JobMode, JobStatus


def test_job_status_values():
    assert {s.value for s in JobStatus} == {"queued", "running", "completed", "failed"}


def test_job_mode_values():
    assert {m.value for m in JobMode} == {"transcribe_only", "enhance_and_transcribe"}


def test_job_tablename():
    assert Job.__tablename__ == "jobs"


def test_job_columns_present():
    expected = {
        "id",
        "status",
        "mode",
        "provider",
        "preset",
        "raw_audio_uri",
        "enhanced_audio_uri",
        "transcript_uri",
        "transcript_text",
        "provider_payload_uri",
        "error_message",
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
    }
    assert set(Job.__table__.columns.keys()) == expected
